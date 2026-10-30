"""Validate a closed saved inspection and provide hash-checked read-only files."""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

from ._contracts import StudioError


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def confined_file(folder: Path, name: str) -> Path:
    if (not isinstance(name, str) or not name or '\\' in name
            or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts):
        raise StudioError('invalid_path', 'Inspection paths must be local relative files')
    path = (folder / name).resolve()
    if not path.is_relative_to(folder) or not path.is_file():
        raise StudioError('invalid_path', 'Inspection file is missing or escapes its registered root')
    return path


def inspect_bundle(folder: Path) -> dict[str, str]:
    """Inspect only the saved-viewer schema. No source reconstruction or upstream imports."""
    try:
        data = json.loads(confined_file(folder, 'bindings.json').read_text())
        motion, human = data['motion'], data['human_motion']
        count, fps = motion['frame_count'], motion['fps']
        if (type(count) is not int or count < 1 or not isinstance(fps, (int, float))
                or isinstance(fps, bool) or not math.isfinite(fps) or fps <= 0
                or human['frame_count'] != count or human['fps'] != fps
                or motion['frame_ids'] != list(range(count))):
            raise ValueError('Human and robot must have identical exact saved frame timelines')
        names = {'bindings.json', 'provenance.json', 'preservation.json'}
        for model in ('human', 'robot'):
            names.update(data['geometry'][model][key] for key in ('vertices', 'faces'))
        names.update(motion[key] for key in ('vertices', 'faces', 'transforms'))
        end = 0
        for chunk in human['chunks']:
            if chunk['start'] != end or type(chunk['count']) is not int or chunk['count'] < 1:
                raise ValueError('Human chunks must cover all frames in exact order')
            names.add(chunk['file'])
            end += chunk['count']
        if end != count:
            raise ValueError('Human chunks do not cover the saved timeline')
        for name in names - {'bindings.json', 'provenance.json', 'preservation.json'}:
            if not isinstance(name, str) or not name.endswith('.bin'):
                raise ValueError('Geometry and motion resources must be binary files')
        if (folder / 'export.log').is_file():
            names.add('export.log')
        return {name: digest(confined_file(folder, name)) for name in sorted(names)}
    except (KeyError, TypeError, ValueError, OSError) as error:
        if isinstance(error, StudioError):
            raise
        raise StudioError('invalid_inspection', f'Invalid saved inspection: {error}') from error
