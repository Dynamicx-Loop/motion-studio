"""Export inspectable exact-frame SOMA human + saved G1 replay to fresh destination."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CHECKOUT = ROOT / 'externals/UMR'
ASSETS = Path('/data/motions/human_models/soma-x/f81a01796f65/overlays/umr')
HERE = Path(__file__).resolve().parent


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot(folder):
    return {str(p.relative_to(folder)): digest(p) for p in folder.rglob('*')
            if p.is_file() and not any(part in ('cache','tmp') for part in p.relative_to(folder).parts)}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run', type=Path)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
run, out = args.run.resolve(), args.destination.resolve()
if out.is_relative_to(run) or run.is_relative_to(out):
    raise ValueError('Inspection must use a separate fresh directory')
before = snapshot(run)
out.mkdir(parents=True, exist_ok=False)
start = time.monotonic()
command = [sys.executable, '-B', str(HERE / 'inspection_worker.py'), str(CHECKOUT), str(run), str(out)]
with (out / 'export.log').open('x') as stream:
    subprocess.run(command, cwd=ROOT, env={**os.environ, 'UMR_SOMA_ASSETS_PATH': str(ASSETS),
        'UMR_SOMA_SMPLX_ASSETS_PATH': str(ASSETS / 'SMPLX'), 'PYTHONDONTWRITEBYTECODE': '1'},
        stdout=stream, stderr=subprocess.STDOUT, check=True)
templates = ROOT / 'motion_studio/integrations/_umr_binding_viewer'
for name in ('index.html','app.js','human-motion.js'):
    shutil.copyfile(templates / name, out / name)
app = out / 'app.js'
app.write_text(app.read_text().replace('binary(motion.transforms, Float32Array,', 'binary(motion.transforms, Float64Array,'))
index = out / 'index.html'
index.write_text(index.read_text().replace('<h1>G1 motion + bindings</h1>',
    '<h1>Generic SOMA + G1 control</h1><p><strong>Unfitted neutral surface.</strong> Official BONES-SEED MHR calibration is missing. This native direct-BVH control is separate from the fitted official route.</p>'))
(out / 'vendor').mkdir()
vendor = ROOT / 'motion_studio/studio/web/inspection/vendor'
for name in ('three.module.js','OrbitControls.js'):
    shutil.copyfile(vendor / name, out / 'vendor' / name)
shutil.copyfile(ROOT / 'docs/site/THIRD_PARTY_NOTICES.md', out / 'THIRD_PARTY_NOTICES.md')
(out / 'export_source').mkdir()
for name in ('export.py','inspection_worker.py','human_replay.py'):
    shutil.copyfile(HERE / name, out / 'export_source' / name)
same = before == snapshot(run)
assert same, 'Source run changed during inspection'
(out / 'preservation.json').write_text(json.dumps({'source_run_unchanged': same},indent=2)+'\n')
(out / 'provenance.json').write_text(json.dumps({'source_run': str(run),
    'cohort': 'generic-neutral-direct-SOMA-control', 'official_fitted_bones_seed': False,
    'command':command, 'wall_seconds':time.monotonic()-start, 'input_hashes':before,
    'output_hashes':snapshot(out), 'scope':'Native SOMA segment labels, barycentric human replay and rigid saved G1 qpos; no new solve'},indent=2)+'\n')
print(out / 'index.html')
