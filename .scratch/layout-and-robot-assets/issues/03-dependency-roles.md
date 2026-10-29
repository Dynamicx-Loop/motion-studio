# 03 — Register active conversion and preserve historical dependency roles

Status: ready-for-agent
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 01
Dependencies: [01 preservation inventory](01-preservation-inventory.md)

## Context

The external manifest lists UMR, hhtools, ProtoMotions and PyRoki. Active conversion
uses hiphi2smplx, clean at `65e51315ebbc82b2f0ff8e35a94565beb1b345e1` at
inspection. Historical UMR checkouts have separate integration/patch state.
menagerie_x is an asset source outside the manifest tool's allowed child paths.

## Outcome and scope

Make a fresh workspace aware of the active conversion dependency while retaining
historical reproduction requirements. Update dependency records and workspace
documentation without updating pins, recreating environments or moving checkouts.

## Acceptance criteria

- Register hiphi2smplx with its verified upstream/clone URL and exact inspected
  commit, after reading its local dependency/license records. A bootstrap of a
  missing directory selects that pin; existing dirty directories remain untouched.
- Inventory clearly distinguishes active UMR/conversion paths, source-only
  ProtoMotions/PyRoki, local hhtools state, historical baseline worktree and
  experimental clone. No source availability is reported as environment readiness.
- Historical records preserve base/HEAD, branch/worktree relation, tracked and
  untracked patch coverage, hashes, reconstruction commands and validation limits.
  Compare the saved surface patch against current dirty files; preserve any delta.
- Preserve the hhtools old location, links, venv paths and Git metadata according
  to the migration record. Keep the menagerie checkout external to bootstrap;
  document its pin and supplied source-root locator for robot resolution.
- Existing UMR manifest pin and baseline cohorts stay unchanged; workspace check
  reports current drift/local edits and bootstrap retains its non-overwrite rule.

## Validation

Run `python3 scripts/workspace.py list` and `python3 scripts/workspace.py check`;
record existing status separately from regressions. Use a temporary local fixture
repository to verify missing bootstrap and preservation of an existing dirty
checkout without network. Verify preserved patches/archives against ticket 01's
receipt in temporary scratch space and validate all added documentation links.

## Comments

Planning only. Read the development policy, external README/manifest/workspace
tool and migration record before implementing; do not advance dependency pins.
