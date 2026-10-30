"""Stage-specific numerical acceptance, used only inside the pinned native runtime."""
from pathlib import Path


def _pair(data, config, pipeline, field):
    import numpy as np
    names = data['names'].astype(str).tolist()
    expected = [pipeline.expected_smpl_slot_name(config), config['robot'].get('slot_name', config['robot']['name'])]
    if len(names) != 2 or len(set(names)) != 2 or set(names) != set(expected):
        raise ValueError(f'Expected exactly human/robot names {expected}, got {names}')
    points = data[field]
    if points.shape != (2,4096,3) or not np.isfinite(points).all():
        raise ValueError('Expected finite paired 4096-slot point clouds')
    return names, [names.index(n) for n in expected]


def validate_dataset(path, config, pipeline):
    import numpy as np
    with np.load(path, allow_pickle=True) as data:
        names, indices = _pair(data, config, pipeline, 'points')
        for index in indices:
            v, f = data[f'mesh_vertices_{index}'], data[f'mesh_faces_{index}']
            if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all() or f.ndim != 2 or f.shape[1] != 3:
                raise ValueError('Malformed reference mesh')
            if not len(f) or f.min() < 0 or f.max() >= len(v):
                raise ValueError('Reference mesh face indices out of range')
            face_ids = data[f'sample_face_ids_{index}']
            if face_ids.shape != (4096,) or face_ids.min() < 0 or face_ids.max() >= len(f):
                raise ValueError('Invalid sampled face IDs')
        if int(data['seed']) != config['correspondence']['dataset']['seed']:
            raise ValueError('Sampling seed disagrees')
        if str(data['custom_robot_xml']) != config['robot']['xml']:
            raise ValueError('Unexpected sampled robot model')
        human = indices[0]
        if data[f'mesh_vertices_{human}'].shape != (10475,3) or data[f'mesh_faces_{human}'].shape != (20908,3):
            raise ValueError('Only native SMPL-X topology is accepted')
    return {'names': names, 'points_shape': [2,4096,3], 'units': 'metres',
            'coordinates': 'SMPL Y-up; robot sampled in selected centered reference pose',
            'effective_seeds': {'human': config['correspondence']['dataset']['seed']+1000,
                                'robot': config['correspondence']['dataset']['seed']+9000}}, ['dataset.npz']


def validate_training(path, config, pipeline):
    import numpy as np
    import torch
    with np.load(path, allow_pickle=True) as data:
        names, _ = _pair(data, config, pipeline, 'reconstructed_slots')
        np.testing.assert_array_equal(data['slot_index'], np.arange(4096))
        if str(data['training_mode']) != 'all_samples':
            raise ValueError('Unexpected training mode')
        for key in ('normalization_scales', 'normalization_centers', 'template_points'):
            if not np.isfinite(data[key]).all():
                raise ValueError(f'Nonfinite {key}')
        if (data['normalization_scales'] <= 0).any():
            raise ValueError('Normalization scales must be positive')
        np.testing.assert_array_equal(np.sort(data['template_sort_index']), np.arange(4096))
        edges = data['template_edge_index']
        if edges.size and (edges.min() < 0 or edges.max() >= 4096):
            raise ValueError('Template edges out of range')
    checkpoint = Path(path).parent / 'checkpoint-final.pt'
    if not checkpoint.is_file() or checkpoint.stat().st_size == 0:
        raise ValueError('Missing final checkpoint')
    # This is a trusted, freshly generated checkpoint, never imported user pickle.
    saved = torch.load(checkpoint, map_location='cpu', weights_only=False)
    if saved['epoch'] != config['correspondence']['train']['epochs']:
        raise ValueError('Checkpoint epoch disagrees with requested training')
    if saved['args']['seed'] != 0 or saved['training_mode'] != 'all_samples':
        raise ValueError('Training seed/mode disagrees')
    return {'names': names, 'slots_shape': [2,4096,3], 'epochs': saved['epoch'],
            'training_seed': 0, 'training_mode': 'all_samples'}, ['train/checkpoint-final.pt', 'train/correspondence_slots_final.npz']


def validate_motion(path, config, request):
    import mujoco
    import numpy as np
    model = mujoco.MjModel.from_xml_path(config['robot']['xml'])
    motion = request['inputs']['motion']
    with np.load(path, allow_pickle=True) as data:
        qpos, ids = data['qpos'], data['frame_ids']
        if qpos.shape != (motion['frame_count'], model.nq) or not np.isfinite(qpos).all():
            raise ValueError('Invalid motion qpos or lost source frames')
        np.testing.assert_array_equal(ids, np.arange(motion['frame_count']))
        if abs(float(data['fps']) - motion['fps']) > 1e-6:
            raise ValueError('Output FPS disagrees with original')
        names = [model.joint(i).name for i in range(model.njnt) if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
        if data['robot_joint_names'].astype(str).tolist() != names:
            raise ValueError('Robot joint order disagrees')
        if Path(str(data['robot_xml'])).resolve() != Path(config['robot']['xml']).resolve():
            raise ValueError('Output model is not the captured derived model')
        if Path(str(data['source_data'])).resolve() != Path(request['inputs']['motion_file']).resolve():
            raise ValueError('Output source is not managed normalized motion')
        norm_error = float(np.abs(np.linalg.norm(qpos[:,3:7], axis=1)-1).max())
        if norm_error > 1e-6:
            raise ValueError(f'Quaternion error {norm_error} exceeds 1e-6')
        excess = 0.
        for joint in request['inputs']['robot']['joints']:
            lo, hi = joint['minimum_rad'], joint['maximum_rad']
            overrides = config['robot'].get('joint_limits', {}).get(joint['name'])
            if overrides:
                lo, hi = max(lo, float(overrides[0])), min(hi, float(overrides[1]))
            values = qpos[:,joint['qpos_index']]
            excess = max(excess, float(np.max(lo-values)), float(np.max(values-hi)))
        if excess > 1e-6:
            raise ValueError(f'Joint limit excess {excess} exceeds 1e-6 rad')
        if not np.isfinite(float(data['smpl_scale'].reshape(-1)[0])) or float(data['smpl_scale'].reshape(-1)[0]) <= 0:
            raise ValueError('Invalid human scale')
        ground_key = 'ground_height' if 'ground_height' in data else 'ground_z'
        if ground_key in data and not np.isfinite(data[ground_key]).all():
            raise ValueError('Invalid ground height')
    return {'frames': motion['frame_count'], 'fps': motion['fps'], 'all_source_frames_preserved': True,
            'qpos_shape': list(qpos.shape), 'quaternion_norm_max_error': norm_error,
            'joint_limit_max_excess_rad': excess, 'robot_joint_names': names,
            'units': 'metres/radians', 'robot_axes': 'Z-up', 'root_quaternion': 'wxyz',
            'reconstruction': motion['reconstruction'],
            'limitations': ['No dynamics/contact/collision feasibility certification']}, ['motion.npz']
