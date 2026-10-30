"""Safe SMPL-X imports and immutable managed versions; upstream never reads originals."""
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import tempfile
import zipfile

from ._contracts import StudioError
from ._history import digest

DEFAULT_MODEL_DIR = Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx')
_DISCLOSURE = 'Native root/body reconstruction uses neutral hands and omits facial channels; all source channels are preserved.'


@dataclass(frozen=True)
class MotionAsset:
    asset_id: str
    name: str
    source_sha256: str
    frame_count: int
    fps: float
    gender: str
    up_axis: str
    pose_layout: str
    betas: tuple[float, ...]
    model_path: str
    model_sha256: str
    reconstruction: str
    channels: tuple[str, ...]
    metadata_sources: dict[str, str]
    units: str = 'metres; axis-angle radians'


def _inspect(source: bytes, metadata: dict):
    # Import lazily: persisted viewing and CLI startup need no scientific runtime.
    try:
        import numpy as np
    except ImportError as error:
        raise StudioError('motion_runtime_missing', 'Motion import needs NumPy in the service Python environment', 409) from error
    try:
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            names = archive.namelist()
            if (len(names) > 128 or len(names) != len(set(names))
                    or any('/' in n or '\\' in n or not n.endswith('.npy') for n in names)
                    or sum(i.file_size for i in archive.infolist()) > 512 * 1024 * 1024):
                raise ValueError('Archive must contain bounded, unique top-level NPY arrays')
            # Bound allocation before NumPy reads payloads (including lying shapes).
            for info in archive.infolist():
                with archive.open(info) as member:
                    version = np.lib.format.read_magic(member)
                    reader = {(1, 0): np.lib.format.read_array_header_1_0,
                              (2, 0): np.lib.format.read_array_header_2_0}.get(version)
                    if reader is None:
                        raise ValueError('Only NPY versions 1 and 2 are supported')
                    shape, _, dtype = reader(member, max_header_size=16384)
                    if dtype.kind not in 'biufUS' or math.prod(shape) > 64_000_000:
                        raise ValueError('Only bounded real numeric/fixed string arrays are supported')
                    if math.prod(shape) * dtype.itemsize != info.file_size - member.tell():
                        raise ValueError('NPY shape and payload length disagree')
        with np.load(io.BytesIO(source), allow_pickle=False, max_header_size=16384) as archive:
            arrays = {name: archive[name] for name in archive.files}
        for name, value in arrays.items():
            if value.dtype.kind not in 'biufUS' or value.size > 64_000_000:
                raise ValueError(f'{name}: only real numeric and fixed string arrays are supported')
            if value.dtype.kind in 'f' and not np.isfinite(value).all():
                raise ValueError(f'{name}: values must be finite')
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, EOFError) as error:
        raise StudioError('invalid_motion', f'Unsafe or malformed NPZ: {error}') from error

    def fail(message):
        raise StudioError('invalid_motion', message)

    def aliases(keys, *, required=True):
        found = [(key, arrays[key]) for key in keys if key in arrays]
        if not found:
            if required:
                fail('Missing required array: ' + '/'.join(keys))
            return None
        first = found[0][1]
        if any(not np.array_equal(first, value) for _, value in found[1:]):
            fail('Conflicting aliases: ' + '/'.join(keys))
        return first

    poses = aliases(('poses', 'pose_aa'), required=False)
    if poses is None:
        root, body = aliases(('root_orient',)), aliases(('pose_body',))
        if root.ndim != 2 or root.shape[1:] != (3,) or body.shape != (len(root), 63):
            fail('root_orient/pose_body require shapes (N,3)/(N,63)')
        poses = np.concatenate((root, body), axis=1)
    if poses.ndim != 2:
        fail('Axis-angle poses require a two-dimensional numeric array')
    if 'smpl_pose_axis_angle' in arrays:
        aa = arrays['smpl_pose_axis_angle']
        if aa.shape != (len(poses), poses.shape[1] // 3, 3) or not np.array_equal(aa.reshape(poses.shape), poses):
            fail('Conflicting smpl_pose_axis_angle alias')
    if 'root_orient' in arrays or 'pose_body' in arrays:
        root, body = aliases(('root_orient',)), aliases(('pose_body',))
        if not np.array_equal(poses[:, :3], root) or not np.array_equal(poses[:, 3:66], body):
            fail('Conflicting full and split pose aliases')
    if poses.dtype.kind not in 'iuf' or poses.ndim != 2 or poses.shape[0] < 1 or poses.shape[1] not in (66, 165):
        fail('Axis-angle poses require shape (N,66) body or (N,165) full SMPL-X')
    frames = len(poses)
    trans, betas = aliases(('trans', 'trans_orig', 'transl')), aliases(('betas', 'beta'))
    if trans.dtype.kind not in 'iuf' or trans.shape != (frames, 3):
        fail('Translation must be numeric (N,3) metres')
    if betas.dtype.kind not in 'iuf' or betas.shape not in ((10,), (1, 10)):
        fail('Shape must contain exactly ten constant betas')
    if any(key in arrays for key in ('timestamps', 'time', 'frame_ids', 'frame_times', 'interaction_objects')):
        fail('Custom timing/frame numbering and interaction objects are unsupported')
    if set(metadata) - {'fps', 'gender', 'up_axis'}:
        fail('Explicit metadata supports only fps, gender, up_axis')
    sources = {}

    def scalar(field, keys, convert):
        values = []
        for key in keys:
            if key in arrays:
                if arrays[key].size != 1:
                    fail(f'{key} must be a single constant value')
                if field == 'fps' and arrays[key].dtype.kind not in 'iuf':
                    fail('FPS must be numeric, not boolean or string')
                raw = arrays[key].item()
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
                values.append((key, convert(raw)))
        if field in metadata:
            if field == 'fps' and (isinstance(metadata[field], bool) or not isinstance(metadata[field], (int, float))):
                fail('Explicit FPS must be a number')
            values.append(('explicit', convert(metadata[field])))
        if not values:
            raise StudioError('missing_metadata', f'Missing {field}; supply it explicitly')
        if any(value != values[0][1] for _, value in values):
            fail(f'Conflicting {field} aliases or explicit metadata')
        sources[field] = ', '.join(key for key, _ in values)
        return values[0][1]

    if 'translation_units' in arrays and (arrays['translation_units'].size != 1 or str(arrays['translation_units'].item()).lower() not in ('m', 'metres', 'meters')):
        fail('Translation units must be metres')
    try:
        fps = scalar('fps', ('mocap_frame_rate', 'mocap_framerate', 'fps'), float)
        gender = scalar('gender', ('gender',), lambda v: str(v).lower())
        up = scalar('up_axis', ('samp_output_up', 'output_up', 'up_axis', 'coordinate_up'), lambda v: str(v).lower())
        if not np.isfinite(fps) or fps <= 0:
            fail('FPS must be positive and finite')
        if 'frame_time' in arrays:
            interval = arrays['frame_time']
            if interval.size != 1 or not np.isclose(float(interval.item()), 1. / fps, atol=1e-9, rtol=1e-6):
                fail('frame_time must agree with constant FPS')
        if 'model_type' in arrays and (arrays['model_type'].size != 1 or str(arrays['model_type'].item()).lower() != 'smplx'):
            fail('Only SMPL-X model_type is supported')
        if gender not in ('neutral', 'male', 'female'):
            fail('Gender must be neutral, male or female')
        if up not in ('y', 'z'):
            fail('Up-axis must be y or z')
        if 'human_scale' in arrays and (arrays['human_scale'].size != 1 or float(arrays['human_scale'].item()) != 1.):
            fail('Translation must already be metres; human_scale must be 1')
    except (TypeError, ValueError, UnicodeError) as error:
        if isinstance(error, StudioError):
            raise
        fail('Invalid scalar metadata: ' + str(error))
    safe = io.BytesIO()
    np.savez(safe, poses=poses, trans=trans, betas=betas.reshape(10), gender=gender,
             mocap_frame_rate=fps, samp_output_up=up)
    return dict(frame_count=frames, fps=fps, gender=gender, up_axis=up,
                pose_layout='smplx-full-165' if poses.shape[1] == 165 else 'smplx-body-66',
                betas=tuple(float(v) for v in betas.reshape(10)), channels=tuple(sorted(arrays)),
                metadata_sources=sources), safe.getvalue()


class _MotionOperations:
    def _init_motions(self, model_dir):
        self.smplx_model_dir = Path(model_dir or DEFAULT_MODEL_DIR).resolve()
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS motion_assets (asset_id TEXT PRIMARY KEY, record TEXT, normalized_sha256 TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS motion_selections ('
                       'run_id TEXT, revision_id TEXT, asset_id TEXT, PRIMARY KEY(run_id, revision_id))')

    def import_motion(self, source_path: Path, *, metadata: dict | None = None) -> MotionAsset:
        """Copy a safe numeric/string NPZ and record explicit metadata/model hashes.

        No source writes, frame filtering, resampling or upstream deserialization.
        Licensed model bytes stay external and are hashed, never unpickled here.
        """
        path = Path(source_path).resolve()
        if not isinstance(metadata, (dict, type(None))):
            raise StudioError('invalid_motion', 'Metadata must be an object')
        try:
            if path.suffix.lower() != '.npz' or path.stat().st_size > 512 * 1024 * 1024:
                raise StudioError('invalid_motion', 'Expected an NPZ up to 512 MiB')
            source = path.read_bytes()
        except OSError as error:
            raise StudioError('invalid_path', f'Cannot read motion: {path}') from error
        details, normalized = _inspect(source, metadata or {})
        model = next((self.smplx_model_dir / f'SMPLX_{details["gender"].upper()}{ext}'
                      for ext in ('.pkl', '.npz')
                      if (self.smplx_model_dir / f'SMPLX_{details["gender"].upper()}{ext}').is_file()), None)
        if model is None:
            raise StudioError('missing_model', f'Install matching SMPL-X {details["gender"]} weights in {self.smplx_model_dir}', 409)
        record = dict(name=path.name, source_sha256=hashlib.sha256(source).hexdigest(),
                      model_path=str(model.resolve()), model_sha256=digest(model),
                      reconstruction=_DISCLOSURE, **details)
        # Name is a display hint; identical bytes and interpretation share a version.
        identity = {k: v for k, v in record.items() if k != 'name'}
        asset_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        with self._connection() as db:
            existing = db.execute('SELECT asset_id FROM motion_assets WHERE asset_id=?', (asset_id,)).fetchone()
            if existing:
                return self.get_motion(asset_id)
            folder = self.roots.assets / 'motions' / asset_id
            folder.parent.mkdir(exist_ok=True)
            temporary = Path(tempfile.mkdtemp(prefix='.import-', dir=folder.parent))
            try:
                (temporary / 'source.npz').write_bytes(source)
                (temporary / 'normalized.npz').write_bytes(normalized)
                (temporary / 'record.json').write_text(json.dumps(dict(asset_id=asset_id, **record), sort_keys=True, indent=2))
                if folder.exists():
                    raise StudioError('asset_conflict', 'Unregistered managed motion already exists', 409)
                temporary.rename(folder)
                db.execute('INSERT INTO motion_assets VALUES (?, ?, ?)',
                           (asset_id, json.dumps(dict(asset_id=asset_id, **record)), hashlib.sha256(normalized).hexdigest()))
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
        return self.get_motion(asset_id)

    def get_motion(self, asset_id: str) -> MotionAsset:
        with self._connection() as db:
            row = db.execute('SELECT record FROM motion_assets WHERE asset_id=?', (asset_id,)).fetchone()
        if row is None:
            raise StudioError('not_found', 'Motion asset does not exist', 404)
        data = json.loads(row['record'])
        for key in ('betas', 'channels'):
            data[key] = tuple(data[key])
        return MotionAsset(**data)

    def list_motions(self) -> tuple[MotionAsset, ...]:
        with self._connection() as db:
            ids = [row['asset_id'] for row in db.execute('SELECT asset_id FROM motion_assets ORDER BY rowid')]
        return tuple(self.get_motion(asset_id) for asset_id in ids)

    def motion_source(self, asset_id: str) -> Path:
        record = self.get_motion(asset_id)
        return self._motion_bytes(asset_id, 'source.npz', record.source_sha256)

    def motion_file(self, asset_id: str) -> Path:
        """Return only hash-verified generated safe NPZ, with unchanged matching weights."""
        record = self.get_motion(asset_id)
        self.motion_source(asset_id)
        model = Path(record.model_path)
        if not model.is_file() or digest(model) != record.model_sha256:
            raise StudioError('changed_model', 'Matching SMPL-X weights are missing or changed; restore recorded bytes', 409)
        with self._connection() as db:
            row = db.execute('SELECT normalized_sha256 FROM motion_assets WHERE asset_id=?', (asset_id,)).fetchone()
        return self._motion_bytes(asset_id, 'normalized.npz', row['normalized_sha256'])

    def _motion_bytes(self, asset_id, name, expected):
        folder = self.roots.assets / 'motions' / asset_id
        path = folder / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(self.roots.assets) or digest(path) != expected:
            raise StudioError('changed_asset', 'Managed motion bytes are missing or changed', 409)
        return path

    def select_motion(self, run_id: str, asset_id: str):
        """Select immutable motion for a fresh draft revision; starts no computation."""
        run = self.get_run(run_id)
        if run.read_only:
            raise StudioError('read_only', 'Historical registrations are read-only', 409)
        self.motion_file(asset_id)
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            revision = db.execute('SELECT revision_id FROM runs WHERE run_id=?', (run_id,)).fetchone()['revision_id']
            previous = db.execute('SELECT asset_id FROM motion_selections WHERE run_id=? AND revision_id<=? '
                                  'ORDER BY revision_id DESC LIMIT 1', (run_id, revision)).fetchone()
            if previous is None or previous['asset_id'] != asset_id:
                revision = f'r{int(revision[1:]) + 1:04d}'
                folder = self.roots.runs / run_id / revision
                folder.mkdir(parents=True, exist_ok=True)
                with (folder / 'motion.json').open('x') as stream:
                    json.dump(asdict(self.get_motion(asset_id)), stream, sort_keys=True, indent=2)
                db.execute('INSERT INTO motion_selections VALUES (?, ?, ?)', (run_id, revision, asset_id))
                db.execute('UPDATE runs SET revision_id=? WHERE run_id=?', (revision, run_id))
        return self.get_run(run_id)
