# UMR integration review — 2026-10-29

Scope: existing integration reviewed against the development policy in
[workflow.md](workflow.md#development-policy). This is an ownership and interface
review of the current workspace, including local experimental code, rather than
a review of upstream UMR's numerical method.

## Findings and disposition

| Finding | Evidence | Disposition |
| --- | --- | --- |
| G1 baseline execution depends on an integration worktree | `scripts/umr_baseline/static_pair.py` defaults to `externals/UMR-baseline-v1`; that worktree stores root-project runners and records under `motion_studio/` | New G1 reproduction uses official `externals/UMR` directly. Preserve the worktree and historical callers until separately migrated. |
| G1 preparation is coupled to Astro | `static_pair.prepare` requires a menagerie revision, copies Astro assets, and prepares both robots; `evaluate_static.evaluate` assumes both arms | New G1 operation requires only official G1 assets, bundled HiPHI input, and local SMPL-X weights. |
| Upstream details leak into callers | Legacy static CLI imports UMR through global `sys.path` changes and exposes preparation/run/evaluation orchestration; evaluator imports multiple upstream numerical modules | New CLI calls one Motion Studio operation; imports, configuration, subprocess stages, and result interpretation live in its adapter. |
| Experimental source changes exist outside Motion Studio | `externals/UMR-astro-surface-experiment` contains uncommitted sampling/projection/binding changes and tests | Excluded from the new baseline. Preserve patches as historical evidence; review justification before adopting any change. |
| Upstream runtime writes can alter its asset directory | `prepare_robot_xml` in official `retarget_smpl_to_humanoid_surface_vector.py` emits a floating-root XML beside the input XML | Adapter copies the shipped G1 bundle into the fresh run and points UMR to that copy. No upstream patch is required. |

The existing root records, source pins, explicit runtime, and frozen output paths
already support reproducibility. The issue is where integration knowledge lives
and how callers use it. Historical experiment results are not invalidated by
these ownership findings.

## Current G1 interface

`motion_studio.integrations.umr.reproduce_g1_baseline(output)` returns a typed
`G1BaselineResult` with motion, validation, and provenance paths. It requires a new
output directory and the inspected UMR pin. It owns the full sequence of prepare,
train, retarget, and validate. It executes in the external's existing environment;
importing the public module or asking the CLI for help needs only system Python.

`motion_studio/integrations/_umr_worker.py` is private adapter implementation in
Motion Studio. It invokes pinned upstream functions and checks upstream outputs
without modifying those functions. The interface deliberately supports this
concrete G1 reproduction rather than offering a generic plugin framework.

The existing pair runner remains a historical reproduction tool. The new operation
has no dependency on the pair worktree, patched clone, old diagnostic report, or
Astro model. Its full-clip result is a new cohort; it does not advance or overwrite
the October 24 static pair.

See the [new experiment record](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-g1-baseline-20261029/README.md)
for commands, validation, and measured results.

## Current UMR experiment

Use the [standard Studio experiment](../experiments/umr-standard/README.md) for
the matched G1 and Astro P2 static binding run.
