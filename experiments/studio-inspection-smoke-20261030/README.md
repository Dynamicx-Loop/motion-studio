# Experiment: derived Studio stage and animated inspection

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-30 / Codex ticket 05.

## Objective and provenance

Inspect verified native artifacts through fresh standalone CPU derivatives; no
training or motion solve. Input cohorts are the exact-file native ticket 04
G1 three-frame/two-epoch smoke and primitive pre-solve smoke documented in
[the native experiment](../studio-native-stages-smoke-20261030/README.md).
UMR pin remains `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, unchanged. Source
full-tree SHA-256 snapshots before/after are saved in each derivative report.
Existing completed runs, externals, original viewer and original human helper
remain unchanged. Derivatives copy native state before service initialization.
Licensed weights are read at the exact recorded file/hash, never copied.

## Commands and retained evidence

Run from Motion Studio; fresh destinations are required:

```sh
python3 -B scripts/smoke_studio_inspection.py \
  --source /data/workspace/motion_studio/outputs/studio-native-smoke-04-06 \
  --output /data/workspace/motion_studio/outputs/studio-inspection-ticket05-g1-05
python3 -B scripts/smoke_studio_inspection.py \
  --source /data/workspace/motion_studio/outputs/studio-native-smoke-04-primitive-03 \
  --output /data/workspace/motion_studio/outputs/studio-inspection-ticket05-primitive-01
STUDIO_INSPECTION_SMOKE=/data/workspace/motion_studio/outputs/studio-inspection-ticket05-g1-05 \
  /data/workspace/motion_studio/externals/UMR/.venv/bin/python -B \
  -m unittest discover -s tests -p test_studio_inspection_runtime.py -v
python3 -B scripts/check.py
python3 -B scripts/check.py --tier robot-static \
  --robot-python /data/workspace/motion_studio/externals/UMR/.venv/bin/python
node tests/test_umr_human_cache.cjs
node tests/test_studio_frame_requests.cjs
```

Native Python is the preserved UMR environment: NumPy 1.26.4, MuJoCo 3.3.7,
PyTorch 2.7.1+cu128. Reconstruction explicitly uses CPU and two PyTorch threads;
no CUDA escalation or repeated training is needed. Runtime commands remove
inherited `PYTHONPATH`/`PYTHONHOME`, preserve HOME and set PYTHONNOUSERSITE=1.
Viewer dependencies are the independently preserved MIT Three.js r165 and
OrbitControls; each bundle includes their original bytes, hashes and notice.

`inspection-smoke.json` records exact bundle paths, timings, source hashes and
preservation. Each bundle has `files.json`, `files.html`, `receipts.json`,
`provenance.json`, `preservation.json` and copied `native/` artifacts, including
config/request/command/validation/logs. Failed/exploratory `g1-01` through `-04`
remain local evidence; `-03` also retains browser screenshots and initial timing
measurements. None is full/default numerical quality acceptance.

## Observed results and limits

- G1 final `-05`: sampling 10.92 s, training 5.72 s, binding 4.14 s,
  synchronized moving export 10.83 s. Primitive `-01`: 2.45/2.85/1.00 s.
  These timings include derivative copying/hash checks and are machine-specific.
- G1 numerical native reference tests pass: exact frame IDs/FPS, independent
  MuJoCo rigid binding replay within 5e-7 m, decoded human vertices and face+bary
  slots within 5.1e-5 m. Source FPS remains 90.00090026855469, scale and ground
  use the saved solve. No resampling/interpolation. Exact model-file/hash
  rejection checks pass before writing replay binaries.
- Primitive sampling/training/binding exports work without motion; static
  ownership uses primitive/null mesh names. Native closest-vs-bary discrepancy
  stays separate from displayed source bary replay. No G1-specific ownership
  assumptions were added to the new path.
- Combined lifecycle/inspection pure checks: 26/26 suites pass. Robot-static tier: 3/3 suites pass. New pure
  inspection/HTTP tests: 4/4. JavaScript stale-seek/cancel/missing-chunk/retry,
  exact chunk boundaries, invalid timelines and cache bounds pass; original
  cache test remains unchanged. Analytic rigid rotation/translation and
  quantization checks cover both sides of the 64-frame boundary.
- Browser: loopback Studio selected all stage tabs, exact frame 1/2, source
  filtering, paired ownership, display centering and reference pose. The pose
  preparation canvas is hidden in inspection tabs, including after its async
  load. Independent static HTTP serving loaded local vendor/resources only,
  with no UMR runtime. Front/rear/side, meshes and slot controls are retained.
  The saved bundle remains readable when a Studio service is configured with
  nonexistent runtime/model locations. A missing favicon in the first browser
  export was corrected in the new template.

The native smoke has only three source frames, so native multi-chunk/full-clip
comparison remains ticket 07. Analytic encoding and JS boundary checks establish
the format/race contract; they do not substitute for that required full-clip
acceptance. No contact, collision, dynamic feasibility or learned-quality claim.

## Combined lifecycle validation

After merging ticket 06, fresh copied state at
`outputs/studio-inspection-ticket05-revisions-01/` saved filter-only revision
r0005 and exported its inherited binding while all registered artifact paths
resolved to authenticated r0004. `revision-inspection.json` records exact paths.
The old r0004 motion was independently exported from verified bundle copies,
selected across refresh, and rendered in the actual loopback browser. Motion and
retargeting show stale in r0005; old r0004 remains available. The browser stopped
at exact frame 2 with looping off, rendered the inherited binding with correct
ownership, and had no console warnings/errors. Measured inspection document
completion was 1285.1 ms and a cached exact-frame step was 7.1 ms on this machine;
these are one observation, not playback throughput guarantees. The earlier UI
HTTP binding-build action completed in 5548.6 ms and exposed its fresh directory.
The combined screenshot is `browser-inherited-binding.png` in that evidence root.
