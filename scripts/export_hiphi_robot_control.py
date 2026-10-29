"""Compare four retargets and export robot visual meshes and full FK transforms."""
import argparse,json,hashlib,shutil
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/hiphi-robot-control';view=out/'viewer';view.mkdir(exist_ok=True)
basis=np.array([[1,0,0],[0,0,1],[0,-1,0.]])
def stats(a):return dict(mean=float(np.mean(a)),p95=float(np.percentile(a,95)),max=float(np.max(a)))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--robots',nargs='+',choices=['astro','g1'],default=['astro','g1']);args=parser.parse_args()
manifest=json.loads((view/'manifest.json').read_text()) if (view/'manifest.json').exists() else {'frames':5468,'robots':{}}
report=json.loads((out/'report.json').read_text()) if (out/'report.json').exists() else {}
for robot in args.robots:
 pair=[];meta=[];bodies=[];model_hashes=[]
 for version in ['reference','reconverted']:
  path=out/robot/f'{version}.npz';z=np.load(path,allow_pickle=True);q=z['qpos'];xml=str(z['robot_xml'].item())
  assert len(q)==5468 and np.isfinite(q).all() and np.array_equal(z['frame_ids'],np.arange(5468))
  model_hashes.append(sha(Path(xml)))
  model=mujoco.MjModel.from_xml_path(xml);data=mujoco.MjData(model);assert model.nq==q.shape[1]
  ids=[i for i in range(model.ngeom) if model.geom_group[i]==1 and model.geom_type[i]==mujoco.mjtGeom.mjGEOM_MESH]
  assert ids
  parts=[];hulls=[]
  for i in ids:
   mid=int(model.geom_dataid[i]);va=int(model.mesh_vertadr[mid]);vn=int(model.mesh_vertnum[mid]);fa=int(model.mesh_faceadr[mid]);fn=int(model.mesh_facenum[mid])
   v=model.mesh_vert[va:va+vn].copy();f=model.mesh_face[fa:fa+fn].copy();stem=f'{robot}-{i}'
   if version=='reference':v.astype('<f4').tofile(view/f'{stem}-v.bin');f.astype('<u4').tofile(view/f'{stem}-f.bin')
   hulls.append(v[ConvexHull(v).vertices] if len(v)>4 else v)
   parts.append(dict(vertices=f'{stem}-v.bin',faces=f'{stem}-f.bin',color=model.geom_rgba[i,:3].tolist()))
  transforms=np.empty((len(q),len(ids),12),dtype='<f4');body=np.empty((len(q),model.nbody,3));low=np.full(3,np.inf);high=-low
  for t,pose in enumerate(q):
   data.qpos[:]=pose;mujoco.mj_forward(model,data);body[t]=data.xpos
   for k,i in enumerate(ids):
    rot=basis@data.geom_xmat[i].reshape(3,3);pos=basis@data.geom_xpos[i];transforms[t,k,:9]=rot.ravel();transforms[t,k,9:]=pos
    world=hulls[k]@rot.T+pos;low=np.minimum(low,world.min(0));high=np.maximum(high,world.max(0))
  transform_file=f'{robot}-{version}-transforms.bin';transforms.tofile(view/transform_file)
  jids=np.flatnonzero(model.jnt_type==mujoco.mjtJoint.mjJNT_HINGE);adr=model.jnt_qposadr[jids];a=q[:,adr]
  limited=jids[model.jnt_limited[jids].astype(bool)];v=np.maximum(model.jnt_range[limited,0]-q[:,model.jnt_qposadr[limited]],q[:,model.jnt_qposadr[limited]]-model.jnt_range[limited,1])
  overrides=json.loads((out/'configs'/f'{robot}-{version}-resolved.json').read_text())['robot'].get('joint_limits',{})
  configured_violation=0.0
  for jid in jids:
   name=model.joint(int(jid)).name
   lower,upper=model.jnt_range[jid] if model.jnt_limited[jid] else [-np.inf,np.inf]
   if name in overrides:
    lower=max(lower,float(overrides[name][0]));upper=min(upper,float(overrides[name][1]));assert lower<=upper
   values=q[:,model.jnt_qposadr[jid]]
   configured_violation=max(configured_violation,float(np.maximum(lower-values,values-upper).max()))
  info=dict(sha256=sha(path),frames=len(q),fps=float(z['fps'].item()),all_finite=True,configured_joint_limit_violation_rad=configured_violation,smpl_scale=float(z['smpl_scale'].item()),zero_source_finger_pose=bool(z['zero_source_finger_pose'].item()),min_visual_y_m=float(low[1]),bounds=[low.tolist(),high.tolist()],joint_limit_violation_rad=max(0,float(v.max())),root_quat_norm_error=float(np.abs(np.linalg.norm(q[:,3:7],axis=1)-1).max()),joint_frame_step_rad=stats(np.abs(np.diff(a,axis=0))))
  pair.append(q);bodies.append(body);meta.append(dict(transforms=transform_file,report=info));print(robot,version,info,flush=True)
 assert meta[0]['report']['fps']==meta[1]['report']['fps']
 assert model_hashes[0]==model_hashes[1], 'Robot XML differs within pair'
 delta=np.abs(pair[0][:,adr]-pair[1][:,adr]);root=np.linalg.norm(pair[0][:,:3]-pair[1][:,:3],axis=1)
 rots=[Rotation.from_quat(q[:,[4,5,6,3]]) for q in pair]
 report[robot]=dict(reference=meta[0]['report'],reconverted=meta[1]['report'],joint_angle_difference_deg=stats(np.degrees(delta)),root_position_difference_m=stats(root),root_orientation_difference_deg=stats(np.degrees((rots[0].inv()*rots[1]).magnitude())),body_origin_difference_m=stats(np.linalg.norm(bodies[0][:,1:]-bodies[1][:,1:],axis=-1)),joint_names=[model.joint(int(i)).name for i in jids],per_joint_mean_difference_deg=np.degrees(delta).mean(0).tolist(),correspondence_sha256=sha(out/robot/'correspondence.npz'),slots_sha256=sha(out/robot/'training/correspondence_slots_final.npz'),robot_xml_sha256=model_hashes[0])
 names=report[robot]['joint_names']
 for group,mask in [('wrists',[('wrist' in name) for name in names]),('non_wrists',[('wrist' not in name) for name in names]),('legs',[any(x in name for x in ['hip','knee','ankle']) for name in names])]:
  report[robot][group+'_angle_difference_deg']=stats(np.degrees(delta[:,mask]))
 worst=np.unravel_index(np.argmax(delta),delta.shape)
 report[robot]['largest_joint_difference_at']={'frame_index':int(worst[0]),'time_s':float(worst[0]/manifest.get('fps',meta[0]['report']['fps'])),'joint':names[worst[1]]}
 # Common centering per robot pair, no relative alignment.
 bounds=np.array([x['report']['bounds'] for x in meta]);center=(bounds[:,0].min(0)+bounds[:,1].max(0))/2;center[1]=0
 manifest['robots'][robot]=dict(parts=parts,variants=meta,center=center.tolist(),frame_joint_rms_deg=np.sqrt(np.mean(np.degrees(delta)**2,axis=1)).tolist(),report=report[robot])
 manifest['fps']=meta[0]['report']['fps']
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(view/'manifest.json').write_text(json.dumps(manifest))
shutil.copytree(ROOT/'outputs/smplx/wendy-viewer/vendor',view/'vendor',dirs_exist_ok=True)
for name in ['index.html','app.js']:shutil.copy(ROOT/'scripts/hiphi-robot-viewer'/name,view/name)
