"""Compare fresh static arrays with the frozen October 24 G1 cohort."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def compare(fresh: Path, historical: Path) -> dict:
    results = {}
    for filename, fields in [
        ('dataset.npz', ['points', 'mesh_vertices_0', 'mesh_faces_0', 'mesh_vertices_1',
                         'mesh_faces_1', 'sample_face_ids_0', 'sample_face_ids_1', 'betas_0']),
        ('train/correspondence_slots_final.npz', ['reconstructed_slots']),
    ]:
        current_path, previous_path = fresh / filename, historical / filename
        with np.load(current_path, allow_pickle=True) as current, np.load(previous_path, allow_pickle=True) as previous:
            measurements = {}
            for field in fields:
                np.testing.assert_array_equal(current[field], previous[field])
                measurements[field] = {'exact_array_equal': True, 'shape': list(current[field].shape)}
        results[filename] = {
            'fresh_sha256': hashlib.sha256(current_path.read_bytes()).hexdigest(),
            'historical_sha256': hashlib.sha256(previous_path.read_bytes()).hexdigest(),
            'fields': measurements,
        }
    return {'scope': 'Static arrays only; historical cohort has no motion output', 'comparisons': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh', type=Path, required=True)
    parser.add_argument('--historical', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.fresh, args.historical)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('All selected static dataset arrays and reconstructed slots match exactly.')
