# Define acceptance of the fitted G1 baseline

Status: open
Type: grilling
Labels: wayfinder:grilling
Assignee: none
Map: [BONES-SEED uniform support in Local Studio](../map.md)
Blocked by: 02, 03

Depends on [Prepare the fitted SOMA source without implicit fallback](02-native-preparation.md)
and [Keep SOMA preview and retarget inspection faithful to the source](03-preview-inspection.md).

## Question

Which observable checks and visual review procedure establish that the complete
Local Studio route correctly reproduces its selected fitted SOMA source and
retargets the full jump-and-land clip to built-in G1?

Specify the fresh experiment contract, numerical tolerances, required artifacts,
regression checks for SMPL-X, and how to record the user's acceptance or defects.
Numerical integrity and visual quality are distinct gates; neither certifies dynamics.

## Evidence

- [Existing comparison](../../../experiments/umr-baseline-g1-comparison-20261102/README.md)
  preserves the generic control; different source clips cannot establish a causal
  ranking of SMPL-X versus SOMA.
- [Stage validation](../../../motion_studio/integrations/_umr_stage_validation.py)
  uses an FPS tolerance smaller than the observed float32 serialization error for
  120.0048 FPS. Define tolerance from the timing contract rather than copy it.
- [Experiment template](../../../experiments/TEMPLATE.md) requires provenance,
  commands, environment, transformations and limitations.

## Comments

Candidates: missing/wrong fit and fallback rejection; source/model hash changes
invalidate dependent results; preserved frames and timestamps; topology continuity;
semantic-label coverage; native source/barycentric and robot rigid replay; finite
qpos, quaternion normalization and joint limits; synchronized visual review of
source/robot motion and both sides of segment bindings. Quantify quality separately
from data integrity and preserve any failure as evidence. No fitted run is claimed.
