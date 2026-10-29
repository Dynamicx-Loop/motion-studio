"""Measure source/target landmark alignment and observed wrist leakage, no solve."""
import json
import sys
from pathlib import Path
from collections import Counter
import numpy as np
import mujoco
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/astro-hand-wrist-correction'
sys.path.insert(0,str(ROOT/'externals/UMR-astro-surface-experiment/scripts'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb
from humanoid_retarget_config import load_config

def quantiles(x):return np.percentile(x,[0,10,50,90,100]).tolist()
def main():
    weights=np.load(ROOT/'outputs/soma-correspondence-audit/human-weight-diagnostics.npz')
    results={}
    for robot,experiment in [('astro','astro-hands-correspondence'),('g1','soma-correspondence-audit')]:
        for source in ['smplx','soma']:
            for center in ['spine1','bbox50']:
                arm=f'{source}_{robot}_{center}';c=load_config(ROOT/f'experiments/{experiment}/{arm}.json')
                ds=np.load(c['correspondence']['dataset']['out'],allow_pickle=True)
                slots=np.load(Path(c['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz',allow_pickle=True)
                a=np.load(ROOT/f'outputs/{experiment}/{arm}-audit.npz')
                model=mujoco.MjModel.from_xml_path(c['robot']['xml']);data=mujoco.MjData(model)
                build.apply_joint_qpos(model,data,c['robot']['tpose_qpos'],required=True);mujoco.mj_forward(model,data)
                v,f,owners,origin,rot,_=rb.collect_root_mesh(model,data,rb.visual_geom_ids(model,'auto'),c['robot']['point_cloud_center'])
                fm=np.array([model.mesh(int(model.geom_dataid[g])).name for g in owners])
                hheight=float(np.ptp(ds['mesh_vertices_0'][:,1]));rheight=float(np.ptp(v[:,2]))
                sample_mesh=fm[ds['sample_face_ids_1']]
                names=list(weights[source+'_joint_names']);joints=weights[source+'_joints']-ds['root_offsets'][0]
                result={'source_height':hheight,'target_height':rheight,'normalization_scales':slots['normalization_scales'].tolist(),'sides':{}}
                for side in ['left','right']:
                    sign=1 if side=='left' else -1
                    srcw=names.index(side[0].upper()+'_Wrist' if source=='smplx' else side.title()+'Hand')
                    srce=names.index(side[0].upper()+'_Elbow' if source=='smplx' else side.title()+'ForeArm')
                    anchors={j:((data.xanchor[model.joint(side+'_'+j+'_joint').id]-origin)@rot).tolist() for j in ['elbow','wrist_roll','wrist_pitch','wrist_yaw']}
                    bnames=[side+'_hand_link',side+'_hand_palm_link']
                    bodies={n:((data.xpos[model.body(n).id]-origin)@rot).tolist() for n in bnames if mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,n)>=0}
                    mesh_names=sorted(set(fm[(np.char.startswith(fm,side+'_'))&np.array(['hand' in n for n in fm])]))
                    face_mask=np.isin(fm,mesh_names);verts=v[np.unique(f[face_mask])]
                    mask=a['source_common']==side+'Hand';wrist=mask&np.char.startswith(a['mesh_names'],side+'_wrist_')
                    actual=mask&np.isin(a['mesh_names'],mesh_names);sample=np.isin(sample_mesh,mesh_names)
                    rp=a['robot_projected'];learn=a['robot_learned'];human=a['human']
                    result['sides'][side]={'source_wrist_normalized':(joints[srcw]/hheight).tolist(),'source_elbow_normalized':(joints[srce]/hheight).tolist(),'target_joints_normalized':{n:(np.array(p)/rheight).tolist() for n,p in anchors.items()},'target_hand_bodies_normalized':{n:(np.array(p)/rheight).tolist() for n,p in bodies.items()},'physical_hand_meshes':mesh_names,'hand_mesh_sample_count':int(sample.sum()),'hand_mesh_bounds_normalized':[(verts.min(0)/rheight).tolist(),(verts.max(0)/rheight).tolist()],'source_hand_outward_quantiles_normalized':quantiles(sign*human[mask,0]/hheight),'learned_hand_outward_quantiles_normalized':quantiles(sign*learn[mask,0]/rheight),'projected_hand_outward_quantiles_normalized':quantiles(sign*rp[mask,1]/rheight),'source_hand_count':int(mask.sum()),'actual_hand_count':int(actual.sum()),'wrist_count':int(wrist.sum()),'high_confidence_wrist_count':int((wrist&a['high_confidence']).sum()),'wrist_source_LBS_group_weight_quantiles':quantiles(a['source_group_weight'][wrist]) if wrist.any() else [],'destinations':dict(Counter(a['mesh_names'][mask])),'actual_hand_sample_outward_quantiles_normalized':quantiles(sign*rb.smpl_frame_to_robot_root(ds['points'][1][sample])[:,1]/rheight)}
                results[arm]=result
    (HERE/'diagnosis.json').write_text(json.dumps(results,indent=2)+'\n')
    for arm,r in results.items():
        print(arm)
        for side,s in r['sides'].items():print(side,'source wrist',s['source_wrist_normalized'],'target hand roots',s['target_hand_bodies_normalized'],'human x',s['source_hand_outward_quantiles_normalized'],'learned x',s['learned_hand_outward_quantiles_normalized'],'hand samples',s['hand_mesh_sample_count'],'wrist high',s['wrist_count'],s['high_confidence_wrist_count'])

if __name__=='__main__':main()
