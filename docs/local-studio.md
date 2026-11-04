# Local Studio

The persistent local application provides saved drafts, managed robot/pose and
SMPL-X motion preparation, explicit native UMR jobs, and read-only historical G1 playback. Startup uses
Python's standard library and independently vendored browser dependencies. Viewing needs neither CUDA nor UMR imports.
Launch from the Motion Studio root:

```sh
python3 -B scripts/studio.py --state outputs/studio-state
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
bindings. Unavailable stages are disabled. Input preparation launches no compute job;
explicit execution controls below launch native stages.

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
training, binding, retargeting and motion. Preparation becomes available after a robot pose is saved. Stage availability uses
`unavailable` and `available`; persistent jobs separately expose their lifecycle state. Historical availability describes
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
stay in the concrete adapter. The execution operations below publish completion only after independent-worker
numerical validation and parent identity/hash/dependency checks.

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
records the copied-file hashes, compiled runtime, limits and derivations. Its
SHA-256 is registered independently in the state SQLite database and verified
before metadata is used. Older/copied asset directories without that registration
fail with `unverified_asset`; reimport their original source closure into a fresh
managed state directory to establish trusted metadata. Keep any
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
  versions and hash-check artifact reads. Returning the native model path also
  verifies every recorded closure file, including mesh/texture dependencies;
  missing, escaping or changed members fail before handoff. Execution should consume
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

## Explicit native stage execution

The **Compute stages** strip above the viewport has **Sampling**, **Binding**,
and **Retargeting** buttons. Each reviews the prerequisite plan without starting
work; use the displayed **Launch … plan** button to execute it. Binding includes
correspondence training, and Retargeting includes all missing prerequisites.
Progress counts, completion, readiness failures, execution errors and Stop remain
visible beside these controls. Per-stage bars use observed training epochs or
retargeted frames; unknown progress is indeterminate. A stage reaches 100% only
after its output is validated. Stage transitions refresh available result tabs
without switching the viewed stage. Detailed native logs remain in Status & logs.
The sidebar's **Advanced execution settings** exposes sampling seed (default 0),
training epochs (500), and trajectory filter (`LQR` or `none`). Merely viewing a tab performs no computation. Saved settings make
an immutable new revision. Modified epochs/seed/filter are experiments; small-epoch
smoke runs are not official-default quality acceptance. Training and solver seeds
stay fixed at zero. The UI `none` value maps to the native solver's `off` value.

The concrete `NativeStages` adapter checks the exact pinned UMR source, independent
interpreter/packages, CUDA device, actual native segmentation/map selection and
licensed input-model hashes. It copies the managed robot closure into a fresh
sampling attempt, applies the saved named radians/root XYZ/wxyz pose, and disables
native XML derivation. Official G1 solve limits apply only to the byte-verified
bundled G1 closure; arbitrary imported robots retain their compiled limits.
For verified official G1, the adapter replaces the generic managed pelvis free
joint in its private copy with native's additional `unitree_g1_float_root` wrapper
(mass 0.001 kg, diagonal inertia 1e-6 kg m²). The pinned pelvis local transform is
verified identity, so saved root XYZ/wxyz maps identically to wrapper qpos. Every
named body's world position/orientation is independently compared before/after
using compiled models and saved qpos at tolerance 1e-10; `model-derivation.json`
records the mapping, inertia and observed errors. Other robots receive no wrapper. Safe
managed normalized motion is the only native input; all its frames are used.

`Studio.plan_execution(run_id, through='retargeting', settings=None)` returns JSON
values: captured run/revision, resolved controls, missing inputs, CUDA readiness,
ordered `stages` needing work, completed stages and semantic fingerprints.
`start_execution` takes the same arguments, saves changed controls as a revision,
and returns a job. Only one native job can be active. Browser navigation and
refresh do not own its lifetime. `get_job(job_id)`/`list_jobs()` return persistent
status, captured plan, stage/attempt identities, observed epoch/frame/log progress
and failure context. `cancel_job` terminates the independent process group and
keeps its logs and partial files; retries use fresh attempts. There is no native
checkpoint continuation. A dead service owner is recorded as interrupted.

The subprocess invokes exactly one of the native dataset/trainer/retarget calls
with `force=True`; it never invokes native `run_pipeline` or implicit stage CLI
routes. Binding invokes the native source barycentric binding, native19 semantic
labeling and projected rigid target-binding functions without solving motion.
The retarget solver recomputes that binding recipe internally; it does not consume
a saved binding NPZ. All merged scientific configuration is persisted in
`humanoid_retarget_runtime_config.json` before native children launch. Retarget
uses the whole managed clip, sequential warm starts and operational SMPL-X batch
cap 128; this cap is not a quality preset.

Attempts have stable fresh paths under
`runs/<run_id>/<revision_id>/<stage>/attempt-<uuid>/`. Completion requires exit zero,
stage-specific numerical validation, confined nonempty required outputs and exact
SHA-256 publication. SQLite publishes the completion atomically only while the
job/revision/settings/dependency fingerprints still match. Cancelled, failed or
changed-input attempts never become reusable completions. A completion receipt
records input/closure/model hashes, exact dependency receipts/artifact hashes,
settings, native/adapter/runtime identity, command/environment overrides, validation
findings and completed UTC. Semantic fingerprints exclude transient attempt/output
paths. Reuse is limited to authenticated compatible prefix stages of the same run; changing recorded bytes
invalidates completion. Related settings revisions can reference an original receipt,
with its revision and receipt hash recorded independently. Every read recursively
checks the original artifacts and dependency chain. Sampling is 4096 paired points with valid reference meshes;
training validates final checkpoint epochs, paired slots/order and normalization;
binding validates barycentric and rigid replay/reference geometry; motion validates
exact frame IDs/FPS, finite qpos, joint order/limits and unit root quaternions.
These representation checks make no contact, collision or dynamics claim.

`stage_receipt(run_id, revision_id, stage)` returns the detached verified receipt.
`stage_artifact(run_id, revision_id, stage, name)` returns only a unique registered
artifact by name/suffix after rechecking the entire receipt's bytes. The receipt's
`artifacts` maps attempt-relative paths to SHA-256. Stage consumers should use:

- sampling: `dataset.npz`, `humanoid_retarget_runtime_config.json`,
  `model/__studio_model.xml` and copied closure;
- training: `train/checkpoint-final.pt`,
  `train/correspondence_slots_final.npz`;
- binding: `binding.npz`, `bindings.json`, human/robot vertex/face binaries;
  static JSON has geometry, paired slot indices, source/target points, semantic
  labels, target body/geom ownership and projection errors, with no motion required;
- retargeting: `motion.npz`; every stage also records `config.json`, `request.json`,
  `command.json`, `native.log` and `validation.json`.

HTTP adds `POST /api/runs/<id>/plan` and `…/execute` with exact fields
`{through, settings}`, `GET …/settings`, `POST …/settings` with `{settings}`,
`GET /api/jobs/<id>`, `POST …/cancel` with `{}`,
`GET …/log/<stage>`, and `GET /artifacts/<run>/<revision>/<stage>/<name>`.
`GET /api/runs/<id>/stages/<stage>/receipt` exposes the verified current-revision
receipt; the UI links native outputs, resolved config, numerical validation and
receipts under each available stage. `GET /api/state` includes jobs. Errors retain
the structured loopback contract.

The independent worker removes inherited `PYTHONPATH`/`PYTHONHOME` and sets
`PYTHONNOUSERSITE=1`; it preserves `HOME`. Readiness uses the same environment.
Exact execution overrides are recorded in `command.json`; logs retain native
commands and output. An externally generated checksum alone is insufficient for
completion: both the numerical worker and the parent publication checks must pass.

The static source binding deliberately uses native face IDs/barycentric weights
for replay. Native's tiny-triangle fallback can return vertex-0 weights while its
nearest-point diagnostic differs. `binding.npz`/`bindings.json` retain that native
closest point and per-slot discrepancy separately; displayed source binding points
are reconstructed from face+bary, matching the solver's replay representation.
Semantic labels still use the unchanged native labeling inputs. No tolerance is
relaxed to conceal this diagnostic discrepancy.


Native model configuration passes the **exact validated `MotionAsset.model_path`
file** for both `smplx_model_dir` and sampling `smpl_models[].dir`. Native supports
this file argument. Consumers/exporters must preserve it rather than reverting to
the parent directory: directory loading can select an unrecorded alternate weight
or overlay manifest. Existing frozen historical exporters keep their old contract;
new inspection adapters must use the exact recorded file.

Publication rechecks every captured dependency receipt and all its artifact hashes
inside the final SQLite publication transaction. Public receipt/artifact reads
recursively recheck the dependency chain, so a changed sampling artifact also
invalidates a previously completed training/binding/retarget receipt.

Focused CUDA smoke commands (fresh destinations required):

```sh
python3 -B scripts/smoke_studio_native.py --output /absolute/fresh/g1-smoke
python3 -B scripts/smoke_studio_native.py --output /absolute/fresh/primitive-smoke --primitive
STUDIO_G1_SMOKE=/absolute/fresh/g1-smoke \
STUDIO_PRIMITIVE_SMOKE=/absolute/fresh/primitive-smoke \
  python3 -B -m unittest discover -s tests -p test_studio_native_runtime.py -v
