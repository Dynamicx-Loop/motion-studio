"""Compare direct head-fit ablations in the common UMR world frame."""
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from pitch import projected_heading, pitch_degrees, variant_pitch_degrees

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True, help='Fresh directory for analysis outputs')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
SOURCE = ROOT / 'externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
PARENTS = [-1,0,0,0,1,2,3,4,5,6,7,8,9,9,9,12,13,14,16,17,18,19]
BASIS = np.array([[1,0,0],[0,0,-1],[0,1,0.]])  # source Y-up -> UMR Z-up
s = np.load(SOURCE)
local = Rotation.from_rotvec(s['poses'][:240].reshape(-1,55,3)[:,:22].reshape(-1,3)).as_matrix().reshape(-1,22,3,3)
global_rot = local.copy()
for j,p in enumerate(PARENTS):
    if p >= 0: global_rot[:,j] = global_rot[:,p] @ local[:,j]
chest = global_rot[:,9,:,1] @ BASIS.T
head = global_rot[:,15,:,1] @ BASIS.T
forward = projected_heading(global_rot[:,0], BASIS)
neutral = np.load(OUT / 'neutral/motion_actor_smplx.npz')
neutral_root = Rotation.from_rotvec(neutral['poses'][:240, :3]).as_matrix()
neutral_forward = projected_heading(neutral_root, BASIS)
angle = lambda x: np.rad2deg(np.arccos(np.clip(x,-1,1)))
pitch = lambda axis: pitch_degrees(axis, forward)
stats = lambda a: {'mean':float(np.mean(a)), 'p95':float(np.percentile(a,95)), 'max':float(np.max(a))}
report = {'definition':'Positive pitch leans toward source pelvis projected +Z (forward); zero is world upright. Axis error compares SMPL-X spine3 global +Y to robot torso global +Z after Y-up -> Z-up conversion. No fitted alignment.', 'source':{'frame92':{'chest_pitch_deg':float(pitch(chest)[92]),'head_pitch_deg':float(pitch(head)[92]),'chest_tilt_deg':float(angle(chest[:,2])[92]),'head_chest_axis_deg':float(angle(np.sum(head*chest,axis=1))[92])}},'robots':{}}
arrays = {'source_chest':chest,'source_head':head,'source_forward':forward,'source_chest_pitch':pitch(chest)}
for robot in ['astro','g1']:
    data_by_variant = {}
    for variant in ['baseline','no-head','no-head-normal','no-head-point','no-head-samples','neutral-baseline','neutral-no-head']:
        path = OUT/f'{robot}-{variant}.npz'
        if not path.exists(): continue
        z=np.load(path,allow_pickle=True);q=z['qpos'];m=mujoco.MjModel.from_xml_path(str(z['robot_xml'].item()));d=mujoco.MjData(m)
        axes=[]
        for pose in q:
            d.qpos[:]=pose;mujoco.mj_forward(m,d);axes.append(d.xmat[m.body('torso_link').id].reshape(3,3)[:,2].copy())
        axes=np.array(axes)
        target = np.tile([0.,0.,1.],(len(q),1)) if variant.startswith('neutral') else chest[:len(q)]
        err=angle(np.sum(target*axes,axis=1));pt=variant_pitch_degrees(axes, variant, forward, neutral_forward) if len(q)==240 else None
        joint_ids=np.flatnonzero(m.jnt_type==mujoco.mjtJoint.mjJNT_HINGE);adr=m.jnt_qposadr[joint_ids]
        config=json.loads((ROOT/f'experiments/hiphi-robot-control/configs/{robot}-reference-resolved.json').read_text())
        violations=[]
        for jid in joint_ids:
            lo,hi=m.jnt_range[jid] if m.jnt_limited[jid] else (-np.inf,np.inf)
            override=config['robot'].get('joint_limits',{}).get(m.joint(int(jid)).name)
            if override: lo=max(lo,float(override[0]));hi=min(hi,float(override[1]))
            violations.append(np.maximum(lo-q[:,m.jnt_qposadr[jid]],q[:,m.jnt_qposadr[jid]]-hi))
        item={'torso_axis_error_deg':stats(err),'robot_tilt_deg':stats(angle(axes[:,2])),'all_finite':bool(np.isfinite(q).all()),'joint_limit_violation_rad':max(0,float(np.max(violations))),'joint_step_rad':stats(np.abs(np.diff(q[:,adr],axis=0))), 'frame_ids_match':bool(np.array_equal(z['frame_ids'],np.arange(len(q))))}
        if len(q)>92:
            item['frame92']={'torso_pitch_deg':float(pt[92]),'torso_axis_error_deg':float(err[92]),'torso_tilt_deg':float(angle(axes[:,2])[92]),'waist_pitch_deg':float(np.rad2deg(q[92,m.jnt_qposadr[m.joint('waist_pitch_joint').id]]))}
            item['window60_150_axis_error_deg']=stats(err[60:151]);item['window60_150_pitch_deg']=stats(pt[60:151])
        d.qpos[:]=m.qpos0
        for name,value in config['robot']['tpose_qpos'].items(): d.qpos[m.jnt_qposadr[m.joint(name).id]]=value
        mujoco.mj_forward(m,d)
        item['configured_tpose_torso_tilt_deg']=float(angle(d.xmat[m.body('torso_link').id].reshape(3,3)[2,2]))
        if variant=='baseline':
            full=np.load(ROOT/f'experiments/hiphi-robot-control/{robot}/reference.npz')['qpos'][:240]
            item['prefix_vs_full_max_qpos_abs_frames0_180']=float(np.max(np.abs(q[:181]-full[:181])))
        data_by_variant[variant]=item
        arrays[f'{robot}_{variant}_axis']=axes;arrays[f'{robot}_{variant}_error']=err
        if pt is not None: arrays[f'{robot}_{variant}_pitch']=pt
    report['robots'][robot]=data_by_variant
