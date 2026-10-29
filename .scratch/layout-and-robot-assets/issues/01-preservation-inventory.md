# 01 — Seal the preservation inventory before structural changes

Status: ready-for-agent
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
