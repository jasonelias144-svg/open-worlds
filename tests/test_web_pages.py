"""The web app's pages (web/) keep its rules (web/README.md).

- Nothing is loaded from outside the site, and nothing is sent anywhere.
  Each page carries a Content-Security-Policy that the browser enforces:
  nothing by default, its own inline script and style, scripts from its
  own site, and connections only to its own site. And no page names an
  outside address, or a way to send one (a beacon, a socket, an event
  stream).
- A script a page loads is a file of the web app, named by a relative
  path: the shared checks (web/lib/checks.js) and the WASI shim
  (web/lib/wasi.js), which tests/web/ runs. A page may compile
  WebAssembly ('wasm-unsafe-eval'), but never evaluate text as script
  ('unsafe-eval').
- The plant page reads the shared vectors by default, from where they are
  in the repository, and takes ?log= only as a path on its own site. The
  map reads the Ur-world's garden from the shared vectors.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
CSP = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">')
SCRIPT_SRC = re.compile(r'<script[^>]*\ssrc="([^"]*)"')


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
        scripts = sorted(WEB.rglob("*.js"))
        self.assertTrue(scripts, "no scripts in web/")
        for page in self.pages() + scripts:
            text = page.read_text(encoding="utf-8")
            for bad in ("http://", "https://", "wss://", "ws://",
                        "sendBeacon", "WebSocket", "EventSource"):
                self.assertNotIn(bad, text, f"{page.relative_to(ROOT)}")
            self.assertNotRegex(text, r"""["'(=]\s*//[A-Za-z0-9]""",
                                f"{page.relative_to(ROOT)}: //host")

    def test_each_script_a_page_loads_is_a_file_of_the_web_app(self):
        loaded = set()
        for page in self.pages():
            for src in SCRIPT_SRC.findall(page.read_text(encoding="utf-8")):
                self.assertRegex(src, r"^[A-Za-z0-9._/-]+$", f"{page.name}: {src}")
                self.assertFalse(src.startswith("/"), f"{page.name}: {src}")
                target = (page.parent / src).resolve()
                self.assertTrue(target.is_relative_to(WEB.resolve()), src)
                self.assertTrue(target.is_file(), src)
                loaded.add(target)
        self.assertEqual(loaded, {(WEB / "lib" / name).resolve()
                                  for name in ("checks.js", "wasi.js")})

    def test_no_page_evaluates_text_as_script(self):
        for page in self.pages():
            m = CSP.search(page.read_text(encoding="utf-8"))
            self.assertNotIn("'unsafe-eval'", m.group(1), page.name)

    def test_the_map_reads_the_gardens_vectors(self):
        page = WEB / "map" / "index.html"
        text = page.read_text(encoding="utf-8")
        for name in ("ur-garden-log", "ur-garden-head", "ur-garden-hosted"):
            path = f"../../vectors/{name}.json"
            self.assertIn(path, text)
            self.assertTrue((page.parent / path).resolve().is_file(), path)

    def test_the_plant_page_reads_the_shared_vectors(self):
        page = WEB / "plant" / "index.html"
        text = page.read_text(encoding="utf-8")
        default = "../../vectors/plant-world.json"
        self.assertIn(default, text)
        self.assertTrue((page.parent / default).resolve().is_file())
        self.assertIn("u.origin === location.origin", text)


if __name__ == "__main__":
    unittest.main()
