"""Run the matched HiPHI SMPL-X static binding experiment through Studio."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from motion_studio.studio import Studio


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def bind(studio, output, key, motion):
    folder = output / key
    folder.mkdir()
    robot = studio.add_builtin_robot(key)
    pose = robot['pose']
    run = studio.create_draft(f'UMR standard · HiPHI Get Up · {key}')
    run = studio.save_robot_pose(run.run_id, robot['asset']['asset_id'],
                                name=pose['name'], qpos=pose['qpos'], torso_body=pose['torso_body'])
    run = studio.select_motion(run.run_id, motion.asset_id)
    run = studio.save_execution_settings(run.run_id, {'sampling_seed': 0, 'epochs': 500})
    write(folder / 'inputs.json', {'robot': robot, 'motion': asdict(motion)})
    plan = studio.plan_execution(run.run_id, through='binding')
    write(folder / 'plan.json', plan)
    if not plan['ready']:
        raise RuntimeError(str(plan))
    job = studio.start_execution(run.run_id, through='binding')
    write(folder / 'launch.json', job)
    previous = None
    while True:
        job = studio.get_job(job['job_id'])
        state = (job['status'], job['stage'], job['message'])
        if state != previous:
            print(key, *state, flush=True)
            previous = state
        if job['status'] not in ('queued', 'running', 'cancelling'):
            break
        time.sleep(2)
    write(folder / 'job.json', job)
    if job['status'] != 'completed':
        raise RuntimeError(f"{key}: {job['message']}")
    receipts = {stage: studio.stage_receipt(run.run_id, run.revision_id, stage)
                for stage in ('sampling', 'training', 'binding')}
    write(folder / 'receipts.json', receipts)
    return {'run_id': run.run_id, 'revision_id': run.revision_id,
            'validation': receipts['binding']['validation']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'outputs'):
        parser.error('Choose a fresh output directory under workspace outputs/')
    output.mkdir(parents=True, exist_ok=False)
    studio = Studio(output / 'state')
    readiness = studio.native_adapter.readiness()
    write(output / 'readiness.json', readiness)
    write(output / 'source.json', {
        'motion_studio_revision': subprocess.check_output(
            ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
        'command': sys.argv, 'stage': 'binding', 'source': 'hiphi-get-up'})
    if not readiness['ready']:
        raise RuntimeError(readiness['message'])
    motion = studio.add_sample_motion('hiphi-get-up')
    results = {key: bind(studio, output, key, motion) for key in ('g1', 'astro')}
    write(output / 'result.json', results)


if __name__ == '__main__':
    main()
