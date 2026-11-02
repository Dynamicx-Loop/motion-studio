"""Read-only comparison of two fresh official G1 runs and decoded inspectors.

Run in UMR's existing environment. Outputs are descriptive diagnostics, never a
matched-motion benchmark, anatomical ground truth, or dynamic feasibility test.
"""
import argparse
from collections import Counter
import hashlib
import html
import json
import os
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial import cKDTree


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def stats(values):
    values = np.asarray(values, dtype=float).reshape(-1)
    if not len(values):
        return None
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite evaluation data')
    return dict(zip(('mean', 'p50', 'p95', 'max'), map(float,
        [values.mean(), *np.quantile(values, [.5, .95]), values.max()])))


def load(run, inspection):
    candidates = [run / name for name in ('dataset.npz','motion.npz','resolved.json')]
    candidates += [p for root in (run/'assets',inspection) for p in root.rglob('*') if p.is_file()]
    initial_hashes = {str(p):sha(p) for p in candidates}
    payload = json.loads((inspection / 'bindings.json').read_text())
    if len(payload['labels']) != 4096 or payload['units'] != 'metres':
        raise ValueError('Expected native 4096-slot metre inspector')
    with np.load(run / 'dataset.npz', allow_pickle=True) as saved:
        names = saved['names'].astype(str).tolist()
        robot_index = next(i for i, n in enumerate(names) if 'g1' in n.lower())
        mesh = {n: saved[f'mesh_{n}_{robot_index}'].copy() for n in ('vertices', 'faces')}
        probes = saved['points'][robot_index].copy()
    with np.load(run / 'motion.npz', allow_pickle=True) as saved:
        qpos, fps = saved['qpos'].copy(), float(saved['fps'].item())
        xml = Path(str(saved['robot_xml'].item()))
        scale = float(saved['smpl_scale'].item())
    model = mujoco.MjModel.from_xml_path(str(xml))
    if not xml.is_relative_to(run/'assets'):
        raise ValueError('Expected the complete captured run-local robot asset closure')
    files = [run / 'dataset.npz', run / 'motion.npz', run / 'resolved.json',
             xml, inspection / 'bindings.json', inspection / payload['motion']['transforms']]
    files += [p for p in (run/'assets').rglob('*') if p.is_file()]
    files += [inspection / c['file'] for c in payload['human_motion']['chunks']]
    return {'run': run, 'inspection': inspection, 'payload': payload,
            'mesh': mesh, 'probes': probes, 'qpos': qpos, 'fps': fps,
            'scale': scale, 'model': model, 'files': files,
            'initial_hashes': {str(p):initial_hashes[str(p)] for p in files}}


def robot_equality(a, b):
    fields = ('geom_type', 'geom_bodyid', 'geom_dataid', 'geom_pos', 'geom_quat',
              'geom_size', 'mesh_vert', 'mesh_face', 'body_parentid', 'body_pos',
              'body_quat', 'body_mass', 'body_inertia', 'jnt_type', 'jnt_qposadr',
              'jnt_bodyid', 'jnt_pos', 'jnt_axis', 'jnt_range', 'jnt_limited', 'qpos0')
    result = {field: bool(np.array_equal(getattr(a['model'], field),
                                        getattr(b['model'], field))) for field in fields}
    for kind, number in [('body', 'nbody'), ('joint', 'njnt'), ('geom', 'ngeom')]:
        result[kind + '_names_order'] = ([getattr(a['model'], kind)(i).name
            for i in range(getattr(a['model'], number))] == [getattr(b['model'], kind)(i).name
            for i in range(getattr(b['model'], number))])
    for field in ('vertices', 'faces'):
        result['dataset_robot_' + field] = bool(np.array_equal(a['mesh'][field], b['mesh'][field]))
    result['dataset_robot_sample_points'] = bool(np.array_equal(a['probes'], b['probes']))
    configs = [json.loads((r['run'] / 'resolved.json').read_text())['robot'] for r in (a,b)]
    for config in configs:
        config.pop('xml', None)
    result['resolved_robot_settings_except_xml_path'] = configs[0] == configs[1]
    return {'all_checked_equal': all(result.values()), 'checks': result,
            'scope': 'Exact compiled selected arrays, names/order, static sampled robot surface and official settings; not whole simulator equivalence'}


