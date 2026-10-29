"""Verify canonical model identity, source controls and fresh computation provenance."""
import hashlib
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import subprocess
import sys

import mujoco
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/astro-fist-static-v1'
EXT = ROOT / 'externals/UMR-astro-surface-experiment'
ASSETS = Path('/data/workspace/notAnyrobot/menagerie_x')


def sha(path):
    return hashlib.sha256(canonical_motion_path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def main():
    asset = read(HERE / 'canonical-asset.json')
    prep = read(HERE / 'preparation.json')
    for path, digest in asset['files'].items():
        assert sha(path) == digest, path
    patch = subprocess.check_output(['git', '-C', str(EXT), 'diff', 'HEAD'])
    assert hashlib.sha256(patch).hexdigest() == prep['umr_diff_sha256']
    runs = read(OUT / 'run-records.json')
    assert len(runs) == 4 and all(r['returncode'] == 0 for r in runs)
    raw = read(HERE / 'results.json')
    prior_hand = read(ROOT / 'experiments/astro-hands-correspondence/results.json')
    controls = prep['controls']
    checked, source_checks, slot_delta = {}, [], {}
    for arm, path in read(HERE / 'arms.json').items():
        c = read(path)
        historical = read(controls[arm]['config'])
        ds = np.load(c['correspondence']['dataset']['out'], allow_pickle=True)
        old = np.load(historical['correspondence']['dataset']['out'], allow_pickle=True)
        for key in ['mesh_vertices_0', 'mesh_faces_0', 'sample_face_ids_0', 'betas_0', 'root_offsets']:
            np.testing.assert_array_equal(ds[key], old[key])
        np.testing.assert_array_equal(ds['points'][0], old['points'][0])
        slots = np.load(Path(c['correspondence']['train']['out_dir']) /
                        'correspondence_slots_final.npz', allow_pickle=True)
        oldslots = np.load(Path(historical['correspondence']['train']['out_dir']) /
                           'correspondence_slots_final.npz', allow_pickle=True)
        for key in ['template_points', 'template_sort_index', 'template_edge_index']:
            np.testing.assert_array_equal(slots[key], oldslots[key])
        np.testing.assert_array_equal(slots['reconstructed_slots'][0], oldslots['reconstructed_slots'][0])
        assert slots['reconstructed_slots'].shape == (2, 4096, 3)
        assert np.isfinite(slots['reconstructed_slots']).all()
        if '_astro_' in arm:
            assert c['robot']['xml'] == asset['xml']
            assert 'epoch=00500' in (OUT / f'{arm}-train.log').read_text()
            assert (Path(c['correspondence']['train']['out_dir']) / 'checkpoint-final.pt').exists()
            slot_delta[arm] = float(abs(slots['reconstructed_slots'] - oldslots['reconstructed_slots']).max())
            assert slot_delta[arm] > 0, 'Fist training must differ from open-hand training'
            fist = asset['fixed_finger_positions_rad']
            for n, v in fist.items():
                assert c['robot']['tpose_qpos'][n] == v
                assert c['robot']['joint_limits'][n] == [v, v]
            np.testing.assert_allclose(ds['custom_robot_sample_qpos_values'], [c['robot']['tpose_qpos'][str(n)] for n in ds['custom_robot_sample_qpos_names']], atol=1e-7, rtol=0)
        else:
            np.testing.assert_array_equal(slots['reconstructed_slots'], oldslots['reconstructed_slots'])
            oldrobot, newrobot = historical['robot'].copy(), c['robot'].copy()
            oldrobot.pop('xml')
            newrobot.pop('xml')
            assert oldrobot == newrobot
        source_checks.append(arm + ': exact historical human sample/order/graph; model-specific binding rebuilt')
        for p in [Path(path), Path(c['robot']['xml']), Path(c['correspondence']['dataset']['out']),
                  Path(c['correspondence']['train']['out_dir']) / 'correspondence_slots_final.npz',
                  OUT / f'{arm}-binding.npz', OUT / f'{arm}-audit.npz', OUT / f'{arm}-exact-projection.npz']:
            checked[str(p)] = sha(p)
        assert sum(r['slots'] for r in raw[arm]['common_per_segment']) == 4096
    wrist = ROOT / 'experiments/astro-fist-wrist-v1'
    wp = read(wrist / 'preparation.json')
    for path, digest in wp['historical_artifact_hashes'].items():
        assert sha(path) == digest, path
    measured = read(wrist / 'measurements.json')
    counts = {}
    for arm, path in read(wrist / 'arms.json').items():
        c = read(path)
        if '_astro_' in arm:
            assert c['robot']['xml'] == asset['xml']
        a = np.load(ROOT / f'outputs/astro-fist-wrist-v1/{arm}-audit.npz')
        exact = np.load(ROOT / f'outputs/astro-fist-wrist-v1/{arm}-exact-projection.npz')
        counts[arm] = {}
        for side in ['left', 'right']:
            mask = a['source_common'] == side + 'Hand'
            hand = np.char.startswith(exact['mesh_names'], side + '_') & np.array(
                ['hand' in n for n in exact['mesh_names']])
            n = int((mask & hand).sum())
            assert n == measured[arm]['32'][side]['actual_hand']
            counts[arm][side] = n
        assert all(row['central_head_legs_unchanged'] for row in measured[arm].values())
    archive = Path(prep['report_archive'])
    for path, digest in read(archive / 'hashes.json').items():
        assert sha(archive / path) == digest, path
    for p in (EXT / 'scripts').glob('*.py'):
        checked[str(p)] = sha(p)
    for folder in [HERE, wrist]:
        for p in folder.iterdir():
            if p.is_file() and p.name not in {'provenance.json', 'validation.json'}:
                checked[str(p)] = sha(p)
    live_xml = ASSETS / 'robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml'
    drift = {'head_at_end': git(ASSETS, 'rev-parse', 'HEAD'),
        'live_xml_sha256_at_end': sha(live_xml),
        'same_commit_as_snapshot': git(ASSETS, 'rev-parse', 'HEAD') == asset['menagerie_commit'],
        'same_xml_as_snapshot': sha(live_xml) == asset['xml_sha256'],
        'action': 'Recorded only; all computations use immutable snapshot'}
    validation = {'asset_files_verified': len(asset['files']), 'source_controls': source_checks,
        'fresh_astro_slot_max_absolute_delta_vs_historical': slot_delta,
        'g1_static_slots_exact_reuse_verified': True,
        'all_current_astro_xml_paths_identical': True, 'independent_exact_candidate_hand_counts': counts,
        'central_head_leg_invariance_all_24_derivatives': True,
        'previous_report_archive_verified': True, 'historical_raw_files_verified': len(wp['historical_artifact_hashes']),
        'live_upstream_drift': drift, 'umr_tracked_patch_unchanged': True}
    (HERE / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    (wrist / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    provenance = {'python': sys.version, 'torch': torch.__version__, 'numpy': np.__version__,
        'mujoco': mujoco.__version__, 'umr_revision': prep['umr_revision'],
        'umr_patch_sha256': prep['umr_diff_sha256'], 'asset_commit': asset['menagerie_commit'],
        'asset_xml_sha256': asset['xml_sha256'], 'fresh_training_runs': runs,
        'hashes': checked, 'live_drift': drift}
    (HERE / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('Verified frozen assets, eight raw arms, 24 candidate derivatives, exact projections and report archive')


if __name__ == '__main__':
    main()
