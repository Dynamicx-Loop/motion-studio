"""Persistent lifecycle at Studio's public run/job seam with real subprocesses."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import unittest

from motion_studio.studio import Studio, StudioError
import test_studio_execution as fixtures


class RevisionTests(unittest.TestCase):
    setUp = fixtures.ProcessJobsTests.setUp
    wait = fixtures.ProcessJobsTests.wait

    def test_saved_revision_preserves_inputs_settings_and_selected_history(self):
        original = self.run
        changed = self.studio.save_execution_settings(original.run_id, {'epochs': 2})
        self.assertEqual(changed.robot_pose_id, original.robot_pose_id)
        self.assertEqual(changed.motion_asset_id, original.motion_asset_id)
        old = self.studio.get_run(original.run_id, original.revision_id)
        self.assertEqual(old.robot_pose_id, original.robot_pose_id)
        self.assertEqual(old.motion_asset_id, original.motion_asset_id)
        self.assertFalse(old.is_latest)
        self.assertEqual(self.studio.execution_settings(old.run_id, old.revision_id)['epochs'], 500)
        self.assertEqual(self.studio.execution_settings(changed.run_id, changed.revision_id)['epochs'], 2)
        revisions = self.studio.list_revisions(old.run_id)
        self.assertEqual([r.revision_id for r in revisions], ['r0001', 'r0002', 'r0003', 'r0004'])
        self.studio.select(old.run_id, old.revision_id)
        reopened = Studio(self.studio.roots.state, native_adapter=self.adapter)
        self.assertEqual(reopened.selected_revision_id(), old.revision_id)
        self.assertEqual(reopened.get_run(old.run_id).revision_id, changed.revision_id)
        with self.assertRaises(StudioError):
            self.studio.get_run(old.run_id, 'r9999')

    def test_revision_edit_exposes_stale_stages_but_retains_verified_old_result(self):
        done = self.wait(self.studio.start_execution(self.run.run_id, through='sampling'))
        self.assertEqual(done['status'], 'completed', done)
        old_revision = done['revision_id']
        old_receipt = self.studio.stage_receipt(self.run.run_id, old_revision, 'sampling')
        changed = self.studio.save_execution_settings(self.run.run_id, {'sampling_seed': 2})
        state = next(s for s in changed.stages if s.stage == 'sampling')
        self.assertEqual(state.status, 'stale')
        self.assertIn('revision', state.reason)
        self.assertEqual(self.studio.stage_receipt(self.run.run_id, old_revision, 'sampling'), old_receipt)
        old = self.studio.get_run(self.run.run_id, old_revision)
        self.assertEqual(next(s.status for s in old.stages if s.stage == 'sampling'), 'available')
        plan = self.studio.plan_execution(self.run.run_id, through='sampling')
        self.assertEqual(plan['stages'], ['sampling'])
        self.assertEqual(plan['reuse_policy'], 'verified-related-revisions')
        self.assertEqual(len(self.studio.list_jobs()), 1, 'edits must not queue computation')

    def test_settings_changes_reuse_only_unchanged_authenticated_prefix(self):
        done = self.wait(self.studio.start_execution(self.run.run_id, through='training'))
        self.assertEqual(done['status'], 'completed', done)
        original_revision = done['revision_id']
        original = self.studio.stage_artifact(self.run.run_id, original_revision, 'sampling', 'dataset.npz')
        changed = self.studio.save_execution_settings(self.run.run_id, {'epochs': 2})
        plan = self.studio.plan_execution(self.run.run_id, through='training')
        self.assertEqual(plan['completed'], ['sampling'])
        self.assertEqual(plan['stages'], ['training'])
        reused = self.studio.stage_artifact(self.run.run_id, changed.revision_id, 'sampling', 'dataset.npz')
        self.assertEqual(reused, original)
        self.assertEqual(next(s.status for s in changed.stages if s.stage == 'training'), 'stale')
        retrained = self.wait(self.studio.start_execution(self.run.run_id, through='training'))
        self.assertEqual(retrained['status'], 'completed', retrained)
        self.assertEqual(set(retrained['attempts']), {'training'})
        original.write_bytes(b'corrupted shared sampling')
        plan = self.studio.plan_execution(self.run.run_id, through='training')
        self.assertEqual(plan['completed'], [])
        self.assertEqual(plan['stages'], ['sampling', 'training'])

    def test_filter_edit_reuses_prefix_but_motion_edit_invalidates_every_stage(self):
        import numpy as np
        worker = self.root / 'external-fixture.py'
        worker.write_text(worker.read_text().replace(
            "name='train/correspondence_slots_final.npz' if r['stage']=='training' else 'dataset.npz'",
            "name={'sampling':'dataset.npz','training':'train/correspondence_slots_final.npz','binding':'bindings.json','retargeting':'motion.npz'}[r['stage']]"))
        done = self.wait(self.studio.start_execution(self.run.run_id))
        self.assertEqual(done['status'], 'completed', done)
        changed = self.studio.save_execution_settings(self.run.run_id, {'trajectory_filter': 'none'})
        plan = self.studio.plan_execution(self.run.run_id)
        self.assertEqual(plan['completed'], ['sampling', 'training', 'binding'])
        self.assertEqual(plan['stages'], ['retargeting'])
        source = self.root / 'different-clip.npz'
        np.savez(source, poses=np.zeros((3,66)), trans=np.ones((3,3)), betas=np.zeros(10),
                 gender='neutral', fps=30., output_up='z')
        motion = self.studio.import_motion(source)
        new_clip = self.studio.select_motion(self.run.run_id, motion.asset_id)
        self.assertEqual(new_clip.robot_pose_id, self.run.robot_pose_id)
        self.assertEqual(self.studio.execution_settings(new_clip.run_id)['trajectory_filter'], 'none')
        self.assertEqual(self.studio.plan_execution(new_clip.run_id)['completed'], [])
        self.assertTrue(all(s.status == 'stale' for s in new_clip.stages if s.stage in ('sampling','training','binding','retargeting')))
        self.assertEqual(self.studio.get_run(new_clip.run_id, changed.revision_id).motion_asset_id, self.run.motion_asset_id)

    def test_viewed_head_follows_saved_edit_but_history_selection_remains_fixed(self):
        self.studio.select(self.run.run_id)
        changed = self.studio.save_execution_settings(self.run.run_id, {'epochs': 2})
        self.assertEqual(self.studio.selected_revision_id(), changed.revision_id)
        self.studio.select(self.run.run_id, self.run.revision_id)
        self.studio.save_execution_settings(self.run.run_id, {'epochs': 3})
        self.assertEqual(self.studio.selected_revision_id(), self.run.revision_id)


class RecoveryTests(unittest.TestCase):
    setUp = fixtures.ProcessJobsTests.setUp
    wait = fixtures.ProcessJobsTests.wait

    def test_service_crash_preserves_prerequisite_kills_orphan_and_requires_explicit_retry(self):
        import json
        import os
        import subprocess
        import sys
        import time
        sampling = self.wait(self.studio.start_execution(self.run.run_id, through='sampling'))
        self.assertEqual(sampling['status'], 'completed', sampling)
        receipt = self.studio.stage_receipt(self.run.run_id, self.run.revision_id, 'sampling')
        worker = self.root / 'external-fixture.py'
        worker.write_text(worker.read_text().replace('time.sleep(.15)', 'time.sleep(60)'))
        service = self.root / 'service.py'
        service.write_text("""import json,sys,time
