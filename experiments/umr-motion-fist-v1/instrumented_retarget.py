"""Observe initialization/QP bounds and persist pre-LQR poses without changing solves."""
from pathlib import Path
import inspect
import json
import runpy
import sys
import numpy as np
script = sys.argv.pop(1)
sys.path.insert(0, str(Path(script).parent))
import smpl_surface_retarget_common as common
original_bounds = common.qvel_step_bounds
original_save = np.savez_compressed
observations = {'qp_bound_calls': 0, 'fixed_finger_bounds_checked': 0, 'max_initial_finger_error_rad': 0.0}

def bounds(model, qpos, *args, **kwargs):
    lower, upper = original_bounds(model, qpos, *args, **kwargs)
    for adr, info in (kwargs.get('joint_limits_by_qpos') or {}).items():
        if '_hand_' in info['name'] and info['lower'] == info['upper']:
            err = abs(float(qpos[adr]) - info['lower'])
            assert err < 1e-7
            dof = info['dof_id']
            assert abs(lower[dof]) < 1e-7 and abs(upper[dof]) < 1e-7
            observations['max_initial_finger_error_rad'] = max(observations['max_initial_finger_error_rad'], err)
            observations['fixed_finger_bounds_checked'] += 1
    observations['qp_bound_calls'] += 1
    return lower, upper

def save(file, *args, **kwargs):
    if 'qpos' in kwargs and 'robot_xml' in kwargs:
        raw = inspect.currentframe().f_back.f_locals['unfiltered_qpos_seq']
        kwargs['unfiltered_qpos'] = raw.copy()
        Path(str(file) + '.fixed-coordinate-observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    return original_save(file, *args, **kwargs)

common.qvel_step_bounds = bounds
np.savez_compressed = save
runpy.run_path(script, run_name='__main__')
