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
<p class="nav-note">Local documentation<br>Independent tools, shared records.<br>No experiment is run by this site.</p><p><a href="{prefix}supporting-records.html"{' aria-current="page"' if current == "supporting-records" else ""}>Supporting records</a></p></aside>
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

    def home(self, search: list):
        timeline = "".join(
            f'<li><time>{x["date"]}</time><h3>{html.escape(x["title"])}</h3><p>{html.escape(x["description"])}</p><a href="{self.url(x["source"])}">Read source record →</a></li>'
            for x in self.catalog["timeline"]
        )
        listing = "".join(
            f'<li><span class="badge {d["state"]}">{STATES[d["state"]]}</span> <a href="{d["url"]}">{html.escape(d["title"])}</a><p class="small">{html.escape(d["description"])}</p></li>'
            for d in search
        )
        values = {
            "TIMELINE": timeline,
            "DOCUMENT_LIST": listing,
        }
        write_pages(self, self.site, values, search)

    def build(self):
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
                "TeX remains readable source notation.",
            ],
        }
        (self.out / "documentation/manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        )
        return manifest
