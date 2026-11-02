"""Fresh native generic SOMA BVH control; no fitted BONES-SEED shape is inferred."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CHECKOUT = ROOT / 'externals/UMR'
OUT = ROOT / 'outputs/umr-baseline-g1-somax-20261102'
SOURCE = Path('/data/motions/datasets/bones-seed/raw/uniform/210531/jump_and_land_light_001__A001.bvh')
ASSETS = Path('/data/motions/human_models/soma-x/f81a01796f65/overlays/umr')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, obj):
    with path.open('x') as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', '-C', str(CHECKOUT), *args], text=True).strip()


def prepare():
    import importlib.metadata
    import numpy as np
    import humanoid_retarget_pipeline as pipeline
    import soma_source
    pin = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
    if git('rev-parse', 'HEAD') != pin or git('diff', pin, '--name-only'):
        raise RuntimeError('Unchanged manifest-pinned upstream is required')
    OUT.mkdir(parents=True, exist_ok=False)
    for folder in ('logs', 'cache', 'tmp'):
        (OUT / folder).mkdir()
    shutil.copytree(CHECKOUT / 'assets/g1', OUT / 'assets/g1')
    config = json.loads((CHECKOUT / 'robot_configs/humanoid_retarget_unitree_g1_example.json').read_text())
    config['robot']['xml'] = str(OUT / 'assets/g1/g1_29dof.xml')
    config.update({
        'smpl_template': {'source': 'motion', 'type': 'soma', 'name': 'auto', 'use_gender': False},
        'motion': {'data': str(SOURCE), 'seq_key': SOURCE.stem},
        'correspondence': {'dataset': {'out': str(OUT / 'dataset.npz'), 'smpl_models': []},
                           'train': {'out_dir': str(OUT / 'train'), 'device': 'cuda', 'seed': 0}},
        'retarget': {'out': str(OUT / 'motion.npz')},
        'view': {'enabled': False},
    })
    write(OUT / 'config.json', config)
    resolved = pipeline.load_pipeline_config(OUT / 'config.json', CHECKOUT / 'humanoid_retarget_defaults_bones_seed.json')
    write(OUT / 'resolved.json', {k: v for k, v in resolved.items() if not k.startswith('_')})
    sequence = soma_source.load_soma_bvh_motion(SOURCE)
    assert sequence['source_format'] == 'soma_bvh' and 'soma_shape_params_path' not in sequence
    template = soma_source.load_soma_bind_tpose_template()
    vertices, joints, faces = soma_source.soma_motion_vertices_joints(sequence, [0], zero_fingers=True)
    assert np.isfinite(vertices).all() and vertices.shape == (1, 18056, 3)
    inputs = {str(SOURCE): digest(SOURCE)}
    for name in git('ls-files').splitlines():
        p = CHECKOUT / name
        if p.is_file() and (p.suffix in {'.py', '.json', '.xml'} or name.startswith('assets/g1/')):
            inputs[str(p)] = digest(p)
    for p in ASSETS.rglob('*'):
        if p.is_file():
            inputs[str(p)] = digest(p)
    # rglob does not descend directory symlinks; these active correspondence assets do.
    for subdir in ('SMPLX',):
        for p in (ASSETS / subdir).rglob('*'):
            if p.is_file():
                inputs[str(p)] = digest(p)
    inputs[str(Path(__file__))] = digest(__file__)
    write(OUT / 'provenance.json', {
        'cohort': 'generic-neutral-direct-SOMA-control', 'official_fitted_bones_seed': False,
        'umr_revision': pin, 'external_status_before': git('status', '--porcelain'),
        'source': str(SOURCE), 'inputs_sha256': inputs,
        'source_format': sequence['source_format'], 'frames': sequence['num_frames'], 'fps': sequence['fps'],
        'template_vertices': len(template['points']), 'template_joints': len(template['joint_names']),
        'source_route': 'Native generic BVH global transforms and neutral bind/T-pose linear blend skinning; no SMPL-X motion conversion',
        'official_blocker': 'Missing uniform soma_base_fit_mhr_params.npz; generic loader does not use a dataset USD rig',
        'asset_overlay': str(ASSETS), 'soma_model_revision': 'f81a01796f652260ff930d5318d6c6b845a505ed',
        'soma_overlay_derivation': str(ASSETS / 'LOCAL_MODIFICATIONS.md'),
        'packages': sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
        'python': sys.version, 'operational_overrides': ['absolute paths', 'fresh copied G1 asset closure', 'no viewer', 'seed zero', 'CUDA training'],
        'calibration_limit': 'Neutral model template is not a fitted uniform BONES-SEED actor surface; skeleton offsets may differ',
    })


def execute(stage):
    command = [sys.executable, str(CHECKOUT / 'scripts/humanoid_retarget_pipeline.py'),
               '--config', str(OUT / 'config.json'), '--defaults',
               str(CHECKOUT / 'humanoid_retarget_defaults_bones_seed.json'), '--skip-view', '--stage', stage]
    environment = os.environ.copy()
    overrides = {'UMR_SOMA_ASSETS_PATH': str(ASSETS), 'UMR_SOMA_SMPLX_ASSETS_PATH': str(ASSETS / 'SMPLX'),
                 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUNBUFFERED': '1', 'CUDA_VISIBLE_DEVICES': '0',
                 'OMP_NUM_THREADS': '4', 'OPENBLAS_NUM_THREADS': '4',
                 'XDG_CACHE_HOME': str(OUT / 'cache'), 'TMPDIR': str(OUT / 'tmp')}
    environment.update(overrides)
    started = time.time()
    snapshot = OUT / f'runner-{stage}.py'
    shutil.copyfile(__file__, snapshot)
    with (OUT / 'logs' / f'{stage}.log').open('x') as log:
        result = subprocess.run(command, cwd=CHECKOUT, env=environment, stdout=log, stderr=subprocess.STDOUT)
    write(OUT / 'logs' / f'{stage}-completed.json', {'command': command, 'cwd': str(CHECKOUT),
        'environment_overrides': overrides, 'started_unix': started,
        'wall_seconds': time.time() - started, 'returncode': result.returncode})
    original = json.loads((OUT / 'provenance.json').read_text())
    runner = str(Path(__file__))
    checked = {name: digest(name) == expected for name, expected in original['inputs_sha256'].items() if name != runner}
    initial_runner = OUT / 'runner-prepared.py'
    runner_preserved = (digest(initial_runner) == original['inputs_sha256'][runner]
                        if initial_runner.exists() else digest(runner) == original['inputs_sha256'][runner])
    write(OUT / f'preservation-{stage}.json', {
        'source_assets_and_upstream_hashes_unchanged': all(checked.values()),
        'changed_inputs': [name for name, passed in checked.items() if not passed],
        'prepared_runner_preserved': runner_preserved,
        'executed_runner_snapshot': str(snapshot), 'executed_runner_sha256': digest(snapshot),
        'external_revision_unchanged': git('rev-parse', 'HEAD') == original['umr_revision'],
        'external_status_unchanged': git('status', '--porcelain') == original['external_status_before'],
    })
    if not all(checked.values()) or not runner_preserved:
        raise RuntimeError('Input preservation failed')
    if result.returncode:
        raise RuntimeError(f'{stage} failed; see retained log')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'build', 'train', 'retarget'))
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output.resolve()
    if OUT.is_relative_to((ROOT / 'externals').resolve()) or OUT.is_relative_to(CHECKOUT.resolve()):
        raise ValueError('Output must be outside externals')
    os.environ['UMR_SOMA_ASSETS_PATH'] = str(ASSETS)
    os.environ['UMR_SOMA_SMPLX_ASSETS_PATH'] = str(ASSETS / 'SMPLX')
    sys.path.insert(0, str(CHECKOUT / 'scripts'))
    if args.stage == 'prepare':
        prepare()
    else:
        execute(args.stage)
