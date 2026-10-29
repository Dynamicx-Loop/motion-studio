"""Freeze one Astro revision, archive the report, and prepare matched static arms."""
import hashlib
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/astro-canonical-static-v1'
ASSETS = Path('/data/workspace/notAnyrobot/menagerie_x')
EXT = ROOT / 'externals/UMR-astro-surface-experiment'
sys.path.insert(0, str(EXT / 'scripts'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb


def sha(p):
    return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def stripped_xml(xml):
    root = ET.fromstring(xml)
    for parent in root.iter():
        for child in list(parent):
            if child.tag == 'keyframe' or (child.tag == 'geom' and child.get('group') == '3'):
                parent.remove(child)
    # Ignore whitespace left by deleted collision elements.
    for node in root.iter():
        node.text = None
        node.tail = None
    return ET.tostring(root)


def main():
    assert not (HERE / 'preparation.json').exists(), 'Use a new version for a new snapshot'
    OUT.mkdir(parents=True, exist_ok=True)
    report = ROOT / 'outputs/umr-binding-report'
    archive = report / 'history/pre-canonical-v3'
    archive.mkdir(parents=True, exist_ok=False)
    for p in report.iterdir():
        if p.name != 'history':
            if p.is_dir():
                shutil.copytree(p, archive / 'report' / p.name)
            else:
                (archive / 'report').mkdir(exist_ok=True)
                shutil.copy2(p, archive / 'report' / p.name)
    shutil.copytree(ROOT / 'experiments/umr-binding-report', archive / 'source',
                    ignore=shutil.ignore_patterns('__pycache__'))
    dump(archive / 'hashes.json', {str(p.relative_to(archive)): sha(p)
                                  for p in archive.rglob('*') if p.is_file()})

    variant = 'robots/astro_p2_43dof_dex3_1'
    frozen = OUT / 'asset-snapshot/astro'
    for name in git(ASSETS, 'ls-files', variant).splitlines():
        source = ASSETS / name
        dest = frozen / source.relative_to(ASSETS / variant)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    g1 = OUT / 'asset-snapshot/g1'
    shutil.copytree(EXT / 'assets/g1', g1,
                    ignore=shutil.ignore_patterns('*.floating_mjcf.xml'))
    xml = frozen / 'astro_p2_43dof_dex3_1.xml'
    old_xml = subprocess.check_output(['git', '-C', str(ASSETS), 'show',
        '1316cac090144c9891453a53b8336e8374c96196:' + variant + '/astro_p2_43dof_dex3_1.xml'])
    assert stripped_xml(xml.read_bytes()) == stripped_xml(old_xml)
    model = mujoco.MjModel.from_xml_path(str(xml))
    data = mujoco.MjData(model)
    old = ROOT / 'experiments/astro-hands-correspondence'
    base = json.loads((old / 'smplx_astro_spine1.json').read_text())
    q = base['robot']['tpose_qpos']
    assert (model.nq, model.nv, model.nu) == (50, 49, 0)
    joints = []
    for j in range(model.njnt):
        if model.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
            continue
        name = model.joint(j).name
        assert model.jnt_range[j, 0] <= q[name] <= model.jnt_range[j, 1]
        joints.append({'name': name, 'qpos_address': int(model.jnt_qposadr[j]),
                       'dof_address': int(model.jnt_dofadr[j]),
                       'range_rad': model.jnt_range[j].tolist(), 'tpose_rad': q[name]})
    assert len(joints) == 43 and sum('_hand_' in j['name'] for j in joints) == 14
    assert not any('neck' in j['name'] for j in joints)
    build.apply_joint_qpos(model, data, q, required=True)
    mujoco.mj_forward(model, data)
    ids = rb.visual_geom_ids(model, 'auto')
    assert len(ids) == 51 and all(model.geom_group[g] == 1 for g in ids)
    assert all(model.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH for g in ids)
    v, f, owners, *_ = rb.collect_root_mesh(model, data, ids, 'body:pelvis')
    historic = np.load(base['correspondence']['dataset']['out'], allow_pickle=True)
    np.testing.assert_array_equal(f, historic['mesh_faces_1'])
    np.testing.assert_allclose(v @ rb.SMPL_TO_ROBOT_ROOT_MATRIX,
                               historic['mesh_vertices_1'], atol=2e-7, rtol=0)
    target = build.build_robot_sample(str(xml), base['robot']['name'], 4096, 9000,
        8, 0., 1., point_cloud_center_name='body:pelvis', tpose_qpos=q,
        visual_geom_policy='auto')
    inventory = [{'geom_id': int(g), 'body_id': int(model.geom_bodyid[g]),
                  'body': model.body(int(model.geom_bodyid[g])).name,
                  'mesh': model.mesh(int(model.geom_dataid[g])).name}
                 for g in ids]
    assert sum('_hand_' in g['mesh'] for g in inventory) == 16
    arms, controls = {}, {}
    for source in ['smplx', 'soma']:
        for center in ['spine1', 'bbox50']:
            for robot in ['astro', 'g1']:
                arm = f'{source}_{robot}_{center}'
                exp = 'astro-hands-correspondence' if robot == 'astro' else 'soma-correspondence-audit'
                origin = ROOT / f'experiments/{exp}/{arm}.json'
                c = json.loads(origin.read_text())
                ds = dict(np.load(c['correspondence']['dataset']['out'], allow_pickle=True))
                human = ds['points'][0].copy()
                dest = OUT / arm
                dest.mkdir()
                if robot == 'astro':
                    for key, field in [('mesh_vertices_1', 'vertices'), ('mesh_faces_1', 'faces'),
                                       ('sample_face_ids_1', 'sample_face_ids')]:
                        ds[key] = target[field]
                    ds['points'][1] = target['points']
                    c['robot']['xml'] = str(xml)
                else:
                    c['robot']['xml'] = str(g1 / 'g1_29dof.xml')
                    (dest / 'train').mkdir()
                    shutil.copy2(Path(c['correspondence']['train']['out_dir']) /
                                 'correspondence_slots_final.npz',
                                 dest / 'train/correspondence_slots_final.npz')
                ds['custom_robot_xml'] = np.asarray(c['robot']['xml'])
                np.testing.assert_array_equal(ds['points'][0], human)
                np.savez_compressed(dest / 'dataset.npz', **ds)
                controls[arm] = {'config': str(origin), 'experiment': exp,
                    'source_arrays_bitwise_inherited': True,
                    'training': 'fresh 500 epochs' if robot == 'astro' else 'exact historical slots reused',
                    'historical_dataset_sha256': sha(c['correspondence']['dataset']['out'])}
                c['correspondence']['dataset']['out'] = str(dest / 'dataset.npz')
                c['correspondence']['train']['out_dir'] = str(dest / 'train')
                c['retarget']['out'] = str(dest / 'STATIC_ONLY_no_trajectory.npz')
                c['experiment'] = {'stage': 'canonical_static', 'retarget_authorized': True,
                    'canonical_asset_manifest': str(HERE / 'canonical-asset.json'),
                    'training': controls[arm]['training'], 'finger_pose': 'zero/open T-pose'}
                dump(HERE / f'{arm}.json', c)
                arms[arm] = str(HERE / f'{arm}.json')
    patch = subprocess.check_output(['git', '-C', str(ASSETS), 'diff', 'HEAD'])
    (HERE / 'menagerie_x.patch').write_bytes(patch)
    umr_patch = subprocess.check_output(['git', '-C', str(EXT), 'diff', 'HEAD'])
    (HERE / 'UMR-astro-surface-experiment.patch').write_bytes(umr_patch)
    asset = {'schema_version': 1, 'date': '2026-10-23',
        'canonical_variant': 'astro_p2_43dof_dex3_1',
        'menagerie_commit': git(ASSETS, 'rev-parse', 'HEAD'),
        'fetched_origin_main': git(ASSETS, 'rev-parse', 'origin/main'),
        'integration': 'Fetch complete; origin/main is ancestor of local HEAD; no merge required',
        'menagerie_status': git(ASSETS, 'status', '--short'),
        'tracked_patch_sha256': hashlib.sha256(patch).hexdigest(),
        'xml': str(xml), 'xml_sha256': sha(xml),
        'pose': 'Open hands; named shoulder rolls +/-pi/2 and elbows +pi/2; fist keyframe not selected',
        'nq': model.nq, 'nv': model.nv, 'nu': model.nu, 'joints': joints,
        'selected_visual_geoms': inventory, 'visual_vertices': len(v), 'visual_faces': len(f),
        'collision_geom_count': int((model.geom_group == 3).sum()),
        'collision_policy': 'Preserved latest primitives; visual surfaces only; no new primitive experiment',
        'historical_geometry_equal_within_200nm': True,
        'historical_xml_equal_after_removing_collision_geoms_and_keyframes': True,
        'files': {str(p): sha(p) for p in (OUT / 'asset-snapshot').rglob('*') if p.is_file()},
        'immutable_for_runs': True, 'mujoco_version': mujoco.__version__}
    dump(HERE / 'canonical-asset.json', asset)
    dump(HERE / 'arms.json', arms)
    dump(HERE / 'preparation.json', {'controls': controls,
        'umr_revision': git(EXT, 'rev-parse', 'HEAD'),
        'umr_diff_sha256': hashlib.sha256(umr_patch).hexdigest(),
        'report_archive': str(archive), 'target_sampler_seed': 9000,
        'source_sampler_seed': 'inherited 1000', 'train_seed': 0})
    print('Frozen', asset['menagerie_commit'], sha(xml), 'and prepared 8 matched arms')


if __name__ == '__main__':
    main()
