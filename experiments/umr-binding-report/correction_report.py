"""Keep static calibration derivatives visibly separate from learned baselines."""
import hashlib,json

def extend(read,table,head,pct,normalize,validate,data,values):
    results=json.loads(read('experiments/astro-hand-wrist-correction/results.json'))
    measured=json.loads(read('experiments/astro-hand-wrist-correction/measurements.json'));rows=[];tradeoffs=[]
    def lr(d,key,percent=False):return ' / '.join(pct(d[s][key]) if percent else str(d[s][key]) for s in ['left','right'])
    for arm,d in results.items():
        validate(d);validate(d,common=True);source,robot,center=arm.split('_')
        label=f'{"SMPL-X" if source=="smplx" else "SOMA"} · {"Astro + Dex3-1" if robot=="astro" else "G1"} · {center} · static calibration'
        data['arms'][arm.replace('_'+robot+'_','_'+robot+'cal_')]={'label':label,'head_torso':head(d),'common':[normalize(r,True) for r in d['common_per_segment']],'native':[normalize(r,False) for r in d['per_segment']],'transfer_common':d['common_source_to_geometry_zone'],'transfer_native':d['source_to_geometry_zone'],'crossings':d['common_joint_plane_checks'],'experiment':'astro-hand-wrist-correction','original_arm':arm}
        a=measured[arm];b,c=a['0'],a['32']
        rows.append([label,lr(c,'slots'),lr(b,'actual_hand')+' → '+lr(c,'actual_hand'),lr(b,'wrist_housing')+' → '+lr(c,'wrist_housing'),lr(b,'actual_hand_coverage20mm',True)+' → '+lr(c,'actual_hand_coverage20mm',True)])
        tradeoffs.append([label,lr(b,'finger')+' → '+lr(c,'finger'),lr(b,'nonhand_on_hand')+' → '+lr(c,'nonhand_on_hand'),f"{c['max_displacement_mm']:.1f}",f"{b['symmetric_sample_mean_distance_mm']:.2f} → {c['symmetric_sample_mean_distance_mm']:.2f}",'('+lr(a['16'],'actual_hand')+') / ('+lr(a['64'],'actual_hand')+')'])
    values['CORRECTION_TABLE']=table(['Calibrated arm','Source hand slots L/R','Actual hand L/R raw → calibrated','Wrist housing L/R raw → calibrated','Actual-hand coverage L/R raw → calibrated'],rows,'Same labels, samples and meshes; k=32 primary. G1 raw controls remain unchanged; G1 derivatives receive the identical rule.')
    values['CORRECTION_TRADEOFFS']=table(['Calibrated arm','Finger mesh L/R raw → calibrated','Non-hand on hand L/R raw → calibrated','Maximum movement (mm)','Global sample distance (mm) raw → calibrated','Actual hand L/R at k16 / k64'],tradeoffs,'Coverage uses fixed training reference samples within 20 mm. Global distance averages both nearest-sample directions; lower is better. G1 has no finger meshes.')
    f=json.loads(read('experiments/astro-hand-wrist-correction/figure-provenance.json'))
    for path,digest in {**f['inputs'],**f['outputs']}.items():assert hashlib.sha256(read(path)).hexdigest()==digest,path
    data['static_correction']={'primary_neighbors':32,'sensitivity_neighbors':[16,64],'derived_arms':8,'raw_control_arms':8,'training_rerun':False,'retargeting':False}
