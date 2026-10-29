#!/usr/bin/env python3
"""Run owned checks: pure by default, other runtime tiers explicitly selected."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from motion_studio.checks import TIERS, check, discover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT,
                        help='Owned source workspace to inspect; no external tests discovered')
    parser.add_argument('--tier', choices=TIERS, action='append',
                        help='Repeat to select tiers; default: pure')
    parser.add_argument('--list', action='store_true', help='Inventory without importing tests')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable inventory/results')
    parser.add_argument('--umr-python', type=Path, help='Explicit interpreter for static saved-run checks')
    parser.add_argument('--umr-run', type=Path, help='Preserved static run; no training or retargeting')
    args = parser.parse_args()
    try:
        if args.list:
            suites = discover(args.root.resolve())
            if args.json:
                print(json.dumps([asdict(suite) for suite in suites], indent=2))
            else:
                for suite in suites:
                    print(f'{suite.tier}: {suite.path}')
                    for value in (*suite.inputs, *suite.modules, *suite.run_inputs):
                        print(f'  requires: {value}')
            return 0 if suites else 1
        report = check(args.root, tiers=tuple(args.tier or ['pure']),
                       umr_python=args.umr_python, umr_run=args.umr_run)
        if args.json:
            print(json.dumps({'selected_tiers': args.tier or ['pure'],
                              'exit_code': report.exit_code, **asdict(report)}, indent=2))
        else:
            print('Selected tiers: ' + ', '.join(args.tier or ['pure']))
            for result in report.outcomes:
                print(f'{result.status}: [{result.tier}] {result.path}')
                if result.status not in ('passed', 'not-selected'):
                    print(result.detail)
            selected = [r for r in report.outcomes if r.status != 'not-selected']
            print(f'{sum(r.status == "passed" for r in selected)}/{len(selected)} '
                  'selected suites passed; unselected tiers are not validated.')
        return report.exit_code
    except (OSError, ValueError, SyntaxError) as error:
        parser.exit(2, f'Check configuration error: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
