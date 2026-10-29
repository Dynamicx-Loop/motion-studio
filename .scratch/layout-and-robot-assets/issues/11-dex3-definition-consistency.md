# 11 — Resolve Dex3 poses and validate intentional model differences

Status: ready-for-agent
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 09
Dependencies: [09 selection resolver](09-astro-selection-resolver.md)

## Context

The Astro Dex3 source has 43 scalar joints: 29 body and 14 hand coordinates.
Its application order differs from native tree order; the fist file is a partial
hand pose. MJCF documentation records intentional collision refinements and a
fist keyframe absent from the earlier URDF conversion. Rebuilding would erase
those changes. Vendor hand licensing does not establish full-bundle permissions.

## Outcome and scope

Add the proposed robots/astro_p2_43dof_dex3_1 metadata and poses through the
resolver, plus a reusable representation-consistency report used for all three
definitions. Preserve menagerie_x as source and its intentionally distinct models.

## Acceptance criteria

- Pin source/mesh/model/pose closure and notices at inspected menagerie revision.
  Read joint-order and fist source records; do not infer 43-coordinate order by
  concatenating runtime qpos offsets or treating free-root values as hinges.
- Define complete zero/open and body-T-pose selections plus an explicit fist
  overlay/base merge rule. Match source fist signs/values and hash. Unknown,
  duplicate, missing, out-of-range or nonfinite joints fail; no implicit fist
  selection from viewer defaults or claim of hardware calibration.
- Runtime report compares joint sets/order mappings, types/axes/limits, named
  frame transforms and inertial totals at declared zero/T/fist poses. Record
  units, runtime, tolerances and source hashes. Use name-based independent
  expectations/source records rather than comparing a function with itself.
- Enumerate known MJCF-only shin/palm/torso/arm/pelvis/contact differences and
  keyframe behavior; visual and collision findings remain separate. Only explicitly
  allowed differences pass; unexplained changes fail. Never regenerate either
  source to make the report pass or claim byte-identical collision models.
- The report format also covers Astro 29 and G1, returning supported/unverified/
  incompatible findings. Cross-method claims requiring an unsupported consistency
  check are blocked. Schema success alone is not kinematic/dynamic validation.

## Validation

Use fixture models with analytically known transforms and deliberate joint/limit/
geometry mismatches to test the report through its public operation. Run available
read-only checks on real source pairs in an existing environment, including fist
overlay expansion to 43 scalar coordinates and native-order mapping. Verify source
hashes/status against the sealed inventory; record unavailable runtimes and the
limits of sampled-pose checks. No dynamics, hand fitting or GPU training required.

## Comments

Planning only. The initial numeric equality tolerances are in the parent spec;
justify exceptions from inspected physical quantities, not a widened tolerance.
