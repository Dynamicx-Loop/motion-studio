"""Owned Wendy BVH conversion; importing this interface needs only Python.

The pinned independent runtime fits fixed neutral SMPL-X shape in metres/Y-up.
Poses are axis-angle radians in SMPL-X order (55 joints, flattened to 165).
Source frames use a half-open interval, with original time = index * frame_time;
no resampling or axis rotation is performed. Fingers/face/eyes are not fitted.
Only fresh owned outputs are written. Invalid input raises ValueError, missing
inputs raise FileNotFoundError, occupied outputs raise FileExistsError. Runtime
failure raises RuntimeError and retains a log plus run-local worker evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from ._wendy_inputs import configuration, source_bvh, dependency, sha256

_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class WendyConversionRequest:
    """Existing JSON config plus independent runtime locations.

    Relative config and configured paths resolve against workspace, preserving
    the historical CLI rule. checkout defaults to externals/hiphi2smplx; python
    defaults to the existing externals/UMR/.venv/bin/python (no installation).
    Explicit locations support read-only canonical inputs from owned worktrees.
    """
    config: Path
    workspace: Path = _ROOT
    checkout: Path | None = None
    python: Path | None = None


@dataclass(frozen=True)
class WendyConversionResult:
    """Fresh validated artifacts; source interval is [start_frame, end_frame).

    Arrays retain source sample spacing; original times are also in both NPZs.
    provenance records full source/config/model/code/environment hashes and the
    operation's output ownership. A run never overwrites an existing artifact.
    """
    motion: Path
    diagnostics: Path
    report: Path
    provenance: Path
    source_excerpt: Path | None
    source: Path
    model: Path
    start_frame: int
    end_frame: int
    frame_time: float

    @property
    def frames(self) -> int:
        return self.end_frame - self.start_frame

    @property
    def fps(self) -> float:
        return 1 / self.frame_time


def _write(path: Path, value: object) -> None:
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def convert_wendy(request: WendyConversionRequest) -> WendyConversionResult:
    """Convert the configured source interval without changing source arrays.

    Config keys: source/model/output paths and positive frames are required.
    Defaults: start_frame=0, unit_scale=0.01, output_up='y', ten zero betas,
    mapping_overrides={}. Overrides map pinned body semantic names to exact BVH
    joint names. Scale/axes are restricted to the current pinned Wendy method;
    betas are exactly ten finite float32 coefficients, held fixed for every frame.
    The worker uses the pinned solver defaults, without shape/finger/face fitting.

    The operation owns motion, diagnostics, report, provenance, log, reservation
    and private work paths beside output; nonzero offsets also own source.bvh.
    The original BVH is read only. Existing paths, including dangling symlinks,
    are refused before writes. Failed runtime runs retain their evidence and
    require a fresh destination; the retained lock is an ownership receipt.
    """
    root = request.workspace.resolve()
    config = root / request.config
    raw_config = config.read_bytes()
    value = configuration(json.loads(raw_config))
    from motion_studio.motion_data_paths import canonical_motion_path
    source = (root / canonical_motion_path(value['source'])).resolve()
    model = (root / canonical_motion_path(value['model'])).resolve()
    output = (root / value['output']).absolute()
    if output.suffix != '.npz':
        raise ValueError('output must end in .npz')
    outputs = {name: output.with_suffix(suffix) for name, suffix in (
        ('motion', '.npz'), ('diagnostics', '.diagnostics.npz'),
        ('report', '.report.json'), ('provenance', '.provenance.json'),
        ('log', '.conversion.log'), ('lock', '.conversion.lock'),
        ('work', '.conversion'))}
    if value['start_frame']:
        outputs['excerpt'] = output.with_suffix('.source.bvh')
    checkout = (request.checkout or root / 'externals/hiphi2smplx').resolve()
    for path in outputs.values():
        if any(path.resolve().is_relative_to(protected) for protected in
               ((root / 'externals').resolve(), checkout)):
            raise ValueError('Outputs must live outside external checkouts')
        if path.exists() or path.is_symlink():
            raise FileExistsError(f'Use fresh outputs; occupied path: {path}')
        if path.resolve() in (source, model, config.resolve()):
            raise ValueError(f'Output conflicts with an input: {path}')
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise FileExistsError(f'Output parent is not a directory: {parent}')
    for required in (source, model):
        if not required.is_file():
            raise FileNotFoundError(required)
    clip = source_bvh(source, value['start_frame'], value['frames'])
    external, mapping = dependency(root, checkout, '65e51315ebbc82b2f0ff8e35a94565beb1b345e1',
               value['mapping_overrides'], clip.names)
    python = (root / (request.python or root / 'externals/UMR/.venv/bin/python')).absolute()
    if not python.is_file():
        raise FileNotFoundError(f'Existing conversion interpreter required: {python}')
    worker = Path(__file__).with_name('_wendy_worker.py')
    files = [source, model, config.resolve(), python, Path(__file__), worker,
             Path(__file__).with_name('_wendy_inputs.py'),
             Path(__file__).parents[1] / 'motion_data_paths.py']
    inputs = {str(p): sha256(p) for p in files}
    if inputs[str(source)] != clip.sha256 or inputs[str(config.resolve())] != hashlib.sha256(raw_config).hexdigest():
        raise ValueError('Source/config changed during conversion preflight')
    inputs.update({str(checkout / name): digest
                   for name, digest in external['tracked_code_sha256'].items()})
    value.update(source=str(source), model=str(model))
    ownership = {name: str(path) for name, path in outputs.items()}
    provenance = dict(created_at=datetime.now(timezone.utc).isoformat(),
        input_sha256=inputs, dependency=external, effective_config=value,
        config_path=str(config.resolve()), mapping=mapping, output_ownership=ownership,
        source_interval=dict(start_frame=value['start_frame'],
                             end_frame_exclusive=value['start_frame'] + value['frames'],
                             source_frames=clip.frames, frame_time=clip.frame_time,
                             original_start_seconds=value['start_frame'] * clip.frame_time),
        source_axes='BVH axes retained; Wendy source declared Y-up', units='metres',
        shape='fixed neutral SMPL-X with configured 10 betas; no shape estimation',
        solver='pinned ConversionConfig defaults, progress=True',
        driver_environment=dict(python=sys.version, platform=platform.platform()),
        status='started')
    output.parent.mkdir(parents=True, exist_ok=True)
    _write(outputs['lock'], dict(output_ownership=ownership))
    # Claim the namespace once, then recheck after reservation. Publication below
    # uses exclusive links too, so a concurrent writer's bytes are never replaced.
    for name, path in outputs.items():
        if name != 'lock' and (path.exists() or path.is_symlink()):
            raise FileExistsError(path)
    work = outputs['work']
    work.mkdir()
    for folder in ('cache', 'tmp'):
        (work / folder).mkdir()
    fit_source = source
    if 'excerpt' in outputs:
        fit_source = work / 'source.bvh'
        with fit_source.open('x') as stream:
            stream.write(clip.excerpt(value['start_frame'], value['frames']))
    job = dict(config=value, checkout=str(checkout), work=str(work),
               source_for_fit=str(fit_source), frame_time=clip.frame_time,
               source_frames=clip.frames, mapping=mapping)
    _write(work / 'request.json', job)
    environment = os.environ.copy()
    overrides = dict(PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
                     PYTHONPATH=str(checkout / 'src'), XDG_CACHE_HOME=str(work / 'cache'),
                     TMPDIR=str(work / 'tmp'), OMP_NUM_THREADS='4')
    environment.update(overrides)
    provenance['environment_overrides'] = overrides
    provenance['command'] = [str(python), str(worker), str(work / 'request.json')]
    try:
        with outputs['log'].open('x') as log:
            process = subprocess.run(provenance['command'], cwd=work, env=environment,
                                     stdout=log, stderr=subprocess.STDOUT, timeout=7200)
        if process.returncode:
            raise RuntimeError(f'Wendy conversion failed ({process.returncode}); see {outputs["log"]}')
        if any(sha256(Path(path)) != digest for path, digest in inputs.items()):
            raise RuntimeError('Conversion source/model/config/code changed during execution')
        report = json.loads((work / 'report.json').read_text())
        if report['frames'] != value['frames'] or report['frame_time'] != clip.frame_time:
            raise ValueError('Worker result changed the requested frame interval/timing')
        publication = {'motion': work / 'motion.npz', 'diagnostics': work / 'diagnostics.npz',
                       'report': work / 'report.json'}
        if 'excerpt' in outputs:
            publication['excerpt'] = fit_source
        for name, staged in publication.items():
            os.link(staged, outputs[name])
            staged.unlink()
        provenance.update(status='complete', report=report,
                          runtime_environment=json.loads((work / 'environment.json').read_text()))
    except BaseException as error:
        provenance.update(status='failed', failure=f'{type(error).__name__}: {error}')
        raise
    finally:
        artifacts = [p for p in outputs.values() if p.is_file()]
        artifacts += [p for p in work.rglob('*') if p.is_file() and
                      not p.is_relative_to(work / 'cache') and not p.is_relative_to(work / 'tmp')]
        provenance['output_sha256'] = {str(p): sha256(p) for p in artifacts}
        provenance['finished_at'] = datetime.now(timezone.utc).isoformat()
        _write(outputs['provenance'], provenance)
    return WendyConversionResult(outputs['motion'], outputs['diagnostics'], outputs['report'],
        outputs['provenance'], outputs.get('excerpt'), source, model, value['start_frame'],
        value['start_frame'] + value['frames'], clip.frame_time)
