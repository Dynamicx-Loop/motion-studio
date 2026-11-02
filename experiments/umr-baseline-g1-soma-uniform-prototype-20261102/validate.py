"""Validate saved native results and fitted reconstruction through its public seam."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from prepare import (ASSETS, CHECKOUT, assert_fitted, digest, environment, fit_path,
                     source_path, write)
sys.path.insert(0, str(CHECKOUT / 'scripts'))


def validate(run):
    import mujoco
    import numpy as np
    import humanoid_retarget_pipeline as pipeline
    import soma_source
    os.environ.update(environment(run))
    config = pipeline.load_pipeline_config(run / 'config.json', CHECKOUT / 'humanoid_retarget_defaults_bones_seed.json')
    assert pipeline.correspondence_dataset_compatible(run / 'dataset.npz', config)
    assert pipeline.correspondence_slots_compatible(run / 'train/correspondence_slots_final.npz', config)
    sequence = soma_source.load_soma_bvh_motion(source_path(run))
    assert_fitted(sequence, fit_path(run))
    source_record = json.loads((run / 'native_source.json').read_text())
    vertices, joints, faces, template = soma_source.soma_template_vertices_joints_faces(sequence=sequence)
    assert hashlib.sha256(faces.astype(np.int32).tobytes()).hexdigest() == source_record['faces_sha256_int32']
    assert list(template['joint_short_names']) == source_record['joint_names']
    # Exercise every input frame with the exact fitted path; bounded memory and identical topology.
    reconstructed = 0
    for start in range(0, sequence['num_frames'], 64):
        ids = np.arange(start, min(start + 64, sequence['num_frames']))
        moving, moving_joints, moving_faces = soma_source.soma_motion_vertices_joints(sequence, ids, zero_fingers=True)
        assert moving.shape == (len(ids), 18056, 3) and moving_joints.shape == (len(ids), 78, 3)
        assert np.isfinite(moving).all() and np.isfinite(moving_joints).all()
        np.testing.assert_array_equal(faces, moving_faces)
        reconstructed += len(ids)
    with np.load(run / 'train/correspondence_slots_final.npz', allow_pickle=True) as saved:
        assert saved['reconstructed_slots'].shape == (2, 4096, 3)
        assert np.isfinite(saved['reconstructed_slots']).all()
        assert str(saved['training_mode']) == 'all_samples'
    with np.load(run / 'motion.npz', allow_pickle=True) as saved:
        qpos, frame_ids, fps = saved['qpos'], saved['frame_ids'], float(saved['fps'].item())
        assert Path(str(saved['source_data'])).resolve() == source_path(run).resolve()
        np.testing.assert_array_equal(frame_ids, np.arange(1165))
        # UMR stores native rate as float32. Budget one float32 ULP, not a decimal equality test.
        fps_tolerance = float(np.spacing(np.float32(sequence['fps'])))
        assert abs(fps - sequence['fps']) <= fps_tolerance
        robot = mujoco.MjModel.from_xml_path(str(saved['robot_xml']))
        assert qpos.shape == (1165, robot.nq) and np.isfinite(qpos).all()
        names = [robot.joint(j).name for j in range(robot.njnt) if robot.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
        assert saved['robot_joint_names'].tolist() == names and len(names) == 29
        norm_error = float(np.abs(np.linalg.norm(qpos[:, 3:7], axis=1)-1).max())
        assert norm_error <= 1e-6
        excess = 0.
        for j in range(robot.njnt):
            if robot.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
                continue
            name = robot.joint(j).name
            lo, hi = robot.jnt_range[j] if robot.jnt_limited[j] else (-np.inf, np.inf)
            if name in config['robot']['joint_limits']:
                a, b = map(float, config['robot']['joint_limits'][name])
                lo, hi = max(a, lo), min(b, hi)
            values = qpos[:, robot.jnt_qposadr[j]]
            excess = max(excess, float((lo-values).max()), float((values-hi).max()))
        assert excess <= 1e-6
        steps = np.abs(np.diff(qpos[:, 7:], axis=0))
        return {'cohort': 'native-fitted-BONES-SEED-uniform-to-official-G1-prototype',
            'official_fitted_bones_seed': True, 'source_format': sequence['source_format'],
            'soma_template_name': sequence['soma_template_name'], 'fit_sha256': digest(fit_path(run)),
            'all_source_motion_frames_reconstructed_finite': reconstructed, 'template_motion_face_order_equal': True,
            'source_topology': [len(vertices), len(faces)], 'source_joint_names': list(template['joint_short_names']),
            'frames': len(qpos), 'fps': fps, 'source_loader_fps': sequence['fps'],
            'native_fps_serialization_absolute_error': abs(fps-sequence['fps']), 'fps_tolerance_one_float32_ulp': fps_tolerance,
            'duration_seconds': len(qpos)/fps, 'qpos_shape': list(qpos.shape), 'robot_joint_names': names,
            'all_source_frames_preserved': True, 'finite_motion': True,
            'official_dataset_and_slots_compatible': True, 'root_quaternion': 'wxyz',
            'quaternion_norm_max_error': norm_error, 'joint_limit_max_excess_rad': excess,
            'joint_step_p95_rad_per_frame': float(np.percentile(steps,95)),
            'joint_step_max_rad_per_frame': float(steps.max()), 'source_scale': float(saved['smpl_scale']),
            'ground_z': float(saved['ground_z']), 'zero_source_finger_pose': bool(saved['zero_source_finger_pose']),
            'limitations': ['Single clip and seed; prototype with native defaults', 'Kinematic validation does not establish fidelity, dynamics or hardware suitability']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    result = validate(args.run.resolve())
    write(args.run.resolve() / 'validation.json', result)
    print(json.dumps(result, indent=2))
