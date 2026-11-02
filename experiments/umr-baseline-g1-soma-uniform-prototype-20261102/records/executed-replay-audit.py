"""Independent all-frame checks of fitted source, BVH FK and rigid robot replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

# Reject mismatched BLAS/CUDA configuration before importing numerical runtimes.
EXPECTED_NUMERICAL_ENVIRONMENT = {'OMP_NUM_THREADS':'4', 'OPENBLAS_NUM_THREADS':'4',
    'CUDA_VISIBLE_DEVICES':'0', 'UMR_SOMA_ASSETS_PATH':'/data/motions/human_models/soma-x/f81a01796f65/overlays/umr',
    'UMR_SOMA_SMPLX_ASSETS_PATH':'/data/motions/human_models/soma-x/f81a01796f65/overlays/umr/SMPLX'}
if __name__ == '__main__' and os.environ.get('UMR_SOMA_DEVICE') not in (None, 'cuda:0'):
    raise RuntimeError('Tight fitted replay requires actual SOMA cuda:0 device')
NUMERICAL_ENVIRONMENT_AT_IMPORT = {k:os.environ.get(k) for k in EXPECTED_NUMERICAL_ENVIRONMENT}
if __name__ == '__main__' and NUMERICAL_ENVIRONMENT_AT_IMPORT != EXPECTED_NUMERICAL_ENVIRONMENT:
    raise RuntimeError('Tight fitted replay audit requires the recorded exporter environment before numerical imports: '+repr(NUMERICAL_ENVIRONMENT_AT_IMPORT))

import mujoco
import numpy as np
import torch
torch.set_num_threads(2)
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'externals/UMR/scripts'))
import soma_source


def stats(a):
    a = np.asarray(a, dtype=float)
    return {'mean': float(a.mean()), 'p95': float(np.quantile(a, .95)), 'max': float(a.max())}


def independent_bvh_fk(sequence, ids, zero_fingers):
    """Parsed BVH cm/degrees -> metres, intrinsic declared Euler channel order."""
    values = sequence['motion_values'][ids]
    transforms = np.broadcast_to(np.eye(4), (len(ids), len(sequence['joint_names']), 4, 4)).copy()
    for j, channels in enumerate(sequence['channels']):
        v = values[:, int(sequence['channel_offsets'][j]):][:, :len(channels)].astype(np.float64)
        pos = np.broadcast_to(np.asarray(sequence['offsets'][j], dtype=np.float64), (len(ids), 3)).copy()
        pcols = [(c, 'XYZ'.index(name[0].upper())) for c, name in enumerate(channels) if 'position' in name.lower()]
        if pcols:
            pos[:] = 0
            for c, axis in pcols:
                pos[:, axis] = v[:, c] * .01
        transforms[:, j, :3, 3] = pos
        rcols = [(c, name[0].upper()) for c, name in enumerate(channels) if 'rotation' in name.lower()]
        finger = soma_source.is_soma_finger_joint_name(sequence['joint_names'][j])
        if rcols and not (zero_fingers and finger):
            transforms[:, j, :3, :3] = Rotation.from_euler(''.join(axis for _, axis in rcols), v[:, [c for c, _ in rcols]], degrees=True).as_matrix()
        parent = int(sequence['parents'][j])
        if parent >= 0:
            transforms[:, j] = transforms[:, parent] @ transforms[:, j]
    return transforms


def main():
    p = argparse.ArgumentParser(__doc__)
    for name in ('run', 'inspection', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    assert torch.cuda.is_available() and torch.get_num_threads() == 2
    hardware = json.loads((args.run/'runtime-hardware.json').read_text())
    assert torch.__version__ == hardware['torch_version']
    runtime = {'environment':NUMERICAL_ENVIRONMENT_AT_IMPORT, 'torch_version':torch.__version__, 'torch_threads':torch.get_num_threads(), 'torch_cuda_runtime':torch.version.cuda, 'cuda_device':torch.cuda.get_device_name(0), 'soma_device':'cuda:0', 'numpy_version':np.__version__}
    payload = json.loads((args.inspection/'bindings.json').read_text())
    human, motion = payload['human_motion'], payload['motion']
    with np.load(args.run/'motion.npz', allow_pickle=True) as saved:
        qpos, ids = saved['qpos'].copy(), saved['frame_ids'].copy()
        source = Path(str(saved['source_data'].item()))
        model = mujoco.MjModel.from_xml_path(str(saved['robot_xml'].item()))
        fps = float(saved['fps'].item())
    files = [source, args.run/'motion.npz', args.inspection/'bindings.json', args.inspection/'binding.npz']
    files += [args.inspection/c['file'] for c in human['chunks']]
    files += [args.inspection/name for name in ('fitted-joints.bin','bvh-joints.bin','joint-map.json','human-faces.bin','human-vertices.bin',motion['transforms'],'replay-diagnostic-verified.json')]
    files += [Path(__file__), args.run/'runtime-hardware.json', args.run/'native_source.json', args.run/'input/bones-seed/shapes/soma_uniform_fit_mhr_params/soma_base_fit_mhr_params.npz']
    def hashes():
        return {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    before = hashes()
    assert payload['official_fitted_bones_seed'] is True
    sequence = soma_source.load_soma_bvh_motion(source)
    assert soma_source._preferred_soma_device(sequence,torch) == 'cuda:0'
    assert sequence['source_format'] == human['source_format'] == 'soma_bvh_boneseed_uniform'
    assert sequence['soma_template_name'] == human['template_name'] == 'soma_uniform'
    assert len(ids) == 1165 and np.array_equal(ids, np.arange(1165))
    assert abs(fps-120.0048) < 1e-5 and abs(fps-float(sequence['fps'])) < 1e-5
    assert human['frame_count'] == motion['frame_count'] == len(ids)
    assert human['fps'] == motion['fps'] == fps
    names = json.loads((args.inspection/'joint-map.json').read_text())
    matched = names['matched_names']
    assert len(matched) == len(set(matched))
    assert matched.count('Hips') == 1
    _, _, template_faces, template = soma_source.soma_template_vertices_joints_faces(sequence=sequence)
    public = list(template['joint_short_names'])
    bvh_names = list(sequence['joint_names'])
    assert names['fitted_names'] == public and names['bvh_names'] == bvh_names
    assert names['fitted_indices'] == [public.index(n) for n in matched]
    assert names['bvh_indices'] == [bvh_names.index(n) for n in matched]
    native_poses, native_transl = soma_source._boneseed_bvh_to_soma_inputs(
        sequence, ids, public, zero_fingers=human['zero_source_finger_pose'])
    expected_poses = np.zeros_like(native_poses)
    expected_transl = None
    for source_j, name in enumerate(bvh_names):
        channels = sequence['channels'][source_j]
        start = int(sequence['channel_offsets'][source_j])
        values = sequence['motion_values'][ids, start:start+len(channels)]
        rc = [(c, channel[0].upper()) for c, channel in enumerate(channels) if 'rotation' in channel.lower()]
        if name in public and public.index(name) > 0 and rc and not (
                human['zero_source_finger_pose'] and soma_source.is_soma_finger_joint_name(name)):
            expected_poses[:,public.index(name)-1] = Rotation.from_euler(
                ''.join(axis for _,axis in rc), values[:,[c for c,_ in rc]], degrees=True).as_rotvec()
        if name == 'Hips':
            expected_transl = np.zeros_like(native_transl)
            for c, channel in enumerate(channels):
                if 'position' in channel.lower():
                    expected_transl[:, 'XYZ'.index(channel[0].upper())] = values[:,c]*.01
    assert expected_transl is not None
    pose_map_error = float(np.abs(native_poses-expected_poses).max())
    translation_map_error = float(np.abs(native_transl-expected_transl).max())
    assert pose_map_error <= 2e-7 and translation_map_error <= 2e-7
    root_id = bvh_names.index(public[0])
    root_start = int(sequence['channel_offsets'][root_id])
    ignored_root_channel_max = float(np.abs(sequence['motion_values'][ids, root_start:root_start+len(sequence['channels'][root_id])]).max())
    assert ignored_root_channel_max == 0, 'Native omitted public Root carries motion'
    hips = public.index('Hips')
    assert human['root_reference_joint_name'] == 'Hips' and human['root_reference_joint_index'] == hips
    n, j = len(ids), len(matched)
    skels = [np.fromfile(args.inspection/file, dtype='<f4').reshape(n,j,3) for file in ('fitted-joints.bin','bvh-joints.bin')]
    with np.load(args.inspection/'binding.npz') as b:
        face_ids, bary = b['source_face_ids'].copy(), b['source_bary'].copy()
    assert face_ids.shape == (4096,) and bary.shape == (4096,3)
    assert np.isfinite(bary).all() and bary.min() >= -2e-6
    np.testing.assert_allclose(bary.sum(axis=1), 1, atol=2e-6, rtol=0)
    f = np.fromfile(args.inspection/'human-faces.bin',dtype='<u4').reshape(-1,3)
    np.testing.assert_array_equal(f, template_faces)
    v = np.fromfile(args.inspection/'human-vertices.bin',dtype='<f4').reshape(-1,3)
    static_slots = np.einsum('sc,scd->sd', bary, v[f[face_ids]])
    np.testing.assert_allclose(static_slots, payload['source'], atol=2e-7, rtol=0)
    source_vertex_error = slot_error = root_error = skeleton_error = bvh_fk_error = 0.
    offset = 0
    for chunk in human['chunks']:
        start, count = chunk['start'], chunk['count']
        assert start == offset
        offset += count
        sl = slice(start,start+count)
        vertices, joints, faces = soma_source.soma_motion_vertices_joints(sequence, ids[sl], batch_size=32, zero_fingers=human['zero_source_finger_pose'])
        np.testing.assert_array_equal(faces, template_faces)
        assert np.isfinite(vertices).all() and np.isfinite(joints).all()
        # The native frame round trip [z,x,y] then [y,z,x] is identity;
        # only the stored ground shift changes source Y before saved scaling.
        vertices[:,:,1] -= human['source_ground_shift_native_z_m']
        joints[:,:,1] -= human['source_ground_shift_native_z_m']
        vertices *= human['source_scale']
        joints *= human['source_scale']
        roots = np.asarray(human['root_positions'])[sl]
        root_error = max(root_error, float(np.abs(roots-joints[:,hips]).max()))
        decoded = np.fromfile(args.inspection/chunk['file'],dtype='<i2').reshape(count,human['vertex_count'],3).astype(float)*human['quantization_m']+roots[:,None]
        source_vertex_error = max(source_vertex_error,float(np.abs(decoded-vertices).max()))
        expected_slots = np.einsum('sc,fscd->fsd',bary,vertices[:,faces[face_ids]])
        actual_slots = np.einsum('sc,fscd->fsd',bary,decoded[:,faces[face_ids]])
        slot_error = max(slot_error,float(np.abs(expected_slots-actual_slots).max()))
        skeleton_error = max(skeleton_error,float(np.abs(skels[0][sl]-joints[:,names['fitted_indices']]).max()))
        independent = independent_bvh_fk(sequence,ids[sl],human['zero_source_finger_pose'])
        native = soma_source.soma_bvh_global_transforms(sequence,ids[sl],zero_fingers=human['zero_source_finger_pose'])
        bvh_fk_error = max(bvh_fk_error,float(np.abs(independent-native).max()))
        points = independent[:, :, :3, 3][:,names['bvh_indices']]
        points[:,:,1] -= human['source_ground_shift_native_z_m']
        points *= human['source_scale']
        skeleton_error = max(skeleton_error,float(np.abs(skels[1][sl]-points).max()))
        print(f'[Audit] source {offset}/{n}',flush=True)
    print(json.dumps({'source_metrics_before_acceptance':{'offset':offset,'root_error':root_error,'source_vertex_error':source_vertex_error,'slot_error':slot_error,'skeleton_error':skeleton_error,'bvh_fk_error':bvh_fk_error}}),flush=True)
    diagnostic_path = args.inspection/'replay-diagnostic-verified.json'
    diagnostic = json.loads(diagnostic_path.read_text())
    native_repeatability = max(diagnostic[k] for k in ('same_model_native_repeat_vertices_max_axis_m', 'same_model_native_repeat_joints_max_axis_m', 'fresh_model_native_vertices_max_axis_m', 'fresh_model_native_joints_max_axis_m', 'direct_vs_common_wrapper_vertices_max_axis_m', 'direct_vs_common_wrapper_joints_max_axis_m'))
    assert diagnostic['runtime'] == runtime
    encoding_budget = human['quantization_m']/2 + 1e-7
    native_budget = 3e-6
    # 50um half-step + <=2um observed native variability + 1um arithmetic margin.
    combined_budget = human['quantization_m']/2 + 3e-6
    assert native_repeatability <= 2e-6
    assert human['max_vertex_axis_error_m'] <= encoding_budget
    assert diagnostic['fresh_quantization_own_reference_max_axis_m'] <= encoding_budget
    assert offset == n and root_error <= 2e-7 and source_vertex_error <= combined_budget
    assert slot_error <= combined_budget and skeleton_error <= native_budget and bvh_fk_error <= 1e-10
    assert np.ptp(np.asarray(human['root_positions']),axis=0).max() > .1
    actual_joint_names = [model.joint(i).name for i in range(model.njnt) if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
    assert actual_joint_names == motion['joint_names']
    transforms = np.fromfile(args.inspection/motion['transforms'],dtype='<f8').reshape(n,len(motion['pieces']),3,4)
    local, piece = np.asarray(motion['slot_local']), np.asarray(motion['slot_piece'])
    geom_ids = np.asarray([p['geom_id'] for p in motion['pieces']])[piece]
    state, rigid_error = mujoco.MjData(model), 0.
    for i, pose in enumerate(qpos):
        state.qpos[:] = pose
        mujoco.mj_forward(model,state)
        native = np.einsum('sij,sj->si',state.geom_xmat[geom_ids].reshape(-1,3,3),local)+state.geom_xpos[geom_ids]
        decoded = np.einsum('sij,sj->si',transforms[i,piece,:,:3],local)+transforms[i,piece,:,3]
        rigid_error = max(rigid_error,float(np.abs(native[:,[1,2,0]]-decoded).max()))
    assert rigid_error <= 5e-7
    center = matched.index('Hips')
    delta = skels[0].astype(float)-skels[1]
    centered_delta = (skels[0]-skels[0][:,center,None])-(skels[1]-skels[1][:,center,None])
    unchanged = before == hashes()
    assert unchanged
    result = {'all_1165_frames_checked':True, 'runtime':runtime,
        'precision_budget':{'mesh_half_quantization_step_m':human['quantization_m']/2, 'float32_encoding_rounding_allowance_m':1e-7, 'native_fitted_forward_repeatability_budget_m':2e-6, 'arithmetic_margin_m':1e-6, 'skeleton_native_replay_axis_tolerance_m':native_budget, 'combined_source_mesh_axis_tolerance_m':combined_budget, 'measured_native_repeatability_max_axis_m':native_repeatability, 'exporter_unquantized_reference_quantization_max_axis_error_m':human['max_vertex_axis_error_m'], 'controlled_diagnostic':diagnostic, 'controlled_diagnostic_sha256':hashlib.sha256(diagnostic_path.read_bytes()).hexdigest(), 'interpretation':'Quantization is checked against its own unquantized reference separately. Independent fitted forward calls vary at micrometre scale even in one process, as measured by native-native repeats. No source route, frames or topology are changed.'},'source_topology_exact_every_chunk':True,
        'fitted_source_native_replay_max_axis_error_m':source_vertex_error,
        'source_4096_barycentric_slots_all_frames_max_axis_error_m':slot_error,
        'source_moving_Hips_anchor_max_axis_error_m':root_error,
        'robot_4096_rigid_slots_all_frames_max_axis_error_m':rigid_error,
        'independent_BVH_FK_vs_native_max_transform_element_error':bvh_fk_error,
        'skeleton_binary_native_replay_max_axis_error_m':skeleton_error,
        'named_joint_map':names, 'local_pose_channel_mapping_max_rotvec_error_rad':pose_map_error,
        'Hips_translation_channel_mapping_max_axis_error_m':translation_map_error,
        'native_public_joint_zero_omitted_from_pose_vector':public[0],
        'ignored_public_Root_all_channel_max_abs':ignored_root_channel_max,'raw_BVH_vs_fitted_model_joint_distance_m':stats(np.linalg.norm(delta,axis=2)),
        'hips_centered_BVH_vs_fitted_model_joint_distance_m':stats(np.linalg.norm(centered_delta,axis=2)),
        'per_joint_hips_centered_distance_m':{name:stats(np.linalg.norm(centered_delta[:,i],axis=1)) for i,name in enumerate(matched)},
        'source_scale':human['source_scale'],'fps':fps,'frame_count':n,
        'preservation':{'all_audit_inputs_unchanged':unchanged,'sha256':before},
        'interpretation':'BVH hierarchy offsets and fitted model rest offsets are different representations; discrepancies are measured diagnostics, not a failed pose-map assertion. Named Hips anchors the fitted mesh, not stationary Root.',
        'limitations':['Visual acceptance remains pending user inspection.','No dynamics, controller rollout, collision evaluation, support-force or contact-truth validation.','Native fitted forward replay checks export fidelity; it does not independently validate the SOMA model implementation.']}
    with args.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('preservation','named_joint_map','per_joint_hips_centered_distance_m')},indent=2))


if __name__ == '__main__':
    main()
