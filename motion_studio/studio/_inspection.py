"""Fresh inspection derivatives: explicit builds and hash-checked offline viewing."""
import json
from pathlib import Path
import subprocess
import uuid

from ._contracts import StudioError
from ._history import confined_file, digest


class _InspectionOperations:
    def _init_inspections(self):
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS inspections ('
                       'run_id TEXT, revision_id TEXT, stage TEXT, folder TEXT, files TEXT, '
                       'PRIMARY KEY(run_id, revision_id, stage))')

    def build_inspection(self, run_id, stage, *, revision_id=None):
        """Build a fresh standalone bundle; never train, solve or alter source stages.

        Captures one immutable revision. Existing completed bundles view without
        licensed weights/runtime. Rebuild is explicit and always allocates a new
        directory. Failure logs stay in the fresh folder; it is never published.
        """
        from motion_studio.integrations.umr_studio_inspection import InspectionInputs, export_inspection
        run = self.get_run(run_id, revision_id)
        revision = run.revision_id
        native_stage = 'retargeting' if stage == 'motion' else stage
        if native_stage not in ('sampling', 'training', 'binding', 'retargeting'):
            raise StudioError('invalid_stage', 'Choose sampling, training, binding or motion')
        receipt = self.stage_receipt(run_id, revision, native_stage)
        receipts = {**receipt['dependencies'], native_stage:receipt}
        paths = {s:self.stage_artifacts(run_id, revision, s) for s in receipts}
        folder = self.roots.exports/run_id/revision/native_stage/uuid.uuid4().hex
        inputs = InspectionInputs(run_id, revision, native_stage, receipts, paths)
        try:
            result = export_inspection(inputs, folder, checkout=self.native_adapter.checkout,
                                       python=self.robot_python)
            # Publication rechecks recursively verified dependencies, including
            # bytes changed while the CPU reconstruction was running.
            if self.stage_receipt(run_id, revision, native_stage) != receipt:
                raise StudioError('changed_artifact', 'Stage changed during inspection export', 409)
            files = json.loads((result/'files.json').read_text())
            files['files.json'] = digest(result/'files.json')
            with self._connection() as db:
                db.execute('INSERT OR REPLACE INTO inspections VALUES (?, ?, ?, ?, ?)',
                           (run_id,revision,native_stage,str(result),json.dumps(files)))
        except StudioError:
            raise
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise StudioError('inspection_failed', f'Inspection export failed; retained logs: {folder}: {error}', 409) from error
        return {'run_id':run_id,'revision_id':revision,'stage':native_stage,'path':str(result),
                'url':self._inspection_url(run_id,revision,native_stage),
                'files_url':self._inspection_url(run_id,revision,native_stage).replace('index.html','files.json')}

    def _inspection_url(self, run_id, revision, stage):
        if stage == 'motion':
            stage = 'retargeting'
        with self._connection() as db:
            row = db.execute('SELECT folder FROM inspections WHERE run_id=? AND revision_id=? AND stage=?',
                             (run_id,revision,stage)).fetchone()
        return f'/inspection/{run_id}/{revision}/{stage}/index.html' if row else None

    def inspection_is_historical(self, run_id):
        """Route saved viewers without hydrating or revalidating native stages."""
        with self._connection() as db:
            row = db.execute('SELECT kind FROM runs WHERE run_id=?', (run_id,)).fetchone()
        if row is None:
            raise StudioError('not_found', 'Run does not exist', 404)
        return row['kind'] == 'historical'

    def exported_inspection_file(self, run_id, revision, stage, name):
        """View a previously built closed bundle, independent of source/runtime/model availability."""
        # Only the requested bundle resource needs verification during streaming.
        self.inspection_is_historical(run_id)
        with self._connection() as db:
            row = db.execute('SELECT folder, files FROM inspections WHERE run_id=? AND revision_id=? AND stage=?',
                             (run_id,revision,stage)).fetchone()
        if not row:
            raise StudioError('not_found','Stage has no built inspection',404)
        files = json.loads(row['files'])
        if name not in files:
            raise StudioError('not_found','File is not a registered inspection resource',404)
        folder = Path(row['folder']).resolve()
        if not folder.is_relative_to(self.roots.exports):
            raise StudioError('invalid_path','Export root is outside managed storage')
        path = confined_file(folder,name)
        if digest(path) != files[name]:
            raise StudioError('changed_artifact','Inspection resource changed after export',409)
        return path
