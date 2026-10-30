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
                if set(data) not in ({'run_id'}, {'run_id', 'revision_id'}):
                    raise StudioError('invalid_fields', 'Expected run_id and optional revision_id')
                self._json(200, asdict(studio.select(self._id(data['run_id']), data.get('revision_id'))))
            elif path.startswith('/api/runs/') and path.endswith('/name'):
                self._fields(data, {'name'})
                self._json(200, asdict(studio.rename_draft(self._id(path.split('/')[3]), data['name'])))
            elif path.startswith('/api/runs/') and path.endswith(('/plan', '/execute')):
                self._fields(data, {'through', 'settings'})
                operation = studio.plan_execution if path.endswith('/plan') else studio.start_execution
                self._json(200 if path.endswith('/plan') else 202,
                    operation(self._id(path.split('/')[3]), through=data['through'], settings=data['settings']))
            elif path.startswith('/api/runs/') and '/inspections/' in path:
                self._fields(data, {'revision_id'})
                parts = path.split('/')
                if len(parts) != 6:
                    raise StudioError('not_found', 'Inspection operation does not exist', 404)
                self._json(201, studio.build_inspection(self._id(parts[3]), parts[5], revision_id=data['revision_id']))
            elif path.startswith('/api/runs/') and path.endswith('/settings'):
                self._fields(data, {'settings'})
                self._json(200, asdict(studio.save_execution_settings(self._id(path.split('/')[3]), data['settings'])))
            elif path.startswith('/api/jobs/') and path.endswith('/cancel'):
                self._fields(data, set())
                self._json(200, studio.cancel_job(self._id(path.split('/')[3])))
            # ROBOT mutations: compile/preview live outside the service runtime.
            elif path == '/api/robots':
                self._fields(data, {'source_path', 'derive_free_root'})
                if not isinstance(data['source_path'], str):
                    raise StudioError('invalid_robot_path', 'MJCF path must be a string')
                self._json(201, asdict(studio.import_robot(Path(data['source_path']),
                    derive_free_root=data['derive_free_root'])))
            elif path.startswith('/api/robots/') and path.endswith('/preview'):
                self._fields(data, {'qpos'})
                self._json(200, studio.preview_robot(path.split('/')[3], data['qpos']))
            elif path.startswith('/api/runs/') and path.endswith('/robot-pose'):
                self._fields(data, {'asset_id', 'name', 'qpos', 'torso_body'})
                self._json(200, asdict(studio.save_robot_pose(self._id(path.split('/')[3]),
                    data['asset_id'], name=data['name'], qpos=data['qpos'], torso_body=data['torso_body'])))
            # MOTION import and draft selection operations.
            elif path == '/api/motions':
                self._fields(data, {'source_path', 'metadata'})
                if not isinstance(data['source_path'], str):
                    raise StudioError('invalid_path', 'Motion source path must be a string')
                self._json(201, asdict(studio.import_motion(Path(data['source_path']), metadata=data['metadata'])))
            elif path.startswith('/api/runs/') and path.endswith('/motion'):
                self._fields(data, {'asset_id'})
                if not isinstance(data['asset_id'], str):
                    raise StudioError('invalid_id', 'Motion asset ID must be a string')
                self._json(200, asdict(studio.select_motion(self._id(path.split('/')[3]), data['asset_id'])))
            else:
                raise StudioError('not_found', 'Operation does not exist', 404)

        def _get(self, path):
            if path == '/api/state':
                self._json(200, {'runs': [asdict(run) for run in studio.list_runs()],
                                 'selected_run_id': studio.selected_run_id(),
                                 'selected_run': asdict(studio.get_run(studio.selected_run_id(), studio.selected_revision_id())) if studio.selected_run_id() else None,
                                 'revisions': [asdict(r) for r in studio.list_revisions(studio.selected_run_id())] if studio.selected_run_id() else [],
                                 'jobs': list(studio.list_jobs()),
                                 'motions': [asdict(asset) for asset in studio.list_motions()],
                                 'robots': [asdict(asset) for asset in studio.list_robots()],
                                 'history_roots': [str(root) for root in studio.history_roots]})
            # ROBOT reads: managed geometry and immutable named poses only.
            elif path == '/api/robots':
                self._json(200, [asdict(asset) for asset in studio.list_robots()])
            elif path.startswith('/api/robots/'):
                parts = path.split('/')
                asset_id = parts[3]
                if len(parts) == 4:
                    self._json(200, asdict(studio.get_robot(asset_id)))
                elif parts[4:] == ['geometry']:
                    self._file(studio.robot_file(asset_id, 'geometry.json'))
                elif parts[4:] == ['poses']:
                    self._json(200, [asdict(pose) for pose in studio.list_robot_poses(asset_id)])
                else:
                    raise StudioError('not_found', 'Robot resource does not exist', 404)
            elif path in {'/vendor/three.module.js', '/vendor/OrbitControls.js'}:
                self._file(_WEB / 'inspection' / path[1:])
            elif path == '/api/motions':
                self._json(200, [asdict(asset) for asset in studio.list_motions()])
            elif path.startswith('/api/motions/'):
                self._json(200, asdict(studio.get_motion(path.removeprefix('/api/motions/'))))
            elif path.startswith('/api/jobs/'):
                parts = path.split('/')
                job_id = self._id(parts[3])
                if len(parts) == 4:
                    self._json(200, studio.get_job(job_id))
                elif len(parts) == 6 and parts[4] == 'log':
                    self._file(studio.job_file(job_id, parts[5]))
                else:
                    raise StudioError('not_found', 'Job resource does not exist', 404)
            elif path.startswith('/artifacts/'):
                parts = path.split('/', 5)
                if len(parts) != 6:
                    raise StudioError('not_found', 'Stage artifact does not exist', 404)
                self._file(studio.stage_artifact(self._id(parts[2]), parts[3], parts[4], parts[5]))
            elif path.startswith('/api/runs/') and '/revisions/' in path:
                parts = path.split('/')
                if len(parts) not in (6, 7, 9):
                    raise StudioError('not_found', 'Revision resource does not exist', 404)
                record = studio.get_run(self._id(parts[3]), parts[5])
                if len(parts) == 6:
                    self._json(200, asdict(record))
                elif parts[6:] == ['settings']:
                    self._json(200, studio.execution_settings(record.run_id, record.revision_id))
                elif len(parts) == 9 and parts[6] == 'stages' and parts[8] == 'receipt':
                    self._json(200, studio.stage_receipt(record.run_id, record.revision_id, parts[7]))
                else:
                    raise StudioError('not_found', 'Revision resource does not exist', 404)
            elif path.startswith('/api/runs/') and path.endswith('/revisions'):
                self._json(200, [asdict(r) for r in studio.list_revisions(self._id(path.split('/')[3]))])
            elif path.startswith('/api/runs/') and '/stages/' in path and path.endswith('/receipt'):
                parts = path.split('/')
                if len(parts) != 7:
                    raise StudioError('not_found', 'Stage receipt does not exist', 404)
                record = studio.get_run(self._id(parts[3]))
                self._json(200, studio.stage_receipt(record.run_id, record.revision_id, parts[5]))
            elif path.startswith('/api/runs/') and path.endswith('/settings'):
                self._json(200, studio.execution_settings(self._id(path.split('/')[3])))
            elif path.startswith('/api/runs/'):
                self._json(200, asdict(studio.get_run(self._id(path.removeprefix('/api/runs/')))))
            elif path.startswith('/inspection/'):
                parts = path.split('/', 3)
                if len(parts) != 4:
                    raise StudioError('not_found', 'Inspection file does not exist', 404)
                run_id, name = self._id(parts[2]), parts[3]
                if not studio.get_run(run_id).read_only:
                    pieces = name.split('/', 2)
                    if len(pieces) != 3:
                        raise StudioError('not_found', 'Stage inspection file does not exist', 404)
                    self._file(studio.exported_inspection_file(run_id, *pieces))
                    return
                if name in {'index.html', 'app.js', 'human-motion.js', 'vendor/three.module.js',
                            'vendor/OrbitControls.js', 'THIRD_PARTY_NOTICES.md'}:
                    self._file(_WEB / 'inspection' / name)
                else:
                    self._file(studio.inspection_file(run_id, name))
            elif path in {'/', '/app.js', '/motion.js', '/execution.js', '/inspection-ui.js', '/robot.js', '/robot-preview.js', '/style.css', '/THIRD_PARTY_NOTICES.md'}:
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
