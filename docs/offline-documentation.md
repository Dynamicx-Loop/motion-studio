# Offline documentation

## Read without a server

Double-click **`docs.html` in the Motion Studio project root**:
`/data/workspace/motion_studio/docs.html`.

This is the documentation itself, not a redirect or a localhost launcher. The
root entry is a script-free overview. Installation, Quick Start, UMR Experiments
and Supporting records each open as a separate generated HTML page through
ordinary relative file links. CSS is inline; the supporting-records page embeds
the optional JavaScript search index and saved figures. Their styles are inline and displayed images are embedded. Reading,
search, navigation, tables and saved visual comparisons require no server,
internet, API, service worker or account. Plain source/provenance attachments are
local files; they are not fetched by application code.

The documentation continues to use the existing research viewer bundle in
`outputs/umr-binding-report/`. Its original bilingual report remains a separate
legacy reading view with the same anchors. New documentation is in English;
original EN/中 pages remain bilingual. TeX is readable source notation, with no
remote math renderer. This small Markdown reader supports the documented subset.

### Direct-file verification and blank-view diagnosis

The automation browser rejected `file://` navigation because its URL policy
permits only HTTP/HTTPS. That denial was not retried or bypassed. No browser
security, permissions or system settings were changed. Static file-link and
embedded-resource checks, plus a JavaScript search test in Node, are automated;
these do **not** establish a successful browser file-open test.

The first user check **failed**: the built-in browser displayed a blank page.
The reported view is not exposed to this task's browser inventory, so its cause
is unresolved. Parsing the saved root file with an HTML5 parser found no errors,
16,565 characters of static main content and all 44 document links. This rules
out an empty generated document, but does not prove a browser can load the file.

The revised reader keeps the complete static document library visible before
JavaScript runs and only reveals search controls after successful initialization.
A generated **`docs-basic.html` in the same project root** provides a small
overview and separate-page links without CSS, JavaScript, CSP or embedded image
payloads. The other pages remain readable without JavaScript. It is a fallback reading view,
not a different site or a localhost launcher. Both root files are built together.

The remaining manual diagnostic is to open `docs-basic.html` in the same browser
and note its address and whether the heading and document links appear. A blank
plain file would narrow the issue toward document loading; a visible plain page
would narrow it toward the enhanced page or its treatment by that browser.
Neither outcome has been observed by this task. Do not change browser security.

### Confirmed authoring-template entry mistake

A later Chrome tab inventory established the actual open URL as
`file:///data/workspace/motion_studio/docs/site/home.html`. At that time this was
an unbuilt authoring fragment: it had no document shell or CSS, still contained
`{{DOC:...}}` tokens, and its `installation.html` and `quick-start.html` links
resolved to nonexistent files under `docs/site/`. This explains that reported
unstyled home and broken subpage navigation. It does not establish the cause of
the earlier, separate report about root `docs.html`.

The original template bytes are preserved at `docs/site/templates/overview.html`.
The builder now writes a complete compatibility overview at the already-open
`docs/site/home.html`, with inline CSS, no scripts, and correct `../../` paths
to root entries and generated section pages. The preferred entry remains root
`docs.html`. Reloading the already-open home file is the minimal remaining
manual check, followed by Installation and Quick Start.

Browser inventory exposed the URL, but observation of that existing file tab
was denied by the browser URL policy (HTTP/HTTPS only). No retry, indirect
navigation or security change followed. Disk parsing and link checks passed;
post-repair rendering of this exact file has not been observed.

## Optional advanced inspectors

Only interactive 3D / motion inspectors need local HTTP for their JavaScript
modules and saved geometry. They are visibly separated under **Optional 3D
tools**, and are not needed to read the documentation or saved figures.
If you choose to use them, start from the project root:

```sh
python3 -m http.server 8770 --bind 127.0.0.1 --directory outputs/umr-binding-report
```

Then open `http://127.0.0.1:8770/inspectors/canonical-motion/index.html`.
Reuse the server if already running; Ctrl+C stops one started in your terminal.
This optional route was verified previously for static inspection and saved
motion playback. It does not perform a new experiment. Untouched historical
archives retain their original dependencies and were not all audited.

