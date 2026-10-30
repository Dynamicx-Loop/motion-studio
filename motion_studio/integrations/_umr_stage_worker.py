"""Private independent-runtime entry point for exactly one explicitly requested stage."""
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n')


def probe():
    import torch
    import hashlib
    sys.path.insert(0, str(Path(sys.argv[2]) / 'scripts'))
    import retarget_body_segment_surface as segments
    _, mapping, segmentation, config = segments.load_smplx_55_to_17_config()
    segmentation = segments.resolve_smplx_55_segmentation_path(segmentation)
    semantics = {'segmentation_sha256': hashlib.sha256(segmentation.read_bytes()).hexdigest(),
                 'map_sha256': hashlib.sha256(config.read_bytes()).hexdigest() if config else
                   hashlib.sha256(mapping.tobytes()).hexdigest(), 'map_source': str(config) if config else 'native built-in mapping',
                 'segmentation_source': str(segmentation)}
    return {'semantics': semantics, 'python': sys.version, 'cuda': torch.cuda.is_available(),
            'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'packages': sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions())}


def dependency_file(request, stage, name):
    receipt = request['dependencies'][stage]
    matches = [p for p in receipt['artifacts'] if p.endswith('/' + name)]
    if len(matches) != 1:
        raise ValueError(f'Missing/ambiguous {stage} dependency {name}')
    home = Path(request['attempt_dir']).parent.parent / stage
    path = home / matches[0]
    import hashlib
    if hashlib.sha256(path.read_bytes()).hexdigest() != receipt['artifacts'][matches[0]]:
        raise ValueError('Dependency bytes changed before worker launch')
    return path


def materialize_pose(model, inputs, output):
    import mujoco
    import numpy as np
    original = mujoco.MjModel.from_xml_path(str(model))
    before = mujoco.MjData(original)
    before.qpos[:] = inputs['pose']['qpos']
    mujoco.mj_forward(original, before)
    tree = ET.parse(model)
    body = tree.getroot().find('./worldbody/body')
    original_root = body.get('name')
    wrapper = inputs['official_g1']
    if wrapper:
        # The pinned G1 has an identity pelvis local transform. Keep native's
        # additional floating-root body/inertia and the user's world-root pose.
        if (not np.allclose(np.fromstring(body.get('pos', '0 0 0'), sep=' '), 0, atol=0, rtol=0)
                or body.get('quat', '1 0 0 0') != '1 0 0 0'):
            raise ValueError('Verified official G1 root transform changed')
        free = body.find('freejoint')
        if free is None:
            raise ValueError('Managed G1 must already record floating-root derivation')
        body.remove(free)
        world = tree.getroot().find('worldbody')
        world.remove(body)
        floating = ET.SubElement(world, 'body', name='unitree_g1_float_root')
        ET.SubElement(floating, 'inertial', pos='0 0 0', mass='0.001', diaginertia='1e-6 1e-6 1e-6')
        ET.SubElement(floating, 'freejoint', name='unitree_g1_float_root_freejoint')
        floating.append(body)
        body = floating
    pose = inputs['pose']['qpos']
    for key in ('euler', 'axisangle', 'xyaxes', 'zaxis'):
        body.attrib.pop(key, None)
    body.set('pos', ' '.join(map(str, pose[:3])))
    body.set('quat', ' '.join(map(str, pose[3:7])))
    tree.write(model)
    derived = mujoco.MjModel.from_xml_path(str(model))
    after = mujoco.MjData(derived)
    after.qpos[:] = pose
    mujoco.mj_forward(derived, after)
    position_error, rotation_error = 0., 0.
    for name in inputs['robot']['bodies']:
        old, new = original.body(name).id, derived.body(name).id
        position_error = max(position_error, float(np.abs(before.xpos[old]-after.xpos[new]).max()))
        rotation_error = max(rotation_error, float(np.abs(before.xmat[old]-after.xmat[new]).max()))
    if position_error > 1e-10 or rotation_error > 1e-10:
        raise ValueError('Derived native root does not preserve the saved world pose')
    write(output / 'model-derivation.json', {
        'official_g1_native_wrapper': wrapper, 'original_root_body': original_root,
        'native_root_body': body.get('name'), 'saved_root_xyz_wxyz': pose[:7],
        'root_pose_mapping': 'identity; official G1 pelvis local transform verified identity',
        'wrapper_inertia': {'mass_kg': .001, 'diagonal_kg_m2': [1e-6]*3} if wrapper else None,
        'all_named_body_world_position_max_error_m': position_error,
        'all_named_body_world_rotation_max_error': rotation_error,
        'world_pose_tolerance': 1e-10})


def configure(checkout, request, pipeline):
    output = Path(request['attempt_dir'])
    inputs, controls = request['inputs'], request['settings']
    if request['stage'] == 'sampling':
        # The managed source closure remains immutable; native children only see this copy.
        for name, path in inputs['robot_files'].items():
            if name.startswith('source/'):
                target = output / 'model' / name.removeprefix('source/')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        model = output / 'model/__studio_model.xml'
        materialize_pose(model, inputs, output)
        config = {}
    else:
        config = json.loads(dependency_file(request, 'sampling', 'humanoid_retarget_runtime_config.json').read_text())
        model = Path(config['robot']['xml'])
    robot = {}
    if inputs['official_g1']:
        robot.update(json.loads((checkout / 'robot_configs/humanoid_retarget_unitree_g1_example.json').read_text())['robot'])
    robot.update({'name': 'unitree_g1' if inputs['official_g1'] else 'studio_robot_' + inputs['robot']['asset_id'][:12],
                  'xml': str(model), 'point_cloud_center': 'body:' + inputs['pose']['torso_body'],
                  'tpose_qpos': {j['name']: inputs['pose']['qpos'][j['qpos_index']] for j in inputs['robot']['joints']},
                  'sample_pose': 'tpose', 'visual_geom_policy': 'auto', 'to_smpl_frame': True,
                  'xml_policy': {'add_freejoint_root': False},
                  'frame_transform': {'smpl_to_robot_root_matrix': [[0,0,1],[1,0,0],[0,1,0]]}})
    if not inputs['official_g1']:
        robot['joint_limits'] = {}
    motion = inputs['motion']
    model_dir = str(Path(motion['model_path']).parent)
    config.update({'robot': robot, 'smplx_model_dir': model_dir,
        'smpl_template': {'source': 'motion', 'type': 'smplx', 'use_betas': True,
                          'use_gender': True, 'name': 'auto'},
        'motion': {'data': inputs['motion_file'], 'seq_key': Path(inputs['motion_file']).stem,
                   'seq_index': 0, 'start': 0, 'end': -1, 'stride': 1, 'max_frames': 0},
        'view': {'enabled': False}})
    config.setdefault('correspondence', {}).update({'reuse_across_smplx_betas': False,
        'shared_config': None, 'shared_smplx_template': None})
    dataset = config['correspondence'].setdefault('dataset', {})
    dataset.update({'out': str(output / 'dataset.npz') if request['stage'] == 'sampling' else
                    str(dependency_file(request, 'sampling', 'dataset.npz')),
                    'seed': controls['sampling_seed'], 'bbox_center_ratio': .45,
                    'smpl_models': [{'type': 'smplx', 'dir': model_dir, 'genders': [motion['gender']]}]})
    train = config['correspondence'].setdefault('train', {})
    train.update({'out_dir': str(output / 'train'), 'epochs': controls['epochs'], 'seed': 0,
                  'device': 'cuda', 'fixed_template': False, 'noise_std': .002,
                  'dropout_ratio': 0., 'resample_every': 0})
    config.setdefault('solver', {})['trajectory_filter_mode'] = 'lqr' if controls['trajectory_filter'] == 'LQR' else 'off'
    config.setdefault('retarget', {}).update({'out': str(output / 'motion.npz'), 'smplx_batch_size': 128,
                                            'stream_chunk_frames': 0})
    if request['stage'] in ('binding', 'retargeting'):
        config['correspondence']['slots'] = str(dependency_file(request, 'training', 'train/correspondence_slots_final.npz'))
    override = output / 'config.json'
    write(override, {k: v for k, v in config.items() if not k.startswith('_')})
    resolved = pipeline.load_pipeline_config(override, checkout / 'humanoid_retarget_defaults.json')
    pipeline.write_runtime_config(resolved, output)
    return resolved


def main(checkout, request_file):
    request = json.loads(request_file.read_text())
    output = Path(request['attempt_dir'])
    sys.path.insert(0, str(checkout / 'scripts'))
    import humanoid_retarget_pipeline as pipeline
    from _umr_stage_validation import validate_dataset, validate_training, validate_motion
    config = configure(checkout, request, pipeline)
    stage = request['stage']
    if stage == 'sampling':
        path = pipeline.build_correspondence_dataset(config, force=True)
        findings, artifacts = validate_dataset(path, config, pipeline)
    elif stage == 'training':
        dataset = dependency_file(request, 'sampling', 'dataset.npz')
        validate_dataset(dataset, config, pipeline)
        path = pipeline.train_correspondence(config, dataset, force=True)
        findings, artifacts = validate_training(path, config, pipeline)
    elif stage == 'binding':
        from _umr_stage_binding import export_binding
        findings, artifacts = export_binding(config, request, output, pipeline, dependency_file)
    elif stage == 'retargeting':
        slots = dependency_file(request, 'training', 'train/correspondence_slots_final.npz')
        validate_training(slots, config, pipeline)
        path = pipeline.retarget_motion(config, slots, force=True)
        findings, artifacts = validate_motion(path, config, request)
    else:
        raise ValueError('Unknown native stage')
    findings.update({'valid': True, 'stage': stage, 'artifacts': artifacts})
    write(output / 'validation.json', findings)
    print(f'STUDIO_STAGE_VALIDATED {stage}', flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'probe':
        print(json.dumps(probe(), allow_nan=False))
    else:
        main(Path(sys.argv[2]), Path(sys.argv[3]))
