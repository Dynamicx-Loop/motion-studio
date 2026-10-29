#!/usr/bin/env python3
"""Fixed-shape Wendy conversion using the existing independent hiphi runtime."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from motion_studio.integrations.wendy import WendyConversionRequest, convert_wendy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/umr/wendy-preview.json')
    parser.add_argument('--checkout', type=Path, help='Read-only pinned hiphi2smplx checkout')
    parser.add_argument('--python', type=Path, help='Existing conversion Python environment')
    args = parser.parse_args()
    result = convert_wendy(WendyConversionRequest(args.config, checkout=args.checkout,
                                                python=args.python))
    print(result.report.read_text(), end='')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(f'Wendy conversion error: {error}', file=sys.stderr)
        sys.exit(1)
