#!/usr/bin/env python3
"""Read-only human model/rig/segmentation audit. Does not load motion poses or retarget.

All numerical derivative arrays are local ignored outputs. The JSON records checks,
joint order and definitions, not licensed model coefficients. Joint-region mappings
are explicit anatomical diagnostics, not claims of equivalent rigs.
"""
from collections import Counter
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import pickle

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/soma-correspondence-audit'
EXT = ROOT / 'externals/UMR-astro-surface-experiment'
ASSETS = Path('/data/motions/human_models/soma-x/f81a01796f65/assets')
OVERLAY = Path('/data/motions/human_models/soma-x/f81a01796f65/overlays/umr')
SMPL = Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl')
MOTION = ROOT / 'externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
os.environ['UMR_SOMA_ASSETS_PATH'] = str(OVERLAY)
os.environ['UMR_SOMA_SMPLX_ASSETS_PATH'] = str(ASSETS / 'SMPLX')
sys.path.insert(0, str(EXT / 'scripts'))
import soma_source as soma
import retarget_body_segment_surface as seg
import build_correspondence_ae_dataset as build
from primitive_surface import bind_points_to_mesh_exact


def sha(path):
    return hashlib.sha256(canonical_motion_path(path).read_bytes()).hexdigest()


def stats(a):
    a = np.asarray(a)
    return dict(min=float(a.min()), mean=float(a.mean()),
                p50=float(np.median(a)), p95=float(np.percentile(a, 95)), max=float(a.max()))


def counts(a):
    return {str(k): int(v) for k, v in sorted(Counter(a).items())}


def matrix(a, b):
    return {str(k): counts(b[a == k]) for k in sorted(set(a))}


def lbs_report(w, names, parents):
    w = np.asarray(w, dtype=np.float64)
    order = np.argsort(w, axis=1)
    top = np.take_along_axis(w, order[:, -2:], 1)
    gap = top[:, 1] - top[:, 0]
    assert np.isfinite(w).all() and w.min() >= 0
    assert np.max(np.abs(w.sum(1) - 1)) < 1e-5
    assert len(names) == w.shape[1] == len(parents)
    assert parents[0] in (-1, 0)
    assert all(0 <= p < j for j, p in enumerate(parents) if j)
    return dict(shape=list(w.shape), finite=True, minimum=float(w.min()),
                negative_count=int((w < 0).sum()), row_sum=stats(w.sum(1)),
                maximum_row_sum_error=float(np.abs(w.sum(1) - 1).max()),
                positive_influences_per_vertex=counts((w > 0).sum(1)),
                influences_above_1e_4_per_vertex=counts((w > 1e-4).sum(1)),
                top_weight=stats(top[:, 1]), top1_minus_top2=stats(gap),
                top_gap_below_005=int((gap < .05).sum()), top_gap_below_01=int((gap < .1).sum()),
                max_weight_below_05=int((top[:, 1] < .5).sum()),
                hierarchy_parent_precedes_child_except_root_sentinel=True,
                root_parent_sentinel=int(parents[0]),
                joints=[dict(index=i, name=n, parent=int(parents[i]),
                             parent_name=names[parents[i]] if parents[i] >= 0 else None,
                             positive_vertex_count=int((w[:, i] > 0).sum()),
                             argmax_vertex_count=int((order[:, -1] == i).sum()),
                             weight_sum=float(w[:, i].sum())) for i, n in enumerate(names)])


def soma_regions(names):
    """18 common categories: native 17 categories but separate neck from head."""
    labels = []
    for n in names:
        if n in ('Root', 'Hips'): label = 'hips'
        elif n in ('Spine1', 'Spine2', 'Chest'): label = 'torso'
        elif n.startswith('Neck'): label = 'neck'
        elif n in ('Head', 'HeadEnd', 'Jaw', 'LeftEye', 'RightEye'): label = 'head/face'
        else:
            side = 'left' if n.startswith('Left') else 'right'
            suffix = n[len(side):]
            label = side + ('Shoulder' if suffix == 'Shoulder' else
                            'Arm' if suffix == 'Arm' else
                            'ForeArm' if suffix == 'ForeArm' else
                            'Hand' if suffix.startswith('Hand') else
                            'UpLeg' if suffix == 'Leg' else
                            'Leg' if suffix == 'Shin' else 'Foot')
        labels.append(label)
    return np.array(labels)


def grouped_weights(w, labels, common):
    return np.stack([w[:, labels == name].sum(1) for name in common], 1)


