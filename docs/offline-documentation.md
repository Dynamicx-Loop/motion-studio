# Offline documentation editions

Open **`docs.html`** in the project root. It is a complete static overview,
with ordinary relative links to Installation, Quick Start, UMR Experiments and
Supporting records. `docs-basic.html` is a plain HTML overview, and
`docs/site/home.html` is a complete compatibility overview for the previously
opened location. These are generated reading entries; none redirects or launches
a server. The authoring overview is `docs/site/templates/overview.html`.

Core reading, navigation, saved figures and progressive search use bundled
content, inline CSS and embedded images. The full document list remains visible
when JavaScript is unavailable. External citations are intentional online links.
Optional 3D inspectors need local HTTP; reading the documentation does not.

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
Without selection, the historical Node command still checks
`outputs/umr-binding-report/supporting-records.html`. Missing selected prerequisites
are reported as unavailable by the root check command, with a nonzero exit.
See [checks](checks.md) for runtime tiers.

For a worktree with source files but separately preserved evidence:

```sh
python3 scripts/build_docs.py --source-root . \
  --evidence-root /data/workspace/motion_studio --edition local-20261029-02
python3 scripts/verify_docs.py --edition local-20261029-02
```

`source-root` owns the catalog, authored templates, styles, search, Markdown
records, small source attachments and the three compatibility entries.
`evidence-root` supplies recorded `outputs/` paths, including the existing
research viewer at `outputs/umr-binding-report/`, the retrospective index at
`outputs/umr-legacy-index-20261024/`, the recorded static baseline at
`outputs/umr-astro-baseline-v1/static-20261024-01/`, and referenced saved figures.
A fresh Git clone does **not** contain these ignored local bundles. Source
availability is not evidence that licensed assets, environments or GPU jobs work.

The owned operation is `motion_studio.documentation.build_edition(source_root,
evidence_root, edition=..., output=..., saved_edition=...)`. It copies the local
report closure, including its saved history and optional inspectors, into staging;
it never hard-links or decorates the research input. Its manifest records copied
input and output hashes, authored-source hashes, byte-exact preserved legacy HTML,
and any existing compatibility entry bytes before replacement. Internal relative
history links remain local to the copied closure. No UMR import, training,
retargeting, download or numerical experiment occurs.

All rendering and required-input checks, local reading links and anchors finish
in staging before publication. A missing source, changed saved snapshot, broken
reading link or other build failure leaves previous entry bytes and editions
intact. Existing root/basic/home entries are archived under
`history/entry-pages/<sha256>/` in the fresh edition. The research input's own
saved originals stay copied and hash-checked under its existing history paths.
Old research URLs and bilingual anchors continue to work at the original input;
the new edition has its own decorated copies.

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
inline reading resources, saved figures and original legacy anchor retention.
The manifest records source/evidence roots; optional overrides support a relocated
local workspace. `verify_docs.py --report PATH` saves an explicit verification
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

## Portable local bundle and optional inspectors

Keep this relative layout when moving a project-root reading edition locally:

```text
docs.html
docs-basic.html
docs/site/home.html
outputs/docs-site/<edition>/docs.html
outputs/docs-site/<edition>/docs-basic.html
outputs/docs-site/<edition>/installation.html
outputs/docs-site/<edition>/quick-start.html
outputs/docs-site/<edition>/umr-experiments.html
outputs/docs-site/<edition>/supporting-records.html
outputs/docs-site/<edition>/documentation/
outputs/docs-site/<edition>/index.html
outputs/docs-site/<edition>/figures/
outputs/docs-site/<edition>/records/
outputs/docs-site/<edition>/history/
outputs/docs-site/<edition>/inspectors/
```

Copy the **whole edition** to retain saved history, attachments, local Three.js
r165 modules and optional inspector geometry. The current local research closure
is about 2.5 GB, mostly saved inspector/history assets. Root entries reference the
selected edition; copying only an entry file is insufficient. An edition's own
`docs.html` is also a usable self-contained entry relative to its adjacent files.
Verification of relocated source hashes still requires the recorded source and
evidence roots or explicit equivalent overrides.

For optional inspectors, open a terminal in the copied edition and run:

```sh
python3 -m http.server 8770 --bind 127.0.0.1
```

Open `http://127.0.0.1:8770/inspectors/canonical-motion/index.html`. This loads saved
geometry and motion; it runs no experiment. Retained historical archives preserve
their original dependencies and are not all audited as interactive applications.
Core reading does not depend on this server.

Keep copies local. Bundled figures, processed human geometry, datasets, model and
robot assets retain their separate terms; copying grants no redistribution rights.
Existing Three.js notices are preserved. No licensed media is downloaded or
uploaded by this workflow.

## Authoring

Edit `docs/site/templates/overview.html`, section templates under
`docs/site/pages/`, `style.css`, `search.js`, and `catalog.json`. Register Markdown
records with a permanent ID, source path, title, state and description; timeline
items refer to registered sources. States are `workspace`, `reference`, `study`,
`guideline`, `baseline` and `legacy`, distinct from tracker statuses.

Keep original experiment provenance, revisions, units, conventions and results.
The reader renders selected recorded evidence and exposes unbundled local paths
explicitly; it does not reconstruct or advance a baseline. The generated
`docs/site/home.html` compatibility page is the documented exception inside the
authored site directory. Do not edit generated entries by hand. Source templates,
owned build/verify code and tests are versioned; generated entries and editions
remain ignored local artifacts.
