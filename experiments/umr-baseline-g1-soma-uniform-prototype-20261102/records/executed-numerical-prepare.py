"""Prepare a fresh, strictly fitted BONES-SEED source; never accept generic fallback."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CHECKOUT = ROOT / 'externals/UMR'
SOURCE = Path('/data/motions/datasets/bones-seed/raw/uniform/210531/jump_and_land_light_001__A001.bvh')
FIT = Path('/data/workspace/notAnyrobot/kimodo/kimodo/assets/skeletons/somaskel30/soma_base_fit_mhr_params.npz')
FIT_SHA256 = '61f0b96c8386a19d44823faf4399816642b7e20691ed5b398c7402921090096e'
SOURCE_SHA256 = 'fe819b350aaf0cb269d810d32124a8e24931bd20586e305407aa59144b1cfaff'
ASSETS = Path('/data/motions/human_models/soma-x/f81a01796f65/overlays/umr')
PIN = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
DEFAULT_OUTPUT = ROOT / 'outputs/umr-baseline-g1-soma-uniform-prototype-20261102'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, obj):
    with Path(path).open('x') as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', '-C', str(CHECKOUT), *args], text=True).strip()


def environment(out):
    return {'UMR_SOMA_ASSETS_PATH': str(ASSETS), 'UMR_SOMA_SMPLX_ASSETS_PATH': str(ASSETS / 'SMPLX'),
            'UMR_WARP_CACHE_DIR': str(out / 'cache/warp'), 'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONUNBUFFERED': '1', 'CUDA_VISIBLE_DEVICES': '0', 'OMP_NUM_THREADS': '4',
            'OPENBLAS_NUM_THREADS': '4', 'XDG_CACHE_HOME': str(out / 'cache'), 'TMPDIR': str(out / 'tmp')}


def assert_fitted(sequence, expected_fit):
    if sequence.get('source_format') != 'soma_bvh_boneseed_uniform':
        raise ValueError(f"Required fitted uniform route; resolved {sequence.get('source_format')!r}; generic fallback rejected")
    if sequence.get('soma_template_name') != 'soma_uniform':
        raise ValueError('Required distinct soma_uniform template')
    found = Path(sequence['soma_shape_params_path'])
    if found.resolve() != Path(expected_fit).resolve() or digest(found) != FIT_SHA256:
        raise ValueError('Required exact verified shared uniform fit')
    if Path(sequence['soma_assets_path']).resolve() != ASSETS.resolve():
        raise ValueError('Unexpected SOMA model assets')


def source_path(out):
    return out / 'input/bones-seed/motions_uniform/bvh' / SOURCE.name


def fit_path(out):
    return out / 'input/bones-seed/shapes/soma_uniform_fit_mhr_params' / FIT.name


def reject_missing_fit(out):
    """Observe native fallback, then reject it before loading any body model."""
    import soma_source
    with tempfile.TemporaryDirectory(dir=out / 'tmp', prefix='missing-fit-') as temp:
        family = Path(temp)
        motion = family / 'motions_uniform/bvh' / SOURCE.name
        motion.parent.mkdir(parents=True)
        motion.symlink_to(SOURCE)
        (family / 'shapes/soma_uniform_fit_mhr_params').mkdir(parents=True)
        (family / 'soma_assets').symlink_to(ASSETS, target_is_directory=True)
        sequence = soma_source.load_soma_bvh_motion(motion)
        try:
            assert_fitted(sequence, family / 'shapes/soma_uniform_fit_mhr_params' / FIT.name)
        except ValueError as exc:
            return {'passed': True, 'native_source_format_without_fit': sequence['source_format'],
                    'rejection': str(exc), 'body_model_loaded': False, 'sampling_training_started': False}
        raise AssertionError('Missing fit was accepted')


def collect_inputs():
    inputs = {str(SOURCE): digest(SOURCE), str(FIT): digest(FIT)}
    for name in git('ls-files').splitlines():
        p = CHECKOUT / name
        if p.is_file() and (p.suffix in {'.py', '.json', '.xml'} or name.startswith('assets/g1/')):
            inputs[str(p)] = digest(p)
    for folder, _dirs, files in os.walk(ASSETS, followlinks=True):
        for name in files:
            p = Path(folder) / name
            inputs[str(p)] = digest(p)
    return inputs


def prepare(out):
    import numpy as np
    import humanoid_retarget_pipeline as pipeline
    import soma_source
    if git('rev-parse', 'HEAD') != PIN or git('diff', PIN, '--name-only'):
        raise RuntimeError('Unchanged pinned upstream required')
    if not FIT.is_file() or digest(FIT) != FIT_SHA256:
        raise ValueError('Missing or incorrect authoritative shared uniform fit')
    if digest(SOURCE) != SOURCE_SHA256:
        raise ValueError('Unexpected source BVH bytes')
    out.mkdir(parents=True, exist_ok=False)
    for name in ('logs', 'cache', 'tmp', 'code'):
        (out / name).mkdir()
    os.environ.update(environment(out))
    write(out / 'missing-fit-rejection.json', reject_missing_fit(out))
    motion, fit = source_path(out), fit_path(out)
    motion.parent.mkdir(parents=True)
    fit.parent.mkdir(parents=True)
    shutil.copyfile(SOURCE, motion)
    shutil.copyfile(FIT, fit)
    (out / 'input/bones-seed/soma_assets').symlink_to(ASSETS, target_is_directory=True)
    assert digest(motion) == SOURCE_SHA256 and digest(fit) == FIT_SHA256
    sequence = soma_source.load_soma_bvh_motion(motion)
    assert_fitted(sequence, fit)
    if sequence['num_frames'] != 1165 or abs(sequence['fps'] - 120.0048) > 1e-8:
        raise ValueError('Unexpected source timeline')
    vertices, joints, faces, template = soma_source.soma_template_vertices_joints_faces(sequence=sequence)
    moving, moving_joints, moving_faces = soma_source.soma_motion_vertices_joints(sequence, [0, 582, 1164], zero_fingers=True)
    assert vertices.shape == (18056, 3) and joints.shape == (78, 3) and faces.shape == (36108, 3)
    assert moving.shape == (3, 18056, 3) and moving_joints.shape == (3, 78, 3)
    assert all(np.isfinite(v).all() for v in (vertices, joints, moving, moving_joints))
    np.testing.assert_array_equal(faces, moving_faces)
    public = list(template['joint_short_names'])
    assert len(set(public)) == 78 and len(set(sequence['joint_names'])) == len(sequence['joint_names'])
    assert set(public) == set(sequence['joint_names']) and public.count('Hips') == 1
    np.savez_compressed(out / 'source_preflight.npz', vertices=vertices, joints=joints, faces=faces,
                        joint_names=np.asarray(public), selected_frame_ids=np.asarray([0, 582, 1164]),
                        moving_vertices=moving, moving_joints=moving_joints)
    write(out / 'native_source.json', {
        'source_format': sequence['source_format'], 'soma_template_name': sequence['soma_template_name'],
        'source_original': str(SOURCE), 'source_data': str(motion), 'source_sha256': SOURCE_SHA256,
        'soma_shape_params_path': str(fit), 'soma_fit_original': str(FIT), 'fit_sha256': FIT_SHA256,
        'soma_assets_path': str(ASSETS), 'soma_lod': 'mid', 'vertices': len(vertices), 'faces': len(faces),
        'faces_sha256_int32': hashlib.sha256(faces.astype(np.int32).tobytes()).hexdigest(),
        'joint_names': public, 'frames': 1165, 'fps': sequence['fps'], 'frame_ids': {'start': 0, 'stop': 1165, 'step': 1},
        'motion_conversion': 'None; native fitted SOMALayer with BVH poses, shared MHR identity and scale, no pose correctives',
        'coordinate_contract': 'BVH cm and degree Euler; SOMA metres Y-up; solve [z,x,y] Z-up; qpos XYZ metres and wxyz',
        'preflight_motion_frames': [0, 582, 1164], 'exact_template_motion_face_order': True,
        'all_public_joints_mapped_by_unique_name': True,
    })
    shutil.copytree(CHECKOUT / 'assets/g1', out / 'assets/g1')
    config = json.loads((CHECKOUT / 'robot_configs/humanoid_retarget_unitree_g1_example.json').read_text())
    config['robot']['xml'] = str(out / 'assets/g1/g1_29dof.xml')
    config.update({
        'smpl_template': {'source': 'motion', 'type': 'soma', 'name': 'auto', 'use_gender': False},
        'motion': {'data': str(motion), 'seq_key': SOURCE.stem},
        'correspondence': {'dataset': {'out': str(out / 'dataset.npz'), 'smpl_models': []},
                           'train': {'out_dir': str(out / 'train'), 'device': 'cuda', 'seed': 0}},
        'retarget': {'out': str(out / 'motion.npz')}, 'view': {'enabled': False}})
    write(out / 'config.json', config)
    resolved = pipeline.load_pipeline_config(out / 'config.json', CHECKOUT / 'humanoid_retarget_defaults_bones_seed.json')
    assert pipeline.smpl_template_config(resolved)['name'] == 'soma_uniform'
    assert resolved['correspondence']['dataset']['num_points'] == 4096
    assert resolved['correspondence']['train']['epochs'] == 500
    write(out / 'resolved.json', {k: v for k, v in resolved.items() if not k.startswith('_')})
    inputs = collect_inputs()
    inputs.update({str(motion): digest(motion), str(fit): digest(fit)})
    for script in ('run.py', 'prepare.py', 'validate.py'):
        p = Path(__file__).parent / script
        shutil.copyfile(p, out / 'code' / script)
        inputs[str(out / 'code' / script)] = digest(p)
    write(out / 'provenance.json', {
        'cohort': 'native-fitted-BONES-SEED-uniform-to-official-G1-prototype', 'official_fitted_bones_seed': True,
        'umr_revision': PIN, 'external_status_before': git('status', '--porcelain'),
        'source': str(SOURCE), 'fit': str(FIT), 'source_format': sequence['source_format'],
        'inputs_sha256': inputs, 'asset_overlay': str(ASSETS),
        'soma_model_revision': 'f81a01796f652260ff930d5318d6c6b845a505ed',
        'python': sys.version, 'executable': sys.executable,
        'packages': sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
        'native_defaults': str(CHECKOUT / 'humanoid_retarget_defaults_bones_seed.json'),
        'baseline_comparison': str(ROOT / 'outputs/umr-baseline-g1-somax-20261102'),
        'differences_from_generic_control': ['recognized run-local family layout', 'verified shared fitted surface and motion reconstruction', 'fresh independently learned correspondence'],
        'licenses': 'Existing authorized local inputs only; BONES-SEED dataset, NVIDIA SOMA-X/model, Kimodo fit and bundled G1 terms remain separate; no redistribution of data/weights in tracked experiment',
    })
