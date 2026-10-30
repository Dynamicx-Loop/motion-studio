"""Immutable revision discovery and independent persisted viewing selection."""
import json
import re

from ._contracts import StageState, StudioError
from motion_studio.integrations.umr_stages import STAGES, canonical_hash


class _RevisionOperations:
    def _init_revisions(self):
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS revisions ('
                       'run_id TEXT, revision_id TEXT, created_at TEXT, '
                       'PRIMARY KEY(run_id, revision_id))')
            # Migrate pre-lifecycle states without rewriting any source or result.
            db.execute("INSERT OR IGNORE INTO revisions SELECT run_id, 'r0001', created_at FROM runs")
            db.execute('INSERT OR IGNORE INTO revisions SELECT run_id, revision_id, created_at FROM runs')
            for table in ('robot_selections', 'motion_selections', 'execution_settings', 'stage_completions'):
                db.execute(f'INSERT OR IGNORE INTO revisions SELECT t.run_id,t.revision_id,r.created_at '
                           f'FROM {table} t JOIN runs r ON t.run_id=r.run_id')
            db.execute("CREATE TRIGGER IF NOT EXISTS revision_created AFTER INSERT ON runs BEGIN "
                       "INSERT INTO revisions VALUES (NEW.run_id,NEW.revision_id,NEW.created_at); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS revision_advanced AFTER UPDATE OF revision_id ON runs "
                       "WHEN NEW.revision_id != OLD.revision_id BEGIN INSERT INTO revisions VALUES "
                       "(NEW.run_id,NEW.revision_id,strftime('%Y-%m-%dT%H:%M:%f+00:00','now')); "
                       "UPDATE preferences SET value=NEW.revision_id WHERE key='selected_revision_id' "
                       "AND value=OLD.revision_id AND (SELECT value FROM preferences "
                       "WHERE key='selected_run_id')=NEW.run_id; END")

    def list_revisions(self, run_id):
        """Return saved snapshots oldest first; reading never changes the editable head."""
        self.get_run(run_id)
        with self._connection() as db:
            rows = db.execute('SELECT revision_id FROM revisions WHERE run_id=? ORDER BY revision_id', (run_id,)).fetchall()
        return tuple(self.get_run(run_id, row['revision_id']) for row in rows)

    def _revision_row(self, row, revision_id):
        if not isinstance(revision_id, str) or not re.fullmatch(r'r[0-9]{4,}', revision_id):
            raise StudioError('invalid_revision', 'Revision must be a saved rNNNN identity')
        with self._connection() as db:
            found = db.execute('SELECT 1 FROM revisions WHERE run_id=? AND revision_id=?',
                               (row['run_id'], revision_id)).fetchone()
        if found is None:
            raise StudioError('not_found', 'Revision does not exist', 404)
        return {**dict(row), 'revision_id': revision_id, 'is_latest': revision_id == row['revision_id']}

    def select(self, run_id, revision_id=None):
        """Persist viewed run/revision. This never moves the editable latest revision."""
        result = self.get_run(run_id, revision_id)
        with self._connection() as db:
            db.executemany('INSERT OR REPLACE INTO preferences VALUES (?, ?)',
                           [('selected_run_id', run_id), ('selected_revision_id', result.revision_id)])
        return result

    def selected_revision_id(self):
        with self._connection() as db:
            row = db.execute("SELECT value FROM preferences WHERE key='selected_revision_id'").fetchone()
        return row['value'] if row else None

    def _revision_stage(self, run_id, revision_id, stage_state):
        lookup_stage = 'retargeting' if stage_state.stage == 'motion' else stage_state.stage
        if stage_state.status == 'available':
            # The caller already verified availability; read only the source
            # reference here instead of hashing the entire chain a second time.
            with self._connection() as db:
                row = db.execute('SELECT receipt FROM stage_completions '
                                 'WHERE run_id=? AND revision_id=? AND stage=?',
                                 (run_id, revision_id, lookup_stage)).fetchone()
            source = json.loads(row['receipt']).get('source_revision') if row else None
            if source:
                return StageState(stage_state.stage, 'available', stage_state.inspection_url,
                                  'Verified compatible result reused from revision ' + source)
            return stage_state
        with self._connection() as db:
            prior = db.execute('SELECT revision_id FROM stage_completions '
                               'WHERE run_id=? AND stage=? AND revision_id<=? '
                               'ORDER BY revision_id DESC LIMIT 1',
                               (run_id, lookup_stage, revision_id)).fetchone()
        if prior:
            reason = ('Saved output failed receipt or dependency verification; recompute explicitly'
                      if prior['revision_id'] == revision_id else
                      'Input/settings revision changed; affected stages require explicit recomputation. '
                      'Old results remain in revision history.')
            return StageState(stage_state.stage, 'stale', reason=reason)
        return stage_state

    def _carry_settings_stages(self, run_id, parent, revision):
        """Reference an unchanged prefix, retaining the source receipt and exact bytes."""
        before, after = self.get_run(run_id, parent), self.get_run(run_id, revision)
        if (before.robot_asset_id, before.robot_pose_id, before.motion_asset_id) != (
                after.robot_asset_id, after.robot_pose_id, after.motion_asset_id):
            return
        old = self.execution_settings(run_id, parent)
        new = self.execution_settings(run_id, revision)
        affected = {'sampling': 'sampling_seed', 'training': 'epochs', 'binding': None,
                    'retargeting': 'trajectory_filter'}
        for stage in STAGES:
            key = affected[stage]
            if key and old[key] != new[key]:
                break
            receipt = self._receipt(run_id, parent, stage)
            if not receipt:
                break
            reference = {'source_revision': receipt['revision_id'], 'receipt_sha256': canonical_hash(receipt)}
            with self._connection() as db:
                db.execute('INSERT OR IGNORE INTO stage_completions VALUES (?, ?, ?, ?)',
                           (run_id, revision, stage, json.dumps(reference)))

    def _revision_is_current(self, run_id, revision_id):
        # A liveness check must not hash completed multi-hundred-MB prerequisites
        # on every subprocess output/heartbeat. Acceptance verifies those bytes.
        with self._connection() as db:
            row = db.execute('SELECT revision_id FROM runs WHERE run_id=?', (run_id,)).fetchone()
        return row is not None and row['revision_id'] == revision_id
