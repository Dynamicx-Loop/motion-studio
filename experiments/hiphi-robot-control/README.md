# Getting_up-get_up_0004: two inputs × two robots

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Four full-length kinematic retargets compare the shipped SMPL-X reference against the fresh BVH-to-SMPL-X conversion, for Astro P2 (29 DOF) and UMR's shipped Unitree G1 (29 DOF).

## Controls

- 5,468 frames at 90.0009 Hz, duration 60.754948 s; no trimming or resampling.
- Same actor betas, neutral SMPL-X model, source scale convention, Y-up, and no source ground alignment.
- Astro uses `configs/umr/astro_p2_29dof.json` plus UMR defaults. The Wendy-specific torso tuning is not used.
- G1 uses `externals/UMR/robot_configs/humanoid_retarget_unitree_g1_example.json`, including its joint-limit overrides, with the shipped `assets/g1/g1_29dof.xml`.
- One correspondence model is built and trained per robot on the actor shape, then reused between reference and reconverted runs. Sampling/solver seed is 0; training is 500 epochs. Correspondence is not shared across robot embodiments.
- Identical solver weights, initial-pose procedure, sequential warm start, LQR filtering, and full input duration within each pair. No post-hoc tuning based on differences.
- UMR's default `zero_source_finger_pose=true` is retained for all four runs. Thus this tests the normal retargeting pipeline, which removes finger-pose differences but retains wrist differences.
- GPU SMPL-X batching is capped at 128 frames for both robots due to available GPU memory; no motion frames are dropped.

The original reference is unchanged. `reconverted_yup.npz` copies the fresh conversion's arrays and adds explicit `output_up="y"` metadata only. Pose, translation, and shape values are unchanged. Input body motion was already found to agree to numerical precision; wrist orientations and finger poses differ because the reference includes external hand fitting.

## Interpretation

Within-robot differences are the experiment's outcome. Cross-robot differences are expected from different geometry, joint limits, learned correspondence, and human-to-robot scaling; they are not conversion error. This four-run experiment cannot independently distinguish wrist effects from sensitivity to tiny numerical differences or establish physical feasibility. No dynamics, balance controller, or robot execution is tested.

`report.json` reports absolute hinge-angle differences, free-root translation distances, quaternion geodesic rotation differences, and body-origin differences in common world coordinates. No trajectory alignment is fitted. Frame steps, joint limits, finite values, and minimum visual-mesh height are checked. Visual mesh minima are exact extrema over mesh vertices, computed using their convex-hull vertices, and do not imply collision or support validity.

## Artifacts and review

- `configs/`: four run configurations.
- `astro/` and `g1/`: shared correspondence/training artifacts and `reference.npz`, `reconverted.npz`.
- Four named `.log` files preserve complete pipeline output.
- `report.json`: paired numerical comparisons and output hashes.
- `viewer/`: synchronized local viewer with robot selector, reference/fresh pair, scrubbing, camera controls, and overlay.

The viewer uses a shared fixed centering translation within each pair and ±1.3 m display offsets. Height and trajectories are preserved; overlay removes the display offsets. Colors identify the two versions, with original robot mesh detail retained.

## Historical reproduction and fresh preparation

The original run used `experiments/hiphi-robot-control/run.py` and
`scripts/export_hiphi_robot_control.py`. **Do not run these historical writers**:
they target the frozen cohort; archived log and mesh targets are read-only, and
other retained evidence can still be replaced. See the
[fresh preparation route](../../docs/artifact-relocation.md#frozen-writers-and-a-fresh-preparation-route),
which creates fresh configurations and model inputs without executing a solve.
Its receipt provides individual execution commands; runtime and model prerequisites
need separate validation. It does not reproduce the old viewer or establish new
numerical results. GPU access is required for the recorded retargets. Source
revisions are UMR `d1cdaedaf67a827198da71c5fa831f48b2e51f91` and hiphi2smplx
`65e51315ebbc82b2f0ff8e35a94565beb1b345e1`.

To view the existing saved viewer from the workspace root:

```bash
python3 -m http.server 8769 --bind 127.0.0.1 --directory experiments/hiphi-robot-control/viewer
```

## Results

| Metric | Astro | G1 |
|---|---:|---:|
| Mean joint difference (degrees) | 1.2700 | 0.7833 |
| Mean wrist difference (degrees) | 4.5176 | 3.0261 |
| Mean non-wrist difference (degrees) | 0.4228 | 0.1983 |
| Mean leg difference (degrees) | 0.0895 | 0.1313 |
| Mean root distance (mm) | 0.7488 | 0.8309 |
| Mean root rotation difference (degrees) | 0.2538 | 0.4290 |

astro: maximum joint difference 16.100° at {'frame_index': 2601, 'time_s': 28.899710916655803, 'joint': 'left_wrist_roll_joint'}; maximum root distance 4.932 mm.
Minimum visual mesh heights: reference -6.69 mm, reconverted -6.59 mm.

g1: maximum joint difference 21.261° at {'frame_index': 4795, 'time_s': 53.27724484635316, 'joint': 'right_hip_pitch_joint'}; maximum root distance 18.209 mm.
Minimum visual mesh heights: reference -10.85 mm, reconverted -10.71 mm.

All four outputs have finite qpos and full frame IDs. Model and configured joint limits hold within 1e-6 rad. Robot XML hashes match within each pair; logs confirm reuse of the shared correspondence slots. Finger clearing is recorded as enabled in every output. The largest average differences are concentrated in wrists (G1 has a transient maximum at its right hip), consistent with the known wrist differences between source motions; causal isolation would require an additional matched-wrist input control. Floor penetration remains in the visual meshes and is not corrected in the viewer.

Review: http://127.0.0.1:8769/ . Provenance and effective configuration equality checks are in provenance.json and configs/*-resolved.json.
