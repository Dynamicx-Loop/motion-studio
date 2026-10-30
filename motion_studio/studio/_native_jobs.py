"""Process-group lifecycle and atomic acceptance for Studio native jobs."""
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import threading
import time
import uuid

from ._contracts import StudioError
from ._history import digest, confined_file
from ._timestamps import now
from ._process_guard import process_identity
from motion_studio.integrations.umr_stages import STAGES, canonical_hash


def _stop(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    # The parent may exit before a descendant that ignores TERM. Kill any
    # remaining group members even when wait() already reaped the worker.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)



def _run(studio, job_id, stage, attempt, request):
    launch = studio.native_adapter.launch(request, attempt)
    command, env = launch['command'], launch['environment']
    (attempt / 'command.json').write_text(json.dumps(launch['provenance']))
    lines = queue.Queue()
    with (attempt / 'native.log').open('wb') as log:
        owner = studio.get_job(job_id)
        guarded = [sys.executable, '-B', str(Path(__file__).with_name('_process_guard.py')),
                   str(owner['owner_pid']), owner['owner_identity'], *command]
        process = subprocess.Popen(guarded, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        studio._update_job(job_id, pid=process.pid, process_identity=process_identity(process.pid), status='running', message=f'{stage}: native setup')
        def read():
            for line in iter(process.stdout.readline, b''):
                log.write(line); log.flush(); lines.put(line)
            process.stdout.close()
        reader = threading.Thread(target=read, daemon=True); reader.start()
        started = time.monotonic()
        while process.poll() is None or reader.is_alive() or not lines.empty():
            job = studio.get_job(job_id)
            if process.poll() is not None and reader.is_alive():
                # A crashed/exited leader must not leave descendants holding
                # stdout (and the compute slot) indefinitely.
                _stop(process)
                reader.join(timeout=5)
            if job['status'] != 'running':
                _stop(process); reader.join(timeout=5)
                raise StudioError('cancelled', 'Native process group stopped', 409)
            if not studio._revision_is_current(job['run_id'], job['revision_id']):
                _stop(process); reader.join(timeout=5)
                raise StudioError('stale_revision', 'Inputs changed; this attempt was not published', 409)
            try:
                line = lines.get(timeout=.1).decode('utf-8', errors='replace').strip()
            except queue.Empty:
                continue
            progress = dict(job['progress'])
            progress.update(studio.native_adapter.decode_progress(line, job['plan']['settings']))
            progress.update(elapsed_seconds=round(time.monotonic()-started, 2), last_line=line[-2000:])
            studio._update_job(job_id, progress=progress, message=f'{stage}: native work')
        code = process.wait()
        if code:
            raise StudioError('native_failed', f'{stage} exited {code}; inspect its retained native.log', 409)
    return command


def _accept(studio, job_id, stage, attempt, request, command):
    job = studio.get_job(job_id)
    plan = studio.plan_execution(job['run_id'], through=stage)
    if (job['status'] != 'running' or plan['revision_id'] != job['revision_id']
            or plan['fingerprints'].get(stage) != job['plan']['fingerprints'][stage]):
        raise StudioError('stale_result', 'Cancelled or changed-input result was not published', 409)
    report = json.loads((attempt / 'validation.json').read_text())
    if report.get('valid') is not True or report.get('stage') != stage or not report.get('artifacts'):
        raise StudioError('invalid_result', 'Worker did not validate required stage outputs', 409)
    for required in studio.native_adapter.required_artifacts(stage):
        if required not in report['artifacts']:
            raise StudioError('invalid_result', f'Missing required stage output: {required}', 409)
    # Native validators inspect arrays before publishing. The parent independently
    # checks confinement, nonempty output files and every exact published byte.
    artifacts = []
    for name in report['artifacts']:
        path = confined_file(attempt, name)
        if path.stat().st_size == 0:
            raise StudioError('invalid_result', 'Native output is empty', 409)
        artifacts.append(attempt.name + '/' + name)
    for path in sorted(attempt.rglob('*')):
        if path.is_file() and not any(p in ('cache', 'tmp') for p in path.relative_to(attempt).parts):
            if not path.resolve().is_relative_to(attempt):
                raise StudioError('invalid_result', 'Escaping native output', 409)
            name = str(path.relative_to(attempt.parent))
            if name not in artifacts:
                artifacts.append(name)
    files = {p: digest(confined_file(attempt.parent, p)) for p in artifacts}
    receipt = {'schema': 1, 'run_id': job['run_id'], 'revision_id': job['revision_id'], 'stage': stage,
               'job_id': job_id, 'attempt_id': attempt.name, 'fingerprint': job['plan']['fingerprints'][stage],
               'dependencies': request['dependencies'], 'inputs': request['inputs'], 'settings': request['settings'],
               'environment': job['plan']['readiness']['identity'], 'command': command,
               'artifacts': files, 'validation': report, 'completed_at': now()}
    receipt_path = attempt / 'receipt.json'
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))
    info = {'files': files, 'receipt_path': attempt.name + '/receipt.json', 'receipt_sha256': canonical_hash(receipt)}
    with studio._connection() as db:
        db.execute('BEGIN IMMEDIATE')
        current = json.loads(db.execute('SELECT data FROM jobs WHERE job_id=?', (job_id,)).fetchone()['data'])
        revision = db.execute('SELECT revision_id FROM runs WHERE run_id=?', (job['run_id'],)).fetchone()['revision_id']
        if current['status'] != 'running' or revision != job['revision_id']:
            receipt_path.unlink()
            raise StudioError('stale_result', 'Late result was not published', 409)
        # Check exact prerequisite receipt identities and every dependency byte
        # again immediately before publication; a semantic fingerprint alone
        # cannot detect changed completed outputs while this worker ran.
        for dependency, captured in request['dependencies'].items():
            current_dependency = studio._receipt(job['run_id'], job['revision_id'], dependency)
            if current_dependency is None or canonical_hash(current_dependency) != canonical_hash(captured):
                receipt_path.unlink()
                raise StudioError('stale_dependency', f'{dependency} changed during {stage}; result not published', 409)
        db.execute('INSERT OR REPLACE INTO stage_completions VALUES (?, ?, ?, ?)',
                   (job['run_id'], job['revision_id'], stage, json.dumps(info)))
        current.setdefault('attempt_statuses', {})[stage] = 'completed'
        db.execute('UPDATE jobs SET data=? WHERE job_id=?', (json.dumps(current), job_id))


