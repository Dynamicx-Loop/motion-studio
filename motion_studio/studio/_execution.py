"""Persistent explicit native jobs; each attempt is fresh and receipts certify bytes."""
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import uuid

from ._contracts import StudioError
from ._recovery import recover_jobs, TERMINAL
from ._process_guard import process_identity
from ._history import digest, confined_file
from motion_studio.integrations.umr_stages import ExecutionSettings, STAGES, NativeStages, canonical_hash


def now():
    return datetime.now(timezone.utc).isoformat()


class _ExecutionOperations:
    def _init_execution(self, adapter=None):
        self.native_adapter = adapter or NativeStages(python=self.robot_python)
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, data TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS stage_completions ('
                       'run_id TEXT, revision_id TEXT, stage TEXT, receipt TEXT, '
                       'PRIMARY KEY(run_id, revision_id, stage))')
            db.execute('CREATE TABLE IF NOT EXISTS execution_settings ('
                       'run_id TEXT, revision_id TEXT, data TEXT, PRIMARY KEY(run_id, revision_id))')
            recover_jobs(self, db, now())

    def list_jobs(self):
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            recover_jobs(self, db, now())
            return tuple(json.loads(row['data']) for row in db.execute('SELECT data FROM jobs ORDER BY rowid'))

    def get_job(self, job_id):
        with self._connection() as db:
            row = db.execute('SELECT data FROM jobs WHERE job_id=?', (job_id,)).fetchone()
        if not row:
            raise StudioError('not_found', 'Job does not exist', 404)
        return json.loads(row['data'])

    def _update_job(self, job_id, **changes):
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM jobs WHERE job_id=?', (job_id,)).fetchone()
            job = json.loads(row['data'])
            if job['status'] in TERMINAL:
                return job
            if job['status'] == 'cancelling' and changes.get('status') == 'running':
                changes.pop('status')
            if job['status'] == 'cancelling' and changes.get('status') == 'completed':
                changes.update(status='cancelled', message='Stopped; completed stage artifacts retained')
            job.update(changes)
            db.execute('UPDATE jobs SET data=? WHERE job_id=?', (json.dumps(job), job_id))
        return job

    def execution_settings(self, run_id, revision_id=None):
        run = self.get_run(run_id, revision_id)
        with self._connection() as db:
            row = db.execute('SELECT data FROM execution_settings WHERE run_id=? AND revision_id<=? '
                             'ORDER BY revision_id DESC LIMIT 1', (run_id, run.revision_id)).fetchone()
        return json.loads(row['data']) if row else asdict(ExecutionSettings())

    def save_execution_settings(self, run_id, settings):
        controls = asdict(ExecutionSettings.from_dict(settings))
        run = self.get_run(run_id)
        if run.read_only:
            raise StudioError('read_only', 'Historical registrations are read-only', 409)
        if controls == self.execution_settings(run_id):
            return run
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT revision_id FROM runs WHERE run_id=?', (run_id,)).fetchone()
            parent = row['revision_id']
            revision = f"r{int(parent[1:])+1:04d}"
            folder = self.roots.runs / run_id / revision
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'settings.json').write_text(json.dumps(controls, sort_keys=True))
            db.execute('INSERT INTO execution_settings VALUES (?, ?, ?)', (run_id, revision, json.dumps(controls)))
            db.execute('UPDATE runs SET revision_id=? WHERE run_id=?', (revision, run_id))
        self._carry_settings_stages(run_id, parent, revision)
        return self.get_run(run_id)

    def _receipt(self, run_id, revision, stage):
        with self._connection() as db:
            row = db.execute('SELECT receipt FROM stage_completions WHERE run_id=? AND revision_id=? AND stage=?',
                             (run_id, revision, stage)).fetchone()
        if not row:
            return None
        try:
            info = json.loads(row['receipt'])
            if 'source_revision' in info:
                source = info['source_revision']
                if source >= revision:
                    return None
                receipt = self._receipt(run_id, source, stage)
                return receipt if receipt and canonical_hash(receipt) == info['receipt_sha256'] else None
            folder = self.roots.runs / run_id / revision / stage
            for name, sha in info['files'].items():
                if digest(confined_file(folder, name)) != sha:
                    return None
            receipt = json.loads(confined_file(folder, info['receipt_path']).read_text())
            if canonical_hash(receipt) != info['receipt_sha256']:
                return None
            if stage not in STAGES or (receipt['run_id'], receipt['revision_id'], receipt['stage']) != (run_id, revision, stage):
                return None
            expected = STAGES[:STAGES.index(stage)]
            if set(receipt['dependencies']) != set(expected):
                return None
            for dependency in expected:
                current = self._receipt(run_id, revision, dependency)
                if current is None or canonical_hash(current) != canonical_hash(receipt['dependencies'][dependency]):
                    return None
            return receipt
        except (OSError, ValueError, KeyError, TypeError, StudioError):
            return None

    def plan_execution(self, run_id, *, through='retargeting', settings=None):
        if through not in STAGES:
            raise StudioError('invalid_stage', 'Choose sampling, training, binding or retargeting')
        controls = ExecutionSettings.from_dict(self.execution_settings(run_id) if settings is None else settings)
        run = self.get_run(run_id)
        if run.read_only:
            raise StudioError('read_only', 'Historical registrations are read-only', 409)
        missing = []
        if not run.robot_asset_id or not run.robot_pose_id:
            missing.append('robot_pose')
        if not run.motion_asset_id:
            missing.append('motion')
        stages = list(STAGES[:STAGES.index(through)+1])
        plan = {'run_id': run_id, 'revision_id': run.revision_id, 'through': through,
                'settings': asdict(controls), 'stages': stages, 'missing_inputs': missing,
                'ready': False, 'completed': [], 'fingerprints': {},
                'reuse_policy': 'verified-related-revisions',
                'reuse_message': 'Only authenticated unchanged prefix stages from related revisions are reused; '
                'robot, pose and motion edits invalidate all stages. No cross-clip reuse.'}
        if missing:
            return plan
        captured = self.native_adapter.capture(self, run)
        readiness = self.native_adapter.readiness()
        plan['readiness'] = readiness
        if not readiness['ready']:
            return plan
        identity = {'inputs': captured, 'environment': readiness['identity']}
        # Paths are provenance, never part of semantic identity.
        identity['inputs'] = {k: v for k, v in captured.items() if k not in ('motion_file', 'robot_files')}
        identity['inputs']['motion'] = {k: v for k, v in captured['motion'].items() if k != 'model_path'}
        previous = None
        for stage in tuple(stages):
            relevant = {'sampling': {'sampling_seed': controls.sampling_seed},
                        'training': {'epochs': controls.epochs}, 'binding': {},
                        'retargeting': {'trajectory_filter': controls.native_filter}}[stage]
            fingerprint = canonical_hash({'schema': 1, 'stage': stage, 'identity': identity,
                                           'settings': relevant, 'dependency': previous})
            plan['fingerprints'][stage] = fingerprint
            receipt = self._receipt(run_id, run.revision_id, stage)
            if receipt and receipt['fingerprint'] == fingerprint and not any(s in plan['stages'] for s in STAGES[:STAGES.index(stage)]):
                plan['completed'].append(stage)
                plan['stages'].remove(stage)
            previous = fingerprint
        plan['ready'] = True
        return plan

    @contextmanager
    def _launch_lock(self):
        with (self.roots.state / 'execution.launch.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise StudioError('job_active', 'Another launch is being reviewed; retry explicitly', 409) from error
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def start_execution(self, run_id, *, through='retargeting', settings=None):
        with self._launch_lock():
            return self._start_execution(run_id, through=through, settings=settings)

    def _start_execution(self, run_id, *, through, settings):
        if any(j['status'] in ('queued', 'running', 'cancelling') for j in self.list_jobs()):
            raise StudioError('job_active', 'Another native job is active; wait or cancel it', 409)
        if settings is not None:
            self.save_execution_settings(run_id, settings)
        plan = self.plan_execution(run_id, through=through)
        if not plan['ready']:
            raise StudioError('not_ready', plan.get('readiness', {}).get('message', 'Select a saved robot pose and motion'), 409)
        job_id = uuid.uuid4().hex
        job = {'job_id': job_id, 'run_id': run_id, 'revision_id': plan['revision_id'],
               'status': 'queued', 'stage': None, 'progress': {}, 'created_at': now(),
               'owner_pid': os.getpid(), 'owner_identity': process_identity(os.getpid()),
               'plan': plan, 'attempts': {}, 'attempt_statuses': {}, 'message': 'Queued'}
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            recover_jobs(self, db, now())
            for row in db.execute('SELECT data FROM jobs'):
                if json.loads(row['data'])['status'] in ('queued', 'running', 'cancelling'):
                    raise StudioError('job_active', 'Another native job is active; wait or cancel it', 409)
            current = db.execute('SELECT revision_id FROM runs WHERE run_id=?', (run_id,)).fetchone()
            if current['revision_id'] != plan['revision_id']:
                raise StudioError('stale_revision', 'Inputs changed during readiness; review the plan again', 409)
            if not plan['stages']:
                raise StudioError('already_complete', 'Requested stages already have verified completion receipts', 409)
            db.execute('INSERT INTO jobs VALUES (?, ?)', (job_id, json.dumps(job)))
        from ._native_jobs import execute_job
        threading.Thread(target=execute_job, args=(self, job_id), daemon=True).start()
        return job

    def cancel_job(self, job_id):
        job = self.get_job(job_id)
        if job['status'] in ('queued', 'running'):
            return self._update_job(job_id, status='cancelling', message='Stopping native process group')
        return job

    def job_file(self, job_id, stage=None):
        job = self.get_job(job_id)
        stage = stage or job['stage']
        if stage not in job['attempts']:
            raise StudioError('not_found', 'Job has no log for this stage', 404)
        folder = self.roots.runs / job['run_id'] / job['revision_id'] / stage
        return confined_file(folder, job['attempts'][stage] + '/native.log')

    def stage_receipt(self, run_id, revision_id, stage):
        """Return a detached verified completion receipt for inspection/export adapters."""
        self.get_run(run_id)
        receipt = self._receipt(run_id, revision_id, stage)
        if not receipt:
            raise StudioError('changed_artifact', 'Stage has no intact completion receipt', 409)
        return receipt

    def stage_artifact(self, run_id, revision_id, stage, name):
        self.get_run(run_id)
        receipt = self._receipt(run_id, revision_id, stage)
        if not receipt:
            raise StudioError('changed_artifact', 'Stage has no intact completion receipt', 409)
        selected = [p for p in receipt['artifacts'] if p == name or p.endswith('/' + name)]
        if len(selected) != 1:
            raise StudioError('not_found', 'Artifact is not uniquely registered in this stage', 404)
        return confined_file(self.roots.runs / run_id / receipt['revision_id'] / stage, selected[0])
