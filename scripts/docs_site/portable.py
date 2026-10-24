"""Publish a root entry from the existing bundle, with no redirect or runtime I/O."""

import base64
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def embed_image(path: Path, data: bytes) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}[
        path.suffix.lower()
    ]
    return "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")


def root_entry(document: str, bundle_prefix: str, root_prefix: str = "") -> str:
    """Rebase ordinary file links and embedded search URLs to the project root.

    No <base>, fetch, modules, service worker, redirect or localStorage is used.
    The original bundle entry and its page links remain usable independently.
    """

    def local_url(value: str) -> str:
        if urlsplit(value).scheme or value.startswith(("#", "//")):
            return value
        if value.split("#", 1)[0] in {"docs.html", "docs-basic.html"}:
            return root_prefix + value
        return bundle_prefix + value

    def attribute(match):
        return (
            match[1] + html.escape(local_url(html.unescape(match[2])), quote=True) + '"'
        )

    # Source text in the embedded JSON escapes '<'; this visits markup attributes only.
    document = re.sub(r'((?:href|src)=")([^"\\]*)"', attribute, document)
    pattern = r'(<script id="search-data" type="application/json">)(.*?)(</script>)'

    def search(match):
        records = json.loads(match[2])
        for record in records:
            record["url"] = local_url(record["url"])
        return (
            match[1]
            + json.dumps(records, ensure_ascii=False).replace("<", "\\u003c")
            + match[3]
        )

    return re.sub(pattern, search, document, flags=re.DOTALL)


class _PlainReader(HTMLParser):
    """Strip enhancements from our generated markup; retain static reading content."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.skip = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skip:
            if tag == self.skip:
                self.depth += 1
            return
        if (
            tag in {"script", "style", "noscript"}
            or attrs.get("id") == "search-controls"
        ):
            self.skip, self.depth = tag, 1
        elif tag == "link" or (tag == "meta" and "http-equiv" in attrs):
            return
        elif tag == "img":
            self.parts.append(html.escape(attrs.get("alt", "Saved image")))
        else:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip:
                self.depth -= 1
                if self.depth == 0:
                    self.skip = None
        else:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def plain_entry(document: str) -> str:
    parser = _PlainReader()
    parser.feed(document)
    plain = "".join(parser.parts).replace('href="docs.html', 'href="docs-basic.html')
    return "<!doctype html>\n" + plain
