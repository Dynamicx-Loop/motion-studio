"""Build a fresh local documentation edition from recorded research inputs."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.documentation import build_edition


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=root)
    parser.add_argument('--evidence-root', type=Path, default=root)
    parser.add_argument('--edition', default='current')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--saved-sources', action='store_true',
                        help='Explicitly allow hash-checked snapshots for missing canonical records')
    parser.add_argument('--saved-edition', type=Path,
                        help='Prior edition containing manifest and source snapshots')
    args = parser.parse_args()
    if args.saved_edition and not args.saved_sources:
        parser.error('--saved-edition requires --saved-sources')
    saved = args.saved_edition or args.evidence_root / 'outputs/umr-binding-report'
    result = build_edition(args.source_root, args.evidence_root, edition=args.edition,
                          output=args.output, saved_edition=saved if args.saved_sources else None)
    print(f'Built {result.documents} documents in {result.output}; open {args.source_root / "docs.html"}')


if __name__ == '__main__':
    main()
