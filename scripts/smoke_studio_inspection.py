"""Derive fresh stage/animated exports from completed smoke evidence, never retrain."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from motion_studio.studio import Studio
from motion_studio.studio._history import digest


def snapshot(folder):
    return {str(p.relative_to(folder)):digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error('Output must be fresh')
    before=snapshot(args.source)
    args.output.mkdir(parents=True)
    # Copy evidence state so service initialization/export registration never writes
    # into the completed native cohort. Internal provenance remains exact original.
    shutil.copytree(args.source/'state',args.output/'state')
    studio=Studio(args.output/'state')
    run,=studio.list_runs()
    available=[s.stage for s in run.stages if s.status=='available']
    stages=['sampling','training','binding']+(['motion'] if 'motion' in available else [])
    results=[]
    for stage in stages:
        started=time.monotonic()
        result=studio.build_inspection(run.run_id,stage)
        result['elapsed_seconds']=time.monotonic()-started
        print(json.dumps(result),flush=True);results.append(result)
    preserved=before==snapshot(args.source)
    report={'source':str(args.source.resolve()),'source_files_sha256':before,
            'source_unchanged':preserved,'exports':results}
    (args.output/'inspection-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
    if not preserved:
        raise RuntimeError('Source preservation failed')


if __name__=='__main__':
    main()
