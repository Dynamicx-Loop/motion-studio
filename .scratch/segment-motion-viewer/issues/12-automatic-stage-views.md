# 12 — Automatic stage visualization and visible progress

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Scope

Load completed stage visualizations directly when selected, preparing missing
derived inspections automatically. Keep standalone export separate. Show visible
loading/failure/retry without launching native pipeline computation. Coalesce
duplicate requests and prevent stale responses from changing the selected view.

Add accessible progress bars near the viewport: measured epoch/frame progress
when known, indeterminate when unknown, and truthful terminal status. Refresh
available results at native stage transitions without switching the user's tab.

## Validation

Focused UI tests for request lifecycle and progress states; actual browser loads
of saved stage results; verify native jobs, revisions and protected files remain
unchanged during viewing.

## Comments

2026-10-30: Delegated independent UI responsibilities to GPT-6.1 Sol high agents.

## Answer

Implemented automatic selected-stage viewing from saved results with cached
reuse, coalesced preparation, local loading/error/retry, stale-view guards and
separate optional standalone export. Existing cached views stay visible during
fresh export. Automatic preparations do not show filesystem paths.

Accessible per-stage bars display measured epoch/frame counts, indeterminate
unknown progress, explicit stopped/failed states and validated completion.
Polling refreshes newly available stage results without changing the viewed tab.

Validation: both inspection/execution UI suites pass (including duplicate request,
alias, async race, failure, cached export, progress and transition cases). Actual
browser prepared/opened motion, sampling, training and binding successfully;
cached binding geometry rendered with four validated bars, no page errors.
Evidence: ev_641e4d30fa846d4b5bba939c2785699cd46a24503062a5a217cd4f97d0f56c05;
rendered screenshot ev_c510ac2d228007bdede4423c5b9a7a158998e6ebc961a8a02882697720ada936.
Screenshot and state snapshots: `outputs/studio-auto-views-20261030/`.

All revisions and job count stayed unchanged. The user's already-running full
clip job completed during this work; the agent launched no native job. Progress
intermediate/error states were tested with mocked APIs. All 288 protected files
passed preservation, and whitespace checks passed.
