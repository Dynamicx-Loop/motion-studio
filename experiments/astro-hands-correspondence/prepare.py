"""Freeze inputs and prepare four static hand-variant datasets; no solver."""
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import numpy as np
import mujoco
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/astro-hands-correspondence'
EXT = ROOT / 'externals/UMR-astro-surface-experiment'
ASSETS = Path('/data/workspace/notAnyrobot/menagerie_x')
sys.path.insert(0, str(EXT / 'scripts'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb

def sha(p): return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()
def dump(p, x): p.write_text(json.dumps(x, indent=2) + '\n')
def git(p, *args): return subprocess.check_output(['git', '-C', str(p), *args], text=True).strip()

def main():
    assert not (HERE / 'preparation.json').exists(), 'Use a new version; never overwrite inputs'
    old = ROOT / 'experiments/soma-correspondence-audit'
    # Freeze historical evidence and identify upstream changes separately.
    immutable = {}
    for folder in ['experiments/soma-correspondence-audit', 'experiments/segment-binding-audit', 'experiments/astro-correspondence-comparison', 'experiments/astro-surface-geometry', 'outputs/soma-correspondence-audit']:
        for p in (ROOT / folder).rglob('*'):
            if p.is_file() and '__pycache__' not in str(p): immutable[str(p)] = sha(p)
    upstream_changes = []
    for p, digest in json.loads((old / 'provenance.json').read_text())['hashes'].items():
        if canonical_motion_path(p).is_file() and sha(p) != digest:
            upstream_changes.append({'path': p, 'historical_sha256': digest, 'current_sha256': sha(p)})
    xml = ASSETS / 'robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml'
    model = mujoco.MjModel.from_xml_path(str(xml)); data = mujoco.MjData(model)
    c = json.loads((old / 'smplx_astro_spine1.json').read_text())
    q = c['robot']['tpose_qpos'].copy()
    joints = []
    for j in range(model.njnt):
        name = model.joint(j).name
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE: continue
        q.setdefault(name, 0.)
        assert model.jnt_range[j, 0] - 1e-8 <= q[name] <= model.jnt_range[j, 1] + 1e-8, name
        joints.append({'name':name,'qpos_address':int(model.jnt_qposadr[j]),'dof_address':int(model.jnt_dofadr[j]),'range_rad':model.jnt_range[j].tolist(),'tpose_rad':q[name]})
    assert len(q) == 43 and model.nq == 50 and model.nv == 49
    build.apply_joint_qpos(model, data, q, required=True); mujoco.mj_forward(model, data)
    ids = rb.visual_geom_ids(model, 'auto')
    assert all(model.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH for g in ids)
    inventory = [{'geom_id':int(g),'body':model.body(int(model.geom_bodyid[g])).name,'mesh':model.mesh(int(model.geom_dataid[g])).name} for g in ids]
    assert sum('_hand_' in g['mesh'] for g in inventory) == 16
    # Existing body visual triangles and landmarks must still match the old model.
    oldmodel = mujoco.MjModel.from_xml_path(c['robot']['xml']); olddata = mujoco.MjData(oldmodel)
    build.apply_joint_qpos(oldmodel, olddata, c['robot']['tpose_qpos'], required=True); mujoco.mj_forward(oldmodel, olddata)
    for j in c['robot']['tpose_qpos']:
        np.testing.assert_allclose(data.xanchor[model.joint(j).id], olddata.xanchor[oldmodel.joint(j).id], atol=1e-8, rtol=0)
    target = build.build_robot_sample(str(xml), 'astro_p2_43dof_dex3_1', 4096, 9000, 8, 0., 1., point_cloud_center_name='body:pelvis', tpose_qpos=q, visual_geom_policy='auto')
    oldds = np.load(c['correspondence']['dataset']['out'], allow_pickle=True)
    ov, of, oo, *_ = rb.collect_root_mesh(oldmodel, olddata, rb.visual_geom_ids(oldmodel,'auto'), 'body:pelvis')
    np.testing.assert_array_equal(of, oldds['mesh_faces_1'])
    np.testing.assert_allclose(ov @ rb.SMPL_TO_ROBOT_ROOT_MATRIX, oldds['mesh_vertices_1'], atol=2e-7, rtol=0)
    assets = {str(p): sha(p) for p in xml.parent.rglob('*') if p.is_file()}
    body_meshes = []
    for node in ET.parse(xml).findall('.//asset/mesh'):
        p = xml.parent / 'meshes' / node.get('file')
        baseline = ASSETS / 'robots/astro_p2_29dof/meshes' / node.get('file')
        if baseline.exists():
            assert sha(p) == sha(baseline), p
            body_meshes.append(str(p))
    arms = {}; controls = {}
    for source in ['smplx','soma']:
        for center in ['spine1','bbox50']:
            arm = f'{source}_astro_{center}'
            c = json.loads((old / f'{arm}.json').read_text())
            ds = dict(np.load(c['correspondence']['dataset']['out'], allow_pickle=True))
            original = {k:v.copy() for k,v in ds.items()}
            for key, field in [('mesh_vertices_1','vertices'),('mesh_faces_1','faces'),('sample_face_ids_1','sample_face_ids')]: ds[key] = target[field]
            ds['points'][1] = target['points']
            ds['names'] = np.array([str(ds['names'][0]), target['name']])
            ds['custom_robot_name'] = np.asarray(target['name'])
            ds['custom_robot_xml'] = np.asarray(str(xml))
            ds['custom_robot_sample_qpos_names'] = np.asarray(list(q), dtype=object)
            ds['custom_robot_sample_qpos_values'] = np.asarray(list(q.values()), dtype=np.float32)
            dest = OUT / arm; dest.mkdir(exist_ok=True)
            np.savez_compressed(dest / 'dataset.npz', **ds)
            for key in ['mesh_vertices_0','mesh_faces_0','sample_face_ids_0','betas_0']:
                np.testing.assert_array_equal(ds[key], original[key])
            np.testing.assert_array_equal(ds['points'][0], original['points'][0])
            c['robot'].update(name=target['name'], xml=str(xml), tpose_qpos=q)
            c['experiment'] = {'stage':'static_correspondence_only','retarget_authorized':False,'source':source,'centering':center,'historical_source_config':str(old/f'{arm}.json'),'variant':'Astro with Dex3-1 sample hands','finger_pose':'all 14 hinge coordinates zero, open vendor pose'}
            c['correspondence']['dataset']['out'] = str(dest/'dataset.npz')
            c['correspondence']['train']['out_dir'] = str(dest/'train')
            c['retarget']['out'] = str(dest/'NOT_AUTHORIZED_retarget.npz')
            dump(HERE/f'{arm}.json',c); arms[arm]=str(HERE/f'{arm}.json')
            controls[arm]={'source_arrays_bitwise_identical_to_historical':True,'target_arrays_identical_across_four_arms':True,'dataset_sha256':sha(dest/'dataset.npz')}
    dump(HERE/'arms.json',arms)
    dump(HERE/'asset-inspection.json',{'menagerie_revision':git(ASSETS,'rev-parse','HEAD'),'menagerie_status':git(ASSETS,'status','--short'),'nq':model.nq,'nv':model.nv,'nu':model.nu,'joint_order':joints,'selected_visual_geoms':inventory,'body_meshes_identical_to_baseline':body_meshes,'unchanged_body_joint_anchors':True,'historical_dataset_geometry_matches_current_old_model':True,'target_bounds_smpl_frame_m':[target['vertices'].min(0).tolist(),target['vertices'].max(0).tolist()],'mesh_count':model.nmesh,'mujoco_version':mujoco.__version__,'asset_hashes':assets})
    dump(HERE/'preparation.json',{'historical_artifact_hashes':immutable,'changed_upstream_inputs_since_old_run':upstream_changes,'controls':controls,'umr_revision':git(EXT,'rev-parse','HEAD'),'umr_diff_sha256':hashlib.sha256(subprocess.check_output(['git','-C',str(EXT),'diff'])).hexdigest(),'source_sampler_seed':1000,'target_sampler_seed':9000,'retarget_run':False})
    dump(ROOT/'configs/umr/astro_p2_43dof_dex3_1-static-v1.json',{'robot':c['robot'],'experiment':c['experiment']})
    print('Prepared four arms; 43 named hinges, 16 hand meshes, unchanged historical body geometry.')

if __name__ == '__main__': main()
