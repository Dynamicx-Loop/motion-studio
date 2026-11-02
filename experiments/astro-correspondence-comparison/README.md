# Experiment: Astro visual and primitive learned correspondences

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-22 / Codex, delegated correspondence comparison.

## Objective

Train separate HiPHI actor ↔ Astro correspondences with visual meshes and collision
primitives, then inspect the paired slots before any motion retargeting. Both
500-epoch training runs completed. Visual production binding passed. **Primitive
production binding was rejected: 470/4096 projected slots (11.47%) lie inside
another selected primitive, including 36 inside a different body's primitive.**
The primitive preview is explicitly diagnostic; it is not a usable accepted
binding. No motion retargeting, motion solve, or simulator rollout was run.

## Provenance

- Source: [UMR](https://github.com/hanyang9/UMR), isolated
  `externals/UMR-astro-surface-experiment`, commit
  `d1cdaedaf67a827198da71c5fa831f48b2e51f91`. MIT license/notices preserved.
- The existing geometry patch is unchanged. Complete tracked/untracked upstream
  edits are preserved in
  [umr-surface-geometry.patch](../astro-surface-geometry/umr-surface-geometry.patch),
  SHA256 `e2cc109b3aa8125034391fde0ae2f66a02ea660a6900ce727351ea1579ca000a`.
  No new external code change was needed. See the
  [geometry experiment](../astro-surface-geometry/README.md) for seven passing
  geometry regressions and baseline checks; those results are reused here.
- Input: shipped `externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
  It contains 5468 frames at 90 Hz. Only neutral gender and its ten actor betas
  inform static correspondence training; the frame poses are not training targets.
  Template name: `smplx_neutral_betas_52fa48a138`. This experiment intentionally uses
  this actor-specific template rather than the HiPHI adapter's beta-zero shared
  G1 cache. No Wendy data or other session outputs are used.
- Licensed SMPL-X source model directory:
  `/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx`.
  Although NPZ models are also present, the existing UMR loader selected
  `SMPLX_NEUTRAL.pkl`; logs and its checksum record the actual loaded asset.
  No model, robot asset, or motion data is copied into tracked experiment files.
  Existing source/model/asset terms apply separately; this does not grant
  redistribution rights.
- Robot asset repository commit:
  `d6a0ee64526c3eaaa7e7beea11bb5ead9d3f44b5`.
  Canonical XML and config hashes match the prior geometry experiment; neither
  was edited. T-pose: shoulder rolls ±π/2 and elbows +π/2, remaining joints zero.
- Python: `externals/UMR/.venv/bin/python`, 3.12.3; Torch 2.7.1+cu128 / CUDA12.8,
  NumPy1.26.4, SciPy1.17.1, MuJoCo3.3.7, trimesh5.1.1. Training ran sequentially
  outside the sandbox on NVIDIA GeForce RTX5070 Laptop GPU, 8,053,915,648 bytes,
  compute capability12.0. No resource errors occurred. Exact runtime and peak
  GPU memory were not instrumented, so this is not a speed/memory benchmark.
- [provenance.json](provenance.json) records input/model/canonical/patch/dataset/
  learned-slot SHA256s and dependency versions. Original checkouts and environments
  were preserved; no package installation, baseline advance, or commit was made.
- Coordinates: metres, human/preview `(left,up,forward)` and robot root
  `(forward,left,up)`, related by the configured permutation matrix. Robot points
  are centered on `body:pelvis`; human mesh/samples on SMPL-X spine1. Each cloud
  is independently floor-shifted and moved horizontally only for display. No
  quaternion convention, temporal resampling, joint trajectory, or FPS conversion
  is involved in this static experiment.

## Reproduction

Working directory: `/data/workspace/motion_studio`.

[visual.json](visual.json) and [primitive.json](primitive.json) extend the existing
UMR defaults. [visual-resolved.json](visual-resolved.json) and
[primitive-resolved.json](primitive-resolved.json) preserve the complete merged
settings. Separate datasets/checkpoints/slot files live under
`outputs/astro-correspondence-comparison/{visual,primitive}/`.

The only experimental variable is robot surface selection (`auto` visual meshes
versus `collision_primitives`, including the geometry patch's exposure sampling).
Both use 4096 points, seed0 (human sampler1000, robot9000), oversample8,
curvature0, same actor betas, same T-pose, fixed human template, deterministic
slot sort `y_z_x`, same geodesic graph with32 neighbours (131072 directed edges),
500 epochs, batch1, AdamW lr0.001 cosine to0.00001, Chamfer1, repulsion0.002
(k8/radius0.035), edge0.4, residual0, noise0.002, dropout0, no dynamic resampling.
`fixed_template=true`/batch1 selects upstream `robot2smpl_only` training and
ensures the human output stays the same ordered input in both runs. The raw robot
normalization height is derived independently from each surface (1.239373m visual,
1.240003m primitive); shared human height is1.661802m. This geometric consequence
is part of the upstream `per_sample_height` normalization rule, not a changed
training hyperparameter. Only seed0 was trained; no multiseed significance claim.

Exact successful stage commands (GPU train commands require host GPU access):

```sh
externals/UMR/.venv/bin/python externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py --config experiments/astro-correspondence-comparison/visual.json --stage build > outputs/astro-correspondence-comparison/visual-build.log 2>&1
externals/UMR/.venv/bin/python externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py --config experiments/astro-correspondence-comparison/visual.json --stage train > outputs/astro-correspondence-comparison/visual-train.log 2>&1
externals/UMR/.venv/bin/python externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py --config experiments/astro-correspondence-comparison/primitive.json --stage build > outputs/astro-correspondence-comparison/primitive-build.log 2>&1
externals/UMR/.venv/bin/python externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py --config experiments/astro-correspondence-comparison/primitive.json --stage train > outputs/astro-correspondence-comparison/primitive-train.log 2>&1
externals/UMR/.venv/bin/python experiments/astro-correspondence-comparison/inspect_pairings.py > outputs/astro-correspondence-comparison/inspection.log 2>&1
MPLCONFIGDIR=/tmp/astro-pairings-matplotlib python3 experiments/astro-correspondence-comparison/plot_pairings.py
cp experiments/astro-correspondence-comparison/viewer.html outputs/astro-correspondence-comparison/viewer/index.html
cp experiments/astro-correspondence-comparison/viewer.js outputs/astro-correspondence-comparison/viewer/app.js
python3 -m http.server 8766 --bind 127.0.0.1 --directory outputs/astro-correspondence-comparison/viewer
```

Train mode reuses the already built matching dataset. `all`, `retarget` and `view`
pipeline stages are outside this experiment. Initial visual build failed before
sampling because inherited default `seq_key=dance1_subject2` did not match the
shipped single-file motion; configs explicitly set `seq_key=motion_actor_smplx`
and successful build logs replaced that failed attempt. No weakened settings,
reduced point counts, discarded cache, or CPU training fallback were used.

## Evaluation

| Static measure | Visual | Primitive |
| --- | ---: | ---: |
| Final logged weighted training loss | 0.001687 | 0.001703 |
| Weighted Chamfer term | 0.000126 | 0.000129 |
| Weighted repulsion / edge terms | 0.001385 / 0.000176 | 0.001404 / 0.000171 |
| Robot learned→projected error mean / p95 / max | 5.69 / 18.60 / 45.05mm | 6.78 / 19.90 / 46.74mm |
| Input samples→projected slots mean / p95 / max | 6.67 / 13.85 / 21.75mm | 6.19 / 13.19 / 20.48mm |
| Selected geoms / occupied projected geoms | 35 /32 | 55 /55 |
| Occupied projected bodies | 32 | 19 |
| Production binder | accepted | **rejected:470 buried slots** |

Loss values are normalized and weighted training terms from the final minibatch,
not physical units or semantic accuracy. Coverage is a nearest-distance statistic
on the sampled reference envelope; primitive statistics include rejected points.
It does not measure contacts, grasp suitability, foot slide, temporal smoothness,
joint limits, collision-free motion, task preservation, or dynamic feasibility.

Assertions confirm finite `(2,4096,3)` learned outputs, actual dataset arm policies,
matching names and target arrays, slot IDs0..4095, and bitwise-equal human mesh,
faces, samples, beta vector, human learned slots, sort order, and template graph
across arms. Human learned slots match ordered input samples within60nm; exact
human projection error mean4.78nm and max89.11nm. Robot production bindings are
compared with the same projection used in the preview. Visual uses existing
nearest-vertex-candidate projection; primitive uses the patched globally complete
triangle projection, then exposure rejection. No validation was bypassed.

The primitive independent audit uses native MuJoCo opposite-direction ray tests
inside analytically shrunken primitives, matching the declared10µm margin and
excluding each point's own inscribed primitive. It independently confirms470
buried points and36 cross-body points. The diagnostic NPZ retains the tentative
face/geom/body ownership and invalid mask, but no accepted primitive production
binding is exported. This is the pre-existing off-surface binding limitation
predicted in the geometry record, now observed on learned slots.

[results.json](results.json) contains complete source-segment→robot-body tables,
body coverage, invalid slot IDs, and projection/coverage measures.
Source labels use existing UMR SMPL-X surface segmentation. Both arms have zero
left/right-opposite body assignments under a simple prefix check; this is only a
coarse audit statistic, not proof of semantic correctness. For example, of414
human head-labelled slots, visual assigns308 to torso_link and87 to head_link;
primitive assigns281 to waist_roll_link and127 to head_link. Many upper-arm or
shoulder-labelled slots also map to torso proxies. These assignments merit
inspection; low Chamfer does not settle anatomical or contact quality.

## Inspection artifacts and observations

Open [local interactive inspector](http://127.0.0.1:8766) while its server is
running, or restart it with the command above. Three.js0.165.0 is fetched from
jsDelivr as in the upstream AdaPT viewer; internet access is needed for rendering.
The AdaPT exporter was inspected but requires racket-specific metadata, so this
experiment adapts its point-cloud approach with paired-slot selection. The
viewer offers both arm identities, raw learned versus projected robot points,
linked selection by slot ID/click, source segment filtering, sparse pair lines,
and input surface overlay. Rejected primitive projections are red and the whole
primitive binding failure is prominently labelled. Red raw learned points mean
their later projected location is rejected. Matched colors derive from the fixed
human position. Exact selected body names and projection errors are displayed.

Static preview:
`outputs/astro-correspondence-comparison/pairings-comparison.png`.
It shows front/rear orthographic point projections (all points shown, no hidden
surface removal) with every64th pair linked. It was visually inspected for layout,
paired order, geometry distinction and rejected-point marking. Interactive orbit
is needed to inspect depth; point splats are not a watertight surface rendering.
The interactive palette is fixed from human positions but is not numerically
identical to the static plot's palette. Both preserve matching pair colors.

Dataset NPZs preserve the canonical meshes. Learned-slot NPZs and final checkpoints
are in each arm's `train/`; `inspected_pairings.npz` additionally preserves raw
learned robot points, tentative projections, slot IDs, body/geom owners, source
labels and rejection mask. `viewer/pairings.json` is a rounded display export;
use NPZs for numerical work. Interactive rendering, both arm selections and rejection status were also checked
in the local browser; the canvas was darkened and enlarged after a contrast check.
`training-metrics.json` preserves all logged epochs and exact train commands.

Source scripts/configs and summaries are in this
experiment; large generated artifacts remain ignored under outputs.

Training is complete and inspection is the stopping point. The primitive binding
needs a separate reviewed exterior-projection design before any future retargeting.
Neither correspondence's motion/contact quality has been established.
