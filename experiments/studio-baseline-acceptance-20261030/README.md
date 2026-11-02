# Experiment: full offline local Studio G1 acceptance

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-30 / Codex, ticket 07.

## Objective and cohort

Official-default application reproduction: fresh sampling seed 0, 500 training
epochs, LQR and every frame of the bundled 5468-frame HiPHI getting-up clip.
Launch and exports use the application HTTP surface, with actual browser import,
pose, launch, inspection and lifecycle checks. Earlier smoke cohorts remain
separate. This establishes execution and representation, not contact, collision,
foot-slip or dynamic feasibility.

All durable evidence is canonical beneath
`/data/workspace/motion_studio/outputs/studio-baseline-acceptance-20261030/`.
The final accepted cohort is `final-cohort/`, run
`886f5c1ba3814b4eb268a84eeb8f1d1d`, immutable revision `r0003`, job
`9f6a6647060d4bc5afd7ecfec6f33124`, executed on final reviewed product code.
Its authoritative standalone bundle is
`final-cohort/state/exports/886f5c1ba3814b4eb268a84eeb8f1d1d/r0003/retargeting/3fc297a962064b93b04579c249415001`.
`final-cohort/evidence/exports.json` records all four stage bundles; the source,
commands, machine, runtime, numerical and browser records are alongside it.

The initial full run is `0b9b5cf42653470f9121fcc759cdbfb7`, revision `r0003`,
job `0802bf7bd90e4e2ab717aba70a4840a8`. It is retained unchanged. Its original
float32 derivative is listed in `exports-original.json`; the reviewed float64
full derivative is
`state/exports/0b9b5cf42653470f9121fcc759cdbfb7/r0003/retargeting/493ff609860540aa84471f026907c0fe`.
`exports.json` selects that corrected derivative. The historical `manual-01`
cohort and original synchronized viewer remain immutable references.

## Provenance and independent runtimes

- UMR pin: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, no upstream patch or
  dependency update. Every native stage receipt records source/default/preset,
  adapter, environment, request, closure and artifact hashes.
- Initial execution source: integration `b5b2364` plus the official-pose change
  committed as `a82eaf5`; `tested-source.json` stores exact working file hashes.
  Reviewed exporter source is integration `cc4f6d1`; `reviewed-source.json` and
  bundle provenance record exact implementation bytes. Refactoring adapter
  identity intentionally invalidates future computational reuse; preserved
  outputs remain available for viewing.
- Interpreter: canonical `externals/UMR/.venv/bin/python`, Python 3.12.3,
  PyTorch 2.7.1+cu128, NumPy 1.26.4, MuJoCo 3.3.7, RTX 5070 Laptop GPU.
  CUDA required host escalation because sandbox CUDA is unavailable. No package
  installation or environment changes were made. Exact package inventory is in
  receipts. Native workers remove inherited Python paths and disable user-site
  imports; command environment overrides remain in each attempt.
- Original clip: pinned
  `sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`,
  SHA-256 `3a3d20c4ebd1727536136888efdde62f7ea685eb6ea0c88f1160116009416808`.
  The safe importer preserves original bytes and creates a numeric/string-only
  managed version, asset `dfd53dd7aa7058ce5af055a9b7f62ff381553f9cd4f640019daf38e4139ed004`.
- Neutral weights are read only from the exact validated file
  `/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl`,
  SHA-256 `381c808965deb4f5e845f8c3eddb0cd69930cc72e5774ce4f34c4ce3cf058361`.
  No weights enter the bundle. Robot, dataset and licensed human-model terms
  remain separate; vendor notices/hashes accompany each bundle.
- Method statements derive from inspected pinned native source. No new reference
  citation keys were introduced. The native/inspection smoke records document
  the same adapter semantics and source barycentric diagnostic distinction.

## Robot selection and representation

The UI imports the exact pinned G1 29-DoF XML/mesh closure, derives a free root on
a managed copy, loads **Load official G1 T-pose**, and explicitly saves the pose.
Only a byte-verified official closure/configuration receives that preset and G1
solve limits. Other imports retain generic numeric/named poses. Four shoulder/
elbow values come from the pinned preset; every other named scalar is explicit.
Root XYZ/wxyz is zero translation/identity; waist-yaw body is the centering frame.

