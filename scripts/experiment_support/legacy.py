"""Read-only reconstruction of completed evidence into a new sealed directory."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

from .contracts import validate
from .files import file_record, read_json, resolve, seal, sha256, write_json
from .metrics import hand_metrics, motion_metrics

STATIC = {
    'soma-correspondence-audit': ('pre_hands', 'raw'),
    'astro-hands-correspondence': ('open_hands_v2', 'raw'),
    'astro-hand-wrist-correction': ('open_hands_v2', 'wrist_k32'),
    'astro-canonical-static-v1': ('open_hands_v4', 'raw'),
    'astro-canonical-wrist-v1': ('open_hands_v4', 'wrist_k32'),
    'astro-fist-static-v1': ('fixed_fist_v1', 'raw'),
    'astro-fist-wrist-v1': ('fixed_fist_v1', 'wrist_k32'),
}
MOTION = {
    'umr-motion-preliminary-v1': 'preliminary_360_frames',
    'umr-motion-preliminary-v2': 'preliminary_full_clip',
    'umr-motion-canonical-v1': 'open_hands_v4',
    'umr-motion-fist-v1': 'fixed_fist_v1',
}
HAND_RECORDS = {
    'astro-fist-static-v1': 'astro-fist-wrist-v1',
    'astro-fist-wrist-v1': 'astro-fist-wrist-v1',
    'astro-canonical-static-v1': 'astro-canonical-wrist-v1',
    'astro-canonical-wrist-v1': 'astro-canonical-wrist-v1',
    'astro-hand-wrist-correction': 'astro-hand-wrist-correction',
}


def _report_helpers(root: Path):
    """Reuse the report's pure validators/normalizer without calling its builder."""
    folder = root / 'experiments/umr-binding-report'
    spec = importlib.util.spec_from_file_location('motion_studio_saved_report', folder / 'build_report.py')
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(folder))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def reconstruct(root: Path, destination: Path) -> dict:
    """No upstream imports, raw writes, GPU work or mutation of historical reports."""
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Reconstruction requires a new directory: {destination}')
    sources = {}

    def read(path: str) -> dict:
        full = root / path
        record = file_record(full, root)
        sources[path] = record
        data = read_json(full)
        if sha256(full) != record['sha256']:
            raise ValueError(f'Source changed while reading: {path}')
        return data

    def evidence(path: str, pointer: str = '') -> dict:
        if path not in sources:
            sources[path] = file_record(root / path, root)
        return {**sources[path], 'pointer': pointer}

    helpers = _report_helpers(root)
    inventory = []
    for folder in sorted((root / 'experiments').iterdir()):
        if not folder.is_dir() or folder == destination:
            continue
        records = []
        # Keep manifests small: numerical arrays, meshes and models stay in place.
        for path in sorted(folder.glob('*')):
            if path.is_file() and path.suffix in {'.json', '.md', '.py', '.patch'}:
                relative = str(path.relative_to(root))
                evidence(relative)
                records.append(relative)
        if records:
            inventory.append({'experiment_id': folder.name, 'evidence_files': records,
                              'normalization': 'per_arm' if folder.name in STATIC | MOTION
                              else 'inventory_only; inspect original schema'})
    for folder in ('references', 'configs/umr'):
        for path in sorted((root / folder).glob('*')):
            if path.is_file() and path.suffix in {'.json', '.md', '.txt'}:
                evidence(str(path.relative_to(root)))
    for path in ['docs/umr-head-objective-investigation.md', 'docs/umr-solver-investigation.md',
                 'docs/umr-soma-setup.md', 'docs/umr-astro-baseline-proposal.md',
                 'schemas/experiments/plan.schema.json', 'schemas/experiments/result.schema.json']:
        evidence(path)
    for path in sorted((root / 'scripts/experiment_support').glob('*.py')):
        evidence(str(path.relative_to(root)))
    results = []
    for experiment, cohort in {**{k: v[0] for k, v in STATIC.items()}, **MOTION}.items():
        result_path = f'experiments/{experiment}/results.json'
        saved = read(result_path)
        run_path = f'experiments/{experiment}/runs.json'
        runs = {r['arm']: r for r in read(run_path)} if (root / run_path).exists() else {}
        if experiment == 'astro-fist-static-v1':
            prov = read(f'experiments/{experiment}/provenance.json')
            runs = {r['arm']: r for r in prov['fresh_training_runs']}
        for arm, row in saved.items():
            parts = arm.split('_')
            source, robot, center = parts[:3]
            variant = STATIC[experiment][1] if experiment in STATIC else (
                'wrist_k32' if parts[-1] == 'candidate' else 'raw')
            config_path = f'experiments/{experiment}/{arm}.json'
            config = read(config_path)
            run = runs.get(arm, {})
            record = {
                'schema_version': 1, 'run_id': f'legacy:{experiment}:{arm}',
                'experiment_id': experiment, 'arm_id': arm, 'cohort_id': cohort,
                'cohort_status': 'legacy',
                'superseded_by': None,
                'task': 'static_correspondence' if experiment in STATIC else 'motion',
                'source_model': source, 'robot': robot, 'center': center, 'variant': variant,
                'matched_control': None, 'evidence_origin': 'retrospective',
                'reproducibility': 'not_rerun',
                'evidence': [evidence(result_path, '/' + arm), evidence(config_path)],
                'conditions': {
                    'robot': config['robot'], 'source_motion_config': config.get('motion'),
                    'training_settings_recorded_in_config': config['correspondence'].get('train'),
                    'solver_settings': config.get('solver'), 'retarget_settings': config.get('retarget'),
                    'experiment_settings': config.get('experiment'),
                    'head_policy': 'See saved config; historical 29DOF head ablation is a separate experiment',
                    'seed_caveat': 'Config defaults do not override preparation provenance; fist target sampler=9000, inherited source=1000',
                    'frames': row.get('frames'), 'fps': row.get('fps'),
                    'joint_names_native_order': row.get('joint_names'),
                    'trajectory_sha256_recorded': row.get('trajectory_sha256'),
                },
                'execution': {k: run.get(k) for k in
                              ('command', 'cwd', 'returncode', 'wall_seconds', 'started_at', 'finished_at')},
                'metrics': [], 'segments': [],
                'unknowns': ['Run start/end timestamps and exact cwd absent from run entry',
                             'Original full dependency/driver closure not established by this reconstruction',
                             'Fresh numerical rerun not performed'],
                'limitations': ['Synthetic legacy ID, not an observed original run ID',
                                'Recorded historical checks are not re-executed by reconstruction',
                                'Raw binary/model hashes are recorded evidence, not revalidated here',
                                'Open-hand to fixed-fist changes geometry and finger freedom together',
                                'All historical cohorts are legacy and excluded from the new baseline; legacy does not mean invalid'],
            }
            if robot == 'astro':
                control_arm = arm.replace('_astro_', '_g1_')
                control_exp = experiment if control_arm in saved else 'soma-correspondence-audit'
                record['matched_control'] = f'legacy:{control_exp}:{control_arm}'
            for name in ('provenance.json', 'preparation.json', 'validation.json',
                         'fixed-fist-validation.json', 'canonical-asset.json', 'runs.json'):
                path = f'experiments/{experiment}/{name}'
                if (root / path).is_file():
                    record['evidence'].append(evidence(path))
            if experiment in STATIC:
                for common, key in [(False, 'per_segment'), (True, 'common_per_segment')]:
                    helpers.validate_result(row, common=common)
                    for i, segment in enumerate(row[key]):
                        record['segments'].append({**helpers.normalize_segment(segment, common),
                            'label_schema': 'common18' if common else 'native19',
                            'source_pointer': f'/{arm}/{key}/{i}'})
                if experiment in HAND_RECORDS:
                    path = f'experiments/{HAND_RECORDS[experiment]}/measurements.json'
                    measurements = read(path)
                    record['metrics'] = hand_metrics(measurements[arm], variant)
                    # Prefix with the evidence file: static metrics use a second source.
                    for item in record['metrics']:
                        item['source_pointer'] = path + '#/' + arm + item['source_pointer']
                    record['evidence'].append(evidence(path, '/' + arm))
                record['limitations'].append('Static sample/segment metrics do not establish motion quality')
            else:
                record['metrics'] = motion_metrics(row)
                for item in record['metrics']:
                    if item['source_pointer'] is not None:
                        item['source_pointer'] = result_path + '#/' + arm + item['source_pointer']
                record['limitations'].extend([
                    'One HiPHI clip; no multi-clip or seed confidence interval',
                    'All-hinge smoothness includes constant fingers; do not rank across embodiments',
                    'Visual floor extent is not self-collision depth, contact force or dynamics feasibility',
                    'Ankle stance is inferred from height, not measured contact'])
            validate(record, 'result')
            results.append(record)
    identities = {r['run_id']: r for r in results}
    for record in results:
        if record['matched_control']:
            control = identities[record['matched_control']]
            for key in ('source_model', 'center', 'variant', 'task'):
                if record[key] != control[key]:
                    raise ValueError(f'Mismatched control: {record["run_id"]}: {key}')
    summary = _summary(results, inventory)
    # Catch concurrent source edits before any output is published.
    for path, item in sources.items():
        if sha256(resolve(root, path)) != item['sha256']:
            raise ValueError(f'Source changed during reconstruction: {path}')
    destination.mkdir(parents=True, exist_ok=False)
    with (destination / 'results.jsonl').open('x') as stream:
        for record in results:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
    write_json(destination / 'inventory.json', inventory)
    write_json(destination / 'summary.json', summary)
    with (destination / 'README.md').open('x') as stream:
        stream.write(_markdown(summary))
    seal(destination, list(sources.values()), root)
    return summary


