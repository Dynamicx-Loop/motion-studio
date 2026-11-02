# Experiment: Astro with Dex3-1 hands, static correspondence

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-23 / Codex; primary-source head/hand research delegated to a background research agent.

## Objective and outcome

Test whether adding the latest Astro hand surfaces resolves the earlier static
correspondence failures. **Four new 500-epoch runs are complete**, using the same
SMPL-X/HiPHI and SOMA sources and spine1/bbox50 centering controls. Four historical
Astro no-hand-mesh arms and four unchanged G1 arms are comparison controls.
No retargeting, solver trajectory, rollout, hardware execution, or new collision-
primitive experiment is authorized or performed.

Adding the hands **does not resolve the head mismatch**. Forearm changes are mixed.
Broad hand-zone precision is 99–100%, but only 24–47% of human hand slots actually
bind to the new same-side palm/finger meshes. The broad zone includes distal wrist
housing and must not be interpreted as successful finger correspondence.

The [fixed-head research note](../../references/umr-fixed-head-and-dex3-hands.md)
confirms no neck articulation on either robot. Head and torso share rigid motion,
but separate surface points have different position Jacobians and may supply
complementary constraints. No head labels, owners, selections or weights were
merged or changed. The user confirmed that their neck question meant **head**
binding; new-hand correspondence is assessed separately here.

## Asset and environment provenance

