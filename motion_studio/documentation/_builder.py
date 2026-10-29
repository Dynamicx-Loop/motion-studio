"""Assemble a portable reading bundle from saved text/data, never experiment code."""

from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib
import html
import json
import re

from .markdown import render
from .portable import embed_image, plain_entry, root_entry
from .pages import PRIMARY, write_pages

STATES = {
    "workspace": "Workspace",
    "reference": "Reference / setup",
    "study": "Paper study",
    "guideline": "Approved direction",
    "baseline": "Baseline candidate",
    "legacy": "Legacy / retrospective",
}
POLICY = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
    "img-src data: 'self'; font-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'"
)
NAV = PRIMARY


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Bundle:
    def __init__(self, root, evidence, output, saved=None):
        self.root, self.evidence, self.out = root, evidence, output
        self.site = root / "docs/site"
        self.base = root / "outputs/umr-astro-baseline-v1/static-20261024-01"
        self.legacy = root / "outputs/umr-legacy-index-20261024"
        self.saved = saved
        saved_sources = saved is not None
        self.inputs, self.outputs, self.unbundled, self.preserved = {}, {}, [], {}
        self.saved_sources, self.reused_sources, self.prior_inputs = (
            saved_sources,
            {},
            {},
        )
        prior = saved / "documentation/manifest.json" if saved else output / "documentation/manifest.json"
        if prior.exists():
            previous = json.loads(prior.read_text())
            self.preserved = previous.get("preserved_originals", {}) if saved is None else {}
            self.prior_inputs = previous.get("inputs", {})
            self.prior_inputs.update(previous.get("reused_source_snapshots", {}))
        self.catalog = json.loads(self.read(self.site / "catalog.json"))
        self.docs = self.catalog["documents"]
        self.paths = {d["path"]: d for d in self.docs}
        if len(self.paths) != len(self.docs) or len(
            {d["id"] for d in self.docs}
        ) != len(self.docs):
            raise ValueError("Duplicate source paths or document IDs")
        for d in self.docs:
            path = Path(d["path"])
            if path.is_absolute() or ".." in path.parts or not (self.root / path).resolve().is_relative_to(self.root):
                raise ValueError("Document source escapes source root: " + d["path"])
            if not re.fullmatch(r"[a-z0-9-]+", d["id"]) or d["state"] not in STATES:
                raise ValueError(f"Invalid document ID or state: {d}")
        self.css = self.read(self.site / "style.css").decode()

    def read(self, path: Path) -> bytes:
        original = str(path.relative_to(self.root))
        resolved = self.evidence / original if original.startswith("outputs/") else path
        if not resolved.exists() and self.saved_sources:
            archived = self.saved / "documentation/sources" / original
            expected = self.prior_inputs.get(original, {}).get("sha256")
            if not expected or not archived.is_file() or digest(archived.read_bytes()) != expected:
                raise ValueError("Missing or unverified saved source: " + original)
            self.reused_sources[original] = {"sha256": expected,
                "snapshot": "documentation/sources/" + original}
            return archived.read_bytes()
        data = resolved.read_bytes()
        self.inputs[original] = {"sha256": digest(data), "bytes": len(data),
            "root": "evidence" if original.startswith("outputs/") else "source"}
        return data

    def available(self, path):
        relative = path.relative_to(self.root)
        return self.evidence / relative if str(relative).startswith("outputs/") else path

    def write(self, relative: str, content: str | bytes):
        data = content.encode() if isinstance(content, str) else content
        path = self.out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        self.outputs[relative] = {"sha256": digest(data), "bytes": len(data)}

    def url(self, path: str) -> str:
        return "documentation/pages/" + self.paths[path]["id"] + ".html"

    def snapshot(self, path: Path) -> str:
        target = "documentation/sources/" + str(path.relative_to(self.root))
        self.write(target, self.read(path))
        return target

    def link(self, source: str, href: str, label: str, image: bool = False) -> str:
        parsed = urlsplit(html.unescape(href))
        text = html.escape(label)
        if parsed.scheme in ("http", "https"):
            return f'<a href="{html.escape(href, quote=True)}" rel="noreferrer" title="Online reference; internet required">{text} ↗</a>'
        if parsed.scheme or parsed.netloc:
            return text + " <small>(unsupported link; see original source)</small>"
        path = (
            ((self.root / source).parent / unquote(parsed.path)).resolve()
            if parsed.path
            else self.root / source
        )
        try:
            relative = str(path.relative_to(self.root))
        except ValueError:
            relative = ""
        prefix = "../../"
        available = self.available(path) if relative else path
        if not available.exists() and self.saved_sources and relative in self.prior_inputs:
            available = self.saved / "documentation/sources" / relative
        if relative in self.paths:
            target = prefix + self.url(relative)
            if parsed.fragment:
                target += "#" + parsed.fragment
        elif (
            relative
            and available.is_file()
            and available.stat().st_size < 4_000_000
            and path.suffix
            in {".json", ".jsonl", ".csv", ".md", ".txt", ".py", ".patch", ".bib"}
            and relative.split("/")[0]
            in {"docs", "references", "experiments", "configs", "outputs", "scripts"}
        ):
            target = prefix + self.snapshot(path)
        elif (
            image
            and relative
            and available.is_file()
            and path.suffix.lower() in {".png", ".jpg", ".svg"}
            and available.stat().st_size < 4_000_000
            and relative.split("/")[0] in {"docs", "experiments", "outputs"}
        ):
            target = prefix + self.snapshot(path)
            return f'<img loading="lazy" src="{embed_image(path, self.read(path))}" alt="{text}">'
        else:
            self.unbundled.append({"source": source, "target": href})
            return f'<span class="unbundled">{text} <small>(local artifact not bundled: <code>{html.escape(href)}</code>)</small></span>'
        return f'<a href="{html.escape(target, quote=True)}">{text}</a>'

    def source_notice(self):
        if self.saved_sources:
            return '<p class="source-notice">Saved evidence edition: missing canonical sources are read from hash-verified local snapshots. This is not a fresh environment or experiment validation.</p>'
        return ""

    def shell(
        self,
        title: str,
        body: str,
        prefix: str = "",
        script: str = "",
        toc: str = "",
        current: str = "",
    ) -> str:
        nav = "".join(
            f'<a href="{prefix}{key}.html"'
            + (' aria-current="page"' if current == key else "")
            + f">{label}</a>"
            for key, label in NAV
        )
        outline = (
            f'<aside class="page-toc"><details open><summary>On this page</summary><nav>{toc}</nav></details></aside>'
            if toc
            else ""
        )
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{POLICY}"><link rel="icon" href="data:,">
<title>{html.escape(title)} · Motion Studio</title><style>{self.css}</style></head><body>
<a class="skip" href="#content">Skip to content</a><header class="topbar">
<a class="brand" href="{prefix}docs.html">MOTION STUDIO <small>/ Documentation</small></a>
<span class="header-note">Local documentation</span></header>
<div class="layout"><aside class="sidebar"><p class="eyebrow">Contents</p><nav class="nav-links" aria-label="Documentation">{nav}</nav>
<p class="nav-note">Local evidence · 24 Oct 2026<br>Independent tools, shared records.<br>No experiment is run by this site.</p><p><a href="{prefix}supporting-records.html"{' aria-current="page"' if current == "supporting-records" else ""}>Supporting records</a></p></aside>
<main id="content">{self.source_notice()}{body}<footer>Motion Studio · Local documentation snapshot · Original sources remain authoritative.</footer></main>{outline}</div>{script}</body></html>'''

    def readers(self) -> list:
        search = []
        for doc in self.docs:
            source = self.read(self.root / doc["path"]).decode()
            raw = self.snapshot(self.root / doc["path"])
            content, headings = render(
                source,
                lambda href, label, image: self.link(doc["path"], href, label, image),
            )
            toc = "".join(
                f'<a href="#{anchor}">{html.escape(text)}</a>'
                for level, anchor, text in headings
                if level <= 2 and anchor != headings[0][1]
            )
            state = doc["state"]
            meta = f"""<div class="source-meta"><span class="badge {state}">{STATES[state]}</span>
<p>{html.escape(doc["description"])}</p><p>Source: <a href="../../{raw}">{html.escape(doc["path"])}</a></p>
<p>SHA-256: <code>{digest(source.encode())}</code></p></div>"""
            if state in {"legacy", "study", "guideline", "baseline"}:
                meta += '<p class="notice legacy">Historical wording is preserved. “Current,” “unborn,” and approval statements describe the source’s observation time. See <a href="../../supporting-records.html#record">current status and decision context</a>.</p>'
            body = f'<article class="reader">{meta}<details><summary>On this page</summary><nav class="toc">{toc}</nav></details>{content}</article>'
            self.write(
                self.url(doc["path"]), self.shell(doc["title"], body, "../../", toc=toc)
            )
            search.append(
                {
                    **doc,
                    "stateLabel": STATES[state],
                    "url": self.url(doc["path"]),
                    "text": source,
                }
            )
        return search

    def baseline(self) -> tuple[str, str, str]:
        data = json.loads(self.read(self.base / "evaluation/results.json"))
        arms = data["arms"]
        cards = []
        for key, title in [("g1", "G1"), ("astro", "Astro")]:
            arm = arms[key]
            rows = arm["per_segment"]
            total = sum(r["slots"] for r in rows)
            compatible = sum(r["compatible_zone_slots"] for r in rows)
            if (
                total != 4096
                or compatible != arm["compatible_slots"]
                or len(rows) != 19
            ):
                raise ValueError(f"Invalid baseline diagnostic: {key}")
            rate = compatible / total * 100
            cards.append(
                f'<div class="card"><span class="badge">SMPL-X → {title}</span><span class="stat">{rate:.2f}%</span><p>{compatible:,} / {total:,} compatible slots</p><div class="metricbar"><span style="width:{rate}%"></span></div></div>'
            )
        g1 = {r["source"]: r for r in arms["g1"]["per_segment"]}
        astro = {r["source"]: r for r in arms["astro"]["per_segment"]}
        rows = [
            [
                name,
                f"{g1[name]['compatible_zone_slots']} / {g1[name]['slots']}",
                f"{astro[name]['compatible_zone_slots']} / {astro[name]['slots']}",
            ]
            for name in sorted(g1)
        ]
        links = []
        for path, title in [
            (self.base / "evaluation/results.json", "Evaluation JSON"),
            (self.base / "provenance.json", "Run provenance"),
            (self.base / "artifact-manifest.json", "Artifact manifest"),
            (
                self.root / "experiments/umr-astro-baseline-v1/execution-status.json",
                "Execution status",
            ),
            (
                self.root / "experiments/umr-astro-baseline-v1/preservation-after.json",
                "Preservation record",
            ),
            (self.root / "configs/umr/experiment-dependencies.json", "Dependency pins"),
        ]:
            links.append(f'<a href="{self.snapshot(path)}">{title}</a>')
        return (
            '<div class="cards">' + "".join(cards) + "</div>",
            table(
                [
                    "Native19 segment",
                    "G1 compatible / slots",
                    "Astro compatible / slots",
                ],
                rows,
            ),
            " · ".join(links),
        )

    def home(self, search: list):
        baseline, segments, links = self.baseline()
        summary = json.loads(self.read(self.legacy / "summary.json"))
        legacy_rows = [
            json.loads(line)
            for line in self.read(self.legacy / "results.jsonl").decode().splitlines()
        ]
        if len(legacy_rows) != summary["normalized_arms"] or any(
            r["cohort_status"] != "legacy" for r in legacy_rows
        ):
            raise ValueError("Legacy index boundary or totals changed")
        registry = [
            [
                "static-20261024-01",
                "Baseline candidate",
                "2 static arms",
                "Single actor/seed; review before motion",
            ]
        ]
        for cohort in summary["cohorts"]:
            registry.append(
                [
                    cohort["cohort_id"],
                    "Legacy / retrospective",
                    f"{cohort['arms']} {cohort['task']} arms",
                    "Saved evidence; not rerun",
                ]
            )
        self.snapshot(self.legacy / "summary.json")
        self.snapshot(self.legacy / "results.jsonl")
        self.snapshot(self.legacy / "manifest.json")
        timeline = "".join(
            f'<li><time>{x["date"]}</time><h3>{html.escape(x["title"])}</h3><p>{html.escape(x["description"])}</p><a href="{self.url(x["source"])}">Read source record →</a></li>'
            for x in self.catalog["timeline"]
        )
        catalog = json.loads(
            self.read(self.root / "experiments/umr-binding-report/catalog.json")
        )
        selected = [
            (k, p)
            for k, p in catalog["figures"].items()
            if k in ("canonical_selected", "canonical_matched")
        ]
        if not selected:
            selected = [
                (k, p) for k, p in catalog["figures"].items() if "canonical" in k
            ][:2]
        media = []
        for key, path in selected:
            target = "documentation/media/" + Path(path).name
            image_data = self.read(self.root / path)
            self.write(target, image_data)
            image_url = embed_image(Path(path), image_data)
            media.append(
                f'<figure><a href="{target}"><img loading="lazy" src="{image_url}" alt="Legacy saved comparison: {html.escape(key.replace("_", " "))}"></a><figcaption>Legacy saved figure · {html.escape(key)}. Source: <code>{html.escape(path)}</code>. Open full size to inspect the original labels; this is not the new baseline.</figcaption></figure>'
            )
        listing = "".join(
            f'<li><span class="badge {d["state"]}">{STATES[d["state"]]}</span> <a href="{d["url"]}">{html.escape(d["title"])}</a><p class="small">{html.escape(d["description"])}</p></li>'
            for d in search
        )
        values = {
            "BASELINE": baseline,
            "SEGMENTS": segments,
            "BASELINE_LINKS": links,
            "REGISTRY": table(
                ["Record / cohort", "State", "Scope", "Interpretation"], registry
            ),
            "LEGACY_COUNTS": f"{summary['normalized_arms']} arms ({summary['static_arms']} static + {summary['motion_arms']} motion) and {summary['segment_rows']:,} segment rows",
            "MEDIA": "".join(media),
            "TIMELINE": timeline,
            "DOCUMENT_LIST": listing,
        }
        write_pages(self, self.site, values, search)

    def decorate_viewer(self):
        """Preserve old generated HTML; add navigation and remove CDN runtime needs."""
        paths = [self.out / "index.html", *sorted((self.out / "inspectors").glob("*/index.html"))]
        orbit = self.out / "inspectors/canonical-motion/vendor/OrbitControls.js"
        # Reuse only matching already-local modules. No package download.
        three = self.out / "inspectors/canonical-motion/vendor/three.module.js"
        if "const REVISION = '165'" not in three.read_bytes().decode():
            raise ValueError("Expected the saved Three.js r165 module")
        self.write("documentation/vendor/three.module.js", three.read_bytes())
        self.write("documentation/vendor/controls/OrbitControls.js", orbit.read_bytes())
        for path in paths:
            relative = str(path.relative_to(self.out))
            current = path.read_bytes().decode()
            marker = "<!-- motion-docs-overlay -->"
            if marker in current:
                current = (
                    (self.out / self.preserved[relative]["archive"]).read_bytes().decode()
                )
            original_hash = digest(current.encode())
            archive = "history/documentation-scaffold/" + original_hash + "/" + relative
            self.write(archive, current)
            self.preserved[relative] = {
                "original_sha256": original_hash,
                "archive": archive,
            }
            is_main = path == self.out / "index.html"
            href = "docs.html" if is_main else "../../docs.html"
            banner = f'''{marker}<div style="background:#fff2da;color:#563d1a;padding:12px 20px;font:14px/1.5 system-ui;border-bottom:1px solid #ba965f"><strong>self.legacy / 历史记录</strong> · Retrospective evidence, not the new baseline. <a style="color:#075c56" href="{href}">Motion Studio documentation / 文档 →</a></div>'''
            if not is_main:
                banner = banner.replace(
                    "background:#fff2da;",
                    "position:fixed;bottom:0;left:0;right:0;z-index:1000;background:#fff2da;",
                )
            if is_main:
                # Persistent context inside the existing sticky header, including deep links.
                current = current.replace(
                    '<div class="top-actions">',
                    '<a style="color:#ffe2a8;font-size:13px" href="docs.html">self.legacy · Documentation / 文档 →</a><div class="top-actions">',
                    1,
                )
            policy = "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'"
            current = current.replace(
                "<head>",
                '<head><meta http-equiv="Content-Security-Policy" content="'
                + policy
                + '">',
                1,
            )
            current = current.replace("<body>", "<body>" + banner, 1)
            current = current.replace(
                "https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js",
                "../../documentation/vendor/three.module.js",
            ).replace(
                "https://cdn.jsdelivr.net/npm/three@0.165.0/examples/jsm/",
                "../../documentation/vendor/",
            )
            self.write(relative, current)
        for relative, info in self.preserved.items():
            archive = self.out / info["archive"]
            if digest(archive.read_bytes()) != info["original_sha256"]:
                raise ValueError("Preserved original changed: " + relative)
            self.outputs[relative] = {
                "sha256": digest((self.out / relative).read_bytes()),
                "bytes": (self.out / relative).stat().st_size,
            }

    def build(self):
        if not (self.out / "index.html").is_file():
            raise FileNotFoundError("Existing research viewer required at " + str(self.out))
        # Validate registered sources before writing any page.
        for doc in self.docs:
            self.read(self.root / doc["path"])
        for path in sorted((self.root / "motion_studio/documentation").glob("*.py")):
            self.read(path)
        self.read(self.root / "scripts/build_docs.py")
        self.read(self.root / "scripts/verify_docs.py")
        self.read(self.root / "scripts/docs_site/test_search.cjs")
        self.write(
            "documentation/THIRD_PARTY_NOTICES.md",
            self.read(self.site / "THIRD_PARTY_NOTICES.md"),
        )
        search = self.readers()
        self.home(search)
        self.decorate_viewer()
        self.write("docs-basic.html", plain_entry((self.out / "docs.html").read_text()))
        manifest = {
            "schema_version": 1,
            "reused_source_snapshots": self.reused_sources,
            "source_mode": "saved snapshots for missing sources"
            if self.saved_sources
            else "canonical workspace sources",
            "snapshot_date": self.catalog["snapshot_date"],
            "documents": len(self.docs),
            "new_experiments": 0,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "preserved_originals": self.preserved,
            "unbundled_links": self.unbundled,
            "limitations": [
                "Original external citations require internet.",
                "3D inspectors require local HTTP.",
                "TeX remains readable source notation.",
                "Fresh clone requires the existing local report/evidence artifacts.",
            ],
        }
        (self.out / "documentation/manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        )
        return manifest


def table(headers: list, rows: list) -> str:
    return (
        '<div class="table-scroll" tabindex="0"><table><thead><tr>'
        + "".join('<th scope="col">' + html.escape(x) + "</th>" for x in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>"
            + "".join("<td>" + html.escape(str(x)) + "</td>" for x in row)
            + "</tr>"
            for row in rows
        )
        + "</tbody></table></div>"
    )
