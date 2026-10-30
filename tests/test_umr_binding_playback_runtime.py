"""Analytic rigid binding replay checks; no UMR import, assets or motion solve."""
CHECK_TIER = 'robot-static'
CHECK_MODULES = ('numpy', 'mujoco')

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import mujoco
import numpy as np

from motion_studio.integrations._umr_inspection_worker import export_motion
from motion_studio.integrations._umr_human_motion import encode_root_relative


class BindingPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name)
        self.xml = self.run / 'model.xml'
        self.xml.write_text('''<mujoco><worldbody><body name="root">
          <freejoint/><geom type="box" size=".1 .1 .1"/>
          <body name="arm" pos="1 0 0"><joint name="hinge" axis="0 0 1"/>
            <geom type="box" size=".1 .1 .1"/></body>
          </body></worldbody></mujoco>''')
        self.model = mujoco.MjModel.from_xml_path(str(self.xml))
        s = np.sqrt(.5)
        self.qpos = np.array([[0, 0, 1, 1, 0, 0, 0, 0],
                              [2, 3, 1, s, 0, 0, s, np.pi / 2],
                              [-1, -2, 2, 1, 0, 0, 0, -np.pi / 2]])
        self.binding = {'geom_ids': np.array([0, 1]),
                        'local_pos': np.array([[0., 0, 0], [1., 0, 0]])}
        self.robot = SimpleNamespace(
            visual_geom_ids=lambda *_: [0, 1],
            geom_local_mesh=lambda *_: (np.array([[0., 0, 0], [1., 0, 0], [0., 1, 0]]),
                                       np.array([[0, 1, 2]])))

    def save(self, **changes):
        fields = dict(qpos=self.qpos, fps=np.array([30.]), frame_ids=np.arange(3),
                      robot_xml=str(self.xml), robot_joint_names=np.array(['hinge']),
                      ground_z=np.array([0.]))
        fields.update(changes)
        np.savez(self.run / 'motion.npz', **fields)

    def export(self):
        return export_motion(self.run, self.run, self.model, self.binding,
                             self.robot, mujoco, np)

    def test_translated_and_rotated_root_and_hinge_worked_example(self):
        self.save()
        meta = self.export()
        matrices = np.fromfile(self.run / meta['transforms'], dtype=meta.get('transform_dtype', '<f4')).reshape(3, 2, 3, 4)
        points = np.einsum('fgij,gj->fgi', matrices[:, :, :, :3], self.binding['local_pos']) + matrices[:, :, :, 3]
        # Native [x,y,z] -> viewer [y,z,x]. Arm pivot is one metre from root;
        # its slot is another metre along local X. Both rotations affect it.
        expected = [[[0, 1, 0], [0, 1, 2]],
                    [[3, 1, 2], [4, 1, 1]],
                    [[-2, 2, -1], [-3, 2, 0]]]
        np.testing.assert_allclose(points, expected, atol=2e-7, rtol=0)
        self.assertEqual((meta['frame_count'], meta['fps'], meta['frame_ids']), (3, 30., [0, 1, 2]))
        self.assertEqual(meta['slot_piece'], [0, 1])
        self.assertEqual(meta['root_quaternion'], 'wxyz')
        json.dumps(meta, allow_nan=False)

    def test_nonfinite_pose_and_nonuniform_frame_ids_are_rejected(self):
        for fields in ({'qpos': np.full((3, 8), np.nan)},
                       {'frame_ids': np.array([0, 1, 3])}, {'fps': np.array([0.])}):
            with self.subTest(fields=list(fields)):
                self.save(**fields)
                with self.assertRaisesRegex(ValueError, 'Invalid saved motion'):
                    self.export()
                self.assertFalse((self.run / 'motion-transforms.bin').exists())

    def test_human_mesh_quantization_preserves_root_and_bounds_error(self):
        root = np.array([[20., 5., -10.]])
        local = np.array([[[.100049, -.300051, .00001], [1., 0., -1.]]])
        encoded = encode_root_relative(local + root[:, None], root, np)
        self.assertEqual(encoded.dtype, np.dtype('<i2'))
        np.testing.assert_array_equal(encoded, [[[1000, -3001, 0], [10000, 0, -10000]]])
        decoded = encoded.astype(float) * .0001 + root[:, None]
        np.testing.assert_allclose(decoded, local + root[:, None], atol=.000051, rtol=0)
        for vertices in (np.full((1, 1, 3), np.nan), np.full((1, 1, 3), 50.)):
            with self.assertRaisesRegex(ValueError, 'represented safely'):
                encode_root_relative(vertices, root, np)

    def test_wrong_joint_order_is_rejected(self):
        self.save(robot_joint_names=np.array(['wrong']))
        with self.assertRaisesRegex(ValueError, 'joint order'):
            self.export()


if __name__ == '__main__':
    unittest.main()
