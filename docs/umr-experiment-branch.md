# Motion Studio UMR experiment branch

The persistent project branch is **`experiments/umr-astro`** in
**`/data/workspace/motion_studio`**. Open that folder in VS Code and select the
Motion Studio repository in Source Control. The nested UMR repositories are
dependencies with separate Git histories.

The root was initially unborn. A selective initial commit on its existing
`master` branch captured 14 existing workspace instruction and dependency files.
The experiment branch then captures the approved guideline, versioned study,
root-owned experiment code, frozen configuration/provenance and small reports.
Other pre-existing files remain in place and untracked unless explicitly selected.

## Repository and artifact boundaries

| Location | Purpose |
| --- | --- |
| Root `experiments/umr-astro` | Project documentation, research protocol, scripts, configuration and small evidence records |
| `externals/UMR` | Official UMR pinned at `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; tracked source unchanged |
| `externals/UMR-baseline-v1` | Preserved execution worktree at `ecf0e11b7ea1880f43a458cce35ba9b086f31a28`, branch `motion-studio/astro-baseline-v1`; a dependency detail |
| `scripts/umr_baseline/` | Root-owned static preparation, bounded execution and evaluation scripts |
| `experiments/umr-astro-baseline-v1/records/static-20261024-01/` | Small frozen record of the completed first static pair |
| `outputs/umr-astro-baseline-v1/static-20261024-01/` | Original local datasets, checkpoints, bindings and frozen assets; excluded from Git |
| Other existing experiment/output directories | Legacy evidence remains untouched and separate |

The [dependency map](../configs/umr/experiment-dependencies.json) records exact
paths, pins and exclusions. The dependency worktree and its historical scripts
remain unchanged. Root scripts are copied from that execution version with only
workspace/path resolution, root-script hashing and a comment correction; see
[adaptation record](../experiments/umr-root-branch-setup/script-adaptation.json).
The earlier execution manifests retain their original paths and hashes.

Root scripts use the existing UMR interpreter. `MOTION_STUDIO_UMR_ROOT` can select
another inspected compatible UMR checkout; its default is `externals/UMR-baseline-v1`.
The venv is shared read-only; outputs and caches require separate fresh paths.
No raw assets, licensed body models, environments or checkpoint binaries are
included in the project commits. A fresh clone alone does not reproduce those
local dependencies, and no remote or push has been configured by this work.

## Current research state

The [guideline](umr-astro-baseline-proposal.md) was approved after its original
review draft. This document records that approval and the corrected repository
scope without changing the frozen proposal bytes. The
[paper study v1](../references/umr-paper-study-v1.md) remains a literature reference.

The [first static pair](../experiments/umr-astro-baseline-v1/README.md) completed
two fresh official-default trainings and binding diagnostics. It is a baseline
candidate for review. Further experiments are paused. Motion optimization,
controlled ablations and dynamics have not begun; matched SOMA-X motion/actor/rig
inputs remain missing. Static binding fractions are not motion scores.

All earlier references to the Motion Studio root being unborn describe its state
at those historical observations. They do not describe the current branch.
