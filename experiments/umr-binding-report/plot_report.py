"""Replot saved pairings only; original evidence and canonical assets are read-only.

The latest grid uses saved common18 labels; earlier grids use native19 labels.
Shoulder masks are the joint-region labels leftShoulder/rightShoulder, never the
artificial UpperArm classes. Coordinates, triangles and point order are unchanged.
"""
from pathlib import Path
import hashlib
import json
import textwrap
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/umr-binding-report/figures'
INPUTS = {}
CHECKS = []
ROWS = [(['head/face', 'neck'], 'Head / neck', '#dc2f5b'),
        (['leftShoulder', 'rightShoulder'], 'Shoulder / clavicle', '#8a48bd'),
        (['torso'], 'Torso', '#bc8300'),
        (['hips'], 'Hips / pelvis', '#dd632b'),
        (['leftUpLeg', 'rightUpLeg'], 'Thigh', '#3869b1'),
        (['leftForeArm', 'rightForeArm'], 'Forearm', '#00856c')]
NAMES = {'human': 'Human source', 'visual': 'Astro visual',
         'primitive': 'Astro primitives\nREJECTED binding',
         'g1': 'G1', 'astro': 'Astro', 'piplus': 'PiPlusPro', 'k1': 'Booster K1',
         't800': 'T800', 'h2': 'H2', 'mimickit': 'MimicKit',
         'g1_racket': 'G1 racket', 'g1_spherehand': 'G1 sphere hands'}


def read(path):
    data = path.read_bytes()
    INPUTS[str(path.relative_to(ROOT))] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return data


def load(experiment):
    view = ROOT / 'outputs' / experiment / 'viewer'
    return view, json.loads(read(view / 'audit.json')), json.loads(read(ROOT / 'experiments' / experiment / 'results.json'))


