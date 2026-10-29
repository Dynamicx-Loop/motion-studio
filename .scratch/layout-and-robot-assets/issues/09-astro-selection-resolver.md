# 09 — Resolve a pinned Astro 29 selection through an owned interface

Status: ready-for-agent
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 01, 02
Dependencies: [01 preservation](01-preservation-inventory.md), [02 checks](02-test-discovery.md)

## Context

menagerie_x already owns the Astro URDF/MJCF, meshes, source records and
conventions. Motion Studio repeats an absolute XML path and T-pose in UMR config.
The source checkout contains generated untracked wrappers; these cannot become
canonical merely because they share the asset directory.

## Outcome and scope

Implement a versioned definition/pose contract and one public typed robot
selection operation, exercised end to end by Astro P2 29 DoF. Use the proposed
robots/astro_p2_29dof metadata and motion_studio/robots ownership unless a
demonstrated simpler organization is documented. Keep original assets upstream.

## Acceptance criteria

- Definition selects the inspected menagerie commit and exact URDF/MJCF/mesh/
  include closure by hash, with provenance/notices, intentional modifications,
  representation, units, axes, root convention and 29-name application order.
  Preserve source records; do not infer blanket asset license rights.
- Named complete zero/T-pose definitions derive from inspected bundle/config
  values, specify radians and root handling and reject unknown/missing/duplicate,
  nonfinite or out-of-limit joints. Do not confuse joint zero with standing height.
- Public operation accepts definition/representation/pose and local source roots;
  returns immutable typed paths, verified closure/identity, ordered pose/joints,
  conventions and validation findings. Source-root mapping supports current
  menagerie location without moving it or extending bootstrap arbitrarily.
- Missing assets, changed required hashes/commit, path escape and unsupported
  representations fail with actionable errors. No downloads, heavy imports,
  generated XML, simulator launch or input mutation during static resolution.
- Deterministic identity covers content and semantics while remaining independent
  of machine-specific root paths. Unrelated generated files do not affect it.
  Runtime URDF/MJCF check status is distinct from static schema validity.
- Small public-interface fixtures join root tests. Preparation of writable
  run-local copies remains an adapter responsibility, not a resolver side effect.

## Validation

Resolve the real pinned Astro bundle read-only and independently verify selected
hashes/joint order against source records. Test a relocated fixture source root,
missing include/mesh, changed bytes, malformed/duplicate pose fields, order/limit
errors and invalid path traversal. Assert no output files or source changes.
Run a focused representation check in an existing compatible runtime if present;
otherwise report runtime validation unverified, not model equivalence.

## Comments

Planning only. No generic asset package manager or second copy of mesh/model
maintenance is needed; the first real selection determines the minimal schema.
