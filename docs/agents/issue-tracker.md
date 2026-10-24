# Issue tracker: Local Markdown

Motion Studio tracks issues, specs, and investigations locally under `.scratch/`.
This is the authoritative tracker before GitHub publication. Adding a GitHub
remote does not change it; switch trackers only when the user requests migration.

## Ticket conventions

- One feature or effort per directory: `.scratch/<feature-slug>/`.
- Specs live at `.scratch/<feature-slug>/spec.md`.
- Keep each implementation ticket in its own file:
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`.
- Allocate the next unused number in that effort; preserve existing ticket paths.
- Use one `Status:` line near the top. Triage statuses are defined in
  [triage-labels.md](triage-labels.md); execution uses `claimed` and `resolved`.
- Record `Category: bug` or `Category: enhancement` for implementation issues.
- Link the parent spec or map and state the outcome, scope, acceptance criteria,
  dependencies, and relevant reproduction or validation commands.
- Append discussion under `## Comments`; preserve the history when updating state.
- Use paths relative to the ticket for links. Resolve bare ticket numbers within
  the current effort; ask which effort when the number is ambiguous.

When a skill says **publish to the issue tracker**, create or update the local
Markdown file. When it says **fetch a ticket**, read the referenced file. Local
publication does not mean creating a remote issue or contacting another person.

The tracker files are eligible for version control in Motion Studio; `.scratch/`
is not ignored. Keep bulky logs, generated results, and private data outside
these tickets, and link to their locations instead.

## Minimal implementation ticket

```markdown
# 01 — <outcome>

Status: needs-triage
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Context

<Problem and supporting evidence.>

## Scope

<Requested behavior and boundaries.>

## Acceptance criteria

- <Observable completion condition.>

## Validation

<Relevant checks and required environment/data.>

## Comments
```

Use `ready-for-agent` once the ticket is sufficiently specified for implementation.
Claim it before work; mark it `resolved` only after recording the result and checks
under `## Answer`. A completed ticket remains in place for traceability.

## Wayfinding operations

For `/wayfinder`, use `.scratch/<effort>/map.md` with `## Notes`,
`## Decisions-so-far`, and `## Fog` sections. Keep each child question in a
separate `.scratch/<effort>/issues/<NN>-<slug>.md` file.

- Record `Type: research`, `prototype`, `grilling`, or `task`.
- Record dependencies as `Blocked by: NN, NN`, or `Blocked by: none`. Numbers
  refer to the same effort; cross-effort dependencies use explicit ticket paths.
- A ticket is unblocked when all listed blockers have `Status: resolved`.
- Scan for open, unblocked, unclaimed tickets; take the first by number among
  tickets ready for agent work. `needs-info`, `ready-for-human`, and `wontfix`
  are not executable agent tickets.
- Claim by saving `Status: claimed` before beginning work.
- Resolve by adding `## Answer`, setting `Status: resolved`, and adding a short
  finding plus a link in the map's Decisions-so-far section.

## Later GitHub migration

Keep using this tracker until migration is requested. During migration, retain
local ticket IDs and history, record a mapping to remote issue URLs, and update
this document and the AGENTS.md pointer together so there is one authoritative
tracker. Creating a remote repository alone is not a ticket-migration request.
