# 04 — Run native UMR stages from the application

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: 02, 03

## Context and outcome

Deliver run native umr stages from the application as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [x] Implement concrete pinned UMR adapter and CUDA readiness; expose Run all/run-through-stage with visible prerequisite computation from UI.
- [x] Execute copied local inputs with official G1 defaults and curated sampling-seed/epochs/LQR-or-none controls, without applying G1 limits to other robots.
- [x] Sampling and training publish validated inspectable artifacts; binding pre-solve artifact constructed from native functions; retarget saves exact full clip and provenance.
- [x] Persist honest stage/epoch/frame/log progress and contextual failures; process isolation and fresh destinations preserve sources/externals.
- [x] Implement deterministic dependency fingerprints/completion receipts, public success/failure tests and focused native smoke checks; no implicit upstream stale reuse.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.


## Answer

Implemented explicit independent native stages, persistent server-owned jobs,
CUDA/pin/model readiness, immutable settings revisions, one-job exclusivity,
process-group cancellation, honest logs/epoch/frame progress and fresh stable
attempts. Native sampling/training/retarget calls use force=True without implicit
pipeline stages. Binding is constructed before solve from native functions.
The UI reviews prerequisites and links outputs/config/validation/receipts/logs.

Completion publication rechecks exact dependency receipt/artifact hashes inside
the transaction; public reads recursively authenticate prerequisite chains.
Both reviewer findings have public red→green regression coverage: exact model-file
routing prevents overlays/alternate siblings, and changed sampling during/after
training prevents publication/invalidates the dependent receipt. Primitive source
binding retains native closest diagnostics separately from exact face+bary replay.

[Experiment and exact smoke evidence](../../../experiments/studio-native-stages-smoke-20261030/README.md)
records final fresh G1 `outputs/studio-native-smoke-04-06` (all four stages,
2 epochs/3-frame fixture) and primitive
`outputs/studio-native-smoke-04-primitive-03` (through binding, no motion).
G1 wrapper saved-pose world errors zero; quaternion max error 5.96e-8,
joint-limit excess zero. Native saved-artifact regression 2/2; pure tier 24/24;
Studio suite 39 tests (37 passed, 2 opt-in saved tests separately passed);
existing UMR integration/canonical/inspection 5/13/5 passed; JS syntax and diff
whitespace pass. Actual browser review restored controls and displayed verified
reuse with no new launch. No upstream/original-viewer/historical writers changed.

This is the focused execution slice. Ticket 05 supplies rich stage/animated
inspection and standalone exports; 06 deepens lifecycle/recovery UX; mandatory
500-epoch/all-5468-frame acceptance remains ticket 07. No full/default or dynamics
quality claim is made from small smoke cohorts. Contracts and reproducible smoke
commands are documented in [Local Studio](../../../docs/local-studio.md).