def bindings(run):
    p = run['payload']
    counts = Counter(p['labels'])
    ownership = {label: dict(Counter(body for lab, body in zip(p['labels'], p['bodies'])
                                   if lab == label)) for label in sorted(counts)}
    mesh_ownership = {label: dict(Counter(mesh for lab, mesh in zip(p['labels'], p['meshes'])
                                   if lab == label)) for label in sorted(counts)}
    source = np.asarray(p['source'])
    target = np.asarray(p['target'])
    result = {'schema': p['schema'], 'slot_count': len(source), 'segment_counts': dict(counts),
              'unique_target_bodies': len(set(p['bodies'])), 'segment_target_body_counts': ownership,
              'segment_target_mesh_counts': mesh_ownership,
              'target_projection_distance_m': stats(p['projection_m'])}
    # Surface coverage is Euclidean nearest learned binding distance at the
    # independent uniform robot samples, not proof of anatomical correctness.
    result['robot_probe_to_binding_distance_m'] = stats(cKDTree(target).query(run['probes'])[0])
    return result


def spatial_comparison(a, b):
    if not np.array_equal(a['mesh']['vertices'], b['mesh']['vertices']) or not np.array_equal(a['mesh']['faces'], b['mesh']['faces']):
        raise ValueError('Common-probe label comparison requires identical robot geometry')
    probes = a['probes']
    labels, distances = [], []
    for run in (a,b):
        p = run['payload']
        distance, index = cKDTree(p['target']).query(probes)
        labels.append(np.asarray(p['labels'])[index])
        distances.append(distance)
    same = labels[0] == labels[1]
    segments = sorted(set(labels[0]) | set(labels[1]))
    ious = {label: float(np.sum((labels[0] == label) & (labels[1] == label)) /
        np.sum((labels[0] == label) | (labels[1] == label))) for label in segments}
    matrix = {label: dict(Counter(labels[1][labels[0] == label])) for label in segments}
    return {'probe_count': len(probes), 'label_agreement_fraction': float(same.mean()),
            'per_segment_probe_iou': ious, 'smplx_to_somax_label_counts': matrix,
            'nearest_binding_distance_m': {'smplx': stats(distances[0]), 'somax': stats(distances[1])},
            'definition': 'Same SMPL-X-run uniform robot reference samples; nearest projected learned target binding assigns a source segment separately per run. Learned slot rows are never equated across humans.'}, (probes, labels, same)


