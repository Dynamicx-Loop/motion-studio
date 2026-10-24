# UMR for Astro: research and experiment guideline

**For review — agree on the research direction before implementation or runs.**
Updated 2026-10-24. This is a basic guideline, not a detailed experiment procedure.

Our goal is to understand how official UMR performs on Astro, then use controlled
experiments to identify what improves its results.

We aim for **competitive, comparable Astro and G1 outcomes within the same source
model**, and **consistent SMPL-X and SOMA-X retargeting quality within each robot**.
These are research goals to test, not assumed equality. Assess binding quality
and motion quality separately with morphology-aware metrics; no acceptable
numerical difference is prescribed by this guideline.

1. **Use the broader official reference set, with G1 as the primary control.**
   Review official published/provided results for all shipped UMR embodiments,
   recording gaps where only assets/configs are available. For the matched Astro
   comparisons, focus on G1 with SMPL-X and SOMA-X where supported. Keep the
   official algorithm unchanged and document minimal custom-robot integration.
2. **Use the latest inspected fixed-fist Astro description.** Pin
   `astro_p2_43dof_dex3_1` at menagerie_x revision
   `d2070956558ffbf9226dcf74017d40740724d8d8`. This is the verified local revision;
   remote freshness has not been checked. Exact asset hashes are in the appendix.
3. **Compare segment bindings first, then retargeted motions, along both axes.**
   **Same robot:** compare SMPL-X versus SOMA-X on G1 and on Astro separately.
   **Same source model:** compare Astro versus G1 for SMPL-X and for SOMA-X.
   Matched attribution requires the same underlying motion/actor and validated
   dual representations; unpaired inputs or conversions remain exploratory.
4. **Freeze the baseline, then run controlled ablations for Astro.** Change one
   factor at a time, or explicitly plan interactions, so improvements can be
   attributed to the change being tested.
5. **Keep all previous runs as legacy artifacts.** Preserve them untouched and
   separate from the new baseline comparisons.

The intended matrix is **SMPL-X / SOMA-X × G1 / Astro**, with binding and motion
evaluation in each cell. The SOMA-X motion branch remains blocked by missing
BONES-SEED motion, matching actor shape and dataset rig. Available model assets
do not fill those gaps; any compatibility conversion must be labeled.

The broader shipped reference set is **PiPlusPro, Booster K1, Unitree G1,
EngineAI T800, Unitree H2 and the MimicKit humanoid character**. Official
demonstrations, published quantitative results and locally reproduced matched
comparisons are distinct evidence. Their coverage differs; this guideline does
not propose rerunning all embodiments or treating them as a common score table.
Existing local **UMR segment-binding audits already cover all six**; use them as
legacy references rather than proposing their generation again by default.

For future work, propose a **dedicated UMR experiment Git branch and worktree**.
A branch isolates tracked change history; separate worktree, environment, config
and output roots are needed to isolate working files, runtime and artifacts.
The Motion Studio root has no commits and contains uncommitted user work, while
external repositories have independent local changes. Preserve that state and
agree on the repository boundary before creating anything. No branch, commit,
worktree, push or experiment is authorized by this guideline.

Use [UMR paper study v1](../references/umr-paper-study-v1.md) as the versioned
methodology reference, separate from new experiment evidence. Controller and
dynamics evaluation remain future work. Detailed run choices can be settled
after this guideline is aligned.

## Supporting appendix — provisional protocol detail

The earlier detailed proposal is retained below for traceability and later
planning. It is supporting material, not an approved procedure or infrastructure
requirement. Specific sample sizes, pilot intervals, schemas and tooling choices
remain deferred. The unfinished scaffold remains paused.

### Objective and rationale

Establish what the pinned official UMR implementation does for the latest
inspected fist Astro description, with G1 as the primary matched control and
SMPL-X and SOMA-X as the two source-model branches. Official evidence for the
other shipped embodiments forms a broader reference layer, with coverage and
evidence type recorded separately. Observe correspondence/binding first, then
kinematic retargeted motion. Only afterward test improvements to Astro.

