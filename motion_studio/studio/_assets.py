"""Asset library operations over immutable robot/motion import contracts."""
from dataclasses import asdict
import base64
import binascii
import io
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

from ._contracts import StudioError

MAX_UPLOAD = 128 * 1024 * 1024


class _AssetOperations:
    def asset_catalog(self):
        from motion_studio.integrations.umr_assets import catalog
        from motion_studio.integrations.menagerie_assets import astro_catalog
        result = catalog(self.native_adapter.checkout)
        result['robots'].append(astro_catalog())
        result['source'] = 'Local pinned UMR examples and bundled Astro P2; separate asset terms apply.'
        self._sample_motion_table()
        with self._connection() as db:
            imported = dict(db.execute('SELECT catalog_id, asset_id FROM sample_motion_assets'))
        for item in result['motions']:
            if item['id'] in imported:
                asset = self.get_motion(imported[item['id']])
                item.update(asset_id=asset.asset_id, frame_count=asset.frame_count, fps=asset.fps)
        return result

    def _sample_motion_table(self):
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS sample_motion_assets ('
                       'catalog_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL)')

    def add_builtin_robot(self, key):
        """Verify pinned source bytes, import closure, return unsaved named T-pose."""
        if key == 'astro':
            from motion_studio.integrations.menagerie_assets import portable_astro, astro_pose
            with portable_astro() as (source, preset, originals):
                asset = self._import_robot(source, False, provenance_files=originals)
                pose = astro_pose(asset, preset)
                self._robot_qpos(asset, pose.qpos)
            return {'asset':asdict(asset), 'pose':asdict(pose)}
        from motion_studio.integrations.umr_assets import portable_robot, robot_preset
        with portable_robot(self.native_adapter.checkout, key) as (source, config, originals):
            asset = self._import_robot(source, True, provenance_files=originals)
        pose = robot_preset(asset, config)
        self._robot_qpos(asset, pose.qpos)
        return {'asset':asdict(asset), 'pose':asdict(pose)}

    def add_sample_motion(self, key):
        from motion_studio.integrations.umr_assets import sample_source
        with sample_source(self.native_adapter.checkout, key) as (source, metadata):
            asset = self.import_motion(source, metadata=metadata)
        self._sample_motion_table()
        with self._connection() as db:
            db.execute('INSERT OR REPLACE INTO sample_motion_assets VALUES (?, ?)', (key, asset.asset_id))
        return asset

    def upload_robot(self, files, *, entry_path='', derive_free_root=False):
        """Import browser bytes or one ZIP without trusting client filesystem paths.

        A folder retains relative paths. Files are bounded and unpacked in isolated
        temporary storage; only the validated MJCF closure becomes a managed asset.
        Nothing is executed other than the independent compiler on validated XML.
        """
        if not isinstance(files, list) or not 1 <= len(files) <= 2048:
            raise StudioError('invalid_upload', 'Choose 1–2048 MJCF/mesh files or one ZIP')
        members, total = {}, 0
        def add(name, data):
            nonlocal total
            path = PurePosixPath(name)
            if (not isinstance(name, str) or not name or path.is_absolute() or '\\' in name
                    or any(p in ('..', '.', '') for p in name.split('/')) or ':' in name or name in members):
                raise StudioError('invalid_upload', 'Upload has duplicate or escaping paths')
            total += len(data)
            if total > MAX_UPLOAD:
                raise StudioError('invalid_upload', 'Unpacked upload exceeds 128 MiB')
            members[name] = data
        try:
            for item in files:
                if not isinstance(item, dict) or set(item) != {'path', 'data'}:
                    raise ValueError('Expected file path and base64 data')
                name, data = item['path'], base64.b64decode(item['data'], validate=True)
                if len(files) == 1 and str(name).lower().endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(data)) as archive:
                        infos = archive.infolist()
                        if len(infos) > 2048 or sum(i.file_size for i in infos) > MAX_UPLOAD:
                            raise ValueError('ZIP exceeds 2048 files or 128 MiB')
                        for info in infos:
                            if info.is_dir():
                                continue
                            if info.external_attr >> 16 & 0o170000 == 0o120000:
                                raise ValueError('ZIP symlinks are unsupported')
                            add(info.filename, archive.read(info))
                else:
                    add(name, data)
        except (ValueError, TypeError, KeyError, binascii.Error, zipfile.BadZipFile, RuntimeError) as error:
            raise StudioError('invalid_upload', f'Invalid uploaded file bundle: {error}') from error
        entries = [name for name in members if name.lower().endswith('.xml')]
        if not entry_path and len(entries) == 1:
            entry_path = entries[0]
        if entry_path not in entries:
            raise StudioError('invalid_upload', 'Choose the main MJCF entry path. XML files: ' + ', '.join(entries[:20]))
        with tempfile.TemporaryDirectory(prefix='studio-upload-', dir=self.roots.assets) as tmp:
            root = Path(tmp)
            for name, data in members.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            if not isinstance(derive_free_root, bool):
                raise StudioError('invalid_upload', 'derive_free_root must be a boolean')
            from ._uploaded_robots import portable_upload
            source, originals = portable_upload(root, entry_path, members)
            return self._import_robot(source, derive_free_root, provenance_files=originals)
