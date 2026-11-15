"""docs/COLLABORATING.md's list of full links ("Every file, by its full
link") and docs/FILES.md hold, between them, every file in the
repository, each once, and every link on either page leads to a file.

The founder pastes those links into a conversation with DeepSeek, which
can open a full link given in a message but not, reliably, one found
inside a page (the founder, 2026-11-15: "I have to provide the link.
Fetching is unreliable from in the page, but from a prompt with full
URL, it has worked."; and later that day: "Remember links in the
collaborating page are not accessible. So all files need links through
this method."). So the lists must be whole and current: this test fails
when a file is added, moved or removed and they aren't changed with it.
COLLABORATING.md lists the files a reader works from; FILES.md, written
by docs/files.py, the files of record (DeepSeek's records, the code
taken from them, and Experiment 001's run logs).
"""
import importlib.util
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "docs", "COLLABORATING.md")
BASE = "https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/"
LINK = re.compile(re.escape(BASE) + r"([^\s)<>\"'`#?]+)")
SECTION = "## Every file, by its full link"

FILES_PAGE = os.path.join(ROOT, "docs", "FILES.md")


def _load_files_script():
    spec = importlib.util.spec_from_file_location(
        "docs_files", os.path.join(ROOT, "docs", "files.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FILES = _load_files_script()
TRACKED = FILES.tracked()


def expected():
    """Every file COLLABORATING.md's list should hold: every file in the
    repository but those FILES.md holds."""
    held_there = set(FILES.here(TRACKED))
    return [p for p in TRACKED if p not in held_there]


def page(path=PAGE):
    with open(path, encoding="utf-8") as f:
        return f.read()


def listed():
    """The paths the list links to, in order."""
    text = page()
    start = text.index(SECTION)
    end = text.find("\n## ", start + len(SECTION))
    return LINK.findall(text[start:end if end >= 0 else len(text)])


@unittest.skipIf(TRACKED is None, "not a git checkout: can't list the files")
class TheList(unittest.TestCase):

    def test_it_holds_every_file_it_should_and_no_other(self):
        have, want = listed(), expected()
        self.assertEqual([BASE + p for p in sorted(set(want) - set(have))],
                         [], "files missing from the list")
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


@unittest.skipIf(TRACKED is None, "not a git checkout: can't list the files")
class TheRest(unittest.TestCase):

    def test_files_page_is_current(self):
        have = page(FILES_PAGE).splitlines()
        want = FILES.render(TRACKED).splitlines()
        first = next((i for i, (a, b) in enumerate(zip(have, want))
                      if a != b), min(len(have), len(want)))
        if have != want:
            self.fail(f"docs/FILES.md is stale from line {first + 1}: "
                      "run python3 docs/files.py")

    def test_the_two_hold_every_file_once(self):
        here = LINK.findall(page(FILES_PAGE))
        both = listed() + here
        self.assertEqual(len(both), len(set(both)), "a file listed twice")
        self.assertEqual(sorted(both), sorted(TRACKED))

    def test_it_holds_the_records(self):
        here = LINK.findall(page(FILES_PAGE))
        self.assertTrue(any(p.startswith("sketches/records/") for p in here))

    def test_every_link_on_it_leads_to_a_file(self):
        for path in LINK.findall(page(FILES_PAGE)):
            with self.subTest(path=path):
                self.assertTrue(
                    os.path.isfile(os.path.join(ROOT, *path.split("/"))),
                    path)


if __name__ == "__main__":
    unittest.main()
