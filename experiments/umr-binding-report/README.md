# UMR canonical Astro evidence report

Current snapshot:2026-10-23,v4. The report leads with one frozen Astro Dex3-1 asset
at `d2070956558ffbf9226dcf74017d40740724d8d8`, four fresh static trainings,
eight candidate calibration branches and eight fresh offline HiPHI motion solves.
Four G1 static slot controls are verified reuses; their bindings/metrics and all
G1 motions are recomputed. The current model XML SHA-256 is
`c688a4177a1ff5ba07764f9e310bb62c33d24a47b193259922a55b6c5fe88c66`.
Historical variants/results and retired holds are grouped in a labeled disclosure.

There are36 numerical source/robot/center/variant arms,1332 verified segment rows
(740historical+592current),20unique English figures shared by EN/中,and current
raw,candidate and synchronized-motion inspectors. All six anatomical figure rows
remain present, including shoulders/clavicles and hips/pelvis. The previous v3
report/source is archived at `outputs/umr-binding-report/history/pre-canonical-v3/`.

The builder reads completed results only. It never trains,calibrates or solves
motion. New actual outputs support the current conclusions: raw static/motion
results reproduce prior visual-surface measurements; the wrist candidate improves
static hand membership but worsens Astro worst visual floor penetration,
37.05→56.71mm for bbox50 and28.14→30.76mm for spine1. Raw is the default.
SOMA-X model auto-detection links work in both UMR checkouts; BONES-SEED motion,
actor-fit and dataset rig inputs remain absent, so no SOMA motion is claimed.

## Build and view

From `/data/workspace/motion_studio`:

```sh
python3 experiments/umr-binding-report/plot_canonical.py  # current saved six-row grids
python3 experiments/astro-canonical-wrist-v1/plot.py  # current saved closeups
python3 experiments/umr-binding-report/build_report.py
python3 experiments/umr-binding-report/verify_report.py
python3 -m http.server 8770 --bind 127.0.0.1 --directory outputs/umr-binding-report
```

Open `http://127.0.0.1:8770/` or the generated
`/data/workspace/motion_studio/outputs/umr-binding-report/index.html`.
The main HTML embeds its CSS, JavaScript, summary data and figures. Narrative,
figures and numerical exploration work without a server or internet. The static
3D inspectors require HTTP and their existing Three.js CDN dependency. Motion
playback bundles its Three.js dependency locally and also requires HTTP. The
report bundles copies of completed inspectors; it never depends on their old
servers remaining alive. Existing ports 8766–8769 and original files are untouched.
No model weights or original motion archives are copied into the report. The
local motion inspector includes derived processed source vertices and robot
transforms for synchronized playback, with their input hashes and conventions. The inspector
bundle contains derived human/robot geometry and remains local, subject to the
original asset terms; this report does not establish redistribution rights.

## Contents and extension contract

- `report.html`: authored synthesis and claim-level evidence links.
- `report.css`: screen and print layout.
- `report.js`: centering chart, segment explorer, figure switch, lazy inspector and
  state-preserving EN/中 toggle. `?lang=en` or `?lang=zh` overrides the optional
  saved language preference. The active document language and accessible toggle
  label update in place; controls, open disclosures and the section/hash survive.
- `zh.json`: authored Simplified Chinese translations, embedded offline. Source
  records and the internal inspector interface remain original English and are
  disclosed as such. Existing figure labels may retain their original language.
- `plot_report.py`: reproducible six-row actual-triangle grids, with explicit
  head/neck, shoulder/clavicle, torso, hips/pelvis, thigh and forearm rows. Uses
  system NumPy/Matplotlib; no body models loaded. Each figure has one English
  asset shared by both report languages, including all added rows. Source grids place the two human references together,
  then the two Astro bindings, then the two G1 bindings. A focused SMPL-X pair
  shows illustrative Astro bbox50 / G1 spine1 configurations; a companion grid
  retains both matched-centering pairs. The selection is region-specific, not an
  overall ranking. G1 remains the current comparison control.
- `outputs/umr-binding-report/figures/provenance.json`: all derivative figure
  inputs/output hashes and per-arm source-mask counts verified against saved
  results. Latest grids use common18; older grids use native19.
- `build_report.py`: reads completed results, validates totals, generates tables,
  embeds figures, snapshots textual records and copies inspection artifacts.
- `catalog.json`: completed experiment inventory and evidence/inspector sources.
- Generated `manifest.json`: SHA-256 provenance of every input used and copied,
  including report source files; HTML/output hashes are recorded separately.
- `localization.py`: authored-text and accessibility translation coverage guard.
- `verify_report.py`: checks all local links, unique shared image payloads, offline
  core dependencies and all 1332 segment metric rows (740 historical + 592 current) against the saved experiment record.
- Generated `build-validation.json`: record of report assembly checks.

To extend, add a completed record to `catalog.json`, update the authored synthesis
and add a clearly named comparison adapter if its schema differs. Keep cohorts,
label definitions, denominators and control differences explicit. Never silently
pool distinct seeds, sources, surfaces, center rules or projection policies.
The build intentionally fails on missing evidence, incomplete region counts,
nonfinite summary metrics or untranslated authored report text. It does not call experiment scripts, GPU code or UMR.

