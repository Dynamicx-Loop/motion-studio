# Experiment: fresh official G1 / SMPL-X getting-up baseline

Date / author: 2026-11-02 / Codex, requested by the project owner.

## Objective and cohort

Fresh official reproduction through Motion Studio's G1 interface: train a new
correspondence and retarget the complete bundled HiPHI `Getting_up-get_up_0004`
SMPL-X motion to the official bundled G1. The separately executed SOMA-X cohort
and cross-model comparison remain separate records. This is a new experiment;
the 33 archived experiment records and their output aliases remain unchanged.

Success requires fresh training, all source frames/FPS retained, finite outputs,
configured joint-limit/quaternion gates, inspectable human/robot bindings and
motion, and unchanged external sources/inputs. Numerical execution and replay
accuracy are measured. Contact, collision, foot-slip, dynamic feasibility and
hardware performance are not established.

Fresh native output:
`outputs/umr-baseline-g1-smplx-20261102/`.
Fresh standalone human/robot reference-binding and motion viewer:
`outputs/umr-baseline-g1-smplx-20261102-inspection/index.html`.
No historical dataset, checkpoint, slot array or motion was reused.

## Provenance and independent runtimes

- Pinned UMR: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; no local source
  patches. The revision, external status and all active source/configuration/G1
  asset hashes are recorded in [provenance.json](records/provenance.json).
- Motion Studio branch: `experiments/umr-baseline`. Exact root revision,
  implementation hashes and working-state evidence are in
  [source.json](records/source.json). Existing owned adapters
  `reproduce_g1_baseline` and `export_g1_bindings` were used without changes.
- Exact input:
  `externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`,
  SHA-256 `3a3d20c4ebd1727536136888efdde62f7ea685eb6ea0c88f1160116009416808`.
  Sequence key `motion_actor_smplx`; 5468 frames. The bundled
  [metadata](records/source-metadata.json) identifies actor A103, female, 163 cm;
  the converted SMPL-X file declares neutral model gender. This distinction is
  preserved, without asserting that neutral model gender is actor metadata.
- Licensed neutral SMPL-X model:
  `/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl`,
  SHA-256 `381c808965deb4f5e845f8c3eddb0cd69930cc72e5774ce4f34c4ce3cf058361`.
  Ten actor betas produce template `smplx_neutral_betas_52fa48a138`.
- Existing independent interpreter: `externals/UMR/.venv/bin/python`; GPU
  NVIDIA GeForce RTX 5070 Laptop GPU. Full package inventory is in
  [environment.json](records/environment.json). Native execution used authorized
  host CUDA access; no dependencies or environment were installed or changed.
- UMR software [MIT notice](records/UMR-LICENSE.txt) is preserved. HiPHI motion,
  SMPL-X model and robot mesh terms remain separate; UMR's software license is
  not a claim of rights to redistribute those assets. Raw outputs/weights stay
  local; this record contains hashes and small receipts, not model weights.

## Robot selection and representation

The native run uses pinned `assets/g1/g1_29dof.xml` and the shipped
`robot_configs/humanoid_retarget_unitree_g1_example.json`, copied to the fresh
run before generating a floating-root wrapper. Every robot asset file remains
byte-identical to the pinned original. The official generic pipeline is the
same route as the October 29 official reproduction; it learns the actor-shaped
SMPL-X template. The newer HiPHI wrapper's shared beta-zero correspondence route
is not silently substituted.

The public `Studio.add_builtin_robot('g1')` selection was separately imported in
fresh CPU-only state. Its full source closure equals this native run. Built-in
and official pose values, root XYZ/wxyz, native 29-joint ordering and
`waist_yaw_link` centering agree; every named body's reference position and
rotation differs by exactly zero. See [builtin-selection.json](records/builtin-selection.json)
and [inspection-validation.json](records/inspection-validation.json).
This establishes the requested selection/reference-pose agreement, without
asserting inertia, collision or hardware equivalence of wrapper implementations.

Root XYZ is `(0,0,0)`, quaternion wxyz `(1,0,0,0)`. All scalar joints are zero
except official shoulder-roll left/right `+/-1.57079632679` rad and elbow
left/right `+1.57079632679` rad. Units are metres/radians; source native Y-up,
robot native Z-up. Native hinge order is retained in the saved motion and
[validation.json](records/validation.json). The eight official solve-limit
overrides, visual `auto` policy and complete solver configuration are in
[resolved.json](records/resolved.json). No robot geometry/settings were changed.

## Processing and learned artifacts

All frame IDs `0..5467` and FPS `90.00090026855469` are retained; duration by
frame count/FPS is `60.75494782478813` s. There is no trim or resampling. Original
source bytes and channels remain intact; native surface reconstruction uses
neutral fingers and omitted facial channels. Native trajectory and viewer use
the saved source scale `0.7957031726837158` and zero native-Z ground shift.
Viewer placement/centering changes display only.

