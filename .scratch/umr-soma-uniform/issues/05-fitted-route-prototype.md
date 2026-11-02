# Validate the fitted SOMA route before product integration

Status: resolved
Type: task
Labels: wayfinder:task
Assignee: /root
Map: [BONES-SEED uniform support in Local Studio](../map.md)
Blocked by: none

## Question

Can an owned experiment explicitly prepare the selected uniform BVH and shared
fit, run pinned native UMR against G1, and expose faithful source reconstruction,
segment bindings and retargeted motion for review without generic fallback?

## Scope

The user authorized implementation on 2026-11-02, delegated to GPT-6.1 Sol/high.
This is a numerical experiment prototype, not the HTML logic/UI demonstration
offered by the Prototype skill. No product schema or interface decision is implied.
Keep current experiment branch and existing controls intact; use fresh outputs.

- Pipeline agent: preparation, native execution, validation, provenance and README.
- Inspection agent: source/robot replay, BVH/fitted comparison and inspection page.
- Parent: coordinate, review evidence, verify the deliverable and record findings.

## Acceptance evidence

Assert fitted uniform route and fit identity before execution; preserve all input
frames and timing; train fresh correspondence; check topology and semantic labels;
verify source and robot replay plus numerical integrity. Provide one reproducible
command and a review page. User visual acceptance remains a separate pending gate.

## Comments

Implementation started in `experiments/umr-baseline-g1-soma-uniform-prototype-20261102/`.
Fresh outputs use the same cohort name under `outputs/`. No legacy experiment or
external source changes are authorized by this task.

## Answer

The executable prototype was delivered on 2026-11-02 by GPT-6.1 Sol/high pipeline,
inspection and independent-review subagents. The strict fitted route ran all
1,165 frames through fresh 4,096-point, 500-epoch correspondence and G1 retargeting.
Numerical checks and the final all-frame replay audit passed; source assets,
upstream source and the generic control were preserved. Parent browser checks
confirmed playback, skeleton overlay, segment filtering and report resources.

See the [experiment record](../../../experiments/umr-baseline-g1-soma-uniform-prototype-20261102/README.md),
[review report](../../../outputs/umr-baseline-g1-soma-uniform-prototype-20261102-02-comparison/index.html),
and [audit](../../../outputs/umr-baseline-g1-soma-uniform-prototype-20261102-02-inspection/audit.json).
The successful run was executed in stages during development; the final combined
command is documented but was not rerun end-to-end after orchestration changes.

The experiment resolves feasibility of this explicit source route, not its
product contract or motion-quality acceptance. User visual acceptance remains
pending. Fitted joints and raw BVH joints differ slightly; their equality is not
an appropriate invariant. Native fitted-forward repeatability and mesh encoding
need separate error budgets, recorded with the effective runtime. These findings
inform the open source, preparation, inspection and acceptance design questions.
No product integration, physical feasibility or broader SOMA support is claimed.
