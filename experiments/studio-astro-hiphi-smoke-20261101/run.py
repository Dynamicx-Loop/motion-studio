"""Run built-in Astro and the short HiPHI sample through the public Studio API."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from motion_studio.integrations.menagerie_assets import ASTRO_ROOT
from motion_studio.studio import Studio


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Fresh experiment output; existing directories are refused')
    parser.add_argument('--epochs', type=int, default=5)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    studio = Studio(output / 'state')
    manifest = json.loads((ASTRO_ROOT / 'manifest.json').read_text())
    protected = {str(path): digest(path) for path in ASTRO_ROOT.rglob('*') if path.is_file()}
    write(output / 'source.json', {
        'motion_studio_revision': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
        'driver_sha256': digest(Path(__file__)), 'astro_source': manifest['source'],
        'astro_derivation': manifest['derivation'], 'cohort': '5-epoch/180-frame workflow smoke; no quality claim'})
    readiness = studio.native_adapter.readiness()
    write(output / 'readiness.json', readiness)
    if not readiness['ready']:
        raise RuntimeError(readiness['message'])
    robot = studio.add_builtin_robot('astro')
    motion = studio.add_sample_motion('hiphi-quick')
    if motion.frame_count != 180:
        raise RuntimeError('Short HiPHI sample no longer contains the expected 180 exact frames')
    protected[motion.model_path] = digest(Path(motion.model_path))
    from motion_studio.integrations.umr_assets import MOTIONS
    original_motion = studio.native_adapter.checkout / MOTIONS['hiphi-quick'][1]
    protected[str(original_motion)] = digest(original_motion)
    write(output / 'protected-files-before.json', protected)
    write(output / 'inputs.json', {'robot': robot, 'motion': asdict(motion)})
    run = studio.create_draft('Astro P2 · short HiPHI · 5-epoch smoke')
    pose = robot['pose']
    run = studio.save_robot_pose(run.run_id, robot['asset']['asset_id'], name=pose['name'],
        qpos=pose['qpos'], torso_body=pose['torso_body'])
    run = studio.select_motion(run.run_id, motion.asset_id)
    run = studio.save_execution_settings(run.run_id, {'sampling_seed': 0, 'epochs': args.epochs, 'trajectory_filter': 'LQR'})
    studio.select(run.run_id)
    plan = studio.plan_execution(run.run_id, through='retargeting')
    write(output / 'plan.json', plan)
    if not plan['ready']:
        raise RuntimeError(str(plan))
    job = studio.start_execution(run.run_id, through='retargeting')
    write(output / 'launch.json', job)
    print(json.dumps({'run_id': run.run_id, 'revision': run.revision_id, 'job_id': job['job_id'],
                      'frames': motion.frame_count, 'fps': motion.fps, 'gpu': readiness['identity']['runtime']['gpu']}), flush=True)
    previous = None
    while True:
        current = studio.get_job(job['job_id'])
        progress = {key: current.get(key) for key in ('status', 'stage', 'progress', 'message')}
        if progress != previous:
            print(json.dumps({'wall_seconds': round(time.monotonic() - started, 1), **progress}), flush=True)
            previous = progress
        if current['status'] in ('completed', 'failed', 'cancelled', 'interrupted'):
            break
        time.sleep(10)
    write(output / 'job.json', current)
    if current['status'] != 'completed':
        raise RuntimeError(f"Job {current['status']}: {current['message']}")
    receipts = {stage: studio.stage_receipt(run.run_id, run.revision_id, stage)
                for stage in ('sampling', 'training', 'binding', 'retargeting')}
    write(output / 'receipts.json', receipts)
    native_seconds = time.monotonic() - started
    print('All four stages validated; exporting synchronized inspection.', flush=True)
    inspection = studio.build_inspection(run.run_id, 'motion', revision_id=run.revision_id)
    write(output / 'inspection.json', inspection)
    changed = [name for name, expected in protected.items() if digest(Path(name)) != expected]
    if changed:
        raise RuntimeError(f'Protected source files changed: {changed}')
    result = {'run_id': run.run_id, 'revision_id': run.revision_id, 'job_id': job['job_id'],
        'status': current['status'], 'settings': plan['settings'], 'validation': receipts['retargeting']['validation'],
        'native_workflow_seconds': native_seconds, 'total_seconds': time.monotonic() - started,
        'inspection': inspection, 'protected_files_unchanged': len(protected)}
    write(output / 'result.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
