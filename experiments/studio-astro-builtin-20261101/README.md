# Experiment: bundled Astro P2 built-in

Date / author: 2026-11-01 / Codex, user-requested asset integration.

## Objective and cohort

Add the latest local default Astro to root `assets/` and the built-in library.
This is a **prepared-only representation and application acceptance** cohort:
import, pose selection, HTTP and preview. No sampling, learned artifacts,
training, retargeting or simulation stepping. Historical definitions and G1/UMR
inputs retain their original pins.

## Provenance and independent runtimes

Source: `menagerie_x` at clean local HEAD
`8e3f382f28831331c448c9d62cd197140da63c65`,
`/data/workspace/notAnyrobot/menagerie_x/astro_p2/`. The supplied
`/workspace/notAnyrobot/menagerie_x` resolves there. No fetch or external edit.

The [manifest](../../assets/robots/astro_p2/manifest.json) records 44 original
source-file SHA-256 values (37 meshes, three MJCF files, four licensing/notice
files), the owned derivative and complete named pose. Original XML:
`26aa55ba581fd9493635e4ed466c026318f500219d6a712dafc57c3fc4d9b75a`;
derived XML:
`044c82b62db549fcf845db3e74ab198618b302e5a7e8ad1afdf6fe81dd35451b`.
The snapshot occupies about 20 MiB. Astro source material carries its preserved
Apache-2.0 grant; separate family notices remain alongside it. No articulated
hand meshes, motion clips or body-model weights are imported by this addition.

Product compilation: **MuJoCo 3.3.7**, `externals/UMR/.venv/bin/python`.
Independent reference: **MuJoCo 3.11.0**,
`/data/workspace/notAnyrobot/menagerie_x/.venv/bin/python`.
System Python runs the service/pure tests; no packages were changed. Owned source
hashes and evidence are under `outputs/studio-astro-builtin-20261101/`.

## Robot selection and representation

Catalog ID `astro`, **Astro P2**, fixed hands, 29 bounded hinges, floating pelvis,
`nq=36`, `nv=35`, 40 bodies, 37 visual mesh geoms and 52 collision geoms.
The owned derivative expands geom-only foot/neck attachments, preserving bodies,
ownership, prefixes, compiler settings and original XML/mesh bytes. Ordinary
uploads retain their strict importer. Managed provenance preserves originals.
Import works without source checkouts; its configured robot compiler is required.

Metres/radians, Z-up, root quaternion wxyz, compiled joint order. T-pose: shoulder
rolls ±π/2, both elbows π/2, other hinges zero, within limits. Root is unchanged;
floor grounding is display-only. The thumbnail projects visual group 1 only;
the full model/interactive preview retain collisions.

## Processing and learned artifacts

No clip/time conversion, resampling, correspondence reuse or learned cache
validation. Selection uses immutable asset/pose revisions. New geometry has a new
asset identity; no old learned-artifact compatibility claim.

## Reproduction

From `/data/workspace/motion_studio`, select a fresh snapshot destination:

```sh
python3 -B scripts/import_astro_assets.py \
  --source /data/workspace/notAnyrobot/menagerie_x \
  --output outputs/astro-snapshots/<fresh-id>
python3 -B scripts/build_studio_thumbnails.py astro
python3 -B scripts/check.py --tier pure --tier javascript
python3 -B scripts/check.py --tier robot-static \
  --robot-python externals/UMR/.venv/bin/python
/data/workspace/notAnyrobot/menagerie_x/.venv/bin/python -B \
  -m unittest discover -s tests -p test_studio_astro_runtime.py -v
```

Snapshot creation refuses existing destinations/source drift. Review a fresh
snapshot before updating the maintained built-in; it is never overwritten in place.

## Evaluation

- **41/41** pure/JavaScript suites and **7/7** robot-static suites passed. New
  coverage includes five snapshot cases and two Astro native/public cases.
  Focused Astro cases also passed in 3.11.0, including local license serving.
- Original/derived arrays matched at absolute tolerance **1e-12**, zero relative
  tolerance, separately in each runtime: root defaults, body inertias/masses/local
  transforms, joint names/order/axes/ranges, geom transforms/sizes/ownership and
  masks. Named body/geom world frames matched in the T-pose. No cross-version
  bitwise-equivalence claim.
- Actual HTTP import/thumbnail/license, idempotency and immutable r0001→r0002
  pose flow passed. The complete upstream license is byte-checked.
- Browser: fresh `outputs/studio-astro-builtin-20261101/browser-state`, port 8774.
  Astro card, Add robot, rendered T-pose, named pose and 29 controls passed;
  no console errors/warnings or native jobs.
  [Screenshot](../../outputs/studio-astro-builtin-20261101/astro-builtin.png).
- Source checkout remained clean at its revision; historical definitions,
  external pins and unrelated local files were preserved.

## Observations and next step

The default Astro supports selection, pose preparation and preview. Representation
parity is measured; browser appearance is a visual check. Retargeting quality,
contact behavior, controller stability and dynamics were not tested. The 43-joint
articulated-hand alternative is not included.
