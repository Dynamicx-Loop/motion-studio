"""Measure retarget torso-axis error against the same source frames."""
import argparse,json
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from hiphi2smplx.skeleton import SMPLX_BODY_PARENTS
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('--assert-improved',action='store_true');p.add_argument('--frame',type=int);a=p.parse_args()
s=np.load(R/'outputs/smplx/wendy_happy_dance_6s_9s.npz');z=np.load(a.result,allow_pickle=True)
poses=s['poses'].reshape(-1,55,3)
local=Rotation.from_rotvec(poses[:,:22].reshape(-1,3)).as_matrix().reshape(-1,22,3,3)
global_rot=local.copy()
for j,parent in enumerate(SMPLX_BODY_PARENTS):
 if parent>=0: global_rot[:,j]=global_rot[:,parent]@local[:,j]
# Chest/spine3 local +Y is the human upright axis. Robot torso local +Z.
human=global_rot[:,9,:,1]
m=mujoco.MjModel.from_xml_path(str(z['robot_xml'].item()));d=mujoco.MjData(m)
bid=m.body('torso_link').id
basis=np.array([[1,0,0],[0,0,1],[0,-1,0]])
robot=[]; limb_vectors={'left':[], 'right':[]}
for q in z['qpos']:
 d.qpos[:]=q;mujoco.mj_forward(m,d);robot.append(basis@d.xmat[bid].reshape(3,3)[:,2])
 for side in limb_vectors:
  limb_vectors[side].append(basis@(d.xpos[m.body(side+'_wrist_yaw_link').id]-d.xpos[m.body(side+'_shoulder_pitch_link').id]))
robot=np.array(robot)
angle=lambda dot:np.rad2deg(np.arccos(np.clip(dot,-1,1)))
h=angle(human[:,1]);r=angle(robot[:,1]);err=angle(np.sum(human*robot,axis=1))
idx=np.arange(len(err)) if a.frame is None else np.array([a.frame])
report={'torso_axis_error_mean_deg':float(err[idx].mean()),'torso_axis_error_p95_deg':float(np.percentile(err[idx],95)),'human_tilt_mean_deg':float(h[idx].mean()),'robot_tilt_mean_deg':float(r[idx].mean()),'robot_tilt_max_deg':float(r[idx].max()),'frame330':{'human_tilt':float(h[330]),'robot_tilt':float(r[330]),'axis_error':float(err[330])}}
source_joints=np.load(R/'outputs/smplx/wendy_happy_dance_6s_9s.diagnostics.npz')['fitted_joints']
for side,shoulder,wrist in [('left',16,20),('right',17,21)]:
 hv=source_joints[:,wrist]-source_joints[:,shoulder];rv=np.asarray(limb_vectors[side])
 hv/=np.linalg.norm(hv,axis=1)[:,None];rv/=np.linalg.norm(rv,axis=1)[:,None]
 report[side+'_arm_direction_error_mean_deg']=float(angle(np.sum(hv*rv,axis=1)).mean())
print(json.dumps(report,indent=2))
a.result.with_suffix('.torso-report.json' if a.frame is None else '.torso-frame-report.json').write_text(json.dumps(report,indent=2)+'\n')
if a.assert_improved:
 # Acceptance for this surface-based fit: substantial torso improvement with
 # bounded arm-direction tradeoff, measured against the untouched baseline.
 baseline_path=R/'outputs/umr/astro_p2_29dof/wendy_6s_9s/retarget.torso-report.json'
 baseline=json.loads(baseline_path.read_text())
 assert report['torso_axis_error_mean_deg'] < baseline['torso_axis_error_mean_deg']*.4, 'Mean torso error did not improve by 60%'
 assert report['torso_axis_error_p95_deg'] < baseline['torso_axis_error_p95_deg']*.4, 'P95 torso error did not improve by 60%'
 assert report['frame330']['axis_error'] < 5, 'Raised-arm torso mismatch remains above 5 degrees'
 for side in ('left','right'):
  key=side+'_arm_direction_error_mean_deg'
  assert report[key] < baseline[key]+5, 'Arm-direction tradeoff exceeds 5 degrees'
 print('PASS: torso improvement and arm tradeoff checks')
