"""The web app's pages (web/) keep its rules (web/README.md).

- Nothing is loaded from outside the site: no page names an http:// or
  https:// address at all, so it fetches no script, style, font or data
  from anywhere else, and sends nothing anywhere.
- The plant page reads the shared vectors by default, from where they are
  in the repository.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


class WebPages(unittest.TestCase):
    def pages(self):
        found = sorted(WEB.rglob("*.html"))
        self.assertTrue(found, "no pages in web/")
        return found

    def test_no_page_loads_anything_from_outside(self):
        for page in self.pages():
            text = page.read_text(encoding="utf-8")
            for scheme in ("http://", "https://", "//cdn", "//fonts"):
                self.assertNotIn(scheme, text, f"{page.relative_to(ROOT)}")

    def test_the_plant_page_reads_the_shared_vectors(self):
        page = WEB / "plant" / "index.html"
        text = page.read_text(encoding="utf-8")
        default = "../../vectors/plant-world.json"
        self.assertIn(default, text)
        self.assertTrue((page.parent / default).resolve().is_file())


if __name__ == "__main__":
    unittest.main()
