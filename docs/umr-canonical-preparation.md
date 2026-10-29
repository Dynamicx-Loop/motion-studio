# Canonical UMR preparation

`motion_studio.integrations.umr_canonical.prepare_canonical_comparison` prepares a
fresh canonical comparison cohort from an explicit robot definition, MJCF, named
pose, SMPL-X clip, actor-shape evidence and neutral model files. It returns frozen
`PreparedCanonicalComparison(model, config, inputs, receipt)` paths. The public
module uses the standard library; upstream imports remain in an explicitly
selected independent interpreter.

This operation creates **prepared-only** inputs. `execution_readiness` is always
false. It generates no correspondence dataset, learned slots, checkpoint or
retargeted motion. Source format, actor-shape agreement, source FPS/conventions,
training, CUDA and numerical compatibility remain unverified. Preparation and a
CPU compile do not establish dynamic feasibility or motion quality.

```python
from pathlib import Path
from motion_studio.integrations.umr_canonical import (
    CanonicalInputs, SamplingSettings, UMRRuntime, prepare_canonical_comparison,
)

result = prepare_canonical_comparison(
    'astro_p2_43dof_dex3_1', 'mjcf', 'tpose_fist',
    CanonicalInputs(
        clip=Path('/data/my-inputs/motion_actor_smplx.npz'),
        shape=Path('/data/my-inputs/actor-shape.json'),
        model_files=(Path('/data/my-models/SMPLX_NEUTRAL.pkl'),),
        fps=90.0, sequence_key='motion_actor_smplx',
    ),
    Path('/data/my-runs/explicit-fresh-cohort'),
    {'menagerie_x': Path('/data/workspace/notAnyrobot/menagerie_x')},
    settings=SamplingSettings(num_points=4096, seed=0),
    runtime=UMRRuntime(
        Path('/data/workspace/motion_studio/externals/UMR'),
        Path('/data/workspace/motion_studio/externals/UMR/.venv/bin/python'),
    ),
)
```

The thin CLI is `python3 scripts/prepare_umr_canonical.py --help`. It requires
`--canonical`, `--robot`, `--representation mjcf`, `--pose`, `--source KEY CHECKOUT`,
`--clip`, `--shape`, repeated `--model-file`, `--fps`, `--sequence-key` and
`--destination`. Source keys are defined in [robot definitions](../robots/README.md).
There is no implicit robot, representation, pose or historical asset fallback.

`runtime=None` records backend/config/environment prerequisites as unverified.
Supplying `UMRRuntime(checkout, python)` requires official UMR revision
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`, no tracked-source modifications, an
existing interpreter and metadata for MuJoCo, NumPy, Torch, SMPL-X and trimesh.
The adapter hashes tracked Python/JSON code/config, the interpreter, package
versions and an empty tracked patch. It copies those code/config bytes as evidence;
it does not execute copied upstream scripts or install dependencies. The prepared
config is an override for the copied pinned `backend/humanoid_retarget_defaults.json`;
its existence is not permission or readiness to run the numerical pipeline.

All selected model/includes, meshes, materials, notices and source records are
copied under the fresh run. Original copied bytes remain intact. A separately
named derived XML expands includes, rebases asset references to run-local copies
and encodes the explicit XYZ/wxyz root pose. UMR receives complete scalar pose
values by validated **native joint names**; the receipt separately records
application order, which differs for Dex3. No URDF conversion, mesh regeneration,
keyframe selection or source modification occurs. Free MJCF roots are required.
Retarget-specific joint-limit overrides are not inferred from an official G1 run.

The adapter records metre/radian/Z-up robot conventions, the SMPL-X-to-robot
matrix, declared native clip FPS, preservation of all clip bytes, and no trimming
or resampling. `auto` geometry selection follows pinned UMR behavior: prefer
noncontact visual meshes outside group 3 and floor/world geoms; fall back to
nonfloor meshes, then supported primitives when needed. This is not a collision
geometry equivalence claim. Centering is `body:waist_yaw_link` for canonical G1,
`body:pelvis` for Astro, and `spine1` for the source. Sampling uses first-hit exterior
surfaces, explicit count/oversampling/occlusion distance and seed. Shape evidence
is copied and hashed; the clip remains the backend source of template betas/gender.

Destinations resolving into selected source roots, input asset directories or
external checkouts (including symlinks) are refused. Existing destinations,
required-source drift and unsupported claims fail before run creation. A later
copy/derivation/drift failure retains `preparation.json` with `state='failed'`.
A failed run cannot resume: use a fresh destination. Source inputs and historical
artifacts are preserved.

## Representation claims

Standalone MJCF preparation asserts no URDF parity. To require a representation
claim, pass a current `compare_representations` report and `required_claims`, or
repeat CLI `--require-claim NAME` with optional `--comparison-python`. The adapter
checks the report's exact definition, pose coverage, selection identities, source
hashes and policy hash, then calls `require_supported` for the requested names.
Global report status is never used as a parity guard. `collision_policy` can
accept documented refinements and never establishes `collision_geometry_equality`.
Astro named-frame findings can pass while inertial findings remain incompatible;
G1's incompatible pair does not prohibit standalone pinned MJCF preparation.

## Learned artifact compatibility

`require_cache_compatible(prepared_receipt, artifact, metadata, *, stage)` accepts
only explicit paths and `stage='dataset'`, `'slots'` or `'checkpoint'`. There is no
filename search, fallback checkpoint or automatic reuse. Producers must record a
complete sidecar after finishing an artifact:

```json
{
  "schema_version": 1,
  "stage": "checkpoint",
  "fingerprint": "<preparation.json fingerprints.checkpoint>",
  "artifact_sha256": "<SHA-256 of completed artifact bytes>",
  "complete": true
}
```

The guard verifies the preparation schema/state, current adapter version/code,
semantic identity, stage fingerprint, all prepared file hashes, sidecar stage and
artifact SHA-256. Missing, incomplete, malformed, edited or incompatible evidence
raises `CanonicalPreparationError`. Resolver failures use `RobotSelectionError`;
I/O errors retain useful path/cause context. Artifact producers and future
execution operations must use this guard before reuse. This preparation route
never loads learned artifacts itself.

Dataset identity includes the complete target closure and edition, pose,
representation, native/application order, visual/collision/centering policy,
source clip/shape/model bytes, declared FPS and sequence, sampling settings/seed,
conversion, adapter version/code and pinned backend/environment identity. Slots
and checkpoint fingerprints additionally bind stage and training defaults/seed.
Changing any dependency invalidates incompatible learned artifacts and requires a
new cohort/retraining. Supplied source, interpreter, input and output **paths** are
excluded from semantic identity; relocating identical content preserves it.
Operational locations and generated-file hashes remain in the receipt for audit.
Matching fingerprints and bytes establish metadata compatibility only; tensor
shapes, learned semantics and numerical runtime compatibility still require
separate validation. Existing artifacts without verified metadata are rejected.

The official `reproduce_g1_baseline(output, workspace=...)` operation retains its
signature, pinned bundled G1 assets, run-local full bundle copy and complete
training/retarget behavior. Historical
`motion_studio.integrations.umr_hiphi_control.prepare_legacy_run` and frozen pair
scripts remain separate inventory-sealed preparation/reproduction tools.

Validation: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py`. The pure suite
covers closed copies, pose/native order, relocation, mesh/shape/order/settings
invalidation, exact-claim guards, malformed evidence, source drift, source-link
protection, destination collisions and retained failure receipts. Real CPU smoke
evidence is described in
[the ticket 12 record](../experiments/layout-and-robot-assets-evidence/ticket12/README.md).
