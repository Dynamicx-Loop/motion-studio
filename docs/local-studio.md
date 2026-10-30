# Local Studio

The persistent local application provides saved drafts, managed robot/pose and
SMPL-X motion preparation, and read-only historical G1 playback. Startup uses
Python's standard library and independently vendored browser dependencies. Viewing needs neither CUDA nor UMR imports.
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
bindings. Native execution arrives in subsequent slices; unavailable stages are disabled
and input preparation launches no compute job.

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

`RunRecord` is immutable: `run_id` is a UUID hex string, `revision_id` starts at
`r0001` and advances on saved input changes, `kind` is `draft` or `historical`, `read_only` explicitly identifies
historical registrations, and `created_at` is an ISO UTC timestamp. `stages`
contains `StageState(stage, status, inspection_url)` for preparation, sampling,
training, binding, retargeting and motion. Preparation becomes available after a robot pose is saved. The service uses
`unavailable` and `available`; execution will add lifecycle states. Historical availability describes
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
stay in the concrete adapter. This preparation slice does not invoke native stage adapters or claim
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

## Robot import and named poses

Import an absolute local MJCF filename in **Managed assets**, then select that
robot in a draft. `Studio(..., robot_python=Path(...))` or CLI `--robot-python`
selects the independent pinned MuJoCo interpreter; the default in this workspace
is `/data/workspace/motion_studio/externals/UMR/.venv/bin/python`. Viewing existing
historical bundles still needs no scientific runtime. Compilation and pose preview
run in that interpreter without importing MuJoCo into the service process.

The source file's parent is the closure boundary. Includes use MuJoCo's main-file
relative path rule, including nested includes. Compiler mesh/texture directories,
meshes, height fields and texture faces are checked and copied before compilation.
Absolute/parent/escaping dependencies, XML entities, missing files and include cycles
fail explicitly. Material references and defaults are checked by the compiler.
One named-body articulated robot, one floating root at qpos index zero and named,
finite-limit hinges are accepted. Slides, balls, ambiguous roots, multi-robot scenes
and plugin/attached/flexible models are rejected. All body names must be unique for
torso selection. This structural subset does not certify humanoid morphology or
dynamic feasibility. The compiled reference pose must satisfy its hinge limits.

Allow fixed-to-floating derivation explicitly in the import form. Only the managed
expanded XML receives the free joint. A massless root receives recorded synthetic
inertia (0.001 kg, diagonal 1e-6 kg m²); fixed-root keyframes are rejected because
their qpos layout needs conversion. Original XML and local dependencies keep their
bytes, including notices among referenced assets; no source is edited. Imported
versions are SHA-256 identified under `assets/robots/<asset_id>/`; `asset.json`
records the copied-file hashes, compiled runtime, limits and derivations. Keep any
additional source license/notice obligations with the robot source; compilation
does not grant redistribution rights.

The mesh preview uses compiled local mesh vertices and exact `mj_forward` geometry
transforms, in metres/Z-up; primitives are triangulated for display. Preview colors
use compiled RGBA; texture rendering is not reproduced. Search joints, edit numeric
radians or sliders, and edit root XYZ metres/quaternion wxyz. Nonfinite values,
wrong nq, non-unit root quaternion and limit violations fail without saving; the
quaternion normalization button is explicit. Reset restores compiled `qpos0`.
Select a torso/centering body, name the pose and save. Loading/resetting changes the
unsaved preview; saving commits an immutable named pose and a fresh run revision.
Reopening restores the saved selection. Old poses and run revisions remain intact.

Public operations return frozen `RobotAsset`, `RobotJoint` and `RobotPose` records:

- `import_robot(source_path, derive_free_root=False)`, `list_robots()`,
  `get_robot(asset_id)` and `robot_file(asset_id, registered_name)` own imported
  versions and hash-check artifact reads. Execution should consume
  `robot_file(asset_id, 'source/__studio_model.xml')` with native root derivation
  disabled, never the original source filename.
- `preview_robot(asset_id, qpos=None)` returns compiled geometry transforms only;
  the registered `geometry.json` holds immutable display geometry.
