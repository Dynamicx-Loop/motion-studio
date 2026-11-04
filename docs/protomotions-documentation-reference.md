# ProtoMotions documentation build reference

Inspected 2026-10-24 at local revision
`f69fdcaabff31846b4d2247207417b57dc788828`. This is a documentation-source
inspection, not an installation, training run or successful offline-browser test.
No files in the ProtoMotions checkout were changed.

## Actual build

ProtoMotions uses **Sphinx**, with **nvidia-sphinx-theme** and **MyST** for Markdown
alongside reStructuredText. Its independent `docs/requirements.txt` specifies
Sphinx `>=7.0,<9.0`, the theme, copy-button extension, type-hint extension and
MyST parser. The configuration uses autodoc/autosummary and mocks heavy
simulation/training imports. This keeps documentation dependency requirements
separate from the simulation runtime.

`docs/Makefile` delegates `make html` to `sphinx-build -M html source build`,
producing `docs/build/html`. Its GitHub Actions workflow installs the docs
requirements, fetches documentation media from Git LFS, builds HTML and publishes
that directory to GitHub Pages. Deployment is separate from the static output.
Navigation is organized through explicit toctree sections: getting started,
tutorials, user guide, key concepts, API reference and community.

Pinned primary sources:

- [Requirements](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/docs/requirements.txt)
- [Configuration](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/docs/source/conf.py)
- [Makefile](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/docs/Makefile)
- [Build/deploy workflow](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/.github/workflows/deploy-docs.yml)
- [Navigation source](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/docs/source/index.rst)

## Hosted versus file-open behavior

Sphinx's standard `html` builder produces HTML files and stylesheets. Its
`dirhtml` builder instead emits directory-style links intended for a server;
ProtoMotions' inspected workflow chooses `html`.
[Official Sphinx builder reference](https://www.sphinx-doc.org/en/master/usage/builders/index.html).

That supports choosing ordinary `.html` page links for Motion Studio. It does
**not** establish that all ProtoMotions features work offline. The local checkout
has no `docs/build/html` output; Sphinx and the NVIDIA theme are not installed
in system Python. Several GIF/MP4 files under `_static` are Git LFS pointers,
not media bytes. Its index also uses remote shields.io badge images. Those
assets cannot be assumed to appear without internet from this source checkout.

The [hosted search page](https://nvlabs.github.io/ProtoMotions/search.html) exposes
navigation and a JavaScript-required search interface. The hosted search scripts
were not retrievable through the web inspection tool, so their file-origin
behavior was not established. No local ProtoMotions docs build or browser
`file://` navigation was performed. Search compatibility is **unverified**, not
claimed to work or fail. Hosted availability is distinct from direct-file proof.

## Applied to Motion Studio

Reuse the small practices: separate authored sources from generated output,
explicit page navigation, ordinary relative `.html` links, a repeatable build,
and an independent reading artifact that does not import the motion runtime.
Keep the current standard-library builder rather than install a framework for
this basic scaffold. The project-root entry is a script-free overview; the separate supporting-records
page embeds search data and scripts. Displayed figures are embedded data URLs. Reader pages have inline styles.
Optional module-based 3D inspectors are separated from core file reading.

The browser's existing file-URL denial remains a verification limit. A filesystem
link traversal and Node search test check the file bundle without automating a
browser or evading that denial. The manual acceptance check is in the
[offline documentation guide](offline-documentation.md).

## Rendered layout inspection and source organization

The official hosted home and Installation pages were inspected in local Chrome
at desktop (1440 × 1000) and mobile (390 × 844) sizes. The desktop view has a
compact top header, a persistent left sidebar with grouped sections and a colored
active-page border, a restrained central reading column, and an “On this page”
list at the right. Installation uses breadcrumb context, bordered code blocks
with copy buttons, and previous/next links. On mobile, site navigation and the
page outline move behind separate header controls; the site menu opens as a drawer.
These are observed hosted behaviors, not evidence of file-open compatibility.

Motion Studio borrows the reading-column, sidebar, page-outline and sequential
navigation patterns with its own typography, colors and branding. Its three
primary links are Installation, Quick Start and UMR Experiments. A separate supporting-records page keeps research and legacy evidence available. With only
three primary links, mobile navigation wraps visibly instead of requiring a
JavaScript drawer. The page outline is a native disclosure. No NVIDIA logo,
remote fonts, theme code or upstream media was copied.

The local ProtoMotions tree separates `docs/source/index.rst` and `conf.py` from
`getting_started/`, `tutorials/`, `user_guide/`, `concepts/` and `api_reference/`.
`source/_static/` holds figures/media and `source/_ext/` holds documentation
extensions. `docs/Makefile` is the build entry; `docs/build/html/` is generated.
Motion Studio applies source/output separation without changing frameworks:

- `docs/site/pages/installation.html`, `quick-start.html` and
  `umr-experiments.html`: editable initial sections.
- `docs/site/pages/supporting-records.html`: preserved archive presentation.
- `docs/site/templates/overview.html`: overview template; `catalog.json`: stable
  source IDs and reading/timeline metadata.
- `docs/site/style.css` and `search.js`: local presentation and enhancement.
- `scripts/build_docs.py`: build entry; `motion_studio/documentation/`: implementation.
- Root `docs.html` and `docs-basic.html`: generated local-file overview entries.
- Bundle-level `installation.html`, `quick-start.html`, `umr-experiments.html`
  and `supporting-records.html`: separate pages with shared navigation.
- `outputs/umr-binding-report/documentation/`: generated readers, source
  snapshots, media, notices and manifest, alongside the existing report.

Ordinary Markdown research sources stay at their original paths. No external
checkout or unrelated project file was reorganized.

The originally opened `docs/site/home.html` was an authoring fragment, not a
built entry. After the observed Chrome path identified this confusion, its
source was preserved under `templates/overview.html`; that old entry path now
receives a generated compatibility overview with correctly rebased relative
links. This is an explicit compatibility exception within the source directory.
