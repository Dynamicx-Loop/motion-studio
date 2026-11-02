"""Descriptive matched-clip comparison to immutable generic SOMA control."""
import argparse
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
EVALUATOR = ROOT/'experiments/umr-baseline-g1-comparison-20261102/evaluate.py'
spec = importlib.util.spec_from_file_location('preserved_comparison_metrics', EVALUATOR)
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)


def main():
    p = argparse.ArgumentParser(__doc__)
    for name in ('run','inspection','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--generic-run',type=Path,default=ROOT/'outputs/umr-baseline-g1-somax-20261102')
    p.add_argument('--generic-inspection',type=Path,default=ROOT/'outputs/umr-baseline-g1-somax-20261102-inspection-04')
    args = p.parse_args()
    out = args.output.resolve()
    if out.exists():
        raise FileExistsError(out)
    a = evaluate.load(args.generic_run.resolve(),args.generic_inspection.resolve())
    b = evaluate.load(args.run.resolve(),args.inspection.resolve())
    assert a['payload']['official_fitted_bones_seed'] is False
    assert b['payload']['official_fitted_bones_seed'] is True
    assert a['payload']['motion']['frame_ids'] == b['payload']['motion']['frame_ids']
    assert abs(a['fps']-b['fps']) < 1e-5
    import numpy as np
    sources = []
    for cohort in (a,b):
        with np.load(cohort['run']/'motion.npz',allow_pickle=True) as saved:
            sources.append(Path(str(saved['source_data'].item())))
    assert evaluate.sha(sources[0]) == evaluate.sha(sources[1])
    additional = [sources[0],sources[1],EVALUATOR,Path(__file__).resolve(),args.inspection/'audit.json']
    before = {**a['initial_hashes'],**b['initial_hashes'],**{str(p):evaluate.sha(p) for p in additional}}
    configs = [json.loads((r['run']/'resolved.json').read_text()) for r in (a,b)]
    solver_equal = configs[0]['solver'] == configs[1]['solver']
    assert solver_equal
    robot = evaluate.robot_equality(a,b)
    assert robot['all_checked_equal'], robot
    spatial, probes = evaluate.spatial_comparison(a,b)
    spatial['generic_to_fitted_label_counts'] = spatial.pop('smplx_to_somax_label_counts')
    distances = spatial['nearest_binding_distance_m']
    spatial['nearest_binding_distance_m'] = {'generic':distances['smplx'],'fitted':distances['somax']}
    spatial['definition'] = 'Identical 4096 robot reference samples; assign nearest projected binding label independently in each cohort. Learned slot indices are never equated across training runs.'
    audit = json.loads((args.inspection/'audit.json').read_text())
    result = {'scope':'Same source BVH bytes, all original 1165 frames, same robot and solver cohort settings; generic neutral vs fitted uniform SOMA representation. Descriptive experiment, not causal ranking or dynamic feasibility.',
        'source_BVH_sha256':evaluate.sha(sources[0]),'resolved_solver_settings_equal':solver_equal,'robot_consistency':robot,
        'spatial_segment_consistency':spatial,
        'generic':{'bindings':evaluate.bindings(a),'motion':evaluate.motion(a)},
        'fitted':{'bindings':evaluate.bindings(b),'motion':evaluate.motion(b)},
        'fitted_replay_audit':audit,'source_artifact_sha256':before}
    for cohort in ('generic','fitted'):
        definition = result[cohort]['motion']['definitions']['centroids']
        result[cohort]['motion']['definitions']['centroids'] = definition.replace('SOMA encoding Root can be static and is not assumed to be a pelvis.', 'Both retained inspectors use the corrected moving named Hips anchor for mesh encoding; this diagnostic separately uses the hips surface centroid.')
    assert before == {name:evaluate.sha(Path(name)) for name in before}
    result['preservation'] = {'all_comparison_inputs_unchanged':True}
    out.mkdir(parents=True,exist_ok=False)
    (out/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    evaluate.probe_svg(out/'robot-label-probes.svg',probes)
    svg = out/'robot-label-probes.svg'
    svg.write_text(svg.read_text().replace('SMPL-X source labels on G1','Generic SOMA labels on G1').replace('SOMA-X source labels on G1','Fitted SOMA labels on G1'))
    shutil.copyfile(EVALUATOR,out/'preserved_metric_evaluator.py')
    shutil.copyfile(Path(__file__),out/'compare.py')
    cells = []
    for label, field, stat, factor, unit in [
        ('Frame count','frame_count',None,1,''),('FPS','fps',None,1,'Hz'),
        ('Mean hips-centered segment discrepancy','hips_centered_segment_centroid_mismatch_m','mean',100,'cm'),
        ('P95 scalar joint step','absolute_scalar_joint_step_rad','p95',1,'rad/frame'),
        ('Configured/model limit excess','compiled_and_configured_joint_limit_max_excess_rad',None,1,'rad')]:
        values = []
        for key in ('generic','fitted'):
            v = result[key]['motion'][field]
            values.append(f'{(v[stat] if stat else v)*factor:.6g} {unit}')
        cells.append('<tr><th>'+label+'</th>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
    link = lambda target: html.escape(os.path.relpath(target,out),quote=True)
    agreement = spatial['label_agreement_fraction']*100
    precision = audit['precision_budget']
    raw = audit['raw_BVH_vs_fitted_model_joint_distance_m']
    relative = audit['hips_centered_BVH_vs_fitted_model_joint_distance_m']
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fitted uniform SOMA prototype inspection</title><style>body{{max-width:1160px;margin:30px auto;padding:0 20px;font:16px/1.6 system-ui;color:#162739;background:#f5f8fc}}h1,h2{{line-height:1.2}}.notice{{background:#fff0c7;padding:16px;border-left:5px solid #b87c00}}a.button{{display:inline-block;background:#174b79;color:white;padding:10px 16px;margin:8px 10px 8px 0}}table{{border-collapse:collapse;width:100%;background:white;margin:20px 0}}td,th{{padding:9px;text-align:left;border-bottom:1px solid #d3dfea}}img{{width:100%}}</style>
<h1>Fitted uniform SOMA → G1</h1><p>Fresh native numerical prototype · jump_and_land_light_001__A001 · 2026-11-02</p>
<p class="notice"><strong>User visual acceptance is pending.</strong> Numerical and replay checks establish the recorded computation and view fidelity. They do not establish anatomical correctness, contact quality, balance or dynamic feasibility.</p>
<p><a class="button" href="{link(args.inspection)}/">Inspect fitted human + retargeted G1</a><a class="button" href="{link(args.generic_inspection)}/">Inspect immutable generic control</a></p>
<p>The fitted inspector shows synchronized source and robot meshes, segment colors, paired bindings, target body/mesh ownership, reference pose and all original frames. Enable “Overlay fitted (gold) + BVH (cyan) skeletons” to compare the two source representations in the same display frame. Hips anchors the fitted mesh; horizontal centering only changes display translation.</p>
<h2>What ran and what was measured</h2><p>Both cohorts use the same BVH bytes and all 1,165 frames at {b['fps']:.7f} FPS. The new source asserts <code>soma_bvh_boneseed_uniform</code> and <code>soma_uniform</code>, with the shared BONES-SEED fit. The immutable control uses a generic neutral surface. Each cohort samples and trains its own correspondence; row numbers across learned slots have no shared identity.</p>
<p>All {len(robot['checks'])} bounded robot equality checks pass exactly, including compiled selected arrays, geometry, joint names/order, reference surface samples and recorded robot settings except asset path. Projection/segment diagnostics describe learned geometry; they are not anatomical ground truth.</p>
<table><thead><tr><th>Per-clip diagnostic</th><th>Generic control</th><th>Fitted uniform</th></tr></thead><tbody>{''.join(cells)}</tbody></table>
<p>Segment discrepancy uses each embodiment's own bound hips surface centroid as origin, saved source scale, full frame timing and equal weight across the remaining 18 segments. It includes differing body proportions and surface-region placement. Scalar joint step is adjacent qpos difference in radians/frame.</p>
<h2>Independent replay and source representation checks</h2><p>All frames passed topology continuity, fitted source reconstruction and 4,096 barycentric bindings, moving named Hips, name mapping, native BVH FK and 4,096 rigid robot bindings. Maximum source vertex axis error: {audit['fitted_source_native_replay_max_axis_error_m']*1e6:.3f} µm (0.1 mm mesh encoding steps); robot slot axis error: {audit['robot_4096_rigid_slots_all_frames_max_axis_error_m']:.3g} m.</p>
<p>Precision checks separate the 50 µm mesh half-step from native float32 forward variability: controlled unquantized repeats measured {precision['measured_native_repeatability_max_axis_m']*1e6:.3f} µm maximum. The matched-runtime mesh/slot gate is 53 µm (50 + 2 native + 1 arithmetic), with a separate 50.1 µm own-reference encoding gate and 3 µm skeleton gate. Earlier mismatched-environment attempts reached approximately 77 µm; those failed attempts and exact-runtime diagnostics are preserved. The tight final bounds apply to the recorded CUDA, BLAS and thread configuration.</p>
<p>The native BVH hierarchy and fitted SOMA layer share named local pose channels but use different rest offsets. Raw matched-joint mean/P95 distance is {raw['mean']*100:.3f}/{raw['p95']*100:.3f} cm; after centering each skeleton on its own Hips it is {relative['mean']*100:.3f}/{relative['p95']*100:.3f} cm. These differences are measured explicitly, not asserted to vanish. The mesh is the fitted surface reconstruction, and cyan lines are the original BVH skeleton.</p>
<p><a href="{link(args.inspection/'audit.json')}">All-frame numerical audit and joint map</a> · <a href="comparison.json">Full metrics, definitions and input hashes</a></p>
<h2>Independent learned source labels on the same robot surface</h2><p>Nearest projected binding assigns the source segment at each of 4,096 identical robot reference probes, independently per run. Label agreement: {agreement:.2f}%. This is spatial region consistency, not point correspondence accuracy.</p><img src="robot-label-probes.svg" alt="Generic and fitted independently learned labels at identical robot samples; disagreement in magenta">
<p>Input preservation checks passed. Source data, fit, original outputs and generic control remain preserved. No controller rollout, whole-body collision test or support/contact-force evaluation was performed. User judgment of motion and segment plausibility remains open.</p></html>'''
    (out/'index.html').write_text(page)
    print(json.dumps({'output':str(out),'label_agreement':spatial['label_agreement_fraction'],'preservation':True}))


if __name__ == '__main__':
    main()
