# 06 — Cancel, recover and revise persistent native runs

Status: ready-for-agent
Category: enhancement
Spec: ../spec.md
Blocked by: 04

## Context and outcome

Deliver cancel, recover and revise persistent native runs as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [ ] One active compute job enforced across requests; viewing other runs remains available; saved drafts never auto-queue.
- [ ] Browser close leaves jobs running; Stop terminates owned process group while preserving completed artifacts/logs.
- [ ] Service interruption recovery marks unfinished attempts interrupted; explicit retry restarts interrupted stage with verified compatible prerequisites.
- [ ] Input/settings edits fork immutable revisions, visibly mark affected stages stale and preserve old result; no cross-clip reuse.
- [ ] Test races, duplicate launches, cancellation escalation, restart recovery, failed/incomplete receipts, corrupted reuse candidates and stale callbacks through public outcomes.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.
