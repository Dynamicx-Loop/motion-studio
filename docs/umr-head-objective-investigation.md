# UMR backward torso lean: head-objective ablation on Astro and G1

2026-10-22. Research and controlled kinematic experiments by Codex.

## Finding

**The fixed-head hypothesis does not explain the backward lean at the reported local frame.** At source index 92 (viewer frame 93, 1.022 s), the actual human upper chest is already tilted backward. Astro and G1 closely reproduce that chest axis. Disabling the direct head surface fit makes both robots lean **slightly farther backward**. Their configured calibration T-poses are upright; a separately constructed, genuinely neutral source also retargets nearly upright.

This finding concerns the inspected `Getting_up-get_up_0004` prefix, not every UMR clip or HHTools. The general mechanism is real: neither robot has an independent actuated head, so fitting its head geometry can affect upstream joints. Here, however, the head objective slightly counters the backward chest orientation rather than creating it. Numerical evidence is in [report.json](../experiments/hiphi-head-objective/report.json), with an independent [original-BVH check](../experiments/hiphi-head-objective/source-crosscheck.json).

![Source skeleton, robot silhouettes, and torso pitch](../experiments/hiphi-head-objective/head-ablation.png)

## What was measured

All signed pitches use source pelvis forward (+Z in its local SMPL-X frame), projected onto the horizontal plane. Positive is forward, negative backward. Human chest is SMPL-X `spine3` (joint 9) global +Y; robot chest is `torso_link` global +Z. Human head is joint 15 global +Y. The human hierarchy is verified against the installed SMPL-X model's `kintree_table`. Source Y-up coordinates are converted to native UMR Z-up using `(x,y,z) → (x,−z,y)`, exactly as the [owning source function](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L257-L274). No fitted alignment, camera-derived angle, or postprocessing correction is used. Axis error is the 3D angle between the two chest upright axes; it does not measure full orientation or yaw agreement. The [measurement script](../experiments/hiphi-head-objective/analyze.py) implements these definitions.

| Frame 92 measurement | Degrees |
|---|---:|
| Original BVH upper chest (`Spine4` global +Y) pitch | −15.206 |
| Actual SMPL-X chest pitch | −13.578 |
| Actual SMPL-X head pitch | −3.549 |
| Actual SMPL-X hips-to-shoulders line pitch | −3.975 |
| Astro configured T-pose torso tilt | 0.000 |
| G1 configured T-pose torso tilt | 0.000 |

