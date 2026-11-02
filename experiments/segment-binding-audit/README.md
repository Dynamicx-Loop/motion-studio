# Experiment: every-segment human ↔ Astro audit with matched G1 control

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-22 / Codex, delegated segment audit.

## Objective and result

Test whether the learned slot correspondence reaches the intended robot geometry,
separately from which MJCF body moves that geometry. No motion retargeting, solve,
rollout, or correction was run. **The Astro mismatch is broader than a missing
neck:** real head/face surface spills into upper torso; proximal arms land on
trunk; thighs extend past knees; forearms extend proximal to elbows. G1 trained
under the matched protocol reduces these specific effects substantially.

- Human `head`: 414 slots = **61 neck + 353 head/face**. Astro visual sends only
  **87/414** to its head shell, **308** to torso, 14 to shoulder hardware, 5 to
  lidar. Of the 353 actual head/face slots, **250 land on torso**. All 61 neck
  slots land on torso/lidar. Primitive sends 127/414 to head shell and 281 to
  torso; it remains a **rejected diagnostic binding**, with 470 buried projections
  including 36 cross-body interiors. G1 sends **408/414 to head shell**, including
  all 353 head/face slots, and only 6 neck slots to torso.
- Astro visual human torso: 486 slots attach to `torso_link`, 206 to `pelvis`,
  59 to hip bodies, 9 to waist bodies. The independent spatial zones count 480
  in trunk, 221 below the waist plane on central geometry, 59 on hip caps.
  Thus the user's torso→pelvis observation is confirmed for a substantial subset;
  the entire torso segment is not displaced. G1 has 723/760 in trunk zones.
- Astro visual thigh slots **more than 20mm below the actual knee plane**:
  106/359 left and 94/339 right, up to 113mm. Primitive: 110 and 94. G1: zero
  on both sides. This exceeds small boundary ambiguity around knee hardware.
- Astro visual forearm slots **more than 20mm proximal to the actual elbow**:
  43/137 left and 42/132 right, up to 102mm. Primitive: 42 and 43. G1: 1 and 0.
  G1 nevertheless has considerable forearm→wrist/hand transfer (51 slots each
  side beyond the wrist-roll plane); it is a control, not anatomical ground truth.
- Astro visual hands all reach the distal wrist/hand zone, but **no separate hand
  mesh is selected**: its visual-only hand spheres are excluded by `auto`. G1
  includes rubber hand meshes. These different hand morphologies limit direct
  contact-quality interpretations. Both visual robots put all human foot slots
  on their same-side ankle-roll mesh; foot-plane scores below are stricter and
  count the part of that mesh above the ankle pivot as a shin zone.

## What the labels mean

Source evidence is pinned UMR `d1cdaedaf67a827198da71c5fa831f48b2e51f91`,
`scripts/retarget_body_segment_surface.py`: map at lines 53–149; loading at
350–399; proximal-arm split at 713–755; slot labelling at 758–801.
The shipped `assets/smplx_parts_segm.pkl` labels SMPL-X faces with 55 joint-region
IDs; the fixed 55→17 map combines neck(12), head(15), jaw(22), eyes(23/24) as
`head`; spine1/2/3(3/6/9) as torso; pelvis(0) as hips. Hand joints/fingers combine
as hands, ankle/foot as feet. The two shoulder classes remain distinct.
The 19-class rule additionally relabels the proximal **0–30% of absolute lateral
extent within each sampled Arm class** as `UpperArm`. It is a slot-dependent
spatial subdivision, not an extra anatomical joint. `Arm` is the remaining distal
part of that same upper arm. Human mesh coloring approximates this split at mesh
vertices; numeric tables and highlighted slots use the exact slot split.

The learner is geometric and does not classify an Astro neck. Source labels are
assigned after correspondence and travel along the ordered slot IDs. Projection
then chooses a target triangle/geom, whose body controls motion. These are five
different facts: source segment, learned paired slot, projection destination,
MJCF body attachment, and visible geometric/anatomical region.

**Crucial control:** G1's selected `head_link` mesh is attached directly to
`torso_link`. Astro's `head_link` body is welded through `torso_link` to
`waist_roll_link`. Neither model has a neck joint. Counting G1's head→`torso_link`
as a head error would therefore be false. The larger/taller distinct G1 head
shell is compatible with better geometric correspondence; the experiment does
not isolate head morphology as the sole cause.

The independent audit convention is implemented in [regions.py](regions.py):

- Identify the head by actual mesh resource or head primitive attachment, sensors
  separately. Do not invent a neck zone. Central geometry is pelvis below the
  waist-yaw pivot; trunk above it. Upper/lower trunk split halfway from waist-yaw
  height to mean shoulder-roll height. This split is a descriptive convention.
- For limb geometry families identified from the inspected MJCF hierarchy, use
  actual canonical joint planes: shoulder-roll/elbow/wrist-roll lateral positions
  for shoulder/upper arm/forearm/hand zones; hip-pitch/knee/ankle-roll heights for
  hip cap/thigh/shin/foot zones. Thus a knee-owned motor protruding above the knee
  can still be geometrically thigh; body name alone is not the semantic test.