The native adapter materializes its separately recorded official floating wrapper,
while preserving imported/managed source bytes. The ticket 04 independent named-body
pose comparison demonstrated zero wrapper pose error. Units are metres/radians,
native robot Z-up, root quaternion wxyz, compiled hinge order retained in motion.
Visual geometry and rigid ownership checks do not establish inertia, collision
or hardware calibration equivalence.

## Processing and learned artifacts

Native source FPS is 90.00090026855469, constant and Y-up. All frame IDs
`0..5467` are retained without trimming, resampling, interpolation or nearest-frame
fallback. Original full SMPL-X channels remain stored, while native reconstruction
uses root/body with neutral hands and omitted face channels. Ten actor betas and
model identity appear in the motion asset/receipts.

Sampling uses 4096 paired points, seed 0 (effective human 1000, robot 9000).
Training uses 500 epochs and seed 0. Native19 semantics, projected rigid binding,
binding k=24 and the solver defaults remain fixed; the operational SMPL-X batch
cap 128 is separate from scientific quality. Complete merged configurations,
normalization, checkpoint/slot order, dependency fingerprints and validation
findings are retained per stage. No historical checkpoint is substituted.

Human display uses 64-frame int16 root-relative chunks at 0.1 mm steps; robot
schema 2 stores float64 3×4 transforms. Display centering and side-by-side placement
change translations only. Chunk loading commits both tracks together. The final
exporter decodes and verifies every robot binding at every saved frame against
native kinematics before publication, with the original 5e-7 m tolerance.

## Reproduction

Run from this source checkout with host CUDA and existing local assets. The
initial actual UI/API service command was:

```sh
python3 -B scripts/studio.py \
  --state /data/workspace/motion_studio/outputs/studio-baseline-acceptance-20261030/state \
  --port 8897 \
  --history-root /data/workspace/motion_studio/outputs/umr-g1-inspection \
  --history /data/workspace/motion_studio/outputs/umr-g1-inspection/manual-01-synchronized
```

The browser created/imported/saved the inputs, reviewed CUDA prerequisites and
clicked **Launch reviewed plan** with `{through: retargeting, settings:
{sampling_seed: 0, epochs: 500, trajectory_filter: LQR}}`. `launched-state.json`,
`completed-job.json`, `receipts.json`, `job-observations.json` and `finish-http.py`
retain the exact selected IDs, plan, commands, fingerprints and HTTP derivations.
The initial job ran from 05:17:44.047249 to 05:20:32.729523 UTC: 168.682 seconds
including orchestration. Last observed stage elapsed values are observations,
not percent completion or promised performance.

Reusable experiment drivers require fresh evidence directories and call only the
owned HTTP interface. Start a fresh host service, then run:

```sh
python3 -B experiments/studio-baseline-acceptance-20261030/run_http.py \
  --url http://127.0.0.1:8900 --evidence /absolute/fresh/evidence
PYTHONPATH= PYTHONNOUSERSITE=1 \
  /data/workspace/motion_studio/externals/UMR/.venv/bin/python -B \
  experiments/studio-baseline-acceptance-20261030/validate.py \
  --evidence /absolute/completed/evidence
```

No restore was needed. Whole-original preservation is checked by
`outputs/studio-implementation-preservation-20261030/verify.py`, using its existing
`before.json`: all 288 original viewer/run files and every pinned external HEAD/
status must remain identical. Evidence never lives inside a disposable code worktree.

## Evaluation

The independent validator reads the saved model and motion, calls MuJoCo
`mj_forward` and native SMPL-X reconstruction separately from export, and tests
frames **0, 63, 64, 1800, 2303, 5467**. It checks source timing, full qpos, native
joint ordering/limits, mesh topology/local vertices, decoded human vertices and
barycentric slots, and rigid robot bindings. Expectations come from native
references, not exporter-produced expected positions.

Initial reviewed-bundle measured gates (`independent-numeric-gates.json`):

