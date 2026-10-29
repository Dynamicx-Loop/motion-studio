"""Show source curvature, robot silhouettes, and torso pitch on identical frames."""
import json
from pathlib import Path
import sys
import mujoco
# Host plotting package is read-only; prefer the UMR runtime for shared dependencies.
sys.path.append("/usr/lib/python3/dist-packages")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
z=np.load(OUT/'metrics.npz');report=json.loads((OUT/'report.json').read_text())
source=np.load(ROOT/'externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz')
f=z['source_forward'][92]
basis=np.array([[1,0,0],[0,0,-1],[0,1,0.]])
parents=[-1,0,0,0,1,2,3,4,5,6,7,8,9,9,9,12,13,14,16,17,18,19]
fig,ax=plt.subplots(2,3,figsize=(15,10),gridspec_kw={'height_ratios':[1.5,1]})
for i,(robot,variant,color) in enumerate([('source','source','#0b8059'),('astro','baseline','#247bb1'),('g1','baseline','#247bb1')]):
    a=ax[0,i]
    if robot=='source':
        joints=source['fitted_joints'][92]@basis.T
        origin=joints[0]@f
        for j,p in enumerate(parents):
            if p>=0:a.plot(joints[[p,j]]@f-origin,joints[[p,j],2],color=color,lw=3,marker='o',ms=4)
        start=joints[9];v=z['source_chest'][92]
        a.arrow(start@f-origin,start[2],.25*(v@f),.25*v[2],width=.008,color='#a23997',zorder=10)
        a.set_title('Actual human source\nChest −13.58°; hips→shoulders −3.97°')
    else:
        for variant,color,shift in [('baseline','#247bb1',-.27),('no-head','#d47b1e',.27)]:
            motion=np.load(OUT/f'{robot}-{variant}.npz',allow_pickle=True)
            m=mujoco.MjModel.from_xml_path(str(motion['robot_xml'].item()));d=mujoco.MjData(m);d.qpos[:]=motion['qpos'][92];mujoco.mj_forward(m,d)
            origin=d.qpos[:3]@f
            triangles=[]
            for g in range(m.ngeom):
                if m.geom_group[g]!=1 or m.geom_type[g]!=mujoco.mjtGeom.mjGEOM_MESH:continue
                mid=m.geom_dataid[g];va=m.mesh_vertadr[mid];vn=m.mesh_vertnum[mid];fa=m.mesh_faceadr[mid];fn=m.mesh_facenum[mid]
                vertices=m.mesh_vert[va:va+vn]@d.geom_xmat[g].reshape(3,3).T+d.geom_xpos[g]
                projected=np.stack([vertices@f-origin+shift,vertices[:,2]],axis=-1)
                triangles.extend(projected[m.mesh_face[fa:fa+fn]])
            a.add_collection(PolyCollection(triangles,facecolor=color,edgecolor='none',alpha=.9))
            body=m.body('torso_link').id;v=d.xmat[body].reshape(3,3)[:,2];start=d.xpos[body]
            a.arrow(start@f-origin+shift,start[2],.25*(v@f),.25*v[2],width=.008,color='#a23997',zorder=10)
        r=report['robots'][robot]
        a.set_title(f'{robot.upper()} · baseline / no head\n'+f"{r['baseline']['frame92']['torso_pitch_deg']:.2f}° / {r['no-head']['frame92']['torso_pitch_deg']:.2f}°")
    a.axhline(0,color='.7',lw=1);a.set_aspect('equal');a.set_xlim(-.6,.6);a.set_ylim(0,1.8);a.set_xlabel('Backward ←  forward distance (m)  → Forward');a.set_ylabel('Height (m)');a.grid(alpha=.15)
t=np.arange(240)/float(source['fps'])
for i,robot in enumerate(['astro','g1']):
    a=ax[1,i]
    a.plot(t,z['source_chest_pitch'],color='#0b8059',label='Human chest')
    for variant,color in [('baseline','#247bb1'),('no-head','#d47b1e')]:a.plot(t,z[f'{robot}_{variant}_pitch'],color=color,label=variant)
    a.axvline(t[92],color='.4',ls='--');a.axhline(0,color='.6',lw=1);a.set_title(robot.upper()+' · signed torso pitch');a.set_xlabel('Source time (s)');a.set_ylabel('Degrees (negative = backward)');a.legend();a.grid(alpha=.15)
a=ax[1,2];a.axis('off')
a.text(0,1,'Frame 92 (display 93), 1.022 s\n\nPurple arrows: chest/torso upright axes.\nHuman has a curved, articulated spine.\nRobot torso and head are rigidly coupled.\n\nHead-off increases backward pitch here.\nTrue neutral input stays near upright.\n\nSide projection uses source forward;\nno fitted orientation or height alignment.\nRobot pair has display offsets only.',va='top',fontsize=12)
fig.suptitle('Backward chest orientation is already present in the source',fontsize=18)
fig.tight_layout();fig.savefig(OUT/'head-ablation.png',dpi=150)
