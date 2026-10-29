"""Sealed, read-only inventory of workspace evidence and dirty Git source.

Capture writes only to a fresh receipt directory. Verification reports drift;
receipt hashes detect changes but do not make a filesystem write-once storage.
Ignored environments/assets are located, not fully backed up or rebuilt.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping, Sequence
import re
import subprocess

from ._files import metadata, record, sha256, walk
from ._git import capture_repository, git
from ._references import input_closure, link_references


@dataclass(frozen=True)
class InventoryResult:
    receipt: Path
    manifest_sha256: str


@dataclass(frozen=True)
class InventoryVerification:
    passed: bool
    errors: tuple[str, ...]
    source_files: int
    repositories: int


def _write(path: Path, value: object) -> None:
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def capture_inventory(workspace: Path, destination: Path, *,
                      repositories: Mapping[str, Path] | None = None,
                      compatibility_roots: Sequence[Path] = (),
                      source_roots: Sequence[Path] = ()) -> InventoryResult:
    """Capture owned evidence plus named/discovered Git repositories, without mutation."""
    workspace, destination = workspace.resolve(), destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Inventory requires a fresh directory: {destination}')
    roots = {'workspace': workspace}
    externals = workspace / 'externals'
    if externals.is_dir():
        roots.update({p.name: p for p in externals.iterdir() if (p / '.git').exists()})
    roots.update({name: p.resolve() for name, p in (repositories or {}).items()})
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', name) for name in roots):
        raise ValueError('Repository identifiers must contain only letters, digits, underscores or hyphens')
    allowed_roots = [*roots.values(), *(p.resolve() for p in source_roots),
                     *(p.resolve() for p in compatibility_roots)]
    destination.mkdir(parents=True, exist_ok=False)
    repos = [capture_repository(root, destination / 'recovery' / name, name)
             for name, root in roots.items()]
    files = [record(path, workspace) for path in walk(workspace, destination, skip_externals=True)]
    for item in repos:
        base = Path(item['root'])
        if base == workspace:
            continue
        for name in item['recovery']['tracked_paths'] + item['recovery']['untracked_source_paths']:
            path = base / name
            if path.is_file() or path.is_symlink():
                files.append(record(path, workspace))
    lookup = {item['absolute_path']: item for item in files}
    closure = []
    for path, expected, evidence in input_closure(files, workspace):
        if not any(path.resolve().is_relative_to(root.resolve()) for root in allowed_roots):
            closure.append({'path': str(path), 'expected_sha256': expected, 'evidence': evidence,
                            'matches': False, 'available': False, 'reason': 'Outside explicit source roots'})
            continue
        key = str(path)
        if path.is_file() and key not in lookup:
            lookup[key] = record(path, workspace)
            lookup[key]['role'] = 'frozen-source'
        closure.append({'path': key, 'expected_sha256': expected, 'evidence': evidence,
                        'matches': lookup.get(key, {}).get('sha256') == expected,
                        'available': path.is_file()})
    files = list(lookup.values())
    link_references(files, workspace)
    unique = {(item['device'], item['inode']): item.get('bytes', 0)
              for item in files if item['kind'] == 'file'}
    storage = {'logical_file_bytes': sum(item.get('bytes', 0) for item in files),
               'unique_stored_file_bytes': sum(unique.values())}
    compatibility = []
    for location in compatibility_roots:
        location = location.absolute()
        compatibility.append({**metadata(location), 'entries': [metadata(p) for p in sorted(location.iterdir())]
                              if location.is_dir() else []})
    manifest = {'schema_version': 1, 'workspace': str(workspace),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_roots': [str(p) for p in allowed_roots],
                'storage': storage, 'frozen_reference_checks': closure,
                'files': sorted(files, key=lambda item: item['absolute_path']),
                'repositories': repos, 'compatibility': compatibility,
                'limitations': ['Ignored assets/environments are not backed up or rebuilt.',
                                'Git object databases remain at their original locations.']}
    _write(destination / 'inventory.json', manifest)
    outputs = [{'path': str(p.relative_to(destination)), 'sha256': sha256(p)}
               for p in sorted(destination.rglob('*')) if p.is_file()]
    _write(destination / 'seal.json', {'schema_version': 1, 'outputs': outputs})
    return InventoryResult(destination, sha256(destination / 'inventory.json'))


def verify_inventory(receipt: Path) -> InventoryVerification:
    """Report source/payload/Git drift without changing the sealed receipt."""
    manifest = json.loads((receipt / 'inventory.json').read_text())
    seal = json.loads((receipt / 'seal.json').read_text())
    errors = []
    for item in seal['outputs']:
        path = receipt / item['path']
        if not path.resolve().is_relative_to(receipt.resolve()) or not path.is_file() or sha256(path) != item['sha256']:
            errors.append(f"Changed receipt payload: {item['path']}")
    expected_payloads = {item['path'] for item in seal['outputs']} | {'seal.json'}
    actual_payloads = {str(p.relative_to(receipt)) for p in receipt.rglob('*') if p.is_file() or p.is_symlink()}
    errors.extend(f'Unsealed receipt payload: {p}' for p in sorted(actual_payloads - expected_payloads))
    if errors:
        return InventoryVerification(False, tuple(errors), 0, 0)
    workspace = Path(manifest['workspace'])
    expected_owned = {item['absolute_path'] for item in manifest['files']
                      if Path(item['absolute_path']).is_relative_to(workspace)
                      and not Path(item['absolute_path']).is_relative_to(workspace / 'externals')}
    actual_owned = {str(p) for p in walk(workspace, receipt.absolute(), skip_externals=True)}
    errors.extend(f'New unrecorded source: {p}' for p in sorted(actual_owned - expected_owned))
    for item in manifest['files']:
        path = Path(item['absolute_path'])
        if path.exists() and path.is_symlink() != (item['kind'] == 'symlink'):
            errors.append(f"Changed source kind: {item['absolute_path']}")
        if item['kind'] == 'symlink' and (not path.is_symlink() or os.readlink(path) != item['symlink_target']):
            errors.append(f"Changed symlink target: {item['absolute_path']}")
        if path.is_symlink() and not path.exists():
            errors.append(f"Broken symlink: {item['absolute_path']}")
        if 'sha256' in item and (not path.is_file() or sha256(path) != item['sha256']):
            errors.append(f"Changed or missing source: {item['absolute_path']}")
    for location in manifest['compatibility']:
        for item in [location, *location['entries']]:
            path = Path(item['absolute_path'])
            if item.get('symlink_target') is not None and (not path.is_symlink() or os.readlink(path) != item['symlink_target']):
                errors.append(f'Changed compatibility symlink: {path}')
            if not path.exists():
                errors.append(f'Missing or broken compatibility path: {path}')
    for item in manifest['repositories']:
        root = Path(item['root'])
        try:
            if git(root, 'rev-parse', 'HEAD').decode().strip() != item['head']:
                errors.append(f"Changed HEAD: {root}")
            if git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all').decode() != item['status_porcelain_z']:
                errors.append(f"Changed Git status: {root}")
            allowed = item['recovery']['tracked_paths']
            patch = git(root, 'diff', '--binary', '--no-ext-diff', '--no-renames', item['head'], '--', *allowed) if allowed else b''
            if hashlib.sha256(patch).hexdigest() != item['recovery']['patch_sha256']:
                errors.append(f'Changed tracked patch: {root}')
        except (OSError, subprocess.CalledProcessError) as error:
            errors.append(f'Repository unavailable: {root}: {error}')
    return InventoryVerification(not errors, tuple(errors), len(manifest['files']), len(manifest['repositories']))
