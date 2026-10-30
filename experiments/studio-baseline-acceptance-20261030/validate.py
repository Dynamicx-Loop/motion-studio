"""Independent native replay gates for an explicitly supplied fresh HTTP cohort.

Run with the pinned UMR interpreter; reads saved results and licensed weights.
Writes a new small numeric report beneath the supplied canonical evidence root.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
import torch

FRAMES = [0, 63, 64, 1800, 2303, 5467]


def validate(root):
    receipts = json.loads((root / 'receipts.json').read_text())
    exports = json.loads((root / 'exports.json').read_text())
    bundle = Path(next(item['path'] for item in exports if item['stage'] == 'retargeting'))
    data = json.loads((bundle / 'bindings.json').read_text())
    receipt = receipts['retargeting']
    native = bundle / 'native/retargeting' / receipt['attempt_id']
    config = json.loads((native / 'humanoid_retarget_runtime_config.json').read_text())
    with np.load(native / 'motion.npz', allow_pickle=True) as saved:
        arrays = {name: saved[name] for name in saved.files}
    qpos, frame_ids = arrays['qpos'], arrays['frame_ids']
    model = mujoco.MjModel.from_xml_path(str(arrays['robot_xml'].item()))
    assert qpos.shape == (5468, model.nq) and np.isfinite(qpos).all()
    np.testing.assert_array_equal(frame_ids, np.arange(5468))
    fps_error = abs(float(arrays['fps']) - receipt['inputs']['motion']['fps'])
    quat_error = float(abs(np.linalg.norm(qpos[:, 3:7], axis=1) - 1).max())
    assert fps_error <= 1e-6 and quat_error <= 1e-6
    excess = 0.
    for joint in receipt['inputs']['robot']['joints']:
        lo, hi = joint['minimum_rad'], joint['maximum_rad']
        bounds = config['robot'].get('joint_limits', {}).get(joint['name'])
        if bounds:
            lo, hi = max(lo, float(bounds[0])), min(hi, float(bounds[1]))
        values = qpos[:, joint['qpos_index']]
        excess = max(excess, float(np.maximum(lo - values, values - hi).max()))
    assert excess <= 1e-6
    names = [model.joint(i).name for i in range(model.njnt)
             if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
    assert names == arrays['robot_joint_names'].tolist()
    meta = data['motion']
    np.testing.assert_array_equal(meta['frame_ids'], frame_ids)
    assert abs(meta['fps'] - float(arrays['fps'])) <= 1e-6
    transforms = np.fromfile(bundle / meta['transforms'], dtype=meta.get('transform_dtype', '<f4')).reshape(5468, -1, 3, 4)
    local, piece = np.asarray(meta['slot_local']), np.asarray(meta['slot_piece'])
    state = mujoco.MjData(model)
    report = {'frames': 5468, 'qpos_shape': list(qpos.shape), 'fps': float(arrays['fps']),
              'fps_error': fps_error, 'quaternion_max_error': quat_error,
              'joint_limit_max_excess_rad': excess, 'checked_frames': FRAMES, 'replay': []}
    sys.path.insert(0, '/data/workspace/motion_studio/externals/UMR/scripts')
    import smpl_surface_retarget_common as common
    import retarget_smpl_to_humanoid_surface_vector as robot
    # Independently reconstruct the local target meshes from the compiled model.
    vertices = np.fromfile(bundle / meta['vertices'], dtype='<f4').reshape(-1, 3)
    faces = np.fromfile(bundle / meta['faces'], dtype='<u4').reshape(-1, 3)
    max_mesh_error = 0.
    for part in meta['pieces']:
        v, f = robot.geom_local_mesh(model, part['geom_id'])
        start, count = part['vertex_start'], part['vertex_count']
        max_mesh_error = max(max_mesh_error, float(abs(vertices[start:start+count] - v).max()))
        np.testing.assert_allclose(vertices[start:start+count], v, atol=2e-7, rtol=0)
        start_f, count_f = part['face_start'], part['face_count']
        np.testing.assert_array_equal(faces[start_f:start_f+count_f], f + start)
    report['target_mesh_max_axis_error_m'] = max_mesh_error
    reference = mujoco.MjData(model)
    for name, value in config['robot']['tpose_qpos'].items():
        reference.qpos[model.joint(name).qposadr[0]] = value
    mujoco.mj_forward(model, reference)
    static_v, static_f, *_ = robot.collect_root_mesh(model, reference,
        robot.visual_geom_ids(model, config['robot']['visual_geom_policy']),
        config['robot']['point_cloud_center'])
    matrix = np.asarray(config['robot']['frame_transform']['smpl_to_robot_root_matrix'])
    static_expected = static_v @ matrix
    static_meta = data['geometry']['robot']
    static_saved = np.fromfile(bundle / static_meta['vertices'], dtype='<f4').reshape(-1, 3)
    static_faces = np.fromfile(bundle / static_meta['faces'], dtype='<u4').reshape(-1, 3)
    np.testing.assert_allclose(static_saved, static_expected, atol=2e-7, rtol=0)
    np.testing.assert_array_equal(static_faces, static_f)
    report['static_target_reference_max_axis_error_m'] = float(abs(static_saved - static_expected).max())
    torch.set_num_threads(2)
    collection, _ = common.load_motion_collection(Path(receipt['inputs']['motion_file']))
    _, sequence = common.select_sequence(collection, str(arrays['source_sequence_key'].item()), 0)
    human = data['human_motion']
    bary, slot_vertices = np.asarray(human['slot_bary']), np.asarray(human['slot_vertices'])
    model_file = Path(config['smplx_model_dir'])
    assert model_file.is_file() and str(model_file) == receipt['inputs']['motion']['model_path']
    assert hashlib.sha256(model_file.read_bytes()).hexdigest() == receipt['inputs']['motion']['model_sha256']
    native_vertices, _, _ = common.source_motion_vertices_joints(sequence, np.asarray(FRAMES), model_file,
        batch_size=32, smplx_device='cpu', smplx_batch_size=32, zero_source_finger_pose=True)
    native_vertices = common.source_points_to_retarget_frame(native_vertices, 'smplx', sequence.get('output_up', 'z'))
    native_vertices[:, :, 2] -= float(arrays['ground_z'])
    native_vertices = (native_vertices * float(arrays['smpl_scale']))[:, :, [1, 2, 0]]
    for index, frame in enumerate(FRAMES):
        state.qpos[:] = qpos[frame]
        mujoco.mj_forward(model, state)
        actual = np.einsum('nij,nj->ni', transforms[frame, piece, :, :3], local) + transforms[frame, piece, :, 3]
        expected = np.empty_like(local)
        for i, part in enumerate(meta['pieces']):
            mask = piece == i
            gid = part['geom_id']
            expected[mask] = (local[mask] @ state.geom_xmat[gid].reshape(3, 3).T + state.geom_xpos[gid])[:, [1, 2, 0]]
        robot_error = float(abs(actual - expected).max())
        assert robot_error <= 5e-7
        chunk = next(c for c in human['chunks'] if c['start'] <= frame < c['start'] + c['count'])
        codes = np.memmap(bundle / chunk['file'], dtype='<i2', mode='r',
                          shape=(chunk['count'], human['vertex_count'], 3))
        decoded = codes[frame - chunk['start']].astype(float) * human['quantization_m'] + human['root_positions'][frame]
        human_error = float(abs(decoded - native_vertices[index]).max())
        slots = (decoded[slot_vertices] * bary[:, :, None]).sum(axis=1)
        reference = (native_vertices[index, slot_vertices] * bary[:, :, None]).sum(axis=1)
        slot_error = float(abs(slots - reference).max())
        assert human_error <= 5.1e-5 and slot_error <= 5.1e-5
        report['replay'].append(dict(frame=frame, robot_binding_axis_error_m=robot_error,
            human_vertex_axis_error_m=human_error, human_binding_axis_error_m=slot_error))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.evidence)
    with (args.evidence / 'independent-numeric-gates.json').open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))
