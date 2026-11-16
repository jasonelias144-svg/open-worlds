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
                     "no newline at the end", "one\r" * 900,
                     "lines\r\nwith both\r\n" * 300,
                     "a page\n\x0cand a form feed\n\n" * 200,
                     "x\u2028y\x85z\n" * 500):
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
        for block in ("```text\n## not a heading\n```\n",
                      "~~~\n## not a heading\n~~~\n",
                      "````\n```\n## not a heading\n```\n````\n",
                      "  ```\n## not a heading\n  ```\n"):
            text = "## One\n\n" + block + "\n## Two\n\nx\n"
            with self.subTest(block=block):
                self.assertEqual([t for t, _ in PARTS.sections(
                    PARTS._lines(text))], ["One", "Two"])

    def test_inline_code_at_the_start_of_a_line_opens_no_block(self):
        text = "## One\n\n``` inline ``` text\n\n## Two\n\nx\n"
        self.assertEqual([t for t, _ in PARTS.sections(
            PARTS._lines(text))], ["One", "Two"])

    def test_a_heading_with_no_title_is_not_a_cut(self):
        text = "intro\n\n##  \n\n## One\n\nx\n"
        self.assertEqual([t for t, _ in PARTS.sections(
            PARTS._lines(text))], ["", "One"])

    def test_no_cut_falls_inside_a_code_block(self):
        block = "```text\n" + "a line\n\nand another\n" * 20 + "```\n\n"
        text = "## Long\n\n" + block * 30
        for _, _, lines in PARTS.cut("p.md", text, 2000):
            body = "".join(lines).replace("## Long\n\n", "")
            self.assertEqual(body, block * (len(body) // len(block)))

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
        items = "- an item\n" * 5
        for text in ("## Same\n\nx\n\n" + "## Same\n\n" + "- y\n" * 400,
                     "## Log\n\n" + items + "## Log\n\n" + items
                     + "## Log 2\n\n" + items,
                     "## Start\n\n" + items + "## !!\n\n" + items
                     + "## ??\n\n" + items):
            parts = PARTS.cut("p.md", "intro\n\n" + text, 70)
            names = [name for name, _, _ in parts]
            with self.subTest(names=names):
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(len(PARTS.render("p.md", parts)),
                                 len(parts))

    def test_a_piece_keeps_its_name_past_the_hundredth(self):
        few = PARTS.cut("p.md", "## Long\n\n" + "- an item\n" * 60, 40)
        many = PARTS.cut("p.md", "## Long\n\n" + "- an item\n" * 600, 40)
        self.assertGreater(len(many), 100)
        self.assertEqual([name for name, _, _ in few][-3:],
                         [name for name, _, _ in many][-3:])


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

    def test_the_text_in_a_part_file_is_the_files_own(self):
        for path in ("docs/p.md", "src/p.rs"):
            for text in (page([2, 45, 2]), "no newline at the end",
                         "one\r" * 900, "lines\r\nwith both\r\n" * 300,
                         "a page\n\x0cand a form feed\n\n" * 200,
                         "ends in blank lines\n\n\n", "\n\n\n"):
                parts = PARTS.cut(path, text, 2000)
                files = PARTS.render(path, parts)
                with self.subTest(path=path, text=text[:20]):
                    self.assertEqual("".join(
                        PARTS.unwrap(t, files[t]) for t in files), text)

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

    def test_every_cut_file_is_whole_in_its_part_files(self):
        # What is written into the part files, not only what was cut:
        # the text between each part's top and bottom lines, joined in
        # the index's order, is the file.
        built = PARTS.build(TRACKED)
        to_cut, _ = PARTS.long_files(TRACKED)
        for path, text in to_cut:
            mine = [t for t in built
                    if t.startswith("%s/%s/" % (PARTS.OUT, path))]
            with self.subTest(path=path):
                self.assertTrue(mine)
                self.assertEqual("".join(
                    PARTS.unwrap(t, built[t]) for t in mine), text)
                with open(os.path.join(ROOT, path), "rb") as f:
                    self.assertEqual(text.encode("utf-8"), f.read())

    def test_an_argument_it_does_not_know_changes_nothing(self):
        # It must stop before it works anything out, let alone writes.
        def never(*_):
            raise AssertionError("the parts were built")
        build, PARTS.build = PARTS.build, never
        try:
            self.assertEqual(PARTS.main(["--chek"]), 2)
        finally:
            PARTS.build = build

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
