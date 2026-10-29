"""Reuse the frozen anatomical audit, then add physical hand-link diagnostics."""
import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'outputs/astro-hands-correspondence'
OLD = ROOT/'experiments/soma-correspondence-audit'
sys.path.insert(0,str(OLD))

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, OLD/filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def main():
    base = load('historical_anatomical_audit','audit.py')
    base.HERE = HERE; base.OUT = OUT; base.VIEW = OUT/'viewer'
    base.VIEW.mkdir(exist_ok=True)
    base.ARMS = json.loads((HERE/'arms.json').read_text())
    results = {}; previews = {}; hand = {}; controls = []
    reference = None
    for arm,path in base.ARMS.items():
        print('AUDIT',arm,flush=True)
        ds, slots, metrics, preview = base.audit(arm,path)
        oldc = json.loads((OLD/f'{arm}.json').read_text())
        oldds = np.load(oldc['correspondence']['dataset']['out'],allow_pickle=True)
        oldslots = np.load(Path(oldc['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz',allow_pickle=True)
        for key in ['mesh_vertices_0','mesh_faces_0','sample_face_ids_0','betas_0']:
            np.testing.assert_array_equal(ds[key],oldds[key])
        for key in ['template_sort_index','template_edge_index','template_points']:
            np.testing.assert_array_equal(slots[key],oldslots[key])
        np.testing.assert_array_equal(slots['reconstructed_slots'][0],oldslots['reconstructed_slots'][0])
        if reference is not None:
            for key in ['mesh_vertices_1','mesh_faces_1','sample_face_ids_1']:
                np.testing.assert_array_equal(ds[key],reference[key])
            np.testing.assert_array_equal(ds['points'][1],reference['points'][1])
        reference = ds
        controls.append(arm+': identical historical source, graph and human slots; identical new target across arms')
        results[arm] = metrics; previews[arm] = preview
        a = np.load(OUT/f'{arm}-audit.npz')
        rows = {}
        for side in ['left','right']:
            source = a['source_common'] == side+'Hand'
            actual = np.char.startswith(a['mesh_names'],side+'_hand_')
            fingers = actual & ~np.char.endswith(a['mesh_names'],'palm_link')
            rows[side] = {'human_hand_slots':int(source.sum()),'same_side_actual_hand_mesh':int((source&actual).sum()),'same_side_finger_mesh':int((source&fingers).sum()),'same_side_palm_mesh':int((source&actual&~fingers).sum()),'hand_slots_by_mesh':base.table(a['source_common'][source],a['mesh_names'][source]),'all_sources_on_actual_hand':base.table(a['source_common'][actual],a['mesh_names'][actual])}
        hand[arm] = rows
    base.dump(HERE/'results.json',results); base.dump(HERE/'hand-diagnostics.json',hand)
    base.dump(HERE/'validation.json',{'assertions':controls,'no_retarget':True,'same_historical_audit_code':str(OLD/'audit.py'),'semantic_groups_unchanged':True})
    for kind in ['per_segment','common_per_segment']:
        rows=[{'arm':arm,**row} for arm,m in results.items() for row in m[kind]]
        keys=[k for k in rows[0] if k!='expected_sample_distance_m']
        with (HERE/(kind.replace('_','-')+'.csv')).open('w') as f:
            w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    base.dump(base.VIEW/'audit.json',{'arms':previews,'human_mesh':next(iter(previews.values()))['human_mesh'],'human_equal':False})
    shutil.copyfile(OLD/'viewer.html',base.VIEW/'index.html')
    js=(OLD/'viewer.js').read_text().replace("?'Astro':'G1'","?'Astro + Dex3-1':'G1'")
    (base.VIEW/'app.js').write_text(js)
    # Exact global triangle projection is an independent diagnostic, never a correction.
    validator=load('historical_global_projection','validate_binding.py')
    validator.HERE=HERE; validator.OUT=OUT
    weights=OUT/'human-weight-diagnostics.npz'
    if not weights.exists(): weights.symlink_to(ROOT/'outputs/soma-correspondence-audit/human-weight-diagnostics.npz')
    validator.main()
    sensitivity={}
    for arm in results:
        a=np.load(OUT/f'{arm}-audit.npz');e=np.load(OUT/f'{arm}-exact-projection.npz')
        sensitivity[arm]={}
        for side in ['left','right']:
            mask=a['source_common']==side+'Hand'
            old=np.char.startswith(a['mesh_names'],side+'_hand_')
            exact=np.char.startswith(e['mesh_names'],side+'_hand_')
            sensitivity[arm][side]={'production_actual_hand_mesh':int((mask&old).sum()),'exact_actual_hand_mesh':int((mask&exact).sum()),'slots':int(mask.sum())}
    base.dump(HERE/'hand-projection-sensitivity.json',sensitivity)

if __name__=='__main__':main()
