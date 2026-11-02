# Experiment: Wendy adapter numerical preservation

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-29 / Motion Studio ticket 04.

## Objective

Check that moving the active converter behind an owned operation preserves the
existing numerical behavior, fields and original source timing. This is an
adapter parity check, not solver tuning or a new historical baseline.

## Provenance

- Method: hiphi2smplx `65e51315ebbc82b2f0ff8e35a94565beb1b345e1`; no upstream edits.
- Owned base: `e215cc26c5c1f39acbf12100ed29c1b579270076`. The original driver is
  reconstructed byte-exactly with `git show e215cc2:scripts/convert_wendy.py`.
- Input: local Wendy happy-dance BVH from the existing preview config; original
  half-open interval `[3,6)`, fixed ten zero neutral SMPL-X betas. Source and model
  SHA-256 plus complete code/config/dependency hashes are in the private output
  provenance. Dataset/model terms remain separate; neither is redistributed.
- Independent runtime: existing `externals/UMR/.venv/bin/python`; no installation,
  fetch, GPU action or environment update. Python, platform and installed package
  versions are retained in each worker environment receipt and provenance.
- Units/conventions: source centimetres scaled by 0.01 to metres, Wendy Y-up
  declared without rotation; pose axis-angle radians in SMPL-X 55-joint order.
  Source frame time `0.00833333`, FPS `120.0000480000192`, no resampling. Fingers,
  eyes and face are unfitted; shape is fixed rather than estimated.
- A second source is the synthetic five-frame, 22-joint
  `tests/fixtures/wendy-known.bvh`, frame time 0.01 seconds. Its `[3,5)` excerpt
  has independently known root positions and original timestamps.

## Reproduction

Durable ignored run root on this machine:
`/data/workspace/motion_studio/outputs/implementation/layout-and-robot-assets/ticket04/`.
It is a real directory; no output writes went through source links. It retains
`reference-driver.py`, original reference config/log/results, `owned-config.json`,
`owned-final-config.json`, `known-config.json` and both initial/final receipts.
The first three-frame check predates final preflight hardening and remains
explicitly recorded as `parity-initial.json`; the accepted final check is
`parity.json`, copied byte-exactly from the durable `parity-final.json`.

The recorded commands used the following explicit paths (rerunning fitting
requires new output names in a copied config):

```sh
ROOT=/data/workspace/motion_studio/outputs/implementation/layout-and-robot-assets/ticket04
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 \
  PYTHONPATH=/data/workspace/motion_studio/externals/hiphi2smplx/src \
  /data/workspace/motion_studio/externals/UMR/.venv/bin/python \
  "$ROOT/reference-driver.py" --config "$ROOT/reference-config.json"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/convert_wendy.py \
  --config "$ROOT/owned-final-config.json" \
  --checkout /data/workspace/motion_studio/externals/hiphi2smplx \
  --python /data/workspace/motion_studio/externals/UMR/.venv/bin/python
PYTHONDONTWRITEBYTECODE=1 \
  /data/workspace/motion_studio/externals/UMR/.venv/bin/python \
  experiments/wendy-conversion-adapter/verify_parity.py "$ROOT" \
  --receipt /tmp/wendy-parity-fresh-receipt.json
```

The operation itself was invoked via its public request/result interface for
these runs, with the same arguments exposed by the CLI above. The saved-result
verification never starts fitting and refuses to replace its receipt.

## Evaluation

Measured final parity: all six legacy motion fields and six diagnostic fields
matched the original script; numerical maximum absolute difference was **0**
under `atol=1e-7`, `rtol=0`. All 16 original report fields matched exactly. Added
indices `[3,4,5]` and timestamps `[0.02499999,0.03333332,0.04166665]` matched the
original source offset within `1e-15` seconds. No visual judgments are claimed.

The known fixture produced two frames at exactly 100 FPS, indices `[3,4]`,
timestamps `[0.03,0.04]`, root metre positions `[[0.03,0,0],[0.04,0,0]]` and a
child's positions `[[0.03,0.1,0],[0.04,0.1,0]]`, within `1e-8` metres and zero
relative tolerance. Ten zero betas and `(2,165)` pose shape were checked. See
[known validation](known-validation.json) and [final parity](parity.json).

## Observations and next step

The solver choices and diagnostics were preserved in these small CPU excerpts.
The owned interface and CLI help run under `python3 -S`; pure boundary tests cover
invalid/nonfinite config/source, malformed hierarchy, out-of-range excerpts,
missing inputs, incompatible manifest pin and every output namespace conflict.
The root check runner discovers them automatically.

No full historical conversion, GPU workflow, contact/foot-slip/joint-limit audit,
visual evaluation or dynamic feasibility check was exercised. Existing Wendy
configs, source clips, historical outputs and unrelated runtimes were preserved.
