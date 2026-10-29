# 10 — Define comparison G1 while preserving official UMR reproduction

Status: ready-for-agent
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 09
Dependencies: [09 selection resolver](09-astro-selection-resolver.md)

## Context

The owned G1 baseline operation already enforces the original UMR pin and copies
its shipped assets/g1 bundle into each new run because upstream writes generated
XML beside its input. Shared selection must not replace this preservation path.
The bundle contains multiple URDF/MJCF editions and local generated wrappers.

## Outcome and scope

Add an explicit G1 29 DoF comparison definition and named poses using the common
resolver, and regression coverage proving canonical metadata cannot change the
official reproduction. Initial comparison source is the pinned UMR shipped G1
edition; menagerie G1 editions are not interchangeable substitutions.

## Acceptance criteria

- Proposed robots/g1_29dof definition selects exact committed input files,
  referenced mesh/include closure, joint order and pose conventions. Inventory
  candidate URDF/MJCF differences; do not include arbitrary local wrapper files.
- Comparison identity/selection is explicit even where source bytes equal official
  G1. Geometry, frame, limit or representation changes create a distinct identity.
- `reproduce_g1_baseline` keeps its signature/defaults/pin and original source
  selection; no canonical override or resolver fallback is added. Public help
  remains independent of robot catalog and scientific runtime availability.
- Behavioral tests establish that changing/removing canonical definitions does
  not redirect official G1 preparation. Run-local asset copy and generated-XML
  isolation preserve upstream bytes, existing baselines and frozen record hashes.
- Consistency report compares named joints/types/axes/limits/frames at zero and
  a declared pose, and inventories visual/collision differences separately.
  Unknown or divergent pairs are not silently certified for cross-method use.

## Validation

Run public G1 safety tests and add fixture-based preparation checks that inspect
resolved XML source and copied asset bytes without training. Verify unreviewed
pin, existing-output and changed-required-asset failures before mutation. With
the existing runtime, compile fresh run-local inputs only and hash the source
bundle before/after. Existing saved numerical reproduction is evidence, not a
newly passed GPU test. Record unexercised compilation/consistency checks.

## Comments

Planning only. Original UMR source assets, October 24 pair and October 29 G1
results remain frozen; this ticket does not advance either baseline.
