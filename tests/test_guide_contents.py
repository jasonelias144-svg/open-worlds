"""The guide's home page lists every chapter of the outline, current.

guide/contents.py writes the contents of guide/README.md from
guide/OUTLINE.md and the chapters' files; this test fails when the
home page is not current, and holds the script to what it promises.
"""

import importlib.util
import os
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location(
        "guide_contents", os.path.join(ROOT, "guide", "contents.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTENTS = _load()


def _outline():
    with open(CONTENTS.OUTLINE, encoding="utf-8") as f:
        return f.read()


class TheHomePage(unittest.TestCase):
    def test_it_is_current(self):
        self.assertEqual(CONTENTS.main(["contents.py", "--check"]), 0)

    def test_the_outline_has_every_part_and_no_number_twice(self):
        parts = CONTENTS.chapters(_outline())
        headings = [h for h, _ in parts]
        self.assertEqual(headings[0], "Front matter")
        self.assertEqual(headings[-1], "Reference")
        self.assertEqual(len(headings), 11)
        for heading, chs in parts:
            self.assertTrue(chs, heading)
        numbers = [c[0] for _, chs in parts for c in chs]
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertIn("I.1", numbers)
        self.assertIn("R.9", numbers)

    def test_a_number_twice_is_refused(self):
        text = _outline().replace("- **I.2 A first walk",
                                  "- **I.1 A first walk")
        with self.assertRaisesRegex(CONTENTS.Problem, "I.1"):
            CONTENTS.chapters(text)


class AChapterWritten(unittest.TestCase):
    def setUp(self):
        self.here = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.here)
        self.saved = CONTENTS.HERE
        CONTENTS.HERE = self.here
        self.addCleanup(setattr, CONTENTS, "HERE", self.saved)
        os.makedirs(os.path.join(self.here, "I"))

    def write(self, name, text):
        with open(os.path.join(self.here, "I", name), "w",
                  encoding="utf-8") as f:
            f.write(text)

    def test_its_progress_and_link_are_listed(self):
        self.write("01-what-open-worlds-is.md",
                   "# I.1 What Open Worlds is\n\nProgress: draft\n")
        text = CONTENTS.contents_text(_outline())
        self.assertIn("| I.1 | [What Open Worlds is]"
                      "(I/01-what-open-worlds-is.md) | draft |", text)
        self.assertIn("; 1 written.", text)
        self.assertIn("| I.2 | A first walk through a multiverse | "
                      "planned |", text)

    def test_with_no_progress_line_it_is_written(self):
        self.write("01-what-open-worlds-is.md", "# I.1 What Open Worlds is\n")
        self.assertIn("(I/01-what-open-worlds-is.md) | written |",
                      CONTENTS.contents_text(_outline()))

    def test_two_files_for_one_chapter_are_refused(self):
        self.write("01-a.md", "x\n")
        self.write("01-b.md", "x\n")
        with self.assertRaisesRegex(CONTENTS.Problem, "I.1 has 2 files"):
            CONTENTS.contents_text(_outline())


if __name__ == "__main__":
    unittest.main()
