"""Execution behavior at the approved Studio and owned adapter seams."""
from pathlib import Path
import tempfile
import unittest

from motion_studio.studio import Studio, StudioError
from motion_studio.integrations.umr_stages import ExecutionSettings


class ExecutionTests(unittest.TestCase):
    def test_settings_reject_unknown_controls_and_translate_no_filter(self):
        settings = ExecutionSettings.from_dict({'sampling_seed': 17, 'epochs': 2, 'trajectory_filter': 'none'})
        self.assertEqual(settings.native_filter, 'off')
        for value in ({'epochs': 0}, {'epochs': True}, {'extra_args': {}}, {'sampling_seed': -1}, {'trajectory_filter': 'off'}):
            with self.subTest(value=value), self.assertRaises(StudioError):
                ExecutionSettings.from_dict(value)

    def test_empty_draft_plan_explains_missing_inputs_without_launching(self):
        with tempfile.TemporaryDirectory() as folder:
            studio = Studio(Path(folder))
            run = studio.create_draft('Native test')
            plan = studio.plan_execution(run.run_id, through='binding')
            self.assertFalse(plan['ready'])
            self.assertEqual(plan['missing_inputs'], ['robot_pose', 'motion'])
            self.assertEqual(plan['stages'], ['sampling', 'training', 'binding'])
            with self.assertRaises(StudioError) as error:
                studio.start_execution(run.run_id, through='binding')
            self.assertEqual(error.exception.code, 'not_ready')
            self.assertEqual(studio.list_jobs(), ())


if __name__ == '__main__':
    unittest.main()


