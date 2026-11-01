"""Versioned, per-file verified source mesh derivatives, independent of runs."""
import json
import math
from pathlib import Path, PurePosixPath
import struct
import subprocess
import uuid

from ._contracts import StudioError
from ._history import digest
from ._preview_builds import _build_lock

SCHEMA = 'motion-studio-source-mesh-v1'


def _resource(folder, name):
    if (not isinstance(name, str) or not name or '\\' in name
            or PurePosixPath(name).name != name or name in {'.', '..'}):
        raise StudioError('invalid_path', 'Source mesh resources must be local file names')
    path = folder / name
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(folder.resolve()):
        raise StudioError('changed_artifact', 'Source mesh resource is missing or escapes its cache', 409)
    return path


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value):
    return isinstance(value, list) and len(value) == 3 and all(_finite(v) for v in value)


def inspect_mesh_preview(folder, asset):
    """Validate worker output/size/timeline/topology before registering its hashes.

    Scientific runtimes are unnecessary for reading or validating this format.
    Only the manifest, native topology and bounded vertex chunks are public.
    """
    try:
        manifest = _resource(folder, 'manifest.json')
        if manifest.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('Manifest exceeds 8 MiB')
        data = json.loads(manifest.read_text())
        count, vertices, faces = data['frame_count'], data['vertex_count'], data['face_count']
        if (data['schema'] != SCHEMA or type(count) is not int or count != asset.frame_count
                or not 1 <= count <= 20000 or not _finite(data['fps']) or data['fps'] != asset.fps
                or type(vertices) is not int or not 1 <= vertices <= 20000
                or type(faces) is not int or not 1 <= faces <= 40000
                or data['chunk_size'] != 64 or data['quantization_m'] != .0001
                or not _finite(data['max_vertex_axis_error_m'])
                or not 0 <= data['max_vertex_axis_error_m'] <= 5.1e-5
                or not _finite(data['ground_z']) or data['thumbnail_frame'] != 0
                or data['zero_source_finger_pose'] is not True
                or data['input_up_axis'] != asset.up_axis
                or data['source_frame_start'] != 0 or data['source_frame_stop_exclusive'] != count
                or data['coordinates'] != 'Z-up metres; original source translation; no resampling'
                or data['encoding'] != 'int16 little endian; frame, vertex, xyz; root-relative Z-up metres'):
            raise ValueError('Unsupported source mesh schema, dimensions or timing')
        roots, bounds = data['root_positions'], data['bounds']
        if (not isinstance(roots, list) or len(roots) != count or not all(_vector(v) for v in roots)
                or not _vector(bounds['min']) or not _vector(bounds['max'])
                or any(a > b for a, b in zip(bounds['min'], bounds['max']))
                or data['ground_z'] != bounds['min'][2]):
            raise ValueError('Invalid source mesh roots/bounds')
        from motion_studio.integrations.umr_stages import PIN
        if (data['source_revision'] != PIN or not isinstance(data['inputs_sha256'], dict)
                or data['inputs_sha256'].get(asset.model_path) != asset.model_sha256):
            raise ValueError('Source mesh model/revision provenance differs from the asset')
        topology = _resource(folder, data['faces'])
        if topology.stat().st_size != faces * 3 * 4:
            raise ValueError('Triangle topology byte count differs')
        if any(index >= vertices for (index,) in struct.iter_unpack('<I', topology.read_bytes())):
            raise ValueError('Triangle topology references missing vertices')
        chunks, names, end = data['chunks'], {'manifest.json', data['faces']}, 0
        if not isinstance(chunks, list) or len(chunks) != math.ceil(count / 64):
            raise ValueError('Source mesh chunks must cover all source frames')
        for chunk in chunks:
            length = min(64, count - end)
            if (type(chunk['start']) is not int or chunk['start'] != end
                    or type(chunk['count']) is not int or chunk['count'] != length
                    or chunk['file'] in names):
                raise ValueError('Source mesh chunks must have a unique contiguous exact timeline')
            path = _resource(folder, chunk['file'])
            if path.stat().st_size != length * vertices * 3 * 2:
                raise ValueError('Vertex chunk byte count differs')
            names.add(chunk['file'])
            end += length
        return {name: digest(_resource(folder, name)) for name in sorted(names)}
    except (KeyError, TypeError, ValueError, OSError) as error:
        if isinstance(error, StudioError):
            raise
        raise StudioError('invalid_preview', f'Invalid source mesh preview: {error}', 409) from error


