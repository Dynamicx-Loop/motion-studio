# Fitted BONES-SEED uniform → native UMR → bundled G1 prototype

Date: 2026-11-02. Branch: `experiments/umr-baseline`. This experiment owns its
configuration, recognized input layout, orchestration, validation and inspector.
No product modules, upstream source, dependency pins, old outputs or source data
were changed. User acceptance remains pending review of the completed prototype.

## Objective and cohort

Execute the selected jump-and-land through UMR's **fitted uniform** SOMA route,
then inspect the full source/robot motion and compare against the immutable
[generic neutral surface control](../umr-baseline-g1-somax-20261102/README.md).
This is a native fitted prototype with official bundled G1 configuration and
native SOMA defaults; it does not claim equivalence with UMR Studio's browser
source pack or CPU solver. Input BVH motion is never converted to SMPL-X.

Completed numerical run:
`/data/workspace/motion_studio/outputs/umr-baseline-g1-soma-uniform-prototype-20261102-02`.
The unsuffixed path preserves the initial sandbox attempt: strict preparation and
CPU sampling passed, then CUDA training failed because the sandbox exposed no
CUDA device. The entire numerical pipeline was rerun freshly under host GPU
access at `-02`; no partial dataset, checkpoint or slots were reused.

## Provenance and runtime

- Input: `/data/motions/datasets/bones-seed/raw/uniform/210531/jump_and_land_light_001__A001.bvh`.
  SHA-256 `fe819b350aaf0cb269d810d32124a8e24931bd20586e305407aa59144b1cfaff`.
- Shared fitted identity: `/data/workspace/notAnyrobot/kimodo/kimodo/assets/skeletons/somaskel30/soma_base_fit_mhr_params.npz`.
  SHA-256 `61f0b96c8386a19d44823faf4399816642b7e20691ed5b398c7402921090096e`.
  The [integration investigation](../../docs/umr-soma-boneseed-integration.md)
  records its independently verified official Kimodo provenance.
- UMR pin: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; independent interpreter
  `externals/UMR/.venv/bin/python`, Python 3.12, Torch `2.7.1+cu128`, CUDA runtime
  12.8; NVIDIA GeForce RTX 5070 Laptop GPU, driver 580.178.04, 8151 MiB.
- SOMA-X assets: revision `f81a01796f652260ff930d5318d6c6b845a505ed`, existing
  compatibility overlay `/data/motions/human_models/soma-x/f81a01796f65/overlays/umr`.
  Its `LOCAL_MODIFICATIONS.md` records existing overlay derivation. Complete active
  assets, SMPLX semantic-transfer files, tracked upstream implementation/config/G1
  closure, originals and run-local input copies are SHA-256 inventoried.
- Runtime packages and source hashes are in `provenance.json`; hardware evidence
  is in `runtime-hardware.json`. Numerical scripts are preserved in `code/`;
  `code/run-inspection.py` separately preserves the later inspection orchestration
  (audit destination and receipt location changes only).

The semantic segmentation asset was explicitly resolved and SHA-256 recorded
after the run in [semantic provenance](records/semantic-segmentation-provenance.json):
`externals/UMR/assets/smplx_parts_segm.pkl`, hash
`bb69c10801205c9cfb5353fdeb1b9cc5ade53d14c265c3339421cdde8b9c91e7`,
byte-identical to its tracked blob at the recorded UMR pin. The pre-run complete
upstream diff check and unchanged status receipts cover that pinned identity. No
optional mapping config resolved; mapping constants are in pinned source. Future
preparation now explicitly hashes the resolved segmentation path too; the originally
executed preparation source remains preserved in the native run.

The adapter copies BVH and fit bytes into the fresh output's
`input/bones-seed/{motions_uniform/bvh,shapes/soma_uniform_fit_mhr_params}` and
links its `soma_assets` to the recorded overlay. This deliberately satisfies the
pinned loader's recognized ancestry without changing original dataset layout.
Before sampling, every stage requires `source_format=soma_bvh_boneseed_uniform`,
`soma_template_name=soma_uniform`, the exact fit hash/path and the selected assets.
The missing-fit probe demonstrates the native loader's generic fallback and our
strict rejection **before loading a body model or training**.

Existing dataset/model/robot access terms remain separate. No downloads or license
acceptance were performed. Restricted BVH/fit/model bytes remain in ignored local
outputs and are not included in tracked experiment records.

## Robot and processing contract

The unchanged bundled `assets/g1` closure is copied into this run. Native
`robot_configs/humanoid_retarget_unitree_g1_example.json` selects its 29 hinges,
`waist_yaw_link` surface center, shoulder roll ±π/2 and elbow +π/2 T-pose,
and eight official solve-limit overrides. The generated floating-root XML stays
beside the run-local XML. Native qpos order is XYZ metres, wxyz, then recorded
hinge names. Nothing is inferred from a similarly named robot catalog entry.

All 1165 BVH frames are retained at native loader rate 120.0048 FPS, without
trimming, stride changes or resampling. The source contains centimetre translations
and declared degree Euler channels. Fitted SOMALayer reconstructs the shared MHR
identity/scale at mid LOD with pose correctives disabled. The template and every
motion frame have 18,056 vertices, 36,108 identically ordered triangles and 78
uniquely name-matched public joints. Native finger rotations are zeroed. SOMA
Y-up geometry maps `[z,x,y]` into robot Z-up; source ground alignment is `none`,
ground shift zero. Native human-to-robot height scale is 0.7407795190811157.

