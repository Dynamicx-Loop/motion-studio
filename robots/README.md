# Robot definitions

Motion Studio owns small versioned selections and poses here. Robot models,
meshes and original notices stay in their upstream checkout. No model is fetched,
regenerated or copied by selection. These definitions are comparison inputs;
original UMR G1 reproduction continues to use its own bundled assets.

```python
from pathlib import Path
from motion_studio.robots import resolve_robot

selection = resolve_robot(
    'astro_p2_29dof', 'mjcf', 'tpose',
    {'menagerie_x': Path('/data/workspace/notAnyrobot/menagerie_x')},
)
# selection.model_path: verified existing source XML
# selection.joint_names / pose_values: application-order names / scalar radians
# selection.root_pose: separate translation in metres and unit wxyz quaternion
```

`resolve_robot(definition_id, representation, pose, source_roots, *,
definitions_root=None)` is the only selection operation. `definitions_root`
selects a catalog explicitly, including small isolated test catalogs. The default
is this directory. Results and their nested records are frozen dataclasses;
collections are tuples. `RobotSelectionError` identifies an unavailable or
incompatible requirement and retains the underlying error where relevant.

The source root must be the named checkout root at the exact commit. Required
files must match both the recorded SHA-256 and committed bytes. Resolution rejects
missing files, changed hashes, changed commits, unsupported representations,
source-path escapes (including escaping symlinks), duplicate JSON fields and
incomplete source closures. Unrelated dirty or generated files are ignored.
A source checkout at an older pin plus local required-file patches is not an
accepted edition; preserve a patch separately before defining a new source edition.

The identity hashes the complete definition, selected representation and expanded
named pose, including provenance, joint ordering and geometry hashes. It excludes
supplied absolute source/catalog paths. Relocating identical source bytes leaves
identity unchanged. Changing other representation metadata also changes identity;
this conservative edition-level invalidation is intentional. Adapters add their
own conversion, sampling, actor and configuration fingerprints.

## Schema version 1

Each `robots/<definition_id>/` has `robot.json` and `poses.json`. IDs contain
lowercase letters, digits, underscores and hyphens. Unknown schema versions fail.
The Astro files are the complete concrete example; there is no package registry
or dependency installer behind this format.

`robot.json` contains:

| Field | Contract |
| --- | --- |
| `schema_version`, `id`, `version` | Schema `1`, directory ID and positive integer edition. |
| `source` | `key` for the supplied root map, upstream `repository`, full `revision` commit. |
| `provenance` | Explicit `license_coverage` (including `unknown`), optional `license_note`, list of intentional `modifications`, and hashed `files` for source records/notices. |
| `conventions` | `length_unit=metre`, `angle_unit=radian`, signed cardinal `up_axis`, `forward_axis`, `left_axis` forming a right-handed frame; named `root_frame`, `root_translation_unit=metre`, `root_quaternion_order=wxyz`. This describes the selection encoding; URDF itself supplies no quaternion encoding. |
| `joint_order` | Application scalar-joint names, each present exactly once. Free-root coordinates are excluded. |
| `representations` | Explicit `urdf` and/or `mjcf` records described below. |

Each representation has a source-relative `model`, `root` (`unencoded` for a
URDF root link; `free` or `fixed` for MJCF), `files`, and `joints`. Each file has
`path`, `sha256` and descriptive `role` (model, mesh, include, material or texture).
The exact representation closure includes model/include references, meshes and
OBJ material-library dependencies. Source-record/notice files are separately
listed under provenance. No path may escape the supplied source root.

`joints` follows native model traversal order and records `name`,
`kind=revolute`, unit `axis=[x,y,z]`, and scalar `lower`/`upper` radians. The
resolver inspects named revolute URDF joints or MJCF hinges and compares the
metadata to the actual XML. Application order can differ from native order;
selection maps by validated names. Other scalar joint types, inherited MJCF
joint defaults and implicit degree conversion are outside this initial contract;
MJCF files must specify radian compiler angles and explicit hinge ranges.

`poses.json` contains `schema_version=1`, `angle_unit=radian` and a `poses`
object keyed by name. Each full pose supplies `joints` as a complete name-to-number
map, `root_translation=[x,y,z]`, `root_quaternion=[w,x,y,z]` and a nonempty
`root_handling` description. Optional fields are `description`, `provenance`,
`representations` (allowed representation names), and `base`. With an explicit
`base`, child joint values override base values by name; root fields inherit
unless supplied. Bases must exist and be acyclic. This supports a hand overlay
without treating an incomplete hand vector as a whole-body pose. Unknown or
missing names, duplicate fields, nonfinite/bool values and model-limit violations
fail. Root translation is finite and quaternion has unit norm within `1e-9`.

