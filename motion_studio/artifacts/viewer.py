"""Static saved robot-viewer graph and binary shape verification."""
import json
from pathlib import Path, PurePosixPath
import re


def verify_saved_viewer(directory: Path) -> dict:
    """Check legacy robot viewer JSON/resources; does not establish WebGL behavior."""
    manifest = json.loads((directory / 'manifest.json').read_text())
    resources = set()
    errors = []

    def resource(name):
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            errors.append(f'Unsafe resource: {name}')
            return None
        path = directory / name
        resources.add(name)
        if not path.is_file():
            errors.append(f'Missing resource: {name}')
            return None
        return path

    for robot in manifest['robots'].values():
        for part in robot['parts']:
            for key in ('vertices', 'faces'):
                path = resource(part[key])
                if path is not None and path.stat().st_size % 12:
                    errors.append(f'Invalid float32 triangle/vertex size: {part[key]}')
        expected = manifest['frames'] * len(robot['parts']) * 12 * 4
        for variant in robot['variants']:
            path = resource(variant['transforms'])
            if path is not None and path.stat().st_size != expected:
                errors.append(f'Transform byte count: {variant["transforms"]}')
    # Saved source templates import only relative JS modules. Check recursively.
    pending = [p for p in ('index.html', 'app.js') if (directory / p).is_file()]
    checked = set()
    while pending:
        name = pending.pop()
        if name in checked:
            continue
        checked.add(name)
        path = resource(name)
        if path is None:
            continue
        for link in re.findall(r'''["'](\./[^"']+)["']''', path.read_text()):
            child = str(PurePosixPath(name).parent / link)
            if resource(child) is not None and child.endswith('.js'):
                pending.append(child)
    return {'passed': not errors, 'errors': errors, 'frames': manifest['frames'],
            'fps': manifest['fps'], 'robots': {n: len(r['parts']) for n, r in manifest['robots'].items()},
            'resources': sorted(resources), 'static_only': True}
