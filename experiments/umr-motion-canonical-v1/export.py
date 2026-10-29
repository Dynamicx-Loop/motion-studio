"""Measure kinematic outputs and export visual meshes; no dynamics simulation."""
from pathlib import Path
import hashlib,json,re,shutil
import numpy as np
import mujoco
from scipy.spatial import ConvexHull
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'outputs/umr-motion-canonical-v1';VIEW=OUT/'viewer';VIEW.mkdir(parents=True,exist_ok=True)
B=np.array([[1,0,0],[0,0,1],[0,-1,0.]])
def stats(a):
 a=np.asarray(a)
 return {'mean':float(a.mean()),'p95':float(np.percentile(a,95)),'max':float(a.max())} if a.size else None
manifest={'arms':{},'source':'HiPHI Getting_up-get_up_0004','blocked_source':'BONES-SEED motion/shape/rig missing'};results={}
for path in sorted(OUT.glob('*/trajectory.npz')):
 arm=path.parent.name;z=np.load(path,allow_pickle=True);q=z['qpos'];fps=float(z['fps'][0]);c=json.loads((HERE/f'{arm}.json').read_text())
 xml=Path(str(z['robot_xml'].item()));m=mujoco.MjModel.from_xml_path(str(xml));d=mujoco.MjData(m)
 assert len(q)==1823 and q.shape[1]==m.nq and np.isfinite(q).all()
 assert np.array_equal(z['frame_ids'],np.arange(0,5468,3))
 ids=[i for i in range(m.ngeom) if m.geom_group[i]==1 and m.geom_type[i]==mujoco.mjtGeom.mjGEOM_MESH]
 parts=[];hulls=[];assets={str(xml):hashlib.sha256(xml.read_bytes()).hexdigest()}
 for i in ids:
  mesh=m.geom_dataid[i];va=m.mesh_vertadr[mesh];vn=m.mesh_vertnum[mesh];fa=m.mesh_faceadr[mesh];fn=m.mesh_facenum[mesh]
  v=m.mesh_vert[va:va+vn].copy();f=m.mesh_face[fa:fa+fn].copy();stem=f'{arm}-{i}'
  v.astype('<f4').tofile(VIEW/f'{stem}-v.bin');f.astype('<u4').tofile(VIEW/f'{stem}-f.bin')
  hulls.append(v[ConvexHull(v).vertices] if len(v)>4 else v)
  parts.append({'vertices':f'{stem}-v.bin','faces':f'{stem}-f.bin','body':m.body(int(m.geom_bodyid[i])).name})
 transforms=np.empty((len(q),len(ids),12),dtype='<f4');minima=[];feet={};positions=[]
 for t,pose in enumerate(q):
  d.qpos[:]=pose;mujoco.mj_forward(m,d);positions.append(d.xpos.copy());low=np.inf
  for k,i in enumerate(ids):
   rot=B@d.geom_xmat[i].reshape(3,3);pos=B@d.geom_xpos[i];transforms[t,k,:9]=rot.ravel();transforms[t,k,9:]=pos
   low=min(low,float((hulls[k]@rot.T+pos)[:,1].min()))
  minima.append(low)
 positions=np.asarray(positions)
 for side in ['left','right']:
  name=side+'_ankle_roll_link';bid=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,name)
  if bid<0:continue
  p=positions[:,bid];h=p[:,2];stance=h<=h.min()+.03;speed=np.linalg.norm(np.diff(p[:,:2],axis=0),axis=1)*fps;mask=stance[1:]&stance[:-1]
  feet[side]={'definition':'ankle body height <= clip minimum + 0.03m; consecutive stance frames; not measured contacts','stance_fraction':float(stance.mean()),'horizontal_speed_m_s':stats(speed[mask]),'horizontal_path_m':float(speed[mask].sum()/fps)}
 joint_ids=np.flatnonzero(m.jnt_type==mujoco.mjtJoint.mjJNT_HINGE);names=[m.joint(int(j)).name for j in joint_ids];angles=q[:,m.jnt_qposadr[joint_ids]];margins=[]
 for k,j in enumerate(joint_ids):
  lo,hi=m.jnt_range[j];over=c['robot'].get('joint_limits',{}).get(names[k]);
  if over:lo=max(lo,float(over[0]));hi=min(hi,float(over[1]))
  margins.append(np.minimum(angles[:,k]-lo,hi-angles[:,k]))
 margins=np.array(margins);log=(OUT/f'{arm}.log').read_text();cost=re.search(r'cost mean=([\d.e+-]+) max=([\d.e+-]+)',log)
 r={'frames':len(q),'fps':fps,'qpos_shape':list(q.shape),'all_finite':True,'joint_names':names,'joint_limit_min_margin_rad':float(margins.min()),'joint_limit_violation_count_1e6':int((margins < -1e-6).sum()),'joint_velocity_abs_rad_s':stats(abs(np.diff(angles,axis=0)*fps)),'joint_acceleration_abs_rad_s2':stats(abs(np.diff(angles,n=2,axis=0)*fps**2)),'visual_min_height_m':float(min(minima)),'visual_penetration_frames_below_minus_1mm':int((np.array(minima)<-.001).sum()),'inferred_stance':feet,'root_net_displacement_m':float(np.linalg.norm(q[-1,:3]-q[0,:3])),'root_path_m':float(np.linalg.norm(np.diff(q[:,:3],axis=0),axis=1).sum()),'root_quaternion_norm_max_error':float(abs(np.linalg.norm(q[:,3:7],axis=1)-1).max()),'solver_reported_cost':{'mean':float(cost[1]),'max':float(cost[2])} if cost else None,'smpl_scale':float(z['smpl_scale'][0]),'trajectory_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'xml_hashes':assets,'self_collision':'not evaluated: visual meshes only; collision primitives deferred','tracking_residuals':'aggregate solver-reported cost only; not per-segment physical distances'}
 transforms.tofile(VIEW/f'{arm}-transforms.bin');center=(B@q[0,:3]);center[1]=0
 manifest['arms'][arm]={'parts':parts,'transforms':f'{arm}-transforms.bin','center':center.tolist(),'scale':r['smpl_scale']}
 manifest.update(frames=len(q),fps=fps);results[arm]=r
 # Preserve model text with an explicit original base directory record (meshes remain hashed upstream).
 shutil.copy2(xml,path.parent/'generated-model.xml')
 (path.parent/'model-base.txt').write_text(str(xml.parent)+'\n')
(HERE/'results.json').write_text(json.dumps(results,indent=2)+'\n');(VIEW/'manifest.json').write_text(json.dumps(manifest))
shutil.copytree(ROOT/'outputs/smplx/wendy-viewer/vendor',VIEW/'vendor',dirs_exist_ok=True)
print(json.dumps({k:{x:v[x] for x in ['visual_min_height_m','joint_limit_min_margin_rad','solver_reported_cost']} for k,v in results.items()},indent=2))
