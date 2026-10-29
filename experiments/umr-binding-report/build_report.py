"""Assemble a local report solely from completed static-audit artifacts.

Run with system Python. No third-party packages, training, model loading, source
mutation, or network access. All rates retain the originating source denominator.
"""
from pathlib import Path
import base64
import hashlib
import html
import json
import math
import sys

# Historical builder remains callable; reusable evidence rules are owned centrally.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from motion_studio.evidence import normalize_segment, validate_static_result as validate_result
from localization import validate_translation
from hands_report import extend as extend_hands
from correction_report import extend as extend_correction
from canonical_report import extend as extend_canonical

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'outputs/umr-binding-report'
INPUTS = {}


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    content = path.read_bytes()
    INPUTS[str(path.relative_to(ROOT))] = {
        'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}
    return content


def record(experiment, filename='results.json'):
    return json.loads(read(f'experiments/{experiment}/{filename}'))


def table(headers, rows, caption):
    e = html.escape
    return ('<div class="table-scroll"><table><caption>' + e(caption) + '</caption>'
            '<thead><tr>' + ''.join('<th scope="col">' + e(x) + '</th>' for x in headers)
            + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(
                ('<th scope="row">' if i == 0 else '<td>') + e(str(x))
                + ('</th>' if i == 0 else '</td>') for i, x in enumerate(row))
                + '</tr>' for row in rows) + '</tbody></table></div>')


def pct(value):
    if value is None:
        return 'N/A'
    assert math.isfinite(value) and 0 <= value <= 1
    return f'{100 * value:.1f}%'


def head(d):
    x = d['head_subregions_to_geometry']['head/face']
    return sum(x.get(z, 0) for z in ('upper torso', 'lower torso')), sum(x.values())


def crossing(d, segment):
    x = d['joint_plane_checks'][segment]
    return x['beyond_joint_plane_over_20mm']


def pair(d, suffix):
    return f"{crossing(d, 'left' + suffix)} / {crossing(d, 'right' + suffix)}"


def arm_label(arm):
    source, robot, center = arm.split('_')
    return f"{'SMPL-X' if source == 'smplx' else 'SOMA'} · {'Astro old / no hand meshes' if robot == 'astro' else 'G1'} · {center}"


def snapshot_records(catalog):
    """Preserve small text evidence with its original relative directory layout."""
    for exp in catalog['experiments']:
        source = ROOT / 'experiments' / exp['id']
        for p in sorted(source.iterdir()):
            if p.is_file() and p.suffix in {'.md', '.json', '.csv', '.py', '.js', '.html', '.patch'}:
                data = read(p)
                target = OUT / 'records' / p.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    for extra in catalog.get('additional_research_notes', []):
        p = ROOT / extra
        target = OUT / 'records' / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(read(p))
    p = ROOT / catalog['research_note']
    target = OUT / 'records' / p.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(read(p))


