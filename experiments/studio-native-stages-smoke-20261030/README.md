# Experiment: explicit Studio native stages and pre-solve binding

Date / author: 2026-10-30 / Codex ticket 04 implementation.

## Objective and cohort

Deliberately selected focused smoke cohorts, not official reproduction/default
quality acceptance. Demonstrate explicit sampling → training → binding → retarget,
source preservation, exact selected-frame output, and static binding without a
motion solve. Both cohorts use two epochs and a separate three-frame fixture.
Measured representation checks are reported below; motion/contact/dynamics quality
and the required full 500-epoch/5468-frame acceptance remain ticket 07.

Fresh outputs (canonical workspace, never reused as writable destinations):

- G1: `/data/workspace/motion_studio/outputs/studio-native-smoke-04-06`,
  run `c1f04cf853e64038bfde9882cbced282`, revision `r0004`,
  job `2bd05b09e6fa4d83a40af8c1a29b3d8d`.
- Primitive import: `/data/workspace/motion_studio/outputs/studio-native-smoke-04-primitive-03`.
  Exact run/job identities are in its `smoke.json` and stage receipts.

Earlier `studio-native-smoke-04-01` through `-05` and primitive `-01`/`-02` retain
exploration/failure evidence. They are superseded by the exact-model-file cohorts
above, not retroactively rewritten or claimed as final acceptance.

## Provenance and independent runtimes

UMR `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, no external patch. Studio implementation
starts at `f227e2e`, merged import hardening `92ba5b0`, then reviewed fixes; exact
adapter/native file SHA-256 values are captured in every stage receipt. All
native Python source/default/preset hashes and runtime package versions are saved.
Scientific imports run only under
`/data/workspace/motion_studio/externals/UMR/.venv/bin/python`:
PyTorch 2.7.1+cu128, NumPy 1.26.4, MuJoCo 3.3.7,
NVIDIA GeForce RTX 5070 Laptop GPU. Host escalation was required because sandbox
CUDA is unavailable. Worker removes `PYTHONPATH`/`PYTHONHOME`, preserves `HOME`,
and sets `PYTHONNOUSERSITE=1`; command/environment changes are recorded.

Source is the pinned bundled HiPHI
`sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
`smoke.json` records its full SHA-256 and the deliberate fixture conversion.
Original source remains intact; fixture contains the first three pose/translation
frames and unchanged constant shape/timing metadata. Safe import creates a numeric/
string-only normalized NPZ. Source asset ID, original/normalized hashes, ten betas,
gender and model hash are in request/receipts. Licensed local neutral weights are
referenced by **exact file** `MotionAsset.model_path` for both sampling and
reconstruction; directory overlay/alternate-weight selection is disabled by this
route. Weights are never copied, edited or redistributed. Native segmentation
uses pinned `assets/smplx_parts_segm.pkl` and the native built-in 55→17 mapping;
actual map/segmentation hashes are recorded. No new citation keys were created;
method claims here come from inspected pinned source. Upstream robot/dataset/model
license and notice obligations remain separate.

## Robot selection and representation

G1 imports the pinned bundled XML/mesh closure, saves the official four-joint
T-pose, all other named scalar values, root XYZ/wxyz and waist-yaw centering.
The adapter verifies official source bytes before applying G1-only solve limits.
Its private XML replaces generic pelvis freejoint derivation with native's
additional `unitree_g1_float_root` wrapper (0.001 kg, 1e-6 kg m² diagonal inertia).
Original/managed assets remain immutable. The pinned pelvis local transform is
identity; every named body's compiled world pose before/after is independently
checked at 1e-10. Observed position and orientation errors: exactly zero.

The primitive fixture has box/capsule geometry, one finite-limit named hinge,
root `[.2,-.1,1]` metres, yaw quaternion wxyz
`[.9238795325112867,0,0,.3826834323650898]`, hinge `.4` radians and torso centering.
It receives no G1 limits/wrapper. Named-body world-pose errors are zero. The
fixture is an ownership/primitive import check, not a humanoid quality claim.

## Processing and learned artifacts