The accumulated legacy studies vary robot geometry, finger freedom, source
identity, centering, calibration and other settings. Pooling them cannot isolate
which change caused a difference. Individual controlled studies retain their
narrow conclusions, but none becomes the new baseline by relabeling it.

The two comparison axes test complementary hypotheses: Astro can achieve
competitive/comparable quality to G1 under a matched source, and each robot can
retain consistent quality across validated SMPL-X/SOMA-X representations.
Neither hypothesis requires identical trajectories or raw scores across different
morphologies. Interpret segment definitions, coverage denominators, scale,
available joints and contact geometry at the binding and motion stages separately.
Any numerical acceptance margin must be explicitly justified during later
experiment planning; none is invented or approved here.

All previous results, configs, checkpoints, trajectories, reports and validators
remain untouched in their current locations. They are **legacy artifacts**, not
members of the new baseline comparison. The older open-hand and later fixed-fist
cohorts remain separate even within the legacy index. Changing open hands to a
fixed fist changes geometry and finger freedom together.

### Verified starting point

Read-only inspection found the following. These are observations, not proposed
results or proof that the future runtime is ready.

| Item | Verified value or scope |
| --- | --- |
| menagerie_x local HEAD | `d2070956558ffbf9226dcf74017d40740724d8d8` |
| Asset | `robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml` |
| XML SHA-256 | `c688a4177a1ff5ba07764f9e310bb62c33d24a47b193259922a55b6c5fe88c66` |
| Fist-pose JSON SHA-256 | `65aa714e64a642058237351515951e3840982d0692cc04c079356e1eb0e0ed7b` |
| Visual mesh inventory | 51 tracked files, individually hashed |
| Mesh-map SHA-256 | `58c3c1d78fc799e5e3abd00cb22ace8cd0733f9acbc56272eb3c62f4373ea97f` |
| Entire tracked robot bundle | 75 files, individually hashed; no tracked changes in this variant |
| Official UMR local HEAD | `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; no tracked changes |

The [inspection manifest](../experiments/umr-astro-baseline-proposal/asset-inspection.json)
records all hashes, the exact map-digest encoding, local repository status and
78 tracked UMR source/config/document files. It is a proposal snapshot, not a
complete frozen execution environment.

No fetch was performed. Cached `origin/main` is
`dfbf8f13ac892dfb8b4b3f69a791e67ebc28d6be`, an ancestor of local HEAD. Therefore
“latest” here means **latest inspected local revision**, not verified latest
remote revision. Existing untracked files were preserved. The separate
`externals/UMR-astro-surface-experiment` checkout has local patches and is excluded
from the proposed unchanged-official-code baseline.

The asset describes 29 body hinges plus 14 finger hinges, a free root, no
actuators, visual meshes and separate collision primitives. Its `fist` keyframe
must be selected explicitly: the asset documentation says an ordinary reset
still selects the unchanged zero-joint pose. The description is a sample hand
mount, not a verified hardware assembly. The MJCF has intentional refinements
absent from the URDF; do not regenerate it from URDF for this baseline.

### Official embodiment reference set and evidence coverage

Verified on 2026-10-24 against pinned UMR
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`: the six base-embodiment configs below
match their committed bytes, and their config-relative XML paths exist. This is
source/asset verification, not compilation, motion reproduction or a result
quality measurement. The paper's benchmark source revision is not independently
established by this checkout pin.

