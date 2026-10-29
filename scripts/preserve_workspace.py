#!/usr/bin/env python3
"""Capture a sealed local preservation receipt, or verify it without mutation."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.preservation import capture_inventory, verify_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    capture = commands.add_parser('capture')
    capture.add_argument('--workspace', type=Path, required=True)
    capture.add_argument('--output', type=Path, required=True)
    capture.add_argument('--repository', action='append', default=[], metavar='NAME=PATH')
    capture.add_argument('--compatibility-root', type=Path, action='append', default=[])
    capture.add_argument('--source-root', type=Path, action='append', default=[],
                         help='Allow hashing only explicitly provenance-named inputs under this root')
    verify = commands.add_parser('verify')
    verify.add_argument('receipt', type=Path)
    args = parser.parse_args()
    if args.command == 'capture':
        repositories = {}
        for value in args.repository:
            if '=' not in value:
                parser.error('--repository expects NAME=PATH')
            name, path = value.split('=', 1)
            if name in repositories:
                parser.error('duplicate --repository identifier: ' + name)
            repositories[name] = Path(path)
        result = capture_inventory(args.workspace, args.output, repositories=repositories,
                                   compatibility_roots=args.compatibility_root,
                                   source_roots=args.source_root)
        print(json.dumps(asdict(result), default=str, indent=2))
        return 0
    result = verify_inventory(args.receipt)
    print(json.dumps(asdict(result), indent=2))
    return 0 if result.passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
