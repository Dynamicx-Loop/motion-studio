"""Bake the exact processed source (finger poses zeroed) in metres, Y up."""
from pathlib import Path
import json,numpy as np,torch,smplx
ROOT=Path(__file__).resolve().parents[2];VIEW=ROOT/'outputs/umr-motion-canonical-v1/viewer'
c=json.loads((Path(__file__).parent/'smplx_g1_spine1_raw.json').read_text());z=np.load(c['motion']['data']);p=z['poses'][0:5468:3].copy();p[:,75:]=0;t=z['trans'][0:5468:3]
m=smplx.SMPLX(c['smplx_model_dir'],gender='neutral',use_pca=False,flat_hand_mean=True,batch_size=1).to('cuda')
vs=[]; js=[]
with torch.no_grad():
 for s in range(0,len(p),30):
  a=torch.as_tensor(p[s:s+30],device='cuda');n=len(a)
  result=m(betas=torch.as_tensor(z['betas'],device='cuda').expand(n,-1),global_orient=a[:,:3],body_pose=a[:,3:66],jaw_pose=a[:,66:69],leye_pose=a[:,69:72],reye_pose=a[:,72:75],left_hand_pose=a[:,75:120],right_hand_pose=a[:,120:165],transl=torch.as_tensor(t[s:s+30],device='cuda'),expression=torch.zeros(n,10,device='cuda'));v=result.vertices.cpu().numpy();vs.append(v);js.append(result.joints.cpu().numpy())
np.save(VIEW/'source-joints.npy',np.concatenate(js));v=np.concatenate(vs);assert np.isfinite(v).all();v.astype('<f4').tofile(VIEW/'source-v.bin');np.asarray(m.faces,dtype='<u4').tofile(VIEW/'source-f.bin')
(VIEW/'source.json').write_text(json.dumps({'vertices':v.shape[1],'frames':len(v),'center':[float(t[0,0]),0,float(t[0,2])],'finger_pose':'zeroed matching solver','units':'metres','up':'Y'}))
