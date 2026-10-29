"""Run only six new correspondence trainings sequentially on an available GPU."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/soma-correspondence-audit'
os.environ['UMR_SOMA_ASSETS_PATH']='/data/motions/human_models/soma-x/f81a01796f65/overlays/umr'
os.environ['UMR_SOMA_SMPLX_ASSETS_PATH']='/data/motions/human_models/soma-x/f81a01796f65/assets/SMPLX'
records=[]
for name,path in json.loads((HERE/'arms.json').read_text()).items():
    c=json.loads(Path(path).read_text())
    if c['experiment'].get('reused_from'):continue
    assert not Path(c['retarget']['out']).exists()
    assert not (Path(c['correspondence']['train']['out_dir'])/'checkpoint-final.pt').exists()
    command=[str(ROOT/'externals/UMR/.venv/bin/python'),str(ROOT/'externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py'),'--config',path,'--stage','train']
    log=OUT/f'{name}-train.log';start=time.time();print('START',name,flush=True)
    with log.open('w') as f:r=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    records.append(dict(arm=name,command=command,log=str(log),returncode=r.returncode,wall_seconds=time.time()-start))
    (OUT/'run-records.json').write_text(json.dumps(records,indent=2)+'\n')
    print('END',name,r.returncode,flush=True)
    if r.returncode:sys.exit(r.returncode)
    assert not Path(c['retarget']['out']).exists()
