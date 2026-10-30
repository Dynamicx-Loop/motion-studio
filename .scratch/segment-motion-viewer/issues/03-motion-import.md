# 03 — Import and inspect explicit SMPL-X motion metadata

Status: ready-for-agent
Category: enhancement
Spec: ../spec.md
Blocked by: 01

## Context and outcome

Deliver import and inspect explicit smpl-x motion metadata as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [ ] Import existing HiPHI and compatible safe single-person NPZ via app into immutable managed storage.
- [ ] Validate pose/translation/shape/FPS/gender/up-axis and aliases, matching local model hashes; missing metadata explicit, unsupported layouts/timing rejected.
- [ ] UI displays frame count/FPS/shape/model provenance and neutral-hand/omitted-face disclosure, selecting an imported motion for a draft.
- [ ] Preserve all source bytes/channels; moving originals does not break imported version. Tests cover baseline headers, malformed arrays/aliases and missing model.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.
