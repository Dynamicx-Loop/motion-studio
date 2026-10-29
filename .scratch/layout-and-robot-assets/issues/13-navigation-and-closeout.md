# 13 — Publish layout navigation and verify preserved workflows

Status: resolved
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

Claimed on 2026-10-29 by ticket 13 implementer from integration
`7abd884575148bd5e91faa01e4a24bc914523058` on `codex/layout-assets-13`.
All listed parents are resolved. Parent closeout remains claimed pending the
coordinating session's final standards/spec review.

## Answer

Published actual navigation for owned operations/adapters, thin and frozen scripts,
tests/schemas/robot definitions, local tracker, experiments, ignored outputs/cache,
independent dependency roles and restoration. The expanded template records cohort,
identity, pose/orders, representation/geometry claims, provenance and stage/cache
limits. Original hhtools migration and historical experiments remain unchanged.
The parent spec is claimed with current scope; final standards/spec review belongs
to the coordinating session and is not preempted by this ticket's resolution.

Two small handoff fixes preserve existing hash checks: `verify_edition` compares
root/home links by resolved destinations, accepting aliases and physical editions;
`verify_docs.py` defaults its source root to the executing checkout. Public tests
first reproduced both failures, then passed alias/target and source-workspace
relocation cases. Publication root bytes remain hashed; public API recorded-root
semantics remain explicit.

[Additive evidence](../../../experiments/layout-and-robot-assets-evidence/ticket13/README.md)
and the [tracked final receipt](../../../experiments/layout-and-robot-assets-evidence/ticket13/closeout.json)
record all checks, durable paths, SHA-256 anchors and limits. Available tiers all
passed: pure 17/17, saved-evidence, JavaScript, UMR static with explicit
`/data/workspace/motion_studio/externals/UMR/.venv/bin/python` and preserved
`outputs/umr-astro-baseline-v1/static-20261024-01`, and robot-static with explicit
`/data/workspace/notAnyrobot/menagerie_x/.venv/bin/python`. CLI help, pin inspection,
saved Wendy 12-array/16-report-field parity, fresh legacy reconstruction (76 arms,
1,924 rows), three real robot selections and fresh Astro 29 preparation/CPU compile
passed. Its 112 prepared hashes and XYZ/wxyz/scalar pose matched at `1e-12`;
MuJoCo 3.3.7 reported nq/nv 36/35, zero simulation steps, prepared-only state and
execution readiness false. No numerical rerun or cache-runtime claim follows.

The fresh `ticket13-20261029-final` edition contains 62 documents, 3,796 verified
source hashes, 3,647 output hashes and 1,424 local links, with zero missing anchors.
Its full 3,648-file / 2,600,568,309-byte closure is independently sealed and copied
once to canonical `outputs/docs-site/ticket13-20261029-final`, with a read-only
per-edition alias in this worktree. HTTP root→Installation→Quick Start→UMR→Supporting,
search, basic and compatibility home entries worked. Current `file://` navigation
was explicitly rejected by the browser protocol policy; no workaround was attempted.
Optional-inspector browser interaction/direct-file WebGL remain unverified.

The final original-inventory check reports exactly **493 declared alias kind changes
and 8,865 additive output paths**, all individually accounted for: zero changed
sealed bytes, zero canonical/external HEAD/status/patch drift, retained original
worktree paths/branches/compatibility links and unchanged frozen ticket06 closure
(3,612 files). No whole-inventory pass or workspace-size reduction is claimed.
The sealed inventory is not rewritten. All 1,019 experiment members/24 directories
and 21 old output cohorts are covered; 526 small source/evidence members remain
with reasons. Source-change snapshot accounts for 154 owned paths, plus this
additive final receipt and final tracker/review metadata. `git diff --check`,
186 Markdown path/anchor checks, ticket numbering/dependencies, package-to-script
import audit and changed-file growth review passed. Changed source/test files are
287/27/177 lines; no abstraction or upstream source edit was added.

### Exact guarded handoff after integration

The publisher is tested for successful handoff, conflicting alias refusal, frozen
byte drift refusal and post-publication rollback. It rechecks the complete seal,
current source hashes, and same-relative regenerated root/basic/home hashes before
publishing. Run only after this ticket is merged into the unchanged source tree:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 /data/workspace/motion_studio/outputs/docs-site/ticket13-20261029-handoff/guarded-handoff.py \
  --root /home/android/.codex/worktrees/layout-robot-assets/motion_studio \
  --frozen /data/workspace/motion_studio/outputs/docs-site/ticket13-20261029-final \
  --seal /data/workspace/motion_studio/outputs/docs-site/ticket13-20261029-handoff/frozen-closure.json \
  --receipt /home/android/.codex/worktrees/layout-robot-assets/motion_studio/outputs/docs-site/ticket13-publication
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_docs.py --edition ticket13-20261029-final
```

Publisher SHA-256: `847c3fb2c9e6883da957d1036c85efae5c4a91303267617e617b7adaeccc0ae3`.
Seal SHA-256: `62bed22c20e99053d380f65b1ee08b6f90408581a9e7ad42be2ebc885230b490`.
Manifest SHA-256: `f5f9fe87a519a8f4b9c3a15ece4cd9b53af00b3f63af8a1b643694e4590f3e09`.
Only the edition child becomes an alias; the output parent stays real. The fresh
publication receipt archives all previous entries under `originals/<path>` and
records their hashes. On any publication/verification failure the script restores
those bytes and removes only a newly installed alias. For deliberate rollback,
copy those verified originals back to their exact recorded root/basic/home paths;
keep both frozen editions and their receipts. Reusing an existing edition was
independently refused with all current entry hashes unchanged.

### Final review correction — 2026-10-29

Three final-review corrections and comparison-version invalidation are recorded in ../review.md. Fresh review-20261029-final edition supersedes the prior reading edition for current source verification; original frozen 06/13 closures remain intact. Parent remains claimed pending coordinating acceptance.

See [review and validation](../review.md). Original Answer/history above remains intact.
