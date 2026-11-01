"""Independent CPU adapter for exact-frame managed SMPL-X body-joint previews."""
import json
from pathlib import Path
import subprocess

from .umr_stages import PIN, native_environment
from motion_studio.studio._history import digest


def build_source_preview(motion, asset, destination, *, checkout, python):
    """Write a fresh source preview with the pinned native reconstruction route.

    Inputs have already passed the safe managed importer. No upstream permissive
    loader sees an original upload. Licensed weights stay at their recorded path.
    """
    if not 1 <= asset.frame_count <= 20000:
        raise ValueError('Source preview supports at most 20000 frames')
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    changed = subprocess.check_output(['git', '-C', str(checkout), 'diff', '--name-only', 'HEAD'], text=True).strip()
    if revision != PIN or changed:
        raise ValueError('Source preview requires unchanged pinned UMR source')
    paths = (Path(motion), Path(asset.model_path))
    hashes = [digest(path) for path in paths]
    if hashes[1] != asset.model_sha256:
        raise ValueError('Recorded model bytes changed')
    destination.mkdir(parents=True, exist_ok=False)
    request = destination / 'request.json'
    request.write_text(json.dumps({'motion':str(motion), 'model':asset.model_path,
                                   'fps':asset.fps, 'frame_count':asset.frame_count}))
    output = destination / 'preview.json'
    worker = Path(__file__).with_name('_umr_source_preview_worker.py')
    with (destination / 'build.log').open('wb') as log:
        subprocess.run([str(python), '-B', str(worker), str(checkout), str(request), str(output)],
                       stdout=log, stderr=subprocess.STDOUT, env=native_environment(), timeout=300, check=True)
    if hashes != [digest(path) for path in paths]:
        raise ValueError('Preview inputs changed during reconstruction')
    return output


def build_source_mesh_preview(motion, asset, destination, *, checkout, python):
    """Create version-one bounded mesh resources separately from legacy joints.

    No run dependency, GPU computation, downloads or source writes. The native
    worker retains at most 64 reconstructed frames and emits 0.1-mm root-relative
    vertex chunks plus one exact native triangle topology.
    """
    if not 1 <= asset.frame_count <= 20000:
        raise ValueError('Source mesh preview supports at most 20000 frames')
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    changed = subprocess.check_output(['git', '-C', str(checkout), 'diff', '--name-only', 'HEAD'], text=True).strip()
    if revision != PIN or changed:
        raise ValueError('Source mesh preview requires unchanged pinned UMR source')
    paths = (Path(motion), Path(asset.model_path))
    hashes = {str(path): digest(path) for path in paths}
    if hashes[str(paths[1])] != asset.model_sha256:
        raise ValueError('Recorded model bytes changed')
    destination.mkdir(parents=True, exist_ok=False)
    request = destination / 'request.json'
    request.write_text(json.dumps({'motion': str(motion), 'model': asset.model_path,
        'fps': asset.fps, 'frame_count': asset.frame_count, 'source_revision': revision,
        'inputs_sha256': hashes}))
    worker = Path(__file__).with_name('_umr_source_mesh_worker.py')
    with (destination / 'build.log').open('wb') as log:
        subprocess.run([str(python), '-B', str(worker), str(checkout), str(request), str(destination)],
                       stdout=log, stderr=subprocess.STDOUT, env=native_environment(), timeout=1800, check=True)
    if hashes != {str(path): digest(path) for path in paths}:
        raise ValueError('Preview inputs changed during reconstruction')
    return destination / 'manifest.json'
