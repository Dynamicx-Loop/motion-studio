# 07 — Validate full offline G1 baseline and document operation

Status: claimed
Category: enhancement
Spec: ../spec.md
Blocked by: 05, 06

## Context and outcome

Deliver validate full offline g1 baseline and document operation as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [ ] Fresh full 5468-frame G1/HiPHI run launched through application on validated CUDA environment with fresh output; all numerical gates checked against native reference.
- [ ] Browser exercise includes imports/pose/stages/playback/bindings, cancel/retry, revision invalidation, reopening, history read-only, offline app and standalone bundle.
- [ ] Record controlled runtime evidence and responsiveness measurements, commands/config/revisions/hashes in experiment template; no byte-identical stochastic expectation.
- [ ] Run applicable checks and preserve original viewer/run/external hashes/status; document start/stop/setup/offline assets/recovery and supported limits.
- [ ] Integration standards+spec review completed and actionable findings fixed before all tickets/spec marked resolved; no required runtime validation silently waived.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.

Ticket 07 uses the already confirmed public Studio and HTTP seams for official-pose success/rejection, retaining generic numeric poses. Full acceptance evidence remains pending final integration review.
