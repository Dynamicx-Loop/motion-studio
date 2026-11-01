# 11 — Visible pipeline actions and execution status

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Context

The user cannot discover sampling/binding/retargeting in the sidebar dropdown,
and failures are hidden in collapsed Status & logs.

## Acceptance criteria

- Place clearly named Sampling, Binding and Retargeting actions near the viewport.
- Show the prerequisite plan and explicit launch there; binding includes training
  and later actions compute missing prerequisites without silently launching.
- Keep progress, completion, failures and cancellation visible there, including
  readiness or request failures. Retain logs and advanced settings.
- Preserve historical read-only behavior, revisions, single-job execution and
  saved-result tabs. Do not start computation during UI validation.

## Comments

2026-10-30: Implementation delegated to GPT-6.1 Sol high; root handles browser
acceptance and documentation. Existing saved run r0004 has completed outputs.

## Answer

Added the viewport Compute stages strip with Sampling, Binding and Retargeting
review buttons, explicit launch, readiness/results, observed progress, failures
and cancellation. Advanced settings and saved artifacts remain in the sidebar.
Active jobs block concurrent launches; historical and saved snapshot controls
are disabled. Stale async responses cannot expose a launch for another render.
Fixed duplicate initial pageshow refresh discovered in browser testing; it could
erase an in-flight plan. Invalid settings now open the settings disclosure.

Validation: focused execution UI tests, existing frame-request/source-mesh JS
suites, syntax and whitespace checks passed. Real browser Sampling review
showed all outputs already verified with no launch; completed job status stayed
visible with Status & logs collapsed. Before/after jobs and runs match exactly.
Progress/failure/cancellation cases were exercised with mocked APIs, not a new
GPU run. Browser evidence: ev_fe2253027911c2670e4f6d2eeaaacb790d869b39ae5300c98ffd611a496fb023.
Screenshot: `outputs/studio-viewport-controls-20261030/controls.png`.
