# Experiment: SMPL-X and SOMA static correspondence on Astro and G1

Date / author: 2026-10-23 / Codex, with background primary-source and asset research.

## Objective and result

Extend the HiPHI/SMPL-X correspondence audit to SOMA, with Unitree G1 as a
counterpart, and distinguish human weight/label problems from target binding
failures. **Eight static arms are complete: six new 500-epoch trainings and two
hash-verified reused SMPL-X results. No motion retargeting, solver trajectory,
rollout, or robot execution was run.**

SOMA **partly improves Astro forearm transfer but does not resolve its head/torso
mismatch**. Under joint centering, head/face→torso slightly worsens from70.8% to73.1%;
under common bbox centering it improves from43.1% to34.1%. G1 remains0% in all four
arms. Astro knee crossings disappear under bbox centering for **both** sources.
This is strong centering sensitivity, not a SOMA-specific fix. Other region
precision/coverage measures can worsen, especially on G1 with bbox centering.
There is no universal winner or established single cause.

These are controlled **template/configuration comparisons**, not an isolated
representation effect: SOMA's public neutral template is not the HiPHI actor,
and source topology, shape, proportions and canonical arm pose differ. The
[cited research note](../../references/umr-smplx-soma-weights.md) traces the method
and terminology to official UMR, SMPL-X and NVIDIA sources.

## Provenance and experiment design

- UMR baseline and reused isolated checkout both at
  `d1cdaedaf67a827198da71c5fa831f48b2e51f91`. The isolated geometry patch is preserved
  with SHA256 `e2cc109b3aa8125034391fde0ae2f66a02ea660a6900ce727351ea1579ca000a`.
  No upstream source, dependencies, canonical Astro XML/config, prior experiment,
  or paused automation was changed.
