"""Prepare fresh outputs from sealed legacy settings without executing UMR.

This is a local preparation receipt, not a claim of historical numerical parity.
The selected model bytes are explicitly those in the preservation inventory.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from motion_studio.artifacts import RelocationError, _hash, _identity, _matches, _path, _write


def prepare_legacy_run(workspace: Path, inventory: Path, inventory_sha256: str,
                       destination: str, interpreter: Path) -> dict:
    """Materialize four configs, verified model/mesh closures and exact commands.

    Never invokes the old runner/exporter, UMR, simulator or training. Read inputs
    stay at their sealed locations. Every generated path and model XML is run-local.
    Missing/drifted closure is an error before run creation, never a substitution.
    """
    root = workspace.absolute()
    if _hash(inventory) != inventory_sha256:
        raise RelocationError('Independent inventory hash mismatch')
    if not destination.startswith('outputs/'):
        raise RelocationError('Fresh run must be under outputs/')
    run = _path(root, destination)
    if run.exists():
        raise RelocationError('Fresh run destination collision')
    records = {r['absolute_path']: r for r in json.loads(inventory.read_text())['files']
               if r.get('absolute_path') and r.get('sha256')}
    inputs = {}

    def sealed(path):
        path = Path(path).absolute()
        record = records.get(str(path))
        if record is None or not _matches(path, record):
            raise RelocationError(f'Missing or drifted frozen input: {path}')
        inputs[str(path)] = record['sha256']
        return path

    def closure(xml):
        base = xml.parent
        selected = {xml}
        pending = [xml]
        while pending:
            current = pending.pop()
            document = ET.parse(sealed(current)).getroot()
            compiler = document.find('compiler')
            meshdir = compiler.get('meshdir', '') if compiler is not None else ''
            texturedir = compiler.get('texturedir', '') if compiler is not None else ''
            for node in document.iter():
                filename = node.get('file')
                if not filename:
                    continue
                prefix = meshdir if node.tag == 'mesh' else texturedir if node.tag == 'texture' else ''
                member = (current.parent / prefix / filename).absolute()
                if not member.resolve().is_relative_to(base.resolve()) or member.is_symlink():
                    raise RelocationError(f'Unsafe model closure: {member}')
                sealed(member)
                if member not in selected:
                    selected.add(member)
                    if node.tag == 'include':
                        pending.append(member)
                if member.suffix.lower() == '.obj':
                    for line in member.read_text().splitlines():
                        if line.startswith('mtllib '):
                            material = member.parent / line.split(maxsplit=1)[1]
                            sealed(material)
                            selected.add(material)
            # Local notices travel with the closure, retaining unknown terms.
        for candidate in base.iterdir():
            if candidate.is_file() and candidate.name.lower().startswith(('license', 'notice', 'readme')):
                sealed(candidate)
                selected.add(candidate)
        return sorted(selected)

    sealed(root / 'externals/UMR/scripts/humanoid_retarget_pipeline.py')
    viewer_sources = [sealed(root / 'scripts/hiphi-robot-viewer' / name) for name in ('index.html', 'app.js')]
    configs, models = {}, {}
    for robot in ('astro', 'g1'):
        for variant in ('reference', 'reconverted'):
            name = f'{robot}-{variant}'
            original = sealed(root / f'experiments/hiphi-robot-control/configs/{name}-resolved.json')
            config = json.loads(original.read_text())
            xml = sealed(Path(config['robot']['xml']))
            if robot in models and models[robot][0] != xml:
                raise RelocationError('Variant model closure mismatch')
            models[robot] = (xml, closure(xml))
            motion = Path(config['motion']['data'])
            if not motion.is_absolute():
                motion = root / 'externals/UMR' / motion
            sealed(motion)
            config['motion']['data'] = str(motion)
            # Resolved historical files contain UMR-root-relative read paths.
            for key in ('smplx_model_dir', 'soma_usd_path'):
                if config.get(key) and not Path(config[key]).is_absolute():
                    config[key] = str(root / 'externals/UMR' / config[key])
            for spec in config['correspondence']['dataset'].get('smpl_models', []):
                if spec.get('dir') and not Path(spec['dir']).is_absolute():
                    spec['dir'] = str(root / 'externals/UMR' / spec['dir'])
            config['robot']['xml'] = str(run / 'assets' / robot / xml.name)
            config['correspondence']['dataset']['out'] = str(run / robot / 'correspondence.npz')
            config['correspondence']['train']['out_dir'] = str(run / robot / 'training')
            config['correspondence']['slots'] = None
            config['correspondence']['shared_config'] = None
            config['correspondence']['shared_smplx_template'] = None
            config['retarget']['out'] = str(run / robot / f'{variant}.npz')
            configs[name] = config
    run.mkdir(parents=True)
    copied = []
    for robot, (xml, members) in models.items():
        for source in members:
            target = run / 'assets' / robot / source.relative_to(xml.parent)
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as stream, target.open('xb') as output:
                shutil.copyfileobj(stream, output)
            if _hash(target) != inputs[str(source)]:
                raise RelocationError(f'Copy mismatch: {target}')
            copied.append({'source': str(source), 'destination': str(target), 'sha256': _hash(target)})
    viewer_files = []
    for source in viewer_sources:
        target = run / 'viewer' / source.name
        target.parent.mkdir(exist_ok=True)
        with source.open('rb') as stream, target.open('xb') as output:
            shutil.copyfileobj(stream, output)
        if _hash(target) != inputs[str(source)]:
            raise RelocationError('Viewer source copy mismatch')
        viewer_files.append({'source': str(source), 'destination': str(target), 'sha256': _hash(target)})
    commands = []
    for name, config in configs.items():
        path = run / 'configs' / f'{name}.json'
        path.parent.mkdir(exist_ok=True)
        _write(path, config)
        commands.append({'argv': [str(interpreter), str(root / 'externals/UMR/scripts/humanoid_retarget_pipeline.py'),
                                  '--config', str(path), '--skip-view'],
                         'cwd': str(root / 'externals/UMR'), 'stdout': str(run / f'{name}.log'),
                         'config_sha256': _hash(path)})
    receipt = {'schema_version': 1, 'state': 'prepared-only', 'inventory_sha256': inventory_sha256,
               'inputs': inputs, 'models': copied, 'commands': commands,
               'viewer': {'destination': str(run / 'viewer'), 'templates': viewer_files,
                          'state': 'source-templates-only; geometry/manifest export not executed'},
               'identity': _identity({'inputs': inputs, 'configs': configs}),
               'limitations': ['No pipeline, training, export or simulator was executed.',
                               'Model closure matches the inventory seal; no historical numerical parity claim.',
                               'Human model/runtime availability is a prerequisite for execution.',
                               'Use a new explicit viewer destination; the historical exporter is unsafe.']}
    _write(run / 'preparation.json', receipt)
    return receipt
