# 12 — Prepare explicit canonical UMR cohorts with provenance guards

Status: resolved
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 03, 10, 11
Dependencies: [03 dependency roles](03-dependency-roles.md), [10 G1 guard](10-g1-definition-baseline-guard.md), [11 Dex3 consistency](11-dex3-definition-consistency.md)

## Context

Shared definitions become useful when an active adapter consumes them. Historical
pair preparation and evaluation mix Astro/G1 assumptions and external imports.
The existing official G1 operation is deliberately narrower and remains intact.
Past geometry experiments also document incomplete cache fingerprint enforcement.

## Outcome and scope

Provide a separate Motion Studio operation and thin CLI to prepare a fresh UMR
canonical comparison cohort from explicit G1/Astro selection and pose, input
provenance and representation checks. Return typed prepared-input/config/receipt
paths. Adapt only this active preparation route; retain historical pair commands
and default worktree paths. Do not add a generic runtime framework or new solver.

## Acceptance criteria

- Caller explicitly selects canonical mode, robot edition/representation/pose,
  input and fresh destination. Official `reproduce_g1_baseline` retains its pinned
  bundled G1 path. A missing canonical choice cannot fall back to official or
  historical assets. Unsupported representation claims fail before preparation.
- Concrete adapter translates selection to UMR config and native joint order,
  enforces independent runtime prerequisites and writes only fresh run-local
  copies/derived geometry. Resolve all mesh/include references inside that closure.
  Public callers need no upstream objects/imports or internal stage orchestration.
- Receipt records cohort kind, source/asset/config/code/patch/environment hashes,
  conventions, pose, visual/collision policy, centering, conversions and stage
  fingerprints. State is prepared-only; training/retarget readiness is not implied.
- Cache compatibility covers target closure, pose, representation, topology/order,
  geometry selection, adapter version and correspondence dependencies including
  human shape/source sampling/settings/seed. Same paths/names are insufficient.
  Changed bytes/settings reject old learned datasets/slots/checkpoints or create
  a cache miss requiring a separate new cohort/retraining; never silently reuse.
- Existing reusable static preparation rules adopted by this route live in owned
  adapter modules. Frozen pair scripts remain supported historical tools, without
  mass editing their evaluator or adopting the experimental UMR patch.
- Preserve original assets and historical artifacts on success/failure. A failed
  preparation retains an honest failed receipt and cannot resume as a completed
  run. Existing destinations and unresolved source drift are rejected.

## Validation

Prepare small fresh fixture cohorts through the public operation; independently
inspect generated config/receipts and source hash equality. Verify path relocation
alone preserves content identity while one changed mesh, pose, joint order, source
shape or sampling policy prevents incompatible cache reuse. Run available real
read-only resolution and CPU compile/preparation smoke checks for explicit robot
selections. Re-run G1 guard/help tests with canonical definitions changed/missing.
No training, full retarget, cross-method quality or dynamics result is claimed.

## Comments

Planning only. This is deliberate adapter adoption for comparison preparation;
a second method and numerical comparison runs require separate concrete needs.

Claimed on 2026-10-29 in `codex/layout-assets-12`, from integration `a9ef925`.

## Answer

Implemented `motion_studio.integrations.umr_canonical.prepare_canonical_comparison`
with frozen typed inputs/settings/runtime/results, and thin
`scripts/prepare_umr_canonical.py`. See [the public contract](../../../docs/umr-canonical-preparation.md).
Explicit canonical robot/edition, MJCF, pose, source clip/shape/model dependencies,
FPS and fresh destination select closed run-local inputs with a separately
derived pose XML and native name/order configuration. Source model/include/mesh
and provenance bytes remain intact. Required representation claims use
`require_supported` individually and reject missing/stale/wrong-definition,
wrong-pose, source-hash or policy reports before run creation; collision policy
never substitutes for collision equality.

Receipts record canonical cohort kind, exact source/assets/config/code/empty
tracked patch/environment identities, pose/order/conventions, geometry/centering,
conversion and distinct dataset/slots/checkpoint fingerprints. Semantic identity
excludes supplied machine/output paths. The explicit public
`require_cache_compatible` checks current adapter identity, prepared bytes,
metadata stage/fingerprint/completeness and artifact SHA-256. Missing or changed
mesh/pose/order/shape/settings/seed/adapter evidence cannot silently reuse a
filename/checkpoint. Fingerprint equality is metadata compatibility only.

Destinations into actual canonical/worktree externals or source/input assets,
including physical symlink targets, existing outputs and preexisting source drift
are rejected. Later failures retain a failed receipt and require a fresh run.
A supplied official UMR runtime must be pinned, have unchanged tracked source and
pass its independent metadata prerequisite probe; missing runtime remains
explicitly unverified. Every success is `prepared-only` with
`execution_readiness=false`. The official G1 reproduction signature/pin/bundled
assets/full-run local copy and historical pair preparation remain unchanged.
No upstream patch, universal runtime framework or URDF conversion was adopted.

Validation on 2026-10-29:

- TDD at the approved public preparation/cache seams: 13 tests pass, including
  closure/includes, native order, path relocation, mesh/shape/order/pose/sampling
  mutation, stale/exact claims, metadata/hash/stage failures, destination and
  unrelated actual external symlink guards, malformed records and failed receipts.
- Merged latest prerequisite integration `3c1b4fa` (all tickets 01–11). Then ran
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py`: 17/17 pure suites pass,
  including official G1 baseline/help/definition-isolation regressions.
- Three fresh final real MJCF cohorts prepared and CPU compiled in existing UMR
  MuJoCo 3.3.7: G1/tpose and Astro29/tpose (nq36/nv35), Dex3/tpose_fist
  (nq50/nv49). Explicit root/scalar poses and native names matched within `1e-12`;
  no simulation stepping. Independent hashes verify original selected robot,
  clip/shape/model/backend, final adapter and all prepared bytes after compile;
  source Git statuses stayed unchanged. [Evidence](../../../experiments/layout-and-robot-assets-evidence/ticket12/README.md)
  records exact command/script hashes and durable final receipts under canonical
  `outputs/implementation/layout-and-robot-assets/ticket12-20261029-validated/`.
  The earlier pre-review set is retained separately without rewriting it.
- New documentation links and whitespace checked; source module is 330 lines,
  with model/runtime responsibilities behind two small private files.

Limits: no dependency install, CUDA job, dataset/training/learned-artifact
production, retarget run, cross-method quality or dynamics evaluation. Raw source
format/shape agreement and future numerical compatibility remain unverified;
static preparation without a supplied runtime cannot establish its prerequisites.
Unselected saved-evidence/JavaScript/static-runtime tiers were not rerun by this
slice; real fresh CPU preparation/compile is the bounded runtime observation.
