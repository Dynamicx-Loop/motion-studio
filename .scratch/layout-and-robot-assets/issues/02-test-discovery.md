# 02 — Provide one check entry with explicit runtime tiers

Status: ready-for-agent
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
