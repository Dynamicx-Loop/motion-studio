# Experiment: wrist-calibration candidates on the canonical Astro snapshot

Date / author: 2026-10-23 / Codex.

## Objective and provenance

Recompute the previously declared candidate intervention on the fresh canonical
Astro learned slots, with matched SMPL-X/SOMA and spine1/bbox50 controls. All
current Astro paths reference the identical frozen XML and asset content hashes
in [the canonical manifest](../astro-canonical-static-v1/canonical-asset.json).
The source arrays, labels, raw checkpoint and samples are unchanged by calibration.
G1 receives the same rule, using its verified reused raw slots and frozen model.
This candidate is not adopted as a universal repair or default motion binding.

Algorithm source [calibration.py](calibration.py) is byte-identical to the prior
candidate. It uses source elbow/wrist joint anchors and nearest k source slots,
without a semantic hand mask, to estimate learned output anchors. A monotone
piecewise lateral map fixes the elbow and physical distal-tip boundary and moves
the learned wrist to the proximal extent of the actual hand mesh. It operates on
every slot in that interval; other coordinates stay fixed. Whole-model visual
projection remains unrestricted. Main k32, sensitivity k16/k64. It does not
retrain or move robot geometry and does not establish finger identities.

The hand-mesh start is an operational physical anchor, not independently validated
anatomical truth. Increased membership is partly intended by construction;
coverage, forearm spill, movement and global fit must be considered as well.
Training-reference coverage is not held-out surface-area coverage.

## Reproduction

From `/data/workspace/motion_studio` after the canonical static runs:

```sh
externals/UMR/.venv/bin/python experiments/astro-canonical-wrist-v1/prepare.py
externals/UMR/.venv/bin/python experiments/astro-canonical-wrist-v1/audit.py
externals/UMR/.venv/bin/python experiments/astro-canonical-wrist-v1/measure.py
python3 experiments/astro-canonical-wrist-v1/plot.py
externals/UMR/.venv/bin/python experiments/astro-canonical-wrist-v1/test_calibration.py
externals/UMR/.venv/bin/python experiments/astro-canonical-static-v1/verify.py
```

Preparation refuses overwrite; use new directories to repeat a fresh experiment.
Plots use system Python's existing Matplotlib (not installed in the UMR venv).
One initial plot attempt in the venv failed on missing Matplotlib; system Python
completed the figure without changing dependencies. Audit/render work interrupted
by the session pause was restarted from saved inputs. No checkpoint was replaced.

## Measured results

| Arm | Actual hand L/R raw→k32 | Coverage L/R k32 | Non-hand on hand L/R k32 | Max movement mm | Global sample distance mm raw→k32 |
|---|---|---|---|---:|---|
| smplx_astro_spine1 | 32 / 41 → 94 / 94 | 93.0% / 95.7% | 0 / 1 | 116.7 | 8.59 → 9.37 |
| smplx_astro_bbox50 | 24 / 24 → 95 / 95 | 90.4% / 94.8% | 1 / 1 | 154.2 | 8.59 → 9.30 |
| soma_astro_spine1 | 36 / 36 → 81 / 75 | 94.8% / 94.0% | 2 / 3 | 100.5 | 8.88 → 9.54 |
| soma_astro_bbox50 | 24 / 23 → 81 / 75 | 93.9% / 94.0% | 1 / 1 | 132.7 | 8.65 → 9.22 |
| smplx_g1_spine1 | 63 / 68 → 91 / 90 | 100.0% / 100.0% | 0 / 0 | 43.1 | 8.72 → 9.06 |
| smplx_g1_bbox50 | 70 / 64 → 93 / 88 | 98.9% / 100.0% | 0 / 1 | 45.4 | 8.89 → 9.23 |
| soma_g1_spine1 | 74 / 67 → 76 / 72 | 100.0% / 100.0% | 2 / 2 | 13.5 | 8.74 → 8.89 |
| soma_g1_bbox50 | 74 / 67 → 75 / 72 | 100.0% / 100.0% | 3 / 3 | 15.5 | 9.16 → 9.36 |

All primary and k16/k64 results are in [measurements.json](measurements.json).
Current hand counts reproduce the prior static candidate findings. Independent
full-triangle projection checks primary mesh counts; production projections remain
authoritative and are not silently replaced. Central/head/leg coordinates and
bindings remain unchanged across all24 derivatives. Increased finger mesh counts
do not prove thumb/index/middle correspondence. The new motion experiment tests
the k32 candidate separately from raw baselines, on the same snapshot.

## Validation and limits

Independent worked-example tests cover monotonicity, mirrored sides, fixed
boundaries, unchanged coordinates, nonmutation and invalid anchor order.
The shared canonical verifier checks raw input hashes, frozen model hashes,
full-triangle primary counts and archive preservation. Projection, anatomical
labels, kinematic ownership and LBS are distinct. Measurements remain static;
only the sibling motion experiment supports claims about actual trajectories.
No dynamic rollout, grasp validation, new primitive comparison or hardware run.
