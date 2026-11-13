"""The conversation records' links into this repository still lead
somewhere.

The records in sketches/records travel on their own, and the founder
leaves links in them on purpose: "That little link could open a whole
window into the project for someone" who meets a record elsewhere. A link
to a file on `main` works only while the file stays where it is. So if a
file a record links to is moved or renamed, this test fails: leave a page
at the old path that points to the new one.

It reads the records as text and imports nothing from sketches/.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDS = os.path.join(ROOT, "sketches", "records")
REPO = "jasonelias144-svg/open-worlds"
LINK = re.compile(
    r"https?://(?:github\.com/" + re.escape(REPO) + r"/(?:blob|tree)/main"
    r"|raw\.githubusercontent\.com/" + re.escape(REPO) + r"/main)"
    r"/([^\s)>\"'`#?]+)")


def links_in(text):
    """The paths of every link to this repository's main branch in
    `text`, without a sentence's closing punctuation."""
    return [path.rstrip(".,;:") for path in LINK.findall(text)]


def record_links():
    """(record, path) for every such link, in every record."""
    found = []
    for name in sorted(os.listdir(RECORDS)):
        with open(os.path.join(RECORDS, name), encoding="utf-8") as f:
            found.extend((name, path) for path in links_in(f.read()))
    return found


class TestRecordLinks(unittest.TestCase):

    def test_the_records_link_into_this_repository(self):
        # If this fails, the pattern no longer matches the records' links,
        # and the next test would check nothing.
        self.assertTrue(record_links())

    def test_every_linked_path_still_exists(self):
        for record, path in record_links():
            with self.subTest(record=record, path=path):
                self.assertTrue(
                    os.path.exists(os.path.join(ROOT, *path.split("/"))),
                    f"{record} links to {path}, which no longer exists")

    def test_the_pattern_reads_both_kinds_of_link(self):
        text = ("see https://github.com/" + REPO + "/blob/main/docs/A.md, "
                "or https://raw.githubusercontent.com/" + REPO +
                "/main/docs/B.md.")
        self.assertEqual(links_in(text), ["docs/A.md", "docs/B.md"])


if __name__ == "__main__":
    unittest.main()
