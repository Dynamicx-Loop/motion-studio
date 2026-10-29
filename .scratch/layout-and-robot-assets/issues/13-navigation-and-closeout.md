# 13 — Publish layout navigation and verify preserved workflows

Status: ready-for-agent
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 04, 05, 06, 08, 12
Dependencies: [04 conversion](04-wendy-conversion-adapter.md), [05 evidence](05-owned-evidence-tools.md), [06 docs](06-documentation-editions.md), [08 artifacts](08-artifact-migration-batches.md), [12 comparisons](12-canonical-comparison-preparation.md)

## Context

README layout currently omits the owned package, tests, schemas and local tracker.
The previous tickets introduce explicit storage, asset and workflow contracts.
Completion requires discoverable instructions and evidence that active entry
points and historical reading/reproduction paths still work together.

## Outcome and scope

Update README, workflow/external/offline documentation and experiment template
navigation to the implemented layout and contracts. Add an additive migration
summary linking exact preservation/relocation/check receipts and retained exceptions.
Run bounded cross-slice acceptance; do not rewrite historical experiment records.

## Acceptance criteria

- Navigation describes owned package/interfaces/adapters, thin scripts, tests,
  schemas, robot definitions, local tracker, experiments and ignored outputs/cache.
  All links match the final implemented paths, not merely the spec's proposals.
- Document dependency roles and source locators, test tiers/prerequisites, fresh
  output rules, compatibility aliases, restoration and intentional retained paths.
  Preserve original hhtools migration record and add only current corrections.
- Clearly distinguish official UMR reproduction using bundled G1 assets from
  deliberately selected canonical comparisons; document representation checks,
  pose conventions, identity/cache rules and retraining implications.
- Experiment template captures source/robot identity, patch/runtime/config/pose,
  geometry policy, conversions and cohort classification without imposing a
  universal motion format or retroactively filling unknown historical fields.
- Demonstrate active CLI help and bounded conversion/evidence/docs/selection/
  preparation paths plus historical data/viewer/static-pair compatibility checks
  where prerequisites exist. No saved evidence check is called a numerical rerun.
- Final preservation receipt accounts for every approved source/output change and
  retained bulk exception. Baseline hashes, unrelated local work and external
  state are unchanged except any explicitly recorded owned dependency metadata.
  All ticket outcomes have recorded checks; unavailable checks remain limitations.

## Validation

Run the root check command and each available opt-in tier with exact interpreter,
run path and edition recorded. Verify all planning/documentation links, anchors,
ticket numbers/dependency graph and `git diff --check`. Audit package dependency
direction and hand-written file growth. Compare sealed before/after manifests,
legacy aliases and frozen baseline asset closures. Check the offline navigation
and selected historical viewer; distinguish direct-file from HTTP browser checks.
Record any unavailable environment/assets/hardware without declaring full parity.

## Comments

Planning only. Close this implementation effort only after the concrete acceptance
evidence exists; publishing the spec and tickets does not resolve them.
