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

### Branches and worktrees

`main` is the sole integration branch for Motion Studio. Start new work from
`main` on a temporary `codex/<short-topic>` branch, review and validate it, then
merge it into `main`. Remove the merged topic branch and its worktree after
preserving any local files needed for recovery. Check for unmerged commits,
uncommitted changes and ignored files before cleanup.

The canonical checkout normally stays on `main`; use linked worktrees for
isolated work. Historical experiment references such as `experiments/umr-astro`
remain available for provenance and are not integration targets. Preserve original
branch names in frozen experiment records. External repositories follow their own
branch conventions and pinned revisions.

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

## Implemented workflow entry points

Owned operations now cover [Wendy conversion](wendy-conversion-adapter.md),
[retrospective evidence reconstruction](evidence.md),
[fresh offline reading editions](offline-documentation.md), and
[explicit canonical UMR preparation](umr-canonical-preparation.md). The latter
resolves [robot definitions and named poses](../robots/README.md), copies a closed
run-local input bundle and records stage fingerprints; it always remains
prepared-only. Metadata compatibility does not establish numerical cache validity.
Official [G1 reproduction](../outputs/artifact-archives/experiment-reset-20261104/experiments/umr-g1-baseline-20261029/README.md) retains
its pinned bundled assets and full training/retarget route independently of this
catalog. Representation findings guard exact requested claims: accepted collision
policy is separate from collision equality, and passing named frames does not
establish inertial or model equivalence. Changed geometry/settings create a new
cohort and can require resampling, correspondence training and binding.

Use [dependency roles](dependency-roles.md) for explicit source locators and
independent environments, [checks](checks.md) for pure and opt-in runtime tiers,
and the [experiment template](../experiments/TEMPLATE.md) for current provenance.
Keep new runs and documentation IDs fresh; never redirect a writer through an old
archive alias. [Preservation](preservation.md) and
[relocation/restoration](artifact-relocation.md) describe immutable receipts,
legacy readers and retained paths. The
[layout closeout](../outputs/artifact-archives/experiment-reset-20261104/experiments/layout-and-robot-assets-evidence/ticket13/README.md)
records the bounded acceptance and limits; historical experiment records remain
authoritative for their own cohorts.

## Next practical milestones

- Run the [standard UMR experiment](../experiments/umr-standard/README.md)
  through binding before planning the matched motion stage.
- Read and annotate the Zotero references, linking methods to experiments.
- Compare a locomotion clip and an interaction clip with explicit quality criteria.
- Extend proven conversion/preparation interfaces only when another real workflow
  demonstrates a shared rule; full canonical retargeting/retraining remains future work.
