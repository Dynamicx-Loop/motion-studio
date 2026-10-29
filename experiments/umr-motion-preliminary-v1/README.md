# Preliminary UMR motion smoke test

2026-10-23. First 12 seconds of shipped HiPHI Getting_up-get_up_0004, frames
0:1080:3, 360 poses at 30.0003 Hz. Four successful offline solves: G1/Astro Dex3-1,
spine1/bbox50. Source motions and static-binding findings were preserved.

Frozen inputs/config hashes are in inputs.json; exact commands and wall times in
runs.json; raw logs and trajectories under outputs/umr-motion-preliminary-v1.
Numerical checks are in results.json. This excerpt only reaches the first crouch;
the [full clip experiment](../umr-motion-preliminary-v2/README.md) supersedes it
for motion inspection without replacing these smoke outcomes. Static source
shape and exact new hand geometry bindings were reused; no old no-hand mappings.
