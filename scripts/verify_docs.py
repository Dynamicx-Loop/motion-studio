"""Check built documentation, source hashes, links and offline runtime contracts."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import base64
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/umr-binding-report"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path, self.ids, self.links, self.runtime, self.text = (
            path,
            set(),
            [],
            [],
            [],
        )
        self.feed(path.read_text())

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


def main():
    manifest = json.loads((OUT / "documentation/manifest.json").read_text())
    for name, info in manifest["inputs"].items():
        assert sha(ROOT / name) == info["sha256"], ("changed source", name)
    for name, info in manifest.get("reused_source_snapshots", {}).items():
        assert sha(ROOT / info["snapshot"]) == info["sha256"], (
            "changed saved source",
            name,
        )
    for name, info in manifest["outputs"].items():
        assert sha(OUT / name) == info["sha256"], ("changed output", name)
    for name, info in manifest["preserved_originals"].items():
        assert sha(OUT / info["archive"]) == info["original_sha256"], ("archive", name)
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
                missing_fragments.append((str(path.relative_to(ROOT)), reference))
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
        assert (
            "outputs/umr-binding-report/" + name + ".html"
            in parsed[(ROOT / "docs.html").resolve()].links
        )
    assert (ROOT / "docs.html").read_text().count("<h1>") == 1
    assert "<script" not in (ROOT / "docs.html").read_text()
    alias = parsed[(ROOT / compatibility["path"]).resolve()]
    for name in ("installation", "quick-start", "umr-experiments"):
        assert "../../outputs/umr-binding-report/" + name + ".html" in alias.links
    assert "../../docs.html" in alias.links
    assert "{{" not in alias.path.read_text()
    assert (
        "<style>" in alias.path.read_text() and "<script" not in alias.path.read_text()
    )
    figure_hashes = {
        hashlib.sha256(base64.b64decode(url.split(",", 1)[1])).hexdigest()
        for url in parsed[(OUT / "supporting-records.html").resolve()].runtime
    }
    catalog = json.loads(
        (ROOT / "experiments/umr-binding-report/catalog.json").read_text()
    )
    assert figure_hashes == {
        sha(ROOT / catalog["figures"][key])
        for key in ("canonical_selected", "canonical_matched")
    }
    # Inspector modules are now local and their prior HTML is archived.
    for path in (OUT / "inspectors").glob("*/index.html"):
        text = path.read_text()
        assert "cdn.jsdelivr.net" not in text, path
        assert "motion-docs-overlay" in text, path
    summary = json.loads(
        (ROOT / "outputs/umr-legacy-index-20261024/summary.json").read_text()
    )
    assert (
        summary["normalized_arms"],
        summary["segment_rows"],
        summary["new_baseline_arms"],
    ) == (76, 1924, 0)
    data = json.loads(
        (
            ROOT
            / "outputs/umr-astro-baseline-v1/static-20261024-01/evaluation/results.json"
        ).read_text()
    )
    assert [data["arms"][a]["compatible_slots"] for a in ["g1", "astro"]] == [
        3562,
        2327,
    ]
    home = (OUT / "umr-experiments.html").read_text() + support_text
    assert all(
        x in home
        for x in [
            "86.96%",
            "56.81%",
            "1,924",
            "not a motion score",
            "SOMA-X",
            "Blocked: matched actor/motion/rig",
        ]
    )
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
        "embedded_figures_match_saved_sources": len(figure_hashes),
        "runtime_resource_reads_required": 0,
        "browser_file_open_verified": False,
        "source_hashes_verified": len(manifest["inputs"]),
        "output_hashes_verified": len(manifest["outputs"]),
        "local_links_verified": links,
        "missing_fragments": missing_fragments,
        "remote_core_runtime_dependencies": remote_runtime,
        "preserved_html_originals": len(manifest["preserved_originals"]),
        "baseline_compatible_slots": {"g1": 3562, "astro": 2327},
        "legacy_arms": 76,
        "legacy_segment_rows": 1924,
        "new_experiments_run": 0,
    }
    (OUT / "documentation/verification.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
