# Experiment: all shipped UMR robot configurations and segment bindings

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-23 / Codex.

## Objective and result

Audit every shipped robot config, distinguish assets/presets from pretrained
correspondence, and inspect all 19 human source segments on actual target geometry.
**Inventory and correspondence inspection are complete. No motion retargeting,
solver trajectory, rollout, or robot execution was started.**

There are **six distinct available target embodiments**: PiPlusPro, Booster K1,
Unitree G1, EngineAI T800, Unitree H2, and the MimicKit humanoid character.
There are additional G1 hand/tool/model variants and source/task defaults; these
are not additional base robot embodiments. Several names in standalone builder
presets refer to assets that are not shipped locally. None are silently dropped.

No shipped robot correspondence checkpoint was found in the pinned tracked files
or in the four official robot-preset bundles. This audit **newly trains** seven
exact-source counterparts and five separately labelled centering controls, and
reuses three existing controlled results. It does not call any newly generated
checkpoint a pretrained distribution artifact.

Measured findings are configuration-sensitive. Astro's head/torso, proximal-arm,
forearm and knee spill persists in the reused results. PiPlusPro also has strong
forearm crossing; its head/thigh result improves markedly with shipped human
centering. K1 has knee crossing despite good head/face transfer. T800/H2 knee
crossings increase with shipped centering. Thus the evidence supports several
failure modes, **not a universal ranking or a morphology-only explanation**.

## Inventory and availability

Pinned repository: `externals/UMR`, commit
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
[Inventory JSON](inventory.json) records all **19 config/default JSONs**, all
**13 robot XML/URDF assets**, standalone builder presets, canonical joint anchors,
axes, selected geom bounds, mesh identities and rigid ownership.

| Embodiment / variant | Shipped config or asset | Official T-pose card | Correspondence inspected |
| --- | --- | --- | --- |
| PiPlusPro (demo label PiPlus) | `humanoid_retarget_hightorque_pipluspro_example.json` | Yes | New matched control + native-centering sensitivity |
| Booster K1 | `humanoid_retarget_booster_k1_example.json` | Yes | New matched control + centering sensitivity |
| Unitree G1 | `humanoid_retarget_unitree_g1_example.json` | Yes | Reused exact-source 500-epoch G1 control |
| EngineAI T800 | `humanoid_retarget_engineai_t800_example.json` | Yes | New matched control + centering sensitivity |
| Unitree H2 | `humanoid_retarget_unitree_h2_example.json` | No | New matched control + centering sensitivity |
| MimicKit humanoid | `humanoid_retarget_mimickit_humanoid_example.json` | No | New controls; patched primitive triangulation, caveat below |
| G1 HiPHI shared correspondence | `humanoid_retarget_unitree_g1_hiphi_shared_correspondence.json` | Same G1 | Source/template variant, beta-zero neutral; no shipped cache at configured path. Actor-specific control above is **not** this native source setting. |
| G1 27-DOF left racket | `humanoid_retarget_unitree_g1_racket_example_adapt.json` | No | New human-only controlled counterpart; native AdaPT composite human+racket source was **not** trained |
| G1 sphere hands | XML + URDF; no separate robot JSON | No | Additional asset-variant control; `auto` omits ankle/foot meshes |
| PiPlusPro colored / K1 `colered` | Alternate XMLs, compile successfully | No separate cards | Visual/pose asset variants of the same embodiments, not separate preset correspondences. No robot JSON selects them. |
| G1 large box | `g1_29dof_w_largebox.xml` | No | **Unavailable:** compiler cannot open `assets/largebox/largebox.obj`; no invented replacement |
| AGIBOT A2 | Standalone builder name / T-pose constants | No | **Unavailable:** `assets/agibot_a2/urdf/model_urdf_mjcf.xml` absent |
| Fourier N1 | Standalone builder name / T-pose constants | No | **Unavailable:** `assets/fourier_n1/n1_tpose_mjcf.xml` absent |
| PND Adam Lite | Standalone builder name / T-pose constants | No | **Unavailable:** `assets/pnd_adam_lite/adam_lite_tpose_mjcf.xml` absent |
| G1 BrainCo hands | Standalone builder default | No | **Unavailable:** `assets/unitree_ros/robots/g1_with_brainco_hand/g1_29dof_mode_15_brainco_hand_tuned.xml` absent; hand variant, not another base robot |
| Standalone legacy original G1 default | `assets/unitree_description/mjcf/g1.xml` | No | That default path is absent. The available configured G1 is `assets/g1/g1_29dof.xml`; no alias was silently substituted. |

