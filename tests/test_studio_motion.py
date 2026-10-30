"""Motion import outcomes through the owned Studio interface."""
from pathlib import Path
import hashlib
import json
from test_studio_http import serving, request
import tempfile
import unittest

try:
    import numpy as np
except ImportError:
    np = None

from motion_studio.studio import Studio, StudioError


@unittest.skipIf(np is None, 'NumPy is required for safe motion import')
class MotionImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.models = self.root / 'models'
        self.models.mkdir()
        (self.models / 'SMPLX_NEUTRAL.pkl').write_bytes(b'local licensed model stand-in')
        self.studio = Studio(self.root / 'state', smplx_model_dir=self.models)

    def source(self, **changes):
        arrays = dict(poses=np.zeros((3, 165), dtype=np.float32),
                      trans=np.zeros((3, 3)), betas=np.arange(10.),
                      gender='neutral', mocap_frame_rate=30., samp_output_up='z')
        arrays.update(changes)
        path = self.root / 'motion.npz'
        np.savez(path, **arrays)
        return path

    def test_import_and_draft_selection_through_http(self):
        source = self.source()
        draft = self.studio.create_draft('HTTP study')
        with serving(self.studio) as server:
            status, _, body = request(server, 'POST', '/api/motions',
                json.dumps({'source_path': str(source), 'metadata': {}}),
                {'Content-Type': 'application/json'})
            self.assertEqual(status, 201)
            asset_id = json.loads(body)['asset_id']
            status, _, body = request(server, 'POST', f'/api/runs/{draft.run_id}/motion',
                json.dumps({'asset_id': asset_id}), {'Content-Type': 'application/json'})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)['motion_asset_id'], asset_id)
            status, _, body = request(server, 'GET', '/api/state')
            self.assertEqual(json.loads(body)['motions'][0]['frame_count'], 3)
            self.assertEqual(request(server, 'GET', '/motion.js')[0], 200)

    def test_hiphi_headers_retain_exact_full_clip_timing(self):
        path = self.root / 'hiphi.npz'
        np.savez(path, poses=np.zeros((5468, 165), dtype=np.float32),
                 smpl_pose_axis_angle=np.zeros((5468, 55, 3), dtype=np.float32),
                 trans=np.zeros((5468, 3)), transl=np.zeros((5468, 3)),
                 betas=np.zeros(10), gender='neutral', output_up='y', coordinate_up='y',
                 mocap_framerate=np.float32(90.00090026855469),
                 fps=np.float32(90.00090026855469), frame_time=0.011111, model_type='smplx')
        asset = self.studio.import_motion(path)
        self.assertEqual((asset.frame_count, asset.fps, asset.up_axis), (5468, 90.00090026855469, 'y'))
        self.assertIn('smpl_pose_axis_angle', asset.channels)

    def test_pickled_code_is_never_executed(self):
        marker = self.root / 'executed'
        class Payload:
            def __reduce__(self):
                return (eval, (f"__import__('pathlib').Path({str(marker)!r}).write_text('executed')",))
        source = self.source(extra=np.array([Payload()], dtype=object))
        with self.assertRaises(StudioError):
            self.studio.import_motion(source)
        self.assertFalse(marker.exists())
        self.assertEqual(self.studio.list_motions(), ())

    def test_boolean_fps_and_conflicting_declared_units_are_rejected(self):
        for changes in ({'mocap_frame_rate': True}, {'translation_units': 'centimetres'}):
            with self.subTest(changes=list(changes)):
                with self.assertRaises(StudioError):
                    self.studio.import_motion(self.source(**changes))

    def test_missing_metadata_requires_explicit_values_and_missing_weights_fail(self):
        path = self.root / 'missing.npz'
        np.savez(path, poses=np.zeros((2, 66)), trans=np.zeros((2, 3)), betas=np.zeros(10))
        with self.assertRaisesRegex(StudioError, 'supply it explicitly'):
            self.studio.import_motion(path)
        metadata = {'fps': 60., 'gender': 'neutral', 'up_axis': 'y'}
        imported = self.studio.import_motion(path, metadata=metadata)
        self.assertEqual((imported.frame_count, imported.fps, imported.up_axis), (2, 60., 'y'))
        self.assertEqual(imported.metadata_sources, dict(fps='explicit', gender='explicit', up_axis='explicit'))
        (self.models / 'SMPLX_NEUTRAL.pkl').unlink()
        with self.assertRaisesRegex(StudioError, 'missing or changed'):
            self.studio.motion_file(imported.asset_id)
        # Saved metadata and preserved source viewing remain usable without weights.
        self.assertEqual(self.studio.get_motion(imported.asset_id), imported)
        with self.assertRaisesRegex(StudioError, 'Install matching'):
            self.studio.import_motion(self.source())

    def test_pickle_arrays_malformed_layouts_and_aliases_never_publish_assets(self):
        for changes in ({'poses': np.zeros((3, 72))}, {'poses': np.zeros((2, 3, 165))},
                        {'trans': np.zeros((2, 3))}, {'betas': np.zeros((3, 10))},
                        {'poses': np.full((3, 165), np.nan)}, {'mocap_frame_rate': 0.},
                        {'fps': 25.}, {'gender': 'unknown'}, {'samp_output_up': 'x'},
                        {'timestamps': [0., .1, .3]}, {'extra': np.array([object()], dtype=object)}):
            with self.subTest(changes=list(changes)):
                with self.assertRaises(StudioError):
                    self.studio.import_motion(self.source(**changes))
        self.assertEqual(self.studio.list_motions(), ())

    def test_reimport_is_identical_new_bytes_make_new_versions_and_tampering_fails(self):
        source = self.source()
        first = self.studio.import_motion(source)
        self.assertEqual(self.studio.import_motion(source), first)
        second = self.studio.import_motion(self.source(trans=np.ones((3, 3))))
        self.assertNotEqual(second.asset_id, first.asset_id)
        self.studio.motion_file(first.asset_id).write_bytes(b'changed')
        with self.assertRaisesRegex(StudioError, 'missing or changed'):
            self.studio.motion_file(first.asset_id)
        self.assertEqual(self.studio.get_motion(first.asset_id), first)

    def test_conflicting_baseline_aliases_and_timing_are_rejected(self):
        for changes in ({'transl': np.ones((3, 3))},
                        {'smpl_pose_axis_angle': np.ones((3, 55, 3))},
                        {'coordinate_up': 'y'}, {'frame_time': .5}):
            with self.subTest(changes=list(changes)):
                with self.assertRaises(StudioError):
                    self.studio.import_motion(self.source(**changes))
        self.assertEqual(self.studio.list_motions(), ())

    def test_import_preserves_source_and_selects_persistent_draft(self):
        source = self.source()
        original = source.read_bytes()
        asset = self.studio.import_motion(source)
        self.assertEqual((asset.frame_count, asset.fps, asset.pose_layout), (3, 30., 'smplx-full-165'))
        self.assertEqual(asset.betas, tuple(float(n) for n in range(10)))
        self.assertEqual(asset.source_sha256, hashlib.sha256(original).hexdigest())
        self.assertIn('neutral hands', asset.reconstruction)
        draft = self.studio.create_draft('Motion study')
        selected = self.studio.select_motion(draft.run_id, asset.asset_id)
        source.rename(self.root / 'moved.npz')
        reopened = Studio(self.root / 'state', smplx_model_dir=self.models)
        self.assertEqual(reopened.get_run(draft.run_id).motion_asset_id, asset.asset_id)
        self.assertEqual(selected.revision_id, 'r0002')
        self.assertEqual(reopened.motion_source(asset.asset_id).read_bytes(), original)
        with np.load(reopened.motion_file(asset.asset_id), allow_pickle=False) as safe:
            self.assertEqual(safe['poses'].shape, (3, 165))
            self.assertEqual(float(safe['mocap_frame_rate']), 30.)
        self.assertEqual(reopened.list_motions(), (asset,))


if __name__ == '__main__':
    unittest.main()
