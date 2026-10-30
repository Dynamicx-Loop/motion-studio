"""Service interruption detection and monotonic persisted job transitions."""
import json
import os
import signal

from ._process_guard import process_identity

ACTIVE = ('queued', 'running', 'cancelling')
TERMINAL = ('completed', 'cancelled', 'failed', 'interrupted')


def recover_jobs(studio, db, timestamp):
    for row in db.execute('SELECT * FROM jobs').fetchall():
        job = json.loads(row['data'])
        if job['status'] not in ACTIVE:
            continue
        owner = job.get('owner_pid')
        # Legacy jobs lack a birth identity: accept a live PID conservatively,
        # but never signal its unverified process group on recovery.
        birth = job.get('owner_identity')
        alive = process_identity(owner) if owner else None
        if alive and (birth is None or alive == birth):
            continue
        pid, worker_birth = job.get('pid'), job.get('process_identity')
        if pid and worker_birth and process_identity(pid) == worker_birth:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        states = job.setdefault('attempt_statuses', {})
        for stage in job['attempts']:
            if states.get(stage) != 'completed':
                states[stage] = 'interrupted'
        job.update(status='interrupted', message='Service interrupted; retry explicitly with a fresh stage attempt',
                   error_code='service_interrupted', finished_at=timestamp)
        db.execute('UPDATE jobs SET data=? WHERE job_id=?', (json.dumps(job), job['job_id']))
