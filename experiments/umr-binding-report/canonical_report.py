"""Current canonical evidence adapter; historical arms keep their own identities."""
import hashlib
import json


def extend(read, table, head, pair, pct, normalize, validate, data, values):
    asset = json.loads(read('experiments/astro-fist-static-v1/canonical-asset.json'))
    raw = json.loads(read('experiments/astro-fist-static-v1/results.json'))
    corrected = json.loads(read('experiments/astro-fist-wrist-v1/results.json'))
    measured = json.loads(read('experiments/astro-fist-wrist-v1/measurements.json'))
    motion = json.loads(read('experiments/umr-motion-fist-v1/results.json'))
    fixed = json.loads(read('experiments/umr-motion-fist-v1/fixed-fist-validation.json'))
    rows, hands, tradeoffs, motions = [], [], [], []
    current = {}
    for arm in data['arms'].values():
        arm['label'] = 'Historical / ' + arm['label']
        arm['historical'] = True
    for kind, exp in [('raw', 'astro-canonical-static-v1'), ('candidate', 'astro-canonical-wrist-v1')]:
        old_records = json.loads(read('experiments/' + exp + '/results.json'))
        for key, d in old_records.items():
            data['arms']['open_v4_' + key + '_' + kind] = {
                'label': 'Historical / open-hand v4 / ' + key + ' / ' + kind,
                'head_torso': head(d), 'common': [normalize(r, True) for r in d['common_per_segment']],
                'native': [normalize(r, False) for r in d['per_segment']],
                'transfer_common': d['common_source_to_geometry_zone'],
                'transfer_native': d['source_to_geometry_zone'], 'crossings': d['common_joint_plane_checks'],
                'experiment': exp, 'original_arm': key, 'historical': True}
    for kind, records, exp in [('raw', raw, 'astro-fist-static-v1'),
                               ('candidate', corrected, 'astro-fist-wrist-v1')]:
        for key, d in records.items():
            validate(d)
            validate(d, common=True)
            source, robot, center = key.split('_')
            label = (f'{"SMPL-X" if source == "smplx" else "SOMA"} · '
                     f'{"Fist Astro d207095" if robot == "astro" else "G1 control"} · '
                     f'{center} · {kind}')
            current[f'canonical_{key}_{kind}'] = {'label': label, 'head_torso': head(d),
                'common': [normalize(r, True) for r in d['common_per_segment']],
                'native': [normalize(r, False) for r in d['per_segment']],
                'transfer_common': d['common_source_to_geometry_zone'],
                'transfer_native': d['source_to_geometry_zone'],
                'crossings': d['common_joint_plane_checks'], 'experiment': exp,
                'original_arm': key, 'canonical_asset_sha256': asset['xml_sha256'] if robot == 'astro' else None,
                'historical': False}
            if kind == 'raw':
                leak, n = head(d)
                rows.append([label, f'{leak}/{n} ({pct(leak/n)})', pair(d, 'UpLeg'), pair(d, 'ForeArm')])
    data['arms'] = {**current, **data['arms']}
    for arm, d in measured.items():
        label = current[f'canonical_{arm}_raw']['label']
        a, b = d['0'], d['32']
        def lr(row, field, percent=False):
            return ' / '.join(pct(row[s][field]) if percent else str(row[s][field])
                              for s in ['left', 'right'])
        hands.append([label, lr(b, 'slots'), lr(a, 'actual_hand') + ' → ' + lr(b, 'actual_hand'),
                      lr(a, 'actual_hand_coverage20mm', True) + ' → ' + lr(b, 'actual_hand_coverage20mm', True)])
        tradeoffs.append([label, lr(a, 'nonhand_on_hand') + ' → ' + lr(b, 'nonhand_on_hand'),
            f"{b['max_displacement_mm']:.1f}",
            f"{a['symmetric_sample_mean_distance_mm']:.2f} → {b['symmetric_sample_mean_distance_mm']:.2f}",
            '(' + lr(d['16'], 'actual_hand') + ') / (' + lr(d['64'], 'actual_hand') + ')'])
    for arm, d in motion.items():
        _, robot, center, kind = arm.split('_')
        label = f'{"Fist Astro d207095" if robot == "astro" else "G1"} · {center} · {kind}'
        motions.append([label, d['frames'], d['joint_limit_violation_count_1e6'],
            f"{-d['visual_min_height_m']*1000:.2f}",
            f"{d['joint_velocity_abs_rad_s']['p95']:.3f}",
            f"{d['joint_acceleration_abs_rad_s2']['p95']:.2f}",
            f"{d['solver_reported_cost']['mean']:.6f}"])
    values['CANONICAL_STATIC_TABLE'] = table(
        ['Source · target · center', 'Head/face → torso ↓', 'Thigh below knee L/R ↓', 'Forearm proximal to elbow L/R ↓'],
        rows, 'Current raw bindings. Four fresh Astro trainings; four G1 slot controls reused with identical provenance and rebuilt bindings.')
    values['CANONICAL_HAND_TABLE'] = table(
        ['Current raw arm', 'Source hand slots L/R', 'Actual hand L/R raw → candidate', 'Actual-hand coverage L/R raw → candidate'],
        hands, 'Same canonical surface and labels; k32 candidate; coverage uses fixed reference samples within 20 mm.')
    values['CANONICAL_TRADEOFF_TABLE'] = table(
        ['Current raw arm', 'Non-hand on hand L/R raw → candidate', 'Maximum movement (mm)', 'Global sample distance (mm) raw → candidate', 'Actual hand L/R at k16 / k64'],
        tradeoffs, 'Static calibration sensitivity and costs. Global distance averages both nearest-sample directions; lower is better.')
    values['CANONICAL_MOTION_TABLE'] = table(
        ['Motion arm', 'Frames', 'Limit violations', 'Worst visual penetration (mm)', 'Speed p95 (rad/s)', 'Acceleration p95 (rad/s²)', 'Mean solver cost before filtering'],
        motions, 'Eight fresh HiPHI solves; 1823 frames each, stride 3. Exported-pose metrics and pre-filter solver costs are distinct.')
    for record in ['experiments/umr-binding-report/canonical-figure-provenance.json',
                   'experiments/astro-fist-wrist-v1/figure-provenance.json']:
        provenance = json.loads(read(record))
        for path, item in {**provenance['inputs'], **provenance['outputs']}.items():
            digest = item['sha256'] if isinstance(item, dict) else item
            assert hashlib.sha256(read(path)).hexdigest() == digest, path
    for center, prefix in [('bbox50','BBOX'),('spine1','SPINE')]:
        for kind in ['raw','candidate']:
            values[f'CANONICAL_{prefix}_{kind.upper()}_MM'] = f"{-motion[f'smplx_astro_{center}_{kind}']['visual_min_height_m']*1000:.2f}"
    values['CANONICAL_COMMIT'] = asset['menagerie_commit']
    values['CANONICAL_XML_SHA256'] = asset['xml_sha256']
    data['canonical'] = {'fixed_fist_validation': fixed, 'asset': asset, 'static_arms': 16, 'motion': motion,
        'four_fresh_astro_trainings': True, 'four_g1_static_slot_controls_reused': True,
        'candidate_adopted_as_default': False, 'motion_arms_fresh': 8}
