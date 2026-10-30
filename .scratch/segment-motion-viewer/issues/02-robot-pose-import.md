# 02 — Import robot assets and edit named T-poses

Status: claimed
Category: enhancement
Spec: ../spec.md
Blocked by: 01

## Context and outcome

Deliver import robot assets and edit named t-poses as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [ ] Import G1/local MJCF closure via app into immutable managed assets; compile in pinned runtime, resolve units/defaults and enforce accepted hinge/root subset.
- [ ] Validate nested dependencies, missing/escaping/cyclic paths and unsupported joints; root conversion occurs only on derived copies with recorded provenance.
- [ ] UI provides torso selection, numeric/root/joint controls with visible mesh preview, limits, reset and named pose save/load.
- [ ] Pose changes create new revisions without mutating imported originals or completed runs; tests cover compiled fixture/defaults and failure cases.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.

Claimed by ticket 02 implementer on isolated branch `codex/studio-02`.
