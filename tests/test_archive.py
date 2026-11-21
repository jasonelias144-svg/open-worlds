"""The archive holds each moved entry whole, and is in step with its pages.

docs/archive.py moves a living page's older dated entries into
archive/, a file for each page and day, and writes the catalogue
(archive/README.md says how). This test runs the script on small pages
of its own, in a git repository of its own, and holds the repository's
own archive to its catalogue and its pages.
"""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_archive():
    spec = importlib.util.spec_from_file_location(
        "docs_archive", os.path.join(ROOT, "docs", "archive.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ARCHIVE = load_archive()

STATUS = """# Status

## Now

- nothing dated here moves: 2026-01-01

## Decided

- 2026-01-05, founder, five.
  Second line of five.

- 2026-01-04, founder, four.

- 2026-01-02, founder, two.
  - a nested line, 2026-01-09

- 2026-01-03, founder, three, out of order.

## Decided by the technical lead

- 2026-01-04, a choice.
- 2026-01-01, an older choice,
  with a second line.

## Log

- 2026-01-05 Claude: five.

- 2026-01-03 Claude: three.

- 2026-01-01 Claude: one.
"""

COLLAB = """# Collaborating

## Messages from the technical lead

Who writes here, and why.

### 2026-01-04, to both: four

Body of four.

```text
    ### 2026-01-01 not a message: indented, in a code block
```

### 2026-01-03, to both: three

Body of three.

### 2026-01-02, to both: two

Body of two.

## The standard

Not dated, and stays.
"""


def dated_entries(text):
    """Every dated entry in the dated sections of a page or a day file,
    as text, found without docs/archive.py: an entry starts at a line
    '- YYYY-MM-DD' or '### YYYY-MM-DD' outside a code block, and runs to
    the next one or the next '## ' heading; blank lines at its end and
    pointer lines are dropped."""
    out, cur, section, fence = [], None, None, False
    dated = ("Decided", "Decided by the technical lead", "Log",
             "Messages from the technical lead")
    for line in text.split("\n"):
        if line.startswith(("```", "~~~")):
            fence = not fence
        if not fence and line.startswith("## "):
            if cur:
                out.append(cur)
            cur, section = None, line[3:].strip()
            continue
        starts = (not fence and section in dated and len(line) > 12
                  and (line.startswith("- 20") or line.startswith("### 20")))
        if starts:
            if cur:
                out.append(cur)
            cur = [line]
        elif cur is not None and not line.startswith("*Earlier entries"):
            cur.append(line)
    if cur:
        out.append(cur)
    texts = []
    for lines in out:
        while lines and not lines[-1].strip():
            lines.pop()
        texts.append("\n".join(lines))
    return texts


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True)


class Pages(unittest.TestCase):
    """Pages of this test's own, in a git repository of its own."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "docs"))
        self.write("STATUS.md", STATUS)
        self.write("docs/COLLABORATING.md", COLLAB)
        git(self.root, "init", "-q")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t",
            "add", "-A")
        self.commit()
        self.old_root = ARCHIVE.ROOT
        ARCHIVE.ROOT = self.root
        self.addCleanup(setattr, ARCHIVE, "ROOT", self.old_root)

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t",
            "commit", "-q", "-m", "c", "--allow-empty")

    def write(self, path, text):
        with open(os.path.join(self.root, path), "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, path):
        with open(os.path.join(self.root, path), encoding="utf-8") as f:
            return f.read()

    def run_it(self, keep=2):
        with contextlib.redirect_stdout(io.StringIO()):
            return ARCHIVE.run(write=True, keep=keep, today="2026-01-06")



class Small(Pages):
    """The script's main path."""

    def test_a_plan_moves_nothing(self):
        report = ARCHIVE.run(write=False, keep=2)
        self.assertEqual(self.read("STATUS.md"), STATUS)
        self.assertFalse(os.path.exists(os.path.join(self.root, "archive")))
        status = [r for r in report if r[0] == "STATUS.md"][0]
        self.assertEqual(status[1], ["2026-01-05", "2026-01-04"])
        self.assertEqual(sorted(status[2]),
                         ["2026-01-01", "2026-01-02", "2026-01-03"])

    def test_the_most_recent_days_stay_and_the_rest_move(self):
        self.run_it()
        page = self.read("STATUS.md")
        for kept in ("five.\n  Second line of five.", "founder, four.",
                     "2026-01-04, a choice.", "2026-01-05 Claude: five."):
            self.assertIn(kept, page)
        for moved in ("founder, two.", "three, out of order",
                      "an older choice", "Claude: three.", "Claude: one."):
            self.assertNotIn(moved, page)
        # A section with no dated entries of its own stays as it was.
        self.assertIn("## Now\n\n- nothing dated here moves: 2026-01-01\n",
                      page)

    def test_an_entry_moves_whole(self):
        self.run_it()
        two = self.read("archive/STATUS/2026-01-02.md")
        self.assertIn("- 2026-01-02, founder, two.\n"
                      "  - a nested line, 2026-01-09\n", two)
        one = self.read("archive/STATUS/2026-01-01.md")
        self.assertIn("- 2026-01-01, an older choice,\n"
                      "  with a second line.\n", one)
        self.assertLess(one.index("## Decided by the technical lead"),
                        one.index("## Log"))

    def test_a_dated_section_opens_with_the_pointer(self):
        self.run_it()
        page = self.read("STATUS.md").split("\n")
        for name in ("Decided", "Decided by the technical lead", "Log"):
            i = page.index("## " + name)
            self.assertEqual(page[i + 2], ARCHIVE.pointer_text("STATUS"))
        self.assertIn("(https://raw.githubusercontent.com/",
                      ARCHIVE.pointer_text("COLLABORATING"))

    def test_a_heading_in_a_code_block_is_not_a_message(self):
        self.run_it()
        collab = self.read("docs/COLLABORATING.md")
        self.assertIn("### 2026-01-04, to both: four", collab)
        self.assertIn("    ### 2026-01-01 not a message: indented, in a "
                      "code block", collab)
        self.assertNotIn("Body of two.", collab)
        self.assertIn("## The standard\n\nNot dated, and stays.\n", collab)
        self.assertIn("Who writes here, and why.", collab)

    def test_the_catalogue_names_each_file(self):
        self.run_it()
        with open(os.path.join(self.root, "archive", "catalog.json")) as f:
            items = json.load(f)["items"]
        paths = [i["path"] for i in items]
        self.assertIn("archive/STATUS/2026-01-03.md", paths)
        three = [i for i in items
                 if i["path"] == "archive/STATUS/2026-01-03.md"][0]
        self.assertEqual(three["sections"],
                         [{"name": "Decided", "entries": 1},
                          {"name": "Log", "entries": 1}])
        self.assertEqual(len(three["commit"]), 40)
        self.assertEqual(three["moved"], "2026-01-06")

    def test_the_check_passes_after_a_run_and_a_second_run_moves_nothing(self):
        self.run_it()
        self.assertEqual(ARCHIVE.check(), [])
        self.commit()
        before = self.read("STATUS.md")
        report = self.run_it()
        self.assertTrue(all(not moving for _, _, moving in report))
        self.assertEqual(self.read("STATUS.md"), before)
        self.assertEqual(ARCHIVE.check(), [])

    def test_a_later_run_moves_the_next_day(self):
        self.run_it()
        self.commit()
        page = self.read("STATUS.md").replace(
            "## Log\n\n" + ARCHIVE.pointer_text("STATUS")
            + "\n\n",
            "## Log\n\n" + ARCHIVE.pointer_text("STATUS")
            + "\n\n- 2026-01-07 Claude: seven.\n\n")
        self.write("STATUS.md", page)
        self.commit()
        self.run_it()
        self.assertTrue(os.path.exists(os.path.join(
            self.root, "archive", "STATUS", "2026-01-04.md")))
        self.assertIn("2026-01-07 Claude: seven.", self.read("STATUS.md"))
        self.assertEqual(ARCHIVE.check(), [])

    def test_an_entry_on_an_archived_day_stops_the_run(self):
        self.run_it()
        page = self.read("STATUS.md").replace(
            "- 2026-01-05 Claude: five.",
            "- 2026-01-05 Claude: five.\n\n- 2026-01-02 Claude: late.")
        self.write("STATUS.md", page)
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "already in the archive"):
            self.run_it()
        self.assertTrue(any("a day in the archive" in p
                            for p in ARCHIVE.check()))

    def test_a_page_not_committed_stops_the_run(self):
        self.write("STATUS.md", STATUS + "\n")
        with self.assertRaisesRegex(ARCHIVE.Problem, "commit it first"):
            self.run_it()
        self.assertFalse(os.path.exists(os.path.join(self.root, "archive")))

    def test_the_check_finds_an_edited_file(self):
        self.run_it()
        path = os.path.join(self.root, "archive", "STATUS", "2026-01-02.md")
        with open(path, "a", encoding="utf-8") as f:
            f.write("an edit\n")
        self.assertTrue(any("sha256" in p for p in ARCHIVE.check()))

    def test_the_check_counts_the_entries_in_each_file(self):
        # An entry taken out, with the catalogue's size and hash made to
        # match: the count still tells.
        self.run_it()
        path = "archive/STATUS/2026-01-03.md"
        text = self.read(path).replace("\n- 2026-01-03 Claude: three.\n", "")
        self.write(path, text)
        cat = os.path.join(self.root, "archive", "catalog.json")
        with open(cat, encoding="utf-8") as f:
            data = json.load(f)
        item = [i for i in data["items"] if i["path"] == path][0]
        item.update(ARCHIVE.file_facts(path))
        items = data["items"]
        self.write("archive/catalog.json", ARCHIVE.catalog_text(items))
        self.write("archive/README.md", ARCHIVE.readme_text(items))
        self.assertTrue(any("entries are not the catalogue's" in p
                            for p in ARCHIVE.check()))

    def test_the_check_finds_a_file_not_in_the_catalogue(self):
        self.run_it()
        self.write("archive/STATUS/2025-12-31.md", "# stray\n")
        self.assertTrue(any("not in the catalogue" in p
                            for p in ARCHIVE.check()))

    def test_the_check_finds_a_missing_pointer(self):
        self.run_it()
        self.write("STATUS.md", self.read("STATUS.md").replace(
            ARCHIVE.pointer_text("STATUS") + "\n\n", "", 1))
        self.assertTrue(any("points to the archive" in p
                            for p in ARCHIVE.check()))

    def test_the_check_finds_a_readme_out_of_step(self):
        self.run_it()
        self.write("archive/README.md", self.read("archive/README.md")
                   + "more\n")
        self.assertTrue(any("README.md" in p for p in ARCHIVE.check()))


