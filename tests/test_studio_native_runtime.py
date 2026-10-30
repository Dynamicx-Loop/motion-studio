"""Opt-in saved-artifact regression for fresh native Studio smoke cohorts.

Run after the documented fresh native smoke commands, setting
STUDIO_PRIMITIVE_SMOKE and STUDIO_G1_SMOKE to their fresh output directories.
No native computation or historical mutation occurs in these checks.
"""
CHECK_TIER = 'saved-evidence'
CHECK_MODULES = ('numpy',)

import json
import os
from pathlib import Path
import unittest

import numpy as np

from motion_studio.studio import Studio


class NativeArtifactTests(unittest.TestCase):
    def cohort(self, variable):
        root = os.environ.get(variable)
        if not root:
            self.skipTest(f'{variable} fresh native smoke path not supplied')
        studio = Studio(Path(root) / 'state')
        run, = studio.list_runs()
        return studio, run

    def test_primitive_binding_replays_barycentric_fallback_and_preserves_closest_diagnostic(self):
        studio, run = self.cohort('STUDIO_PRIMITIVE_SMOKE')
        receipt = studio.stage_receipt(run.run_id, run.revision_id, 'binding')
        path = lambda stage, name: studio.stage_artifact(run.run_id, run.revision_id, stage, name)
        with np.load(path('sampling', 'dataset.npz'), allow_pickle=True) as data:
            names = data['names'].astype(str).tolist()
            human = next(i for i,n in enumerate(names) if n.startswith('smplx_'))
            vertices, faces = data[f'mesh_vertices_{human}'], data[f'mesh_faces_{human}']
        with np.load(path('binding', 'binding.npz'), allow_pickle=False) as binding:
            reconstructed = (vertices[faces[binding['source_face_ids']]] * binding['source_bary'][:,:,None]).sum(axis=1)
            np.testing.assert_allclose(binding['source_points'], reconstructed, atol=5e-7, rtol=0)
            # This cohort must actually exercise native's tiny-triangle fallback.
            self.assertGreater(float(np.abs(binding['source_native_closest_points']-reconstructed).max()), 1e-5)
            expected = binding['source_points'].copy()
        payload = json.loads(path('binding','bindings.json').read_text())
        np.testing.assert_allclose(payload['source'], expected, atol=5e-7, rtol=0)
        self.assertTrue(all(mesh is None for mesh in payload['meshes']))
        self.assertGreater(receipt['validation']['source_native_closest_axis_discrepancy_max_m'], 1e-5)
        config = json.loads(path('sampling','humanoid_retarget_runtime_config.json').read_text())
        self.assertEqual(config['robot']['joint_limits'], {})
        self.assertEqual(config['smplx_model_dir'], receipt['inputs']['motion']['model_path'])
        self.assertFalse(receipt['inputs']['official_g1'])
        self.assertFalse(list((studio.roots.runs/run.run_id/run.revision_id).rglob('motion.npz')))

    def test_official_g1_wrapper_preserves_pose_and_exact_smoke_frames(self):
        studio, run = self.cohort('STUDIO_G1_SMOKE')
        path = lambda stage, name: studio.stage_artifact(run.run_id, run.revision_id, stage, name)
        derived = json.loads(path('sampling','model-derivation.json').read_text())
        self.assertTrue(derived['official_g1_native_wrapper'])
        self.assertEqual(derived['native_root_body'], 'unitree_g1_float_root')
        self.assertLessEqual(derived['all_named_body_world_position_max_error_m'], 1e-10)
        self.assertLessEqual(derived['all_named_body_world_rotation_max_error'], 1e-10)
        receipt = studio.stage_receipt(run.run_id, run.revision_id, 'retargeting')
        config = json.loads(path('sampling','humanoid_retarget_runtime_config.json').read_text())
        self.assertEqual(config['smplx_model_dir'], receipt['inputs']['motion']['model_path'])
        self.assertEqual(config['correspondence']['dataset']['smpl_models'][0]['dir'], receipt['inputs']['motion']['model_path'])
        with np.load(path('retargeting','motion.npz'), allow_pickle=True) as data:
            np.testing.assert_array_equal(data['frame_ids'], [0,1,2])
            self.assertEqual(data['qpos'].shape, (3,36))
        self.assertEqual(receipt['settings']['epochs'], 2)
        self.assertLessEqual(receipt['validation']['quaternion_norm_max_error'], 1e-6)
        self.assertLessEqual(receipt['validation']['joint_limit_max_excess_rad'], 1e-6)


if __name__ == '__main__':
    unittest.main()
