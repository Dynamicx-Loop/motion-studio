#!/usr/bin/env python3
"""Inspect or bootstrap Motion Studio's independent external checkouts."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git(path, *args):
    return subprocess.check_output(
        ['git', '-C', str(path), *args], text=True, stderr=subprocess.PIPE
    ).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'check', 'bootstrap'])
    parser.add_argument('--source-workspace', type=Path,
                        help='Read-only checkout inspection root; manifest stays owned by this workspace')
    args = parser.parse_args()
    if args.source_workspace is not None and args.command == 'bootstrap':
        parser.error('--source-workspace is for read-only list/check only')
    source = args.source_workspace.resolve() if args.source_workspace is not None else ROOT
    if not source.is_dir():
        raise ValueError(f'Source workspace does not exist: {source}')
    manifest = json.loads((ROOT / 'externals/manifest.json').read_text())
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported manifest schema')
    failed = False
    for project in manifest['projects']:
        relative = Path(project['path'])
        if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != 'externals' or relative.parts[1] in ('.', '..'):
            raise ValueError(f'External path must be directly under externals: {relative}')
        path = source / relative
        if path.resolve().parent != (source / 'externals').resolve():
            raise ValueError(f'External path must be directly under externals: {path}')
        if args.command == 'list':
            print(f"{project['name']}: {project['path']} @ {project['revision']}")
            continue
        if args.command == 'bootstrap':
            if path.exists() or path.is_symlink():
                print(f"KEEP {project['path']} (already exists)")
                continue
            env = os.environ.copy()
            if project.get('skip_lfs', False):
                env['GIT_LFS_SKIP_SMUDGE'] = '1'
            subprocess.run(['git', 'clone', '--', project['url'], str(path)], check=True, env=env)
            subprocess.run(['git', '-C', str(path), 'checkout', '--detach',
                            project['revision']], check=True, env=env)
            if project['upstream'] != project['url']:
                subprocess.run(['git', '-C', str(path), 'remote', 'add', 'upstream',
                                project['upstream']], check=True)
            print(f"CREATED {project['path']}")
            continue
        if not (path / '.git').exists():
            print(f"MISSING {project['path']}")
            failed = True
            continue
        head = git(path, 'rev-parse', 'HEAD')
        status = git(path, 'status', '--short')
        matches = head == project['revision']
        print(f"{'OK' if matches else 'DRIFT'} {project['path']} @ {head}")
        if status:
            print('  Local changes (preserved):\n' + '\n'.join('    ' + s for s in status.splitlines()))
        failed |= not matches
    return int(failed)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f'Workspace error: {error}', file=sys.stderr)
        sys.exit(1)
