# Sample-data UMR retargeting verification on bundled G1

Date: 2026-11-02. Cohort: two independent full-clip execution checks using the
official bundled G1 and native defaults. This does not advance a historical
baseline or establish matched motion-quality comparison between datasets.

## Completed results

Both full clips completed fresh training and retargeting and passed all validation
checks. [Saved summary](records/summary.json) contains motion hashes and numerical
diagnostics; per-case execution records retain commands, timings and preservation
outcomes. Run artifacts are under
`outputs/sample-data/umr-g1-verification-20261102/`.

| Source | Retained frames | Saved FPS | qpos shape | Joint-limit excess | Train / retarget time |
| --- | ---: | ---: | --- | ---: | --- |
| BONES-SEED jump-and-land | 1170 / 1170 | 120.004799 | `(1170, 36)` | 0 rad | 58.9 s / 34.2 s |
| Wendy victory SMPL-X | 1383 / 1383 | 70.000069 | `(1383, 36)` | 0 rad | 41.9 s / 32.4 s |

The training stage includes fresh dataset preparation. Maximum root-quaternion
norm error was below 1e-6 for both. Source/model/configuration hashes and upstream
revision/status were unchanged after each run. The validator emitted a NumPy
scalar-conversion deprecation warning when reading the saved one-element FPS;
both checks completed successfully. The executed runner snapshots retain the
exact source used for these records.

## Inputs, runtime and commands

Motion Studio samples:

- BONES-SEED `jump_and_land_light_003__A001.bvh`, 1170 source frames, uniform
  shared fitted MHR identity; no SMPL-X conversion.
- FZMotion `victory-146-short_Skeleton1.npz`, 1383 source frames, the previously
  converted fixed-neutral SMPL-X Wendy motion. Original BVH and conversion
  diagnostics remain preserved separately.

UMR revision: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, unchanged tracked
source, independent `externals/UMR/.venv/bin/python`, NVIDIA GeForce RTX 5070
Laptop GPU. No installation or download. Source, model and robot terms remain
separate; payloads and model weights remain local and Git-ignored.

From the Motion Studio root, with host GPU access:

```sh
externals/UMR/.venv/bin/python -B experiments/sample-data-umr-g1-20261102/run.py --output outputs/sample-data/umr-g1-verification-20261102
```

The output path must be fresh; the runner refuses occupied destinations. Run
configs, resolved defaults, input/code/model hashes, runtime packages, logs,
stage commands and timings, copied robot assets, datasets, slots and motions
are stored independently below `bones-seed/` and `wendy/`. The runner itself is
snapshotted per run. No source input is rewritten. Model paths and linked SOMA-X
assets are included in provenance, with preservation checked after each run.

## Processing and validation

Both cases independently sample 4096 source/robot points and train fresh
correspondence for 500 epochs, seed zero, without borrowing old slots. Native
solver/contact settings, sequential warm start and LQR filtering are retained.
Operational overrides are absolute paths, run-local robot copies, no viewer,
CUDA training and a 64-frame SMPL-X batch cap. BONES-SEED discovery must resolve
`soma_bvh_boneseed_uniform` and `soma_uniform` with the verified shared fit;
generic fallback is rejected before training.

All source frames are requested with stride one. BONES-SEED uses the native
loader's approximately 120.0048 FPS and Wendy uses its saved approximately
70.00007 FPS. Source surfaces are meters/Y-up; UMR maps source to robot Z-up.
Robot qpos contains XYZ meters, wxyz root quaternion, then the 29 recorded G1
hinge joints in radians. No resampling or intentional trimming is configured.

Validation checks exact frame indices and counts, FPS within one float32 ULP,
finite qpos, expected robot dimension and joint order, unit root quaternions
within 1e-6, effective XML/configuration joint limits within 1e-6 radians, and
native dataset/slots compatibility with finite `(2, 4096, 3)` learned slots.
Adjacent joint steps are reported as diagnostics. Per-run JSON records are
authoritative for executed outcomes.

Successful numerical execution does not establish visual motion fidelity,
contact preservation, floor clearance, collision freedom, dynamic feasibility
or hardware suitability. No viewer or independent quality study is part of this
bounded verification.
