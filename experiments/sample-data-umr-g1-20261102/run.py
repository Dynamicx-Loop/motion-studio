"""Run two fresh official-default G1 sample verifications in UMR's runtime."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
UMR = ROOT / 'externals/UMR'
PIN = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
MODEL = Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx')
SAMPLES = ROOT / 'data/sample_data'
SOMA = SAMPLES / 'bones-seed/soma_assets'
CASES = {
    'bones-seed': SAMPLES / 'bones-seed/motions_uniform/bvh/jump_and_land_light_003__A001.bvh',
    'wendy': SAMPLES / 'fzmotion/smplx/victory-146-short_Skeleton1.npz',
}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', '-C', str(UMR), *args], text=True).strip()


def validate(out, config, source, pipeline):
    import mujoco
    import numpy as np
    import smpl_surface_retarget_common as common
    data, _ = common.load_motion_collection(source)
    _, seq = common.select_sequence(data, source.stem, 0)
    expected = common.sequence_frame_count(seq)
    assert pipeline.correspondence_dataset_compatible(out / 'dataset.npz', config)
    slots = out / 'train/correspondence_slots_final.npz'
    assert pipeline.correspondence_slots_compatible(slots, config)
    with np.load(slots, allow_pickle=True) as z:
        assert z['reconstructed_slots'].shape == (2, 4096, 3)
        assert np.isfinite(z['reconstructed_slots']).all()
    with np.load(out / 'motion.npz', allow_pickle=True) as z:
        qpos, ids, fps = z['qpos'], z['frame_ids'], float(z['fps'])
        robot = mujoco.MjModel.from_xml_path(str(z['robot_xml']))
        assert qpos.shape == (expected, robot.nq) and np.isfinite(qpos).all()
        np.testing.assert_array_equal(ids, np.arange(expected))
        assert abs(fps - seq['fps']) <= float(np.spacing(np.float32(seq['fps'])))
        assert Path(str(z['source_data'])).resolve() == source.resolve()
        names = [robot.joint(j).name for j in range(robot.njnt)
                 if robot.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
        assert len(names) == 29 and z['robot_joint_names'].tolist() == names
        norm_error = float(np.abs(np.linalg.norm(qpos[:, 3:7], axis=1) - 1).max())
        assert norm_error <= 1e-6
        excess = 0.
        for j in range(robot.njnt):
            if robot.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
                continue
            lo, hi = robot.jnt_range[j] if robot.jnt_limited[j] else (-np.inf, np.inf)
            override = config['robot']['joint_limits'].get(robot.joint(j).name)
            if override:
                a, b = map(float, override)
                lo, hi = max(a, lo), min(b, hi)
            values = qpos[:, robot.jnt_qposadr[j]]
            excess = max(excess, float((lo-values).max()), float((values-hi).max()))
        assert excess <= 1e-6, excess
        steps = np.abs(np.diff(qpos[:, 7:], axis=0))
        return dict(source=str(source), source_sha256=digest(source),
                    source_format=seq['source_format'], source_template=seq.get('soma_template_name', 'smplx_neutral'),
                    frames=expected, fps=fps, qpos_shape=list(qpos.shape), all_source_frames_preserved=True,
                    finite_motion=True, dataset_and_slots_compatible=True, root_quaternion='wxyz',
                    quaternion_norm_max_error=norm_error, joint_limit_max_excess_rad=excess,
                    joint_step_p95_rad_per_frame=float(np.percentile(steps, 95)),
                    joint_step_max_rad_per_frame=float(steps.max()), robot_joint_names=names,
                    motion_sha256=digest(out / 'motion.npz'),
                    limitations=['Numerical execution and kinematic validity only',
                                 'No visual fidelity, contact, collision or dynamic feasibility assessment'])


def run_case(kind, parent, pipeline):
    import torch
    import smpl_surface_retarget_common as common
    source = CASES[kind]
    out = parent / kind
    out.mkdir()
    for name in ['logs', 'cache', 'tmp']:
        (out / name).mkdir()
    overrides = dict(PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1', OMP_NUM_THREADS='4',
                     OPENBLAS_NUM_THREADS='4', CUDA_VISIBLE_DEVICES='0', XDG_CACHE_HOME=str(out / 'cache'),
                     TMPDIR=str(out / 'tmp'), UMR_WARP_CACHE_DIR=str(out / 'cache/warp'),
                     UMR_SOMA_ASSETS_PATH=str(SOMA.resolve()), UMR_SOMA_SMPLX_ASSETS_PATH=str(SOMA.resolve() / 'SMPLX'))
    os.environ.update(overrides)
    data, _ = common.load_motion_collection(source)
    _, seq = common.select_sequence(data, source.stem, 0)
    if kind == 'bones-seed':
        assert seq['source_format'] == 'soma_bvh_boneseed_uniform'
        assert seq['soma_template_name'] == 'soma_uniform'
        assert digest(seq['soma_shape_params_path']) == '61f0b96c8386a19d44823faf4399816642b7e20691ed5b398c7402921090096e'
    else:
        assert seq['source_format'] == 'smplx_npz' and seq['output_up'] == 'y'
    shutil.copytree(UMR / 'assets/g1', out / 'assets/g1')
    cfg = json.loads((UMR / 'robot_configs/humanoid_retarget_unitree_g1_example.json').read_text())
    cfg['robot']['xml'] = str(out / 'assets/g1/g1_29dof.xml')
    cfg.update(smplx_model_dir=str(MODEL), motion=dict(data=str(source), seq_key=source.stem),
               correspondence=dict(dataset=dict(out=str(out / 'dataset.npz'),
                   smpl_models=[] if kind == 'bones-seed' else [dict(type='smplx', dir=str(MODEL), genders=['neutral'])]),
                   train=dict(out_dir=str(out / 'train'), device='cuda', seed=0)),
               retarget=dict(out=str(out / 'motion.npz'), smplx_batch_size=64), view=dict(enabled=False))
    if kind == 'bones-seed':
        cfg['smpl_template'] = dict(source='motion', type='soma', name='auto', use_gender=False)
        cfg['soma_usd_path'] = str(SAMPLES / 'bones-seed/shapes/soma_base_rig/soma_base_skel_minimal.usd')
        cfg['smpl_template']['soma_usd_path'] = cfg['soma_usd_path']
    defaults = UMR / ('humanoid_retarget_defaults_bones_seed.json' if kind == 'bones-seed' else 'humanoid_retarget_defaults.json')
    write(out / 'config.json', cfg)
    config = pipeline.load_pipeline_config(out / 'config.json', defaults)
    assert config['correspondence']['train']['epochs'] == 500
    assert config['correspondence']['dataset']['num_points'] == 4096
    write(out / 'resolved.json', {k:v for k,v in config.items() if not k.startswith('_')})
    inputs = {str(source): digest(source), str(MODEL / 'SMPLX_NEUTRAL.pkl'): digest(MODEL / 'SMPLX_NEUTRAL.pkl')}
    for name in git('ls-files').splitlines():
        p = UMR / name
        if p.is_file() and (p.suffix in {'.py', '.json', '.xml'} or name.startswith('assets/g1/')):
            inputs[str(p)] = digest(p)
    manifest = json.loads((SAMPLES / 'manifest.json').read_text())
    for item in manifest['local_model_links'][0]['files']:
        p = SOMA / item['path']; inputs[str(p)] = digest(p)
        assert inputs[str(p)] == item['sha256']
    if kind == 'bones-seed':
        p = Path(seq['soma_shape_params_path']); inputs[str(p)] = digest(p)
    inputs[str(out / 'config.json')] = digest(out / 'config.json')
    inputs[str(out / 'runner.py')] = digest(out / 'runner.py') if (out / 'runner.py').exists() else digest(__file__)
    shutil.copyfile(__file__, out / 'runner.py')
    status = git('status', '--porcelain')
    write(out / 'provenance.json', dict(umr_revision=PIN, external_status_before=status,
          inputs_sha256=inputs, environment_overrides=overrides, python=sys.version,
          gpu=torch.cuda.get_device_name(0), packages=sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
          source_format=seq['source_format'], native_defaults=str(defaults),
          scope='Fresh 4096-point sampling, 500-epoch training, full clip retargeting; official bundled G1'))
    for stage in ['train', 'retarget']:
        command = [sys.executable, '-B', str(UMR / 'scripts/humanoid_retarget_pipeline.py'),
                   '--config', str(out / 'config.json'), '--defaults', str(defaults), '--skip-view', '--stage', stage]
        started = time.monotonic()
        print(f'{kind}: starting {stage}', flush=True)
        with (out / 'logs' / f'{stage}.log').open('x') as log:
            completed = subprocess.run(command, cwd=UMR, stdout=log, stderr=subprocess.STDOUT)
        write(out / 'logs' / f'{stage}-completed.json', dict(command=command, cwd=str(UMR), returncode=completed.returncode, wall_seconds=time.monotonic()-started))
        if completed.returncode:
            raise RuntimeError(f'{kind} {stage} failed; see {out}/logs/{stage}.log')
        print(f'{kind}: {stage} completed in {time.monotonic()-started:.1f}s', flush=True)
    result = validate(out, config, source, pipeline)
    write(out / 'validation.json', result)
    changed = [p for p,h in inputs.items() if digest(p) != h]
    unchanged = not changed and git('status', '--porcelain') == status and git('rev-parse', 'HEAD') == PIN
    write(out / 'preservation.json', dict(unchanged=unchanged, changed_inputs=changed))
    assert unchanged
    print(f'{kind}: PASS {result["frames"]} frames', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'outputs')
    if out.exists(): raise FileExistsError(out)
    assert git('rev-parse', 'HEAD') == PIN and not git('diff', PIN, '--name-only')
    import torch
    if not torch.cuda.is_available(): raise RuntimeError('Host CUDA access required')
    out.mkdir(parents=True)
    sys.path.insert(0, str(UMR / 'scripts'))
    import humanoid_retarget_pipeline as pipeline
    results = {kind:run_case(kind, out, pipeline) for kind in CASES}
    write(out / 'summary.json', results)


if __name__ == '__main__':
    main()
