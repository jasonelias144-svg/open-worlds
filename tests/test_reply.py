"""The file the founder gives DeepSeek is what its sources make.

docs/reply.py builds one file for each return to DeepSeek: the
technical lead's reply, then the code as it stands, each file whole
(sketches/replies/README.md). This test builds small replies of its own
to check the script, and holds every reply kept in sketches/replies/ to
its spec: within its limit, ending with its last line, and, while it is
current, byte for byte what its text and the repository's files make.

It imports docs/reply.py and nothing from sketches/: the files there
are read as text.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLIES = os.path.join(ROOT, "sketches", "replies")


def load_reply():
    spec = importlib.util.spec_from_file_location(
        "docs_reply", os.path.join(ROOT, "docs", "reply.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPLY = load_reply()


def kept_specs():
    return sorted(os.path.join(REPLIES, name) for name in os.listdir(REPLIES)
                  if name.endswith(".json"))


class Small(unittest.TestCase):
    """A reply built here, in a folder of its own."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "code", "src"))
        os.makedirs(os.path.join(self.root, "replies"))
        self.write("code/src/a.rs", "fn a() {}\n")
        self.write("code/Cargo.toml", "[package]\nname = \"a\"")  # no last newline
        self.write("replies/r.txt", "Dear reader.\n\n")
        self.spec = {
            "text": "r.txt", "out": "r-out.txt", "root": "code",
            "name": "crate", "limit": 1000, "current": True,
            "files": [["Cargo.toml", "as written"], ["src/a.rs", "changed"]],
            "folder": os.path.join(self.root, "replies"),
        }

    def write(self, path, text):
        with open(os.path.join(self.root, path), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(text)

    def build(self):
        return REPLY.build(self.spec, self.root)

    def test_it_is_the_text_then_each_file_whole_then_the_last_line(self):
        self.assertEqual(
            self.build(),
            "Dear reader.\n\n"
            "----- FILE: crate/Cargo.toml  (as written) -----\n"
            "```toml\n[package]\nname = \"a\"\n```\n\n"
            "----- FILE: crate/src/a.rs  (changed) -----\n"
            "```rust\nfn a() {}\n```\n\n"
            "END OF FILE\n")

    def test_the_files_can_be_read_back_out_of_it(self):
        self.assertEqual(
            REPLY.embedded(self.build()),
            [("crate/Cargo.toml", "as written", "[package]\nname = \"a\"\n"),
             ("crate/src/a.rs", "changed", "fn a() {}\n")])

    def test_a_file_that_would_end_its_own_block_is_refused(self):
        self.write("code/src/a.rs", "// ```\nfn a() {}\n")
        with self.assertRaisesRegex(REPLY.Problem, "three backticks"):
            self.build()

    def test_a_reply_over_its_limit_is_refused(self):
        self.spec["limit"] = 100
        with self.assertRaisesRegex(REPLY.Problem, "over the limit of 100"):
            self.build()

    def test_a_text_that_holds_the_last_line_is_refused(self):
        self.write("replies/r.txt", "Dear reader.\nEND OF FILE\n\n")
        with self.assertRaisesRegex(REPLY.Problem, "layout"):
            self.build()

    def test_a_text_must_end_with_an_empty_line(self):
        self.write("replies/r.txt", "Dear reader.\n")
        with self.assertRaisesRegex(REPLY.Problem, "empty line"):
            self.build()

    def test_a_kept_file_out_of_step_with_its_sources_is_caught(self):
        self.write("replies/r-out.txt", self.build())
        self.assertEqual(REPLY.check(self.spec, self.root), [])
        self.write("code/src/a.rs", "fn a() { /* moved on */ }\n")
        self.assertEqual(
            REPLY.check(self.spec, self.root),
            ["it is not what its text and the repository's files now make"])
        # A past reply is a record: it is no longer held to the files.
        self.spec["current"] = False
        self.assertEqual(REPLY.check(self.spec, self.root), [])

    def test_a_kept_file_cut_short_is_caught_even_when_past(self):
        whole = self.build()
        self.write("replies/r-out.txt", whole[:-len("END OF FILE\n")])
        self.spec["current"] = False
        self.assertEqual(REPLY.check(self.spec, self.root),
                         ["it doesn't end with the line END OF FILE"])

    def test_a_missing_file_is_said(self):
        self.assertEqual(REPLY.check(self.spec, self.root),
                         ["r-out.txt is missing"])

    def test_reading_back_says_what_is_wrong(self):
        whole = self.build()
        cargo = ("----- FILE: crate/Cargo.toml  (as written) -----\n"
                 "```toml\n[package]\nname = \"a\"\n```\n\n")
        a = ("----- FILE: crate/src/a.rs  (changed) -----\n"
             "```rust\nfn a() {}\n```\n\n")
        self.assertEqual(whole, "Dear reader.\n\n" + cargo + a
                         + "END OF FILE\n")
        order = "the files in it are not the spec's, in order"
        end = "it doesn't end with the line END OF FILE"
        cases = [
            ("as built", whole, []),
            ("a file changed", whole.replace("fn a() {}", "fn b() {}"),
             ["crate/src/a.rs differs from the repository"]),
            ("a file left out", whole.replace(a, ""), [order]),
            ("the files the other way round",
             "Dear reader.\n\n" + a + cargo + "END OF FILE\n",
             [order, "crate/src/a.rs differs from the repository",
              "crate/Cargo.toml differs from the repository"]),
            ("a file twice", whole.replace(a, a + a), [order]),
            ("cut off before the last line",
             whole[:-len("END OF FILE\n")], [end]),
            ("cut off inside the last file", whole[:whole.index("fn a")],
             [order, end]),
            ("no newline after the last line", whole[:-1], [end]),
            ("a newline too many", whole + "\n", [end]),
            ("something after the last line", whole + "more\n", [end]),
        ]
        for name, text, want in cases:
            with self.subTest(name):
                self.assertEqual(
                    REPLY.read_back(self.spec, text, self.root), want)

    def test_the_limit_itself_is_allowed_and_one_byte_more_is_not(self):
        size = len(self.build().encode("utf-8"))
        self.spec["limit"] = size
        self.assertEqual(len(self.build().encode("utf-8")), size)
        self.spec["limit"] = size - 1
        with self.assertRaisesRegex(
                REPLY.Problem, f"{size} bytes, over the limit of {size - 1}"):
            self.build()

    def test_a_note_must_fit_on_one_line(self):
        for note in ("two\nlines", "a return\rin it"):
            with self.subTest(note=note):
                self.spec["files"][0][1] = note
                with self.assertRaisesRegex(REPLY.Problem, "one line"):
                    self.build()
        # What looks like the end of a header is still only a note.
        self.spec["files"][0][1] = "as written) -----"
        self.assertEqual(REPLY.embedded(self.build())[0][1],
                         "as written) -----")

    def test_a_path_stays_where_the_spec_says(self):
        self.write("secret.txt", "not for the reader\n")
        for path in ("../secret.txt", os.path.join(self.root, "secret.txt"),
                     "src/../../secret.txt", "src//a.rs", "./src/a.rs",
                     "src/a b.rs", "src\\a.rs", ""):
            with self.subTest(path=path):
                self.spec["files"][1][0] = path
                with self.assertRaisesRegex(REPLY.Problem, "under \"root\""):
                    self.build()
        self.spec["files"][1][0] = "src/a.rs"
        for key in ("out", "text"):
            for name in ("../x.txt", "sub/x.txt", "/tmp/x.txt", "..", ""):
                with self.subTest(key=key, name=name):
                    spec = dict(self.spec, **{key: name})
                    with self.assertRaisesRegex(REPLY.Problem, "beside"):
                        REPLY.build(spec, self.root)
                    with self.assertRaisesRegex(REPLY.Problem, "beside"):
                        REPLY.check(spec, self.root)
        # Writing must never overwrite the reply's own text, or a spec.
        for out in ("r.txt", "r.json", "other.json"):
            with self.subTest(out=out):
                with self.assertRaisesRegex(REPLY.Problem, "overwrite"):
                    REPLY.build(dict(self.spec, out=out), self.root)
        for path in ("src/a\x00.rs", "src/a\x07.rs"):
            with self.subTest(path=path):
                self.spec["files"][1][0] = path
                with self.assertRaisesRegex(REPLY.Problem, "under \"root\""):
                    self.build()
        self.spec["files"][1][0] = "src/a.rs"
        for limit in (0, -1, True, "1000", 10.5, None):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(REPLY.Problem, "whole number"):
                    REPLY.build(dict(self.spec, limit=limit), self.root)
        for root in ("..", "/", "code/../.."):
            with self.subTest(root=root):
                with self.assertRaisesRegex(REPLY.Problem, "\"root\""):
                    REPLY.build(dict(self.spec, root=root), self.root)

    def test_what_cannot_be_read_is_said_not_thrown(self):
        self.write("replies/r-out.txt", self.build())
        os.remove(os.path.join(self.root, "code", "src", "a.rs"))
        with self.assertRaisesRegex(REPLY.Problem, "src/a.rs: can't be read"):
            self.build()
        self.assertEqual(REPLY.check(self.spec, self.root),
                         ["src/a.rs: can't be read under code"])
        self.write("code/src/a.rs", "fn a() {}\n")
        for files in (["Cargo.toml"], [["Cargo.toml"]],
                      [["Cargo.toml", "a note", "more"]], [["Cargo.toml", 1]],
                      "Cargo.toml"):
            with self.subTest(files=files):
                with self.assertRaisesRegex(REPLY.Problem, "pairs"):
                    REPLY.build(dict(self.spec, files=files), self.root)
        with open(os.path.join(self.root, "replies", "r-out.txt"), "wb") as f:
            f.write(b"\xff\xfe not text\nEND OF FILE\n")
        self.assertEqual(REPLY.check(self.spec, self.root), ["it is not text"])
        os.remove(os.path.join(self.root, "replies", "r.txt"))
        with self.assertRaisesRegex(REPLY.Problem, "r.txt: can't be read"):
            self.build()

    def test_a_past_file_must_still_end_exactly(self):
        whole = self.build()
        self.spec["current"] = False
        for name, text in (("no newline after it", whole[:-1]),
                           ("a newline too many", whole + "\n"),
                           ("something after it", whole + "more\n")):
            with self.subTest(name):
                self.write("replies/r-out.txt", text)
                self.assertEqual(REPLY.check(self.spec, self.root),
                                 ["it doesn't end with the line END OF FILE"])

    def test_writing_it_gives_what_was_built_and_says_what_went_wrong(self):
        path = os.path.join(self.root, "replies", "r.json")
        spec = {key: self.spec[key] for key in REPLY.KEYS}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f)

        def run(*args):
            said = io.StringIO()
            with contextlib.redirect_stdout(said), \
                    contextlib.redirect_stderr(said):
                code = REPLY.main(["reply.py", *args], self.root)
            return code, said.getvalue()

        self.assertEqual(run(path),
                         (0, "r-out.txt: 176 bytes, 14 lines, 2 files\n"))
        with open(os.path.join(self.root, "replies", "r-out.txt"),
                  encoding="utf-8", newline="") as f:
            self.assertEqual(f.read(), self.build())
        self.assertEqual(run("--check", path), (0, ""))
        self.write("code/src/a.rs", "fn a() { /* moved on */ }\n")
        self.assertEqual(
            run("--check", path),
            (1, "r-out.txt: it is not what its text and the repository's "
                "files now make\n"))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dict(spec, limit=10), f)
        self.assertEqual(run(path),
                         (1, "192 bytes, over the limit of 10\n"))
        self.assertEqual(run()[0], 2)
        missing = os.path.join(self.root, "replies", "none.json")
        self.assertEqual(run(missing),
                         (1, f"{missing}: can't be read as JSON\n"))
        with open(missing, "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assertEqual(run("--check", missing),
                         (1, f"{missing}: can't be read as JSON\n"))

        # After writing, the file is read from disk as a reader would
        # read it: a problem found then is said, and the run fails.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f)
        real, calls = REPLY.read_back, []

        def second_time(*args):
            calls.append(args[1])
            return real(*args) if len(calls) == 1 else ["planted"]

        REPLY.read_back = second_time
        self.addCleanup(setattr, REPLY, "read_back", real)
        self.assertEqual(
            run(path),
            (1, "r-out.txt: planted\n"
                "r-out.txt was written, and is wrong as it stands: build it "
                "again once this is mended\n"))
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], calls[1])


