from pathlib import Path
import sys,json,numpy as np,mujoco
R=Path('/data/workspace/motion_studio');sys.path.insert(0,str(R/'externals/UMR-astro-surface-experiment/scripts'))
import smpl_surface_retarget_common as c
config=json.loads((R/'experiments/umr-motion-fist-v1/smplx_astro_bbox50_raw.json').read_text());m=mujoco.MjModel.from_xml_path(config['robot']['xml']);limits,matched=c.build_scalar_joint_limits(m,config['robot']['joint_limits']);fist=json.loads((R/'experiments/astro-fist-static-v1/canonical-asset.json').read_text())['fixed_finger_positions_rad'];assert set(fist).issubset(matched)
q=c.clamp_joint_ranges(m,m.qpos0,joint_limits_by_qpos=limits)
lo,hi=c.qvel_step_bounds(m,q,.15,joint_limits_by_qpos=limits)
dq=c.solve_clarabel_qp_step(np.eye(m.nv),np.ones(m.nv),.001,lo,hi)
for n,v in fist.items():
 j=m.joint(n);a=int(j.qposadr[0]);d=int(j.dofadr[0]);assert q[a]==v and abs(dq[d])<1e-9 and lo[d]==hi[d]==0
assert abs(dq).max()>.01
print('14 preset clamps and QP constraints verified against nonzero conflicting objective; body DOFs remain free')