```

These intentionally derive a separately labeled three-frame fixture from the
preserved HiPHI source and use two training epochs. The application still passes
all frames of its selected managed motion without trimming/resampling. The smoke
script records fixture conversion and original-source hash. The primitive cohort
stops at binding with no motion file and covers native tiny-triangle diagnostics.
Neither smoke establishes full-clip/default quality; the separate
[full G1 acceptance](../outputs/artifact-archives/experiment-reset-20261104/experiments/studio-baseline-acceptance-20261030/README.md)
records fresh 500-epoch/all-5468-frame application execution. Ticket 05 adds rich stage/animated
inspection and standalone exports; ticket 06 deepens lifecycle/recovery UX.

## Stage inspection and standalone exports

Select an available sampling, training, binding, retargeting or motion tab to
load its visualization directly in the viewport. Missing views are prepared
automatically from saved results; cached views reopen immediately. Loading and
failures are visible, with explicit retry after a failed preparation. This
CPU-only derivation does not train or solve motion and can run while a native job
computes. Standalone export remains a separate optional action. Its output is always a fresh directory under managed
`exports/`; failed derivations retain their fresh log/failure files and are never
published as an inspection. Historical viewing still uses the preserved original
owned viewer. New imports use an additive stage viewer, with local vendor bytes
independently checked against `web/vendor-manifest.json`.

Native completed stages use the main **Properties** panel for playback, exact
frame/segment/slot selection, binding readouts, mesh/point visibility and camera
presets. The embedded renderer fills the viewport without its own sidebar.
Static stages show a concise reference-pose label and the applicable binding
controls; motion retains exact stepping, timeline, speed, loop and centering.
Clicking a rendered point updates the same selected slot in Properties. Renderer
loading/errors appear there with **Reload stage viewer**; derivation failures
retain their separate retry action. Standalone viewers retain their own controls,
and the preserved historical viewer keeps its original layout.

The live shell at `/stage-inspection/index.html?bundle=<registered-viewer-url>`
reads data through the existing hash-checked inspection resource routes. It does
not modify cached bundle bytes or their integrity registrations. Its owned
`motion-studio-inspection-v1` bridge publishes renderer control capabilities,
values and readouts; Properties sends only control commands, leaving playback,
frame commits, selection and camera state in the renderer. Both sides check the
message origin, source window and a navigation-specific session. Run/revision/
stage switches and explicit reload allocate fresh sessions, rejecting old messages.
State updates preserve existing input elements so playback does not replace
focused controls. New standalone exports include the bridge locally; embedded
mode is opt-in, so independently served bundles retain their sidebar.

Sampling shows independent sampled surfaces: matching sample indices do not imply
learned correspondence, so paired lines are disabled. Training shows learned
paired slot identity before rigid ownership exists. Binding uses the verified
pre-solve JSON/geometry/NPZ, including primitive geometry and optional mesh names,
without requiring motion or licensed weights. Source native19 semantic labels,
paired slot index, and target body/geom ownership remain distinct. Source points
use face+bary replay; raw native closest-point discrepancies remain separately
visible. Reference projection errors are diagnostics, not motion quality scores.

Motion reconstruction uses the exact receipt-validated SMPL-X model **file** and
SHA-256; selecting a parent directory or changed model is rejected. It retains
neutral-hand/omitted-face disclosure, all exact frame IDs and FPS, saved source
scale and ground convention. Robot motion stores rigid geom-local meshes and
frame transforms; human motion uses 64-frame int16 root-relative vertex chunks
at 0.1 mm steps. The maximum allowed human axis decoding error is 5.1e-5 m and
robot binding replay axis tolerance is 5e-7 m. Frame requests commit both tracks
only after the requested human chunk is ready. Three chunks are cached with the
displayed chunk pinned; stale requests cannot replace a newer seek, and a missing
chunk stops playback with an error. No interpolation or nearest-frame fallback
is used. Filtering, paired-slot selection/lines, mesh visibility, camera presets,
orbit/zoom, reference pose, exact stepping/scrubbing, speed/loop/end-stop and
horizontal centering are retained. Centering and placement affect display only.

`Studio.build_inspection(run_id, stage, revision_id=None)` captures one revision
and returns its bundle path, viewer URL and file manifest URL. `motion` is an
inspection alias for the retargeting completion. `stage_artifacts(run, revision,
stage)` batch-resolves registered files after recursively verifying the receipt
once; a reused receipt retains its authenticated source revision. Export rechecks
all captured source bytes before and after derivation and rechecks receipts
before publication. `exported_inspection_file(run, revision, stage, name)` serves
only registered, hash-checked bundle resources; existing bundles do not require
source weights, an independent runtime or intact source completions to view.
HTTP adds `POST /api/runs/<run>/inspections/<stage>` with `{revision_id}` and
`GET /inspection/<run>/<revision>/<stage>/<resource>`.

**Native outputs, config, logs** opens the standalone file index. Each bundle
contains copied native artifacts/receipts, export provenance, preservation/hash
manifests, notices, and all frontend dependencies. It excludes licensed weights.
To view independently, serve the returned directory over local HTTP, for example
`python3 -m http.server --bind 127.0.0.1 --directory /absolute/bundle/path`.
No UMR runtime is needed for viewing; double-click/file-URL support is not promised.
Original robot, motion and human-model terms remain separate.

Fresh derivative validation against the completed focused native smoke (no new
training and no writes to that source) is available through:

```sh
python3 -B scripts/smoke_studio_inspection.py \
  --source /absolute/completed-native-smoke --output /absolute/fresh-derivative
