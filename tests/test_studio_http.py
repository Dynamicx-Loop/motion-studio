"""Studio HTTP boundary: real requests against a loopback ephemeral server."""
from contextlib import contextmanager
from pathlib import Path
import http.client
import json
import tempfile
import threading
import unittest

from motion_studio.studio import Studio, StudioError
from motion_studio.studio.http import create_server
import test_studio


@contextmanager
def serving(studio):
    server = create_server(studio, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def request(server, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection(*server.server_address, timeout=5)
    conn.request(method, path, body=body, headers=headers or {})
    response = conn.getresponse()
    data = response.read()
    result = response.status, dict(response.getheaders()), data
    conn.close()
    return result


class StudioHTTPTests(unittest.TestCase):
    def test_historical_viewer_uses_owned_scripts_and_rejects_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = test_studio.StudioTests.bundle(root / 'history' / 'g1')
            (bundle / 'app.js').write_text('UNTRUSTED HISTORICAL SCRIPT')
            studio = Studio(root / 'state', history_roots=(root / 'history',))
            with serving(studio) as server:
                status, _, body = request(server, 'POST', '/api/history',
                    json.dumps({'name': 'G1 reference', 'inspection_path': str(bundle)}),
                    {'Content-Type': 'application/json'})
                self.assertEqual(status, 201)
                record = json.loads(body)
                prefix = '/inspection/' + record['run_id'] + '/'
                status, _, body = request(server, 'GET', prefix + 'app.js')
                self.assertEqual(status, 200)
                self.assertNotIn(b'UNTRUSTED HISTORICAL SCRIPT', body)
                for file in ('index.html', 'human-motion.js', 'vendor/three.module.js',
                             'vendor/OrbitControls.js', 'THIRD_PARTY_NOTICES.md', 'mesh.bin'):
                    self.assertEqual(request(server, 'GET', prefix + file)[0], 200, file)
                status, _, body = request(server, 'POST', '/api/runs/' + record['run_id'] + '/name',
                    '{"name":"Changed"}', {'Content-Type': 'application/json'})
                self.assertEqual(status, 409)
                self.assertEqual(json.loads(body)['error']['code'], 'read_only')
                self.assertEqual((bundle / 'app.js').read_text(), 'UNTRUSTED HISTORICAL SCRIPT')

    def test_storage_failure_returns_actionable_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio = Studio(Path(tmp) / 'state')
            (studio.roots.state / 'studio.sqlite3').write_bytes(b'not a database')
            with serving(studio) as server:
                with self.assertLogs('motion_studio.studio.http', level='ERROR'):
                    status, _, body = request(server, 'GET', '/api/state')
                self.assertEqual(status, 500)
                self.assertEqual(json.loads(body)['error']['code'], 'service_error')

    def test_invalid_requests_are_structured_and_paths_confined(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio = Studio(Path(tmp) / 'state')
            with serving(studio) as server:
                cases = [
                    ('GET', '/%2e%2e/AGENTS.md', None, {}, 404, 'not_found'),
                    ('GET', '/api/runs/../../etc/passwd', None, {}, 400, 'invalid_id'),
                    ('POST', '/api/runs', '{', {'Content-Type': 'application/json'}, 400, 'invalid_json'),
                    ('POST', '/api/runs', '{}', {'Content-Type': 'application/json'}, 400, 'invalid_fields'),
                    ('POST', '/api/runs', 'name=x', {}, 415, 'invalid_json'),
                    ('POST', '/api/runs', '{"name":"x"}', {'Content-Type': 'application/json', 'Origin': 'https://remote.example'}, 403, 'invalid_origin'),
                    ('GET', '/api/state', None, {'Host': 'remote.example'}, 403, 'invalid_host'),
                ]
                for method, path, body, headers, expected, code in cases:
                    with self.subTest(path=path, code=code):
                        status, _, data = request(server, method, path, body, headers)
                        self.assertEqual(status, expected)
                        self.assertEqual(json.loads(data)['error']['code'], code)
                self.assertEqual(studio.list_runs(), ())

    def test_create_select_and_reopen_through_http(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio = Studio(Path(tmp) / 'state')
            with serving(studio) as server:
                status, _, body = request(server, 'POST', '/api/runs', '{"name":"A draft"}',
                                          {'Content-Type': 'application/json'})
                self.assertEqual(status, 201)
                record = json.loads(body)
                status, _, body = request(server, 'POST', '/api/selection',
                                          json.dumps({'run_id': record['run_id']}),
                                          {'Content-Type': 'application/json'})
                self.assertEqual(status, 200)
                status, _, body = request(server, 'GET', '/api/state')
                state = json.loads(body)
                self.assertEqual(state['selected_run_id'], record['run_id'])
                self.assertEqual(state['runs'][0]['name'], 'A draft')
                status, _, body = request(server, 'GET', '/')
                self.assertEqual(status, 200)
                self.assertIn(b'Stage viewport', body)
            with serving(Studio(Path(tmp) / 'state')) as server:
                _, _, body = request(server, 'GET', '/api/state')
                self.assertEqual(json.loads(body)['selected_run_id'], record['run_id'])


if __name__ == '__main__':
    unittest.main()
