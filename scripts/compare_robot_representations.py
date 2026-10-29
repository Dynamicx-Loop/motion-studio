#!/usr/bin/env python3
"""Emit a read-only bounded URDF/MJCF report using an existing CPU runtime."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from motion_studio.robots import compare_representations


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('definition_id')
    parser.add_argument('--source',action='append',nargs=2,metavar=('KEY','ROOT'),required=True)
    parser.add_argument('--pose',action='append',help='Repeat explicit pose names; default zero/tpose')
    parser.add_argument('--runtime-python',type=Path,help='Existing MuJoCo interpreter; omit for static findings only')
    args=parser.parse_args()
    report=compare_representations(args.definition_id,dict(args.source),
        poses=tuple(args.pose or ('zero','tpose')),runtime_python=args.runtime_python)
    print(json.dumps(asdict(report)|{'status':report.status},indent=2,allow_nan=False))
    return 0


if __name__=='__main__':
    sys.exit(main())
