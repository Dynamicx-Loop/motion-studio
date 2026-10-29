# Agent instructions

## Scope and project context

Motion Studio is an early-stage collection of independent motion retargeting and
editing tools. Build shared workflow pieces from demonstrated needs in real
experiments; keep each upstream project's runtime and dependencies independent.

## Development ownership

- Treat external repositories as pinned, static dependencies. Implement Motion
  Studio features, experiments, interfaces, adapters, and tests in this root project.
- Route product code through Motion Studio-owned interfaces. Keep external imports,
  configuration translation, and runtime invocation inside concrete adapters;
  callers request outcomes using Motion Studio inputs and results.
- Prefer configuration and adapters over external source edits. Make an external
  patch only when a required capability cannot reasonably be provided that way;
  keep it minimal and preserve its revision, patch, rationale, and validation.
- Before adding an integration, patching an external, or updating a dependency,
  read [the development policy](docs/workflow.md#development-policy).

## Workspace context

- Before changing workspace structure or integration scope, read
  [README.md](README.md) and [docs/workflow.md](docs/workflow.md).
- Before managing external checkouts or advancing a baseline, read
  [externals/README.md](externals/README.md),
  [externals/manifest.json](externals/manifest.json), and
  [scripts/workspace.py](scripts/workspace.py). The root tracks the manifest and
  ignores checkout contents; unavoidable upstream patches must be preserved
  separately from the manifest pin.
- Before moving hhtools, changing its environment paths, or working with the old
  compatibility location, read [docs/migration.md](docs/migration.md). Use the
  checkout under `externals/` as canonical; preserve local edits, ignored assets,
  Git metadata, and compatibility links.
- Before setting up or comparing ProtoMotions and PyRoki, read
  [docs/protomotions-pyroki.md](docs/protomotions-pyroki.md). Follow each external
  project's own instructions for its setup and code changes. Source availability
  alone does not establish that dependencies, large assets, or GPU jobs work.

Preserve upstream licenses and notices. Check dataset, model-weight, and asset
terms separately when importing or redistributing them.

## Deep modules and clean interfaces

- Design deep modules: substantial behavior behind a small interface. Depth is
  the complexity callers avoid learning, not implementation line count.
- Keep related knowledge and invariants in the module that owns them. Expose the
  fewest operations and parameters callers need; keep implementation helpers
  private and let callers request outcomes without orchestrating internal steps.
- Make interface contracts explicit: typed inputs and results, units, array
  shapes, ordering, mutation, configuration, and expected failures as relevant.
  Validate external data before passing it into domain logic.
- Start with functions and concrete types. Add adapters or protocols where real
  alternatives vary; extract abstractions when they centralize a shared rule or
  hide meaningful complexity. Prefer composition and keep one-off logic local.
- Separate numerical computation from CLI handling, file I/O, visualization, and
  simulator setup. Pass runtime dependencies from entry points, return results
  where practical, and make necessary side effects explicit.
- Keep dependency flow acyclic. Reuse existing project and upstream facilities;
  handle failures where they can be acted on, preserving causes and useful context.

## File size and organization

- Prefer hand-written source and test files of **400–500 lines or fewer**. This
  is a maintainability guideline, **not a hard limit**. Prioritize cohesive logic,
  readable formatting, useful documentation, and clean interfaces over line count.
- As a file grows, look for coherent responsibilities to split when that improves
  clarity and locality. A deep module can span private files behind one small
  interface. Keep related logic together when a split adds indirection or scatters
  knowledge; consider extractions within the requested change's scope.
- Keep scripts thin: argument parsing, dependency wiring, and calls to reusable
  modules. Name modules after their responsibility instead of accumulating
  unrelated helpers in `utils.py`.
- Apply size guidance to hand-written code; change generated files through their
  source or generator. Preserve external projects' own conventions when editing
  their code rather than reformatting upstream files wholesale.

## Motion data and reproducibility

- Preserve source clips and keep processing and editing reproducible. Make units,
  FPS and timestamps, coordinate frames and axes, quaternion conventions, joint
  order, embodiment, and calibration explicit at import/export interfaces.
  Record conversions and information loss, including trimming and resampling.
- For experiments and comparisons, use [experiments/TEMPLATE.md](experiments/TEMPLATE.md)
  to capture input provenance, source revisions and local patches, environments,
  exact commands, configuration, and results. Follow
  [docs/workflow.md](docs/workflow.md) for comparison criteria.
- Support method and solver claims with inspected source or primary references,
  identifying revisions where relevant. Distinguish measured results, visual
  judgments, and inferences; kinematic plausibility does not establish dynamic
  feasibility. Use [references/README.md](references/README.md) for the reading index.

## Validation and completion

- Test observable behavior through module interfaces with expectations from a
  specification, worked example, or independent reference. Favor meaningful
  success, failure, and edge cases over tests tied to implementation details.
- Keep validation proportionate to the change. For numerical checks, use explicit
  tolerances and controlled seeds where relevant. Run applicable checks from the
  owning project's configuration; use focused smoke checks when full workflows
  require unavailable environments, assets, or hardware.
- Before finishing, review interface complexity, file growth, and the diff. Report
  checks run and material limitations, including workflows not exercised. For
  documentation-only changes, verify referenced paths and whitespace.

## Current library documentation with Context7

Use Context7 MCP whenever answering questions about a library, framework, SDK,
API, CLI tool, or cloud service, including API syntax, configuration, version
migration, setup, and library-specific debugging, even for familiar tools.

1. Start with `resolve-library-id` using the library name and documentation topic,
   unless the user supplies an exact `/org/project` library ID.
2. Choose the best match by exact name, description relevance, snippet coverage,
   source reputation (prefer High/Medium), and benchmark score. Use a
   version-specific ID when a version is requested; retry with alternate names or
   queries when results do not fit.
3. Call `query-docs` with that ID and a focused question for one concept. Query
   distinct concepts separately unless the question concerns their interaction.
4. Answer using the fetched documentation. Prefer Context7 over web search for
   library documentation.

Context7 is unnecessary for general programming concepts, scripts written from
scratch, business-logic debugging, code review, or refactoring unless the task
also requires library-specific documentation.

## Agent skills

### Issue tracker

Track specs and tickets as local Markdown under `.scratch/`. Before creating,
reading, or updating tickets, read [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md).
This remains the tracker until an explicit migration to GitHub Issues.

### Triage labels

Use the five default triage roles as local statuses. Before triaging tickets,
read [docs/agents/triage-labels.md](docs/agents/triage-labels.md).

### Domain docs

Use a single-context glossary and ADR layout. Before exploring domain concepts
or architectural decisions, read [docs/agents/domain.md](docs/agents/domain.md).
