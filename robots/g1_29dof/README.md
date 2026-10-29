# G1 29 DoF comparison selection

Edition 1 explicitly selects pinned UMR `assets/g1/g1_29dof.xml` or
`assets/g1/g1_29dof.urdf`. Each closure contains the model, 36 OBJ meshes and
`logo_link.mtl` (38 files), plus separately hashed UMR LICENSE and official
example configuration. No source model bytes are committed here. Asset licensing
coverage remains unknown beyond the recorded UMR notice.

```python
from motion_studio.robots import resolve_robot
selection = resolve_robot('g1_29dof', 'mjcf', 'tpose', {'UMR': '/path/to/UMR'})
```

`zero` and `tpose` are complete 29-joint scalar poses in native traversal order,
metres/radians, Z-up/X-forward/Y-left, separate pelvis XYZ and wxyz root pose.
The T-pose expands omitted joints to zero and retains the example's exact
`1.57079632679` calibration numbers. Zero root translation is a model origin,
not a standing height. Retarget-only limit overrides remain backend settings.

The comparison identity includes the explicit definition, representation and
pose. Equal source bytes do not merge this selection with official reproduction.
Changing geometry, frames, limits, ordering, provenance or pose changes identity.

## Candidate inventory and consistency limits

The shipped spherehand URDF/XML replaces the hands; largebox XML and 27-DoF
left-racket adaptation are separate candidates. None is selected. Generated
`*.floating_mjcf.xml` files and local `reference`/`reconverted` wrappers are not
committed comparison inputs. Menagerie G1 is another edition and is not a fallback.

[Consistency observations](consistency-observations.json) record exact model
hashes, all named joint types/axes/limits, separate visual/collision inventories,
and prior controlled CPU frame measurements at `zero` and `tpose`. These source
observations used MuJoCo 3.11.0 with explicit URDF floating pelvis,
`discardvisual=false`, `fusestatic=false`, `strippath=false`,
`inertiafromgeom=false`. They are bounded inspection evidence, not a newly run
shared validator report. Ticket 11 supplies the common runtime operation.

The pair is **incompatible** with a parity claim at the specified 1e-6 m/rad
thresholds: wrist-roll limit rounding differs by 2.054e-6 rad; observed frame
orientation errors are about 1.4568e-6 rad. Five fixed URDF frames are absent from
MJCF; controlled-import totals are 35.14914202 versus 35.525142 kg. Named hinges
and axes agree, but these other differences cannot be erased by matching names.
Visual/collision equivalence remains **unverified**, with no broad exceptions.
Neither model was edited and tolerances were not widened.

Standalone MJCF compilation succeeded using the existing UMR MuJoCo 3.3.7
runtime, only on a fresh full run-local bundle copy: nq=36, nv=35, nbody=51,
mass=35.525142 kg. Source bundle hashes matched before and after. Local ignored
receipt: `outputs/implementation/layout-and-robot-assets/ticket10/compile.json`
under `/data/workspace/motion_studio/` (stable local receipt; model copies remain
in the ticket worktree). No simulation stepping, training, retargeting or GPU
validation was performed. Historical saved reproduction remains frozen evidence.

## Official reproduction remains independent

`reproduce_g1_baseline(output, *, workspace=...)` retains its original pin,
configuration/calibration and full G1 bundle copy. It never reads this catalog.
Its generated XML stays under the fresh run. Public help requires neither this
catalog nor scientific dependencies. Fixture tests remove/redirect the isolated
package's actual default catalog and verify selected XML, complete bundle bytes,
calibration, full motion input and preservation through the public operation.
Only external filesystem/Git/process boundaries are replaced by fixtures; those
checks do not establish that a scientific run passes.