STUDIO_INSPECTION_SMOKE=/absolute/fresh-derivative \
  externals/UMR/.venv/bin/python -B -m unittest discover -s tests \
  -p test_studio_inspection_runtime.py -v
node tests/test_studio_frame_requests.cjs
```

The three-frame smoke establishes bounded representation and offline viewing.
Native full-clip chunk-boundary comparisons and default/full-clip execution
are recorded in [the full acceptance experiment](../outputs/artifact-archives/experiment-reset-20261104/experiments/studio-baseline-acceptance-20261030/README.md),
separate from analytic 64-frame quantization and asynchronous boundary tests.

## Recovery and immutable revision history

The **Saved revision** selector restores a persisted snapshot independently of the
latest editable revision. Viewing an old snapshot never moves the editable head;
select the latest revision to change its inputs or settings. Saving a robot pose,
motion selection or execution settings creates a new revision, preserving the other
selected inputs and settings. An unchanged save creates no revision and queues no
work. A viewed latest revision follows its next saved edit; an explicitly selected
older snapshot stays selected across refresh/restart.

Settings changes retain only an authenticated unchanged prefix: epochs changes can
reuse sampling; trajectory filter changes can reuse sampling, training and binding.
Sampling-seed changes invalidate all native stages. Robot, pose or motion-version
changes invalidate every native stage, including cross-clip correspondence. New
receipts preserve the exact reused dependency receipts and hashes. Available reused
stages identify the source revision; affected stages show **stale** and require an
explicit launch. Corrupt receipts/artifacts make the entire dependent chain stale.
Old revisions and their original files are never rewritten by reuse or retries.
The plan returns `reuse_policy='verified-related-revisions'` and a visible policy
message; environment/fingerprint mismatch also forces fresh computation.

Launch review/insertion is protected across threads and local service processes;
only one active job can exist in a state root. Other drafts/runs remain browsable.
The persistent status footer exposes **Stop active job** while viewing any run.
Closing a browser tab or refreshing leaves the server-owned process running.
Stopped/failed/interrupted jobs offer **Review explicit retry**: the plan lists the
verified prerequisites that remain and allocates fresh attempt directories for all
work that needs restarting. No automatic queue or mid-stage epoch/frame resume is
provided. Completed prerequisites, partial files and native logs are retained.

On Linux, the service records its PID, kernel process start identity, boot ID and
PID namespace; a small stdlib guard owns each native process group and watches
that service identity.
Service death stops the group (TERM then KILL, including TERM-ignoring descendants).
Reopening detects a dead owner, kills any still-owned verified group and marks the
unfinished job and attempt `interrupted`. PID reuse cannot target an unrelated
process. Recovery signals verified groups only in the same boot and PID namespace. A
previous boot proves interruption without signalling a stored PID. If owner
visibility differs or cannot be established (including legacy jobs without scope
metadata), the job stays active/busy with a visible recovery notice; absence from
the current process namespace does not prove service death. Inspect/cancel it
from its original service environment. Legacy jobs without a birth identity are
never signalled using an unverified PID. Terminal state updates are monotonic, and final publication checks
refuse cancelled, interrupted or changed-revision callbacks.

Additional owned reads are `get_run(run_id, revision_id=None)`,
`list_revisions(run_id)`, `execution_settings(run_id, revision_id=None)` and
`selected_revision_id()`. `select(run_id, revision_id=None)` persists the viewed
snapshot, defaulting to the current head. `RunRecord.is_latest` indicates whether
that snapshot is editable; `StageState.reason` explains stale/reused availability.
HTTP adds `GET /api/runs/<id>/revisions`, `GET …/revisions/<revision>`,
`GET …/revisions/<revision>/settings`, and
`GET …/revisions/<revision>/stages/<stage>/receipt`. Selection accepts an optional
`revision_id`; `/api/state` includes `selected_run` and its `revisions`.

Lifecycle tests use real subprocess fixtures through public Studio/HTTP operations,
without repeating native numerical solves. Browser evidence is under
`outputs/studio-lifecycle-ticket06-20261030/`: its clearly labeled subprocess fixture
exercises close/reopen, saved-run browsing during work, Stop/retry, related settings
reuse, stale stages and old-revision refresh restoration. Native full-clip/default
quality acceptance is recorded in [the full application experiment](../outputs/artifact-archives/experiment-reset-20261104/experiments/studio-baseline-acceptance-20261030/README.md).

## Replay encoding and adapter launch boundary

New native inspection derivatives declare robot `transform_schema: 2` and
`transform_dtype: "<f8"`: little-endian float64 row-major 3×4 geometry-local to
world matrices in saved frame/geometry order. Before publication the exporter
decodes the saved bytes and checks every robot binding against native kinematics
at the unchanged 5e-7 m per-axis tolerance. `max_binding_axis_error_m` records the
largest measured error. The viewer accepts original bundles with absent encoding
metadata as their original float32 representation; unknown encodings fail clearly.
This representation check makes no claim about motion quality or dynamics.

Owned historical and native viewers use one human chunk-cache source. Fresh
standalone bundles copy it into their root alongside the transform decoder, so
all application imports remain local relative paths. The original integration
viewer and historical output bytes remain preserved.

`NativeStages.launch` owns process environment/command provenance and temporary
runtime directories; `decode_progress` translates observed native output, and
`required_artifacts` identifies native stage completion files. Studio owns the
process group, cancellation, elapsed time, retained logs and atomic receipt
publication. These lifecycle operations share a leaf UTC timestamp module and
have no reverse import from the native job runner to execution operations.

Native CUDA acceptance services must run in the host environment that exposes
CUDA and the owning process namespace. The validation agent's restricted shell
can use a separate PID namespace: opening the same state there cannot establish
host-owner death. Run the persistent service and its native workers in one
execution environment; a browser can connect from another environment without
starting a second service against the same state. The final acceptance cohort
uses fresh managed state and host execution, preserving the initial cohort and
the recorded namespace-mismatch incident.

## Full G1 workflow and local prerequisites

Use the existing pinned UMR environment and licensed local SMPL-X files; the
application installs or downloads nothing. The service Python needs NumPy for
motion import. Robot compilation uses `--robot-python` (default: the canonical
UMR `.venv/bin/python`), and `--smplx-model-dir` selects the existing licensed
model directory. Native execution requires host CUDA; run the service in the
host process namespace. Viewing an exported bundle requires only local HTTP and
a WebGL browser. A sandbox without CUDA is suitable for saved viewing, not native
acceptance. Keep services sharing state in the same process namespace.

For the demonstrated G1 case:

1. Create a named draft. Import the pinned
   `externals/UMR/assets/g1/g1_29dof.xml` and enable fixed-to-floating derivation.
2. Choose the imported robot and **Load official G1 T-pose**. This only loads
   unsaved controls. The adapter checks the complete managed source against the
   pinned official closure and configuration; other or changed imports receive
   `unsupported_preset`. Generic numeric poses and saved named poses remain usable.
   **Save pose to fresh revision** records the selected waist-yaw centering and
   official shoulder/elbow values, in radians.
3. Import the complete bundled HiPHI
   `sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
   The library reports 5468 frames, 90.00090026855469 FPS, neutral gender and Y-up.
