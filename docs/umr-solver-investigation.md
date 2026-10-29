# Official UMR: retargeting methods and solver stack

Investigated 2026-10-22 by inspecting source code. Official checkout:
`externals/UMR`, commit `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
Unofficial comparison: `longchengzhuo/Unified-Motion-Retargeting`, commit
`0aa1855fe4f65a73681ffbd1d9f95ab1c2bad9ca` (read-only temporary checkout).
The findings describe these revisions; they are not benchmark results.

## Direct answer

**Official UMR uses MuJoCo plus a custom constrained least-squares retargeter,
solved directly with Clarabel. It does not use Mink in the inspected retargeting
path.** Its learned correspondence stage uses a PyTorch network trained with
AdamW. The unofficial reproduction really does use Mink, but that is its own
implementation choice, not evidence that official UMR depends on Mink.
The official pipeline selects its training and retarget scripts explicitly;
the retarget code calls the project's own Clarabel wrapper.
[Pipeline dispatch](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/humanoid_retarget_pipeline.py#L890-L1000),
[official solver call](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L2102-L2116),
[dependency list](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/requirements-umr.txt).

## Stage 1: learn surface correspondence

The network is `PointNetTemplateResidualAE`: pointwise convolutional features,
max pooling to a latent vector, and an MLP that predicts ordered 3D residuals
added to a fixed template point cloud. This produces template-indexed surface
points rather than directly predicting a robot trajectory. The training objective
combines symmetric squared Chamfer distance, point repulsion, residual magnitude,
and residual edge smoothness. The trainer uses AdamW and optionally cosine
learning-rate scheduling. Individual loss weights are configurable and may be
zero, so these terms are supported rather than necessarily active in every run.
[Architecture and basic losses](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L244-L298),
[optimizer and loss assembly](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L670-L750).

The pipeline reuses compatible correspondence slots for the configured source
and robot templates; otherwise it trains and exports new slots. Thus, the learned
mapping is an input to subsequent geometric optimization, not an RL controller.
[Reuse and training configuration](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/humanoid_retarget_pipeline.py#L890-L942),
[slot export](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L799-L823).

## Stage 2: optimize robot configurations

For each frame, `solve_frame_body_segment_qp` repeatedly computes current robot
kinematics, builds weighted residuals and Jacobians, solves for a tangent-space
configuration increment, and integrates that increment with `mj_integratePos`.
This is a **damped Gauss–Newton-style constrained iteration**: that characterization
follows directly from its `P = J.T @ J + damping * I` and `q = J.T @ residual`
assembly. In compact form, each local subproblem minimizes
`0.5 * ||J Δq + r||² + 0.5 * damping * ||Δq||²`, with configured constraints
and possible slack penalties.
[Frame iteration and point/normal terms](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1760-L1809),
[quadratic assembly](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L1613-L1630),
[integration](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L2102-L2119).

Supported residuals include matched surface-point positions, surface normals,
self-contact distances, ground contact and contact anchors, object-contact
vectors, joint temporal smoothing, and penetration penalties. Their activation
and weights depend on the source adapter and configuration; this is not simply
sparse end-effector IK.
[Residual assembly](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1770-L1975).

Supported constraints include joint/configuration bounds, local and root step
limits, linearized ground/self/object separation inequalities, and optional
nonnegative slack variables with quadratic penalties. L2 step limits are encoded
as **second-order cones**. Consequently, the helper's name `solve_clarabel_qp_step`
does not mean every configuration is a linearly constrained QP: with L2 limits it
solves a quadratic conic problem using Clarabel's cone interface.
[Bounds and collision constraints](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1980-L2101),
[slack and cone construction, direct solver](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L1613-L1751).

MuJoCo supplies forward kinematics (`mj_forward`), geometric Jacobians (`mj_jac`),
geometry distance queries (`mj_geomDistance`), and configuration integration.
NumPy/SciPy assemble the optimization arrays/sparse matrices; Clarabel solves the
subproblem. This inspected path is kinematic optimization, not forward-dynamics
trajectory optimization or RL. Collision/contact matching alone does not establish
dynamic feasibility or stable physical tracking.
[Kinematics](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L993-L1007),
[collision queries](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L1122-L1218),
[solver](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L1556-L1751).

## Temporal strategy and batch path

Sequential solving initializes each frame from the preceding solution. Optional
bidirectional solving computes forward and backward trajectories, then uses dynamic
programming to select candidates with frame cost, joint continuity cost, and a
switch penalty. This is trajectory initialization/candidate selection, not a claim
that the Clarabel solver itself is warm-started: the helper constructs a new
`DefaultSolver` for each call. The stream/batch retargeter also calls the same
Clarabel wrapper.
[Sequence solving and DP](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L2690-L2816),
[solver creation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L1743-L1751),
[batch solver call](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector_batch.py#L1472-L1489).

## Why the unofficial implementation mentions Mink

That repository explicitly labels itself an independent, unaffiliated reproduction.
It wraps point/normal/contact objectives as Mink tasks and constraints as Mink
limits. Its frame loop calls `mink.solve_ik` for the ordinary path. For an L2 trust
region, it calls a custom `solve_ik_socp` helper that obtains the objective and
linear constraints from `mink.build_ik`, adds a second-order cone, and calls
Clarabel directly. The README's general description of Clarabel via `qpsolvers`
therefore needs this source-level qualification for the L2 branch.
[Unofficial status and stack](https://github.com/longchengzhuo/Unified-Motion-Retargeting/blob/0aa1855fe4f65a73681ffbd1d9f95ab1c2bad9ca/README.md#L20-L28),
[branching solver loop](https://github.com/longchengzhuo/Unified-Motion-Retargeting/blob/0aa1855fe4f65a73681ffbd1d9f95ab1c2bad9ca/umr/retarget/pipeline.py#L375-L395),
[L2 helper](https://github.com/longchengzhuo/Unified-Motion-Retargeting/blob/0aa1855fe4f65a73681ffbd1d9f95ab1c2bad9ca/umr/limits/trust_region.py#L53-L121).

The two implementations share a broad correspondence-plus-constrained-optimization
idea and a Clarabel backend, but their source organization and abstractions differ.
No numerical equivalence or performance equivalence has been demonstrated here.
A switch from Mink to PyRoki in a different project therefore does not imply that
official UMR needs a Mink replacement. A future PyRoki port of UMR would require
recreating its surface objectives, correspondence binding, constraints, and temporal
logic and then validating the result; replacing a package name would not suffice.
