"""Verify exported binary replay against independent native rigid kinematics."""
import argparse
import json
from pathlib import Path
import sys
import mujoco
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run', type=Path)
parser.add_argument('inspection', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
payload = json.loads((args.inspection / 'bindings.json').read_text())
meta, human = payload['motion'], payload['human_motion']
with np.load(args.run / 'motion.npz', allow_pickle=True) as saved:
    qpos = saved['qpos']
    model = mujoco.MjModel.from_xml_path(str(saved['robot_xml']))
    source = str(saved['source_data'].item())
    frame_ids = saved['frame_ids']
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'externals/UMR/scripts'))
import soma_source
sequence = soma_source.load_soma_bvh_motion(source)
assert list(sequence['joint_names']).count('Hips') == 1
hips = list(sequence['joint_names']).index('Hips')
assert human['root_reference_joint_name'] == 'Hips' and human['root_reference_joint_index'] == hips
native_hips = soma_source.soma_bvh_global_transforms(sequence,frame_ids,zero_fingers=True)[:,hips,:3,3]
native_hips[:,1] -= human['source_ground_shift_native_z_m']
expected_roots = native_hips * human['source_scale']
root_error = float(np.abs(expected_roots-np.asarray(human['root_positions'])).max())
assert root_error <= 2e-7
assert float(np.ptp(expected_roots,axis=0).max()) > .1
state = mujoco.MjData(model)
transforms = np.fromfile(args.inspection / meta['transforms'], dtype='<f8').reshape(len(qpos),len(meta['pieces']),3,4)
local = np.asarray(meta['slot_local'])
piece = np.asarray(meta['slot_piece'])
geom_ids = np.asarray([p['geom_id'] for p in meta['pieces']])[piece]
error = 0.
for i, pose in enumerate(qpos):
    state.qpos[:] = pose
    mujoco.mj_forward(model, state)
    native = np.einsum('sij,sj->si',state.geom_xmat[geom_ids].reshape(-1,3,3),local)+state.geom_xpos[geom_ids]
    decoded = np.einsum('sij,sj->si',transforms[i,piece,:,:3],local)+transforms[i,piece,:,3]
    error = max(error,float(np.abs(native[:,[1,2,0]]-decoded).max()))
assert error <= 5e-7
assert human['frame_count'] == meta['frame_count'] == len(qpos)
assert human['fps'] == meta['fps']
assert human['max_vertex_axis_error_m'] <= 5.1e-5
assert sum(c['count'] for c in human['chunks']) == len(qpos)
assert payload['official_fitted_bones_seed'] is False
for chunk in human['chunks']:
    assert (args.inspection/chunk['file']).stat().st_size == chunk['count']*human['vertex_count']*3*2
with np.load(args.inspection / 'binding.npz') as b:
    bary = b['source_bary']
    np.testing.assert_allclose(bary.sum(axis=1),1,atol=2e-6,rtol=0)
    v = np.fromfile(args.inspection/'human-vertices.bin',dtype='<f4').reshape(-1,3)
    f = np.fromfile(args.inspection/'human-faces.bin',dtype='<u4').reshape(-1,3)
    expected = (v[f[b['source_face_ids']]]*bary[:,:,None]).sum(axis=1)
    np.testing.assert_allclose(expected,payload['source'],atol=2e-7,rtol=0)
dist = np.asarray(payload['projection_m'])
report = {'all_robot_frames_and_4096_bindings_checked':True,'robot_binary_rigid_replay_max_axis_error_m':error,
    'all_source_pelvis_frames_checked':True,'source_root_reference_joint_name':'Hips','source_root_reference_joint_index':hips,
    'source_pelvis_anchor_max_axis_error_m':root_error,
    'robot_replay_axis_tolerance_m':5e-7,'source_face_bary_replay_checked':True,
    'human_binary_chunks_and_timeline_checked':True,'human_max_vertex_axis_error_m':human['max_vertex_axis_error_m'],
    'source_scale':human['source_scale'],'source_ground_shift_native_z_m':human['source_ground_shift_native_z_m'],
    'native19_segment_counts':payload['counts'],'robot_slot_projection_mean_m':float(dist.mean()),
    'robot_slot_projection_p95_m':float(np.percentile(dist,95)), 'robot_slot_projection_max_m':float(dist.max()),
    'limitations':['Projection is a reference-pose diagnostic, not anatomical accuracy or motion quality.','No dynamics or controller evaluation.']}
with args.report.open('x') as stream:
    json.dump(report,stream,indent=2,allow_nan=False)
    stream.write('\n')
print(json.dumps(report,indent=2))
