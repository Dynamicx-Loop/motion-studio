"""Matched raw/calibrated measurements with fixed labels and physical mesh identities."""
import json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'outputs/astro-hand-wrist-correction'
sys.path.insert(0,str(ROOT/'externals/UMR-astro-surface-experiment/scripts'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb

def actual(names,side):return np.char.startswith(names,side+'_')&np.array(['hand' in n for n in names])
def main():
    controls=json.loads((HERE/'preparation.json').read_text())['controls'];results={}
    for arm,path in json.loads((HERE/'arms.json').read_text()).items():
        print('MEASURE',arm,flush=True);c=json.loads(Path(path).read_text());ds=np.load(c['correspondence']['dataset']['out'],allow_pickle=True)
        a=np.load(ROOT/'outputs'/controls[arm]['experiment']/f'{arm}-audit.npz');labels=a['source_common'];raw=a['robot_learned']
        model=mujoco.MjModel.from_xml_path(c['robot']['xml']);d=mujoco.MjData(model);build.apply_joint_qpos(model,d,c['robot']['tpose_qpos'],required=True);mujoco.mj_forward(model,d)
        v,f,o,_,_,_=rb.collect_root_mesh(model,d,rb.visual_geom_ids(model,'auto'),c['robot']['point_cloud_center']);fm=np.array([model.mesh(int(model.geom_dataid[g])).name for g in o]);ref=rb.smpl_frame_to_robot_root(ds['points'][1]);refnames=fm[ds['sample_face_ids_1']]
        results[arm]={}
        for k in [0,16,32,64]:
            p=raw if k==0 else np.load(OUT/arm/f'k{k}/correspondence_slots_final.npz')['reconstructed_slots'][1]
            b=rb.bind_robot_slots(model,SimpleNamespace(config_data=c),p);projected=b['root_points']
            # Binding face indices refer to the same unrestricted visual geometry.
            names=np.array([model.mesh(int(model.geom_dataid[g])).name for g in b['geom_ids']])
            displacement=np.linalg.norm(p-raw,axis=1)
            unchanged=np.isin(labels,['head/face','neck','torso','hips','leftUpLeg','rightUpLeg','leftLeg','rightLeg','leftFoot','rightFoot'])
            np.testing.assert_array_equal(p[unchanged],raw[unchanged]);np.testing.assert_allclose(projected[unchanged],a['robot_projected'][unchanged],atol=1e-7,rtol=0)
            pr=rb.smpl_frame_to_robot_root(p);nearest=cKDTree(ref).query(pr)[0];reverse=cKDTree(pr).query(ref)[0]
            row={'moved_slots':int((displacement>0).sum()),'max_displacement_mm':float(displacement.max()*1000),'mean_displacement_mm':float(displacement.mean()*1000),'mean_projection_distance_mm':float(np.linalg.norm(pr-projected,axis=1).mean()*1000),'symmetric_sample_mean_distance_mm':float((nearest.mean()+reverse.mean())*500),'central_head_legs_unchanged':True}
            for side in ['left','right']:
                mask=labels==side+'Hand';hand=actual(names,side);fingers=hand&np.array(['palm' not in n for n in names]) if '_astro_' in arm else np.zeros(len(names),bool)
                sample=actual(refnames,side);dist=cKDTree(projected[mask]).query(ref[sample])[0]
                wrist=np.char.startswith(names,side+'_wrist_')
                row[side]={'slots':int(mask.sum()),'actual_hand':int((mask&hand).sum()),'finger':int((mask&fingers).sum()),'wrist_housing':int((mask&wrist).sum()),'other':int((mask&~(hand|wrist)).sum()),'nonhand_on_hand':int((~mask&hand).sum()),'hand_reference_samples':int(sample.sum()),'actual_hand_coverage20mm':float((dist<=.02).mean()),'hand_mean_displacement_mm':float(displacement[mask].mean()*1000),'high_confidence_actual_hand':int((mask&a['high_confidence']&hand).sum()),'source_hand_projection_distance_mm':float(np.linalg.norm(pr[mask]-projected[mask],axis=1).mean()*1000),'nonhand_sources_on_hand':{str(x):int(((labels==x)&hand).sum()) for x in np.unique(labels[~mask&hand])}}
            results[arm][str(k)]=row
        print(arm,[(s,results[arm]['0'][s]['actual_hand'],results[arm]['32'][s]['actual_hand']) for s in ['left','right']],flush=True)
    (HERE/'measurements.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
