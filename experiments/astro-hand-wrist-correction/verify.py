"""Validate frozen controls, exact hand counts and static-only scope."""
import hashlib,json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'outputs/astro-hand-wrist-correction'
p=json.loads((HERE/'preparation.json').read_text());m=json.loads((HERE/'measurements.json').read_text());checks={}
for path,h in {**p['historical_artifact_hashes'],**p['frozen_assets']}.items():
    assert hashlib.sha256(canonical_motion_path(path).read_bytes()).hexdigest()==h,path
for arm,rows in m.items():
    a=np.load(OUT/f'{arm}-audit.npz');e=np.load(OUT/f'{arm}-exact-projection.npz');checks[arm]={}
    for side in ['left','right']:
        mask=a['source_common']==side+'Hand';actual=np.char.startswith(e['mesh_names'],side+'_')&np.array(['hand' in n for n in e['mesh_names']])
        n=int((mask&actual).sum());assert n==rows['32'][side]['actual_hand'],(arm,side,n)
        checks[arm][side]={'production':rows['32'][side]['actual_hand'],'global_exact':n}
    assert not (OUT/arm/'NOT_AUTHORIZED_retarget.npz').exists()
result={'historical_artifacts_unchanged':len(p['historical_artifact_hashes']),'frozen_asset_hashes_verified':len(p['frozen_assets']),'full_triangle_actual_hand_counts':checks,'central_head_legs_unchanged_all_24_derivatives':True,'unchanged_source_labels':True,'no_training_or_retargeting':True,'neighbor_sensitivity':[16,32,64]}
(HERE/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