def labels_report(labels, grouped, common):
    winner = np.asarray(common)[grouped.argmax(1)]
    id_by_name = {name: i for i, name in enumerate(common)}
    label_w = grouped[np.arange(len(labels)), [id_by_name[n] for n in labels]]
    return dict(counts=counts(labels), label_to_grouped_lbs_argmax=matrix(labels, winner),
                disagreement_count=int((labels != winner).sum()),
                confident_argmax_disagreements=int(((labels != winner) & (grouped.max(1) >= .8)).sum()),
                label_lbs_mass=stats(label_w),
                label_lbs_mass_below_half=int((label_w < .5).sum()),
                per_label={n: dict(vertices=int((labels == n).sum()),
                                   argmax_disagreements=int(((labels == n) & (labels != winner)).sum()),
                                   label_mass=stats(label_w[labels == n])) for n in sorted(set(labels))})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with SMPL.open('rb') as handle:
        raw = pickle.load(handle, encoding='latin1')
    smpl_names_by_id = {i: n for n, i in raw['joint2num'].item().items()}
    smpl_names = [smpl_names_by_id[i] for i in range(55)]
    smpl_parents = raw['kintree_table'][0].astype(np.int64).copy()
    smpl_parents[0] = -1
    smpl_w = np.asarray(raw['weights'])
    with np.load(MOTION, allow_pickle=True) as motion:
        betas = build.coerce_betas(motion['betas'], 10)
    smpl_v, smpl_j, smpl_f = build.load_smpl_template(SMPL.parent, 'smplx', 'neutral', betas)
    np.testing.assert_array_equal(smpl_f, raw['f'])
    # Confirm the concrete loader, not merely this manual file read, uses same LBS.
    model = build.build_smplx_model(SMPL.parent, 'neutral', 1)
    np.testing.assert_array_equal(model.lbs_weights.detach().cpu().numpy(), smpl_w)
    with (EXT / 'assets/smplx_parts_segm.pkl').open('rb') as handle:
        raw55 = pickle.load(handle, encoding='latin1')['segm'].astype(np.int32)
    raw55_vertices = seg.vertex_part_ids_from_face_part_ids(smpl_f, raw55 + 1, len(smpl_v)) - 1
    partnames = seg.BODY_SEGMENT_PART_NAMES
    smpl_joint_regions = np.array([partnames[int(i)] for i in seg.SMPLX_55_TO_17_SEGM_ID_TO_CLASS_ID])
    smpl_joint_regions[12] = 'neck'
    smpl_joint_regions[np.isin(np.arange(55), [15, 22, 23, 24])] = 'head/face'
    smpl_labels = smpl_joint_regions[raw55_vertices]
    template = soma.load_soma_bind_tpose_template(OVERLAY, 'mid')
    soma_w = template['skinning_weights']
    with np.load(OVERLAY / 'SOMA_neutral.npz', allow_pickle=False) as overlay:
        overlay_arrays = {key: overlay[key] for key in overlay.files}
    with np.load(ASSETS / 'SOMA_neutral.npz', allow_pickle=False) as official:
        preserved = {key: bool(np.array_equal(official[key], overlay_arrays[key])) for key in official.files}
    assert all(preserved.values()), preserved
    # Reconstruct from the official slim NPZ + USD using installed official code.
    # Unlike the setup tool, this script never writes assets or environment files.
    layer = soma._soma_x_layer(str(ASSETS), lod='mid', device='cpu')
    reconstructed = {key: np.asarray(value) for key, value in layer._public_mid_rig_data.items()
                     if not np.asarray(value).dtype.hasobject}
    regenerated = {key: bool(np.array_equal(value, overlay_arrays[key]))
                   for key, value in reconstructed.items()}
    assert set(reconstructed) == set(overlay_arrays)
    assert all(regenerated.values()), regenerated
    snames = template['joint_names']
    sregions = soma_regions(snames)
    common = sorted(set(smpl_joint_regions) | set(sregions))
    smpl_grouped = grouped_weights(smpl_w, smpl_joint_regions, common)
    soma_grouped = grouped_weights(soma_w, sregions, common)
    base_v, base_f = seg._load_obj_vertices_faces(str(ASSETS / 'SMPLX/base_body.obj'))
    wrap_v, wrap_f = seg._load_obj_vertices_faces(str(ASSETS / 'SMPLX/SOMA_wrap.obj'))
    assert np.array_equal(base_f, smpl_f), 'Face count alone is insufficient for raw55 transfer'
    # Trimesh and official loader triangulate each quad along different diagonals.
    # Check original polygon/vertex identities instead of demanding triangle order.
    wrap_polygons = [[int(x.split('/')[0]) - 1 for x in line.split()[1:]]
                     for line in (ASSETS / 'SMPLX/SOMA_wrap.obj').read_text().splitlines()
                     if line.startswith('f ')]
    np.testing.assert_array_equal(np.concatenate(wrap_polygons), overlay_arrays['face_vert_indices'])
    np.testing.assert_array_equal([len(p) for p in wrap_polygons], overlay_arrays['face_vert_counts'])
    binding = seg._bind_points_to_mesh_faces(wrap_v, base_v, base_f, nearest_vertex_k=32)
    exact_binding = bind_points_to_mesh_exact(wrap_v, base_v, base_f)
    soma_raw55 = raw55[binding['face_ids']]
    soma_labels = smpl_joint_regions[soma_raw55]
    soma_native17, _, _, _, transfer_errors = seg.smplx_soma_mid_vertex_part_ids()
    np.testing.assert_array_equal(soma_native17, seg.SMPLX_55_TO_17_SEGM_ID_TO_CLASS_ID[soma_raw55])
    native_face17 = seg.majority_face_part_ids(template['faces'], soma_native17)
    exact55 = raw55[exact_binding['face_ids']]
    exact17 = seg.SMPLX_55_TO_17_SEGM_ID_TO_CLASS_ID[exact55]
    # Discontinuity is useful evidence: hard face labels collapse mixed vertices.
    tri_labels = soma_native17[template['faces']]
    mixed = (tri_labels != tri_labels[:, :1]).any(1)
    smpl_fw = smpl_w[smpl_f].mean(1)
    native55_winner = smpl_fw.argmax(1)
    inputs = [SMPL, MOTION, OVERLAY / 'SOMA_neutral.npz', ASSETS / 'SOMA_neutral.npz',
              ASSETS / 'SOMA_template_rig.usda', ASSETS / 'SOMA_procedural_transforms.json',
              ASSETS / 'MHR/mhr_model_lod1.pt', ASSETS / 'MHR/base_body_lod1.obj',
              ASSETS / 'MHR/SOMA_wrap_lod1.obj', ASSETS / 'SMPLX/base_body.obj',
              ASSETS / 'SMPLX/SOMA_wrap.obj', EXT / 'assets/smplx_parts_segm.pkl']
    file_records = {str(p): dict(sha256=sha(p), bytes=p.stat().st_size,
                                resolved=str(p.resolve())) for p in inputs}
    manifest = json.loads(Path('/data/motions/human_models/soma-x/f81a01796f65/asset-manifest.json').read_text())
    manifest_checks = {}
    for entry in manifest['files']:
        path = ASSETS / entry['path']
        if str(path) in file_records:
            manifest_checks[entry['path']] = file_records[str(path)]['sha256'] == entry['sha256']
    assert all(manifest_checks.values())
    report = dict(
        purpose='Static source model, LBS, hierarchy and segmentation audit; no motion poses evaluated.',
        context7='SOMA-X resolve returned only unrelated TileDB-SOMA; official installed source and pinned model assets used.',
        versions={p: importlib.metadata.version(p) for p in ['py-soma-x', 'smplx', 'torch', 'numpy', 'scipy']},
        files=file_records,
        official_manifest_verification=dict(revision=manifest['revision'], checks=manifest_checks),
        definitions={
            'model_parameters': 'SMPL-X shape/pose bases, joint regressor, hand PCA; SOMA shape bases and identity backend. Not correspondence network weights.',
            'lbs': 'Vertex-by-joint nonnegative blend weights that deform each body mesh; inspected independently of labels.',
            'segmentation': 'UMR discrete SMPL-X face labels and SOMA wrapper label transfer; categorical, not LBS.',
            'common_labels': '18 categories: UMR 17 with neck separate from head/face; arm extra 19-way split deliberately excluded from LBS comparison.',
            'common_lbs': 'Sum all joint LBS influences within each explicitly listed anatomical group, then compare group argmax with discrete source label.',
            'disagreement': 'Not automatically an error: labels are hard anatomical partitions; LBS blends across boundaries and may assign mechanical influence outside them.',
            'smpl_vertex_label': 'Majority incident raw55 face labels; lowest index wins a tie.',
            'soma_vertex_label': 'Raw55 of nearest SMPL-X base-body face to corresponding SOMA_wrap vertex; upstream uses its 17-class collapse.',
            'joint_label_semantics': 'SMPL-X Shoulder joint deforms upper arm; Collar deforms shoulder. SOMA Shoulder is clavicle; Arm upper arm. SOMA Leg thigh; Shin lower leg.'},
        common_labels=common,
        overlay=dict(original_slim_keys_preserved=preserved,
                     official_loader_reconstruction_equal=regenerated,
                     all_equal=True, lod='mid', joints=78, vertices=18056,
                     identity_backend_in_constructor='mhr', identity_coefficients=int(layer.identity_model.num_identity_coeffs),
                     scale_parameters=int(layer.num_scale_params),
                     native_static_template='Neutral bind_shape posed by public T-pose transforms; not the MHR zero-identity forward mesh'),
        smplx=dict(lbs=lbs_report(smpl_w, smpl_names, smpl_parents),
                   joint_common_regions=smpl_joint_regions.tolist(),
                   model_arrays={k: dict(shape=list(raw[k].shape), finite=bool(np.isfinite(raw[k]).all())) for k in ['v_template','shapedirs','posedirs','J_regressor','hands_componentsl','hands_componentsr','hands_meanl','hands_meanr']},
                   actor_betas=betas.tolist(), actor_betas_sha256=hashlib.sha256(betas.tobytes()).hexdigest(),
                   labels=labels_report(smpl_labels, smpl_grouped, common),
                   raw55_face_vs_mean_vertex_lbs_argmax_disagreements=int((raw55 != native55_winner).sum()),
                   raw55_face_vs_mean_vertex_lbs_argmax=matrix(raw55, native55_winner),
                   template_bounds_m=[smpl_v.min(0).tolist(),smpl_v.max(0).tolist()]),
        soma=dict(lbs=lbs_report(soma_w, snames, overlay_arrays['joint_parent_ids']),
                  joint_common_regions=sregions.tolist(),
                  labels=labels_report(soma_labels, soma_grouped, common),
                  wrapper_binding_error_obj_units=stats(transfer_errors),
                  wrapper_complete_nearest_triangle_check=dict(
                      projection_error_excess=stats(binding['errors'] - exact_binding['errors']),
                      excess_over_1micrometer=int(((binding['errors'] - exact_binding['errors']) > 1e-6).sum()),
                      raw55_changed=int((exact55 != soma_raw55).sum()),
                      native17_changed=int((exact17 != soma_native17).sum()),
                      note='Changes can include equal-distance shared-edge face ties; no upstream labels are replaced.'),
                  base_obj_bounds=[base_v.min(0).tolist(),base_v.max(0).tolist()],
                  wrapper_obj_bounds=[wrap_v.min(0).tolist(),wrap_v.max(0).tolist()],
                  wrapper_polygons_equal_template=True,
                  wrapper_triangulated_faces_equal_template=bool(np.array_equal(wrap_f, template['faces'])),
                  wrapper_triangulation_note='Original polygon vertex order matches exactly; Trimesh quad diagonals differ from official triangles. UMR transfers vertex labels, so triangle identity is not required.',
                  smpl_base_faces_equal_loaded_model=True,
                  native17_mixed_vertex_faces=int(mixed.sum()), native17_face_count=len(native_face17),
                  native17_majority_face_labels=counts(native_face17),
                  model_arrays={k: dict(shape=list(overlay_arrays[k].shape), finite=bool(np.isfinite(overlay_arrays[k]).all())) for k in ['mean','shapedirs','eigenvalues','bind_shape','bind_pose_world','t_pose_world']},
                  template_bounds_m=[template['points'].min(0).tolist(), template['points'].max(0).tolist()]),
    )
    np.savez_compressed(OUT / 'human-weight-diagnostics.npz',
                        common_names=np.array(common), smplx_weights=smpl_w, soma_weights=soma_w,
                        smplx_grouped_weights=smpl_grouped, soma_grouped_weights=soma_grouped,
                        smplx_joint_common_regions=smpl_joint_regions, soma_joint_common_regions=sregions,
                        smplx_joint_names=np.array(smpl_names), soma_joint_names=np.array(snames),
                        smplx_raw55_face_labels=raw55, smplx_raw55_vertex_labels=raw55_vertices,
                        soma_raw55_vertex_labels=soma_raw55, soma_native17_vertex_labels=soma_native17,
                        soma_native17_face_labels=native_face17, soma_wrap_bound_faces=binding['face_ids'],
                        soma_wrap_bound_bary=binding['bary'], soma_wrap_binding_errors=binding['errors'],
                        soma_wrap_exact_bound_faces=exact_binding['face_ids'],
                        soma_wrap_exact_raw55=exact55,
                        smplx_vertices=smpl_v, smplx_faces=smpl_f, smplx_joints=smpl_j,
                        soma_vertices=template['points'], soma_faces=template['faces'],
                        soma_joints=template['t_pose_world'][:, :3, 3])
    report['diagnostics_npz_sha256'] = sha(OUT / 'human-weight-diagnostics.npz')
    (HERE / 'human-weights.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k]['lbs'] | {'joints': len(report[k]['lbs']['joints'])}
                      for k in ['smplx', 'soma']}, indent=2))


if __name__ == '__main__':
    main()
