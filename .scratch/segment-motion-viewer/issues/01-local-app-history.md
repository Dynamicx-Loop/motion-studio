# 01 — Persistent local application and historical playback

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Context and outcome

Deliver persistent local application and historical playback as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [x] Launch a loopback offline application with the agreed layout, API error handling and thin CLI; importing service modules needs no upstream scientific imports.
- [x] Create/list/reopen persistent drafts and read-only historical result registrations through UI and owned typed operations.
- [x] Open preserved G1 inspection in the app without altering its files; all frontend assets served locally with notices, independently packaged from old output locations.
- [x] Establish documented internal service/adaptor result contracts for downstream tickets, including run/revision/stage identities and managed storage roots.
- [x] Browser refresh restores selected persisted state; API/path validation and historical read-only behavior tested; original viewer files remain unchanged.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.

Claimed 2026-10-30 by ticket 01 implementer in `codex/studio-01`. Public seams: typed persistent Studio operations and HTTP/browser outcomes, as approved by the parent spec Testing Decisions.

## Answer

Implemented the additive `motion_studio.studio` package, thin `scripts/studio.py`
CLI and offline local application. Drafts, historical registrations and selected
run identity persist in SQLite. Historical inspection references are confined to
explicit configured roots, recorded by SHA-256 and served read-only through owned
frontend code; historical scripts are never executed. Frontend Three.js r165 and
OrbitControls are independently vendored with MIT notices and a provenance/hash
manifest. Existing viewer source, historical result bytes and externals were not
modified. Managed storage and typed service/adapter result contracts are documented
in [Local Studio](../../../docs/local-studio.md).

TDD observations: initial draft test failed on missing service package; historical
registration failed on absent operation; HTTP creation failed on missing transport;
independent viewer HTTP test failed on missing owned assets; storage-failure test
failed on a dropped connection before structured 500 handling was implemented.

Validation on 2026-10-30:

- `python3 -B -m unittest discover -s tests -p 'test_studio*.py' -v`: 9 passed.
- `python3 -B scripts/check.py --tier pure --json`: all 20 selected suites passed,
  including the two new Studio suites; six runtime/JavaScript suites not selected.
- `node --check` on the new app and copied inspection app/human-motion modules:
  passed. `git diff --check`: passed with upstream vendor whitespace explicitly
  preserved by its scoped `.gitattributes`.
- Chrome via loopback port 8783 opened preserved `manual-01-synchronized`: both
  meshes/bindings rendered, 4096 slots/19 segments, timeline 0–5467 at saved
  90.00090026855469 FPS, exact +1 step reached source frame 1. Browser refresh
  restored the historical selection. Draft creation through the UI and subsequent
  refresh restored that draft. All parent/iframe resource URLs used the local
  origin. Screenshot: worktree `outputs/ticket01-browser.png` (ignored).
- Expected errors tested: invalid names/fields/JSON/IDs, escaping and symlinked
  historical files, changed artifact hashes, historical mutation, cross-origin and
  invalid Host requests, and storage failure. Import and CLI help use no NumPy,
  Torch, MuJoCo or SMPL-X runtime.

Scope limits: saved-viewing/draft slice only. Preparation, native execution,
job lifecycle, new numerical validation and fresh full G1 acceptance belong to
subsequent tickets. Refresh restores run/revision identity; transient playback
frame/camera/filter state reloads from the inspection's initial frame.
