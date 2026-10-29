"""Separate centering-sensitivity results; only centering differs from base configs."""
import json,csv,copy
import numpy as np
import audit
from pathlib import Path

def main():
    payload=json.loads((audit.VIEW/'audit.json').read_text());base_metrics=json.loads((audit.HERE/'results.json').read_text());metrics={}
    for base in ['piplus','k1','t800','h2','mimickit']:
        arm=base+'_native_center';print('AUDIT',arm,flush=True)
        ds,slots,m,preview=audit.audit(arm,audit.HERE/(arm+'.json'));preview['comparison_group']='native_center_sensitivity'
        # Keep the shifted source surface aligned with that arm's learned source slots.
        hm=copy.deepcopy(payload['human_mesh']);fn=arm+'-human-vertices.bin';ds['mesh_vertices_0'].astype('<f4').tofile(audit.VIEW/fn);hm['vertices']['file']=fn
        preview['human_mesh']=hm
        base_slots=np.load(Path(json.loads((audit.HERE/(base+'.json')).read_text())['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz',allow_pickle=True)
        m['control_difference']={'human_center':'native bbox_ratio','ratio':json.loads((audit.HERE/(arm+'.json')).read_text())['correspondence']['dataset']['bbox_center_ratio'],
          'human_slots_bitwise_equal_to_spine1_control':bool(np.array_equal(slots['reconstructed_slots'][0],base_slots['reconstructed_slots'][0])),
          'note':'Same actor/seed/point budget/schedule/robot/T-pose. Centering changes source coordinates and may change sampled/ordered human points. Not pooled with exact-source controls.'}
        payload['arms'][arm]=preview;metrics[arm]=m
    audit.dump(audit.HERE/'native-center-results.json',metrics)
    with (audit.HERE/'native-center-per-segment.csv').open('w') as f:
        cols=['arm']+[k for k in next(iter(metrics.values()))['per_segment'][0] if k!='expected_sample_distance_m'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for a,m in metrics.items():
            for row in m['per_segment']:w.writerow({'arm':a,**{k:v for k,v in row.items() if k in cols}})
    payload['comparison_groups']={'exact_source':{'human_bitwise_equal':True},'native_center_sensitivity':{'human_bitwise_equal_to_exact_source':False}}
    audit.dump(audit.VIEW/'audit.json',payload)
if __name__=='__main__':main()
