"""Hash-registered source-joint preview derivatives; immutable inputs stay intact."""
from pathlib import Path
import subprocess
import uuid

from ._contracts import StudioError
from ._history import digest
from ._preview_builds import _build_lock
from ._source_mesh_preview import _SourceMeshPreviewOperations


class _SourcePreviewOperations(_SourceMeshPreviewOperations):
    def _source_preview_table(self):
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS source_previews ('
                       'asset_id TEXT PRIMARY KEY, path TEXT NOT NULL, sha256 TEXT NOT NULL)')

    def build_source_preview(self, asset_id):
        """Build/cache all source frames on CPU, without selecting or changing a run.

        Skeleton shows the first 22 SMPL-X joints, Z-up metres, exact saved FPS.
        Each derivative is registered independently of its mutable JSON bytes.
        """
        # Recheck the persistent cache only after acquiring the asset's lock;
        # repeated HTTP requests share one CPU reconstruction, even if several
        # Studio instances serve the same managed state in this process.
        with _build_lock(self.roots.state, asset_id):
            return self._build_source_preview_locked(asset_id)

    def _build_source_preview_locked(self, asset_id):
        self._source_preview_table()
        asset = self.get_motion(asset_id)
        if asset.frame_count > 20000:
            raise StudioError('preview_limit', 'Source preview supports at most 20000 frames', 409)
        with self._connection() as db:
            existing = db.execute('SELECT path FROM source_previews WHERE asset_id=?', (asset_id,)).fetchone()
        if not existing:
            source = self.motion_file(asset_id)
            from motion_studio.integrations.umr_source_preview import build_source_preview
            destination = self.roots.exports / 'source-preview' / asset_id / uuid.uuid4().hex
            try:
                path = build_source_preview(source, asset, destination,
                    checkout=self.native_adapter.checkout, python=self.robot_python)
                self.motion_file(asset_id)
                with self._connection() as db:
                    db.execute('INSERT OR IGNORE INTO source_previews VALUES (?, ?, ?)',
                               (asset_id, str(path), digest(path)))
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                raise StudioError('preview_failed', f'CPU source preview failed; log: {destination / "build.log"}: {error}', 409) from error
        self.source_preview_file(asset_id)
        return {'asset_id': asset_id, 'frame_count': asset.frame_count, 'fps': asset.fps,
                'url': f'/api/motions/{asset_id}/preview-data'}

    def source_preview_file(self, asset_id):
        """Read only registered source previews, with exact hash/path verification."""
        self._source_preview_table()
        self.get_motion(asset_id)
        with self._connection() as db:
            row = db.execute('SELECT * FROM source_previews WHERE asset_id=?', (asset_id,)).fetchone()
        if row is None:
            raise StudioError('not_found', 'Build this source preview first', 404)
        path = Path(row['path'])
        if (not path.resolve().is_relative_to(self.roots.exports / 'source-preview')
                or not path.is_file() or path.is_symlink() or digest(path) != row['sha256']):
            raise StudioError('changed_artifact', 'Source preview bytes are missing or changed', 409)
        return path
