# Motion Studio sample data

Local examples for inspection and experiments, modeled on UMR's `sample_data/`.
The UMR files were copied unchanged from revision
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`. FZMotion adds an original Wendy
motion and its session T-pose from the shared local dataset, together with a
derived fixed-shape SMPL-X version of the full motion. Original payloads remain
unchanged; the conversion preserves timing without trimming or resampling.

| Directory | Local contents |
| --- | --- |
| `adapt/` | SMPL-X body and racket motion, trajectory and T-poses |
| `bones-seed/` | Three uniform BVHs, shared fit, rig USD and local SOMA-X link |
| `grail/` | G1 SMPL-X overlay, slope sequence and scene assets |
| `hiphi/` | Getting-up BVH, converted SMPL-X motion and metadata |
| `humanoid_character/` | MimicKit humanoid spinkick motion |
| `lafan1_smplx/` | Converted `dance1_subject2.npz` |
| `nr/` | Skinned FBX character, reference skeleton and motion BVH |
| `omnicontact/` | Converted SMPL-X interaction motion and object assets |
| `omomo/` | Upstream guide only; dataset not supplied |
| `fzmotion/` | Wendy victory BVH, T-pose, fitted SMPL-X motion and provenance |

This is 77 source and derived files, about 73 MiB. The manifest records each
source-relative path, byte count and SHA-256. The UMR selection includes every
Git-tracked file under its `sample_data/`, plus its license. The upstream untracked
`soma_assets` symlink is excluded from the UMR copy. Shared model and calibration
locations now live under `assets/human_models/`
and `assets/calibrations/`. UMR discovery is provided by run-local preparation in the owned sample runner.
The old sample-facing asset aliases are retired. Guides and the manifest are tracked;
motion payloads, conversion sidecars and FZMotion source metadata are ignored by Git.

## Restore and verify

From the Motion Studio root:

```sh
python3 scripts/sample_data.py populate
python3 scripts/sample_data.py check
```

Population uses the existing `externals/UMR` and `/data/motions` sources; it
does not download or install anything. For another workspace or data location:

```sh
python3 scripts/sample_data.py populate --source-workspace /path/to/motion_studio --motions-root /path/to/motions
```

Matching existing files are retained. Changed files are reported and never
overwritten; missing or changed sources fail visibly. Successful entries may be
restored even if other entries fail. `check` needs the samples, manifests and
linked local SOMA-X model and calibration bundles.
`assets/local-manifest.json` owns shared model/calibration hashes and canonical
link targets. This sample manifest describes motion payloads and upstream guides.
`populate` restores missing links but never replaces an occupied path.
Additional local files are outside this manifest's verification scope.

## Use and terms

Per-dataset READMEs, except FZMotion's, are unchanged upstream adapter guides.
Their commands and relative links describe the **UMR checkout**, not this root.
Use explicit absolute data paths when configuring an owned Motion Studio
experiment, and write results under a fresh `outputs/` path. This collection does
not change application defaults or establish new adapter support. Required model
weights, character definitions and independent runtimes remain separate.

UMR's software notice is preserved in [UMR-LICENSE.txt](UMR-LICENSE.txt).
Dataset and model terms apply separately; upstream READMEs retain their source
attributions and terms. GRAIL is marked CC BY-NC 4.0 and the LAFAN1 guide marks
CC BY-NC-ND 4.0. BONES-SEED samples are local gated data; OMOMO payloads are absent. Keep this collection
local; copying bundled files here does not grant additional redistribution rights.
FZMotion is proprietary and must remain local. Source availability and checksum
verification do not establish retargeting quality or runtime compatibility.