| Base embodiment | Pinned shipped config | Declared target XML |
| --- | --- | --- |
| HiTorque PiPlusPro (Studio label PiPlus) | [PiPlusPro config](../externals/UMR/robot_configs/humanoid_retarget_hightorque_pipluspro_example.json) | `assets/PiPlusPro/xml/PiPlusPro_S_12L10A2G2H1W_ZedMini.xml` |
| Booster K1 | [K1 config](../externals/UMR/robot_configs/humanoid_retarget_booster_k1_example.json) | `assets/booster_k1/K1_serial_tpose_mjcf.xml` |
| Unitree G1 | [G1 config](../externals/UMR/robot_configs/humanoid_retarget_unitree_g1_example.json) | `assets/g1/g1_29dof.xml` |
| EngineAI T800 | [T800 config](../externals/UMR/robot_configs/humanoid_retarget_engineai_t800_example.json) | `assets/t800/xml/serial_t800_tpose_mjcf.xml` |
| Unitree H2 | [H2 config](../externals/UMR/robot_configs/humanoid_retarget_unitree_h2_example.json) | `assets/h2_description/H2_stl_mjcf.xml` |
| MimicKit humanoid character | [MimicKit config](../externals/UMR/robot_configs/humanoid_retarget_mimickit_humanoid_example.json) | `assets/mimickit/humanoid.xml` |

Evidence coverage must stay explicit:

