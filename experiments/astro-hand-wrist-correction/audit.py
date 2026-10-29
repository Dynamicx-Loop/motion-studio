"""Run the unchanged anatomical audit on eight calibrated derivatives."""
import csv,importlib.util,json,shutil,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/astro-hand-wrist-correction';OLD=ROOT/'experiments/soma-correspondence-audit'
sys.path.insert(0,str(OLD))
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,OLD/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    base=load('historical_audit','audit.py');base.HERE=HERE;base.OUT=OUT;base.VIEW=OUT/'viewer';base.VIEW.mkdir(exist_ok=True)
    results={};previews={}
    controls=json.loads((HERE/'preparation.json').read_text())['controls']
    for arm,path in json.loads((HERE/'arms.json').read_text()).items():
        print('AUDIT',arm,flush=True)
        ds,s,m,p=base.audit(arm,path);results[arm]=m;previews[arm]=p
        raw=np.load(controls[arm]['slots'],allow_pickle=True)
        for key in ['template_sort_index','template_edge_index','template_points']:
            np.testing.assert_array_equal(s[key],raw[key])
        np.testing.assert_array_equal(s['reconstructed_slots'][0],raw['reconstructed_slots'][0])
    base.dump(HERE/'results.json',results)
    for kind in ['per_segment','common_per_segment']:
        rows=[{'arm':arm,**row} for arm,m in results.items() for row in m[kind]]
        with (HERE/(kind.replace('_','-')+'.csv')).open('w') as f:
            w=csv.DictWriter(f,fieldnames=[k for k in rows[0] if k!='expected_sample_distance_m'],extrasaction='ignore');w.writeheader();w.writerows(rows)
    base.dump(base.VIEW/'audit.json',{'arms':previews,'human_mesh':next(iter(previews.values()))['human_mesh'],'human_equal':False})
    (base.VIEW/'index.html').write_text((OLD/'viewer.html').read_text().replace('SMPL-X / SOMA correspondence audit','Static wrist/palm calibration audit').replace('SMPL-X / SOMA audit','Static wrist/palm calibration').replace('Different source templates · 4096 slots · 500 epochs · no retargeting','Calibrated derivatives only · frozen checkpoints · no retraining or retargeting'))
    (base.VIEW/'app.js').write_text((OLD/'viewer.js').read_text().replace("?'Astro':'G1'","?'Astro Dex3 calibrated':'G1 calibrated'"))
    validator=load('global_projection','validate_binding.py');validator.HERE=HERE;validator.OUT=OUT
    weights=OUT/'human-weight-diagnostics.npz'
    if not weights.exists():weights.symlink_to(ROOT/'outputs/soma-correspondence-audit/human-weight-diagnostics.npz')
    validator.main()
if __name__=='__main__':main()
