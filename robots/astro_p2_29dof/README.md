# Astro P2 29 DoF, edition 1

This selection pins menagerie_x commit
`d2070956558ffbf9226dcf74017d40740724d8d8`. Each representation uses its committed
model and 35 referenced STL meshes. Four hashed source records (`SOURCE.json`,
`robot.yaml`, `MJCF.md`, `mjcf-conversion.json`) preserve application order,
provenance, intentional changes and collision conversion details. No meshes or
models are redistributed here. No assembly-wide asset license was found during
inspection; coverage remains explicitly unknown.

Both application and native scalar orders have 29 joints. The named `zero` pose
sets every scalar hinge to zero. `tpose` preserves the complete existing
`configs/umr/astro_p2_29dof.json` values: shoulder rolls ±π/2 and both elbows +π/2,
with all other joints zero. The pose record retains the configuration hash.
Both poses use the model origin with no standing-height offset; an adapter owns
world placement and calibration.

URDF root handling is `unencoded`; MJCF has a free joint at pelvis. Motion Studio
encodes separately selected root data as XYZ metres and wxyz quaternion. This does
not add a floating joint to the source URDF. The source conversion retains fixed
frames/inertias and converts 39 cylinder-plus-sphere collision assemblies to
capsules. The exact source conversion record is included by hash; static resolver
validation does not establish runtime or collision parity.

See [the definition contract](../README.md) for the operation, schema and limits.
