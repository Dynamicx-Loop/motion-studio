# 08 — Apply storage policy to the remaining inventoried artifacts

Status: ready-for-agent
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 07
Dependencies: [07 relocation pilot](07-artifact-migration-pilot.md)

## Context

The inspected experiment tree is about 1.55 GiB, spread across many historical
cohorts. A successful single pilot does not finish the layout cleanup. Viewer
geometry, checkpoints and generated models need the same preservation guarantees
as the pilot, including cohorts referred to by the offline research bundle.

## Outcome and scope

Apply the verified relocation operation to the remaining artifacts classified by
ticket 01. Execute one complete cohort/resource closure per batch, maintaining a
batch ledger. Process only the sealed inventory; newly discovered or changed
local work is reported for review rather than absorbed into a stale move plan.

## Acceptance criteria

- Ledger lists every inventoried experiment directory and each generated cohort
  as migrated, retained-with-reason or already correctly placed. No silent gaps.
  Source/config/patch/provenance/small-result files remain version-control eligible.
- Copy/verify/compatibility checks pass per batch before considering the next;
  historical hashes and records are unchanged, with additive relocation maps.
  Large JSON geometry is classified by purpose, not treated as small text evidence.
- Frozen baseline assets, raw outputs, experiment scripts and legacy absolute/
  relative references remain readable. Do not regenerate geometry or reinterpret
  past results with the latest robot definition.
- All moved bytes live in ignored run/archive storage; old links resolve to the
  same bytes. Keep originals where compatibility cannot be proved and document
  a concrete remaining constraint. Existing aliases/worktree metadata survive.
- Compare unique stored bytes separately from logical file sizes so symlinks or
  temporary duplicate copies do not produce misleading cleanup claims. Report
  remaining bulk and reasons. No broad ignore/deletion hides unresolved work.

## Validation

Run full relocation verification against the original inventory and sample hash
checks independent of the migrator. Traverse local paths in experiment README,
config, viewer and documentation resource graphs, including optional inspectors.
Exercise restore for one small archived member without modifying the only copy.
Recheck frozen run manifests and all repository status/worktree/link inventories.
No GPU or numerical rerun is required; report viewer checks not exercised.

## Comments

Planning only. This ticket completes the bounded inventory, not an open-ended
cleanup of all future outputs or unrelated user files.
