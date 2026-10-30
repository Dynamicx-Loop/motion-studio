"""Recovery of saved ownership across execution environments at Studio's seam."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from motion_studio.studio import Studio, StudioError
from motion_studio.studio._process_guard import process_identity


class OwnerScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / 'state'
        self.studio = Studio(self.state)
        self.run = self.studio.create_draft('Saved foreign owner')
        self.sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
        self.addCleanup(self.stop_sentinel)

    def stop_sentinel(self):
        if self.sentinel.poll() is None:
            self.sentinel.terminate()
        self.sentinel.wait(timeout=5)

    def saved_job(self, scope):
        # Fixture models a persisted job owned by a service invisible here. Its
        # worker PID happens to collide with an unrelated process in this scope.
        job = {'job_id': 'foreign-fixture', 'run_id': self.run.run_id,
               'revision_id': self.run.revision_id, 'status': 'running',
               'stage': 'training', 'progress': {}, 'message': 'Native work',
               'owner_pid': 2147483647, 'owner_identity': 'foreign-birth',
               'pid': self.sentinel.pid, 'process_identity': process_identity(self.sentinel.pid),
               'attempts': {'training': 'attempt-fixture'},
               'attempt_statuses': {'training': 'running'}, 'plan': {}}
        if scope is not None:
            job['owner_scope'] = scope
        with sqlite3.connect(self.state / 'studio.sqlite3') as db:
            db.execute('INSERT INTO jobs VALUES (?, ?)', (job['job_id'], json.dumps(job)))
        return job

    def test_foreign_namespace_owner_stays_active_and_never_signals_local_pid(self):
        job = self.saved_job({'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                              'pid_namespace': 'pid:[foreign-fixture]'})
        reopened = Studio(self.state)
        observed = reopened.list_jobs()[0]
        self.assertEqual(observed['status'], 'running')
        self.assertEqual(observed['attempt_statuses']['training'], 'running')
        self.assertIn('visibility', observed['recovery_notice'])
        self.assertIsNone(self.sentinel.poll(), 'foreign stored PID must never signal a local process')
        with self.assertRaises(StudioError) as failure:
            reopened.start_execution(self.run.run_id)
        self.assertEqual(failure.exception.code, 'job_active')
        self.assertEqual(reopened.get_job(job['job_id'])['status'], 'running')

    def test_prior_boot_owner_is_interrupted_without_signalling_reused_worker_pid(self):
        self.saved_job({'boot_id': 'a-previous-boot',
                        'pid_namespace': os.readlink('/proc/self/ns/pid')})
        observed = Studio(self.state).list_jobs()[0]
        self.assertEqual(observed['status'], 'interrupted')
        self.assertEqual(observed['attempt_statuses']['training'], 'interrupted')
        self.assertEqual(observed['error_code'], 'service_interrupted')
        self.assertIsNone(self.sentinel.poll(), 'prior-boot worker PID cannot identify a current process')
        self.assertEqual(len(Studio(self.state).list_jobs()), 1, 'recovery must not automatically retry')

    def test_legacy_unobservable_owner_remains_busy_without_a_namespace_proof(self):
        self.saved_job(None)
        reopened = Studio(self.state)
        self.assertEqual(reopened.list_jobs()[0]['status'], 'running')
        self.assertIsNone(self.sentinel.poll())
        with self.assertRaises(StudioError) as failure:
            reopened.start_execution(self.run.run_id)
        self.assertEqual(failure.exception.code, 'job_active')
