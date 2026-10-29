# Experiment: static wrist-to-palm calibration with G1 control

Date / author: 2026-10-23 / Codex delegated investigation.

## Objective and diagnosis

Test whether an anatomically motivated, label-independent static landmark calibration
reduces source hand assignments to Astro wrist housing. Keep raw Astro and G1 controls;
apply the same rule to G1 as a specificity check. No motion retargeting authorized.

The minimal red reproducer consistently finds 74/99 SMPL-X bbox50 left-hand slots on
wrist housing (36 yaw, 19 pitch, 19 roll), only 24/99 on actual Dex3 meshes.
The old broad hand zone starts at wrist-roll and includes housing; it is not a hand-mesh label.
An independent full-triangle projector had already preserved the baseline hand counts.

The diagnostic supports a proportion/landmark mismatch plus an unconstrained objective:
height-normalized human wrist lateral coordinates are ~0.381 (SMPL-X) / 0.408 (SOMA),
while Astro's actual hand starts at 0.526; G1 starts at 0.416. Astro's palm frame is
159.5 mm beyond wrist-roll. Learned hand medians lie proximal to the Astro hand start.
Target hand surfaces are present in the reference cloud (115/116 Astro samples versus
92/92 G1), and most wrist-bound human slots have confident source-hand weights.
This rules out absent hand exposure or uncertain labels as sufficient explanations;
it does not prove sampling density or source pose has no influence.
Inspected training uses geometric Chamfer/repulsion/edge losses without a hand landmark term.
See [primary-source note](../../references/umr-wrist-hand-static-correction.md) and
[diagnosis.json](diagnosis.json) for source references and full measurements.

## Controlled intervention

Operate after the frozen learned correspondence, before unrestricted production projection.
For each side estimate learned elbow and wrist X from the corresponding robot outputs
of the 32 human surface slots closest to that source rig joint. Apply a monotone linear
map with knots (learned elbow, same elbow), (learned wrist, physical hand mesh start),
(physical hand tip, same tip). Outside the elbow-to-tip interval it is identity.
Apply to every predicted slot in that coordinate interval, without consulting source labels.
Y/Z, source slots, meshes, samples, ordering, graph and checkpoint remain unchanged.
Both sides use the same rule; no snap is restricted to hand meshes. No model XML is corrected.

The proximal hand mesh extent is an explicit operational anchor, not an independently
validated universal anatomical wrist. This intervention intentionally moves the learned
wrist towards the hand; increased mesh membership is therefore expected. Coverage,
non-hand spill and global surface fit are necessary counterchecks. It is a candidate static
calibration demonstration, not an adopted general repair or learned finger correspondence.
Primary k=32 and sensitivity k=16/64 were declared before measuring outcomes; no tuning.

## Provenance

UMR isolated checkout d1cdaedaf67a827198da71c5fa831f48b2e51f91, existing patch preserved.
Astro frozen committed model 1316cac090144c9891453a53b8336e8374c96196; source and target
arrays reuse the four Astro-hands arms and four prior G1 arms, all 4096 slots,
500 training epochs, seed0. No new training or sampling. Reference target samples
remain those used during training, not held-out surface-area samples.
The source templates differ in identity, topology and arm pose; this experiment does
not isolate those differences. G1 has rubber hands and no finger hinges.

Current upstream XML had concurrent collision-only edits (hash recorded in preparation.json).
They are preserved. This experiment uses a frozen historical XML and copied meshes;
its exact faces and visual vertices/transforms match saved baseline geometry within 2e-7 m.
Compare named meshes, never shifted numeric geom IDs. 265 historical artifact hashes and
53 frozen-asset hashes passed final verification. Assets retain source licenses; not published.

All coordinates are physical metres; source axes +X left, +Y up, +Z forward; target root
axes follow the existing robot transform. Static T-pose only, no FPS/clip/quaternions changed.
Astro shoulder rolls ±pi/2, elbows pi/2, fingers zero. Runtime: existing UMR Python venv
for NumPy/SciPy/MuJoCo, system Python3/Matplotlib for plotting. CPU-only; no GPU jobs.