from pathlib import Path
from motion_studio.studio import Studio
from motion_studio.integrations.umr_stages import NativeStages
class Adapter(NativeStages):
 def readiness(self): return {'ready':True,'identity':{'fixture':'external-runtime-v1'},'message':'fixture runtime'}
 def command(self, request): return [sys.executable,'-B','-u',sys.argv[3],str(request)]
s=Studio(Path(sys.argv[1]),native_adapter=Adapter())
j=s.start_execution(sys.argv[2],through='training')
print(j['job_id'],flush=True)
while True: time.sleep(1)
""")
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        process = subprocess.Popen([sys.executable, '-B', str(service), str(self.studio.roots.state),
                                    self.run.run_id, str(worker)], stdout=subprocess.PIPE, text=True, env=env)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        job_id = process.stdout.readline().strip()
        deadline = time.monotonic() + 5
        while not self.studio.get_job(job_id)['progress'] and time.monotonic() < deadline:
            time.sleep(.02)
        running = self.studio.get_job(job_id)
        self.assertEqual(running['status'], 'running', running)
        process.kill(); process.wait(); process.stdout.close()
        reopened = Studio(self.studio.roots.state, native_adapter=self.adapter)
        interrupted = reopened.get_job(job_id)
        self.assertEqual(interrupted['status'], 'interrupted', interrupted)
        self.assertEqual(interrupted['attempt_statuses']['training'], 'interrupted')
        self.assertEqual(reopened.stage_receipt(self.run.run_id, self.run.revision_id, 'sampling'), receipt)
        self.assertIn('retry', interrupted['message'].lower())
        self.assertTrue(reopened.job_file(job_id).is_file())
        self.assertEqual({j['job_id'] for j in reopened.list_jobs()}, {sampling['job_id'], job_id},
                         'reopening must not automatically retry')
        deadline = time.monotonic() + 5
        def alive(pid):
            try:
                return Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0] != 'Z'
            except FileNotFoundError:
                return False
        while alive(running['pid']) and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertFalse(alive(running['pid']), 'orphan process group survived service death')
        worker.write_text(worker.read_text().replace('time.sleep(60)', 'time.sleep(.15)'))
        self.studio = reopened
        done = self.wait(reopened.start_execution(self.run.run_id, through='training'))
        self.assertEqual(set(done['attempts']), {'training'})
        self.assertEqual(done['status'], 'completed', done)
        self.assertNotEqual(done['attempts'], interrupted['attempts'])

    def test_duplicate_requests_and_second_service_never_queue_or_mutate_settings(self):
        import json
        import os
        import subprocess
        import sys
        worker = self.root / 'external-fixture.py'
        worker.write_text(worker.read_text().replace('time.sleep(.15)', 'time.sleep(1)'))
        other = Studio(self.studio.roots.state, native_adapter=self.adapter)
        def launch(index):
            try:
                return (self.studio if index % 2 else other).start_execution(self.run.run_id, through='sampling')
            except StudioError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(launch, range(8)))
        jobs = [value for value in results if isinstance(value, dict)]
        self.assertEqual(len(jobs), 1, results)
        self.assertEqual([v for v in results if isinstance(v, str)], ['job_active'] * 7)
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        result = subprocess.run([sys.executable, '-B', '-c',
            "from pathlib import Path; from motion_studio.studio import Studio,StudioError; "
            "import sys; s=Studio(Path(sys.argv[1])); "
            "exec(\"try: s.start_execution(sys.argv[2],settings={'epochs':2})\\nexcept StudioError as e: print(e.code)\")",
            str(self.studio.roots.state), self.run.run_id], env=env, text=True, capture_output=True)
        self.assertEqual(result.stdout.strip(), 'job_active', result.stderr)
        self.assertEqual(self.studio.execution_settings(self.run.run_id)['epochs'], 500)
        viewing = self.studio.create_draft('Can view while computing')
        self.studio.select(viewing.run_id)
        self.assertEqual(self.studio.get_run(viewing.run_id).revision_id, 'r0001')
        self.assertEqual(len(self.studio.list_jobs()), 1)
        self.assertEqual(self.wait(jobs[0])['status'], 'completed')

    def test_cancel_escalates_to_descendant_group_and_retains_log_without_receipt(self):
        import os
        import time
        worker = self.root / 'external-fixture.py'
        worker.write_text("""import subprocess,sys,time
