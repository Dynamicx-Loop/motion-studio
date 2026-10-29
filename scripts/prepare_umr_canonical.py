#!/usr/bin/env python3
"""Prepare a fresh explicit canonical UMR cohort; never train or retarget."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.integrations.umr_canonical import (
    CanonicalInputs, SamplingSettings, UMRRuntime, prepare_canonical_comparison,
)
from motion_studio.robots import compare_representations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--canonical', action='store_true', required=True,
                        help='Explicitly opt into canonical comparison preparation')
    parser.add_argument('--robot', required=True, help='Canonical definition ID/edition')
    parser.add_argument('--representation', choices=('mjcf',), required=True)
    parser.add_argument('--pose', required=True, help='Complete named pose from the definition')
    parser.add_argument('--source', action='append', nargs=2, metavar=('KEY', 'CHECKOUT'), required=True)
    parser.add_argument('--clip', type=Path, required=True)
    parser.add_argument('--shape', type=Path, required=True, help='Actor shape evidence, preserved verbatim')
    parser.add_argument('--model-file', type=Path, action='append', required=True,
                        help='Explicit neutral SMPL-X model dependency; repeat for all files')
    parser.add_argument('--fps', type=float, required=True, help='Declared native clip FPS; no resampling')
    parser.add_argument('--sequence-key', required=True)
    parser.add_argument('--destination', type=Path, required=True, help='Fresh run directory')
    parser.add_argument('--num-points', type=int, default=4096)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--oversample-ratio', type=int, default=8)
    parser.add_argument('--occlusion-distance', type=float, default=.12)
    parser.add_argument('--umr-checkout', type=Path)
    parser.add_argument('--umr-python', type=Path)
    parser.add_argument('--require-claim', action='append', default=[],
                        help='Require this exact URDF/MJCF claim at selected pose; repeat as needed')
    parser.add_argument('--comparison-python', type=Path, help='Existing MuJoCo interpreter for requested claims')
    args = parser.parse_args()
    if bool(args.umr_checkout) != bool(args.umr_python):
        parser.error('--umr-checkout and --umr-python must be supplied together')
    if len({key for key, _ in args.source}) != len(args.source):
        parser.error('Source keys must be distinct')
    roots = dict(args.source)
    try:
        report = compare_representations(args.robot, roots, poses=(args.pose,),
            runtime_python=args.comparison_python) if args.require_claim else None
        result = prepare_canonical_comparison(args.robot, args.representation, args.pose,
            CanonicalInputs(args.clip, args.shape, tuple(args.model_file), args.fps, args.sequence_key),
            args.destination, roots,
            settings=SamplingSettings(args.num_points, args.seed, args.oversample_ratio, args.occlusion_distance),
            runtime=UMRRuntime(args.umr_checkout, args.umr_python) if args.umr_checkout else None,
            representation_report=report, required_claims=tuple(args.require_claim))
        print(json.dumps({key: str(value) for key, value in asdict(result).items()}, indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, f'Canonical preparation failed: {error}\n')


if __name__ == '__main__':
    main()
