# Prepare the fitted SOMA source without implicit fallback

Status: open
Type: grilling
Labels: wayfinder:grilling
Assignee: none
Map: [BONES-SEED uniform support in Local Studio](../map.md)
Blocked by: 01

Depends on [Represent SOMA motion and fitted-source readiness](01-source-contract.md).

## Question

How should the owned UMR adapter prepare the explicitly selected uniform fit and
BVH for pinned native UMR, prove the resolved route, and capture all dependencies
needed for reproducible stage execution and invalidation?

Decide the prepared-source result, run-local layout versus explicit native entry
points, and ownership of family/fit resolution, topology, semantic transfer and
coordinate conventions. Identify which existing stages can remain unchanged.

## Evidence

- [Native family/fit discovery](../../../externals/UMR/scripts/soma_source.py)
  recognizes `motions_uniform`, not this dataset's `raw/uniform` path. A missing
  discovered fit can silently retain the generic source format.
- [Stage configuration](../../../motion_studio/integrations/_umr_stage_worker.py),
  [validation](../../../motion_studio/integrations/_umr_stage_validation.py), and
  [binding](../../../motion_studio/integrations/_umr_stage_binding.py) assume SMPL-X.
- [Stage identity](../../../motion_studio/studio/_execution.py) already provides
  reuse/invalidation machinery; extend its inputs rather than add another cache.

## Comments

Recommended invariant: require `soma_bvh_boneseed_uniform`, `soma_uniform`, exact
selected fit identity, and matching template/motion face ordering before sampling.
Include model/overlay/transfer assets and reconstruction settings in identity.
A changed fitted surface requires fresh correspondence and bindings. A run-local
recognized dataset layout is a candidate adapter implementation, not yet selected.
