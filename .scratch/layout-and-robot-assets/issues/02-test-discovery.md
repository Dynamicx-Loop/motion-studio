# 02 — Provide one check entry with explicit runtime tiers

Status: resolved
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: none

## Context

Tests exist in the root tests directory and three script subdirectories plus a
JavaScript search test. There is no root test configuration. The static-pair
suite imports upstream modules and sets its run argument only when executed as
a script; indiscriminate discovery will not correctly run it.

## Outcome and scope

Add a thin root check command that discovers owned test suites and reports
their prerequisites and results. Reuse unittest and existing test seams. Separate
pure system-Python checks from saved-evidence, JavaScript and external-runtime
checks. Do not add a common scientific environment or run training.

## Acceptance criteria

- A documented default command runs the current pure G1 interface, motion-path
  and Markdown-reader suites without importing UMR/scientific runtimes.
- A visible suite inventory includes legacy reconstruction, static-pair and
  JavaScript search checks. An unregistered new owned test is detected rather
  than silently omitted; external checkout tests are excluded deliberately.
- Saved-evidence checks require declared local records; static checks take an
  explicit preserved run path and external interpreter. Missing prerequisites
  are reported as unavailable, with tier coverage distinct from passing tests.
- Any selected suite failure propagates a nonzero exit. No-tests-discovered and
  bad run paths cannot produce a successful full-validation claim.
- Existing command behavior remains valid. Root import/help works without GPU,
  model weights, dependency installs or network. Test configuration stays small.

## Validation

Run the default command from the root and verify its reported suites against
the inventory. Exercise fixture cases for a failing test, newly added suite,
missing evidence/runtime and empty discovery. Run Node search checks only with
their existing bundle available and record unavailable tiers honestly. Do not
claim the static suite passed unless executed with its real run path and venv.

## Comments

Planning only. Preserve the existing tests' behavior; later slices update this
entry as their owned modules and fixtures become available.

Implementation claimed by ticket02 subagent on codex/layout-assets-02, based on integration seed 8d7dff5.

## Answer

Implemented on `codex/layout-assets-02` from integration source seed `8d7dff5`.
The [root command](../../../scripts/check.py) calls the owned
[discovery/run interface](../../../motion_studio/checks.py); its private unittest
loader preserves relative script-package imports and rejects empty suites.
[Usage and tier metadata](../../../docs/checks.md) document the command and its
prerequisites. New owned Python test files are discovered as pure automatically;
AST-only literal metadata classifies saved-evidence/static suites. JavaScript
search is inventoried separately. No upstream runtime is imported by inventory.

Validation in the isolated ticket worktree:

- TDD: observed failing cases before implementing auto-discovery, empty discovery,
  empty suite, package-relative imports, tier isolation, unknown tier, saved input,
  runtime module, static run input, JavaScript discovery and CLI failure behavior.
  Ten fixture tests exercise the public API/CLI using independent tiny projects.
- `python3 scripts/check.py`: four pure suites passed, 23 Python tests. All three
  non-default tiers were visibly not selected rather than silently called passed.
- `python3 scripts/check.py --tier saved-evidence --tier javascript --tier umr-static
  --json` before local resource links: saved evidence passed; JavaScript and
  static suites reported missing inputs/interpreter/run as unavailable; exit 1.
- Full explicit run selected `pure`, `saved-evidence`, `javascript`, `umr-static`,
  with `--umr-python /data/workspace/motion_studio/externals/UMR/.venv/bin/python`
  and `--umr-run /data/workspace/motion_studio/outputs/umr-astro-baseline-v1/static-20261024-01`:
  all seven suites passed (30 Python tests, Node search six cases/46 documents).
  Static tests validated saved configs/input hashes; no training or numerical
  retargeting rerun occurred. JavaScript success is not browser file-open validation.
- Local ignored child links provided read-only UMR/historical checkout and reading
  bundle access; no external/output data was provisioned, installed or modified.
- `git diff --check` passed for the ticket changes. Files remain below 200 lines.

Status changed from claimed to resolved after the selected tier checks passed.
