"""Private CPU inspection adapter. No upstream entry point or motion solver runs."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace


def export_motion(run, output, reference, binding, robot, mujoco, np):
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
    if not xml.is_relative_to(run):
        raise ValueError('Motion XML must be in the preserved run')
    model = mujoco.MjModel.from_xml_path(str(xml))
    if (qpos.ndim != 2 or qpos.shape[1] != model.nq or len(qpos) == 0
            or not np.isfinite(qpos).all() or not np.isfinite(fps) or fps <= 0
            or frame_ids.shape != (len(qpos),) or frame_ids.dtype.kind not in 'iu'
            or not np.all(np.diff(frame_ids) == 1) or not np.isfinite(ground)):
        raise ValueError('Invalid saved motion dimensions, positions or timing')
    actual_names = [model.joint(i).name for i in range(model.njnt)
                    if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
    if joint_names != actual_names:
        raise ValueError('Saved motion joint order differs from its model')
    if model.jnt_type[0] != mujoco.mjtJoint.mjJNT_FREE or model.jnt_qposadr[0] != 0:
        raise ValueError('Expected a leading free root with wxyz quaternion')
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
    transforms = np.empty((len(qpos), len(ids), 3, 4), dtype='<f8')
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
            'transforms': 'motion-transforms.bin', 'transform_schema': 2, 'transform_dtype': '<f8', 'transform_layout': 'frame, geom, row, column; float64 little endian; 3x4 row-major',
            'coordinates': 'geom-local native Z-up to world Y-up [native y, native z, native x]; metres',
            'vertices': 'motion-vertices.bin', 'faces': 'motion-faces.bin',
            'vertex_count': vertex_offset, 'face_count': face_offset, 'pieces': pieces,
            'slot_local': binding['local_pos'].tolist(),
            'slot_piece': [ids.index(int(g)) for g in binding['geom_ids']],
            'display_origin': [float(qpos[0, 1]), ground, float(qpos[0, 0])],
            'root_positions': qpos[:, [1, 2, 0]].tolist(),
            'scope': 'Saved qpos replay; rigid bindings reconstructed in the reference pose, no per-frame rebind or solver telemetry'}


def main(checkout, run, output):
    from human_replay import export_human_motion
    sys.path.insert(0, str(checkout / 'scripts'))
    import mujoco
    import numpy as np
    import build_correspondence_ae_dataset as build
    import humanoid_retarget_pipeline as pipeline
    import retarget_body_segment_surface as segments
    import retarget_smpl_to_humanoid_surface_vector as robot
    import smpl_surface_retarget_common as common

    config = pipeline.load_pipeline_config(run / 'config.json', checkout / 'humanoid_retarget_defaults_bones_seed.json')
    segments.configure_body_segment_surface(config)
    with np.load(run / 'dataset.npz', allow_pickle=True) as data:
        human_vertices, human_faces = data['mesh_vertices_0'], data['mesh_faces_0']
        target_vertices, target_faces = data['mesh_vertices_1'], data['mesh_faces_1']
    with np.load(run / 'train/correspondence_slots_final.npz', allow_pickle=True) as data:
        human, target = data['reconstructed_slots']
    if human.shape != (4096, 3) or target.shape != human.shape or not np.isfinite([human, target]).all():
        raise ValueError('Invalid saved G1 slot arrays')
    k = int(config['solver'].get('bind_nearest_vertex_k', 24))
    source_binding = common.bind_points_to_mesh(human, human_vertices, human_faces, nearest_vertex_k=k)
    part_ids = segments.soma_slot_part_ids_from_smplx_correspondence(
        human_faces, source_binding['face_ids'], len(human_vertices),
        slot_points=source_binding['closest_points'])
    names = [segments.BODY_SEGMENT_PART_NAMES[int(part)] for part in part_ids]
    source_bary = (human_vertices[human_faces[source_binding['face_ids']]] * source_binding['bary'][:, :, None]).sum(axis=1)
    model = mujoco.MjModel.from_xml_path(config['robot']['xml'])
    state = mujoco.MjData(model)
    build.apply_joint_qpos(model, state, config['robot']['tpose_qpos'], required=True)
    mujoco.mj_forward(model, state)
    vertices, faces, *_ = robot.collect_root_mesh(model, state, robot.visual_geom_ids(model, 'auto'), config['robot']['point_cloud_center'])
    np.testing.assert_array_equal(faces, target_faces)
    np.testing.assert_allclose(vertices @ robot.SMPL_TO_ROBOT_ROOT_MATRIX, target_vertices, atol=2e-7, rtol=0)
    binding = robot.bind_robot_slots(model, SimpleNamespace(config_data=config), target,
                                    nearest_vertex_k=k, project_to_surface=True, source_model_type='soma')
    projected = binding['root_points'] @ robot.SMPL_TO_ROBOT_ROOT_MATRIX
    owners = [model.body(int(model.geom_bodyid[int(g)])).name for g in binding['geom_ids']]
    mesh_names = [model.mesh(int(model.geom_dataid[int(g)])).name for g in binding['geom_ids']]
    geometry = {}
    for name, v, f in [('human', human_vertices, human_faces), ('robot', target_vertices, target_faces)]:
        if not np.isfinite(v).all() or f.min() < 0 or f.max() >= len(v):
            raise ValueError('Invalid mesh export')
        np.asarray(v, dtype='<f4').tofile(output / f'{name}-vertices.bin')
        np.asarray(f, dtype='<u4').tofile(output / f'{name}-faces.bin')
        geometry[name] = {'vertices': f'{name}-vertices.bin', 'faces': f'{name}-faces.bin',
                          'vertex_count': len(v), 'face_count': len(f)}
    distances = np.linalg.norm(robot.smpl_frame_to_robot_root(target) - binding['root_points'], axis=1)
    np.savez_compressed(output / 'binding.npz', source_face_ids=source_binding['face_ids'], source_bary=source_binding['bary'], source_points=source_bary, source_part_ids=part_ids, target_geom_ids=binding['geom_ids'], target_local_pos=binding['local_pos'], target_root_points=binding['root_points'], target_projected_smpl=projected, projection_m=distances)
    payload = {'run': run.name + ' — fitted uniform SOMA prototype', 'source_route': 'soma_bvh_boneseed_uniform', 'official_fitted_bones_seed': True, 'schema': segments.BODY_SEGMENT_SCHEMA, 'units': 'metres',
               'coordinates': 'saved SOMA Y-up frame; independent display floor offsets only',
               'scope': 'Reference bindings reconstructed and attached to saved G1 motion; not a saved per-frame solver trace',
               'geometry': geometry, 'source': source_bary.tolist(), 'source_native_closest': source_binding['closest_points'].tolist(),
               'target': projected.tolist(), 'labels': names, 'bodies': owners, 'meshes': mesh_names,
               'geom_ids': binding['geom_ids'].tolist(), 'projection_m': distances.tolist(),
               'counts': {name: names.count(name) for name in sorted(set(names))},
               'motion': export_motion(run, output, model, binding, robot, mujoco, np),
               'human_motion': export_human_motion(run, output, config, source_binding, common, robot, np)}
    (output / 'bindings.json').write_text(json.dumps(payload, allow_nan=False) + '\n')


if __name__ == '__main__':
    main(*map(Path, sys.argv[1:4]))
