# Fresh G1 binding and motion comparison

Date / author: 2026-11-02 / Codex, requested by the project owner.

Follow-up on 2026-11-02 found the shared uniform surface-fit file locally and
verified it against official Kimodo bytes. The SOMA BVH already carries a uniform
skeleton; the original run used a generic neutral surface because UMR's path and
asset discovery did not select the uniform fitted route. See the
[SOMA investigation correction](../umr-baseline-g1-somax-20261102/README.md#follow-up-correction-uniform-skeleton-and-available-surface-fit).
The measurements below and immutable browser report still describe the original
generic-surface control. A fitted rerun has not been performed by this investigation.

## Objective and cohort

Inspect the human/robot segment bindings for each human representation, inspect
each source clip against its retargeted G1 motion, and measure how consistently
the two learned mappings label the same robot surface.

This is a fresh descriptive comparison of two distinct cohorts:

- [SMPL-X official-default reproduction](../umr-baseline-g1-smplx-20261102/README.md):
  bundled HiPHI `Getting_up-get_up_0004`, actor-shape neutral SMPL-X, complete
  official G1 training and motion route. This is the generic pipeline's
  actor-shape template route, not the newer HiPHI wrapper's shared beta-zero
  correspondence route.
- [SOMA-X generic control](../umr-baseline-g1-somax-20261102/README.md):
  BONES-SEED uniform `210531/jump_and_land_light_001__A001.bvh`, native generic
  neutral SOMA bind/T-pose mesh and BVH/LBS reconstruction. The dataset-specific
  uniform fitted shape is unavailable. This control does not reproduce that
  missing fitted MHR/SOMA embodiment.

Both select the pinned bundled official 29-DoF G1 preset, including its T-pose,
waist-yaw centering, limits and solver defaults. The motion and human shape differ
between cohorts. Their quality differences cannot be attributed to human model
choice alone. No legacy result or upstream source is changed by this evaluation.

## Provenance and independent runtime

UMR revision: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`. Run-local inputs,
asset/model terms, complete commands, environments and per-stage preservation
receipts belong to the two linked run records. This comparison invokes no
training, retargeting or simulation stepping.

The evaluator uses the existing `externals/UMR/.venv/bin/python` and its installed
NumPy, SciPy and MuJoCo. It reads `dataset.npz`, `motion.npz`, `resolved.json` and
each standalone inspection export. The derived JSON records SHA-256 hashes of
those files, every consumed human replay chunk, robot transforms and the exact
evaluator source. All consumed artifact hashes are checked again after analysis.
Raw source/model weights remain in their original local locations; the
comparison does not copy or redistribute them.

Fresh paths:

- `outputs/umr-baseline-g1-smplx-20261102/`
- `outputs/umr-baseline-g1-smplx-20261102-inspection/`
- `outputs/umr-baseline-g1-somax-20261102/`
- `outputs/umr-baseline-g1-somax-20261102-inspection-04/`
- `outputs/umr-baseline-g1-comparison-20261102-04/`

## Reproduction and viewing

Run from `/data/workspace/motion_studio` after both run/inspection exports finish:

```sh
externals/UMR/.venv/bin/python -B \
  experiments/umr-baseline-g1-comparison-20261102/evaluate.py \
  --smplx-run outputs/umr-baseline-g1-smplx-20261102 \
  --somax-run outputs/umr-baseline-g1-somax-20261102 \
  --smplx-inspection outputs/umr-baseline-g1-smplx-20261102-inspection \
  --somax-inspection outputs/umr-baseline-g1-somax-20261102-inspection-04 \
  --output outputs/umr-baseline-g1-comparison-20261102-04
```

The destination must be fresh. Use another suffix for a repeat. Inputs stay
read-only. To view the comparison and both interactive inspectors:

```sh
python3 -B -m http.server 8873 --bind 127.0.0.1 --directory outputs
```

Open [comparison](http://127.0.0.1:8873/umr-baseline-g1-comparison-20261102-04/),
[SMPL-X source/G1](http://127.0.0.1:8873/umr-baseline-g1-smplx-20261102-inspection/),
or [SOMA-X source/G1](http://127.0.0.1:8873/umr-baseline-g1-somax-20261102-inspection-04/).
The inspectors retain full saved frame IDs/FPS; their display decoders and
quantization validation are documented in the owning run records. Playback is
kinematic reconstruction of saved motion, not a physics rollout.

## Metric definitions and supported claims

**Robot identity.** Compare selected compiled geometry, mesh topology/order,
kinematic arrays, joint ranges, mass/inertia arrays, qpos0, and body/joint/geometry
names/order exactly. Compare the saved robot reference vertices, faces and
sample points exactly. Compare resolved robot settings after excluding the
run-specific XML pathname. These bounded checks do not certify whole-model or
simulator equivalence.

**Segment bindings.** Both use native
`smplx_55_to_19_upper_arm_v1`. The labels describe the source human surface
segments. Target body/mesh ownership describes robot attachment; these are
different concepts. Native SOMA labels are transferred through the pinned
SMPL-X-to-SOMA surface correspondence, not inferred from the robot body names.
Count each segment and report its robot body ownership distribution, target
surface projection distance, and independent robot-sample coverage distance.
The fixed-head G1 has no matching articulated human neck; a head label can
legitimately belong to the robot's torso body. Segment presence is coverage,
not evidence of anatomical accuracy.

**Cross-human robot consistency.** The robot reference meshes must be exactly
equal. At each of the same 4,096 saved uniform robot surface samples, assign the
nearest projected target binding's source segment independently for each run.
Report label agreement, per-segment intersection-over-union and the complete
label confusion counts. The front-view SVG uses these identical probe locations.
Learned slot rows are never matched across separately trained humans. The SVG
is a two-dimensional projection with no depth occlusion, not a rendered surface
segmentation. These nearest-neighbor labels depend on learned binding density
and placement and are a diagnostic rather than a ground-truth annotation.

**Per-motion fidelity diagnostics.** Decode full source replay chunks and rigid
robot slot transforms. Coordinates are Y-up metres; robot native `[x,y,z]`
becomes `[y,z,x]`. Source reconstruction already includes each run's saved scale,
ground convention, shape, finger policy and exact frame IDs. Mean bound-slot
positions define each segment's surface centroid. Subtract each model's own
bound `hips` surface centroid and report Euclidean centroid discrepancy; retain
all rotations. Also report world-frame angles between corresponding named
segment-centroid vectors. Embodiment proportions and segment placement contribute
to both metrics: neither is anatomical correspondence ground truth. The aggregate excludes
the trivially zero anchored hips region and weights the other 18 segments
equally, avoiding torso slot density dominating the mean. SOMA skeleton Root
index 0 is static; its corrected inspection uses moving Hips index 1 as the
quantization/display anchor. This metric uses the bound hips region in both
embodiments and does not equate unlike skeleton root definitions.

**Limits and smoothness.** Report quaternion norm error, compiled and configured
joint-limit excess, and absolute adjacent scalar joint differences in radians.
The latter is a per-frame, clip-specific diagnostic; the different FPS must be
considered when comparing it.

**Floor/motion proxy.** For each bound foot region, compute the fifth percentile
of slot heights above the shared `y=0` floor on each frame. An adjacent-frame
interval is near the floor when both values are at most 2 cm. Report the fraction
of these intervals and the foot surface centroid's horizontal speed, separately
for source and robot. Report the fraction of frames below -5 mm. The source and
robot thresholds select separate interval sets. This does not identify support
contacts, contact forces or foot slip against known stationary contacts, and
does not evaluate the whole foot mesh, whole-body collisions or dynamic balance.

## Validation

An independent two-probe worked example verified that permuting learned slot
rows leaves spatial agreement unchanged, while swapping the spatial labels
changes agreement from 100% to 0%. A separate two-point, two-frame worked
trajectory placed the human and robot at different global origins but identical
relative poses: hips-centered discrepancy was zero, foot height was zero, and
both near-floor horizontal speeds were exactly 1 m/s at 10 Hz. The evaluator
byte-compiles. Full artifact hash preservation and real-run numerical results
are recorded below and in the small tracked comparison receipt.

[Browser validation](browser-validation.json) checked the final report, both
linked inspectors, SVG/asset HTTP responses, sampled beginning/middle/end frames,
reference poses, playback and a SOMA segment filter. No horizontal overflow or
application console errors appeared at 1400 by 950; only an unrelated favicon
404 occurred. This is sampled visual/interaction validation, not full-motion
quality certification.

## Results

All 28 bounded robot checks pass exactly. The two datasets have identical G1
reference geometry (192,938 vertices and 385,626 triangles), identical ordering,
and the same 4,096 robot samples. Both learned maps contain all 19 human segment
labels and attach to 33 robot bodies. Each has 4,096 paired learned slots.

| Measured diagnostic | SMPL-X official reproduction | SOMA generic control |
| --- | ---: | ---: |
| Frames / FPS | 5,468 / 90.0009003 | 1,165 / 120.004799 |
| Saved human scale | 0.7957032 | 0.7462310 |
| Mean target slot projection distance | 7.03 mm | 7.27 mm |
| Mean independent robot-probe coverage distance | 6.58 mm | 6.99 mm |
| Mean hips-centered segment discrepancy | 4.753 cm | 3.178 cm |
| P95 hips-centered segment discrepancy | 8.469 cm | 6.351 cm |
| Model + configured limit excess | 0 rad | 0 rad |
| P95 / maximum scalar-joint step | 0.024253 / 0.153127 rad/frame | 0.014285 / 0.245884 rad/frame |

The independently assigned source-segment labels agree on 3,604 of 4,096 common
robot probes (**87.9883%**). Highest region IoUs are head (95.74%), left foot
(92.26%) and right foot (90.53%). Lowest are rightUpperArm (56.94%), hips (63.27%),
rightArm (64.71%) and rightShoulder (67.02%). This localizes disagreements around
pelvis and arm/shoulder boundaries; it does not establish which assignment is
anatomically correct. Human head bindings attach mostly to the G1 head mesh
(SMPL-X 408/415; SOMA 371/384), whose rigid owner is `torso_link` in both runs.
Body ownership alone would hide that distinction.

Robot near-floor foot-centroid mean speeds are 0.115/0.130 m/s (left/right) in
the getting-up clip and 0.0388/0.0372 m/s in the jump/landing control. Source means
are 0.0587/0.0444 and 0.0111/0.0110 m/s respectively, on their independently
thresholded intervals. The measured robot values indicate near-floor motion
worth visual inspection, rather than certified slip. Neither robot foot proxy
falls below -5 mm. The generic SOMA source foot-height proxy does fall below
-5 mm for about 60%/83% of frames; that belongs to this uncalibrated generic
control and is not evidence about the missing fitted uniform body.

The final evaluation preserved all 416 consumed files and the exact evaluator
source. [evaluation-receipt.json](evaluation-receipt.json) retains the small
numerical evidence, full-measurement hash and evaluator hash. Complete body/mesh
ownership, per-segment direction/fidelity statistics, input hashes and the
common-probe SVG stay in the fresh output. The report links both full-motion
inspectors. Browser validation is recorded separately by the parent task.

Earlier comparison derivatives at the unsuffixed path and `-02`/`-03` are
retained as superseded intermediate diagnostics. The final `-04` derivative uses
the explicit named-Hips SOMA `-inspection-04` export and symmetric hips-surface
centering. The first two derivatives used inconsistent skeleton root definitions;
they must not be used for the reported fidelity comparison. The intermediate
`-03` corrected centering but predates the final inspector and frozen evaluator.

Matched motion, calibrated human shape, externally annotated contacts, collision
analysis and physics rollout remain necessary for stronger quality or dynamics
claims. The lower generic-control centroid discrepancy is not evidence that
SOMA retargeting is better than SMPL-X.
