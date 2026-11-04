# Motion Studio assets

This directory holds bundled assets and local references to shared human assets.
`robots/astro_p2/` contains the built-in default Astro P2 model and its meshes,
source notices, SHA-256 manifest and owned Studio import derivative.

`menagerie_x` remains the source of Astro changes. Updates are explicit snapshots
of a reviewed source revision; importing or viewing the built-in uses this local
copy and never fetches or modifies another repository. New managed assets and
generated results still belong to the selected Studio state or `outputs/`.

See the [Astro snapshot](robots/astro_p2/README.md) for provenance, licenses,
the update command and validation scope. Historical definitions under `robots/`
retain their original pins and are separate from this current application asset.

## Shared human models and calibration

`human_models/soma-x/` exposes the existing original SOMA-X assets
and UMR compatibility overlay. `calibrations/bones-seed/` exposes the shared
uniform fit, reference rig and notices. Dataset calibration stays separate from
the general body model. These payload directories are local, Git-ignored links
into `/data/motions`; only guides and `local-manifest.json` are tracked here.
There is no model-weight copy or automatic download.

Active code uses these owned asset paths. The UMR sample runner prepares its
required discovery layout inside fresh runs; the old sample aliases are retired.
From the workspace root, `python3 scripts/sample_data.py populate` restores
missing links and samples, and `check` verifies payload hashes and link targets.
Use `--motions-root` when canonical storage lives elsewhere. Occupied paths and
changed bytes are reported rather than replaced. Model and dataset terms remain
separate; local availability does not grant redistribution rights.
