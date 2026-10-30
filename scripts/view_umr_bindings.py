"""Export segment bindings with saved motion playback from a completed G1 run."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.integrations.umr_inspection import export_g1_bindings

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = export_g1_bindings(args.run, args.output)
    print(f'Inspector: {result.index}\nProvenance: {result.provenance}')
