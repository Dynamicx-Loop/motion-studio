# Implementation orchestration

Status: active

The user authorized `ask-matt` → `implement-spec` orchestration on 2026-10-29.
Implementer subagents work on individual branches/worktrees; a merger integrates
resolved tickets on `codex/layout-and-robot-assets`. The main session coordinates.
No remote issues or pull requests are created by this local-tracker workflow.

## Source checkpoint

The integration branch starts from a source-only checkpoint of the dirty canonical
workspace at `/data/workspace/motion_studio`, original branch `experiments/umr-astro`,
HEAD `1bfa7fc4931fec7ebc5f19444515a3125ff5207b`. Original working files and staging
were not changed. The checkpoint is preservation context, not implementation.

644 owned source/small-evidence files (10,692,896 bytes) were copied byte-exactly.
497 generated/media/binary/third-party/local-only entries (1,656,700,060 bytes) were
excluded and retained at their original locations. The ignored selection manifest
is `outputs/implementation/layout-and-robot-assets/seed-manifest.json`, SHA-256
`7c26dc24003aa6a496d290b587755d8da985614f3bf8f2c5f71fe30b965739db`.
It records all selected/excluded paths and hashes plus canonical Git status.

## Local resources and safeguards

Existing external/output children are ignored links to the canonical workspace.
Treat them as READ-ONLY INPUTS: do not build, regenerate, decorate or write through
these links. New output/run names belong to the individual worktree's own output
directory. Never replace the entire output directory with a canonical symlink.
An implementer should pass explicit canonical evidence roots when supported.
Excluded experiment artifacts are available only in the canonical workspace; they
were not copied or silently relocated into the source checkpoint.

`workspace.py` rejects per-checkout links that resolve outside its externals root.
This is an existing safety rule; ticket 03 may provide explicit source-workspace
inspection without changing bootstrap preservation semantics. Setup does not
weaken that rule. Environments, large assets and generated reader entries remain
local prerequisites, not committed distribution assets.

The managed integration checkout is outside the current sandbox writable roots.
Terminal writes/commits there require `require_escalated`; isolated implementer
worktrees may instead use writable `/tmp` paths with their Git metadata operations
escalated. Never reset or switch the canonical checkout.

## Preservation checkpoint validation

The source snapshot retained historical CSV line endings and patch whitespace
byte-exactly. The initial staged whitespace check reports pre-existing findings
in 23 files; full output is in the ignored seed-whitespace receipt.
Do not reformat historical evidence to clear those baseline findings. New
implementation diffs are checked relative to this source checkpoint.
