"""Capture reconstructable dirty source without editing a live Git checkout."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

from ._files import ENVIRONMENT_PARTS, TEXT_SUFFIXES, secret, sha256


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)


def names(root: Path, *args: str) -> list[str]:
    return [p.decode() for p in git(root, *args).split(b'\0') if p]


def capture_repository(root: Path, payload: Path, identifier: str) -> dict:
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    status = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    changed = names(root, 'diff', '--name-only', '--no-renames', '-z', head)
    allowed = [p for p in changed if not secret(Path(p))]
    payload.mkdir(parents=True)
    patch = payload / 'tracked.patch'
    patch.write_bytes(git(root, 'diff', '--binary', '--no-ext-diff', '--no-renames', head,
                         '--', *allowed) if allowed else b'')
    untracked = names(root, 'ls-files', '--others', '--exclude-standard', '-z')
    recover = [p for p in untracked if not secret(Path(p))
               and not any(part in ENVIRONMENT_PARTS for part in Path(p).parts)
               and (root / p).suffix.lower() in TEXT_SUFFIXES
               and (root / p).is_file() and (root / p).stat().st_size <= 4 * 1024 * 1024]
    archive = payload / 'untracked-source.tar'
    with tarfile.open(archive, 'w') as tar:
        for name in recover:
            tar.add(root / name, arcname=name, recursive=False)
    recovery_errors = []
    with tempfile.TemporaryDirectory(prefix='motion-studio-recovery-') as temporary:
        restored = Path(temporary)
        for name in allowed:
            listing = git(root, 'ls-tree', head, '--', name).decode()
            if not listing:
                continue
            target = restored / name
            target.parent.mkdir(parents=True, exist_ok=True)
            original = git(root, 'show', f'{head}:{name}')
            if listing.startswith('120000 '):
                target.symlink_to(original.decode())
            else:
                target.write_bytes(original)
        if patch.stat().st_size:
            subprocess.run(['git', 'apply', '--check', str(patch)], cwd=restored, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['git', 'apply', str(patch)], cwd=restored, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for name in allowed:
            source, target = root / name, restored / name
            if source.is_file() and (not target.is_file() or sha256(source) != sha256(target)):
                recovery_errors.append(name)
            elif not source.exists() and target.exists():
                recovery_errors.append(name)
        with tarfile.open(archive) as tar:
            for name in recover:
                member = tar.getmember(name)
                if member.issym():
                    if member.linkname != os.readlink(root / name):
                        recovery_errors.append(name)
                else:
                    target = restored / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read())
                    if sha256(target) != sha256(root / name):
                        recovery_errors.append(name)
    ignored = names(root, 'ls-files', '--others', '--ignored',
                    '--exclude-standard', '--directory', '-z')
    ignored_entries = []
    for name in ignored:
        path = root / name.rstrip('/')
        entry = {'path': name, 'absolute_path': str(path), 'exists': path.exists(),
                 'kind': 'symlink' if path.is_symlink() else 'directory' if path.is_dir() else 'file'}
        if path.exists() or path.is_symlink():
            entry['lstat_bytes'] = path.lstat().st_size
        if path.is_symlink():
            entry['symlink_target'] = os.readlink(path)
        ignored_entries.append(entry)
    return {'id': identifier, 'root': str(root), 'head': head,
            'status_porcelain_z': status.decode(),
            'status_sha256': hashlib.sha256(status).hexdigest(),
            'worktrees_porcelain': git(root, 'worktree', 'list', '--porcelain').decode(),
            'git_dir': git(root, 'rev-parse', '--absolute-git-dir').decode().strip(),
            'ignored_locations': ignored, 'ignored_entries': ignored_entries,
            'recovery': {'status': 'verified' if not recovery_errors else 'failed',
                         'errors': recovery_errors, 'tracked_paths': allowed,
                         'excluded_sensitive_tracked_paths': sorted(set(changed) - set(allowed)),
                         'patch_sha256': sha256(patch), 'untracked_source_files': len(recover),
                         'untracked_source_paths': recover,
                         'untracked_not_archived': sorted(set(untracked) - set(recover)),
                         'archive_sha256': sha256(archive)}}
