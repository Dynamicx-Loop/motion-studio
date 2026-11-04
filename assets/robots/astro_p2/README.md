# Astro P2 built-in snapshot

Motion Studio's **Astro P2** card (`astro`) uses the default fixed-hand,
29-joint body from `menagerie_x` revision
`8e3f382f28831331c448c9d62cd197140da63c65`, recorded on 2026-11-01.
The source checkout was clean. The user-provided
`/workspace/notAnyrobot/menagerie_x` resolves on this host to
`/data/workspace/notAnyrobot/menagerie_x`.

- `astro_p2.xml`, `foot_collisions.xml`, `neck_handle_collisions.xml` and all
  37 referenced meshes under `assets/` preserve the source bytes unchanged.
- `astro_p2_studio.xml` is an owned import derivative. It expands only the
  geom-only foot/neck model attachments, preserving named bodies, geom ownership,
  name prefixes and compiler settings. Studio's ordinary importer retains its
  existing confinement and supported-element checks.
- `manifest.json` records the repository/revision, source and derived SHA-256
  values, metre/radian/Z-up conventions, root quaternion wxyz and complete named
  T-pose. Root placement is unchanged; the viewport floor offset is display-only.

The snapshot includes **52 collision geoms and 37 visual mesh geoms**, with one
floating root (`nq=36`, `nv=35`). The named T-pose uses shoulder rolls ±π/2 and
both elbows π/2, with other hinges zero, within compiled limits. The articulated
43-joint Dex3-1 alternative is not included in this snapshot.

## Terms

The default model and Astro meshes are covered by the upstream Apache-2.0
[LICENSE](LICENSE). The unchanged [LICENSING.md](LICENSING.md) explains family
provenance and separate third-party terms. [LICENSE.Unitree](LICENSE.Unitree) and
[LICENSE.Menagerie](LICENSE.Menagerie) are preserved with it; retaining these
notices does not import the articulated-hand or retired scene assets. Links in
the upstream licensing notes describe that source repository's full family.

## Reproduce or update

From the Motion Studio root, select a fresh destination:

```sh
python3 -B scripts/import_astro_assets.py \
  --source /data/workspace/notAnyrobot/menagerie_x \
  --output outputs/astro-snapshots/<fresh-id>
```

The command refuses existing destinations, source edits differing from the
selected HEAD, unsupported collision-model semantics and escaping dependencies.
Review the new snapshot, its terms and native checks before replacing the
built-in in version control. The command changes neither upstream sources nor
old experiment definitions. Historical G1/UMR inputs remain separately pinned.

Regenerate the card's visual-only T-pose thumbnail with
`python3 -B scripts/build_studio_thumbnails.py astro`. It uses the existing
independent robot compiler and Pillow/NumPy; no native job is started.

The [acceptance record](../../../outputs/artifact-archives/experiment-reset-20261104/experiments/archive/studio-astro-builtin-20261101/README.md)
records public import, HTTP, named-pose and native representation checks. These
checks establish the stated representation parity, not motion quality,
controller stability, contact performance or dynamic feasibility.