class Kept(unittest.TestCase):
    """The replies in sketches/replies/."""

    def test_there_is_one(self):
        self.assertTrue(kept_specs())

    def test_each_is_what_its_spec_says(self):
        # If this fails for a current reply, the code it holds has
        # changed: write the next reply, and set this one's "current"
        # to false in the same change (sketches/replies/README.md).
        for path in kept_specs():
            with self.subTest(reply=os.path.basename(path)):
                self.assertEqual(REPLY.check(REPLY.load(path)), [])

    def test_each_has_its_three_files_and_no_others(self):
        names = set(os.listdir(REPLIES)) - {"README.md"}
        want = set()
        for path in kept_specs():
            spec = REPLY.load(path)
            want |= {os.path.basename(path), spec["text"], spec["out"]}
        self.assertEqual(names, want)

    def test_the_readme_gives_each_files_size_and_hash(self):
        with open(os.path.join(REPLIES, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        for path in kept_specs():
            spec = REPLY.load(path)
            with open(os.path.join(REPLIES, spec["out"]), "rb") as f:
                data = f.read()
            # In the reply's own row of the table, not just somewhere on
            # the page: this hash is all that holds a past reply's file.
            name = os.path.basename(path)[:-len(".json")]
            rows = [line for line in readme.split("\n")
                    if line.startswith(f"| `{name}` |")]
            with self.subTest(reply=spec["out"]):
                self.assertEqual(len(rows), 1)
                cells = [cell.strip() for cell in rows[0].split("|")]
                self.assertEqual(cells[-3], format(len(data), ","))
                self.assertEqual(
                    cells[-2], f"`{hashlib.sha256(data).hexdigest()}`")

    def test_a_spec_names_only_what_it_needs(self):
        for path in kept_specs():
            with open(path, encoding="utf-8") as f:
                spec = json.load(f)
            with self.subTest(reply=os.path.basename(path)):
                self.assertEqual(
                    sorted(spec),
                    ["current", "files", "limit", "name", "out", "root",
                     "text"])


if __name__ == "__main__":
    unittest.main()
