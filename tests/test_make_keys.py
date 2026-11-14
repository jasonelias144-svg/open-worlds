"""The tool that makes the project's keys (formats/make_keys.py), run on
throwaway directories: it makes a key for each role, signs the first key
list with the new root, keeps the private halves only outside this
repository, never writes over a key, and prints no secret."""
import contextlib
import io
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from formats import make_keys, records
from tests.test_no_private_keys import private_key_material


class TestMakeKeys(unittest.TestCase):

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.place = Path(self._dir.name)
        self.private = self.place / "private"
        self.private.mkdir()
        self.key_list = self.place / "public" / "key-list.json"

    def run_tool(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = make_keys.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_it_makes_every_role_and_a_key_list_that_holds(self):
        code, out, _ = self.run_tool("--private", str(self.private),
                                     "--key-list", str(self.key_list))
        self.assertEqual(code, 0)
        key_list = json.loads(self.key_list.read_text(encoding="utf-8"))
        records.check(key_list)
        self.assertEqual(key_list["version"], 1)
        self.assertEqual([(e["role"], e["name"], "sealing" in e)
                          for e in key_list["keys"]], make_keys.PLAN)
        self.assertEqual(records.key_list_root(key_list),
                         key_list["issuer"])
        make_keys.check_kept(key_list, self.private)
        self.assertEqual(private_key_material(out), [])

    def test_the_private_halves_are_readable_by_their_owner_only(self):
        self.run_tool("--private", str(self.private),
                      "--key-list", str(self.key_list))
        kept = sorted((self.private / "keys").iterdir())
        self.assertEqual(len(kept), len(make_keys.PLAN))
        for path in kept:
            with self.subTest(path=path.name):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertTrue(private_key_material(
                    path.read_text(encoding="utf-8")))
        self.assertEqual(private_key_material(
            self.key_list.read_text(encoding="utf-8")), [])

    def test_every_key_is_new(self):
        a = make_keys.make_keys()
        b = make_keys.make_keys()
        keys = [h["signing"] for h in a + b] + [
            h["sealing"] for h in a + b if "sealing" in h]
        self.assertEqual(len(keys), len(set(keys)))

    def test_it_never_writes_over_a_key(self):
        self.run_tool("--private", str(self.private),
                      "--key-list", str(self.key_list))
        before = {p.name: p.read_text() for p in
                  (self.private / "keys").iterdir()}
        self.key_list.unlink()
        code, _, err = self.run_tool("--private", str(self.private),
                                     "--key-list", str(self.key_list))
        self.assertEqual(code, 1)
        self.assertIn("kept there already", err)
        self.assertEqual({p.name: p.read_text() for p in
                          (self.private / "keys").iterdir()}, before)
        self.assertFalse(self.key_list.exists())

    def test_it_refuses_this_repository(self):
        for place in (make_keys.REPOSITORY, make_keys.REPOSITORY / "keys",
                      make_keys.REPOSITORY / "formats"):
            with self.subTest(place=str(place)):
                with self.assertRaises(make_keys.KeyMakingError):
                    make_keys.check_private_place(
                        place if place.is_dir() else make_keys.REPOSITORY)
        code, _, err = self.run_tool(
            "--private", str(make_keys.REPOSITORY / "formats"),
            "--key-list", str(self.key_list))
        self.assertEqual(code, 1)
        self.assertIn("this repository", err)
        self.assertFalse(self.key_list.exists())

    def test_a_place_inside_the_repository_is_refused_without_git(self):
        # Without Git, or before a first commit, the path alone decides.
        repository = self.place / "not-yet-a-repository"
        inside = repository / "keys"
        inside.mkdir(parents=True)
        for place in (repository, inside):
            with self.subTest(place=place.name):
                with self.assertRaises(make_keys.KeyMakingError):
                    make_keys.check_private_place(place,
                                                  repository=repository)

    def test_it_refuses_a_link_into_this_repository(self):
        link = self.place / "a-link"
        os.symlink(make_keys.REPOSITORY / "formats", link)
        with self.assertRaises(make_keys.KeyMakingError):
            make_keys.check_private_place(link)

    def _repository(self, path):
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t",
               "-C", str(path)]
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        # Its own content, so that two made in the same second have
        # different first commits.
        (path / "a").write_text(str(path))
        subprocess.run(git + ["add", "a"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "a"], check=True)

    def test_it_refuses_another_checkout_of_this_repository(self):
        # A clone elsewhere is the same repository: it shares the first
        # commit, so it is refused wherever it is.
        public = self.place / "public-repository"
        self._repository(public)
        clone = self.place / "elsewhere" / "clone"
        subprocess.run(["git", "clone", "-q", str(public), str(clone)],
                       check=True)
        with self.assertRaises(make_keys.KeyMakingError):
            make_keys.check_private_place(clone, repository=public)
        with self.assertRaises(make_keys.KeyMakingError):
            make_keys.check_private_place(clone / "", repository=public)

    def test_another_repository_or_an_empty_one_is_allowed(self):
        public = self.place / "public-repository"
        self._repository(public)
        other = self.place / "other-repository"
        self._repository(other)
        empty = self.place / "empty-repository"
        subprocess.run(["git", "init", "-q", str(empty)], check=True)
        make_keys.check_private_place(other, repository=public)
        make_keys.check_private_place(empty, repository=public)
        make_keys.check_private_place(self.private, repository=public)

    def test_a_kept_key_that_differs_is_found(self):
        self.run_tool("--private", str(self.private),
                      "--key-list", str(self.key_list))
        key_list = json.loads(self.key_list.read_text(encoding="utf-8"))
        path = self.private / "keys" / make_keys.file_name("ALICE")
        other = make_keys.make_keys([("individual", "ALICE", True)])[0]
        os.chmod(path, 0o600)
        path.write_text(json.dumps(other))
        with self.assertRaises(make_keys.KeyMakingError):
            make_keys.check_kept(key_list, self.private)

    def test_file_names(self):
        self.assertEqual(make_keys.file_name("the project's templates"),
                         "the-projects-templates.json")
        self.assertEqual(make_keys.file_name("ALICE"), "alice.json")
        names = [make_keys.file_name(n) for _, n, _ in make_keys.PLAN]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
