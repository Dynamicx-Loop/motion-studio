# 12 — Prepare explicit canonical UMR cohorts with provenance guards

Status: ready-for-agent
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
