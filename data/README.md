# Local data

The shared local data root is `/data/motions`. See its
[directory convention and migration record](/data/motions/README.md).
Shared human-model assets live in `human_models/<model>/<release-or-revision>/`;
datasets live in `datasets/<source>/{raw,calibration,derived}/`.

The [sample collection](sample_data/README.md) contains local UMR examples and a
FZMotion Wendy clip with its T-pose and fitted SMPL-X motion, plus three local
BONES-SEED motions. Its guides, license notice and checksum
manifest are tracked; motion payloads remain ignored and local. Restore or verify
them with `python3 scripts/sample_data.py populate` or `check`.

Store or link experiment inputs here when useful; other contents are ignored by
the root repository. Record source, license, and checksums in experiment notes.
Configure each external project to use canonical data paths, or provide its
required layout through local symlinks. Keep upstream environments independent.

The temporary legacy aliases under `/data/motions` have been removed. Historical
run records keep their original paths and hashes; archive readers resolve moved
model filenames through `scripts/motion_data_paths.py` and the saved move map.