4. Keep sampling seed 0, epochs 500 and LQR. Review the prerequisite plan, confirm
   that CUDA is ready, then **Launch reviewed plan**. Tabs themselves launch no
   work. Native stage progress and retained log links appear in the footer.
5. Select an available stage to load its visualization automatically. Sampling shows
   independent sampled surfaces; training shows learned pairs; binding adds native
   semantic labels and target ownership; motion preserves exact source timing.
   Use the saved revision selector to inspect earlier results after changing inputs.
6. Open **Native outputs, config, logs** for the standalone file index. Serve the
   returned fresh bundle directory with local HTTP to view it independently.

`official_robot_pose(asset_id) -> RobotPosePreset` and
`GET /api/robots/<asset_id>/official-pose` return typed unsaved values, units and
centering body. They create no named pose, revision or compute job. Official G1
solve limits remain isolated in the concrete adapter; this preset never applies
G1 assumptions to other imports.

The [acceptance experiment](../outputs/artifact-archives/experiment-reset-20261104/experiments/studio-baseline-acceptance-20261030/README.md)
records full-clip numerical gates, machine timings, browser actions, source hashes,
original preservation and limits. Its offline audit establishes that observed
resources were local; it does not claim that networking was disabled. Input,
robot asset and model terms remain separate. Neutral hands and omitted facial
channels are a reconstruction limit, not a change to preserved source bytes.