- UMR baseline and isolated experiment checkout:
  `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; existing experimental patch unchanged.
  [Preparation record](preparation.json) captures the current full tracked diff
  SHA256 separately from the historical exported patch file. No UMR edits.
- Menagerie local HEAD: `1316cac090144c9891453a53b8336e8374c96196`.
  Read-only `git ls-remote origin HEAD` returned
  `dfbf8f13ac892dfb8b4b3f69a791e67ebc28d6be`, an ancestor of the local hand commit.
  No fetch/reset/checkout was needed. All local untracked files remain intact.
- New model:
  `/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml`.
  Original `astro_p2_29dof` remains unchanged. New versioned static config:
  [astro_p2_43dof_dex3_1-static-v1.json](../../configs/umr/astro_p2_43dof_dex3_1-static-v1.json).
- Independently loaded in the existing MuJoCo 3.3.7 runtime: `nq=50`, `nv=49`,
  43 scalar hinges, 14 finger hinges, no neck hinges, `nu=0`. Named qpos addresses
  and limits are captured; no assumption that native array order matches body-
  then-hands application order. The G1 control has 29 hinges and no finger hinges.
- Pose: original shoulder rolls left +π/2, right −π/2; both elbows +π/2;
  other 25 body hinges zero; all 14 hand hinges zero (vendor open pose).
  All coordinates satisfy model limits. All 29 body anchors match the original
  model within 1e-8 m; copied body meshes match byte-for-byte. Original collected
  triangles match the historical dataset (faces exact, vertices within 200 nm).
- Visual-only automatic policy selects 51 mesh geoms, including 16 Dex3 meshes.
  No primitive surfaces enter the new datasets. The new mesh union has 354241
  vertices / 719466 triangles. [Asset inspection](asset-inspection.json) records
  selected geom→body→mesh identities and hashes every variant asset.
- Hands come from official Unitree ROS revision
  `5994d4faef0a9cadd3287f8de0199a67eeb2a259`, with original license/source records
  retained beside the model. The Astro mount is an explicitly documented sample
  adapter, not validated hardware geometry. Asset/model terms remain separate;
  derived meshes and checkpoints stay in local ignored outputs.
- Runtime reused: Python 3.12.3, Torch 2.7.1+cu128, NumPy 1.26.4, MuJoCo 3.3.7,
  and prior UMR dependencies. Host RTX 5070 Laptop access was checked before
  sequential training; only the desktop process was initially using GPU memory.
  No installation or driver changes. [Provenance](provenance.json) records versions,
  commands, elapsed times, final losses and input/output hashes.

## Protocol and controls

Each new arm copies its exact historical human mesh, samples, face identities,
shape parameters and centering offsets. The new target surface is sampled **once**
with the original sampler seed9000,4096 slots,oversample8,curvature0,first-hit exterior
policy; those target arrays are identical across all four new arms. Human source
sampler seed1000 is inherited without resampling. Source centering remains an
identical-sample translation within each source. Old versus new target samples
are not pointwise identical: global area sampling/FPS changes with the new surface.
Thus this is a complete pipeline comparison after a surface change, not a
pointwise hand-only perturbation or a multiple-seed causal estimate.

Unchanged training: seed0,500 epochs,batch1,fixed template,robot2smpl_only,
per-sample-height normalization,AdamW lr0.001 cosine→0.00001,Chamfer1,
repulsion0.002/k8/radius0.035,edge0.4/geodesic32,residual0,noise0.002,
dropout0,no resampling. Human template order, graph and output slots are verified
bitwise equal to the corresponding historical run. Human LBS/labels do not supervise
correspondence training. All merged configs are retained.

SMPL-X uses only the static neutral actor shape in the original HiPHI
`Getting_up-get_up_0004/motion_actor_smplx.npz`; SOMA uses the original official
public neutral template/overlay. Sources remain different in shape, proportions
and arm pose. The previous [source comparison](../soma-correspondence-audit/README.md)
contains their hashes, licenses and exact construction. Robot root coordinates
are `(forward,left,up)`, source coordinates `(left,up,forward)`, metres/radians;
Astro target center stays `body:pelvis`, G1 stays `body:waist_yaw_link`.
No temporal sampling, trajectory quaternion conversion or motion data is used.

## Measured results

Head/face excludes neck; SMPL-X denominator353, SOMA320. Crossings are canonical
axis-aligned joint-plane distances >20mm, not motion errors. Entries show
**old Astro → Astro with hands**; G1 head/face→torso remains0 in all four controls.

| Source / center | Head/face→torso | Thigh below knee L/R | Forearm proximal to elbow L/R |
| --- | ---: | --- | --- |
| SMPL-X spine1 | 250/353 →249/353 (70.8→70.5%) | 106/94 →106/95 | 43/42 →42/38 |
| SMPL-X bbox50 | 152/353 →154/353 (43.1→43.6%) | 0/0 →0/0 | 49/44 →46/46 |
| SOMA spine1 | 234/320 →235/320 (73.1→73.4%) | 77/62 →77/63 | 23/26 →21/25 |
| SOMA bbox50 | 109/320 →124/320 (34.1→38.8%) | 0/0 →0/0 | 27/28 →28/31 |

Head-shell assignments are88/353,198/353,55/320,196/320 in the same order.
Some spine1 points reach sensors/shoulders; the complete distributions, precision,
coverage and high-confidence subsets remain in [results.json](results.json),
[common-region CSV](common-per-segment.csv) and [native19 CSV](per-segment.csv).
The new hand geometry does not materially alter the head/torso kinematic structure.

| Source / center | Source hand slots L/R | Actual same-side Dex3 mesh L/R | Of those, finger mesh L/R | Broad hand-zone precision L/R |
| --- | --- | --- | --- | --- |
| SMPL-X spine1 | 99/98 | 32/41 | 9/14 | 100%/100% |
| SMPL-X bbox50 | 99/98 | 24/24 | 8/7 | 99.0%/100% |
| SOMA spine1 | 82/77 | 36/36 | 13/12 | 100%/100% |
| SOMA bbox50 | 82/77 | 24/23 | 7/6 | 100%/100% |

The remaining hand slots mostly land on wrist-yaw meshes. A source hand region
is not a finger identity; these counts do not establish thumb/index/middle matching
or finger motion transfer. [Hand diagnostics](hand-diagnostics.json) retain actual
mesh destinations and every source region assigned to new hand meshes.
Hand-zone coverage ≤20mm decreases in all eight side/source/center comparisons
(e.g. SMPL-X spine1 89.5/94.4%→77.8/78.6%). The new target reference set and surface
are larger/different, so coverage denominators change; this is not a held-out
surface-area statistic or an apples-to-apples missing-point count.

## Independent validation and limitations

The unchanged historical audit code computes common18/native19 diagnostics and
production nearest-vertex-candidate projections. A separate global-triangle
projector checks every16384 learned robot slots against the actual new triangles.
[Binding validation](binding-validation.json) retains both results; production
bindings remain authoritative for the report, with exact projection only a
sensitivity check. All knee/elbow crossing counts match. Full search changes
head/face→torso from249→250 for SMPL-X spine1 and235→237 for SOMA spine1;
both bbox50 counts stay unchanged. These small local projection differences do
not change the head-failure conclusion. All eight actual hand-mesh counts also
match full search: [hand projection sensitivity](hand-projection-sensitivity.json).
No correction is silently substituted.

The first attempt stopped before optimization because copied dataset metadata
still named the old robot. It produced no trained result. `custom_robot_name`, XML,
and all43 qpos names/values were corrected; before/after hashes and failed logs
are retained. `prepare.py` now writes these fields correctly on fresh preparation.
The inherited unused bbox_center_ratio scalar remains0.45 as in the historical
copy; explicit `center_modes`, source offsets and resolved config define bbox50.
Trimesh emits texture-color NaN warnings while loading; coordinates, slots and
reported numerical results are finite and geometry equality checks pass.

Only one training seed and one open finger pose were tested. The experiment does
not isolate target resampling variance, morphology, arm pose, relative frame choice,
or finger pose. The head hypothesis is therefore **not solved by adding hands**;
head objective simplification remains an explicit future decision requiring
separate residual/weight ablations. Collision experiments are deferred. Motion,
contacts, dynamics, joint-limit behavior, self-collision, grasp quality and hardware
feasibility remain untested.

## Reproduction and inspection

From `/data/workspace/motion_studio`, use a fresh version/output destination for a
new run. Preparation and training refuse existing completed artifacts.

```sh
externals/UMR/.venv/bin/python experiments/astro-hands-correspondence/prepare.py
externals/UMR/.venv/bin/python experiments/astro-hands-correspondence/run_correspondence.py
externals/UMR/.venv/bin/python experiments/astro-hands-correspondence/audit.py
MPLCONFIGDIR=/tmp/astro-hands-mpl python3 experiments/astro-hands-correspondence/plot_evidence.py
externals/UMR/.venv/bin/python experiments/astro-hands-correspondence/verify_and_record.py
python3 experiments/umr-binding-report/build_report.py
python3 experiments/umr-binding-report/verify_report.py
```

The integrated [bilingual report](http://127.0.0.1:8770/?lang=en#hands) preserves
all earlier comparisons and adds seven-row actual-triangle figures including hands,
closeups, quantitative old/new/G1 comparisons and a new-hand mesh inspector.
One English image per figure is shared by both languages. Saved data and exact
commands are local; the optional inspector loads the existing Three.js CDN.
