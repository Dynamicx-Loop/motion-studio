"""Stream every full-clip SMPL-X frame to one-second local browser chunks."""
import json, shutil
from pathlib import Path
import numpy as np
import torch
import smplx
ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'configs/umr/wendy-full.json').read_text())
path=ROOT/c['output']; out=path.parent/'wendy-full-viewer';out.mkdir(exist_ok=True)
z=np.load(path);d=np.load(path.with_suffix('.diagnostics.npz'))
model=smplx.SMPLX(c['model'],gender='neutral',use_pca=False,flat_hand_mean=True,batch_size=1).to('cuda')
low=np.full(3,np.inf);high=-low;max_error=0;first_height=None;center=None
with torch.no_grad():
 for chunk_start in range(0,len(z['poses']),120):
  chunks=[]
  for start in range(chunk_start,min(chunk_start+120,len(z['poses'])),30):
   pose=torch.tensor(z['poses'][start:min(start+30,len(z['poses']))],device='cuda');n=len(pose)
   result=model(betas=torch.tensor(z['betas'],device='cuda').expand(n,-1),
    global_orient=pose[:,:3],body_pose=pose[:,3:66],jaw_pose=pose[:,66:69],
    leye_pose=pose[:,69:72],reye_pose=pose[:,72:75],left_hand_pose=pose[:,75:120],right_hand_pose=pose[:,120:165],
    transl=torch.tensor(z['trans'][start:start+n],device='cuda'),expression=torch.zeros(n,10,device='cuda'))
   v=result.vertices.cpu().numpy();j=result.joints[:,:22].cpu().numpy()
   assert np.isfinite(v).all() and np.isfinite(j).all()
   low=np.minimum(low,v.min((0,1)));high=np.maximum(high,v.max((0,1)))
   max_error=max(max_error,float(np.linalg.norm(j-d['fitted_joints'][start:start+n],axis=-1).max()))
   if first_height is None:first_height=float(np.ptp(v[0,:,1]));center=j[0,0].tolist()
   chunks.append(v)
  np.concatenate(chunks).astype('<f4').tofile(out/f'vertices-{chunk_start//120:03d}.bin')
  print(f'Baked {min(chunk_start+120,len(z["poses"]))}/{len(z["poses"])} frames',flush=True)
np.asarray(model.faces,dtype='<u4').tofile(out/'faces.bin')
d['source_joints'].astype('<f4').tofile(out/'source.bin')
report=json.loads(path.with_suffix('.report.json').read_text())
report.update(mesh_bounds=[low.tolist(),high.tolist()],mesh_min_y_m=float(low[1]),mesh_joint_vs_ik_max_m=max_error,mesh_height_first_frame_m=first_height)
path.with_suffix('.report.json').write_text(json.dumps(report,indent=2)+'\n')
manifest=dict(frames=len(z['poses']),vertices=10475,fps=float(z['mocap_framerate']),chunk_frames=120,
 source_joints=d['source_joints'].shape[1],source_parents=d['source_parents'].tolist(),center=center,report=report)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
for name in ('index.html','app.js'):shutil.copy(ROOT/'scripts/wendy-full-viewer'/name,out/name)
shutil.copytree(ROOT/'outputs/smplx/wendy-viewer/vendor',out/'vendor',dirs_exist_ok=True)
print(json.dumps(report,indent=2))