- `save_robot_pose(run_id, asset_id, name=…, qpos=…, torso_body=…)` returns a new
  `RunRecord` with `robot_asset_id` and `robot_pose_id`. Identical selection is a
  no-op. All other saved changes increment the current revision transactionally.
  `get_robot_pose(asset_id, pose_id)` and `list_robot_poses(asset_id)` retrieve named
  snapshots with full root/hinge qpos order and explicit units. Selection history
  remains valid across other input revisions; writes to historical runs fail.

HTTP adds `POST /api/robots` with `{source_path, derive_free_root}`, `GET /api/robots`
and `GET /api/robots/<asset_id>`; `GET …/geometry`, `GET …/poses`;
`POST …/preview` with `{qpos}`; and `POST /api/runs/<run_id>/robot-pose` with
`{asset_id, name, qpos, torso_body}`. `/api/state` includes `robots`. Expected errors
retain the existing structured HTTP contract. New selection revisions invalidate
uncomputed downstream stages; execution/cache lifecycle handling is a later slice.
## SMPL-X motion preparation

The managed-assets panel imports a local `.npz`, inspects its metadata and selects
it for the current editable draft. Import retains every original byte/channel and
all frames in `assets/motions/<sha256>/source.npz`; moving the original is safe.
The immutable version identity combines source bytes, resolved metadata and local
model provenance. Selecting a different version creates a new draft revision and
an immutable `runs/<id>/<revision>/motion.json`; it starts no computation.

Supported motion has numeric axis-angle `poses`/`pose_aa` with shape `(N,66)`
(root plus 21 body joints) or `(N,165)` (full SMPL-X), or `root_orient (N,3)` plus
`pose_body (N,63)`. Translation `trans`/`trans_orig`/`transl` must be finite `(N,3)`
metres, shape `betas`/`beta` is ten constant values `(10,)` or `(1,10)`. Gender is
neutral/male/female. Positive constant FPS and Y/Z-up must be recorded or supplied
explicitly in the form. Aliases, split/full poses, baseline `smpl_pose_axis_angle`,
`coordinate_up` and `frame_time` must agree. Custom timestamps/frame IDs,
per-frame shape, unsupported layouts and non-unit `human_scale` are rejected.
No resampling, scaling or frame removal occurs.

Every archived array is inspected with pickle disabled. Object/structured/complex
arrays, duplicate/escaping archive names and unbounded payloads are rejected;
NPY headers are checked against payload lengths before allocation. Original
untrusted files never reach the native permissive loader. `normalized.npz` is a
separately hashed, generated numeric/string-only native input with explicit
canonical metadata. Native reconstruction uses root/body pose, neutral hands and
omits facial channels; the UI and version record disclose this limitation.

Motion import lazily needs NumPy in the service interpreter. Startup and persisted
viewing do not import NumPy or UMR. `--smplx-model-dir` configures licensed local
weights, defaulting to the existing `/data/motions/human_models/smplx/1.1/…/smplx`
location. A matching `SMPLX_<GENDER>.pkl` or `.npz` must exist; it is hashed and
referenced, never copied or unpickled by import. Missing/changed weights prevent
selecting/reconstructing the asset while saved metadata and viewing remain usable.

Additional owned operations are `import_motion(source_path, metadata=None)`,
`list_motions()`, `get_motion(asset_id)`, `select_motion(run_id, asset_id)`,
`motion_source(asset_id)` and `motion_file(asset_id)`. `MotionAsset` contains frame
count/FPS, pose layout, betas, axes/units, gender, channels, metadata origins, source
and model hashes, and reconstruction disclosure. `motion_source` verifies retained
bytes; `motion_file` verifies the generated input and recorded model. Both return
managed paths. Callers must use `motion_file` for native execution.

HTTP adds `POST /api/motions` with `{source_path, metadata}`,
`GET /api/motions`, `GET /api/motions/<asset_id>`, and
`POST /api/runs/<run_id>/motion` with `{asset_id}`. `/api/state` includes `motions`
and `RunRecord.motion_asset_id`. Expected failures include `missing_metadata`,
`invalid_motion`, `missing_model`, `changed_model` and `changed_asset`.