## Asset library and quick source preview

The left library now offers four real, locally bundled pinned UMR robots: Unitree
G1, Booster K1, HiTorque PiPlus and EngineAI T800, plus the bundled **Astro P2**
default 29-joint model from `menagerie_x`. Drag a card into the scene or
choose **Add robot**. Each imports its verified complete closure and native named
T-pose; previewing starts no sampling, training or solve. Editing a completed run
or historical reference this way creates a new asset-study draft. Ordinary draft
input changes retain the existing immutable-revision behavior. All prior viewers
and completed outputs remain available in **Saved runs & history**.

PiPlus and T800 use sibling mesh/texture directories upstream. Their owned
adapter copies pinned, byte-verified dependencies into a confined portable model,
rebasing only file references. Managed `source/provenance/` retains the original
XML/dependency bytes, preset and hash-bound derivation description. G1/K1 retain
their normal import path. No external source or pin is changed. Robot cards use
locally rendered thumbnails of these actual compiled T-poses; separate robot
mesh redistribution terms still apply. Texture reproduction remains unsupported.

Astro uses the self-contained [root asset snapshot](../assets/robots/astro_p2/README.md)
at `menagerie_x` revision `8e3f382f28831331c448c9d62cd197140da63c65`.
Its original XML, 37 meshes, shared collision models and notices remain unchanged;
an owned XML derivative expands the geom-only attachments for the existing Studio
importer. Per-file hashes are checked before and after import, and managed
provenance preserves the original XML and notices. This card needs neither a live
`menagerie_x` nor UMR checkout for importing/previewing; it uses the configured
independent robot runtime. Native retargeting still requires UMR and its separate
inputs. The 43-joint articulated-hand variant and historical Astro catalog pins
remain separate. Astro's card thumbnail renders visual group 1 without collision
group 3 overlays; saved model geometry and collision settings are preserved.

