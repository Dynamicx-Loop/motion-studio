# Wendy victory sample: BVH to SMPL-X

Date: 2026-11-02. Cohort: standalone fixed-shape conversion, not an official UMR
reproduction or robot-retargeting comparison. Goal: provide a UMR-readable sample
while preserving the entire original clip and its timing.

## Provenance and runtime

Source: `data/sample_data/fzmotion/wendy/2026-10-19/victory-146-short_Skeleton1.bvh`,
copied from the proprietary local FZMotion Wendy session. SHA-256:
`713d602dd4037fd87f2972c428dfbef811e5cf4b80daafcb6c859bcaa9ff9a37`.
Keep source and derived files local; no redistribution permission recorded.

The Motion Studio Wendy adapter uses hiphi2smplx revision
`65e51315ebbc82b2f0ff8e35a94565beb1b345e1`, without external source patches, and
`externals/UMR/.venv/bin/python`. Licensed neutral SMPL-X model:
`/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.npz`.
Model SHA-256: `376021446ddc86e99acacd795182bbef903e61d33b76b9d8b359c2b0865bd992`.
Model assets and their terms remain separate. Full code/input hashes, platform
and dependency versions are retained in the provenance/environment files.

## Reproduction and preservation

From the Motion Studio root:

```sh
python3 -B scripts/convert_wendy.py --config configs/umr/wendy-victory-sample.json
```

Original destination: `outputs/sample-data/wendy-victory-smplx-20261102/`.
It is occupied; use a new output path in a new config for a rerun. The adapter
refuses overwrites. A reusable copy of motion and provenance is preserved under
`/data/motions/datasets/fzmotion/derived/smplx/wendy-victory-20261102-v1/`.
The sample manifest records hashes for `data/sample_data/fzmotion/smplx/` copies;
`python3 scripts/sample_data.py populate` restores them from the canonical copy.

## Processing and measured results

All 1383 frames were fitted at source frame time 0.0142857 seconds (about 70 FPS).
Source interval: `[0, 1383)`; no trimming, resampling or axis rotation.
Centimeters-to-meters scale: 0.01, declared Y-up. Input BVH Euler channels become
float32 SMPL-X axis-angle radians `[1383, 165]`; translation is meters `[1383, 3]`.
Ten fixed zero betas and neutral gender are retained. Original frame indices and
float64 timestamps are included. No quaternion ordering applies to these outputs.

The fitter reports mean joint residual 0.0351683 m and maximum per-frame mean
0.0389147 m. These are fitting diagnostics, not independent accuracy measurements.
Actor shape, fingers, face and eyes were not estimated. The session T-pose was
not used to estimate shape. Conversion uses the adapter's existing initialization
and default solver settings; no sampling or learned correspondence.

## Validation and limits

Verified finite pose/translation arrays, shapes, exact source frame indices and
timestamps (absolute tolerance 1e-12 s). UMR revision
`d1cdaedaf67a827198da71c5fa831f48b2e51f91` successfully loaded and selected the
NPZ through `smpl_surface_retarget_common.load_motion_collection` and
`select_sequence` in its existing runtime, reporting neutral gender, Y-up,
1383 frames and about 70 FPS. Float32 FPS differs slightly from the reciprocal
of source frame time; float64 frame time and timestamps preserve source timing.

The whole sample collection passes checksum verification. No visual quality
assessment, correspondence training, robot solver, contact/foot-slip study,
collision check or dynamic-feasibility evaluation was performed. Robot-specific
configuration, model setup and fresh outputs remain prerequisites for retargeting.
