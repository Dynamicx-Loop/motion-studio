# Reusable segment binding and motion viewer: handoff

Prepared 2026-10-30 for a new Motion Studio chat using GPT-6 Astra, medium
reasoning. The user requested a reusable Motion Studio module, starting with a
design grilling grounded in the existing docs and working viewer.

## Start here

1. Read root `AGENTS.md`, `README.md`, `docs/workflow.md`, and
   [the current viewer guide](../../docs/umr-g1-binding-viewer.md).
2. Read the installed `mattpocock-skills:grilling` skill and run its interview
   workflow. Investigate repository facts with fresh-context exploration agents
   as the skill directs; user decisions belong in numbered frontier rounds,
   with recommendations. Ask independent questions together, then wait.
3. Inspect the implementation and validation pointers below. Establish the
   design tree from the user's goals and demonstrated needs, rather than
   treating this handoff's open questions as settled requirements.
4. Reach explicit shared understanding with the user before implementation,
   as required by the grilling skill. Capture the agreed design and acceptance
   criteria under this effort using the local tracker conventions.

The installed grilling skill is at
`/home/android/.codex/plugins/cache/mattpocock/mattpocock-skills/1.3.2/skills/productivity/grilling/SKILL.md`.
For module/interface decisions read `mattpocock-skills:codebase-design` and the
repository's domain guidance when applicable. Before creating specs or tickets,
read `docs/agents/issue-tracker.md`; before triage read `docs/agents/triage-labels.md`.
Context7 is required for current library/API documentation per `AGENTS.md`.

## Workspace and preservation

Use `/data/workspace/motion_studio` directly. At handoff its branch is
`experiments/umr-astro`, HEAD `7c0f615ff6b6c411874040fd9da28d566bcbfb82`.
The viewer implementation, guide, and tests below are new, untracked local
files. A checkout of HEAD alone will omit them. Reinspect local status before
editing; preserve unrelated local work, historical experiment aliases,
external checkouts, frozen baseline assets, and existing generated exports.

Motion Studio owns new feature code. External projects remain pinned static
dependencies behind concrete adapters, with their separate runtimes. Follow
`docs/workflow.md` rather than adding product behavior upstream. Preserve the
completed run and use fresh output directories for derived exports.

## Working implementation

The viewer evolved from a static binding inspector to saved G1 playback, then
synchronized reference-human and G1 playback with bindings on both surfaces.
It is a functioning G1/UMR-specific vertical slice, not yet the requested
reusable module.

- Public operation: `motion_studio/integrations/umr_inspection.py`,
  `export_g1_bindings(run, destination, workspace=...) -> BindingInspection`.
- Scientific adapter: `motion_studio/integrations/_umr_inspection_worker.py`.
- Source reconstruction: `motion_studio/integrations/_umr_human_motion.py`.
- Browser: `motion_studio/integrations/_umr_binding_viewer/` containing
  `index.html`, `app.js`, and `human-motion.js`.
- Thin CLI: `scripts/view_umr_bindings.py --run ... --output ...`.
- Guide: `docs/umr-g1-binding-viewer.md`.
- Checks: `tests/test_umr_inspection.py`,
  `tests/test_umr_binding_playback_runtime.py`, `tests/test_umr_human_cache.cjs`.

The current browser URL is
`http://127.0.0.1:8772/manual-01-synchronized/`. Its files are under
`outputs/umr-g1-inspection/manual-01-synchronized/`. The guide includes the
localhost server command if it needs restarting. Previous static and
robot-only exports remain alongside it; preserve them.

