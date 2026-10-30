"""Public inspection safety checks need no UMR/scientific runtime."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from motion_studio.integrations.umr_inspection import export_g1_bindings


class BindingInspectionTests(unittest.TestCase):
    def test_changed_completed_config_is_rejected_before_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); run=root/'outputs/run'; run.mkdir(parents=True)
            for name in ('config.json','resolved.json','dataset.npz','motion.npz','validation.json',
                         'train/correspondence_slots_final.npz'):
                p=run/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'original')
            (run/'artifacts.json').write_text(json.dumps({'config.json':hashlib.sha256(b'original').hexdigest()}))
            (run/'config.json').write_bytes(b'changed')
            for name in ('outputs/umr-binding-report/documentation/vendor/three.module.js',
                         'outputs/umr-binding-report/documentation/vendor/controls/OrbitControls.js',
                         'docs/site/THIRD_PARTY_NOTICES.md'):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
            def git_result(command, **kwargs):
                return 'd1cdaedaf67a827198da71c5fa831f48b2e51f91' if 'rev-parse' in command else ''
            with patch('subprocess.check_output',side_effect=git_result):
                with self.assertRaisesRegex(ValueError,'Completed run artifact changed: config.json'):
                    export_g1_bindings(run,root/'outputs/viewer',workspace=root)
            self.assertFalse((root/'outputs/viewer').exists())
            self.assertEqual((run/'config.json').read_bytes(),b'changed')

    def test_dangling_destination_alias_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'outputs').mkdir()
            output=root/'outputs/alias'; output.symlink_to(root/'outputs/missing')
            with self.assertRaises(FileExistsError):
                export_g1_bindings(root/'run',output,workspace=root)
            self.assertTrue(output.is_symlink())

    def test_existing_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); output=root/'outputs/inspection'; output.mkdir(parents=True)
            marker=output/'original'; marker.write_text('keep')
            with self.assertRaises(FileExistsError):
                export_g1_bindings(root/'run',output,workspace=root)
            self.assertEqual(marker.read_text(),'keep')

    def test_missing_run_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); output=root/'outputs/inspection'
            with self.assertRaises(FileNotFoundError):
                export_g1_bindings(root/'missing',output,workspace=root)
            self.assertFalse(output.exists())

    def test_export_cannot_modify_its_input_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); run=root/'outputs/run'; run.mkdir(parents=True)
            marker=run/'original';marker.write_text('keep')
            with self.assertRaises(ValueError):
                export_g1_bindings(run,run/'viewer',workspace=root)
            self.assertEqual(list(run.iterdir()),[marker])
