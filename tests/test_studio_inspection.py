"""Owned inspection/export seam: immutable sources and explicit stage selection."""
from pathlib import Path
import tempfile
import unittest
from motion_studio.studio import Studio, StudioError


class InspectionTests(unittest.TestCase):
    def test_uncomputed_stage_cannot_create_or_publish_an_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio = Studio(Path(tmp))
            run = studio.create_draft('Empty')
            with self.assertRaises(StudioError) as failure:
                studio.build_inspection(run.run_id, 'binding')
            self.assertEqual(failure.exception.code, 'changed_artifact')
            self.assertEqual(list(studio.roots.exports.iterdir()), [])

class SavedInspectionStreamingTests(unittest.TestCase):
    def test_streaming_is_independent_of_native_receipts_but_checks_every_resource(self):
        import json
        from unittest.mock import patch
        from motion_studio.studio._history import digest
        with tempfile.TemporaryDirectory() as tmp:
            studio = Studio(Path(tmp)); run = studio.create_draft('Saved motion')
            folder = studio.roots.exports/'stream'; folder.mkdir()
            chunk = folder/'human-motion-000.bin'; chunk.write_bytes(b'exact saved frames')
            with studio._connection() as db:
                db.execute('INSERT INTO inspections VALUES (?, ?, ?, ?, ?)',
                    (run.run_id, run.revision_id, 'retargeting', str(folder),
                     json.dumps({chunk.name:digest(chunk)})))
            # A closed exported viewer must not inspect its original compute
            # receipts on every streamed chunk, even if originals disappear.
            with patch.object(studio, '_receipt', side_effect=AssertionError('Native pipeline revalidated during streaming')):
                self.assertEqual(studio.exported_inspection_file(run.run_id, run.revision_id, 'retargeting', chunk.name), chunk)
                # Exercise the transport too: its historical/native routing must
                # not hydrate the run before handing off the chunk request.
                import threading, urllib.request
                from motion_studio.studio.http import create_server
                server = create_server(studio, port=0)
                thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
                try:
                    url = f'http://127.0.0.1:{server.server_port}/inspection/{run.run_id}/{run.revision_id}/retargeting/{chunk.name}'
                    with urllib.request.urlopen(url) as response:
                        self.assertEqual(response.read(), b'exact saved frames')
                finally:
                    server.shutdown(); server.server_close()
                chunk.write_bytes(b'corrupted chunk')
                with self.assertRaises(StudioError) as failure:
                    studio.exported_inspection_file(run.run_id, run.revision_id, 'retargeting', chunk.name)
                self.assertEqual(failure.exception.code, 'changed_artifact')
                with self.assertRaises(StudioError) as missing:
                    studio.exported_inspection_file('missing', run.revision_id, 'retargeting', chunk.name)
                self.assertEqual(missing.exception.status, 404)

class StandaloneBindingTests(unittest.TestCase):
    def test_binding_bundle_is_closed_and_does_not_need_models_or_motion(self):
        import hashlib
        import json
        from motion_studio.integrations.umr_studio_inspection import InspectionInputs, export_inspection
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'saved'; source.mkdir()
            payload = {'run':'fixture', 'schema':'native19', 'geometry':{},
                       'source':[[0,0,0]], 'target':[[1,0,0]], 'labels':['torso'],
                       'bodies':['body'], 'meshes':[None], 'geom_ids':[0],
                       'projection_m':[0], 'counts':{'torso':1}}
            for model in ('human', 'robot'):
                payload['geometry'][model] = {'vertices':model+'-vertices.bin', 'faces':model+'-faces.bin',
                                             'vertex_count':3,'face_count':1}
                (source/(model+'-vertices.bin')).write_bytes(bytes(36))
                (source/(model+'-faces.bin')).write_bytes(bytes(12))
            (source/'bindings.json').write_text(json.dumps(payload))
            (source/'binding.npz').write_bytes(b'opaque native binding retained')
            paths = {p.name:p for p in source.iterdir()}
            receipt = {'run_id':'fixture','revision_id':'r0001','stage':'binding', 'dependencies':{},
                       'artifacts':{name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in paths.items()}}
            inputs = InspectionInputs('fixture', 'r0001', 'binding', {'binding':receipt}, {'binding':paths})
            before = {p:p.read_bytes() for p in paths.values()}
            result = export_inspection(inputs, root/'fresh')
            self.assertEqual(json.loads((result/'bindings.json').read_text()), payload)
            self.assertTrue((result/'vendor/three.module.js').is_file())
            self.assertTrue((result/'native/binding/binding.npz').is_file())
            self.assertTrue((result/'files.json').is_file())
            self.assertTrue((result/'bridge.js').is_file())
            self.assertEqual((result/'bridge.js').read_bytes(),
                (Path(__file__).parents[1]/'motion_studio/studio/web/stage-inspection/bridge.js').read_bytes())
            # The exported app's relative imports resolve inside its own folder.
            import re
            for name in re.findall(r"from ['\"]\./([^'\"]+)['\"]", (result/'app.js').read_text()):
                self.assertIn(name, json.loads((result/'files.json').read_text()))
                self.assertTrue((result/name).is_file(), name)
            self.assertEqual((result/'human-motion.js').read_bytes(),
                (Path(__file__).parents[1]/'motion_studio/studio/web/human-motion.js').read_bytes())
            self.assertEqual({p:p.read_bytes() for p in paths.values()}, before)
            with self.assertRaises(FileExistsError):
                export_inspection(inputs, result)

    def test_changed_native_bytes_fail_before_creating_a_destination(self):
        import hashlib
        from motion_studio.integrations.umr_studio_inspection import InspectionInputs, export_inspection
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'saved').mkdir(); native=root/'saved/binding.npz'; native.write_bytes(b'changed')
            receipt={'artifacts':{'binding.npz':hashlib.sha256(b'original').hexdigest()}}
            inputs=InspectionInputs('fixture','r0001','binding',{'binding':receipt},{'binding':{'binding.npz':native}})
            with self.assertRaisesRegex(ValueError,'Changed stage artifact'):
                export_inspection(inputs,root/'fresh')
            self.assertFalse((root/'fresh').exists())

class InspectionHTTPTests(unittest.TestCase):
    def test_explicit_build_reports_missing_receipt_and_does_not_start_a_job(self):
        import json
        import threading
        import urllib.request
        import urllib.error
        from motion_studio.studio.http import create_server
        with tempfile.TemporaryDirectory() as tmp:
            studio=Studio(Path(tmp));run=studio.create_draft('No compute')
            server=create_server(studio,port=0)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                request=urllib.request.Request(f'http://127.0.0.1:{server.server_port}/api/runs/{run.run_id}/inspections/binding',
                    json.dumps({'revision_id':run.revision_id}).encode(),{'Content-Type':'application/json'})
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(request)
                self.assertEqual(error.exception.code,409)
                self.assertEqual(json.load(error.exception)['error']['code'],'changed_artifact')
                self.assertEqual(studio.list_jobs(),())
                self.assertEqual(list(studio.roots.exports.iterdir()),[])
            finally:
                server.shutdown();server.server_close()
