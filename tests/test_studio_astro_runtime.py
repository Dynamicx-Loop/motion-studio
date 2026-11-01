"""Bundled Astro public import/HTTP flow and native source representation parity."""
CHECK_TIER = 'robot-static'
CHECK_MODULES = ('numpy', 'mujoco')

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from motion_studio.integrations.menagerie_assets import ASTRO_ROOT, SOURCE_ENTRY
from motion_studio.studio import Studio
from test_studio_http import serving, request
from test_studio_robots import PYTHON


@unittest.skipUnless(PYTHON.is_file(), 'Existing independent robot runtime unavailable')
class AstroBuiltinRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # An absent external checkout must not block the bundled robot.
        self.studio = Studio(Path(self.tmp.name) / 'state', robot_python=PYTHON,
                             native_adapter=SimpleNamespace(checkout=Path(self.tmp.name) / 'no-UMR'))

    def test_builtin_is_available_without_external_source_and_preserves_immutable_pose_flow(self):
        catalog = self.studio.asset_catalog()['robots']
        self.assertTrue(next(item for item in catalog if item['id'] == 'astro')['available'])
        self.assertFalse(any(item['available'] for item in catalog if item['id'] != 'astro'))
        with serving(self.studio) as server:
            status, _, body = request(server, 'POST', '/api/catalog/robots', '{"id":"astro"}',
                                      {'Content-Type': 'application/json'})
            self.assertEqual(status, 201, body)
            result = json.loads(body)
            self.assertEqual(request(server, 'GET', '/thumbnails/astro.png')[0], 200)
            status, _, license_text = request(server, 'GET', '/licenses/astro-p2.txt')
            self.assertEqual(status, 200)
            self.assertEqual(license_text, (ASTRO_ROOT / 'LICENSE').read_bytes())
        asset, pose = result['asset'], result['pose']
        self.assertEqual((len(asset['joints']), len(pose['qpos'])), (29, 36))
        self.assertEqual((asset['root_body'], pose['torso_body']), ('pelvis', 'waist_roll_link'))
        self.assertEqual(self.studio.list_runs(), ())
        self.assertEqual(self.studio.add_builtin_robot('astro')['asset']['asset_id'], asset['asset_id'])
        draft = self.studio.create_draft('Bundled Astro')
        selected = self.studio.save_robot_pose(draft.run_id, asset['asset_id'], name=pose['name'],
            qpos=pose['qpos'], torso_body=pose['torso_body'])
        self.assertEqual(selected.revision_id, 'r0002')
        self.assertEqual(self.studio.get_run(draft.run_id, 'r0001').robot_asset_id, None)
        self.assertEqual(len(self.studio.preview_robot(asset['asset_id'], pose['qpos'])['transforms']), 89)
        geometry = json.loads(self.studio.robot_file(asset['asset_id'], 'geometry.json').read_text())
        self.assertEqual(sum(geom['group'] == 1 for geom in geometry['geometries']), 37)
        self.assertEqual(sum(geom['group'] == 3 for geom in geometry['geometries']), 52)
        for name in ('astro_p2.xml', 'foot_collisions.xml', 'neck_handle_collisions.xml', 'LICENSE', 'manifest.json'):
            preserved = self.studio.robot_file(asset['asset_id'], 'source/provenance/menagerie_x/' + name)
            self.assertEqual(preserved.read_bytes(), (ASTRO_ROOT / name).read_bytes())

    def test_compiled_models_and_tpose_frames_match_unchanged_source(self):
        import mujoco
        import numpy as np
        result = self.studio.add_builtin_robot('astro')
        asset, pose = result['asset'], result['pose']
        original = mujoco.MjModel.from_xml_path(str(ASTRO_ROOT / SOURCE_ENTRY))
        managed = mujoco.MjModel.from_xml_path(str(self.studio.robot_file(asset['asset_id'], 'source/__studio_model.xml')))
        self.assertEqual((managed.nq, managed.nv, managed.nbody, managed.ngeom), (36, 35, 40, 89))
        self.assertEqual(int(np.count_nonzero(managed.geom_type == mujoco.mjtGeom.mjGEOM_MESH)), 37)
        self.assertEqual(int(np.count_nonzero(managed.geom_contype | managed.geom_conaffinity)), 52)
        self.assertEqual([original.joint(i).name for i in range(original.njnt)],
                         [managed.joint(i).name for i in range(managed.njnt)])
        self.assertEqual([original.body(i).name for i in range(original.nbody)],
                         [managed.body(i).name for i in range(managed.nbody)])
        for field in ('qpos0', 'body_mass', 'body_inertia', 'body_pos', 'body_quat', 'body_ipos', 'body_iquat',
                      'body_parentid', 'jnt_range', 'jnt_axis', 'jnt_bodyid', 'jnt_qposadr',
                      'geom_pos', 'geom_quat', 'geom_size', 'geom_bodyid', 'geom_contype', 'geom_conaffinity'):
            with self.subTest(field=field):
                np.testing.assert_allclose(getattr(original, field), getattr(managed, field), atol=1e-12, rtol=0)
        source_state, managed_state = mujoco.MjData(original), mujoco.MjData(managed)
        source_state.qpos[:] = managed_state.qpos[:] = pose['qpos']
        mujoco.mj_forward(original, source_state)
        mujoco.mj_forward(managed, managed_state)
        for field in ('xpos', 'xmat', 'geom_xpos', 'geom_xmat'):
            np.testing.assert_allclose(getattr(source_state, field), getattr(managed_state, field), atol=1e-12, rtol=0)
        print(f'Astro representation parity in MuJoCo {mujoco.__version__}: 29 hinges, 37 visual meshes, 52 collision geoms')
