# BONES-SEED uniform support in Local Studio

Status: open
Labels: wayfinder:map

## Destination

Find a buildable plan for BONES-SEED uniform BVH import, fitted SOMA human
preview, native UMR retargeting to built-in G1, and synchronized binding/motion
inspection in Local Studio. A fresh fitted G1 baseline is the acceptance case.
This map produces decisions for a later spec; it does not implement the feature.

## Notes

- User confirmed this destination on 2026-11-02.
- User confirmed that valid BVHs remain importable and skeleton-previewable
  without fitted assets. Fitted preview and retargeting must be blocked until
  their prerequisites are satisfied; no automatic generic-surface fallback.
- User requires automated checks plus their review of synchronized human/robot
  motion and segment bindings before accepting the first fitted baseline.
- On 2026-11-02 the user authorized the focused executable experiment described
  in [Validate the fitted SOMA route](issues/05-fitted-route-prototype.md), delegated
  to GPT-6.1 Sol/high subagents. This is an execution exception for gathering
  evidence before product design, not authorization to implement the full Studio.
- Preserve the existing generic SOMA control and all historical experiment data.
- Follow [development policy](../../docs/workflow.md): owned source interfaces
  and adapters, pinned unchanged UMR, independent runtime, fresh output paths.
- Use Ask Matt / Wayfinder, Grilling and Domain Modeling for decision sessions.
  Follow the [local tracker](../../docs/agents/issue-tracker.md).
- Existing evidence is in the [integration trace](../../docs/umr-soma-boneseed-integration.md)
  and [uniform-fit correction](../../experiments/umr-baseline-g1-somax-20261102/README.md).
  The fit exists and static fitted loading passed; fitted motion/retargeting has
  not yet been validated. Native and browser configurations are distinct.
- Proposed baseline: keep the selected jump-and-land BVH's full native timeline,
  the pinned native G1 setup, and explicitly recorded native solver settings.
  A browser-matched cohort is outside this first milestone.
- Motion skeleton, fitted body surface, human semantic segment, and robot rigid
  body ownership must remain distinct concepts in the proposed contract.

## Decisions-so-far

- [Validate the fitted SOMA route before product integration](issues/05-fitted-route-prototype.md):
  executable experiment passed numerical, all-frame replay and browser checks;
  user visual acceptance and the product design questions remain open.

## Fog

The extent of changes to existing saved-source records and preview derivatives
depends on the selected source contract. Record any compatibility choices exposed
by that decision as new questions rather than assuming old records are disposable.
If fitted-motion validation exposes a mismatch between skeleton and reconstructed
surface, determine its cause before deciding whether any calibration step belongs
in the product. Static loading alone does not establish this behavior.

## Out of scope

Proportional actor fits, arbitrary SOMA skeleton variants and Kimodo import
formats; automatic body fitting; browser solver parity; a universal motion format
or plugin framework; changes to pinned external source; dynamics certification;
rerunning or replacing legacy experiments. These require explicit scope expansion.

## Frontier query

Read child files under `issues/`; take open, unassigned questions whose listed
blockers are resolved. Claim before work. Charting leaves these questions open;
no implementation tickets or implementation spec have been created.