p=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print("descendant-ready",flush=True);time.sleep(60)'])
print('descendant-pid='+str(p.pid),flush=True)
time.sleep(60)
""")
        job = self.studio.start_execution(self.run.run_id, through='sampling')
        deadline = time.monotonic() + 5
        text = ''
        while time.monotonic() < deadline:
            try:
                text = self.studio.job_file(job['job_id']).read_text()
            except StudioError:
                pass
            if 'descendant-ready' in text:
                break
            time.sleep(.02)
        self.assertIn('descendant-ready', text)
        self.studio.cancel_job(job['job_id'])
        done = self.wait(job)
        self.assertEqual(done['status'], 'cancelled', done)
        self.assertEqual(done['attempt_statuses']['sampling'], 'cancelled')
        pid = int(text.split('descendant-pid=')[1].splitlines()[0])
        try:
            state = Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0]
            self.assertEqual(state, 'Z', 'descendant process survived cancel escalation')
        except FileNotFoundError:
            pass
        self.assertIn('descendant-ready', self.studio.job_file(job['job_id']).read_text())
        with self.assertRaises(StudioError):
            self.studio.stage_receipt(self.run.run_id, self.run.revision_id, 'sampling')

    def test_cancel_after_worker_writes_outputs_never_publishes_late_completion(self):
        import time
        worker = self.root / 'external-fixture.py'
        worker.write_text(worker.read_text() + "\nprint('outputs-written',flush=True)\ntime.sleep(1)\n")
        job = self.studio.start_execution(self.run.run_id, through='sampling')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.studio.get_job(job['job_id'])['progress'].get('last_line') == 'outputs-written':
                break
            time.sleep(.02)
        self.assertEqual(self.studio.get_job(job['job_id'])['progress']['last_line'], 'outputs-written')
        self.studio.cancel_job(job['job_id'])
        done = self.wait(job)
        self.assertEqual(done['status'], 'cancelled', done)
        with self.assertRaises(StudioError):
            self.studio.stage_receipt(self.run.run_id, self.run.revision_id, 'sampling')
        self.assertEqual(self.studio.cancel_job(job['job_id']), done, 'terminal cancellation must be idempotent')

    def test_edit_while_running_rejects_stale_attempt_and_preserves_new_draft(self):
        import time
        worker = self.root / 'external-fixture.py'
        worker.write_text(worker.read_text().replace('time.sleep(.15)', 'time.sleep(1)'))
        job = self.studio.start_execution(self.run.run_id, through='sampling')
        deadline = time.monotonic() + 5
        while not self.studio.get_job(job['job_id'])['progress'] and time.monotonic() < deadline:
            time.sleep(.02)
        changed = self.studio.save_execution_settings(self.run.run_id, {'epochs': 2})
        done = self.wait(job)
        self.assertEqual(done['status'], 'failed', done)
        self.assertEqual(done['error_code'], 'stale_revision')
        self.assertEqual(self.studio.get_run(self.run.run_id), changed)
        for revision in (self.run.revision_id, changed.revision_id):
            with self.assertRaises(StudioError):
                self.studio.stage_receipt(self.run.run_id, revision, 'sampling')
        self.assertEqual(len(self.studio.list_jobs()), 1)

    def test_native_crash_and_incomplete_receipt_never_become_reusable(self):
        worker = self.root / 'external-fixture.py'
        original = worker.read_text()
        worker.write_text(original.replace('time.sleep(.15)', 'sys.exit(23)'))
        failed = self.wait(self.studio.start_execution(self.run.run_id, through='sampling'))
        self.assertEqual(failed['status'], 'failed', failed)
        self.assertEqual(failed['error_code'], 'native_failed')
        self.assertTrue(self.studio.job_file(failed['job_id']).read_text())
        self.assertEqual(self.studio.plan_execution(self.run.run_id, through='sampling')['completed'], [])
        worker.write_text(original)
        completed = self.wait(self.studio.start_execution(self.run.run_id, through='sampling'))
        self.assertEqual(completed['status'], 'completed', completed)
        artifact = self.studio.stage_artifact(self.run.run_id, self.run.revision_id, 'sampling', 'dataset.npz')
        (artifact.parent / 'receipt.json').write_text('{"stage":"sampling"}')
        self.assertEqual(self.studio.plan_execution(self.run.run_id, through='sampling')['completed'], [])
        with self.assertRaises(StudioError):
            self.studio.stage_receipt(self.run.run_id, self.run.revision_id, 'sampling')

    def test_crashed_process_leader_cannot_leave_descendants_or_hold_compute_slot(self):
        import os
        import signal
        import time
        worker = self.root / 'external-fixture.py'
        worker.write_text("""import subprocess,sys,time
