# Standard UMR experiment

Compare the built-in Unitree G1 and Astro P2 in Motion Studio using the same
pinned HiPHI Get Up SMPL-X clip and actor shape. Both arms use their Studio
reference poses, official UMR, 4,096 samples, seed 0 and 500 training epochs.

## Run

Use the pinned UMR checkout, its existing environment, the local licensed
SMPL-X weights and a CUDA-capable runtime. From the Motion Studio root:

```sh
python3 -B experiments/umr-standard/run.py --output outputs/<fresh-run-id>
```

The driver creates a fresh Studio state, samples and trains each robot separately,
then runs Studio's native pre-solve binding stage. Both arms must publish
validated stage receipts. Inputs, plans, runtime identity and receipts are saved
alongside the state. To inspect it, launch Studio with
`python3 -B scripts/studio.py --state outputs/<fresh-run-id>/state`.

Compare the same human segment in both reference-pose views and inspect the
target mesh and body for representative slots. Record projection distances
separately from visual placement. A robot's reference pose and centering are
part of its configuration. This static stage does not execute motion retargeting.

## First run · 2026-11-04

Both robots completed sampling, training and binding with pinned UMR
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`. The SMPL-X vertices, triangles,
shape coefficients and sampled source points matched exactly across both arms.
Studio validated the source barycentric replay and robot rigid attachment replay.

| Robot | Validated slots | Robot projection distance p95 |
| --- | ---: | ---: |
| G1 | 4,096 | 19.51 mm |
| Astro P2 | 4,096 | 17.97 mm |

Projection distance measures how far a learned slot moved to reach the target
mesh. Anatomical placement and motion quality need separate review.

The local output is `outputs/umr-standard-20261104/`. Read
`comparison.json` for the run IDs and numerical checks. Open the saved Studio
state with:

```sh
python3 -B scripts/studio.py --state outputs/umr-standard-20261104/state
```
