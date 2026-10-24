# Scope and evolution

## Stage 1: collection and daily use (current)

Maintain independent checkouts of useful open-source projects. Study their methods,
record setup requirements, reproduce representative examples, and use them for real
motion work. Build a reference library and capture failures as well as successes.

## Stage 2: reproducible comparison

Use the same source clips and target embodiments across methods where supported.
Record input hashes, source revisions and patches, environment, exact commands,
calibration, FPS, units, axes, quaternion ordering, and joint ordering. Compare
runtime, contact preservation, foot sliding, joint-limit violations, smoothness,
collisions, and task fidelity. Separate measured outcomes from visual judgments.
Do not equate kinematic plausibility with dynamic feasibility.

## Stage 3: shared workflow

Extract adapters and common metadata from repeated workflows: import → inspect →
retarget → edit/refine → validate → export. Preserve source data and keep edits
reversible. Candidate editing operations include trimming, resampling, alignment,
blending, and contact correction. Define a common motion contract only after
comparing real formats and their information loss.

## Stage 4: integrated studio

Bring proven adapters into a consistent editing and visualization interface, with
batch execution, provenance, and reproducible exports. This is a direction, not an
implemented feature set or a commitment to a particular frontend or solver.

## Next practical milestones

- Reproduce one UMR example and one hhtools example on the same target robot.
- Capture an Astro P2 baseline, including the existing local robot changes.
- Read and annotate the Zotero references, linking methods to experiments.
- Compare a locomotion clip and an interaction clip with explicit quality criteria.
- Promote the first repeated conversion or editing step into a shared utility.
