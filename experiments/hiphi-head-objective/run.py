"""Prepare and run reversible UMR head-objective controls using existing slots."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
UMR=ROOT/'externals/UMR'
VARIANTS=['baseline','no-head','no-head-normal','no-head-point','no-head-samples','neutral-baseline','neutral-no-head']
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prepare-only',action='store_true')
args=parser.parse_args()
(OUT/'configs').mkdir(exist_ok=True)
(OUT/'neutral').mkdir(exist_ok=True)
source=UMR/'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
s=np.load(source)
pose=np.zeros((240,165),np.float32);pose[:,1]=-np.pi/2
neutral=OUT/'neutral/motion_actor_smplx.npz'
if not neutral.exists():
    np.savez_compressed(neutral,poses=pose,trans=np.repeat(s['trans'][92:93],240,axis=0),betas=s['betas'],gender=s['gender'],fps=s['fps'],mocap_framerate=s['mocap_framerate'],output_up='y',model_type='smplx')
costs={'no-head':(20,0,0),'no-head-normal':(20,1,0),'no-head-point':(20,0,1),'no-head-samples':(0,0,0),'neutral-no-head':(20,0,0)}
for robot in ['astro','g1']:
    for variant in VARIANTS:
        c={'extends':str(ROOT/f'experiments/hiphi-robot-control/configs/{robot}-reference.json'),'motion':{'max_frames':240},'retarget':{'out':str(OUT/f'{robot}-{variant}.npz')}}
        if variant in costs:
            count,point,normal=costs[variant]
            c['solver']={'body_segment':{'cost_config':{'head':{'sample_slots':count,'point_cost':point,'normal_cost':normal}}}}
        if variant.startswith('neutral'):c['motion']['data']=str(neutral)
        path=OUT/'configs'/f'{robot}-{variant}.json'
        # Existing configurations are part of the experiment provenance.
        if not path.exists():path.write_text(json.dumps(c,indent=2)+'\n')
        if args.prepare_only:continue
        with (OUT/f'{robot}-{variant}.log').open('w') as log:
            subprocess.run([sys.executable,'scripts/humanoid_retarget_pipeline.py','--stage','retarget','--skip-view','--config',str(path)],cwd=UMR,stdout=log,stderr=subprocess.STDOUT,check=True)
