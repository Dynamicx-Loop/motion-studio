# Keep SOMA preview and retarget inspection faithful to the source

Status: open
Type: grilling
Labels: wayfinder:grilling
Assignee: none
Map: [BONES-SEED uniform support in Local Studio](../map.md)
Blocked by: 01

Depends on [Represent SOMA motion and fitted-source readiness](01-source-contract.md).

## Question

What contracts let skeleton preview, fitted mesh preview, binding inspection and
saved-motion replay share the same source interpretation, without requiring
fitted assets merely to view a valid skeleton?

Decide hierarchy and moving-anchor metadata, axes and timing representation,
derivative identity/versioning, and the UI's presentation of readiness and source
semantic labels versus robot body ownership. Identify preserved viewer contracts.

## Evidence

- [Skeleton preview worker](../../../motion_studio/integrations/_umr_source_preview_worker.py)
  currently assumes the SMPL-X hierarchy.
- [Mesh preview worker](../../../motion_studio/integrations/_umr_source_mesh_worker.py)
  and [human replay](../../../motion_studio/integrations/_umr_studio_human.py)
  assume SMPL-X source interpretation.
- [SOMA experiment replay](../../../experiments/umr-baseline-g1-somax-20261102/human_replay.py)
  and [replay audit](../../../experiments/umr-baseline-g1-somax-20261102/audit_replay.py)
  provide tested evidence for the named moving `Hips` anchor; stationary `Root`
  must not be treated as the moving body anchor.

## Comments

Recommend reusing the existing geometry/barycentric/rigid replay formats where
their actual contracts fit SOMA. Skeleton and fitted-surface previews need explicit
labels because they can differ slightly; neither may silently stand in for the other.
