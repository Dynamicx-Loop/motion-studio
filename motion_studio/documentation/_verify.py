"""Check built documentation, source hashes, links and offline runtime contracts."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re



class Page(HTMLParser):
    def __init__(self, path, content=None):
        super().__init__()
        self.path, self.ids, self.links, self.runtime, self.text = (
            path,
            set(),
            [],
            [],
            [],
        )
        self.feed(path.read_text() if content is None else content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            assert attrs["id"] not in self.ids, (self.path, "duplicate", attrs["id"])
            self.ids.add(attrs["id"])
        if attrs.get("href"):
            self.links.append(attrs["href"])
        if tag in {"img", "script", "iframe", "source", "video", "audio"} and attrs.get(
            "src"
        ):
            self.runtime.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.runtime.append(attrs["href"])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _link_destinations(page):
    """Resolve local page links independently of a publication alias's spelling."""
    destinations = set()
    for reference in page.links:
        url = urlsplit(reference)
        if not url.scheme and not url.netloc:
            destinations.add((page.path.parent / unquote(url.path)).resolve()
                             if url.path else page.path.resolve())
    return destinations


def verify_edition(output, *, source_root=None, evidence_root=None):
    OUT = Path(output).absolute()
    manifest = json.loads((OUT / "documentation/manifest.json").read_text())
    ROOT = Path(source_root or manifest["source_root"]).resolve()
    EVIDENCE = Path(evidence_root or manifest["evidence_root"]).resolve()

    for name, info in manifest["inputs"].items():
        assert sha((EVIDENCE if info.get("root") == "evidence" else ROOT) / name) == info["sha256"], ("changed source", name)
    for name, info in manifest.get("reused_source_snapshots", {}).items():
        assert sha(OUT / info["snapshot"]) == info["sha256"], (
            "changed saved source",
            name,
        )
    for name, info in manifest["outputs"].items():
        assert sha(OUT / name) == info["sha256"], ("changed output", name)
    for name, info in manifest["preserved_originals"].items():
        assert sha(OUT / info["archive"]) == info["original_sha256"], ("archive", name)
    for name, target in manifest.get("portable_links", {}).items():
        assert (OUT / name).is_symlink() and __import__('os').readlink(OUT / name) == target
        assert (OUT / name).resolve().is_relative_to(OUT.resolve())
    for name, info in manifest["preserved_originals"].items():
        original_ids = set(re.findall(r'id=[\"\']([^\"\']+)', (OUT / info['archive']).read_text()))
        current_ids = set(re.findall(r'id=[\"\']([^\"\']+)', (OUT / name).read_text()))
        assert original_ids <= current_ids, ('legacy anchors', name)
    entry = manifest["root_entry"]
    assert entry["path"] == "docs.html"
    assert sha(ROOT / entry["path"]) == entry["sha256"]
    plain = manifest["plain_entry"]
    assert sha(ROOT / plain["path"]) == plain["sha256"]
    compatibility = manifest["compatibility_entry"]
    assert sha(ROOT / compatibility["path"]) == compatibility["sha256"]
    pages = [
        ROOT / "docs.html",
        OUT / "docs.html",
        ROOT / "docs-basic.html",
        OUT / "docs-basic.html",
        ROOT / compatibility["path"],
        *[
            OUT / (name + ".html")
            for name in (
                "installation",
                "quick-start",
                "umr-experiments",
                "supporting-records",
            )
        ],
        *sorted((OUT / "documentation/pages").glob("*.html")),
    ]
    parsed = {p.resolve(): Page(p) for p in pages}
    links, remote_runtime, missing_fragments = 0, [], []
    for path, page in parsed.items():
        if path.name != "docs-basic.html":
            assert "connect-src 'none'" in path.read_text()
        for reference in page.links + page.runtime:
            url = urlsplit(reference)
            if url.scheme in {"http", "https", "data"}:
                continue
            assert not url.scheme and not url.netloc, (path, reference)
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            assert target.exists(), ("missing link", path, reference)
            if (
                target in parsed
                and url.fragment
                and unquote(url.fragment) not in parsed[target].ids
            ):
                missing_fragments.append((str(path), reference))
            links += 1
        remote_runtime.extend(
            x for x in page.runtime if urlsplit(x).scheme in {"http", "https"}
        )
    assert not missing_fragments, ("missing fragments", missing_fragments)
    assert not remote_runtime
    # This is filesystem validation of file-open dependencies, not browser navigation.
    for page in parsed.values():
        assert all(url.startswith("data:") for url in page.runtime), page.path
        text = page.path.read_text()
        assert "<base " not in text and 'http-equiv="refresh"' not in text
        for script in re.findall(r"<script>(.*?)</script>", text, re.DOTALL):
            assert not re.search(
                r"\b(fetch|XMLHttpRequest|WebSocket|Worker)\s*\(|\bimport\s|serviceWorker|localStorage",
                script,
            )
    support_text = (OUT / "supporting-records.html").read_text()
    # Reading is authored HTML, not a script-generated application shell.
    for path in pages:
        source = path.read_text()
        body = re.search(r"<main[^>]*>(.*?)</main>", source, re.DOTALL)[1]
        assert "<h1" in body and len(body) > 1000, ("empty reader", path)
        assert not re.search(r"<main[^>]*(?:hidden|display:\s*none)", source)
    for path in (ROOT / "docs-basic.html", OUT / "docs-basic.html"):
        source = path.read_text()
        assert not re.search(r"<(?:script|style|img|iframe|link)\b", source)
        assert "http-equiv" not in source and 'id="search-controls"' not in source
    index = json.loads(
        re.search(
            r'<script id="search-data" type="application/json">(.*?)</script>',
            support_text,
            re.DOTALL,
        )[1]
    )
    for doc in index:
        assert doc["url"].startswith("documentation/pages/")
        assert (OUT / doc["url"]).is_file()
        assert doc["url"] in parsed[(OUT / "supporting-records.html").resolve()].links
    for name, title in [
        ("installation", "Installation"),
        ("quick-start", "Quick Start"),
        ("umr-experiments", "UMR Experiments"),
    ]:
        source = (OUT / (name + ".html")).read_text()
        assert source.count("<h1>") == 1 and f"<h1>{title}</h1>" in source
        assert f'href="{name}.html" aria-current="page"' in source
        assert "<script" not in source
        assert (OUT / (name + ".html")).resolve() in _link_destinations(
            parsed[(ROOT / "docs.html").resolve()])
    assert (ROOT / "docs.html").read_text().count("<h1>") == 1
    assert "<script" not in (ROOT / "docs.html").read_text()
    alias = parsed[(ROOT / compatibility["path"]).resolve()]
    for name in ("installation", "quick-start", "umr-experiments"):
        assert (OUT / (name + ".html")).resolve() in _link_destinations(alias)
    assert (ROOT / "docs.html").resolve() in _link_destinations(alias)
    assert "{{" not in alias.path.read_text()
    assert (
        "<style>" in alias.path.read_text() and "<script" not in alias.path.read_text()
    )
    primary = (OUT / "umr-experiments.html").read_text()
    assert "Standard setup" in primary
    assert "static-20261024-01" not in primary
    assert all(doc["state"] != "legacy" for doc in index)
    assert "static-20261024-01" not in support_text.split('<script id="search-data"', 1)[0]
    assert not (OUT / "inspectors").exists()
    result = {
        "documents": len(index),
        "source_mode": manifest.get("source_mode"),
        "reused_source_snapshots_verified": len(
            manifest.get("reused_source_snapshots", {})
        ),
        "root_entry": "docs.html",
        "compatibility_entry": compatibility["path"],
        "plain_entry": "docs-basic.html",
        "static_library_links_without_javascript": len(index),
        "supporting_record_search_destinations": len(index),
        "separate_primary_pages": 3,
        "root_landing_has_no_script": True,
        "runtime_resource_reads_required": 0,
        "browser_file_open_verified": False,
        "source_hashes_verified": len(manifest["inputs"]),
        "output_hashes_verified": len(manifest["outputs"]),
        "local_links_verified": links,
        "missing_fragments": missing_fragments,
        "remote_core_runtime_dependencies": remote_runtime,
        "preserved_html_originals": len(manifest["preserved_originals"]),
        "new_experiments_run": 0,
    }
    for name, info in manifest.get("preserved_entries", {}).items():
        assert sha(OUT / info["archive"]) == info["original_sha256"], ("preserved entry", name)
    return result


