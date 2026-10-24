"""Evaluate fresh static slots with official binding and existing audit regions.

Evaluation only: this does not modify learned slots, calibration, or UMR code.
Native19 labels and geometry zones are diagnostics, not anatomical ground truth.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import mujoco
import numpy as np
from scipy.spatial import cKDTree

from static_pair import UMR, WORKSPACE, check_official_source, sha, write
import build_correspondence_ae_dataset as build
import humanoid_retarget_pipeline as pipeline
import retarget_smpl_to_humanoid_surface_vector as rb
import retarget_body_segment_surface as seg
import smpl_surface_retarget_common as common


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stats(values):
    return {'mean': float(np.mean(values)), 'p95': float(np.percentile(values, 95)),
            'max': float(np.max(values))}


def evaluate(run, workspace):
    check_official_source()
    provenance = json.loads((run / 'provenance.json').read_text())
    for path, expected in provenance['inputs_sha256'].items():
        if sha(path) != expected:
            raise ValueError('Frozen input changed: ' + path)
    region_path = workspace / 'experiments/segment-binding-audit/regions.py'
    region = load_module('existing_anatomical_regions', region_path)
    report_folder = workspace / 'experiments/umr-binding-report'
    sys.path.insert(0, str(report_folder))
    report = load_module('existing_report_validators', report_folder / 'build_report.py')
    destination = run / 'evaluation'
    destination.mkdir(exist_ok=False)
    results, datasets, learned_human = {}, {}, {}
    for arm in ['g1', 'astro']:
        receipt = json.loads((run / 'logs' / (arm + '-completed.json')).read_text())
        if receipt['returncode'] != 0 or receipt.get('timed_out'):
            raise ValueError('Training did not complete: ' + arm)
        config = pipeline.load_pipeline_config(run / 'configs' / (arm + '.json'), UMR / 'humanoid_retarget_defaults.json')
        dataset_path = Path(config['correspondence']['dataset']['out'])
        slot_path = Path(config['correspondence']['train']['out_dir']) / 'correspondence_slots_final.npz'
        assert pipeline.correspondence_dataset_compatible(dataset_path, config)
        assert pipeline.correspondence_slots_compatible(slot_path, config)
        ds = np.load(dataset_path, allow_pickle=True)
        slots = np.load(slot_path, allow_pickle=True)
        assert str(slots['training_mode']) == 'all_samples'
        assert slots['reconstructed_slots'].shape == (2, 4096, 3)
        assert np.isfinite(slots['reconstructed_slots']).all()
        human, robot = slots['reconstructed_slots']
        datasets[arm] = ds
        learned_human[arm] = human
        source_binding = common.bind_points_to_mesh(human, ds['mesh_vertices_0'], ds['mesh_faces_0'], nearest_vertex_k=24)
        labels = seg.smplx_slot_part_ids_from_binding(
            ds['mesh_faces_0'], source_binding['face_ids'], template_vertices=ds['mesh_vertices_0'],
            bary=source_binding['bary'], slot_points=source_binding['closest_points'])
        names = np.array([seg.BODY_SEGMENT_PART_NAMES[int(i)] for i in labels])
        model = mujoco.MjModel.from_xml_path(config['robot']['xml'])
        data = mujoco.MjData(model)
        build.apply_joint_qpos(model, data, config['robot']['tpose_qpos'], required=True)
        mujoco.mj_forward(model, data)
        geometry = rb.collect_root_mesh(model, data, rb.visual_geom_ids(model, 'auto'), config['robot']['point_cloud_center'])
        vertices, faces, owners, center, rotation, _ = geometry
        np.testing.assert_array_equal(faces, ds['mesh_faces_1'])
        np.testing.assert_allclose(vertices @ rb.SMPL_TO_ROBOT_ROOT_MATRIX, ds['mesh_vertices_1'], atol=2e-7, rtol=0)
        production = rb.bind_robot_slots(model, SimpleNamespace(config_data=config), robot,
                                        nearest_vertex_k=24, project_to_surface=True, source_model_type='smplx')
        points = production['root_points']
        face_bodies = np.array([model.body(int(model.geom_bodyid[g])).name for g in owners])
        face_meshes = np.array([model.mesh(int(model.geom_dataid[g])).name for g in owners])
        bodies = np.array([model.body(int(model.geom_bodyid[g])).name for g in production['geom_ids']])
        meshes = np.array([model.mesh(int(model.geom_dataid[g])).name for g in production['geom_ids']])
        anchors = region.joint_anchors(model, data, center, rotation)
        zones = region.geometry_regions(points, bodies, meshes, anchors)
        sample_faces = ds['sample_face_ids_1']
        samples = rb.smpl_frame_to_robot_root(ds['points'][1])
        sample_zones = region.geometry_regions(samples, face_bodies[sample_faces], face_meshes[sample_faces], anchors)
        rows = []
        for name in sorted(set(names)):
            mask = names == name
            allowed = list(region.expected_regions(name))
            correct = int((mask & np.isin(zones, allowed)).sum())
            expected_samples = np.isin(sample_zones, allowed)
            distances = cKDTree(points[mask]).query(samples[expected_samples])[0]
            rows.append({'source': name, 'slots': int(mask.sum()), 'compatible_zone_slots': correct,
                         'zone_precision': correct / int(mask.sum()),
                         'expected_target_sample_count': int(expected_samples.sum()),
                         'expected_sample_coverage_within_20mm': float((distances <= .02).mean()) if len(distances) else None})
        result = {'per_segment': rows,
                  'compatible_slots': sum(row['compatible_zone_slots'] for row in rows),
                  'total_slots': len(names),
                  'source_projection_distance_m': stats(source_binding['errors']),
                  'robot_projection_distance_m': stats(np.linalg.norm(rb.smpl_frame_to_robot_root(robot) - points, axis=1)),
                  'dataset_sha256': sha(dataset_path), 'slots_sha256': sha(slot_path),
                  'training_wall_seconds': receipt['wall_seconds'],
                  'native19_source_counts': {name: int((names == name).sum()) for name in sorted(set(names))}}
        report.validate_result(result)
        results[arm] = result
        np.savez_compressed(destination / (arm + '-binding.npz'), **production,
                            source_face_ids=source_binding['face_ids'], source_bary=source_binding['bary'],
                            source_native19=names, robot_geometry_zone=zones, body_names=bodies, mesh_names=meshes)
    for key in ['mesh_vertices_0', 'mesh_faces_0', 'sample_face_ids_0', 'betas_0']:
        np.testing.assert_array_equal(datasets['g1'][key], datasets['astro'][key])
    np.testing.assert_array_equal(datasets['g1']['points'][0], datasets['astro']['points'][0])
    write(destination / 'results.json', {
        'schema_version': 1, 'run_id': run.name, 'cohort_status': 'baseline_candidate',
        'evidence_origin': 'prospective', 'reproducibility': 'executed_once',
        'stage': 'static_correspondence_and_binding', 'arms': results,
        'checks': {'matched_source_mesh_shape_samples': True, 'both_target_meshes_match_datasets_200nm': True,
                   'native19_report_validator_passed': True, 'official_tracked_source_unchanged': True},
        'learned_human_slot_difference_m': stats(np.linalg.norm(learned_human['astro'] - learned_human['g1'], axis=1)),
        'evaluation_sources': {str(region_path): sha(region_path),
                               str(report_folder / 'build_report.py'): sha(report_folder / 'build_report.py'),
                               str(Path(__file__)): sha(__file__)},
        'definitions': {'precision': 'Compatible target-zone slots divided by native19 source-segment slots',
                        'coverage': 'Fraction of sampled expected target zone within 20 mm of same-source-segment projected slots',
                        'projection_distance': 'Learned slot to production projected visual surface, metres; not penetration'},
        'limitations': ['One actor and seed; no repeatability rerun or statistical acceptance threshold',
                        'Diagnostic target zones reused from existing audit; not unique anatomical ground truth',
                        'Raw metres and 20 mm coverage depend on robot scale; interpret per segment and morphology',
                        'Official all_samples training may change learned human slots independently per robot',
                        'Native19 only; common18/LBS confidence and global exact-triangle comparison not measured',
                        'No trajectory, floor penetration, collision or controller result measured']})
    print(json.dumps({arm: {'compatible_slots': result['compatible_slots'], 'total_slots': result['total_slots'],
                            'projection_distance_m': result['robot_projection_distance_m']}
                      for arm, result in results.items()}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, default=WORKSPACE)
    args = parser.parse_args()
    evaluate(args.run.resolve(), args.workspace.resolve())