p=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print("descendant-ready",flush=True);time.sleep(60)'])
print('descendant-pid='+str(p.pid),flush=True)
time.sleep(60)
""")
        job = self.studio.start_execution(self.run.run_id, through='sampling')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            current = self.studio.get_job(job['job_id'])
            if current['progress'].get('last_line') == 'descendant-ready':
                break
            time.sleep(.02)
        self.assertEqual(current['progress'].get('last_line'), 'descendant-ready')
        os.kill(current['pid'], signal.SIGKILL)
        done = self.wait(job)
        self.assertEqual(done['status'], 'failed', done)
        self.assertEqual(done['error_code'], 'native_failed')
        self.assertFalse(any(j['status'] in ('queued','running','cancelling') for j in self.studio.list_jobs()))
        pid = int(self.studio.job_file(job['job_id']).read_text().split('descendant-pid=')[1].splitlines()[0])
        try:
            self.assertEqual(Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0], 'Z')
        except FileNotFoundError:
            pass


class RevisionHTTPTests(unittest.TestCase):
    def test_revision_selection_and_settings_round_trip_without_moving_head(self):
        import json
        import tempfile
        import threading
        import urllib.request
        from motion_studio.studio.http import create_server
        with tempfile.TemporaryDirectory() as folder:
            studio = Studio(Path(folder))
            original = studio.create_draft('Immutable HTTP snapshots')
            changed = studio.save_execution_settings(original.run_id, {'epochs': 2})
            server = create_server(studio, port=0)
            self.addCleanup(server.server_close)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.shutdown)
            base = f'http://127.0.0.1:{server.server_port}'
            def request(path, value=None):
                req = urllib.request.Request(base+path, None if value is None else json.dumps(value).encode(),
                                             {'Content-Type':'application/json'})
                with urllib.request.urlopen(req) as response:
                    return json.load(response)
            selected = request('/api/selection', {'run_id':original.run_id, 'revision_id':original.revision_id})
            self.assertFalse(selected['is_latest'])
            state = request('/api/state')
            self.assertEqual(state['selected_run']['revision_id'], original.revision_id)
            self.assertEqual(state['runs'][0]['revision_id'], changed.revision_id)
            self.assertEqual([r['revision_id'] for r in state['revisions']], ['r0001','r0002'])
            prefix = f'/api/runs/{original.run_id}/revisions'
            self.assertEqual(len(request(prefix)), 2)
            self.assertEqual(request(prefix+'/r0001/settings')['epochs'], 500)
            self.assertEqual(request(prefix+'/r0002/settings')['epochs'], 2)
            self.assertEqual(request(prefix+'/r0001')['revision_id'], 'r0001')
