# Experiment: one canonical Astro visual-surface baseline

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-23 / Codex.

## Objective

Refresh the latest Astro asset, rerun source/centering controls, and use one
immutable model across sampling, learned slots, projection, audit, calibration,
motion and report views. Offline retargeting is authorized. No hardware execution
or new collision-primitive comparison is included.

## Provenance and integration

Fetched `menagerie_x` origin. Local HEAD
`d2070956558ffbf9226dcf74017d40740724d8d8` contains the latest available Dex3-1
variant and is three commits ahead of fetched origin/main
`dfbf8f13ac892dfb8b4b3f69a791e67ebc28d6be`, its ancestor. No merge or reset was
needed. Tracked asset patch is empty; all untracked work remains intact. Exact
status and every copied file hash are in [canonical-asset.json](canonical-asset.json).
The snapshot copies tracked variant assets, retaining source records and licenses;
untracked generated trajectory sidecars are not canonical inputs.

The XML SHA-256 is
`c688a4177a1ff5ba07764f9e310bb62c33d24a47b193259922a55b6c5fe88c66`.
All current Astro static, calibration and motion configs use that same frozen XML
under `outputs/astro-canonical-static-v1/asset-snapshot/astro/`. G1 is separately
frozen as a comparison control. Live upstream drift is recorded at completion,
not incorporated into runs. The previous report/source is archived under
`outputs/umr-binding-report/history/pre-canonical-v3/` with file hashes.

UMR baseline and experiment checkout are pinned to
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`; the existing experimental patch is
preserved in `UMR-astro-surface-experiment.patch`. Full source hashes include
untracked runtime modules, so a tracked patch alone is not the reproducibility
record. Existing Python 3.12 / Torch 2.7.1+cu128 / MuJoCo 3.3.7 environment and
RTX 5070 Laptop GPU are reused. GPU jobs run serially; no dependency installation.

## Protocol

Four fresh Astro trainings: SMPL-X/HiPHI actor and public-neutral SOMA, each with
spine1/bbox50 source centering. Four G1 static slot controls are reused after
exact source/geometry/config checks; all G1 bindings and metrics are recomputed.
Within each source, original human meshes, samples, sample IDs, shape, slot order
and graph are retained. bbox50 is a translation of the same source samples.
SMPL-X and SOMA remain different identities, poses and topologies.

The Astro visual surface is sampled once with seed9000, 4096 points,
oversample8, curvature0 and first-hit exterior policy. The four target datasets
are identical. Training retains seed0,500epochs,batch1,robot2smpl_only,fixed
template,per_sample_height,AdamW lr0.001 cosine→0.00001,Chamfer1,
repulsion0.002/k8/radius0.035,edge0.4/geodesic32,noise0.002,no resampling.
Source labels and LBS do not supervise the training.

Named T-pose: shoulder rolls +pi/2 left and -pi/2 right, both elbows +pi/2;
other body hinges and all 14 finger hinges zero. All coordinates satisfy limits.
The latest fist keyframe is deliberately not selected for this matched control.
Model:43 hinges,nq50,nv49,nu0. There are no neck hinges. Fixed head ownership
does not establish redundant head/torso point objectives. No labels, source
points, normal residuals or segment weights were merged.

The new commit differs from 1316cac only in collision geoms and keyframes;
removing those XML elements yields equivalent definitions. Selected actual
visual triangles match historical data within200nm, faces exactly. 51 mesh geoms
include16 hand meshes,354241 vertices and719466 triangles. All face→geom→body→mesh
bindings and joint qpos/dof addresses are rebuilt. Collision primitives are
retained in the snapshot but excluded from selected visual surfaces.

Coordinates: human(left,up,forward), robot(forward,left,up), metres/radians.
Point-cloud origins remain Astro pelvis and G1 waist-yaw. No temporal resampling
occurs in this static stage. Inherited unused bbox ratio metadata is interpreted
through actual saved root offsets and configs, as in the historical source audit.

## Reproduction

The commands below document this historical cohort and may write to its fixed
paths. Do not run them against retained evidence; adapt every destination to a
fresh cohort before reuse.

From `/data/workspace/motion_studio`:

```sh
externals/UMR/.venv/bin/python experiments/astro-canonical-static-v1/prepare.py
externals/UMR/.venv/bin/python experiments/astro-canonical-static-v1/run_correspondence.py
externals/UMR/.venv/bin/python experiments/astro-canonical-static-v1/audit.py
python3 experiments/umr-binding-report/plot_canonical.py
```

Preparation and training refuse to overwrite inputs/checkpoints. To repeat from
scratch, use a new version directory and update its paths. Audits/plots can be
rebuilt from the saved outputs. Dataset and model terms apply separately; large
assets/checkpoints and derived geometry remain local ignored outputs.

## Measured results

Head/face excludes neck. Crossings are canonical planes >20mm, not motion errors.

| Source / center | Head/face→torso | Knee crossings L/R | Elbow crossings L/R | Actual hand L/R |
|---|---:|---:|---:|---:|
| smplx_astro_spine1 | 249/353 | 106 / 95 | 42 / 38 | 32 / 41 |
| smplx_astro_bbox50 | 154/353 | 0 / 0 | 46 / 46 | 24 / 24 |
| soma_astro_spine1 | 235/320 | 77 / 63 | 21 / 25 | 36 / 36 |
| soma_astro_bbox50 | 124/320 | 0 / 0 | 28 / 31 | 24 / 23 |

Fresh production mesh-destination distributions match the prior hand experiment
exactly. This is measured reproducibility with unchanged visual inputs, not
proof that future changes cannot affect correspondence. Head mismatch persists;
broad hand-zone precision still differs from actual palm/finger mesh membership.
G1 remains a useful head/knee control with other regional errors.

## Validation and limits

Production nearest-vertex-candidate bindings are retained in metrics. Independent
full-triangle projection checks each arm, saved separately in
[binding-validation.json](binding-validation.json). Numerical model IDs are never
copied from historical geoms. Source labels, precision versus sample coverage,
native19 versus common18 and rigid ownership are kept distinct.

One seed, one static pose, training-sample coverage and different source identities
limit generality. This stage does not establish dynamic or articulated hand
correspondence. See the sibling canonical wrist and motion experiments for actual
candidate and trajectory measurements. Figures use one English image set shared
by both report languages and retain six anatomical rows including shoulders and
hips. Interrupted render/audit processes were restarted; completed checkpoints
were retained rather than silently retrained or relabeled.

The user's SOMA-X path was checked and linked in both UMR checkouts; see
[soma-local-links.json](soma-local-links.json) and
[the setup note](../../docs/umr-soma-setup.md). Model availability does not supply
a BONES-SEED motion or actor shape. Source assets and original motions remain intact.
