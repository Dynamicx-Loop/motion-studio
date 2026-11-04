# Local SOMA-X model assets

Shared model revision: `f81a01796f652260ff930d5318d6c6b845a505ed`.

Motion Studio exposes one selected revision directly under `soma-x/`. The exact
upstream commit and file hashes live in `assets/local-manifest.json`; a revision
folder is unnecessary in this workspace layout. Canonical storage paths retain
their original names for compatibility with existing runs.

```text
assets/        -> /data/motions/human_models/soma-x/f81a01796f65/assets
overlays/umr/  -> /data/motions/human_models/soma-x/f81a01796f65/overlays/umr
```

`assets/` contains the unchanged official downloads. `overlays/umr/` is the
existing compatibility bundle used by pinned UMR; its `LOCAL_MODIFICATIONS.md`
records the derived neutral NPZ with public bind/T-pose rig arrays. Its other
files link back to the original assets. No weights were moved or duplicated.

These are shared body-model assets, independent of any sample motion or
dataset-specific body fit. BONES-SEED uniform calibration is exposed separately
under `assets/calibrations/bones-seed/`.

The workspace's `assets/local-manifest.json` records both source directories,
model revision and file hashes. `python3 scripts/sample_data.py populate`
recreates the local links; `check` verifies them. `--motions-root` can select a
different canonical data root. Payload links are Git-ignored; this guide and
manifest are tracked. Source licenses and notices remain alongside the assets.
