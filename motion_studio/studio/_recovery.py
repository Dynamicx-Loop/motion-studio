"""Service interruption detection and monotonic persisted job transitions."""
import json
import os
import signal

from ._process_guard import process_identity, process_scope

ACTIVE = ('queued', 'running', 'cancelling')
TERMINAL = ('completed', 'cancelled', 'failed', 'interrupted')


def recover_jobs(studio, db, timestamp):
    for row in db.execute('SELECT * FROM jobs').fetchall():
        job = json.loads(row['data'])
        if job['status'] not in ACTIVE:
            continue
        owner = job.get('owner_pid')
        scope, current_scope = job.get('owner_scope'), process_scope()
        same_scope = scope is not None and scope == current_scope
        prior_boot = (isinstance(scope, dict) and isinstance(current_scope, dict)
                      and bool(scope.get('boot_id'))
                      and scope['boot_id'] != current_scope['boot_id'])
        birth = job.get('owner_identity')
        alive = process_identity(owner) if owner else None
        # Legacy records can confirm a live owner, but cannot prove that an
        # invisible/reused PID belongs to a dead service in this namespace.
        if (same_scope or scope is None) and alive and (birth is None or alive == birth):
            if job.pop('recovery_notice', None):
                db.execute('UPDATE jobs SET data=? WHERE job_id=?', (json.dumps(job), job['job_id']))
            continue
        if not same_scope and not prior_boot:
            job['recovery_notice'] = ('Owner visibility is unknown from this execution environment; '
                                      'job remains active. Open its original service environment.')
            db.execute('UPDATE jobs SET data=? WHERE job_id=?', (json.dumps(job), job['job_id']))
            continue
        # A prior boot proves owner death, but its stored PID must never be
        # interpreted in this boot. Only a matching scope permits group signals.
        pid, worker_birth = job.get('pid'), job.get('process_identity')
        if same_scope and pid and worker_birth and process_identity(pid) == worker_birth:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        job.pop('recovery_notice', None)
        states = job.setdefault('attempt_statuses', {})
        for stage in job['attempts']:
            if states.get(stage) != 'completed':
                states[stage] = 'interrupted'
        job.update(status='interrupted', message='Service interrupted; retry explicitly with a fresh stage attempt',
                   error_code='service_interrupted', finished_at=timestamp)
        db.execute('UPDATE jobs SET data=? WHERE job_id=?', (json.dumps(job), job['job_id']))
