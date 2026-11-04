# 05 — Inspect stages and export synchronized moving bindings

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: 04

## Context and outcome

Deliver inspect stages and export synchronized moving bindings as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [x] UI renders samples/canonical bindings and saved motion from explicit adapter artifacts, preserving agreed existing viewer controls.
- [x] Generalize owned inspection path for accepted robot imports while retaining 4096/native19 and SMPL-X constraints; original viewer implementation remains preserved.
- [x] Exact frame stepping/scrubbing and synchronized chunk readiness, display-only transforms and bounded caching; errors surfaced instead of mismatched frames.
- [x] Fresh standalone bundles include local dependencies/notices and native result/config/log/provenance access; no runtime needed to view.
- [x] Independent numerical/reference and JS tests retain agreed robot/human tolerances, chunk-boundary/race cases and no original-run mutation.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.

2026-10-30: Claimed ticket 05 in isolated `codex/studio-05`. Confirmed public seams: owned Studio inspection/export and HTTP operations, saved numeric replay and JavaScript synchronized frame/cache behavior.

## Answer

Implemented owned, additive stage and animated inspections plus fresh standalone
HTTP bundles. Sampling indices, learned pair identity, source native19 labels and
rigid target ownership remain distinct. Static bindings consume the explicit
verified JSON/NPZ/geometry and retain native closest diagnostics separately from
face+bary replay. General robot geometry includes primitives with optional mesh
names. Original viewer/human helper and completed native cohorts remain unchanged.

Public Studio/HTTP builds capture a saved revision, batch-resolve verified native
artifacts (including authenticated inherited source revisions), verify copied
bytes, reconstruct only from those copies, and recheck receipts before publishing.
Bundles contain local vendored dependencies/notices, native result/config/log/
receipt files, hashes and provenance. Viewing needs no scientific runtime or
model weights. Motion reconstruction requires the exact recorded model file/hash;
directory fallback and model mismatch are rejected. Existing controls are retained,
with exact synchronized frame commits, bounded cache, and visible loading errors.
A browser-detected asynchronous preparation-canvas overlay was fixed at the stage
viewport boundary.

Validation: 26/26 combined pure suites, 3/3 robot-static suites; 4/4 new public
inspection/HTTP tests; 5 analytic replay/quantization cases; 3/3 actual pinned CPU
native-reference/model-rejection tests; original cache and new exact-frame/chunk/
race/cancel/error JS checks. Fresh G1 four-stage derivative:
`outputs/studio-inspection-ticket05-g1-05`; primitive three-stage derivative:
`outputs/studio-inspection-ticket05-primitive-01`. Their reports record source
full-tree preservation and fresh bundle identities. Combined filter-only revision
reuse/old motion export and browser evidence are at
`outputs/studio-inspection-ticket05-revisions-01`. All five stage HTTP inspection
routes returned 200; explicit UI build returned a fresh path. Standalone HTTP
viewing loaded only local dependencies; browser stepping/filtering/reference/
centering, exact end-stop and old-revision/inherited binding navigation passed.

Evidence and contracts: [experiment](../../../outputs/artifact-archives/experiment-reset-20261104/experiments/archive/studio-inspection-smoke-20261030/README.md)
and [Local Studio](../../../docs/local-studio.md#stage-inspection-and-standalone-exports).
The actual native cohort has three frames; the analytic 64-frame quantization and
JS chunk-boundary/race gates do not replace native full-clip chunk comparisons.
Fresh 500-epoch/all-5468-frame and quality acceptance remains mandatory ticket 07.
No contact/dynamics quality claim or runtime/vendor download was introduced.
