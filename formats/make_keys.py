"""Make the project's keys (course step 3; docs/research/KEYS.md).

    python3 -m formats.make_keys --private ../open-worlds-private \\
        --key-list keys/key-list.json

Makes one key for each role in PLAN, from the operating system's
randomness (through `cryptography`), and writes:

- **the private halves** into `--private`, one file per holder, readable
  by its owner only: `keys/<holder>.json`, with the role, the name, and
  the secrets as Multikey (`secretKeyMultibase`, and for a holder things
  are sealed to, `sealingSecretMultibase`). That directory must be the
  top of a full clone of the private repository. The tool refuses any
  place inside this repository's working tree; a worktree of it; a clone
  whose history, on any branch, shares its first commit, or whose remotes
  name it or are paths on this computer; one that can push anywhere but
  its remotes; a shallow clone; and a `keys/`
  that is there already, so it never writes over a key. A clone of a
  fork of this repository, under another name and with its history cut,
  is beyond what it can tell.
- **the first key list** to `--key-list`, signed by the new root: every
  role's public keys (formats/records.py, `open-worlds/key-list/v1`).

It makes everything or nothing: the private halves are written into a
new folder only the owner can open, and moved into place with the key
list when both are whole. It prints the public keys, never a secret.
Committing and pushing the private halves is done in the private
repository, at once; the key list comes here through a reviewed pull
request.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519

from . import records, seal
from .multikey import (did_key, sealing_from_multikey, sealing_multikey,
                       sealing_secret_from_multikey, sealing_secret_multikey,
                       secret_from_multikey, secret_multikey)

#: This repository's working tree, which no private half may enter.
REPOSITORY = Path(__file__).resolve().parent.parent

#: Each role, a name for its holder, and whether things are sealed to it
#: (docs/research/KEYS.md, "Decided by the technical lead", point 1).
PLAN: List[Tuple[str, str, bool]] = [
    ("root", "the multiverse", False),
    ("code", "the code role", False),
    ("mindRecords", "the project's mind records", False),
    ("templates", "the project's templates", False),
    ("admin", "ADMIN", False),
    ("world", "the Ur-world", True),
    ("individual", "ALICE", True),
    ("individual", "BOB", True),
]


class KeyMakingError(Exception):
    """Keys that can't be made, or kept, as asked."""


def _raw(private: Any) -> bytes:
    return private.private_bytes(serialization.Encoding.Raw,
                                 serialization.PrivateFormat.Raw,
                                 serialization.NoEncryption())


