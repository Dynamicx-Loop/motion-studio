# Workspace migration — 2026-10-21

Canonical project root: `/data/workspace/motion_studio`.

- `UMR/` moved to `externals/UMR/`.
- `/data/workspace/rplab/human-humanoid-tools/` migrated to
  `externals/human-humanoid-tools/`, including Git metadata, ignored local files,
  the Python environment, assets, and uncommitted work.
- Existing hhtools modifications to the Astro P2 robot and Codex configuration,
  untracked research notes, MCP launcher files, and the Wendy motion symlink were
  preserved. The copied Codex configuration now uses the canonical location.
- The old location retains protected metadata because the workspace sandbox mounts
  it read-only. Compatibility links point its moved top-level entries to the new
  location. Existing absolute environment paths therefore still resolve. Treat
  the new location as canonical; do not develop in both Git metadata copies.
- Existing linked Git worktrees were not relocated or re-registered. Their metadata
  still refers to the original checkout. Keep that compatibility location while
  those worktrees or old environment paths are in use.

The root manifest pins committed baselines, not local edits or ignored assets.
Back up or commit external-project changes separately before recreating this
workspace elsewhere. The retained hhtools virtual environment is machine-specific;
a fresh machine must install its own environment using the upstream instructions.

Validation covers checkout revisions, preserved Git status, bibliography entries,
and workspace tooling. Full retargeting jobs and GPU dependency installation are
outside this structural migration and have not been run.
