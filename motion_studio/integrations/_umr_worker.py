"""Private UMR runtime adapter. Invoked only through reproduce_g1_baseline."""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
import shutil
import sys


def _write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def _prepare(checkout, output, model_dir, pipeline):
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; baseline requires host GPU access')
    # UMR emits a floating-root XML beside its input XML. Give it a private copy.
    shutil.copytree(checkout / 'assets/g1', output / 'assets/g1')
    config = json.loads((checkout / 'robot_configs/humanoid_retarget_unitree_g1_example.json').read_text())
    config['robot']['xml'] = str(output / 'assets/g1/g1_29dof.xml')
    config.update({
        'smplx_model_dir': str(model_dir),
        'motion': {'data': str(checkout / 'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'),
                   'seq_key': 'motion_actor_smplx'},
        'correspondence': {
            'dataset': {'out': str(output / 'dataset.npz'),
                        'smpl_models': [{'type': 'smplx', 'dir': str(model_dir), 'genders': ['neutral']}]},
            'train': {'out_dir': str(output / 'train'), 'device': 'cuda', 'seed': 0}},
        'retarget': {'out': str(output / 'motion.npz'), 'smplx_batch_size': 128},
        'view': {'enabled': False},
    })
    _write(output / 'config.json', config)
    resolved = pipeline.load_pipeline_config(output / 'config.json', checkout / 'humanoid_retarget_defaults.json')
    defaults = json.loads((checkout / 'humanoid_retarget_defaults.json').read_text())
    if resolved['solver'] != defaults['solver']:
        raise ValueError('Solver defaults changed')
    for key, value in defaults['correspondence']['train'].items():
        if key != 'device' and resolved['correspondence']['train'][key] != value:
            raise ValueError(f'Training default changed: {key}')
    for key, value in defaults['correspondence']['dataset'].items():
        if key != 'smpl_models' and resolved['correspondence']['dataset'][key] != value:
            raise ValueError(f'Dataset default changed: {key}')
    _write(output / 'resolved.json', {k: v for k, v in resolved.items() if not k.startswith('_')})
    _write(output / 'environment.json', {
        'python': sys.version, 'gpu': torch.cuda.get_device_name(0),
        'packages': sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
    })


def _validate(checkout, output, pipeline):
    import mujoco
    import numpy as np
    import retarget_smpl_to_humanoid_surface_vector as robot_module
    config = pipeline.load_pipeline_config(output / 'config.json', checkout / 'humanoid_retarget_defaults.json')
    if not pipeline.correspondence_dataset_compatible(output / 'dataset.npz', config):
        raise ValueError('Incompatible correspondence dataset')
    slot_path = output / 'train/correspondence_slots_final.npz'
    if not pipeline.correspondence_slots_compatible(slot_path, config):
        raise ValueError('Incompatible correspondence slots')
    with np.load(slot_path, allow_pickle=True) as slots:
        learned = slots['reconstructed_slots']
        if learned.shape != (2, 4096, 3) or not np.isfinite(learned).all():
            raise ValueError('Invalid learned slots')
        if str(slots['training_mode']) != 'all_samples':
            raise ValueError('Unexpected training mode')
    with np.load(output / 'motion.npz', allow_pickle=True) as result:
        qpos = result['qpos']
        ids = result['frame_ids']
        fps = float(result['fps'])
        robot = mujoco.MjModel.from_xml_path(str(result['robot_xml']))
        names = result['robot_joint_names'].tolist()
        if not np.isfinite(qpos).all() or qpos.ndim != 2 or qpos.shape[1] != robot.nq:
            raise ValueError('Invalid motion qpos')
        _, sequence = pipeline._motion_sequence_for_template(config)
        frame_count = len(sequence['pose_aa'])
        source_fps = float(sequence['fps'])
        np.testing.assert_array_equal(ids, np.arange(frame_count))
        if abs(fps - source_fps) > 1e-6:
            raise ValueError('Frame rate changed')
        norm_error = float(np.max(np.abs(np.linalg.norm(qpos[:, 3:7], axis=1) - 1)))
        if norm_error > 1e-6:
            raise ValueError('Invalid free-root wxyz quaternions')
        excess = 0.0
        overrides = config['robot']['joint_limits']
        for j in range(robot.njnt):
            if robot.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
                continue
            name = robot.joint(j).name
            lower, upper = robot.jnt_range[j] if robot.jnt_limited[j] else (-np.inf, np.inf)
            if name in overrides:
                lo, hi = map(float, overrides[name])
                lower, upper = max(lower, lo), min(upper, hi)
            values = qpos[:, robot.jnt_qposadr[j]]
            excess = max(excess, float(np.max(lower - values)), float(np.max(values - upper)))
        if excess > 1e-6:
            raise ValueError(f'Joint limit excess: {excess}')
        # Independent geometry consistency check using the saved static dataset.
        data = mujoco.MjData(robot)
        import build_correspondence_ae_dataset as build
        build.apply_joint_qpos(robot, data, config['robot']['tpose_qpos'], required=True)
        mujoco.mj_forward(robot, data)
        vertices, faces, *_ = robot_module.collect_root_mesh(
            robot, data, robot_module.visual_geom_ids(robot, 'auto'), config['robot']['point_cloud_center'])
        with np.load(output / 'dataset.npz', allow_pickle=True) as dataset:
            np.testing.assert_array_equal(faces, dataset['mesh_faces_1'])
            np.testing.assert_allclose(vertices @ robot_module.SMPL_TO_ROBOT_ROOT_MATRIX,
                                       dataset['mesh_vertices_1'], atol=2e-7, rtol=0)
        steps = np.abs(np.diff(qpos[:, 7:], axis=0))
        _write(output / 'validation.json', {
            'frames': frame_count, 'fps': fps, 'duration_seconds': frame_count / fps,
            'qpos_shape': list(qpos.shape), 'robot_joint_names': names,
            'all_source_frames_preserved': True, 'official_dataset_and_slots_compatible': True,
            'static_geometry_matches_within_200nm': True, 'finite_motion': True,
            'quaternion_norm_max_error': norm_error, 'joint_limit_max_excess_rad': excess,
            'joint_step_p95_rad_per_frame': float(np.percentile(steps, 95)),
            'joint_step_max_rad_per_frame': float(steps.max()),
            'conventions': {'units': 'metres/radians', 'source_axes': 'Y-up',
                            'robot_axes': 'Z-up', 'root_quaternion': 'wxyz',
                            'joint_order': 'robot_joint_names; free-root first 7 qpos'},
            'limitations': ['Single clip and seed', 'No visual review performed',
                            'No independent floor, contact, sliding or collision audit',
                            'No dynamics, controller or hardware validation',
                            'Static anatomical diagnostic is not a motion-quality score'],
        })


if __name__ == '__main__':
    checkout, output, model_dir = map(Path, sys.argv[1:4])
    sys.path.insert(0, str(checkout / 'scripts'))
    import humanoid_retarget_pipeline as pipeline
    if sys.argv[4] == 'prepare':
        _prepare(checkout, output, model_dir, pipeline)
    elif sys.argv[4] == 'validate':
        _validate(checkout, output, pipeline)
    else:
        raise ValueError('Unknown worker action')
