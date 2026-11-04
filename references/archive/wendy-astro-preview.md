# Wendy → Astro: 6–9 second excerpt

Completed 2026-10-22 after the user approved the SMPL-X preview and requested
Astro retargeting. All 360 frames were processed with no stride or resampling.

## Inspect

Local viewer: http://127.0.0.1:8766/?v=astro

Human is on the left, Astro on the right, driven by one frame index/playback
clock. Pause, scrub, slow playback, orbit and front/side views apply to both.
The optional orange BVH skeleton overlays the human by default. Physical
sizes are retained: UMR estimated human height 1.72109 m and robot height
1.23894 m, using scale 0.719857 for retargeting. The viewer shows the original,
unscaled human next to the actual-size robot.

Robot world coordinates are Z-up in the saved NPZ. The preview applies the
inverse of UMR's Y-up-to-Z-up basis: `(x,y,z) -> (x,z,-y)`, then a constant
horizontal display translation. This preserves robot height, orientation
relative to the human, and root displacement. Visual geometry is exported
from MuJoCo's compiled mesh arrays and animated with `mj_forward` geom poses.
No physics simulation or controller tracking has been run.

## Run and artifacts

- Source: `outputs/smplx/wendy_happy_dance_6s_9s.npz`.
- Derived config: `configs/umr/astro-wendy-6s-9s.json`. Extends UMR defaults and
  the existing `configs/umr/astro_p2_29dof.json`, which was not modified.
  Only source selection and output/cache paths are specialized.
- Result: `outputs/umr/astro_p2_29dof/wendy_6s_9s/retarget.npz`.
- Correspondence dataset, trained slots/checkpoint and `pipeline.log` are in
  the same output directory. Standard 4096 points and 500 training epochs.
- UMR generated `retarget.floating_mjcf.xml` beside the canonical Astro XML;
  the result points to that generated model. Canonical XML is unchanged.
- Viewer exporter: `scripts/export_astro_wendy_preview.py`.
- Browser assets: `outputs/smplx/wendy-viewer/`, with checked screenshots
  `astro-preview.png` (8.75 s) and `astro-mid-preview.png` (7 s).

From `/data/workspace/motion_studio/externals/UMR`, with host GPU access:

```bash
.venv/bin/python scripts/humanoid_retarget_pipeline.py \
  --config /data/workspace/motion_studio/configs/umr/astro-wendy-6s-9s.json \
  --skip-view
```

From `/data/workspace/motion_studio`:

```bash
externals/UMR/.venv/bin/python scripts/export_astro_wendy_preview.py
python3 -m http.server 8766 --bind 127.0.0.1 --directory outputs/smplx/wendy-viewer
```

The original human mesh bake remains reused. If it is rebuilt with
`export_wendy_preview.py`, rerun the Astro exporter afterward to restore
robot metadata in the combined viewer manifest.

## Checks and observations

- `qpos` shape `(360,36)`: floating base plus 29 actuated joints.
- 120.000045776 Hz, matching the human NPZ; frame IDs exactly 0–359.
- All qpos finite; root quaternion norm maximum error 5.96e-8.
- Maximum joint-limit excess 1.19e-9 rad (floating-point tolerance).
- Maximum joint change between adjacent frames 0.071858 rad.
- Minimum robot visual mesh height over the clip: +0.007579 m.
- UMR reports final cost mean 0.081504, maximum 0.100793; these are solver
  objective values, not centimeter errors.
- Browser loaded without displayed errors; synchronized scrubbing inspected
  at 7 s and 8.75 s. Robot follows the broad arm/leg gestures; the raised-arm
  pose shows more torso lean than the human. No parameters were tuned to
  hide this difference. Timing restarts at the end of the three-second loop,
  so the loop boundary is not a continuous dance transition.
- This is a kinematic retargeting inspection artifact. Balance, dynamics,
  actuator feasibility and controller tracking have not been validated.

Numerical details: `retarget.preview-report.json` next to the result.

## Subsequent torso tuning

The user requested less torso lean. The viewer now defaults to the tuned
result and includes an Original/Tuned comparison. See
`references/archive/wendy-astro-torso-tuning.md` for controlled trials, tradeoffs and the
explicit exporter command for the tuned output. The original NPZ is preserved.
