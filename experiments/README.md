# Experiment index

## Current experiments

The new G1 study on `experiments/umr-baseline` uses fresh outputs and retains
the complete requested source clips. It contributes evidence toward the future
experiment contract; it does not declare that contract settled.

| Experiment | Scope |
| --- | --- |
| [G1 / SMPL-X](umr-baseline-g1-smplx-20261102/README.md) | Official-default UMR reproduction with the full HiPHI get-up clip. |
| [G1 / SOMA-X](umr-baseline-g1-somax-20261102/README.md) | Preserved direct jump-and-land BVH control with generic surface; shared uniform fit subsequently located and verified. |
| [G1 / fitted uniform SOMA prototype](umr-baseline-g1-soma-uniform-prototype-20261102/README.md) | Fresh full-clip native fitted route, numerical validation and source/robot inspection; visual acceptance pending. |
| [G1 comparison](umr-baseline-g1-comparison-20261102/README.md) | Human/robot bindings, source/retarget replay, and robot binding consistency across source models. |

The clips differ, so motion-quality differences cannot be attributed solely to
the human model. Each record states its execution status, actual source route,
settings, validation and limitations.

## Legacy experiments

All 33 experiment directories in this section are **legacy**, designated on
2026-11-02. They remain in place for historical evidence and reference. New
experiments will establish a standard experiment contract; that contract is
not yet settled. Legacy status does not invalidate recorded results or assert
compliance with the future contract. It applies to this listed set, not
automatically to experiments added later.

These records describe distinct inputs, controls, and stages; dates alone do not
make a cohort disposable. Links lead to each legacy record. Results and supporting
payloads may live in ignored `outputs/`.
See [preservation](../docs/preservation.md) and [artifact relocation](../docs/artifact-relocation.md)
for receipts, resource closures, archived payloads and legacy aliases before
moving or removing anything. A directory listing alone cannot establish that a
resource is unused or reproducible.

On 2026-11-02, source and documentation corrections were additive maintenance;
saved numeric reports and archived payloads remain historical. Source drift from
old preservation receipts must be understood in that context. No experiment
directory was proven disposable from age alone; historical writers can overwrite
evidence and should not be assumed safe to rerun.

