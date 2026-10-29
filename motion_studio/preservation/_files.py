"""File records for the preservation receipt; no directory-symlink traversal."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

SECRET_PARTS = {'.git', '.aws', '.codex', '.agents', '.ssh', '.gnupg', '.vscode', '.local'}
ENVIRONMENT_PARTS = {'.venv', 'venv', 'node_modules', '__pycache__', 'cache', 'tmp'}
TEXT_SUFFIXES = {'.py', '.md', '.json', '.csv', '.patch', '.html', '.js', '.cjs', '.css',
                 '.yaml', '.yml', '.toml', '.ini', '.txt', '.xml', '.urdf', '.sh', '.bib'}
GENERATED_SUFFIXES = {'.npz', '.npy', '.pt', '.pth', '.bin', '.png', '.jpg', '.jpeg',
                      '.webp', '.gif', '.mp4', '.stl', '.obj', '.ply', '.pkl', '.zip'}


def secret(path: Path) -> bool:
    return (any(p in SECRET_PARTS for p in path.parts)
            or any(p.startswith('.env') or p in {'.netrc', '.npmrc', 'credentials'} for p in path.parts))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def display(path: Path, workspace: Path) -> str:
    return str(path.relative_to(workspace)) if path.is_relative_to(workspace) else str(path)


def role(path: Path, workspace: Path) -> str:
    relative = display(path, workspace)
    if relative.startswith('outputs/') or path.suffix.lower() in GENERATED_SUFFIXES:
        return 'generated'
    if path.suffix.lower() == '.json' and path.stat().st_size > 1024 * 1024:
        return 'generated'
    if relative in {'docs.html', 'docs-basic.html', 'docs/site/home.html'}:
        return 'generated'
    if path.suffix.lower() in {'.json', '.csv'} and relative.startswith('experiments/'):
        return 'small-result'
    return 'source'


def record(path: Path, workspace: Path) -> dict:
    info = path.lstat()
    item = {'path': display(path, workspace), 'absolute_path': str(path),
            'kind': 'symlink' if path.is_symlink() else 'file', 'lstat_bytes': info.st_size,
            'device': info.st_dev, 'inode': info.st_ino, 'role': role(path, workspace),
            'cohort': None, 'inbound_references': []}
    parts = Path(item['path']).parts
    if len(parts) > 1 and parts[0] in {'experiments', 'outputs'}:
        item['cohort'] = parts[1]
    if path.is_symlink():
        item['symlink_target'] = os.readlink(path)
    if path.is_file() and not secret(path.resolve()):
        before = path.stat()
        item.update(bytes=before.st_size, sha256=sha256(path))
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError(f'Source changed while hashing: {path}')
    return item


def walk(root: Path, destination: Path, *, skip_externals: bool = False):
    for folder, directories, files in os.walk(root, followlinks=False):
        base = Path(folder)
        kept = []
        for name in sorted(directories):
            child = base / name
            if child == destination or secret(child.relative_to(root)) or name in ENVIRONMENT_PARTS:
                continue
            if skip_externals and child == root / 'externals':
                continue
            if child.is_symlink():
                yield child
            else:
                kept.append(name)
        directories[:] = kept
        for name in sorted(files):
            child = base / name
            if child != destination and not secret(child.relative_to(root)):
                yield child


def metadata(path: Path) -> dict:
    item = {'absolute_path': str(path), 'exists': path.exists(),
            'kind': 'symlink' if path.is_symlink() else 'directory' if path.is_dir() else 'file'}
    if path.exists() or path.is_symlink():
        item['lstat_bytes'] = path.lstat().st_size
    if path.is_symlink():
        item['symlink_target'] = os.readlink(path)
    return item
