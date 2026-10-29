#!/usr/bin/env python3
"""Audit all shipped canonical correspondences, export geometry; never solve motion."""
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
from collections import Counter
import hashlib,json,pickle,sys,csv,shutil
import numpy as np
import mujoco
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
EXT=ROOT/'externals/UMR-astro-surface-experiment'
sys.path.insert(0,str(EXT/'scripts'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb
import retarget_body_segment_surface as seg
from humanoid_retarget_config import load_config
from primitive_surface import bind_points_to_mesh_exact,PrimitiveUnion
from smpl_surface_retarget_common import bind_points_to_mesh
from types import SimpleNamespace
from regions import geometry_regions,joint_anchors,rigid_owner,ownership_region,expected_regions
OUT=ROOT/'outputs/all-robot-segment-audit'
VIEW=OUT/'viewer'
ARMS={name:HERE/(name+'.json') for name in ['piplus','k1','t800','h2','mimickit','g1_racket','g1_spherehand']}


def sha(path):return hashlib.sha256(canonical_motion_path(path).read_bytes()).hexdigest()
def table(a,b):
    return {s:dict(sorted(Counter(np.asarray(b)[np.asarray(a)==s]).items())) for s in sorted(set(a))}
def dump(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
def stats(x):return {'mean':float(np.mean(x)),'p95':float(np.percentile(x,95)),'max':float(np.max(x))}


def geometry(model,data,c,policy):
    ids=rb.visual_geom_ids(model,policy)
    v,f,owners,center,rotation,_=rb.collect_root_mesh(model,data,ids,c['robot']['point_cloud_center'])
    face_bodies=np.array([model.body(int(model.geom_bodyid[g])).name for g in owners])
    face_meshes=np.array([model.mesh(int(model.geom_dataid[g])).name if model.geom_type[g]==mujoco.mjtGeom.mjGEOM_MESH else model.geom(int(g)).name or model.body(int(model.geom_bodyid[g])).name for g in owners])
    return v,f,owners,center,rotation,face_bodies,face_meshes


def export_mesh(name,v,f,owners,bodies,meshes,anchors):
    # Geoms have disjoint vertex blocks in the collected mesh. Every vertex gets
    # one actual geom owner, plus an independent spatial audit region.
    vb=np.empty(len(v),object);vm=np.empty(len(v),object);vg=np.empty(len(v),np.int32)
    for g in np.unique(owners):
        face=np.flatnonzero(owners==g);verts=np.unique(f[face]);vb[verts]=bodies[face[0]];vm[verts]=meshes[face[0]];vg[verts]=g
    regions=geometry_regions(v,vb,vm,anchors)
    region_names=sorted(set(regions));body_names=sorted(set(vb))
    arrays={'vertices':(v@rb.SMPL_TO_ROBOT_ROOT_MATRIX).astype('<f4'),'faces':f.astype('<u4'),
            'regions':np.array([region_names.index(x) for x in regions],dtype='<u2'),
            'bodies':np.array([body_names.index(x) for x in vb],dtype='<u2')}
    meta={'region_names':region_names,'body_names':body_names}
    for key,a in arrays.items():
        filename=f'{name}-{key}.bin';a.tofile(VIEW/filename);meta[key]={'file':filename,'shape':a.shape}
    meta['geoms']=[{'id':int(g),'body':bodies[np.flatnonzero(owners==g)[0]],'mesh':meshes[np.flatnonzero(owners==g)[0]]} for g in np.unique(owners)]
    return meta


def audit(arm,path):
    c=load_config(path);dump(HERE/f'{arm}-resolved.json',c)
    ds=np.load(c['correspondence']['dataset']['out'],allow_pickle=True)
    sp=Path(c['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz'
    slots=np.load(sp,allow_pickle=True); human,learned=slots['reconstructed_slots']
    assert not Path(c['retarget']['out']).exists()
    assert str(slots['training_mode'])=='robot2smpl_only'
    assert human.shape==learned.shape==(4096,3) and np.isfinite(learned).all()
    np.testing.assert_array_equal(slots['slot_index'],np.arange(4096))
    hbind=bind_points_to_mesh_exact(human,ds['mesh_vertices_0'],ds['mesh_faces_0'])
    source_ids=seg.smplx_slot_part_ids_from_binding(ds['mesh_faces_0'],hbind['face_ids'],template_vertices=ds['mesh_vertices_0'],bary=hbind['bary'],slot_points=hbind['closest_points'])
    names={v:k for k,v in seg.SMPLX_PART_IDS.items()};sources=np.array([names[x] for x in source_ids])
    raw=pickle.load(open(EXT/'assets/smplx_parts_segm.pkl','rb'),encoding='latin1')['segm'].reshape(-1)
    raw_slots=raw[hbind['face_ids']]
    model=mujoco.MjModel.from_xml_path(c['robot']['xml']);data=mujoco.MjData(model)
    build.apply_joint_qpos(model,data,c['robot'].get('tpose_qpos',{}),required=True);mujoco.mj_forward(model,data)
    v,f,o,center,rot,fb,fm=geometry(model,data,c,c['robot']['visual_geom_policy'])
    anchors=joint_anchors(model,data,center,rot)
    p=rb.smpl_frame_to_robot_root(learned)
    bound=bind_points_to_mesh(p,v,f,method='nearest_vertex')
    face=bound['face_ids'];projected=bound['closest_points'];geom=o[face];bodies=fb[face];meshes=fm[face]
    invalid=np.zeros(len(human),bool);failure=None
    production=rb.bind_robot_slots(model,SimpleNamespace(config_data=c),learned)
    np.testing.assert_allclose(production['root_points'],projected,atol=1e-7,rtol=0)
    buried=np.zeros(len(human),bool)
    if all(model.geom_type[int(g)]!=mujoco.mjtGeom.mjGEOM_MESH for g in np.unique(o)):
        union=PrimitiveUnion.from_model(model,data,np.unique(o),center,rot)
        buried=~union.exterior_mask(projected,geom)
    regions=geometry_regions(projected,bodies,meshes,anchors)
    rigid=np.array([rigid_owner(model,int(model.geom_bodyid[g])) for g in geom])
    kin=np.array([ownership_region(x) for x in rigid])
    # Training reference samples inherit their actual sample face ownership.
    # This is reference-cloud coverage, not held-out surface-area recall.
    sample_faces=ds['sample_face_ids_1'];sample_points=rb.smpl_frame_to_robot_root(ds['points'][1])
    sample_regions=geometry_regions(sample_points,fb[sample_faces],fm[sample_faces],anchors)
    rows=[]
    for source in sorted(set(sources)):
        mask=sources==source;allowed=expected_regions(source);target=np.isin(regions,list(allowed))
        expected_sample=np.isin(sample_regions,list(allowed));expected_n=int(expected_sample.sum())
        same_source_nearest=cKDTree(projected[mask]).query(sample_points[expected_sample])[0] if expected_n else np.array([])
        correct=int((mask&target).sum())
        rows.append({'source':source,'slots':int(mask.sum()),'compatible_zone_slots':correct,
            'zone_precision':correct/int(mask.sum()),'zone_leakage':1-correct/int(mask.sum()),
            'zone_recall_among_assigned_slots':correct/int(target.sum()) if target.sum() else None,
            'expected_target_sample_count':expected_n,
            'expected_sample_coverage_within_20mm':float((same_source_nearest<=.02).mean()) if expected_n else None,
            'expected_sample_distance_m':stats(same_source_nearest) if expected_n else None,
            'rejected_slots':int(invalid[mask].sum()),'analytic_buried_slots':int(buried[mask].sum()), 'target_zone_available':bool(expected_n)})
    # Plane penetration quantities separate strong cross-joint evidence from
    # points near joint hardware. Still canonical evidence, not motion error.
    crossing={}
    for side in ('left','right'):
        for source,axis,cut,direction in [(side+'UpLeg',2,anchors[side+'_knee_joint'][2],-1),
            (side+'ForeArm',1,anchors[side+'_elbow_joint'][1],-1 if side=='left' else 1),
            (side+'Arm',1,anchors[side+'_elbow_joint'][1],1 if side=='left' else -1)]:
            mask=sources==source;distance=direction*(projected[mask,axis]-cut)
            crossing[source]={'beyond_joint_plane_over_20mm':int((distance>.02).sum()),'slots':int(mask.sum()),'max_beyond_m':float(max(0,distance.max()))}
    metrics={'arm':arm,'source_to_geometry_zone':table(sources,regions),'source_to_body':table(sources,bodies),
        'source_to_mesh':table(sources,meshes),'source_to_rigid_owner':table(sources,rigid),
        'source_to_kinematic_region':table(sources,kin),'per_segment':rows,'joint_plane_checks':crossing,
        'raw55_source_counts':{str(k):int(x) for k,x in sorted(Counter(raw_slots).items())},
        'head_subregions_to_geometry':table(np.array(['neck' if x==12 else 'head/face' for x in raw_slots])[sources=='head'],regions[sources=='head']),
        'projection_error_m':stats(bound['errors']),'rejected_slots':int(invalid.sum()),'production_failure':failure,'analytic_buried_primitive_slots':int(buried.sum()),
        'anchors_root_m':anchors,'profile_notes':{'t800':'No wrist or separate hand model: hand zones unavailable; forearm terminal shell takes hand slots.','k1':'No waist joint/pelvis shell; hips/trunk boundary is not equivalent to articulated-waist robots.','g1_spherehand':'Auto surface selection excludes ankle/foot meshes with contact flags. Foot zones absent from selected surface, although full model has feet. Overlay exposes omitted geometry.','g1_racket':'Human-only control of task variant; native AdaPT composite source is not used. Tool-racket transfers are separate from anatomical hand zones.','mimickit':'Wrist boundary is welded hand body origin, not a wrist joint. Auto primitive fallback uses experimental winding patch; interior check is diagnostic.'}.get(arm.replace('_native_center',''),''),'normalization_scales':slots['normalization_scales'].tolist(),
        'target_sample_zone_counts':dict(Counter(sample_regions)),
        'selected_geom_inventory':[], 'hashes':{'dataset':sha(c['correspondence']['dataset']['out']),'slots':sha(sp),'robot_xml':sha(c['robot']['xml'])}}
    for g in np.unique(o):
        fi=np.flatnonzero(o==g);verts=v[np.unique(f[fi])];bid=int(model.geom_bodyid[g])
        metrics['selected_geom_inventory'].append({'geom':int(g),'body':fb[fi[0]],'mesh':fm[fi[0]],'rigid_owner':rigid_owner(model,bid),'bounds_root_m':[verts.min(0).tolist(),verts.max(0).tolist()]})
    mesh=export_mesh(arm,v,f,o,fb,fm,anchors)
    visual_mesh=None
    if arm=='g1_spherehand':
        vv,ff,oo,_,_,bb,mm=geometry(model,data,c,'mesh_no_floor')
        visual_mesh=export_mesh(arm+'-shell',vv,ff,oo,bb,mm,anchors)
    preview={'human':human.tolist(),'learned':learned.tolist(),'projected':(projected@rb.SMPL_TO_ROBOT_ROOT_MATRIX).tolist(),
        'source_labels':sources.tolist(),'source55':raw_slots.tolist(),'bodies':bodies.tolist(),'meshes':meshes.tolist(),'rigid':rigid.tolist(),
        'regions':regions.tolist(),'geom_ids':geom.tolist(),'invalid':np.flatnonzero(invalid).tolist(),'buried_diagnostic':np.flatnonzero(buried).tolist(),
        'mesh':mesh,'visual_mesh':visual_mesh,'anchors':anchors,'metrics':metrics}
    np.savez_compressed(OUT/f'{arm}-audit.npz',human=human,robot_learned=learned,robot_projected=projected,
        source_labels=sources,source55=raw_slots,geom_ids=geom,body_names=bodies,mesh_names=meshes,rigid_owners=rigid,
        geometry_regions=regions,buried_projection_diagnostic=buried,invalid_projection=invalid,slot_ids=slots['slot_index'])
    return ds,slots,metrics,preview


def main():
    VIEW.mkdir(parents=True,exist_ok=True)
    result={}
    for a,p in ARMS.items():
        print('AUDIT',a,flush=True)
        result[a]=audit(a,p)
    ref=result['piplus']
    prior=json.loads((ROOT/'outputs/segment-binding-audit/viewer/audit.json').read_text())
    prior_config=load_config(ROOT/'experiments/segment-binding-audit/g1.json')
    prior_ds=np.load(prior_config['correspondence']['dataset']['out'],allow_pickle=True)
    prior_slots=np.load(Path(prior_config['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz',allow_pickle=True)
    for key in ['mesh_vertices_0','mesh_faces_0','sample_face_ids_0','betas_0']:
        np.testing.assert_array_equal(ref[0][key],prior_ds[key])
    for key in ['template_sort_index','template_edge_index','template_points']:
        np.testing.assert_array_equal(ref[1][key],prior_slots[key])
    np.testing.assert_array_equal(ref[1]['reconstructed_slots'][0],prior_slots['reconstructed_slots'][0])
    np.testing.assert_array_equal(ref[0]['points'][0],prior_ds['points'][0])
    for file in (ROOT/'outputs/segment-binding-audit/viewer').glob('*.bin'):
        shutil.copyfile(file,VIEW/file.name)
    for arm,(ds,slots,_,_) in result.items():
        np.testing.assert_array_equal(ds['points'][0],ref[0]['points'][0])
        for key in ['mesh_vertices_0','mesh_faces_0','sample_face_ids_0','betas_0']:
            np.testing.assert_array_equal(ds[key],ref[0][key],err_msg=arm+key)
        for key in ['template_sort_index','template_edge_index','template_points']:
            np.testing.assert_array_equal(slots[key],ref[1][key],err_msg=arm+key)
        np.testing.assert_array_equal(slots['reconstructed_slots'][0],ref[1]['reconstructed_slots'][0])
    metrics={a:r[2] for a,r in result.items()}
    metrics.update({a:d['metrics'] for a,d in prior['arms'].items()})
    dump(HERE/'results.json',metrics)
    with (HERE/'per-segment.csv').open('w') as handle:
        cols=['arm']+[k for k in metrics['piplus']['per_segment'][0] if k!='expected_sample_distance_m']
        w=csv.DictWriter(handle,fieldnames=cols);w.writeheader()
        for a,m in metrics.items():
            for row in m['per_segment']:w.writerow({'arm':a,**{k:v for k,v in row.items() if k in cols}})
    data={a:r[3] for a,r in result.items()}
    data.update(prior['arms'])
    # Source mesh uses original face segmentation, plus 19-way split evaluated at
    # actual mesh vertices. Source slots retain the exact official slot split.
    hv=ref[0]['mesh_vertices_0'];hf=ref[0]['mesh_faces_0'];face_ids=seg.load_smplx17_face_parts()[0]
    vertex_ids=seg.vertex_part_ids_from_face_part_ids(hf,face_ids,len(hv))
    vertex_ids=seg.relabel_upper_arm_slots(vertex_ids,hv)
    names={v:k for k,v in seg.SMPLX_PART_IDS.items()}
    human_meta={'names':[names.get(i,'unlabelled') for i in range(20)]}
    for key,array in [('vertices',hv.astype('<f4')),('faces',hf.astype('<u4')),('regions',vertex_ids.astype('<u2'))]:
        fn='human-'+key+'.bin';array.tofile(VIEW/fn);human_meta[key]={'file':fn,'shape':array.shape}
    dump(VIEW/'audit.json',{'arms':data,'human_mesh':human_meta,'human_equal':True})
    print(json.dumps({a:{'head':m['head_subregions_to_geometry'],'projection':m['projection_error_m'],'joint_crossing':m['joint_plane_checks']} for a,m in metrics.items()},indent=2))

if __name__=='__main__':main()
