# Astro P2 with sample Dex3-1 hands

Pinned source is menagerie_x `d2070956558ffbf9226dcf74017d40740724d8d8`.
The source remains authoritative for meshes, assembled model and notices;
resolution checks exact model/mesh/provenance hashes and committed bytes.
`LICENSE.Unitree` applies to the bundled vendor hand component; full assembly
and mesh redistribution permission remains unknown. No asset is copied here.

Application order is the 43 names in pinned `joint-order.json`, independently
recorded in robot.json. Native MJCF traversal puts left fingers before the right
arm, so map by name. Seven free-root values are separate XYZ/wxyz, never hinges.
All scalar coordinates and physical ranges use radians. Source finger axes and
mirrored signs are retained; controller limits/calibration are not inferred.

Select `zero` or `open` for complete body-zero/open hands, `tpose` for the
existing body T-pose/open hands, `fist` for explicit zero-body plus the 14-joint
source overlay, or `tpose_fist` for explicit T-pose plus that overlay. `base`
merges named child joints over the complete base, inheriting the root pose.
The source fist SHA-256 is
`65aa714e64a642058237351515951e3840982d0692cc04c079356e1eb0e0ed7b`.
Thumb opposition is zero; left thumb bends +0.9/+1.3, right -0.9/-1.3;
left index/middle -1.55/-1.7, right +1.55/+1.7. These are sample poses without
standing clearance, grasping, contact, dynamics or hardware calibration claims.

MJCF's `fist` keyframe is explicitly loaded by its viewer; ordinary MuJoCo reset
uses scalar zero. Motion Studio never silently selects the viewer default.
The pinned MJCF intentionally has different collisions from the earlier URDF:
see [consistency.json](consistency.json) for enumerated hash-bound refinements and
the separately hashed upstream MJCF.md/review records for exact dimensions.
Regenerating from URDF would erase final collision refinements and the keyframe.
Neither model is regenerated here. Visual and collision findings stay separate.

Use the [shared read-only operation](../README.md#bounded-representation-checks)
for claims at declared poses. Current frames pass 1e-6 m/rad, total mass matches
41.69666115 kg, but aggregate inertia fails the conservative 1e-6 kg m² bound.
Static selection stays valid; this does not assert complete pair equivalence.
