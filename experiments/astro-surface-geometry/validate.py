#!/usr/bin/env python3
"""Run static Astro geometry validation without training or retargeting."""
import argparse
from pathlib import Path
from geometry_checks import ROOT, gates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/astro-surface-geometry")
    args = parser.parse_args()
    gates(args.out.resolve())


if __name__ == "__main__":
    main()
