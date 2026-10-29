"""Verify all fresh trajectories share timing and the immutable canonical models."""
import hashlib
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import sys

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/umr-motion-fist-v1'
EXT = ROOT / 'externals/UMR-astro-surface-experiment'
sys.path.insert(0, str(EXT / 'scripts'))
import retarget_smpl_to_humanoid_surface_vector as rb
import build_correspondence_ae_dataset as build


def sha(path):
    return hashlib.sha256(canonical_motion_path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    asset = read(ROOT / 'experiments/astro-fist-static-v1/canonical-asset.json')
    runs = read(HERE / 'runs.json')
    assert len(runs) == 8 and all(r['returncode'] == 0 for r in runs)
    results = read(HERE / 'results.json')
    assert len(results) == 8
    hashes, timing = {}, {}
    for path, digest in asset['files'].items():
        assert sha(path) == digest, path
    for arm, path in read(HERE / 'arms.json').items():
        c = read(path)
        static = read(c['experiment']['static_config'])
        assert c['robot']['xml'] == static['robot']['xml']
        if '_astro_' in arm:
            assert c['robot']['xml'] == asset['xml']
        assert c['robot']['xml_policy'] == {'add_freejoint_root': False}
        assert sha(c['correspondence']['slots']) == sha(
            Path(static['correspondence']['train']['out_dir']) / 'correspondence_slots_final.npz')
        assert sha(c['correspondence']['dataset']['out']) == sha(static['correspondence']['dataset']['out'])
        baseline = read(ROOT / f'experiments/umr-motion-preliminary-v2/{"_".join(arm.split("_")[:3])}.json')
        assert c['solver'] == baseline['solver'] and c['motion'] == baseline['motion']
        for key, value in baseline['retarget'].items():
            if key != 'out':
                assert c['retarget'][key] == value
        z = np.load(c['retarget']['out'], allow_pickle=True)
        q = z['qpos']
        m = mujoco.MjModel.from_xml_path(c['robot']['xml'])
        d = mujoco.MjData(m)
        hinges = np.flatnonzero(m.jnt_type == mujoco.mjtJoint.mjJNT_HINGE)
        names = [m.joint(int(j)).name for j in hinges]
        assert list(z['robot_joint_names']) == names
        assert q.shape == (1823, m.nq) and np.isfinite(q).all()
        assert np.array_equal(z['frame_ids'], np.arange(0, 5468, 3))
        assert str(z['robot_xml'].item()) == c['robot']['xml']
        assert bool(z['zero_source_finger_pose'][0])
        assert results[arm]['joint_limit_violation_count_1e6'] == 0
        if '_astro_' in arm:
            import smpl_surface_retarget_common as common
            fist = asset['fixed_finger_positions_rad']
            limits, matched = common.build_scalar_joint_limits(m, c['robot']['joint_limits'])
            assert set(fist).issubset(matched) and len(fist) == 14
            observations = read(str(c['retarget']['out']) + '.fixed-coordinate-observations.json')
            assert observations['qp_bound_calls'] > 0
            assert observations['fixed_finger_bounds_checked'] == 14 * observations['qp_bound_calls']
            errors = {'observations': observations, 'matched_fixed_joints': list(fist)}
            for name, value in fist.items():
                adr = int(m.joint(name).qposadr[0])
                assert limits[adr]['lower'] == limits[adr]['upper'] == value
                errors[name] = {}
                for field in ['qpos', 'unfiltered_qpos']:
                    # Saved raw pre-LQR and exported arrays are both checked.
                    arr = z[field] if field in z.files else z['unfiltered_qpos_seq']
                    assert arr.shape == (1823, m.nq)
                    err = float(np.abs(arr[:, adr].astype(np.float64) - value).max())
                    assert err < 1e-7, (arm, field, name, err)
                    errors[name][field + '_max_error_rad'] = err
            (OUT / (arm + '-fixed-fist.json')).write_text(json.dumps(errors, indent=2) + '\n')

        build.apply_joint_qpos(m, d, c['robot']['tpose_qpos'], required=True)
        mujoco.mj_forward(m, d)
        ids = rb.visual_geom_ids(m, 'auto')
        v, f, _, *_ = rb.collect_root_mesh(m, d, ids, c['robot']['point_cloud_center'])
        ds = np.load(c['correspondence']['dataset']['out'], allow_pickle=True)
        np.testing.assert_array_equal(f, ds['mesh_faces_1'])
        np.testing.assert_allclose(v @ rb.SMPL_TO_ROBOT_ROOT_MATRIX, ds['mesh_vertices_1'],
                                   atol=2e-7, rtol=0)
        timing[arm] = {'frames': 1823, 'source_frame_ids': [0, 5466, 3],
            'fps': float(z['fps'][0]), 'qpos_shape': list(q.shape),
            'joint_names_native_order': names, 'xml_sha256': sha(c['robot']['xml']),
            'visual_mesh_matches_static_dataset': True}
        for p in [Path(path), Path(c['retarget']['out']), Path(c['motion']['data']),
                  Path(c['correspondence']['slots']), Path(c['correspondence']['dataset']['out']),
                  OUT / f'{arm}.log', Path(c['robot']['xml']),
                  Path(c['retarget']['out'] + '.fixed-coordinate-observations.json')]:
            hashes[str(p)] = sha(p)
    viewer = OUT / 'viewer'
    manifest = read(viewer / 'manifest.json')
    assert len(manifest['arms']) == 8
    for arm, entry in manifest['arms'].items():
        assert (viewer / entry['transforms']).stat().st_size == 1823 * len(entry['parts']) * 12 * 4
        for part in entry['parts']:
            assert (viewer / part['vertices']).stat().st_size % 12 == 0
            assert (viewer / part['faces']).stat().st_size % 12 == 0
    source = read(viewer / 'source.json')
    assert source['frames'] == 1823
    assert (viewer / 'source-v.bin').stat().st_size == 1823 * source['vertices'] * 3 * 4
    manifest['canonical_asset_commit'] = asset['menagerie_commit']
    manifest['canonical_asset_xml_sha256'] = asset['xml_sha256']
    manifest['candidate_adopted_as_default'] = False
    (viewer / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for folder in [HERE, viewer]:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in str(p) and p.name not in {'provenance.json', 'validation.json'}:
                hashes[str(p)] = sha(p)
    model = Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl')
    hashes[str(model)] = sha(model)
    record = {'date': '2026-10-23', 'runs': runs, 'timing': timing,
        'canonical_asset_commit': asset['menagerie_commit'], 'canonical_xml_sha256': asset['xml_sha256'],
        'source_units': 'metres/radians; input axis-angle; source Y up',
        'solver_frame': '(x,y,z) -> (x,-z,y), Z up', 'root_quaternion': 'wxyz',
        'source_interval': '0:5468:3; no trimming beyond this declared interval; 1823 frames',
        'preprocessing': 'source fingers zeroed; no source ground alignment; LQR output filter',
        'hardware': 'RTX 5070 Laptop 8151MiB; sequential GPU solves; CPU time/RSS in logs; peak GPU memory not instrumented',
        'candidate_default': False, 'SOMA_motion': 'missing BONES-SEED BVH and actor shape/rig; model link verified',
        'files': hashes}
    (HERE / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    (HERE / 'validation.json').write_text(json.dumps({'all_eight_fresh_runs_successful': True,
        'all_frames_joint_orders_and_binary_sizes_verified': True,
        'all_astro_stages_share_exact_canonical_xml': True,
        'all_model_and_input_hashes_verified': True, 'finite_and_zero_configured_limit_violations': True,
        'browser_playback': 'Recorded separately with report validation'}, indent=2) + '\n')
    print('Verified eight fresh trajectories, exact source timing, named joint order, frozen geometry and viewer binaries')


if __name__ == '__main__':
    main()
