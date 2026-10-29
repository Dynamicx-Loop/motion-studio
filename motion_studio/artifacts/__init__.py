"""Copy-first local evidence relocation, anchored to an independent inventory.

Operations accept explicit data roots; importing never discovers or changes data.
Archives remain local, with original terms. Modes resist accidental ordinary-user
writers; they are not protection from owners deliberately changing permissions.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
from typing import Sequence


class RelocationError(ValueError):
    """A conflict, drift or unsafe path prevented preservation work."""


def _hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def _identity(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _path(root: Path, relative: str, *, leaf_alias: bool = False) -> Path:
    name = PurePosixPath(relative)
    if not relative or name.is_absolute() or '..' in name.parts or str(name) != relative:
        raise RelocationError(f'Unsafe relative path: {relative}')
    path = root / relative
    for part in path.parents:
        if part == root.parent:
            break
        if part.is_symlink():
            raise RelocationError(f'Symlink traversal: {part}')
        if part == root:
            break
    if path.is_symlink() and not leaf_alias:
        raise RelocationError(f'Symlink traversal: {path}')
    return path


def _matches(path: Path, item: dict) -> bool:
    return path.is_file() and path.stat().st_size == item['bytes'] and _hash(path) == item['sha256']


def plan_relocation(workspace: Path, inventory: Path, inventory_sha256: str,
                    selection: Sequence[tuple[str, str]], destination: str) -> dict:
    """Return a dry plan for explicit (path, reviewed role) members; write nothing.

    Inventory hash is supplied by the caller's independent preservation anchor.
    Source paths must be ordinary workspace files; archive must be under outputs.
    """
    root = workspace.absolute()
    if _hash(inventory) != inventory_sha256:
        raise RelocationError('Independent inventory hash mismatch')
    if not destination.startswith('outputs/'):
        raise RelocationError('Archive must be under ignored outputs/')
    archive = _path(root, destination)
    if archive.exists():
        raise RelocationError(f'Destination collision: {archive}')
    originals = {r['path']: r for r in json.loads(inventory.read_text())['files'] if r.get('path')}
    files = []
    seen = set()
    for name, role in selection:
        if not name.startswith('experiments/') or name in seen:
            raise RelocationError(f'Invalid or duplicate experiment member: {name}')
        seen.add(name)
        source = _path(root, name)
        original = originals.get(name)
        if original is None or original.get('kind') != 'file' or not _matches(source, original):
            raise RelocationError(f'Source drift or unsealed file: {name}')
        target = f'{destination}/files/{name}'
        files.append({'source': name, 'destination': target, 'role': role,
                      'bytes': original['bytes'], 'sha256': original['sha256'],
                      'mode': stat.S_IMODE(source.stat().st_mode),
                      'inbound_references': original.get('inbound_references', []),
                      'compatibility': 'relative-symlink-readonly',
                      'alias_target': os.path.relpath(root / target, source.parent)})
    if not files:
        raise RelocationError('Empty selection')
    return {'schema_version': 1, 'workspace': str(root), 'archive': destination,
            'inventory': str(inventory.absolute()), 'inventory_sha256': inventory_sha256,
            'logical_bytes': sum(r['bytes'] for r in files),
            'temporary_duplicate_bytes': sum(r['bytes'] for r in files), 'files': files}


def _write(path: Path, value: dict) -> None:
    temporary = path.with_suffix('.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _load(receipt: Path) -> dict:
    if receipt.is_symlink():
        raise RelocationError('Receipt must not be a symlink')
    value = json.loads(receipt.read_text())
    if _identity(value['plan']) != value['plan_sha256']:
        raise RelocationError('Changed migration plan')
    return value


def _validate(plan: dict) -> tuple[Path, Path]:
    root = Path(plan['workspace'])
    if not plan['archive'].startswith('outputs/'):
        raise RelocationError('Archive must be under ignored outputs/')
    if _hash(Path(plan['inventory'])) != plan['inventory_sha256']:
        raise RelocationError('Independent inventory changed')
    archive = _path(root, plan['archive'])
    originals = {r.get('path'): r for r in json.loads(Path(plan['inventory']).read_text())['files']}
    for item in plan['files']:
        original = originals.get(item['source'], {})
        if any(original.get(k) != item[k] for k in ('sha256', 'bytes')):
            raise RelocationError('Plan differs from independent inventory')
        source = _path(root, item['source'], leaf_alias=True)
        target = _path(root, item['destination'])
        expected = archive / 'files' / item['source']
        if target != expected or not item['source'].startswith('experiments/'):
            raise RelocationError('Destination outside approved archive')
        if source.is_symlink() and (os.readlink(source) != item['alias_target'] or not _matches(target, item)):
            raise RelocationError(f'Unverified alias: {source}')
        if item['alias_target'] != os.path.relpath(target, source.parent):
            raise RelocationError('Changed alias target')
        if not _matches(source, item):
            raise RelocationError(f'Source drift: {source}')
        if target.exists() and not _matches(target, item):
            raise RelocationError(f'Archive drift: {target}')
    return root, archive


def relocate(plan: dict, *, resume: bool = False, step_limit: int | None = None) -> Path:
    """Copy/verify every member before atomically replacing individual old paths.

    A bounded step_limit supports staged operations. Resume revalidates the entire
    plan, sources and existing copies; completed aliases must match recorded links.
    A crash leaves originals or verified copies readable. No archive is deleted.
    """
    root, archive = _validate(plan)
    receipt = archive / 'relocation.json'
    if archive.exists():
        if not resume or not receipt.is_file() or _load(receipt)['plan'] != plan:
            raise RelocationError('Destination collision or stale resume receipt')
    else:
        if resume:
            raise RelocationError('Missing resume receipt')
        archive.mkdir(parents=True)
        _write(receipt, {'plan': plan, 'plan_sha256': _identity(plan), 'state': 'copying'})
    steps = 0
    for item in plan['files']:
        target = _path(root, item['destination'])
        if target.exists():
            continue
        if step_limit is not None and steps >= step_limit:
            return receipt
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.copying')
        if temporary.exists():
            # A known interrupted copy is disposable while the original is intact.
            if temporary.is_symlink():
                raise RelocationError('Unsafe partial copy')
            temporary.unlink()
        with (root / item['source']).open('rb') as source, temporary.open('xb') as output:
            shutil.copyfileobj(source, output, 1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        if not _matches(temporary, item):
            raise RelocationError(f'Copy mismatch: {temporary}')
        temporary.chmod(item['mode'] & ~0o222)
        os.replace(temporary, target)
        steps += 1
    # Check every copy again before the first source is replaced.
    for item in plan['files']:
        if not _matches(root / item['destination'], item):
            raise RelocationError('Incomplete archive')
    _validate(plan)
    for item in plan['files']:
        source = root / item['source']
        if source.is_symlink():
            continue
        if step_limit is not None and steps >= step_limit:
            return receipt
        temporary = source.with_name(source.name + '.relocation-link')
        if temporary.exists() or temporary.is_symlink():
            raise RelocationError(f'Alias staging collision: {temporary}')
        temporary.symlink_to(item['alias_target'])
        os.replace(temporary, source)
        steps += 1
    value = _load(receipt)
    value['state'] = 'aliased'
    _write(receipt, value)
    return receipt


def verify_relocation(receipt: Path) -> dict:
    """Check bytes through both names, alias identities and archive write bits."""
    value = _load(receipt)
    plan = value['plan']
    root, _ = _validate(plan)
    errors = []
    for item in plan['files']:
        target = root / item['destination']
        if not _matches(target, item):
            errors.append(f'Missing or changed archive: {target}')
        elif target.stat().st_mode & 0o222:
            errors.append(f'Writable archive: {target}')
    return {'passed': not errors, 'errors': errors, 'state': value['state'],
            'files': len(plan['files']), 'logical_bytes': plan['logical_bytes']}


def restore(receipt: Path) -> None:
    """Restore ordinary originals and recorded modes, retaining all archive copies."""
    value = _load(receipt)
    plan = value['plan']
    root, _ = _validate(plan)
    if not verify_relocation(receipt)['passed']:
        raise RelocationError('Cannot restore an unverified archive')
    for item in plan['files']:
        source = root / item['source']
        if not source.is_symlink():
            continue
        temporary = source.with_name(source.name + '.restoring')
        with (root / item['destination']).open('rb') as stream, temporary.open('xb') as output:
            shutil.copyfileobj(stream, output)
            output.flush()
            os.fsync(output.fileno())
        if not _matches(temporary, item):
            raise RelocationError('Restore mismatch')
        temporary.chmod(item['mode'])
        os.replace(temporary, source)
    value['state'] = 'restored'
    _write(receipt, value)
