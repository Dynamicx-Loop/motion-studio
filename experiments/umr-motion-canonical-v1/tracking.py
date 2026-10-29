"""Independent root-relative anatomical landmark proxy, not UMR objective residual."""
from pathlib import Path
import json,numpy as np,mujoco
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'outputs/umr-motion-canonical-v1'
j=np.load(OUT/'viewer/source-joints.npy');j=j[:,:,:3]@np.array([[1,0,0],[0,0,1],[0,-1,0]])
r=json.loads((HERE/'results.json').read_text())
def stats(x):return {'mean_m':float(x.mean()),'p95_m':float(np.percentile(x,95)),'max_m':float(x.max())}
for arm,a in r.items():
 z=np.load(OUT/arm/'trajectory.npz',allow_pickle=True);q=z['qpos'];m=mujoco.MjModel.from_xml_path(str(z['robot_xml'].item()));d=mujoco.MjData(m)
 pairs={'left_wrist':('left_wrist_yaw_link',20),'right_wrist':('right_wrist_yaw_link',21),'left_ankle':('left_ankle_roll_link',7),'right_ankle':('right_ankle_roll_link',8)}
 body={k:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,n) for k,(n,_) in pairs.items()};errors={k:[] for k,v in body.items() if v>=0}
 for t,p in enumerate(q):
  d.qpos[:]=p;mujoco.mj_forward(m,d)
  for k in errors:
   source=(j[t,pairs[k][1]]-j[t,0])*a['smpl_scale'];robot=d.xpos[body[k]]-p[:3]
   errors[k].append(np.linalg.norm(robot-source))
 a['root_relative_anatomical_proxy']={'definition':'Euclidean error between robot wrist-yaw/ankle-roll body origin relative to free root and scaled SMPL-X wrist/ankle joint relative to pelvis; no fitted rotation. Morphology and differing joint centers contribute. Not learned surface residual or a quality ranking.','landmarks':{k:stats(np.array(v)) for k,v in errors.items()}}
(HERE/'results.json').write_text(json.dumps(r,indent=2)+'\n');(OUT/'viewer/results.json').write_text(json.dumps(r,indent=2)+'\n')
