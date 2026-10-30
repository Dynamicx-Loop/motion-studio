"""Robot HTTP slice uses the same operations as the local editor."""
import json
from pathlib import Path
import tempfile
import unittest

from motion_studio.studio import Studio
from test_studio_http import request, serving
from test_studio_robots import PYTHON


@unittest.skipUnless(PYTHON.is_file(), 'pinned independent MuJoCo runtime unavailable')
class RobotHTTPTests(unittest.TestCase):
    def test_import_preview_save_and_reload_pose_through_http(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xml = root / 'robot.xml'
            xml.write_text('<mujoco><worldbody><body name="pelvis"><freejoint/>'
                '<geom type="box" size=".1 .1 .1"/><body name="torso"><joint name="arm" range="-90 90"/>'
                '<geom type="sphere" size=".1"/></body></body></worldbody></mujoco>')
            studio = Studio(root / 'state', robot_python=PYTHON)
            with serving(studio) as server:
                headers = {'Content-Type': 'application/json'}
                status, _, body = request(server, 'POST', '/api/robots',
                    json.dumps(dict(source_path=str(xml), derive_free_root=False)), headers)
                self.assertEqual(status, 201, body)
                asset = json.loads(body)
                asset_id = asset['asset_id']
                self.assertEqual(request(server, 'GET', f'/api/robots/{asset_id}/geometry')[0], 200)
                self.assertEqual(request(server, 'GET', '/robot.js')[0], 200)
                self.assertEqual(request(server, 'GET', '/vendor/three.module.js')[0], 200)
                draft = studio.create_draft('HTTP pose')
                status, _, body = request(server, 'POST', f'/api/runs/{draft.run_id}/robot-pose',
                    json.dumps(dict(asset_id=asset_id, name='T-pose', qpos=asset['default_qpos'], torso_body='torso')), headers)
                self.assertEqual(status, 200, body)
                self.assertEqual(json.loads(body)['revision_id'], 'r0002')
                status, _, body = request(server, 'GET', f'/api/robots/{asset_id}/poses')
                self.assertEqual(json.loads(body)[0]['name'], 'T-pose')
                status, _, body = request(server, 'POST', f'/api/robots/{asset_id}/preview',
                    json.dumps({'qpos': asset['default_qpos']}), headers)
                self.assertEqual(status, 200, body)
                self.assertEqual(len(json.loads(body)['transforms']), 2)
                status, _, body = request(server, 'GET', '/api/state')
                self.assertEqual(len(json.loads(body)['robots']), 1)