## Rebuild after editing

```sh
python3 scripts/build_docs.py
python3 scripts/verify_docs.py
```

If canonical records are unavailable in the current checkout, the normal build
fails before writing pages. An explicit preservation-only rebuild is available:

```sh
python3 scripts/build_docs.py --saved-sources
python3 scripts/verify_docs.py
```

This mode reads a missing source only from its existing local snapshot after
checking the previously recorded SHA-256. It never restores or alters Git files.
Every generated page displays “Saved evidence edition”; the manifest records
`reused_source_snapshots`. An earlier revision reused ten missing sources while the execution checkout
reported `master` at `72647c2`, rather than the supplied experiment branch.
After explicit user authorization, the root was safely switched back to
`experiments/umr-astro`; the normal canonical-source build now passes with zero
snapshot fallbacks. The earlier reason for the checkout mismatch is unknown.

Both commands use system Python and its standard library. They do not import
UMR, train, retarget, install packages or use the network. The builder expects
the existing local research bundle and saved experiment records. A fresh Git
clone alone does not include ignored outputs or legacy user files.

The builder writes root `docs.html` and `docs-basic.html`, plus the existing bundle entry and
`documentation/` under `outputs/umr-binding-report/`. Both overview entry points are built
from the same sources; root URLs are rebased at build time. Search lives on
`outputs/umr-binding-report/supporting-records.html`. Displayed figures are data URLs, avoiding file-origin image
policy differences. There is no runtime path discovery.
It preserves a byte-exact copy of each existing HTML entry it decorates under
`history/documentation-scaffold/` before adding a legacy banner and local
inspector dependency paths. Original experiment sources and artifacts stay
unchanged. Rebuilding the original research report may overwrite its decorated
HTML; run the docs builder afterward to reapply the additive navigation.

The documentation manifest records source SHA-256 hashes, generated output
hashes, preserved originals and unavailable/unbundled source links. The older
report manifest describes its original build, before the documented decoration.
The docs builder hashes the current baseline evidence and snapshots small JSON
records; it does not rerun the experiment or revalidate all raw tensors.

## Add a study

1. Write a versioned Markdown note in `references/`. Separate paper claims,
   inspected implementation, measured results and inference; pin source revisions.
2. Add a document to `docs/site/catalog.json`: a permanent `id`, project-relative
   `path`, `title`, `state` and short `description`. Use `study` or `reference`.
3. Add a dated timeline item only if it records a meaningful research decision;
   link its `source` to a registered document. Rebuild and verify.

## Add an experiment

1. Start from `experiments/TEMPLATE.md`; keep inputs, configs, commands, source
   revisions, units, axes, FPS, joint order and failure states explicit.
2. Register its README with a permanent ID. Use `baseline` only for the separately
   reviewed prospective cohort; previous reports remain `legacy`.
3. Keep raw artifacts in their existing output location. Add selected local
   figures with provenance when available; do not invent media or pool unlike
   cohorts. The registry reads the frozen legacy index and the current baseline.
   Updating its numerical contract requires an explicit builder change and review.
4. Rebuild, verify, and inspect the changed page in a local browser.

Supported document states are `workspace`, `reference`, `study`, `guideline`,
`baseline` and `legacy`. These are documentation evidence labels, not tracker
triage statuses. No ticket migration is part of this scaffold.

## Portability and boundaries

For the project-root entry, preserve this relative layout when copying locally:

```text
docs.html
docs-basic.html
outputs/umr-binding-report/docs.html
outputs/umr-binding-report/docs-basic.html
outputs/umr-binding-report/installation.html
outputs/umr-binding-report/quick-start.html
outputs/umr-binding-report/umr-experiments.html
outputs/umr-binding-report/supporting-records.html
outputs/umr-binding-report/documentation/
outputs/umr-binding-report/index.html   # original bilingual report
```

Copy the whole `outputs/umr-binding-report/` folder as well if you want the
optional inspectors and historical archives. The core reading bundle is not
just the single root file: linked reader pages and source attachments must
accompany it. Moving the project directory together keeps relative links valid.
Keep copies local: bundled processed human/robot geometry and legacy figures
retain their original asset terms, and this work grants no redistribution rights.
No external licensed media was downloaded or uploaded.

