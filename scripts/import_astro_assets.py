"""Snapshot the committed default Astro P2 robot into Motion Studio assets."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.integrations.menagerie_assets import ASTRO_ROOT, snapshot_astro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Existing menagerie_x checkout; never fetched or modified')
    parser.add_argument('--output', type=Path, default=ASTRO_ROOT, help='Fresh snapshot destination')
    args = parser.parse_args()
    manifest = snapshot_astro(args.source, args.output)
    print(f"Astro P2 @ {manifest['source']['revision']} -> {args.output}")


if __name__ == '__main__':
    main()
