# UMR preliminary motion: G1 versus Astro Dex3-1

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-23 / Codex. Offline retargeting explicitly authorized.
No physical execution or deployment.

## Objective and protocol

Inspect the whole UMR workflow on the actual shipped HiPHI SMPL-X get-up clip,
using the latest local Astro 43-hinge variant with two three-finger Dex3-1 hands
and the shipped G1 29-hinge model. Preserve a matched spine1 comparison and a
matched bbox50 comparison. The default viewer also presents G1 spine1 / Astro
bbox50 as **per-robot static-evidence selections**, chosen before motion results:
G1 spine1 had stronger torso/hip/thigh correspondence; Astro bbox50 removed
static knee crossings and improved those regions. Neither is a universal best.
No objective, head label, or residual was removed; no post-hoc solver tuning.

Smoke v1 retains 360 poses from the first 12 seconds. Full v2 uses frames
`0:5468:3`: 1,823 poses, frame IDs 0…5466, FPS 30.0003. Original was 5,468 frames
at 90.0009 Hz. Uniform decimation keeps every third frame, with no interpolation
or antialias filter; the final original frame 5467 is omitted. Both robots and
both centering controls use identical frame IDs and timing. No input was edited.

BONES-SEED is blocked on actual gated motion/shape/rig inputs: see
[BONES-SEED.md](BONES-SEED.md). No SOMA motion result or cross-representation
conclusion is claimed; public SOMA static templates are not substituted.

## Provenance and contracts

[provenance.json](provenance.json) hashes configs, source, copied datasets/slots,
robot assets, output trajectories and current tracked UMR/menagerie patches.
UMR baseline is d1cdaedaf67a827198da71c5fa831f48b2e51f91; runtime uses the existing
isolated surface-geometry patch, not a changed checkout. Menagerie local revision
1316cac090144c9891453a53b8336e8374c96196 contains the sample Dex3-1 hand mount.
Its geometry is a documented adapter assumption, not validated hardware geometry.
Body model/dataset/mesh licenses remain separate; local outputs are not published.

The exact HiPHI actor template `smplx_neutral_betas_52fa48a138` matches the cached
source slots; reuse-across-betas is disabled. Existing completed 500-epoch seed0
4096-slot bindings were copied, not retrained. New Astro triangles/bind pose and
production projection checks are captured in copied `static-hands-*` records;
G1 records remain in `experiments/soma-correspondence-audit`. Source slot mesh
binding errors round to zero in logs. All four solves bind 4096 robot slots;
selected segment contact subset is 456 slots. Production nearest-vertex-k24
projection remains in use; full-triangle static sensitivity is evidence only.
Astro has 51 selected visual mesh geoms and 43 hinge values; fingers start at
vendor zero/open pose. Shoulder rolls are +pi/2,-pi/2 and both elbows +pi/2.

Units: metres/radians. Source uses Y up; solver converts (x,y,z)→(x,-z,y), Z up.
Robot qpos is xyz + wxyz free-root quaternion + named scalar hinges. Joint order
is saved in each trajectory and results.json, not assumed body-then-fingers.
Astro nq=50/nv=49; G1 nq=36/nv=35. Source fingers are zeroed by baseline settings;
this does not establish finger-identity transfer or grasp quality. Each robot
uses its slot-derived height scale. Source ground alignment is none, ground z=0,
no objects/support furniture. Scene meshes are visual only, collision primitives
deferred; self-penetration constraints are disabled.

Solver configuration is frozen in four JSON files: sequential warm start,
15 initial-pose iterations, 1 iteration/frame, step limit0.15, global step0.4,
segment surface/normal costs, ground/self-contact map costs, all-slot hard ground
constraint, then LQR smoothing. G1's supplied joint-limit overrides are retained.
These are finite-iteration kinematic solves, not convergence or dynamic guarantees.
Generated floating MJCF sidecars are an upstream behavior beside original assets;
original XML/STL inputs remain unchanged, and generated model text is copied
into each output arm with its base path recorded.

## Reproduction and artifacts

The original `run.py`, `export.py`, `source.py`, `tracking.py` and
`provenance.py` use fixed historical output paths. **Do not run them against this
frozen cohort**; copying the viewer into its old output directory also writes to
historical evidence. There is no equivalent fresh-output runner for this cohort.
[Canonical UMR preparation](../../docs/umr-canonical-preparation.md) creates a new,
prepared-only cohort, not a rerun of these four solves or their viewer. A future
reproduction needs separately validated fresh configurations and output paths.

The existing viewer can be served read-only from the workspace root:

```sh
python3 -m http.server 8772 --bind 127.0.0.1 --directory outputs/umr-motion-preliminary-v2/viewer
```

