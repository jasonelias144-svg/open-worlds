"""The web app's pages (web/) keep its rules (web/README.md).

- Nothing is loaded from outside the site, and nothing is sent anywhere.
  Each page carries a Content-Security-Policy that the browser enforces:
  nothing by default, its own inline script and style, and connections
  only to its own site. And no page names an outside address, or a way
  to send one (a beacon, a socket, an event stream).
- The plant page reads the shared vectors by default, from where they are
  in the repository, and takes ?log= only as a path on its own site.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
CSP = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">')


class WebPages(unittest.TestCase):
    def pages(self):
        found = sorted(WEB.rglob("*.html"))
        self.assertTrue(found, "no pages in web/")
        return found

    def test_each_page_has_a_policy_the_browser_enforces(self):
        for page in self.pages():
            m = CSP.search(page.read_text(encoding="utf-8"))
            self.assertTrue(m, f"{page.relative_to(ROOT)}: no CSP")
            rules = {r.split()[0]: r.split()[1:]
                     for r in m.group(1).split(";") if r.strip()}
            self.assertEqual(rules.get("default-src"), ["'none'"])
            self.assertEqual(rules.get("connect-src"), ["'self'"])
            for name, sources in rules.items():
                for source in sources:
                    self.assertNotRegex(source, r"^(https?:|//|\*)",
                                        f"{page.name}: {name} {source}")

    def test_no_page_names_an_outside_address(self):
        for page in self.pages():
            text = page.read_text(encoding="utf-8")
            for bad in ("http://", "https://", "wss://", "ws://",
                        "sendBeacon", "WebSocket", "EventSource"):
                self.assertNotIn(bad, text, f"{page.relative_to(ROOT)}")
            self.assertNotRegex(text, r"""["'(=]\s*//[A-Za-z0-9]""",
                                f"{page.relative_to(ROOT)}: //host")

    def test_the_plant_page_reads_the_shared_vectors(self):
        page = WEB / "plant" / "index.html"
        text = page.read_text(encoding="utf-8")
        default = "../../vectors/plant-world.json"
        self.assertIn(default, text)
        self.assertTrue((page.parent / default).resolve().is_file())
        self.assertIn("u.origin === location.origin", text)


if __name__ == "__main__":
    unittest.main()