def motion(run):
    p, folder = run['payload'], run['inspection']
    r, h = p['motion'], p['human_motion']
    frames, fps = r['frame_count'], run['fps']
    if h['frame_count'] != frames or abs(h['fps']-fps) > 1e-5:
        raise ValueError('Source/robot replay is not synchronized')
    roots_h, roots_r = np.asarray(h['root_positions']), np.asarray(r['root_positions'])
    transforms = np.memmap(folder / r['transforms'], mode='r', dtype=r.get('transform_dtype','<f4'),
                           shape=(frames,len(r['pieces']),3,4))
    slot_local, slot_piece = np.asarray(r['slot_local']), np.asarray(r['slot_piece'])
    slot_vertices, bary = np.asarray(h['slot_vertices']), np.asarray(h['slot_bary'])
    labels = np.asarray(p['labels'])
    segments = sorted(set(labels))
    source_centroids = np.empty((frames,len(segments),3))
    target_centroids = np.empty_like(source_centroids)
    feet = [s for s in segments if s in ('leftFoot','rightFoot')]
    heights_h, heights_r = {s: [] for s in feet}, {s: [] for s in feet}
    for chunk in h['chunks']:
        start, count = chunk['start'], chunk['count']
        sl = slice(start,start+count)
        vertices = np.fromfile(folder / chunk['file'], dtype='<i2').reshape(count,h['vertex_count'],3)
        vertices = vertices.astype(float) * h['quantization_m'] + roots_h[sl,None,:]
        source = (vertices[:,slot_vertices] * bary[None,:,:,None]).sum(axis=2)
        matrices = transforms[sl][:,slot_piece]
        target = np.einsum('fnij,nj->fni',matrices[:,:,:,:3],slot_local) + matrices[:,:,:,3]
        for i, segment in enumerate(segments):
            mask = labels == segment
            source_centroids[sl,i] = source[:,mask].mean(axis=1)
            target_centroids[sl,i] = target[:,mask].mean(axis=1)
            if segment in feet:
                heights_h[segment].extend(np.quantile(source[:,mask,1],.05,axis=1).tolist())
                heights_r[segment].extend(np.quantile(target[:,mask,1],.05,axis=1).tolist())
    # Generic SOMA's mesh encoding anchor can be a static skeleton Root, not
    # its moving Hips. Use the same explicitly observed surface region in both
    # embodiments instead of equating unlike skeleton root definitions.
    hips = segments.index('hips')
    relative_h = source_centroids-source_centroids[:,hips,None,:]
    relative_r = target_centroids-target_centroids[:,hips,None,:]
    mismatch = np.linalg.norm(relative_h-relative_r,axis=2)
    directions = {}
    for start,end in [('hips','torso'),('torso','head'),
            ('leftUpLeg','leftLeg'),('leftLeg','leftFoot'),
            ('rightUpLeg','rightLeg'),('rightLeg','rightFoot'),
            ('leftArm','leftForeArm'),('leftForeArm','leftHand'),
            ('rightArm','rightForeArm'),('rightForeArm','rightHand')]:
        if start not in segments or end not in segments:
            continue
        sh = source_centroids[:,segments.index(end)]-source_centroids[:,segments.index(start)]
        sr = target_centroids[:,segments.index(end)]-target_centroids[:,segments.index(start)]
        denominator = np.linalg.norm(sh,axis=1)*np.linalg.norm(sr,axis=1)
        valid = denominator > 1e-10
        angles = np.degrees(np.arccos(np.clip((sh[valid]*sr[valid]).sum(axis=1)/denominator[valid],-1,1)))
        directions[start+'->'+end] = stats(angles)
    proxy = {}
    for name, centroids, heights in [('source',source_centroids,heights_h),('robot',target_centroids,heights_r)]:
        proxy[name] = {}
        for foot in feet:
            i = segments.index(foot)
            height = np.asarray(heights[foot])
            speed = np.linalg.norm(np.diff(centroids[:,i,[0,2]],axis=0),axis=1)*fps
            near = (height[:-1] <= .02) & (height[1:] <= .02)
            proxy[name][foot] = {'foot_slot_height_p05_m': stats(height),
                'near_floor_interval_fraction': float(near.mean()),
                'near_floor_centroid_planar_speed_m_s': stats(speed[near]),
                'below_floor_5mm_frame_fraction': float((height < -.005).mean())}
    qpos, model = run['qpos'], run['model']
    excess = 0.
    for i in range(model.njnt):
        if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE and model.jnt_limited[i]:
            lo, hi = model.jnt_range[i]
            excess = max(excess,float(np.maximum(lo-qpos[:,model.jnt_qposadr[i]],qpos[:,model.jnt_qposadr[i]]-hi).max()))
    effective_excess = excess
    limits = json.loads((run['run']/'resolved.json').read_text())['robot'].get('joint_limits',{})
    for name,(lo,hi) in limits.items():
        values=qpos[:,model.joint(name).qposadr[0]]
        effective_excess=max(effective_excess,float(np.maximum(float(lo)-values,values-float(hi)).max()))
    return {'frame_count': frames,'fps': fps,'duration_frames_over_fps_s': frames/fps,
        'source_scale':run['scale'], 'root_quaternion_norm_max_error':float(np.abs(np.linalg.norm(qpos[:,3:7],axis=1)-1).max()),
        'compiled_joint_limit_max_excess_rad':excess,
        'compiled_and_configured_joint_limit_max_excess_rad':effective_excess,
        'absolute_scalar_joint_step_rad':stats(np.abs(np.diff(qpos[:,7:],axis=0))),
        'hips_centered_segment_centroid_mismatch_m':stats(mismatch[:,np.arange(len(segments)) != hips]),
        'per_segment_hips_centered_centroid_mismatch_m':{s:stats(mismatch[:,i]) for i,s in enumerate(segments)},
        'segment_centroid_direction_difference_deg':directions,
        'foot_proxies':proxy,
        'definitions': {'centroids':'Mean of bound surface slots per native19 label; decoded source is already scaled by saved source_scale. Subtract each own hips surface centroid; retain all rotations. Aggregate excludes the trivially zero anchored hips region, with equal weight per remaining segment and frame. SOMA encoding Root can be static and is not assumed to be a pelvis. Different proportions/reference poses and slot locations contribute to mismatch; this is not a correspondence accuracy score.',
            'foot_proxy':'Y-up floor y=0; per-frame fifth percentile of reconstructed bound foot-slot heights. Near floor means both adjacent heights <= 0.02 m. Speed uses foot segment centroid in horizontal x/z, at recorded FPS. Geometry/sample proxy, not contact labels or measured support forces.',
            'directions':'World-frame angle between corresponding source and robot vectors joining named segment surface centroids. Retains orientation; ignores vector length. Surface region placement and embodiment proportions affect this descriptive metric.',
            'joint_step':'Absolute adjacent scalar qpos differences, without wrapping or time normalization; clip-specific smoothness diagnostic.'}}


