#!/usr/bin/env python3
"""Explicit 3-frame/2-epoch native smoke cohort; never full/default acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from motion_studio.studio import Studio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='Fresh absolute smoke output directory')
    parser.add_argument('--primitive', action='store_true', help='Primitive imported robot; stop at pre-solve binding')
    args = parser.parse_args()
    output = args.output.resolve()
    checkout = Path('/data/workspace/motion_studio/externals/UMR')
    if any(output.is_relative_to(p) for p in (checkout, ROOT/'externals')):
        parser.error('Smoke output must be outside external source trees')
    output.mkdir(parents=True, exist_ok=False)
    studio = Studio(output/'state')
    source = checkout/'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
    import numpy as np
    with np.load(source, allow_pickle=False) as data:
        arrays = {name:data[name] for name in data.files}
    for name in ('poses','pose_aa','trans','trans_orig','transl','smpl_pose_axis_angle'):
        if name in arrays and arrays[name].ndim >= 2:
            arrays[name] = arrays[name][:3]
    np.savez(output/'three-frame-source.npz', **arrays)
    if args.primitive:
        xml = output/'primitive.xml'
        xml.write_text('<mujoco><compiler angle="radian"/><worldbody><body name="pelvis"><freejoint/>'
            '<geom type="box" size=".16 .12 .25"/><body name="torso" pos="0 0 .4">'
            '<joint name="shoulder" range="-1 1"/><geom type="capsule" size=".13 .2"/>'
            '</body></body></worldbody></mujoco>')
        robot = studio.import_robot(xml)
        pose = [.2,-.1,1.,.9238795325112867,0.,0.,.3826834323650898,.4]
        torso = 'torso'
    else:
        robot = studio.import_robot(checkout/'assets/g1/g1_29dof.xml', derive_free_root=True)
        pose = list(robot.default_qpos)
        g1 = json.loads((checkout/'robot_configs/humanoid_retarget_unitree_g1_example.json').read_text())['robot']
        for joint in robot.joints:
            pose[joint.qpos_index] = g1['tpose_qpos'].get(joint.name, pose[joint.qpos_index])
        torso = 'waist_yaw_link'
    draft = studio.create_draft('Primitive pre-solve binding smoke' if args.primitive else 'G1 3-frame/2-epoch smoke; not full/default acceptance')
    run = studio.save_robot_pose(draft.run_id, robot.asset_id, name='Smoke reference pose', qpos=pose, torso_body=torso)
    motion = studio.import_motion(output/'three-frame-source.npz')
    run = studio.select_motion(run.run_id, motion.asset_id)
    job = studio.start_execution(run.run_id, through='binding' if args.primitive else 'retargeting',
        settings={'sampling_seed':0, 'epochs':2, 'trajectory_filter':'none'})
    while True:
        job = studio.get_job(job['job_id'])
        print(json.dumps({k:job.get(k) for k in ('job_id','status','stage','progress','message')}), flush=True)
        if job['status'] not in ('queued','running','cancelling'):
            break
        time.sleep(1)
    (output/'smoke.json').write_text(json.dumps({'source':str(source),
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'fixture_conversion':'First three pose/translation frames only; source preserved; no resampling',
        'cohort':'Focused 2-epoch smoke, not full-clip/default acceptance', 'job':job}, indent=2))
    if job['status'] != 'completed':
        print(studio.job_file(job['job_id']).read_text()[-12000:], file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
