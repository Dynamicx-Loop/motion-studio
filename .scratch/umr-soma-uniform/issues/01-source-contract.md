# Represent SOMA motion and fitted-source readiness

Status: open
Type: grilling
Labels: wayfinder:grilling
Assignee: none
Map: [BONES-SEED uniform support in Local Studio](../map.md)
Blocked by: none

## Question

What small source contract represents an immutable BONES-SEED uniform BVH and
its independently selected fitted reconstruction, while preserving existing
SMPL-X records and allowing skeleton preview before model/fit assets are ready?

Decide source identity versus reconstruction identity, readiness transitions,
asset registration and actionable failures. The user's no-fallback and
skeleton-preview policies are fixed inputs, not questions to reopen.

## Evidence

- [MotionAsset and import](../../../motion_studio/studio/_motion.py) currently
  require SMPL-X fields, weights and a normalized NPZ.
- [Integration trace](../../../docs/umr-soma-boneseed-integration.md) distinguishes
  uniform BVH motion, the verified shared fit and SOMA runtime assets.

## Comments

Recommended starting point: explicit SMPL-X/SOMA source variants with only common
timing/provenance fields shared; separate source validity from fitted readiness.
This is a proposal, not a settled schema or an instruction to implement it.
