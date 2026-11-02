# HiPHI BVH-to-SMPL-X controlled comparison

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

The full Getting_up-get_up_0004 BVH conversion reproduces the shipped SMPL-X body's motion to floating-point precision. The shipped reference includes external wrist/finger fitting that the body-only rerun does not perform. This is a reproducibility result on one motion, not independent anatomical ground truth or validation of Wendy's different skeleton mapping.

## Inputs and controls

- Source: `externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor.bvh`, downloaded from hpc-1's `/data/share/resources/motion_data/HiPHI_extracted_actor_bvh/HiPHI/data/Getting_up/get_up/Getting_up-get_up_0004/`.
- Source SHA-256: `0b326a142f659a23c6c8daf1c21d2a814b83d22b2bfdc16d23ed80dbfb108e48`.
- Reference: adjacent `motion_actor_smplx.npz`, SHA-256 `3a3d20c4ebd1727536136888efdde62f7ea685eb6ea0c88f1160116009416808`.
- All 5,468 frames at source frame time 0.011111 s; duration 60.754948 s. No trimming, resampling, temporal alignment, fitted spatial alignment, or floor correction.
- Same neutral SMPL-X model and reference actor's ten betas. Actor metadata says female; the actual reference model is neutral, so the experiment matches neutral.
- Native HiPHI mapping; centimeters converted to meters by the converter's standard 0.01 scale. Native Y-up output.
- Default conversion settings match recorded reference settings: 10 iterations, damping .01, position cost 1, extremity multiplier 5, orientation/posture/root-posture costs .1, DAQP solver. The current default integration dt is .01; the reference does not record dt.
- hiphi2smplx commit `65e51315ebbc82b2f0ff8e35a94565beb1b345e1`; UMR commit `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
- No weights were tuned to improve agreement.

## Results across all frames

| Measurement | Mean | 95th percentile | Maximum |
|---|---:|---:|---:|
| 22 body joints, world-space difference | 0.000173 mm | 0.000311 mm | 0.000622 mm |
| Translation difference | 0.000070 mm | 0.000246 mm | 0.000358 mm |
| Local body rotation difference, joints 0–19 | 0.0000117° | 0.0000384° | 0.0001044° |
| Rerun per-frame mean IK target residual | 36.586 mm | 42.352 mm | 43.739 mm |
| Reference stored per-frame mean IK target residual | 36.586 mm | 42.352 mm | 43.739 mm |

Joint differences compare newly solved joints with joints reconstructed from the reference pose, translation, and actor shape. Earlier auditing confirmed those reconstructed reference joints agree with its stored fitted joints to <0.0005 mm. Tiny differences are consistent with numerical precision. The IK residual concerns calibrated fitting targets (including equivalent foot targets), and is not direct mesh-to-capture ground-truth error.

Body rotation metrics exclude wrist joints 20–21: the reference records wrist orientations supplied by an external MANO fitting step. All 30 finger poses are also supplied by that external fit. The rerun uses the body converter's wrist solution and zero finger poses. Both actual outputs are shown, with no copied reference hand poses in the rerun.

The machine-readable `report.json` also contains full-mesh differences and a separate attribution control: replace only reference wrist/hand/face poses with rerun values, keeping reference body joints 0–19 and translation, and compare the resulting mesh to the rerun. That control measures mesh agreement after removing the known hand-stage differences; it is not the motion displayed in the viewer.

The earlier zero-beta ablation changed joint positions by 35.76 mm on average with pose/translation fixed. Therefore using mean shape for this comparison would introduce an avoidable confound. Wendy's true shape is unknown; this experiment does not measure Wendy's shape error.

## Review

Viewer: http://127.0.0.1:8768/

Blue left = shipped SMPL-X with fitted hands. Orange right = fresh BVH body conversion. Both use the same frame clock, actor shape, common fixed centering translation, and original height. Side-by-side mode adds fixed ±1.5 m horizontal offsets for viewing only. Overlay mode removes those offsets. Full-resolution meshes retain every frame in one-second chunks, with a bounded browser cache. Scrubbing pauses playback; camera views, frame stepping, and playback speeds are available.

Artifacts: `reconverted.npz`, `report.json`, `conversion.log`, `export.log`, `viewer/`.

## Historical reproduction and viewing

The original commands used `scripts/validate_hiphi_conversion.py --bvh ...` and
`scripts/export_hiphi_comparison.py`. **Do not run these historical writers**:
they use fixed cohort paths and can replace retained reports or archive aliases.
See [artifact relocation](../../docs/artifact-relocation.md#remaining-sealed-batches-and-complete-ledger).
There is currently no fresh-output reproduction route for this conversion control;
[HiPHI robot-control preparation](../../docs/artifact-relocation.md#frozen-writers-and-a-fresh-preparation-route)
prepares a separate robot comparison, not a conversion rerun.

The existing viewer is read-only when served from the workspace root:

```bash
python3 -m http.server 8768 --bind 127.0.0.1 --directory experiments/hiphi-conversion-control/viewer
```

## Mesh control and viewer verification

Across all frames and 10,475 mesh vertices, the actual reference-versus-rerun distance is mean **3.151 mm**, p95 **24.134 mm**, maximum **62.987 mm**. After matching wrist/hand/face poses in the attribution control, it is mean **0.000145 mm**, p95 **0.000338 mm**, maximum **0.001086 mm**. Thus the full-mesh discrepancy is explained by the excluded pose components to numerical precision; body-only conversion is reproducible here.

Both original outputs contain below-floor vertices (reference minimum Y −57.5 mm; rerun −62.0 mm). These heights remain visible without correction; the experiment does not establish physical contact validity.

Verified both sets of 61 binary mesh chunks against their exact expected byte counts, including the final 68 frames. Browser checks covered 10 s, 20 s, the last frame (5468/5468 at 60.744 s), playback, and the overlay toggle without reported loading errors. Review screenshots are saved under viewer/.
