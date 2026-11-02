# Native generic SOMA → official bundled G1 control

Date: 2026-11-02. Branch: `experiments/umr-baseline`. No external source edits,
branch changes, dependency updates, or legacy output writes.

## Follow-up correction: uniform skeleton and available surface fit

Investigation on 2026-11-02 corrected the initial asset-availability conclusion
below. The input BVH already describes a uniform skeleton. The prior native run
used those BVH transforms with a generic neutral **surface**; it did not replace
the input skeleton with an arbitrary neutral skeleton.

The shared fitted surface parameters are available locally at
`/data/workspace/notAnyrobot/kimodo/kimodo/assets/skeletons/somaskel30/soma_base_fit_mhr_params.npz`.
Its SHA-256 is
`61f0b96c8386a19d44823faf4399816642b7e20691ed5b398c7402921090096e`.
The local bytes match the file in the official `nv-tlabs/kimodo` repository at
revision `e1c219c99b4b94ba48be1fb6a1cbc64ecee4c954` exactly.
[NVIDIA's skeleton documentation](https://research.nvidia.com/labs/sil/projects/kimodo/docs/key_concepts/skeleton.html)
identifies these as the shared BONES-SEED identity parameters. This verifies
official Kimodo provenance; a separate byte comparison with the gated BONES-SEED
download was not performed. The asset remains in its existing location.

UMR's pinned loader recognizes the literal ancestor name `motions_uniform`;
the supplied `raw/uniform` path does not select that family. Its automatic lookup
also needs a discoverable root containing `shapes` and `soma_assets`. The previous
lookup therefore did not establish workspace-wide absence of the uniform fit.
The single-motion loader silently selected generic `soma_bvh` when it found no
shape. See [family detection](../../externals/UMR/scripts/soma_source.py#L84),
[shape discovery](../../externals/UMR/scripts/soma_source.py#L133), and
[motion loading](../../externals/UMR/scripts/soma_source.py#L364).

A read-only CPU check supplying the discovered fit to UMR's fitted template
loader succeeded: 18,056 finite vertices, 78 joints and 36,108 faces. This was
static validation, not a new correspondence or motion run. The corrective run
should use a fresh recognized `motions_uniform/bvh` layout, explicitly record
the verified fit, require `source_format=soma_bvh_boneseed_uniform` and
`soma_template_name=soma_uniform`, then retrain correspondence and retarget.
The old run remains a generic-surface control; its measurements are unchanged.
Missing standalone dataset USD is not a blocker for this installed fitted path.

The official [UMR Studio](https://hanyang9.github.io/UMR/umr_studio.html) is a
separate browser pipeline. Its SOMA Flip reference uses a precomputed source
pack; availability of that example does not demonstrate automatic fitting of
arbitrary uploaded BVHs. Its published template is geometrically closer to the
local generic neutral template than to this shared fitted template (vertex RMS
after an unconstrained affine fit: 0.597 mm versus 5.55 mm). This is a geometric
diagnostic, not proof of the Studio pack's generating route: its manifest lacks
fit provenance. The local Motion Studio currently imports SMPL-X NPZ motion
rather than SOMA BVH. [Investigation evidence](records/uniform-fit-investigation.json)
records asset/source hashes, the static check and Studio manifest identity.
The historical availability statements below
describe the initial run and are superseded by this correction.

## Objective and cohort

Execute fresh correspondence sampling/training, full native retargeting, segment
bindings, and synchronized source-human/robot inspection for
`jump_and_land_light_001__A001.bvh`, using the same bundled G1 as the fresh SMPL-X
Getting_up experiment. This is a **generic neutral direct-SOMA control**, not an
official fitted BONES-SEED/MHR reproduction. It is native direct BVH reconstruction,
with no conversion of this clip to SMPL-X.

The requested fitted uniform BONES-SEED route is blocked by the absent
`shapes/soma_uniform_fit_mhr_params/soma_base_fit_mhr_params.npz`. The dataset's
`/data/motions/datasets/bones-seed/dataset.json` independently inventories missing
calibration. No actor shape was guessed or borrowed from another project.

Pinned `scripts/soma_source.py::load_soma_bvh_motion` sets fitted-route metadata
only when `find_boneseed_shape_params` finds that NPZ; uniform recognition also
expects a `motions_uniform` directory name. The actual source is under
`raw/uniform`, and no fit exists in its discoverable roots. Consequently its
native `source_format` is `soma_bvh`. The generic template and motion functions
discard `soma_usd_path` and use the verified neutral bind/T-pose mesh and BVH
global transforms with linear blend skinning. The missing dataset USD rig is an
inventory gap, **not a demonstrated runtime requirement** for this generic
route or the installed SOMALayer fitted route. The build log's printed USD path
does not establish that the file was loaded.

The generic control was executed after the parent disclosed that distinction
and allowed its labeled default after an optional clarification interval.
Original fitted-route execution remains pending the authoritative uniform fit.

## Provenance and independent runtime

- Input: `/data/motions/datasets/bones-seed/raw/uniform/210531/jump_and_land_light_001__A001.bvh`.
- SHA-256: `fe819b350aaf0cb269d810d32124a8e24931bd20586e305407aa59144b1cfaff`.
- Native UMR: `externals/UMR`, unchanged revision
  `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
- Interpreter: `externals/UMR/.venv/bin/python`, Python 3.12; complete package
  versions and implementation/configuration/asset hashes in the run's
  `provenance.json`. Torch `2.7.1+cu128`, CUDA runtime 12.8, NVIDIA GeForce RTX
  5070 Laptop GPU. Sampling and inspection ran on CPU; training and native solve
  ran in the host context exposing CUDA.
- SOMA-X assets: pinned NVIDIA revision
  `f81a01796f652260ff930d5318d6c6b845a505ed`, verified original assets and the
  separately documented UMR compatibility overlay under
  `/data/motions/human_models/soma-x/f81a01796f65/overlays/umr`.
  `LOCAL_MODIFICATIONS.md` describes the added public rig arrays; originals remain
  unchanged. Generic reconstruction does not run MHR identity fitting or pose
  correctives. The overlay template has 18,056 vertices, 36,108 triangles and 78
  public joints, all matched by name to the BVH.
- Dataset access and original BONES-SEED nonredistribution terms remain separate
  from NVIDIA's model license and robot assets. No downloads or license acceptance
  occurred; source BVH and model weights are not copied into this experiment.

Run: `/data/workspace/motion_studio/outputs/umr-baseline-g1-somax-20261102`.
Final inspector:
`/data/workspace/motion_studio/outputs/umr-baseline-g1-somax-20261102-inspection-04`.
All output paths are fresh, independent of historical aliases. Source input,
upstream revision/status and active implementation/assets were hash-checked after
training and retargeting; both preservation receipts pass. The prepared runner
was enhanced after preparation: `runner-prepared.py`, `runner-evolution.json`,
and per-stage `runner-*.py` snapshots preserve the exact executed source versions
and hashes. Current `run.py` also refuses outputs inside externals.

Small byte-identical metadata copies are retained in [records/](records/) for
Git review: [native provenance](records/provenance.json), [configuration](records/config.json),
[resolved settings](records/resolved.json), [validation](records/validation.json),
[training preservation](records/preservation-train.json),
[retarget preservation](records/preservation-retarget.json), per-stage completion
receipts, [runner evolution](records/runner-evolution.json),
[final inspection provenance](records/inspection-provenance.json),
[inspection preservation](records/inspection-preservation.json), and the
[final anchor/replay audit](records/replay-audit-04.json).
[Copied-records receipt](records/copied-records.json) records original absolute
paths, SHA-256 values and byte counts. Native outputs remain unchanged; heavy
tensors, weights and meshes stay under ignored outputs.

## Robot, bindings, and settings

The complete unchanged bundled `assets/g1` closure is copied into the fresh run.
Selection uses `robot_configs/humanoid_retarget_unitree_g1_example.json`:
29 scalar hinges, `waist_yaw_link` point-cloud center, left/right shoulder roll
`+/-1.57079632679` radians and both elbows `+1.57079632679` radians. The native
floating-root XML derivative is emitted only beside that copied XML. Its leading
qpos has XYZ metres and wxyz quaternion, followed by native hinge ordering saved
in `validation.json`. Eight official solve-limit overrides are retained.

Defaults come from `humanoid_retarget_defaults_bones_seed.json`, extending
`humanoid_retarget_defaults.json`. Complete resolved settings are saved in
`resolved.json`. Samples: two independently sampled 4096-point surfaces, seed 0,
spine1 source centering, 8× oversampling, first-hit exterior filtering. Training:
500 epochs, seed 0, all samples, per-sample-height normalization, official
geodesic edge/Chamfer/repulsion settings. Solver: official native19 body segments,
one iteration, sequential warm start, hard surface-slot ground constraint,
native source contact rules, and LQR trajectory filtering. No solver tuning.

Human segment labels use native
`soma_slot_part_ids_from_smplx_correspondence` with the verified SMPLX→SOMA mesh
correspondence assets; this is semantic transfer, **not SMPL-X motion conversion**.
All 19 labels occur. `binding.npz` preserves human face/barycentric bindings,
semantic part IDs, target rigid geometry owners/local positions and projections.
Robot body/mesh ownership and source semantic labels are distinct. Paired slots
are learned within this run and must not be treated as matching row identities
to the independently trained SMPL-X run.

## Motion conventions and processing

BVH frame time is 0.008333 seconds. UMR rounds reciprocal FPS to 120.0048;
its NPZ float32 serialization stores 120.00479888916016 (absolute difference
1.11084e-6). All 1165 frames `[0,1165)` are retained, without trimming, stride
changes or resampling; duration by frame-count/FPS is 9.7079451 seconds.
BVH offsets/translations are interpreted as centimetres and Euler channels as
degrees in their declared channel order by the pinned loader. Native SOMA
Y-up source points are mapped to robot Z-up as `[z,x,y]`; display maps native
robot coordinates back to Y-up as `[y,z,x]`. Native `source_ground_align=none`
and ground shift 0 are retained. The official human-height scaling is
0.7462310194969177 (template height 1.771973 m; robot height about 1.3223 m).
Finger rotations are zeroed by the official setting; original BVH bytes remain
unchanged. This neutral surface is not calibrated to the uniform BVH skeleton.

The inspector reconstructs the same native generic source motion and saved scale,
ground convention, finger setting and exact IDs. Human vertices use 64-frame
int16 root-relative chunks with 0.1 mm steps. The anchor is explicitly the moving
`Hips` public joint at index 1, validated to exist uniquely. Public `Root` index 0
is stationary and is not a pelvis anchor. Float64 robot transforms replay saved
qpos with geometry-local mesh/binding positions. Mesh filtering, native19 labels,
paired-slot selection, exact timeline seeks, reference pose, speed, camera controls
and display-only horizontal centering remain inspectable over local HTTP.

## Reproduction

From the Motion Studio root, choose a new run path; prepare refuses an existing
destination. The original actual commands are retained in `logs/*-completed.json`.
The following reproduces current scripts into fresh paths:

```sh
externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-somax-20261102/run.py prepare --output /absolute/fresh/run
externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-somax-20261102/run.py build --output /absolute/fresh/run
externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-somax-20261102/run.py train --output /absolute/fresh/run
externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-somax-20261102/run.py retarget --output /absolute/fresh/run
UMR_SOMA_ASSETS_PATH=/data/motions/human_models/soma-x/f81a01796f65/overlays/umr externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-somax-20261102/validate.py /absolute/fresh/run
externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-somax-20261102/export.py /absolute/fresh/run /absolute/fresh/inspection
externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-somax-20261102/audit_replay.py /absolute/fresh/run /absolute/fresh/inspection /absolute/fresh/audit.json
python3 -m http.server --bind 127.0.0.1 --directory /absolute/fresh/inspection
```

Train/retarget require host GPU access; view requires only local HTTP and WebGL.
Inspection is a separate fresh directory, never a descendant of the native run.

## Evaluation and limits

Measured wall times: sampling 10.483 s, training 38.376 s, full retarget 33.439 s.
`validation.json` passes finite `(1165,36)` qpos, full source IDs/rate within native
serialization precision, compatible saved dataset/slots, 29-joint order,
quaternion norm maximum error 5.96046e-8, and zero excess over combined model and
official solve limits. Joint step p95 is 0.0142854 rad/frame; maximum 0.245884
rad/frame. These are bounded diagnostics, not motion-quality certificates.

`replay-audit-04.json` checks every saved robot frame and all 4096 bindings,
human binary sizes/timeline and quantization, source face/bary replay, and every
moving Hips anchor against independently reconstructed BVH kinematics. Reference
robot slot projection mean is 0.00727047 m, p95 0.01968595 m, maximum 0.03751976 m;
projection measures static binding, not anatomical validity or fidelity.

Retained derivative history: the first inspector failed its preservation gate
because validation.json was added concurrently (no scientific input changed).
`-02` passed export but used stationary Root0 as a display/quantization anchor;
decoded world meshes were valid, horizontal centering and pelvis-relative metrics
were unsuitable. `-03` corrected Hips1. Final `-04` also makes the unique named
Hips contract explicit; all previous derivatives remain preserved. The failed
initial validator's exact-FPS equality was corrected to the explicit 1e-5 native
serialization tolerance before publishing successful validation.

The cross-model report separately compares static binding distributions and
within-clip source/robot diagnostics. The actions, source topology, calibration
availability, durations and rates differ, so it cannot isolate model quality.
No dynamics, controller, hardware, independent anatomical ground truth or
task-matched performance comparison is claimed. The official fitted BONES-SEED
run requires its authoritative uniform fit and a separate fresh cohort.
