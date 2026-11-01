"""Robot import operations. Public caller seam is Studio, not this private mixin."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

from ._contracts import RunRecord, StudioError
from ._robot_assets import RobotAsset, RobotPose, RobotPosePreset, decode_asset, hash_file, import_asset, runtime


class _RobotOperations:
    def import_robot(self, source_path: Path, *, derive_free_root: bool = False) -> RobotAsset:
        """Copy a complete MJCF closure and compile it in the configured pinned runtime.

        Imports never edit originals. Only a single named-body articulated root,
        bounded hinges and one free joint are accepted. Metadata is radians/metres.
        """
        if not isinstance(derive_free_root, bool):
            raise StudioError('invalid_robot', 'derive_free_root must be a boolean')
        return self._import_robot(source_path, derive_free_root)

    def _import_robot(self, source_path, derive_free_root, *, provenance_files=None):
        asset = import_asset(self.roots.assets, self.robot_python, source_path,
                             derive_free_root, self.get_robot, provenance_files=provenance_files)
        # Hash trusted compiler output, never bootstrap trust from a mutable manifest.
        manifest = json.dumps(asdict(asset), allow_nan=False).encode()
        self._robot_metadata_digest(asset.asset_id, hashlib.sha256(manifest).hexdigest())
        return self.get_robot(asset.asset_id)

    def _robot_metadata_digest(self, asset_id, register=None):
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS robot_assets ('
                       'asset_id TEXT PRIMARY KEY, manifest_sha256 TEXT NOT NULL)')
            if register is not None:
                db.execute('INSERT OR IGNORE INTO robot_assets VALUES (?, ?)', (asset_id, register))
            row = db.execute('SELECT manifest_sha256 FROM robot_assets WHERE asset_id=?',
                             (asset_id,)).fetchone()
        if row is None:
            raise StudioError('unverified_asset', 'Robot asset has no trusted metadata registration; '
                              'reimport into a fresh managed state directory', 409)
        return row['manifest_sha256']

    def list_robots(self) -> tuple[RobotAsset, ...]:
        folder = self.roots.assets / 'robots'
        return tuple(self.get_robot(p.name) for p in sorted(folder.glob('*')) if (p / 'asset.json').is_file())

    def get_robot(self, asset_id: str) -> RobotAsset:
        home = self._robot_home(asset_id)
        try:
            path = home / 'asset.json'
            raw = path.read_bytes()
        except FileNotFoundError as error:
            raise StudioError('not_found', 'Robot asset does not exist', 404) from error
        expected = self._robot_metadata_digest(asset_id)
        if not path.resolve().is_relative_to(home) or hashlib.sha256(raw).hexdigest() != expected:
            raise StudioError('changed_artifact', 'Managed robot metadata changed', 409)
        return decode_asset(json.loads(raw))

    def _robot_home(self, asset_id):
        if not isinstance(asset_id, str) or len(asset_id) != 64 or any(c not in '0123456789abcdef' for c in asset_id):
            raise StudioError('invalid_robot_id', 'Robot ID must be a SHA-256 hex string')
        return self.roots.assets / 'robots' / asset_id

    def robot_file(self, asset_id: str, name: str) -> Path:
        """Resolve a recorded artifact; native model handoff verifies its full closure."""
        asset = self.get_robot(asset_id)
        home = self._robot_home(asset_id)
        path = home / name
        if name not in asset.files or not path.resolve().is_relative_to(home) or not path.is_file():
            raise StudioError('not_found', 'Robot artifact is not registered', 404)
        names = asset.files if name == 'source/__studio_model.xml' else (name,)
        for member in names:
            candidate = home / member
            if (not candidate.resolve().is_relative_to(home) or not candidate.is_file()
                    or hash_file(candidate) != asset.files[member]):
                raise StudioError('changed_artifact', 'Managed robot bytes changed', 409)
        return path

    def preview_robot(self, asset_id: str, qpos: list[float] | tuple[float, ...] | None = None) -> dict:
        asset = self.get_robot(asset_id)
        values = self._robot_qpos(asset, list(asset.default_qpos) if qpos is None else qpos)
        model = self.robot_file(asset_id, 'source/__studio_model.xml')
        return runtime(self.robot_python, {'operation': 'preview', 'model': str(model), 'qpos': values})

    @staticmethod
    def _robot_qpos(asset, values):
        if not isinstance(values, (list, tuple)) or len(values) != len(asset.default_qpos):
            raise StudioError('invalid_pose', 'Pose qpos must match compiled model nq')
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in values):
            raise StudioError('invalid_pose', 'Pose values must be finite numbers')
        if abs(sum(x*x for x in values[3:7]) - 1) > 1e-6:
            raise StudioError('invalid_pose', 'Root quaternion wxyz must have unit norm')
        for joint in asset.joints:
            if not joint.minimum_rad <= values[joint.qpos_index] <= joint.maximum_rad:
                raise StudioError('invalid_pose', f'{joint.name} exceeds compiled limits in radians')
        return tuple(float(x) for x in values)

    def official_robot_pose(self, asset_id: str) -> RobotPosePreset:
        """Load unsaved pinned G1 pose values, refusing other or changed robots.

        No revision is created until the caller explicitly saves these values.
        Generic imported robots retain the normal numeric/named-pose workflow.
        """
        preset = self.native_adapter.official_pose(self, asset_id)
        self._robot_qpos(self.get_robot(asset_id), preset.qpos)
        return preset

    def list_robot_poses(self, asset_id: str) -> tuple[RobotPose, ...]:
        self.get_robot(asset_id)
        folder = self._robot_home(asset_id) / 'poses'
        return tuple(self.get_robot_pose(asset_id, p.stem) for p in sorted(folder.glob('*.json')))

    def get_robot_pose(self, asset_id: str, pose_id: str) -> RobotPose:
        self.get_robot(asset_id)
        if not isinstance(pose_id, str) or len(pose_id) != 64 or any(x not in '0123456789abcdef' for x in pose_id):
            raise StudioError('invalid_pose', 'Pose ID must be a SHA-256 hex string')
        try:
            value = json.loads((self._robot_home(asset_id) / 'poses' / (pose_id + '.json')).read_text())
        except FileNotFoundError as error:
            raise StudioError('not_found', 'Named pose does not exist', 404) from error
        payload = {key: value[key] for key in ('asset_id', 'name', 'torso_body', 'qpos')}
        if hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest() != pose_id:
            raise StudioError('changed_artifact', 'Named pose bytes changed', 409)
        return RobotPose(**{**value, 'qpos': tuple(value['qpos'])})

    def save_robot_pose(self, run_id: str, asset_id: str, *, name: str,
                        qpos: list[float] | tuple[float, ...], torso_body: str) -> RunRecord:
        """Save an immutable named pose and select it in a fresh draft revision.

        Root XYZ is metres, root orientation quaternion wxyz; bounded hinges radians.
        Existing pose files and prior revision records are never overwritten.
        """
        run = self.get_run(run_id)
        if run.read_only:
            raise StudioError('read_only', 'Historical registrations are read-only', 409)
        asset = self.get_robot(asset_id)
        name = self._name(name)
        values = self._robot_qpos(asset, qpos)
        if torso_body not in asset.bodies:
            raise StudioError('invalid_pose', 'Select a named robot body for torso/centering')
        payload = dict(asset_id=asset_id, name=name, torso_body=torso_body, qpos=values)
        pose_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        pose = RobotPose(pose_id=pose_id, **payload)
        home = self._robot_home(asset_id) / 'poses'
        home.mkdir(exist_ok=True)
        try:
            with (home / (pose_id + '.json')).open('x') as stream:
                json.dump(asdict(pose), stream, allow_nan=False)
        except FileExistsError:
            self.get_robot_pose(asset_id, pose_id)
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM runs WHERE run_id = ?', (run_id,)).fetchone()
            selected = self._robot_selection(db, run_id, row['revision_id'])
            if selected and selected['pose_id'] == pose_id:
                return self.get_run(run_id)
            revision = f"r{int(row['revision_id'][1:]) + 1:04d}"
            folder = self.roots.runs / run_id / revision
            folder.mkdir(parents=True, exist_ok=True)
            with (folder / 'robot.json').open('x') as stream:
                json.dump(dict(asset_id=asset_id, pose_id=pose_id), stream)
            db.execute('INSERT INTO robot_selections VALUES (?, ?, ?, ?)',
                       (run_id, revision, asset_id, pose_id))
            db.execute('UPDATE runs SET revision_id = ? WHERE run_id = ?', (revision, run_id))
        return self.get_run(run_id)

    @staticmethod
    def _robot_selection(db, run_id, revision):
        return db.execute('SELECT * FROM robot_selections WHERE run_id = ? AND revision_id <= ? '
                          'ORDER BY revision_id DESC LIMIT 1', (run_id, revision)).fetchone()