(args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez_compressed(args.output/'metrics.npz',**arrays)
print(json.dumps(report,indent=2))

# Independent original-BVH check, before conversion into SMPL-X.
from hiphi2smplx.bvh import load_bvh
from hiphi2smplx.kinematics import forward_kinematics
bvh_path=next(SOURCE.parent.glob('*.bvh'))
clip=load_bvh(bvh_path)
local_bvh=Rotation.from_rotvec(clip.local_rotations.reshape(-1,3)).as_matrix().reshape(*clip.local_rotations.shape[:2],3,3)
positions,rotations=forward_kinematics(local_bvh,clip.local_translations,clip.root_translations,clip.skeleton.parents)
heading=rotations[92,0,:,2].copy();heading[1]=0;heading/=np.linalg.norm(heading)
source_pitch=lambda v:float(np.degrees(np.arctan2(v@heading,v[1])))
crosscheck={'original_bvh_frame92':{},'bvh_path':str(bvh_path)}
for name in ['Spine','Spine2','Spine4','Neck','Head']:
    index=clip.skeleton.joint_names.index(name)
    crosscheck['original_bvh_frame92'][name+'_axis_pitch_deg']=source_pitch(rotations[92,index,:,1])
joints=s['fitted_joints'][92]
crosscheck['smplx_anatomical_frame92']={'hips_to_shoulders_pitch_deg':source_pitch((joints[16]+joints[17])/2-(joints[1]+joints[2])/2),'spine3_to_neck_pitch_deg':source_pitch(joints[12]-joints[9])}
(args.output/'source-crosscheck.json').write_text(json.dumps(crosscheck,indent=2)+'\n')
# Assert hierarchy against the model artifact, rather than trusting a copied table.
model_parents=np.load(ROOT/'externals/UMR/smpl/SMPLX_NEUTRAL.npz',allow_pickle=True)['kintree_table'][0,:22].astype(np.int64)
model_parents[0]=-1
assert np.array_equal(model_parents,PARENTS)
