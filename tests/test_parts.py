"""parts/ holds every long file a reader works from, cut into parts short
enough to be read whole by a reader who is shown only the start of a
page, and it is in step with those files.

A tool that opens a page for a reader may show only its start, so a
longer page can't be read to its end through its own link.
docs/parts.py cuts each such file into parts; this test fails when a
file changes and its parts aren't made again, when a part is too long,
or when a long file is neither cut nor named as left whole.
"""
import importlib.util
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location(
        "docs_parts", os.path.join(ROOT, "docs", "parts.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PARTS = _load()
TRACKED = PARTS.FILES.tracked()
LINK = re.compile(re.escape(PARTS.BASE) + r"([^\s)<>\"'`#?]+)")


def joined(parts):
    return "".join("".join(lines) for _, _, lines in parts)


def page(sections):
    """A Markdown page: a title, then "## " sections of the given
    numbers of items, each item a line of 100 bytes."""
    out = ["# A page\n", "\n", "What it is for.\n"]
    for number, items in enumerate(sections, 1):
        out += ["\n", "## Section %d\n" % number, "\n"]
        out += ["- %s\n" % ("item %d.%d " % (number, i)).ljust(97, "x")
                for i in range(items)]
    return "".join(out)


class TheCut(unittest.TestCase):

    def test_the_parts_joined_are_the_text(self):
        for text in (page([3, 400, 5]), page([400]), page([]), "",
                     "no newline at the end"):
            with self.subTest(text=text[:30]):
                self.assertEqual(joined(PARTS.cut("p.md", text, 2000)), text)
                self.assertEqual(joined(PARTS.cut("p.py", text, 2000)), text)

    def test_no_part_is_longer_than_the_room(self):
        for path in ("p.md", "p.py"):
            for _, _, lines in PARTS.cut(path, page([3, 400, 5]), 2000):
                self.assertLessEqual(len("".join(lines).encode()), 2000)

    def test_sections_that_fit_are_gathered_in_order(self):
        parts = PARTS.cut("p.md", page([5, 5, 5, 5, 5]), 1100)
        self.assertEqual([name for name, _, _ in parts],
                         ["start", "section-3", "section-5"])
        self.assertEqual(parts[0][1], 'from the start to "Section 2"')
        self.assertEqual(parts[1][1], '"Section 3" to "Section 4"')
        self.assertEqual(parts[2][1], '"Section 5"')

    def test_a_long_section_is_gathered_from_its_end(self):
        parts = PARTS.cut("p.md", page([2, 45, 2]), 2000)
        names = [name for name, _, _ in parts]
        self.assertEqual(names, ["start", "section-2-03", "section-2-02",
                                 "section-2-01", "section-3"])
        # The piece at the section's end is full; the one at its top
        # holds what is left over, with the heading.
        self.assertIn("## Section 2\n", parts[1][2])
        self.assertGreater(len(parts[3][2]), len(parts[1][2]))

    def test_an_item_added_at_the_top_changes_one_part(self):
        before = page([2, 45, 2])
        after = before.replace("## Section 2\n\n",
                               "## Section 2\n\n- a new item\n")
        old = PARTS.render("p.md", PARTS.cut("p.md", before, 2000))
        new = PARTS.render("p.md", PARTS.cut("p.md", after, 2000))
        self.assertEqual(sorted(old), sorted(new))
        self.assertEqual([p for p in old if old[p] != new[p]],
                         ["parts/p.md/section-2-03.md"])

    def test_a_cut_falls_between_items_not_inside_one(self):
        item = "- an item\n  that runs on\n  for three lines\n"
        text = "## Long\n\n" + item * 60
        for _, _, lines in PARTS.cut("p.md", text, 1000):
            body = "".join(lines).replace("## Long\n\n", "")
            self.assertEqual(body, item * (len(body) // len(item)))

    def test_a_heading_in_a_code_block_is_not_a_cut(self):
        text = "## One\n\n```text\n## not a heading\n```\n\n## Two\n\nx\n"
        self.assertEqual([t for t, _ in PARTS.sections(
            text.splitlines(keepends=True))], ["One", "Two"])

    def test_an_item_too_long_for_a_part_is_cut_between_its_lines(self):
        text = "## Long\n\n- one item\n" + "  and a line of it\n" * 200
        parts = PARTS.cut("p.md", text, 1000)
        self.assertGreater(len(parts), 3)
        self.assertEqual(joined(parts), text)

    def test_other_files_are_numbered_from_the_start(self):
        text = "".join("def f%d():\n    return %d\n\n" % (i, i)
                       for i in range(200))
        parts = PARTS.cut("p.py", text, 1000)
        self.assertEqual([name for name, _, _ in parts][:3],
                         ["01", "02", "03"])
        for _, _, lines in parts:
            self.assertTrue("".join(lines).startswith("def f"))

    def test_two_parts_never_share_a_name(self):
        text = "## Same\n\nx\n\n" + "## Same\n\n" + "- y\n" * 400
        names = [name for name, _, _ in PARTS.cut("p.md", text, 600)]
        self.assertEqual(len(names), len(set(names)))


class ThePartFiles(unittest.TestCase):

    def test_each_part_says_where_it_belongs_and_what_comes_next(self):
        files = PARTS.render("docs/p.md", PARTS.cut(
            "docs/p.md", page([2, 45, 2]), 2000))
        order = list(files)
        for i, target in enumerate(order):
            text = files[target]
            self.assertIn("Part of `docs/p.md`", text)
            if i + 1 < len(order):
                self.assertTrue(text.rstrip("\n").endswith(
                    "The next part: " + PARTS.BASE + order[i + 1]), target)
            else:
                self.assertTrue(text.rstrip("\n").endswith(
                    "End of `docs/p.md`."), target)

    def test_a_part_of_a_file_that_is_not_markdown_is_plain_text(self):
        files = PARTS.render("src/p.rs", PARTS.cut(
            "src/p.rs", "fn main() {}\n" * 300, 1000))
        self.assertTrue(all(t.endswith(".txt") for t in files))
        self.assertTrue(all(t.startswith("parts/src/p.rs/") for t in files))


@unittest.skipIf(TRACKED is None, "not a git checkout: can't list the files")
class TheRepository(unittest.TestCase):

    def test_the_parts_are_in_step(self):
        missing, changed, extra = PARTS.stale(PARTS.build(TRACKED),
                                              PARTS.on_disk())
        self.assertEqual(
            (missing[:5], changed[:5], extra[:5]), ([], [], []),
            "parts/ is out of step (missing, changed, left over): "
            "run python3 docs/parts.py")

    def test_no_part_is_longer_than_the_limit(self):
        for target, text in PARTS.build(TRACKED).items():
            with self.subTest(part=target):
                self.assertLessEqual(len(text.encode("utf-8")), PARTS.LIMIT)

    def test_every_cut_file_is_whole_in_its_parts(self):
        to_cut, _ = PARTS.long_files(TRACKED)
        self.assertTrue(to_cut)
        for path, text in to_cut:
            with self.subTest(path=path):
                self.assertEqual(joined(PARTS.cut(path, text)), text)

    def test_every_long_file_is_cut_or_named_as_left_whole(self):
        to_cut, left = PARTS.long_files(TRACKED)
        accounted = {p for p, _ in to_cut} | {p for ps in left.values()
                                              for p in ps}
        long_ones = {p for p in PARTS.working(TRACKED) if os.path.getsize(
            os.path.join(ROOT, p)) > PARTS.LIMIT}
        self.assertEqual(long_ones, accounted)
        index = PARTS.build(TRACKED)[PARTS.INDEX]
        for (what, _), _ in left.items():
            self.assertIn("`%s`" % what, index)

    def test_the_index_lists_every_part_once_in_reading_order(self):
        built = PARTS.build(TRACKED)
        listed = LINK.findall(built[PARTS.INDEX])
        self.assertEqual(listed, [t for t in built if t != PARTS.INDEX])
        self.assertEqual(len(listed), len(set(listed)))

    def test_the_pages_a_reader_starts_from_are_cut(self):
        cut_files = {p for p, _ in PARTS.long_files(TRACKED)[0]}
        for path in ("STATUS.md", "docs/COLLABORATING.md", "docs/TOPICS.md"):
            self.assertIn(path, cut_files)


if __name__ == "__main__":
    unittest.main()