| Gate | Measured | Required |
| --- | --- | --- |
| Frames/qpos | 5468 × 36, finite, IDs exact | All frames, native nq |
| FPS error | 0 | <=1e-6 |
| Root quaternion maximum norm error | 5.960464477539063e-8 | <=1e-6 |
| Joint-limit maximum excess | 0 rad | <=1e-6 rad |
| Selected-frame robot binding maximum axis error | 4.440892098500626e-16 m | <=5e-7 m |
| Selected-frame human vertex maximum axis error | 5.0079917907730476e-5 m | <=5.1e-5 m |
| Selected-frame human binding maximum axis error | 4.995861053469497e-5 m | <=5.1e-5 m |
| Target local mesh vertices/faces | Exact | vertices atol 2e-7 m; faces exact |

The reviewed exporter additionally reports all-frame decoded robot binding error
0 m. Root final-review evidence independently compared **all human chunks and
all robot frames** through the existing saved native-reference suite (3 tests,
18.171 seconds), supplementing these six distributed boundary checks.

Initial observed native training ended at epoch 500 with 33.1 seconds last log
elapsed; retargeting ended at 5468/5468 with 107.88 seconds. HTTP exports took
4.350/5.511/4.073 seconds for sampling/training/binding, 18.357 seconds for the
original moving bundle; reviewed moving export took 18.578 seconds. These are
single-machine observations. Config comparison with historical `manual-01` is
saved as `historical-config-comparison.json`: scientific defaults/seed/500 epochs/
LQR/full selection agree; managed paths/sequence name, exact weight-file selection,
explicit formerly implicit defaults/zero pose values and explicit orchestration
are recorded differences. New stochastic training need not be byte identical.
Both cohorts retain finite 5468×36 motion, timing and representation gates.

Browser evidence in `browser-evidence.json` records imports/pose/launch, historical
browsing during compute, all stage availability, exact scrubbing, filtered paired
ownership, mesh visibility, camera presets, centering/reference pose, speed,
looping and exact final-frame end-stop. A leftHand selection showed 98 slots and
slot 2594 attached to left_wrist_yaw_link, geom 74. Corrected full motion used the
reviewed bundle in both app and standalone HTTP. Measured exact seeks were
35/21/125/127/130 ms for frames 63/64/1800/2303/5467. Cached stage click readiness
was 311 ms; standalone reload-to-frame-0 readiness 551 ms. At speed 1, source
frame 1800 advanced to 2090 in 3562 ms including control calls; this measures
source timeline progression, **not rendered-frame throughput**. Frame skipping
is allowed; no claim to render every ~90 FPS source frame is made.

`offline-resource-audit.json` lists observed app and standalone resources: all
loopback, no external dependency observed. Networking was **not disabled**.
`standalone-file-audit.json` verified all 182 registered file hashes; standalone
viewing used only Python's static HTTP server on port 8899, with no native runtime
call. No file-URL/double-click support is claimed. Console warning/error reads
were empty during completed checks. A subsequent viewer load after its temporary
service exited correctly failed to fetch; that service-lifetime event is separate
from the successful playback/resource audit.

Initial owning checks: 26/26 pure suites and 3/3 robot-static suites pass. The
human cache, exact frame-request and transform-encoding JavaScript suites pass.
Official-pose HTTP regression observed red 404 before implementation and green
success plus generic-source refusal afterward; existing generic import/pose
regressions pass. Checked commands/results live in the canonical evidence root.

## Observations and next step

Visual judgment: source human and retargeted robot remain synchronized through the
getting-up/crouching sequence, with surfaces and selected rigid attachments moving.
Projection distances are reference diagnostics, not quality scores. No contact,
foot-slip, collision or dynamics evaluation was performed or inferred.

A separate epochs-499 revision preserved the full original revision and reused
sampling while visibly marking affected stages stale. Actual browser closure/
reopening left its training active; browsing history and **Stop active job**
cancelled at observed epoch 1, retaining logs. **Review explicit retry** allocated
a fresh attempt. That retry was marked interrupted by a temporary second service
in another process namespace, which could not observe the host owner PID. This
is retained in `cancelled-native-state.json` and `retry-completed-state.json` as a
real failure found during acceptance, not claimed as successful crash recovery.
The final-review correction records boot/PID-namespace ownership, treats an
unobservable owner as unknown/busy, and never signals an unverified PID. The
fresh final acceptance below repeats native execution under one host service;
fixture ticket 06 separately covers service death and descendant cleanup.

