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
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
run, out = args.run.resolve(), args.output.resolve()
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
    '<h1>Fitted uniform SOMA + G1</h1><p>Native fitted BONES-SEED prototype. <strong>Visual acceptance pending.</strong></p>'))
shutil.copyfile(HERE / 'skeleton-overlay.js', out / 'skeleton-overlay.js')
app.write_text(app.read_text().replace("import {humanMotion} from './human-motion.js';", "import {humanMotion} from './human-motion.js';\nimport {skeletonOverlay} from './skeleton-overlay.js';").replace("  const replay = humanMotion(human, binary);", "  const skeleton = await skeletonOverlay(scene, THREE, human, binary);\n  const replay = humanMotion(human, binary);").replace("    const reference = $('reference').checked;", "    const reference = $('reference').checked;\n    const root = human.root_positions[frame], firstRoot = human.root_positions[0];\n    skeleton(frame, [offsets[0] - ($('center').checked ? root[0] : firstRoot[0]), 0, -($('center').checked ? root[2] : firstRoot[2])], !reference && $('skeletons').checked);").replace("  $('play').onclick = () => {", "  $('skeletons').onchange = pose;\n  $('play').onclick = () => {"))
index.write_text(index.read_text().replace('<label>Source segment', '<label><input id="skeletons" type="checkbox"> Overlay fitted (gold) + BVH (cyan) skeletons</label><p><small>Named joints share pose channels; fitted rest offsets can differ. Overlay preserves absolute source scale and translation. Hips anchors mesh decoding. <a href="audit.json">Numerical audit</a></small></p><label>Source segment'))
(out / 'vendor').mkdir()
vendor = ROOT / 'motion_studio/studio/web/inspection/vendor'
for name in ('three.module.js','OrbitControls.js'):
    shutil.copyfile(vendor / name, out / 'vendor' / name)
shutil.copyfile(ROOT / 'docs/site/THIRD_PARTY_NOTICES.md', out / 'THIRD_PARTY_NOTICES.md')
(out / 'export_source').mkdir()
for name in ('export.py','inspection_worker.py','human_replay.py','skeleton-overlay.js','audit_replay.py','compare.py','replay_diagnostic.py'):
    shutil.copyfile(HERE / name, out / 'export_source' / name)
same = before == snapshot(run)
assert same, 'Source run changed during inspection'
(out / 'preservation.json').write_text(json.dumps({'source_run_unchanged': same},indent=2)+'\n')
(out / 'provenance.json').write_text(json.dumps({'source_run': str(run),
    'cohort': 'native-fitted-uniform-SOMA-prototype', 'official_fitted_bones_seed': True,
    'runtime_environment':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES','UMR_SOMA_DEVICE','UMR_SOMA_ASSETS_PATH','UMR_SOMA_SMPLX_ASSETS_PATH')}, 'command':command, 'wall_seconds':time.monotonic()-start, 'input_hashes':before,
    'output_hashes':snapshot(out), 'scope':'Native SOMA segment labels, barycentric human replay and rigid saved G1 qpos; no new solve'},indent=2)+'\n')
print(out / 'index.html')