The completed source run is `outputs/umr-g1-baseline/manual-01/`:
5,468 frames, 90.00090026855469 FPS, G1 qpos width 36, 4,096 learned paired
slots, native19 source segment labels. Pinned official UMR is
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`; its runtime is
`externals/UMR/.venv/bin/python`. The existing local SMPL-X model is required
for human reconstruction. This workflow does no training, retargeting solve,
or simulation stepping.

Observed behavior worth retaining: shared play/pause, original frame/FPS
scrubbing, frame stepping, speed, loop, segment filtering, paired slot
selection, target body/mesh ownership, ray-picked points, optional paired
lines and mesh visibility, orbit/zoom, front/rear/side camera fitting, static
reference-pose comparison, and optional horizontal centering for both models.
These are existing capabilities, not a preapproved scope for every future
adapter.

## Contracts and current limits

Human bindings use saved learned slot IDs projected to template triangles,
then barycentric transport on the deforming human mesh. Robot bindings are
geom-local points transformed with the mesh geometry at each saved qpos.
Labels describe source segments; target ownership is recorded separately.
They are reconstructed bindings, not saved per-frame optimizer telemetry or
evidence of anatomical accuracy or dynamic feasibility.

The viewer uses Y-up metres. Native robot `[x,y,z]` becomes `[y,z,x]`.
Root quaternions in the saved motion use `wxyz`. Human reconstruction retains
source shape, saved frame IDs, finger policy, ground shift, and retargeting
scale (this run: 0.7957031726837158). Human vertices are root-relative int16
with 0.1 mm steps, chunked in groups of 64 frames, with three chunks cached.
Roots retain float32 precision. Human and robot wait together for required
chunks; display rendering can skip frames to track playback time. Centering
changes display translation, preserving rotations and vertical motion.

Current specialization includes a fixed UMR revision and unchanged source
checks, fixed 4,096 slots, required source reconstruction, G1/free-root and
model geometry checks, contiguous frame IDs, zero-finger SMPL-X route,
unmodified SMPL-X model directory, fixed output filenames/schema, and
vendored Three.js copied from an earlier generated report under
`outputs/umr-binding-report/documentation/vendor`. These assumptions need
inspection and explicit design decisions before generalizing. Consider
validation, failure reporting, asset ownership and licensing as part of the
interface, without promising unsupported formats or robots.

The exporter rejects existing destinations, verifies recorded run artifact
hashes, snapshots the complete run, checks the pinned upstream state before
and after, and records export code hashes, provenance and preservation.
Human source/model hashes are also recorded and checked during export.

## Evidence and checks already run

Read the records rather than rerunning expensive exports merely for context:

- `outputs/umr-g1-inspection/manual-01-synchronized/human-verification.json`:
  direct SMPL-X forward comparison at frames 0, 63, 64, 1800, 2303, 5467;
  maximum vertex-axis error 0.0000501078 m and binding-axis error
  0.0000499597 m, within 0.000051 m. Includes browser observations.
- That export's `provenance.json`, `preservation.json`, `export_source/`,
  `verify_human.py`, and `preview.jpg` preserve the derivation and example.
- `outputs/umr-g1-inspection/manual-01-playback/motion-verification.json`:
  sampled robot world-point error 0.000000119454 m against saved-model
  forward kinematics, within 0.0000005 m.
- Most recent pure + JavaScript selection: 20/20 suites passed. Robot-static
  selection: 2/2 suites passed, including four analytic replay/encoding tests.
- Browser checks covered both moving meshes and slot positions, hand filtering,
  scrubbing, a human-chunk boundary, static comparison, end-stop and looping.
- JavaScript syntax, export hash receipts and whitespace were checked.

Focused commands are documented in `docs/checks.md` and the test metadata.
The last checks used `python3 -B scripts/check.py --tier pure --tier javascript`
and `python3 -B scripts/check.py --tier robot-static --robot-python
/data/workspace/motion_studio/externals/UMR/.venv/bin/python`.

## Candidate interview branches

Settle these through the grilling design tree, respecting prerequisites:
which concrete reuse cases come first; whether the module is an embeddable
viewer, export operation, local application or combination; supported input
and binding contracts; adapter boundaries and runtime ownership; optional
human/robot/binding tracks; synchronization and coordinate/scale semantics;
portable assets and offline behavior; performance and precision budgets;
integration with existing Motion Studio robot/artifact interfaces; migration
and regression acceptance. These are questions, not architectural decisions.