Bundled text attachments retain original relative paths under
`documentation/sources/`. Registered Markdown links point to rendered pages.
External citations stay links labeled online. Links to large data, external
checkouts, missing files or unsupported assets become explicit unbundled-path
notes; the unchanged raw Markdown preserves the original link. Full-fidelity
source and provenance always remain available alongside the reading view.

The existing saved Three.js r165 modules are reused locally for inspectors;
license notices are preserved. No system or browser-wide network setting is
changed. Core pages include a restrictive content policy that prevents remote
runtime resources; external citation navigation is still an intentional action.

See [the ProtoMotions documentation reference](protomotions-documentation-reference.md)
for the inspected build and the simple practices reused here.

## Authoring structure

Edit the three initial sections under `docs/site/pages/`: `installation.html`,
`quick-start.html`, and `umr-experiments.html`. `templates/overview.html` authors the overview; each section template now builds to its own
HTML file. `supporting-records.html` is a separate page preserving the library,
chronology and legacy figures without adding a primary navigation entry. The
shared shell supplies a three-link sidebar, current-page indication and page
outline; previous/next links move between real HTML files. Earlier overview
fragment links retain a small compatibility link list, not concatenated content. Edit `style.css`
for layout and `search.js` for progressive search. Original Markdown/JSON
records remain at their original paths and are selected by `catalog.json`.

This borrows ProtoMotions' authored-pages versus generated-output separation,
without adopting its Sphinx runtime. Root HTML files and the compatibility `docs/site/home.html` are generated: change the
source and rebuild, rather than editing generated pages by hand.

## Proposed docs branch — not executed

A dedicated root-repository branch such as `docs/offline-scaffold` is useful for
reviewing documentation independently. It is unrelated to the Git branch in
`externals/UMR-baseline-v1`; that dependency stays untouched.

After the existing no-commit hold is lifted and the root checkout mismatch is
resolved, first inventory and hash the docs-owned changes. Preserve a copy of
the portable output bundle and a whitelist of authored files. Create a separate
root-repository worktree from the verified `experiments/umr-astro` revision, then
create the docs branch there. Copy only that whitelist and the README docs
section into the new worktree; compare hashes and review its diff before any
selective staging or commit. Leave the original checkout, its untracked files
and all nested repositories in place. Do not use a blanket stash, reset or clean.

The whitelist is `docs/site/`, `docs/offline-documentation.md`,
`docs/protomotions-documentation-reference.md`, `scripts/build_docs.py`,
`scripts/verify_docs.py`, `scripts/docs_site/`, the README documentation section,
and generated root entries for review. The generated bundle under ignored
`outputs/` is necessary for reading and must accompany a local handoff; a fresh
Git clone does not currently reproduce it. Whether to version a distributable
bundle is a separate review decision, not an ignore-policy change made here.
No branch, worktree, stage or commit was created by this proposal.

### Separate-page revision validation

The root overview and three primary pages contain no scripts. Supporting records
contains the prebundled search index and its optional enhancement; its complete
44-document list is authored HTML. Static checks validate cross-page anchors and
current-page markers. In the local HTTP preview, the full sequence Overview →
Installation → Quick Start → UMR Experiments → Supporting records changed to
distinct HTML URLs with one primary heading each. Desktop and mobile checks and
SOMA + baseline search passed. This does not establish direct-file browser
acceptance or explain the original blank built-in-browser report.

## What the documentation commit contains

The local documentation commit versions authored templates, catalog, CSS/JS,
build/verification scripts, reading tests and small verification notes. Generated
`docs.html`, `docs-basic.html`, compatibility `docs/site/home.html` and the
`outputs/umr-binding-report/` reading bundle remain local generated artifacts.
They are preserved and reproducible here with the normal build command. They
are not committed as launchers pointing to an absent generated bundle.

A fresh clone still requires the recorded local research/evidence artifacts and
legacy records before the complete documentation build can run. This source
commit does not package licensed media, checkpoints, models, external dependency
contents or unrelated user work, and does not change ignore policies.
