# BONES-SEED sample calibration from existing local assets

Date: 2026-11-02. Cohort: source preparation and CPU surface reconstruction only.
Objective: make all three owned uniform BVH samples discover their shared fitted
body in pinned UMR, without accepting the generic-neutral fallback. No download,
package installation, upstream source edit or new terms acceptance was performed.

## Inputs and preservation

The [local setup guide](../../data/sample_data/bones-seed/shapes/README.md) records
the exact original Kimodo fit and soma-retargeter rig paths, revisions, notices,
optional absent reference BVH and existing SOMA-X compatibility overlay. The
[sample manifest](../../data/sample_data/manifest.json) records every copied
file's SHA-256 and ten linked model/notice file hashes. Canonical calibration
copies were added under `/data/motions/datasets/bones-seed/calibration/`; original
source clips, model assets, experiment cohorts and migration metadata are intact.

The uniform fit has SHA-256
`61f0b96c8386a19d44823faf4399816642b7e20691ed5b398c7402921090096e`.
Its Kimodo provenance was verified against upstream in the earlier saved
investigation; no new BONES-SEED download was compared. SOMA-X revision is
`f81a01796f652260ff930d5318d6c6b845a505ed`; the existing derived neutral NPZ is
explicitly documented by its `LOCAL_MODIFICATIONS.md`. Data/model/asset terms
remain separate and payloads stay local and Git-ignored.

## Validation

UMR revision `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, independent interpreter
`externals/UMR/.venv/bin/python`, and `UMR_SOMA_DEVICE=cpu` were used. The probe
imported `externals/UMR/scripts/soma_source.py` and, for each sample:

1. Called `load_soma_bvh_motion`, asserting `soma_bvh_boneseed_uniform`,
   `soma_uniform`, the exact shared-fit path and resolved local model path.
2. Called `soma_template_vertices_joints_faces(sequence=sequence)` and
   `soma_motion_vertices_joints(sequence, [0, T//2, T-1], zero_fingers=True)`.
3. Asserted template vertices `(18056, 3)`, joints `(78, 3)`, faces `(36108, 3)`,
   corresponding three-frame motion shapes, finite geometry, identical ordered
   triangle arrays and equality of BVH/model joint-name sets.

[validation.json](validation.json) records frame counts, FPS, selected frame IDs
and measured outcomes. All three passed. BVH centimeter translation and Euler
degree channels are interpreted by the native loader; reconstructed surfaces are
meters in SOMA's Y-up frame. Source files and timing were not edited or resampled.
The sparse sampled-frame check does not assess every reconstructed motion frame.

The CPU probe emitted Warp's no-CUDA notice, a sparse-tensor beta warning and
trimesh texture aggregation warnings. Numerical geometry assertions passed.
No GPU training, correspondence reuse, robot retargeting, contact or dynamic
evaluation was performed. This is fitted-source readiness, not a new robot result.

Restoration and integrity commands from the Motion Studio root:

```sh
python3 scripts/sample_data.py populate
python3 scripts/sample_data.py check
```

The model bundle remains in place; missing sample links are restored without
overwriting occupied paths. Model-file changes cause verification failure.