- Collapse welded attachments to the first joint-bearing ancestor for rigid
  ownership tables. No articulated joint is collapsed. Geometry and ownership
  tables remain separate, including full geom inventory and bounds.
- `zone_precision` = fraction of a source segment landing in its declared
  compatible zone(s); leakage is its complement. `zone_recall_among_assigned_slots`
  = that segment's share of all slots landing in its expected zones. `Arm` and
  `UpperArm` share a zone, so their individual recall is intentionally competitive.
  Coverage is the fraction of independently sampled expected-zone target points
  within **20mm** of any projected slot from the source segment; distances and
  sample counts are also provided. These are sampled, convention-dependent
  diagnostic measures, **not semantic ground-truth accuracy or surface-area recall**.
  Primitive metrics include rejected projections and cannot establish usable quality.

## Every source segment

The following strict zone compatibility percentages use the definitions above.
They are not a single overall robot score. In particular, clavicle/shoulder
surfaces can reasonably overlap trunk, and hand/foot shells straddle joint planes.
The complete transfer matrices by geometric zone, mesh, body and rigid owner,
per-segment precision/recall/coverage and rejection counts are in
[results.json](results.json); spreadsheet-readable measures are in
[per-segment.csv](per-segment.csv).

| Source segment | Slots | Astro visual | Astro primitive † | G1 control | Examination |
| --- | ---: | ---: | ---: | ---: | --- |
| head | 414 | 21.0% | 30.7% | 98.6% | Astro head/face spills into chest; G1 head shell captures all353 head/face slots. |
| hips | 480 | 29.2% | 32.5% | 71.0% | Astro largely onto proximal moving thighs; G1 mostly pelvis/hip caps. |
| leftArm | 88 | 71.6% | 67.0% | 100.0% | Astro partial trunk/shoulder transfer; G1 entirely upper arm. |
| leftFoot | 141 | 99.3% | 100.0% | 67.4% | All visual slots on same-side foot mesh; pivot-plane score is stricter. |
| leftForeArm | 137 | 46.7% | 51.1% | 55.5% | Astro often proximal to elbow; G1 wrist/hand extension remains. |
| leftHand | 99 | 100.0% | 100.0% | 100.0% | Distal wrist/hand zone; Astro visual lacks separate hand shell. |
| leftLeg | 262 | 82.4% | 81.3% | 96.6% | Astro partially on feet; G1 mostly shin. |
| leftShoulder | 69 | 2.9% | 0.0% | 49.3% | Astro mainly trunk; G1 splits shoulder hardware/trunk. Clavicle boundary ambiguous. |
| leftUpLeg | 359 | 62.4% | 60.4% | 96.4% | Astro extends onto shin beyond knee; G1 stays above knee almost entirely. |
| leftUpperArm | 61 | 0.0% | 0.0% | 96.7% | Astro entirely medial to shoulder-roll plane/on trunk; G1 mostly upper arm. |
| rightArm | 99 | 65.7% | 67.7% | 100.0% | Astro partial trunk/shoulder transfer; G1 entirely upper arm. |
| rightFoot | 141 | 96.5% | 99.3% | 65.2% | All visual slots on same-side foot mesh; pivot-plane score is stricter. |
| rightForeArm | 132 | 51.5% | 53.0% | 54.5% | Astro often proximal to elbow; G1 wrist/hand extension remains. |
| rightHand | 98 | 100.0% | 99.0% | 100.0% | Distal wrist/hand zone; Astro visual lacks separate hand shell. |
| rightLeg | 290 | 87.2% | 83.4% | 94.1% | Astro partially on feet; G1 mostly shin. |
| rightShoulder | 77 | 6.5% | 0.0% | 40.3% | Astro mainly trunk; G1 splits shoulder hardware/trunk. Clavicle boundary ambiguous. |
| rightUpLeg | 339 | 63.7% | 62.2% | 98.5% | Astro extends onto shin beyond knee; G1 stays above knee almost entirely. |
| rightUpperArm | 50 | 0.0% | 0.0% | 94.0% | Astro entirely medial to shoulder-roll plane/on trunk; G1 mostly upper arm. |
| torso | 760 | 63.2% | 62.8% | 95.1% | Astro lower transfer into pelvis/hip hardware; G1 mostly trunk. |

† Primitive binding is rejected; percentages describe tentative projections only.

## Provenance and control

The pinned UMR tracked-file inventory contains no `.pt`, `.pth`, `.ckpt`, or
correspondence-slot `.npz`; the distributed NPZs are example motions and source
models/templates. The README says the quick start builds or reuses correspondence.
The shipped HiPHI shared G1 config specifies beta-zero source shape, which would
confound this actor comparison even if a separately generated cache existed.
Accordingly this is **newly trained matched G1 correspondence using the shipped
G1 XML/T-pose**, not a claim to inspect nonexistent shipped pretrained bindings.

