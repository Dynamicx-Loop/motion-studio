"""Versioned source surfaces, exact binary frames and registered read-only HTTP."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

CHECK_MODULES = ('numpy',)
try:
    import numpy as np
except ImportError:
    np = None

from motion_studio.integrations._umr_source_mesh_worker import export_mesh
from motion_studio.integrations.umr_stages import PIN
from motion_studio.studio import Studio, StudioError
from motion_studio.studio._history import digest
from motion_studio.studio._source_mesh_preview import inspect_mesh_preview, SCHEMA
from test_studio_http import serving, request


@unittest.skipIf(np is None, 'NumPy unavailable')
class SourceMeshPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        model = self.root / 'models'
        model.mkdir()
        (model / 'SMPLX_NEUTRAL.pkl').write_bytes(b'fixture')
        self.studio = Studio(self.root / 'state', smplx_model_dir=model)
        source = self.root / 'clip.npz'
        np.savez(source, poses=np.zeros((66,66)), trans=np.zeros((66,3)), betas=np.zeros(10),
                 gender='neutral', fps=48., samp_output_up='z')
        self.asset = self.studio.import_motion(source)

    def fixture(self, motion, asset, destination, **options):
        destination.mkdir(parents=True)
        roots = np.column_stack((np.arange(asset.frame_count) * .15, np.zeros((asset.frame_count,2))))
        local = np.array([[-.40003, .20002, -.70001], [.2,.3,.4], [.3,.5,.1]])
        def reconstruct(sequence, ids, model, **kwargs):
            vertices = roots[ids, None] + local
            joints = np.repeat(roots[ids,None], 22, axis=1)
            faces = np.array([[0,1,2]], dtype=np.int32)
            if hasattr(self, 'mutate_native'):
                self.mutate_native(vertices,joints,faces,ids)
            return vertices, joints, faces
        common = SimpleNamespace(load_motion_collection=lambda _: ({}, None),
            select_sequence=lambda *args: ('clip', {'fps':asset.fps, 'output_up':asset.up_axis}),
            sequence_frame_count=lambda _: asset.frame_count, source_motion_vertices_joints=reconstruct,
            source_points_to_retarget_frame=lambda values, *args: values)
        export_mesh({'motion':str(motion), 'model':asset.model_path, 'fps':asset.fps,
            'frame_count':asset.frame_count, 'source_revision':PIN,
            'inputs_sha256':{str(motion):digest(motion), asset.model_path:asset.model_sha256}},
            destination, common, np)
        return destination / 'manifest.json'

    def build(self):
        with patch('motion_studio.integrations.umr_source_preview.build_source_mesh_preview', self.fixture):
            return self.studio.build_source_mesh_preview(self.asset.asset_id)

    def test_mesh_chunks_preserve_exact_boundary_frames_and_translation(self):
        self.build()
        manifest = self.studio.source_mesh_preview_file(self.asset.asset_id)
        data = json.loads(manifest.read_text())
        self.assertEqual([(c['start'],c['count']) for c in data['chunks']], [(0,64),(64,2)])
        self.assertEqual((data['frame_count'],data['fps'],data['schema']), (66,48.,SCHEMA))
        for frame in (0,63,64,65):
            chunk = data['chunks'][frame // 64]
            encoded = np.fromfile(self.studio.source_mesh_preview_file(self.asset.asset_id,chunk['file']), '<i2').reshape(chunk['count'],3,3)
            decoded = encoded[frame-chunk['start']] * data['quantization_m'] + data['root_positions'][frame]
            expected = np.array([[-.40003,.20002,-.70001], [.2,.3,.4], [.3,.5,.1]]) + [frame*.15,0,0]
            np.testing.assert_allclose(decoded, expected, atol=5.1e-5, rtol=0)
        np.testing.assert_array_equal(np.fromfile(manifest.parent/'faces.bin','<u4'), [0,1,2])
        self.assertEqual(self.studio.list_runs(), ())

    def test_legacy_skeleton_is_preserved_and_never_reused_as_surface(self):
        self.studio._source_preview_table()
        old = self.studio.roots.exports/'source-preview'/'old.json'
        old.parent.mkdir()
        old.write_text('{"frames":[]}')
        with self.studio._connection() as db:
            db.execute('INSERT INTO source_previews VALUES (?, ?, ?)', (self.asset.asset_id,str(old),digest(old)))
        with self.assertRaises(StudioError) as error:
            self.studio.source_mesh_preview_file(self.asset.asset_id)
        self.assertEqual(error.exception.code,'not_found')
        self.build()
        self.assertEqual(old.read_text(),'{"frames":[]}')

    def test_registered_files_reopen_without_source_weights_or_builder_and_detect_tampering(self):
        result = self.build()
        folder = self.studio.source_mesh_preview_file(self.asset.asset_id).parent
        Path(self.asset.model_path).unlink()
        self.studio.motion_source(self.asset.asset_id).unlink()
        recreated = Studio(self.studio.roots.state)
        self.assertEqual(recreated.build_source_mesh_preview(self.asset.asset_id), result)
        self.assertTrue(recreated.source_mesh_preview_file(self.asset.asset_id,'faces.bin').is_file())
        for name in ('faces.bin','vertices-001.bin','manifest.json'):
            path = folder/name
            original = path.read_bytes()
            path.write_bytes(original+b'changed')
            with self.assertRaises(StudioError) as error:
                recreated.source_mesh_preview_file(self.asset.asset_id,name)
            self.assertEqual(error.exception.code,'changed_artifact')
            path.write_bytes(original)
        with self.assertRaises(StudioError):
            recreated.source_mesh_preview_file(self.asset.asset_id,'../request.json')

    def test_registration_rejects_bad_sizes_timeline_topology_and_manifest(self):
        source = self.studio.motion_file(self.asset.asset_id)
        folder = self.root/'fixture'
        self.fixture(source,self.asset,folder)
        manifest = folder/'manifest.json'
        baseline = json.loads(manifest.read_text())
        variants = []
        for field, value in [('schema','old'), ('root_positions',[[0,0,float('nan')]]*66),
                             ('fps',24), ('vertex_count',4), ('input_up_axis','y')]:
            data = copy.deepcopy(baseline)
            data[field] = value
            variants.append(data)
        data = copy.deepcopy(baseline)
        data['chunks'][1]['start'] = 63
        variants.append(data)
        for data in variants:
            manifest.write_text(json.dumps(data))
            with self.assertRaises(StudioError):
                inspect_mesh_preview(folder,self.asset)
        manifest.write_text(json.dumps(baseline))
        np.array([0,1,4],dtype='<u4').tofile(folder/'faces.bin')
        with self.assertRaisesRegex(StudioError,'missing vertices'):
            inspect_mesh_preview(folder,self.asset)

    def test_cache_folder_and_resource_symlinks_are_refused(self):
        self.build()
        path = self.studio.source_mesh_preview_file(self.asset.asset_id,'faces.bin')
        outside = self.root/'outside.bin'
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaises(StudioError) as error:
            self.studio.source_mesh_preview_file(self.asset.asset_id,'faces.bin')
        self.assertEqual(error.exception.code,'changed_artifact')
        with self.studio._connection() as db:
            db.execute('UPDATE source_mesh_previews SET path=?',(str(self.root),))
        with self.assertRaises(StudioError):
            self.studio.source_mesh_preview_file(self.asset.asset_id)

    def test_concurrent_reconstruction_is_coalesced(self):
        calls, barrier = [], threading.Barrier(6)
        def builder(*args,**options):
            calls.append(1)
            return self.fixture(*args,**options)
        def build(index):
            studio = Studio(self.studio.roots.state)
            barrier.wait(5)
            return studio.build_source_mesh_preview(self.asset.asset_id)
        with patch('motion_studio.integrations.umr_source_preview.build_source_mesh_preview',builder):
            with ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(build,range(6)))
        self.assertEqual(len(calls),1)
        self.assertTrue(all(result==results[0] for result in results))

    def test_invalid_native_geometry_cannot_publish_a_derivative(self):
        def nonfinite(vertices,joints,faces,ids):
            vertices[0,0,0] = np.nan
        def overflow(vertices,joints,faces,ids):
            vertices[0,0,0] += 4
        def invalid_topology(vertices,joints,faces,ids):
            faces[0,0] = 4
        def changing_topology(vertices,joints,faces,ids):
            if ids[0] > 0:
                faces[0] = [2,1,0]
        for mutation in (nonfinite,overflow,invalid_topology,changing_topology):
            self.mutate_native = mutation
            with self.subTest(mutation=mutation.__name__):
                with self.assertRaises(StudioError) as error:
                    self.build()
                self.assertEqual(error.exception.code,'preview_failed')
                with self.assertRaises(StudioError) as missing:
                    self.studio.source_mesh_preview_file(self.asset.asset_id)
                self.assertEqual(missing.exception.code,'not_found')

    def test_http_serves_only_registered_manifest_topology_chunks(self):
        before = digest(self.studio.motion_source(self.asset.asset_id))
        with patch('motion_studio.integrations.umr_source_preview.build_source_mesh_preview',self.fixture):
            with serving(self.studio) as server:
                prefix = f'/api/motions/{self.asset.asset_id}'
                status,_,body = request(server,'POST',prefix+'/mesh-preview','{}',{'Content-Type':'application/json'})
                self.assertEqual(status,201)
                url = json.loads(body)['url']
                self.assertEqual(request(server,'GET',url)[0],200)
                for name in ('faces.bin','vertices-000.bin','vertices-001.bin'):
                    self.assertEqual(request(server,'GET',prefix+'/mesh-preview-data/'+name)[0],200)
                self.assertEqual(request(server,'GET',prefix+'/mesh-preview-data/request.json')[0],404)
        self.assertEqual(self.studio.list_runs(),())
        self.assertEqual(digest(self.studio.motion_source(self.asset.asset_id)),before)