The scalar zero pose does not imply standing height, ground contact, calibration,
or dynamic feasibility. Model joint limits are separate from any concrete
retargeter's narrower solve-time constraints.

## Validation limits

`static_validation='validated'` means pinned bytes, closure, joint metadata,
conventions and selected pose passed the checks above. `runtime_validation` is
`unverified`: resolution never imports a simulator, launches a process running a
model, writes XML, installs dependencies or mutates inputs. Compiling a model,
comparing URDF/MJCF frames/inertia/visuals/collisions and preparing writable
run-local copies are separate concrete adapter operations. Static selection is
not a representation-parity certificate.

Run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py` for the automatically
discovered pure fixture tests. A read-only real-source smoke check is the example
above with `urdf`/`mjcf` and `zero`/`tpose` selected explicitly.

## Bounded representation checks

`compare_representations(definition_id, source_roots, *, poses=('zero','tpose'),
runtime_python=None, definitions_root=None)` returns a frozen `ConsistencyReport`.
It reuses verified selections; no runtime means runtime claims remain unverified.
An explicit existing MuJoCo interpreter runs a separate CPU worker, compiling
original MJCF and an in-memory URDF with absolute mesh paths, explicit compiler
settings, and a massless `world` link/floating joint to the declared root. No model
files are rewritten and no simulation is stepped. XYZ/wxyz root values and scalar
joints are assigned explicitly by name at every pose; keyframe defaults are ignored.

`report.findings` contains exact `check`, `status`, `detail` records. `supports(name)`
and `require_supported(names)` guard **only** named claims; unknown names fail.
Callers must state the checks their comparison needs. Standalone MJCF preparation
requires no assertion that a URDF pair is equivalent. Report `schema_version=1`
records selection identities, source hashes, policy hash, runtime and tolerances.

The declared summary checks are `joint_metadata`, `joint_order`, `named_frames`,
`inertial_totals`, `visual_geometry_equality` and `collision_policy`. Global
`status` summarizes these checks plus pose/representation/runtime failures.
`collision_geometry_equality` is a separate optional finding excluded from that
summary: accepted intentional refinements **never** establish collision equality.
The visual/collision geometry equality scope is compiled body-local type, size,
position, quaternion and mesh name with verified source closure bytes, excluding
world environment geoms. It does not establish rendered surface, material,
contact response, controller, or dynamic equivalence.

Position uses maximum named-body translation **Euclidean distance** in metres;
rotation uses maximum relative rotation angle in radians. Both defaults are
`1e-6`, without per-robot exceptions. Inertial checks measure total mass (kg),
world COM distance (m), and maximum absolute component of the aggregate world
inertia tensor about that COM (kg m²), including rotated principal inertias and
parallel-axis terms at each pose. The initial conservative thresholds are
`1e-6 kg`, `1e-6 m`, `1e-6 kg m²`; these are numerical comparison criteria, not
sensor accuracy or physical equivalence claims. Astro mass totals agree, but
measured aggregate inertia errors slightly exceed this threshold, so the
inertial claim remains incompatible rather than widening the tolerance.

`consistency.json` enumerates narrow accepted collision refinements and binds
both original model hashes, entire representation closures and source revision.
Any unrecognized changed pair cannot use these allowances. Resolver hash/commit
validation still applies before and after the worker. Geometry findings are
separate from frame/joint/inertial findings; no full-pose-space guarantee follows.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py --tier robot-static \
  --robot-python /data/workspace/notAnyrobot/menagerie_x/.venv/bin/python
PYTHONDONTWRITEBYTECODE=1 python3 scripts/compare_robot_representations.py \
  astro_p2_43dof_dex3_1 --source menagerie_x /data/workspace/notAnyrobot/menagerie_x \
  --pose zero --pose tpose --pose fist --pose tpose_fist \
  --runtime-python /data/workspace/notAnyrobot/menagerie_x/.venv/bin/python
```

The explicit `robot-static` tier runs analytic fixture models and reports an
unavailable interpreter/dependency as unavailable. Default pure checks never
import MuJoCo/NumPy. The report CLI emits findings even when incompatible; its
exit code means successful reporting, not certification. Inspect exact claims.
See the committed [measured reports](../experiments/layout-and-robot-assets-evidence/ticket11/README.md).