def file_name(name: str) -> str:
    """The file a holder's private halves are kept in."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", ""))
    return slug.strip("-") + ".json"


def _git(path: Path, *args: str) -> Optional[str]:
    """What `git <args>` prints in `path`, or None if it fails."""
    try:
        out = subprocess.run(["git", *args], cwd=path, capture_output=True,
                             check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.decode().strip()


def _root_commits(path: Path) -> Set[str]:
    """The first commits of every history the repository at `path`
    holds, on any branch, remote branch or tag, which name the repository
    it is a checkout of; none outside Git, or before a first commit. In a
    shallow clone these are only where its history was cut, so the caller
    refuses shallow clones."""
    return set((_git(path, "rev-list", "--max-parents=0", "--all")
                or "").split())


def is_local_path(url: str) -> bool:
    """Whether a remote's URL is a path on this computer, as Git reads
    it: `file://`, or no scheme and no `host:` before the first slash."""
    url = url.strip()
    if url.lower().startswith("file://"):
        return True
    if "://" in url:
        return False
    colon, slash = url.find(":"), url.find("/")
    return colon == -1 or (slash != -1 and slash < colon)


def repository_name(url: str) -> Optional[str]:
    """The owner and name a remote's URL points to, as `owner/name` in
    lower case (`https://host/o/n.git`, `git@host:o/n`, a proxy's
    `http://…/git/o/n`, or a path), or None."""
    u = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", url.strip())
    u = u.replace(":", "/").rstrip("/")
    if u.lower().endswith(".git"):
        u = u[:-4]
    parts = [part for part in u.split("/") if part]
    return "/".join(parts[-2:]).lower() if len(parts) >= 2 else None


def _remote_urls(path: Path) -> Set[str]:
    """Every URL the remotes of the checkout at `path` fetch from or push
    to."""
    return {fields[1] for fields in
            (line.split() for line in
             (_git(path, "remote", "-v") or "").splitlines())
            if len(fields) >= 2}


def _push_targets(path: Path) -> Set[str]:
    """Where Git may push from the checkout at `path` besides its
    remotes' own URLs: `remote.pushDefault`, `branch.<b>.pushRemote` and
    `branch.<b>.remote`, from any of Git's config files. Each is a
    remote's name, `.` (the checkout itself), or a URL or path that `git
    remote -v` doesn't show."""
    out = _git(path, "config", "--get-regexp",
               r"^(remote\.pushdefault|branch\..*\.(remote|pushremote))$")
    return {fields[1].strip() for fields in
            (line.split(None, 1) for line in (out or "").splitlines())
            if len(fields) == 2}


def _remote_names(path: Path) -> Set[str]:
    """The repositories the remotes of the checkout at `path` name."""
    return {name for name in map(repository_name, _remote_urls(path))
            if name}


def _common_dir(path: Path) -> Optional[Path]:
    """The Git directory the checkout at `path` shares with its other
    worktrees, or None outside Git."""
    out = _git(path, "rev-parse", "--git-common-dir")
    return (path / out).resolve() if out else None


def check_private_place(private: Path,
                        repository: Optional[Path] = None) -> None:
    """KeyMakingError unless `private` is the top of a full clone of
    another repository than this one: outside this repository's working
    tree, not one of its worktrees, with remotes that name another
    repository, and sharing no first commit with it. A shallow clone, of
    either, is refused, since its first commits are only where its history
    was cut."""
    private = private.resolve()
    repository = (REPOSITORY if repository is None else repository).resolve()
    if not private.is_dir():
        raise KeyMakingError(f"{private} is not a directory")
    if private == repository or repository in private.parents:
        raise KeyMakingError(
            "the private halves may not be written inside this "
            "repository's working tree")
    top = _git(private, "rev-parse", "--show-toplevel")
    if top is None or Path(top).resolve() != private:
        raise KeyMakingError(
            f"{private} is not the top of a Git checkout: clone the "
            "private repository there")
    if "true" in (_git(private, "rev-parse", "--is-shallow-repository"),
                  _git(repository, "rev-parse",
                       "--is-shallow-repository")):
        raise KeyMakingError(
            "a shallow clone can't be told from this repository by its "
            "history: fetch the whole history first (git fetch "
            "--unshallow)")
    common = _common_dir(private)
    if common is not None and common == _common_dir(repository):
        raise KeyMakingError(
            "the private halves may not be written into a worktree of "
            "this repository")
    urls = _remote_urls(private)
    if not urls:
        raise KeyMakingError(
            f"{private} has no remote: it must be a clone of the private "
            "repository")
    if any(is_local_path(url) for url in urls):
        raise KeyMakingError(
            f"{private} has a remote that is a path on this computer, "
            "which can't be told from this repository: its remotes must "
            "be the private repository's address")
    stray = (_push_targets(private)
             - set((_git(private, "remote") or "").split()) - {"."})
    if stray:
        raise KeyMakingError(
            f"{private} can push to {sorted(stray)[0]!r}, which isn't one "
            "of its remotes (remote.pushDefault, or a branch's remote or "
            "pushRemote): Git would push where `git remote -v` doesn't "
            "show")
    remotes = _remote_names(private)
    if remotes & _remote_names(repository):
        raise KeyMakingError(
            "the private halves may not be written into a clone whose "
            "remote is this repository")
    if _root_commits(private) & _root_commits(repository):
        raise KeyMakingError(
            "the private halves may not be written into a checkout of "
            "this repository")


def make_keys(plan: Sequence[Tuple[str, str, bool]] = PLAN
              ) -> List[Dict[str, Any]]:
    """A new key for each role in `plan`: the private halves as Multikey,
    with the public halves beside them."""
    made = []
    for role, name, sealed_to in plan:
        signing = _raw(ed25519.Ed25519PrivateKey.generate())
        holder: Dict[str, Any] = {
            "role": role, "name": name,
            "secretKeyMultibase": secret_multikey(signing),
            "signing": did_key(_public(signing))}
        if sealed_to:
            sealing = _raw(x25519.X25519PrivateKey.generate())
            seal.check_public(seal.public_from_secret(sealing))
            holder["sealingSecretMultibase"] = sealing_secret_multikey(
                sealing)
            holder["sealing"] = sealing_multikey(
                seal.public_from_secret(sealing))
        made.append(holder)
    return made


def _public(secret: bytes) -> bytes:
    return ed25519.Ed25519PrivateKey.from_private_bytes(
        secret).public_key().public_bytes(serialization.Encoding.Raw,
                                          serialization.PublicFormat.Raw)


def first_key_list(made: Sequence[Dict[str, Any]],
                   time: str) -> Dict[str, Any]:
    """Version 1 of the key list, naming every holder's public keys,
    signed by the root among them."""
    roots = [h for h in made if h["role"] == "root"]
    if len(roots) != 1:
        raise KeyMakingError("the plan must name exactly one root")
    keys = []
    for h in made:
        entry = {"role": h["role"], "name": h["name"],
                 "signing": h["signing"]}
        if "sealing" in h:
            entry["sealing"] = h["sealing"]
        keys.append(entry)
    unsigned = {"format": "open-worlds/key-list/v1",
                "issuer": roots[0]["signing"], "version": 1,
                "time": time, "keys": keys}
    return records.sign(unsigned,
                        secret_from_multikey(roots[0]["secretKeyMultibase"]),
                        time)


def _write_new(path: Path, text: str, mode: int) -> None:
    """Write `text` to a new file, readable as `mode` says; never over an
    existing one, and never through a link."""
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL
             | getattr(os, "O_NOFOLLOW", 0))
    fd = os.open(path, flags, mode)
    try:
        f = os.fdopen(fd, "w", encoding="utf-8")
    except BaseException:
        os.close(fd)
        os.unlink(path)
        raise
    try:
        with f:
            f.write(text)
    except BaseException:
        # Made here, so taken away here: a failed write leaves nothing.
        os.unlink(path)
        raise


def stage_private_halves(made: Sequence[Dict[str, Any]],
                         private: Path) -> Path:
    """Each holder's private halves, one new file each, readable by its
    owner only, in a new folder in `private` that only its owner can
    open; the caller moves it into place as `keys/` (`keep`)."""
    check_private_place(private)
    if os.path.lexists(private / "keys"):
        raise KeyMakingError(
            f"{private / 'keys'} is there already: the tool makes it new, "
            "and never writes over a key")
    names = [file_name(h["name"]) for h in made]
    if len(set(names)) != len(names):
        raise KeyMakingError("two holders would share a file")
    staging = Path(tempfile.mkdtemp(prefix=".keys-being-made-",
                                    dir=private.resolve()))
    try:
        for h, name in zip(made, names):
            _write_new(staging / name,
                       json.dumps(h, indent=1, ensure_ascii=False) + "\n",
                       0o600)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return staging


def keep(staging: Path, private: Path) -> Path:
    """Move the staged halves into place as `private`/keys/, which must
    not be there yet."""
    folder = private.resolve() / "keys"
    if os.path.lexists(folder):
        raise KeyMakingError(f"{folder} is there already")
    os.rename(staging, folder)
    return folder


def write_private_halves(made: Sequence[Dict[str, Any]],
                         private: Path) -> List[Path]:
    """Each holder's private halves, to a new `private`/keys/, one new file
    each, readable by its owner only."""
    folder = keep(stage_private_halves(made, private), private)
    return [folder / file_name(h["name"]) for h in made]


def check_kept(key_list: Dict[str, Any], private: Path) -> None:
    """KeyMakingError unless every holder in `key_list` has its private
    halves in `private`/keys/, and they are the halves of the keys the
    list names."""
    _check_kept_in(key_list, private / "keys")


def _check_kept_in(key_list: Dict[str, Any], folder: Path) -> None:
    records.check(key_list)
    for entry in key_list["keys"]:
        path = folder / file_name(entry["name"])
        try:
            kept = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise KeyMakingError(f"{entry['name']}: {e}") from None
        signing = secret_from_multikey(kept["secretKeyMultibase"])
        if did_key(_public(signing)) != entry["signing"]:
            raise KeyMakingError(f"{entry['name']}: another signing key")
        if "sealing" in entry:
            sealing = sealing_secret_from_multikey(
                kept["sealingSecretMultibase"])
            if (seal.public_from_secret(sealing)
                    != sealing_from_multikey(entry["sealing"])):
                raise KeyMakingError(f"{entry['name']}: another sealing key")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _make_all(private: Path, key_list_path: Path) -> Dict[str, Any]:
    """Make every key and the first key list, and put them in place:
    everything, or nothing left behind."""
    check_private_place(private)
    if os.path.lexists(key_list_path):
        raise KeyMakingError(f"{key_list_path} is there already")
    made = make_keys()
    key_list = first_key_list(made, _now())
    staging = stage_private_halves(made, private)
    staged_list = key_list_path.with_name(f".{key_list_path.name}.being-made")
    made_here: List[Path] = []
    try:
        _check_kept_in(key_list, staging)
        key_list_path.parent.mkdir(parents=True, exist_ok=True)
        _write_new(staged_list,
                   json.dumps(key_list, indent=1, ensure_ascii=False) + "\n",
                   0o644)
        made_here.append(staged_list)
        os.link(staged_list, key_list_path)
        made_here.append(key_list_path)
        staged_list.unlink()
        made_here.remove(staged_list)
        keep(staging, private)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        for path in made_here:
            try:
                path.unlink()
            except OSError:
                pass
        raise
    return key_list


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--private", type=Path, required=True,
                        help="a checkout of the private repository")
    parser.add_argument("--key-list", type=Path, required=True,
                        help="where the first key list is written")
    args = parser.parse_args(argv)
    try:
        key_list = _make_all(args.private, args.key_list)
    except (KeyMakingError, records.RecordError, OSError, ValueError) as e:
        print(f"not made: {e}", file=sys.stderr)
        return 1
    for entry in key_list["keys"]:
        sealing = f", sealing {entry['sealing']}" if "sealing" in entry else ""
        print(f"{entry['role']}: {entry['name']}: {entry['signing']}"
              f"{sealing}")
    print(f"key list, version 1: {records.record_hash(key_list)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
