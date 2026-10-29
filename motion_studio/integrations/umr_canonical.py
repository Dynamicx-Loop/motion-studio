"""Fresh, explicit canonical UMR preparation; never executes train or retarget.

All paths are local. Input clip/shape/model bytes are opaque preserved evidence;
format and numerical compatibility remain unverified. XYZ/wxyz roots are separate
from scalar radians. Selection and configuration are owned here, UMR imports stay
in its independent interpreter. Official G1 reproduction is a separate operation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import shutil
from typing import Mapping

from motion_studio.robots import ConsistencyReport, RobotSelectionError, resolve_robot
from ._umr_canonical_runtime import inspect_runtime, verify_runtime_unchanged
from ._umr_canonical_model import materialize_pose

ADAPTER_VERSION = 'canonical-preparation-v1'


class CanonicalPreparationError(ValueError):
    """Missing, changed or incompatible preparation/cache requirements."""


@dataclass(frozen=True)
class CanonicalInputs:
    """SMPL-X clip, explicit shape evidence, neutral model files, native clip FPS.

    Shape evidence must describe the clip actor; preparation hashes/copies it but
    does not assert agreement with the clip. No trim/resample is performed.
    """
    clip: Path
    shape: Path
    model_files: tuple[Path, ...]
    fps: float
    sequence_key: str = 'motion_actor_smplx'
    gender: str = 'neutral'


@dataclass(frozen=True)
class SamplingSettings:
    """First-hit exterior surface sampling; order is native XML/mesh face order."""
    num_points: int = 4096
    seed: int = 0
    surface_oversample_ratio: int = 8
    exterior_occlusion_distance: float = 0.12


@dataclass(frozen=True)
class UMRRuntime:
    """Explicit pinned official checkout and existing interpreter; no discovery/install."""
    checkout: Path
    python: Path


@dataclass(frozen=True)
class PreparedCanonicalComparison:
    model: Path
    config: Path
    inputs: Path
    receipt: Path


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def _adapter_code():
    return {p.name: _hash(p) for p in (Path(__file__),
        Path(__file__).with_name('_umr_canonical_runtime.py'),
        Path(__file__).with_name('_umr_canonical_model.py'))}


def _fingerprints(common, train):
    dataset = _identity(common)
    return {'dataset': dataset, **{stage: _identity({'stage': stage, 'dataset': dataset,
             'train': train, 'seed': common['sampling']['seed']}) for stage in ('slots', 'checkpoint')}}


def _write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def _claims(selection, report, claims, roots, catalog):
    if not claims:
        return None
    if report is None:
        raise CanonicalPreparationError('Supply a current representation report for requested claims')
    if (report.schema_version != 1 or report.definition_id != selection.definition_id
            or selection.pose_name not in report.poses or len(set(report.poses)) != len(report.poses)):
        raise CanonicalPreparationError('Representation report definition/pose/schema mismatch')
    pairs = [resolve_robot(selection.definition_id, rep, pose, roots, definitions_root=catalog)
             for pose in report.poses for rep in ('urdf', 'mjcf')]
    hashes = tuple(sorted({(f.relative_path, f.sha256) for s in pairs for f in s.files}))
    policy = Path(catalog) / selection.definition_id / 'consistency.json'
    if (report.identities != tuple(s.identity for s in pairs) or report.source_hashes != hashes
            or report.policy_sha256 != (_hash(policy) if policy.exists() else '')):
        raise CanonicalPreparationError('Representation report is stale for current definition/source/pose/policy')
    report.require_supported(claims)
    # Supported collision_policy can accept refinements; it never proves equality.
    return {'required': list(claims), 'report': asdict(report)}


def prepare_canonical_comparison(
    definition_id: str, representation: str, pose: str, inputs: CanonicalInputs,
    destination: Path, source_roots: Mapping[str, Path | str], *,
    settings: SamplingSettings = SamplingSettings(), runtime: UMRRuntime | None = None,
    definitions_root: Path | None = None, representation_report: ConsistencyReport | None = None,
    required_claims: tuple[str, ...] = (),
) -> PreparedCanonicalComparison:
    """Copy verified inputs into a fresh closed cohort and return prepared paths.

    Explicit ID/representation/pose are required; MJCF only, with no URDF conversion.
    Missing runtime yields an unverified prerequisite record, never execution
    readiness. A supplied runtime must be pinned, unchanged and probe successfully.
    Failures before creation leave no run; later failures retain a failed receipt.
    Existing destinations cannot resume. Source drift raises; inputs are read-only.
    """
    if representation != 'mjcf':
        raise CanonicalPreparationError('Canonical UMR preparation supports explicit MJCF only')
    catalog = definitions_root or Path(__file__).resolve().parents[2] / 'robots'
    selection = resolve_robot(definition_id, representation, pose, source_roots, definitions_root=catalog)
    claim_record = _claims(selection, representation_report, required_claims, source_roots, catalog)
    if (type(inputs.fps) not in (int, float) or not math.isfinite(inputs.fps) or inputs.fps <= 0
            or not inputs.sequence_key or inputs.gender != 'neutral' or not inputs.model_files):
        raise CanonicalPreparationError('Supply positive FPS, sequence key and explicit neutral SMPL-X model files')
    if (type(settings.num_points) is not int or settings.num_points < 1
            or type(settings.seed) is not int or settings.seed < 0
            or type(settings.surface_oversample_ratio) is not int or settings.surface_oversample_ratio < 1
            or type(settings.exterior_occlusion_distance) not in (int, float)
            or not math.isfinite(settings.exterior_occlusion_distance)
            or settings.exterior_occlusion_distance < 0):
        raise CanonicalPreparationError('Invalid source/target sampling settings')
    output = Path(destination).resolve()
    clip_name = 'clip' + Path(inputs.clip).suffix
    sources = [(clip_name, Path(inputs.clip).resolve()), ('shape', Path(inputs.shape).resolve())]
    model_names = [Path(p).name for p in inputs.model_files]
    if len(set(model_names)) != len(model_names):
        raise CanonicalPreparationError('Model filenames must be unique')
    sources += [('model/' + name, Path(path).resolve()) for name, path in zip(model_names, inputs.model_files)]
    protected = [Path(p).resolve() for p in source_roots.values()]
    protected += [p.parent for _, p in sources]
    if runtime:
        protected.append(Path(runtime.checkout).resolve())
    # Inspect physical checkout roots too, including links used by managed worktrees.
    externals = Path(__file__).resolve().parents[2] / 'externals'
    protected.append(externals.resolve())
    if externals.is_dir():
        protected += [p.resolve() for p in externals.iterdir() if p.is_dir()]
    if any(output.is_relative_to(p) for p in protected):
        raise CanonicalPreparationError('Destination resolves into external/source assets')
    if output.exists() or Path(destination).is_symlink():
        raise FileExistsError(f'Use a fresh destination: {destination}')
    source_hashes = {name: _hash(path) for name, path in sources}
    runtime_record, runtime_files = inspect_runtime(runtime)
    source_members = [(f'assets/{f.relative_path}', f.path, f.sha256) for f in selection.files]
    source_members += [(f'input/{name}', path, source_hashes[name]) for name, path in sources]
    source_members += [(f'backend/{name}', path, digest) for name, path, digest in runtime_files]
    # Revalidate all required source bytes immediately before creating anything.
    for _, path, digest in source_members:
        if _hash(path) != digest:
            raise CanonicalPreparationError(f'Source drift before preparation: {path}')
    copied_model_relative = 'assets/' + selection.model_path.relative_to(selection.source_root).as_posix()
    model_relative = str(Path(copied_model_relative).with_name(selection.model_path.stem + '-canonical-pose.xml'))
    relatives = [relative for relative, _, _ in source_members]
    if len(set(relatives)) != len(relatives) or model_relative in relatives:
        raise CanonicalPreparationError('Conflicting model/input closure destinations')
    native_pose = dict(zip(selection.joint_names, selection.pose_values))
    code = _adapter_code()
    geometry = {'visual': 'UMR auto visual_geom_policy; native geom and mesh face order',
                'collision': 'preserved; UMR auto prefers noncontact visual meshes, falls back to other meshes/primitive surfaces if none',
                'centering': 'body:waist_yaw_link' if definition_id == 'g1_29dof' else f'body:{selection.conventions.root_frame}',
                'source_center': 'spine1', 'topology': 'original compiled mesh/primitive surface order; not generated here'}
    target = {'selection': selection.identity, 'files': [(f.relative_path, f.sha256) for f in selection.files],
              'native_order': selection.native_joint_names, 'application_order': selection.joint_names,
              'pose': asdict(selection.root_pose) | {'joints': native_pose}, 'geometry': geometry}
    common = {'adapter_version': ADAPTER_VERSION, 'adapter_code': code,
              'backend': runtime_record['identity'], 'target': target,
              'source': source_hashes, 'fps': inputs.fps, 'sequence_key': inputs.sequence_key,
              'gender': inputs.gender, 'sampling': asdict(settings),
              'conversions': {'smpl_to_robot_root_matrix': [[0,0,1],[1,0,0],[0,1,0]],
                              'source_axes': 'SMPL-X Y-up, X-left, Z-forward',
                              'clip': 'unchanged bytes; no trim/resample; format unverified',
                              'model': 'includes expanded; asset references rebased run-local; root pos/quat set to explicit pose; scalars assigned by name'}}
    fingerprints = _fingerprints(common, runtime_record['defaults_train'])
    config = {
        'smplx_model_dir': str(output/'input/model'),
        'smpl_template': {'source': 'motion', 'type': 'smplx', 'use_betas': True, 'use_gender': True},
        'robot': {'name': definition_id, 'xml': str(output/model_relative),
                  'xml_policy': {'add_freejoint_root': False},
                  'point_cloud_center': geometry['centering'], 'visual_geom_policy': 'auto',
                  'sample_pose': 'tpose', 'tpose_qpos': {n: native_pose[n] for n in selection.native_joint_names},
                  'to_smpl_frame': True, 'frame_transform': {'smpl_to_robot_root_matrix': common['conversions']['smpl_to_robot_root_matrix']}},
        'motion': {'data': str(output/'input'/clip_name), 'seq_key': inputs.sequence_key,
                   'start': 0, 'end': -1, 'stride': 1, 'max_frames': 0},
        'correspondence': {'reuse_across_smplx_betas': False, 'shared_config': None,
                           'shared_smplx_template': None, 'slots': None, 'smpl_name': 'auto',
                           'dataset': asdict(settings) | {'out': str(output/'derived/dataset.npz'),
                               'smpl_center': 'spine1', 'exterior_surface': True, 'exterior_method': 'first_hit',
                               'smpl_models': [{'type': 'smplx', 'dir': str(output/'input/model'), 'genders': ['neutral']}]},
                           'train': {'out_dir': str(output/'derived/train'), 'seed': settings.seed}},
        'retarget': {'out': str(output/'derived/motion.npz')}, 'view': {'enabled': False}}
    receipt = {'schema_version': 1, 'cohort_kind': 'canonical-comparison', 'state': 'preparing',
               'execution_readiness': False, 'model': model_relative, 'config': 'config.json', 'inputs': 'inputs.json',
               'semantic_identity': _identity(common), 'semantic_inputs': common,
               'runtime': runtime_record, 'representation_claims': claim_record,
               'joint_order': {'native': list(selection.native_joint_names), 'application': list(selection.joint_names)},
               'conventions': asdict(selection.conventions), 'geometry_policy': geometry,
               'pose': {'name': pose, 'root_translation_m': list(selection.root_pose.translation),
                        'root_quaternion_wxyz': list(selection.root_pose.quaternion), 'joints_rad': native_pose},
               'fingerprints': fingerprints, 'source_locations': {n: str(p) for n,p in sources},
               'robot_source_root': str(selection.source_root), 'provenance': asdict(selection.provenance),
               'limitations': ['Prepared only; no dataset, slots, checkpoint, training or retargeting generated.',
                   'Fingerprint equality does not prove numerical runtime compatibility.',
                   'Source shape/clip/model agreement and future surface topology remain unverified.',
                   'No representation parity, collision, dynamics or hardware claim beyond required exact findings.']}
    output.mkdir(parents=True, exist_ok=False)
    receipt_path = output/'preparation.json'
    try:
        for relative, path, digest in source_members:
            target_path = output/relative
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('rb') as src, target_path.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            if _hash(target_path) != digest:
                raise CanonicalPreparationError(f'Copy hash mismatch: {relative}')
        materialize_pose(output/copied_model_relative, output/model_relative, selection, output)
        (output/'derived').mkdir()
        _write(output/'config.json', config)
        _write(output/'inputs.json', {'source_sha256': source_hashes, 'fps': inputs.fps,
                                     'shape': 'input/shape', 'clip': 'input/' + clip_name, 'models': model_names,
                                     'pose': target['pose'], 'sampling': asdict(settings)})
        for _, path, digest in source_members:
            if _hash(path) != digest:
                raise CanonicalPreparationError(f'Source changed during preparation: {path}')
        # Re-resolution also checks source commit and definition/pose drift.
        if resolve_robot(definition_id, representation, pose, source_roots,
                         definitions_root=catalog).identity != selection.identity:
            raise CanonicalPreparationError('Selection changed during preparation')
        verify_runtime_unchanged(runtime, runtime_record)
        if _adapter_code() != code:
            raise CanonicalPreparationError('Adapter code changed during preparation')
        receipt['prepared_files'] = {p.relative_to(output).as_posix(): _hash(p)
                                     for p in sorted(output.rglob('*')) if p.is_file()}
        receipt['state'] = 'prepared-only'
    except BaseException as error:
        receipt.update(state='failed', failure=f'{type(error).__name__}: {error}')
        _write(receipt_path, receipt)
        raise
    _write(receipt_path, receipt)
    return PreparedCanonicalComparison(output/model_relative, output/'config.json', output/'inputs.json', receipt_path)


def _record(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise CanonicalPreparationError('Duplicate evidence field: ' + key)
            value[key] = item
        return value
    value = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        raise CanonicalPreparationError('Unsupported cache/preparation evidence schema')
    return value


def require_cache_compatible(prepared_receipt: Path, artifact: Path, metadata: Path, *, stage: str) -> Path:
    """Verify an explicit learned artifact's sidecar and bytes, never search/fallback.

    Sidecar schema 1: stage (dataset/slots/checkpoint), fingerprint, artifact_sha256,
    complete=true. Producers must record these after completing an artifact. This
    guard verifies identity/integrity, not tensor shapes or numerical compatibility.
    """
    try:
        receipt = _record(prepared_receipt)
        sidecar = _record(metadata)
        if (receipt['schema_version'] != 1 or receipt['cohort_kind'] != 'canonical-comparison'
                or receipt['state'] != 'prepared-only' or stage not in ('dataset', 'slots', 'checkpoint')):
            raise CanonicalPreparationError('Require a completed canonical preparation and known cache stage')
        common = receipt['semantic_inputs']
        if (receipt['semantic_identity'] != _identity(common)
                or common['adapter_version'] != ADAPTER_VERSION
                or common['adapter_code'] != _adapter_code()
                or receipt['fingerprints'] != _fingerprints(common, receipt['runtime']['defaults_train'])):
            raise CanonicalPreparationError('Preparation identity/adapter/fingerprint drift; prepare a new cohort')
        if not {receipt['model'], receipt['config'], receipt['inputs']} <= set(receipt['prepared_files']):
            raise CanonicalPreparationError('Prepared file evidence is incomplete')
        root = Path(prepared_receipt).resolve().parent
        for relative, digest in receipt['prepared_files'].items():
            path = (root/relative).resolve()
            if not path.is_relative_to(root) or _hash(path) != digest:
                raise CanonicalPreparationError('Prepared input drift: ' + relative)
        if (sidecar.get('schema_version') != 1 or sidecar.get('complete') is not True
                or sidecar.get('stage') != stage
                or sidecar.get('fingerprint') != receipt['fingerprints'][stage]
                or sidecar.get('artifact_sha256') != _hash(artifact)):
            raise CanonicalPreparationError('Incompatible or unverified learned artifact; prepare a new cohort/retrain')
        return Path(artifact).resolve()
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise CanonicalPreparationError(f'Cache evidence unavailable/invalid: {error}') from error
