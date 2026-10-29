# Dependency roles and historical recovery

Inspected 2026-10-29. The [manifest](../externals/manifest.json) pins fresh source
checkouts. The [role record](../configs/dependency-roles.json) supplements it with
local recovery coverage; [UMR experiment dependencies](../configs/umr/experiment-dependencies.json)
retain historical cohort requirements unchanged. All paths below are local inputs.

| Checkout | Role and state | Runtime boundary |
| --- | --- | --- |
| `externals/UMR` | Active official reproduction; pinned `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; one untracked data link | Existing `.venv`; official bundled assets and original cohorts remain unchanged |
| `externals/hiphi2smplx` | Active conversion; clean detached `65e51315ebbc82b2f0ff8e35a94565beb1b345e1` | Python >=3.10; NumPy, SciPy, Mink, MuJoCo, qpsolvers, DAQP, Torch, h5py, smplx, tqdm declared upstream; registration itself performed no install/runtime test |
| `externals/ProtoMotions` | Clean at manifest pin; source only | LFS smudging disabled; assets, environment and jobs unverified |
| `externals/pyroki` | Clean at manifest pin; source only | Independent environment unverified |
| `externals/human-humanoid-tools` | At manifest pin with eight status entries | Existing Astro changes, assets, venv and compatibility links preserved |
| `externals/UMR-baseline-v1` | Clean linked UMR worktree on `motion-studio/astro-baseline-v1`, HEAD `ecf0e11b7ea1880f43a458cce35ba9b086f31a28` | Historical static cohort; shared original UMR venv; no default bootstrap |
| `externals/UMR-astro-surface-experiment` | Independent clone, branch `main`, official base/HEAD `d1cdaedaf67a827198da71c5fa831f48b2e51f91`; six modified tracked scripts, two untracked source files and one data link | Historical geometry cohorts; no default bootstrap or fresh numerical run |
| `/data/workspace/notAnyrobot/menagerie_x` | Asset source HEAD `d2070956558ffbf9226dcf74017d40740724d8d8`, local generated/untracked work preserved | Remains outside bootstrap; robot selection supplies this explicit local source-root locator and validates selected bytes |

hiphi2smplx origin and upstream are both
`https://github.com/noitom-robotics/hiphi2smplx.git`, confirmed from local remote
metadata. Its local README, `pyproject.toml` and MIT LICENSE were inspected at the
pin. The CLI supports HiPHI's 22 body joints; face/eye/finger fitting is absent.
SMPL-X models and beta-fit mean/pose priors are separately licensed inputs; the
upstream README describes their acquisition. Registration does not fetch them,
create an environment or establish conversion readiness.

The old hhtools location `/data/workspace/rplab/human-humanoid-tools` retains its
protected Git metadata and compatibility aliases. Existing absolute environment
paths and linked worktrees still rely on it. Follow [migration notes](migration.md):
use the externals checkout canonically and preserve both metadata/aliases; no path
or environment was moved during this ticket.

## Sealed evidence and source coverage

The [initial inventory](../outputs/preservation/layout-and-robot-assets-20261029-01/inventory.json)
SHA-256 is `32c9f10f145814668c2b19caf0555e3aa2c7f6ad416252c542be68f357eb30d7`.
Its recovery payloads, exact status, Git/worktree relationships, ignored locations,
compatibility aliases and exclusions remain immutable. See [receipt boundaries](preservation.md).

The new local [recovery comparison](../outputs/dependency-roles/layout-and-robot-assets-20261029-03-verified/report.json)
has SHA-256 `4aa23956354993217d0b869ebdf25307c9df644123f99f851139de88a09dd809`.
It records independently checked payload hashes and every recovered source hash.
This is an additive receipt; the initial failed scratch validation attempt at the
sibling `layout-and-robot-assets-20261029-03` directory is incomplete and unused.

The [historical surface patch](../experiments/astro-surface-geometry/umr-surface-geometry.patch)
SHA-256 `e2cc109b3aa8125034391fde0ae2f66a02ea660a6900ce727351ea1579ca000a`
was applied to the official HEAD blobs in disposable scratch space. It reproduced
all six modified tracked scripts plus `scripts/primitive_surface.py` and
`tests/test_surface_geometry.py` exactly. These also matched the initial inventory
tracked patch plus untracked archive and the live files. There is **no current
source delta**; the receipt retains an intentionally empty `saved-to-current.patch`.
`sample_data/bones-seed/soma_assets` is an unarchived data symlink, located in the
inventory; environments and ignored generated files remain in place.

For the baseline worktree, `baseline-from-official.patch` preserves all 16 committed
additions relative to the official base. Scratch recovery matched all 16 HEAD
blobs. The branch includes commits `e045058beccefe5b23985c451e264894395bc95a`
and `ecf0e11b7ea1880f43a458cce35ba9b086f31a28`; its Git directory remains under
`externals/UMR/.git/worktrees/UMR-baseline-v1`. The patch supplements existing
Git history; it does not rewrite it or change the historical cohort.

## Reconstruction and inspection

Reconstruct only inside a fresh disposable directory. Given an existing source
object repository and a fresh scratch directory, populate changed tracked paths
listed in the role record using `git show <base>:<path>`. For the experimental
clone, apply either `historical-surface.patch`, or `tracked.patch` followed by
`untracked-source.tar` from the verified receipt. The latter archive contains only
the two source paths named above. Do not apply both alternatives. Compare each
recovered file's SHA-256 with `report.json`. No live checkout is a recovery target.

For example, after populating the six base files in fresh scratch space:

```sh
git apply /data/workspace/motion_studio/outputs/dependency-roles/layout-and-robot-assets-20261029-03-verified/historical-surface.patch
```

The baseline additions can be recovered in an empty scratch directory with:

```sh
git apply /data/workspace/motion_studio/outputs/dependency-roles/layout-and-robot-assets-20261029-03-verified/baseline-from-official.patch
```

Inspect canonical sources from an owned worktree without canonical writes:

```sh
python3 scripts/workspace.py list
python3 scripts/workspace.py check --source-workspace /data/workspace/motion_studio
```

This uses the executing worktree's manifest and reports pin drift and local edits.
Only list/check accept `--source-workspace`; bootstrap continues to operate locally
and retains resolved-child path validation and non-overwrite behavior. A fresh
bootstrap selects hiphi2smplx's exact pin; existing directories remain untouched.

Validation used local fixture repositories with no network to check pin selection,
dirty/untracked preservation, outside-link/traversal rejection and read-only source
inspection. These structural checks do not establish environment readiness,
numerical equivalence, robot dynamics or hardware safety. Git object databases,
licensed models, ignored assets and excluded sensitive configuration are not a
complete machine backup; exact recovery exclusions remain in the inventory.

## Later owned validation and selection

The table records ticket 03 registration evidence. Subsequently the
[Wendy adapter](wendy-conversion-adapter.md) ran a bounded three-frame CPU excerpt
with exact saved-field parity; this does not establish a full conversion or GPU
workflow. [Canonical preparation](umr-canonical-preparation.md) later copied and
CPU-compiled explicitly selected G1/Astro MJCF cohorts; all remain prepared-only.
Use [robot definitions](../robots/README.md) for source-key locators and separate
representation findings, [checks](checks.md) for exact runtime prerequisites, and
the [closeout](../experiments/layout-and-robot-assets-evidence/ticket13/README.md)
for bounded cross-workflow validation. Original recovery claims above retain their
dated scope; no upstream pin, environment or historical baseline was advanced.
