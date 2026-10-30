"""Persistent local Studio public outcomes; no external scientific runtime."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from motion_studio.studio import Stage, Studio, StudioError


class StudioTests(unittest.TestCase):
    def test_historical_registration_reopens_read_only_without_changing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = self.bundle(root / 'history' / 'g1')
            before = {p.name: p.read_bytes() for p in bundle.iterdir()}
            studio = Studio(root / 'state', history_roots=(root / 'history',))
            historical = studio.register_history('G1 historical reference', bundle)
            reopened = Studio(root / 'state', history_roots=(root / 'history',))
            self.assertEqual(reopened.get_run(historical.run_id), historical)
            self.assertTrue(historical.read_only)
            self.assertEqual(historical.stages[-1].stage, Stage.MOTION)
            self.assertEqual(historical.stages[-1].status, 'available')
            self.assertEqual(reopened.inspection_file(historical.run_id, 'mesh.bin').read_bytes(), b'geometry')
            with self.assertRaisesRegex(StudioError, 'read-only'):
                studio.rename_draft(historical.run_id, 'Changed')
            self.assertEqual(before, {p.name: p.read_bytes() for p in bundle.iterdir()})
            self.assertEqual(studio.register_history('Same', bundle).run_id, historical.run_id)

    def test_history_paths_and_changed_artifacts_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio = Studio(root / 'state', history_roots=(root / 'history',))
            bundle = self.bundle(root / 'elsewhere')
            with self.assertRaisesRegex(StudioError, 'outside'):
                studio.register_history('Escaping', bundle)
            bundle = self.bundle(root / 'history' / 'g1')
            (bundle / 'mesh.bin').unlink()
            (bundle / 'mesh.bin').symlink_to(root / 'elsewhere' / 'mesh.bin')
            with self.assertRaisesRegex(StudioError, 'escapes'):
                studio.register_history('Symlink', bundle)
            (bundle / 'mesh.bin').unlink()
            (bundle / 'mesh.bin').write_bytes(b'geometry')
            record = studio.register_history('Valid', bundle)
            with self.assertRaises(StudioError):
                studio.inspection_file(record.run_id, '../elsewhere/mesh.bin')
            (bundle / 'mesh.bin').write_bytes(b'changed')
            with self.assertRaisesRegex(StudioError, 'changed'):
                studio.inspection_file(record.run_id, 'mesh.bin')
            self.assertEqual(len(studio.list_runs()), 1)

    def test_invalid_names_and_timing_create_no_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio = Studio(root / 'state', history_roots=(root / 'history',))
            for name in ('', '   ', 'x' * 121, None):
                with self.assertRaises(StudioError):
                    studio.create_draft(name)
            folder = self.bundle(root / 'history' / 'bad')
            data = json.loads((folder / 'bindings.json').read_text())
            data['motion']['frame_ids'] = [0, 2]
            (folder / 'bindings.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(StudioError, 'timelines'):
                studio.register_history('Missing frame', folder)
            self.assertEqual(studio.list_runs(), ())

    @staticmethod
    def bundle(folder):
        folder.mkdir(parents=True)
        (folder / 'mesh.bin').write_bytes(b'geometry')
        (folder / 'bindings.json').write_text(json.dumps({
            'geometry': {'human': {'vertices': 'mesh.bin', 'faces': 'mesh.bin'},
                         'robot': {'vertices': 'mesh.bin', 'faces': 'mesh.bin'}},
            'motion': {'frame_count': 2, 'frame_ids': [0, 1], 'fps': 30,
                       'vertices': 'mesh.bin', 'faces': 'mesh.bin', 'transforms': 'mesh.bin'},
            'human_motion': {'frame_count': 2, 'fps': 30,
                             'chunks': [{'file': 'mesh.bin', 'start': 0, 'count': 2}]}}))
        (folder / 'provenance.json').write_text('{}')
        (folder / 'preservation.json').write_text('{}')
        return folder

    def test_cli_help_and_service_import_need_no_scientific_runtime(self):
        root = Path(__file__).resolve().parents[1]
        imported = subprocess.run([sys.executable, '-B', '-c',
            "import motion_studio.studio, motion_studio.studio.http, sys; "
            "assert not {'numpy', 'torch', 'mujoco', 'smplx'} & set(sys.modules)"],
            cwd=root, capture_output=True, text=True)
        self.assertEqual(imported.returncode, 0, imported.stderr)
        helped = subprocess.run([sys.executable, '-B', str(root / 'scripts/studio.py'), '--help'],
                                cwd=root, capture_output=True, text=True)
        self.assertEqual(helped.returncode, 0, helped.stderr)
        self.assertIn('--history-root', helped.stdout)

    def test_draft_reopens_after_service_recreation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio = Studio(root / 'state', history_roots=(root / 'history',))
            draft = studio.create_draft('Walking study')
            studio.select(draft.run_id)
            reopened = Studio(root / 'state', history_roots=(root / 'history',))
            self.assertEqual(reopened.list_runs(), (draft,))
            self.assertEqual(reopened.get_run(draft.run_id).name, 'Walking study')
            self.assertEqual(reopened.selected_run_id(), draft.run_id)
            self.assertFalse(draft.read_only)
            self.assertEqual(draft.revision_id, 'r0001')
            self.assertTrue(all(stage.status == 'unavailable' for stage in draft.stages))


if __name__ == '__main__':
    unittest.main()
