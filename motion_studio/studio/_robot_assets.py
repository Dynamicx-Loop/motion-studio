"""Confined MJCF source closure and isolated compiled-runtime transport."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from ._contracts import StudioError


@dataclass(frozen=True)
class RobotJoint:
    name: str
    minimum_rad: float
    maximum_rad: float
    qpos_index: int


@dataclass(frozen=True)
class RobotAsset:
    asset_id: str
    name: str
    root_body: str
    bodies: tuple[str, ...]
    joints: tuple[RobotJoint, ...]
    default_qpos: tuple[float, ...]
    derived: tuple[str, ...]
    runtime: str
    files: dict[str, str]
    source_entry: str = ''


@dataclass(frozen=True)
class RobotPose:
    pose_id: str
    asset_id: str
    name: str
    torso_body: str
    qpos: tuple[float, ...]
    units: str = 'metres; radians; root quaternion wxyz'


@dataclass(frozen=True)
class RobotPosePreset:
    """Unsaved pose values; loading changes no run or named-pose records."""
    name: str
    torso_body: str
    qpos: tuple[float, ...]
    units: str = 'metres; radians; root quaternion wxyz'


def decode_asset(data):
    return RobotAsset(**{**data, 'bodies': tuple(data['bodies']),
        'joints': tuple(RobotJoint(**x) for x in data['joints']),
        'default_qpos': tuple(data['default_qpos']), 'derived': tuple(data['derived'])})


def hash_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def runtime(python, request):
    try:
        result = subprocess.run([str(python), '-B', str(Path(__file__).with_name('_robot_worker.py'))],
            input=json.dumps(request, allow_nan=False), capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise StudioError('robot_runtime', f'Pinned robot compiler unavailable: {error}', 409) from error
    if result.returncode:
        raise StudioError('invalid_robot', result.stderr.strip()[-3000:] or 'Robot compilation failed')
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise StudioError('robot_runtime', 'Robot compiler returned invalid metadata', 409) from error


def source_closure(source):
    """Expand includes using MJCF main-file-relative semantics, preserving originals."""
    source = Path(source)
    if not source.is_absolute() or source.is_symlink():
        raise StudioError('invalid_robot_path', 'Use an absolute regular MJCF file, not a symlink')
    root = source.parent.resolve()
    files, active = {}, set()

    def locate(name):
        value = Path(name)
        if value.is_absolute() or '..' in value.parts or not name:
            raise StudioError('invalid_robot_path', f'Escaping/absolute dependency: {name}')
        path = root / value
        if not path.resolve().is_relative_to(root) or path.is_symlink() or not path.is_file():
            raise StudioError('invalid_robot_path', f'Missing or escaping dependency: {name}')
        files[value.as_posix()] = path
        return path

    def parse(name):
        path = locate(name)
        if path in active:
            raise StudioError('invalid_robot_path', f'Cyclic MJCF include: {name}')
        active.add(path)
        raw = path.read_bytes()
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
            raise StudioError('invalid_robot', 'XML entities and document types are unsupported')
        try:
            tree = ET.fromstring(raw)
        except ET.ParseError as error:
            raise StudioError('invalid_robot', f'Invalid MJCF XML: {error}') from error
        for parent in list(tree.iter()):
            for index, child in reversed(list(enumerate(list(parent)))):
                if child.tag == 'include':
                    included = parse(child.get('file', ''))
                    parent.remove(child)
                    for replacement in reversed(list(included)):
                        parent.insert(index, replacement)
        active.remove(path)
        return tree

    tree = parse(source.name)
    if tree.tag != 'mujoco':
        raise StudioError('invalid_robot', 'Expected an MJCF mujoco root')
    compiler = {}
    for node in tree.findall('compiler'):
        compiler.update(node.attrib)
    for key in ('meshdir', 'texturedir', 'assetdir'):
        path = Path(compiler.get(key, ''))
        if path.is_absolute() or '..' in path.parts:
            raise StudioError('invalid_robot_path', f'Escaping compiler {key}')
    for node in tree.iter():
        if node.tag in {'plugin', 'extension', 'attach', 'model', 'skin', 'flexcomp'}:
            raise StudioError('invalid_robot', f'Unsupported MJCF element: {node.tag}')
        for key, name in node.attrib.items():
            if key not in {'file', 'fileleft', 'fileright', 'fileup', 'filedown', 'filefront', 'fileback'}:
                continue
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise StudioError('invalid_robot_path', f'Escaping/absolute dependency: {name}')
            if compiler.get('strippath') == 'true':
                name = Path(name).name
            folder = compiler.get('assetdir', '')
            if node.tag in {'mesh', 'hfield'}:
                folder = compiler.get('meshdir', folder)
            elif node.tag == 'texture':
                folder = compiler.get('texturedir', folder)
            locate(str(Path(folder) / name))
    return tree, files


def import_asset(assets_root, python, source, derive_free_root, existing_asset):
    tree, sources = source_closure(source)
    fingerprint = {name: hash_file(path) for name, path in sorted(sources.items())}
    identity = hashlib.sha256(json.dumps({'schema': 'studio-robot-v1', 'files': fingerprint, 'entry': Path(source).name,
        'derive_free_root': derive_free_root}, sort_keys=True).encode()).hexdigest()
    home = assets_root / 'robots' / identity
    if home.exists():
        return existing_asset(identity)
    home.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=home.parent) as tmp:
        stage = Path(tmp)
        for name, path in sources.items():
            target = stage / 'source' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            if hash_file(target) != fingerprint[name]:
                raise StudioError('changed_robot_source', 'Robot source changed during import', 409)
        # Expanded derived XML sits beside its copied assets; source bytes remain intact.
        model = stage / 'source' / '__studio_model.xml'
        if model.name in sources:
            raise StudioError('invalid_robot', 'Reserved filename __studio_model.xml')
        model.write_bytes(ET.tostring(tree))
        result = runtime(python, {'operation': 'import', 'model': str(model),
            'derive_free_root': derive_free_root, 'geometry': str(stage / 'geometry.json')})
        record = RobotAsset(identity, Path(source).stem, result['root_body'], tuple(result['bodies']),
            tuple(RobotJoint(**x) for x in result['joints']), tuple(result['default_qpos']),
            tuple(result['derived']), result['runtime'], {}, source_entry=Path(source).name)
        stored = {p.relative_to(stage).as_posix(): hash_file(p)
                  for p in stage.rglob('*') if p.is_file()}
        record = RobotAsset(**{**record.__dict__, 'files': stored})
        (stage / 'asset.json').write_text(json.dumps(asdict(record), allow_nan=False))
        # Atomic publish; no mutation of an existing hash-identified version.
        try:
            stage.rename(home)
        except OSError:
            if not (home / 'asset.json').is_file():
                raise
    return record
