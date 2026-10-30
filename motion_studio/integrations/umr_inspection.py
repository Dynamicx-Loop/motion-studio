"""Read-only segment binding reconstruction and playback of a completed G1 run."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

_ROOT = Path(__file__).resolve().parents[2]
_PIN = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'


@dataclass(frozen=True)
class BindingInspection:
    index: Path
    provenance: Path


def _hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(folder):
    return {str(p.relative_to(folder)): _hash(p)
            for p in sorted(folder.rglob('*')) if p.is_file()}


def export_g1_bindings(run: Path, destination: Path, *, workspace: Path = _ROOT) -> BindingInspection:
    """Export bindings and saved motion in Y-up metres; never train or solve motion.

    Uses saved learned slot IDs, the saved human mesh/shape and run-local robot
    assets. Native19 source labels and production nearest-vertex-k projection
    are recomputed with the pinned implementation. They are diagnostic labels,
    not anatomical correctness or dynamic feasibility certificates.
    """
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    workspace, run, destination = workspace.resolve(), run.resolve(), destination.resolve()
    if (not destination.is_relative_to((workspace / 'outputs').resolve())
            or destination.is_relative_to(run) or run.is_relative_to(destination)):
        raise ValueError('Inspection must be a separate directory under workspace outputs')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    for name in ('config.json', 'resolved.json', 'dataset.npz', 'motion.npz',
                 'validation.json', 'artifacts.json', 'train/correspondence_slots_final.npz'):
        if not (run / name).is_file():
            raise FileNotFoundError(run / name)
    checkout = workspace / 'externals/UMR'
    git = lambda *args: subprocess.check_output(['git', '-C', str(checkout), *args], text=True).strip()
    if git('rev-parse', 'HEAD') != _PIN or git('diff', _PIN, '--name-only'):
        raise ValueError('Inspection requires unchanged pinned official UMR source')
    vendor = workspace / 'outputs/umr-binding-report/documentation/vendor'
    resources = [(vendor / 'three.module.js', 'vendor/three.module.js'),
                 (vendor / 'controls/OrbitControls.js', 'vendor/OrbitControls.js'),
                 (workspace / 'docs/site/THIRD_PARTY_NOTICES.md', 'THIRD_PARTY_NOTICES.md')]
    for source, _ in resources:
        if not source.is_file():
            raise FileNotFoundError(source)
    before, status = _snapshot(run), git('status', '--porcelain')
    recorded = json.loads((run / 'artifacts.json').read_text())
    for name, expected in recorded.items():
        if before.get(name) != expected:
            raise ValueError('Completed run artifact changed: ' + name)
    destination.mkdir(parents=True, exist_ok=False)
    worker = Path(__file__).with_name('_umr_inspection_worker.py')
    human_worker = worker.with_name('_umr_human_motion.py')
    try:
        with (destination / 'export.log').open('x') as log:
            subprocess.run([str(checkout / '.venv/bin/python'), '-B', str(worker),
                            str(checkout), str(run), str(destination)],
                           cwd=workspace, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                           stdout=log, stderr=subprocess.STDOUT, timeout=600, check=True)
        templates = Path(__file__).with_name('_umr_binding_viewer')
        for source, name in resources:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for name in ('index.html', 'app.js', 'human-motion.js'):
            shutil.copyfile(templates / name, destination / name)
        (destination / 'export_source').mkdir()
        for source in (Path(__file__), worker, human_worker):
            shutil.copyfile(source, destination / 'export_source' / source.name)
        record = {'source_run': str(run), 'umr_revision': _PIN, 'inputs_sha256': before,
                  'implementation_sha256': {p.name: _hash(p) for p in
                      [Path(__file__), worker, human_worker, templates / 'index.html', templates / 'app.js', templates / 'human-motion.js']},
                  'scope': 'Derived native19/production bindings with saved qpos replay; no training or motion solve',
                  'outputs_sha256': _snapshot(destination)}
        (destination / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    finally:
        unchanged = before == _snapshot(run) and git('status', '--porcelain') == status and git('rev-parse', 'HEAD') == _PIN
        (destination / 'preservation.json').write_text(json.dumps({'run_and_external_unchanged': unchanged}) + '\n')
        if not unchanged:
            raise RuntimeError('Inspection input preservation failed')
    return BindingInspection(destination / 'index.html', destination / 'provenance.json')