Fresh surface sampling uses 4096 points each, seed 0, native source spine1
centering, 8× oversampling and first-hit exterior robot filtering. Fresh
correspondence training uses 500 epochs, seed 0, all samples and native height
normalization, geodesic/Chamfer/repulsion settings. Retargeting retains native19
semantic budgets/contact defaults, sequential warm start, one iteration and LQR
trajectory filtering. SMPLX→SOMA asset correspondence transfers semantic surface
labels; this does not convert the motion to SMPL-X. The fitted body and its
motion reconstruction are the intended cohort difference from the generic
control; independently learned slots do not share semantic row identity.

## Reproduction

From `/data/workspace/motion_studio`, choose a previously unused output under
`outputs/`. The following single command executes preparation, fresh sampling,
training, retargeting, full numerical validation, inspector export, replay audit
and the generic-control comparison:

```sh
externals/UMR/.venv/bin/python -B experiments/umr-baseline-g1-soma-uniform-prototype-20261102/run.py all --output outputs/<fresh-run-id>
```

The successful `-02` execution was staged while these prototype scripts were
developed: the numerical pipeline ran through `all --skip-inspection`, followed
by inspection export and separately preserved audit/diagnostic/comparison commands.
The final single-command chain above has been reviewed for argument/data flow
and its stages executed, but has not been rerun as one whole command.

Host GPU access and the existing assets/environment are prerequisites. Existing
run or derivative destinations are refused. `--skip-inspection` runs the numerical
pipeline only; the same `run.py inspect --output outputs/<run-id>` adds its fresh
sibling inspector/comparison. Individual `prepare`, `build`, `train`, `retarget`
and `validate` stages are also available; their existing receipt/output files are
refused. Each native stage saves its exact command, environment, wall time, log
and source-preservation receipt. `run_manifest.json` hashes fresh dataset,
checkpoint/slot artifacts and retargeted motion. Reproduce from the authoritative
original assets plus recorded copied layout; old outputs are never writer inputs.

## Measured numerical results

Sampling took 13.404 s, 500-epoch training 38.916 s, full native retarget 37.087 s.
Validation reconstructed all 1165 fitted source frames and confirmed finite
vertices/joints and invariant topology/face order. Saved G1 motion is finite
`(1165,36)` with exact frame IDs/order and the recorded 29-joint order. Maximum
wxyz norm error is 5.96046e-8; maximum excess over combined model and official
solve joint limits is zero. Joint-step p95 is 0.01520294 rad/frame and maximum
0.27251029 rad/frame. These are diagnostic measurements, not quality guarantees.

Native NPZ serializes FPS as float32 `120.00479888916016`, differing from loader
rate by 1.11084e-6. Validation allows one float32 ULP, 7.62939e-6, justified by
that serialization. Duration by frame count/FPS is 9.7079451 seconds. Dataset/slots
pass the pinned pipeline's compatibility guards. Original BVH/fit, model assets,
upstream hashes/revision/status and prepared script snapshots passed preservation
after build, train, retarget and validation.

## Inspection and limits

Inspection and same-clip comparison are separate fresh derivatives, retaining the
source-human mesh, fitted skeleton, independent BVH skeleton, native19 labels,
source/robot bindings, all-frame robot replay and reference pose. The moving
`Hips` joint is the explicit encoding/display anchor; public `Root` is stationary
for this clip. Each inspector also retains its executed source files and input
preservation receipt. The generic control remains immutable.

Numerical validation, replay/inspection checks and user acceptance are distinct.
Numerical validation and the final all-frame replay audit passed. Browser
checks are recorded separately, and user acceptance remains pending.

The source mapping follows the pinned loader's public-root convention. Replay
audits check omitted Root channels, named mapping, native reconstruction,
quantization, bindings and robot transforms; matching does not imply fitted and
BVH skeleton bone positions are equal. Full mesh storage uses root-relative
0.1 mm int16 chunks, recording quantization as information loss.

Replay auditing requires the recorded CUDA device/runtime, Torch threads 2,
OpenMP/OpenBLAS threads 4, CUDA device selection 0 and exact SOMA asset paths
before numerical imports. A controlled 64-frame diagnostic measured repeated
native fitted forwards varying by up to 1.90735 µm on vertices and 1.78814 µm
on joints in the same process; this is independent of mesh quantization.
The explicit mesh/slot budget is 53 µm: 50 µm encoder half-step, 2 µm measured
native repeatability and 1 µm arithmetic margin. Fitted skeleton replay allows
3 µm; Hips/root and independent BVH FK gates remain unchanged. The diagnostic
separately gates own-reference quantization at 50.1 µm and native repeat at 2 µm.
An unmatched-environment attempt reached about 77 µm and failed; the exact-env
full replay reached about 51.1 µm. Initial overly strict gates, the NumPy indexing
fix and all failed diagnostic attempts remain preserved with executed sources
and logs. These tolerances establish bounded same-runtime replay precision,
not bitwise or cross-runtime equality.

The final all-1165-frame audit measured source mesh axis error 51.3501 µm,
4096 barycentric source-slot error 50.6866 µm, fitted skeleton error 1.43051 µm,
moving-Hips anchor error zero, and all 4096 rigid robot-slot replay error zero.
Independent BVH forward kinematics agrees with native transforms within
1.66533e-15. The final runtime-matched diagnostic measured native repeatability
1.43051 µm; earlier 1.90735 µm diagnostics remain retained. Exact native source,
fit and all audit inputs passed their preservation gate.

This single-clip, single-seed prototype has no controller, dynamics, physical
hardware, independent anatomical correspondence ground truth or task-success
validation. Contact, slide, smoothness, label coverage and binding diagnostics
should guide visual review; they do not establish dynamic feasibility. Measured
comparison results and visual judgments are kept distinct. Broader reusable Studio
SOMA integration and additional clips remain follow-up work.
