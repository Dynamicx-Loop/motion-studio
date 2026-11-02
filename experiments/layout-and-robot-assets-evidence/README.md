# Experiment: owned legacy evidence reconstruction parity

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-29, Motion Studio ticket 05 implementation.

## Objective

Extract active evidence reconstruction/preflight and demonstrated pure report
rules into Motion Studio without changing any saved metric, legacy identity or
execution claim. Compare fresh old/new reconstruction, not numerical reruns.

## Provenance

- Original saved inputs: `/data/workspace/motion_studio`, owned source snapshot
  `de0d6f54bffdb8fc915fa4e2df2e09a6a1892f2c`; canonical original HEAD remains
  `1bfa7fc4931fec7ebc5f19444515a3125ff5207b` with its preserved dirty state.
- Owned implementation: `463a35e`; validated after merging integration checkpoint
  `bbd6dac8f80ca63e6a7267fa0db4a4b54ba589c0`. The old implementation remains
  available in the canonical preserved workspace and source checkpoint.
- The [committed comparison record](validation.json) retains all four before/after
  output hashes, the complete saved summary and verification findings.
- Source closure: all 459 old reconstruction sources match both ticket 01's sealed
  inventory and their current canonical hashes. Original source records, config,
  robot identities, calibration, FPS, units, axes and joint ordering are retained
  without reinterpretation. Original asset/dataset terms continue to apply.
- Environment: existing system Python 3.12 and installed tooling `jsonschema`,
  CPU file/JSON processing only. No runtime dependencies or assets were installed.
  No reference method or solver claim is made by this ownership change.

## Reproduction

From the owned checkout, select fresh destinations under its own ignored outputs.
Do not write through an output link into canonical evidence. This example uses
original canonical code for the before reconstruction and owned code for after:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, '/data/workspace/motion_studio/scripts')
from experiment_support.legacy import reconstruct as old_reconstruct
from motion_studio.evidence import reconstruct, verify_bundle
root = Path('/data/workspace/motion_studio')
before = Path('outputs/evidence-parity/<fresh-id>/before')
after = Path('outputs/evidence-parity/<fresh-id>/after')
old_reconstruct(root, before)
reconstruct(root, after)
for name in ('results.jsonl', 'inventory.json', 'summary.json', 'README.md'):
    assert (before / name).read_bytes() == (after / name).read_bytes(), name
assert verify_bundle(after, root)['passed']
PY
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py --tier pure --tier saved-evidence
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 -m unittest experiment_support.test_legacy -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/preserve_workspace.py verify /data/workspace/motion_studio/outputs/preservation/layout-and-robot-assets-20261029-01
```

This comparison depends on the preserved canonical old implementation. The compact
record deliberately avoids transient output links. New bundles add a sealed
`implementation.json` receipt and owned source/schema hashes to their manifests.
Historical manifests are not rewritten.

## Evaluation

All four existing reconstructed outputs were byte-identical: 52 static arms,
24 motion arms, 1,924 native/common segment rows and zero new baseline arms.
Metric values, definitions, source pointers, legacy cohorts and limitations match.
Both old/new bundle verification passed. The new bundle verifies 470 source and
five output files; the additional output is implementation provenance.

Ten fixture tests cover small reconstruction without a report builder, preserved
source denominators, preparation without execution, invalid contracts/JSON,
source drift, bundle tampering, overwrite refusal and retrospective-claim rejection.
Eight selected root suites passed after merging ticket 03; the standalone historical
command also passed all four saved-evidence tests. Other runtime tiers were not run.

## Observations and next step

The initial full preservation verification passed for 9,975 files and nine
repositories. Final full verification correctly reports ten new ignored ticket 03
receipt payloads, with no changes to original sources, repository HEAD/status,
tracked patches or compatibility aliases. All 459 reconstruction input hashes
also independently match the sealed inventory. External worktree listings match;
the root listing reflects authorized task worktrees and integration advancement.
The initial inventory remains immutable.

Preflight still reports file readiness separately from runtime readiness.
Reservations remain `prepared_only`, with no stages executed and execution
readiness false. Saved numerical records establish this structural parity only;
no report build, UMR static runtime, training, retargeting, controller or GPU work
was exercised. Raw binary/model hashes mentioned by historical records remain
recorded claims rather than newly validated numerical inputs.
