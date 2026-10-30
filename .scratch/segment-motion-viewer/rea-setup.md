# REA local setup — 2026-10-30

Installed official npm `rea-agents@6.8.0` (MIT), isolated from Motion Studio and external runtimes. Source: https://github.com/morluto/rea and https://github.com/morluto/rea/blob/main/docs/installation.md.

## Installation

- Runtime: `.cache/rea-tooling/node-v22.23.4-linux-x64/bin/node`, official Node archive verified against the release SHASUMS256.txt. Existing Node 22.23.2 unchanged.
- Package: `.cache/rea-tooling/installation/node_modules/rea-agents`; exact dependency lock in adjacent package-lock.json.
- CLI: `/data/workspace/motion_studio/.cache/rea-tooling/rea`.
- npm integrity: `sha512-9QDeRnGqEDzABZyr04eLnBXBv/c6I9/TWu/6M0MD4pEfkySI/BIgwTODIbAReX3C1x6hjw9+Jlx4A2yUSPZ9ww==`.
- Acquisition: `npm --cache /tmp/rea-npm-cache install --prefix /data/workspace/motion_studio/.cache/rea-tooling/installation --no-audit --no-fund rea-agents@6.8.0`, with isolated Node bin first on PATH.
- Applied `rea setup --client codex --yes --json` after inspecting `--dry-run --json`.
- Registration: `/home/android/.codex/config.toml`; original backup: `/home/android/.codex/config.toml.rea.backup`.
- Skill: `/home/android/.agents/skills/reverse-engineer-anything`.

Keep `.cache/rea-tooling` in place: the MCP registration refers to its absolute runtime and entry script. It is a retained local tool installation, despite the cache directory name. Restart Codex to discover the new MCP tools; CLI is usable immediately.

## Validation

Setup returned `ready`, applied `configured_codex` and `installed_skill`, and scoped doctor healthy true. CLI help reports 6.8.0. Static JavaScript smoke analysis of a one-function fixture succeeded with no integrity contradictions. Evidence and setup receipts: `outputs/rea-setup-20261030/`.

Native disassemblers were not installed; browser capture and a full native analysis were not exercised. No external repository pins, viewer code, or completed runs were changed. This is tooling setup, not a new retargeting cohort.