| Experiment | Status | Recorded role | Purpose |
| --- | --- | --- | --- |
| [all-robot-segment-audit](all-robot-segment-audit/README.md) | Legacy | Historical cohort/control | Shipped robot configurations and segment bindings. |
| [astro-canonical-static-v1](astro-canonical-static-v1/README.md) | Legacy | Historical open-hand cohort/control | Frozen Astro visual-surface static baseline and controls in report v4. |
| [astro-canonical-wrist-v1](astro-canonical-wrist-v1/README.md) | Legacy | Historical open-hand cohort/control | Wrist calibration candidates on canonical static slots in report v4. |
| [astro-correspondence-comparison](astro-correspondence-comparison/README.md) | Legacy | Historical cohort/control | Visual versus primitive learned correspondence. |
| [astro-fist-static-v1](astro-fist-static-v1/README.md) | Legacy | Report v5 cohort | Fixed-fist static correspondence; historical runtime and evidence. |
| [astro-fist-wrist-v1](astro-fist-wrist-v1/README.md) | Legacy | Report v5 cohort | Fixed-fist wrist calibration; historical runtime and evidence. |
| [astro-hand-wrist-correction](astro-hand-wrist-correction/README.md) | Legacy | Historical cohort/control | Initial wrist-to-palm calibration with G1 control. |
| [astro-hands-correspondence](astro-hands-correspondence/README.md) | Legacy | Historical cohort/control | Dex3-1 hand surfaces and static correspondence. |
| [astro-surface-geometry](astro-surface-geometry/README.md) | Legacy | Historical geometry audit | Measured visual and primitive sampling and binding checks; retained patch. |
| [hiphi-conversion-control](hiphi-conversion-control/README.md) | Legacy | Historical cohort/control | Full BVH-to-SMPL-X conversion comparison. |
| [hiphi-head-objective](hiphi-head-objective/README.md) | Legacy | Historical cohort/control | Head objective ablation and source cross-check. |
| [hiphi-robot-control](hiphi-robot-control/README.md) | Legacy | Historical cohort/control | HiPHI robot control comparison. |
| [layout-and-robot-assets-evidence](layout-and-robot-assets-evidence/README.md) | Legacy | Prior reference | Reconstruction parity, preservation and relocation evidence. |
| [segment-binding-audit](segment-binding-audit/README.md) | Legacy | Historical cohort/control | Human-to-Astro segment audit with matched G1. |
| [soma-correspondence-audit](soma-correspondence-audit/README.md) | Legacy | Historical cohort/control | SMPL-X and SOMA static correspondence controls. |
| [studio-asset-library-20261030](studio-asset-library-20261030/README.md) | Legacy | Smoke/acceptance | Robot library, custom import and playback workflow. |
| [studio-astro-builtin-20261101](studio-astro-builtin-20261101/README.md) | Legacy | Smoke/acceptance | Built-in Astro import, pose and preview acceptance. |
| [studio-astro-full-hiphi-20261101](studio-astro-full-hiphi-20261101/README.md) | Legacy | Prior reference | Full HiPHI clip and 500-epoch built-in Astro run. |
| [studio-astro-hiphi-smoke-20261101](studio-astro-hiphi-smoke-20261101/README.md) | Legacy | Smoke/acceptance | Short Astro end-to-end workflow. |
| [studio-baseline-acceptance-20261030](studio-baseline-acceptance-20261030/README.md) | Legacy | Prior reference | Full G1 application acceptance and retained cohorts. |
| [studio-inspection-smoke-20261030](studio-inspection-smoke-20261030/README.md) | Legacy | Smoke/acceptance | Derived stage and animated inspection. |
| [studio-native-stages-smoke-20261030](studio-native-stages-smoke-20261030/README.md) | Legacy | Smoke/acceptance | Native stages and pre-solve binding. |
| [umr-astro-baseline-proposal](umr-astro-baseline-proposal/README.md) | Legacy | Setup/proposal | Asset inspection and baseline review records. |
| [umr-astro-baseline-v1](umr-astro-baseline-v1/README.md) | Legacy | Prior study baseline | First official-default Astro/G1 static diagnostic baseline candidate, distinct from later Studio and reproduction cohorts. |
| [umr-binding-report](umr-binding-report/README.md) | Legacy | Prior report reference | Canonical Astro evidence report v5 and historical disclosure. |
| [umr-g1-baseline-20261029](umr-g1-baseline-20261029/README.md) | Legacy | Prior reference | Official-default G1 reproduction via Motion Studio. |
| [umr-motion-canonical-v1](umr-motion-canonical-v1/README.md) | Legacy | Historical open-hand cohort/control | Canonical Astro raw/candidate motion with G1 controls in report v4. |
| [umr-motion-fist-v1](umr-motion-fist-v1/README.md) | Legacy | Report v5 cohort | Fixed-fist HiPHI motion; historical runtime and evidence. |
| [umr-motion-preliminary-v1](umr-motion-preliminary-v1/README.md) | Legacy | Smoke/acceptance | Short motion smoke; v2 supersedes it for motion inspection, while retaining its outcomes. |
| [umr-motion-preliminary-v2](umr-motion-preliminary-v2/README.md) | Legacy | Historical cohort/control | Full decimated HiPHI motion with G1/Astro controls. |
| [umr-root-branch-setup](umr-root-branch-setup/README.md) | Legacy | Setup/proposal | Root branch setup and verification records. |
| [wendy-conversion-adapter](wendy-conversion-adapter/README.md) | Legacy | Smoke/acceptance | Converter adapter numerical parity and timing. |
| [wendy-torso](wendy-torso/README.md) | Legacy | Incomplete/config-only | Wendy torso and iteration configurations; no completed experiment result recorded. |

Recorded roles describe the historical work, not active status or compliance
with a future contract. Legacy labels are not deletion decisions or claims of
equivalence between cohorts. Investigate individual redundant generated members
only against receipts, inbound references, and complete resource closures; no whole directory
is established as safe to remove by this inventory.
