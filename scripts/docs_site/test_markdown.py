"""Observable reading contracts for the small local Markdown renderer."""

import unittest
from .markdown import render


class MarkdownReadingTests(unittest.TestCase):
    def test_wrapped_paragraph_emphasis(self):
        content, _ = render(
            "A **strong claim\nacross lines** remains readable.",
            lambda href, label, image: label,
        )
        self.assertIn("<strong>strong claim\nacross lines</strong>", content)

    def test_table_and_duplicate_heading_anchors(self):
        content, headings = render(
            "# Note\n## Evidence\n## Evidence\n\n| A | B |\n| --- | ---: |\n| 3 | 4 |",
            lambda href, label, image: label,
        )
        self.assertEqual([h[1] for h in headings], ["note", "evidence", "evidence-1"])
        self.assertIn('<th scope="col">A</th>', content)
        self.assertIn("<td>3</td><td>4</td>", content)

    def test_code_and_raw_html_are_inert(self):
        content, _ = render(
            "<script>alert(1)</script>\n\n```sh\nrm fake-file\n```\n\n`<img onerror=x>`",
            lambda href, label, image: label,
        )
        self.assertNotIn("<script>", content)
        self.assertNotIn("<img", content)
        self.assertIn("&lt;script&gt;", content)
        self.assertIn("<pre><code>rm fake-file</code></pre>", content)

    def test_links_are_resolved_by_bundle_not_executed(self):
        observed = []

        def link(href, label, image):
            observed.append((href, label, image))
            return "<a>resolved</a>"

        content, _ = render(
            "[source](../record.md#evidence) and ![figure](plot.png)", link
        )
        self.assertEqual(
            observed,
            [("../record.md#evidence", "source", False), ("plot.png", "figure", True)],
        )
        self.assertEqual(content, "<p><a>resolved</a> and <a>resolved</a></p>")


if __name__ == "__main__":
    unittest.main()
