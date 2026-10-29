"""Audit the shipped reference; optionally rerun conversion from its original BVH.
No alignment, rescaling, time warping, or parameter tuning is performed.
"""
import argparse, hashlib, json
from dataclasses import asdict
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from hiphi2smplx.smplx import load_smplx_body
from hiphi2smplx.kinematics import forward_kinematics
from hiphi2smplx.pipeline import ConversionConfig, fit_bvh, save_result
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--bvh', type=Path)
a = p.parse_args()
ref = ROOT/'externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
model = Path(json.loads((ROOT/'configs/umr/wendy-full.json').read_text())['model'])
out = ROOT/'experiments/hiphi-conversion-control'; out.mkdir(exist_ok=True)
z = np.load(ref); pose = z['poses'].reshape(-1,55,3); n=len(pose)
def stats(x):
 return dict(mean=float(np.mean(x)),p95=float(np.percentile(x,95)),max=float(np.max(x)))
def joints(betas):
 body=load_smplx_body(model,betas)
 rot=Rotation.from_rotvec(pose[:,:22].reshape(-1,3)).as_matrix().reshape(n,22,3,3)
 return forward_kinematics(rot,np.broadcast_to(body.skeleton.rest_offsets,(n,22,3)),z['trans']+body.rest_joints[0],body.skeleton.parents)[0]
matched=joints(z['betas']); zero=joints(np.zeros(10))
report=dict(reference=str(ref),sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),model=str(model),
 frames=n,fps=float(z['fps']),duration_s=n*float(z['frame_time']),
 all_numeric_fields_finite=all(np.isfinite(z[k]).all() for k in z.files if z[k].dtype.kind in 'fiu'),
 pose_alias_exact=bool(np.array_equal(z['poses'],z['smpl_pose_axis_angle'].reshape(n,165))),
 translation_alias_exact=bool(np.array_equal(z['trans'],z['transl'])),
 matched_shape_joint_reconstruction_m=stats(np.linalg.norm(matched-z['fitted_joints'],axis=-1)),
 zero_shape_change_world_m=stats(np.linalg.norm(zero-matched,axis=-1)),
 zero_shape_change_root_relative_m=stats(np.linalg.norm((zero-zero[:,:1])-(matched-matched[:,:1]),axis=-1)),
 stored_source_fit_residual_m=stats(z['per_frame_residuals']),
 nonzero_hand_frames=int(np.any(pose[:,25:]!=0,axis=(1,2)).sum()),
 original_bvh_available=bool(a.bvh),validation_status='reference audit only; original BVH required')
config=ConversionConfig(progress=True)
report['rerun_settings']=asdict(config)
if a.bvh:
 r=fit_bvh(a.bvh,model,z['betas'],config=config,skeleton_map='hiphi')
 if len(r.poses)!=n or not np.isclose(r.frame_time,float(z['frame_time']),rtol=1e-6):
  raise ValueError('Source frame count/timing mismatch; refusing automatic alignment')
 save_result(out/'reconverted.npz',r)
 report['bvh_sha256']=hashlib.sha256(a.bvh.read_bytes()).hexdigest()
 report['body_joint_error_m']=stats(np.linalg.norm(r.fitted_joints-matched,axis=-1))
 report['translation_error_m']=stats(np.linalg.norm(r.trans-z['trans'],axis=-1))
 # Wrist orientation was overwritten by external MANO in the shipped reference.
 pr=Rotation.from_rotvec(pose[:,:20].reshape(-1,3))
 rr=Rotation.from_rotvec(r.poses[:,:20].reshape(-1,3))
 report['non_wrist_body_rotation_error_deg']=stats(np.degrees((pr.inv()*rr).magnitude()))
 report['rerun_source_fit_residual_m']=stats(r.residuals)
 report['validation_status']='matched source comparison completed; inspect metrics, not ground-truth accuracy'
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
