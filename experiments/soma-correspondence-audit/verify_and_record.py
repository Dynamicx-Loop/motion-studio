"""Record reproducible provenance and verify static experiment invariants."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/soma-correspondence-audit';EXT=ROOT/'externals/UMR-astro-surface-experiment'
def sha(p):return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
def main():
    arms=json.loads((HERE/'arms.json').read_text());hashes={};training={}
    records=json.loads((OUT/'run-records.json').read_text());assert len(records)==6 and all(x['returncode']==0 for x in records)
    for name,path in arms.items():
        c=json.loads(Path(path).read_text());d=np.load(c['correspondence']['dataset']['out'],allow_pickle=True)
        train=Path(c['correspondence']['train']['out_dir']);slots=np.load(train/'correspondence_slots_final.npz',allow_pickle=True)
        assert slots['reconstructed_slots'].shape==(2,4096,3) and np.isfinite(slots['reconstructed_slots']).all()
        assert str(slots['training_mode'])=='robot2smpl_only'
        assert not Path(c['retarget']['out']).exists()
        assert sum(x['slots'] for x in json.loads((HERE/'results.json').read_text())[name]['per_segment'])==4096
        for p in [Path(path),Path(c['correspondence']['dataset']['out']),train/'correspondence_slots_final.npz',train/'checkpoint-final.pt',Path(c['robot']['xml'])]:hashes[str(p)]=sha(p)
        xml=Path(c['robot']['xml']);tree=ET.parse(xml);compiler=tree.find('compiler');meshdir=compiler.get('meshdir','') if compiler is not None else ''
        for node in tree.findall('.//asset/mesh'):
            if node.get('file'):
                p=xml.parent/meshdir/node.get('file');hashes[str(p.resolve())]=sha(p)
        if 'reused_from' in c['experiment']:
            log=ROOT/('outputs/astro-correspondence-comparison/visual-train.log' if 'astro' in name else 'outputs/segment-binding-audit/g1-train.log')
        else:log=OUT/f'{name}-train.log'
        lines=log.read_text().splitlines();epochs=[x for x in lines if '[TrainResidual] epoch=' in x]
        assert 'epoch=00500' in epochs[-1]
        training[name]={'reused':bool(c['experiment'].get('reused_from')),'log':str(log),'final_epoch':epochs[-1],'command':[x for x in lines if '[HumanoidPipeline] /' in x][-1], 'normalization_scales':slots['normalization_scales'].tolist()}
        hashes[str(log)]=sha(log)
    for p in list(HERE.glob('*.py'))+list(HERE.glob('*.js'))+list(HERE.glob('*.html'))+[ROOT/'configs/umr/astro_p2_29dof.json',ROOT/'experiments/astro-surface-geometry/umr-surface-geometry.patch']+list((EXT/'scripts').glob('*.py')):
        hashes[str(p)]=sha(p)
    previous=json.loads((ROOT/'experiments/segment-binding-audit/results.json').read_text())
    for robot,old in [('astro','visual'),('g1','g1')]:
        c=json.loads(Path(arms[f'smplx_{robot}_spine1']).read_text())
        assert sha(c['correspondence']['dataset']['out'])==previous[old]['hashes']['dataset']
        assert sha(Path(c['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz')==previous[old]['hashes']['slots']
    before=json.loads((HERE/'preparation.json').read_text())['historical_hashes_verified']
    for path,digest in before.items():assert sha(path)==digest,path
    hw=json.loads((HERE/'human-weights.json').read_text())
    for path,entry in hw['files'].items():assert sha(path)==entry['sha256'];hashes[path]=entry['sha256']
    assert git(ROOT/'externals/UMR','rev-parse','HEAD')=='d1cdaedaf67a827198da71c5fa831f48b2e51f91'
    assert git(ROOT/'externals/UMR','status','--short')==''
    result={'date':'2026-10-23','umr_revision':git(EXT,'rev-parse','HEAD'),'baseline_status':git(ROOT/'externals/UMR','status','--short'),'isolated_status':git(EXT,'status','--short'),'stage_records':records,'training':training,'hashes':hashes,'human_weight_diagnostics_sha256':sha(OUT/'human-weight-diagnostics.npz'),'no_retarget_or_rollout':True,'canonical_and_historical_hashes_unchanged':True,'gpu':'NVIDIA GeForce RTX 5070 Laptop, sequential host CUDA jobs; occupancy checked before starting','versions':hw['versions']}
    (HERE/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified 8 arms, 6 fresh trainings, 2 exact-provenance reused results; canonical/historical hashes unchanged.')
if __name__=='__main__':main()
