"""Freeze raw controls and create separately named calibrated slot derivatives."""
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import numpy as np
import mujoco
from calibration import infer_calibration,calibrate_slots
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/astro-fist-wrist-v1'
ASSETS=Path('/data/workspace/notAnyrobot/menagerie_x')
EXT=ROOT/'externals/UMR-astro-surface-experiment'
sys.path.insert(0,str(EXT/'scripts'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb
from humanoid_retarget_config import load_config

def sha(p):return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()

def main():
    assert not (HERE/'preparation.json').exists(),'Refuse to overwrite prepared experiment'
    immutable={}
    for exp in ['astro-fist-static-v1']:
        for top in ['experiments','outputs']:
            for p in (ROOT/top/exp).rglob('*'):
                if p.is_file() and '__pycache__' not in str(p):immutable[str(p)]=sha(p)
    bundle=ASSETS/'robots/astro_p2_43dof_dex3_1'
    frozen=ROOT/'outputs/astro-fist-static-v1/asset-snapshot/astro'
    weights=np.load(ROOT/'outputs/soma-correspondence-audit/human-weight-diagnostics.npz')
    records={};arms={};controls={}
    for robot,exp in [('astro','astro-fist-static-v1'),('g1','astro-fist-static-v1')]:
        for source in ['smplx','soma']:
            for center in ['spine1','bbox50']:
                arm=f'{source}_{robot}_{center}';basepath=ROOT/f'experiments/{exp}/{arm}.json'
                c=load_config(basepath);c.pop('_config_path',None);c.pop('_config_dir',None)
                baseline_slots=Path(c['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz'
                s=dict(np.load(baseline_slots,allow_pickle=True));ds=np.load(c['correspondence']['dataset']['out'],allow_pickle=True)
                if robot=='astro':c['robot']['xml']=str(frozen/'astro_p2_43dof_dex3_1.xml')
                model=mujoco.MjModel.from_xml_path(c['robot']['xml']);data=mujoco.MjData(model)
                build.apply_joint_qpos(model,data,c['robot']['tpose_qpos'],required=True);mujoco.mj_forward(model,data)
                v,f,owners,origin,rotation,_=rb.collect_root_mesh(model,data,rb.visual_geom_ids(model,'auto'),c['robot']['point_cloud_center'])
                np.testing.assert_array_equal(f,ds['mesh_faces_1']);np.testing.assert_allclose(v@rb.SMPL_TO_ROBOT_ROOT_MATRIX,ds['mesh_vertices_1'],atol=2e-7,rtol=0)
                fm=np.array([model.mesh(int(model.geom_dataid[g])).name for g in owners])
                human,predicted=s['reconstructed_slots'];names=list(weights[source+'_joint_names']);joints=weights[source+'_joints']-ds['root_offsets'][0]
                variants={}
                for k in [16,32,64]:
                    calibrations=[]
                    for side,sign in [('left',1),('right',-1)]:
                        elbow=names.index(side[0].upper()+'_Elbow' if source=='smplx' else side.title()+'ForeArm')
                        wrist=names.index(side[0].upper()+'_Wrist' if source=='smplx' else side.title()+'Hand')
                        mask=np.char.startswith(fm,side+'_')&np.array(['hand' in n for n in fm])
                        hand_vertices=v[np.unique(f[mask])]
                        # Physical hand mesh proximal and distal extents, not wrist-roll pivot.
                        extent=sign*hand_vertices[:,1]
                        calibrations.append(infer_calibration(human,predicted,joints[elbow],joints[wrist],sign,extent.min(),extent.max(),k))
                    corrected=calibrate_slots(predicted,calibrations)
                    np.testing.assert_array_equal(corrected[:,1:],predicted[:,1:])
                    variants[str(k)]={'calibrations':[asdict(x) for x in calibrations],'moved_slots':int(np.any(corrected!=predicted,axis=1).sum()),'max_displacement_m':float(np.linalg.norm(corrected-predicted,axis=1).max())}
                    d={key:value.copy() for key,value in s.items()};d['reconstructed_slots'][1]=corrected
                    d['static_correction']=np.asarray('monotone_lateral_elbow_wrist_palm_v1')
                    dest=OUT/arm/f'k{k}';dest.mkdir(parents=True)
                    np.savez_compressed(dest/'correspondence_slots_final.npz',**d)
                    if k==32:
                        c['correspondence']['train']['out_dir']=str(dest)
                        c['experiment']={'stage':'static_slot_calibration_only','retarget_authorized':True,'raw_control_config':str(basepath),'raw_slots':str(baseline_slots),'calibration':'monotone lateral elbow/wrist→physical palm start','neighbors':32,'training_rerun':False,'source_labels_used_for_correction':False,'unrestricted_projection':True}
                        c['retarget']['out']=str(OUT/arm/'STATIC_ONLY_no_trajectory.npz')
                        dump(HERE/f'{arm}.json',c);arms[arm]=str(HERE/f'{arm}.json')
                records[arm]=variants;controls[arm]={'config':str(basepath),'dataset':c['correspondence']['dataset']['out'],'slots':str(baseline_slots),'experiment':exp,'source_and_target_arrays_unchanged':True,'target_geometry_matches_saved_dataset':True}
    dump(HERE/'arms.json',arms);dump(HERE/'calibration-parameters.json',records)
    dump(HERE/'preparation.json',{'historical_artifact_hashes':immutable,'controls':controls,'asset_revision':'d2070956558ffbf9226dcf74017d40740724d8d8','observed_working_xml_sha256':sha(bundle/'astro_p2_43dof_dex3_1.xml'),'frozen_xml_sha256':sha(frozen/'astro_p2_43dof_dex3_1.xml'),'observed_menagerie_status':git(ASSETS,'status','--short'),'frozen_assets':{str(p):sha(p) for p in frozen.rglob('*') if p.is_file()},'umr_revision':git(EXT,'rev-parse','HEAD'),'umr_diff_sha256':hashlib.sha256(subprocess.check_output(['git','-C',str(EXT),'diff'])).hexdigest(),'correction_neighbors_primary':32,'sensitivity_neighbors':[16,64],'retarget_run':False})
    print('Prepared eight corrected arms and sixteen neighbor sensitivities; raw datasets/checkpoints untouched.')

if __name__=='__main__':main()
