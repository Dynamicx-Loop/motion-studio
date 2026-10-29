"""Independent worked examples for saved evidence and non-executing plans."""
import hashlib
import json
from pathlib import Path

STATIC = ('soma-correspondence-audit', 'astro-hands-correspondence',
          'astro-hand-wrist-correction', 'astro-canonical-static-v1',
          'astro-canonical-wrist-v1', 'astro-fist-static-v1', 'astro-fist-wrist-v1')
MOTION = ('umr-motion-preliminary-v1', 'umr-motion-preliminary-v2',
          'umr-motion-canonical-v1', 'umr-motion-fist-v1')
ARM = 'smplx_g1_spine1'


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def static_row():
    # Both partitions total 4096 independently: 4078+18 and 4079+17.
    native = [{'source': 'head', 'slots': 4078, 'compatible_zone_slots': 2039,
               'zone_precision': 0.5}]
    native += [{'source': f'part-{i}', 'slots': 1, 'compatible_zone_slots': 1,
                'zone_precision': 1.0} for i in range(18)]
    common = [{'source': 'head', 'slots': 4079, 'compatible': 0, 'zone_precision': 0.0}]
    common += [{'source': f'part-{i}', 'slots': 1, 'compatible': 1,
                'zone_precision': 1.0} for i in range(17)]
    return {'per_segment': native, 'common_per_segment': common}


def saved_evidence(root: Path):
    for name in STATIC + MOTION:
        folder = root / 'experiments' / name
        row = static_row() if name in STATIC else {
            'visual_min_height_m': -0.002, 'frames': 10, 'fps': 30,
            'visual_penetration_frames_below_minus_1mm': 2,
            'joint_limit_violation_count_1e6': 0, 'joint_limit_min_margin_rad': 0.25,
            'joint_velocity_abs_rad_s': {'mean': 0.5},
            'joint_acceleration_abs_rad_s2': {'mean': 0.75}}
        write(folder / 'results.json', {ARM: row})
        write(folder / (ARM + '.json'), {'robot': {'name': 'g1'},
                                       'correspondence': {'train': {'seed': 7}}})
        write(folder / 'provenance.json', {'fresh_training_runs': [{'arm': ARM}]})
        hand = {'symmetric_sample_mean_distance_mm': 5,
                'left': {'actual_hand': 3, 'slots': 8, 'actual_hand_coverage20mm': 0.25,
                         'hand_reference_samples': 12},
                'right': {'actual_hand': 4, 'slots': 8, 'actual_hand_coverage20mm': 0.5,
                          'hand_reference_samples': 12}}
        write(folder / 'measurements.json', {ARM: {'0': hand, '32': hand}})
    for path in ('docs/umr-head-objective-investigation.md',
                 'docs/umr-solver-investigation.md', 'docs/umr-soma-setup.md',
                 'docs/umr-astro-baseline-proposal.md'):
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('Saved fixture note.\n')
    # Historical source schemas are inputs; validation uses the owned schema closure.
    for kind in ('plan', 'result'):
        write(root / f'schemas/experiments/{kind}.schema.json', {})


def plan_fixture(root: Path):
    (root / 'input.txt').write_text('Pinned fixture input.\n')
    digest = hashlib.sha256(b'Pinned fixture input.\n').hexdigest()
    return {
        'schema_version': 1, 'experiment_id': 'fixture', 'cohort_id': 'new-fixture',
        'question': 'Does preparation preserve non-execution?',
        'source': {'kind': 'smplx_hiphi', 'clip_id': 'fixture', 'actor_id': None,
                   'interval': {'start': 0, 'end_exclusive': 1, 'stride': 1,
                                'source_fps': 30, 'output_fps': 30},
                   'conventions': {'length_unit': 'm', 'angle_unit': 'rad',
                                   'source_up': 'Y', 'solver_up': 'Z',
                                   'source_to_solver': 'x,-z,y', 'root_quaternion': 'wxyz',
                                   'joint_order': 'named', 'preprocessing': 'none'}},
        'conditions': {key: 'fixture' for key in ('body_pose', 'finger_policy',
                        'head_policy', 'hand_geometry', 'surface_policy')},
        'inputs': [{'id': role, 'role': role, 'path': 'input.txt', 'sha256': digest,
                    'required': True} for role in
                   ('motion_actor', 'robot', 'code', 'dependencies', 'config')],
        'code': {'repository': 'fixture', 'revision': None, 'patch_input': None,
                 'closure_note': 'fixture'},
        'environment': {'python': 'unused', 'dependency_input': 'dependencies',
                        'device': 'unused', 'variables': {}},
        'seeds': {key: None for key in ('source_sampling', 'target_sampling', 'training', 'solver')},
        'arms': [{'id': 'control', 'robot': 'g1', 'center': 'spine1', 'variant': 'raw',
                  'config_input': 'config', 'matched_control': None},
                 {'id': 'astro', 'robot': 'astro', 'center': 'spine1', 'variant': 'raw',
                  'config_input': 'config', 'matched_control': 'control'}],
        'stages': [{'id': 'evaluation', 'kind': 'evaluation', 'input_ids': ['config'],
                    'argv': ['must-not-execute'], 'cwd': '.', 'outputs': ['result.json']}],
        'runtime_checks': {'environment': 'not established'}, 'acceptance': ['fixture only']}