class Harder(Pages):
    """What the first review of the script found it did not hold."""

    def everything(self):
        texts = dated_entries(self.read("STATUS.md")) + dated_entries(
            self.read("docs/COLLABORATING.md"))
        base = os.path.join(self.root, "archive")
        for folder in ("STATUS", "COLLABORATING"):
            path = os.path.join(base, folder)
            for name in sorted(os.listdir(path)) if os.path.isdir(path) \
                    else []:
                texts += dated_entries(self.read(
                    os.path.join("archive", folder, name)))
        return sorted(texts)

    def test_every_entry_is_kept_once_and_unchanged(self):
        before = self.everything()
        self.run_it()
        self.assertEqual(self.everything(), before)
        self.commit()
        self.run_it(keep=1)
        self.assertEqual(self.everything(), before)
        self.assertEqual(ARCHIVE.check(), [])

    def test_the_rest_of_a_page_is_unchanged(self):
        self.run_it()
        page = self.read("docs/COLLABORATING.md")
        self.assertTrue(page.startswith(COLLAB[:COLLAB.index("### ")]
                                        .replace("\n\nWho", "\n\n"
                                                 + ARCHIVE.pointer_text(
                                                     "COLLABORATING")
                                                 + "\n\nWho")))
        self.assertTrue(page.endswith(COLLAB[COLLAB.index("## The standard"):]))

    def test_a_line_at_the_margin_inside_an_entry_stops_the_run(self):
        self.write("STATUS.md", STATUS.replace(
            "- 2026-01-04, founder, four.\n",
            "- 2026-01-04, founder, four.\nA paragraph at the margin.\n"))
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "left margin"):
            self.run_it()
        self.assertFalse(os.path.exists(os.path.join(self.root, "archive")))
        self.assertTrue(any("left margin" in p for p in ARCHIVE.check()))

    def test_a_run_that_stops_writes_nothing(self):
        os.makedirs(os.path.join(self.root, "archive", "COLLABORATING"))
        self.write("archive/COLLABORATING/2026-01-02.md", "# in the way\n")
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "exists already"):
            self.run_it()
        self.assertEqual(self.read("STATUS.md"), STATUS)
        self.assertFalse(os.path.exists(
            os.path.join(self.root, "archive", "STATUS")))
        self.assertFalse(os.path.exists(
            os.path.join(self.root, "archive", "catalog.json")))

    def test_two_runs_that_both_move_leave_one_pointer(self):
        self.run_it(keep=3)
        self.commit()
        self.run_it(keep=1)
        for path in ("STATUS.md", "docs/COLLABORATING.md"):
            text = self.read(path)
            pointers = text.count("*Earlier entries are in the archive")
            sections = 3 if path == "STATUS.md" else 1
            self.assertEqual(pointers, sections, path)
        self.assertEqual(ARCHIVE.check(), [])

    def test_a_pointer_out_of_place_is_put_right(self):
        self.run_it()
        self.commit()
        pointer = ARCHIVE.pointer_text("STATUS")
        page = self.read("STATUS.md").replace(
            "## Log\n\n" + pointer + "\n\n", "## Log\n\n" + pointer + "\n")
        self.write("STATUS.md", page)
        self.assertTrue(any("points to the archive" in p
                            for p in ARCHIVE.check()))
        self.commit()
        self.run_it()
        self.assertEqual(self.read("STATUS.md").count(pointer), 3)
        self.assertEqual(ARCHIVE.check(), [])

    def test_a_missing_catalogue_is_a_problem(self):
        self.run_it()
        os.remove(os.path.join(self.root, "archive", "catalog.json"))
        os.remove(os.path.join(self.root, "archive", "README.md"))
        problems = ARCHIVE.check()
        self.assertTrue(any("catalog.json is missing" in p for p in problems))
        self.assertTrue(any("not in the catalogue" in p for p in problems))
        self.assertTrue(any("holds nothing" in p for p in problems))

    def test_a_page_not_tracked_stops_the_run(self):
        git(self.root, "rm", "-q", "--cached", "STATUS.md")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t",
            "commit", "-q", "-m", "untrack")
        with self.assertRaisesRegex(ARCHIVE.Problem, "not committed"):
            self.run_it()

    def test_an_entry_changed_with_its_hash_is_found_at_the_commit(self):
        self.run_it()
        path = "archive/STATUS/2026-01-02.md"
        self.write(path, self.read(path).replace("founder, two.",
                                                 "founder, TWO."))
        cat = os.path.join(self.root, "archive", "catalog.json")
        with open(cat, encoding="utf-8") as f:
            items = json.load(f)["items"]
        [i for i in items if i["path"] == path][0].update(
            ARCHIVE.file_facts(path))
        self.write("archive/catalog.json", ARCHIVE.catalog_text(items))
        self.write("archive/README.md", ARCHIVE.readme_text(items))
        self.assertTrue(any("word for word" in p for p in ARCHIVE.check()))

    def test_a_redaction_is_recorded(self):
        self.run_it()
        path = "archive/STATUS/2026-01-02.md"
        self.write(path, self.read(path).replace(
            "a nested line", "[redacted]"))
        self.assertTrue(ARCHIVE.check())
        ARCHIVE.rehash(path, "a private detail", today="2026-01-07")
        notes = []
        self.assertEqual(ARCHIVE.check(notes), [])
        self.assertTrue(any("redacted since" in n for n in notes))
        self.assertIn("(redacted since)", self.read("archive/README.md"))
        with self.assertRaisesRegex(ARCHIVE.Problem, "why"):
            ARCHIVE.rehash(path, " ")

    def test_a_tilde_block_is_a_code_block_too(self):
        self.write("docs/COLLABORATING.md", COLLAB.replace(
            "Body of two.\n",
            "Body of two.\n\n~~~\n    ## indented\n~~~\n\nStill two.\n"))
        self.commit()
        self.run_it()
        two = self.read("archive/COLLABORATING/2026-01-02.md")
        self.assertIn("    ## indented\n~~~\n\nStill two.", two)
        self.assertEqual(ARCHIVE.check(), [])

    def test_a_heading_at_the_margin_in_a_code_block_stops_the_run(self):
        for line in ("## not a section", "### 2026-01-01 not a message"):
            with self.subTest(line=line):
                self.write("docs/COLLABORATING.md", COLLAB.replace(
                    "Body of two.\n",
                    "Body of two.\n\n~~~\n" + line + "\n~~~\n"))
                self.commit()
                with self.assertRaisesRegex(ARCHIVE.Problem,
                                            "entry or a section"):
                    self.run_it()
                self.assertTrue(any("entry or a section" in p
                                    for p in ARCHIVE.check()))

    def test_an_empty_section_is_named_as_empty(self):
        self.write("STATUS.md", STATUS.replace(
            "## Log\n\n- 2026-01-05 Claude: five.\n\n"
            "- 2026-01-03 Claude: three.\n\n- 2026-01-01 Claude: one.\n",
            "## Log\n"))
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "is empty"):
            self.run_it()

    def test_nothing_to_move_in_a_new_repository_writes_nothing(self):
        report = self.run_it(keep=9)
        self.assertTrue(all(not moving for _, _, moving in report))
        self.assertFalse(os.path.exists(os.path.join(self.root, "archive")))
        self.assertEqual(ARCHIVE.check(), [])


