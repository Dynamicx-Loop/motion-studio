"""Compare only explicit saved small excerpts; never launch fitting or write inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('root', type=Path)
parser.add_argument('--candidate', default='owned-final')
parser.add_argument('--receipt', required=True, type=Path)
args = parser.parse_args()
comparisons = {}
for suffix in ('.npz', '.diagnostics.npz'):
    with np.load((args.root / 'reference/motion.npz').with_suffix(suffix), allow_pickle=False) as old, \
            np.load((args.root / args.candidate / 'motion.npz').with_suffix(suffix), allow_pickle=False) as new:
        for field in old.files:
            if old[field].dtype.kind in 'iuf':
                np.testing.assert_allclose(new[field], old[field], rtol=0, atol=1e-7)
                comparisons[suffix + ':' + field] = {
                    'max_abs_difference': float(np.max(np.abs(new[field] - old[field]))),
                    'atol': 1e-7, 'rtol': 0}
            else:
                np.testing.assert_array_equal(new[field], old[field])
                comparisons[suffix + ':' + field] = {'exact': True}
        np.testing.assert_array_equal(new['source_frame_indices'], [3, 4, 5])
        np.testing.assert_allclose(new['source_timestamps'],
                                   [0.02499999, 0.03333332, 0.04166665], rtol=0, atol=1e-15)
old = json.loads((args.root / 'reference/motion.report.json').read_text())
new = json.loads((args.root / args.candidate / 'motion.report.json').read_text())
for field, value in old.items():
    assert new[field] == value, field
paths = [args.root / 'reference-driver.py', args.root / 'reference-config.json',
         args.root / 'reference.log']
paths.extend(p for folder in ('reference', args.candidate)
             for p in (args.root / folder).rglob('*') if p.is_file())
hashes = {str(p.relative_to(args.root)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in paths}
result = dict(validation='fresh CPU excerpt [3,6), original driver at e215cc2',
              frames=3, frame_time=0.00833333,
              source_timestamps=[0.02499999, 0.03333332, 0.04166665], comparisons=comparisons,
              legacy_report_fields_exact=list(old), files_sha256=hashes,
              limits=['No full historical conversion rerun', 'No GPU or dynamic feasibility check'])
with args.receipt.open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(f'12 legacy fields and 16 report fields match; receipt: {args.receipt}')
