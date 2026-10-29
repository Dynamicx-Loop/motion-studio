#!/usr/bin/env python3
"""Audit trained canonical pairings and export preview data; never solve motion."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import mujoco
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = ROOT / 'externals/UMR-astro-surface-experiment'
sys.path.insert(0, str(EXTERNAL / 'scripts'))
sys.path.insert(0, str(ROOT / 'experiments/astro-surface-geometry'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as robot_bind
import retarget_body_segment_surface as segments
from humanoid_retarget_config import load_config
from primitive_surface import PrimitiveUnion, bind_points_to_mesh_exact
from geometry_checks import independent_interior, world_from_root

OUT = ROOT / 'outputs/astro-correspondence-comparison'


def distribution(values):
    a = np.asarray(values)
    return dict(mean=float(a.mean()), p95=float(np.percentile(a, 95)), max=float(a.max()))


def audit(arm):
    config = load_config(ROOT / f'experiments/astro-correspondence-comparison/{arm}.json')
    dataset = np.load(OUT / arm / 'dataset.npz', allow_pickle=True)
    slots = np.load(OUT / arm / 'train/correspondence_slots_final.npz', allow_pickle=True)
    assert slots['names'].tolist() == dataset['names'].tolist()
    assert str(dataset['custom_robot_visual_geom_policy']) == config['robot']['visual_geom_policy']
    assert str(dataset['custom_robot_xml']) == config['robot']['xml']
    assert not Path(config['retarget']['out']).exists()
    assert str(slots['training_mode']) == 'robot2smpl_only'
    assert np.array_equal(slots['slot_index'], np.arange(4096))
    assert np.array_equal(slots['target_points'], dataset['points'])
    ordered_human = dataset['points'][0][slots['template_sort_index']]
    np.testing.assert_allclose(slots['reconstructed_slots'][0], ordered_human, rtol=0, atol=6e-8)
    learned = slots['reconstructed_slots']
    assert learned.shape == (2, 4096, 3) and np.isfinite(learned).all()
    human_binding = bind_points_to_mesh_exact(learned[0], dataset['mesh_vertices_0'], dataset['mesh_faces_0'])
    try:
        part_ids = segments.smplx_slot_part_ids_from_binding(dataset['mesh_faces_0'], human_binding['face_ids'], template_vertices=dataset['mesh_vertices_0'], bary=human_binding['bary'], slot_points=human_binding['closest_points'])
        labels = {int(v): k for k,v in segments.SMPLX_PART_IDS.items()}
        source_labels = [labels[int(i)] for i in part_ids]
    except FileNotFoundError:
        source_labels = ['unavailable'] * 4096
    model = mujoco.MjModel.from_xml_path(config['robot']['xml'])
    data = mujoco.MjData(model)
    build.apply_joint_qpos(model, data, config['robot']['tpose_qpos'], required=True)
    mujoco.mj_forward(model, data)
    geom_ids = robot_bind.visual_geom_ids(model, config['robot']['visual_geom_policy'])
    vertices, faces, owners, center, rotation, _ = robot_bind.collect_root_mesh(model, data, geom_ids, config['robot']['point_cloud_center'])
    points_root = robot_bind.smpl_frame_to_robot_root(learned[1])
    # Inspect actual production binding first. Rejected primitive projections remain
    # available only as diagnostic previews with an explicit invalid mask.
    binding_failure = None
    try:
        production = robot_bind.bind_robot_slots(model, SimpleNamespace(config_data=config), learned[1])
    except ValueError as exc:
        binding_failure = str(exc)
        production = None
    from smpl_surface_retarget_common import bind_points_to_mesh
    binding = bind_points_to_mesh(points_root, vertices, faces, method='exact' if arm == 'primitive' else 'nearest_vertex')
    chosen_geoms = owners[binding['face_ids']]
    body_ids = model.geom_bodyid[chosen_geoms]
    body_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(i)) for i in body_ids]
    projected = binding['closest_points']
    invalid = np.zeros(4096, bool)
    interior = None
    if arm == 'primitive':
        union = PrimitiveUnion.from_model(model, data, geom_ids, center, rotation)
        invalid = ~union.exterior_mask(projected, chosen_geoms)
        interior = independent_interior(world_from_root(projected,center,rotation),chosen_geoms,model,data,geom_ids)
        assert interior['count'] == int(invalid.sum())
    if production is not None:
        np.testing.assert_allclose(production['root_points'], projected, rtol=0,atol=1e-7)
    # SMPL left/up/forward coordinates; row-vector inverse of root frame map.
    projected_smpl = projected @ robot_bind.SMPL_TO_ROBOT_ROOT_MATRIX
    unique, counts = np.unique(body_names, return_counts=True)
    mapping = {}
    for source, body in zip(source_labels, body_names):
        mapping.setdefault(source, {})[body] = mapping.setdefault(source, {}).get(body, 0) + 1
    opposite = [i for i,(a,b) in enumerate(zip(source_labels,body_names)) if (a.startswith('left') and b.startswith('right_')) or (a.startswith('right') and b.startswith('left_'))]
    # Distances from the independently sampled target cloud to learned/projected
    # slots measure reference surface coverage, not motion/contact preservation.
    coverage = cKDTree(projected_smpl).query(dataset['points'][1])[0]
    metrics = dict(names=slots['names'].tolist(), geometry_policy=config['robot']['visual_geom_policy'], finite=True,
        human_ordered_sample_error_m=distribution(np.linalg.norm(learned[0]-ordered_human,axis=1)),
        human_projection_error_m=distribution(human_binding['errors']),
        robot_projection_error_m=distribution(binding['errors']), target_to_projected_coverage_m=distribution(coverage),
        body_coverage=dict(zip(unique.tolist(), counts.tolist())), selected_geoms=int(len(geom_ids)), occupied_geoms=int(len(np.unique(chosen_geoms))),
        source_segment_to_robot_body=mapping, opposite_side_count=len(opposite), opposite_side_slot_ids=opposite,
        rejected_slot_count=int(invalid.sum()), rejected_slot_ids=np.flatnonzero(invalid).tolist(),
        production_binding_failure=binding_failure, independent_projected_interior=interior,
        normalization_scales=slots['normalization_scales'].tolist())
    np.savez_compressed(OUT / arm / 'inspected_pairings.npz',human=learned[0],robot_learned=learned[1],robot_projected=projected_smpl,
        invalid_projection=invalid,geom_ids=chosen_geoms,body_ids=body_ids,body_names=np.asarray(body_names),source_labels=np.asarray(source_labels),slot_ids=slots['slot_index'])
    preview = dict(human=learned[0].round(7).tolist(), learned=learned[1].round(7).tolist(), projected=projected_smpl.round(7).tolist(),
        input=dataset['points'][1].round(7).tolist(),invalid=np.flatnonzero(invalid).tolist(),bodies=body_names,source_labels=source_labels,metrics=metrics)
    return dataset, slots, metrics, preview


def main():
    results = {arm:audit(arm) for arm in ['visual','primitive']}
    a,b = results['visual'],results['primitive']
    for field in ['mesh_vertices_0','mesh_faces_0','sample_face_ids_0','betas_0']:
        assert np.array_equal(a[0][field],b[0][field]), field
    for field in ['template_sort_index','template_edge_index','template_points']:
        assert np.array_equal(a[1][field],b[1][field]),field
    np.testing.assert_array_equal(a[0]['points'][0],b[0]['points'][0])
    assert not np.array_equal(a[0]['points'][1],b[0]['points'][1])
    np.testing.assert_array_equal(a[1]['reconstructed_slots'][0],b[1]['reconstructed_slots'][0])
    report={'shared_human_mesh_samples_learned_slots_order_graph_bitwise_equal':True,'arms':{arm:r[2] for arm,r in results.items()}}
    (OUT / 'metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT / 'experiments/astro-correspondence-comparison/results.json').write_text(json.dumps(report,indent=2)+'\n')
    viewer=OUT / 'viewer';viewer.mkdir(exist_ok=True)
    (viewer/'pairings.json').write_text(json.dumps({arm:r[3] for arm,r in results.items()},separators=(',',':')))
    print(json.dumps({arm:{k:v for k,v in r[2].items() if k not in ['source_segment_to_robot_body','opposite_side_slot_ids','rejected_slot_ids']} for arm,r in results.items()},indent=2))


if __name__ == '__main__':
    main()
