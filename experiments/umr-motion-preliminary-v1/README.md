# Preliminary UMR motion smoke test

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

2026-10-23. First 12 seconds of shipped HiPHI Getting_up-get_up_0004, frames
0:1080:3, 360 poses at 30.0003 Hz. Four successful offline solves: G1/Astro Dex3-1,
spine1/bbox50. Source motions and static-binding findings were preserved.

Frozen inputs/config hashes are in inputs.json; exact commands and wall times in
runs.json; raw logs and trajectories under outputs/umr-motion-preliminary-v1.
Numerical checks are in results.json. This excerpt only reaches the first crouch;
the [full clip experiment](../umr-motion-preliminary-v2/README.md) supersedes it
for motion inspection without replacing these smoke outcomes. Static source
shape and exact new hand geometry bindings were reused; no old no-hand mappings.