Both cohorts: sampling seed 0 (human effective 1000, robot 9000), 4096 paired
points, pinned surface/exterior/normalization/training/solver defaults, training
seed 0, two epochs, trajectory filter UI `none` → native `off`. SMPL-X batch cap
128 is an operational override. Saved FPS is 90.00090026855469, source Y-up,
robot Z-up, metres/radians, root quaternion wxyz. No resampling/interpolation.
The application processes all three frames of the independently selected fixture;
it does not internally trim the selected motion. Native reconstruction uses
root/body, neutral hands and omits expressive face/hands, with originals retained.

Dataset/training/binding/motion hashes, exact captured dependency receipts,
semantic fingerprints, full merged configuration, commands and validation findings
live under stable `attempt-<uuid>` stage paths. Native stages use separated calls
with `force=True`; no native pipeline/implicit prerequisite/cache path is used.

Binding preserves native face+bary representation. The primitive learned source
contains a tiny triangle where native returns vertex-0 bary weights while its raw
closest-point diagnostic differs by `0.00014101527631282806` metres per axis.
Published source positions reconstruct face+bary, matching solver replay; raw
native closest points/errors and per-slot discrepancy remain separately recorded.
Native semantic labeling inputs stay unchanged. No tolerance was weakened.

## Reproduction

From Motion Studio, with host GPU access and the existing licensed assets:

```sh
python3 -B scripts/smoke_studio_native.py --output /absolute/fresh/g1-smoke
python3 -B scripts/smoke_studio_native.py --output /absolute/fresh/primitive-smoke --primitive
STUDIO_G1_SMOKE=/absolute/fresh/g1-smoke \
STUDIO_PRIMITIVE_SMOKE=/absolute/fresh/primitive-smoke \
  python3 -B -m unittest discover -s tests -p test_studio_native_runtime.py -v
```

The actual final commands used output directories `studio-native-smoke-04-06` and
`studio-native-smoke-04-primitive-03` above. Existing destinations are refused.
The service first saves immutable managed inputs; no native call receives an
original import path. No preservation/restore operation was needed.

## Evaluation

- Final G1: validated sampling `(2,4096,3)`, native SMPL-X mesh topology, final
  two-epoch checkpoint and slots, 4096 pre-solve native19 bindings, qpos `(3,36)`,
  exact frame IDs `[0,1,2]`, exact FPS, quaternion max error
  `5.960464477539063e-08`, joint-limit max excess `0` rad.
- Final primitive: sampling/training/binding complete; no `motion.npz` exists.
  Native target reference faces exact, vertices tolerance 2e-7 m, rigid target
  replay tolerance 5e-7 m. Primitive mesh ownership uses optional mesh names.
- Saved native regression: 2/2 pass with explicit final output paths. It covers
  exact weight-file config, official wrapper equivalence, exact frames, primitive
  ownership/no-G1 limits/no-motion and source bary fallback representation.
- Public Studio/HTTP suite: 39 tests, 37 pass plus 2 explicit saved-cohort tests
  skipped without environment paths; those two separately pass above. Eight
  execution tests include failure/no-output, cancel/fresh retry, exclusivity,
  settings revisions, HTTP/log/artifact/receipt access, tampered output and changed
  prerequisite during/after training. Review reproductions observed red→green.
- Root pure checks: 24/24 suites pass. Existing UMR integration/canonical/inspection
  suites pass 5/13/5 tests. JavaScript syntax and whitespace checks pass.
- Actual loopback browser: selected final G1 cohort, saved epochs/filter restored,
  all four compute-stage availability/log links visible, completed frame progress
  says output validated. Review plan reports no missing work after exact receipt
  checks, without launching another job. Numeric pose preview and local resources
  loaded. Rich stage/animated inspection/export belongs ticket 05.

## Observations and next step

This establishes bounded numerical execution and representation, not contact,
foot-slip, collision, dynamic feasibility, or full/default learned quality.
Historical outputs, external source and original viewer received no writes.
Full-clip/default acceptance stays mandatory in ticket 07. Ticket 05 consumes
verified artifact/receipt APIs and exact weight-file provenance; ticket 06 deepens
cancellation/recovery/revision UX and service-interruption handling.