- SMPL-X actor comes from the shipped
  `sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
  Only neutral gender and ten actor betas define its static template; temporal
  poses do not train correspondence. Actual loaded asset is
  `/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl`,
  SHA256 `381c808965deb4f5e845f8c3eddb0cd69930cc72e5774ce4f34c4ce3cf058361`.
- SOMA uses `/data/motions/human_models/soma-x/f81a01796f65/overlays/umr/SOMA_neutral.npz`, the compatibility
  overlay derived from NVIDIA HF revision
  `f81a01796f652260ff930d5318d6c6b845a505ed`. UMR poses its public bind shape into
  the saved T-pose; **this is not a zero-MHR-identity forward mesh**. The original
  assets are untouched. [Human audit](human-weights.json) records actual files,
  resolved symlinks, hashes, shapes and fresh official-loader verification.
- Astro visual surfaces use the canonical XML and existing completed T-pose:
  shoulder rolls ±π/2, both elbows +π/2, all other scalar joints zero. G1 uses the
  same previously audited XML/T-pose. Astro remains centered on `body:pelvis`, G1
  on `body:waist_yaw_link`. Between-robot differences therefore include their
  native target frame conventions, not only morphology.
- **Per robot, target mesh vertices/faces/samples/face IDs are bitwise identical
  across all sources and center arms. Per source/center, human mesh, samples,
  template order/graph and human output slots are bitwise identical across robots.**
  Original datasets are copied as explicit target controls after historical hash
  verification. SOMA is generated once with upstream `build_soma_samples`.
- `spine1` uses SMPL-X joint3 versus SOMA public joint2 (`Spine1`). `bbox50`
  subtracts the complete **xyz bbox midpoint**, not only a vertical offset.
  Within each source, it translates the same sampled points without resampling
  (100nm tolerance), retaining face identities. This isolates centering from
  sample changes. Neither arm silently optimizes one source or uses a different
  target protocol.
- Common protocol:4096 slots; seed0; source sampler1000, robot9000; oversample8;
  source area sampling/FPS, robot first-hit exterior sampling; curvature0;
  `fixed_template=true`, `robot2smpl_only`, batch1;500epochs; AdamW lr0.001 cosine
  to0.00001; Chamfer1; repulsion0.002,k8,radius0.035; edge0.4,geodesic32;
  residual0;noise0.002;dropout0;no resampling. Source labels/LBS do not supervise
  this learning. Full merged configs, exact train commands and final losses are
  in [provenance.json](provenance.json).
- Per-sample-height normalization divides by each native height; it does not
  recenter or equalize proportions. SMPL-X height1.661802m; SOMA1.771973m;
  Astro selected surface1.239373m. The source center height fractions are
  0.584263 and0.600363. Relative bbox shifts from spine1 are SMPL-X
  `[-0.000374,-0.140028,+0.016180]m` and SOMA
  `[-0.000013,-0.177840,+0.051746]m`.
- Canonical poses are also unequal: SMPL-X shoulder→elbow elevations are
  −15.07° left/−7.65° right (65.19/34.48mm drop); SOMA is horizontal on both sides.
  [Source-template comparison](source-template-comparison.json) measures all
  source joints, normalized lengths, slopes, bounds and centers. No corrective
  posing or fitted identity conversion was introduced.
- Runtime: Python3.12.3, Torch2.7.1+cu128, MuJoCo3.3.7, NumPy1.26.4,
  SciPy1.17.1, trimesh5.1.1, py-soma-x0.3.4, smplx0.1.28. Six sequential host-GPU
  jobs on RTX5070 Laptop; GPU occupancy was checked first. No installation or
  driver change. Logged wall times are not a benchmark.
- Human coordinates `(left,up,forward)`; robot root `(forward,left,up)`;
  metres/radians. No motion resampling or trajectory quaternion convention is
  involved. Downloaded USD animation has separate conventions below.
- UMR MIT and existing notices preserved; SMPL-X/HiPHI/robot asset terms remain
  separate. Model arrays, meshes, checkpoints and downloaded animation stay in
  local ignored outputs, not redistributed with the report.

## Human assets, weights and labels

Four quantities are kept separate: body-model parameters, LBS skinning matrices,
discrete segmentation/cost weights, and learned correspondence-network weights.
UMR does **not** copy human LBS columns into robot joints: common slot index
transfers source region/cost semantics, while robot face→geom→body binding
supplies rigid motion ownership.

| Check | SMPL-X | SOMA public mid rig |
| --- | ---: | ---: |
| LBS matrix | 10475×55 | 18056×78 |
| Negative/nonfinite values | 0/0 | 0/0 |
| Maximum row-sum error | 4.47e-8 | 6.74e-8 |
| Vertices with top1−top2 influence <0.05 | 211 | 634 |
| Vertices with largest individual weight <0.5 | 345 | 1093 |
| Discrete common label vs grouped-LBS argmax disagreements | 10/10475 | 758/18056 |
| Of those, grouped-LBS winner ≥0.8 | 0 | 98 |
| Slot common label vs grouped-LBS argmax disagreements | 71/4096 | 377/4096 |
| Slots passing declared-label weight ≥0.8 and no SOMA mixed-face flag | 2702 | 2868 |

All51 overlay arrays match a fresh official reconstruction bitwise; every
original slim-NPZ entry is preserved. Eight used original SOMA assets were
reverified against the pinned manifest. The full internal rig has auxiliary
joints; the public78-joint reduction aggregates removed joint influences into
retained ancestors. Joint names, ordering, parents, influence counts and all
region disagreements are retained in [human-weights.json](human-weights.json).
This validates the static public data, not dynamic equivalence with expanded
procedural posing.

SOMA's UMR labels still come from SMPL-X: official `SOMA_wrap` vertices inherit
nearest `SMPLX/base_body` face labels, which are collapsed55→17; native SOMA
faces then receive majority labels, followed by UMR's sample-dependent arm split
into19 labels. They are **not** native SOMA LBS argmax labels. Disagreements with
LBS therefore need interpretation, not automatic correction. SOMA's375 torso
vertex disagreements include155→leftShoulder,143→rightShoulder and59→neck;
head/face→neck44 and neck→head48 show central boundary ambiguity.

The correspondence OBJ and actual SOMA mesh have identical original quad polygons
and vertex order, but differing triangle diagonals. Vertex-label transfer remains
valid; triangle identity was not assumed. An independent complete nearest-triangle
check improved93 wrapper projections by >1µm (max0.182mm), changed13 raw55 labels
but **zero native17 labels**. The nearest-vertex search shortcut therefore does
not explain the native17 discrepancies measured here.

## Anatomical diagnostic definitions

[Native per-segment CSV](per-segment.csv) preserves UMR's19 labels for every arm.
[Common anatomical CSV](common-per-segment.csv) merges `UpperArm`/`Arm`, separates
neck from head/face, and gives18 named groups with explicit per-joint LBS maps.
This is an anatomical comparison vocabulary, not an assertion of equivalent
55/78-joint rigs. SOMA common labels are majority votes of transferred raw55
vertex categories; mixed-category triangles are flagged. SMPL-X's original face
label is authoritative for that diagnostic, so its mixed-face flag is not a
comparable boundary statistic.

A **high-confidence subset** requires ≥80% barycentrically interpolated LBS mass
in the declared common region and no mixed SOMA common-category triangle. This
is a sensitivity analysis, not anatomical ground truth. No points are removed
from native totals. The source-side knee/elbow plane checks find **zero** >20mm
crossings for either source, including the high-confidence subset.

Target regions reuse the independently inspected
[Astro/G1 geometry definitions](../segment-binding-audit/regions.py): actual
`head_link` mesh identity; limb families cut by shoulder/elbow/wrist lateral
coordinates and hip/knee/ankle heights; trunk split at waist height and halfway
to shoulder height. Head mesh identity is separate from body name: G1 head mesh
belongs to `torso_link`; Astro head is welded and moves with `waist_roll_link`.
Neither has a neck DOF. Tables retain actual mesh, body and first joint-bearing
ancestor separately. A correct rigid owner alone is not a correct anatomical match.

Cross-joint thresholds are canonical **axis-aligned T-pose cuts**, not full
bone-normal planes or motion errors: thigh >20mm below knee; forearm >20mm
proximal to elbow. Region precision counts compatible zones; coverage uses the
same4096 target reference samples and20mm distance, not held-out area or continuous
surface coverage. Neck compatible zones (`head shell`,`upper torso`) are an
explicit ambiguity convention and must not be pooled into head/face accuracy.

## Measured correspondence results

Head/face excludes neck. Counts retain source-specific denominators; no cross-model
slot or vertex identity is assumed. L/R entries refer to source left/right.

| Center | Source | Robot | Head/face→torso | Head/face→head shell | Thigh below knee L/R | Forearm proximal to elbow L/R |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| spine1 | SMPL-X | Astro | 250/353 (70.8%) | 87/353 | 106/359;94/339 | 43/137;42/132 |
| spine1 | SOMA | Astro | 234/320 (73.1%) | 62/320 | 77/392;62/373 | 23/129;26/135 |
| spine1 | SMPL-X | G1 | 0/353 | 353/353 | 0/359;0/339 | 1/137;0/132 |
| spine1 | SOMA | G1 | 0/320 | 320/320 | 0/392;0/373 | 0/129;0/135 |
| bbox50 | SMPL-X | Astro | 152/353 (43.1%) | 201/353 | 0/359;0/339 | 49/137;44/132 |
| bbox50 | SOMA | Astro | 109/320 (34.1%) | 211/320 | 0/392;0/373 | 27/129;28/135 |
| bbox50 | SMPL-X | G1 | 0/353 | 353/353 | 0/359;0/339 | 0/137;0/132 |
| bbox50 | SOMA | G1 | 0/320 | 320/320 | 0/392;0/373 | 0/129;0/135 |

At spine1, remaining Astro head/face slots reach shoulders/sensors; full
[results.json](results.json) preserves every destination and all segment coverage.
The high-confidence subset retains Astro head/face→torso **219/321 SMPL-X versus
212/298 SOMA** at spine1 and **126/321 versus92/298** at bbox50. G1 remains zero.
Thus neck-merging and uncertain skinning boundaries cannot explain the observed
head failure. A concrete viewer example is SOMA bbox50 slot4066: confident
head/face source paired to Astro torso.

For high-confidence Astro forearms, proximal-elbow crossings are25/105 and26/103
for SMPL-X versus8/110 and10/112 for SOMA at spine1;31/105 and28/103 versus12/110
and12/112 at bbox50. This supports reduced crossing in this source-template
comparison even after excluding ambiguous labels. It does not isolate whether
shape, horizontal arm pose, proportions or representation caused it.

Reduced knee crossing is not sufficient to declare better leg transfer. At
bbox50, Astro thigh-zone precision is93.6%/96.2% for SMPL-X versus80.6%/79.1% for
SOMA; SOMA sends more thigh points toward hip/pelvis zones. On G1 it is71.3%/73.7%
versus48.5%/46.4%. Similarly G1 forearm-zone precision falls55.5%/56.8%→41.1%/43.0%
at bbox50 as points extend distally. Zero proximal crossing misses these effects.

Coverage and precision answer different questions. Astro head-shell coverage is
100% within20mm for both sources despite substantial head/face leakage. G1 head
precision stays100%, while coverage at bbox50 is55.1% for SMPL-X and56.9% for SOMA.
Inspect the full transfer and coverage tables instead of a pooled score. Final
normalized weighted loss spans0.001671–0.001746; lower loss is not evidence of
anatomical correctness.

## Independent binding sensitivity

[Global-triangle validation](binding-validation.json) compares all32768 robot
slots with the preserved production nearest-vertex-candidate projector. It also
verifies the target meshes against dataset triangles/coordinates and both source
meshes against the audited human assets. The reference projector never increases
query-to-surface distance beyond200nm numerical tolerance.

The shortcut is not exact:221–290 slots per arm improve by >1µm with complete
search; maximum distance improvement is17.3–32.2mm. Actual owner changes are3–6
for Astro and141–163 for G1, with69–105 G1 changes at equal distance within1µm
(overlap/tie ambiguity). Spatial-zone changes are2–15 per arm. These are local
projection/ownership limitations, not evidence that every changed binding is
anatomically wrong.

**All eight head/face→torso counts and all forearm crossing counts are unchanged.**
Only the SOMA/Astro spine1 knee counts change77/62→78/61; all other knee counts
match. Thus the principal conclusions survive independent global projection.
Main tables and the viewer deliberately retain actual production bindings;
`*-exact-projection.npz` files preserve the separate diagnostic rather than
silently replacing production results.

## Real SOMA motion availability

The initial setup had no BONES-SEED BVHs or fitted actor shapes. This experiment
obtained the **official public `example_animation.usd`** from the same pinned
NVIDIA revision, retained its Apache-2.0 license/model card, and verified its Git
blob hash. Official CPU readers produce finite local/world transforms
`(931,78,4,4)`,24fps,time codes0–930 (38.75s). Source stage units are centimeters,
Y-up; reader output is meters; scales are unity. This is a real shipped animation,
not synthetic data. [Motion inventory](motion-inventory.json) and its script
record the exact source and verification.

It is not the HiPHI actor or clip and is not an installed UMR-ready BVH. No
USD-to-UMR adapter or matched HiPHI→SOMA pose inversion was run. BONES-SEED remains
gated and absent; using that route would require the user to obtain licensed BVHs
and the correct uniform/actor shape fit. No such action is needed for this
completed static experiment. The research note inspects the supported SMPL-X
identity backend and pose-conversion route; exact actor/surface/pose equivalence
would still require an additional validated control.

## Reproduction, inspection and validation

The commands below document this historical cohort and may write to its fixed
paths. Do not run them against retained evidence; adapt every destination to a
fresh cohort before reuse.

Working directory: `/data/workspace/motion_studio`; original UMR virtual environment.
Only experiment-local files are written. `prepare.py` refuses existing derivative
datasets; `run_correspondence.py` refuses existing checkpoints. Use a fresh output
folder for a new measurement; do not overwrite these records or force cache reuse.
The training driver has no build-all, retarget, view or simulation stage.
The copied NPZ retains the baseline's legacy `bbox_center_ratio=0.45` scalar;
it is unused by training and is not the derivative center. For bbox50, the
explicit translation in `prepare.py`, `center_modes=bbox_ratio_0.500000`, saved
root offsets, resolved config ratio0.5 and `preparation.json` define the actual
center. This inherited metadata is disclosed rather than rewriting measured
binary inputs after training.

```sh
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/human_weights.py > outputs/soma-correspondence-audit/human-weights.log 2>&1
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/prepare.py > outputs/soma-correspondence-audit/prepare.log 2>&1
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/run_correspondence.py
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/motion_inventory.py
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/source_template_comparison.py
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/audit.py > outputs/soma-correspondence-audit/audit.log 2>&1
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/validate_binding.py > outputs/soma-correspondence-audit/binding-validation.log 2>&1
externals/UMR/.venv/bin/python experiments/soma-correspondence-audit/verify_and_record.py
MPLCONFIGDIR=/tmp/soma-audit-mpl python3 experiments/soma-correspondence-audit/plot_audit.py
cp experiments/soma-correspondence-audit/viewer.html outputs/soma-correspondence-audit/viewer/index.html
cp experiments/soma-correspondence-audit/viewer.js outputs/soma-correspondence-audit/viewer/app.js
python3 -m http.server 8769 --bind 127.0.0.1 --directory outputs/soma-correspondence-audit/viewer
```

GPU training and the browser-visible server use host access. Before GPU work,
`nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv` showed
only the desktop process. The six command/status/time records, all actual training
commands, dataset/checkpoint/model/config/XML/mesh hashes and code hashes are in
[provenance.json](provenance.json); source binding/equality assertions are in
[validation.json](validation.json). Historical SMPL-X segment/mesh/plane results
were reproduced exactly. No prior results or canonical hashes changed.

Open [the actual-mesh inspector](http://127.0.0.1:8769/). It has eight clearly
separated source/target/centering arms, native19 filters, paired slot selection,
mesh/body/spatial-zone coloring, joint landmarks, grouped-LBS confidence and
raw/common labels. Target display is equal-height by default; metrics remain in
metres. Surface coloring computes the arm split over vertices, while exact slot
labels use their sampled range, so colored mesh boundaries are schematic.
Three.js0.165.0 comes from jsDelivr and requires network access.

Static evidence in ignored outputs:

- `segment-evidence-spine1.png`: native-joint-center comparison.
- `segment-evidence-bbox50.png`: common-bbox-center comparison.
- `viewer-soma-astro.png`: actual interactive mesh screenshot.
- Eight `*-audit.npz` files: full per-slot source/robot positions, labels,
  confidence, actual geometry/body/rigid ownership and slot IDs.
- `human-weight-diagnostics.npz`: independent human weights/rigs/labels and
  wrapper bindings; model derivatives remain local.

All eight target selections and head filters were checked in the in-app browser;
[the browser record](browser-verification.json) preserves visible slot details.
Both static figures and a100%-head-influence torso-bound slot4066 were visually
inspected. Independent full-triangle binding checks completed. Scripts compile; JSON parses;
references and whitespace checked. One intermediate audit read overlapped the
human-weights file being regenerated; it stopped with a ZIP error and was rerun
successfully only after that artifact was finalized. No failed partial report
was used. The standard Chrome connector was unavailable due to its occupied
profile; the in-app browser was used without stopping anyone else's browser.

Only seed0 was tested. Geometry identity and production binding acceptance do not
establish semantic truth. Confidence thresholds, anatomical grouping and 20mm cuts
are explicit audit conventions. No motion/contact quality, dynamic feasibility,
self-collision, foot slip, joint-limit behavior or rollout safety is established.
The completed stopping point is static inspection; no retargeting follows.
