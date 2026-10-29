"""File readiness and a non-executing run reservation; never import upstream code."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import uuid

from ._contracts import validate
from ._files import (file_record, implementation_sources, read_json,
                     record_implementation, resolve, seal, sha256, write_json)


def inspect_plan(plan: dict, root: Path) -> dict:
    """Return v1 file checks for a plan under explicit root; never execute stages.

    Invalid contracts raise ValueError. Missing or drifting input bytes produce
    blocked checks. A file-ready result always has execution_ready=False because
    no launcher exists. Neither the plan nor its inputs are mutated.
    """
    root = root.expanduser().resolve()
    validate(plan, 'plan')
    checks, sources = [], []

    def check(identity: str, status: str, detail: str) -> None:
        checks.append({'id': identity, 'status': status, 'detail': detail})

    def inspect(identity: str, path: Path, expected: str | None, required: bool) -> bool:
        if not path.is_file():
            check(identity, 'blocked' if required else 'unknown', f'Missing file: {path}')
            return False
        try:
            with path.open('rb') as stream:
                prefix = stream.read(150)
            if prefix.startswith(b'version https://git-lfs.github.com/spec/v1'):
                check(identity, 'blocked', 'Git LFS pointer; payload is unavailable')
                return False
            record = file_record(path, root)
        except OSError as error:
            check(identity, 'blocked', f'Cannot read {path}: {error}')
            return False
        sources.append(record)
        if expected is None:
            check(identity, 'blocked' if required else 'unknown',
                  f"Unpinned file; observed sha256={record['sha256']}")
            return False
        if record['sha256'] != expected:
            check(identity, 'blocked', f"Hash mismatch: {path}; observed={record['sha256']}")
            return False
        check(identity, 'passed', str(path))
        return True

    roles = {item['role'] for item in plan['inputs'] if item['required']}
    required_roles = {'robot', 'code', 'dependencies', 'config'}
    if plan['source']['kind'] == 'soma_bones_seed':
        required_roles |= {'motion', 'actor_shape', 'rig_bvh', 'rig_usd'}
    else:
        required_roles |= {'motion_actor'}
    for role in sorted(required_roles - roles):
        check(f'role:{role}', 'blocked', 'Required input role is undeclared')
    for item in plan['inputs']:
        path = resolve(root, item['path'])
        if inspect(item['id'], path, item['sha256'], item['required']) and item.get('manifest_key'):
            members = read_json(path).get(item['manifest_key'])
            if not isinstance(members, dict) or not members:
                check(item['id'] + ':members', 'blocked', 'Manifest must contain a nonempty hash map')
                continue
            for member, digest in sorted(members.items()):
                if isinstance(digest, dict):
                    digest = digest.get('sha256')
                if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                    check(item['id'] + ':' + member, 'blocked', 'Invalid member SHA-256')
                    continue
                inspect(item['id'] + ':' + member, resolve(root, member), digest, True)
    for key, item in plan['runtime_checks'].items():
        # Hashing a saved check is necessary but not sufficient: an adapter must
        # establish that it covers this exact input set and selected environment.
        check('runtime:' + key, 'deferred', item)
    check('execution_adapter', 'deferred',
          'No launcher installed: reserve records a plan only; no stages execute')
    return {'schema_version': 1, 'experiment_id': plan['experiment_id'],
            'file_ready': not any(c['status'] == 'blocked' for c in checks),
            'execution_ready': False, 'checks': checks,
            'sources': list({s['path']: s for s in sources}.values())}


def reserve(plan_path: Path, root: Path, output_root: Path) -> Path:
    """Create an exclusive, sealed preparation receipt only after file checks pass."""
    root = root.expanduser().resolve()
    plan_path = plan_path.expanduser().absolute()
    output_root = output_root.expanduser().absolute()
    plan_hash = sha256(plan_path)
    plan = read_json(plan_path)
    report = inspect_plan(plan, root)
    if not report['file_ready']:
        raise ValueError('Preflight blocked; inspect the preflight JSON before reserving a run')
    if sha256(plan_path) != plan_hash:
        raise ValueError('Plan changed during preflight')
    # Detect common input edits between inspection and reservation.
    for source in report['sources']:
        if sha256(resolve(root, source['path'])) != source['sha256']:
            raise ValueError(f"Input changed during preflight: {source['path']}")
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_id = f"{plan['experiment_id']}-{stamp}-{uuid.uuid4().hex[:12]}"
    destination = output_root / run_id
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination / 'plan.json', plan)
    write_json(destination / 'preflight.json', report)
    write_json(destination / 'receipt.json', {
        'schema_version': 1, 'run_id': run_id, 'state': 'prepared_only',
        'stages_executed': [], 'created_at': stamp, 'plan_sha256': plan_hash,
        'execution_ready': False, 'runtime_environment': None,
        'failure': None, 'note': 'No subprocess, training, binding, retargeting or filtering ran.'})
    implementation = implementation_sources(root)
    record_implementation(destination, implementation)
    seal(destination, report['sources'] + [file_record(plan_path, root)] + implementation, root)
    return destination
