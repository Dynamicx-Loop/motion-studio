# BONES-SEED uniform calibration

Motion Studio exposes shared dataset calibration here:

```text
assets/calibrations/bones-seed/
  soma_uniform_fit_mhr_params/ -> /data/motions/datasets/bones-seed/calibration/soma_uniform_fit_mhr_params
  soma_base_rig/              -> /data/motions/datasets/bones-seed/calibration/soma_base_rig
  notices/                    -> /data/motions/datasets/bones-seed/calibration/notices
```

The shared uniform fit came from the existing Kimodo checkout at
`/data/workspace/notAnyrobot/kimodo`, revision
`3b98f78344cb6c1580d7e5cb95aa2ea4320bafe9`. SHA-256 is
`61f0b96c8386a19d44823faf4399816642b7e20691ed5b398c7402921090096e`.
The earlier investigation in
`experiments/umr-baseline-g1-somax-20261102/records/uniform-fit-investigation.json`
records byte equality with NVIDIA Kimodo's official shared BONES-SEED fit at
upstream revision `e1c219c99b4b94ba48be1fb6a1cbc64ecee4c954`. It was not compared
with a newly downloaded BONES-SEED archive.

The reference rig USD came from the existing soma-retargeter checkout at
`/data/workspace/github/soma-x/soma-retargeter`, revision
`b3ef2708d84bfd1314ddb52d0db6c9c211df1f57`. It is retained for reference, but
UMR's pinned fitted uniform route does not read this standalone USD or the absent
`soma_base_skel_minimal.bvh`. The shared fit is the required dataset-specific
input. Proportional actor fits are not needed for the current uniform clips.

`assets/local-manifest.json` records calibration hashes and local link targets.
Notices remain under `notices/`; dataset terms apply separately. Canonical
storage and migration metadata remain intact. The general SOMA-X model lives
separately at `assets/human_models/soma-x/`, with its exact upstream revision and
existing UMR overlay derivation recorded in metadata.

## Use with UMR

Active code should select this calibration directory and
`assets/human_models/soma-x/overlays/umr` directly. The old sample-directory
`shapes` and `soma_assets` aliases have been retired.

Pinned UMR discovers a BONES-SEED fit through a literal `motions_uniform`
ancestor with sibling `shapes/` and `soma_assets/` directories. The owned sample
verification runner now constructs that layout inside each fresh run under
`input/bones-seed/`, copying the source BVH and linking to the shared assets.
This requirement is confined to runtime preparation. Original sample directories
contain motions and guides only.

Use the runner in `experiments/sample-data-umr-g1-20261102/run.py` with a fresh
output path for full execution. It explicitly rejects generic fallback by
asserting `soma_bvh_boneseed_uniform`, `soma_uniform` and the shared-fit hash before
training. Passing a raw sample BVH directly to the native loader without this
layout can select the generic neutral body instead.

`python3 scripts/sample_data.py populate` restores samples and shared asset links;
`check` verifies them. It does not recreate the retired sample aliases. No asset
bytes were changed or downloaded. Historical run snapshots and their recorded
paths remain intact.
