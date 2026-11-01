# Experiment: local Studio asset-library acceptance

Date / author: 2026-10-30 / Codex, local user-requested follow-up.

## Objective and cohort

Demonstrate immediately usable local robot cards, custom file drops and sample
motion playback/testing, following observed official Studio interaction. This is
a deliberately shortened **workflow smoke** cohort, separate from the immutable
500-epoch/5468-frame G1 acceptance. Measured contracts and visual judgments are
listed separately; no new quality/dynamics result is claimed.

New run `fb8714deee944e41a2c9e6ea5e91fe82`, revision `r0004`, job
`69101dbeeea94e4ea400a870119b761d` used the existing application's managed state
under `outputs/studio-baseline-acceptance-20261030/final-cohort/state`.
The earlier acceptance run `886f5c1ba3814b4eb268a84eeb8f1d1d` stayed `r0004`.

## Provenance and independent runtimes

Native UMR remains pinned at `d1cdaedaf67a827198da71c5fa831f48b2e51f91`,
without upstream patches. Owned source changes live on `codex/local-umr-studio`;
`implementation-sha256.json` records the follow-up source bytes. The complete
native plan/runtime/configuration and dependency hashes are retained in
[quick-run receipt](../../outputs/studio-asset-library-research/quick-run.json).
Independent interpreter: `externals/UMR/.venv/bin/python`; service interpreter:
system `python3` with the existing lazy NumPy motion-import requirement.
Licensed SMPL-X weights remain at the configured local model location, hashed
and never redistributed. Robot, model and dataset terms remain separate.

## Robot selection and representation

All four local pinned official robot closures compile: G1, K1, PiPlus, T800.
Native named T-poses satisfy compiled limits. PiPlus/T800 references to sibling
mesh/texture directories are rebased in owned temporary copies; original bytes,
preset and derivation hashes remain in managed `source/provenance/`. Independent
compilation of their untouched originals and rebased models gives equal geometry
transforms in the named pose at `1e-12` absolute tolerance. No model equivalence,
texture-rendering or dynamics claim follows.

Pose coordinates retain metres, Z-up, root quaternion wxyz and hinge radians.
The visible floor follows actual mesh lower bounds without changing saved root
coordinates or calibration. Browser visual judgment confirmed complete T-poses
and floor placement. K1 was added with an actual browser drag; T800 with its
accessible Add robot button. Custom ZIP upload/import also passed.

## Processing and learned artifacts

The quick clip retains source frames `[0,180)` of bundled HiPHI get-up at
`90.00090026855469` FPS. No scaling, coordinate conversion or resampling occurs;
the original managed NPZ records parent SHA-256, revision, path, full source count
and interval. Full HiPHI and the full ADAPT Y-up person clip remain separate
choices. ADAPT's pinned wrapper explicitly declares Y-up; objects are omitted.

Native smoke used sampling seed 0, **5 training epochs**, LQR, and all selected
180 frames through sampling/training/binding/retargeting. It is not an official
quality setting. Source preview reconstructs actual first-22 SMPL-X body joints
on CPU, neutral hands, exact FPS/frames; it is not a robot solve or full mesh.

## Reproduction

From the workspace root, launch the documented local service and create a fresh
asset-study draft. Add G1, select HiPHI **2s quick test**, verify source stepping,
close its preview, set training epochs to 5, review Run all and launch. Use fresh
managed run/revision identities rather than modifying this cohort. Full server
arguments and browser/REA provenance are in the
[evidence record](../../outputs/studio-asset-library-research/README.md) and
[server record](../../outputs/studio-asset-library-research/server.json).

Focused checks:

```sh
python3 -B scripts/check.py --tier pure
python3 -B -m unittest discover -s tests -p test_studio_assets_runtime.py -v
python3 -B -m unittest discover -s tests -p test_studio_source_preview_runtime.py -v
```

Thumbnail generator: `python3 -B scripts/build_studio_thumbnails.py` (Pillow,
NumPy, local pinned source and independent MuJoCo runtime required).

## Evaluation

- Owning pure tier: 29/29 selected suites passed.
- Four library-runtime cases passed: all four built-ins, actual HTTP byte import,
  sibling mesh/includes with bounded rebase, source trim equality/FPS/provenance,
  and ADAPT Y-up metadata. Upload contract case rejects escaping/noncanonical/
  duplicate names and ZIP symlinks. No external fetch is attempted.
- Six source-preview contract cases passed, including eight concurrent callers
  sharing one build, cache tampering/confinement and saved viewing without weights.
  Independent two-frame native preview translation passed at `3e-7 m` tolerance.
- Modified browser modules passed `node --check`; diff whitespace check passed.
- Browser: actual K1 drag, G1 new-draft behavior from completed selection, ZIP
  import, source frame stepping, full T800 pose/ground and narrow-viewport fitting
  passed. CUA console reported zero errors/warnings; independent REA 1440×900
  screenshot is [local-studio.png](../../outputs/studio-asset-library-research/local-studio.png).
- The 180-frame native smoke completed every stage and published validated output.
- Original preservation verifier passed all 288 files; external states unchanged.

## Observations and next step

Source skeleton playback and native workflow smoke are demonstrated. Full-quality
retraining, expressive hands/face, texture reproduction, interaction objects,
contact/slip/collision metrics and dynamic feasibility were not evaluated here.
The older full-quality cohort retains its separate acceptance evidence. Official
webpage REA behavior research establishes interface observations, not compute
parity with its deployed implementation.
