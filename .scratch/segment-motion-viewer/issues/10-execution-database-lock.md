# 10 — Run all fails before sampling

Status: resolved
Category: bug
Spec: ../spec.md
Blocked by: none

## Context

User launched the G1/short HiPHI pipeline twice on run
`f9eb1a58ca8c42468e2b4edb1e49e62a`, revision `r0004`. Both jobs failed
before recording a stage attempt, with `database is locked` after about ten
seconds. CUDA readiness passed. Result tabs correctly remained unavailable,
but the failure was hidden in the collapsed status area.

## Scope and acceptance criteria

Diagnose and fix the transaction contention through the actual execution path.
Add a regression test; preserve failed attempts, saved runs and pinned externals.
Restart the idle local service with the fix and verify the original request can
advance into native computation without the database error.

## Comments

2026-10-30: Backend diagnosis delegated to GPT-6.1 Sol high. No native log exists
for either failure because execution stopped before sampling was launched.

## Diagnosis and fix

`list_runs()` kept a live SQLite SELECT cursor while hydrating records through
other connections. The worker's first stage update then waited to commit behind
that reader; nested record reads waited behind the pending commit. Materializing
the run rows and closing the listing connection before hydration breaks the cycle.
No timeout increase, schema change, or upstream edit was needed.

The coordinated regression invokes real `start_execution`/`execute_job` alongside
public `list_runs`. Before the fix it reproduces the exact failure in 0.54 seconds
(stage null, attempts empty, database locked); afterward it completes sampling.
All 32 focused execution/lifecycle/core/HTTP tests pass. Whitespace checks pass.
The original preservation verifier reports all 288 protected files unchanged.

The idle service was restarted with the fix (PID 553717); the original r0004
request was retried as `ee3d5f51a2fd4bcbbe46638913c99f97`, preserving 500 epochs,
seed 0 and LQR. Evidence is under `outputs/studio-execution-lock-20261030/`.

## Answer

Original native Run all retry completed successfully: sampling, 500-epoch
training, binding and all 180 retarget frames validated. Browser status shows
all six stage tabs available and completed outputs validated. No new input
revision was created (r0004 retained). Prior job records and all other runs
compare exactly equal before/after. Status & logs is left expanded for the user.
