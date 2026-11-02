"""Independent saved output gates; no training or retarget solver runs."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CHECKOUT = ROOT / 'externals/UMR'
sys.path.insert(0, str(CHECKOUT / 'scripts'))
import mujoco
import numpy as np
import humanoid_retarget_pipeline as pipeline
import soma_source

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run', type=Path)
args = parser.parse_args()
run = args.run.resolve()
config = pipeline.load_pipeline_config(run / 'config.json', CHECKOUT / 'humanoid_retarget_defaults_bones_seed.json')
assert pipeline.correspondence_dataset_compatible(run / 'dataset.npz', config)
assert pipeline.correspondence_slots_compatible(run / 'train/correspondence_slots_final.npz', config)
with np.load(run / 'train/correspondence_slots_final.npz', allow_pickle=True) as saved:
    assert saved['reconstructed_slots'].shape == (2, 4096, 3)
    assert np.isfinite(saved['reconstructed_slots']).all()
    assert str(saved['training_mode']) == 'all_samples'
with np.load(run / 'motion.npz', allow_pickle=True) as saved:
    qpos, frame_ids, fps = saved['qpos'], saved['frame_ids'], float(saved['fps'].item())
    sequence = soma_source.load_soma_bvh_motion(str(saved['source_data']))
    assert sequence['source_format'] == 'soma_bvh'
    np.testing.assert_array_equal(frame_ids, np.arange(sequence['num_frames']))
    assert abs(fps-sequence['fps']) <= 1e-5
    robot = mujoco.MjModel.from_xml_path(str(saved['robot_xml']))
    assert qpos.shape == (sequence['num_frames'], robot.nq) and np.isfinite(qpos).all()
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
    result = {'cohort': 'generic-neutral-direct-SOMA-control', 'official_fitted_bones_seed': False,
        'frames': len(qpos), 'fps': fps, 'source_loader_fps': sequence['fps'], 'native_fps_serialization_absolute_error': abs(fps-sequence['fps']), 'duration_seconds': len(qpos)/fps,
        'qpos_shape': list(qpos.shape), 'robot_joint_names': names,
        'all_source_frames_preserved': True, 'finite_motion': True,
        'official_dataset_and_slots_compatible': True, 'root_quaternion': 'wxyz',
        'quaternion_norm_max_error': norm_error, 'joint_limit_max_excess_rad': excess,
        'joint_step_p95_rad_per_frame': float(np.percentile(steps,95)), 'joint_step_max_rad_per_frame': float(steps.max()),
        'source_scale': float(saved['smpl_scale']), 'ground_z': float(saved['ground_z']),
        'zero_source_finger_pose': bool(saved['zero_source_finger_pose']),
        'limitations': ['Neutral generic surface; uniform fitted BONES-SEED shape unavailable',
            'Single clip and seed; different action from SMPL-X control', 'No controller, dynamics or hardware validation']}
with (run / 'validation.json').open('x') as stream:
    json.dump(result, stream, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps(result, indent=2))
