"""The tool that makes the project's keys (formats/make_keys.py), run on
throwaway directories: it makes a key for each role, signs the first key
list with the new root, keeps the private halves only in a full clone of
another repository, never writes over a key or through a link, leaves
nothing behind when it fails, and prints no secret.

"This repository" is a throwaway one here (`make_keys.REPOSITORY` is
patched), since a CI checkout is shallow and the tool refuses to run
beside a shallow clone; one test checks the real checkout's own paths."""
import contextlib
import io
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from formats import make_keys, records
from tests.test_no_private_keys import private_key_material

REAL_REPOSITORY = make_keys.REPOSITORY


def git(path, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    "-c", "init.defaultBranch=main", "-C", str(path),
                    *args], check=True, capture_output=True)


def repository(path, remote=None, commits=1):
    """A repository at `path`, with commits of its own content, so that
    two made in the same second differ, and a remote if one is given."""
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    for i in range(commits):
        (path / "a").write_text(f"{path} {i}")
        git(path, "add", "a")
        git(path, "commit", "-q", "-m", f"commit {i}")
    if remote:
        git(path, "remote", "add", "origin", remote)
    return path


PUBLIC_URL = "https://example.invalid/project/the-public-repository.git"
PRIVATE_URL = "https://example.invalid/project/the-private-keys.git"