Source experiments and full reproduction instructions are snapshotted under
`records/experiments/` in the output bundle. The report links their original
commands for traceability, not as an instruction to run them now. Historical images remain unchanged. Expanded actual-triangle renders are
report-local derivatives, using unchanged saved coordinates, selected triangles
and pairings. New charts summarize saved measurements only. No classification,
correction, training, retargeting or rollout is performed.

Validation performed for this report is recorded in `validation.json` after browser
review. This record must distinguish report checks from historical experiment checks.

## Historical v2 hand-variant extension

The new first section at `?lang=en#hands` adds four completed static runs from
`experiments/astro-hands-correspondence`, three English figures shared by both
languages, and the independent fixed-head research note. `hands_report.py` adapts
new data without replacing the original eight-arm arrays; old Astro selector
labels explicitly say no hand meshes. `hands-section.html` contains the bilingual
extension; all its authored text passes the same translation guard. The new
inspector is bundled under `inspectors/hands/`.

The previous report and source files are preserved under local ignored
`outputs/umr-binding-report/history/pre-hands-v1/` with hashes. Historical experiment
files, source datasets and all old figures remain unchanged. Figure provenance
for the new three images is separate in the new experiment; the original seven-
derivative guard is retained. The final report has 14 unique English images,
12 source/target/center arms, and 444 verified numerical rows. Both old and new
source labels/metrics remain accessible; G1 is reused as the control.

## Historical v3 static wrist/palm calibration extension

The focused first section at `?lang=en#wrist-correction` records one completed
label-independent static calibration with unchanged raw Astro/G1 controls. Eight
primary derivatives and k16/64 sensitivity reuse all datasets/checkpoints.
`correction_report.py` and `correction-section.html` add before/after physical
hand counts, actual-hand coverage, displacement, forearm spill and surface-fit
tradeoffs. One matched English closeup figure is shared by both languages.
The hand-mesh improvement is explicitly not an adopted universal repair.

The v2 report/source snapshot is `outputs/umr-binding-report/history/pre-wrist-correction-v2/`.
The v3 bundle has 20 arms, 740 verified rows and 15 unique embedded images; the
original 444 rows are unchanged. Calibrated arms are clearly labeled; the new
inspector is under `inspectors/correction/`. The report builder itself performs no
calibration, training or motion. Final checks are in `validation.json`.

## Historical open-hand canonical extension (v4)

- `canonical_report.py` adapts the completed canonical raw/calibrated/motion
  records without replacing historical arrays. Current arms precede clearly
  prefixed historical arms; the explorer defaults to raw Astro bbox50.
- `canonical-section.html` and `canonical-zh.json` provide the current bilingual
  narrative,tables,metric tradeoff,model pin and evidence links. Historical holds
  are explicitly retired; old text stays available for provenance.
- `plot_canonical.py` reuses the six-row actual-triangle renderer for fresh saved
  raw bindings,with adjacent source references and matched-centering companions.
  `canonical-figure-provenance.json` hashes all inputs/outputs and source masks.
- `inspectors/canonical/`, `inspectors/canonical-correction/` and
  `inspectors/canonical-motion/` show the identical Astro model snapshot. Motion
  offers selected/matched centers and raw/k32 candidate,defaulting to raw.
- The state-preserving EN/中 toggle retains selections,disclosures,hash and the
  loaded inspector. Both languages use the same numeric data and image payloads.
- `verify_report.py` checks local links,20unique images,1332exact segment rows,
  the single current Astro hash and8fresh motion records. Browser checks cover
  language equality,state,figure enlargement,inspectors and synchronized playback.

To reproduce computation,follow the three current experiment READMEs. The report
server on127.0.0.1:8770 remains in place while the bundle updates. Do not run old
`plot_report.py` merely to update current evidence: it rebuilds the historical
figure provenance from its own inputs. The archived historical figures remain
unchanged and keep their own hash guards.

## Current fixed-fist extension (v5)

Current records are `astro-fist-static-v1`, `astro-fist-wrist-v1`, and
`umr-motion-fist-v1`. Four fresh 500-epoch Astro trainings resample the exact
latest named fist pose; all 14 finger coordinates are held by equal named-joint
QP bounds through initialization, solve and filtering. Eight motion solves are
fresh; G1 static slots retain exact historical provenance. Instrumentation stores
pre-LQR arrays without changing upstream code or optimization.

`fixed-fist-validation.json` checks all frames, all 14 preset/keyframe/config
values, 1837 QP calls per Astro arm, 25718 finger-bound checks, initialization
and both exported/raw arrays. Max deviation is below 1e-7 rad.

The full v4 report and sources are immutable at `history/pre-fist-v4/`, with
archive hashes. Its 16 arms remain in the numerical explorer under historical
open-hand v4 labels. There are now 52 arms and 1924 segment rows, including
1332 historical rows and 592 current rows. Twenty English images remain shared
between EN and Chinese. Current inspectors use actual fixed-fist geometry.

Open→fist changes surface geometry and finger freedom simultaneously; the report
does not infer an isolated pose effect. All-hinge smoothness includes constant
fingers. The candidate remains experimental. BONES-SEED motion/shape/rig is still
unavailable. No hardware execution or new collision-primitive experiments.
