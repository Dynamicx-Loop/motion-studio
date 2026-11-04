# UMR wrist housing and hand slots: static correction evidence

Research date: 2026-10-23. Scope: source inspection for the controlled static
hand-binding experiment. This note identifies mechanisms and testable hypotheses;
it does not claim that one mechanism alone explains the measured bindings.
No motion retargeting, rollout or hardware test is part of this investigation.

## Finding

The correspondence objective has no anatomical hand-versus-wrist constraint.
Its starting template and smoothness graph come from the human, while its target
is an unordered robot surface. Height normalization leaves local proportions
and the serial robot wrist unchanged. Astro's palm frame lies 159.5 mm beyond
its wrist-roll joint in the neutral wrist configuration, so a region boundary
at wrist-roll includes substantial housing before the actual hand. These are
concrete reasons to inspect geometric registration before interpreting a high
coarse hand-zone score as hand-mesh correspondence. The evidence below supports
that hypothesis; a controlled experiment is needed to establish its effect.

The paper describes canonical T-pose correspondence learning separately from
motion retargeting. Its human template supplies ordered surface slots and the
robot supplies unordered geometry. A manually specified landmark calibration
would therefore be an additional experimental prior, not an existing anatomical
guarantee of UMR. [UMR paper, §III-B](https://arxiv.org/html/2609.02134v2#S3).

## Source versions and local provenance

The inspected UMR checkout is based on
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`, with the pre-existing surface patch in
`externals/UMR-astro-surface-experiment`. The trainer is unchanged relative to
that commit. Menagerie is based on
`1316cac090144c9891453a53b8336e8374c96196`. The local Astro hand commit may not be
published remotely, so its local model and experiment hashes remain authoritative.
Source links below distinguish upstream code from local audit conventions.

During inspection the current Astro XML had collision-only local edits compared
with that Menagerie commit. Its SHA-256 was
`bba912f94c0b0cb622c83d0dcdbeb8acbbbb89421129df1d8668f4971fad11b6`, whereas the
previous experiment recorded
`9df1549627abc9ed18b3d42e43d5850833ba5a53a8152a454ec92c806f4ecbef`.
The inspected diff changed collision dimensions and added collision geoms;
it did not change visual meshes, body transforms or joints. Added geoms can
change numeric geom IDs. A comparison must preserve these user edits and either
freeze the historical XML or verify selected visual geometry equivalence by
mesh/body identity and world vertices. A raw geom-ID equality check is not
sufficient across these files. The historical hashes are in the
[previous model note](umr-fixed-head-and-dex3-hands.md#reproducibility); the live
[Astro MJCF](/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml)
and its Git diff are the source of the drift observation.

## What training does and does not align

`per_sample_height` starts with zero centers and divides each object by its own
height. It uses mesh vertices if available. Height is the Y extent, falling back
to the largest extent if Y is less than 60% of that extent. The routine performs
no translation, wrist alignment or segment-wise proportion adjustment. Any
centering already performed during dataset construction remains a separate
choice. Equal normalized height does not establish equal shoulder, elbow, wrist
or palm locations. [Normalization implementation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L47).

The decoder predicts residuals added to the fixed human template. Its final
layer is zero-initialized in the configured mode, so the initial reconstruction
is the human template. The geodesic graph is built from the source human mesh
and sample faces. Edge smoothness penalizes differences between residual vectors
on connected slots; it does not impose target anatomy or require the original
edge lengths to remain exact. This encourages nearby human slots to deform
coherently, which can make a local proportion mismatch consequential.
[Decoder](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L244),
[geodesic graph and edge penalty](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L320),
[template state construction](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L517).

The loss sums symmetric squared nearest-neighbor Chamfer distance, repulsion,
residual magnitude and residual-edge smoothness, with configurable weights.
There is no hand label, target mesh-owner label or wrist/palm landmark term.
Thus a human hand slot covering nearby wrist housing can satisfy geometric
coverage and smoothness without being penalized for anatomical identity. This
is a mechanism permitted by the objective, not proof of the particular optimum
reached in any arm of the experiment.
[Geometric losses](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L281),
[loss assembly](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L733).

In fixed-template export the human reconstruction is restored exactly to the
ordered template, with zero human residuals. A target-only correction can
therefore preserve human slot identity without implying that the target
correspondence remained unchanged. Record the learned target and the corrected
target separately. [Export behavior](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L560).

## Wrist and hand are different diagnostic objects

At zero wrist angles, Astro's serial body offsets are 47 mm from wrist-roll to
wrist-pitch, 44.998 mm from pitch to yaw, then 67.502 mm from yaw to the left
hand frame. The palm is fixed at that hand frame. Their sum is 159.500 mm; the
right total is 159.498 mm. Elbow-to-wrist-roll is another 114 mm. These are model
frame offsets, not measured skin landmarks or validated mounting dimensions.
[Pinned Astro hierarchy](https://github.com/notAnyrobot/menagerie_x/blob/1316cac090144c9891453a53b8336e8374c96196/robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml#L199),
[local mounting assumptions](/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_43dof_dex3_1/README.md).

The inspected G1 control also has a serial wrist: 38 mm, 46 mm, then 41.5 mm
along X to the rubber-hand frame, with a 3 mm lateral offset at the last step.
Its longitudinal wrist-roll-to-hand-frame offset is 125.5 mm. This control uses
the fixed rubber-hand meshes and has no articulated finger hinges; it must not
be interpreted as a second Dex3 target. The anatomical comparison should use
explicit mesh identities appropriate to each model.
[G1 wrist and rubber-hand hierarchy](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/assets/g1/g1_29dof.xml#L245).

The existing audit's geometric hand zone begins at the wrist-roll plane for the
arm family. Its ownership label also maps any wrist body to “hand.” Consequently,
high hand-zone agreement and low actual-hand-mesh agreement can coexist without
a numerical inconsistency. These are explicitly diagnostic zones, not unique
anatomical ground truth. Preserve the historical convention for comparability,
but report actual palm/finger mesh counts separately.
[Local region definitions](/data/workspace/motion_studio/experiments/segment-binding-audit/regions.py:21).

The human `leftHand`/`rightHand` audit groups merge wrist-associated classes and
all finger classes through the SMPL-X 55-to-17 remapping. They do not retain
individual finger identity. A hand-mesh improvement therefore cannot certify
thumb/index/middle matching, especially for a five-finger source and three-finger
target. Boundary slots should be separated from distal source-hand slots when
testing the ambiguity hypothesis.
[Source remapping](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L97),
[label loading](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L369),
[SMPL-X/SOMA provenance](umr-smplx-soma-weights.md).

## Sampling and projection are separate hypotheses

The local patched dataset builder draws triangle-area-weighted surface
candidates, applies exterior filtering when enabled, then farthest-point
sampling. Its first-hit mode tests face visibility from outside views and
requires at least two hits. These operations do not impose a minimum number of
palm or finger samples. Thin or occluded pieces can consequently be represented
unevenly; this must be measured from the frozen target sample, not inferred
solely from its visual appearance.
[Local sampler](/data/workspace/motion_studio/externals/UMR-astro-surface-experiment/scripts/build_correspondence_ae_dataset.py:347),
[exterior filtering](/data/workspace/motion_studio/externals/UMR-astro-surface-experiment/scripts/build_correspondence_ae_dataset.py:501).

Binding projects learned robot slots to the selected union of robot surfaces,
records the winning triangle's geom ID, and stores positions/normals in that
geom's frame. It does not restrict a source hand slot to a hand mesh. Compare
the learned position before projection with its projected point and the nearest
actual-hand point. If a global exact-triangle check preserves the bad ownership,
the fast projector is unlikely to explain that ownership result; the point
already favors the wrist surface under the same projection rule.
[Local production binding](/data/workspace/motion_studio/externals/UMR-astro-surface-experiment/scripts/retarget_smpl_to_humanoid_surface_vector.py:657),
[minimal observed-failure reproduction](../outputs/artifact-archives/experiment-reset-20261104/experiments/astro-hand-wrist-correction/reproduce.py).

## Controlled static alternatives

These are proposed experimental interpretations, not upstream guarantees or
measured outcomes. Choose parameters from independent geometry before inspecting
the final hand-mesh score, and retain the unmodified baseline.

| Intervention | What it can establish | Main confound |
| --- | --- | --- |
| Smooth geometric registration using explicit wrist/palm landmarks | Whether local canonical proportion/alignment explains part of the leakage while allowing unrestricted target-surface projection | The selected landmarks introduce a prior; moving neighboring forearm slots can trade hand improvement for forearm errors. |
| Target-only static shift of a fixed source-hand slot set, then unrestricted projection | Whether a simple distal position correction is sufficient for the observed learned slots | A hard hand boundary can create discontinuities; choosing shift magnitude to maximize hand counts overfits the diagnostic. |
| Add a soft landmark term and retrain on frozen samples | Whether training can accommodate geometric anchors under the original smoothness and surface losses | Changes optimization, and a seed-only result does not separate initialization sensitivity from landmark effect. |
| Increase or balance target hand samples | Whether insufficient target representation materially changes the solution | Changes the Chamfer target distribution as well as sample count; requires frozen source slots and a separate arm. |
| Restrict source-hand projection to hand meshes | Demonstrates an imposed binding policy | Actual-hand success becomes true by construction; it cannot independently validate learned correspondence. |
| Rename wrist housing as hand | Changes report semantics | Does not correct geometry or physical ownership. |

Keep G1's original results unchanged as the control. If a generic geometric
correction is also evaluated on G1, publish it as a separate arm with the same
rule and no hand-specific tuning; retain the original control alongside it.
Preserve source samples, source faces/barycentrics, slot ordering and graph,
target samples, centering, normalization, pose, training seed and objective
where the chosen intervention permits. State every exception. Do not silently
change the physical canonical model to improve the correspondence score.

An informative result includes actual palm/finger/wrist counts by side, distal
source-hand results, wrong-side assignments, target hand coverage, displacement
and projection-distance distributions, and non-hand changes. Geometric
calibration should be checked against landmarks not used to choose its parameter
when possible. Independently confirm selected robot visual vertices and human
template arrays are unchanged. Separate numerical facts from visual judgments
and from causal inference; even a clear static improvement does not establish
finger identity, dexterity, dynamic feasibility or motion-retargeting quality.

## Inspection checks

The unmodified trainer's SHA-256 was
`90cb6e79f869fc424dad57252604fe33e8b2317f638a1cab63475d3b280d0df6`.
The local region-definition file's SHA-256 was
`4a13b915ad6869254ba1c7928a10e42473e168f87497df29654ca5b1f9a14be3`.
No experiment, model, UMR implementation or report file was changed for this
source note. The static experiment's measurements and exact selected correction
belong in its own versioned record, rather than being presented as source facts.