class TestMakeKeys(unittest.TestCase):

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.place = Path(self._dir.name)
        # Git's own config files, kept apart from this machine's, so that
        # a push target set there can't change what these tests see.
        self.global_config = self.place / "gitconfig"
        self.global_config.write_text("")
        env = mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(self.global_config),
            "GIT_CONFIG_NOSYSTEM": "1"})
        env.start()
        self.addCleanup(env.stop)
        self.public = repository(self.place / "public", PUBLIC_URL,
                                 commits=3)
        patch = mock.patch.object(make_keys, "REPOSITORY", self.public)
        patch.start()
        self.addCleanup(patch.stop)
        self.private = repository(self.place / "private", PRIVATE_URL,
                                  commits=0)
        self.key_list = self.public / "keys" / "key-list.json"

    def run_tool(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = make_keys.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def make(self):
        return self.run_tool("--private", str(self.private),
                             "--key-list", str(self.key_list))

    def refused(self, place, why=None):
        with self.assertRaises(make_keys.KeyMakingError) as caught:
            make_keys.check_private_place(place)
        if why:
            self.assertIn(why, str(caught.exception))

    def left_behind(self):
        """What a run left in the private checkout, apart from Git's own
        folder, and beside the key list."""
        names = [p.name for p in self.private.iterdir() if p.name != ".git"]
        if self.key_list.parent.is_dir():
            names += [p.name for p in self.key_list.parent.iterdir()]
        return sorted(names)

    # Making.

    def test_it_makes_every_role_and_a_key_list_that_holds(self):
        code, out, _ = self.make()
        self.assertEqual(code, 0)
        key_list = json.loads(self.key_list.read_text(encoding="utf-8"))
        records.check(key_list)
        self.assertEqual(key_list["version"], 1)
        self.assertEqual([(e["role"], e["name"], "sealing" in e)
                          for e in key_list["keys"]], make_keys.PLAN)
        self.assertEqual(records.key_list_root(key_list),
                         key_list["issuer"])
        self.assertEqual(records.key_list_chain_problems([key_list]), [])
        make_keys.check_kept(key_list, self.private)
        self.assertEqual(private_key_material(out), [])
        self.assertEqual(self.left_behind(), ["key-list.json", "keys"])

    def test_the_private_halves_are_readable_by_their_owner_only(self):
        self.make()
        folder = self.private / "keys"
        self.assertEqual(stat.S_IMODE(folder.stat().st_mode), 0o700)
        kept = sorted(folder.iterdir())
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

    # Never over a key, never through a link.

    def test_it_never_writes_over_a_key(self):
        self.make()
        before = {p.name: p.read_text() for p in
                  (self.private / "keys").iterdir()}
        self.key_list.unlink()
        code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("is there already", err)
        self.assertEqual({p.name: p.read_text() for p in
                          (self.private / "keys").iterdir()}, before)
        self.assertFalse(self.key_list.exists())

    def test_a_keys_folder_already_there_is_refused(self):
        (self.private / "keys").mkdir()
        code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("is there already", err)
        self.assertEqual(list((self.private / "keys").iterdir()), [])
        self.assertFalse(self.key_list.exists())

    def test_a_keys_link_into_this_repository_is_refused(self):
        planted = self.public / "planted"
        planted.mkdir()
        os.symlink(planted, self.private / "keys")
        code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("is there already", err)
        self.assertEqual(list(planted.iterdir()), [])
        with self.assertRaises(make_keys.KeyMakingError):
            make_keys.write_private_halves(make_keys.make_keys(),
                                           self.private)
        self.assertEqual(list(planted.iterdir()), [])

    def test_no_secret_is_written_if_keys_is_there_already(self):
        (self.private / "keys").mkdir()
        with mock.patch.object(make_keys, "_write_new") as write:
            with self.assertRaises(make_keys.KeyMakingError):
                make_keys.stage_private_halves(make_keys.make_keys(),
                                               self.private)
        write.assert_not_called()

    def test_keys_appearing_while_they_are_made_is_refused(self):
        staging = make_keys.stage_private_halves(make_keys.make_keys(),
                                                 self.private)
        (self.private / "keys").mkdir()
        with self.assertRaises(make_keys.KeyMakingError):
            make_keys.keep(staging, self.private)
        self.assertEqual(list((self.private / "keys").iterdir()), [])
        self.assertTrue(staging.is_dir())

    def test_two_holders_that_would_share_a_file_are_refused(self):
        made = make_keys.make_keys([("individual", "ALICE", True),
                                    ("individual", "alice", True)])
        with self.assertRaises(make_keys.KeyMakingError):
            make_keys.stage_private_halves(made, self.private)
        self.assertEqual(self.left_behind(), [])

    def test_an_existing_key_list_is_refused_before_any_key_is_made(self):
        self.key_list.parent.mkdir()
        self.key_list.write_text("{}")
        code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("is there already", err)
        self.assertEqual(self.left_behind(), ["key-list.json"])

    # Everything or nothing.

    def test_a_key_list_that_cant_be_written_leaves_nothing(self):
        # The key list's folder is a file, so it can't be made.
        self.key_list.parent.write_text("not a folder")
        code, out, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("not made", err)
        self.assertEqual(out, "")
        self.assertEqual(
            [p.name for p in self.private.iterdir() if p.name != ".git"],
            [])

    def test_a_failure_moving_the_keys_into_place_leaves_nothing(self):
        with mock.patch.object(make_keys.os, "rename",
                               side_effect=OSError("no room")):
            code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("no room", err)
        self.assertEqual(self.left_behind(), [])

    def test_a_key_list_appearing_while_it_is_written_leaves_nothing(self):
        with mock.patch.object(make_keys.os, "link",
                               side_effect=FileExistsError("there now")):
            code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("there now", err)
        self.assertEqual(self.left_behind(), [])

    def test_a_staged_list_that_cant_be_removed_leaves_no_secret(self):
        real_unlink = Path.unlink

        def refuses_staged(path, *args, **kwargs):
            if path.name.endswith(".being-made"):
                raise PermissionError("not allowed")
            return real_unlink(path, *args, **kwargs)

        with mock.patch.object(Path, "unlink", autospec=True,
                               side_effect=refuses_staged):
            code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("not allowed", err)
        # Only the public list's staged copy is left, and it says so.
        self.assertEqual(self.left_behind(), [".key-list.json.being-made"])

    def failing_writes(self, fail_on):
        """os.fdopen, made to fail writing on its `fail_on`th call."""
        real_fdopen = os.fdopen
        calls = []

        class FailingFile:
            def __init__(self, f):
                self.f = f

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                self.f.close()
                return False

            def write(self, text):
                raise OSError(28, "No space left on device")

        def fdopen(fd, *args, **kwargs):
            calls.append(fd)
            f = real_fdopen(fd, *args, **kwargs)
            return FailingFile(f) if len(calls) == fail_on else f

        return mock.patch.object(make_keys.os, "fdopen", fdopen)

    def test_a_write_that_fails_leaves_no_file(self):
        path = self.place / "a-new-file"
        with self.failing_writes(1):
            with self.assertRaises(OSError):
                make_keys._write_new(path, "text", 0o600)
        self.assertFalse(path.exists())

    def test_a_staged_list_that_cant_be_written_leaves_nothing(self):
        # Eight private halves are written, then the staged key list.
        with self.failing_writes(len(make_keys.PLAN) + 1):
            code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("No space left", err)
        self.assertEqual(self.left_behind(), [])

    def test_a_failure_writing_a_private_half_leaves_nothing(self):
        real = make_keys._write_new
        calls = []

        def fails_on_the_third(path, text, mode):
            calls.append(path)
            if len(calls) == 3:
                raise OSError("disk full")
            real(path, text, mode)

        with mock.patch.object(make_keys, "_write_new", fails_on_the_third):
            code, _, err = self.make()
        self.assertEqual(code, 1)
        self.assertIn("disk full", err)
        self.assertEqual(
            [p.name for p in self.private.iterdir() if p.name != ".git"],
            [])
        self.assertFalse(self.key_list.exists())

    # Only a full clone of another repository.

    def test_it_refuses_this_repository_and_places_inside_it(self):
        for place in (self.public, self.public / "sub"):
            place.mkdir(exist_ok=True)
            with self.subTest(place=place.name):
                self.refused(place, "inside this repository's working tree")
        code, _, err = self.run_tool("--private", str(self.public / "sub"),
                                     "--key-list", str(self.key_list))
        self.assertEqual(code, 1)
        self.assertIn("this repository", err)
        self.assertFalse(self.key_list.exists())

    def test_it_refuses_places_inside_the_real_checkout(self):
        # The real checkout, wherever these tests run: the path decides
        # before anything else, so a shallow CI checkout is refused too.
        for place in (REAL_REPOSITORY, REAL_REPOSITORY / "formats",
                      REAL_REPOSITORY / "tests"):
            with self.subTest(place=place.name):
                with self.assertRaises(make_keys.KeyMakingError) as caught:
                    make_keys.check_private_place(
                        place, repository=REAL_REPOSITORY)
                self.assertIn("inside this repository's working tree",
                              str(caught.exception))

    def test_a_place_inside_the_repository_is_refused_without_git(self):
        # Without Git, or before a first commit, the path alone decides.
        not_yet = self.place / "not-yet-a-repository"
        inside = not_yet / "keys"
        inside.mkdir(parents=True)
        for place in (not_yet, inside):
            with self.subTest(place=place.name):
                with self.assertRaises(make_keys.KeyMakingError) as caught:
                    make_keys.check_private_place(place, repository=not_yet)
                self.assertIn("inside this repository's working tree",
                              str(caught.exception))

    def test_it_refuses_a_link_into_this_repository(self):
        (self.public / "sub").mkdir()
        link = self.place / "a-link"
        os.symlink(self.public / "sub", link)
        self.refused(link, "inside this repository's working tree")

    def test_it_refuses_what_isnt_the_top_of_a_checkout(self):
        plain = self.place / "plain"
        plain.mkdir()
        self.refused(plain, "not the top of a Git checkout")
        (self.private / "sub").mkdir()
        self.refused(self.private / "sub", "not the top of a Git checkout")
        self.refused(self.place / "nowhere", "not a directory")

    def test_it_refuses_another_clone_of_this_repository(self):
        # A clone elsewhere is the same repository: its remote names it,
        # and it shares the first commit, so it is refused wherever it is.
        clone = self.place / "elsewhere" / "clone"
        subprocess.run(["git", "clone", "-q", str(self.public), str(clone)],
                       check=True, capture_output=True)
        self.refused(clone)
        self.refused(Path(str(clone) + "/"))
        # With its remote changed, its first commit still gives it away.
        git(clone, "remote", "set-url", "origin", PRIVATE_URL)
        self.refused(clone, "a checkout of this repository")

    def test_it_refuses_a_shallow_clone(self):
        shallow = self.place / "shallow"
        subprocess.run(["git", "clone", "-q", "--depth", "1",
                        f"file://{self.public}", str(shallow)],
                       check=True, capture_output=True)
        # Its remote changed, and its first commit is only where its
        # history was cut: the only sign left is that it is shallow.
        git(shallow, "remote", "set-url", "origin", PRIVATE_URL)
        self.refused(shallow, "shallow")

    def test_it_refuses_to_run_beside_a_shallow_clone(self):
        shallow_public = self.place / "shallow-public"
        subprocess.run(["git", "clone", "-q", "--depth", "1",
                        f"file://{self.public}", str(shallow_public)],
                       check=True, capture_output=True)
        with self.assertRaises(make_keys.KeyMakingError) as caught:
            make_keys.check_private_place(self.private,
                                          repository=shallow_public)
        self.assertIn("shallow", str(caught.exception))

    def test_it_refuses_a_worktree_of_this_repository(self):
        for args in (["-b", "a-branch"], ["--orphan", "-b", "an-orphan"]):
            tree = self.place / args[-1]
            with self.subTest(worktree=args[-1]):
                try:
                    git(self.public, "worktree", "add", "-q", *args,
                        str(tree))
                except subprocess.CalledProcessError:
                    # `--orphan` came with Git 2.42.
                    self.skipTest("this Git can't make an orphan worktree")
                self.refused(tree, "a worktree of this repository")

    def test_it_refuses_an_empty_clone_whose_remote_is_this_repository(self):
        # Before a first commit, only the remote tells the two apart.
        for i, url in enumerate((
                PUBLIC_URL,
                "git@example.invalid:Project/The-Public-Repository",
                "http://proxy@127.0.0.1:1/git/project/the-public-repository/")):
            empty = repository(self.place / f"empty-{i}", url, commits=0)
            with self.subTest(url=url):
                self.refused(empty, "whose remote is this repository")

    def test_it_refuses_a_remote_that_is_a_path_on_this_computer(self):
        # A push from there lands in a checkout of this repository, one
        # push away from where it is published.
        for i, url in enumerate((str(self.public), "../public",
                                 f"file://{self.public}")):
            empty = repository(self.place / f"by-path-{i}", url, commits=0)
            with self.subTest(url=url):
                self.refused(empty, "a path on this computer")

    def test_it_refuses_a_clone_on_a_branch_with_no_commits_yet(self):
        # Its HEAD has no history, but its other branches share this
        # repository's first commit.
        clone = self.place / "clone"
        subprocess.run(["git", "clone", "-q", str(self.public), str(clone)],
                       check=True, capture_output=True)
        git(clone, "remote", "set-url", "origin", PRIVATE_URL)
        git(clone, "checkout", "-q", "--orphan", "fresh")
        self.refused(clone, "a checkout of this repository")

    def test_it_refuses_a_push_target_that_isnt_one_of_its_remotes(self):
        # `git remote -v` doesn't show these, but `git push` goes there.
        settings = [("remote.pushDefault", str(self.public)),
                    ("remote.pushDefault", PUBLIC_URL),
                    ("branch.main.pushRemote", str(self.public)),
                    ("branch.main.remote", "../public")]
        for i, (key, value) in enumerate(settings):
            place = repository(self.place / f"pushes-{i}", PRIVATE_URL,
                               commits=0)
            git(place, "config", key, value)
            with self.subTest(key=key, value=value):
                self.refused(place, "isn't one of its remotes")

    def test_a_push_target_with_spaces_is_not_its_remote(self):
        # Git keeps the spaces inside a quoted value, and reads " origin"
        # as a path, not as the remote named origin.
        for i, value in enumerate((" origin", "origin ", "origin\t",
                                   "origin\nx")):
            place = repository(self.place / f"spaced-{i}", PRIVATE_URL,
                               commits=0)
            git(place, "config", "remote.pushDefault", value)
            with self.subTest(value=value):
                self.refused(place, "isn't one of its remotes")

    def test_it_refuses_a_remote_kept_the_old_way(self):
        # Files in .git/remotes or .git/branches: Git still reads them for
        # a name that isn't a configured remote; `git remote -v` doesn't
        # show them.
        for i, (kind, text) in enumerate((
                ("branches", f"{self.public}\n"),
                ("remotes", f"URL: {self.public}\n"))):
            place = repository(self.place / f"old-style-{i}", PRIVATE_URL,
                               commits=0)
            folder = place / ".git" / kind
            folder.mkdir(exist_ok=True)
            (folder / "origin").write_text(text)
            with self.subTest(kind=kind):
                self.refused(place, "kept the old way")

    def test_empty_old_style_folders_are_allowed(self):
        for kind in ("branches", "remotes"):
            (self.private / ".git" / kind).mkdir(exist_ok=True)
        make_keys.check_private_place(self.private)

    def test_it_refuses_a_remote_helper_or_an_address_with_spaces(self):
        for i, url in enumerate(("ext::git-remote-ext %S",
                                 "fd::17",
                                 "https://example.invalid/project/the "
                                 "private-keys.git")):
            place = repository(self.place / f"helper-{i}", url, commits=0)
            with self.subTest(url=url):
                self.refused(place, "plain address")

    def test_a_push_target_set_in_gits_own_config_is_refused_too(self):
        self.global_config.write_text(
            f"[remote]\n\tpushDefault = {self.public}\n")
        self.refused(self.private, "isn't one of its remotes")

    def test_push_targets_that_are_its_remotes_are_allowed(self):
        for i, (key, value) in enumerate([
                ("remote.pushDefault", "origin"),
                ("branch.main.remote", "origin"),
                ("branch.main.remote", "."),
                ("branch.main.pushRemote", "origin")]):
            place = repository(self.place / f"allowed-{i}", PRIVATE_URL,
                               commits=0)
            git(place, "config", key, value)
            with self.subTest(key=key, value=value):
                make_keys.check_private_place(place)

    def test_local_paths(self):
        for url, local in [("/home/someone/repo", True), ("../repo", True),
                           ("repo", True), ("file:///home/someone/repo", True),
                           ("FILE:///repo", True), ("https://host/o/r", False),
                           ("git@host:o/r.git", False),
                           ("ssh://git@host/o/r", False)]:
            with self.subTest(url=url):
                self.assertEqual(make_keys.is_local_path(url), local)

    def test_it_refuses_a_checkout_with_no_remote(self):
        self.refused(repository(self.place / "lone"), "no remote")

    def test_another_repository_is_allowed_empty_or_not(self):
        make_keys.check_private_place(self.private)
        other = repository(self.place / "other", PRIVATE_URL, commits=2)
        make_keys.check_private_place(other)

    def test_repository_names(self):
        for url, name in [
                ("https://github.com/Owner/Repo.git", "owner/repo"),
                ("git@github.com:owner/repo", "owner/repo"),
                ("ssh://git@github.com/owner/repo.git/", "owner/repo"),
                ("http://local_proxy@127.0.0.1:8080/git/owner/repo",
                 "owner/repo"),
                ("/home/someone/owner/repo", "owner/repo"),
                ("repo", None)]:
            with self.subTest(url=url):
                self.assertEqual(make_keys.repository_name(url), name)
        self.assertNotEqual(
            make_keys.repository_name("https://github.com/o/repo"),
            make_keys.repository_name("https://github.com/o/repo-private"))

    # Checking what was kept.

    def test_a_kept_key_that_differs_is_found(self):
        self.make()
        key_list = json.loads(self.key_list.read_text(encoding="utf-8"))
        path = self.private / "keys" / make_keys.file_name("ALICE")
        other = make_keys.make_keys([("individual", "ALICE", True)])[0]
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
