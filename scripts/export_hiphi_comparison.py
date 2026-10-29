"""Bake full, synchronized reference/reconversion meshes and mesh error metrics."""
import json, shutil
from pathlib import Path
import numpy as np
import torch
import smplx
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/hiphi-conversion-control'; view=out/'viewer';view.mkdir(exist_ok=True)
r=json.loads((out/'report.json').read_text())
z=np.load(r['reference']); c=np.load(out/'reconverted.npz');n=len(z['poses'])
assert c['poses'].shape==z['poses'].shape and np.array_equal(c['betas'],z['betas'])
model=smplx.SMPLX(r['model'],gender='neutral',use_pca=False,flat_hand_mean=True,batch_size=1).to('cuda')
centers=[]; bounds=[]; all_errors=[]; body_errors=[]; frame_errors=[]
def bake(p,t):
 p=torch.as_tensor(p,device='cuda');b=len(p)
 v=model(betas=torch.as_tensor(z['betas'],device='cuda').expand(b,-1),global_orient=p[:,:3],body_pose=p[:,3:66],jaw_pose=p[:,66:69],leye_pose=p[:,69:72],reye_pose=p[:,72:75],left_hand_pose=p[:,75:120],right_hand_pose=p[:,120:165],transl=torch.as_tensor(t,device='cuda'),expression=torch.zeros(b,10,device='cuda')).vertices.cpu().numpy()
 assert np.isfinite(v).all()
 return v
lo=np.full((2,3),np.inf);hi=-lo
with torch.no_grad():
 for start in range(0,n,90):
  pairs=[[],[]]
  for s in range(start,min(start+90,n),30):
   end=min(s+30,start+90,n)
   vp=[]
   for k,d in enumerate([z,c]):
    v=bake(d['poses'][s:end],d['trans'][s:end]);vp.append(v);pairs[k].append(v)
    lo[k]=np.minimum(lo[k],v.min((0,1)));hi[k]=np.maximum(hi[k],v.max((0,1)))
   e=np.linalg.norm(vp[0]-vp[1],axis=-1);all_errors.append(e.reshape(-1));frame_errors.extend(e.mean(1).tolist())
   # Standardize wrists/hands/face to the rerun, retaining reference body joints 0..19.
   p=z['poses'][s:end].copy();p[:,60:]=c['poses'][s:end,60:]
   body_errors.append(np.linalg.norm(bake(p,z['trans'][s:end])-vp[1],axis=-1).reshape(-1))
  for k in range(2):np.concatenate(pairs[k]).astype('<f4').tofile(view/f'{k}-{start//90:03d}.bin')
  print(f'{min(start+90,n)}/{n}',flush=True)
np.asarray(model.faces,dtype='<u4').tofile(view/'faces.bin')
def stats(a):
 a=np.concatenate(a);return dict(mean=float(a.mean()),p95=float(np.percentile(a,95)),max=float(a.max()))
r['mesh_error_all_vertices_m']=stats(all_errors)
r['mesh_error_with_matching_wrists_hands_face_m']=stats(body_errors)
r['mesh_bounds_m']=[lo.tolist(),hi.tolist()]
r['rerun_all_parameters_finite']=all(np.isfinite(c[k]).all() for k in ['poses','trans','betas'])
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
# Shared fixed translation for display; side-by-side spacing is the only per-actor offset.
center=((lo.min(0)+hi.max(0))/2).tolist();center[1]=0
(view/'manifest.json').write_text(json.dumps(dict(frames=n,fps=r['fps'],vertices=10475,chunk_frames=90,center=center,frame_mesh_error_m=frame_errors,report=r)))
shutil.copytree(ROOT/'outputs/smplx/wendy-viewer/vendor',view/'vendor',dirs_exist_ok=True)
for name in ['index.html','app.js']:shutil.copy(ROOT/'scripts/hiphi-comparison-viewer'/name,view/name)
print(json.dumps(r,indent=2))