def _summary(results: list[dict], inventory: list[dict]) -> dict:
    counts = Counter((r['cohort_id'], r['task']) for r in results)
    fixed_fist_motion = [r for r in results if r['cohort_id'] == 'fixed_fist_v1' and r['task'] == 'motion']
    motion = []
    for r in fixed_fist_motion:
        metrics = {m['id']: m['value'] for m in r['metrics']}
        motion.append({'arm': r['arm_id'], 'frames': r['conditions']['frames'],
                       'fps': r['conditions']['fps'],
                       'worst_visual_below_floor_mm': metrics['visual_floor_worst_below_floor_extent'],
                       'joint_limit_violation_joint_frames': metrics['configured_joint_limit_violations']})
    return {'schema_version': 1, 'evidence_origin': 'retrospective', 'reproducibility': 'not_rerun',
            'normalized_arms': len(results), 'static_arms': sum(r['task'] == 'static_correspondence' for r in results),
            'motion_arms': sum(r['task'] == 'motion' for r in results),
            'segment_rows': sum(len(r['segments']) for r in results),
            'legacy_segment_rows': sum(len(r['segments']) for r in results if r['cohort_status'] == 'legacy'),
            'new_baseline_arms': 0,
            'inventory_experiments': len(inventory),
            'cohorts': [{'cohort_id': c, 'task': t, 'arms': n} for (c, t), n in sorted(counts.items())],
            'legacy_fixed_fist_motion': motion,
            'disclosures': [
                'Four legacy fixed-fist Astro trainings; four G1 static slot controls are reused, not retrained',
                'Eight fresh motion solves are recorded historically; none rerun in this task',
                'BONES-SEED motion, matching actor shape and rig unavailable; no SOMA motion result',
                'Report README opening 37.05→56.71 and 28.14→30.76 mm describes open-hand v4',
                'Legacy fixed-fist values must be read from umr-motion-fist-v1/results.json',
                'Raw remains default; a single extent metric does not adopt the calibration candidate',
                '19DOF/29DOF head-objective history must not be projected onto fixed-fist evidence'.replace('19DOF/29DOF', '29DOF'),
                'Legacy recorded solver self-penetration cost=0 and hard constraint=false; limit compliance is not collision freedom']}


