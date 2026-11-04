# 08 — Official-style asset library and quick source previews

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Context

The completed local application needs the official Studio's immediately usable
asset experience: real robot cards, drag into the viewport, custom file drops and
sample motions. Existing native computation, integrity and preserved output
contracts remain authoritative.

## Scope and acceptance criteria

- Four locally bundled official robots (G1, K1, PiPlus, T800), complete verified
  closures and native named T-poses; accessible use buttons and drag/drop.
- Ground plane follows actual displayed geometry bounds without changing saved
  physical qpos or calibration. Root/joint editing remains available.
- Browser uploads support MJCF plus dependent files/folder or ZIP, bounded and
  confined, preserving originals; custom import validation stays strict.
- Local real sample motions include a visibly labeled short quick-test derivation
  with recorded source hash, retained exact FPS/frame interval, full source option,
  and source motion playback before training. No simulated results presented as
  solved robot motion.
- Official-style asset/sidebar/pipeline/viewport/property layout; old viewer
  modules, historical outputs and pinned externals stay intact.
- Public behavior tests, runtime smoke checks and browser acceptance; record limits.

## Validation

Focused Studio Python suites, native-runtime import/pose checks for all four,
JavaScript syntax checks and browser workflow validation.

## Comments

2026-10-30: Claimed for the user-requested follow-up. Official REA evidence is
retained at `outputs/studio-asset-library-research/README.md`. PiPlus and T800
require owned rebasing of verified sibling asset paths into a closed import;
original source XML/dependencies and conversion provenance are preserved.

## Implementation result

- Added owned pinned-UMR example catalog with actual G1/K1/PiPlus/T800 compiled
  native T-poses and local rendered model thumbnails. Complete sources are
  reverified against the pinned commit before/after import. PiPlus/T800 sibling
  dependencies are rebased in owned temporary copies with original bytes and
  hash-bound derivation records retained. No upstream files or pins changed.
- Added accessible asset cards plus real drag/drop, forwarding drops from the
  same-origin inspection iframe. Completed/historical selections produce a fresh
  asset-study draft. Library switching, pending upload chooser and current source
  previews have explicit state/lifecycle handling.
- Added bounded XML+dependency, folder and ZIP uploads with an explicit main-XML
  chooser and root-derivation checkbox. Upload-only rebasing accepts sibling paths
  confined to the complete selected bundle, including main-relative includes.
  Traversal outside that boundary, duplicate/canonical aliases, archive symlinks,
  invalid XML, cyclic/missing includes and oversized bundles fail explicitly.
  Absolute-path import boundaries remain unchanged.
- Added actual SMPL-X body-joint source previews via independent CPU native
  reconstruction, exact original frames/FPS and neutral hands, with play/pause,
  exact stepping/scrubbing, looping and orbit/zoom. Previews are hash registered,
  reusable without weights after creation, and concurrent same-asset requests
  coalesce into one build. No source preview trains or solves robot motion.
- Added full HiPHI, exact 180-frame / original-FPS quick-test excerpt with recorded
  parent hash/revision/interval and no resampling, plus full ADAPT Y-up person
  motion (interaction objects excluded). Original source NPZ is downloadable.
- Updated official-style light library/scene/properties layout, collapsed logs,
  default final-pose framing across viewport aspects and display floor at actual
  mesh lower bound. Saved qpos/calibration never changes for display grounding.

## Validation so far

- `python3 -B scripts/check.py --tier pure`: **29/29 selected suites passed**.
- `python3 -B -m unittest discover -s tests -p test_studio_assets_runtime.py -v`:
  four runtime cases passed, covering all four actual compiled robots, named
  pose limits/preview, real HTTP browser-byte imports, uploaded sibling mesh+
  include closure and escape rejection, exact source trim/FPS/provenance.
- `test_studio_assets.py`: canonical traversal/alias/duplicate/symlink refusal.
- `test_studio_source_preview.py`: six public contract cases passed, including
  eight concurrent builds across Studio instances, cache tamper/confinement and
  saved viewing without weights. Opt-in `test_studio_source_preview_runtime.py`
  passed actual two-frame SMPL-X reconstruction with translation atol `3e-7 m`.
- Modified JavaScript modules pass `node --check`; `git diff --check` clean.
- An indiscriminate Studio unittest discovery under the system interpreter had two
  import errors from existing opt-in MuJoCo suites. Owning tier selection above
  passed; the independent native runtime exercises passed separately.

Browser acceptance and a short native quick-test run are being recorded by the
orchestrator. Keep this ticket claimed until that evidence and preservation check
are attached. This change does not claim full-mesh source rendering, texture
rendering, interaction objects, dynamic feasibility or a new full-quality cohort.


## Answer

Resolved after implementation, independent correctness review and parent browser/
native acceptance. The [experiment record](../../../outputs/artifact-archives/experiment-reset-20261104/experiments/archive/studio-asset-library-20261030/README.md)
records source/runtime boundaries, exact short-clip semantics and checks. Browser
evidence and native receipt are retained in
[`outputs/studio-asset-library-research`](../../../outputs/studio-asset-library-research/README.md).
Actual K1 drag/drop, G1 new-draft behavior, ZIP import, source exact stepping,
T800 full T-pose/display ground and a fresh 5-epoch/180-frame all-stage native run
passed. Console had no errors/warnings. Original preservation passed all 288 files;
no pinned external or original viewer/result changed. This is workflow smoke,
not a new full-quality motion cohort.
