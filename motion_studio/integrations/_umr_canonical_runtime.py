"""Private pinned UMR prerequisite inspection. Never imports upstream into caller."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

_REVISION = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'


def inspect_runtime(runtime):
    if runtime is None:
        return ({'status': 'unverified', 'identity': {'status': 'unverified'},
                 'defaults_train': {'status': 'unverified'},
                 'reason': 'No explicit UMR runtime supplied; backend/config/environment not verified.'}, [])
    from .umr_canonical import CanonicalPreparationError, _hash, _identity
    root, python = Path(runtime.checkout).resolve(), Path(runtime.python).absolute()

    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.PIPE).strip()

    try:
        checkout_root, head = git('rev-parse', '--show-toplevel'), git('rev-parse', 'HEAD')
    except (OSError, subprocess.CalledProcessError) as error:
        raise CanonicalPreparationError(f'UMR checkout unavailable: {root}') from error
    if checkout_root != str(root) or head != _REVISION:
        raise CanonicalPreparationError('Canonical adapter requires the pinned official UMR checkout')
    if git('diff', _REVISION, '--name-only'):
        raise CanonicalPreparationError('Tracked UMR source drift; no experimental patch adoption')
    files = []
    for name in git('ls-files').splitlines():
        path = root/name
        if path.suffix in ('.py', '.json') and path.is_file():
            files.append((name, path, _hash(path)))
    defaults = json.loads((root/'humanoid_retarget_defaults.json').read_text())
    probe = '''import importlib.metadata,json,sys
packages={n:importlib.metadata.version(n) for n in ['mujoco','numpy','torch','smplx','trimesh']}
print(json.dumps({'python':sys.version,'packages':packages}))'''
    try:
        result = subprocess.run([str(python), '-c', probe], capture_output=True, text=True,
                                timeout=30, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        if result.returncode:
            raise CanonicalPreparationError('UMR runtime prerequisite probe failed: ' + result.stderr[-2000:])
        environment = json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        raise CanonicalPreparationError(f'UMR runtime unavailable: {error}') from error
    identity = {'revision': _REVISION, 'tracked_patch_sha256': hashlib.sha256(b'').hexdigest(),
                'code_config_sha256': {n:h for n,_,h in files}, 'environment': environment,
                'interpreter_sha256': _hash(python)}
    return ({'status': 'prerequisites-inspected', 'identity': identity,
             'defaults_train': defaults['correspondence']['train'],
             'checkout': str(root), 'python': str(python), 'status_before': git('status', '--porcelain'),
             'environment_sha256': _identity(environment),
             'execution': 'unverified; no CUDA, model-format, training or retarget test'}, files)


def verify_runtime_unchanged(runtime, record):
    if runtime is None:
        return
    from .umr_canonical import CanonicalPreparationError
    root = Path(runtime.checkout).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.PIPE).strip()
    if (git('rev-parse', 'HEAD') != _REVISION or git('diff', _REVISION, '--name-only')
            or git('status', '--porcelain') != record['status_before']):
        raise CanonicalPreparationError('UMR source changed during preparation')