- Original Astro arms are reused without retraining or editing their configs,
  slots or checkpoint files. Original canonical Astro XML/config are unchanged.
  The isolated UMR geometry patch remains as recorded in the
  [prior experiment](../astro-correspondence-comparison/README.md).
- G1 uses `assets/g1/g1_29dof.xml`, shipped shoulder-roll ±π/2/elbow π/2 T-pose
  and `body:waist_yaw_link` centering. The different root origin cancels in
  centered normalization but is recorded; axes are metres in robot
  `(forward,left,up)` and human/viewer `(left,up,forward)`. No temporal resampling,
  joint trajectories or quaternion processing occurs here.
- Same permitted HiPHI file, actor betas `52fa48a138`, neutral SMPL-X model,
  4096 points, seed0, samplers1000/9000, oversample8, first-hit exterior sampling,
  fixed human template, batch1, robot2smpl_only, 500 epochs, AdamW cosine
  lr0.001→0.00001, Chamfer1, repulsion0.002, edge0.4, noise0.002, no dropout or
  dynamic resampling. Per-surface height normalization remains upstream behavior.
  Exact merged configs are preserved as `*-resolved.json`.
- Python3.12.3, Torch2.7.1+cu128, existing UMR environment, RTX5070 Laptop GPU.
  G1 trained sequentially with host GPU access; final logged weighted loss0.001695.
  Same loss magnitude does not imply semantic equivalence. Only seed0 is compared;
  no multiseed confidence, runtime benchmark or causal morphology attribution.
- Assertions establish **bitwise equal human meshes, sampled points, betas,
  learned human slots, slot ordering and template graph across all three arms**.
  No Wendy assets or motion data were accessed. No baseline advance or install.
  Input/model/robot/mesh/config/checkpoint hashes are in [provenance.json](provenance.json).
  Model, motion and robot assets retain their respective terms; generated geometry
  exports are local inspection artifacts, not a redistribution license.

## Reproduction and outputs

The commands below document this historical cohort and may write to its fixed
paths. Do not run them against retained evidence; adapt every destination to a
fresh cohort before reuse.

From `/data/workspace/motion_studio`:

```sh
externals/UMR/.venv/bin/python externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py --config experiments/segment-binding-audit/g1.json --stage build > outputs/segment-binding-audit/g1-build.log 2>&1
externals/UMR/.venv/bin/python externals/UMR-astro-surface-experiment/scripts/humanoid_retarget_pipeline.py --config experiments/segment-binding-audit/g1.json --stage train > outputs/segment-binding-audit/g1-train.log 2>&1
externals/UMR/.venv/bin/python experiments/segment-binding-audit/audit.py > outputs/segment-binding-audit/audit.log 2>&1
MPLCONFIGDIR=/tmp/segment-audit-mpl python3 experiments/segment-binding-audit/plot_audit.py
cp experiments/segment-binding-audit/viewer.html outputs/segment-binding-audit/viewer/index.html
cp experiments/segment-binding-audit/viewer.js outputs/segment-binding-audit/viewer/app.js
python3 -m http.server 8767 --bind 127.0.0.1 --directory outputs/segment-binding-audit/viewer
```

Open [the mesh audit viewer](http://127.0.0.1:8767/). It includes all19 source
filters, actual solid meshes, spatial-zone/body colors, joint landmarks, primitive
visual-shell overlay, paired slot selection and actual mesh/body/rigid-owner data.
The selected slot is always inside the source filter; the old8766 inspector's
stale selected-foot highlight was fixed as well. Points can be shown through
geometry explicitly (default) or depth-tested. Primitive rejection is prominent.
Three.js0.165.0 is loaded from jsDelivr; internet access is required.

Static evidence: `outputs/segment-binding-audit/segment-evidence.png` shows source,
Astro visual, rejected primitive, and G1 head/neck, torso, thigh and forearm
transfers over their complete selected surface triangles. Highlighted points are
shown through the mesh; black marks identify actual knee/elbow pivots. Orbit the
viewer to assess depth. Binary meshes, per-slot audit NPZs, G1 dataset/checkpoints
and logs stay in ignored `outputs/segment-binding-audit/`.

Validation: G1 build/train completed; production G1 visual binding matched the
preview projection; all slot/source equality assertions passed; all19 count rows
sum to4096 for each arm; primitive rejection mask unchanged470. Browser checked
solid geometry and head filtering (head selects slot3668, never foot0). G1 and
primitive numerical exports passed; their interactive target switch/overlay were
not separately verified before the preview server stopped. Parent chat is
restarting the server. Static figure visually inspected. Source scripts
compile; configuration JSON parses; referenced paths and whitespace checked.

These are canonical correspondence diagnoses. They do not measure motion,
contacts, grasp fidelity, joint-limit behavior, stability, or dynamic feasibility.
No automatic relabelling, correction, further training or retargeting follows.
