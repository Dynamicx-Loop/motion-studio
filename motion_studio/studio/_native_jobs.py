"""Process-group lifecycle and atomic acceptance for Studio native jobs."""
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import threading
import time
import uuid

from ._contracts import StudioError
from ._history import digest, confined_file
from ._execution import now
from motion_studio.integrations.umr_stages import STAGES, canonical_hash, native_environment


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
    command = studio.native_adapter.command(request)
    env = {**native_environment(), 'PYTHONUNBUFFERED': '1', 'PYTHONDONTWRITEBYTECODE': '1',
           'HUMANOID_BATCH_PROGRESS': '1', 'XDG_CACHE_HOME': str(attempt / 'cache'),
           'TMPDIR': str(attempt / 'tmp'), 'OMP_NUM_THREADS': '4', 'MKL_NUM_THREADS': '4'}
    (attempt / 'tmp').mkdir()
    (attempt / 'cache').mkdir()
    (attempt / 'command.json').write_text(json.dumps({'argv': command, 'removed_environment': ['PYTHONPATH', 'PYTHONHOME'], 'overrides': {k: env[k] for k in (
        'PYTHONUNBUFFERED', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE', 'HUMANOID_BATCH_PROGRESS', 'XDG_CACHE_HOME', 'TMPDIR', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')}}))
    lines = queue.Queue()
    with (attempt / 'native.log').open('wb') as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        studio._update_job(job_id, pid=process.pid, status='running', message=f'{stage}: native setup')
        def read():
            for line in iter(process.stdout.readline, b''):
                log.write(line); log.flush(); lines.put(line)
            process.stdout.close()
        reader = threading.Thread(target=read, daemon=True); reader.start()
        started = time.monotonic()
        while process.poll() is None or reader.is_alive() or not lines.empty():
            job = studio.get_job(job_id)
            if job['status'] == 'cancelling':
                _stop(process); reader.join(timeout=5)
                raise StudioError('cancelled', 'Native process group stopped', 409)
            if studio.get_run(job['run_id']).revision_id != job['revision_id']:
                _stop(process); reader.join(timeout=5)
                raise StudioError('stale_revision', 'Inputs changed; this attempt was not published', 409)
            try:
                line = lines.get(timeout=.1).decode('utf-8', errors='replace').strip()
            except queue.Empty:
                continue
            progress = dict(job['progress'])
            epoch = re.search(r'\[TrainResidual\] epoch=(\d+)', line)
            frames = re.match(r'__HUMANOID_BATCH_PROGRESS__ (\d+) (\d+)', line)
            if epoch:
                progress.update(epoch=int(epoch[1]), epochs=job['plan']['settings']['epochs'])
            if frames:
                progress.update(frames_done=int(frames[1]), frames_total=int(frames[2]))
            progress.update(elapsed_seconds=round(time.monotonic()-started, 2), last_line=line[-2000:])
            studio._update_job(job_id, progress=progress, message=f'{stage}: native work')
        code = process.wait()
        if code:
            raise StudioError('native_failed', f'{stage} exited {code}; inspect its retained native.log', 409)
    return command


def _accept(studio, job_id, stage, attempt, request, command):
    job = studio.get_job(job_id)
    plan = studio.plan_execution(job['run_id'], through=stage)
    if (job['status'] == 'cancelling' or plan['revision_id'] != job['revision_id']
            or plan['fingerprints'].get(stage) != job['plan']['fingerprints'][stage]):
        raise StudioError('stale_result', 'Cancelled or changed-input result was not published', 409)
    report = json.loads((attempt / 'validation.json').read_text())
    if report.get('valid') is not True or report.get('stage') != stage or not report.get('artifacts'):
        raise StudioError('invalid_result', 'Worker did not validate required stage outputs', 409)
    required = {'sampling': 'dataset.npz', 'training': 'train/correspondence_slots_final.npz',
                'binding': 'bindings.json', 'retargeting': 'motion.npz'}[stage]
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
        if current['status'] == 'cancelling' or revision != job['revision_id']:
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


def execute_job(studio, job_id):
    job = studio.get_job(job_id)
    try:
        for stage in job['plan']['stages']:
            if studio.get_job(job_id)['status'] == 'cancelling':
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
            studio._update_job(job_id, stage=stage, attempts=job['attempts'], progress={}, message=f'{stage}: starting')
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
        studio._update_job(job_id, status=status, finished_at=now(), message=str(error),
                           error_code=getattr(error, 'code', 'stage_failed'))
