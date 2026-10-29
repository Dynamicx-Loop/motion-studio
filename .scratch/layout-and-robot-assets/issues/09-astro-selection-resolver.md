# 09 — Resolve a pinned Astro 29 selection through an owned interface

Status: resolved
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

Claimed in isolated `/tmp/motion-studio-layout-ticket09` on `codex/layout-assets-09`; ancestor `bbd6dac8f80ca63e6a7267fa0db4a4b54ba589c0` verified.

## Answer

Implemented `motion_studio.robots.resolve_robot(definition_id, representation,
pose, source_roots, *, definitions_root=None)` with frozen selection, joint,
source-file, root-pose, convention and provenance records. Arrays/collections are
tuples; source paths are immutable `Path` values. See
[the public contract](../../../robots/README.md) and
[Astro edition notes](../../../robots/astro_p2_29dof/README.md).

The small schema-v1 Astro definition pins menagerie_x commit
`d2070956558ffbf9226dcf74017d40740724d8d8`. Each representation selects exactly
its original model and 35 referenced meshes, plus four separately hashed source
records (`SOURCE.json`, `robot.yaml`, `MJCF.md`, `mjcf-conversion.json`). All
required bytes were independently compared to the pinned committed blobs; no
models/meshes were copied into Motion Studio. Assembly-wide license coverage
remains explicitly unknown; source-record modifications and conversion details
are preserved, with no inferred redistribution rights.

Static selection validates both current and committed required bytes, exact
source commit, XML dependency closure, native joint names/order/types/axes/limits,
application order, right-handed axes, root frame/kind and complete named poses.
URDF root encoding is `unencoded`; MJCF has a `free` root. Root XYZ metres/wxyz
unit quaternion are separate from scalar radians. `zero` is complete joint-zero;
`tpose` preserves the existing complete Astro configuration values and its hash.
Explicit base/overlay pose expansion supports the next Dex3 slice. Unknown,
missing, duplicate, nonfinite, bool or out-of-limit pose values fail. Errors also
cover missing/drifted source files, uncommitted wrappers, unsupported formats,
path traversal/escaping links and incompatible model metadata. No runtime files
are generated or source files changed. Selection identity includes definition,
representation and expanded selected-pose semantics, independent of machine paths;
unrelated generated files do not enter it. Adapter-specific configuration and
writable preparation remain outside resolution.

Validation on 2026-10-29:

- Red/green public-seam fixture slices ran under system Python. The focused suite
  finishes with 12 tests: relocation/immutable results, source/hash/commit drift,
  missing include/mesh, uncommitted closure, duplicate fields, path escape,
  unsupported representation, independent joint metadata/order, pose limits and
  malformed values, overlays/cycles and explicit representation restrictions.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_robots.py`:
  12 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py`: root pure-tier check passed
  (8/8 selected pure suites) after incorporating integration tip `f0314c54e58f98d009ff179e06c48555a50cb14a`.
  Unselected external/saved-evidence/JavaScript tiers are not runtime validation.
- Real read-only selection: URDF/MJCF × zero/T-pose all resolve 29 joints and
  40 verified files. Application order and T-pose values were independently
  checked against `robot.yaml` and `configs/umr/astro_p2_29dof.json`; all selected file hashes were
  rechecked and menagerie Git status stayed byte-for-byte unchanged.
- `git diff --check` and documentation relative-link/path review passed.

No simulator/representation-pair check was run by this static resolver slice;
`runtime_validation='unverified'` is explicit for every result. Ticket 11 owns
shared consistency validation. No kinematic equivalence, dynamic feasibility,
physical calibration, fresh baseline or GPU result is claimed.
