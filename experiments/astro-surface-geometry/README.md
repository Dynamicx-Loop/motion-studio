# Experiment: Astro visual meshes versus collision primitive surfaces

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-22 / Codex, delegated geometry setup.

## Objective

Set up independent visual and primitive arms and pass static sampling/binding
checks before considering correspondence training or retargeting. Neither training
nor retargeting was started. No motion, SMPL-X template, or correspondence model
was needed or loaded. Geometry validation is complete within the limits below.

## Provenance

- UMR source and isolated clone: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
  Source: [UMR](https://github.com/hanyang9/UMR). Its MIT license/notices remain.
- The independent clone is
  `/data/workspace/motion_studio/externals/UMR-astro-surface-experiment`.
  It has its own Git metadata and copied objects; it does not share a worktree or
  mutate `/data/workspace/motion_studio/externals/UMR`. No commit, baseline advance,
  reset, package installation, or Wendy checkout change was made.
- Uncommitted UMR changes, including the new module and tests, are preserved in
  [umr-surface-geometry.patch](umr-surface-geometry.patch). The patch was checked
  with `git apply --check` against the unchanged source repository. SHA256:
  `e2cc109b3aa8125034391fde0ae2f66a02ea660a6900ce727351ea1579ca000a`.
- Astro asset repository HEAD:
  `d6a0ee64526c3eaaa7e7beea11bb5ead9d3f44b5`.
  Canonical XML:
  `/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_29dof/astro_p2_29dof.xml`.
  SHA256: `89f179ea9fb51ff53a9a1d3fa9cef6049f843e0e3ad21a886677e3a5341767f7`.
  Canonical config `/data/workspace/motion_studio/configs/umr/astro_p2_29dof.json`
  SHA256: `4e0f69aff52297fbc10c6440ebdec28a2fe6296e03e3127c765a21f3a676a6cb`.
  Both hashes were checked before/after validation. Neither file changed.
- Input clip: none. The only motion path reserved in the isolated configs is the
  shipped `externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`;
  it was not read, copied, converted, or evaluated. Existing asset/data terms apply;
  no robot mesh, human model, or motion assets are redistributed here.
- Python: original `externals/UMR/.venv/bin/python`, Python 3.12.3, NumPy 1.26.4,
  SciPy 1.17.1, trimesh 5.1.1, MuJoCo 3.3.7, Torch 2.7.1+cu128.
  Geometry checks used CPU, with no GPU job. Static plotting used system Python
  with NumPy 1.26.4 / Matplotlib 3.6.3; the UMR environment was left unchanged.
- Units: metres/radians. Canonical T-pose has left/right shoulder roll +/−π/2
  and both elbows +π/2. Array rows are points `(N,3)`; sample faces retain compiled
  geom/body ordering. Robot root axes are forward/left/up; SMPL sampling coordinates
  are left/up/forward. Both conversion directions were checked. No motion FPS,
  temporal resampling, or quaternion conversion applies to this static experiment.

## Reproduction

Working directory: `/data/workspace/motion_studio`.

Existing isolation was created with:

```sh
git clone --no-hardlinks externals/UMR externals/UMR-astro-surface-experiment
```

To recreate a missing isolated checkout, use the above clone and then apply the
saved patch **inside that new clone**. Do not apply it to the canonical checkout.
Do not clone over an existing directory or discard existing local edits.

The supported geometry-only entry point is:

```sh
externals/UMR/.venv/bin/python -m unittest discover -s externals/UMR-astro-surface-experiment/tests -v
externals/UMR/.venv/bin/python experiments/astro-surface-geometry/validate.py > outputs/astro-surface-geometry/validation.log 2>&1
MPLCONFIGDIR=/tmp/astro-surface-matplotlib python3 experiments/astro-surface-geometry/plot_clouds.py
git -C externals/UMR-astro-surface-experiment diff --check
git -C externals/UMR apply --check /data/workspace/motion_studio/experiments/astro-surface-geometry/umr-surface-geometry.patch
```

[visual.json](visual.json) uses `auto`; [primitive.json](primitive.json) uses
`collision_primitives`. Both retain the canonical MJCF and T-pose. Each reserves
separate dataset, training, and future retarget paths beneath
`outputs/astro-surface-geometry/{visual,primitive}/`, with `slots=null`. Those
pipeline outputs were not created. These configs contain metadata only; they do
not disable the upstream training/retarget pipeline. Run `validate.py` for the
currently authorized geometry stage.

The validator uses seeds 9000/9001/9002 at 512 points, plus seed 9000 at 4,096
primitive points; both displayed surfaces use 4,096 points, seed 9000. All use
oversample ratio 8, curvature weight 0, curvature power 1, and existing `first_hit`
exterior filtering. The primitive arm additionally rejects points strictly inside
another selected analytic primitive with a 10 µm margin before FPS. Too few
survivors raise an error. The analytic test excludes each point's generating geom
because curved triangles are inscribed in their own primitive.

Outputs are under `/data/workspace/motion_studio/outputs/astro-surface-geometry/`:
`metrics.json`, `validation.log`, `baseline-visual.npz`, `visual-4096.npz`,
`primitive-4096.npz`, `clouds.npz`, and `surface-comparison.png`.
[results.json](results.json) preserves the measured metrics and per-geom coverage
outside ignored outputs. Re-running validation updates ignored outputs; the saved
results file is this run's record.

## Evaluation

| Geometry gate | Measured result |
| --- | --- |
| Explicit visual selection | 35 meshes; 191,377 vertices; 393,798 triangles |
| Explicit primitive selection | 55 group-3 collision-enabled primitives; excludes the two group-1 hand spheres |
| Primitive triangulation | 18,350 vertices; 32,616 triangles after removing 2,016 pole degeneracies |
| Winding / degeneracy | 0 nonoutward / 0 degenerate primitive faces |
| Raw area sample interior audit | 6,693/20,000 (33.465%) inside another primitive; 614 across bodies |
| Final primitive sample interior audit | 0/512 for each of three seeds; 0/4,096 at seed 9000 |
| Primitive point rebinding | Maximum 31.94 nm; tolerance 100 nm; 0 changed body owners |
| Geom identity ambiguity | 11/4,096 coincident foot-surface ties; same body, displacement below 1.2 nm |
| Coverage | All 55 selected geoms and all 19 represented bodies receive samples at 4,096 points |
| Frame / entry point agreement | SMPL-frame and root-frame sampling equivalent; single/batch bindings identical |
| Owner motion | Independent original-geom transport after synthetic shoulder/hip offsets agrees within 100 nm |
| Default visual regression | Vertices, faces, 512 samples/face IDs, geom IDs, local positions/normals all bitwise identical to original UMR |
| Focused regressions | 7 tests pass, including exhaustive projection reference, small triangles, invalid input, and rejection of buried bindings |

The independent interior audit uses native MuJoCo primitive ray intersections on
shapes shrunk by the margin: for convex primitives, an interior point has hits in
both opposite directions. It does not reuse the production NumPy containment
implementation. Normals are checked against centered convex primitive centroids,
and binding normals have unit length. Per-point foot tie source/target names are
recorded in `results.json`; they are toe/heel/bridge proxies sharing the same foot
body, so their kinematic ownership is unchanged.

Indicative CPU timings for the final run are in `results.json`; they are not a
controlled A/B speed benchmark. No contacts, foot slip, joint limits, temporal
smoothness, physical simulation, or retargeting fidelity were evaluated.

## Observations and next step

The patch wires the explicit policy from the shared pipeline into dataset sampling
and uses the same selector in single/batch binding. It corrects ring winding and
removes zero-area pole triangles. The primitive binder uses globally complete
centroid-radius candidates and a projection based on plane/segment distances.
It leaves default visual binding on its existing code path.

The original nearest-vertex shortcut fails on a coarse large triangle even when
the query lies on it. A second reproduced issue was trimesh 5.1.1's absolute
region tolerance: on a 1 mm triangle, the point `(20 µm,20 µm,0)` projects 20 µm
to an edge. The experimental projector fixes both errors; the small-triangle
regression was observed failing before the fix.

The static plot shows the intended broader, smoother proxy envelope and altered
hand/foot detail. This is a visual observation, not evidence of motion quality.
The proxy remains a triangulated approximation, not an exact analytic union
surface. Group 3 is Astro's convention, not a universal MuJoCo collision rule.

Passing point rebinding is a geometry gate only. No learned correspondence was
trained or tested. For an arbitrary reconstructed off-surface point, the nearest
triangle can still lie on a buried surface; primitive binding explicitly rejects
that case. It does not search Boolean-union intersection curves for an alternative
exterior point. This behavior needs inspection before any later learned-slot work.
The exposure filter is reference-pose only and does not establish absence of
interpenetration in later poses. Keep the canonical physical model unchanged.

No global cache fingerprint enforcement was added to UMR: this experiment prevents
accidental cache reuse through separate arm paths, null explicit slots, and saved
policy metadata. Existing cache compatibility outside these paths remains a
limitation. Other source-specific builders (character/AdaPT) were not expanded or
validated; this work targets the shared Astro/SMPL-X/HiPHI dataset route and its
single/batch robot binding functions. Geometry-only validation never invokes the
human dataset builder or pipeline main function.
