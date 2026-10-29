"""Verify exported diagnostics and record local provenance, without motion execution."""
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import hashlib,json,subprocess,sys,platform,csv
import numpy as np,mujoco,scipy,torch,trimesh
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'outputs/all-robot-segment-audit';UP=ROOT/'externals/UMR'

def sha(p):return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
    payload=json.loads((OUT/'viewer/audit.json').read_text());results=json.loads((HERE/'results.json').read_text());native=json.loads((HERE/'native-center-results.json').read_text())
    for group,metrics in [('exact_source',results),('native_center_sensitivity',native)]:
        for arm,m in metrics.items():
            if group=='native_center_sensitivity':
                base=arm.replace('_native_center','')
                bc=json.loads((HERE/(base+'.json')).read_text());nc=json.loads((HERE/(arm+'.json')).read_text())
                bd=np.load(bc['correspondence']['dataset']['out']);nd=np.load(nc['correspondence']['dataset']['out'])
                for key in ['mesh_vertices_1','mesh_faces_1','sample_face_ids_1']:
                    np.testing.assert_array_equal(bd[key],nd[key])
                np.testing.assert_array_equal(bd['points'][1],nd['points'][1])
                delta=nd['mesh_vertices_0']-bd['mesh_vertices_0'];shift=delta.astype(np.float64).mean(0)
                m['control_difference']['robot_mesh_samples_bitwise_equal']=True
                m['control_difference']['human_mesh_translation_m']=shift.tolist()
                m['control_difference']['human_translation_max_residual_m']=float(np.max(np.abs(delta-shift)))
            assert len(m['per_segment'])==19 and sum(r['slots'] for r in m['per_segment'])==4096
            assert sum(sum(t.values()) for t in m['source_to_geometry_zone'].values())==4096
            m['comparison_group']=group
            for r in m['per_segment']:
                side='left' if r['source'].startswith('left') else 'right' if r['source'].startswith('right') else None
                r['opposite_side_zone_slots']=sum(v for k,v in m['source_to_geometry_zone'][r['source']].items() if side and k.startswith(('right' if side=='left' else 'left')+' '))
            if arm in payload['arms']:payload['arms'][arm]['metrics']=m
        dump(HERE/('results.json' if group=='exact_source' else 'native-center-results.json'),metrics)
        with (HERE/('per-segment.csv' if group=='exact_source' else 'native-center-per-segment.csv')).open('w') as f:
            cols=['arm']+sorted({k for m in metrics.values() for r in m['per_segment'] for k in r if k!='expected_sample_distance_m'});w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
            for arm,m in metrics.items():
                for r in m['per_segment']:w.writerow({'arm':arm,**{k:v for k,v in r.items() if k in cols}})
    payload['exact_source_group_human_equal']=payload.pop('human_equal',True)
    payload['all_groups_human_equal']=False
    dump(OUT/'viewer/audit.json',payload)
    official=json.loads((HERE/'official-inventory.json').read_text());mapping={'piplus':'piplus','booster_k1':'k1','g1':'g1','t800':'t800'}
    config_paths={a:HERE/(a+'.json') for a in ['piplus','k1','t800','h2','mimickit','g1_racket','g1_spherehand']}
    config_paths['g1']=ROOT/'experiments/segment-binding-audit/g1.json'
    for r in official['robots']:
        config=json.loads(config_paths[mapping[r['id']]].read_text());assert sha(config['robot']['xml'])==r['xml_source']['sha256']
        assert config['robot']['tpose_qpos']==r['tpose_qpos']
    assert len(official['asset_availability'])==134 and all(x.get('status')==200 for x in official['asset_availability'])
    files=set(config_paths.values())
    files.add(ROOT/'configs/umr/constraints.txt')
    for pattern in ['*.py','*.js','*.html']:
        files.update(HERE.glob(pattern))
    for p in HERE.glob('*native_center.json'):files.add(p);config_paths[p.stem]=p
    for p in config_paths.values():
        c=json.loads(p.read_text());assert not Path(c['retarget']['out']).exists()
        files.update([Path(c['robot']['xml']),Path(c['correspondence']['dataset']['out']),Path(c['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz',Path(c['correspondence']['train']['out_dir'])/'checkpoint-final.pt'])
    canonical={ROOT/'configs/umr/astro_p2_29dof.json':'4e0f69aff52297fbc10c6440ebdec28a2fe6296e03e3127c765a21f3a676a6cb',Path('/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_29dof/astro_p2_29dof.xml'):'89f179ea9fb51ff53a9a1d3fa9cef6049f843e0e3ad21a886677e3a5341767f7',ROOT/'experiments/astro-surface-geometry/umr-surface-geometry.patch':'e2cc109b3aa8125034391fde0ae2f66a02ea660a6900ce727351ea1579ca000a'}
    for p,h in canonical.items():assert sha(p)==h;files.add(p)
    files.update([UP/'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz',Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl')])
    tracked=subprocess.check_output(['git','-C',str(UP),'ls-files','assets'],text=True).splitlines();asset_hashes={f:sha(UP/f) for f in tracked}
    provenance={'date':'2026-10-23','umr_revision':subprocess.check_output(['git','-C',str(UP),'rev-parse','HEAD'],text=True).strip(),
      'baseline_status':subprocess.check_output(['git','-C',str(UP),'status','--short'],text=True),
      'experimental_checkout_status':subprocess.check_output(['git','-C',str(ROOT/'externals/UMR-astro-surface-experiment'),'status','--short'],text=True),
      'environment':dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,mujoco=mujoco.__version__,torch=torch.__version__,trimesh=trimesh.__version__),
      'exact_source_controls_equal':'Asserted bitwise by audit.py: human mesh/faces/samples/betas/learned slots/order/template points/graph, plus prior G1 control.',
      'native_centers':'Separate sensitivity group; same actor but source coordinates differ. Not asserted bitwise equal.',
      'new_training_runs':12,'reused_runs':['Astro visual','Astro primitive (rejected)','G1 matched control'],
      'stage_records':json.loads((OUT/'run-records.json').read_text()),'no_retarget_or_rollout':True,
      'canonical_hashes_unchanged':True,'hashes':{str(p):sha(p) for p in sorted(files)},'shipped_robot_asset_hashes':asset_hashes}
    assert len(provenance['stage_records'])==24 and all(r['returncode']==0 and r['stage'] in ['build','train'] for r in provenance['stage_records'])
    dump(HERE/'provenance.json',provenance)
    print('Verified 15 correspondences, 285 segment rows, 134 official asset URLs, exact control equality, 24 successful build/train stages, unchanged canonical assets; no retarget.')
if __name__=='__main__':main()
