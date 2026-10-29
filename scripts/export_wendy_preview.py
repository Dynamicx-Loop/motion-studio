"""Bake local SMPL-X meshes for an offline browser preview; no model weights copied."""
import json
import shutil
from pathlib import Path
import numpy as np
import torch
import smplx
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'configs/umr/wendy-dance-preview.json').read_text())
path=ROOT/config['output']
out=path.parent/'wendy-viewer'
out.mkdir(exist_ok=True)
z=np.load(path)
d=np.load(path.with_suffix('.diagnostics.npz'))
device='cuda'
model=smplx.SMPLX(config['model'],gender='neutral',use_pca=False,flat_hand_mean=True,batch_size=30).to(device)
vertices=[]; joints=[]
with torch.no_grad():
    for start in range(0,len(z['poses']),30):
        pose=torch.tensor(z['poses'][start:start+30],device=device)
        n=len(pose)
        result=model(betas=torch.tensor(z['betas'],device=device).expand(n,-1),
            global_orient=pose[:,:3],body_pose=pose[:,3:66],jaw_pose=pose[:,66:69],
            leye_pose=pose[:,69:72],reye_pose=pose[:,72:75],
            left_hand_pose=pose[:,75:120],right_hand_pose=pose[:,120:165],
            transl=torch.tensor(z['trans'][start:start+30],device=device),
            expression=torch.zeros(n,10,device=device))
        vertices.append(result.vertices.cpu().numpy())
        joints.append(result.joints[:,:22].cpu().numpy())
v=np.concatenate(vertices); j=np.concatenate(joints)
assert np.isfinite(v).all() and np.isfinite(j).all()
v.astype('<f4').tofile(out/'vertices.bin')
np.asarray(model.faces,dtype='<u4').tofile(out/'faces.bin')
d['source_joints'].astype('<f4').tofile(out/'source.bin')
report=json.loads(path.with_suffix('.report.json').read_text())
report.update(mesh_bounds=[v.min((0,1)).tolist(),v.max((0,1)).tolist()],
    mesh_min_y_m=float(v[:,:,1].min()),
    mesh_joint_vs_ik_max_m=float(np.linalg.norm(j-d['fitted_joints'],axis=-1).max()),
    mesh_height_first_frame_m=float(np.ptp(v[0,:,1])))
path.with_suffix('.report.json').write_text(json.dumps(report,indent=2)+'\n')
manifest=dict(frames=len(v),vertices=v.shape[1],fps=float(z['mocap_framerate']),
    start_frame=config['start_frame'], source_joints=d['source_joints'].shape[1],
    source_parents=d['source_parents'].tolist(), center=j[:,:,0:3].mean((0,1)).tolist(),report=report)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
for name in ('index.html','app.js'):
    shutil.copy(ROOT/'scripts/wendy-viewer'/name,out/name)
print(json.dumps(report,indent=2))
