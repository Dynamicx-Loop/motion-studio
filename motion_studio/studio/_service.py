"""Persistent application state. Each operation owns a short SQLite transaction."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import uuid

from ._robots import _RobotOperations

from ._history import confined_file, digest, inspect_bundle
from ._contracts import RunRecord, Stage, StageState, StorageRoots, StudioError
from ._motion import _MotionOperations


class Studio(_RobotOperations, _MotionOperations):
    def __init__(self, state_root: Path, *, history_roots: tuple[Path, ...] = (),
                 robot_python: Path | None = None, smplx_model_dir: Path | None = None):
        self.robot_python = Path(robot_python) if robot_python else Path('/data/workspace/motion_studio/externals/UMR/.venv/bin/python')
        state = Path(state_root).resolve()
        self.history_roots = tuple(Path(p).resolve() for p in history_roots)
        if any(state.is_relative_to(p) or p.is_relative_to(state) for p in self.history_roots):
            raise StudioError('storage_overlap', 'State and historical roots must be separate')
        self.roots = StorageRoots(state, state / 'assets', state / 'runs', state / 'exports')
        for path in (state, self.roots.assets, self.roots.runs, self.roots.exports):
            path.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS runs ('
                       'run_id TEXT PRIMARY KEY, revision_id TEXT, name TEXT, kind TEXT,'
                       'created_at TEXT, inspection_path TEXT UNIQUE)')
            db.execute('CREATE TABLE IF NOT EXISTS history_files ('
                       'run_id TEXT, name TEXT, sha256 TEXT, PRIMARY KEY(run_id, name))')
            db.execute('CREATE TABLE IF NOT EXISTS robot_selections ('
                       'run_id TEXT, revision_id TEXT, asset_id TEXT, pose_id TEXT, '
                       'PRIMARY KEY(run_id, revision_id))')
            db.execute('CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT)')

        self._init_motions(smplx_model_dir)

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.roots.state / 'studio.sqlite3', timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_draft(self, name: str) -> RunRecord:
        """Persist a named empty draft with revision r0001; launches no computation."""
        name = self._name(name)
        run_id = uuid.uuid4().hex
        with self._connection() as db:
            db.execute('INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)',
                       (run_id, 'r0001', name, 'draft', datetime.now(timezone.utc).isoformat(), None))
        return self.get_run(run_id)

    def register_history(self, name: str, inspection: Path) -> RunRecord:
        """Register a saved inspection under an explicitly permitted root, read-only.

        Hashes only referenced files, never writes to the inspection, never executes
        its scripts. Duplicate registration returns the existing identity.
        """
        name = self._name(name)
        folder = Path(inspection).resolve()
        if not any(folder.is_relative_to(root) for root in self.history_roots):
            raise StudioError('invalid_path', 'Inspection is outside configured historical roots')
        files = inspect_bundle(folder)
        run_id = uuid.uuid4().hex
        with self._connection() as db:
            existing = db.execute('SELECT run_id FROM runs WHERE inspection_path = ?', (str(folder),)).fetchone()
            if existing:
                run_id = existing['run_id']
            else:
                db.execute('INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)',
                           (run_id, 'r0001', name, 'historical', datetime.now(timezone.utc).isoformat(), str(folder)))
                db.executemany('INSERT INTO history_files VALUES (?, ?, ?)',
                               ((run_id, key, value) for key, value in files.items()))
        return self.get_run(run_id)

    def rename_draft(self, run_id: str, name: str) -> RunRecord:
        record = self.get_run(run_id)
        if record.read_only:
            raise StudioError('read_only', 'Historical registrations are read-only', 409)
        name = self._name(name)
        with self._connection() as db:
            db.execute('UPDATE runs SET name = ? WHERE run_id = ?', (name, run_id))
        return self.get_run(run_id)

    def inspection_file(self, run_id: str, name: str) -> Path:
        """Resolve only registered data files; reject missing, escaping or changed bytes."""
        record = self.get_run(run_id)
        if record.inspection_path is None:
            raise StudioError('not_found', 'Run has no saved inspection', 404)
        folder = Path(record.inspection_path)
        if not any(folder.is_relative_to(root) for root in self.history_roots):
            raise StudioError('invalid_path', 'Historical root is no longer permitted')
        with self._connection() as db:
            row = db.execute('SELECT sha256 FROM history_files WHERE run_id = ? AND name = ?',
                             (run_id, name)).fetchone()
        if row is None:
            raise StudioError('not_found', 'File is not a registered inspection artifact', 404)
        path = confined_file(folder, name)
        if digest(path) != row['sha256']:
            raise StudioError('changed_artifact', 'Historical artifact changed since registration', 409)
        return path

    def list_runs(self) -> tuple[RunRecord, ...]:
        with self._connection() as db:
            return tuple(self._record(row) for row in db.execute('SELECT * FROM runs ORDER BY created_at, run_id'))

    def get_run(self, run_id: str) -> RunRecord:
        with self._connection() as db:
            row = db.execute('SELECT * FROM runs WHERE run_id = ?', (run_id,)).fetchone()
        if row is None:
            raise StudioError('not_found', 'Run does not exist', 404)
        return self._record(row)

    def select(self, run_id: str) -> RunRecord:
        """Persist selection independently of browser storage; return the selected run."""
        result = self.get_run(run_id)
        with self._connection() as db:
            db.execute('INSERT OR REPLACE INTO preferences VALUES (?, ?)', ('selected_run_id', run_id))
        return result

    def selected_run_id(self) -> str | None:
        with self._connection() as db:
            row = db.execute('SELECT value FROM preferences WHERE key = ?', ('selected_run_id',)).fetchone()
        return row['value'] if row else None

    @staticmethod
    def _name(name):
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise StudioError('invalid_name', 'Name must contain 1–120 characters')
        return name.strip()

    def _record(self, row):
        historical = row['kind'] == 'historical'
        inspection_url = f"/inspection/{row['run_id']}/index.html"
        with self._connection() as db:
            robot = self._robot_selection(db, row['run_id'], row['revision_id'])
            motion = db.execute('SELECT asset_id FROM motion_selections WHERE run_id=? AND revision_id<=? '
                                'ORDER BY revision_id DESC LIMIT 1', (row['run_id'], row['revision_id'])).fetchone()
        stages = tuple(
            StageState(stage, 'available', inspection_url)
            if historical and stage == Stage.MOTION else
            StageState(stage, 'available')
            if not historical and robot and stage == Stage.PREPARATION else StageState(stage)
            for stage in Stage
        )
        return RunRecord(row['run_id'], row['revision_id'], row['name'], row['kind'],
                         historical, row['created_at'], stages, row['inspection_path'],
                         robot_asset_id=robot['asset_id'] if robot else None,
                         robot_pose_id=robot['pose_id'] if robot else None,
                         motion_asset_id=motion['asset_id'] if motion else None)
