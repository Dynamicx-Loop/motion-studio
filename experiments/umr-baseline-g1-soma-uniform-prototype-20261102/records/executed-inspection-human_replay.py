"""Exact fitted SOMA replay and raw BVH skeleton diagnostic; no model fitting."""
import hashlib
from pathlib import Path


def _digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encode_root_relative(vertices, roots, np):
    """Int16 root-relative metres, 0.1 mm steps; reject overflow/nonfinite data."""
    local = vertices - roots[:, None, :]
    codes = np.rint(local / .0001)
    if not np.isfinite(codes).all() or np.abs(codes).max() > 32767:
        raise ValueError('Human mesh cannot be represented safely at 0.1 mm resolution')
    return codes.astype('<i2')


def export_human_motion(run, output, config, binding, common, robot, np):
    import torch
    torch.set_num_threads(2)
    with np.load(run / 'motion.npz', allow_pickle=True) as saved:
        source = Path(str(saved['source_data'].item())).resolve()
        key = str(saved['source_sequence_key'].item())
        frame_ids = saved['frame_ids'].copy()
        scale = float(saved['smpl_scale'].item())
        ground = float(saved['ground_z'].item())
        zero_fingers = bool(saved['zero_source_finger_pose'].item())
        fps = float(saved['fps'].item())
    if not zero_fingers:
        raise ValueError('This fitted SOMA replay supports the saved zero-finger route only')
    collection, _ = common.load_motion_collection(source)
    selected_key, sequence = common.select_sequence(collection, key, 0)
    if (selected_key != key or common.source_model_type(sequence) != 'soma'
            or frame_ids.min() < 0 or frame_ids.max() >= common.sequence_frame_count(sequence)
            or not np.isclose(float(sequence['fps']), fps, atol=1e-5, rtol=0)
            or not np.isfinite(scale) or scale <= 0):
        raise ValueError('Saved source motion and replay frames/rate do not agree')
    model_dir = Path(config['smplx_model_dir']).resolve()
    import soma_source
    if sequence.get('source_format') != 'soma_bvh_boneseed_uniform' or sequence.get('soma_template_name') != 'soma_uniform':
        raise ValueError('Fitted uniform route required; generic fallback refused')
    model_path = Path(sequence['soma_shape_params_path'])
    gender = 'neutral'
    hashes = {str(p): _digest(p) for p in (source, model_path)}
    template = robot.smpl_template_config(config, sequence, key, gender)
    v, j, faces, joint_names, source_type = common.source_template_vertices_joints_faces(sequence, template, model_dir)
    with np.load(run / 'dataset.npz', allow_pickle=True) as saved:
        centered, _, _ = common.center_source_template(v, j, str(saved['center_modes'][0]), joint_names=joint_names, source_type='soma')
        np.testing.assert_allclose(centered, saved['mesh_vertices_0'], atol=2e-6, rtol=0)
        np.testing.assert_array_equal(faces, saved['mesh_faces_0'])
    face_ids = np.asarray(binding['face_ids'])
    bary = np.asarray(binding['bary'])
    if (face_ids.shape != (4096,) or bary.shape != (4096, 3)
            or not np.isfinite(bary).all() or face_ids.min() < 0 or face_ids.max() >= len(faces)
            or not np.allclose(bary.sum(axis=1), 1, atol=2e-6)):
        raise ValueError('Invalid human surface binding')
    if list(joint_names).count('Hips') != 1:
        raise ValueError('Expected exactly one named SOMA Hips joint for pelvis anchoring')
    hips_index = list(joint_names).index('Hips')
    bvh_names = list(sequence['joint_names'])
    if len(set(joint_names)) != len(joint_names) or len(set(bvh_names)) != len(bvh_names):
        raise ValueError('Joint names must be unique')
    matched = [name for name in bvh_names if name in joint_names]
    native_ids = [bvh_names.index(name) for name in matched]
    fitted_ids = [list(joint_names).index(name) for name in matched]
    parents = [matched.index(bvh_names[int(sequence['parents'][bvh_names.index(name)])])
               if int(sequence['parents'][bvh_names.index(name)]) >= 0
               and bvh_names[int(sequence['parents'][bvh_names.index(name)])] in matched else -1
               for name in matched]
    fitted_skeleton, bvh_skeleton = [], []
    chunks, roots, max_error = [], [], 0.
    chunk_size = 64
    for start in range(0, len(frame_ids), chunk_size):
        ids = frame_ids[start:start + chunk_size]
        vertices, joints, actual_faces = common.source_motion_vertices_joints(
            sequence, ids, model_dir, batch_size=32, smplx_device='cpu',
            smplx_batch_size=32, zero_source_finger_pose=zero_fingers)
        np.testing.assert_array_equal(actual_faces, faces)
        vertices = common.source_points_to_retarget_frame(vertices, 'soma', sequence.get('output_up', 'z'))
        joints = common.source_points_to_retarget_frame(joints, 'soma', sequence.get('output_up', 'z'))
        # The recorded ground shift was computed over the original entire clip.
        # Applying it directly avoids recomputing a different floor per chunk.
        vertices[:, :, 2] -= ground
        joints[:, :, 2] -= ground
        vertices = (vertices * scale)[:, :, [1, 2, 0]]
        joints = (joints * scale)[:, :, [1, 2, 0]]
        root = joints[:, hips_index]
        raw_joints = soma_source.soma_bvh_global_transforms(sequence, ids, zero_fingers=zero_fingers)[:, :, :3, 3]
        raw_joints[:, :, 1] -= ground
        bvh_skeleton.append((raw_joints[:, native_ids] * scale).astype('<f4'))
        fitted_skeleton.append(joints[:, fitted_ids].astype('<f4'))
        encoded = encode_root_relative(vertices, root, np)
        max_error = max(max_error, float(np.abs(encoded.astype(np.float32) * .0001 + root[:, None] - vertices).max()))
        name = f'human-motion-{len(chunks):03d}.bin'
        encoded.tofile(output / name)
        chunks.append({'file': name, 'start': start, 'count': len(ids)})
        roots.extend(root.tolist())
        print(f'[HumanReplay] {start + len(ids)}/{len(frame_ids)} frames', flush=True)
    if hashes != {name: _digest(name) for name in hashes}:
        raise RuntimeError('Human source/model changed during export')
    np.concatenate(fitted_skeleton).tofile(output / 'fitted-joints.bin')
    np.concatenate(bvh_skeleton).tofile(output / 'bvh-joints.bin')
    (output / 'joint-map.json').write_text(__import__('json').dumps({
        'matched_names': matched, 'parents': parents, 'fitted_indices': fitted_ids,
        'bvh_indices': native_ids, 'fitted_names': list(joint_names), 'bvh_names': bvh_names,
        'bvh_unmatched': [n for n in bvh_names if n not in joint_names],
        'fitted_unmatched': [n for n in joint_names if n not in bvh_names],
        'coordinates': 'Y-up metres, saved source scale and source ground shift',
        'scope': 'Raw BVH global skeleton and fitted SOMA model transforms share names and local pose channels; fitted shape rest offsets may differ.'}, indent=2)+'\n')
    return {'frame_count': len(frame_ids), 'fps': fps, 'vertex_count': len(v),
            'chunk_size': chunk_size, 'chunks': chunks, 'root_positions': roots,
            'encoding': 'int16 little endian; frame, vertex, xyz; root-relative Y-up metres',
            'quantization_m': .0001, 'max_vertex_axis_error_m': max_error,
            'root_reference_joint_name': 'Hips', 'root_reference_joint_index': hips_index, 'root_anchor_joint': 'Hips', 'root_anchor_joint_index': hips_index, 'source_scale': scale, 'source_ground_shift_native_z_m': ground,
            'source_format': sequence['source_format'], 'template_name': sequence['soma_template_name'],
            'skeleton': {'joint_map': 'joint-map.json', 'joint_count': len(matched), 'fitted': 'fitted-joints.bin', 'bvh': 'bvh-joints.bin'},
            'zero_source_finger_pose': zero_fingers, 'inputs_sha256': hashes,
            'slot_vertices': faces[face_ids].tolist(), 'slot_bary': bary.tolist(),
            'scope': 'Original source motion reconstructed with saved shape, frame IDs, scale and ground shift; no resampling'}
