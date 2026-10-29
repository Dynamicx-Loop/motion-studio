#!/usr/bin/env python3
"""Reproduce the complete official UMR G1 baseline into a fresh directory."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.integrations.umr import reproduce_g1_baseline

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = reproduce_g1_baseline(args.output)
    print(f'Motion: {result.motion}\nValidation: {result.validation}\nProvenance: {result.provenance}')
