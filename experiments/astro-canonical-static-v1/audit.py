"""Rebuild bindings and anatomical metrics on the exact frozen model."""
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/astro-canonical-static-v1'
OLD = ROOT / 'experiments/soma-correspondence-audit'
sys.path.insert(0, str(OLD))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, OLD / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    base = load('canonical_anatomical_audit', 'audit.py')
    base.HERE, base.OUT, base.VIEW = HERE, OUT, OUT / 'viewer'
    base.VIEW.mkdir(exist_ok=True)
    arms = json.loads((HERE / 'arms.json').read_text())
    results, previews, hands, bindings = {}, {}, {}, {}
    reference = {}
    for arm, path in arms.items():
        print('AUDIT', arm, flush=True)
        ds, slots, metrics, preview = base.audit(arm, path)
        robot = arm.split('_')[1]
        if robot in reference:
            for key in ['mesh_vertices_1', 'mesh_faces_1', 'sample_face_ids_1']:
                np.testing.assert_array_equal(ds[key], reference[robot][key])
            np.testing.assert_array_equal(ds['points'][1], reference[robot]['points'][1])
        reference[robot] = ds
        c = json.loads(Path(path).read_text())
        model = mujoco.MjModel.from_xml_path(c['robot']['xml'])
        data = mujoco.MjData(model)
        base.build.apply_joint_qpos(model, data, c['robot']['tpose_qpos'], required=True)
        mujoco.mj_forward(model, data)
        v, f, owners, *_ = base.geometry(model, data, c, 'auto')
        np.testing.assert_array_equal(f, ds['mesh_faces_1'])
        np.testing.assert_allclose(v @ base.rb.SMPL_TO_ROBOT_ROOT_MATRIX,
                                   ds['mesh_vertices_1'], atol=2e-7, rtol=0)
        b = base.rb.bind_robot_slots(model, SimpleNamespace(config_data=c),
                                    slots['reconstructed_slots'][1])
        projected = base.bind_points_to_mesh(base.rb.smpl_frame_to_robot_root(
            slots['reconstructed_slots'][1]), v, f, method='nearest_vertex')
        np.testing.assert_array_equal(b['geom_ids'], owners[projected['face_ids']])
        bids = model.geom_bodyid[b['geom_ids']]
        np.savez_compressed(OUT / f'{arm}-binding.npz', **b,
            body_ids=bids, face_ids=projected['face_ids'],
            body_names=np.array([model.body(int(i)).name for i in bids]),
            mesh_names=np.array([model.mesh(int(model.geom_dataid[g])).name
                                 for g in b['geom_ids']]))
        bindings[arm] = {'xml': c['robot']['xml'], 'xml_sha256': base.sha(c['robot']['xml']),
            'face_count': len(f), 'all_4096_face_geom_body_mesh_bindings_rebuilt': True,
            'dataset_geometry_equal_within_200nm': True,
            'numeric_geom_ids_reused_from_history': False}
        results[arm], previews[arm] = metrics, preview
        a = np.load(OUT / f'{arm}-audit.npz')
        hands[arm] = {}
        for side in ['left', 'right']:
            mask = a['source_common'] == side + 'Hand'
            actual = np.char.startswith(a['mesh_names'], side + '_') & np.array(
                ['hand' in n for n in a['mesh_names']])
            fingers = actual & np.array(['palm' not in n for n in a['mesh_names']])
            if robot == 'g1':
                fingers[:] = False
            hands[arm][side] = {'human_hand_slots': int(mask.sum()),
                'same_side_actual_hand_mesh': int((mask & actual).sum()),
                'same_side_finger_mesh': int((mask & fingers).sum()),
                'hand_slots_by_mesh': base.table(a['source_common'][mask], a['mesh_names'][mask])}
    for kind in ['per_segment', 'common_per_segment']:
        rows = [{'arm': arm, **row} for arm, m in results.items() for row in m[kind]]
        with (HERE / (kind.replace('_', '-') + '.csv')).open('w') as f:
            w = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k != 'expected_sample_distance_m'],
                               extrasaction='ignore')
            w.writeheader()
            w.writerows(rows)
    base.dump(HERE / 'results.json', results)
    base.dump(HERE / 'hand-diagnostics.json', hands)
    base.dump(HERE / 'numeric-bindings.json', bindings)
    base.dump(base.VIEW / 'audit.json', {'arms': previews,
        'human_mesh': next(iter(previews.values()))['human_mesh'], 'human_equal': False})
    (base.VIEW / 'index.html').write_text((OLD / 'viewer.html').read_text().replace(
        'SMPL-X / SOMA audit', 'Canonical Astro d207095 / G1 control'))
    (base.VIEW / 'app.js').write_text((OLD / 'viewer.js').read_text().replace(
        "?'Astro':'G1'", "?'Canonical Astro d207095':'G1 reused control'"))
    validator = load('canonical_global_projection', 'validate_binding.py')
    validator.HERE, validator.OUT = HERE, OUT
    shutil.copy2(ROOT / 'outputs/soma-correspondence-audit/human-weight-diagnostics.npz',
                 OUT / 'human-weight-diagnostics.npz')
    validator.main()


if __name__ == '__main__':
    main()
