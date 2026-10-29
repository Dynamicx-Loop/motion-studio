import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'experiments/hiphi-robot-control';umr=root/'externals/UMR'
for robot in ['astro','g1']:
 for version in ['reference','reconverted']:
  name=f'{robot}-{version}';print('START',name,flush=True)
  with (out/f'{name}.log').open('w') as log:
   subprocess.run([sys.executable,str(umr/'scripts/humanoid_retarget_pipeline.py'),'--config',str(out/'configs'/f'{name}.json'),'--skip-view'],cwd=umr,stdout=log,stderr=subprocess.STDOUT,check=True)
  print('DONE',name,flush=True)
