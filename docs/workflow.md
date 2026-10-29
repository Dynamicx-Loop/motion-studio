# Scope and evolution

## Development policy

Motion Studio owns its product development. External repositories provide pinned,
static modules whose source stays unchanged during ordinary feature work. Static
means stable between deliberate dependency updates, not permanently frozen.

### Ownership and dependency flow

Keep application behavior, user interfaces, orchestration, experiments, adapters,
configuration, and tests in the Motion Studio repository, outside `externals/`.
External checkouts retain their own history, environments, licenses, and assets.
Existing experimental clones and worktrees are historical dependencies, not the
default home for new Motion Studio features. Preserve their local work until an
explicit migration replaces their callers and records.

Use this dependency direction:

```text
Motion Studio UI / CLI / workflows
    → Motion Studio interface
    → concrete external adapter
    → pinned external functions or command-line entry points
```

The interface belongs to Motion Studio. Define small operations around real
outcomes, such as retargeting a clip, rather than mirroring every upstream
function. Begin with concrete functions and types; introduce a shared protocol
only when actual alternatives require one. A seam does not require a common
runtime or a universal motion format.

Each adapter owns upstream imports, checkout discovery, configuration translation,
format conversion, and invocation. Call functions directly when runtimes are
compatible; otherwise invoke the upstream entry point in its own environment and
exchange explicit files or structured results. Keep upstream-specific objects and
process setup inside the adapter. External modules remain independent of Motion
Studio code.

Specify typed inputs and results, units, FPS/timestamps, axes, quaternion and joint
ordering, calibration, mutation, output ownership, and expected failures where
relevant. Validate external results at the seam, record conversions and information
loss, and preserve upstream error causes. Keep environment and file side effects
explicit. Test observable behavior through the Motion Studio interface, with
focused integration checks against the pinned external when available.

### Exceptions and dependency updates

Try upstream configuration, extension hooks, and a Motion Studio adapter first.
If a required capability still needs an external source change, isolate the
smallest patch in that external repository and follow its own instructions. Keep
product-specific behavior in Motion Studio. Record the base revision, reason an
adapter is insufficient, patch or commit, and validation in the owning experiment
or change record; preserve enough information to reconstruct the patched state.
The root manifest alone does not preserve local external changes. Prefer an
upstreamable fix and retire the patch when an adopted upstream revision supplies it.

Update external pins deliberately: inspect upstream changes, preserve existing
patches and assets, run applicable adapter compatibility checks, then update the
manifest and document validation limits. Keep historical baseline revisions and
results intact; a dependency update does not rerun or advance a research baseline.
Apply this policy to new and changed integrations incrementally rather than
rewriting unrelated legacy experiments.

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
