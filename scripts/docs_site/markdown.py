"""Small, dependency-free Markdown reader for the project's documentation subset.

Raw HTML is escaped. Fences (including historical Mermaid/TeX) remain readable
source. Link rewriting belongs to the bundle builder, not the renderer.
"""

import html
import re
from collections.abc import Callable


def slug(text: str) -> str:
    return re.sub(r"[^\w\- ]", "", text.lower()).strip().replace(" ", "-")


def inline(text: str, link: Callable[[str, str, bool], str]) -> str:
    tokens: list[str] = []

    def hold(value: str) -> str:
        tokens.append(value)
        return f"\x00{len(tokens) - 1}\x00"

    text = re.sub(
        r"`([^`]+)`", lambda m: hold("<code>" + html.escape(m[1]) + "</code>"), text
    )
    text = re.sub(
        r'(!?)\[([^\]]+)\]\(([^\s]+?)(?:\s+"[^"]*")?\)',
        lambda m: hold(link(m[3], m[2], bool(m[1]))),
        text,
    )
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    for index, token in enumerate(tokens):
        text = text.replace(f"\x00{index}\x00", token)
    return text


def render(source: str, link: Callable[[str, str, bool], str]) -> tuple[str, list]:
    lines = source.splitlines()
    blocks, headings, seen = [], [], {}
    i = 0

    def fmt(value):
        return inline(value, link)

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append(
                "<pre><code>" + html.escape("\n".join(code)) + "</code></pre>"
            )
            i += 1
            continue
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level, text = len(match[1]), match[2]
            base = slug(text)
            count = seen.get(base, 0)
            seen[base] = count + 1
            anchor = base + (f"-{count}" if count else "")
            headings.append((level, anchor, text))
            blocks.append(f'<h{level} id="{anchor}">{fmt(text)}</h{level}>')
            i += 1
            continue
        if (
            i + 1 < len(lines)
            and "|" in line
            and re.match(r"^\s*\|?\s*:?-{3}", lines[i + 1])
        ):

            def cells(row):
                return [fmt(x.strip()) for x in row.strip().strip("|").split("|")]

            headers = cells(line)
            rows = []
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(
                    "<tr>"
                    + "".join("<td>" + x + "</td>" for x in cells(lines[i]))
                    + "</tr>"
                )
                i += 1
            blocks.append(
                '<div class="table-scroll" tabindex="0"><table><thead><tr>'
                + "".join('<th scope="col">' + x + "</th>" for x in headers)
                + "</tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table></div>"
            )
            continue
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\d+\.", line))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and re.match(r"^\s*(?:[-*]|\d+\.)\s+", lines[i]):
                parts = [re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i])]
                i += 1
                while (
                    i < len(lines)
                    and lines[i].startswith("  ")
                    and not re.match(r"^\s*(?:[-*]|\d+\.)\s+", lines[i])
                ):
                    parts.append(lines[i].strip())
                    i += 1
                items.append("<li>" + fmt(" ".join(parts)) + "</li>")
            blocks.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        if re.match(r"^\s*---+\s*$", line):
            blocks.append("<hr>")
            i += 1
            continue
        if line.startswith(">"):
            blocks.append("<blockquote>" + fmt(line.lstrip("> ")) + "</blockquote>")
            i += 1
            continue
        paragraph = [line]
        i += 1
        while (
            i < len(lines)
            and lines[i].strip()
            and not re.match(r"^(#|```|>|[-*] |\d+\. |\|)", lines[i])
        ):
            paragraph.append(lines[i])
            i += 1
        blocks.append("<p>" + fmt("\n".join(paragraph)) + "</p>")
    return "\n".join(blocks), headings
