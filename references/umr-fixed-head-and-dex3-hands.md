# UMR fixed-head constraints and Astro Dex3-1 hands

Research date: 2026-10-23. Scope: inspected kinematics, static Jacobians,
correspondence semantics and potential objective ablations. The user confirmed
that the neck-related question meant **head binding**. Hand correspondence is a
separate question. No motion retargeting, solver rollout, collision-primitive
experiment or hardware execution was performed for this note.

## Finding

Both inspected robots have a head fixed to the upper torso and no neck joint.
That removes independent head articulation; it does **not** make all head
surface residuals redundant. Head and torso points share an upstream rigid
motion, but their positions, normals, targets and weights can constrain that
motion differently. Removing a head objective is a task-priority decision,
whereas storing its points in the torso's frame can be an equivalent change of
coordinates. The distinction follows from the actual UMR objective and the
model hierarchies below, not from a retargeting result.

UMR's paper separates canonical correspondence learning from subsequent
constrained surface matching. Its correspondences represent surface locations,
not a one-to-one joint map. This is why a fixed robot head may still receive
surface anchors. [UMR paper, sections III-B and III-C](https://arxiv.org/html/2609.02134v2#S3).

## Models actually inspected

UMR and its isolated experiment checkout are based on
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`. Menagerie is
`1316cac090144c9891453a53b8336e8374c96196`. The new asset is a **separate**
`astro_p2_43dof_dex3_1` model; the original `astro_p2_29dof` model remains present.
This is not an in-place replacement of the historical model. The local hand
commit is ahead of the observed remote default branch; pinned GitHub links may
not resolve until that commit is published. The inspected local
[variant README](/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_43dof_dex3_1/README.md)
and [MJCF](/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml)
are authoritative for this workspace, with hashes recorded below.
[Variant source and mounting assumptions](https://github.com/notAnyrobot/menagerie_x/blob/1316cac090144c9891453a53b8336e8374c96196/robots/astro_p2_43dof_dex3_1/README.md).

| Loaded model | `nq` / `nv` | Hinge joints | Hand hinges | Neck/head hinges | Actuators in XML |
| --- | --- | --- | --- | --- | --- |
| Astro original 29 DOF | 36 / 35 | 29 | 0 | 0 | 0 |
| Astro Dex3-1 variant | 50 / 49 | 43 | 14 | 0 | 0 |
| UMR G1 control, `g1_29dof.xml` | 36 / 35 | 29 | 0 | 0 | 0 |

These counts were measured by loading the exact files in UMR's MuJoCo 3.3.7
runtime. The floating base contributes seven position coordinates and six
velocity coordinates. A model's hinge count does not assert that this XML
provides a controller or actuators.

In Astro, `head_link` is a jointless child of `torso_link`, itself fixed below
`waist_roll_link`. Both compile to rigid ownership (`body_weldid`) by
`waist_roll_link`; their parent chain includes the three waist hinges and the
floating base. In the G1 control, the `head_link` **mesh** is directly attached
to body `torso_link`; it is not a separate articulated head body. Its chain
also includes the three waist hinges and the floating base.
[Astro torso and head](https://github.com/notAnyrobot/menagerie_x/blob/1316cac090144c9891453a53b8336e8374c96196/robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml#L158),
[G1 torso-owned head geometry](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/assets/g1/g1_29dof.xml#L209).

The new Astro palms are fixed through the existing hand frames, 67.502 mm
(left) and 67.500 mm (right) along wrist-yaw +X. Each palm has seven descendant
finger hinges: three thumb, two middle and two index. The 16 hand visual meshes
come from pinned official Unitree assets. Their internal kinematics are
distinct from the sample Astro attachment transform, which is not a verified
mechanical mount. Joint-name mapping is required because MJCF tree order inserts
the left fingers before the right arm. This differs materially from the fixed
head case. The G1 **control used here** has no finger hinges; other G1 assets
and real G1 configurations must not be conflated with it.
[Astro hand hierarchy](https://github.com/notAnyrobot/menagerie_x/blob/1316cac090144c9891453a53b8336e8374c96196/robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml#L209),
[official Dex3-1 left-hand source](https://github.com/unitreerobotics/unitree_ros/blob/5994d4faef0a9cadd3287f8de0199a67eeb2a259/robots/dexterous_hand_description/dex3_1/dex3_1_l.urdf),
[right-hand source](https://github.com/unitreerobotics/unitree_ros/blob/5994d4faef0a9cadd3287f8de0199a67eeb2a259/robots/dexterous_hand_description/dex3_1/dex3_1_r.urdf).

## What a binding controls

UMR projects a learned robot slot onto a selected surface triangle, obtains
that triangle's geometry ID, and stores a local position and normal in the
geometry frame. The geometry's body supplies the kinematic Jacobian. Separately,
the corresponding **source** slot's semantic region determines sampling and
cost. These are four different identifiers: source region, target mesh,
target body and target rigid-motion owner. Equal owners cannot certify a
correct anatomical match: a source face point on the torso mesh can have the
right rigid ancestor but the wrong position and normal.
[Binding implementation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L657),
[slot kinematics](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L867),
[source-region cost assignment](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L957).

Default semantic selection requests 20 head slots at point/normal costs 1/1,
50 torso slots at 20/5, and 15 slots per hand at 10/1. Selection takes fewer
when a region has insufficient candidates; configuration can override these
defaults. They are per-slot coefficients, not normalized per-region budgets.
If all requested slots exist, nominal head versus torso point-coefficient sums
are 20 versus 1000, and normal sums are 20 versus 250. Those sums do not measure
actual influence: residual magnitude, spatial lever arm and Jacobian direction
also matter. These are retarget-stage settings, not evidence that static
training used anatomical supervision.
[Defaults](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L158),
[selection](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L936).

For a selected slot, the inspected optimizer stacks
`sqrt(wp) * (p(q) - source_point)` and
`sqrt(wn) * (n(q) - target_normal)` with their Jacobians. Position Jacobians
come from `mj_jac`; the normal derivative is `-[n]× Jω`. MuJoCo documents these
as 3-by-`nv` derivatives of a point/frame attached to a body. A fixed descendant
therefore still responds to movable ancestors. UMR's default `tpose_offset`
normal mode transports the robot's reference normals through source-face
deformation. It does not inherently remove human neck motion from those targets.
[Residual assembly](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L1770),
[Jacobian implementation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smpl_surface_retarget_common.py#L893),
[normal target transport](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L2613),
[MuJoCo `mj_jac`](https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html#mj-jac).

## Static evidence and its limits

I evaluated one deterministic probe per visual mesh: the mean of the compiled
head or torso mesh vertices, transformed by its geometry frame. Both elbows
were set to +π/2, shoulder rolls to left +π/2 and right −π/2; other hinges
remained at zero. This is a kinematic probe, **not** a learned slot, a surface
coverage statistic or a motion trial. For all three models, the only nonzero
combined point/rotation-Jacobian columns belonged to the floating base and the
three waist joints (threshold `1e-10`).

| Model | `max(abs(Jω_head − Jω_torso))` | `norm(Jp_head − Jp_torso, 'fro')` |
| --- | --- | --- |
| Astro original | 0 | 0.4302853306 |
| Astro with hands | 0 | 0.4302853306 |
| G1 control | 0 | 0.4908287195 |

The latter numbers are numerical matrix differences in MuJoCo's native velocity
coordinates, not a metric to compare robot quality. They demonstrate that
identical rotational ancestry does not make the point Jacobians identical.
The unchanged Astro values also verify that adding these hands did not change
the head/torso kinematics at this probe pose.

The following reasoning is a deduction from rigid kinematics, not a measured
retargeting outcome. For two points on one rigid body,
`v_head − v_torso = ω × (p_head − p_torso)`. Different offsets supply different
rotational leverage; different normal directions constrain different rotations.
Additional points can leave Jacobian rank unchanged while changing the weighted
normal matrix `Jᵀ W J` and gradient `Jᵀ W r`. Thus head rows need not add a new
independent DOF or new row-space dimension to change the compromise selected
by least squares. Conversely, if torso constraints already specify the same
rigid transform exactly and all head targets agree, head rows can be redundant
for that ideal solution. Neither universal benefit nor universal redundancy
follows from fixed-head ownership alone.

Human neck articulation creates a plausible **conflict**: head and torso source
targets may demand incompatible motions of one robot rigid assembly. The
optimizer may trade that error against torso, waist, root or other objectives.
Whether this matters in a particular clip requires later evidence; static
correspondence cannot establish the size or desirability of that tradeoff.

## Options to investigate before changing bindings

| Option | Consequence and evidence needed |
| --- | --- |
| Keep distinct head semantics and mesh bindings | Preserves anatomical auditing and current objective. Inspect head-shell versus torso-shell rates and face/neck subregions even when rigid owner agrees. |
| Consolidate storage under one rigid owner | Can be kinematically equivalent if every local point/normal is transformed correctly and original geometry identity, source labels, targets, selection and weights remain available. Verify world points/normals and Jacobians before and after. Simply changing an ID is incorrect. |
| Disable head point and/or normal costs | Changes the objective, not the kinematic model. Compare point-only, normal-only and both-disabled ablations with fixed selected slots. Do not change correspondence training at the same time. |
| Relabel head as torso | Usually changes sampling and costs (default point 1→20, normal 1→5) and can hide semantic errors. It is not equivalent to ownership consolidation. |
| Adapt human head motion to a rigid torso target | Explicitly projects away unrepresentable relative neck motion; retains robot head geometry. Record lost motion and compare torso/head residuals separately. This is a new target-construction policy requiring later validation. |

For a future motion study, retain raw anatomical diagnostics and measure head
and torso errors, waist/root compensation, and objective contributions under
the ablations. A static precursor can examine per-region Jacobian row spaces
and weighted information contributions without solving motion. No binding
merge or objective correction is justified solely by the present ownership
inspection.

For the new hands, keep palm, thumb, index and middle mesh coverage separate
from the coarse `leftHand`/`rightHand` source label. A hand-region match does
not establish finger identity or compatibility between a five-finger human and
a three-finger robot. A palm point has no finger-joint sensitivity; a finger
point can depend on its own finger chain as well as the upstream wrist/arm.
Per-link counts, side consistency, projection error, unrepresented fingers,
and source-hand versus forearm leakage are therefore necessary static
diagnostics. Aggregate hand improvement alone would not validate dexterous
retargeting. Source label provenance and its finger merging are documented in
[the SMPL-X/SOMA note](umr-smplx-soma-weights.md).

## Reproducibility

The inspected model file SHA-256 values are:

| File | SHA-256 |
| --- | --- |
| Menagerie `robots/astro_p2_29dof/astro_p2_29dof.xml` | `89f179ea9fb51ff53a9a1d3fa9cef6049f843e0e3ad21a886677e3a5341767f7` |
| Menagerie `robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml` | `9df1549627abc9ed18b3d42e43d5850833ba5a53a8152a454ec92c806f4ecbef` |
| Experimental UMR `assets/g1/g1_29dof.xml` | `8c586e4747da85804180fe44d8692e0fd8231356728b6327e256dca498087a78` |

The isolated checkout's existing patch affects surface selection/binding,
including the separately gated collision-primitive path. The inspected
position/normal residual assembly and slot-Jacobian implementation above are
unchanged from the pinned upstream revision. No patch was modified here.
Hashes of the inspected experimental files are:

| File under `externals/UMR-astro-surface-experiment/scripts/` | SHA-256 |
| --- | --- |
| `retarget_smpl_to_humanoid_surface_vector.py` | `db7cb75e82de2def9be9689dcb946e03aa2c19054ed5cee0cfabdfe9a279214d` |
| `smpl_surface_retarget_common.py` | `24bdf3de2a9cd1a6618142e870508c4d34874e2ecdb5cfdfe7098d7f52a4bc2d` |
| `retarget_body_segment_surface.py` | `d9b918f06f769ceb8acc42a726fa105d64947fa2f7c9fb5da0e7687161ab4a84` |

The static probe is reproducible from the workspace root with
`externals/UMR/.venv/bin/python`, using this Python body. It only evaluates
kinematics; `mj_forward` does not integrate time or perform retargeting.

```python
from pathlib import Path
import mujoco
import numpy as np

menagerie = Path('/data/workspace/notAnyrobot/menagerie_x/robots')
paths = [menagerie / name / f'{name}.xml' for name in
         ('astro_p2_29dof', 'astro_p2_43dof_dex3_1')]
paths += [Path('externals/UMR-astro-surface-experiment/assets/g1/g1_29dof.xml')]
for path in paths:
    model = mujoco.MjModel.from_xml_path(str(path.resolve()))
    data = mujoco.MjData(model)
    for name, angle in {
        'left_shoulder_roll_joint': np.pi / 2,
        'right_shoulder_roll_joint': -np.pi / 2,
        'left_elbow_joint': np.pi / 2,
        'right_elbow_joint': np.pi / 2,
    }.items():
        data.qpos[model.jnt_qposadr[model.joint(name).id]] = angle
    mujoco.mj_forward(model, data)
    jacobians = []
    for part in ('head', 'torso'):
        geom = next(g for g in range(model.ngeom)
                    if model.geom_group[g] == 1 and model.geom_dataid[g] >= 0
                    and model.mesh(int(model.geom_dataid[g])).name == part + '_link')
        mesh = int(model.geom_dataid[geom])
        start, count = model.mesh_vertadr[mesh], model.mesh_vertnum[mesh]
        mean_vertex = model.mesh_vert[start:start + count].mean(axis=0)
        point = mean_vertex @ data.geom_xmat[geom].reshape(3, 3).T + data.geom_xpos[geom]
        jp, jr = np.zeros((3, model.nv)), np.zeros((3, model.nv))
        body = int(model.geom_bodyid[geom])
        mujoco.mj_jac(model, data, jp, jr, point, body)
        jacobians.append((jp, jr))
        print(part, model.body(body).name,
              model.body(int(model.body_weldid[body])).name)
    print(path.name, model.nq, model.nv, model.nu,
          np.max(np.abs(jacobians[0][1] - jacobians[1][1])),
          np.linalg.norm(jacobians[0][0] - jacobians[1][0]))
```

Context7 was resolved to `/google-deepmind/mujoco` and queried for the point
and rotation Jacobian contract. The official documentation and pinned source
were inspected together; runtime measurements above use installed MuJoCo
3.3.7 rather than assuming the current documentation version is installed.
