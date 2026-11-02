#!/usr/bin/env python3
"""Restore or check local sample bytes against the tracked sample manifest."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def child(root, relative):
    """Resolve manifest paths without permitting traversal outside their root."""
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError(f'Invalid manifest path: {relative}')
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes root: {path}')
    if path.is_symlink():
        raise ValueError(f'Expected a regular file, found symlink: {path}')
    return path


def matches(data, entry):
    return (len(data) == entry['bytes']
            and hashlib.sha256(data).hexdigest() == entry['sha256'])


def local_model_link(samples, motions_root, entry, populate):
    """Verify model bytes in place and restore an explicit directory link."""
    relative = Path(entry['path'])
    if relative.is_absolute() or '..' in relative.parts or relative.name in ('', '.'):
        raise ValueError(f'Invalid model link path: {relative}')
    target = child(samples, relative.parent) / relative.name
    source = child(motions_root, entry['source_path'])
    for item in entry['files']:
        path = source / item['path']
        if not path.resolve().is_relative_to(motions_root.resolve()):
            raise ValueError(f'Model file escapes data root: {path}')
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if path.stat().st_size != item['bytes'] or digest != item['sha256']:
            raise ValueError(f'Model checksum differs: {path}')
    if target.is_symlink():
        if target.resolve() != source.resolve():
            raise ValueError(f'Existing model link differs: {target}')
        return False
    if target.exists():
        raise ValueError(f'Existing model path preserved: {target}')
    if not populate:
        raise FileNotFoundError(f'Model link missing: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source.resolve(), target_is_directory=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['populate', 'check'])
    parser.add_argument('--source-workspace', type=Path, default=ROOT,
                        help='Workspace holding the original externals/UMR checkout')
    parser.add_argument('--motions-root', type=Path, default=Path('/data/motions'),
                        help='Canonical local dataset root; no download is performed')
    args = parser.parse_args()
    samples = ROOT / 'data/sample_data'
    manifest = json.loads((samples / 'manifest.json').read_text())
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported sample manifest schema')
    sources = {'umr': args.source_workspace / 'externals/UMR',
               'fzmotion': args.motions_root,
               'bones-seed': args.motions_root}
    failures = []
    restored = 0
    for entry in manifest['files']:
        try:
            target = child(samples, entry['path'])
            if target.exists():
                if not matches(target.read_bytes(), entry):
                    raise ValueError('Existing sample differs; preserved without overwriting')
            elif args.command == 'check':
                raise FileNotFoundError('Sample is missing; run populate with local sources')
            else:
                source = child(sources[entry['source']], entry['source_path'])
                data = source.read_bytes()
                if not matches(data, entry):
                    raise ValueError(f'Source checksum differs: {source}')
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(data)
                restored += 1
        except (OSError, ValueError) as error:
            failures.append(f"{entry['path']}: {error}")
    link_failures = []
    links = manifest.get('local_model_links', [])
    for entry in links:
        try:
            local_model_link(samples, args.motions_root, entry, args.command == 'populate')
        except (OSError, ValueError) as error:
            link_failures.append(f"{entry['path']}: {error}")
    for failure in failures + link_failures:
        print(f'FAIL {failure}', file=sys.stderr)
    print(f"{len(manifest['files']) - len(failures)}/{len(manifest['files'])} "
          f'samples verified; {restored} restored; {len(failures)} failed')
    if links:
        print(f'{len(links) - len(link_failures)}/{len(links)} local model links verified')
    return bool(failures or link_failures)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f'Sample data error: {error}', file=sys.stderr)
        sys.exit(1)
