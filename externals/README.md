# External projects

Each project is an independent Git checkout, not vendored source or a submodule.
The root repository ignores checkout contents and tracks `manifest.json` instead.
This preserves upstream histories and allows different environments and release cycles.

Treat these checkouts as pinned, static dependencies. Motion Studio interfaces,
adapters, and feature development live in the root project. Follow the
[development policy](../docs/workflow.md#development-policy) before adding an
integration or modifying external source.

The manifest records clone URLs, upstream URLs, and the exact baseline commits.
Run `python3 scripts/workspace.py check` from the root to report missing checkouts,
revision drift, or local edits. `bootstrap` only clones missing projects; it never
pulls, resets, installs dependencies, or overwrites existing directories.

To adopt another project, review its license and setup, add a unique path and pinned
commit to the manifest, then bootstrap it and document a representative experiment.
When advancing a revision, review changes and record validation before updating the
manifest. Commit local development inside the external project separately.

Projects with `skip_lfs: true` clone with Git LFS smudging disabled. Their source is
available, but large assets may remain pointer files until explicitly fetched.
ProtoMotions uses this setting; see [setup notes](../docs/protomotions-pyroki.md).

## Active and historical roles

The manifest includes active hiphi2smplx conversion at the inspected commit
`65e51315ebbc82b2f0ff8e35a94565beb1b345e1`. Its MIT license applies to the
code; SMPL-X models and beta-fit priors have separate terms and are not bundled.
Its local README, LICENSE and pyproject.toml were inspected without installation.

The historical UMR baseline worktree and surface experiment clone are archived
under `outputs/artifact-archives/umr-historical-checkouts-20261104/`.
menagerie_x remains at its supplied local path, outside default bootstrap.
See [dependency roles and checkout retirement](../docs/dependency-roles.md#2026-11-04-checkout-retirement) and the
[machine-readable record](../configs/dependency-roles.json) for exact revisions,
recovery hashes, source coverage and validation limits.

From an isolated owned worktree, inspect the actual canonical checkouts against
that worktree's manifest with:

```sh
python3 scripts/workspace.py list
python3 scripts/workspace.py check --source-workspace /data/workspace/motion_studio
```

`--source-workspace` is read-only and available only for list/check. It does not
read the other workspace's manifest or redirect bootstrap. The default resolved
child-path restriction remains: a checkout link escaping externals is rejected.
Bootstrap never installs runtimes, updates an existing checkout or materializes
historical local patches.

## Owned workflow navigation

[Wendy conversion](../docs/wendy-conversion-adapter.md) uses a concrete adapter
and an explicit existing interpreter. [Robot selection](../robots/README.md) accepts
source keys such as `menagerie_x` and `UMR` with local checkout roots, validating
exact revisions and required bytes without moving them into bootstrap.
[Canonical preparation](../docs/umr-canonical-preparation.md) makes fresh run-local
copies and records prepared-only identity/cache evidence. Official G1 reproduction
continues to use its own bundled assets. See [check tiers](../docs/checks.md) and
the [closeout evidence](../outputs/artifact-archives/experiment-reset-20261104/experiments/layout-and-robot-assets-evidence/ticket13/README.md)
for measured CPU/structural checks and unavailable workflows.
