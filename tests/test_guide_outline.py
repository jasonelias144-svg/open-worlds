"""The guide's outline names every area of the repository.

The founder asked that the guide "touches all areas of code"
(guide/README.md). This test holds the outline to that as the
repository grows: every top-level folder and file, every page and tool
in docs/ and docs/research/, and every Rust crate must be named in
guide/OUTLINE.md, by its path.
"""

import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"__pycache__", "target"}


def _names(folder):
    path = os.path.join(ROOT, folder)
    return sorted(n for n in os.listdir(path)
                  if not n.startswith(".") and n not in SKIP)


def areas():
    """Each area as the outline would name it."""
    found = []
    for name in _names(""):
        full = os.path.join(ROOT, name)
        found.append(name + "/" if os.path.isdir(full) else name)
    for folder in ("docs", "docs/research"):
        for name in _names(folder):
            if os.path.isfile(os.path.join(ROOT, folder, name)):
                found.append(folder + "/" + name)
    for name in _names("rust"):
        if os.path.isfile(os.path.join(ROOT, "rust", name, "Cargo.toml")):
            found.append("rust/" + name)
    return found


class Outline(unittest.TestCase):
    def test_every_area_is_named(self):
        with open(os.path.join(ROOT, "guide", "OUTLINE.md"),
                  encoding="utf-8") as f:
            text = f.read()
        missing = [a for a in areas() if a not in text]
        self.assertEqual(missing, [], "areas the guide's outline does not "
                         "name; give each a chapter's sources")

    def test_the_areas_are_found(self):
        found = areas()
        for area in ("multiverse/", "docs/COMMONS.md", "rust/ur-world",
                     "docs/research/KEYS.md", "CHARTER.md"):
            self.assertIn(area, found)


if __name__ == "__main__":
    unittest.main()
