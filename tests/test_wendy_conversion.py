"""System-Python checks of the owned conversion boundary; no solver imports."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from motion_studio.integrations.wendy import WendyConversionRequest, convert_wendy


class WendyConversionTests(unittest.TestCase):
    def test_invalid_numeric_configuration_is_rejected_without_writes(self):
        cases = ({'frames': True}, {'frames': 2, 'start_frame': -1},
                 {'frames': 2, 'unit_scale': float('nan')},
                 {'frames': 2, 'unit_scale': 1},
                 {'frames': 2, 'betas': [0] * 9 + [float('inf')]})
        for value in cases:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                config = root / 'config.json'
                config.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    convert_wendy(WendyConversionRequest(config, workspace=root))
                self.assertEqual(sorted(p.name for p in root.iterdir()), ['config.json'])

    def setup_request(self, root, **changes):
        source = root / 'source.bvh'
        source.write_bytes((Path(__file__).parent / 'fixtures/wendy-boundaries.bvh').read_bytes())
        model = root / 'model.npz'
        model.write_bytes(b'placeholder: never opened by failure tests')
        value = dict(source=str(source), model=str(model), output='new/motion.npz',
                     frames=2, start_frame=3)
        value.update(changes)
        config = root / 'config.json'
        config.write_text(json.dumps(value))
        return WendyConversionRequest(config, workspace=root)

    def test_known_five_frame_source_rejects_end_past_five(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.setup_request(root, frames=3)
            with self.assertRaisesRegex(ValueError, r'\[3, 6\).*\[0, 5\)'):
                convert_wendy(request)
            self.assertFalse((root / 'new').exists())

    def test_missing_source_is_reported_without_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.setup_request(root, source=str(root / 'absent.bvh'))
            with self.assertRaises(FileNotFoundError):
                convert_wendy(request)
            self.assertFalse((root / 'new').exists())

    def test_all_output_conflicts_preserve_existing_bytes(self):
        suffixes = ('.npz', '.diagnostics.npz', '.report.json', '.provenance.json',
                    '.source.bvh', '.conversion.log', '.conversion.lock', '.conversion')
        for suffix in suffixes:
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                request = self.setup_request(root)
                occupied = (root / 'new/motion.npz').with_suffix(suffix)
                occupied.parent.mkdir()
                occupied.write_bytes(b'previous result')
                with self.assertRaises(FileExistsError):
                    convert_wendy(request)
                self.assertEqual(occupied.read_bytes(), b'previous result')
                self.assertEqual(list(occupied.parent.iterdir()), [occupied])

    def test_nonfinite_source_is_rejected_even_outside_excerpt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.setup_request(root)
            source = root / 'source.bvh'
            source.write_text(source.read_text().replace('0 0 0 0 0 0', 'nan 0 0 0 0 0', 1))
            with self.assertRaisesRegex(ValueError, 'source frame 0'):
                convert_wendy(request)
            self.assertFalse((root / 'new').exists())

    def test_incompatible_pin_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.setup_request(root)
            manifest = root / 'externals/manifest.json'
            manifest.parent.mkdir()
            manifest.write_text(json.dumps({'projects': [
                {'name': 'hiphi2smplx', 'revision': '0' * 40}]}))
            with self.assertRaisesRegex(ValueError, 'revision'):
                convert_wendy(request)
            self.assertFalse((root / 'new').exists())

    def test_cli_help_and_public_import_need_only_python_standard_library(self):
        root = Path(__file__).resolve().parents[1]
        for command in ([sys.executable, '-S', str(root / 'scripts/convert_wendy.py'), '--help'],
                        [sys.executable, '-S', '-c',
                         'from motion_studio.integrations.wendy import convert_wendy; '
                         'import sys; assert "numpy" not in sys.modules; '
                         'assert "hiphi2smplx" not in sys.modules']):
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_configuration_cannot_silently_contain_invalid_values(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.setup_request(root, unused=float('nan'))
            with self.assertRaisesRegex(ValueError, 'Unknown configuration'):
                convert_wendy(request)
            self.assertFalse((root / 'new').exists())

    def test_source_hierarchy_must_be_valid_before_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.setup_request(root)
            source = root / 'source.bvh'
            source.write_text(source.read_text().replace('ROOT Hips', 'JOINT Hips'))
            with self.assertRaisesRegex(ValueError, 'hierarchy'):
                convert_wendy(request)
            self.assertFalse((root / 'new').exists())

    def test_invalid_excerpt_is_rejected_without_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root / 'config.json'
            config.write_text(json.dumps({'frames': 0}))
            with self.assertRaisesRegex(ValueError, 'frames'):
                convert_wendy(WendyConversionRequest(config, workspace=root))
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['config.json'])


if __name__ == '__main__':
    unittest.main()
