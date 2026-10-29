"""Definition loading and static resolution; private to the robots interface."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

from . import Provenance, RobotSelection, RobotSelectionError, SourceFile
from ._model import inspect_model, validate_joints
from ._schema import conventions, read_json, resolve_pose


def relative_path(root, value):
    path = Path(value)
    if not value or path.is_absolute() or '..' in path.parts or '\\' in value:
        raise RobotSelectionError(f'Expected a source-relative path without escape: {value}')
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise RobotSelectionError(f'Source path escapes root through a link: {value}')
    return resolved


def resolve(identifier, representation, pose_name, roots, catalog):
    if not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', identifier):
        raise RobotSelectionError(f'Invalid definition ID: {identifier!r}')
    definition = read_json(relative_path(catalog.resolve(), identifier) / 'robot.json')
    poses = read_json(relative_path(catalog.resolve(), identifier) / 'poses.json')
    if definition['id'] != identifier or type(definition['version']) is not int or definition['version'] < 1:
        raise RobotSelectionError('Definition ID/version mismatch or invalid version')
    convention = conventions(definition['conventions'])
    if representation not in ('urdf', 'mjcf') or representation not in definition['representations']:
        raise RobotSelectionError(f'Unsupported representation {representation!r} for {identifier}')
    source = definition['source']
    if not re.fullmatch('[0-9a-f]{40}', source['revision']):
        raise RobotSelectionError('Source revision must be a full 40-character Git commit')
    if not isinstance(source['repository'], str) or not source['repository']:
        raise RobotSelectionError('Source repository must identify the upstream source')
    if source['key'] not in roots:
        raise RobotSelectionError(f"Supply source_roots[{source['key']!r}] for {source['repository']}")
    root = Path(roots[source['key']]).resolve()
    try:
        checkout = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-toplevel'],
                                          text=True, stderr=subprocess.PIPE).strip()
        revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                          text=True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError as error:
        raise RobotSelectionError(f'Required source checkout unavailable at {root}') from error
    if Path(checkout).resolve() != root:
        raise RobotSelectionError(f'Supply the source checkout root, not a subdirectory: {root}')
    if revision != source['revision']:
        raise RobotSelectionError(f"Source {source['key']} commit drift: expected "
                                  f"{source['revision']}, found {revision} at {root}")
    model = definition['representations'][representation]
    entries = model['files'] + definition['provenance']['files']
    files = []
    paths = [entry['path'] for entry in entries]
    if len(paths) != len(set(paths)):
        raise RobotSelectionError('Duplicate required source path in closure/provenance')
    provenance = definition['provenance']
    if not isinstance(provenance['license_coverage'], str) or not provenance['license_coverage']:
        raise RobotSelectionError('Record explicit provenance license_coverage, including unknowns')
    if not isinstance(provenance['modifications'], list) or not all(
            isinstance(item, str) for item in provenance['modifications']):
        raise RobotSelectionError('Provenance modifications must be an explicit list of descriptions')
    note = provenance.get('license_note', '')
    if not isinstance(note, str):
        raise RobotSelectionError('Provenance license_note must be text')
    provenance_result = Provenance(provenance['license_coverage'], note, tuple(provenance['modifications']))
    for entry in entries:
        path = relative_path(root, entry['path'])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry['sha256']:
            raise RobotSelectionError(f"Required source hash drift: {path}; expected "
                                      f"{entry['sha256']}, found {digest}")
        try:
            committed = subprocess.check_output(['git', '-C', str(root), 'show',
                f"{revision}:{entry['path']}"], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            raise RobotSelectionError(f"Required source not committed at {revision}: {entry['path']}") from error
        if hashlib.sha256(committed).hexdigest() != digest:
            raise RobotSelectionError(f"Required source differs from committed bytes: {entry['path']}")
        if not isinstance(entry['role'], str) or not entry['role']:
            raise RobotSelectionError(f"Required source role missing: {entry['path']}")
        files.append(SourceFile(entry['path'], path, digest, entry['role']))
    native, root_name, root_kind = inspect_model(root, model['model'], representation,
        [entry['path'] for entry in model['files']], relative_path)
    if root_name != definition['conventions']['root_frame'] or root_kind != model['root']:
        raise RobotSelectionError('Root frame/kind differs from selected model')
    joints = validate_joints(model, definition['joint_order'], native)
    values, root_pose, pose = resolve_pose(poses, pose_name, representation, joints)
    identity_data = {'definition': definition, 'pose_name': pose_name,
                     'pose': pose, 'representation': representation}
    identity = hashlib.sha256(json.dumps(identity_data, sort_keys=True,
                              separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return RobotSelection(identifier, definition['version'], representation, pose_name,
        source['key'], revision, source['repository'], provenance_result, root,
        relative_path(root, model['model']), tuple(files), joints,
        tuple(j.name for j in native), values,
        root_pose, model['root'], convention, identity,
        ('Required source closure hashes and pinned commit verified.',
         'Native joint metadata, application order, conventions and named pose validated.',
         f"Asset license coverage: {definition['provenance']['license_coverage']}.",
         'Runtime representation checks unverified; no simulator was loaded.'))
