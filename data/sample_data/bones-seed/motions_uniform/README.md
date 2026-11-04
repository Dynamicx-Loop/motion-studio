# Local BONES-SEED examples

Three original uniform BVHs are available in `bvh/`:

- `walk_forward_amateur_003__A001.bvh`
- `jump_and_land_light_003__A001.bvh`
- `looking_in_the_mirror_amateur_001__A001_M.bvh`

They were copied without conversion, trimming or resampling from
`/data/motions/datasets/bones-seed/raw/uniform/210531/`. The parent collection's
manifest records exact source paths and SHA-256 checksums. Joint names, hierarchy,
Euler channel order and per-file frame times remain as supplied. Dataset-specific
units and axes have not been independently verified.

These gated dataset files stay local and Git-ignored; the upstream dataset terms
prohibit redistribution. No download or new license acceptance was performed.

Shared calibration and SOMA-X assets are now installed under `assets/`. See
[local calibration setup](../../../../assets/calibrations/bones-seed/README.md)
for provenance and run-local UMR preparation. The old `shapes` and `soma_assets`
aliases in this sample directory have been retired. Axxx names are retained, but
these clips come from the **uniform** source directory and must not be treated
as actor-proportional motion on the basis of their filenames.
