"""Prepare static controlled datasets; never load SOMA motion or run a solver."""
import hashlib,json,os,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/soma-correspondence-audit'
EXT=ROOT/'externals/UMR-astro-surface-experiment'
os.environ['UMR_SOMA_ASSETS_PATH']='/data/motions/human_models/soma-x/f81a01796f65/overlays/umr'
os.environ['UMR_SOMA_SMPLX_ASSETS_PATH']='/data/motions/human_models/soma-x/f81a01796f65/assets/SMPLX'
sys.path.insert(0,str(EXT/'scripts'))
import build_correspondence_ae_dataset as build
from humanoid_retarget_config import load_config

def sha(p):return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    # Require historical exact hashes before inheriting any target or checkpoint.
    checks={}
    for record in ['segment-binding-audit','astro-correspondence-comparison']:
        p=json.loads((ROOT/f'experiments/{record}/provenance.json').read_text())
        for path,digest in p.get('hashes',p.get('sha256',{})).items():
            if canonical_motion_path(path).is_file():
                actual=sha(path);assert actual==digest,(path,actual,digest)
                checks[path]=actual
    soma=build.build_soma_samples(None,4096,1000,8,0.,1.,'spine1',.5,name='soma_static_neutral')[0]
    configs={};controls={}
    for robot,old in [('astro','experiments/astro-correspondence-comparison/visual.json'),('g1','experiments/segment-binding-audit/g1.json')]:
        base=load_config(ROOT/old)
        original=dict(np.load(base['correspondence']['dataset']['out'],allow_pickle=True))
        for source in ['smplx','soma']:
            for center in ['spine1','bbox50']:
                name=f'{source}_{robot}_{center}'
                c=json.loads(json.dumps(base));c.pop('_config_path',None);c.pop('_config_dir',None)
                c['experiment']={'stage':'static_correspondence_only','retarget_authorized':False,'source':source,'centering':center,'sample_control':'identical source sample identities across centering; identical target arrays across source'}
                if source=='smplx' and center=='spine1':
                    c['experiment']['reused_from']=old
                else:
                    dest=OUT/name;dest.mkdir(parents=True,exist_ok=True)
                    d={k:v.copy() for k,v in original.items()}
                    if source=='soma':
                        c['smpl_template']={'source':'manual','type':'soma','name':'soma_static_neutral','use_betas':False,'use_gender':False}
                        c['motion']={'data':None,'seq_key':None,'seq_index':0}
                        c['correspondence']['smpl_name']='soma_static_neutral'
                        for key,new in [('mesh_vertices_0','vertices'),('mesh_faces_0','faces'),('sample_face_ids_0','sample_face_ids'),('betas_0','betas')]:d[key]=soma[new].copy()
                        d['points'][0]=soma['points'];d['root_offsets'][0]=soma['root_offset']
                        d['names']=np.array(['soma_static_neutral',str(original['names'][1])])
                    # Retain inherited scalar metadata for exact captured-run replay.
                    # bbox_center_ratio is unused by training; center_modes, offsets,
                    # config and preparation.json specify the actual derived center.
                    delta=np.zeros(3,dtype=np.float32)
                    if center=='bbox50':
                        delta=build.bbox_ratio_center(d['mesh_vertices_0'],.5)
                        d['mesh_vertices_0']-=delta;d['points'][0]-=delta
                        d['root_offsets'][0]+=delta
                        d['center_modes']=np.array(['bbox_ratio_0.500000',str(original['center_modes'][1])])
                        c['correspondence']['dataset']['smpl_center']='bbox_ratio'
                        c['correspondence']['dataset']['bbox_center_ratio']=.5
                    for key in ['mesh_vertices_1','mesh_faces_1','sample_face_ids_1']:
                        np.testing.assert_array_equal(d[key],original[key])
                    np.testing.assert_array_equal(d['points'][1],original['points'][1])
                    c['correspondence']['dataset']['out']=str(dest/'dataset.npz')
                    c['correspondence']['train']['out_dir']=str(dest/'train')
                    c['retarget']['out']=str(dest/'NOT_AUTHORIZED_retarget.npz')
                    assert not (dest/'dataset.npz').exists(), 'Refuse to overwrite prepared dataset'
                    np.savez_compressed(dest/'dataset.npz',**d)
                    controls[name]={'source_center_translation_m':delta.tolist(),'source_center_absolute_m':d['root_offsets'][0].tolist(),'source_height_m':float(np.ptp(d['mesh_vertices_0'][:,1])),'target_arrays_bitwise_equal':True,'dataset_sha256':sha(dest/'dataset.npz')}
                assert not Path(c['retarget']['out']).exists()
                dump(HERE/f'{name}.json',c);configs[name]=str(HERE/f'{name}.json')
    dump(HERE/'arms.json',configs);dump(HERE/'preparation.json',{'historical_hashes_verified':checks,'controls':controls,'soma_motion_used':False})

if __name__=='__main__':main()
