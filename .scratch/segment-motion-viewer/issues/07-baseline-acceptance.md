# 07 — Validate full offline G1 baseline and document operation

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: 05, 06

## Context and outcome

Deliver validate full offline g1 baseline and document operation as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [x] Fresh full 5468-frame G1/HiPHI run launched through application on validated CUDA environment with fresh output; all numerical gates checked against native reference.
- [x] Browser exercise includes imports/pose/stages/playback/bindings, cancel/retry, revision invalidation, reopening, history read-only, offline app and standalone bundle.
- [x] Record controlled runtime evidence and responsiveness measurements, commands/config/revisions/hashes in experiment template; no byte-identical stochastic expectation.
- [x] Run applicable checks and preserve original viewer/run/external hashes/status; document start/stop/setup/offline assets/recovery and supported limits.
- [x] Integration standards+spec review completed and actionable findings fixed before all tickets/spec marked resolved; no required runtime validation silently waived.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.

Ticket 07 uses the already confirmed public Studio and HTTP seams for official-pose success/rejection, retaining generic numeric poses. Full acceptance evidence remains pending final integration review.


## Answer

Runtime acceptance is complete; ready for root resolution after final evidence
review. The ticket remains claimed for the orchestrator's closeout step.

- Added typed unsaved official G1 pose loading through Studio, HTTP and UI, limited
  to the byte-verified pinned closure/configuration. Existing numeric/named poses
  remain usable. Public HTTP red→green regression covers all four official joints
  and rejects filename-only impersonation.
- Executed two fresh full 500-epoch/all-5468-frame cohorts through the application.
  The authoritative final-code run is `886f5c1ba3814b4eb268a84eeb8f1d1d/r0003`,
  job `9f6a6647060d4bc5afd7ecfec6f33124`; all numerical gates pass. Independent
  six-frame/chunk-boundary checks and all-frame native-reference tests pass.
- Actual browser imports/pose/launch, all stages, filtering/ownership, playback,
  exact seeks, loop/end-stop, centering/reference, history, reopening and standalone
  local HTTP viewing passed. Offline evidence is an observed resource audit;
  networking was not disabled.
- Final native revision invalidation, cancellation and explicit fresh retry passed,
  reusing only authenticated sampling and preserving the complete full revision.
  A discovered cross-namespace interruption in the initial cohort was retained,
  fixed and covered by regression plus fresh final native acceptance.
- Final validation: 27 pure suites, 3 robot-static suites, 3 JavaScript suites,
  3 full saved native-reference tests, pose HTTP regression, source/asset hashes,
  syntax, documentation paths and whitespace. Whole original viewer/run receipt
  passes all 288 files and pinned external HEAD/status. Native final cohort 73
  files and final bundle 182 files remain byte verified after lifecycle checks.
- Final standards/spec review cleared the integrated product/namespace fixes;
  root reviews this final evidence delta and owns the last checkbox/status change.

[Experiment, reproduction commands, measurements and limitations](../../../experiments/studio-baseline-acceptance-20261030/README.md).
Canonical evidence root:
`/data/workspace/motion_studio/outputs/studio-baseline-acceptance-20261030/`.
No bulky evidence or external source changes are committed. Neutral-hand/omitted-
face reconstruction remains disclosed; no contact, collision or dynamics claim.


### Root integration closure

Merged as `b8d363c`. Both [Standards](../reviews/standards.md) and [Spec](../reviews/spec.md) reviews are clear, including the namespace correction. Final documentation/test delta reviewed; focused official-pose HTTP regression and whitespace passed. Full stable-code native, browser, numerical and preservation evidence inspected in the acceptance experiment. All acceptance criteria are met; no required runtime workflow was waived.
