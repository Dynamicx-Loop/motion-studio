"""Run frozen arms serially, retaining failures and resource measurements."""
from pathlib import Path
import subprocess,sys,time,json
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'outputs/umr-motion-preliminary-v2'
records=[]
for robot,center in [('g1','spine1'),('astro','bbox50'),('g1','bbox50'),('astro','spine1')]:
 arm=f'smplx_{robot}_{center}'
 cmd=[sys.executable,str(ROOT/'externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py'),'--config',str(HERE/f'{arm}.json'),'--stage','retarget','--skip-view']
 t=time.monotonic();print('START',arm,flush=True)
 with (OUT/f'{arm}.log').open('w') as log:
  p=subprocess.run(['/usr/bin/time','-v',*cmd],stdout=log,stderr=subprocess.STDOUT)
 records.append({'arm':arm,'command':cmd,'returncode':p.returncode,'wall_seconds':time.monotonic()-t})
 (HERE/'runs.json').write_text(json.dumps(records,indent=2)+'\n');print('DONE',records[-1],flush=True)
