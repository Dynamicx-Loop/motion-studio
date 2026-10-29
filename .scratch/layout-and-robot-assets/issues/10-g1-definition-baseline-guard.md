# 10 — Define comparison G1 while preserving official UMR reproduction

Status: resolved
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

Claimed on `codex/layout-assets-10` from `54ac3e3`; approved seams are public
`reproduce_g1_baseline`, CLI help, and `resolve_robot`.

## Answer

Implemented [explicit G1 comparison definition](../../../robots/g1_29dof/README.md),
complete zero/T-pose records, and
[bounded consistency observations](../../../robots/g1_29dof/consistency-observations.json).
Exact pinned source closure is 38 files per representation, with two separate
provenance files. No upstream models/assets were added to Git or modified.
Joint metadata and poses resolve against committed UMR bytes for both formats.
The URDF/MJCF pair is incompatible at unchanged spec tolerances (wrist limit and
orientation differences, missing fixed frames and different mass totals); visual
and collision equivalence remains unverified. Ticket 11 owns common runtime
validation/certification; this record does not claim it has run.

The original public baseline signature/defaults, pin, worker, configuration and
full-bundle preparation are unchanged. A fresh-output safety gap is closed when
`externals/UMR` or the destination resolves through symlinks into the actual
external source. Tests operate through the public baseline in an isolated package
with its actual default catalog removed or redirected. Tiny fixture boundaries
replace scientific runtime, Git's pinned identity and licensed human-model I/O;
real owned preparation copies every asset, preserves calibration/full clip, and
keeps generated XML local. Existing output and frozen-record fixture bytes remain
unchanged. Changed required assets, unreviewed pins and existing runs fail before
output mutation. Public help remains runtime/catalog independent.

Validation:

- TDD red/green: linked-external destination test failed on original guard, passed
  after tightening; explicit G1 selection failed before definition, passed after.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py`: all 10 pure suites passed.
- Four real-source read-only selections (`urdf`/`mjcf`, `zero`/`tpose`) passed,
  each with 29 ordered scalar joints and 40 required source/provenance files.
- Existing UMR MuJoCo 3.3.7 compiled only a fresh full run-local G1 copy:
  nq=36, nv=35, nbody=51, mass=35.525142 kg. Whole source bundle hashes matched
  before/after. Stable ignored receipt and exact compile script:
  `/data/workspace/motion_studio/outputs/implementation/layout-and-robot-assets/ticket10/`.
- `git diff --check` passed; source paths and new local documentation links checked.

No GPU job, training, motion retargeting, simulation stepping, upstream writes,
asset regeneration or historical baseline advancement was performed. Prior
MuJoCo 3.11 controlled-import measurements are labeled prior observations;
the new 3.3.7 compile is not a parity claim or a newly passed numerical baseline.
