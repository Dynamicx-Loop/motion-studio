# 05 — Reconstruct sealed legacy evidence through owned modules

Status: claimed
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 01, 02
Dependencies: [01 preservation](01-preservation-inventory.md), [02 checks](02-test-discovery.md)

## Context

Reusable contracts, file sealing, metrics, preflight and reconstruction live in
scripts/experiment_support. Reconstruction also imports pure report helpers from
an experiment script dynamically. Existing tests establish retrospective labels,
76 legacy arms and refusal to overwrite; those are preservation contracts.

## Outcome and scope

Provide owned evidence reconstruction and plan inspection/reservation operations,
with existing scripts/import paths retained as compatibility shims where used.
Move the active implementation and demonstrated pure report rules into cohesive
package modules. Keep experiment-specific reproduction tools and original records.

## Acceptance criteria

- Reconstruct into a fresh destination through an explicit input/root contract;
  returned summary and sealed evidence retain source hashes and provenance.
  Callers do not import scripts or execute report builders to access validators.
- Preserve existing record IDs, labels, metrics and limitations. Reconstruction
  remains retrospective/not-rerun; no old arm becomes a new baseline.
- Preflight/reservation still reports prepared-only with no stages executed and
  execution readiness false where no launcher exists. Layout cleanup does not
  make an unfinished execution feature appear complete.
- Old active imports/commands resolve through small compatibility wrappers;
  source-hash recording includes the new implementation and accurately records
  the migration without rewriting old manifests. No new package-to-script cycle.
- Root checks cover source drift, invalid contracts, sealed manifest verification,
  overwrite refusal and retrospective-claim rejection with small fixtures.

## Validation

Compare fresh before/after reconstruction summaries and semantically stable
records against the frozen sources; only declared implementation provenance may
change. Existing saved-evidence expectations are 52 static arms, 24 motion arms,
1,924 segment rows and zero new baseline arms, subject to verified source closure.
Verify all input hashes/status remain unchanged using ticket 01's receipt.
Record unavailable saved evidence separately from passing fixture checks.

## Comments

Planning only. Moving code does not authorize a numerical rerun, new metrics,
changing experiment classifications or rewriting historical scripts wholesale.

Claimed on 2026-10-29 in `codex/layout-assets-05` at integration checkpoint
`de0d6f54bffdb8fc915fa4e2df2e09a6a1892f2c`; scope limited to owned evidence tools.
