"""G1 reproduction interface; callers need no UMR imports or configuration knowledge.

Runs the complete bundled HiPHI clip without trimming/resampling. Outputs are new,
local files; existing destinations are refused. UMR executes in its own Python
runtime. Failures retain logs and raise RuntimeError; no automatic resume or CPU
fallback. Returned paths point to validated results, not a dynamics certificate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

_WORKSPACE = Path(__file__).resolve().parents[2]
_REVISION = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
_MOTION = 'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'


@dataclass(frozen=True)
class G1BaselineResult:
    """Local motion NPZ and JSON validation/provenance records."""
    motion: Path
    validation: Path
    provenance: Path


def _git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(checkout), *args], text=True).strip()


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path: Path, value: object) -> None:
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def _execute(command: list[str], checkout: Path, output: Path, stage: str,
             environment: dict[str, str], timeout: int) -> None:
    receipt = {'command': command, 'cwd': str(checkout), 'timeout_seconds': timeout,
               'started_at': datetime.now(timezone.utc).isoformat()}
    _write(output / 'logs' / f'{stage}-started.json', receipt)
    started = time.monotonic()
    with (output / 'logs' / f'{stage}.log').open('x') as log:
        process = subprocess.Popen(command, cwd=checkout, env=environment,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except BaseException:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            receipt.update(returncode=process.returncode, interrupted_or_timed_out=True,
                           wall_seconds=time.monotonic() - started)
            _write(output / 'logs' / f'{stage}-completed.json', receipt)
            raise
    receipt.update(returncode=process.returncode, wall_seconds=time.monotonic() - started,
                   finished_at=datetime.now(timezone.utc).isoformat())
    _write(output / 'logs' / f'{stage}-completed.json', receipt)
    if process.returncode:
        raise RuntimeError(f'UMR {stage} failed ({process.returncode}); see {output}/logs/{stage}.log')


def reproduce_g1_baseline(output: Path, *, workspace: Path = _WORKSPACE) -> G1BaselineResult:
    """Fresh official-default training + full HiPHI retargeting, seed zero.

    Uses the manifest-pinned official checkout and its existing .venv. Model assets
    are read from /data/motions; source, assets, adapter and environment provenance
    are recorded. Only operational overrides (paths, device, batch cap, no viewer)
    are applied. The solver, calibration, contacts and filters retain UMR defaults.
    Requires CUDA; maximum training time 10 min, motion time 2 hours.
    """
    workspace, output = workspace.resolve(), output.resolve()
    checkout = workspace / 'externals/UMR'
    if (output.is_relative_to(workspace / 'externals')
            or output.is_relative_to((workspace / 'externals').resolve())
            or output.is_relative_to(checkout.resolve())):
        raise ValueError('Output must live outside external checkouts')
    if output.exists():
        raise FileExistsError(f'Use a fresh output directory: {output}')
    projects = json.loads((workspace / 'externals/manifest.json').read_text())['projects']
    pin = next(p['revision'] for p in projects if p['name'] == 'UMR')
    if pin != _REVISION or _git(checkout, 'rev-parse', 'HEAD') != pin:
        raise ValueError('Review adapter compatibility before changing the UMR revision')
    if _git(checkout, 'diff', pin, '--name-only'):
        raise ValueError('Official tracked UMR source must be unchanged')
    python = checkout / '.venv/bin/python'
    model = Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx')
    for required in [python, model / 'SMPLX_NEUTRAL.pkl', checkout / _MOTION]:
        if not required.is_file():
            raise FileNotFoundError(required)
    # Hash active implementation/configuration and G1 assets, not unrelated datasets.
    inputs = {}
    for name in _git(checkout, 'ls-files').splitlines():
        path = checkout / name
        if path.is_file() and (path.suffix in {'.py', '.json', '.xml'} or name.startswith('assets/g1/')):
            inputs[str(path)] = _hash(path)
    for path in [checkout / _MOTION, model / 'SMPLX_NEUTRAL.pkl',
                 Path(__file__), Path(__file__).with_name('_umr_worker.py')]:
        inputs[str(path)] = _hash(path)
    status = _git(checkout, 'status', '--porcelain')
    output.mkdir(parents=True, exist_ok=False)
    for folder in ['logs', 'cache', 'tmp']:
        (output / folder).mkdir()
    environment = os.environ.copy()
    overrides = {'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUNBUFFERED': '1', 'CUDA_VISIBLE_DEVICES': '0',
                 'OMP_NUM_THREADS': '4', 'XDG_CACHE_HOME': str(output / 'cache'),
                 'TMPDIR': str(output / 'tmp')}
    environment.update(overrides)
    _write(output / 'provenance.json', {
        'created_at': datetime.now(timezone.utc).isoformat(), 'umr_revision': pin,
        'checkout': str(checkout), 'python': str(python), 'inputs_sha256': inputs,
        'external_status_before': status, 'environment_overrides': overrides,
        'scope': 'Fresh G1 correspondence training and complete bundled HiPHI motion',
        'operational_overrides': ['absolute paths', 'copied G1 asset bundle', 'CUDA',
                                  'training seed 0', 'SMPL-X batch cap 128', 'no viewer'],
        'historical_baseline': 'experiments/umr-astro-baseline-v1/records/static-20261024-01',
    })
    worker = str(Path(__file__).with_name('_umr_worker.py'))
    base = [str(python), worker, str(checkout), str(output), str(model)]
    try:
        _execute([*base, 'prepare'], checkout, output, 'prepare', environment, 120)
        pipeline = [str(python), str(checkout / 'scripts/humanoid_retarget_pipeline.py'),
                    '--config', str(output / 'config.json'), '--defaults',
                    str(checkout / 'humanoid_retarget_defaults.json'), '--skip-view']
        _execute([*pipeline, '--stage', 'train'], checkout, output, 'train', environment, 600)
        _execute([*pipeline, '--stage', 'retarget'], checkout, output, 'retarget', environment, 7200)
        _execute([*base, 'validate'], checkout, output, 'validate', environment, 180)
    finally:
        unchanged = (_git(checkout, 'status', '--porcelain') == status
                     and _git(checkout, 'rev-parse', 'HEAD') == pin
                     and all(_hash(Path(p)) == h for p, h in inputs.items()))
        _write(output / 'preservation.json', {'external_and_inputs_unchanged': unchanged})
        if not unchanged:
            raise RuntimeError('External/input preservation check failed')
    artifacts = {str(p.relative_to(output)): _hash(p) for p in sorted(output.rglob('*'))
                 if p.is_file() and not p.is_relative_to(output / 'cache')}
    _write(output / 'artifacts.json', artifacts)
    return G1BaselineResult(output / 'motion.npz', output / 'validation.json', output / 'provenance.json')
