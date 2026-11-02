# Experiment: built-in Astro P2, full HiPHI, 500 epochs

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-11-01 / Codex delegated execution, requested by the user.

## Objective and cohort

Run the **entire HiPHI get-up clip** through built-in Astro P2 with **500 fresh
training epochs**, then open synchronized playback for review. This is a fresh
Astro full-clip cohort, separate from the short five-epoch smoke and historical
G1 acceptance. Successful numerical execution does not certify motion quality,
contact behavior or dynamic feasibility.

Run `39e72257a97e4a508c21473399106ab7`, revision `r0003`, job
`b5e525f05c3e48e29cfc762ffa5413fc`. Fresh output:
`outputs/studio-astro-full-hiphi-20261101/full-01/`.

## Provenance and independent runtimes

Motion Studio base revision `2ec8bc9`; the exact full revision and driver SHA-256
are recorded in `source.json` under the output directory. [run.py](run.py) uses
the public Studio API for built-in import, immutable selections, planning,
execution and inspection. No product changes were needed.

UMR remains unmodified at `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
Astro uses the [bundled snapshot](../../assets/robots/astro_p2/manifest.json)
from `menagerie_x` revision `8e3f382f28831331c448c9d62cd197140da63c65`.
Full source/derived hashes, native/adapter hashes, commands, environment overrides
and packages are preserved in the source/readiness files and completion receipts.

Native interpreter: `externals/UMR/.venv/bin/python`, existing CUDA environment,
NVIDIA GeForce RTX 5070 Laptop GPU; service Python 3.12.3. The sandbox cannot see
CUDA, so the explicitly requested run used the host executor. No runtime package
or external source was changed. Licensed SMPL-X weights remain in their original
local location, checked by hash and excluded from the exported bundle. Astro,
dataset and model-weight terms retain their separate coverage.

## Robot selection and representation

Built-in `astro`, managed identity
`e5689bca41566d83201ce919013da2a6f72d0d5084f968be269de7fba18c3fdf`:
29 bounded hinges, one pelvis floating root, `nq=36`, named T-pose and torso
`waist_roll_link`. Metres/radians, native Z-up, root quaternion wxyz and compiled
joint ordering are explicit in inputs/receipts. The generic robot path applies
neither the G1-only root wrapper nor G1 joint-limit overrides. Sampling/binding
use 37 visual meshes; saved model collision geometry remains intact.

## Processing and learned artifacts

Sample ID **`hiphi-get-up`**, not `hiphi-quick`. Source:
`externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
All **5,468 frames**, IDs **0–5467**, at **90.00090026855469 FPS** (about 60.75 s)
were retained. No trimming, resampling or interpolation. Managed normalization
preserves source bytes; native reconstruction uses neutral hands and omits facial
channels, as disclosed by the motion import contract.

Sampling seed 0, training seed 0, 4,096 paired slots, native19 segmentation,
**500 epochs**, **LQR** trajectory filter. All four stages ran fresh; no smoke
checkpoint or learned correspondence was reused. Native motion has shape
**(5468,36)**. Changed geometry/inputs form a new cohort, not evidence of cache
compatibility with earlier experiments.

## Reproduction

From `/data/workspace/motion_studio`, using the host with GPU access and a fresh
output destination (existing destinations are refused):

```sh
python3 -B experiments/studio-astro-full-hiphi-20261101/run.py \
  --output outputs/studio-astro-full-hiphi-20261101/<fresh-id>
```

The driver defaults to 500 epochs and guards the expected complete frame count.
Plans, captured inputs, every command/log/receipt, output hashes and the standalone
inspection remain local under the fresh output. [result.json](result.json)
records the exact identities and artifact paths.

Independent checks for this saved export:

```sh
STUDIO_INSPECTION_SMOKE=/data/workspace/motion_studio/outputs/studio-astro-full-hiphi-20261101/full-01 \
  externals/UMR/.venv/bin/python -B -m unittest discover \
  -s tests -p test_studio_inspection_runtime.py -v
```

To reopen the saved state:

```sh
python3 -B scripts/studio.py \
  --state outputs/studio-astro-full-hiphi-20261101/full-01/state --port 8775
```

Then open the inspection path recorded in `result.json`. Bundle viewing requires
neither UMR nor licensed model weights. Recreating the result needs the recorded
runtime and assets.

## Evaluation

- Sampling, 500-epoch training, binding and full retargeting completed and each
  published a validated authenticated receipt.
- Import/preparation/native workflow **159.32 s**; including synchronized export
  **179.02 s**. These are one-run wall timings, not benchmark claims.
- Finite `(5468,36)` qpos, exact source IDs/FPS and joint order passed. Maximum
  joint-limit excess **0 rad**; root-quaternion norm error **5.960464477539063e-8**.
- All three independent export tests passed in **18.98 s**, checking every saved
  frame: robot mesh/binding replay against native FK at **5e-7 m** axis tolerance,
  decoded human vertices/barycentric bindings at **5.1e-5 m**, and strict source
  model-path/hash failure cases.
- All **49 protected input files** and **494 unrelated local files/links** stayed
  unchanged. Product code, native source, external pins and old cohorts were
  preserved.

- Browser timeline exposed all frames through 5467. Play from frame 1855 crossed
  multiple 64-frame chunk boundaries, advancing 2307→2379 in 0.8 s without a
  loading hold/error. Play near 5465 looped to 67. Exact seek to 1800 displayed
  20.00 s/source frame 1800. Console warnings/errors: **0**.
  [Screenshot](../../outputs/studio-astro-full-hiphi-20261101/full-01/playback.png)
  and `browser-checks.json` preserve evidence. The viewer was left paused at
  frame 1800 for review on loopback port 8775.

## Observations and next step

The complete saved result is available for visual review. Numerical gates cover
representation and input preservation, not controller stability, collisions,
contact quality, slip or dynamics. Those need their own evaluation. Playback
evidence is recorded separately under the output directory.
