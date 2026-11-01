# 15 — Bundle the current Astro robot in root assets

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Context

User requested a dedicated project-root `assets/` directory and the latest Astro
from `/workspace/notAnyrobot/menagerie_x` as a built-in robot. That path resolves
to `/data/workspace/notAnyrobot/menagerie_x`; its clean local HEAD is
`8e3f382f28831331c448c9d62cd197140da63c65`. The maintained default is Astro P2
with 29 hinges, original fixed hands and shared foot/neck collision submodels.

## Scope

Copy the default robot's exact local source closure into `assets/robots/astro_p2/`
with its source revision, per-file hashes and upstream license/notice files.
Add the Astro P2 card to the existing local asset library and support its named
T-pose, import and preview through the existing immutable managed-asset interface.
Keep any compatibility conversion owned, bounded and reproducible. Preserve the
source checkout, historical robot definitions, experiment cohorts and UMR pins.

## Acceptance criteria

- The bundled model imports without the `menagerie_x` or UMR checkout; the
  configured independent robot compiler remains an explicit prerequisite.
- Preserve all 37 meshes and original XML files; reject missing/changed/escaping
  snapshot files. Source refresh refuses local drift and existing destinations.
- Named-pose values remain within compiled limits; root translation/quaternion
  conventions remain explicit. Add/drag uses the existing immutable draft flow.
- Resolve latest source collision attachments without weakening ordinary uploads
  or the strict importer. Native source/derived representation checks cover all
  named bodies, joints, geom transforms, inertias, masks and collision ownership.
- Serve an actual model thumbnail; record source/derived hashes, update command,
  tests and limits. No learned-artifact or motion-quality claim follows.

## Validation

Pure snapshot preservation/failure tests; public Studio/HTTP import, pose and
preview; source versus derived model checks in existing MuJoCo 3.3.7 and source
MuJoCo 3.11.0 runtimes; applicable owned pure/JavaScript/static checks, documentation
links and whitespace. No GPU training/retargeting is required for this asset change.

## Answer

Added the self-contained 20 MiB default Astro snapshot and built-in card, preserving
44 original source files, hashes and licenses at revision
`8e3f382f28831331c448c9d62cd197140da63c65`. The owned geom-only attachment
conversion retains source bodies, compiler settings and collision ownership;
ordinary imports retain their supported-element restrictions.

Public HTTP/import, idempotency, immutable pose revision, named T-pose and browser
preview passed with 29 controls and no console errors. Native model/frame parity
passed at 1e-12 absolute tolerance in MuJoCo 3.3.7 and 3.11.0 separately. All 41
pure/JavaScript and seven robot-static suites passed; focused Astro checks also
cover local licenses and unchanged-source/escaping-file failures.

[Acceptance and provenance](../../../experiments/studio-astro-builtin-20261101/README.md)
record commands, runtimes, hashes and limits. No native pipeline stages ran;
source checkout, old definitions and external pins remain unchanged.