The source has a curved, articulated spine: original BVH `Spine`, `Spine2`, and `Spine4` axes have pitches +11.722°, −2.585°, and −15.206° respectively. A near-upright hips-to-shoulders line therefore coexists with a backward upper chest. Its outstretched-arm stance is **a motion frame resembling a T-pose**, not the zero-body-pose calibration. This also explains why copying an upper-chest orientation onto a rigid robot trunk can look more pronounced than the human silhouette. The numerical curvature is measured; the explanation of visual emphasis is an inference. The BVH hierarchy and transforms come from the original clip, parsed by [hiphi2smplx's source parser](https://github.com/noitom-robotics/hiphi2smplx/blob/65e51315ebbc82b2f0ff8e35a94565beb1b345e1/src/hiphi2smplx/bvh.py) and [forward kinematics](../externals/hiphi2smplx/src/hiphi2smplx/kinematics.py).

## What the head objective actually is

UMR does not create a standalone head-link orientation task here. It learns corresponding surface slots, labels source slots by semantic body segment, binds corresponding robot slots to robot surface geometry, and jointly fits point positions and transported surface normals. The default `head` segment has 20 sampled slots, point cost 1, and normal cost 1; `torso` has 50, 20, and 5. These are [source defaults](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L161-L184). Slot costs are assigned by **source** segment, so “head off” below means disabling that semantic surface objective, not deleting a robot link or guaranteeing every labeled slot binds to the anatomical head.

The solver adds square-root-weighted point and normal residual/Jacobian rows and skips rows whose respective cost is zero. It retains separate contact and smoothness terms. In `tpose_offset` mode, robot calibration normals are transported using source mesh-face deformation; they are not a direct head bone quaternion target. See [point/normal residual construction](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1770-L1810), [segment costs](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L2437-L2478), and [normal transport](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L2609-L2673).

Astro's `head_link` is a jointless child of its jointless `torso_link`, downstream of waist pitch/roll/yaw. G1's head meshes are geoms directly on `torso_link`, downstream of the waist joints. Neither has a neck/head joint in this model. Thus a head surface orientation residual cannot be independently resolved by turning the head. Sources: [Astro XML](/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_29dof/astro_p2_29dof.xml:142) and [shipped G1 XML](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/assets/g1/g1_29dof.xml#L201-L219).

## Controlled results

Each robot reuses its own existing learned correspondence. Fourteen runs cover seven variants × two robots. Every run processes source frames 0–239 sequentially, preserving all warm-start history before the inspected frame; the source prefix is 2.656 s from first to last timestamp at 90.0009 Hz. Solver iterations, contacts, filtering, seed, template shape, robot configuration and joint limits remain fixed within each comparison. Astro uses canonical defaults, not Wendy torso tuning. No new correspondence training was performed.

The main ablation keeps `sample_slots=20` and sets only `point_cost=0, normal_cost=0`. This preserves the selected slot sampling and contact setup. Per-segment overrides must include all three fields because UMR [replaces the whole segment entry](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L233-L294).

| Actual source, frame 92 | Astro pitch | G1 pitch |
|---|---:|---:|
| Baseline head point/normal 1/1 | −13.444° | −13.599° |
| Direct head fit disabled, 0/0 | −14.510° | −14.273° |
| Head normal disabled, point retained | −14.419° | −14.180° |
| Head point disabled, normal retained | −13.522° | −13.684° |

Disabling the head increases backward pitch by 1.066° on Astro and 0.674° on G1. Normal fitting explains most of this small corrective effect. This is consistent with the source head being more upright than its upper chest, although the actual objective transports surface normals rather than directly targeting that head-axis measurement.

| Chest-axis error against actual source | Astro baseline → head off | G1 baseline → head off |
|---|---:|---:|
| Frame 92 | 0.855° → 1.327° | 1.501° → 1.730° |
| Mean, frames 60–150 | 1.165° → 1.739° | 2.214° → 2.324° |
| Mean, full 240-frame prefix | 1.715° → 1.941° | 3.765° → 3.703° |
| P95, full prefix | 3.160° → 3.444° | 6.246° → 6.355° |

The tiny G1 full-prefix mean improvement does not remove the observed backward stance. It reflects different errors elsewhere in a prefix that starts moving forward near its end. Results do not justify recommending a global head-off setting.

A broader `sample_slots=0` trial gave frame-92 pitches Astro −14.372° and G1 −12.391°. **This is not an isolated head-objective test.** UMR uses one RNG for successive segment samples, so skipping head draws changes later segment samples; selected-slot contact maps change too. Its full-prefix mean axis errors worsen to 2.048° and 4.113°. The sampler's [owning code](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L936-L955) explains this confound. No conclusion about a pure head-link effect is drawn from that variant.

## Genuine neutral-pose control

A synthetic source retains the actor's betas, gender, FPS and frame-92 translation, repeats 240 frames, sets all non-root pose axis angles to zero, and uses a pure −90° Y-axis root yaw. It has exactly upright chest/head axes and no source spine curvature. It is stored separately in [neutral/motion_actor_smplx.npz](../experiments/hiphi-head-objective/neutral/motion_actor_smplx.npz); the real clip is untouched. The correspondence remains the same actor/robot pair. The construction is in [run.py](../experiments/hiphi-head-objective/run.py).

| Mean torso tilt from upright, neutral input | Astro | G1 |
|---|---:|---:|
| Baseline head enabled | 0.878° | 0.548° |
| Direct head fit disabled | 0.989° | 0.607° |

The configured robot T-pose itself has 0° torso tilt. Retargeted neutral is not exactly that calibration pose: the solver still fits geometry, contacts, and configured constraints (including G1's 0.1-rad knee lower limits). Neither neutral case reproduces the ~13.5° backward chest seen at the reported real-motion frame.

## Provenance and reproduction

- UMR: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; no tracked upstream code patch was introduced.
- hiphi2smplx: `65e51315ebbc82b2f0ff8e35a94565beb1b345e1`.
- Astro assets: menagerie_x `d6a0ee64526c3eaaa7e7beea11bb5ead9d3f44b5`, plus existing local asset state recorded in provenance. G1 uses UMR's shipped XML and joint overrides.
- Input: shipped neutral-actor SMPL-X `externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`, and its adjacent original BVH. Prefixing truncates the clip to 240 frames; no resampling or pose alteration occurs in actual-motion runs. Synthetic neutral is explicitly separate.
- Runtime: UMR `.venv`, Python 3.12.3, NumPy 1.26.4, PyTorch 2.7.1+cu128, MuJoCo 3.3.7, Mink 1.1.0, RTX 5070 Laptop 8GB. GPU SMPL-X batch cap 128; seed 0. Source finger clearing remains enabled.
- Units: metres and radians; source Y-up, robot native Z-up; qpos free-root quaternion is wxyz, scalar joint order is stored in each output's `robot_joint_names`. Viewer alone uses `(x,y,z) → (x,z,−y)` and fixed display translations.
- [Provenance/hashes](../experiments/hiphi-head-objective/provenance.json), [configs and resolved configs](../experiments/hiphi-head-objective/configs/), per-run logs, and outputs reside under `experiments/hiphi-head-objective/`. Source and output hashes are recorded. Upstream automatically generated separate floating-base XML companions beside the robot XMLs; it did not replace the canonical XMLs or configs.
- Source clips, models and meshes retain their original licenses/asset terms; these local experiments do not establish redistribution permission.

From the workspace root, using host GPU access for retargeting:

```bash
externals/UMR/.venv/bin/python experiments/hiphi-head-objective/run.py
externals/UMR/.venv/bin/python experiments/hiphi-head-objective/analyze.py
externals/UMR/.venv/bin/python experiments/hiphi-head-objective/export_viewer.py
MPLCONFIGDIR=/tmp/hiphi-head-matplotlib externals/UMR/.venv/bin/python experiments/hiphi-head-objective/plot.py
python3 -m http.server 8770 --bind 127.0.0.1 --directory experiments/hiphi-head-objective/viewer
```

`run.py` preserves existing configs and uses UMR's existing-output reuse; remove only the desired experiment output or use the per-run pipeline command with `--force-retarget` for a fresh solve. The plotting script uses the host's read-only Matplotlib package after importing the UMR runtime's dependencies, without installing anything into UMR. Logs retain the exact pipeline commands. Each actual solve ran `humanoid_retarget_pipeline.py --stage retarget --skip-view --config <absolute experiment config>` from `externals/UMR`.

## Validation, review and limits

All fourteen outputs have 240 finite qpos frames, expected frame IDs, and satisfy model plus configured joint limits within 1e-6 rad. The two prefix baselines are **bit-identical to the existing full-clip qpos through frame 180**, including frame 92, validating sequential initialization and excluding a nearby LQR end-boundary artifact. Resolved main-pair configs differ only in head-cost override, output path and config provenance path. Correspondence files are reused unchanged. No canonical config, baseline output, or original viewer was replaced.

The [separate local viewer](http://127.0.0.1:8770/) starts paused at frame 93 and supports Astro/G1, baseline/head-off comparison, scrubbing and overlay. Browser checks verified both robot selectors, frame/time, numerical labels and no application error; the initial missing-favicon request was resolved. The [figure](../experiments/hiphi-head-objective/head-ablation.png) was rendered and inspected, showing actual source curvature and FK robot silhouettes rather than camera-derived angle estimates.

The user's [official browser Studio](https://hanyang9.github.io/UMR/umr_studio.html) screenshot shows the **Motion** stage at frame 36/450, 1.17 s, despite the adjacent panel being called “T-pose editor.” It is therefore not evidence that the configured neutral calibration itself leans. The official page describes a browser-adapted pipeline and says its performance is not representative of native UMR. Its exact source subsampling, trained correspondence, solver state and output were not recovered here, so this investigation does **not** claim numerical reproduction or causal diagnosis of that separate browser run.

This experiment is restricted to the reported stance and its first 240-frame neighborhood. It does not test the full getting-up sequence, HHTools' mapping, other robots, dynamics, balance, self-collision or execution feasibility. No torso-normal tuning was used. The evidence supports retaining baseline head settings for this clip; a future objective aimed at the human's gross trunk line instead of upper-chest orientation would be a separate retargeting design choice with its own fidelity tradeoff.
