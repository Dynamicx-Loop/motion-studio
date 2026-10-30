"""Private CPU inspection adapter. No upstream entry point or motion solver runs."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace


def export_motion(run, output, reference, binding, robot, mujoco, np, *, expected_xml=None):
    """Store rigid geom poses, not millions of duplicated animated slot points.

    Matrices are row-major 3x4, geom-local Z-up metres to world Y-up metres.
    Frames retain the saved sample order and rate, without interpolation.
    """
    with np.load(run / 'motion.npz', allow_pickle=True) as saved:
        qpos = saved['qpos']
        fps = float(saved['fps'].item())
        frame_ids = saved['frame_ids']
        xml = Path(str(saved['robot_xml'].item())).resolve()
        joint_names = saved['robot_joint_names'].tolist()
        ground = float(saved['ground_z'].item())
    if expected_xml is not None:
        if xml != Path(expected_xml).resolve():
            raise ValueError('Motion XML differs from the exact validated sampling model')
    elif not xml.is_relative_to(run):
        raise ValueError('Motion XML must be in the preserved run')
    model = reference if expected_xml is not None else mujoco.MjModel.from_xml_path(str(xml))
    if (qpos.ndim != 2 or qpos.shape[1] != model.nq or len(qpos) == 0
            or not np.isfinite(qpos).all() or not np.isfinite(fps) or fps <= 0
            or frame_ids.shape != (len(qpos),) or frame_ids.dtype.kind not in 'iu'
            or not np.array_equal(frame_ids, np.arange(len(qpos))) or not np.isfinite(ground)):
        raise ValueError('Invalid saved motion dimensions, positions or timing')
    actual_names = [model.joint(i).name for i in range(model.njnt)
                    if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
    if joint_names != actual_names:
        raise ValueError('Saved motion joint order differs from its model')
    if model.jnt_type[0] != mujoco.mjtJoint.mjJNT_FREE or model.jnt_qposadr[0] != 0:
        raise ValueError('Expected a leading free root with wxyz quaternion')
    if np.max(np.abs(np.linalg.norm(qpos[:, 3:7], axis=1)-1)) > 1e-6:
        raise ValueError('Invalid saved root quaternion norm')
    for joint in range(model.njnt):
        if model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_HINGE and model.jnt_limited[joint]:
            values = qpos[:, model.jnt_qposadr[joint]]
            low, high = model.jnt_range[joint]
            if np.max(np.maximum(low-values, values-high)) > 1e-6:
                raise ValueError('Saved motion exceeds compiled joint limits')
    # Fail closed if the saved floating model changed geometry/order. Geoms can
    # be unnamed, so a name-only remap would silently attach some slots wrongly.
    if model.ngeom != reference.ngeom:
        raise ValueError('Motion and binding geometry differ')
    for field in ('geom_type', 'geom_bodyid', 'geom_dataid', 'geom_pos',
                  'geom_quat', 'geom_size', 'mesh_vert', 'mesh_face',
                  'body_parentid', 'body_pos', 'body_quat', 'jnt_type',
                  'jnt_qposadr', 'jnt_bodyid', 'jnt_pos', 'jnt_axis', 'qpos0'):
        np.testing.assert_array_equal(getattr(model, field), getattr(reference, field))
    if ([model.body(i).name for i in range(model.nbody)] !=
            [reference.body(i).name for i in range(reference.nbody)]):
        raise ValueError('Motion and binding body order differ')
    ids = list(map(int, robot.visual_geom_ids(reference, 'auto')))
    if not set(map(int, binding['geom_ids'])).issubset(ids):
        raise ValueError('Bound slot has no visual geometry')
    if binding['local_pos'].shape != (len(binding['geom_ids']), 3) or not np.isfinite(binding['local_pos']).all():
        raise ValueError('Invalid geometry-local bindings')
    vertices, faces, pieces = [], [], []
    vertex_offset = face_offset = 0
    for geom_id in ids:
        v, f = robot.geom_local_mesh(reference, geom_id)
        vertices.append(v)
        faces.append(np.asarray(f) + vertex_offset)
        pieces.append({'geom_id': geom_id, 'vertex_start': vertex_offset,
                       'vertex_count': len(v), 'face_start': face_offset, 'face_count': len(f)})
        vertex_offset += len(v)
        face_offset += len(f)
    np.asarray(np.concatenate(vertices), dtype='<f4').tofile(output / 'motion-vertices.bin')
    np.asarray(np.concatenate(faces), dtype='<u4').tofile(output / 'motion-faces.bin')
    state = mujoco.MjData(model)
    transforms = np.empty((len(qpos), len(ids), 3, 4), dtype='<f4')
    # World Z-up -> Y-up uses [native y, native z, native x]. Rotation and
    # translation are both converted; local geometry remains in native axes.
    for frame, pose in enumerate(qpos):
        state.qpos[:] = pose
        mujoco.mj_kinematics(model, state)
        transforms[frame, :, :, :3] = state.geom_xmat[ids].reshape(-1, 3, 3)[:, [1, 2, 0], :]
        transforms[frame, :, :, 3] = state.geom_xpos[ids][:, [1, 2, 0]]
    if not np.isfinite(transforms).all():
        raise ValueError('Nonfinite motion transforms')
    transforms.tofile(output / 'motion-transforms.bin')
    return {'frame_count': len(qpos), 'fps': fps, 'frame_ids': frame_ids.tolist(),
            'qpos_width': model.nq, 'joint_names': joint_names, 'root_quaternion': 'wxyz',
            'transforms': 'motion-transforms.bin', 'transform_layout': 'frame, geom, row, column; float32 little endian; 3x4 row-major',
            'coordinates': 'geom-local native Z-up to world Y-up [native y, native z, native x]; metres',
            'vertices': 'motion-vertices.bin', 'faces': 'motion-faces.bin',
            'vertex_count': vertex_offset, 'face_count': face_offset, 'pieces': pieces,
            'slot_local': binding['local_pos'].tolist(),
            'slot_piece': [ids.index(int(g)) for g in binding['geom_ids']],
            'display_origin': [float(qpos[0, 1]), ground, float(qpos[0, 0])],
            'root_positions': qpos[:, [1, 2, 0]].tolist(),
            'scope': 'Saved qpos replay; rigid bindings reconstructed in the reference pose, no per-frame rebind or solver telemetry'}
