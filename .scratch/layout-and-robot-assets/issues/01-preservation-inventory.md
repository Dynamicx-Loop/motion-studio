# 01 — Seal the preservation inventory before structural changes

Status: resolved
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: none

## Context

The workspace contains modified/untracked root work, ignored experiment outputs,
dirty external checkouts, a linked UMR worktree and old hhtools compatibility
paths. Manifest pins cannot reconstruct this state. The spec's size/status
observations are an inspection snapshot, not a recovery inventory.

## Outcome and scope

Create a read-only inventory operation and a sealed local receipt that allows a
later migration to prove what it preserved. Cover the root, all seven current
external directories, menagerie_x, experiment/output evidence, frozen robot
closures, Git/worktree metadata, environment locations and compatibility links.
Classify active, historical, generated, source and unknown entries without moving
them. Keep bulky/private recovery payloads in ignored storage and safe summaries
with experiment records. Do not enumerate credential contents into receipts.

## Acceptance criteria

- Inventory records exact HEAD/status, base pins, tracked diff hashes, untracked
  source files, ignored asset/environment locations, symlink targets and relevant
  worktree links. Unknown completeness is explicit, not a clean-state claim.
- Artifact inventory records paths, size, SHA-256, source/generated role, frozen
  cohort membership and inbound path references. Distinguish symlink size from
  unique stored bytes; include large JSON and binary viewer assets.
- Frozen October 24 pair, G1 runs 20261029-01/02 and historical geometry cohorts
  have independently verifiable asset/config/result closures. No baseline is
  relabeled, resumed, rebuilt or changed.
- Recovery material includes dirty tracked patches plus untracked source and
  ignored-asset manifests; verify patch applicability and recovered file hashes
  in disposable scratch space. Record unavailable assets without claiming recovery.
- Rechecking reports drift and cannot silently rewrite its own baseline receipt.
  Existing output conflicts and broken links fail clearly; receipt creation is
  exclusive and never resets, cleans, stashes or modifies an external checkout.

## Validation

Use small temporary fixtures for files, ignored/untracked work, a linked worktree,
symlinks, missing targets and changed hashes. On this workspace, compare a second
inventory against the sealed first receipt and independently sample recorded
hashes. Verify preservation with `git status --porcelain=v1 -uall` in each repo
and `git -C externals/UMR worktree list --porcelain`; approved new owned inventory
files are the only intended change. Record the exact commands and recovery result.

## Comments

Planning only. Initial classification and preservation policy are authorized;
destructive checkout cleanup is outside this ticket.

Implementation claimed by ticket01 subagent on codex/layout-assets-01; base 8d7dff5.


## Answer

Implemented owned `capture_inventory` / `verify_inventory` operations, a thin
`preserve_workspace.py` command and [usage/receipt boundaries](../../../docs/preservation.md).
Capture seals evidence and dirty-source recovery in a fresh local destination;
verification reports drift without changing the receipt. Source/test files stay
under the soft size guideline and use only the standard library plus Git.

Canonical workspace receipt:
[sealed inventory](../../../outputs/preservation/layout-and-robot-assets-20261029-01/inventory.json),
[seal](../../../outputs/preservation/layout-and-robot-assets-20261029-01/seal.json).
Inventory SHA-256:
`32c9f10f145814668c2b19caf0555e3aa2c7f6ad416252c542be68f357eb30d7`.

- Captured 9,975 files, 16,218,203,231 logical bytes and 16,211,912,731 unique
  stored ordinary-file bytes. Source/experiment/output roles, cohort names,
  symlinks and inbound reference hints are retained.
- All nine repositories passed disposable dirty-source recovery: root, seven
  external checkouts and menagerie_x. Recovery payloads preserve nine root and
  nine external tracked changes (sensitive config paths excluded explicitly),
  plus eligible untracked text/small evidence. No live checkout was patched.
- Recorded 34 old hhtools compatibility entries with no broken captured links.
  Environment/ignored locations are metadata-only; no environments were copied.
- Preserved 8,200 explicit historical path/hash references: 5,855 match current
  files; remaining unavailable/mismatched historical references are findings,
  not silently repaired or called reproduced. Frozen run and experiment bytes
  are hashed independently of those recorded expectations.

Validation:

```sh
python3 -m unittest discover -s tests -p test_preservation.py -v
python3 scripts/check.py
python3 scripts/preserve_workspace.py capture --workspace /data/workspace/motion_studio --output /data/workspace/motion_studio/outputs/preservation/layout-and-robot-assets-20261029-01 --repository menagerie=/data/workspace/notAnyrobot/menagerie_x --compatibility-root /data/workspace/rplab/human-humanoid-tools --source-root /data/motions
python3 scripts/preserve_workspace.py verify /data/workspace/motion_studio/outputs/preservation/layout-and-robot-assets-20261029-01
```

Eleven focused preservation tests passed; the root command passed all five
selected pure suites. Full canonical verification passed with zero errors. An
independent five-file sample covered a checkpoint, official copied G1 XML, frozen
Astro XML, preserved geometry patch and owned adapter; all SHA-256 values matched.
Independent HEAD/status comparisons passed for all nine repositories. No migration,
GPU job, dependency installation or baseline advancement occurred.

Limits: this is not a full Git-object/environment/ignored-binary backup. Exact
excluded paths and unavailable historical hash references remain in the receipt.
Artifact roles/reference extraction aid reviewed migration planning and do not
prove that every text token is an executable dependency. Future implementation
changes must be recorded separately; this initial receipt remains immutable.
