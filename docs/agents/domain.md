# Domain documentation

Motion Studio uses a single-context domain layout: root `GLOSSARY.md` and
`docs/adr/`. Independent upstream checkouts under `externals/` do not by themselves
make Motion Studio a multi-context monorepo.

## Before exploring a domain area

Read the root glossary if present, then ADRs relevant to the area being changed.
Follow the external project's own domain documentation when changing its code.
If the glossary or ADR directory does not yet exist, proceed silently. Create
these documents through domain-modeling when concrete terms or decisions are
resolved, rather than filling them with speculative definitions.

## Vocabulary and decisions

Use glossary terms consistently in code, tickets, specs, tests, and research
notes. If a needed concept is absent, check existing usage before proposing a
new term; record a real terminology gap for domain-modeling.

Keep architectural decisions under `docs/adr/` with numbered descriptive filenames.
If a proposal conflicts with an existing ADR, identify the conflict and explain
why the decision should be revisited rather than silently overriding it.