def plot(experiment, columns, filename, center=None, heading=None):
    view, data, records = load(experiment)
    common = center is not None
    fig, axes = plt.subplots(6, len(columns), figsize=(3.25 * len(columns), 18.5), facecolor='white')
    for col, column in enumerate(columns):
        source, name = column[:2]
        column_center = column[2] if len(column) == 3 else center
        key = f'{source}_{"astro" if name == "human" else name}_{column_center}' if common else ('visual' if name == 'human' and 'visual' in data['arms'] else 'g1' if name == 'human' else name)
        arm = data['arms'][key]
        meta = (arm['human_mesh'] if common else data['human_mesh']) if name == 'human' else arm['mesh']
        vertices = np.frombuffer(read(view / meta['vertices']['file']), dtype='<f4').reshape(-1, 3)
        faces = np.frombuffer(read(view / meta['faces']['file']), dtype='<u4').reshape(-1, 3)
        triangles = vertices[faces]
        triangles = triangles[np.argsort(triangles[:, :, 2].mean(1))]
        points = np.asarray(arm['human'] if name == 'human' else arm['projected'])
        labels = np.asarray(arm['source_common'] if common else arm['source_labels'])
        saved = records[key]['common_per_segment' if common else 'per_segment']
        counts = {r['source']: r['slots'] for r in saved}
        for label in ['leftShoulder', 'rightShoulder', 'hips']:
            actual = int(np.count_nonzero(labels == label))
            assert actual == counts[label], (experiment, key, label, actual, counts[label])
            CHECKS.append({'experiment': experiment, 'arm': key, 'column': name, 'scheme': 'common18' if common else 'native19', 'label': label, 'plotted_slots': actual, 'saved_slots': counts[label]})
        for row, (segments, title, color) in enumerate(ROWS):
            ax = axes[row, col]
            ax.add_collection(PolyCollection(triangles[:, :, :2], facecolor='#c8cdd2', edgecolor='none', rasterized=True))
            mask = np.isin(labels, segments if common or row else ['head'])
            ax.scatter(points[mask, 0], points[mask, 1], s=5, c=color, zorder=3, linewidths=0)
            if row == 0:
                neck = labels == 'neck' if common else mask & (np.asarray(arm['source55']) == 12)
                ax.scatter(points[neck, 0], points[neck, 1], s=5, c='#00a9c7', zorder=4, linewidths=0)
            if name != 'human' and row in [4, 5]:
                for side in ['left', 'right']:
                    anchor = arm['anchors'][side + ('_knee_joint' if row == 4 else '_elbow_joint')]
                    ax.plot([anchor[1] - .045, anchor[1] + .045], [anchor[2], anchor[2]], c='black', lw=1, zorder=5)
            ax.set_aspect('equal')
            ax.set_xlim(vertices[:, 0].min() - .035, vertices[:, 0].max() + .035)
            ax.set_ylim(vertices[:, 1].min() - .035, vertices[:, 1].max() + .035)
            ax.axis('off')
            if row == 0:
                ax.set_title((source.upper().replace('SMPLX', 'SMPL-X') + ' · ' if common else '') + NAMES[name] + ('\n' + column_center if len(column) == 3 else ''), fontsize=11)
            if col == 0:
                ax.text(-.07, .5, title, transform=ax.transAxes, rotation=90, va='center', ha='right', fontsize=10)
    scheme = 'common18' if common else 'native19'
    title_lines = [heading or f'Saved static pairings · {center or scheme} · actual selected triangles',
                   'Red: head/face; cyan: neck; purple: shoulder/clavicle; orange: hips/pelvis; gold: torso; blue: thigh; green: forearm; black: knee/elbow pivots',
                   'Shoulder = leftShoulder/rightShoulder joint regions, not artificial UpperArm subdivisions. Hips/pelvis = hips source class, not thighs.',
                   'Points visible through geometry; independent equal-height views.' +
                   (' Different source shapes and samples; no cross-source slot identity.' if common and not heading else '')]
    width = 40 * len(columns)
    fig.suptitle('\n'.join(textwrap.fill(line, width=width) for line in title_lines), fontsize=10 if len(columns) == 2 else 11)
    fig.subplots_adjust(top=.86 if len(columns) == 2 else .895, bottom=.02, left=.055, right=.995, hspace=.09, wspace=.08)
    fig.savefig(OUT / filename, dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    columns = [(s, n) for n in ['human', 'astro', 'g1'] for s in ['smplx', 'soma']]
    for center in ['spine1', 'bbox50']:
        plot('soma-correspondence-audit', columns, f'segment-evidence-{center}-expanded.png', center)
    plot('soma-correspondence-audit', [('smplx', 'astro', 'bbox50'), ('smplx', 'g1', 'spine1')],
         'selected-smplx-expanded.png', 'mixed',
         'Selected SMPL-X illustrations · different centering, not a matched-center ranking')
    plot('soma-correspondence-audit', [(
        'smplx', robot, c) for c in ['spine1', 'bbox50'] for robot in ['astro', 'g1']],
         'matched-smplx-expanded.png', 'mixed',
         'SMPL-X companion controls · matched spine1 pair, then matched bbox50 pair')
    plot('segment-binding-audit', [(None, n) for n in ['human', 'visual', 'primitive', 'g1']], 'segment-evidence-expanded.png')
    plot('all-robot-segment-audit', [(None, n) for n in ['human', 'piplus', 'k1', 'g1', 't800']], 'demo-evidence-expanded.png')
    plot('all-robot-segment-audit', [(None, n) for n in ['visual', 'h2', 'mimickit', 'g1_racket', 'g1_spherehand']], 'additional-evidence-expanded.png')
    read(Path(__file__))
    for exp in ['soma-correspondence-audit', 'segment-binding-audit', 'all-robot-segment-audit']:
        read(ROOT / 'experiments' / exp / 'plot_audit.py')
    manifest = {'purpose': 'Replot existing saved labels, triangles and projected slots; no new experiment', 'figure_language': 'en',
                'inputs': INPUTS, 'source_mask_checks': CHECKS,
                'outputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*-expanded.png'))}}
    (OUT / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Generated {len(manifest["outputs"])} English expanded grids; {len(CHECKS)} source-mask checks passed.')


if __name__ == '__main__':
    main()