## Reproduction

From `/data/workspace/motion_studio` (prepare refuses an already prepared directory):

```bash
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/reproduce.py
# Expected assertion failure: 74/99 slots on wrist housing.
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/diagnose.py
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/prepare.py
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/audit.py
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/measure.py
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/test_calibration.py
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/reproduce.py --slots outputs/astro-hand-wrist-correction/smplx_astro_bbox50/k32/correspondence_slots_final.npz
externals/UMR/.venv/bin/python experiments/astro-hand-wrist-correction/verify.py
MPLCONFIGDIR=/tmp/motion-studio-mpl python3 experiments/astro-hand-wrist-correction/plot.py
```

## Evaluation

All eight primary arms use the unchanged common18/native19 audit. All 24 calibrated
variants preserve central/head/leg coordinates and projected points. Exact global-triangle
projection agrees with all primary actual-hand counts. Two independent worked-example
unit tests pass, and the minimal symptom reproducer turns green (95/99 hand,4 housing).
Numerical records: measurements.json, calibration-parameters.json, results.json,
binding-validation.json, validation.json; viewer in outputs/astro-hand-wrist-correction/viewer.

| Arm | Hand L raw → calibrated / total | Hand R raw → calibrated / total | Global sample distance mm raw → calibrated |
| --- | --- | --- | --- |
| smplx_astro_spine1 | 32 → 94 / 99 | 41 → 94 / 98 | 8.59 → 9.37 |
| smplx_astro_bbox50 | 24 → 95 / 99 | 24 → 95 / 98 | 8.59 → 9.30 |
| soma_astro_spine1 | 36 → 81 / 82 | 36 → 75 / 77 | 8.88 → 9.54 |
| soma_astro_bbox50 | 24 → 81 / 82 | 23 → 75 / 77 | 8.65 → 9.22 |
| smplx_g1_spine1 | 63 → 91 / 99 | 68 → 90 / 98 | 8.72 → 9.06 |
| smplx_g1_bbox50 | 70 → 93 / 99 | 64 → 88 / 98 | 8.89 → 9.23 |
| soma_g1_spine1 | 74 → 76 / 82 | 67 → 72 / 77 | 8.74 → 8.89 |
| soma_g1_bbox50 | 74 → 75 / 82 | 67 → 72 / 77 | 9.16 → 9.36 |

Astro actual-hand precision rises from24–47% to95–99%; hand reference coverage within20mm
rises from76–93% to90–96%. Finger mesh assignments rise from6–14 to20–30 per side,
without validating individual digit identities. Mean hand movement is64–105mm; maximum
whole-slot displacement is101–154mm. Zero tothree source forearm slots per side now reach
hand meshes. Global symmetric sample mean distance worsens in every arm (Astro+0.58–0.78mm,
G1+0.16–0.34mm). This is mean nearest-reference distance in each direction averaged in
physical metres, not the original normalized training loss. Forearm housing spacing is
stretched while distal hand spacing is compressed, visible in the matched closeups.

G1 improves mesh membership too, but coverage is essentially unchanged (99–100%). Its
maximum displacement is14–45mm. Therefore the rule is not uniquely Astro-specific, although
Astro needs a substantially larger correction. Across k16/32/64, Astro actual-hand precision
ranges92–99%; the qualitative result survives while several boundary slots change.

## Conclusion and limits

The test demonstrates a substantial static wrist/palm alignment contribution and shows
why the broad hand-zone score hid the error. It does not establish a unique root cause or
that this calibration is optimal. Residual hand errors, forearm stretching, surface-fit
regression, unchanged head mismatch, one seed and reused reference samples remain limits.
No finger semantics, articulation, contacts, collision response, dynamics, temporal
smoothness or motion were tested. Keep motion retargeting on hold.

Completion note: the upstream working XML changed again during this experiment.
`provenance.json` records both observed hashes. The current working asset is not
the experiment input; it was preserved without rollback. All results use the
frozen historical XML and verified matching visual triangles.
