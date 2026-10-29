# Experiment: bounded robot representation consistency

Date / author: 2026-10-29 / Motion Studio ticket 11 implementer.

## Objective

Compare pinned URDF/MJCF scalar joints, frames and inertial totals at declared
poses; preserve intentional collision differences without certifying equality.
All source selection and reporting operations are read-only. No clip, GPU,
training, retargeting, model regeneration or dynamics is involved.

## Provenance

- Implementation branch: `codex/layout-assets-11`, integration base `1935afa`.
  `preservation-receipt.json` seals worker/operation hashes and report hashes.
- Astro29 and Dex3: menagerie_x commit
  `d2070956558ffbf9226dcf74017d40740724d8d8`, original local source at
  `/data/workspace/notAnyrobot/menagerie_x`.
- G1: original official UMR asset pair, UMR commit
  `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, local source at
  `/data/workspace/motion_studio/externals/UMR`.
- Each report records complete selected source hashes, expanded selection
  identities, policy hash and runtime. Required files were checked against both
  the pinned Git commit and definition hashes; checked again after the worker.
  Source Git status hashes before/after are unchanged in the preservation receipt.
- Asset permissions remain separately qualified by each robot definition.
  No source model/mesh is committed or redistributed here. Dex3's vendor notice
  does not establish full-assembly licensing.
- Runtime: existing menagerie `.venv/bin/python`, MuJoCo 3.11.0, NumPy 2.4.4.
  CPU forward computation only, `PYTHONDONTWRITEBYTECODE=1`; no packages installed.
- Units: metres, radians, kg, kg m². Z-up/X-forward/Y-left. Root XYZ/wxyz
  separately encoded; scalar application order maps to native order by name.
- Source method: pinned MJCF.md, joint-order.json, fist-pose.json and final
  mjcf-fist-review.json; prior conversion record is intentionally older than the
  final model. The source importer convention is reproduced in report findings.
- API reference fetched with Context7 before implementation:
  [MuJoCo Python model loading and named access](https://mujoco.readthedocs.io/en/stable/python.html),
  [mj_forward](https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html).

## Reproduction

From any checkout of this implementation, use a fresh result destination if
saving output. Canonical source paths below are read-only inputs.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py --tier robot-static \
  --robot-python /data/workspace/notAnyrobot/menagerie_x/.venv/bin/python
PYTHONDONTWRITEBYTECODE=1 python3 scripts/compare_robot_representations.py \
  astro_p2_29dof --source menagerie_x /data/workspace/notAnyrobot/menagerie_x \
  --runtime-python /data/workspace/notAnyrobot/menagerie_x/.venv/bin/python
PYTHONDONTWRITEBYTECODE=1 python3 scripts/compare_robot_representations.py \
  astro_p2_43dof_dex3_1 --source menagerie_x /data/workspace/notAnyrobot/menagerie_x \
  --pose zero --pose tpose --pose fist --pose tpose_fist \
  --runtime-python /data/workspace/notAnyrobot/menagerie_x/.venv/bin/python
PYTHONDONTWRITEBYTECODE=1 python3 scripts/compare_robot_representations.py \
  g1_29dof --source UMR /data/workspace/motion_studio/externals/UMR \
  --runtime-python /data/workspace/notAnyrobot/menagerie_x/.venv/bin/python
```

Runtime fixture tests independently check mass 2.1 kg, worked COM coordinates at
zero and 90° bend, aggregate inertia components, an intentional 0.25 m frame
shift, a physical limit difference, unexplained sphere-radius difference, and
exact-hash collision policy versus equality guards. Pure tests cover static
versus runtime claims and missing/failed runtimes. Existing resolver tests cover
invalid, duplicate, unknown, incomplete, nonfinite and out-of-range named poses.
Real Dex3 smoke resolved both representations at all five named poses, checked
43-coordinate expansion, mirrored thumb signs and different native order.

## Evaluation

Read exact findings in [Astro29](astro29-report.json), [Dex3](dex3-report.json),
and [G1](g1-report.json). Position uses Euclidean distance and rotation uses the
relative rotation angle, both with unchanged 1e-6 m/rad thresholds. Inertial
criteria are absolute 1e-6 kg / 1e-6 m / 1e-6 kg m², the last applied to maximum
aggregate world tensor component about COM. These deliberately conservative
numeric criteria have no physical accuracy or dynamic-equivalence meaning.

- Astro29/Dex3 named frames and scalar metadata pass at sampled poses. Maximum
  observed translation is 2.65731e-7 m and rotation 4.62158e-7 rad.
- Mass totals match exactly: 40.58255359 kg / 41.69666115 kg respectively.
  Aggregate inertia errors are about 1.2–1.3e-6 kg m² and exceed the initial
  absolute bound. `inertial_totals` and global summary remain incompatible;
  no tolerance was widened after observing results.
- Visual compiled descriptions pass the documented bounded check. Collision
  geometry differs and equality fails. Only hash-bound enumerated Astro
  refinements satisfy `collision_policy`.
- G1 reports 35.14914202 versus 35.525142 kg, five missing fixed frames
  (d435/head/imu/logo/mid360), wrist-roll limits differing by 2.054e-6 rad and
  rotation errors about 1.4563e-6 rad. Claims fail individually. The standalone
  MJCF is still a valid selected representation; official reproduction is intact.

## Observations and next step

These measured CPU samples establish only the claims explicitly supported by
this operation. They do not certify arbitrary pose-space, rendering, collision
surfaces, contact clearance, controller compatibility, dynamic feasibility,
grasping or hardware calibration. No simulator integration step or viewer was
run. Callers guard exact required claims, never infer parity from schema success
or a broad status. No upstream edits or regeneration were used to improve results.
