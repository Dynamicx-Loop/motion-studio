"""Strict JSON and streaming hashes, with exclusively created output bundles."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from motion_studio.motion_data_paths import canonical_motion_path


def read_json(path: Path) -> Any:
    def invalid(value: str) -> None:
        raise ValueError(f"Nonfinite JSON number in {path}: {value}")

    def unique(pairs: list[tuple[str, Any]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(), parse_constant=invalid, object_pairs_hook=unique)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, root: Path) -> dict:
    absolute = path.absolute()
    return {'path': str(absolute.relative_to(root)) if absolute.is_relative_to(root)
            else str(absolute), 'sha256': sha256(path), 'bytes': path.stat().st_size}


def resolve(root: Path, path: str) -> Path:
    value = Path(path).expanduser()
    return canonical_motion_path(value if value.is_absolute() else root / value)


def write_json(path: Path, data: Any) -> None:
    # No overwrite option: a new run/reconstruction always gets a new directory.
    with path.open('x') as stream:
        stream.write(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n')


def seal(directory: Path, sources: list[dict], root: Path) -> None:
    outputs = [file_record(p, directory) for p in sorted(directory.rglob('*'))
               if p.is_file()]
    write_json(directory / 'manifest.json', {
        'schema_version': 1, 'workspace_at_creation': str(root),
        'sources': sources, 'outputs': outputs,
        'policy': 'Content hashes detect edits; local filesystem is not write-once storage.'})


def verify_bundle(directory: Path, root: Path) -> dict:
    manifest = read_json(directory / 'manifest.json')
    errors = []
    for group, base in [('sources', root), ('outputs', directory)]:
        for item in manifest[group]:
            path = resolve(base, item['path'])
            if group == 'outputs' and not path.resolve().is_relative_to(directory.resolve()):
                errors.append(f"Output escapes bundle: {item['path']}")
                continue
            if not path.is_file():
                errors.append(f"Missing {group}: {item['path']}")
            elif sha256(path) != item['sha256']:
                errors.append(f"Changed {group}: {item['path']}")
    expected = {i['path'] for i in manifest['outputs']} | {'manifest.json'}
    actual = {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}
    errors.extend(f'Unsealed output: {p}' for p in sorted(actual - expected))
    return {'passed': not errors, 'errors': errors,
            'source_files': len(manifest['sources']), 'output_files': len(manifest['outputs'])}


def implementation_sources(root: Path) -> list[dict]:
    """Hash the executing owned code/schema closure, independently of input root."""
    folder = Path(__file__).resolve().parent
    workspace = folder.parents[1]
    paths = [*sorted(folder.glob('*.py')), workspace / 'motion_studio/__init__.py',
             workspace / 'motion_studio/motion_data_paths.py',
             workspace / 'schemas/experiments/plan.schema.json',
             workspace / 'schemas/experiments/result.schema.json']
    return [file_record(path, root) for path in paths]


def record_implementation(destination: Path, sources: list[dict]) -> None:
    write_json(destination / 'implementation.json', {
        'schema_version': 1, 'operation_package': 'motion_studio.evidence',
        'migration': 'Owned evidence implementation replaces scripts/experiment_support; '
                     'pure static rules extracted from experiments/umr-binding-report/build_report.py. '
                     'Historical manifests and original records are not rewritten.',
        'sources': sources})