class Second(Pages):
    """What the second review of the script found it did not hold."""

    def test_a_code_block_never_closed_stops_the_run(self):
        self.write("docs/COLLABORATING.md", COLLAB.replace(
            "Body of two.\n", "Body of two.\n\n```text\nnever closed\n"))
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "never closed"):
            self.run_it()
        self.assertFalse(os.path.exists(os.path.join(self.root, "archive")))
        self.assertTrue(any("never closed" in p for p in ARCHIVE.check()))

    def test_a_block_that_joins_two_entries_stops_the_run(self):
        # A block opened in one entry and closed in a later one would
        # make the two one entry, filed under the first one's day.
        self.write("STATUS.md", STATUS.replace(
            "- 2026-01-04, founder, four.\n",
            "- 2026-01-04, founder, four.\n  ```\n\n"
            "- 2026-01-03, founder, a block's other end.\n  ```\n"))
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "entry or a section"):
            self.run_it()
        self.assertTrue(any("would start an entry" in p
                            for p in ARCHIVE.check()))

    def test_a_day_file_with_a_block_never_closed_is_a_problem(self):
        self.run_it()
        path = "archive/STATUS/2026-01-02.md"
        self.write(path, self.read(path) + "\n```\n")
        ARCHIVE.rehash(path, "a test", today="2026-01-07")
        self.assertTrue(any(p.startswith(path) and "never closed" in p
                            for p in ARCHIVE.check()))

    def test_a_block_left_open_and_closed_by_a_later_one_stops_the_run(self):
        # The second review's case: a block left open in an old message
        # is closed by a later section's bare fence, so the page as a
        # whole looks closed, and the message would take every section
        # up to there with it.
        page = COLLAB.replace(
            "Body of two.\n", "Body of two.\n\n```text\nnever closed\n")
        page = page.replace(
            "Not dated, and stays.\n",
            "Not dated, and stays.\n\n```\nbare\n```\n\n"
            "## Last\n\n```text\na list\n```\n")
        self.write("docs/COLLABORATING.md", page)
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "entry or a section"):
            self.run_it()
        self.assertFalse(os.path.exists(os.path.join(self.root, "archive")))
        self.assertTrue(any("entry or a section" in p
                            for p in ARCHIVE.check()))

    def test_the_check_does_not_count_a_pointer_in_a_code_block(self):
        pointer = ARCHIVE.pointer_text("COLLABORATING")
        self.write("docs/COLLABORATING.md", COLLAB.replace(
            "Who writes here, and why.\n",
            "Who writes here, and why.\n\n```text\n" + pointer
            + "\n```\n"))
        self.commit()
        self.run_it()
        self.assertEqual(ARCHIVE.check(), [])

    def test_a_date_later_than_tomorrow_stops_the_run(self):
        self.write("STATUS.md", STATUS.replace(
            "- 2026-01-05 Claude: five.", "- 2062-01-05 Claude: five."))
        self.commit()
        with self.assertRaisesRegex(ARCHIVE.Problem, "later than tomorrow"):
            self.run_it()
        self.assertTrue(any("later than tomorrow" in p
                            for p in ARCHIVE.check(today=datetime.date(
                                2026, 1, 6))))

    def test_a_catalogue_that_cannot_be_read_is_a_problem(self):
        self.run_it()
        self.write("archive/catalog.json", "{ not json")
        self.assertTrue(any("can't be read" in p for p in ARCHIVE.check()))
        self.write("archive/catalog.json", json.dumps(
            {"items": [{"path": "archive/STATUS/2026-01-01.md"}]}))
        self.assertTrue(any("lacks" in p for p in ARCHIVE.check()))

    def test_a_stray_file_and_a_missing_file_are_problems(self):
        self.run_it()
        self.write("archive/notes.txt", "stray\n")
        os.remove(os.path.join(self.root, "archive", "STATUS",
                               "2026-01-01.md"))
        problems = ARCHIVE.check()
        self.assertTrue(any("not an archive file" in p for p in problems))
        self.assertTrue(any("in the catalogue but missing" in p
                            for p in problems))

    def test_an_entry_of_another_day_in_a_day_file_is_a_problem(self):
        self.run_it()
        path = "archive/STATUS/2026-01-02.md"
        self.write(path, self.read(path).replace(
            "- 2026-01-02, founder, two.", "- 2026-01-09, founder, two."))
        ARCHIVE.rehash(path, "a test", today="2026-01-07")
        self.assertTrue(any("an entry dated 2026-01-09" in p
                            for p in ARCHIVE.check()))

    def test_a_second_pointer_is_a_problem(self):
        self.run_it()
        pointer = ARCHIVE.pointer_text("STATUS")
        self.write("STATUS.md", self.read("STATUS.md").replace(
            "- 2026-01-05 Claude: five.\n",
            "- 2026-01-05 Claude: five.\n\n" + pointer + "\n"))
        self.assertTrue(any("the one line that points" in p
                            for p in ARCHIVE.check()))

    def test_a_section_emptied_by_a_run_ends_with_one_blank_line(self):
        self.run_it(keep=1)
        page = self.read("STATUS.md")
        self.assertIn(ARCHIVE.pointer_text("STATUS") + "\n\n## Log", page)
        self.assertNotIn("\n\n\n", page)

    def test_a_pointer_like_line_in_a_code_block_is_kept(self):
        pointer = ARCHIVE.pointer_text("COLLABORATING")
        self.write("docs/COLLABORATING.md", COLLAB.replace(
            "Who writes here, and why.\n",
            "Who writes here, and why.\n\n```text\n" + pointer
            + "\n```\n"))
        self.commit()
        self.run_it()
        self.assertIn("```text\n" + pointer + "\n```",
                      self.read("docs/COLLABORATING.md"))


class TheRepository(unittest.TestCase):
    """The repository's own archive."""

    def test_the_archive_is_in_step(self):
        notes = []
        self.assertEqual(ARCHIVE.check(notes), [])
        # CI fetches the commits the catalogue names, so every archived
        # entry is compared with its page there; locally, a clone made
        # with its history has them too.
        if os.environ.get("OPEN_WORLDS_REQUIRE_ARCHIVE_COMMITS"):
            self.assertEqual(notes, [])

    def test_the_script_says_what_it_would_move(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = ARCHIVE.main([])
        self.assertEqual(code, 0)
        self.assertIn("STATUS.md: keeps", out.getvalue())


if __name__ == "__main__":
    unittest.main()
