# Offline documentation editions

Open **`docs.html`** in the project root. It is a complete static overview,
with ordinary relative links to Installation, Quick Start, UMR Experiments and
Supporting records. `docs-basic.html` is a plain HTML overview, and
`docs/site/home.html` is a complete compatibility overview for the previously
opened location. These are generated reading entries; none redirects or launches
a server. The authoring overview is `docs/site/templates/overview.html`.

Core reading, navigation and search use bundled content and inline CSS.
The full document list remains visible when JavaScript is unavailable.
External citations are intentional online links. Historical reports and 3D
inspectors are separate from the current documentation.

## Build a fresh edition

From the owned source workspace:

```sh
python3 scripts/build_docs.py --edition local-20261029-01
python3 scripts/verify_docs.py --edition local-20261029-01
node scripts/docs_site/test_search.cjs --edition local-20261029-01
python3 scripts/check.py --tier javascript --docs-edition outputs/docs-site/local-20261029-01
```

The default edition name is `current`. Every destination must be fresh; choose a
new name for the next build. No existing edition is overwritten. `--output PATH`
selects a different fresh destination on build, verify and Node search commands.
The check command's `--docs-edition PATH` selects the generated directory explicitly.
Without selection, the Node check follows the current root `docs.html` entry.
Missing selected prerequisites
are reported as unavailable by the root check command, with a nonzero exit.
See [checks](checks.md) for runtime tiers.

For a worktree with source files but separately preserved evidence:

```sh
python3 scripts/build_docs.py --source-root . \
  --evidence-root /data/workspace/motion_studio --edition local-20261029-02
python3 scripts/verify_docs.py --source-root . \
  --evidence-root /data/workspace/motion_studio --edition local-20261029-02
```

`source-root` owns the catalog, templates, styles, and Markdown sources.
`evidence-root` supplies any local artifacts referenced by those sources.
The builder includes the current catalog and preserves the prior compatibility
entry bytes. Historical reports and inspector assets are kept in their
original evidence bundles.

The owned operation is `motion_studio.documentation.build_edition(source_root,
evidence_root, edition=..., output=..., saved_edition=...)`. Rendering,
required-input checks, and local link validation finish in staging before
publication. A failure leaves the previous entry and editions intact.

## Explicit saved-source fallback

Ordinary builds require canonical source records. To reuse missing source text
from a previous edition, explicitly select preservation-only fallback:

```sh
python3 scripts/build_docs.py --edition saved-20261029-01 --saved-sources \
  --saved-edition outputs/docs-site/local-20261029-01
python3 scripts/verify_docs.py --edition saved-20261029-01
```

The fallback snapshot must match the prior manifest's recorded SHA-256. Missing
or changed snapshots fail; canonical files that exist remain authoritative.
`--saved-sources` alone explicitly selects snapshots in the input research bundle.
Every generated reading page displays **Saved evidence edition** when fallback
is enabled, and the manifest names each reused source snapshot. This is saved
evidence, not fresh environment or experiment validation. No canonical file is
restored or changed by fallback.

## Verification and browser limits

`motion_studio.documentation.verify_edition(output)` verifies source/output and
preserved-original hashes, local links and fragments, catalog/search destinations,
and inline reading resources.
The manifest records the original source/evidence roots. The CLI defaults its
source root to the executing checkout, so an ordinary `--edition` verification
survives a handoff from a temporary build worktree. The Python API retains recorded
roots unless explicitly overridden. Use `--source-root` and `--evidence-root` when
checking a different or relocated workspace. Both a same-relative per-edition alias
and its physical target verify by resolved link destinations; source/output and
root-entry byte hashes remain enforced. `verify_docs.py --report PATH` saves an explicit verification
receipt. Verification alone does not mutate the research bundle.

Pure fixture tests run in `python3 scripts/check.py`. They exercise publication,
missing inputs, broken authored links, explicit saved fallback and corrupt
snapshots without requiring the real local evidence. The Node search check runs
six progressive-search cases in its explicit JavaScript tier; it does not prove
browser direct-file rendering.

An earlier user file-open check produced a blank page. A later inventory found
`docs/site/home.html` had been an unbuilt template fragment; its authoring source
was preserved at `templates/overview.html` and the generated compatibility entry
now has a full document shell and valid links. Those observations do not establish
the cause of the earlier blank root entry. Browser automation has historically
rejected `file://` navigation under its HTTP/HTTPS policy. Static checks and HTTP
preview are distinct evidence; they do not establish successful direct-file
rendering. Browser security settings are unchanged.

## Portable local bundle

Copy the complete selected edition to keep its pages, source attachments and
build manifest together. Open the edition's own `docs.html` when reading a
standalone copy. The project-root entries point into the selected edition.
Verification also needs the recorded source and evidence roots or equivalent
overrides.

The superseded `review-20261029-complete` edition is kept under
`outputs/artifact-archives/offline-docs-20261104/` for historical reference.
The current edition contains guides and research references. Open the
historical edition directly for its legacy records and inspectors.

## Authoring

Edit `docs/site/templates/overview.html`, section templates under
`docs/site/pages/`, `style.css`, `search.js`, and `catalog.json`. Register Markdown
records with a permanent ID, source path, title, state and description; timeline
items refer to registered sources. States are `workspace`, `reference`, `study`,
`guideline` and `baseline`, distinct from tracker statuses.

Keep original experiment provenance, revisions, units, conventions and results.
The reader renders selected recorded evidence and exposes unbundled local paths
explicitly; it does not reconstruct or advance a baseline. The generated
`docs/site/home.html` compatibility page is the documented exception inside the
authored site directory. Do not edit generated entries by hand. Source templates,
owned build/verify code and tests are versioned; generated entries and editions
remain ignored local artifacts.
