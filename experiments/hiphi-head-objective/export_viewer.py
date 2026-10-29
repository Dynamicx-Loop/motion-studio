"""Export the controlled baseline/no-head prefix without touching baseline viewer."""
import json
import shutil
from pathlib import Path
import numpy as np
import mujoco

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
VIEW=OUT/'viewer';VIEW.mkdir(exist_ok=True)
OLD=ROOT/'experiments/hiphi-robot-control/viewer'
basis=np.array([[1,0,0],[0,0,1],[0,-1,0.]])
original=json.loads((OLD/'manifest.json').read_text())
metrics=json.loads((OUT/'report.json').read_text())
m={'frames':240,'fps':original['fps'],'robots':{},'head_report':metrics}
for robot in ['astro','g1']:
    info=original['robots'][robot]
    for part in info['parts']:
        for key in ['vertices','faces']:shutil.copy2(OLD/part[key],VIEW/part[key])
    pair=[];variants=[]
    for variant in ['baseline','no-head']:
        z=np.load(OUT/f'{robot}-{variant}.npz',allow_pickle=True);q=z['qpos'];pair.append(q)
        model=mujoco.MjModel.from_xml_path(str(z['robot_xml'].item()));data=mujoco.MjData(model)
        ids=[i for i in range(model.ngeom) if model.geom_group[i]==1 and model.geom_type[i]==mujoco.mjtGeom.mjGEOM_MESH]
        assert len(ids)==len(info['parts'])
        transforms=np.empty((len(q),len(ids),12),dtype='<f4')
        for t,pose in enumerate(q):
            data.qpos[:]=pose;mujoco.mj_forward(model,data)
            for k,i in enumerate(ids):
                transforms[t,k,:9]=(basis@data.geom_xmat[i].reshape(3,3)).ravel()
                transforms[t,k,9:]=basis@data.geom_xpos[i]
        filename=f'{robot}-{variant}-transforms.bin';transforms.tofile(VIEW/filename);variants.append({'transforms':filename})
    adr=model.jnt_qposadr[np.flatnonzero(model.jnt_type==mujoco.mjtJoint.mjJNT_HINGE)]
    delta=np.degrees(pair[0][:,adr]-pair[1][:,adr]);rms=np.sqrt(np.mean(delta**2,axis=1))
    m['robots'][robot]={'parts':info['parts'],'variants':variants,'center':info['center'],'frame_joint_rms_deg':rms.tolist(),'report':{'joint_angle_difference_deg':{'mean':float(np.abs(delta).mean())},'root_position_difference_m':{'mean':float(np.linalg.norm(pair[0][:,:3]-pair[1][:,:3],axis=1).mean())},'largest_joint_difference_at':{'frame_index':92}}}
    m['robots'][robot]['pitch']={v:np.load(OUT/'metrics.npz')[f'{robot}_{v}_pitch'].tolist() for v in ['baseline','no-head']}
m['source_pitch']=np.load(OUT/'metrics.npz')['source_chest_pitch'].tolist()
(VIEW/'manifest.json').write_text(json.dumps(m))
shutil.copytree(OLD/'vendor',VIEW/'vendor',dirs_exist_ok=True)
html=(ROOT/'scripts/hiphi-robot-viewer/index.html').read_text().replace('HiPHI · robot retarget control','HiPHI · head objective ablation').replace('Getting_up-get_up_0004 · robot control experiment','Does disabling the head remove backward lean?').replace('5,468 frames · 60.75 seconds · shared correspondence within each pair · default finger clearing','240-frame sequential prefix · same correspondence and source · direct head costs 1/1 → 0/0').replace('Blue · shipped SMPL-X input','Blue · baseline head fit').replace('Orange · fresh conversion input','Orange · direct head fit disabled').replace('Largest difference','Screenshot frame 93')
(VIEW/'index.html').write_text(html)
js=(ROOT/'scripts/hiphi-robot-viewer/app.js').read_text().replace('let playing=true,t=0,last=null,current=-1','let playing=false,t=92/m.fps,last=null,current=-1').replace("el('frame').max=m.frames-1;","el('frame').max=m.frames-1;el('play').textContent='Play';")
js=js.replace("el('metrics').textContent=`Joint RMS difference: ${m.robots[el('robot').value].frame_joint_rms_deg[i].toFixed(3)}°`;","const p=m.robots[el('robot').value].pitch;el('metrics').textContent=`Pitch: human chest ${m.source_pitch[i].toFixed(2)}° · baseline ${p.baseline[i].toFixed(2)}° · no head ${p['no-head'][i].toFixed(2)}° (negative = backward)`;")
js=js.replace("el('front').onclick=()=>view(0,.3,6.5);el('side').onclick=()=>view(6,1,3);","el('front').onclick=()=>view(-6.5,.3,0);el('side').onclick=()=>view(0,.3,6.5);")
(VIEW/'app.js').write_text(js)
(VIEW/'favicon.ico').write_bytes(b'')
print(VIEW)
