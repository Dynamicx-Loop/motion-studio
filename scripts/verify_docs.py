"""Verify a selected local documentation edition without computing new results."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.documentation import verify_edition


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--report', type=Path, help='Save a verification receipt at this explicit path')
    parser.add_argument('--edition', default='current')
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--evidence-root', type=Path)
    args = parser.parse_args()
    result = verify_edition(args.output or root / 'outputs/docs-site' / args.edition,
                           source_root=args.source_root, evidence_root=args.evidence_root)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