def snapshot_inspectors(catalog):
    count = 0
    for key, source in catalog['inspectors'].items():
        for p in sorted((ROOT / source).rglob('*')):
            if not p.is_file():
                continue
            # Copy bytes, never symlink mutable old results or write into them.
            data = read(p)
            target = OUT / 'inspectors' / key / p.relative_to(ROOT / source)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != hashlib.sha256(data).hexdigest():
                target.write_bytes(data)
            count += 1
    return count


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(read(HERE / 'catalog.json'))
    soma = record('soma-correspondence-audit')
    robots = record('all-robot-segment-audit')
    native = record('all-robot-segment-audit', 'native-center-results.json')
    for d in soma.values():
        validate_result(d)
        validate_result(d, common=True)
    for group in (robots, native):
        for d in group.values():
            validate_result(d)
    assert len(soma) == 8 and len(robots) == 10 and len(native) == 5

    latest_rows = []
    for center in ('spine1', 'bbox50'):
        for robot in ('astro', 'g1'):
            for source in ('smplx', 'soma'):
                arm = f'{source}_{robot}_{center}'
                d = soma[arm]
                leak, total = head(d)
                latest_rows.append([arm_label(arm), f'{leak}/{total} ({pct(leak/total)})',
                                    pair(d, 'UpLeg'), pair(d, 'ForeArm')])

    labels = {'visual': 'Astro visual', 'primitive': 'Astro primitives †', 'g1': 'G1',
              'piplus': 'PiPlusPro', 'k1': 'Booster K1', 't800': 'T800', 'h2': 'H2',
              'mimickit': 'MimicKit ‡', 'g1_racket': 'G1 racket', 'g1_spherehand': 'G1 sphere hands'}
    robot_rows = []
    for key in ('visual', 'primitive', 'piplus', 'k1', 'g1', 't800', 'h2', 'mimickit', 'g1_racket', 'g1_spherehand'):
        d = robots[key]
        leak, total = head(d)
        robot_rows.append([labels[key], f'{leak}/{total}', pair(d, 'UpLeg'), pair(d, 'ForeArm')])

    native_rows = []
    for key, d in native.items():
        base = key.removesuffix('_native_center')
        b = robots[base]
        native_rows.append([labels[base], f'{head(b)[0]} → {head(d)[0]}',
                            f'{pair(b,"UpLeg")} → {pair(d,"UpLeg")}',
                            f'{pair(b,"ForeArm")} → {pair(d,"ForeArm")}'])

    center_rows = []
    specs = [('head/face', 'coverage_within_20mm', 'Head-shell coverage'),
             ('torso', 'zone_precision', 'Torso precision'), ('hips', 'zone_precision', 'Hips precision'),
             ('leftUpLeg', 'zone_precision', 'Left thigh precision'),
             ('rightUpLeg', 'zone_precision', 'Right thigh precision')]
    for segment, metric, label in specs:
        values = []
        for robot in ('astro', 'g1'):
            for source in ('smplx', 'soma'):
                vals = [next(r for r in soma[f'{source}_{robot}_{c}']['common_per_segment'] if r['source'] == segment)[metric]
                        for c in ('spine1', 'bbox50')]
                values.append(f'{pct(vals[0])} → {pct(vals[1])}')
        center_rows.append([label] + values)

    data = {'schema_version': 1, 'snapshot_date': catalog['snapshot_date'], 'arms': {}}
    for arm, d in soma.items():
        data['arms'][arm] = {
            'label': arm_label(arm), 'head_torso': head(d),
            'common': [normalize_segment(r, True) for r in d['common_per_segment']],
            'native': [normalize_segment(r, False) for r in d['per_segment']],
            'transfer_common': d['common_source_to_geometry_zone'],
            'transfer_native': d['source_to_geometry_zone'],
            'crossings': d['common_joint_plane_checks'],
        }

    values = {
        'CSS': read(HERE / 'report.css').decode(), 'JS': read(HERE / 'report.js').decode(),
        'I18N': read(HERE / 'zh.json').decode().replace('<', '\\u003c'),
        'DATA': json.dumps(data, separators=(',', ':')).replace('<', '\\u003c'),
        'LATEST_TABLE': table(['Source · target · center', 'Head/face → torso ↓', 'Thigh below knee L/R ↓', 'Forearm proximal to elbow L/R ↓'], latest_rows, 'Saved production bindings; crossing threshold >20 mm. Counts are not motion errors.'),
        'ROBOT_TABLE': table(['Target', 'Head/face → torso /353', 'Thigh below knee L/R', 'Forearm proximal to elbow L/R'], robot_rows, 'Exact-source SMPL-X comparison: identical actor/template, 4096 slots, 500 epochs.'),
        'NATIVE_TABLE': table(['Robot', 'Head/face → torso', 'Knee crossings L/R', 'Elbow crossings L/R'], native_rows, 'Earlier sensitivity study: spine1 → robot-specific shipped bbox ratio. Different from common bbox50.'),
        'CENTER_TABLE': table(['Metric ↑', 'Astro · SMPL-X', 'Astro · SOMA', 'G1 · SMPL-X', 'G1 · SOMA'], center_rows, 'Within each source: spine1 → bbox50; percentages retain their original denominators.'),
        'CATALOG_TABLE': table(['Completed record', 'Scope', 'Outcome'], [[e['title'], e['stage'], e['status']] for e in catalog['experiments']], 'These records reuse some checkpoints. Their arm counts must not be added as independent runs.'),
    }
    extend_hands(read, table, head, pair, pct, normalize_segment, validate_result, data, values)
    extend_correction(read, table, head, pct, normalize_segment, validate_result, data, values)
    extend_canonical(read, table, head, pair, pct, normalize_segment, validate_result, data, values)
    translations = json.loads(values['I18N'])
    translations.update(json.loads(read(HERE / 'canonical-zh.json')))
    for arm in data['arms'].values():
        translations[arm['label'].removeprefix('Historical / ')] = arm['label'].removeprefix('Historical / ').replace('static calibration', '静态校准')
        translations[arm['label']] = arm['label'].replace('Historical / ', '历史 / ').replace('Canonical Astro d207095', '当前 Astro d207095').replace('Fist Astro d207095', '握拳 Astro d207095').replace('open-hand v4', '张手 v4').replace('G1 control', 'G1 对照').replace('static calibration', '静态校准').replace('raw', '原始').replace('candidate', '候选')
    values['I18N'] = json.dumps(translations, ensure_ascii=False).replace('<', '\\u003c')
    values['DATA'] = json.dumps(data, separators=(',', ':')).replace('<', '\\u003c')
    for key, path in catalog['figures'].items():
        values['FIG_' + key] = 'data:image/png;base64,' + base64.b64encode(read(path)).decode()
    template = read(HERE / 'report.html').decode()
    template = template.replace('{{CANONICAL_SECTION}}', read(HERE / 'canonical-section.html').decode())
    read(HERE / 'canonical_report.py')
    template = template.replace('{{HANDS_SECTION}}', read(HERE / 'hands-section.html').decode())
    read(HERE / 'hands_report.py')
    template = template.replace('{{CORRECTION_SECTION}}', read(HERE / 'correction-section.html').decode())
    read(HERE / 'correction_report.py')
    for key, value in values.items():
        template = template.replace('{{' + key + '}}', value)
    assert '{{' not in template, 'Unresolved report token'
    translated_texts = validate_translation(template, json.loads(values['I18N']), [a['label'] for a in data['arms'].values()])
    (OUT / 'index.html').write_text(template)
    (OUT / 'summary-data.json').write_text(json.dumps(data, indent=2) + '\n')
    snapshot_records(catalog)
    copied = snapshot_inspectors(catalog)
    derivation = json.loads(read(catalog['figure_derivation']))
    for path, info in derivation['inputs'].items():
        assert hashlib.sha256(read(path)).hexdigest() == info['sha256'], 'Stale figure input: ' + path
    for path, digest in derivation['outputs'].items():
        assert hashlib.sha256(read(OUT / 'figures' / path)).hexdigest() == digest, 'Stale derivative figure: ' + path
    for path in catalog['historical_figures'].values():
        read(path)
    read(HERE / 'verify_report.py')
    read(HERE / 'localization.py')
    read(HERE / 'plot_report.py')
    read(HERE / 'build_report.py')
    read(ROOT / 'motion_studio/evidence/report_rules.py')
    read(HERE / 'README.md')
    manifest = {'schema_version': 1, 'snapshot_date': catalog['snapshot_date'],
                'purpose': 'Read-only synthesis inputs; no experiment executed',
                'inputs': INPUTS,
                'outputs': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                            for name in ('index.html', 'summary-data.json')}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    validation = {'completed': True, 'source_records': len(catalog['experiments']),
                  'latest_arms': len(data['arms']), 'current_canonical_arms': 16, 'fresh_motion_arms': 8, 'new_hand_arms': 4, 'static_calibration_arms': 8, 'common_rows': len(data['arms']) * 18, 'native_rows': len(data['arms']) * 19,
                  'all_robot_arms': len(robots) + len(native), 'inspector_files_copied': copied,
                  'slot_totals_and_precision_formulas_verified': True,
                  'figures_embedded': len(catalog['figures']),
                  'authored_texts_with_chinese_translation': translated_texts,
                  'expanded_figure_mask_checks': len(derivation['source_mask_checks']),
                  'single_english_figure_set_shared_by_languages': derivation['figure_language'] == 'en',
                  'training_or_retargeting_executed': False,
                  'browser_review': 'Recorded separately after browser inspection'}
    (OUT / 'build-validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    print(json.dumps(validation, indent=2))
    print(OUT / 'index.html')


if __name__ == '__main__':
    main()
