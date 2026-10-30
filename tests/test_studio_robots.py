"""Robot import and numeric pose behavior through the public Studio seam."""
from pathlib import Path
import math
import tempfile
import unittest

from motion_studio.studio import Studio, StudioError

PYTHON = Path('/data/workspace/motion_studio/externals/UMR/.venv/bin/python')


@unittest.skipUnless(PYTHON.is_file(), 'pinned independent MuJoCo runtime unavailable')
class RobotImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.xml = self.source / 'robot.xml'
        self.xml.write_text('''<mujoco><compiler angle="degree"/>
<default><joint type="hinge" range="-90 45" limited="true"/></default>
<worldbody><body name="pelvis" pos="0 0 1"><freejoint/>
<geom type="box" size=".1 .1 .1"/><body name="torso" pos="0 0 .3">
<joint name="shoulder"/><geom type="capsule" size=".05 .2"/>
</body></body></worldbody></mujoco>''')
        self.studio = Studio(self.root / 'state', robot_python=PYTHON)

    def test_import_uses_compiled_defaults_and_preserves_source(self):
        original = self.xml.read_bytes()
        asset = self.studio.import_robot(self.xml)
        self.assertEqual(asset.root_body, 'pelvis')
        self.assertEqual(asset.bodies, ('pelvis', 'torso'))
        self.assertAlmostEqual(asset.joints[0].minimum_rad, -math.pi / 2)
        self.assertAlmostEqual(asset.joints[0].maximum_rad, math.pi / 4)
        self.assertEqual(asset.joints[0].name, 'shoulder')
        self.assertEqual(self.xml.read_bytes(), original)
        self.assertEqual(self.studio.import_robot(self.xml).asset_id, asset.asset_id)
        self.xml.unlink()
        reopened = Studio(self.root / 'state', robot_python=PYTHON)
        self.assertEqual(reopened.get_robot(asset.asset_id), asset)
        self.assertTrue(reopened.robot_file(asset.asset_id, 'source/robot.xml').is_file())
        preview = reopened.preview_robot(asset.asset_id)
        self.assertEqual(len(preview['transforms']), 2)
        self.assertAlmostEqual(preview['transforms'][0]['position'][2], 1)

    def test_pose_limits_named_snapshots_and_fresh_revisions_survive_reopen(self):
        asset = self.studio.import_robot(self.xml)
        draft = self.studio.create_draft('Calibration')
        qpos = list(asset.default_qpos)
        qpos[0] = .25
        qpos[7] = .5
        run = self.studio.save_robot_pose(draft.run_id, asset.asset_id, name='Arms raised',
                                         qpos=qpos, torso_body='torso')
        self.assertEqual(run.revision_id, 'r0002')
        self.assertEqual(run.robot_asset_id, asset.asset_id)
        self.assertEqual(next(x.status for x in run.stages if x.stage == 'preparation'), 'available')
        pose = self.studio.get_robot_pose(asset.asset_id, run.robot_pose_id)
        self.assertEqual(pose.qpos[7], .5)
        self.assertEqual(pose.torso_body, 'torso')
        self.assertEqual(pose.units, 'metres; radians; root quaternion wxyz')
        same = self.studio.save_robot_pose(draft.run_id, asset.asset_id, name='Arms raised',
                                          qpos=qpos, torso_body='torso')
        self.assertEqual(same.revision_id, 'r0002')
        qpos[7] = -.5
        changed = self.studio.save_robot_pose(draft.run_id, asset.asset_id, name='Arms down',
                                             qpos=qpos, torso_body='pelvis')
        self.assertEqual(changed.revision_id, 'r0003')
        reopened = Studio(self.root / 'state', robot_python=PYTHON)
        self.assertEqual(reopened.get_robot_pose(asset.asset_id, run.robot_pose_id), pose)
        previous = self.studio.roots.runs / run.run_id / 'r0002' / 'robot.json'
        self.assertEqual(__import__('json').loads(previous.read_text())['pose_id'], run.robot_pose_id)
        self.assertEqual(len(reopened.list_robot_poses(asset.asset_id)), 2)
        self.assertEqual(self.studio.get_robot(asset.asset_id).default_qpos[7], 0)
        for invalid in ([*qpos[:7], 2], [*qpos[:3], 0, 0, 0, 0, 0], [float('nan')]*8):
            with self.assertRaises(StudioError):
                self.studio.save_robot_pose(draft.run_id, asset.asset_id, name='Invalid',
                                           qpos=invalid, torso_body='torso')
        with self.assertRaises(StudioError):
            self.studio.save_robot_pose(draft.run_id, asset.asset_id, name='Wrong torso',
                                       qpos=qpos, torso_body='missing')
        self.assertEqual(reopened.get_run(draft.run_id).revision_id, 'r0003')

    def test_nested_closure_and_recorded_fixed_to_free_derivation(self):
        (self.source / 'parts').mkdir()
        body = self.xml.read_text().split('<worldbody>')[1].split('</worldbody>')[0]
        body = body.replace('<freejoint/>', '').replace('<geom type="box" size=".1 .1 .1"/>', '')
        (self.source / 'parts' / 'body.xml').write_text('<mujocoinclude>' + body + '</mujocoinclude>')
        (self.source / 'parts' / 'outer.xml').write_text('<mujocoinclude><include file="parts/body.xml"/></mujocoinclude>')
        self.xml.write_text('<mujoco><compiler angle="degree"/>'
            '<default><joint range="-90 45" limited="true"/></default>'
            '<worldbody><include file="parts/outer.xml"/></worldbody></mujoco>')
        original = self.xml.read_bytes()
        with self.assertRaisesRegex(StudioError, 'floating root'):
            self.studio.import_robot(self.xml)
        asset = self.studio.import_robot(self.xml, derive_free_root=True)
        self.assertEqual(len(asset.default_qpos), 8)
        self.assertTrue(any('Synthetic root inertia' in x for x in asset.derived))
        self.assertIn('source/parts/body.xml', asset.files)
        self.assertEqual(self.xml.read_bytes(), original)
        self.assertEqual(self.studio.preview_robot(asset.asset_id)['transforms'][0]['position'][2], 1.3)
        copied = self.studio.robot_file(asset.asset_id, 'source/parts/body.xml')
        copied.write_text('changed')
        with self.assertRaisesRegex(StudioError, 'changed'):
            self.studio.preview_robot(asset.asset_id)

    def test_rejects_missing_cyclic_escaping_and_unsupported_inputs(self):
        baseline = self.xml.read_text()
        cases = {
            'missing': '<mujoco><include file="missing.xml"/></mujoco>',
            'cycle': '<mujoco><include file="robot.xml"/></mujoco>',
            'escaping': '<mujoco><include file="../outside.xml"/></mujoco>',
            'absolute mesh': baseline.replace('<worldbody>', '<asset><mesh file="/tmp/out.obj"/></asset><worldbody>'),
            'missing texture': baseline.replace('<worldbody>', '<asset><texture name="t" type="2d" file="missing.png"/></asset><worldbody>'),
            'material': baseline.replace('<geom type="box"', '<geom material="missing" type="box"'),
            'slide': baseline.replace('<joint name="shoulder"/>', '<joint name="shoulder" type="slide"/>'),
            'ball': baseline.replace('<joint name="shoulder"/>', '<joint name="shoulder" type="ball"/>'),
            'unbounded': baseline.replace('limited="true"', 'limited="false"'),
            'unnamed hinge': baseline.replace('name="shoulder"', ''),
            'extra robot': baseline.replace('</worldbody>', '<body name="other"><freejoint/><geom type="sphere" size=".1"/></body></worldbody>'),
        }
        for reason, xml in cases.items():
            with self.subTest(reason=reason):
                self.xml.write_text(xml)
                with self.assertRaises(StudioError):
                    self.studio.import_robot(self.xml)
        self.assertEqual(self.studio.list_robots(), ())

    def test_import_requires_valid_initial_pose_within_compiled_limits(self):
        self.xml.write_text(self.xml.read_text().replace('range="-90 45"', 'range="10 45"'))
        with self.assertRaisesRegex(StudioError, 'default pose'):
            self.studio.import_robot(self.xml)

    def test_robot_and_motion_changes_preserve_other_input_across_revisions(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest('NumPy unavailable for combined motion selection')
        models = self.root / 'models'
        models.mkdir()
        (models / 'SMPLX_NEUTRAL.pkl').write_bytes(b'test model provenance only')
        studio = Studio(self.root / 'state', robot_python=PYTHON, smplx_model_dir=models)
        motion = self.root / 'motion.npz'
        np.savez(motion, poses=np.zeros((2, 66)), trans=np.zeros((2, 3)),
                 betas=np.zeros(10), gender='neutral', mocap_frame_rate=30., samp_output_up='y')
        human = studio.import_motion(motion)
        robot = studio.import_robot(self.xml)
        draft = studio.create_draft('Combined inputs')
        first = studio.save_robot_pose(draft.run_id, robot.asset_id, name='Reference',
                                        qpos=list(robot.default_qpos), torso_body='torso')
        second = studio.select_motion(draft.run_id, human.asset_id)
        self.assertEqual(second.revision_id, 'r0003')
        self.assertEqual(second.robot_pose_id, first.robot_pose_id)
        qpos = list(robot.default_qpos)
        qpos[7] = .5
        third = studio.save_robot_pose(draft.run_id, robot.asset_id, name='Changed',
                                       qpos=qpos, torso_body='pelvis')
        self.assertEqual(third.revision_id, 'r0004')
        self.assertEqual(third.motion_asset_id, human.asset_id)
        self.assertEqual(studio.select_motion(draft.run_id, human.asset_id).revision_id, 'r0004')
        reopened = Studio(self.root / 'state', robot_python=PYTHON, smplx_model_dir=models)
        self.assertEqual(reopened.get_run(draft.run_id), third)
        preview = studio.preview_robot(robot.asset_id, qpos)
        self.assertAlmostEqual(preview['transforms'][1]['rotation'][0], .8775825618903728, places=12)
        self.assertAlmostEqual(preview['transforms'][1]['rotation'][1], -.479425538604203, places=12)
