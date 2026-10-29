"""Saved viewer graph checks do not run historical exporters."""
import json
from pathlib import Path
import tempfile
import unittest
from motion_studio.artifacts.viewer import verify_saved_viewer


class ViewerTests(unittest.TestCase):
    def test_missing_resource_or_transform_shape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'manifest.json').write_text(json.dumps({'frames': 2, 'fps': 90,
                'robots': {'robot': {'parts': [{'vertices': 'v.bin', 'faces': 'f.bin'}],
                                    'variants': [{'transforms': 't.bin'}]}}}))
            (root / 'v.bin').write_bytes(b'0' * 12)
            (root / 'f.bin').write_bytes(b'0' * 12)
            (root / 't.bin').write_bytes(b'0' * 96)
            self.assertTrue(verify_saved_viewer(root)['passed'])
            (root / 'index.html').write_text('<script type="importmap">{"imports":{"three":"./vendor/three.js"}}</script>')
            self.assertFalse(verify_saved_viewer(root)['passed'])
            (root / 'index.html').unlink()
            (root / 't.bin').write_bytes(b'0' * 4)
            self.assertFalse(verify_saved_viewer(root)['passed'])
            (root / 'f.bin').unlink()
            self.assertFalse(verify_saved_viewer(root)['passed'])
