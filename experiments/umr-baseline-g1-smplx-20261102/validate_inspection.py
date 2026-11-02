"""Independent native kinematic checks of the saved standalone G1 derivative."""
import argparse
import json
from pathlib import Path
import sys

import mujoco
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--inspection', required=True, type=Path)
    parser.add_argument('--selection', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run, inspection = args.run.resolve(), args.inspection.resolve()
    data = json.loads((inspection / 'bindings.json').read_text())
    selection = json.loads(args.selection.read_text())
    with np.load(run / 'motion.npz', allow_pickle=True) as saved:
        qpos = saved['qpos']
        model = mujoco.MjModel.from_xml_path(str(saved['robot_xml'].item()))
        np.testing.assert_array_equal(saved['frame_ids'], data['motion']['frame_ids'])
        assert float(saved['fps']) == data['motion']['fps'] == data['human_motion']['fps']
        assert len(qpos) == data['human_motion']['frame_count']
        joint_names = saved['robot_joint_names'].tolist()
    assert joint_names == [joint['name'] for joint in selection['asset']['joints']]
    transforms = np.fromfile(inspection / data['motion']['transforms'], dtype='<f4').reshape(
        len(qpos), len(data['motion']['pieces']), 3, 4)
    local = np.array(data['motion']['slot_local'])
    piece = np.array(data['motion']['slot_piece'])
    geom = np.array(data['geom_ids'])
    state = mujoco.MjData(model)
    axis_error = 0.
    # All saved frames and all 4096 bindings, measured against native kinematics.
    for index, pose in enumerate(qpos):
        state.qpos[:] = pose
        mujoco.mj_kinematics(model, state)
        native = (np.einsum('nij,nj->ni', state.geom_xmat[geom].reshape(-1, 3, 3), local)
                  + state.geom_xpos[geom])[:, [1, 2, 0]]
        matrices = transforms[index, piece].astype(np.float64)
        decoded = np.einsum('nij,nj->ni', matrices[:, :, :3], local) + matrices[:, :, 3]
        axis_error = max(axis_error, float(np.max(np.abs(native - decoded))))
    assert axis_error <= 5e-7, axis_error
    builtin = mujoco.MjModel.from_xml_path(selection['managed_model'])
    baseline = mujoco.MjModel.from_xml_path(selection['baseline_model'])
    builtin_state, baseline_state = mujoco.MjData(builtin), mujoco.MjData(baseline)
    builtin_state.qpos[:] = selection['official_pose']['qpos']
    baseline_state.qpos[:] = baseline.qpos0
    config = json.loads((run / 'resolved.json').read_text())
    for name, value in config['robot']['tpose_qpos'].items():
        baseline_state.qpos[baseline.jnt_qposadr[baseline.joint(name).id]] = value
    mujoco.mj_forward(builtin, builtin_state)
    mujoco.mj_forward(baseline, baseline_state)
    errors = []
    for body in selection['asset']['bodies']:
        a, b = builtin.body(body).id, baseline.body(body).id
        errors.extend([float(np.max(np.abs(builtin_state.xpos[a] - baseline_state.xpos[b]))),
                       float(np.max(np.abs(builtin_state.xmat[a] - baseline_state.xmat[b])))])
    assert max(errors) <= 1e-12
    result = {'all_frames': len(qpos), 'all_slots': len(local),
              'all_frame_robot_binding_axis_error_m': axis_error,
              'robot_binding_axis_tolerance_m': 5e-7,
              'human_vertex_axis_error_m': data['human_motion']['max_vertex_axis_error_m'],
              'human_vertex_axis_tolerance_m': 5.1e-5,
              'builtin_native_joint_order_equal': True,
              'builtin_reference_named_body_max_error': max(errors),
              'semantic_schema': data['schema'], 'segment_counts': data['counts'],
              'human_chunks': len(data['human_motion']['chunks']),
              'limitations': ['Human vertex error is the exporter measurement, not a second independent reconstruction.',
                              'Reference transforms and surface replay do not establish contact, collision, dynamics or hardware feasibility.']}
    assert result['human_vertex_axis_error_m'] <= 5.1e-5
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
