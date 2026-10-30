# 04 — Run native UMR stages from the application

Status: ready-for-agent
Category: enhancement
Spec: ../spec.md
Blocked by: 02, 03

## Context and outcome

Deliver run native umr stages from the application as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [ ] Implement concrete pinned UMR adapter and CUDA readiness; expose Run all/run-through-stage with visible prerequisite computation from UI.
- [ ] Execute copied local inputs with official G1 defaults and curated sampling-seed/epochs/LQR-or-none controls, without applying G1 limits to other robots.
- [ ] Sampling and training publish validated inspectable artifacts; binding pre-solve artifact constructed from native functions; retarget saves exact full clip and provenance.
- [ ] Persist honest stage/epoch/frame/log progress and contextual failures; process isolation and fresh destinations preserve sources/externals.
- [ ] Implement deterministic dependency fingerprints/completion receipts, public success/failure tests and focused native smoke checks; no implicit upstream stale reuse.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.
