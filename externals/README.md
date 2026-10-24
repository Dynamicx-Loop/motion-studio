# External projects

Each project is an independent Git checkout, not vendored source or a submodule.
The root repository ignores checkout contents and tracks `manifest.json` instead.
This preserves upstream histories and allows different environments and release cycles.

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
