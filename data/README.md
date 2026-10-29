# Local data

The shared local data root is `/data/motions`. See its
[directory convention and migration record](/data/motions/README.md).
Shared human-model assets live in `human_models/<model>/<release-or-revision>/`;
datasets live in `datasets/<source>/{raw,calibration,derived}/`.

Store or link experiment inputs here when useful; contents are ignored by the
root repository. Record source, license, and checksums in experiment notes.
Configure each external project to use canonical data paths, or provide its
required layout through local symlinks. Keep upstream environments independent.

The temporary legacy aliases under `/data/motions` have been removed. Historical
run records keep their original paths and hashes; archive readers resolve moved
model filenames through `scripts/motion_data_paths.py` and the saved move map.