The recorded `run.py` executed arms serially. GPU was idle of compute
jobs before starting. Exact subprocess commands, exit codes, elapsed time are in
[runs.json](runs.json); `/usr/bin/time -v` CPU RSS and complete solver diagnostics
are in output logs. GPU total memory spot sample was2367MiB; peak GPU memory was
not instrumented. Timing includes startup, geometry, source evaluation and solve;
it is not a controlled speed benchmark. No dependency installation was needed.

## Evaluation definitions and limits

[results.json](results.json) evaluates exported, filtered qpos: finite values,
quaternion normalization, named configured limit margins (1e-6rad tolerance),
finite-difference hinge velocity/acceleration, root net displacement/path length,
and exact minimum visual-mesh vertex height via convex-hull extrema. Inferred
stance uses ankle-body height within30mm of that foot's minimum in this clip;
horizontal speed/path counts consecutive inferred-stance frames. This heuristic
is not contact metadata and is particularly limited during kneeling/get-up.
Root-relative wrist/ankle anatomical errors compare scaled SMPL-X joint centers
with robot body origins; offsets/morphology contribute, so they are explicitly
proxies rather than learned surface residuals. Full per-segment post-filter
objective residuals and reliable self-collision were not instrumented.

UMR log cost is the aggregate **pre-LQR** solver cost, not residual of exported
poses. One iteration/frame does not establish convergence. Low slot penetration
constraints do not guarantee whole-mesh clearance or post-filter feasibility.
No balance, support force, torque, actuator velocity limit, dynamics, grasp or
hardware safety claim follows from playback. One motion/seed and decimated FPS
limit generality; representation effects cannot be inferred without SOMA motion.

## Measured results

All four full outputs are finite, with zero configured joint-limit violations at
1e-6 rad tolerance. Some joints reach their bounds (minimum margin0).

| Arm | Worst mesh penetration mm | Joint speed p95 rad/s | Joint acceleration p95 rad/s² | Solver mean cost (pre-filter) | Wall s |
| --- | ---: | ---: | ---: | ---: | ---: |
| smplx_astro_bbox50 | 37.05 | 1.889 | 21.17 | 0.091196 | 51.0 |
| smplx_astro_spine1 | 28.14 | 1.803 | 20.96 | 0.129721 | 50.5 |
| smplx_g1_bbox50 | 18.02 | 2.241 | 24.24 | 0.102672 | 48.5 |
| smplx_g1_spine1 | 14.02 | 2.074 | 23.38 | 0.057813 | 49.4 |

The static-selected Astro bbox50 improves its ankle anatomical proxy over spine1,
but worsens worst visual floor penetration (37 versus28mm). G1 spine1 has lower
pre-filter cost and penetration than its bbox50 control. These are different
embodiments and objectives with different geometry/scale, not a universal quality
ranking. Inferred-stance mean horizontal ankle speed ranges0.063–0.138m/s across
side/arm combinations; the heuristic includes real repositioning and cannot be
reported as measured slip alone. Full limb proxy, root and smoothness summaries
remain in results.json.

Concurrent menagerie edits modify only group3 collision geometry.
[geometry-compatibility.json](geometry-compatibility.json) verifies all51 mesh
hashes and exact XML equality after excluding those collision geoms. They were
not edited by this experiment and do not enter selected visual meshes or active
self-collision constraints. Bindings were rebuilt on each current model, avoiding
stale numeric geom IDs. The newer experimental wrist calibration in
`experiments/astro-hand-wrist-correction` is a static candidate intervention; it
is not silently substituted for the baseline learned bindings in this experiment.

Viewer: [full synchronized playback](http://127.0.0.1:8772/). It uses native human
height and each robot's native size, source/G1/Astro fixed horizontal display
offsets, initial-root horizontal centering, and no vertical adjustment or
per-frame alignment. The comparison selector exposes both matched controls.
Original source orientation is restored for display by inverse Z-up conversion.

## Visual review and validation

Browser review checked native-size source/G1/Astro at standing, initial crouch
and floor-supported phases (including source frame4515, about50.17s), with all
three selector settings. Broad lowering/rising behavior is recognizable, while
arm support pose, knee/hip configuration and foot clearance differ. This is a
qualitative observation, not a support/contact or dynamic feasibility finding.
The viewer is paused at a floor-supported pose for inspection.

Validation:232 recorded input/output hashes, all four trajectory shapes/frame IDs,
finite qpos, all mesh references and transform binary sizes, Python compilation,
local documentation links and whitespace. No upstream source edits were made.
All new hand slots use the hand-variant geometry; historical reports remain intact.
