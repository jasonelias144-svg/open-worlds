"""Make the project's keys (course step 3; docs/research/KEYS.md).

    python3 -m formats.make_keys --private ../open-worlds-private \\
        --key-list keys/key-list.json

Makes one key for each role in PLAN, from the operating system's
randomness (through `cryptography`), and writes:

- **the private halves** into `--private`, one file per holder, readable
  by its owner only: `keys/<holder>.json`, with the role, the name, and
  the secrets as Multikey (`secretKeyMultibase`, and for a holder things
  are sealed to, `sealingSecretMultibase`). That directory must be a
  checkout of the private repository: the tool refuses any place inside
  this repository's working tree, and never writes over a key.
- **the first key list** to `--key-list`, signed by the new root: every
  role's public keys (formats/records.py, `open-worlds/key-list/v1`).

It prints the public keys, never a secret. Committing and pushing the
private halves is done in the private repository, at once; the key list
comes here through a reviewed pull request.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
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


def _root_commits(path: Path) -> Set[str]:
    """The first commits of the history checked out at `path`, which name
    the repository it is a checkout of; none outside Git, or before a
    first commit."""
    try:
        out = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"],
                             cwd=path, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return set()
    return set(out.stdout.decode().split())


def check_private_place(private: Path,
                        repository: Path = REPOSITORY) -> None:
    """KeyMakingError unless `private` is an existing directory outside
    this repository's working tree, and not in any other checkout of this
    repository: a history that shares its first commit is the same
    repository, wherever it is."""
    private = private.resolve()
    repository = repository.resolve()
    if not private.is_dir():
        raise KeyMakingError(f"{private} is not a directory")
    if private == repository or repository in private.parents:
        raise KeyMakingError(
            "the private halves may not be written inside this "
            "repository's working tree")
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
    existing one."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)


def write_private_halves(made: Sequence[Dict[str, Any]],
                         private: Path) -> List[Path]:
    """Each holder's private halves, to `private`/keys/, one new file
    each, readable by its owner only. Nothing is written if any file
    exists already."""
    check_private_place(private)
    folder = private / "keys"
    folder.mkdir(exist_ok=True)
    paths = [folder / file_name(h["name"]) for h in made]
    if len(set(paths)) != len(paths):
        raise KeyMakingError("two holders would share a file")
    taken = [p for p in paths if p.exists()]
    if taken:
        raise KeyMakingError(f"a key is kept there already: {taken[0]}")
    for h, path in zip(made, paths):
        _write_new(path, json.dumps(h, indent=1, ensure_ascii=False) + "\n",
                   0o600)
    return paths


def check_kept(key_list: Dict[str, Any], private: Path) -> None:
    """KeyMakingError unless every holder in `key_list` has its private
    halves in `private`/keys/, and they are the halves of the keys the
    list names."""
    records.check(key_list)
    for entry in key_list["keys"]:
        path = private / "keys" / file_name(entry["name"])
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--private", type=Path, required=True,
                        help="a checkout of the private repository")
    parser.add_argument("--key-list", type=Path, required=True,
                        help="where the first key list is written")
    args = parser.parse_args(argv)
    try:
        check_private_place(args.private)
        if args.key_list.exists():
            raise KeyMakingError(f"{args.key_list} exists already")
        made = make_keys()
        key_list = first_key_list(made, _now())
        write_private_halves(made, args.private)
        args.key_list.parent.mkdir(parents=True, exist_ok=True)
        _write_new(args.key_list,
                   json.dumps(key_list, indent=1, ensure_ascii=False) + "\n",
                   0o644)
        check_kept(key_list, args.private.resolve())
    except (KeyMakingError, records.RecordError) as e:
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
