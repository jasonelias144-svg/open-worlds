"""docs/COLLABORATING.md's list of full links ("Every file, by its full
link") names exactly the files it says it does, and every one exists.

The founder pastes those links into a conversation with DeepSeek, which
can open a full link given in a message but not, reliably, one found
inside a page (the founder, 2026-11-15: "I have to provide the link.
Fetching is unreliable from in the page, but from a prompt with full
URL, it has worked."). So the list must be whole and current: this test
fails when a file is added, moved or removed and the list isn't changed
with it. It also checks that every full link anywhere on the page leads
to a file that exists.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "docs", "COLLABORATING.md")
BASE = "https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/"
LINK = re.compile(re.escape(BASE) + r"([^\s)<>\"'`#?]+)")
SECTION = "## Every file, by its full link"

# The files the list holds, besides those found below.
ALWAYS = ["README.md", "AGENTS.md", "STATUS.md", "rust/README.md",
          "rust/Cargo.toml", "rust/rust-toolchain.toml",
          "vectors/README.md", "sketches/README.md", "sketches/INDEX.md"]


def _files(folder, suffix, deep=True):
    """Paths, from the root, of the files under `folder` ending in
    `suffix` (in its subfolders too, if `deep`)."""
    top = os.path.join(ROOT, folder)
    found = []
    for here, dirs, names in os.walk(top):
        dirs.sort()
        if not deep:
            dirs.clear()
        found.extend(os.path.relpath(os.path.join(here, n), ROOT)
                     .replace(os.sep, "/")
                     for n in sorted(names) if n.endswith(suffix))
    return found


def expected():
    """Every file the list should hold: the pages in docs/, the key
    list, the schemas, and each Rust crate's manifest, library code and
    examples (not its tests), with ALWAYS."""
    paths = list(ALWAYS)
    paths += _files("docs", ".md")
    paths += _files("keys", "", deep=False)
    paths += _files("schemas", ".json", deep=False)
    rust = os.path.join(ROOT, "rust")
    for crate in sorted(os.listdir(rust)):
        if os.path.isfile(os.path.join(rust, crate, "Cargo.toml")):
            paths.append(f"rust/{crate}/Cargo.toml")
            paths += _files(f"rust/{crate}/src", ".rs")
            paths += _files(f"rust/{crate}/examples", ".rs", deep=False)
    return paths


def page():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def listed():
    """The paths the list links to, in order."""
    text = page()
    start = text.index(SECTION)
    end = text.find("\n## ", start + len(SECTION))
    return LINK.findall(text[start:end if end >= 0 else len(text)])


class TheList(unittest.TestCase):

    def test_it_holds_every_file_it_should_and_no_other(self):
        have, want = listed(), expected()
        self.assertEqual(sorted(set(want) - set(have)), [],
                         "files missing from the list")
        self.assertEqual(sorted(set(have) - set(want)), [],
                         "files in the list it shouldn't hold")

    def test_no_file_twice(self):
        have = listed()
        self.assertEqual(len(have), len(set(have)))

    def test_it_holds_the_key_list(self):
        # The file DeepSeek couldn't open in record 012-07-03, as no
        # list had given it its link.
        self.assertIn("keys/key-list.json", listed())

    def test_every_full_link_on_the_page_leads_to_a_file(self):
        for path in LINK.findall(page()):
            path = path.rstrip(".,;:")
            with self.subTest(path=path):
                self.assertTrue(
                    os.path.isfile(os.path.join(ROOT, *path.split("/"))),
                    path)


if __name__ == "__main__":
    unittest.main()
