"""Pre-solve static source/rigid target binding from native scientific functions."""
import json
from types import SimpleNamespace


def export_binding(config, request, output, pipeline, dependency_file):
    import mujoco
    import numpy as np
    import build_correspondence_ae_dataset as build
    import retarget_body_segment_surface as segments
    import retarget_smpl_to_humanoid_surface_vector as robot
    import smpl_surface_retarget_common as common
    from _umr_stage_validation import validate_dataset, validate_training
    dataset = dependency_file(request, 'sampling', 'dataset.npz')
    slots = dependency_file(request, 'training', 'train/correspondence_slots_final.npz')
    validate_dataset(dataset, config, pipeline)
    validate_training(slots, config, pipeline)
    human_name = pipeline.expected_smpl_slot_name(config)
    robot_name = config['robot'].get('slot_name', config['robot']['name'])
    with np.load(dataset, allow_pickle=True) as data:
        names = data['names'].astype(str).tolist()
        h, r = names.index(human_name), names.index(robot_name)
        human_vertices, human_faces = data[f'mesh_vertices_{h}'], data[f'mesh_faces_{h}']
        target_vertices, target_faces = data[f'mesh_vertices_{r}'], data[f'mesh_faces_{r}']
    human, *_ = common.load_slot_data(slots, human_name, 'reconstructed_slots')
    target, *_ = common.load_slot_data(slots, robot_name, 'reconstructed_slots')
    segments.configure_body_segment_surface(config)
    k = int(config['solver']['bind_nearest_vertex_k'])
    source = common.bind_points_to_mesh(human, human_vertices, human_faces, nearest_vertex_k=k)
    parts = segments.smplx_slot_part_ids_from_binding(human_faces, source['face_ids'],
        template_vertices=human_vertices, bary=source['bary'], slot_points=source['closest_points'])
    labels = [segments.BODY_SEGMENT_PART_NAMES[int(part)] for part in parts]
    model = mujoco.MjModel.from_xml_path(config['robot']['xml'])
    state = mujoco.MjData(model)
    build.apply_joint_qpos(model, state, config['robot']['tpose_qpos'], required=True)
    mujoco.mj_forward(model, state)
    vertices, faces, _, center_pos, center_rot, _ = robot.collect_root_mesh(model, state,
        robot.visual_geom_ids(model, config['robot']['visual_geom_policy']), config['robot']['point_cloud_center'])
    matrix = np.asarray(config['robot']['frame_transform']['smpl_to_robot_root_matrix'])
    np.testing.assert_array_equal(faces, target_faces)
    np.testing.assert_allclose(vertices @ matrix, target_vertices, atol=2e-7, rtol=0)
    binding = robot.bind_robot_slots(model, SimpleNamespace(config_data=config), target,
        nearest_vertex_k=k, project_to_surface=True, source_model_type='smplx')
    gids = binding['geom_ids']
    if gids.shape != (4096,) or gids.min() < 0 or gids.max() >= model.ngeom:
        raise ValueError('Invalid target binding geom IDs')
    for key in ('local_pos', 'local_normals', 'root_points'):
        if binding[key].shape != (4096,3) or not np.isfinite(binding[key]).all():
            raise ValueError(f'Invalid target binding {key}')
    bary = source['bary']
    if bary.shape != (4096,3) or not np.isfinite(bary).all() or bary.min() < -1e-6 or bary.max() > 1+1e-6:
        raise ValueError('Invalid source barycentric binding')
    np.testing.assert_allclose(bary.sum(axis=1), 1, atol=1e-6, rtol=0)
    expected = (human_vertices[human_faces[source['face_ids']]] * bary[:,:,None]).sum(axis=1)
    # Native's tiny-triangle barycentric fallback can select vertex0 while its
    # nearest-point diagnostic remains on an edge. Replay/solver uses bary, so
    # publish that representation and preserve the raw nearest diagnostic too.
    bary_error = np.abs(expected-source['closest_points']).max(axis=1)
    if not np.isfinite(expected).all():
        raise ValueError('Nonfinite source barycentric reconstruction')
    replay = np.empty_like(binding['root_points'])
    for gid in np.unique(gids):
        mask = gids == gid
        world = binding['local_pos'][mask] @ state.geom_xmat[int(gid)].reshape(3,3).T + state.geom_xpos[int(gid)]
        replay[mask] = (world-center_pos) @ center_rot
    np.testing.assert_allclose(replay, binding['root_points'], atol=5e-7, rtol=0)
    projected = binding['root_points'] @ matrix
    distances = np.linalg.norm(target-projected, axis=1)
    if not np.isfinite(distances).all():
        raise ValueError('Nonfinite projection error')
    np.savez_compressed(output / 'binding.npz', slot_index=np.arange(4096,dtype=np.int32),
        source_face_ids=source['face_ids'], source_bary=bary, source_points=expected,
        source_native_closest_points=source['closest_points'], source_native_projection_m=source['errors'],
        source_barycentric_vs_native_closest_axis_error_m=bary_error,
        source_normals=source['closest_normals'], source_part_ids=parts,
        target_geom_ids=gids, target_local_pos=binding['local_pos'], target_local_normals=binding['local_normals'],
        target_root_points=binding['root_points'], target_projected_smpl=projected, projection_m=distances)
    geometry = {}
    artifacts = ['binding.npz', 'bindings.json']
    for name, v, f in [('human',human_vertices,human_faces),('robot',target_vertices,target_faces)]:
        np.asarray(v,dtype='<f4').tofile(output / f'{name}-vertices.bin')
        np.asarray(f,dtype='<u4').tofile(output / f'{name}-faces.bin')
        geometry[name] = {'vertices': f'{name}-vertices.bin', 'faces': f'{name}-faces.bin',
                          'vertex_count': len(v), 'face_count': len(f)}
        artifacts.extend([f'{name}-vertices.bin', f'{name}-faces.bin'])
    mesh_names = [model.mesh(int(model.geom_dataid[int(g)])).name
                  if model.geom_type[int(g)] == mujoco.mjtGeom.mjGEOM_MESH else None for g in gids]
    payload = {'run': request['run_id'], 'schema': segments.BODY_SEGMENT_SCHEMA, 'units': 'metres',
        'coordinates': 'SMPL Y-up; centered static reference meshes',
        'scope': 'Pre-solve binding; source semantic labels differ from target geometry ownership; solver recomputes this native recipe',
        'geometry': geometry, 'slot_index': list(range(4096)), 'source': expected.tolist(),
        'source_native_closest': source['closest_points'].tolist(),
        'source_barycentric_vs_native_closest_axis_error_m': bary_error.tolist(),
        'target': projected.tolist(), 'labels': labels,
        'bodies': [model.body(int(model.geom_bodyid[int(g)])).name for g in gids], 'meshes': mesh_names,
        'geom_ids': gids.tolist(), 'geom_types': [int(model.geom_type[int(g)]) for g in gids],
        'projection_m': distances.tolist(), 'counts': {label: labels.count(label) for label in sorted(set(labels))}}
    (output / 'bindings.json').write_text(json.dumps(payload, allow_nan=False))
    return {'slot_count': 4096, 'schema': segments.BODY_SEGMENT_SCHEMA,
            'source_barycentric_verified': True,
            'source_native_closest_axis_discrepancy_max_m': float(bary_error.max()),
            'source_representation': 'native face+bary replay; nearest diagnostic retained separately', 'target_rigid_replay_axis_tolerance_m': 5e-7,
            'target_reference_axis_tolerance_m': 2e-7, 'motion_required': False}, artifacts
