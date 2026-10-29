"""Observable preservation receipts using independent temporary Git fixtures."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile
import unittest

from motion_studio.preservation import capture_inventory, verify_inventory


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / 'workspace'
        self.root.mkdir()
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.email', 'test@example.invalid')
        git(self.root, 'config', 'user.name', 'Test')
        (self.root / 'owned.py').write_text('original\n')
        (self.root / '.gitignore').write_text('outputs/\n.venv/\n.env\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'Fixture')
        (self.root / 'owned.py').write_text('changed\n')
        (self.root / 'new.py').write_text('untracked\n')
        self.destination = self.base / 'receipt'

    def tearDown(self):
        self.temporary.cleanup()

    def test_capture_seals_known_bytes_and_verifies_dirty_source_recovery(self):
        before = git(self.root, 'status', '--porcelain=v1', '-uall')
        result = capture_inventory(self.root, self.destination)
        manifest = json.loads((result.receipt / 'inventory.json').read_text())
        owned = next(r for r in manifest['files'] if r['path'] == 'owned.py')
        self.assertEqual(owned['sha256'], hashlib.sha256(b'changed\n').hexdigest())
        self.assertEqual(owned['role'], 'source')
        self.assertEqual(manifest['repositories'][0]['recovery']['status'], 'verified')
        self.assertEqual(manifest['repositories'][0]['recovery']['untracked_source_files'], 1)
        self.assertEqual(git(self.root, 'status', '--porcelain=v1', '-uall'), before)
        self.assertTrue(verify_inventory(result.receipt).passed)

    def test_changed_alias_target_is_drift_even_when_bytes_match(self):
        (self.root / 'first.txt').write_text('same')
        (self.root / 'second.txt').write_text('same')
        alias = self.root / 'alias.txt'
        alias.symlink_to('first.txt')
        capture_inventory(self.root, self.destination)
        seal_before = (self.destination / 'seal.json').read_bytes()
        alias.unlink()
        alias.symlink_to('second.txt')
        result = verify_inventory(self.destination)
        self.assertFalse(result.passed)
        self.assertTrue(any('symlink' in error.lower() for error in result.errors), result.errors)
        self.assertEqual((self.destination / 'seal.json').read_bytes(), seal_before)

    def test_artifacts_keep_cohort_links_and_distinct_storage_accounting(self):
        experiment = self.root / 'experiments' / 'pilot'
        (experiment / 'viewer').mkdir(parents=True)
        (experiment / 'README.md').write_text('[mesh](viewer/mesh.bin)\n')
        (experiment / 'viewer' / 'mesh.bin').write_bytes(b'abc')
        (experiment / 'viewer' / 'alias.bin').symlink_to('mesh.bin')
        capture_inventory(self.root, self.destination)
        manifest = json.loads((self.destination / 'inventory.json').read_text())
        mesh = next(item for item in manifest['files'] if item['path'].endswith('/mesh.bin'))
        self.assertEqual(mesh['cohort'], 'pilot')
        self.assertEqual(mesh['sha256'], 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertIn('experiments/pilot/README.md', mesh['inbound_references'])
        self.assertEqual(manifest['storage']['logical_file_bytes'] - manifest['storage']['unique_stored_file_bytes'], 3)

    def test_provenance_named_input_and_environment_locations_are_explicit(self):
        asset = self.base / 'upstream-model.bin'
        asset.write_bytes(b'abc')
        experiment = self.root / 'experiments' / 'frozen'
        experiment.mkdir(parents=True)
        (experiment / 'provenance.json').write_text(json.dumps({'inputs_sha256': {
            str(asset): 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'}}))
        environment = self.root / '.venv'
        environment.mkdir()
        (environment / 'do-not-read.txt').write_text('not an environment backup')
        capture_inventory(self.root, self.destination, source_roots=[self.base])
        manifest = json.loads((self.destination / 'inventory.json').read_text())
        closure = manifest['frozen_reference_checks']
        self.assertTrue(any(item['path'] == str(asset) and item['matches'] for item in closure))
        self.assertTrue(any(item['absolute_path'] == str(asset) for item in manifest['files']))
        self.assertTrue(any(item['path'] == '.venv/' for item in manifest['repositories'][0]['ignored_entries']))
        self.assertFalse(any(item['absolute_path'].endswith('do-not-read.txt') for item in manifest['files']))

    def test_linked_worktree_and_compatibility_aliases_are_recorded_without_traversal(self):
        linked = self.root / 'externals' / 'historical'
        linked.parent.mkdir()
        git(self.root, 'worktree', 'add', '-q', '-b', 'historical', str(linked))
        compatibility = self.base / 'old-location'
        compatibility.mkdir()
        (compatibility / 'owned.py').symlink_to(self.root / 'owned.py')
        (compatibility / 'missing').symlink_to('gone')
        capture_inventory(self.root, self.destination, compatibility_roots=[compatibility])
        manifest = json.loads((self.destination / 'inventory.json').read_text())
        historical = next(item for item in manifest['repositories'] if item['id'] == 'historical')
        self.assertIn(str(linked), historical['worktrees_porcelain'])
        self.assertEqual(manifest['compatibility'][0]['entries'][0]['symlink_target'], 'gone')
        self.assertFalse(verify_inventory(self.destination).passed)
        self.assertTrue((compatibility / 'missing').is_symlink())

    def test_new_ignored_artifact_is_detected_without_mutating_receipt(self):
        outputs = self.root / 'outputs'
        outputs.mkdir()
        (outputs / 'original.bin').write_bytes(b'abc')
        self.destination = outputs / 'inventory'
        capture_inventory(self.root, self.destination)
        inventory_before = (self.destination / 'inventory.json').read_bytes()
        (outputs / 'new.bin').write_bytes(b'extra')
        result = verify_inventory(self.destination)
        self.assertFalse(result.passed)
        self.assertTrue(any('new.bin' in error for error in result.errors), result.errors)
        self.assertEqual((self.destination / 'inventory.json').read_bytes(), inventory_before)

    def test_existing_receipt_and_broken_links_fail_without_overwriting(self):
        self.destination.mkdir()
        marker = self.destination / 'keep.txt'
        marker.write_text('keep')
        with self.assertRaises(FileExistsError):
            capture_inventory(self.root, self.destination)
        self.assertEqual(marker.read_text(), 'keep')
        broken_receipt = self.base / 'broken-receipt'
        (self.root / 'broken.txt').symlink_to('missing.txt')
        capture_inventory(self.root, broken_receipt)
        result = verify_inventory(broken_receipt)
        self.assertFalse(result.passed)
        self.assertTrue(any('Broken symlink' in e for e in result.errors))

    def test_credentials_are_not_read_into_patch_archive_or_manifest(self):
        credential = self.root / '.env'
        credential.write_text('before-secret')
        git(self.root, 'add', '-f', '.env')
        git(self.root, 'commit', '-qm', 'Tracked credential fixture')
        credential.write_text('after-secret')
        aws = self.root / '.aws'
        aws.mkdir()
        (aws / 'credentials').write_text('aws-secret')
        capture_inventory(self.root, self.destination)
        payload = b''.join(p.read_bytes() for p in self.destination.rglob('*') if p.is_file())
        for value in [b'before-secret', b'after-secret', b'aws-secret']:
            self.assertNotIn(value, payload)
        self.assertTrue(verify_inventory(self.destination).passed)

    def test_tampered_recovery_payload_is_rejected(self):
        capture_inventory(self.root, self.destination)
        patch = self.destination / 'recovery' / 'workspace' / 'tracked.patch'
        patch.write_bytes(b'corrupt')
        result = verify_inventory(self.destination)
        self.assertFalse(result.passed)
        self.assertTrue(any('receipt payload' in e.lower() for e in result.errors))

    def test_unsealed_receipt_payload_is_reported(self):
        capture_inventory(self.root, self.destination)
        (self.destination / 'extra.txt').write_text('unsealed')
        result = verify_inventory(self.destination)
        self.assertFalse(result.passed)
        self.assertTrue(any('Unsealed' in e for e in result.errors))

    def test_missing_dependency_is_a_failed_verification_report(self):
        dependency = self.root / 'externals' / 'dependency'
        dependency.parent.mkdir()
        subprocess.run(['git', 'clone', '-q', '--no-hardlinks', str(self.root), str(dependency)], check=True)
        capture_inventory(self.root, self.destination)
        dependency.rename(dependency.with_name('moved'))
        result = verify_inventory(self.destination)
        self.assertFalse(result.passed)
        self.assertTrue(any('repository unavailable' in e.lower() for e in result.errors), result.errors)


if __name__ == '__main__':
    unittest.main()
