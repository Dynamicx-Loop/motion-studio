# Final integration review resolution

Review baseline: `8ea1494…b5b2364`. Review fixes incorporate the official G1 pose
integration `8ad6730` and preserve its typed preset and byte-verified G1 ownership.

## Findings addressed

- **Standards P2 — adapter process details:** `NativeStages.launch` now owns UMR
  environment, runtime temporary directories and command provenance;
  `decode_progress` owns native progress decoding and `required_artifacts` owns
  native output names. Studio retains process-group cancellation, elapsed time,
  logs, confinement, dependency/hash checks and atomic publication. A behavioral
  Studio subprocess regression supplies a custom environment, progress convention
  and required filename and verifies completed status, observed counter and output.
- **Standards P3 — dependency cycle:** execution and job publication share a leaf
  UTC timestamp module. The native job runner no longer imports execution.
- **Cache duplication:** the owned historical and native viewers use one bounded
  cache source, including exact timeline/integer-frame validation. Export copies
  that source into each standalone bundle; packaging tests verify every relative
  application import resolves inside the bundle. Original integration viewer files
  remain unchanged.
- **Spec P2 — robot transform precision:** new exports explicitly declare schema 2
  and little-endian float64 matrices (`transform_dtype: "<f8"`). The exporter
  decodes saved bytes and rejects per-axis binding errors above the unchanged
  5e-7 m gate against native kinematics for every frame. The analytic regression
  adds native root translation `[100.123456, 50.123456, 0]` to the independent
  worked example: original bytes fail at 2.8623e-6 m, corrected bytes pass. Both
  viewers decode schema 2 and retain original absent-metadata float32 support;
  unknown encodings fail clearly. Original saved bundles are untouched.

## Validation

Durable reports: `outputs/studio-final-review-20261030/` in the canonical workspace.

- `check-pure.json`: all 26 selected pure suites passed.
- `check-robot-static.json`: all 3 selected robot-static suites passed, including
  the translated-root analytic fixture and existing historical playback checks.
- `cache-js.log` and `encoding-js.log`: frame races/cancel/retry/cache bounds and
  explicit float64/historical float32 encoding checks passed. Both viewer app
  files pass Node syntax checks. `git diff --check` passed.
- `original-precision-red.log` plus `reproduce-original-precision.py`: the unchanged
  original `b5b2364` exporter reproduces the translated-root failure.
- Corrected app HTTP service at port 8898 built a fresh full baseline motion
  derivative in 18.578 seconds from verified completed stage receipts. Run
  `0b9b5cf42653470f9121fcc759cdbfb7`, revision `r0003`, all 5468 frames. Export:
  `outputs/studio-baseline-acceptance-20261030/state/exports/0b9b5cf42653470f9121fcc759cdbfb7/r0003/retargeting/493ff609860540aa84471f026907c0fe`.
  `corrected-export.json` records the HTTP result; the bundle records implementation
  file hashes, native receipts and explicit encoding. Every saved robot binding
  passed the exporter gate with maximum axis error 0 m.
- `independent-full-reference.log`: all 3 existing independent saved-export tests
  passed in 18.171 seconds, decoding all human chunks/vertices/barycentric slots
  against native source and every robot frame/binding against `mj_forward`, plus
  exact-frame/FPS and model-file/hash rejection checks. Robot tolerance remains
  5e-7 m; human tolerance remains 5.1e-5 m.
- `preservation.json`: all 73 native stage artifact hashes still match their
  receipts. Previous full baseline derivative remains saved; its export listing
  is `outputs/studio-baseline-acceptance-20261030/exports-original.json`.

No native re-solve was needed for the orchestration/representation corrections.
The separately completed ticket 07 full 500-epoch/5468-frame native acceptance
and browser/quality observations remain recorded by ticket 07; representation
checks establish neither contact quality nor dynamic feasibility.

## Follow-up: cross-namespace recovery

Ticket 07 exposed an actual recovery defect when a restricted-shell service at
port 8898 read state owned by the host CUDA service: an owner absent from that
PID namespace was falsely marked interrupted. This incident is retained as a
failure, not evidence of successful crash recovery. The port 8898 service has
exited; no unknown process was signalled during cleanup.

The narrow correction records boot/PID namespace with each new job. Recovery
leaves foreign or unprovable owners active, publishes a visible `recovery_notice`
and blocks new launches. It signals groups only after confirming the same scope
and exact worker birth identity. A previous boot proves interruption but never
permits signalling that boot's stored PID. Invisible legacy records remain busy
until observed/cancelled from their owning environment. Same-scope real service
death keeps the existing explicit-retry behavior.

`test_studio_owner_scope.py` covers foreign namespace and legacy invisible owners
plus previous-boot PID collision using a real unrelated sentinel process. All
three pass; the original implementation fails the foreign-namespace regression
by returning `interrupted`. `owner-scope-lifecycle.log` records the existing real
service-crash/orphan/retry and lifecycle checks. Native final acceptance will use
fresh `outputs/studio-baseline-acceptance-20261030/final-cohort/state` under one
host CUDA service after this correction is committed; the initial cohort remains
preserved and is identified by its own source receipts.
