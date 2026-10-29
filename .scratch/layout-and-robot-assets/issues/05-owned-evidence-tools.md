# 05 — Reconstruct sealed legacy evidence through owned modules

Status: resolved
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


## Answer

Active reconstruction, schema contracts, sealing, recorded metrics and plan
inspection/reservation now live behind the small `motion_studio.evidence` public
interface. The two pure report rules are owned there; reconstruction and the
static evaluator no longer load an experiment report builder for validation.
Historical report generation and `experiment_support.*` imports remain supported
through small compatibility imports. Recorded motion-path behavior moved unchanged
to `motion_studio.motion_data_paths`, with the old script module alias retained;
this owned path is available for ticket 04 without changing data conventions.

New reconstruction/preparation bundles record the ownership migration and exact
executing code/schema hashes in a sealed `implementation.json`. Historical
manifests are untouched. Input root and exclusive destination are explicit;
retrospective/not-rerun, legacy IDs/cohorts, metrics, caveats and prepared-only /
false execution-readiness contracts remain intact. No package imports scripts.

Acceptance evidence is in the [experiment record](../../../experiments/layout-and-robot-assets-evidence/README.md)
and [committed comparison receipt](../../../experiments/layout-and-robot-assets-evidence/validation.json).
The [operation guide](../../../docs/evidence.md) documents contracts and compatibility.

Validation after merging integration checkpoint
`bbd6dac8f80ca63e6a7267fa0db4a4b54ba589c0`:

- Ten small public fixture tests passed. They cover reconstruction without a
  report builder, original denominators, non-executing reservation, invalid
  contracts/JSON, source drift, manifest/output verification, overwrite refusal
  and rejection of retrospective tested-rerun claims. New seam slices were run
  red before extraction/export, then green. Existing preservation rules stayed
  covered without inventing numerical expectations.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py --tier pure --tier saved-evidence`
  passed all eight selected suites. The saved test retains `CHECK_TIER` and its
  historical command; its four tests also passed with `PYTHONPATH=scripts`.
  Historical module imports resolve with only that scripts path on `PYTHONPATH`.
- Fresh canonical old/new reconstruction produced byte-identical `results.jsonl`,
  `inventory.json`, `summary.json` and `README.md`: 52 static arms, 24 motion arms,
  1,924 segment rows and zero new baseline arms. Both bundles verified; only the
  declared implementation provenance/manifest changed in the new bundle.
- All 459 original reconstruction sources independently match ticket 01's sealed
  inventory and current hashes. All nine canonical repository HEAD/status values
  are unchanged; external worktree listings are unchanged. Initial full receipt
  verification passed. Final verification correctly reports ten additive ignored
  ticket 03 dependency-receipt payloads, with no original source/alias/patch drift;
  authorized root task worktrees/integration advancement explain its Git worktree
  listing change. The original receipt was not rewritten.
- New diff whitespace and documentation relative links were checked. Owned source
  files remain under 400 lines, with cohesive private modules behind public outcomes.

Limits: no numerical recomputation, report rebuild, UMR static runtime evaluation,
installation, GPU job or upstream import was performed. The saved record comparison
is structural parity, not dynamics/contact validity or a fresh solver result.
Transient comparison bundles are deliberately not linked as durable evidence;
small committed validation records retain their hashes and findings.
