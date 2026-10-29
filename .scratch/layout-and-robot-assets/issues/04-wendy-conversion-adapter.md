# 04 — Run active Wendy conversion through an owned operation

Status: resolved
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 02, 03
Dependencies: [02 checks](02-test-discovery.md), [03 dependency roles](03-dependency-roles.md)

## Context

The Wendy converter imports hiphi2smplx directly and executes parsing/fitting at
module scope. It handles excerpt selection, fixed actor shape, skeleton overrides,
source timing and diagnostic output. Those are active integration responsibilities.

## Outcome and scope

Expose one typed Motion Studio conversion operation for the current Wendy
configuration and make its existing CLI thin. Keep upstream imports, mapping
registration and invocation inside the concrete adapter and its private runtime
worker if needed. Migrate this active command first; inventory other direct
conversion imports as explicitly retained historical tools or later active work.

## Acceptance criteria

- Operation inputs/results specify source clip/model/config, frame interval,
  unit scale, axes, frame time/FPS, shape, mapping, output ownership and failures.
  Existing config defaults and output/diagnostic/report fields remain supported.
- Retain current numerical choices and information-loss labels: fixed neutral
  shape, source timing, declared axes and unfitted fingers/face. Preserve original
  BVH and arrays; excerpt metadata records original frame offset and checksum.
- Importing the public operation and CLI help requires only system Python.
  hiphi2smplx objects, global skeleton mutation and venv setup do not leak to
  callers; worker isolation or scoped restoration prevents cross-call leakage.
- Reject invalid/nonfinite configuration, out-of-range excerpts and conflicting
  output or diagnostic paths before overwriting data. Record code/dependency,
  source/config/model hashes, environment, conversions and derived output hashes.
- CLI smoke and owned interface tests join the root check inventory. Historical
  scripts/configs/results remain available; no upstream edits or solver tuning.

## Validation

Use a small known BVH fixture for excerpt boundaries and true timestamps, plus
missing-input, incompatible pin and output-conflict cases through the public
operation. Where the pinned runtime/model are present, convert a small fresh
excerpt and compare timing, fields, shape and numerical values with a preserved
reference under explicit tolerances. Record unavailable numerical validation;
do not overwrite or rerun the full historical Wendy conversion as a unit test.

## Comments

Claimed on `codex/layout-assets-04` from `e215cc2`; public conversion seam approved in parent orchestration. The scope is current conversion behavior, not a general import
format or mass refactor of experimental scripts.


## Answer

Implemented `motion_studio.integrations.wendy.convert_wendy` with typed request
and result, system-Python preflight, process-isolated pinned hiphi worker and thin
existing CLI. Preserved solver defaults, fixed shape, source frame spacing,
original motion/diagnostic fields and all 16 report fields. Added original
indices/timestamps, explicit information loss, whole-input/code/config/model/
environment hashes and output ownership. All sibling outputs and invalid source/
config/range/mapping are checked before writes; publication never overwrites.
Historical direct import callers are inventoried in
[owned conversion documentation](../../../docs/wendy-conversion-adapter.md).

Validation: root `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py` passed
12/12 selected pure suites, including ten public conversion/CLI tests. Fresh CPU
Wendy excerpt `[3,6)` matched all 12 legacy NPZ/diagnostic fields (maximum absolute
difference 0, atol 1e-7, rtol 0), and all 16 report fields exactly. Synthetic
five-frame source `[3,5)` verified 100 FPS, original timestamps and known metre
positions independently. [Experiment and preserved receipts](../../../experiments/wendy-conversion-adapter/README.md)
record commands, hashes and limits. No upstream edits/install, full historical
conversion, GPU job or dynamic-feasibility claim. Existing outputs were retained.