def validate_staged_reading(stage, destination, root, entries):
    """Check final relative destinations while bytes still live in staging."""
    core = ['docs.html', 'docs-basic.html', 'installation.html', 'quick-start.html',
            'umr-experiments.html', 'supporting-records.html']
    pages = {path.resolve(): Page(path) for path in [
        *(stage / name for name in core),
        *sorted((stage / 'documentation/pages').glob('*.html'))]}
    pages.update({(root / name).resolve(): Page(root / name, content)
                  for name, content in entries.items()})
    for path, page in pages.items():
        for reference in page.links + page.runtime:
            url = urlsplit(reference)
            if url.scheme in {'http', 'https', 'data'}:
                continue
            if url.scheme or url.netloc:
                raise ValueError(f'Unsupported reading link: {path}: {reference}')
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if target.is_relative_to(destination):
                target = stage / target.relative_to(destination)
            if target not in pages and not target.exists():
                raise ValueError(f'Missing reading link: {path}: {reference}')
            if target in pages and url.fragment and unquote(url.fragment) not in pages[target].ids:
                raise ValueError(f'Missing reading anchor: {path}: {reference}')
        if any(urlsplit(url).scheme in {'http', 'https'} for url in page.runtime):
            raise ValueError(f'Remote reading dependency: {path}')
        if not all(url.startswith('data:') for url in page.runtime):
            raise ValueError(f'Unbundled reading dependency: {path}')
