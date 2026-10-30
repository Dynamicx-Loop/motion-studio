"""Loopback HTTP transport for owned Studio operations; no job lifetime in the UI."""
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import mimetypes
from pathlib import Path
import shutil
import sqlite3
from urllib.parse import unquote, urlsplit

from . import Studio, StudioError

_WEB = Path(__file__).with_name('web')
_LOG = logging.getLogger(__name__)


def create_server(studio: Studio, *, port: int = 8773) -> ThreadingHTTPServer:
    """Bind IPv4 loopback only. Caller owns serve_forever/shutdown/server_close."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            _LOG.info(format, *args)

        def do_GET(self):
            self._dispatch(False)

        def do_POST(self):
            self._dispatch(True)

        def _dispatch(self, mutate):
            try:
                host = self.headers.get('Host', '')
                allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
                if host not in allowed:
                    raise StudioError('invalid_host', 'Use this application through its loopback URL', 403)
                origin = self.headers.get('Origin')
                if mutate and origin and origin != f'http://{host}':
                    raise StudioError('invalid_origin', 'Cross-origin changes are refused', 403)
                path = unquote(urlsplit(self.path).path)
                if mutate:
                    self._post(path, self._body())
                else:
                    self._get(path)
            except StudioError as error:
                self._json(error.status, {'error': {'code': error.code, 'message': str(error)}})
            except (OSError, ValueError, TypeError, sqlite3.Error):
                _LOG.exception('Studio request failed')
                self._json(500, {'error': {'code': 'service_error', 'message': 'Local service failed; inspect service logs'}})

        def _body(self):
            if self.headers.get_content_type() != 'application/json':
                raise StudioError('invalid_json', 'Expected application/json', 415)
            try:
                length = int(self.headers.get('Content-Length', '-1'))
                if not 0 <= length <= 65536:
                    raise ValueError()
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError()
                return data
            except (ValueError, UnicodeError) as error:
                raise StudioError('invalid_json', 'Expected a JSON object up to 64 KiB') from error

        def _post(self, path, data):
            if path == '/api/runs':
                self._fields(data, {'name'})
                self._json(201, asdict(studio.create_draft(data['name'])))
            elif path == '/api/history':
                self._fields(data, {'name', 'inspection_path'})
                if not isinstance(data['inspection_path'], str):
                    raise StudioError('invalid_path', 'Inspection path must be a string')
                self._json(201, asdict(studio.register_history(data['name'], Path(data['inspection_path']))))
            elif path == '/api/selection':
                self._fields(data, {'run_id'})
                self._json(200, asdict(studio.select(self._id(data['run_id']))))
            elif path.startswith('/api/runs/') and path.endswith('/name'):
                self._fields(data, {'name'})
                self._json(200, asdict(studio.rename_draft(self._id(path.split('/')[3]), data['name'])))
            else:
                raise StudioError('not_found', 'Operation does not exist', 404)

        def _get(self, path):
            if path == '/api/state':
                self._json(200, {'runs': [asdict(run) for run in studio.list_runs()],
                                 'selected_run_id': studio.selected_run_id(),
                                 'history_roots': [str(root) for root in studio.history_roots]})
            elif path.startswith('/api/runs/'):
                self._json(200, asdict(studio.get_run(self._id(path.removeprefix('/api/runs/')))))
            elif path.startswith('/inspection/'):
                parts = path.split('/', 3)
                if len(parts) != 4:
                    raise StudioError('not_found', 'Inspection file does not exist', 404)
                run_id, name = self._id(parts[2]), parts[3]
                if not studio.get_run(run_id).read_only:
                    raise StudioError('not_found', 'Run has no historical inspection', 404)
                if name in {'index.html', 'app.js', 'human-motion.js', 'vendor/three.module.js',
                            'vendor/OrbitControls.js', 'THIRD_PARTY_NOTICES.md'}:
                    self._file(_WEB / 'inspection' / name)
                else:
                    self._file(studio.inspection_file(run_id, name))
            elif path in {'/', '/app.js', '/style.css', '/THIRD_PARTY_NOTICES.md'}:
                file = 'index.html' if path == '/' else path[1:]
                self._file(_WEB / file)
            else:
                raise StudioError('not_found', 'Resource does not exist', 404)

        @staticmethod
        def _fields(data, required):
            if set(data) != required:
                raise StudioError('invalid_fields', 'Expected fields: ' + ', '.join(sorted(required)))

        @staticmethod
        def _id(value):
            if not isinstance(value, str) or len(value) != 32 or any(c not in '0123456789abcdef' for c in value):
                raise StudioError('invalid_id', 'Run ID must be 32 lowercase hexadecimal characters')
            return value

        def _headers(self, status, content_type, length):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(length))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'")
            self.end_headers()

        def _json(self, status, data):
            body = json.dumps(data, allow_nan=False).encode()
            self._headers(status, 'application/json; charset=utf-8', len(body))
            self.wfile.write(body)

        def _file(self, path):
            try:
                stream = path.open('rb')
            except FileNotFoundError as error:
                raise StudioError('not_found', 'Resource file is missing', 404) from error
            with stream:
                content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
                self._headers(200, content_type, path.stat().st_size)
                shutil.copyfileobj(stream, self.wfile)

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)