The ten root `humanoid_retarget_defaults*.json` files and
`robot_configs/humanoid_retarget_defaults_adapt.json` are source/task/batch
settings without a target XML: ordinary SMPL-X, HiPHI, bones seed, NR, character,
HSI/HOI standard/GRAIL, batch, and AdaPT variants. The G1 shared and racket configs
are explicitly identified above. Inventorying them does not imply every source
pipeline or native full preset was executed.

### Official web-demo evidence

The [official Studio](https://hanyang9.github.io/UMR/umr_studio.html) and its
[robot manifest](https://hanyang9.github.io/UMR/static/assets/studio_robot_presets/manifest.json?v=20260905-studio-robot-presets-v1)
were read on 2026-10-23. [Official inventory](official-inventory.json) preserves
URLs, declared file lists/sizes, HTTP checks and downloaded text/XML hashes.
All **134 declared asset URLs returned HTTP 200**. The four fetched XML hashes
and configured T-pose dictionaries match the corresponding local controls exactly.
Mesh/texture URLs were checked by HEAD; their remote bytes were not all hashed,
so XML identity is not asserted as a bytewise proof of every remote asset.

`mujoco-viewer.js` loads the preset's asset files and applies its T-pose. The
[browser runtime](https://hanyang9.github.io/UMR/static/js/browser-umr-runtime-exact-v1.js?v=20260927-hiphi-sit-lqr-v1)
invokes fresh 60-epoch CPU/WASM correspondence training on source and robot
samples before binding. Preset bundles contain no `.npz/.pt/.pth/.ckpt` robot
correspondences. The website is not a supplied pretrained robot-binding library,
and its 60-epoch runtime was not executed or equated to these native 500-epoch
controls. The supplied screenshot is corroborating page evidence only.

## Provenance and controlled settings

- Existing baseline and canonical Astro config/XML remain unchanged. Builds use
  the existing isolated `externals/UMR-astro-surface-experiment` at the same commit,
  with its preserved [geometry patch](../astro-surface-geometry/umr-surface-geometry.patch),
  SHA256 `e2cc109b3aa8125034391fde0ae2f66a02ea660a6900ce727351ea1579ca000a`.
  No new external source edits, installs, checkout reset, or baseline advance.
- Only permitted input:
  `externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
  Actor betas hash `52fa48a138`, neutral SMPL-X, actual loaded model
  `/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl`.
  Its shape/gender create a static source; motion-frame poses are not training targets.
  No Wendy files or other sessions' results were used.
- Exact-source group: spine1-centered identical human mesh, samples, betas,
  reconstructed source slots, ordering, template points and graph; **bitwise
  equality asserted against every new arm and the existing G1 control**. The
  existing Astro/G1 equality assertions are reused from the prior audit.
- 4096 slots, seed0, human sampler1000 / robot9000, oversample8, first-hit exterior
  sampling, curvature0, fixed source template, `robot2smpl_only`, batch1,
  500 epochs, AdamW lr0.001 cosine to0.00001, Chamfer1, repulsion0.002 (k8,
  radius0.035), edge0.4/geodesic32, residual0, noise0.002, no dropout/resampling.
  Per-surface height normalization is retained. Different native robot centers,
  T-poses, proportions, selected surfaces and heights remain recorded differences.
- Separate centering-sensitivity group: five robot-specific shipped `bbox_ratio`
  source centers replace spine1; all other settings remain the matched protocol.
  Robot meshes and sampled target arrays are bitwise equal to their spine1
  counterparts. Human coordinates/sampling can change; MimicKit changes a few
  source segment slot counts. **These are not full native-preset runs**, and
  individual slot IDs are not asserted to correspond across centering groups.
- Python3.12.3 / Torch2.7.1+cu128 / MuJoCo3.3.7 / NumPy1.26.4 /
  SciPy1.17.1 / trimesh5.1.1; original UMR virtual environment. Sequential host-GPU
  training on RTX5070 Laptop 8GB. [Provenance](provenance.json) includes commands,
  statuses, stage wall times, input/model/config/XML/mesh/checkpoint hashes and
  source status. Wall times are not a controlled runtime benchmark.
- Units metres/radians. Robot root coordinates `(forward,left,up)`; human/viewer
  coordinates `(left,up,forward)`. T-pose joints come from each robot's shipped
  config. Static H2 is compiled fixed-base as supplied; the future retarget-stage
  floating-root wrapper is not invoked. No FPS conversion, temporal resampling,
  quaternion trajectory, contact solve, or simulation is involved.
- UMR MIT notices preserved. SMPL-X, HiPHI and robot assets retain separate terms.
  No new redistribution rights are inferred from repository availability. Binary
  models, sampled meshes and checkpoints remain local ignored inspection outputs.

### MimicKit geometry gate

MimicKit uses the `auto` primitive fallback, not visual triangle assets.
[The geometry gate](mimickit-geometry-gate.json) compares each convex sphere/capsule/box
triangle's normal against its centroid-to-interior direction. Baseline produces
11640 triangles: **768 degenerate, 10848 inward, 24 outward**. The preserved
experimental triangulation produces10872 nondegenerate outward triangles.
Thus these training results use that existing fix and are **not stock-baseline
primitive-sampler results**. No canonical XML or physical collision model changes.

The unchanged `auto` binder accepts MimicKit projections mechanically, but the
analytic primitive-union diagnostic (the existing helper, 10µm interior margin,
excluding the generating primitive) flags **36/4096** buried projections in the
exact-source arm and **43/4096** in its centering arm. Amber viewer points expose
these; they are warnings, not an altered rejection mask. Astro's explicit primitive
policy remains rejected at470 points including36 cross-body interiors.

## Diagnostic definitions and limits

[regions.py](regions.py) uses per-robot inspected mesh identities and joint
anchors. Mesh/body/rigid-owner transfer matrices stay separate. A rigid owner is
the first joint-bearing ancestor; only welded attachments are collapsed.

- Head shell identity: PiPlusPro `head_pitch_link`, K1 `Head_2`, T800
  `LINK_HEAD_YAW`, H2 `head_yaw_link`, MimicKit `head`, G1 `head_link`.
  Smaller neck motor/bracket meshes are labelled `neck hardware`, camera/sensors
  separately. Astro/G1 heads are welded, whereas the other supplied targets have
  articulated head/neck joints. A body name alone is not semantic evidence.
- Arm/leg families come from each inspected hierarchy, cut by canonical
  shoulder-roll/elbow/distal-hand-boundary lateral planes and hip/knee/ankle
  height planes. PiPlusPro's calf joint is its knee. K1's terminal `Elbow_Yaw`
  boundary is a declared distal-hand convention, not a claimed wrist joint.
  MimicKit's hand-body origin is a welded distal boundary. T800 has no separate
  wrist/hand zone; terminal elbow-yaw shells receive hand slots.
- Central geometry uses waist-yaw height, and splits trunk halfway to shoulder
  height. MimicKit uses abdomen height. K1 has a rigid trunk without a waist joint
  or distinct pelvis shell: its trunk is not falsely split into an invented
  articulated pelvis. Consequently its strict hips score is not comparable to
  articulated-waist robots. Source shoulders/clavicles may reasonably overlap trunk.
- `zone_precision` is compatible-zone slots / source slots; `zone_leakage` is
  its complement. `zone_recall_among_assigned_slots` is that source's share of all
  slots in its compatible zones. `Arm` and `UpperArm` share a target zone.
  Coverage at20mm uses the **training target reference cloud**, not held-out
  samples, continuous surface area, or semantic ground truth. Dense transfer can
  give high coverage while many other slots leak elsewhere. Zero expected samples
  is shown as N/A; distinguish physically absent T800 hand zones from excluded
  sphere-hand G1 foot meshes. Full transfer tables retain the measured destinations.
- Cross-joint diagnostics count thigh slots >20mm below knee, forearm slots
  >20mm medial/proximal to elbow, and upper-arm `Arm` slots >20mm distal to elbow.
  These are spatial T-pose conventions, not motion errors. A fixed20mm threshold
  has different relative sizes on PiPlusPro and H2; no pooled robot quality score.
- Human `head` has414 slots:353 head/face +61 neck. The shipped55→17 mapping merges
  those anatomical categories. The19-way rule additionally partitions each sampled
  arm's proximal0–30% lateral extent into `UpperArm`; it is not another joint.
  Mesh coloring approximates that split at vertices; selected slots/tables use
  exact slot labels. Low loss, zero opposite-side assignments and binding acceptance
  do not establish semantic correctness, contacts, or dynamic feasibility.

## Measured exact-source results

All counts below use the same source slots. Head/face columns exclude the61 neck
slots. Full19-segment precision/leakage/recall/coverage and mesh/body/owner transfer
matrices are in [results.json](results.json) and [per-segment.csv](per-segment.csv).

| Target | Head/face → head shell /353 | Head/face → torso | Thigh >20mm below knee L/R | Forearm >20mm proximal to elbow L/R |
| --- | ---: | ---: | ---: | ---: |
| PiPlusPro | 219 | 78 | 21/9 | 81/76 |
| Booster K1 | 349 | 0 | 59/42 | 0/0 |
| G1 | 353 | 0 | 0/0 | 1/0 |
| T800 | 353 | 0 | 0/0 | 20/16 |
| H2 | 351 | 0 | 4/0 | 0/0 |
| MimicKit | 352 | 1 | 17/3 | 38/38 |
| G1 racket | 353 | 0 | 0/0 | 0/1 |
| G1 sphere hands | 353 | 0 | 0/0 | 2/2 |
| Astro visual | 87 | 250 | 106/94 | 43/42 |
| Astro primitives † | 127 | 220 | 110/94 | 42/43 |

† Astro primitive projections remain rejected diagnostic results. G1 racket uses
human-only source shape; all99 left-hand slots reach its racket mesh. This is a
tool-bearing task variant, not a new robot or a native AdaPT-contact validation.
Sphere-hand G1 maps both141-slot foot segments to knee meshes because `auto`
excludes its contact-enabled ankle/foot meshes. That is a surface-selection gap,
not proof that the full model lacks feet. The viewer can overlay all its meshes.

H2/G1 largely avoid the strong proximal-forearm crossing seen in Astro/PiPlusPro,
but both put many forearm slots in distal wrist/hand zones. Strict feet scores
are affected by ankle shells straddling the pivot plane; mesh transfer tables
separate same-side-foot attachment from this spatial convention. These results
identify common boundary compression/extension and source-label artifacts, while
head morphology, root centering, terminal structures and surface selection create
robot-specific cases. The opposite-side spatial-zone diagnostic counts one slot for T800 and one for
MimicKit in the exact-source set, and one for native-centered MimicKit; the other
rows are zero. These isolated counts also are not a semantic-quality guarantee.
Only one seed is tested; none isolates a single cause.

## Separate native-centering sensitivity

[Native-center results](native-center-results.json) and
[native-center segment CSV](native-center-per-segment.csv) preserve this group.
Same actor and training protocol, different source centering; do not pool these
rows with the bitwise-source comparison.

| Target | Shipped ratio | Head/face → head shell /353 | Head/face → torso | Thigh knee crossing L/R | Forearm elbow crossing L/R |
| --- | ---: | ---: | ---: | ---: | ---: |
| PiPlusPro | 0.534057 | 308 | 7 | 0/0 | 83/81 |
| Booster K1 | 0.566227 | 352 | 0 | 33/17 | 0/0 |
| T800 | 0.646516 | 323 | 30 | 73/50 | 19/16 |
| H2 | 0.615693 | 327 | 17 | 44/25 | 0/0 |
| MimicKit | 0.590406 | 346 | 7 | 25/5 | 38/33 |

PiPlusPro head/face→torso drops78→7 and thigh crossings21/9→0/0, while elbow
crossings81/76→83/81 persist. K1 knee crossings59/42→33/17 improve but remain.
T800 0/0→73/50 and H2 4/0→44/25 knee crossings worsen. This is direct evidence of
centering sensitivity, not a claim that native presets are globally better/worse.
The native actor differs from the default LAFAN1 source and beta-zero G1 shared
source, and the training schedule is our fixed protocol. No native full-pipeline
performance or motion-quality claim follows.

## Reproduction and outputs

The commands below document this historical cohort and may write to its fixed
paths. Do not run them against retained evidence; adapt every destination to a
fresh cohort before reuse.

Working directory: `/data/workspace/motion_studio`.
All configs and merged `*-resolved.json` files are beside this record. Twelve
new dataset/train pairs live under ignored `outputs/all-robot-segment-audit/`.
The driver only allows build/train stages; retarget paths are named
`NOT_AUTHORIZED_retarget.npz` and verified absent.

```sh
python3 experiments/all-robot-segment-audit/inspect_official.py
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/inspect_inventory.py
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/validate_mimickit_geometry.py
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/run_correspondence.py piplus k1 t800 h2 mimickit g1_racket
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/run_correspondence.py g1_spherehand
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/audit.py
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/run_correspondence.py piplus_native_center k1_native_center t800_native_center h2_native_center mimickit_native_center
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/audit_native_centers.py
externals/UMR/.venv/bin/python experiments/all-robot-segment-audit/verify_and_record.py
MPLCONFIGDIR=/tmp/all-robot-audit-mpl python3 experiments/all-robot-segment-audit/plot_audit.py
cp experiments/all-robot-segment-audit/viewer.html outputs/all-robot-segment-audit/viewer/index.html
cp experiments/all-robot-segment-audit/viewer.js outputs/all-robot-segment-audit/viewer/app.js
python3 -m http.server 8768 --bind 127.0.0.1 --directory outputs/all-robot-segment-audit/viewer
```

Host access is required for the GPU train commands and browser-accessible server.
Completed datasets/checkpoints can be reused by upstream cache behavior; do not
confuse reuse with a fresh training measurement. The run record preserves actual
successful commands and logs. Re-running the driver appends stage records; the
verification's24-record assertion describes this captured experiment.

Open [the all-robot mesh inspector](http://127.0.0.1:8768/).
It has15 targets in separately labelled comparison groups, all19 source filters,
actual selected triangle meshes, full-model overlays for Astro primitive and G1
sphere hands, spatial/body coloring, paired slot selection, joint landmarks,
exposure warnings, and default equal-height display. Display scaling is explicit;
metrics remain in original metres. Turn equal-height display off for physical
size comparison. Source meshes follow each native-centering arm's coordinates.
Three.js0.165.0 loads from jsDelivr, requiring network access.

Static evidence in `outputs/all-robot-segment-audit/`:

- `demo-evidence.png`: source and all four official-card embodiments;
- `additional-evidence.png`: Astro, H2, MimicKit, racket and sphere-hand variants;
- `all-segments.png`: complete19-segment strict-zone matrix, N/A where absent;
- `piplus-head-viewer.png`, `spherehand-foot-overlay.png`: actual browser evidence.

Static columns are independently fitted; screenshots/viewer support depth
inspection. Highlighted points are visible through geometry by default. The
additional figure's sphere-hand surface intentionally lacks feet; the overlay
screenshot shows the complete asset around that selected surface.

Validation:24 new build/train stages succeeded;15 correspondence exports and285
segment rows sum correctly; exact-source equality checks pass; native target
meshes/samples match their controls; production bind projections match displayed
projections; original primitive rejection mask remains470. Official metadata/XML
identity and134 asset URLs verified. Canonical Astro XML/config and geometry-patch
hashes unchanged; baseline UMR clean. Browser switched all15 targets with source
head selection inside the filter and solid source/target meshes; all19 filters
checked on G1, full-model overlay and narrow/wide camera fitting inspected.
[Browser verification](browser-verification.json) records the15 loaded source/target
triangle counts and successful filtered selections. Python/JavaScript syntax,
referenced paths and whitespace checked. No motion
retargeting, contact measurement, solver rollout, hardware execution, multiseed
confidence estimate, or automatic correspondence correction was performed.
