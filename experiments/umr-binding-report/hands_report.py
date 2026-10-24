"""Versioned four-arm hand experiment adapter; keep the original eight arms intact."""
import json

def extend(read, table, head, pair, pct, normalize_segment, validate_result, data, values):
    new=json.loads(read('experiments/astro-hands-correspondence/results.json'))
    old=json.loads(read('experiments/soma-correspondence-audit/results.json'))
    hand=json.loads(read('experiments/astro-hands-correspondence/hand-diagnostics.json'))
    rows=[];hand_rows=[]
    for arm,d in new.items():
        validate_result(d);validate_result(d,common=True)
        source,_,center=arm.split('_');label=f'{"SMPL-X" if source=="smplx" else "SOMA"} · Astro + Dex3-1 · {center}'
        data['arms'][arm.replace('_astro_','_astrohands_')]={'label':label,'head_torso':head(d),'common':[normalize_segment(r,True) for r in d['common_per_segment']],'native':[normalize_segment(r,False) for r in d['per_segment']],'transfer_common':d['common_source_to_geometry_zone'],'transfer_native':d['source_to_geometry_zone'],'crossings':d['common_joint_plane_checks'],'experiment':'astro-hands-correspondence','original_arm':arm}
        for variant,result in [('Astro old / no hand meshes',old[arm]),('Astro new / Dex3-1',d),('G1 unchanged control',old[arm.replace('_astro_','_g1_')])]:
            leak,n=head(result)
            rows.append([f'{source.upper().replace("SMPLX","SMPL-X")} / {center}',variant,f'{leak}/{n} ({pct(leak/n)})',pair(result,'UpLeg'),pair(result,'ForeArm')])
        h=hand[arm];rs={r['source']:r for r in d['common_per_segment']}
        hand_rows.append([label,' / '.join(str(h[s]['human_hand_slots']) for s in ['left','right']),' / '.join(str(h[s]['same_side_actual_hand_mesh']) for s in ['left','right']),' / '.join(str(h[s]['same_side_finger_mesh']) for s in ['left','right']),' / '.join(pct(rs[s+'Hand']['zone_precision']) for s in ['left','right']),' / '.join(pct(rs[s+'Hand']['coverage_within_20mm']) for s in ['left','right'])])
    values['HANDS_TABLE']=table(['Source / center','Asset cohort','Head/face → torso ↓','Thigh below knee L/R ↓','Forearm proximal to elbow L/R ↓'],rows,'Matched source and center; historical Astro and G1 values are reused, not retrained.')
    values['HAND_MESH_TABLE']=table(['New Astro arm','Hand source slots L/R','Actual Dex3 mesh L/R','Finger mesh L/R','Hand-zone precision L/R','Hand-zone coverage L/R'],hand_rows,'Actual palm/finger mesh ownership differs from the broad hand zone, which includes distal wrist housing.')
    derivation=json.loads(read('experiments/astro-hands-correspondence/figure-provenance.json'))
    import hashlib
    for path,digest in {**derivation['inputs'],**derivation['outputs']}.items():
        assert hashlib.sha256(read(path)).hexdigest()==digest,path
    data['hands_experiment']={'new_arms':4,'historical_control_arms':8,'figure_language':'en'}
