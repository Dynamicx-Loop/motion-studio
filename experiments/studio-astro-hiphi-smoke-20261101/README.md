# Experiment: Astro P2 and short HiPHI end-to-end smoke

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-11-01 / Codex, requested native end-to-end test.

## Objective and cohort

Run the built-in **Astro P2** with **HiPHI · 2s quick test** through fresh sampling,
training, binding, retargeting and synchronized inspection. This is a deliberately
reduced **five-epoch/180-frame workflow smoke**, separate from full-quality
acceptance and all historical cohorts. It measures successful execution, recorded
representation contracts and viewing; it does not establish motion quality or
physical feasibility.

Run `7dec132c6ee745899b034f453d70b8df`, revision `r0004`, job
`e64f2436904749ffad305efff23be2d9`, fresh output:
`outputs/studio-astro-hiphi-smoke-20261101/smoke-01/`.

## Provenance and independent runtimes

Motion Studio base revision `9b8dfbe6f816355954f56ef84b96cbb17c6e3018`.
[run.py](run.py) records its own SHA-256 and invokes the public `Studio` API,
using the same built-in robot/sample imports, immutable selection/settings,
planning, execution and inspection operations as the application.

UMR remains at unmodified `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
Astro uses the [root snapshot](../../assets/robots/astro_p2/manifest.json) from
`menagerie_x` `8e3f382f28831331c448c9d62cd197140da63c65`; its upstream checkout
is not used at runtime. Astro source/derived hashes and all native/adapter/runtime
identities are retained in `source.json`, `readiness.json` and stage receipts
under the output above. No external source, pin or runtime packages changed.

Service/driver: system Python 3.12.3. Native runtime:
`externals/UMR/.venv/bin/python`, existing CUDA stack and NVIDIA GeForce RTX 5070
Laptop GPU. The sandbox probe could not see CUDA; execution used the authorized
host runtime, without a CPU fallback. Full package versions are in readiness and
receipts. Licensed SMPL-X weights stay at their original local path, hash-checked
and excluded from the export. Astro, motion and model terms remain separate.

## Robot selection and representation

Built-in ID `astro`, managed identity
`e5689bca41566d83201ce919013da2a6f72d0d5084f968be269de7fba18c3fdf`,
29 hinges, `nq=36`, named T-pose, pelvis floating root and `waist_roll_link`
centering. Metres/radians, native Z-up and root quaternion wxyz. The generic robot
path used no official-G1 root wrapper or G1-only joint-limit overrides. Sampling
and binding used the 37 visual meshes; original collision geometry stays in the
managed model. Root-pose materialization and native configuration are recorded
in the sampling attempt. Display centering is separate from saved qpos.

## Processing and learned artifacts

The pinned HiPHI source is
`externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
`hiphi-quick` keeps exact original frames `[0,180)` at **90.00090026855469 FPS**,
about two seconds, with no resampling. The managed original NPZ records parent
source hash/revision, frame count and trim interval. `inputs.json` records body
shape, gender, axes, source/model hashes and reconstruction disclosure.

Settings: sampling seed 0, training seed 0, **5 epochs**, 4,096 paired slots,
native19 segmentation and **LQR** trajectory filter. All four stages ran fresh;
no learned artifact was reused. Reconstruction uses neutral hands and omits facial
channels while preserving original source bytes. Native output `motion.npz` has
shape **(180,36)**, source frame IDs 0–179, original FPS and 29 named robot joints.

## Reproduction

From `/data/workspace/motion_studio`, on the host with GPU access, select a fresh
output destination; the driver refuses an existing one:

```sh
python3 -B experiments/studio-astro-hiphi-smoke-20261101/run.py \
  --output outputs/studio-astro-hiphi-smoke-20261101/<fresh-id>
```

The driver preserves plans, input identities, every stage command/environment,
native logs, receipts, validation and a standalone inspection. Review
[result.json](result.json) for exact output identities and paths.
Independent export checks for this saved run:

```sh
STUDIO_INSPECTION_SMOKE=/data/workspace/motion_studio/outputs/studio-astro-hiphi-smoke-20261101/smoke-01 \
  externals/UMR/.venv/bin/python -B -m unittest discover \
  -s tests -p test_studio_inspection_runtime.py -v
```

View this saved state, then open the Motion inspection URL in `result.json`:

```sh
python3 -B scripts/studio.py \
  --state outputs/studio-astro-hiphi-smoke-20261101/smoke-01/state --port 8774
```

Exported bundle viewing needs no UMR or model-weight runtime. Recreating the run
needs its recorded dependencies.

## Evaluation

- Sampling, training, binding and retargeting each exited successfully, validated
  outputs and published an authenticated receipt. The job completed normally.
- Import/preparation and native workflow: **59.75 s**; including inspection export:
  **71.09 s**. These are this run's wall timings, not a throughput benchmark.
- Finite qpos (180×36), exact frame IDs and FPS passed. Maximum root quaternion
  norm error **5.960464477539063e-8**; maximum joint-limit excess **0 rad**.
- Three independent export checks passed: robot replay/rigid binding versus native
  FK at 5e-7 m axis tolerance; human decoded vertices/barycentric bindings versus
  native SMPL-X at 5.1e-5 m, covering all three chunks; strict model-path/hash checks.
- Actual browser Play/loop and seek to source frame 128 passed with no loading
  hold, page error or console warning/error observed. Both tracks used one saved
  timeline. [Playback screenshot](../../outputs/studio-astro-hiphi-smoke-20261101/smoke-01/playback.png).
- All **49 protected input files** and **494 unrelated local files/links** remained
  unchanged. Product source, historical robot definitions and native pins were
  unchanged. Full artifact hashes and native logs remain in the fresh output.

## Observations and next step

The built-in Astro now has a demonstrated complete native route with the short
sample, including saved playback. Five epochs and the first two seconds are a
workflow smoke only. Full-clip/high-epoch quality, contact/slip/collision metrics
and dynamic feasibility were not evaluated. A full-quality cohort would require
separate fresh training and its own acceptance record.