def _markdown(summary: dict) -> str:
    lines = ['# Reconstructed Motion Studio evidence', '',
             'This is a derived index of saved records, not a tested numerical rerun. '
             'All indexed cohorts are legacy, excluded from the new baseline. '
             'Original records and their hashes are in `manifest.json`. No raw artifact was changed.', '',
             f"Normalized {summary['static_arms']} static arms, {summary['segment_rows']} segment rows "
             f"and {summary['motion_arms']} motion arms. Earlier dissimilar audits remain inventoried, not pooled.", '',
             '| Legacy fixed-fist motion arm | Frames | Worst visual below-floor extent (mm) | Limit violations (joint-frames) |',
             '| --- | ---: | ---: | ---: |']
    for row in summary['legacy_fixed_fist_motion']:
        lines.append(f"| {row['arm']} | {row['frames']} | {row['worst_visual_below_floor_mm']:.4f} | "
                     f"{row['joint_limit_violation_joint_frames']} |")
    lines.extend(['', 'These are post-filter visual-mesh extrema against Z=0. '
                  'They are not collision-geometry depths, forces or selected-slot constraints.', ''])
    lines.extend('- ' + text for text in summary['disclosures'])
    lines.extend(['', 'Use `results.jsonl` for per-arm conditions, exact saved config paths, commands, '
                  'unknowns, matched controls, metric units/aggregation and native19/common18 rows. '
                  'All raw/pre-filter physical clearance values remain unmeasured in this reconstruction.', ''])
    return '\n'.join(lines)
