# 06 — Cancel, recover and revise persistent native runs

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: 04

## Context and outcome

Deliver cancel, recover and revise persistent native runs as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [x] One active compute job enforced across requests; viewing other runs remains available; saved drafts never auto-queue.
- [x] Browser close leaves jobs running; Stop terminates owned process group while preserving completed artifacts/logs.
- [x] Service interruption recovery marks unfinished attempts interrupted; explicit retry restarts interrupted stage with verified compatible prerequisites.
- [x] Input/settings edits fork immutable revisions, visibly mark affected stages stale and preserve old result; no cross-clip reuse.
- [x] Test races, duplicate launches, cancellation escalation, restart recovery, failed/incomplete receipts, corrupted reuse candidates and stale callbacks through public outcomes.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.


## Answer

Implemented immutable run revision discovery/selection separately from the editable
head, persisted refresh/restart restoration, input/settings preservation, visible
stale/reused stage reasons, explicit settings save and explicit retry planning.
Settings revisions carry only an authenticated unchanged prefix: epochs retains
sampling; smoothing retains sampling/training/binding. Each reference records the
original revision and receipt hash and rechecks the original dependency/artifact
chain; robot/pose/motion changes invalidate all stages, with no cross-clip reuse.
Original artifacts and older snapshots remain intact and browsable.

Compute launches are serialized across requests/processes before settings mutation,
with transactional single-active-job enforcement. Native process groups run beneath
an independent stdlib guard tied to the service PID's kernel start identity. Service
death stops the group; reopening records unfinished work as interrupted and requires
explicit retry. Stop escalates through TERM/KILL for descendants. Terminal updates
are monotonic; cancelled/interrupted/stale completions cannot publish. Attempts,
completed prerequisites and logs are retained; crashed leaders cannot leave an
orphan holding the compute slot or output pipe. Browser lifetime remains independent.
The global status/Stop control remains available while viewing other saved runs.

Validation at the explicitly approved public Studio/HTTP and concrete-adapter seams:

- TDD: observed missing revision API and stale-state failures before implementing
  those slices; exercised subsequent lifecycle outcomes with real subprocesses.
- `python3 -B -m unittest discover -s tests -p test_studio_lifecycle.py -v`:
  13 passed. Covers concurrent launches from threads, independent Studio objects
  and a separate service process; cancellation escalation/late outputs/idempotence;
  killed service plus orphan cleanup and fresh retry retaining sampling; native and
  process-leader crashes; corrupted/incomplete receipts; related-revision reuse;
  cross-clip invalidation; input/settings preservation; revision HTTP selection.
- `python3 -B scripts/check.py --tier pure`: 25/25 selected suites passed.
- `node --check motion_studio/studio/web/app.js` and `…/execution.js`: passed.
- `git diff --check`: passed. New cohesive private modules are under 125 lines;
  lifecycle tests remain below 400 lines. No external source/pin changes.
- Browser smoke used the hidden Codex in-app browser against loopback :8786 and a
  clearly labeled real subprocess fixture (no native solve). Launched sampling via
  UI, closed/reopened the tab with the same active job, saved epochs=2 and retained
  sampling, inspected another draft during training, stopped it from the global
  footer, reviewed explicit retry (training only, fresh attempt), saved seed=2 with
  visibly stale stages, selected the old completed snapshot and refreshed.
  Public HTTP records independently checked final states, distinct attempt IDs and
  exact reused receipt equality. Durable evidence:
  [browser report](../../../outputs/studio-lifecycle-ticket06-20261030/browser-evidence.json),
  [stale revision](../../../outputs/studio-lifecycle-ticket06-20261030/stale-revision.png),
  [reopened history](../../../outputs/studio-lifecycle-ticket06-20261030/history-reopened.png).

Limits: Linux process-identity/group semantics are intentional for this local host.
Legacy jobs lacking a kernel birth identity are never signalled via an unverified
PID. No native numerical rerun was needed for the focused lifecycle suite; ticket07
retains fresh full-clip/default-quality GPU acceptance. Ticket05 owns rich stage
inspections/export and is merged separately; no historical output, canonical asset,
pinned external, or original viewer was changed.
