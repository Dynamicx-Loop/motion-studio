# Owned check command

From the Motion Studio root, run:

```sh
python3 scripts/check.py
python3 scripts/check.py --list
```

The default runs every discovered pure Python suite using the calling Python.
It needs no UMR, GPU, model weights or installed scientific runtime. The inventory
lists all owned suites and their declared prerequisites without importing them.
`--json` produces a machine-readable inventory or result report.

The command discovers `test*.py` and `test*.cjs` under `tests/`, `scripts/` and
`motion_studio/`. It does not traverse `externals/`, experiments or generated
outputs. New Python suites are pure by default, so adding a test requires no
central registry change. Each suite runs in a separate subprocess; package-relative
imports and existing standalone test commands remain supported.

## Explicit runtime tiers

Select one or more tiers by repeating `--tier`:

```sh
python3 scripts/check.py --tier saved-evidence
python3 scripts/check.py --tier javascript
python3 scripts/check.py --tier umr-static \
  --umr-python externals/UMR/.venv/bin/python \
  --umr-run outputs/umr-astro-baseline-v1/static-20261024-01
```

| Tier | Checks and prerequisites |
| --- | --- |
| `pure` | G1 interface safety, recorded motion paths, Markdown reading and check-command fixtures; subsequent owned pure tests are discovered automatically. |
| `saved-evidence` | Retrospective legacy reconstruction, declared saved experiment records and schema-validation package in the calling Python. No numerical rerun. |
| `javascript` | Node.js search check against the existing generated reading bundle. Its six cases do not establish browser direct-file rendering. |
| `umr-static` | Original static-pair suite, explicit external interpreter, preserved run/config/assets and the pinned historical checkout. No training, retargeting or simulation. |

An unavailable selected prerequisite produces `unavailable` and a nonzero exit;
it is never a passing or silently skipped check. A failing suite, empty test suite
or no discovered/selected checks also exits nonzero. Unselected tiers are visibly
`not-selected`; a successful default command validates only the pure tier.
No command installs packages, downloads assets or creates a shared environment.

Use `--root <source-workspace>` to check another owned workspace explicitly.
That workspace must contain the code and declared evidence required by the
selected suites. Worktree users can supply verified read-only external/evidence
links locally; the command does not provision or modify those inputs.

## Declare a suite needing more than pure Python

Add literal module-level metadata to the Python test file:

```python
CHECK_TIER = 'saved-evidence'
CHECK_INPUTS = ('experiments/example/results.json',)
CHECK_MODULES = ('jsonschema',)
```

`CHECK_INPUTS` paths are relative to the selected source workspace. Optional
`CHECK_MODULES` names are probed in the selected interpreter before test import.
Static suites may declare `CHECK_RUN_INPUTS`, relative to the explicit saved run.
Inventory parses literals with the Python AST rather than executing test code;
unknown tiers and malformed metadata fail configuration validation.

JavaScript suites are assigned to `javascript` automatically and can declare a
JSON array of prerequisite paths in a `// CHECK_INPUTS: [...]` comment. Tests
requiring a generated edition must declare that input rather than appearing in
the pure tier. Keep unit fixtures small and independent of the full real workspace.

The owned API is `motion_studio.checks.discover(root)` for immutable suite records
and `check(root, tiers=..., umr_python=..., umr_run=...)` for immutable outcomes
and an aggregate exit code. The command only parses arguments and renders reports.
