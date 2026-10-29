# umr-motion-fist-v1

Fresh fist cohort dated 2026-10-23. The previous open-hand experiment remains immutable.
The exact model and 14 named preset coordinates are pinned in `../astro-fist-static-v1/canonical-asset.json`.
Body T-pose uses shoulder rolls ±pi/2 and elbows +pi/2. Visual surfaces only; no new collision-primitive experiment or hardware execution.

Raw four Astro trainings use 4096 target samples, seed 9000; 500 epochs, training seed 0. G1 static slots retain exact historical provenance. SMPL-X and SOMA identities differ.
The wrist candidate is separately measured and is not adopted as default.
HiPHI motion uses 1823 frames from 0:5468:3, with all 14 Astro fingers fixed by equal named-joint QP bounds during initialization and solve; exported LQR poses are checked.
BONES-SEED matching motion/shape/rig remain unavailable; SOMA static results do not substitute for motion.

See adjacent JSON results, preparation, runs and validation records for actual computed values and exact commands.
