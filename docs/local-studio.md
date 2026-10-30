# Local Studio

The persistent local application currently provides saved drafts and read-only
historical G1 playback. It uses Python's standard library and independently
vendored browser dependencies. Viewing needs neither CUDA nor UMR imports.
Launch from the Motion Studio root:

```sh
python3 -B scripts/studio.py --state outputs/studio-state \
  --history-root /data/workspace/motion_studio/outputs/umr-g1-inspection \
  --history /data/workspace/motion_studio/outputs/umr-g1-inspection/manual-01-synchronized
```

Open the printed loopback URL (default `http://127.0.0.1:8773/`). `--history-root`
is repeatable and explicitly grants read-only registration beneath each directory.
`--history` registers an inspection at startup; the UI can register others inside
those roots. Re-registering a directory returns the same run identity. State and
historical roots must be separate. Do not point state at an existing research run.
No asset download, accounts, external requests or scientific runtime is needed.

The sidebar creates and reopens named drafts and historical registrations. The
center contains stage availability and the inspection viewport; details and status/
log links remain accessible. Selecting a tab never starts work. Refresh restores
the selected persisted run/revision. Playback position and transient camera/filter
controls start fresh when the inspection reloads. Current historical results expose
motion inspection, including static reference pose and synchronized human/robot
bindings. Input preparation and execution arrive in subsequent slices; unavailable
stages are disabled and drafts launch nothing.

The service binds only `127.0.0.1`, checks Host, refuses cross-origin changes and
accepts only bounded JSON object mutations. This is a single-user local service,
not an authenticated remote deployment. Stop it with Ctrl-C. SQLite transactions
persist registrations, draft names and selected identity across process restarts.

## Owned operations and storage

Import `Studio`, `RunRecord`, `Stage`, `StageState`, `StageArtifact`, `StageResult`,
`StorageRoots` and `StudioError` from `motion_studio.studio`. No upstream objects,
NumPy arrays, simulator models or GPU imports cross this service boundary.

- `Studio(state_root: Path, history_roots: tuple[Path, ...] = ())` creates managed
  state directories and opens short independent transactions per operation.
- `create_draft(name) -> RunRecord`, `list_runs() -> tuple[RunRecord, ...]`,
  `get_run(run_id) -> RunRecord`, `rename_draft(run_id, name) -> RunRecord` own
  persistent draft metadata. Names contain 1–120 characters; creating a draft
  makes no scientific inputs and starts no work.
- `select(run_id) -> RunRecord` and `selected_run_id() -> str | None` persist the
  current identity independently of browser storage.
- `register_history(name, inspection: Path) -> RunRecord` reads a complete existing
  synchronized inspection under a configured root. `inspection_file(run_id, name)
  -> Path` checks registered membership, confinement and the recorded SHA-256.
  It returns only data/log/provenance artifacts; historical HTML/scripts are never
  executed. The HTTP transport serves owned viewer code and vendor files instead.

`RunRecord` is immutable: `run_id` is a UUID hex string, `revision_id` currently
`r0001`, `kind` is `draft` or `historical`, `read_only` explicitly identifies
historical registrations, and `created_at` is an ISO UTC timestamp. `stages`
contains `StageState(stage, status, inspection_url)` for preparation, sampling,
training, binding, retargeting and motion. This slice uses `unavailable` and
`available`; execution will add lifecycle states. Historical availability describes
saved inspection access, not a newly executed native stage or verified new solve.

`studio.roots` exposes `StorageRoots(state, assets, runs, exports)`. State holds
`studio.sqlite3`; imported immutable asset versions belong under `assets`, new
run revisions under `runs/<run_id>/<revision_id>/`, stage artifacts under
`runs/<run_id>/<revision_id>/<stage>/`, and fresh inspection exports under
`exports`. These roots are owned by the application. Historical paths are external,
read-only references and cannot receive derivatives. Subsequent execution must
allocate fresh destinations; do not repurpose historical output paths.

For concrete adapters, `StageResult(run_id, revision_id, stage, artifacts)` is the
small result envelope. Each `StageArtifact(relative_path, sha256, media_type)`
references bytes relative to its managed stage directory. Construction alone is
not a completion receipt: the receiving execution operation must validate exact
identity, path confinement, hashes and stage-specific output requirements before
publishing completion. Scientific configuration translation and runtime invocation
stay in the concrete adapter. This initial slice does not invoke adapters or claim
cache reuse, cancellation or stage execution.

Expected failures use `StudioError(code, message, status)`. HTTP represents these as
`{"error":{"code":"…","message":"…"}}`; missing objects are 404, historical
mutations and changed artifacts are 409, invalid inputs/paths are 400. Unexpected
local service failures are 500 with details in service stderr. Callers can act on
`code` without parsing messages. Registered inspection validation covers its saved
frame timeline, closed referenced-file set and hashes; it does not repeat native
numerical validation or certify motion quality.

## HTTP contract

- `GET /api/state`: runs, selected_run_id, configured history_roots.
- `GET /api/runs/<run_id>`: one serialized `RunRecord`.
- `POST /api/runs` with `{name}`: create draft, 201.
- `POST /api/history` with `{name, inspection_path}`: register historical result, 201.
- `POST /api/selection` with `{run_id}`: persist selection, 200.
- `POST /api/runs/<run_id>/name` with `{name}`: rename draft, 200; historical 409.
- `GET /inspection/<run_id>/<file>`: independently owned frontend or hash-checked
  registered historical artifact. No directory browsing or arbitrary file access.

All POST requests need `Content-Type: application/json` and exact named fields.
The HTTP server returned by `motion_studio.studio.http.create_server(studio, port=…)`
binds loopback; the caller owns `serve_forever`, `shutdown` and `server_close`.

## Dependency provenance and checks

`motion_studio/studio/web/inspection/vendor/` independently preserves Three.js
r165 and OrbitControls with MIT notices. `web/vendor-manifest.json` records hashes
and the initial already-local extraction provenance. Serving the app never reads
old generated vendor directories. The original viewer sources and generated
inspection remain unchanged. Research asset terms remain separate.

```sh
python3 -B -m unittest discover -s tests -p 'test_studio*.py' -v
python3 -B scripts/check.py --tier pure
node --check motion_studio/studio/web/app.js
```

The pure suites exercise process recreation, selection, historical read-only
behavior and changed/escaping data through owned operations and real loopback
requests. Browser validation for this slice opened the preserved full G1 inspection,
stepped exact source frames, created a draft, restored each selected run on refresh,
and checked that all page/iframe resource URLs use the local origin. Fresh native
execution and the broader lifecycle acceptance belong to later tickets.
