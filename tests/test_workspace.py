"""Workspace CLI checks use disposable local repositories, never network."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/workspace.py'


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'owned'
        (self.root / 'scripts').mkdir(parents=True)
        (self.root / 'externals').mkdir()
        shutil.copyfile(SCRIPT, self.root / 'scripts/workspace.py')
        self.source = Path(self.temp.name) / 'source'
        self.checkout = self.source / 'externals/converter'
        self.checkout.mkdir(parents=True)
        self.git(self.checkout, 'init', '-q')
        self.git(self.checkout, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.checkout, 'config', 'user.name', 'Fixture')
        (self.checkout / 'source.txt').write_text('pinned\n')
        self.git(self.checkout, 'add', '.')
        self.git(self.checkout, 'commit', '-qm', 'pin')
        self.pin = self.git(self.checkout, 'rev-parse', 'HEAD').strip()
        self.manifest = {'schema_version': 1, 'projects': [{
            'name': 'converter', 'path': 'externals/converter',
            'url': str(self.checkout), 'upstream': str(self.checkout),
            'revision': self.pin}]}
        self.save_manifest()

    def git(self, root, *args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True,
                                       stderr=subprocess.PIPE)

    def save_manifest(self):
        (self.root / 'externals/manifest.json').write_text(json.dumps(self.manifest))

    def command(self, *args):
        return subprocess.run([sys.executable, str(self.root / 'scripts/workspace.py'), *args],
                              text=True, capture_output=True)

    def test_explicit_inspection_uses_owned_pin_and_reports_source_drift_without_mutation(self):
        (self.checkout / 'source.txt').write_text('local edit\n')
        self.manifest['projects'][0]['revision'] = '0' * 40
        self.save_manifest()
        before = self.git(self.checkout, 'status', '--porcelain')
        result = self.command('check', '--source-workspace', str(self.source))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('DRIFT externals/converter @ ' + self.pin, result.stdout)
        self.assertIn('Local changes (preserved)', result.stdout)
        self.assertEqual(self.git(self.checkout, 'status', '--porcelain'), before)
        self.assertEqual((self.checkout / 'source.txt').read_text(), 'local edit\n')


    def test_missing_bootstrap_selects_pin_then_preserves_dirty_existing_checkout(self):
        (self.checkout / 'source.txt').write_text('newer upstream\n')
        self.git(self.checkout, 'commit', '-qam', 'newer')
        result = self.command('bootstrap')
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.root / 'externals/converter'
        self.assertEqual(self.git(target, 'rev-parse', 'HEAD').strip(), self.pin)
        self.assertEqual((target / 'source.txt').read_text(), 'pinned\n')
        (target / 'source.txt').write_text('keep me\n')
        (target / 'untracked.txt').write_text('also keep\n')
        before = self.git(target, 'status', '--porcelain')
        result = self.command('bootstrap')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('KEEP externals/converter', result.stdout)
        self.assertEqual(self.git(target, 'status', '--porcelain'), before)
        self.assertEqual((target / 'source.txt').read_text(), 'keep me\n')
        self.assertEqual((target / 'untracked.txt').read_text(), 'also keep\n')

    def test_read_only_source_option_cannot_redirect_bootstrap(self):
        result = self.command('bootstrap', '--source-workspace', str(self.source))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('read-only', result.stderr)
        self.assertFalse((self.root / 'externals/converter').exists())

    def test_outside_symlink_and_traversal_are_rejected(self):
        (self.root / 'externals/converter').symlink_to(self.checkout)
        result = self.command('bootstrap')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('directly under externals', result.stderr)
        self.manifest['projects'][0]['path'] = 'externals/../escape'
        self.save_manifest()
        result = self.command('bootstrap')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'escape').exists())


if __name__ == '__main__':
    unittest.main()
