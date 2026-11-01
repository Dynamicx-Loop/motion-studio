"""Actual native source surfaces versus direct SMPL-X forward reconstruction."""
import json
from pathlib import Path
import tempfile
import unittest

CHECK_TIER = 'robot-static'
CHECK_MODULES = ('numpy', 'mujoco', 'torch', 'smplx')

from motion_studio.studio import Studio
from motion_studio.studio._history import digest
from motion_studio.studio._motion import DEFAULT_MODEL_DIR

try:
    import numpy as np
except ImportError:
    np = None

PYTHON = Path('/data/workspace/motion_studio/externals/UMR/.venv/bin/python')


@unittest.skipUnless(np is not None and PYTHON.is_file() and (DEFAULT_MODEL_DIR/'SMPLX_NEUTRAL.pkl').is_file(),
                     'Native SMPL-X runtime/weights unavailable')
class SourceMeshRuntimeTests(unittest.TestCase):
    def test_mesh_matches_direct_model_across_chunk_boundary_and_y_up_transform(self):
        import smplx
        import torch
        torch.set_num_threads(2)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio = Studio(root/'state',robot_python=PYTHON)
            poses = np.zeros((66,165),dtype=np.float32)
            poses[:,3] = np.linspace(0,.4,66)
            poses[:,49] = np.linspace(-.2,.3,66)
            poses[:,75:90] = .3  # Ignored expressive hand input must stay neutral.
            translation = np.column_stack((np.linspace(0,1,66),np.linspace(.3,.6,66),np.linspace(-.5,.7,66))).astype(np.float32)
            betas = np.linspace(-.15,.15,10).astype(np.float32)
            source = root/'source.npz'
            np.savez(source,poses=poses,trans=translation,betas=betas,gender='neutral',fps=47.5,samp_output_up='y')
            asset = studio.import_motion(source)
            before = digest(studio.motion_source(asset.asset_id))
            response = studio.build_source_mesh_preview(asset.asset_id)
            data = json.loads(studio.source_mesh_preview_file(asset.asset_id).read_text())
            self.assertEqual((response['frame_count'],response['fps']),(66,47.5))
            self.assertEqual(data['input_up_axis'],'y')
            ids = np.array([0,63,64,65])
            model = smplx.SMPLX(asset.model_path,gender='neutral',use_pca=False,flat_hand_mean=True,
                                num_betas=10,ext='pkl',batch_size=4)
            with torch.no_grad():
                direct = model(global_orient=torch.from_numpy(poses[ids,:3]),
                    body_pose=torch.from_numpy(poses[ids,3:66]),
                    betas=torch.from_numpy(np.repeat(betas[None],4,axis=0)),
                    transl=torch.from_numpy(translation[ids]),
                    left_hand_pose=torch.zeros((4,45)),right_hand_pose=torch.zeros((4,45)),return_verts=True)
            native = direct.vertices.numpy()[:,:,[0,2,1]].copy()
            native[:,:,1] *= -1  # Pinned Y-up -> Z-up: (x,y,z) -> (x,-z,y).
            actual_roots = direct.joints.numpy()[:,0][:,[0,2,1]].copy()
            actual_roots[:,1] *= -1
            np.testing.assert_allclose(np.asarray(data['root_positions'])[ids],actual_roots,atol=3e-7,rtol=0)
            faces = np.fromfile(studio.source_mesh_preview_file(asset.asset_id,data['faces']),'<u4').reshape(-1,3)
            np.testing.assert_array_equal(faces,model.faces)
            worst = 0.
            for index,frame in enumerate(ids):
                chunk = data['chunks'][frame//64]
                codes = np.fromfile(studio.source_mesh_preview_file(asset.asset_id,chunk['file']),'<i2').reshape(chunk['count'],data['vertex_count'],3)
                decoded = codes[frame-chunk['start']].astype(float)*.0001 + data['root_positions'][frame]
                worst = max(worst,float(np.max(np.abs(decoded-native[index]))))
                np.testing.assert_allclose(decoded,native[index],atol=5.1e-5,rtol=0)
            self.assertLessEqual(worst,5.1e-5)
            self.assertEqual(studio.list_runs(),())
            self.assertEqual(digest(studio.motion_source(asset.asset_id)),before)
            self.assertEqual(data['zero_source_finger_pose'],True)
            print(f'Direct native SMPL-X reference: faces={len(faces)}, vertices={data["vertex_count"]}, max_axis_error_m={worst:.10g}')
