"""Independent array checks for fixed-fist initialization, QP constraints and exports."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import mujoco
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/umr-motion-fist-v1'

def sha(p):
    return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()

def main():
    asset = json.loads((ROOT / 'experiments/astro-fist-static-v1/canonical-asset.json').read_text())
    fist = asset['fixed_finger_positions_rad']
    assert len(fist) == 14
    records = {}
    for arm, path in json.loads((HERE / 'arms.json').read_text()).items():
        c = json.loads(Path(path).read_text())
        z = np.load(c['retarget']['out'], allow_pickle=True)
        m = mujoco.MjModel.from_xml_path(c['robot']['xml'])
        assert np.isfinite(z['qpos']).all() and np.isfinite(z['unfiltered_qpos']).all()
        if '_astro_' not in arm:
            continue
        assert sha(c['robot']['xml']) == asset['xml_sha256']
        ds = np.load(c['correspondence']['dataset']['out'], allow_pickle=True)
        pose = dict(zip(ds['custom_robot_sample_qpos_names'], ds['custom_robot_sample_qpos_values']))
        key = m.key('fist').qpos
        errors = {}
        for name, value in fist.items():
            adr = int(m.joint(name).qposadr[0])
            assert key[adr] == value
            assert c['robot']['joint_limits'][name] == [value, value]
            assert c['robot']['tpose_qpos'][name] == value
            assert abs(float(pose[name]) - value) < 1e-7
            errors[name] = {field: float(abs(z[field][:, adr].astype(np.float64) - value).max())
                            for field in ['qpos', 'unfiltered_qpos']}
            assert all(err < 1e-7 for err in errors[name].values())
        observations = json.loads(Path(c['retarget']['out'] + '.fixed-coordinate-observations.json').read_text())
        assert observations['qp_bound_calls'] == 1837
        assert observations['fixed_finger_bounds_checked'] == 14 * observations['qp_bound_calls']
        assert observations['max_initial_finger_error_rad'] == 0
        log = (OUT / (arm + '.log')).read_text()
        assert 'configured=14 matched_same_name=14 scalar_joints=43' in log
        assert not any(s in log for s in ['QP failed', 'Traceback', '[JointLimit][WARN]', 'fallback'])
        records[arm] = {'tolerance_rad': 1e-7, 'frames': len(z['qpos']),
                        'observations': observations, 'per_joint_max_errors_rad': errors,
                        'trajectory_sha256': sha(c['retarget']['out'])}
    source = json.loads((HERE / 'source-reuse.json').read_text())
    for path, item in source['files'].items():
        assert sha(path) == item['sha256'] == item['copied_sha256']
        assert sha(OUT / 'viewer' / Path(path).name) == item['sha256']
    result = {'astro_fixed_fist_arms': records, 'all14_keyframe_preset_and_config_equal': True,
              'source_viewer_exact_reuse_verified': True, 'no_solver_failure_or_lock_warning': True}
    (HERE / 'fixed-fist-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({arm: {'calls': v['observations']['qp_bound_calls'],
        'max_pre_and_post_error_rad': max(max(e.values()) for e in v['per_joint_max_errors_rad'].values())}
        for arm, v in records.items()}, indent=2))

if __name__ == '__main__':
    main()