- **Published quantitative results:** the official paper states all quantitative
  evaluations use **Unitree G1**. Its tracking and interaction tables are not
  six-robot scores and do not share the local Astro binding metric definitions.
  [Paper v2, §IV and Tables II–IV](https://arxiv.org/html/2609.02134v2#S4).
- **Published qualitative results:** §IV-A / Figure 5 presents four source
  representations and five humanoid embodiments. The accessible text does not
  enumerate their individual labels, so this inspection does not map those five
  to every shipped config or assert six-cell result coverage.
  [Paper v2, §IV-A](https://arxiv.org/html/2609.02134v2#S4.SS1).
- **Official project demonstrations:** the project page labels Studio examples
  PiPlus, Adam and Fourier N1, and separately demonstrates racket-equipped G1.
  These are qualitative references. Adam/N1 demonstrations do not imply their
  complete assets ship in this pinned repository, and G1+racket is a variant,
  not another base embodiment. [Official project page](https://hanyang9.github.io/UMR/).
- **Provided Studio assets:** the preserved 2026-10-23 official manifest lists
  PiPlus, K1, G1 and T800 preset bundles, with no learned correspondence checkpoint
  files. All five saved webpage/manifest/runtime source hashes were reverified
  here; current live manifest retrieval was unavailable. These bundles are
  selectable assets/T-poses, not precomputed comparable results.
  [Official inventory](../experiments/all-robot-segment-audit/official-inventory.json)
  and [preserved manifest](../outputs/all-robot-segment-audit/official/manifest.json).
- **Pinned repository provision:** no tracked generated `output/`/`outputs/`
  files, `correspondence_slots` files, or `.pt/.pth/.ckpt/.safetensors`
  checkpoints were found. Source motions and task auxiliary records are present;
  their existence is not a complete all-embodiment retarget-result distribution.
- **Local legacy comparisons:** the prior all-robot audit contains locally
  trained/reused static results, not official released results. It performed no
  motion runs, and its MimicKit primitive geometry used an experimental patch.
  Preserve its findings as legacy with those caveats, not as an unchanged-official
  baseline. [Audit record](../experiments/all-robot-segment-audit/README.md).

Existing local coverage was checked directly against the saved JSON records:

| Legacy record | Verified coverage | What it does not establish |
| --- | --- | --- |
| [All-robot results](../experiments/all-robot-segment-audit/results.json) | 10 static SMPL-X arms × 19 segment rows: all six base embodiments, G1 racket/sphere-hand variants, and Astro visual/primitive diagnostics | Not official published outputs, not six new-baseline runs, and not SOMA-X coverage of all six robots |
| [Native-centering results](../experiments/all-robot-segment-audit/native-center-results.json) | Five additional centering arms × 19 rows; with the preceding record, 15 arms / 285 rows | Sensitivity variants, not five more base embodiments or pooled comparable scores |
| [SMPL-X/SOMA audit](../experiments/soma-correspondence-audit/results.json) | Eight static arms: two source models × Astro/G1 × spine1/bbox50; 152 native19 and 144 common18 rows | Static templates differ in identity/geometry; not a matched dual-model motion comparison |
| [Legacy fixed-fist static](../experiments/astro-fist-static-v1/results.json) and [wrist candidates](../experiments/astro-fist-wrist-v1/results.json) | Each has the same eight-cell static layout and 296 segment rows; raw/candidate are separate variants | Historical patched experiments, not the new unchanged-official baseline |
| [Legacy fixed-fist motion](../experiments/umr-motion-fist-v1/results.json) | Eight SMPL-X-only motion arms: Astro/G1 × two centers × raw/candidate | No SOMA-X motion arm; cannot complete the source-model axis |

These are **UMR** records. GMR is a separate method in external comparisons;
the wording of the request does not relabel these local audits as GMR runs.
Review existing saved bindings before deciding what genuinely needs a new run.

G1 shared-HiPHI, racket and sphere-hand variants, and PiPlusPro/K1 alternate
visual XMLs remain explicitly named variants. G1 large-box references an absent
box mesh in the recorded inventory. Standalone preset names AGIBOT A2, Fourier
N1 and PND Adam Lite do not have complete shipped model paths in that inventory;
they are not silently added to the six available base embodiments. Source/task
defaults are not additional robots. See the
[full inventory](../experiments/all-robot-segment-audit/inventory.json).

For future reference entries, retain embodiment/variant, original source URL or
pinned path, paper/code version, source motion/model, evidence type (published
quantitative, published qualitative, provided artifact, local reproduction),
metric definition and coverage gaps. Missing per-robot metrics stay unknown.
G1 remains the primary matched Astro control; broader references supply context
without authorizing additional runs or a pooled ranking.

### Baseline boundary and comparison matrix

**Proposed rule:** keep official UMR source unchanged and start from its pinned
defaults, resolving their inheritance explicitly. Use a separate, reviewable
custom-robot integration config for asset paths, named joint order, coordinate
transforms, body calibration pose, fist policy and robot-specific correspondence
inputs. Record every config delta and why it is necessary.

Do not inherit old wrist calibration, bbox50 centering, objective weights,
sampling modifications, torso tuning or filter changes. Use official `spine1`
centering initially. Keep the official filter selected by resolved defaults;
do not silently turn it off. Fresh correspondence training is from scratch;
no resume path was found in the inspected workflow, and this is not universal
model fine-tuning.

The HiPHI defaults point to G1-specific shared correspondence files. Astro must
receive its own correspondence assets through official configuration. The
recommended comparison trains fresh, actor-specific correspondences for both
targets rather than inheriting a historical G1 checkpoint. This is an explicit
experimental input/config choice, not a claim to reproduce the shipped demo
unchanged. Any code change found necessary is a separately labeled adaptation
and pauses the claim of an unchanged official baseline for that branch.

| Source branch | Astro fist | Matched G1 | Support and input status |
| --- | --- | --- | --- |
| SMPL-X | Binding and motion | Same actor, clip, frame interval, source samples and settings | Official HiPHI/SMPL-X path exists. Local HiPHI evidence is available; new input/runtime preflight still required. |
| SOMA-X | Binding and motion | Same SOMA actor/shape, clip, rig, interval and source samples | Official BONES-SEED/SOMA path exists. Matching BONES-SEED motion, actor fit and dataset rig remain missing. |

This is four source/robot cells, evaluated at both internal UMR stages. A cell
may be blocked; a public neutral SOMA template does not substitute for missing
motion or its actor geometry. Uniform BONES-SEED needs the shared
`soma_base_fit_mhr_params.npz`; proportional sequences need the exact `Axxx.npz`,
plus the dataset BVH/USD rig. No dataset access terms were accepted here.

The local SOMA-X setup also uses a documented compatibility overlay: it adds
public rig arrays to a derived neutral NPZ. Official UMR supports a SOMA-X-backed
adapter, but this local asset representation is an **adaptation**. Hash its
originals, derived file and conversion recipe separately. Do not silently call
it equivalent to a wholly unmodified asset path; decide whether it is acceptable
for an explicitly labeled adapted branch or whether that branch stays blocked.

Both comparison axes are central at **both** stages:

- **Hold the robot fixed:** compare SMPL-X versus SOMA-X on G1, and separately on
  Astro. This asks how the source representation affects each robot's result.
- **Hold the source model fixed:** compare Astro versus G1 under SMPL-X, and
  separately under SOMA-X. This asks how the target embodiment affects results.

For matched attribution, use the same underlying motion and actor, with validated
SMPL-X/SOMA-X representations, documented fitting/conversion error, comparable
frame intervals and a justified common segment definition. A static comparison
must similarly distinguish source shape/identity from representation. A HiPHI
SMPL-X clip and an unrelated BONES-SEED SOMA clip remain exploratory observations,
not a source-model ablation. Missing inputs leave cells blocked; they do not
remove either comparison axis from the research goal. Matched dual-representation
motion equivalence is not established today.

### Evaluation contract

UMR has two internal comparison stages. Training and binding receive distinct
provenance inside stage 1; optimization and trajectory filtering receive distinct
provenance inside stage 2. Downstream controller/dynamics execution is a separate
future gate, not a third UMR stage or a current claim.

**Stage 1 — correspondence and mesh binding.** Preserve training samples, source
identity/shape, source and target sampling seeds, complete hyperparameters,
checkpoint/slot hashes and binding/projection policy. Evaluate native labels
and a documented common label set separately; never pool native19 and common18
denominators. Reuse existing report normalizers and audit checks after reviewing
their applicability and redirecting their output paths.

Report per-segment slot counts, compatible-zone precision/leakage, reference
sample coverage within 20 mm, physical hand-mesh membership, projection distance
and joint-plane crossings. Give each measure its denominator, units and label
definition. Anatomical hand-zone membership is not physical hand-mesh membership.
Static correspondence quality is not motion quality.

**Stage 2 — kinematic motion.** Preserve source frame IDs, exact FPS and interval,
all coordinate conversions, joint order and root quaternion convention. Keep
pre-filter and exported post-filter arrays and metrics separate. If unchanged
official execution does not expose an intermediate, mark it unavailable and
review any proposed observation mechanism before using it; do not silently
monkey-patch the baseline.

| Measure | Required definition |
| --- | --- |
| Worst visual below-floor extent | `max(0, -min(z))`, over the declared visual mesh vertices and frames against an explicitly defined floor; report mm. Also report minimum signed height, thresholded frame count and denominator. |
| Selected surface-slot clearance | Separate metric on the actual constrained slots; no inference about all mesh vertices. |
| Collision-geometry clearance / self-penetration | Separate geometry, pair exclusions, signed-distance/contact convention and aggregation. Unknown until evaluated; visual extent is not a substitute. |
| Joint-limit compliance | Named configured bounds, tolerance in radians, minimum margin and violating joint-frame count. |
| Motion smoothness | Time-normalized derivatives, FPS, finite-difference rule and joint subset; distinguish body-only from all hinges and fixed fingers. |
| Contact / slip | Use measured or declared contacts when available; height-based ankle stance remains an explicitly labeled proxy. |
| Tracking fidelity | Label physical landmark proxies separately from learned-surface residuals and weighted solver objective. |

The legacy values 22.69/17.38 mm and 26.55/25.89 mm are **worst visual below-floor
extents**, raw/candidate in the old fixed-fist cohort. They are not generic
collision depths or contact forces and are excluded from the new baseline.
The existing report README opening values 28.14/30.76 and 37.05/56.71 mm belong
to the older open-hand cohort; that file was not edited.

Solver temporal penalties use frame differences without time normalization;
FPS/stride changes can change the effective problem. An optimizer step bound is
not a physical velocity limit. The inspected defaults disable robot
self-penetration penalties and hard constraints. Zero joint-limit violations
therefore do not establish collision freedom, dynamic feasibility or hardware
safety. Force and controller metrics remain unmeasured.

The earlier [29DOF head-objective study](umr-head-objective-investigation.md)
exists: disabling head fitting slightly increased backward torso pitch at its
inspected frame. It does not establish the effect on the new fist cohort.

### Reproducibility and standardized evidence

Before any run, create a unique cohort/run ID and a new output directory. Never
overwrite or reuse an old run as if it were fresh. Resolve all paths from a
configurable workspace/data root; capture both the resolved path and content
identity. Record:

- Exact code revision, tracked patch and explicitly included untracked source;
  independent runtime interpreter, dependency versions/lock, driver/device and
  relevant non-secret environment settings. A commit alone is insufficient.
- Motion, actor shape/gender/rig, model weights, XML, mesh closure, pose preset,
  configuration and checkpoint hashes, separated by stage and dependency.
- Source frame IDs, units, FPS/timestamps, axes/transforms, quaternion ordering,
  named joint order, source finger/head policy, trimming, resampling, scaling and
  any information loss or conversion assumptions.
- Effective source/target sampling, training and solver seeds; all resolved
  hyperparameters. An inherited config seed must not replace a measured
  preparation seed. Current legacy target sampling used 9000 despite other
  seed fields in its configs.
- Exact argv and cwd, stage inputs/outputs, start/end times, return code, logs,
  resource measurements, failures and skipped stages. Failure is evidence;
  never replace it with a success-shaped record.

Proposed standardized result identity is
`cohort + run + source/actor + robot + stage + variant + seed`. Every metric has
a definition/version, value or explicit null, units, population/denominator,
aggregation, geometry, trajectory stage and source evidence reference. Track
`recorded`, `derived`, `not_measured`, and `retrospective reconstruction` versus
`tested reproducible rerun` explicitly. Seal manifests with content hashes;
hashes detect edits but do not make ordinary local storage write-once.

Every future experiment report should also carry a separate, versioned
`literature_studies` field. This records the research that informed the protocol,
not experimental evidence or validation of the run. Pin the exact study version
and file hash used when interpreting results; a later study revision must not
silently change the meaning of an already published report.

The proposed report metadata contract is:

```json
{
  "literature_studies": [
    {
      "study_id": "umr-methodology",
      "version": "v1",
      "path": "references/umr-paper-study-v1.md",
      "sha256": "f3d540a28ae372b0a4819641899e2ad4f03ed1e4f227ff7b3980cadc7fa459ba",
      "status": "published",
      "published_date": "2026-10-24",
      "source_task": "01a16ceb-3496-71a5-81db-f29b6f867039",
      "referenced_sections": [
        "Identity and evidence boundaries",
        "Correspondence learning, binding, and adaptation",
        "Per-frame optimization and contact interpretation",
        "What the paper establishes",
        "Reuse contract and next questions"
      ],
      "role": "methodology_and_protocol_rationale",
      "unknown_reason": null
    }
  ],
  "experiment_evidence": []
}
```

The published [UMR paper study v1](../references/umr-paper-study-v1.md) has been
verified against the SHA-256 above. Its listed sections support the protocol's
methodology and evidence boundaries. Preserve the study's own paper/code revision
and citation provenance. `experiment_evidence` separately references actual run
manifests, measured results, validation records and their hashes. A literature
statement or code-derived expectation must never be presented as a measurement
of Astro.

The study's section titled “Current Astro evidence and its limits” describes the
latest historical fixed-fist cohort. Under this newly agreed protocol, those
findings are **legacy evidence**, excluded from the new baseline comparisons;
the study's historical use of “current” does not promote that cohort into the
new baseline. The study file is preserved unchanged. Its publication and this
reference update do not lift the review gate.

Preflight should fail on missing motion/actor/rig, hash drift, LFS pointers,
unresolved model compatibility, unmatched controls or unsafe output paths.
File availability, numerical runtime validation and execution authorization are
separate gates. A passing file check must never launch training. Existing
validators that write fixed historical paths must not be run as-is.

After approval, normalize legacy records into a new derived index without
rewriting them. The inspected report covers 52 static arms and 1,924 segment
rows. Four saved motion cohorts provide 24 motion arms. Early heterogeneous
audits and the head ablation should be inventoried under their own definitions,
not forced into a misleading pooled score. No derived index has been generated
in this task.

### Tentative pilot option and later ablations

This is an earlier planning option, not part of the guideline approval or a
selected experiment. Its scope and parameters remain deferred.

After review and a successful cheap preflight, start with **one SMPL-X actor,
one official centering rule, one seed and two fresh static correspondence/binding
arms: Astro fist and G1**. Use official training defaults and the approved minimal
robot integration. Review stage-1 binding evidence before authorizing a small
motion continuation. This is an engineering pilot, not a statistical benchmark.

For that continuation, propose a declared 240-frame prefix of the bundled
`Getting_up-get_up_0004` source at its native stride 1, identically applied to
both robots, with source FPS measured from the actual input. A prefix is a
limited test with filter boundary effects; it is not the old 1,823-frame,
stride-3 cohort. Decide the interval before execution. Expand to the full clip,
additional motions and seeds only after the pilot is reviewed. Keep the SOMA-X
rows blocked until their input and adaptation decisions are resolved.

After a baseline is accepted, change one factor at a time: for example centering,
wrist calibration, head objective, or finger freedom. Hold all other hashes and
settings fixed and compare matched Astro/G1 arms where applicable. If interacting
factors are the question, use an explicitly planned factorial design. Never
combine “improvements” first and attribute their aggregate effect to one change.

### Deferred execution-planning questions

These questions belong to later experiment planning. They are not five decisions
the user must make to agree on the basic research guideline.

1. **Asset freshness:** accept the inspected local d207095 bundle, or check the
   remote before freezing? The proposal currently makes no remote freshness claim.
2. **Fist policy:** recommended fixed named finger coordinates throughout
   initialization, optimization and export, using official supported joint-limit
   configuration. Merely loading a fist keyframe does not enforce this. Approve
   this as a custom-robot condition and verify it without source changes.
3. **SOMA-X branch:** accept an explicitly labeled compatibility-asset adaptation,
   or hold for a fully compatible official asset layout? Matching dataset motion,
   actor fit and rig are still required either way.
4. **Pilot scope:** accept the SMPL-X two-arm static pilot first, followed only
   after review by the proposed 240-frame native-rate motion pair? Alternatively
   wait until all four source/robot cells are ready.
5. **Comparison inputs:** retain both axes as the research goal; identify which
   cells can support matched comparisons and label the others exploratory or
   blocked until equivalent motion/actor inputs and conversion confounds are
   established.

### Work already started, now paused

Before the review gate arrived, eight additive draft implementation files were
created: two JSON schemas and six Python package files under
`scripts/experiment_support/`. They are **unfinished and untested**, have no CLI,
and have not produced a derived index or launched an experiment. In particular,
the draft legacy adapter still labels the previous fixed-fist cohort “current”;
that conflicts with the newly agreed all-legacy boundary and must be revised
after approval. It is not an accepted contract or ready-to-run delivery.

These draft files remain in place; no rollback, reset, clean, stash, commit,
push, package installation, asset upload or cloud provisioning occurred. The
only work after the review gate was read-only inspection and preparation of this
proposal and its supporting hash manifest. Numerical/model/GPU validation was
not attempted. No scientific or operational decision above is silently resolved
by the presence of draft code.
