# 13 — Inspection controls in the main Properties panel

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Context

Completed stage viewers embed their own 280-pixel sidebar inside the scene even
though Studio already has a Properties panel. Consolidate the controls without
creating a second independent playback/selection state.

## Scope

Use an owned live embedded renderer against registered, hash-checked inspection
resources. Move playback, exact frame, segment/slot, binding display, mesh and
camera controls to main Properties with synchronized renderer state. Preserve
standalone controls, historical viewer routes, completed outputs, export bytes
and registered hashes. Stage/run/revision changes discard old renderer sessions.
No native computation or external source changes.

## Acceptance criteria

- Embedded stage geometry uses the whole viewport without an inner sidebar.
- Properties commands operate the renderer; playback and point picks update the
  same Properties state without rebuilding focused controls on every frame.
- Static-stage disabled controls and sampling unpaired-line restrictions remain.
- Loading, resource failure and retry are visible; stale sessions cannot act.
- Original standalone bundles and historical viewer continue to work.

## Validation

Focused JavaScript command/state tests, HTTP static resource and confinement
checks, inspection/export checks and browser QA by the coordinating agent.

## Comments

2026-10-30: Claimed for the user-requested delegated refinement. New live shell
avoids mutating previously exported frontend bytes or integrity registrations.

## Answer

Implemented an owned live renderer shell that reads existing registered bundle
resources without overwriting exported files or integrity registrations. A
versioned command/state bridge keeps exact frame commits, playback, selection,
camera and rendering state in the renderer; Properties displays capabilities and
sends commands. Both sides validate origin, source window and navigation session.
Stage/run/revision changes and reload reject stale messages. Existing input DOM
survives frame updates. Static stages hide disabled playback and show the reference
pose label before segment/binding controls. Export links also live in Properties.

Standalone exports keep their original controls/layout and include the local
bridge dependency; existing standalone bundles and historical viewer routes remain
unchanged. Historical inspection intentionally retains its previous layout.

Validation passed:

- `node tests/test_studio_inspection_bridge.cjs`: renderer command/state sync,
  origin/source/session checks, disabled controls, resource confinement, control
  persistence, reload, failure and stale navigation.
- `node tests/test_studio_inspection_controls.cjs`: existing cached bundle reuse,
  stage aliases, asynchronous failures/retry/export and stale view handling.
- `python3 -B -m unittest discover -s tests -p test_studio_http.py -v` (5 cases)
  and `-p test_studio_inspection.py -v` (4 cases), including closed standalone
  imports, immutable source bytes, static route confinement and no job creation.
- `externals/UMR/.venv/bin/python -B -m unittest discover -s tests -p
  test_studio_inspection_playback.py -v`: 6 independent rigid/quantization cases,
  including exact 64-frame chunk boundary and float64 binding precision.
  System Python lacks MuJoCo; the owning UMR interpreter passes these checks.
- Existing frame-request, execution-control, robot-transform and source-mesh
  JavaScript suites passed. `git diff --check` passed.

Coordinator browser QA opened existing Binding and full-clip Motion bundles with
no console/page errors. Next slot updated binding slot 1; +1 frame displayed
exact frame 1/5467 and source frame 1. The inner sidebar is hidden and canvas fills
the iframe. Static playback group is hidden. Evidence:
`outputs/studio-layout-20261030/properties.png`, capture
`ev_4a9fbe7411e98f928022b09b4e117ff5b7ad62272ce46b4b1742f7938211900a`.
Coordinator preservation verification passed all 288 protected files. No native
job was launched and no external source or pin changed.
