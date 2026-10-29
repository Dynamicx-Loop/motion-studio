# UMR human weights and SMPL-X/SOMA correspondence

Research date: 2026-10-23. Scope: static source templates, weight and label
provenance, and correspondence binding; no motion retargeting or robot execution.
The measured comparison lives in
[the SOMA correspondence experiment](../experiments/soma-correspondence-audit/README.md).

## What changes when the source changes

HiPHI is the motion dataset/source; SMPL-X is the body representation of the
converted actor motion. SOMA-X is a library and asset system implementing the
SOMA representation with several identity backends. Changing a clip, changing
its actor shape, changing mesh/rig representation, and changing an identity
backend are distinct interventions. UMR itself separates canonical point-cloud
learning from motion optimization and reuses correspondence for motions sharing
a template and robot. [UMR overview and source table](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/README.md#supported-motion-sources),
[NVIDIA overview](https://github.com/NVlabs/SOMA-X#overview).

In the inspected UMR implementation, `smpl_template_config` reads gender and up
to ten actor betas from the sequence; `load_smpl_template` calls the body model
without motion-frame poses. The dataset consists of samples from that static
mesh. The PointNet residual autoencoder consumes these sampled point clouds,
not a temporal pose training sequence. Its parameters, normalization, sampling,
and fixed-template ordering determine the learned slot positions.
[Template selection](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/humanoid_retarget_pipeline.py#L613),
[static template generation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/build_correspondence_ae_dataset.py#L567),
[training implementation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L101).

The unshaped SOMA path is particularly important: `soma_template_vertices_joints_faces`
uses `load_soma_bind_tpose_template`, which skins the public bind shape into
the saved T-pose. It does **not** create a neutral MHR identity by evaluating
zero MHR coefficients. The BONES-SEED branch instead uses fitted identity,
scale, and optional bone-length values with `SOMALayer`. Therefore comparing
the HiPHI-shaped SMPL-X template with this public SOMA template changes both
representation and body geometry; it is not the same-actor experiment.
[UMR SOMA template branches](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/soma_source.py#L714),
[bind-template construction](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/soma_source.py#L295).

## Four different meanings of weights

| Quantity | Meaning and role in this experiment |
| --- | --- |
| Body-model parameters/assets | SMPL-X template, shape/expression/pose bases, joint regressor and actor betas; SOMA rig/topology and optional identity model parameters. These describe human geometry and articulation. |
| LBS skinning weights | A vertex-by-joint matrix determining blended human deformation. Values and hierarchy need direct auditing. An argmax is only the largest influence, not an anatomical boundary definition. |
| Segmentation and cost weights | Discrete region labels and region-specific sample counts, point costs and normal costs. They select and weight surface constraints; they are not learned human skinning weights. |
| Learned correspondence weights | The neural encoder/decoder parameters trained on static point clouds, producing ordered slots. A slot pairing is distinct from either body's joint influences. |

SMPL-X loads `weights` as `lbs_weights` and `kintree_table[0]` as `parents`,
setting the root parent to -1. UMR's loader selects `.pkl` before `.npz` when
given a folder and both exist; the selected file, not the folder name, establishes
asset identity. It uses ten betas, full hand rotations and flat hand mean.
[Installed SMPL-X source](../externals/UMR/.venv/lib/python3.12/site-packages/smplx/body_models.py),
[UMR loader](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/smplx_model_loader.py#L31).
The cost configuration and learned parameters occupy separate modules.
[Region costs](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L155),
[autoencoder and losses](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L244).

## Rigs and the compatibility overlay

SMPL-X has 10,475 mesh vertices and 55 LBS joint columns in the loaded neutral
model. SOMA mid topology has 18,056 vertices. Its public skeleton has 78 entries,
including a virtual Root, while pose inputs omit Root and have 77 rotations.
Unlike SMPL-X's single neck entry, SOMA exposes Neck1, Neck2, Head and HeadEnd.
It also includes explicit end joints and a different hand hierarchy. Public
joint indices must therefore never be copied between representations.
[SMPL-X joint names](../externals/UMR/.venv/lib/python3.12/site-packages/smplx/joint_names.py),
[SOMA 0.3.4 joint contract](https://github.com/NVlabs/SOMA-X/blob/56a3d957a549c66425b500fddf7f3183bc6fbdff/soma/body/soma.py#L39).

The pinned NVIDIA asset release stores rig arrays in `SOMA_template_rig.usda`;
the slim neutral NPZ stores other body data. The installed official loader reads
the USD and derives a public rig by keeping the configured joint names,
remapping parents and accumulating removed procedural/auxiliary joint weights
into their nearest retained ancestors. It saves this public rig in
`_public_mid_rig_data` before restoring the expanded rig for procedural posing.
This is a documented reduction, not independent human segmentation.
[Official loader](https://github.com/NVlabs/SOMA-X/blob/56a3d957a549c66425b500fddf7f3183bc6fbdff/soma/body/soma.py#L580),
[weight aggregation](https://github.com/NVlabs/SOMA-X/blob/56a3d957a549c66425b500fddf7f3183bc6fbdff/soma/procedural_transforms.py#L512).

The local overlay serializes the official loader's public mid rig dictionary
and points other asset entries to unchanged originals. UMR's standalone
bind-template path needs those NPZ arrays, converts centimeters to meters, and
applies `T_pose_world @ inverse(bind_pose_world)` through public LBS weights.
The current compatibility check must compare the derived arrays against a fresh
official load, not merely confirm that the NPZ opens. The public reduction may
preserve a canonical template while differing from expanded procedural skinning
under motion; a static correspondence experiment does not validate that dynamic
equivalence. [Overlay derivation script](/data/motions/human_models/soma-x/f81a01796f65/tools/prepare_umr_overlay_and_verify.py),
[UMR dense weights and posing](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/soma_source.py#L249),
[setup provenance](../docs/umr-soma-setup.md).

The current CPU audit independently reconstructed all 51 serializable overlay
arrays and found bitwise equality, while preserving the slim original keys.
Both loaded LBS matrices are finite, nonnegative and normalized: maximum row-sum
errors are approximately `4.47e-8` for SMPL-X and `6.74e-8` for SOMA. SOMA's
Root, HeadEnd, eyes and toe-end joints have zero LBS mass; their presence in the
hierarchy does not imply direct skin influence. This verifies numerical and
overlay integrity, not semantic interchangeability.
[Audit implementation](../experiments/soma-correspondence-audit/human_weights.py),
[measured human-weight results](../experiments/soma-correspondence-audit/human-weights.json).

## How UMR derives and transfers segment labels

SMPL-X segment labels come from an external 55-class face segmentation and a
55-to-17 map. The map combines neck, head, jaw and eye classes as `head`, merges
spine classes as `torso`, and merges finger joints into hands. The default
19-class schema further splits each arm label using the proximal 0–30% of
the absolute lateral-coordinate range of that run's candidate slots. This split
is geometric and sample-dependent, not a new shoulder joint or an LBS threshold.
[Map and schema](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L77),
[arm split](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L716).

With the installed wrap assets, SOMA labels still originate from that SMPL-X
segmentation. Each SOMA-wrap vertex is projected onto nearby SMPL-X base-body
faces, inherits the selected face's 17-class label, and transfers by SOMA vertex
order. Each SOMA triangle receives a majority vertex label; each bound slot
inherits its triangle label before the same 19-class arm split. This is not
SOMA skinning-weight argmax, nor does it use native `segment_*` masks. UMR also
has a separate nearest-joint fallback if wrap assets are unavailable; mixing
the two label paths would confound a comparison.
[Wrap transfer and majority labels](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L635),
[SOMA slot label paths](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_body_segment_surface.py#L809).

Measured discrete-label versus grouped-LBS argmax disagreements occur at
10/10,475 SMPL-X vertices and 758/18,056 SOMA vertices. SOMA's disagreements
include torso/shoulder and neck/head boundaries. These are diagnostic
disagreements, not 758 demonstrated model errors. An independent complete
nearest-triangle wrap check changes 13 raw 55-class vertex labels but no native
17-class labels. The wrap's original polygons preserve SOMA vertex order even
though Trimesh and the official loader choose different quad triangulation
diagonals. [Measured human-weight results](../experiments/soma-correspondence-audit/human-weights.json).

On the target side, learned robot slots are projected onto robot surface faces.
Each face supplies a geometry ID; positions and normals are stored in that
geometry's local frame. Human LBS weights are not copied into robot joints by
this binding function. Shared slot index carries the source region/cost onto
the target surface constraint. Consequently a correct human weight matrix can
coexist with a source head slot landing on a torso mesh, and a correct target
geometry owner does not establish anatomical identity.
[Robot binding](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/retarget_smpl_to_humanoid_surface_vector.py#L657).

## Available motion and possible matched controls

The setup initially contained model/rig assets but no BONES-SEED BVHs or fitted
actor shapes. For this audit, the public NVIDIA `example_animation.usd` was
downloaded from the same pinned HF revision, verified against its upstream Git
blob hash, and inspected with official CPU USD readers. It contains 931 samples
at 24 fps, time codes 0–930, 78 public joints, Y-up centimeter stage units, unit
scales, and finite transforms. The reader's meter-unit local and world arrays
both have shape `(931,78,4,4)`. This is a real shipped SOMA animation, not a
synthetic substitute or the HiPHI actor. Its license and model card are retained.
[Reproducible inventory script](../experiments/soma-correspondence-audit/motion_inventory.py),
[measured inventory](../experiments/soma-correspondence-audit/motion-inventory.json),
[pinned official animation](https://huggingface.co/nvidia/SOMA-X/blob/f81a01796f652260ff930d5318d6c6b845a505ed/example_animation.usd).

That USD is readable by SOMA-X, but the inspected UMR motion route consumes
SOMA BVH plus the appropriate shape fit. No USD-to-UMR adapter or matched
HiPHI-to-SOMA conversion is validated here. Uniform BONES-SEED motion requires
`soma_base_fit_mhr_params.npz`; proportional motion requires its actor-matched
`Axxx.npz`. Those gated files remain absent and no dataset agreement was
accepted. [UMR BONES-SEED contract](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/sample_data/bones-seed/README.md).

A stronger future actor-shape control is possible through SOMA's SMPL-X
identity backend: provide the exact licensed SMPL-X file explicitly and the
same ten betas. The backend transfers native rest geometry through its wrap and
blending machinery, so this still does not create vertex identity or guarantee
identical canonical surface geometry. Explicit path selection matters because
SOMA's backend searches NPZ before PKL, the reverse of UMR's folder loader.
[Installed 0.3.4 backend](https://github.com/NVlabs/SOMA-X/blob/56a3d957a549c66425b500fddf7f3183bc6fbdff/soma/body/identity_model.py#L219).
Official SMPL-family motion conversion uses pose inversion, optionally refined
with autograd; conversion therefore needs reconstruction-error and pose-reference
checks rather than an assumption of exact equivalence. Identity-backend fitting
is another distinct operation. Neither optimization was run here.
[Official conversion tools](https://github.com/NVlabs/SOMA-X/blob/main/docs/tools.md#smpl-family-to-soma).

## Interpretation rules for the controlled comparison

These are methodological deductions from the mechanisms above:

- Report loaded-file hashes, vertex/joint ordering, finite values, negative
  values, row-sum errors, influence counts and top-two influence margins.
  A small argmax margin marks label uncertainty; it is not proof of corruption.
- Compare merged anatomical regions, then retain neck/head and proximal/distal
  arm diagnostics separately. The 19 labels are UMR's common task vocabulary,
  not a one-to-one joint mapping. Report disagreement with LBS-based regions
  and with independent geometry/joint-plane regions.
- Hold target T-pose, selected meshes, normalization, source centering rule,
  slots, seeds and optimization settings fixed. Compare native-centering effects
  separately. Equal setting names such as `spine1` do not guarantee equivalent
  anatomical locations across rigs.
- Use per-source rates as well as counts: source meshes and sampled slots differ,
  so a raw count decrease can be a coverage change. Report unrepresented regions,
  target coverage and bind projection errors.
- Distinguish rigid moving-body ownership from independent mesh identity, and
  test knee/elbow planes independently. Neck labels alone cannot excuse face
  slots landing on the torso. A lower training loss is not anatomical validation.
- Static success establishes neither motion deformation fidelity nor dynamic
  feasibility. The public example validates source availability and parsing only.

Read-only inspection of this experiment's controls confirms that `bbox50`
translates the source by the full three-dimensional bbox midpoint, not only its
vertical component. Height normalization divides by each source mesh's own
height and leaves its center unchanged. Thus it removes overall scale but not
proportions, reference-pose differences or relative source/target origins.
The retained target centers also differ between robots (Astro pelvis versus
G1 waist-yaw body). Between-robot gaps consequently include target configuration
choices; within-robot source changes are the stronger controls.
[Preparation code](../experiments/soma-correspondence-audit/prepare.py),
[recorded controls](../experiments/soma-correspondence-audit/preparation.json),
[normalization implementation](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/scripts/train_correspondence_template_residual_ae.py#L58).

The measured source mesh heights are 1.661802 m (HiPHI-shaped SMPL-X) and
1.771973 m (public SOMA). Their Spine1 origins lie at 58.426% and 60.036% of
mesh height above the bottom. SMPL-X's left elbow is approximately 65.2 mm
below its shoulder in the generated canonical template, whereas SOMA's left
Arm/ForeArm joint heights coincide. Thus the source pose mismatch is measurable
even before learning. Full joint coordinates, normalized spans, bilateral
arm elevations, and centering translations are retained in
[source-template-comparison.json](../experiments/soma-correspondence-audit/source-template-comparison.json),
generated by [source_template_comparison.py](../experiments/soma-correspondence-audit/source_template_comparison.py).

## Inspected versions and reproducibility

UMR: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`. SOMA assets:
HF `f81a01796f652260ff930d5318d6c6b845a505ed`. Runtime:
`py-soma-x==0.3.4`, `smplx==0.1.28`. SOMA tag v0.3.4 resolves to
commit `56a3d957a549c66425b500fddf7f3183bc6fbdff`; the installed
`soma/body/soma.py` SHA-256 exactly matches that tag's raw source. Other installed
implementation hashes inspected here are:

| Installed source | SHA-256 |
| --- | --- |
| `soma/body/soma.py` | `65859314910acb0cfe4623d126c1356686a3302406c40ac7bf57eae9bf66277b` |
| `soma/procedural_transforms.py` | `3e1f2073263c44f9d18049269b92ef22c8862c4378f28adaed10198dbb69558c` |
| `soma/body/identity_model.py` | `0041215e7a3c849803e4c64045e28ad17d352907baa340989deaab94d972d380` |
| `smplx/body_models.py` | `037e3a4c71894465834f3ab9c4f2bd76443c4ef2e230d8796b5addb3d6ed8ffd` |

Context7 resolution selected `/vchoutas/smplx` and queried model loading/LBS
documentation. Two SOMA-X queries returned unrelated libraries, so SOMA claims
were checked against official NVIDIA documentation and the installed source.
Live `main` documentation is background; the pinned installed code establishes
this experiment's behavior. Quantitative matrix/overlay checks and run hashes
belong to the linked experiment, not to undocumented assumptions about a path.
