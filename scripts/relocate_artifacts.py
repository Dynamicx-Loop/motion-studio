#!/usr/bin/env python3
"""Plan, apply, verify or restore explicitly selected sealed experiment artifacts."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.artifacts import plan_relocation, relocate, restore, verify_relocation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('plan', help='Dry run: JSON plan on stdout; writes nothing')
    plan.add_argument('--workspace', type=Path, required=True)
    plan.add_argument('--inventory', type=Path, required=True)
    plan.add_argument('--inventory-sha256', required=True)
    plan.add_argument('--destination', required=True, help='Workspace-relative fresh outputs path')
    plan.add_argument('--selection', type=Path, required=True, help='JSON files list with explicit path and reviewed role')
    apply = sub.add_parser('apply')
    apply.add_argument('plan', type=Path)
    apply.add_argument('--resume', action='store_true')
    apply.add_argument('--step-limit', type=int)
    for name in ('verify', 'restore'):
        sub.add_parser(name).add_argument('receipt', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            selection = json.loads(args.selection.read_text())['files']
            result = plan_relocation(args.workspace, args.inventory, args.inventory_sha256,
                                     [(r['path'], r['role']) for r in selection], args.destination)
        elif args.command == 'apply':
            result = str(relocate(json.loads(args.plan.read_text()), resume=args.resume, step_limit=args.step_limit))
        elif args.command == 'verify':
            result = verify_relocation(args.receipt)
        else:
            restore(args.receipt)
            result = {'state': 'restored', 'receipt': str(args.receipt)}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if isinstance(result, dict) and result.get('passed') is False else 0
    except (OSError, ValueError) as error:
        parser.exit(2, f'Relocation refused: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
