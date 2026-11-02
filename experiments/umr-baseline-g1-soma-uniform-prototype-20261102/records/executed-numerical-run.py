"""Execute the fitted native SOMA experiment into a fresh destination."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from prepare import (CHECKOUT, DEFAULT_OUTPUT, ROOT, assert_fitted, digest, environment,
                     fit_path, git, prepare, source_path, write)


def preserve(out, stage):
    original = json.loads((out / 'provenance.json').read_text())
    changed = [name for name, expected in original['inputs_sha256'].items() if digest(name) != expected]
    result = {'source_assets_and_upstream_hashes_unchanged': not changed, 'changed_inputs': changed,
              'external_revision_unchanged': git('rev-parse', 'HEAD') == original['umr_revision'],
              'external_status_unchanged': git('status', '--porcelain') == original['external_status_before']}
    write(out / f'preservation-{stage}.json', result)
    if not all(result[k] for k in ('source_assets_and_upstream_hashes_unchanged', 'external_revision_unchanged', 'external_status_unchanged')):
        raise RuntimeError('Source preservation failed')


def execute(out, stage):
    import soma_source
    assert_fitted(soma_source.load_soma_bvh_motion(source_path(out)), fit_path(out))
    command = [sys.executable, '-B', str(CHECKOUT / 'scripts/humanoid_retarget_pipeline.py'),
               '--config', str(out / 'config.json'), '--defaults',
               str(CHECKOUT / 'humanoid_retarget_defaults_bones_seed.json'), '--skip-view', '--stage', stage]
    overrides = environment(out)
    started = time.time()
    with (out / 'logs' / f'{stage}.log').open('x') as log:
        result = subprocess.run(command, cwd=CHECKOUT, env={**os.environ, **overrides}, stdout=log, stderr=subprocess.STDOUT)
    write(out / 'logs' / f'{stage}-completed.json', {'command': command, 'cwd': str(CHECKOUT),
          'environment_overrides': overrides, 'started_unix': started,
          'wall_seconds': time.time() - started, 'returncode': result.returncode})
    preserve(out, stage)
    if result.returncode:
        raise RuntimeError(f'{stage} failed; see {out / "logs" / (stage + ".log")}')
    print(f'{stage} completed in {time.time() - started:.3f}s', flush=True)


def inspect(out):
    folder = Path(__file__).parent
    inspection = out.with_name(out.name + '-inspection')
    comparison = out.with_name(out.name + '-comparison')
    commands = [
        [sys.executable, '-B', str(folder / 'export.py'), '--run', str(out), '--output', str(inspection)],
        [sys.executable, '-B', str(folder / 'audit_replay.py'), '--run', str(out), '--inspection', str(inspection), '--output', str(out / 'replay-audit.json')],
        [sys.executable, '-B', str(folder / 'compare.py'), '--run', str(out), '--inspection', str(inspection), '--output', str(comparison)],
    ]
    for command in commands:
        subprocess.run(command, check=True, cwd=ROOT, env={**os.environ, **environment(out)})
    write(out / 'inspection-completed.json', {'commands': commands, 'inspection': str(inspection), 'comparison': str(comparison)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', nargs='?', default='all', choices=('all', 'prepare', 'build', 'train', 'retarget', 'validate', 'inspect'))
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--skip-inspection', action='store_true', help='Run numerical stages and validation only')
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to((ROOT / 'outputs').resolve()):
        raise ValueError('Experiment output must be a fresh path under Motion Studio outputs/')
    os.environ.update(environment(out))
    sys.path.insert(0, str(CHECKOUT / 'scripts'))
    if args.stage in ('all', 'prepare'):
        prepare(out)
        print(f'Prepared strict fitted uniform route: {out}', flush=True)
    for stage in ('build', 'train', 'retarget'):
        if args.stage in ('all', stage):
            execute(out, stage)
    if args.stage in ('all', 'validate'):
        from validate import validate
        write(out / 'validation.json', validate(out))
        preserve(out, 'validate')
        artifacts = {}
        for path in [out / 'dataset.npz', out / 'motion.npz', *sorted((out / 'train').rglob('*'))]:
            if path.is_file():
                artifacts[str(path.relative_to(out))] = {'sha256': digest(path), 'bytes': path.stat().st_size}
        write(out / 'run_manifest.json', {'status': 'numerical-validation-passed', 'artifacts': artifacts,
              'invocation': sys.argv, 'runtime': sys.executable, 'pipeline_source_snapshots': str(out / 'code')})
    if args.stage == 'inspect' or (args.stage == 'all' and not args.skip_inspection):
        inspect(out)


if __name__ == '__main__':
    main()
