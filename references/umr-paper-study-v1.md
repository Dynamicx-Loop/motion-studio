# UMR paper study v1: method, implementation, and Astro evidence

Date: **2026-10-24**. Status: versioned research record; no new experiment.

Study finding: UMR learns reusable static surface correspondence, then performs
kinematic motion optimization. Astro adaptation must validate correspondence,
motion references, and downstream control separately. Current evidence supports
fresh correspondence training and optional geometric calibration, not a validated
universal-model fine-tuning procedure or dexterous-hand controller.

Suggested citation: *Motion Studio, UMR paper study v1*, 2026-10-24,
`references/umr-paper-study-v1.md`. Cite the original paper separately. Substantive
future revisions should receive a new versioned report rather than silently
changing the evidence underlying an experiment's citation.

## Identity and evidence boundaries

**Unified Motion Retargeting for Humanoids with Learned Point Cloud Correspondence**,
Hanyang Cao, Yuetong Fang, Taesoo Kwon, Runyi Yu, Ji Ma, Jing Tan, Yangchen Zhou,
Baoze Du, Yi Gu, Yukang Gao, Ruoli Dai, Lei Han, and Renjing Xu.
The inspected paper is **arXiv:2609.02134v2, 7 September 2026**.
References: [official version](https://arxiv.org/abs/2609.02134v2),
[supplied full text](https://drive.google.com/file/d/1k_xqtsMGZTD9yBR-H5cvZbiZzrI9wS5X/view),
[project](https://hanyang9.github.io/UMR/).

This note distinguishes four evidence classes:

- **Paper:** statements and equations in the inspected version.
- **Code:** behavior inspected at UMR revision
  `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
- **Recorded result:** existing local experiment artifacts, not rerun here.
- **Inference:** mathematical interpretation or an implication requiring validation.

The complete extracted paper text, including tables and references, was read.
PDF visual pagination was unavailable, so citations use verified sections and
equations, not page numbers. Zotero's local API probe was blocked with `Errno 1`
(`Operation not permitted`); the supplied Drive copy provided the full text.
Research followed the primary-source approach in the
[research skill](skill://mattpocock-skills@mattpocock/home/android/.codex/plugins/cache/mattpocock/mattpocock-skills/1.3.1/skills/engineering/research/SKILL.md).
The background agent was explicitly requested with GPT-6 Astra / High;
actual runtime model/effort was not independently
verifiable from exposed metadata. No session storage was inspected.
Only this report and its reading-index entry were added; no training,
retargeting, installation, asset change,
commit, upload, or independent rerun of recorded validations occurred.

## Motivation and the reusable interface

**Paper, §§I and III-A:** sparse manually paired joints encode particular skeletons
and miss contact-relevant surface geometry. UMR instead uses ordered exterior
surface points as shared human–robot anchors. It learns correspondence in aligned
canonical T-poses, binds those points to meshes, then solves robot configurations
frame by frame. Correspondence learning and motion solving are separate stages.

The source interface requires a canonical source mesh and its posed surfaces over
time; the target requires robot geometry, kinematics, limits, and an aligned
canonical configuration. Outputs are robot generalized-coordinate trajectories,
not control policies or force commands. Mesh topology and skeleton topology need
not match. The implementation's adapters include SMPL-X/HiPHI, LAFAN1, SOMA/BONES-SEED,
humanoid characters, GRAIL, OmniContact, OMOMO, AdaPT and NR sources; that list
does not establish that all adapters or datasets have been exercised locally.
[Upstream source interface and adapters](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/README.md#L46-L83)

“No manual mapping” concerns human-to-robot correspondence pairs. It does not mean
no canonical-pose preparation, source geometry, segmentation, or weighting.
Paper §III-B transfers human segment labels through the learned ordering; §IV-A
uses source-specific segmentation, treating its unsegmented scanned mesh as one
region. Inference: geometric ordering alone cannot prove anatomical ownership,
finger identity, or suitability of every surface match.

## Correspondence learning, binding, and adaptation

**Paper, §III-B, Eq. 1:** an ordered human cloud \(X_h\) supplies slot indices;
an unordered robot cloud \(X_r\) supplies target geometry. A PointNet-style encoder
and MLP decoder predict residual coordinates:

\[
\widehat X_r=X_h+D_\theta(E_\theta(X_r)),\qquad
\widehat x_i^r=x_i^h+d_i.
\]

Equations 2–5 define
\(L_{corr}=\lambda_cL_c+\lambda_rL_r+\lambda_eL_e\), where

\[
L_c=\frac1N\sum_i\min_j\|\widehat x_i^r-x_j^r\|^2
+\frac1N\sum_j\min_i\|x_j^r-\widehat x_i^r\|^2,
\]
\[
L_r=\frac1{NK_r}\sum_i\sum_{\ell\in N_r(i)}
\exp(-\|\widehat x_i^r-\widehat x_\ell^r\|^2/r^2),\qquad
L_e=\frac1{|E|}\sum_{(i,\ell)\in E}\|d_i-d_\ell\|^2.
\]

Chamfer fits the target surface, repulsion discourages collapse, and geodesic
edge regularization encourages coherent deformation. These losses do not provide
anatomical correspondence ground truth. In §III-C, human points subsequently
follow their source meshes through barycentric transport; robot points follow
link-local bindings through forward kinematics.

**Code:** training reads static template point clouds, optional mesh/face metadata,
and normalization records. It constructs a new model and AdamW optimizer, then
starts at epoch 1. The inspected CLI has no checkpoint-resume/fine-tuning option.
It exports checkpoints and slots; the pipeline can reuse compatible slots.
Thus existing Astro adaptation is fresh correspondence training or slot reuse,
not demonstrated fine-tuning of a universal pretrained retargeter.
[Dataset and architecture](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L101-L298),
[training entry point](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L644-L750)

The paper does not specify concrete network widths, point count, epochs, optimizer,
learning-rate schedule, loss coefficients, repulsion neighborhood/radius, or a
fine-tuning protocol. Those reproduction details must come from pinned code and
resolved configurations. Code additionally supports a residual-magnitude penalty
absent from paper Eq. 2; its weight is zero in the current Astro configuration.

**Recorded configuration:** current Astro training uses 4,096 target samples,
sampling seed 9000, 500 epochs, training seed 0, fixed-template mode and batch size
1. Chamfer/repulsion/edge weights are 1/.002/.4; geodesic k is 32. Per-sample-height
normalization, source centering and actor identity are part of the correspondence
contract. They affect geometric alignment without independently establishing
anatomical correctness. Reuse across SMPL-X betas is disabled.
[Protocol](../outputs/artifact-archives/experiment-reset-20261104/experiments/astro-fist-static-v1/README.md),
[resolved configuration](../outputs/artifact-archives/experiment-reset-20261104/experiments/astro-fist-static-v1/smplx_astro_bbox50-resolved.json)

Inference: changing actor shape, target visual geometry, canonical hand pose,
normalization or slot order requires a compatibility review and usually new
sampling/binding or training. Upstream compatibility checks primarily inspect
sample names and training mode, not complete geometry hashes. Frozen manifests
are stronger evidence than a matching robot name.
[Compatibility checks](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/humanoid_retarget_pipeline.py#L390-L464)

## Per-frame optimization and contact interpretation

**Paper, §III-C, Eqs. 6–8:** robot configuration \(q_t\) minimizes
\(\|r_p(q_t)\|^2+\|r_c(q_t)\|^2\). Pose rows combine
\(\sqrt{w_i^p}(x_i^r-x_{t,i}^h)\) and
\(\sqrt{w_i^n}(\bar n_i^r-\bar n_{t,i}^h)\);
normal targets express orientation changes relative to canonical bindings.
Contact rows are \(\sqrt{w_i^c}(c_i^r-c_{t,i}^h)\) on the active contact set.

Equations 9–11 choose the human point's nearest environment point
\(y_{t,\pi(i)}\), define both contact vectors relative to that same point, and
activate points whose source distance is within \(\tau_c\).
**Inference:** with this identical environment point,

\[
(x_i^r-y_{t,\pi(i)})-(x_{t,i}^h-y_{t,\pi(i)})=x_i^r-x_{t,i}^h.
\]

That contact residual is additional positional emphasis on an environment-selected
subset. The environment still controls activation and weighting; this observation
does not make every implemented contact term redundant or imply force constraints.

**Code qualification:** source and retarget object sizes can differ, and short
source vectors can be snapped to zero; cancellation then does not reduce to the
same source-position residual. Ground height and persistent anchor terms are
separate. The inspected self-contact branch uses a one-sided pair-distance
residual when robot distance is below source distance, rather than the paper's
generic vector expression.
[Object preparation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1260-L1322),
[contact residuals](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1811-L1908)

**Paper, Eqs. 12–14:** each local update solves

\[
\min_{\Delta q}\frac12\|r+J\Delta q\|^2+\frac\mu2\|\Delta q\|^2
\quad\text{s.t.}\quad
q^-\le q_t+\Delta q\le q^+,\quad A_t\Delta q\le b_t,
\quad\|\Delta q\|_2\le\eta.
\]

Floor rows are \(-J_i^z\Delta q\le z_i^r-z_f\) for active near-floor points.
The exact L2 bound makes this a convex quadratic conic subproblem, despite the
paper's QP terminology. Code assembles \(P=J^TJ+\mu I\), \(g=J^Tr\), uses
Clarabel cones, and integrates the increment with MuJoCo. This path is custom
kinematic optimization, not Mink or an RL controller.
[Matrix/cone assembly](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L1616-L1751)

Paper Eq. 6 contains no explicit velocity/acceleration penalty despite temporal
consistency language. Code adds scalar-joint first and second frame differences,
initializes each frame from its predecessor, and supports trajectory filtering.
Those differences lack explicit division by frame duration: changing FPS changes
their physical interpretation. The optimization step limit is not a physical
velocity limit, and previous-pose initialization is distinct from warm-starting
Clarabel's internal state.
[Smoothing](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1910-L1918),
[sequence initialization](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L2700-L2751)

## What the paper establishes

**Paper, §IV:** all quantitative evaluation uses Unitree G1. Four source formats
and five embodiments appear qualitatively in §IV-A. LAFAN1 tracking compares 40
motions using BeyondMimic; success means completing a reference window without
termination, not direct ground-truth correspondence accuracy. Tables II–III show
advantages over GMR and competitive, not uniformly superior, Unitree results.

The SONIC comparison changes two factors: **SOMA-Proportional + UMR** versus
released **SOMA-Uniform + GMR** references (§IV-B, Fig. 6). Its roughly 10% late
training gain without the SMPL encoder therefore supports the combined pipeline,
not an isolated causal retargeter improvement. With the SMPL encoder, performance
is reported comparable. Actor geometry may help, but this design does not
separate its contribution.

Table IV favors UMR on Carry, Kick, Push, Stair and Slope; **Chair favors
OmniRetarget** on success and joint error. Downstream policy results and selected
real-robot demonstrations establish useful references for those controllers,
not general physical feasibility. Table I's 25.79-second setup and 65.29-FPS overall
throughput were measured on an RTX 4070 Ti SUPER and Core Ultra 7 265KF over
LAFAN1, not on Astro. The paper used RTX 4090 GPUs for downstream policy training.
Section V explicitly identifies mesh/canonical-template dependence and leaves
dexterous hands and multi-agent interaction for future work.

## Current Astro evidence and its limits

**Recorded result:** the current fixed-fist cohort uses
`astro_p2_43dof_dex3_1`, menagerie commit
`d2070956558ffbf9226dcf74017d40740724d8d8`, XML SHA-256
`c688a4177a1ff5ba07764f9e310bb62c33d24a47b193259922a55b6c5fe88c66`.
It has 29 body joints plus 14 finger coordinates held to a named fist preset.
Four Astro trainings and eight HiPHI motion solves are recorded, with G1 static
slots reused as documented controls. Each solve contains 1,823 frames from
`0:5468:3`, approximately 30 Hz.
[Asset manifest](../outputs/artifact-archives/experiment-reset-20261104/experiments/astro-fist-static-v1/canonical-asset.json),
[motion record](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-motion-fist-v1/README.md)

| Astro centering | Raw worst visual floor penetration | Wrist candidate |
| --- | ---: | ---: |
| bbox50 | 26.55 mm | 25.89 mm |
| spine1 | 22.69 mm | 17.38 mm |

These are negative visual minimum heights converted to penetration magnitudes.
Saved checks report finite outputs, zero configured joint-limit violations, and
fixed-finger errors below `1e-7` rad before and after filtering. They were inspected,
not rerun. The wrist candidate remains optional; it is a geometric remap, not
retraining or validated finger correspondence.
[Results](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-motion-fist-v1/results.json),
[validation](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-motion-fist-v1/validation.json),
[finger checks](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-motion-fist-v1/fixed-fist-validation.json)

Do not substitute older open-hand penetration numbers for this cohort. Open-to-fist
changes geometry and finger freedom together, preventing an isolated pose-effect
claim. Nor does old 29-DOF head-on/off evidence establish the same result for this
43-DOF cohort: the earlier controlled prefix found head-off slightly increased
backward lean, while source upper chest already leaned backward.
[Historical ablation](../docs/umr-head-objective-investigation.md),
[cohort disclosures](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-binding-report/README.md)

Current configurations disable robot self-penetration cost and its hard constraint.
Surface-slot floor constraints do not ensure complete visual clearance after LQR
filtering. Report raw and filtered trajectories separately: solver cost is an
aggregate pre-filter quantity, not a post-filter surface residual. Inferred stance
from ankle height is a proxy, not measured contact/slip. Root-relative landmark
errors include morphology and center differences; all-hinge smoothness includes
constant fingers. One iteration per frame, one clip and one training seed do not
establish convergence or generalization.
[Configuration](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-motion-fist-v1/smplx_astro_bbox50_raw.json),
[metric definitions](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-motion-canonical-v1/README.md#evaluation-and-limitations)

## Reuse contract and next questions

Future reports should cite **this path, paper v2, and both full source revisions**.
Keep raw baselines, frozen assets, original clips and historical records immutable;
create separately named variants. Record source and model hashes; tracked patches
and untracked runtime files; environments; commands; resolved configs; seeds;
sampling, normalization, centering, segmentation and bindings; actor shape;
joint order/addresses, units, axes and quaternion order; source frame IDs, FPS,
trimming/resampling; fixed fingers; solver/filter settings; raw/filtered outputs;
metric definitions, tolerances and failed runs. Canonical UMR had no tracked edits
at inspection, while the separate experiment checkout had local modifications;
the baseline commit alone does not reproduce that checkout.

The fixed-fist [preparation record](../outputs/artifact-archives/experiment-reset-20261104/experiments/astro-fist-static-v1/preparation.json)
pins the experimental tracked diff SHA-256 to
`5d9feed17c5c70f4bc42df85093540d6147148212880b48cae5d125ce8b02b8c`;
its [preserved patch](../outputs/artifact-archives/experiment-reset-20261104/experiments/astro-fist-static-v1/UMR-astro-surface-experiment.patch)
must accompany the experiment's other source hashes. The experimental checkout
currently has six modified tracked scripts. Its results must not be described as
unmodified upstream results. Conversely, the inspected upstream revision is a
source snapshot for this study, not a verified identification of the exact commit
used in the paper's benchmark runs. Record these distinctions even when a
numerical comparison appears to reproduce earlier measurements.

Priorities are post-filter surface/contact residuals, reliable whole-mesh collision
checks, FPS sensitivity, additional clips/seeds, independent hand correspondence
evaluation, and controlled current-model objective ablations. BONES-SEED remains
blocked by missing actual motion BVH, matched actor-fit NPZ and dataset rig BVH/USD;
installed SOMA runtime assets and static neutral bindings are not substitutes.
[Exact missing inputs](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-motion-canonical-v1/BONES-SEED.md)

A separate downstream-control gate must assess tracking, balance, forces, actuator
and torque limits, friction, collision clearance and robustness before any physical
execution claim. Kinematic reference quality, policy training success and hardware
validation are distinct outcomes, as required by the
[workspace comparison workflow](../docs/workflow.md).