class _SourceMeshPreviewOperations:
    def _source_mesh_tables(self):
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS source_mesh_previews ('
                       'asset_id TEXT, schema TEXT, path TEXT NOT NULL, PRIMARY KEY(asset_id, schema))')
            db.execute('CREATE TABLE IF NOT EXISTS source_mesh_files ('
                       'asset_id TEXT, schema TEXT, name TEXT, sha256 TEXT NOT NULL, '
                       'PRIMARY KEY(asset_id, schema, name))')

    def build_source_mesh_preview(self, asset_id):
        """Cache all exact source mesh frames on CPU. Never selects or edits a run.

        Persistent versioned derivatives remain viewable without models, source
        assets or a native runtime. Concurrent callers share a single build.
        """
        with _build_lock(self.roots.state, (SCHEMA, asset_id)):
            self._source_mesh_tables()
            asset = self.get_motion(asset_id)
            with self._connection() as db:
                exists = db.execute('SELECT 1 FROM source_mesh_previews WHERE asset_id=? AND schema=?',
                                    (asset_id, SCHEMA)).fetchone()
            if not exists:
                source = self.motion_file(asset_id)
                from motion_studio.integrations.umr_source_preview import build_source_mesh_preview
                destination = self.roots.exports / 'source-mesh-v1' / asset_id / uuid.uuid4().hex
                try:
                    path = build_source_mesh_preview(source, asset, destination,
                        checkout=self.native_adapter.checkout, python=self.robot_python)
                    self.motion_file(asset_id)
                    if path != destination / 'manifest.json':
                        raise ValueError('Native preview returned an unexpected manifest path')
                    files = inspect_mesh_preview(destination, asset)
                    data = json.loads(path.read_text())
                    if data['inputs_sha256'].get(str(source)) != digest(source):
                        raise ValueError('Source mesh motion provenance differs from the managed asset')
                    with self._connection() as db:
                        db.execute('INSERT INTO source_mesh_previews VALUES (?, ?, ?)',
                                   (asset_id, SCHEMA, str(destination)))
                        db.executemany('INSERT INTO source_mesh_files VALUES (?, ?, ?, ?)',
                            [(asset_id, SCHEMA, name, sha) for name, sha in files.items()])
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    raise StudioError('preview_failed', f'CPU source mesh preview failed; log: {destination / "build.log"}: {error}', 409) from error
            self.source_mesh_preview_file(asset_id)
            return {'asset_id': asset_id, 'frame_count': asset.frame_count, 'fps': asset.fps,
                    'schema': SCHEMA, 'url': f'/api/motions/{asset_id}/mesh-preview-data/manifest.json'}

    def source_mesh_preview_file(self, asset_id, name='manifest.json'):
        """Read only independently hash-registered resources, no reconstruction."""
        self._source_mesh_tables()
        self.get_motion(asset_id)
        with self._connection() as db:
            row = db.execute('SELECT p.path, f.sha256 FROM source_mesh_previews p '
                'JOIN source_mesh_files f USING(asset_id, schema) '
                'WHERE p.asset_id=? AND p.schema=? AND f.name=?', (asset_id, SCHEMA, name)).fetchone()
        if row is None:
            raise StudioError('not_found', 'Build this source mesh preview first or request a registered resource', 404)
        folder = Path(row['path'])
        base = self.roots.exports / 'source-mesh-v1'
        if not folder.is_relative_to(base) or not folder.resolve().is_relative_to(base.resolve()):
            raise StudioError('changed_artifact', 'Source mesh cache escaped its registered root', 409)
        if any(p.is_symlink() for p in (folder, *folder.parents) if p.is_relative_to(self.roots.exports)):
            raise StudioError('changed_artifact', 'Source mesh cache contains a symbolic link', 409)
        path = _resource(folder, name)
        if digest(path) != row['sha256']:
            raise StudioError('changed_artifact', 'Source mesh bytes are missing or changed', 409)
        return path
