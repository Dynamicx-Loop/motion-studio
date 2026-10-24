"""Assemble separate static guide pages using one shared navigation shell."""

import html
import json
import re

PRIMARY = [
    ("installation", "Installation"),
    ("quick-start", "Quick Start"),
    ("umr-experiments", "UMR Experiments"),
]
TOC = {
    "installation": [
        ("prerequisites", "Prerequisites"),
        ("legion-setup", "Legion setup"),
    ],
    "quick-start": [
        ("open-docs", "Read documentation"),
        ("read-plan", "Review the plan"),
    ],
    "umr-experiments": [
        ("method", "Study guideline"),
        ("baseline", "Current evidence"),
    ],
    "supporting-records": [
        ("registry", "Registry"),
        ("media", "Legacy media"),
        ("record", "Research record"),
        ("library", "Search records"),
        ("maintain", "Use and update"),
    ],
}


def write_pages(bundle, site, values, search):
    templates = {"docs": bundle.read(site / "templates/overview.html").decode()}
    for key, _ in [*PRIMARY, ("supporting-records", "Supporting records")]:
        templates[key] = bundle.read(site / "pages" / (key + ".html")).decode()
    owners = {}
    # Actual section ownership determines cross-page fragment links.
    for key, body in templates.items():
        if key != "docs":
            owners.update({anchor: key for anchor in re.findall(r'id="([^"]+)"', body)})
    data = json.dumps(search, ensure_ascii=False).replace("<", "\\u003c")
    script = f'<script id="search-data" type="application/json">{data}</script><script>{bundle.read(site / "search.js").decode()}</script>'
    titles = dict(
        PRIMARY,
        **{
            "docs": "Motion Studio documentation",
            "supporting-records": "Supporting records",
        },
    )
    for key, body in templates.items():
        body = re.sub(r"\{\{DOC:([^}]+)\}\}", lambda m: bundle.url(m[1]), body)
        for name, value in values.items():
            body = body.replace("{{" + name + "}}", value)
        if "{{" in body:
            raise ValueError("Unresolved page template token: " + key)

        def destination(match):
            anchor = match[1]
            owner = owners.get(anchor, key)
            return f'href="{owner + ".html" if owner != key else ""}#{anchor}"'

        body = re.sub(r'href="#([^"]+)"', destination, body)
        toc = "".join(
            f'<a href="#{anchor}">{html.escape(label)}</a>'
            for anchor, label in TOC.get(key, [])
        )
        bundle.write(
            key + ".html",
            bundle.shell(
                titles[key],
                body,
                script=script if key == "supporting-records" else "",
                toc=toc,
                current=key,
            ),
        )