def execute_job(studio, job_id):
    job = studio.get_job(job_id)
    try:
        for stage in job['plan']['stages']:
            if studio.get_job(job_id)['status'] not in ('queued', 'running'):
                raise StudioError('cancelled', 'Job cancelled before native launch', 409)
            run = studio.get_run(job['run_id'])
            if run.revision_id != job['revision_id']:
                raise StudioError('stale_revision', 'Inputs changed before launch', 409)
            inputs = studio.native_adapter.capture(studio, run)
            dependencies = {}
            for dependency in STAGES[:STAGES.index(stage)]:
                receipt = studio._receipt(job['run_id'], job['revision_id'], dependency)
                if not receipt or receipt['fingerprint'] != job['plan']['fingerprints'][dependency]:
                    raise StudioError('stale_dependency', f'{dependency} receipt is missing or changed', 409)
                dependencies[dependency] = receipt
            attempt = studio.roots.runs / job['run_id'] / job['revision_id'] / stage / ('attempt-' + uuid.uuid4().hex)
            attempt.mkdir(parents=True)
            job['attempts'][stage] = attempt.name
            states = studio.get_job(job_id).get('attempt_statuses', {})
            states[stage] = 'running'
            studio._update_job(job_id, stage=stage, attempts=job['attempts'], attempt_statuses=states, progress={}, message=f'{stage}: starting')
            request = {'run_id': job['run_id'], 'revision_id': job['revision_id'], 'job_id': job_id,
                       'stage': stage, 'attempt_dir': str(attempt), 'inputs': inputs,
                       'settings': job['plan']['settings'], 'dependencies': dependencies}
            request_file = attempt / 'request.json'
            request_file.write_text(json.dumps(request, allow_nan=False))
            command = _run(studio, job_id, stage, attempt, request_file)
            # Closure/model checks after work protect against input edits mid-job.
            if studio.native_adapter.capture(studio, run) != inputs:
                raise StudioError('changed_input', 'Managed inputs changed during native work', 409)
            _accept(studio, job_id, stage, attempt, request, command)
        studio._update_job(job_id, status='completed', finished_at=now(), message='All requested outputs validated')
    except Exception as error:
        status = 'cancelled' if isinstance(error, StudioError) and error.code == 'cancelled' else 'failed'
        current = studio.get_job(job_id)
        if current['status'] == 'cancelling':
            status = 'cancelled'
        states = current.get('attempt_statuses', {})
        if current['stage'] and states.get(current['stage']) != 'completed':
            states[current['stage']] = status
        studio._update_job(job_id, status=status, attempt_statuses=states, finished_at=now(), message=str(error),
                           error_code=getattr(error, 'code', 'stage_failed'))