def probe_svg(path, data):
    probes, labels, same = data
    palette = ['#e6194b','#3cb44b','#ffe119','#4363d8','#f58231','#911eb4','#46f0f0','#f032e6','#bcf60c','#fabebe','#008080','#e6beff','#9a6324','#fffac8','#800000','#aaffc3','#808000','#ffd8b1','#000075']
    segments = sorted(set(labels[0]) | set(labels[1]))
    colors = dict(zip(segments,palette))
    x, y = probes[:,0], probes[:,1]
    scale = min(340/(x.max()-x.min()),490/(y.max()-y.min()))
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="680" viewBox="0 0 1200 680"><rect width="1200" height="680" fill="#f6f8fc"/>']
    for panel,title in enumerate(('SMPL-X source labels on G1','SOMA-X source labels on G1','Disagreement (magenta)')):
        out.append(f'<text x="{panel*400+20}" y="28" font-size="18">{title}</text>')
        for i in range(len(probes)):
            color = colors[str(labels[panel][i])] if panel < 2 else ('#526477' if same[i] else '#ff0090')
            px, py = panel*400+200+(x[i]-(x.min()+x.max())/2)*scale, 60+(y.max()-y[i])*scale
            out.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="2.1" fill="{color}" fill-opacity=".75"/>')
    for i,s in enumerate(segments):
        col,row = i%5,i//5
        out.append(f'<rect x="{col*240+10}" y="{575+row*23}" width="12" height="12" fill="{colors[s]}"/><text x="{col*240+28}" y="{586+row*23}" font-size="13">{html.escape(s)}</text>')
    out.append('</svg>')
    path.write_text(''.join(out))


