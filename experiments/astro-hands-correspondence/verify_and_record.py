"""Verify experimental controls, immutable evidence, and all new artifact hashes."""
import hashlib
import json
import subprocess
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/astro-hands-correspondence'

def sha(p):return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()
def main():
    prep=json.loads((HERE/'preparation.json').read_text())
    for p,digest in prep['historical_artifact_hashes'].items(): assert sha(p)==digest,p
    asset=json.loads((HERE/'asset-inspection.json').read_text())
    for p,digest in asset['asset_hashes'].items():assert sha(p)==digest,p
    records=json.loads((OUT/'run-records.json').read_text())
    assert len(records)==4 and all(r['returncode']==0 for r in records)
    results=json.loads((HERE/'results.json').read_text());bindings=json.loads((HERE/'binding-validation.json').read_text())
    sensitivity=json.loads((HERE/'hand-projection-sensitivity.json').read_text())
    assert all(r['production_actual_hand_mesh']==r['exact_actual_hand_mesh'] for d in sensitivity.values() for r in d.values())
    hashes={};training={}
    for arm,path in json.loads((HERE/'arms.json').read_text()).items():
        c=json.loads(Path(path).read_text());t=Path(c['correspondence']['train']['out_dir'])
        ds=np.load(c['correspondence']['dataset']['out'],allow_pickle=True);s=np.load(t/'correspondence_slots_final.npz',allow_pickle=True)
        assert str(ds['custom_robot_name'])==c['robot']['name']==str(ds['names'][1])
        assert len(ds['custom_robot_sample_qpos_names'])==43
        assert s['reconstructed_slots'].shape==(2,4096,3) and np.isfinite(s['reconstructed_slots']).all()
        assert str(s['training_mode'])=='robot2smpl_only'
        assert not Path(c['retarget']['out']).exists()
        assert sum(r['slots'] for r in results[arm]['common_per_segment'])==4096
        assert bindings[arm]['source_mesh_matches_audited_asset'] and bindings[arm]['target_mesh_matches_dataset']
        log=OUT/f'{arm}-train.log';epochs=[x for x in log.read_text().splitlines() if '[TrainResidual] epoch=' in x]
        assert 'epoch=00500' in epochs[-1]
        training[arm]={'final_epoch':epochs[-1],'normalization_scales':s['normalization_scales'].tolist(),'config':path}
        for p in [Path(path),Path(c['correspondence']['dataset']['out']),t/'checkpoint-final.pt',t/'correspondence_slots_final.npz',log,OUT/f'{arm}-audit.npz',OUT/f'{arm}-exact-projection.npz']:hashes[str(p)]=sha(p)
    for p in HERE.iterdir():
        if p.is_file() and p.name!='provenance.json':hashes[str(p)]=sha(p)
    ext=ROOT/'externals/UMR-astro-surface-experiment'
    patch=subprocess.check_output(['git','-C',str(ext),'diff'])
    assert hashlib.sha256(patch).hexdigest()==prep['umr_diff_sha256']
    for p in (ext/'scripts').glob('*.py'): hashes[str(p)]=sha(p)
    result={'date':'2026-10-23','umr_revision':prep['umr_revision'],'menagerie_revision':asset['menagerie_revision'],'stage_records':records,'training':training,'hashes':hashes,'historical_files_verified_unchanged':len(prep['historical_artifact_hashes']),'assets_verified_unchanged':len(asset['asset_hashes']),'umr_patch_unchanged':True,'g1_controls':'Four original arms reused unchanged; no retraining','no_retarget_or_rollout':True,'failed_attempt':'failed-metadata-attempt.log: old custom_robot_name, stopped before training; corrected with joint/XML metadata and recorded in preparation.json','versions':json.loads((ROOT/'experiments/soma-correspondence-audit/human-weights.json').read_text())['versions']}
    (HERE/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified four completed trainings, source/target controls, old artifacts and new assets unchanged.')

if __name__=='__main__':main()
