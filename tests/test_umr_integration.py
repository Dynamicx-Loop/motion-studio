"""Public-interface safety tests; no upstream imports, GPU, or model assets."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from motion_studio.integrations.umr import reproduce_g1_baseline


class G1BaselineTests(unittest.TestCase):
    def test_existing_run_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'run'
            output.mkdir()
            marker = output / 'original.txt'
            marker.write_text('preserve')
            with self.assertRaises(FileExistsError):
                reproduce_g1_baseline(output, workspace=Path(folder))
            self.assertEqual(marker.read_text(), 'preserve')
            self.assertEqual(list(output.iterdir()), [marker])

    def test_output_in_external_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            output = workspace / 'externals/UMR/run'
            with self.assertRaisesRegex(ValueError, 'outside external'):
                reproduce_g1_baseline(output, workspace=workspace)
            self.assertFalse(output.exists())

    def test_unreviewed_pin_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / 'externals').mkdir()
            (workspace / 'externals/manifest.json').write_text(json.dumps({
                'projects': [{'name': 'UMR', 'revision': 'unreviewed'}]}))
            with self.assertRaisesRegex(ValueError, 'compatibility'):
                reproduce_g1_baseline(workspace / 'run', workspace=workspace)
            self.assertFalse((workspace / 'run').exists())

    def test_cli_help_needs_no_umr_runtime(self):
        result = subprocess.run(['python3', 'scripts/reproduce_umr_g1.py', '--help'],
                                text=True, capture_output=True, check=True)
        self.assertIn('--output', result.stdout)


if __name__ == '__main__':
    unittest.main()
