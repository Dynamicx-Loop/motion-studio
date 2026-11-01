"""Local, pinned official Studio examples; no network or scientific imports."""
from pathlib import Path
import hashlib
import json
import subprocess
import shutil
import xml.etree.ElementTree as ET
from contextlib import contextmanager
import tempfile

from motion_studio.studio._contracts import StudioError
from motion_studio.studio._robot_assets import source_closure, RobotPosePreset

PIN = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
ROBOTS = {'g1': ('Unitree G1', 'unitree_g1'), 'k1': ('Booster K1', 'booster_k1'),
          'piplus': ('HiTorque PiPlus', 'hightorque_pipluspro'), 't800': ('EngineAI T800', 'engineai_t800')}
MOTIONS = {
    'hiphi-quick': ('HiPHI · 2s quick test', 'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz', {}),
    'hiphi-get-up': ('HiPHI · Get up', 'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz', {}),
    'adapt-tennis': ('ADAPT · Tennis', 'sample_data/adapt/duanxiran_fq2/source_motion.npz', {'up_axis': 'y'}),
}


def _verified(checkout, path):
    relative = path.relative_to(checkout).as_posix()
    try:
        original = subprocess.check_output(['git', '-C', str(checkout), 'show', f'{PIN}:{relative}'], stderr=subprocess.PIPE)
        if hashlib.sha256(original).digest() != hashlib.sha256(path.read_bytes()).digest():
            raise ValueError('bytes changed')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise StudioError('catalog_unavailable', f'Pinned example unavailable or changed: {relative}', 409) from error


def robot_source(checkout, key):
    if not isinstance(key, str) or key not in ROBOTS:
        raise StudioError('not_found', 'Built-in robot does not exist', 404)
    config = checkout / 'robot_configs' / f'humanoid_retarget_{ROBOTS[key][1]}_example.json'
    _verified(checkout, config)
    robot = json.loads(config.read_text())['robot']
    source = (config.parent / robot['xml']).resolve()
    _verified(checkout, source)
    return source, robot


@contextmanager
def portable_robot(checkout, key):
    """Rebase verified sibling dependencies for built-ins only; preserve originals.

    Custom imports retain the strict source-parent boundary. Every referenced
    original and its config is copied into provenance, including original XML.
    """
    source, config = robot_source(checkout, key)
    if key in ('g1', 'k1'):
        _, files = source_closure(source)
        for path in files.values():
            _verified(checkout, path)
        yield source, config, {}
        for path in files.values():
            _verified(checkout, path)
        robot_source(checkout, key)
        return
    tree = ET.parse(source)
    root = tree.getroot()
    if root.find('include') is not None:
        raise StudioError('catalog_unavailable', 'Built-in rebasing does not support includes', 409)
    compiler = root.find('compiler')
    directories = dict(compiler.attrib) if compiler is not None else {}
    originals = {'provenance/original.xml':source}
    with tempfile.TemporaryDirectory(prefix='studio-builtin-') as tmp:
        stage = Path(tmp)
        index = 0
        for node in root.iter():
            for field, name in list(node.attrib.items()):
                if field not in ('file','fileleft','fileright','fileup','filedown','filefront','fileback'):
                    continue
                directory = directories.get('assetdir', '')
                if node.tag in ('mesh','hfield'):
                    directory = directories.get('meshdir', directory)
                elif node.tag == 'texture':
                    directory = directories.get('texturedir', directory)
                original = (source.parent / directory / name).resolve()
                if not original.is_relative_to(source.parent.parent):
                    raise StudioError('catalog_unavailable', 'Built-in dependency escapes asset edition', 409)
                _verified(checkout, original)
                relative = f'files/{index:04d}-{original.name}'
                (stage / 'files').mkdir(exist_ok=True)
                shutil.copyfile(original, stage / relative)
                node.set(field, relative)
                originals['provenance/' + original.relative_to(source.parent.parent).as_posix()] = original
                index += 1
        if compiler is not None:
            for field in ('assetdir','meshdir','texturedir','strippath'):
                compiler.attrib.pop(field, None)
        portable = stage / source.name
        tree.write(portable)
        config_path = checkout / 'robot_configs' / f'humanoid_retarget_{ROBOTS[key][1]}_example.json'
        originals['provenance/preset.json'] = config_path
        note = stage / 'derivation.json'
        note.write_text(json.dumps({'source_revision':PIN, 'source_path':str(source.relative_to(checkout)),
            'conversion':'Rebased file references into a confined flat asset directory; original XML and dependencies preserved',
            'original_hashes':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in originals.items()}}, indent=2))
        checked_paths=tuple(originals.values())
        originals['provenance/derivation.json'] = note
        yield portable, config, originals
        for path in checked_paths:
            _verified(checkout, path)


def robot_preset(asset, robot):
    values = list(asset.default_qpos)
    for joint in asset.joints:
        values[joint.qpos_index] = robot['tpose_qpos'].get(joint.name, values[joint.qpos_index])
    torso = robot['point_cloud_center'].removeprefix('body:')
    return RobotPosePreset('Built-in T-pose', torso, tuple(values))


def motion_source(checkout, key):
    if not isinstance(key, str) or key not in MOTIONS:
        raise StudioError('not_found', 'Sample motion does not exist', 404)
    _, relative, metadata = MOTIONS[key]
    source = checkout / relative
    if key == 'adapt-tennis':
        _verified(checkout, checkout / 'robot_configs/humanoid_retarget_defaults_adapt.json')
    _verified(checkout, source)
    return source, metadata


def catalog(checkout):
    robots, motions = [], []
    for key, (name, _) in ROBOTS.items():
        path = checkout / 'robot_configs' / f'humanoid_retarget_{ROBOTS[key][1]}_example.json'
        robots.append({'id':key, 'name':name, 'available':path.is_file(), 'revision':PIN,
                       'description':'Pinned UMR model · named T-pose · local meshes'})
    for key, (name, relative, _) in MOTIONS.items():
        motions.append({'id':key, 'name':name, 'available':(checkout / relative).is_file(), 'revision':PIN,
                        'description':('2s excerpt · exact original frames / FPS · trim recorded' if key == 'hiphi-quick' else 'Full source clip · original FPS · CPU source preview')})
    return {'robots':robots, 'motions':motions, 'source':'Local pinned UMR examples; separate asset terms apply.'}


@contextmanager
def sample_source(checkout, key):
    source, metadata = motion_source(checkout, key)
    if key != 'hiphi-quick':
        yield source, metadata
        _verified(checkout, source)
        return
    import numpy as np
    with np.load(source, allow_pickle=False) as saved:
        fps = float(saved['fps'].item())
        stop = min(len(saved['poses']), round(fps * 2))
        with tempfile.TemporaryDirectory(prefix='studio-sample-') as tmp:
            output = Path(tmp) / 'hiphi_get_up_2s.npz'
            np.savez(output, poses=saved['poses'][:stop], trans=saved['trans'][:stop],
                     betas=saved['betas'], gender=saved['gender'], fps=fps,
                     coordinate_up=saved['coordinate_up'],
                     original_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                     original_source_path=str(source.relative_to(checkout)),
                     original_revision=PIN, original_frame_count=len(saved['poses']),
                     source_frame_start=0, source_frame_stop_exclusive=stop,
                     conversion='Trim exact source frames [0, stop); no resampling, scaling or coordinate conversion')
            yield output, metadata
            _verified(checkout, source)
