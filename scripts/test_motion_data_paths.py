"""Recorded-path relocation checks independent of installed model assets."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from motion_studio import motion_data_paths as paths


class RecordedMotionPathTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.manifest = Path(self.folder.name) / 'moves.json'
        self.manifest.write_text(json.dumps({
            '/data/motions/soma': '/data/motions/human_models/soma-x/revision',
            '/data/motions/soma/umr_assets':
                '/data/motions/human_models/soma-x/revision/overlays/umr',
            '/data/motions/bvh/wendy':
                '/data/motions/datasets/fzmotion/raw/bvh/wendy/2026-10-19',
        }))
        self.mapping = patch.object(paths, '_MAP', self.manifest)
        self.mapping.start()
        self.addCleanup(self.mapping.stop)

    def test_specific_overlay_move_precedes_model_root(self):
        self.assertEqual(
            paths.canonical_motion_path('/data/motions/soma/umr_assets/model.npz'),
            Path('/data/motions/human_models/soma-x/revision/overlays/umr/model.npz'))

    def test_original_clip_filename_and_suffix_are_preserved(self):
        self.assertEqual(
            paths.canonical_motion_path('/data/motions/bvh/wendy/a clip.bvh'),
            Path('/data/motions/datasets/fzmotion/raw/bvh/wendy/2026-10-19/a clip.bvh'))

    def test_new_and_unrelated_paths_need_no_move_manifest(self):
        self.manifest.unlink()
        for value in ['/data/motions/human_models/smplx/release/model.npz',
                      '/data/motions/soma-other/model.npz', 'relative/model.npz']:
            self.assertEqual(paths.canonical_motion_path(value), Path(value))

    def test_unknown_legacy_dataset_is_not_guessed(self):
        with self.assertRaisesRegex(ValueError, 'No unambiguous'):
            paths.canonical_motion_path('/data/motions/bvh/another-source/clip.bvh')

    def test_config_copy_preserves_values_and_original_record(self):
        original = {'inputs': {'/data/motions/soma/assets/model.npz': 'original-sha'},
                    'settings': [None, 30.0, True],
                    'model': '/data/motions/soma/umr_assets/model.npz'}
        before = copy.deepcopy(original)
        relocated = paths.canonical_motion_config(original)
        self.assertEqual(original, before)
        self.assertEqual(relocated['inputs'], {
            '/data/motions/human_models/soma-x/revision/assets/model.npz': 'original-sha'})
        self.assertEqual(relocated['settings'], [None, 30.0, True])
        self.assertEqual(relocated['model'],
                         '/data/motions/human_models/soma-x/revision/overlays/umr/model.npz')


if __name__ == '__main__':
    unittest.main()