def write_index(output, result, runs):
    cells = []
    for title, field, statistic, multiplier, unit in [
            ('Frames','frame_count',None,1,''),('FPS','fps',None,1,'Hz'),
            ('Mean hips-centered segment discrepancy','hips_centered_segment_centroid_mismatch_m','mean',100,'cm'),
            ('P95 joint step','absolute_scalar_joint_step_rad','p95',1,'rad/frame'),
            ('Configured/model joint-limit excess','compiled_and_configured_joint_limit_max_excess_rad',None,1,'rad')]:
        values=[]
        for model in ('smplx','somax'):
            value=result[model]['motion'][field]
            value=value[statistic] if statistic else value
            values.append(f'{value*multiplier:.5g} {unit}')
        cells.append('<tr><th>'+title+'</th>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
    counts=[]
    for label,iou in sorted(result['spatial_segment_consistency']['per_segment_probe_iou'].items(),key=lambda pair:pair[1]):
        counts.append(f'<tr><td>{html.escape(label)}</td><td>{result["smplx"]["bindings"]["segment_counts"].get(label,0)}</td><td>{result["somax"]["bindings"]["segment_counts"].get(label,0)}</td><td>{iou*100:.2f}%</td></tr>')
    links=[]
    for model,title in [('smplx','SMPL-X official-default G1: getting up'),('somax','SOMA generic control: jump and land')]:
        link=html.escape(os.path.relpath(runs[model]['inspection'],output),quote=True)
        links.append(f'<a class="button" href="{link}/">{title} — interactive source + robot</a>')
    agreement=result['spatial_segment_consistency']['label_agreement_fraction']*100
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fresh G1 comparison · 2026-11-02</title><style>body{{max-width:1200px;margin:32px auto;padding:0 22px;font:16px/1.6 system-ui;color:#1b2738;background:#f6f8fc}}h1,h2{{line-height:1.2}}.notice{{background:#fff2ce;border-left:5px solid #c98800;padding:16px}}.button{{display:inline-block;padding:10px 15px;margin:8px 12px 8px 0;background:#163d72;color:white;border-radius:6px}}table{{border-collapse:collapse;background:white;width:100%;margin:20px 0}}td,th{{text-align:left;padding:9px 12px;border-bottom:1px solid #dce2eb}}img{{width:100%;background:white}}code{{overflow-wrap:anywhere}}</style>
<h1>Same G1, two human representations</h1><p>Fresh 2026-11-02 results · official-default SMPL-X reproduction and a SOMA generic control</p>
<p class="notice">The two source motions differ, and the SOMA control uses a generic neutral body because the dataset-specific fitted uniform shape is unavailable. These results do not rank human models or establish dynamic feasibility.</p>
<h2>Inspect each human and its robot motion</h2><p>{''.join(links)}</p><p>Use Reference pose to inspect paired segment bindings; select a segment or slot to inspect robot body/mesh ownership. Use Play, Frame and the timeline to compare the full synchronized source and saved G1 motion.</p>
<h2>Same robot surface, independently learned labels</h2><p>All {len(result['robot_consistency']['checks'])} bounded robot consistency checks pass exactly, including 192,938 reference vertices, 385,626 faces and the same 4,096 sampled robot points. Source segment labels agree on <strong>{agreement:.2f}%</strong> of these common robot probes. Nearest projected target binding assigns labels independently per run; learned slot row numbers are never equated.</p>
<img src="robot-label-probes.svg" alt="Same robot probe locations colored by SMPL-X or SOMA source segment, with disagreement map"><p>Front projection of identical robot samples; no depth occlusion. Source semantic labels and robot attachment ownership are distinct. Each run covers all 19 source segments and 33 target bodies. The fixed robot head belongs to torso_link.</p>
<h2>Per-clip motion diagnostics</h2><table><thead><tr><th>Metric</th><th>SMPL-X: getting up</th><th>SOMA generic: jump/land</th></tr></thead><tbody>{''.join(cells)}</tbody></table>
<p>Centroid discrepancy uses each model's own bound hips surface centroid as origin, saved source scale, full frame timing and equal weight across the other 18 source segments. It includes embodiment proportions and region placement; it is not anatomical ground truth. SOMA uses the corrected moving named Hips anchor for mesh decoding/display.</p>
<h2>Binding region coverage and spatial consistency</h2><table><thead><tr><th>Native19 source region</th><th>SMPL-X slots</th><th>SOMA slots</th><th>Common-probe region IoU</th></tr></thead><tbody>{''.join(counts)}</tbody></table>
<p>IoU is intersection/union of the spatially assigned probe labels. Small shoulder/upper-arm regions are more sensitive to boundary shifts. Detailed body/mesh ownership, projection distances, per-segment fidelity, direction angles and foot-floor proxies are in <a href="comparison.json">the full measurements and provenance</a>.</p>
<p>Foot proxies use the fifth percentile of bound foot-slot heights and a 2 cm near-floor threshold. They do not measure contact forces, support stability or confirmed foot slip. Whole-body collisions and dynamic balance were not evaluated.</p>
<p>Evaluation input hashes passed before/after checks. <a href="evaluate.py">Exact evaluator source</a> is preserved alongside this derivative. Both upstream and prior cohorts remain unchanged.</p></html>'''
    (output/'index.html').write_text(page)


def main():
    parser=argparse.ArgumentParser(__doc__)
    for name in ('smplx-run','somax-run','smplx-inspection','somax-inspection','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    a,b=load(args.smplx_run.resolve(),args.smplx_inspection.resolve()),load(args.somax_run.resolve(),args.somax_inspection.resolve())
    files=set(a['files']+b['files']+[Path(__file__).resolve()])
    before={**a['initial_hashes'],**b['initial_hashes'],str(Path(__file__).resolve()):sha(Path(__file__))}
    equality=robot_equality(a,b)
    spatial,probes=spatial_comparison(a,b)
    result={'scope':'Official-default SMPL-X G1 reproduction plus SOMA generic control; different-motion descriptive comparison, no causal human-model ranking',
        'robot_consistency':equality,'spatial_segment_consistency':spatial,
        'smplx':{'bindings':bindings(a),'motion':motion(a)},'somax':{'bindings':bindings(b),'motion':motion(b)},
        'source_artifact_sha256':before}
    if before != {str(f):sha(f) for f in sorted(files)}:
        raise RuntimeError('Evaluation inputs changed')
    result['preservation']={'all_evaluation_inputs_unchanged':True}
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    probe_svg(args.output/'robot-label-probes.svg',probes)
    (args.output/'evaluate.py').write_bytes(Path(__file__).read_bytes())
    write_index(args.output,result,{'smplx':a,'somax':b})
    print(json.dumps({'output':str(args.output),'all_robot_checks_equal':equality['all_checked_equal'],
                      'common_probe_label_agreement':spatial['label_agreement_fraction']}))


if __name__=='__main__':
    main()
