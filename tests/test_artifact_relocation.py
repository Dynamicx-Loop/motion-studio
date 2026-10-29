"""Relocation behavior at the approved owned operation seam."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import subprocess
import sys

from motion_studio.artifacts import plan_relocation, relocate, verify_relocation, restore


class ArtifactRelocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'experiments/pilot/nested').mkdir(parents=True)
        self.source = self.root / 'experiments/pilot/nested/item.bin'
        self.source.write_bytes(b'preserved evidence\x00')
        self.inventory = self.root / 'inventory.json'
        self.inventory.write_text(json.dumps({'files': [{
            'path': 'experiments/pilot/nested/item.bin', 'kind': 'file',
            'bytes': 19, 'sha256': 'b22889362dd99acb79137f90a0c201f6155ea8256f22c818345f25e7662b47f38',
            'inbound_references': ['experiments/pilot/README.md']}]}))
        # The literal fixture is independently anchored, not populated by migration.
        entry = json.loads(self.inventory.read_text())
        entry['files'][0]['sha256'] = hashlib.sha256(b'preserved evidence\x00').hexdigest()
        self.inventory.write_text(json.dumps(entry))
        self.anchor = hashlib.sha256(self.inventory.read_bytes()).hexdigest()
        self.destination = self.root / 'outputs/archive/pilot'

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self):
        return plan_relocation(self.root, self.inventory, self.anchor,
                               [('experiments/pilot/nested/item.bin', 'generated-run')],
                               'outputs/archive/pilot')

    def test_source_drift_and_destination_collision_fail_before_mutation(self):
        plan = self.plan()
        self.source.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'drift'):
            relocate(plan)
        self.assertFalse(self.destination.exists())
        self.source.write_bytes(b'preserved evidence\x00')
        self.destination.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.plan()

    def test_interrupted_copy_resumes_and_stale_receipt_is_refused(self):
        plan = self.plan()
        receipt = relocate(plan, step_limit=1)
        self.assertFalse(self.source.is_symlink())
        self.assertEqual(self.source.read_bytes(), b'preserved evidence\x00')
        relocate(plan, resume=True)
        self.assertTrue(self.source.is_symlink())
        self.assertTrue(verify_relocation(receipt)['passed'])
        value = json.loads(receipt.read_text())
        value['plan']['files'][0]['sha256'] = '0' * 64
        receipt.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'Changed'):
            relocate(plan, resume=True)

    def test_symlink_parent_traversal_and_relative_escape_are_refused(self):
        nested = self.source.parent
        outside = self.root / 'outside'
        nested.rename(outside)
        nested.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'traversal'):
            self.plan()

    def test_ordinary_writer_refuses_archive_before_downstream_action(self):
        if __import__('os').geteuid() == 0:
            self.skipTest('write refusal requires ordinary user')
        relocate(self.plan())
        result = subprocess.run([sys.executable, '-c',
            'import pathlib,sys; pathlib.Path(sys.argv[1]).open("w"); print("DOWNSTREAM")',
            str(self.source)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('PermissionError', result.stderr)
        self.assertNotIn('DOWNSTREAM', result.stdout)
        self.assertEqual(self.source.read_bytes(), b'preserved evidence\x00')

    def test_interrupted_alias_installation_keeps_both_members_readable(self):
        second = self.source.with_name('second.bin')
        second.write_bytes(b'second')
        baseline = json.loads(self.inventory.read_text())
        baseline['files'].append({'path': 'experiments/pilot/nested/second.bin',
            'kind': 'file', 'bytes': 6,
            'sha256': hashlib.sha256(b'second').hexdigest()})
        self.inventory.write_text(json.dumps(baseline))
        self.anchor = hashlib.sha256(self.inventory.read_bytes()).hexdigest()
        plan = plan_relocation(self.root, self.inventory, self.anchor,
            [(r['path'], 'generated-run') for r in baseline['files']], 'outputs/archive/pilot')
        receipt = relocate(plan, step_limit=3)
        self.assertTrue(self.source.is_symlink())
        self.assertFalse(second.is_symlink())
        self.assertEqual(self.source.read_bytes(), b'preserved evidence\x00')
        self.assertEqual(second.read_bytes(), b'second')
        relocate(plan, resume=True)
        self.assertTrue(second.is_symlink())
        self.assertTrue(verify_relocation(receipt)['passed'])

    def test_archive_drift_and_unverified_alias_are_refused(self):
        plan = self.plan()
        receipt = relocate(plan)
        target = self.source.resolve()
        target.chmod(0o644)
        target.write_bytes(b'changed archive')
        with self.assertRaisesRegex(ValueError, 'alias|drift'):
            verify_relocation(receipt)
        with self.assertRaises(ValueError):
            restore(receipt)
        self.assertEqual(target.read_bytes(), b'changed archive')

    def test_copy_verify_alias_and_restore_preserve_bytes_and_mode(self):
        mode = self.source.stat().st_mode & 0o777
        plan = self.plan()
        self.assertFalse(self.destination.exists())
        self.assertEqual(plan['files'][0]['compatibility'], 'relative-symlink-readonly')
        receipt = relocate(plan)
        self.assertTrue(self.source.is_symlink())
        self.assertFalse(Path(self.source.readlink()).is_absolute())
        self.assertEqual(self.source.read_bytes(), b'preserved evidence\x00')
        self.assertEqual(self.source.stat().st_mode & 0o222, 0)
        self.assertTrue(verify_relocation(receipt)['passed'])
        restore(receipt)
        self.assertFalse(self.source.is_symlink())
        self.assertEqual(self.source.stat().st_mode & 0o777, mode)
        self.assertTrue((self.destination / 'files/experiments/pilot/nested/item.bin').is_file())


if __name__ == '__main__':
    unittest.main()
