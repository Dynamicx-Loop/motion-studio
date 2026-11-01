"""Independent native CPU preview numerical smoke check; opt-in robot runtime."""
import json
from pathlib import Path
import tempfile
import unittest

from motion_studio.studio import Studio
from motion_studio.studio._motion import DEFAULT_MODEL_DIR
from motion_studio.studio._history import digest

CHECK_TIER = 'robot-static'
CHECK_MODULES = ('numpy', 'mujoco', 'torch')

try:
    import numpy as np
except ImportError:
    np = None

PreviewStudio = Studio

PYTHON = Path('/data/workspace/motion_studio/externals/UMR/.venv/bin/python')


@unittest.skipUnless(np is not None and PYTHON.is_file() and (DEFAULT_MODEL_DIR / 'SMPLX_NEUTRAL.pkl').is_file(),
                     'Independent SMPL-X runtime/weights unavailable')
class SourcePreviewRuntime(unittest.TestCase):
    def test_native_body_joints_keep_exact_frames_fps_and_translation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio = PreviewStudio(root / 'state', robot_python=PYTHON)
            source = root / 'two-frames.npz'
            translation = np.array([[0.,0.,0.], [.25,-.5,1.]])
            np.savez(source, poses=np.zeros((2,66)), trans=translation, betas=np.zeros(10),
                     gender='neutral', fps=48., samp_output_up='z')
            asset = studio.import_motion(source)
            before = digest(studio.motion_source(asset.asset_id))
            result = studio.build_source_preview(asset.asset_id)
            payload = json.loads(studio.source_preview_file(asset.asset_id).read_text())
            self.assertEqual((result['frame_count'], result['fps']), (2,48.))
            joints = np.asarray(payload['frames'])
            self.assertEqual(joints.shape, (2,22,3))
            np.testing.assert_allclose(joints[1]-joints[0], np.repeat(translation[1,None],22,axis=0), atol=3e-7)
            self.assertEqual(payload['parents'][0], -1)
            self.assertTrue(np.isfinite(payload['ground_z']))
            self.assertEqual(studio.list_runs(), ())
            self.assertEqual(digest(studio.motion_source(asset.asset_id)), before)
