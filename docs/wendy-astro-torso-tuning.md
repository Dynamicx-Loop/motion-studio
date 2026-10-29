# Reducing Astro torso lean

Completed 2026-10-22 for the same source frames 720–1079 (6–9 s), 360 frames
at 120.000045776 Hz. Viewer: http://127.0.0.1:8766/?v=torso-tuned .
Select **Tuned torso** or **Original** to compare at the same paused frame.

## Diagnosis

The original result has a mean 12.801° torso-axis difference from the human,
with p95 28.108°. At source 8.75 s, human chest tilt is 4.639° from vertical,
while the robot torso tilts 27.047°. This is present in FK, independently
of camera and display offsets.

The measurement uses SMPL-X spine3/chest (joint 9) global +Y and Astro
`torso_link` global +Z, transformed into a common basis. It measures upright
axis agreement, not full yaw orientation. Shoulder-to-wrist direction is
also measured as a gesture-quality guardrail; differing robot proportions
mean it is not a perfect anatomical correspondence metric.

Controlled variants reuse exactly the same correspondence and motion:

| Variant | Torso axis mean / p95 (deg) | Robot tilt at 8.75 s (deg) |
|---|---:|---:|
| Original | 12.801 / 28.108 | 27.047 |
| Self-contact weight 500 → 0 | 12.489 / 26.058 | 25.162 |
| Solver iterations 1 → 5 | 12.795 / 28.088 | 26.668 |
| Torso normal cost 5 → 50 | **4.046 / 6.324** | **7.538** |
| Torso normal cost 5 → 100 | 3.860 / 5.530 | 7.390 |
| Torso normal 50 + arm/forearm normals 5 → 20 | 9.335 / 18.106 | 17.129 |

The evidence points to competing fitting objectives, with insufficient torso
orientation weight relative to the rest of the surface fit. UMR fits points
and transported surface normals; it has no explicit chest-upright task in
this run. Lean can improve the other targets. Self-contact and inadequate
iteration count were not dominant causes in the controlled tests. Stronger
arm weights reintroduce lean, further demonstrating the tradeoff.
This does not prove every contributor to the residual error; correspondence,
proportions and nonrigid human torso surface deformation can also matter.

## Selected change

`configs/umr/astro-wendy-6s-9s-tuned.json` extends the original excerpt config
and overrides only torso normal cost to 50 plus output path. Explicitly
retains torso `sample_slots=50` and `point_cost=20`: UMR replaces a segment's
whole cost object, rather than merging its individual keys.

An initial exploratory run omitted those two fields, which disabled torso
sampling. It was rejected and rerun with the complete object; all results
in the table refer to the corrected controlled variant.

The selected change reduces mean torso-axis error by 68.4%, p95 by 77.5%,
and raised-arm axis error from 25.464° to 3.195°. Weight 100 had diminishing
returns and a larger arm penalty, so 50 was selected. Canonical Astro config,
T-pose, contact weights, iterations and filtering remain unchanged.

Tradeoffs and validation:

- Mean left arm direction error: 15.679° → 19.433° (+3.754°).
- Mean right arm direction error: 9.865° → 11.410° (+1.546°).
- Joint-step p95: 0.017394 → 0.018741 rad/frame. Max: 0.071858 → 0.099123
  rad/frame (same frame transition 269→270 and scalar joint index 23).
- Absolute second-difference p95: 0.006414 → 0.006732 rad/frame².
- Finite qpos `(360,36)`; unchanged frame IDs and frame rate.
- Maximum joint-limit excess 3.58e-9 rad; quaternion norm error 5.96e-8.
- Minimum visual mesh height +0.001962 m; no visual-mesh ground penetration.
- Browser checked at 7 s and 8.75 s. Original/Tuned switch changes robot
  animation and metrics without changing human or playback frame.
- Kinematic only; balance, dynamics and tracking have not been validated.

An exploratory strict target of mean <3° / p95 <5° was not reached by the
surface-weight trials. The retained regression check instead enforces the
requested reduction with a stated tradeoff budget: >60% improvement in both
mean and p95, raised-arm error <5°, and each arm mean error increasing <5°.
The untouched baseline fails; the selected result passes. This is a
clip-specific acceptance check, not a universal robot-motion quality test.

## Artifacts and reproduction

- Original: `outputs/umr/astro_p2_29dof/wendy_6s_9s/retarget.npz` (preserved).
- Tuned: `outputs/umr/astro_p2_29dof/wendy_6s_9s/retarget_torso_tuned.npz`.
- Variant configs: `experiments/wendy-torso/`; retained diagnostic experiments.
- Logs and `.torso-report.json` / `.preview-report.json` beside results.
- Screenshots: `outputs/smplx/wendy-viewer/astro-torso-tuned.png` and
  `astro-torso-tuned-mid.png`.
- Original browser transforms preserved as `robot-baseline-transforms.bin`.

From the UMR directory (host GPU access):

```bash
.venv/bin/python scripts/humanoid_retarget_pipeline.py \
  --stage retarget --skip-view --force-retarget \
  --config /data/workspace/motion_studio/configs/umr/astro-wendy-6s-9s-tuned.json
```

From the workspace root:

```bash
externals/UMR/.venv/bin/python scripts/check_wendy_torso.py \
  outputs/umr/astro_p2_29dof/wendy_6s_9s/retarget_torso_tuned.npz --assert-improved
externals/UMR/.venv/bin/python scripts/export_astro_wendy_preview.py \
  --result outputs/umr/astro_p2_29dof/wendy_6s_9s/retarget_torso_tuned.npz
```

The checker requires the baseline `.torso-report.json`; regenerate it by
running the same checker on `retarget.npz` without `--assert-improved`.
The tuned result is byte-identical to the selected `torso_normal_50.npz`
experiment, copied to a stable final path. No pose postprocessing was added.
