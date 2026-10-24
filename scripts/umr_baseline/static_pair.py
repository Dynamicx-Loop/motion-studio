"""Prepare one fresh official-default SMPL-X pair; run one bounded static arm.

No motion stage, downloads, installs, upstream edits, or implicit resume. Reuse
the existing UMR interpreter. Every invocation is recorded in a new run folder.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

WORKSPACE = Path(__file__).resolve().parents[2]
UMR = Path(os.environ.get('MOTION_STUDIO_UMR_ROOT', WORKSPACE / 'externals/UMR-baseline-v1')).resolve()
sys.path.insert(0, str(UMR / 'scripts'))
import humanoid_retarget_pipeline as pipeline

REVISION = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
ASTRO_REVISION = 'd2070956558ffbf9226dcf74017d40740724d8d8'
ASTRO_DIR = 'robots/astro_p2_43dof_dex3_1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def check_official_source():
    # This branch may add integration files, but cannot change upstream files.
    changed = git(UMR, 'diff', REVISION, '--name-only', '--', '.', ':!motion_studio')
    if changed:
        raise ValueError('Official tracked content differs: ' + changed)


def prepare(args):
    import mujoco
    import numpy as np
    check_official_source()
    if git(args.menagerie, 'rev-parse', 'HEAD') != ASTRO_REVISION:
        raise ValueError('Inspect the changed Astro revision before preparing a new cohort')
    if git(args.menagerie, 'status', '--porcelain', '--untracked-files=no', '--', ASTRO_DIR):
        raise ValueError('Astro tracked bundle changed since review')
    args.run.mkdir(parents=True, exist_ok=False)
    for folder in ['configs', 'assets/astro', 'cache', 'tmp', 'logs']:
        (args.run / folder).mkdir(parents=True)
    asset_files = git(args.menagerie, 'ls-files', '--', ASTRO_DIR).splitlines()
    inputs = {}
    for name in asset_files:
        src = args.menagerie / name
        target = args.run / 'assets/astro' / src.relative_to(args.menagerie / ASTRO_DIR)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        inputs[str(src)] = sha(src)
        inputs[str(target)] = sha(target)
    motion = UMR / 'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
    inputs[str(motion)] = sha(motion)
    defaults = UMR / 'humanoid_retarget_defaults.json'
    g1_path = UMR / 'robot_configs/humanoid_retarget_unitree_g1_example.json'
    g1 = json.loads(g1_path.read_text())
    g1['robot']['xml'] = str((g1_path.parent / g1['robot']['xml']).resolve())
    fist = json.loads((args.run / 'assets/astro/fist-pose.json').read_text())['joint_positions']
    pose = dict(g1['robot']['tpose_qpos'])
    pose.update(fist)
    astro = {'robot': {'name': 'astro_p2_43dof_dex3_1',
                      'xml': str(args.run / 'assets/astro/astro_p2_43dof_dex3_1.xml'),
                      'point_cloud_center': 'body:pelvis', 'tpose_qpos': pose}}
    observations = {}
    for arm, robot in [('g1', g1), ('astro', astro)]:
        override = copy.deepcopy(robot)
        override.update({'smplx_model_dir': str(args.smplx),
                         'motion': {'data': str(motion), 'seq_key': 'motion_actor_smplx'}})
        override['correspondence'] = {
            'dataset': {'out': str(args.run / arm / 'dataset.npz'),
                        'smpl_models': [{'type': 'smplx', 'dir': str(args.smplx), 'genders': ['neutral']}]},
            'train': {'out_dir': str(args.run / arm / 'train'), 'device': 'cuda', 'seed': 0}}
        override['retarget'] = {'out': str(args.run / arm / 'NOT_AUTHORIZED_motion.npz')}
        path = args.run / 'configs' / (arm + '.json')
        write(path, override)
        config = pipeline.load_pipeline_config(path, defaults)
        write(args.run / 'configs' / (arm + '-resolved.json'),
              {k: v for k, v in config.items() if not k.startswith('_')})
        template = pipeline.smpl_template_config(config)
        template['betas'] = None if template['betas'] is None else template['betas'].tolist()
        model = mujoco.MjModel.from_xml_path(config['robot']['xml'])
        import build_correspondence_ae_dataset as build
        data = mujoco.MjData(model)
        build.apply_joint_qpos(model, data, config['robot']['tpose_qpos'], required=True)
        mujoco.mj_forward(model, data)
        for name, value in config['robot']['tpose_qpos'].items():
            joint = model.joint(name)
            if bool(joint.limited[0]) and not joint.range[0] <= value <= joint.range[1]:
                raise ValueError(f'{arm}/{name}: static pose outside MJCF limits')
        observations[arm] = {'template': template, 'nq': model.nq, 'nv': model.nv,
                             'joints': [model.joint(i).name for i in range(model.njnt)],
                             'training_mode': pipeline.expected_correspondence_training_mode(config)}
    assert observations['astro']['template'] == observations['g1']['template']
    # Record both available file formats; the official loader chooses pkl first.
    gender = observations['g1']['template']['gender'].upper()
    for ext in ['npz', 'pkl']:
        p = args.smplx / f'SMPLX_{gender}.{ext}'
        if p.exists():
            inputs[str(p)] = sha(p)
    # Include official implementation/configuration plus the entire G1 asset set.
    for name in git(UMR, 'ls-files').splitlines():
        p = UMR / name
        if (p.suffix in {'.py', '.json', '.xml'} or name.startswith('assets/g1/')) and p.is_file():
            inputs[str(p)] = sha(p)
    for p in (args.run / 'configs').glob('*.json'):
        inputs[str(p)] = sha(p)
    study = args.workspace / 'references/umr-paper-study-v1.md'
    inputs[str(study)] = sha(study)
    guideline = args.workspace / 'docs/umr-astro-baseline-proposal.md'
    inputs[str(guideline)] = sha(guideline)
    for p in Path(__file__).resolve().parent.glob('*.py'):
        inputs[str(p)] = sha(p)
    write(args.run / 'provenance.json', {
        'schema_version': 1, 'run_id': args.run.name, 'cohort_status': 'baseline_candidate',
        'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'umr_revision': REVISION, 'branch': git(UMR, 'branch', '--show-current'),
        'astro_revision': ASTRO_REVISION, 'worktree': str(UMR),
        'python': sys.executable, 'python_version': sys.version,
        'packages': sorted({d.metadata['Name'] + '==' + d.version for d in importlib.metadata.distributions()}),
        'inputs_sha256': inputs, 'observations': observations,
        'literature_studies': [{'path': str(study), 'version': 'v1', 'sha256': sha(study)}],
        'environment_overrides': {'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '0',
                                  'OMP_NUM_THREADS': '4', 'XDG_CACHE_HOME': str(args.run / 'cache'),
                                  'TMPDIR': str(args.run / 'tmp')},
        'scope': 'Two fresh static trainings only; no retarget or ablations',
        'default_training': '500 epochs, batch 2, all_samples, 4096 points; source slots may differ after training',
        'isolation': 'Separate worktree/config/output/cache; existing UMR venv shared read-only, not a new env',
        'limitations': ['Single source actor, single seed; not a repeatability study',
                        'SOMA-X matched motion/actor/rig unavailable',
                        'Astro static fist pose only; motion finger constraints require a separate reviewed config',
                        'No remote freshness check; all previous runs excluded as legacy']})
    print(json.dumps({'run': str(args.run), 'observations': observations}, indent=2))


def run_arm(args):
    import torch
    check_official_source()
    provenance = json.loads((args.run / 'provenance.json').read_text())
    for path, expected in provenance['inputs_sha256'].items():
        if sha(path) != expected:
            raise ValueError('Frozen input changed: ' + path)
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; no automatic CPU fallback')
    if (args.run / args.arm).exists():
        raise FileExistsError('Arm output already exists; use a new run, never resume/overwrite')
    command = [sys.executable, str(UMR / 'scripts/humanoid_retarget_pipeline.py'),
               '--config', str(args.run / 'configs' / (args.arm + '.json')),
               '--defaults', str(UMR / 'humanoid_retarget_defaults.json'),
               '--stage', 'train', '--skip-view']
    environment = os.environ.copy()
    environment.update(provenance['environment_overrides'])
    receipt = {'command': command, 'cwd': str(UMR), 'timeout_seconds': 600,
               'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
               'device': torch.cuda.get_device_name(0), 'total_memory_bytes': torch.cuda.get_device_properties(0).total_memory,
               'environment_overrides': provenance['environment_overrides']}
    write(args.run / 'logs' / (args.arm + '-started.json'), receipt)
    started = time.monotonic()
    with (args.run / 'logs' / (args.arm + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=UMR, env=environment, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            receipt['returncode'] = process.wait(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            receipt.update(returncode=process.returncode, timed_out=True)
    receipt.update(wall_seconds=time.monotonic() - started,
                   finished_at=dt.datetime.now(dt.timezone.utc).isoformat())
    write(args.run / 'logs' / (args.arm + '-completed.json'), receipt)
    print(json.dumps(receipt, indent=2))
    if receipt['returncode']:
        raise SystemExit(receipt['returncode'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--arm', choices=['g1', 'astro'])
    parser.add_argument('--workspace', type=Path, default=WORKSPACE)
    parser.add_argument('--menagerie', type=Path)
    parser.add_argument('--smplx', type=Path)
    args = parser.parse_args()
    args.run = args.run.resolve()
    if args.action == 'prepare':
        if not args.menagerie or not args.smplx:
            parser.error('prepare requires --menagerie and --smplx')
        prepare(args)
    else:
        if not args.arm:
            parser.error('run requires --arm')
        run_arm(args)


if __name__ == '__main__':
    main()
