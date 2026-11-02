# UMR canonical Astro evidence report

Current snapshot: 2026-10-23, v5. The report uses one frozen Astro Dex3-1
asset at `d2070956558ffbf9226dcf74017d40740724d8d8`, with XML SHA-256
`c688a4177a1ff5ba07764f9e310bb62c33d24a47b193259922a55b6c5fe88c66`.
Four Astro correspondences were freshly trained on the fixed-fist surface; G1
static slots retain their historical provenance. Eight offline HiPHI motion
solves use raw and candidate bindings. All 14 Astro finger coordinates are fixed.
The preceding open-hand v4 cohort remains separately labeled in the report.

The v5 report contains 52 numerical arms and 1,924 segment rows (1,332 historical
and 592 current), with 20 English figures shared by both languages. The wrist
candidate increases static hand membership. In the fixed-fist motion cohort,
worst visual floor penetration decreases from 26.55 to 25.89 mm for bbox50 and
from 22.70 to 17.38 mm for spine1. Substantial penetration remains; raw is the
default. The historical open-hand v4 results instead worsened from 37.05 to
56.71 mm and 28.14 to 30.76 mm, respectively. Neither cohort establishes dynamic
feasibility. BONES-SEED motion, actor fit and dataset rig inputs remain absent.

The builder reads completed results; it does not train, calibrate or solve motion.
The commands below document the captured build and write to fixed historical
paths. Do not run them against retained evidence; a new edition requires fresh,
explicit output paths as described in [offline documentation](../../docs/offline-documentation.md).

## Build and view

From `/data/workspace/motion_studio`:

```sh
python3 experiments/umr-binding-report/plot_canonical.py  # current saved six-row grids
python3 experiments/astro-fist-wrist-v1/plot.py  # v5 saved closeups
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
  core dependencies and segment metric rows against the saved experiment records.
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
  records without replacing historical arrays. At v4, current arms preceded
  historical arms and the explorer defaulted to raw Astro bbox50.
- `canonical-section.html` and `canonical-zh.json` provided that edition’s bilingual
  narrative, tables, metric tradeoff, model pin and evidence links.
  Historical holds were explicitly retired; old text stays available for provenance.
- `plot_canonical.py` reuses the six-row actual-triangle renderer for fresh saved
  raw bindings,with adjacent source references and matched-centering companions.
  `canonical-figure-provenance.json` hashes all inputs/outputs and source masks.
- `inspectors/canonical/`, `inspectors/canonical-correction/` and
  `inspectors/canonical-motion/` show the identical Astro model snapshot. Motion
  offers selected/matched centers and raw/k32 candidate,defaulting to raw.
- The state-preserving EN/中 toggle retains selections,disclosures,hash and the
  loaded inspector. Both languages use the same numeric data and image payloads.
- `verify_report.py` checks local links,20unique images,1332exact segment rows,
  the then-current Astro hash and eight fresh motion records. Browser checks covered
  language equality,state,figure enlargement,inspectors and synchronized playback.

The original v4 build commands and output paths are retained for provenance. Do
not run its writers against retained evidence; `plot_report.py` also rebuilds
historical figure provenance. Archived figures retain their own hash guards.

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
