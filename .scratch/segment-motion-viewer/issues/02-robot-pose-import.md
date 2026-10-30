# 02 — Import robot assets and edit named T-poses

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: 01

## Context and outcome

Deliver import robot assets and edit named t-poses as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [x] Import G1/local MJCF closure via app into immutable managed assets; compile in pinned runtime, resolve units/defaults and enforce accepted hinge/root subset.
- [x] Validate nested dependencies, missing/escaping/cyclic paths and unsupported joints; root conversion occurs only on derived copies with recorded provenance.
- [x] UI provides torso selection, numeric/root/joint controls with visible mesh preview, limits, reset and named pose save/load.
- [x] Pose changes create new revisions without mutating imported originals or completed runs; tests cover compiled fixture/defaults and failure cases.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.

Claimed by ticket 02 implementer on isolated branch `codex/studio-02`.

## Answer

Implemented the owned robot import and numeric pose slice, including the same
service/HTTP operations consumed by the application UI. Source closure traversal
checks nested includes with main-file-relative MJCF semantics, compiler asset
directories and texture faces; copies are hash-identified and compiled in the
explicit independent MuJoCo interpreter. Compiled defaults/degree conversion and
finite named hinge limits determine the contract. Unsupported joints/roots,
missing/cyclic/escaping dependencies, invalid material references and malformed
poses fail explicitly. Fixed-to-free conversion writes only expanded derived XML;
synthetic inertia is recorded when a massless root needs it.

The local editor renders compiled mesh geometry and pose transforms, provides
searchable joint sliders/numbers, root XYZ/quaternion controls, explicit units,
limits, reset, torso selection and immutable named pose save/load. A saved change
allocates a fresh revision, preserves earlier pose/revision files, and exposes
preparation inspection without launching work. Robot/motion selection histories
survive each other's revisions and service recreation. Metadata/pose contracts
and the optional `--robot-python` interpreter path are documented in
[Local Studio](../../../docs/local-studio.md).

Validation (2026-10-30):

- TDD red/green cycles through `Studio` import/pose operations and the real HTTP
  surface; 25 combined Studio tests passed after merging ticket 03. Fixtures cover
  compiled degree/default limits, nested closures, fixed-root synthetic inertia,
  unsupported joints, bad/missing/cyclic/escaping dependencies, named pose limits,
  immutable versions/revisions, and robot/motion selection preservation. A worked
  hinge rotation is checked against independent numerical literals.
- The root pure check passed all 22 selected suites before integration and all
  23 selected suites after merging ticket 03. Node syntax checks passed for app, robot,
  robot-preview and motion modules; `git diff --check` passed.
- Real pinned G1 `g1_29dof.xml` compiled and imported: 29 hinges, nq 36, 101 robot
  geoms. Canonical source was read only. Browser forms on a fresh local test state
  imported that G1 and the full existing HiPHI motion (5468 frames,
  90.00090026855469 FPS), saved the robot pose at r0002, selected motion at r0003,
  and saved shoulder ±1.5 rad at r0004. Reload restored both input selections and
  exact joint values. Reset, named pose loading, torso selection, searchable
  controls and visible mesh changes were exercised. Browser smoke states are
  `/tmp/studio-02-g1-check` and `/tmp/studio-02-combined`; no native solve was started.

Limits: preview uses compiled RGBA rather than texture rendering; geometric
primitives are triangulated for display. Structural support does not certify
humanoid morphology, contacts or dynamics. Native stage execution/cache lifecycle
and full G1 solve acceptance remain later tickets. Existing viewer, runs and pinned
externals were not modified.

### Import review corrections (2026-10-30)

Review of the completed import slice at integration `3e081b5` reproduced three
observable defects. Each fix used a red/green regression through the public
`Studio` import, native-file, metadata or pose operation, with the canonical
independent interpreter at `externals/UMR/.venv/bin/python`:

- Changing a managed tetrahedron OBJ after import still allowed
  `robot_file(id, 'source/__studio_model.xml')` to return the native model. That
  handoff now verifies every recorded file's confinement, presence and SHA-256;
  changed and missing mesh dependencies both reject it. Preview uses this same
  closure-checked handoff.
- Editing `asset.json` to raise the compiled hinge maximum to 999 allowed a
  saved qpos of 100. The importer now registers a SHA-256 derived from its trusted
  compiler record independently in SQLite. Metadata is verified against that
  registration before decoding or use, so changed limits and replacement per-file
  digests fail on pose save, native handoff, reopening and reimport. Existing JSON
  schema and asset identities remain unchanged. Legacy/copied directories lacking
  a trusted registration fail clearly with `unverified_asset`; their original
  closure can be imported into a fresh managed state directory.
- A valid fixed root containing an explicit zero-mass/zero-inertia element failed
  floating-root derivation because the worker appended a duplicate inertial.
  Derivation now replaces that element on the managed copy. The regression checks
  the single synthetic 0.001 kg / diagonal 1e-6 kg m² inertial, successful compiled
  preview and unchanged source bytes.

Validation: all 29 combined Studio tests passed, including four added regressions
for the three findings and rejection of unregistered legacy metadata. All 23
selected pure suites passed via `python3 -B scripts/check.py --tier pure`, and
`git diff --check` passed. The review
corrections do not exercise native pipeline stages or claim full-run acceptance.