Ticket 07 remains claimed until final standards/spec closure. Do not interpret
this record's measured gates as permission to waive remaining required checks.


## Final reviewed-code acceptance and closure handoff

The final host service used fresh `final-cohort/state` on port 8900, code commit
`a6aa5c2336c010312e3ec4049fbfd6aef3850fc5` containing reviewed integration
`e4e0eb25fa2051551f8125ce0bfd373e847e2d66`. No product code changed between
this full run, cancellation and retry. `final-cohort/source.json` stores exact
source hashes; `commands.json` records the actual service/HTTP commands.
`machine.json` records Intel i9-14900HX, 32 logical CPUs, 32,571,000 kB RAM and
Linux 7.0.0-38. The runtime receipt records the RTX 5070 Laptop CUDA environment.
The job records its boot ID, host PID namespace, owner PID and kernel birth
identity; browsers and the HTTP driver never opened application state directly.

The final full job ran 05:29:47.550091–05:32:41.353442 UTC, **173.803 seconds**
including orchestration. Observed retarget elapsed was **108.95 seconds**.
HTTP sampling/training/binding/moving exports took **4.305 / 5.213 / 3.937 /
21.405 seconds**. Every selected-frame gate above repeated with the same measured
bounds, including exact static target reference vertices/faces. Final independent
all-human-chunks/all-robot-frames reference tests passed **3/3 in 20.754 seconds**.
See `evidence/independent-numeric-gates.json`,
`evidence/full-native-reference.log`, `evidence/stage-preservation.json` and
`validation.log`.

Actual final-code lifecycle validation used separate revision `r0004`, epochs 499.
Sampling remained available with an authenticated `r0003` receipt; affected stages
became visibly stale. Browser closure/reopening and historical browsing left native
training active. **Stop active job** cancelled job
`31f4a2e065e849c08ae8dc78052b66f8` at observed epoch 100, retaining
`attempt-4cb9597189b64a978a42e780a2aac325`. **Review explicit retry** launched only
training as job `e7f22f0b6aea41b9b840e0a8f5297529`, fresh
`attempt-34b2950dec8a45899736175017ec0509`. It completed with a validated
499-epoch checkpoint, observed elapsed 34.25 s; its last periodic log was epoch
400 rather than an invented 499 progress line. No namespace interruption recurred.
The original full revision remained browsable throughout. `lifecycle-*.json`
retain states, both attempts and verified reused receipts.

Final browser checks inspected the sampling distinction (paired lines disabled),
training pairs without ownership, pre-solve binding ownership, then synchronized
motion. Reopened `r0003` stayed immutable while retry computed. Six exact seeks
0/63/64/1800/2303/5467 took **46/20/25/225/234/227 ms** including control calls.
The final standalone HTTP bundle reached frame 0 in **2991 ms** including opening
and observation. Step 63→64, final-frame end-stop, loop 5466→2, source filtering,
selected ownership, reference pose, centering, meshes, paired lines and camera
presets passed. Console warnings/errors were empty. The 18 observed standalone
resources were all local, including chunk 085; networking remained enabled.
These observations and their limits are saved in `browser-evidence.json` and
`offline-resource-audit.json`.

Final owning checks passed **27 pure suites**, **3 robot-static suites** and the
three JavaScript cache/frame/encoding suites. The official-pose HTTP test passes
for all four preset joints and rejects a generic robot even when its filename is
`g1_29dof.xml`. All 73 original final-cohort native artifact hashes and all 182
bundle file hashes still match after cancellation/retry. The whole-original
288-file/external receipt also passes (`original-preservation-final.json`).
New documentation links, script syntax and whitespace were checked.

Both integration reviewers cleared the product and namespace correction. Ticket
07 is ready for root closeout after reviewing this final documentation/evidence
delta; it remains claimed until that explicit orchestration step. Temporary owned
services are stopped only after all jobs become terminal. Restart from canonical
integrated source with the final managed state; selected revision `r0003` is saved.