class ProcessJobsTests(unittest.TestCase):
    def setUp(self):
        import json
        import sys
        from motion_studio.integrations.umr_stages import NativeStages
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        worker = self.root / 'external-fixture.py'
        worker.write_text('''import json,sys,time
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text()); p=Path(r['attempt_dir'])
print('[TrainResidual] epoch=00001 loss=0.25',flush=True)
time.sleep(.15)
(p/'dataset.npz').write_bytes(b'fixture external dataset')
(p/'validation.json').write_text(json.dumps({'stage':r['stage'],'valid':True,'artifacts':['dataset.npz']}))
''')
        class ExternalFixture(NativeStages):
            def readiness(self):
                return {'ready': True, 'identity': {'fixture': 'external-runtime-v1'}, 'message': 'fixture runtime'}
            def command(self, request):
                return [sys.executable, '-B', '-u', str(worker), str(request)]
        self.adapter = ExternalFixture()
        python = Path('/data/workspace/motion_studio/externals/UMR/.venv/bin/python')
        if not python.is_file():
            self.skipTest('Independent MuJoCo runtime unavailable for managed input fixture')
        models = self.root / 'models'; models.mkdir()
        (models / 'SMPLX_NEUTRAL.pkl').write_bytes(b'fixture weights not unpickled')
        self.studio = Studio(self.root / 'state', robot_python=python,
                             smplx_model_dir=models, native_adapter=self.adapter)
        xml = self.root / 'robot.xml'
        xml.write_text('<mujoco><worldbody><body name="root"><freejoint/>'
            '<geom type="box" size=".1 .1 .1"/><body name="torso"><joint name="j" range="-30 30"/>'
            '<geom type="sphere" size=".1"/></body></body></worldbody></mujoco>')
        robot = self.studio.import_robot(xml)
        run = self.studio.create_draft('Subprocess fixture')
        run = self.studio.save_robot_pose(run.run_id, robot.asset_id, name='Reference',
                                         qpos=robot.default_qpos, torso_body='torso')
        import numpy as np
        source = self.root / 'source.npz'
        np.savez(source, poses=np.zeros((3,66)), trans=np.zeros((3,3)), betas=np.zeros(10),
                 gender='neutral', fps=30., output_up='z')
        motion = self.studio.import_motion(source)
        self.run = self.studio.select_motion(run.run_id, motion.asset_id)

    def wait(self, job):
        import time
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            current = self.studio.get_job(job['job_id'])
            if current['status'] not in ('queued', 'running', 'cancelling'):
                return current
            time.sleep(.02)
        self.fail('job did not finish')

    def test_subprocess_publishes_receipt_and_reuses_only_unchanged_bytes(self):
        plan = self.studio.plan_execution(self.run.run_id, through='sampling')
        self.assertTrue(plan['ready'])
        job = self.studio.start_execution(self.run.run_id, through='sampling')
        with self.assertRaises(StudioError) as error:
            self.studio.start_execution(self.run.run_id, through='sampling')
        self.assertEqual(error.exception.code, 'job_active')
        done = self.wait(job)
        self.assertEqual(done['status'], 'completed', done)
        self.assertEqual(done['progress']['epoch'], 1)
        self.assertTrue(self.studio.job_file(job['job_id']).read_text().startswith('[TrainResidual]'))
        complete = self.studio.plan_execution(self.run.run_id, through='sampling')
        self.assertEqual(complete['stages'], [])
        path = self.studio.stage_artifact(self.run.run_id, complete['revision_id'], 'sampling', 'dataset.npz')
        self.assertEqual(path.read_bytes(), b'fixture external dataset')
        path.write_bytes(b'changed')
        self.assertEqual(self.studio.plan_execution(self.run.run_id, through='sampling')['stages'], ['sampling'])
        with self.assertRaises(StudioError):
            self.studio.stage_artifact(self.run.run_id, complete['revision_id'], 'sampling', 'dataset.npz')

    def test_cancel_retains_partial_log_and_retry_allocates_fresh_attempt(self):
        worker = self.root / 'external-fixture.py'
        worker.write_text(worker.read_text().replace('time.sleep(.15)', 'time.sleep(3)'))
        job = self.studio.start_execution(self.run.run_id, through='sampling')
        import time
        deadline = time.monotonic()+3
        while not self.studio.get_job(job['job_id'])['progress'] and time.monotonic()<deadline:
            time.sleep(.02)
        self.studio.cancel_job(job['job_id'])
        cancelled = self.wait(job)
        self.assertEqual(cancelled['status'], 'cancelled', cancelled)
        self.assertEqual(self.studio.plan_execution(self.run.run_id, through='sampling')['stages'], ['sampling'])
        self.assertTrue(self.studio.job_file(job['job_id']).is_file())
        worker.write_text(worker.read_text().replace('time.sleep(3)', 'time.sleep(.15)'))
        retry = self.wait(self.studio.start_execution(self.run.run_id, through='sampling'))
        self.assertEqual(retry['status'], 'completed')
        self.assertNotEqual(retry['attempts'], cancelled['attempts'])

    def test_changed_settings_make_revision_and_failed_output_has_no_receipt(self):
        changed = self.studio.save_execution_settings(self.run.run_id, {'epochs':2})
        self.assertNotEqual(changed.revision_id, self.run.revision_id)
        self.assertEqual(self.studio.execution_settings(self.run.run_id)['epochs'], 2)
        worker = self.root / 'external-fixture.py'
        worker.write_text(worker.read_text().replace("'artifacts':['dataset.npz']", "'artifacts':['missing.npz']"))
        job = self.wait(self.studio.start_execution(self.run.run_id, through='sampling'))
        self.assertEqual(job['status'], 'failed')
        self.assertEqual(job['error_code'], 'invalid_result')
        self.assertEqual(self.studio.plan_execution(self.run.run_id, through='sampling')['stages'], ['sampling'])

    def test_http_plan_launch_status_and_registered_log_use_same_owned_job(self):
        import json
        import threading
        import urllib.request
        from motion_studio.studio.http import create_server
        server = create_server(self.studio, port=0)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(server.shutdown)
        base = f'http://127.0.0.1:{server.server_port}'
        def post(path, data):
            request = urllib.request.Request(base+path, json.dumps(data).encode(), {'Content-Type':'application/json'})
            with urllib.request.urlopen(request) as response:
                return json.load(response)
        plan = post(f'/api/runs/{self.run.run_id}/plan', {'through':'sampling','settings':{}})
        self.assertEqual(plan['stages'], ['sampling'])
        job = post(f'/api/runs/{self.run.run_id}/execute', {'through':'sampling','settings':{}})
        done = self.wait(job)
        with urllib.request.urlopen(base+'/api/jobs/'+job['job_id']) as response:
            self.assertEqual(json.load(response)['status'], 'completed')
        with urllib.request.urlopen(base+'/api/jobs/'+job['job_id']+'/log/sampling') as response:
            self.assertIn(b'epoch=00001', response.read())
        with urllib.request.urlopen(base+f'/artifacts/{self.run.run_id}/{done["revision_id"]}/sampling/dataset.npz') as response:
            self.assertEqual(response.read(), b'fixture external dataset')
