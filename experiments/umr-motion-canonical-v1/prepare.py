"""Prepare fresh raw/candidate motion comparisons from canonical static outputs."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/umr-motion-canonical-v1'


def main():
    assert not (HERE / 'arms.json').exists(), 'Use a new version for another experiment'
    arms = {}
    for kind, exp in [('raw', 'astro-canonical-static-v1'),
                      ('candidate', 'astro-canonical-wrist-v1')]:
        for robot in ['astro', 'g1']:
            for center in ['spine1', 'bbox50']:
                static_arm = f'smplx_{robot}_{center}'
                arm = static_arm + '_' + kind
                c = json.loads((ROOT / f'experiments/umr-motion-preliminary-v2/{static_arm}.json').read_text())
                static = json.loads((ROOT / f'experiments/{exp}/{static_arm}.json').read_text())
                c['robot'] = static['robot']
                # Both frozen models already contain a free root.
                c['robot']['xml_policy'] = {'add_freejoint_root': False}
                dest = OUT / arm
                dest.mkdir(parents=True)
                shutil.copy2(static['correspondence']['dataset']['out'], dest / 'dataset.npz')
                shutil.copy2(Path(static['correspondence']['train']['out_dir']) /
                             'correspondence_slots_final.npz', dest / 'slots.npz')
                c['correspondence']['dataset']['out'] = str(dest / 'dataset.npz')
                c['correspondence']['slots'] = str(dest / 'slots.npz')
                c['correspondence']['train']['out_dir'] = str(dest / 'unused-training')
                c['retarget']['out'] = str(dest / 'trajectory.npz')
                c['experiment'] = {'stage': 'offline_motion', 'retarget_authorized': True,
                    'static_config': str(ROOT / f'experiments/{exp}/{static_arm}.json'),
                    'binding_variant': kind, 'candidate_adopted_as_default': False,
                    'canonical_asset_manifest': str(ROOT / 'experiments/astro-canonical-static-v1/canonical-asset.json'),
                    'protocol': 'Full 5468-frame source; stride 3; same solver; fresh motion solves'}
                path = HERE / f'{arm}.json'
                path.write_text(json.dumps(c, indent=2) + '\n')
                arms[arm] = str(path)
    (HERE / 'arms.json').write_text(json.dumps(arms, indent=2) + '\n')
    print('Prepared 8 fresh motion solves: raw/candidate × Astro/G1 × spine1/bbox50')


if __name__ == '__main__':
    main()
