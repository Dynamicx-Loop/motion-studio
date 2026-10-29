# 03 — Register active conversion and preserve historical dependency roles

Status: resolved
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

Claimed by ticket03 implementer on `codex/layout-assets-03`; ancestry checked against
`de0d6f54bffdb8fc915fa4e2df2e09a6a1892f2c`. Read the development policy, external README/manifest/workspace
tool and migration record before implementing; do not advance dependency pins.


## Answer

Registered clean hiphi2smplx at `65e51315ebbc82b2f0ff8e35a94565beb1b345e1`
with verified local origin/upstream URL after inspecting its README, pyproject and
MIT license. Existing manifest pins, UMR cohorts, environments, external checkouts
and original dirty canonical source remain unchanged.

Added [dependency roles and recovery](../../../docs/dependency-roles.md) and the
[machine-readable inventory supplement](../../../configs/dependency-roles.json).
Historical UMR worktree/clone and local menagerie source remain outside bootstrap;
hhtools metadata, environment paths and old compatibility aliases remain intact.
The workspace CLI can inspect explicit canonical sources using this worktree's
manifest through `check --source-workspace /data/workspace/motion_studio`; this
read-only option cannot redirect bootstrap or bypass its path restrictions.

Independent scratch recovery compared all six tracked and two untracked surface
source files against both the saved patch and initial inventory recovery payloads:
8/8 matched current bytes. No source delta was found; an empty additive delta is
retained. The baseline patch independently recovered 16/16 committed additions
from the official base. Exact Git/worktree relationships, patch/archive hashes,
source hashes, exclusions and reconstruction instructions are in the new record.

Stable local receipt:
`/data/workspace/motion_studio/outputs/dependency-roles/layout-and-robot-assets-20261029-03-verified/report.json`,
SHA-256 `4aa23956354993217d0b869ebdf25307c9df644123f99f851139de88a09dd809`.
The earlier sibling scratch-validation attempt is incomplete and unused.

Validation (all Python commands used `PYTHONDONTWRITEBYTECODE=1`):

- New read-only inspection test failed before implementation and passed afterward.
  Four local fixture tests passed: pin-specific missing bootstrap, existing
  dirty/untracked preservation, drift reporting without mutation, redirected
  bootstrap rejection and existing outside-link/traversal safety coverage.
- `python3 scripts/workspace.py list`: five pinned projects listed.
- `python3 scripts/workspace.py check --source-workspace /data/workspace/motion_studio`:
  all five revisions match; UMR's existing data link and eight hhtools status
  entries reported as preserved local work.
- `python3 scripts/check.py`: 6/6 selected pure suites passed. Other tiers remain
  explicitly unselected; no external runtime, environment install or GPU run.
- Initial receipt seal hashes validated. Full initial inventory verification
  rechecked 9,975 files and nine repositories; its only ten findings are newly
  added ticket03 receipt files under `outputs/dependency-roles/`. No prior source,
  alias, HEAD, status or patch drift. Independent statuses of all eight dependency
  repositories also matched the initial receipt. Initial inventory not rewritten.
- Added documentation links resolved against owned sources or explicit canonical
  local evidence; `git diff --check` passed.

Limits: source presence does not establish runtime readiness. Git objects, ignored
assets/environments and licensed data remain at original locations; the surface
data symlink is located but not archived. Sensitive tracked hhtools configuration
is excluded by the original receipt. No remote freshness check, dependency upgrade,
reclone of existing checkouts, historical numerical rerun or baseline advancement.
