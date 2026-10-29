"""Build/train only, sequentially; never invokes retarget or view stages."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/all-robot-segment-audit'
PYTHON=ROOT/'externals/UMR/.venv/bin/python'
PIPELINE=ROOT/'externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py'

def main():
    records=json.loads((OUT/'run-records.json').read_text()) if (OUT/'run-records.json').exists() else []
    for name in sys.argv[1:] or ['piplus','k1','t800','h2','mimickit','g1_racket','g1_spherehand']:
        config=HERE/f'{name}.json';c=json.loads(config.read_text())
        assert not Path(c['retarget']['out']).exists()
        for stage in ['build','train']:
            command=[str(PYTHON),str(PIPELINE),'--config',str(config),'--stage',stage]
            log=OUT/f'{name}-{stage}.log';start=time.time()
            print(f'START {name} {stage}',flush=True)
            with log.open('w') as f: result=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
            records.append(dict(robot=name,stage=stage,command=command,log=str(log),returncode=result.returncode,wall_seconds=time.time()-start))
            (OUT/'run-records.json').write_text(json.dumps(records,indent=2)+'\n')
            print(f'END {name} {stage}: {result.returncode}',flush=True)
            if result.returncode: break
        assert not Path(c['retarget']['out']).exists()
if __name__=='__main__':main()