The preview floor follows the actual transformed mesh lower bound. This is display
placement only: root XYZ/wxyz, joint values, saved poses and native calibration
are unchanged. It does not establish foot contact or dynamic feasibility.

Drop a self-contained MJCF, select its dependent files, choose a folder, or drop a
ZIP. The chooser opens to select the main XML if the bundle has several XML files;
for ZIPs supply its exact internal main XML path, or leave blank if there is only
one. Import is explicit after file selection. Fixed-to-floating derivation is an
explicit checkbox. Uploads allow at most 2048 files / 128 MiB unpacked and refuse
escaping, duplicate/noncanonical paths and archive symlinks. Browser bundles use their explicitly uploaded root as the closure boundary;
sibling paths inside that bundle are rebased with originals/provenance preserved.
Absolute local-path imports retain their strict main-file-parent boundary.
Missing or escaping dependencies fail instead of being fetched or guessed.

**Motions** offers the full bundled HiPHI get-up clip, a separate 2-second quick-test
excerpt, and the full ADAPT Y-up source person motion (its pinned wrapper declares Y-up;
interaction objects are omitted).
Sample cards display actual SMPL-X surface thumbnails and offer source preview
without selecting a run. Explicit **Use** selects the managed clip. Source mesh
play/pause, exact stepping/scrubbing, looping and orbit/zoom work before any native
training. This is reconstructed source motion; robot retargeting remains a
separate explicit operation. The short clip retains exact source frames `[0, 180)`, original
FPS and translations; its original NPZ records parent path, SHA-256, revision,
full frame count and trim interval, without resampling/scaling. **Original NPZ /
provenance** downloads these retained bytes. Native execution uses exactly the
selected clip; choosing the full source intentionally retains all its frames.

