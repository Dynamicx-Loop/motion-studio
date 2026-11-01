"""Observable source replay contracts, independent of native retarget jobs."""
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
import threading
from unittest.mock import patch

CHECK_MODULES = ('numpy',)

from motion_studio.studio import Studio, StudioError
from motion_studio.studio._source_preview import _SourcePreviewOperations
from motion_studio.studio._history import digest

try:
    import numpy as np
except ImportError:
    np = None


PreviewStudio = Studio if hasattr(Studio, 'build_source_preview') else type(
    'PreviewStudio', (_SourcePreviewOperations, Studio), {})


@unittest.skipIf(np is None, 'NumPy unavailable')
class SourcePreviewContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        models = self.root / 'models'
        models.mkdir()
        (models / 'SMPLX_NEUTRAL.pkl').write_bytes(b'fixture')
        self.studio = PreviewStudio(self.root / 'state', smplx_model_dir=models)
        path = self.root / 'motion.npz'
        np.savez(path, poses=np.zeros((2, 66)), trans=np.zeros((2,3)), betas=np.zeros(10),
                 gender='neutral', fps=30., samp_output_up='z')
        self.asset = self.studio.import_motion(path)

    def publish_fixture(self, path=None):
        self.studio._source_preview_table()
        path = path or self.studio.roots.exports / 'source-preview' / 'fixture.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"frames":[]}')
        with self.studio._connection() as db:
            db.execute('INSERT INTO source_previews VALUES (?, ?, ?)',
                       (self.asset.asset_id, str(path), digest(path)))
        return path

    def test_missing_preview_is_explicit(self):
        with self.assertRaises(StudioError) as failure:
            self.studio.source_preview_file(self.asset.asset_id)
        self.assertEqual(failure.exception.code, 'not_found')

    def test_registered_cache_returns_without_run_changes_and_detects_tampering(self):
        path = self.publish_fixture()
        result = self.studio.build_source_preview(self.asset.asset_id)
        self.assertEqual(result['frame_count'], 2)
        self.assertEqual(self.studio.list_runs(), ())
        recreated = PreviewStudio(self.studio.roots.state)
        self.assertEqual(recreated.source_preview_file(self.asset.asset_id), path)
        path.write_text('{}')
        with self.assertRaises(StudioError) as failure:
            recreated.source_preview_file(self.asset.asset_id)
        self.assertEqual(failure.exception.code, 'changed_artifact')

    def test_cache_cannot_escape_export_root(self):
        self.publish_fixture(self.root / 'outside.json')
        with self.assertRaises(StudioError) as failure:
            self.studio.source_preview_file(self.asset.asset_id)
        self.assertEqual(failure.exception.code, 'changed_artifact')

    def test_changed_model_blocks_reconstruction(self):
        Path(self.asset.model_path).write_bytes(b'changed')
        with self.assertRaises(StudioError) as failure:
            self.studio.build_source_preview(self.asset.asset_id)
        self.assertEqual(failure.exception.code, 'changed_model')

    def test_saved_derivative_remains_viewable_without_model(self):
        path = self.publish_fixture()
        Path(self.asset.model_path).unlink()
        self.assertEqual(self.studio.build_source_preview(self.asset.asset_id)['frame_count'], 2)
        self.assertEqual(self.studio.source_preview_file(self.asset.asset_id), path)


    def test_simultaneous_requests_share_one_cpu_derivative(self):
        start = threading.Barrier(8)
        entered = threading.Event()
        release = threading.Event()
        calls = []

        def reconstruct(source, asset, destination, **options):
            calls.append(destination)
            entered.set()
            self.assertTrue(release.wait(5))
            destination.mkdir(parents=True)
            output = destination / 'preview.json'
            output.write_text('{"frames":[]}')
            return output

        def request_preview(index):
            # Include independent Studio instances to cover shared state access.
            studio = self.studio if index % 2 else PreviewStudio(self.studio.roots.state)
            start.wait(timeout=5)
            return studio.build_source_preview(self.asset.asset_id)

        with patch('motion_studio.integrations.umr_source_preview.build_source_preview', reconstruct):
            with ThreadPoolExecutor(max_workers=8) as pool:
                requests = [pool.submit(request_preview, index) for index in range(8)]
                self.assertTrue(entered.wait(5))
                release.set()
                results = [request.result(timeout=10) for request in requests]
        self.assertEqual(len(calls), 1)
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(self.studio.list_runs(), ())
        self.assertTrue(self.studio.source_preview_file(self.asset.asset_id).is_file())
