"""Pinned, portable Astro assets from a deliberately selected menagerie_x checkout.

Snapshot creation reads Git-tracked source bytes without changing the checkout.
The built-in reader needs only the resulting root assets, never menagerie_x.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from motion_studio.studio._contracts import StudioError
from motion_studio.studio._robot_assets import RobotPosePreset


ASTRO_ROOT = Path(__file__).resolve().parents[2] / 'assets' / 'robots' / 'astro_p2'
SCHEMA = 'motion-studio-builtin-robot-v1'
ENTRY = 'astro_p2_studio.xml'
SOURCE_ENTRY = 'astro_p2.xml'
COLLISIONS = ('foot_collisions.xml', 'neck_handle_collisions.xml')
LICENSES = ('LICENSE', 'LICENSING.md', 'LICENSE.Unitree', 'LICENSE.Menagerie')


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file(root, name):
    if (not isinstance(name, str) or not name or Path(name).is_absolute()
            or any(part in ('', '.', '..') for part in name.split('/')) or '\\' in name):
        raise StudioError('invalid_builtin', 'Bundled assets must use confined relative paths', 409)
    path = Path(name)
    file = root / path
    if (not file.is_file() or not file.resolve().is_relative_to(root.resolve())
            or any(parent.is_symlink() for parent in (file, *file.parents) if parent.is_relative_to(root))):
        raise StudioError('catalog_unavailable', f'Bundled Astro file is missing or escapes its snapshot: {name}', 409)
    return file


def _xml(path):
    raw = path.read_bytes()
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('XML entities and document types are unsupported')
    return ET.fromstring(raw)


def _portable_xml(root):
    """Inline only Astro's geom-only collision attachments, preserving bodies.

    This deliberately bounded conversion rejects new attachment semantics rather
    than guessing. Original XML and meshes remain in the snapshot unchanged.
    """
    tree = _xml(root / SOURCE_ENTRY)
    if tree.tag != 'mujoco' or tree.get('model') != 'astro_p2':
        raise ValueError('Expected the default Astro P2 MJCF')
    compiler = tree.find('compiler')
    settings = ('angle', 'inertiafromgeom', 'fusestatic')
    models = {}
    declarations = tree.findall('./asset/model')
    if {node.get('file') for node in declarations} != set(COLLISIONS):
        raise ValueError('Expected the inspected Astro foot and neck collision models')
    for node in declarations:
        if set(node.attrib) != {'name', 'file'}:
            raise ValueError('Unsupported collision model declaration')
        model = _xml(_file(root, node.get('file')))
        other = model.find('compiler')
        if (model.tag != 'mujoco' or compiler is None or other is None
                or any(other.get(key) != compiler.get(key) for key in settings)
                or set(other.attrib) - set(settings)
                or any(child.tag not in {'compiler', 'worldbody'} for child in model)):
            raise ValueError('Collision submodel compiler/sections require a new inspected conversion')
        world = model.find('worldbody')
        if (world is None or any(child.tag not in {'body', 'geom'} for child in world.iter()
                                 if child is not world)
                or any(set(child.attrib) & {'file', 'class', 'childclass', 'mesh', 'hfield', 'material'}
                       for child in world.iter())
                or any(set(body.attrib) != {'name'} for body in world.iter('body'))):
            raise ValueError('Only the inspected named, untransformed geom-only collision bodies are supported')
        name = node.get('name')
        if not name or name in models:
            raise ValueError('Collision model names must be unique')
        models[name] = world
    for parent in list(tree.iter()):
        for child in list(parent):
            if child.tag != 'attach':
                continue
            if set(child.attrib) - {'model', 'body', 'prefix'} or child.get('model') not in models:
                raise ValueError('Unsupported collision attachment')
            world = models[child.get('model')]
            targets = list(world)
            if child.get('body'):
                targets = [body for body in world.findall('body') if body.get('name') == child.get('body')]
                if len(targets) != 1:
                    raise ValueError('Collision attachment body is missing or ambiguous')
            index = list(parent).index(child)
            parent.remove(child)
            for offset, original in enumerate(targets):
                replacement = copy.deepcopy(original)
                for node in replacement.iter():
                    if 'name' in node.attrib:
                        node.set('name', child.get('prefix', '') + node.get('name'))
                parent.insert(index + offset, replacement)
    for asset in tree.findall('asset'):
        for node in asset.findall('model'):
            asset.remove(node)
    tree.insert(0, ET.Comment(' SPDX-License-Identifier: Apache-2.0; owned collision-attachment expansion. '))
    encoded = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
    return b'\n'.join(line.rstrip() for line in encoded.splitlines()) + b'\n'


def snapshot_astro(checkout: Path, destination: Path) -> dict:
    """Copy the current committed default Astro closure to a fresh destination.

    The manifest records every source and generated SHA-256. Licensed source
    files must match HEAD; local edits require a deliberate source commit first.
    This does not fetch, modify external state, or advance old robot definitions.
    """
    checkout, destination = Path(checkout).resolve(), Path(destination).absolute()
    if destination.resolve().is_relative_to(checkout):
        raise ValueError('Snapshot destination must be outside the source checkout')
    if destination.exists():
        raise ValueError(f'Snapshot destination already exists: {destination}')
    source = checkout / 'astro_p2'
    tree = _xml(source / SOURCE_ENTRY)
    names = {SOURCE_ENTRY, *COLLISIONS, *LICENSES}
    compiler = tree.find('compiler')
    if compiler is None:
        raise ValueError('Expected explicit Astro compiler settings')
    for node in tree.findall('./asset/mesh'):
        names.add((Path(compiler.get('meshdir', '')) / node.attrib['file']).as_posix())
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    source_files = {}
    for name in sorted(names):
        path = _file(source, name)
        committed = subprocess.check_output(['git', '-C', str(checkout), 'show', f'{revision}:astro_p2/{name}'])
        source_files[name] = hashlib.sha256(committed).hexdigest()
        if _digest(path) != source_files[name]:
            raise ValueError(f'Source differs from committed revision {revision}: {name}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.astro-snapshot-', dir=destination.parent) as tmp:
        stage = Path(tmp) / 'snapshot'
        stage.mkdir()
        for name in source_files:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
            if _digest(target) != source_files[name]:
                raise ValueError(f'Source changed while copying: {name}')
        (stage / ENTRY).write_bytes(_portable_xml(stage))
        joints = {node.attrib['name']: 0.0 for node in tree.iter('joint') if node.get('type', 'hinge') != 'free'}
        tpose = {'left_shoulder_roll_joint': math.pi / 2, 'right_shoulder_roll_joint': -math.pi / 2,
                 'left_elbow_joint': math.pi / 2, 'right_elbow_joint': math.pi / 2}
        if not set(tpose).issubset(joints):
            raise ValueError('Astro T-pose joints differ from the inspected body')
        joints.update(tpose)
        manifest = {'schema': SCHEMA, 'id': 'astro', 'name': 'Astro P2', 'entry': ENTRY,
            'source': {'repository': 'https://github.com/notAnyrobot/menagerie_x', 'revision': revision,
                       'root': 'astro_p2', 'files_sha256': source_files},
            'derivation': {'method': 'Inline geom-only foot/neck collision model attachments, preserving body ownership and prefixes',
                           'source_units': 'metres; radians; Z-up; floating root quaternion wxyz',
                           'generated_files_sha256': {ENTRY: _digest(stage / ENTRY)}},
            'pose': {'name': 'Built-in T-pose', 'torso_body': 'waist_roll_link', 'joints': joints,
                     'root': 'Unchanged compiled default root; floor placement is display-only'}}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        stage.rename(destination)
    return manifest


def astro_catalog(root: Path | None = None) -> dict:
    root = Path(root) if root is not None else ASTRO_ROOT
    try:
        manifest = json.loads((root / 'manifest.json').read_text())
        revision = manifest['source']['revision']
    except (OSError, KeyError, ValueError, TypeError):
        revision = None
    return {'id': 'astro', 'name': 'Astro P2', 'revision': revision,
            'available': revision is not None and (root / ENTRY).is_file(),
            'description': 'Bundled menagerie_x model · 29 joints · named T-pose · local meshes'}


def _verified(root):
    try:
        manifest = json.loads(_file(root, 'manifest.json').read_text())
        if manifest['schema'] != SCHEMA or manifest['id'] != 'astro' or manifest['entry'] != ENTRY:
            raise ValueError('Unsupported Astro snapshot manifest')
        if (not {SOURCE_ENTRY, *COLLISIONS, *LICENSES}.issubset(manifest['source']['files_sha256'])
                or set(manifest['derivation']['generated_files_sha256']) != {ENTRY}):
            raise ValueError('Incomplete Astro source/derivation records')
        files = {**manifest['source']['files_sha256'], **manifest['derivation']['generated_files_sha256']}
        for name, expected in files.items():
            if _digest(_file(root, name)) != expected:
                raise ValueError(f'Bundled Astro bytes changed: {name}')
        if _file(root, ENTRY).read_bytes() != _portable_xml(root):
            raise ValueError('Bundled Astro conversion differs from its preserved source')
        return manifest
    except (OSError, KeyError, TypeError, ValueError, ET.ParseError) as error:
        raise StudioError('catalog_unavailable', f'Bundled Astro snapshot is unavailable: {error}', 409) from error


@contextmanager
def portable_astro(root: Path | None = None):
    """Return a verified, importable local MJCF and preserved source notices."""
    root = Path(root) if root is not None else ASTRO_ROOT
    manifest = _verified(root)
    originals = {'provenance/menagerie_x/' + name: root / name
                 for name in (SOURCE_ENTRY, *COLLISIONS, *LICENSES, 'manifest.json')}
    yield root / ENTRY, manifest['pose'], originals
    _verified(root)


def astro_pose(asset, pose) -> RobotPosePreset:
    if set(pose['joints']) != {joint.name for joint in asset.joints}:
        raise StudioError('catalog_unavailable', 'Astro preset and compiled joint names differ', 409)
    values = list(asset.default_qpos)
    for joint in asset.joints:
        values[joint.qpos_index] = pose['joints'][joint.name]
    return RobotPosePreset(pose['name'], pose['torso_body'], tuple(values))