New source previews require the configured independent UMR interpreter, matching
licensed weights and existing lazy NumPy motion-import dependency. Registered
previews reopen with checked hashes without scientific dependencies or weights.
Surface previews preserve every source frame, exact FPS and original source
translation in metres/Z-up. Hands are neutral and facial channels are omitted.
The separately versioned `motion-studio-source-mesh-v1` manifest records the native
triangle topology, source/model SHA-256, pinned native revision, input up-axis,
whole-clip bounds and minimum native Z for display grounding. No ground shift,
resampling or scale is applied to the stored mesh. Sixty-four-frame little-endian
int16 chunks encode root-relative XYZ at 0.1 mm steps, with per-frame native root
positions and measured maximum per-axis error at most `5.1e-5 m`. Only the small
manifest uses JSON; the full source vertices remain bounded binary chunks.
The CPU preview limit is 20000 source frames. It starts no native job and makes
no run revision. Existing joint-only previews and their registry remain intact.

Additional operations: `asset_catalog()`, `add_builtin_robot(id)` returning an
imported asset plus unsaved preset, `add_sample_motion(id)`, `upload_robot(files,
entry_path='', derive_free_root=False)` for bounded `{path,data(base64)}` file
records, `build_source_preview(asset_id)` and `source_preview_file(asset_id)`.
The surface operations are `build_source_mesh_preview(asset_id)` and
`source_mesh_preview_file(asset_id, name='manifest.json')`. The cache registers
each manifest, face topology and vertex chunk with its own independent SHA-256;
unregistered files, traversal, symlinks, changed bytes and escaped roots fail.
Concurrent requests for the same asset/schema share one CPU reconstruction.
HTTP adds `POST /api/catalog/robots` and `…/motions` with `{id}`,
`POST /api/robot-upload`, `POST /api/motions/<id>/preview` with `{}`,
`GET /api/motions/<id>/preview-data` and `…/source`. Asset actions verify actual
pinned bytes at import; catalog availability alone is not runtime readiness.
Mesh HTTP uses `POST /api/motions/<id>/mesh-preview` with `{}` and
`GET /api/motions/<id>/mesh-preview-data/<registered-file>`. The POST returns the
manifest URL; the manifest names topology and chunk resources for read-only
loading. A legacy skeleton derivative cannot satisfy a surface request. Sample
catalog entries expose their managed `asset_id`, frame count and FPS after
idempotent import, allowing one unified card for catalog and imported versions.