Sampling uses seed 0, 4096 points per surface, spine1 human centering, oversample
ratio 8, exterior first-hit sampling and occlusion distance 0.12 m. Training uses
500 epochs, batch size 2, seed 0, `all_samples`, per-sample-height normalization,
the official geodesic-edge/chamfer/repulsion settings and no checkpoint reuse.
Solver LQR, contact defaults, k=24 projected robot binding and native19 semantics
`smplx_55_to_19_upper_arm_v1` remain official defaults. The operational SMPL-X
batch cap is 128 for the local GPU; it does not change source frame selection.
Complete dataset/slot compatibility checks pass. Exact configuration and learned
artifact SHA-256 values are in [resolved.json](records/resolved.json) and
[artifacts.json](records/artifacts.json). Changed models/shape/pose/settings must
form a fresh cohort; no similarly named cache was substituted.

The standalone derivative replays saved qpos using float32 geometry transforms
and 86 human mesh chunks of at most 64 frames, int16 root-relative XYZ at 0.1 mm.
It includes all 4096 human semantic labels, human face/barycentric bindings and
robot geom-local/body ownership. Projection distances are reference diagnostics,
not motion-fidelity scores or saved per-frame solver telemetry. Export hashes and
preservation are in [inspection-provenance.json](records/inspection-provenance.json)
and [inspection-preservation.json](records/inspection-preservation.json).

## Reproduction

Run from `/data/workspace/motion_studio` with the existing licensed local assets
and host CUDA. Destinations must be fresh; the adapters refuse existing folders.
The actual commands were:

```sh
python3 -B scripts/reproduce_umr_g1.py \
  --output /data/workspace/motion_studio/outputs/umr-baseline-g1-smplx-20261102
python3 -B scripts/view_umr_bindings.py \
  --run outputs/umr-baseline-g1-smplx-20261102 \
  --output outputs/umr-baseline-g1-smplx-20261102-inspection
python3 -B experiments/umr-baseline-g1-smplx-20261102/verify_builtin.py \
  --run outputs/umr-baseline-g1-smplx-20261102 \
  --output outputs/umr-baseline-g1-smplx-20261102-builtin-02
externals/UMR/.venv/bin/python -B \
  experiments/umr-baseline-g1-smplx-20261102/validate_inspection.py \
  --run outputs/umr-baseline-g1-smplx-20261102 \
  --inspection outputs/umr-baseline-g1-smplx-20261102-inspection \
  --selection outputs/umr-baseline-g1-smplx-20261102-builtin-02/selection.json \
  --output experiments/umr-baseline-g1-smplx-20261102/records/inspection-validation.json
```

To view without the scientific runtime, serve the inspection folder using an
ordinary local HTTP server and open `index.html`. Direct file-URL support is not
claimed. All assets needed for the viewer are local; licensed weights are absent.

Native stages have exact command/cwd/start/end/exit-code receipts in `records/`
and retained original logs under the native output. External HEAD/status and all
recorded source/model/asset hashes were unchanged after execution; the entire
native run and external remained unchanged after export. No restore was needed.
The first CPU selection check remains in sibling `-builtin/`: its experiment
assertion compared a list with a tuple and stopped after import. The corrected
checker compares values after tuple normalization and ran in fresh `-builtin-02`;
there was no robot or product-code defect and no recomputation of the baseline.

## Evaluation

| Measured gate | Result |
| --- | --- |
| Prepare | 1.76946 s, exit zero |
| Sampling + 500-epoch training | 43.12742 s, exit zero |
| Full retarget stage | 101.84951 s, exit zero |
| Frame count / qpos | 5468 / `(5468,36)`, all finite |
| Timing / frame IDs | Exact source FPS and every source ID |
| Quaternion maximum norm error | `5.960464477539063e-8` |
| Model + configured limit maximum excess | `0` rad (tolerance `1e-6`) |
| Scalar-joint absolute step P95 / max | `0.02425267696 / 0.1531265974` rad/frame |
| Saved static robot geometry | Faces exact; vertices within `2e-7` m |
| Dataset / slot compatibility | Both pass; finite `(2,4096,3)` slots |
| All-frame robot replay axis error | `1.2429001672309425e-7` m (tolerance `5e-7`) |
| Human vertex quantization axis error | `5.0067901611328125e-5` m (exporter measurement, tolerance `5.1e-5`) |
| Built-in selection named-body reference error | `0`; joint order/closure/pose agree |
| External/input and completed-run preservation | Pass |

Runtime is one-machine observation, not a controlled performance benchmark.
The experiment validator independently applies native MuJoCo kinematics for
every saved frame and checks all 4096 robot binding positions against decoded
viewer bytes. The human quantization bound is the exporter's measurement; a
second full independent human reconstruction was not performed here.

## Observations and next step

The fresh scientific pipeline, static compatibility and inspectable replay gates
pass. Native19 label counts and source scale are in
[inspection-summary.json](records/inspection-summary.json). Source segment labels
and target rigid ownership remain distinct meanings. A learned correspondence's
anatomical correctness is not established by having a label or a small projection
distance. Parent-owned browser evidence and the separate SOMA-X comparison record
provide the cross-model visual review; no unsupplied visual quality score is
inferred here. Contact/slip/collision/dynamics remain unevaluated.
