"""Test vectors for sealed records (formats/sealed.py), in
vectors/formats/sealed-records-v1.json, which rust/formats reads too.

    python3 -m formats.sealed_vectors     rewrite the file from this code

It holds:

- parties (test keys, public to everyone, never for anything real), each
  with a signing key (as in records-v1.json) and a sealing key;
- world-keys and journal entries that hold, and some that must be refused;
- envelopes that open, each with the hash of the record inside;
- envelopes that must be refused when opened, each saying what it was
  sealed to, under which label, and what is inside, so anyone can check
  that it is what its name says;
- envelopes refused for their shape alone.

Sealing is random, so this code keeps each box already in the file if it
still opens, with the key and label stated, to exactly what is stated;
otherwise it seals a new one. tests/test_formats_sealed.py checks that
the file is still exactly what this code writes.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from multiverse import ed25519

from . import proof, records, seal, sealed
from .canonical import canonical
from .multikey import (did_key, sealing_multikey, sealing_secret_multikey,
                       secret_multikey)

FILE = (Path(__file__).resolve().parent.parent
        / "vectors" / "formats" / "sealed-records-v1.json")
CREATED = "2026-11-14T04:00:00Z"
PARTIES = ["ALICE", "BOB", "the Ur-world"]
WORLD_KEY = "open-worlds/world-key/v1"
JOURNAL = "open-worlds/journal/v1"


def _secret(name: str) -> bytes:
    # The same signing keys as records-v1.json's parties.
    return hashlib.sha256(
        f"open-worlds test party: {name}; never for anything real".encode()
    ).digest()


def _sealing_secret(name: str) -> bytes:
    return hashlib.sha256(
        f"open-worlds sealing test key: {name}; never for anything real"
        .encode()).digest()


def _sealing_public(name: str) -> bytes:
    return seal.public_from_secret(_sealing_secret(name))


def _did(name: str) -> str:
    return did_key(ed25519.public_key(_secret(name)))


def _signed(record: Dict[str, Any], by: str) -> Dict[str, Any]:
    # Signed without records.check, so records that must be refused can
    # be made too.
    return proof.sign(record, _secret(by), CREATED)


PATH = hashlib.sha256(b"a path in the Ur-world, as placed").hexdigest()


def _records() -> Dict[str, Dict[str, Any]]:
    ur = _did("the Ur-world")
    return {
        "ALICE's world-key": _signed({
            "format": "open-worlds/world-key/v1",
            "issuer": ur, "holder": _did("ALICE"),
            "path": PATH, "tick": 1200,
        }, "the Ur-world"),
        "ALICE's journal entry": _signed({
            "format": "open-worlds/journal-entry/v1",
            "author": _did("ALICE"), "world": ur, "tick": 1201,
            "text": "The last symbol was by the old well. BOB saw it first.",
            "remembers": [{"world": ur, "tick": 1190},
                          {"world": ur, "tick": 1200}],
        }, "ALICE"),
        "BOB's journal entry": _signed({
            "format": "open-worlds/journal-entry/v1",
            "author": _did("BOB"), "world": ur, "tick": 1202,
            "text": "Quiet today.",
        }, "BOB"),
    }


def _refused_records(good: Dict[str, Dict[str, Any]]
                     ) -> List[Dict[str, Any]]:
    key = {k: v for k, v in good["ALICE's world-key"].items()
           if k != "proof"}
    entry = {k: v for k, v in good["ALICE's journal entry"].items()
             if k != "proof"}
    out = []

    def add(name: str, record: Dict[str, Any], why: str) -> None:
        out.append({"name": name, "record": record, "why": why})

    add("a world-key signed by its holder", _signed(dict(key), "ALICE"),
        "a world-key is signed by its issuer")
    add("a world-key with a field the schema doesn't know",
        _signed(dict(key, copies=2), "the Ur-world"),
        "no other fields")
    add("a world-key naming no path",
        _signed({k: v for k, v in key.items() if k != "path"},
                "the Ur-world"),
        "path is required")
    add("a journal entry signed by someone else",
        _signed(dict(entry), "BOB"),
        "a journal entry is signed by its author")
    add("a journal entry that remembers nothing, said as an empty list",
        _signed(dict(entry, remembers=[]), "ALICE"),
        "remembers, if there, names at least one event")
    add("a journal entry of only spaces",
        _signed(dict(entry, text="   "), "ALICE"),
        "text isn't only spaces")
    add("a journal entry naming no world",
        _signed({k: v for k, v in entry.items() if k != "world"}, "ALICE"),
        "world is required")
    return out


def _opens_to(box_hex: str, sealed_for: str, label: str,
              inside: bytes) -> bool:
    try:
        return seal.open_box(bytes.fromhex(box_hex),
                             _sealing_secret(sealed_for), label) == inside
    except (ValueError, seal.SealError):
        return False


def vectors(old: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    old = old or {}
    old_opens = {e["name"]: e for e in old.get("opens", [])}
    old_refused = {e["name"]: e for e in old.get("refused", [])}
    good = _records()
    for name, record in good.items():
        records.check(record)

    def box(old_entry: Optional[Dict[str, Any]], sealed_for: str,
            label: str, inside: bytes) -> str:
        if old_entry and _opens_to(old_entry["envelope"]["box"],
                                   sealed_for, label, inside):
            return old_entry["envelope"]["box"]
        return seal.seal(inside, _sealing_public(sealed_for), label).hex()

    opens = []
    for name, owner, label in [
            ("ALICE's world-key, sealed to ALICE", "ALICE", WORLD_KEY),
            ("ALICE's journal entry, sealed to ALICE", "ALICE", JOURNAL),
            ("BOB's journal entry, sealed to BOB", "BOB", JOURNAL)]:
        record = good[name.split(", sealed")[0]]
        envelope = {"format": sealed.ENVELOPE, "label": label,
                    "to": _did(owner),
                    "box": box(old_opens.get(name), owner, label,
                               canonical(record))}
        opened = sealed.open_record(envelope, _sealing_secret(owner),
                                    _did(owner), label)
        opens.append({"name": name, "opener": owner, "label": label,
                      "envelope": envelope,
                      "record": records.record_hash(opened),
                      "fingerprint": sealed.fingerprint(envelope)})

    world_key = good["ALICE's world-key"]
    unsigned_key = {k: v for k, v in world_key.items() if k != "proof"}
    log_head = _signed({"format": "open-worlds/log-head/v1",
                        "world": _did("the Ur-world"), "length": 0,
                        "last": "0" * 64, "tick": 0}, "the Ur-world")
    changed = copy.deepcopy(world_key)
    changed["tick"] = 1199

    refused: List[Dict[str, Any]] = []

    def refuse(name: str, *, inside: bytes, sealed_for: str,
               sealed_under: str, to: str, label: str, opener: str,
               opener_label: str, why: str) -> None:
        envelope = {"format": sealed.ENVELOPE, "label": label,
                    "to": _did(to),
                    "box": box(old_refused.get(name), sealed_for,
                               sealed_under, inside)}
        refused.append({
            "name": name, "envelope": envelope, "opener": opener,
            "label": opener_label, "why": why,
            "sealedFor": sealed_for, "sealedUnder": sealed_under,
            "inside": inside.hex()})

    refuse("ALICE's world-key, sealed again to BOB",
          inside=canonical(world_key), sealed_for="BOB",
          sealed_under=WORLD_KEY, to="BOB", label=WORLD_KEY, opener="BOB",
          opener_label=WORLD_KEY,
          why="the box opens, but the world-key names ALICE")
    refuse("BOB's journal entry, sealed to ALICE",
          inside=canonical(good["BOB's journal entry"]), sealed_for="ALICE",
          sealed_under=JOURNAL, to="ALICE", label=JOURNAL, opener="ALICE",
          opener_label=JOURNAL,
          why="the box opens, but the entry is BOB's")
    refuse("a world-key under the journal's label",
          inside=canonical(world_key), sealed_for="ALICE",
          sealed_under=JOURNAL, to="ALICE", label=JOURNAL, opener="ALICE",
          opener_label=JOURNAL,
          why="the box opens, but a world-key isn't sealed as a journal")
    refuse("an envelope whose label lies",
          inside=canonical(world_key), sealed_for="ALICE",
          sealed_under=JOURNAL, to="ALICE", label=WORLD_KEY, opener="ALICE",
          opener_label=WORLD_KEY,
          why="sealed under the journal's label, so it doesn't open as a "
              "world-key")
    refuse("an envelope for another purpose than the opener's",
          inside=canonical(world_key), sealed_for="ALICE",
          sealed_under=WORLD_KEY, to="ALICE", label=WORLD_KEY,
          opener="ALICE", opener_label=JOURNAL,
          why="the opener asked for a journal entry")
    refuse("an envelope addressed to someone else",
          inside=canonical(world_key), sealed_for="ALICE",
          sealed_under=WORLD_KEY, to="BOB", label=WORLD_KEY, opener="ALICE",
          opener_label=WORLD_KEY, why="addressed to BOB")
    refuse("a box sealed to ALICE, opened by BOB",
          inside=canonical(world_key), sealed_for="ALICE",
          sealed_under=WORLD_KEY, to="BOB", label=WORLD_KEY, opener="BOB",
          opener_label=WORLD_KEY, why="BOB's key doesn't open it")
    refuse("inside, a world-key not in its one RFC 8785 form",
          inside=json.dumps(world_key, indent=1).encode(),
          sealed_for="ALICE", sealed_under=WORLD_KEY, to="ALICE",
          label=WORLD_KEY, opener="ALICE", opener_label=WORLD_KEY,
          why="a record is sealed in its RFC 8785 form only")
    refuse("inside, a world-key changed after it was signed",
          inside=canonical(changed), sealed_for="ALICE",
          sealed_under=WORLD_KEY, to="ALICE", label=WORLD_KEY,
          opener="ALICE", opener_label=WORLD_KEY,
          why="its proof no longer verifies")
    refuse("inside, a world-key signed by its holder",
          inside=canonical(_signed(dict(unsigned_key), "ALICE")),
          sealed_for="ALICE", sealed_under=WORLD_KEY, to="ALICE",
          label=WORLD_KEY, opener="ALICE", opener_label=WORLD_KEY,
          why="a world-key is signed by its issuer")
    refuse("inside, a record of a kind that isn't sealed",
          inside=canonical(log_head), sealed_for="ALICE",
          sealed_under=WORLD_KEY, to="ALICE", label=WORLD_KEY,
          opener="ALICE", opener_label=WORLD_KEY,
          why="a log head holds, but isn't a world-key")
    refuse("inside, not a record",
          inside=b"not a record", sealed_for="ALICE",
          sealed_under=WORLD_KEY, to="ALICE", label=WORLD_KEY,
          opener="ALICE", opener_label=WORLD_KEY, why="not JSON")
    refuse("inside, a record without its proof",
          inside=canonical(unsigned_key), sealed_for="ALICE",
          sealed_under=WORLD_KEY, to="ALICE", label=WORLD_KEY,
          opener="ALICE", opener_label=WORLD_KEY,
          why="only a signed record is sealed")

    base = opens[0]["envelope"]
    shapes = [
        ("a box of odd length", dict(base, box=base["box"][:-1]),
         "hex in whole bytes"),
        ("a box in capitals", dict(base, box=base["box"].upper()),
         "lowercase hex"),
        ("a box too short to hold anything", dict(base, box="00" * 47),
         "at least 48 bytes"),
        ("a label not in use", dict(base, label="open-worlds/world-key/v2"),
         "a label in use"),
        ("a field the schema doesn't know", dict(base, sender="ALICE"),
         "no other fields"),
        ("addressed to no did:key", dict(base, to="ALICE"),
         "to is a did:key"),
        ("no box", {k: v for k, v in base.items() if k != "box"},
         "box is required"),
    ]
    return {
        "about": (
            "Sealed records (formats/sealed.py, rust/formats): world-keys "
            "and journal entries, signed, sealed to the one they name, in "
            "envelopes. Written by python3 -m formats.sealed_vectors; test "
            "keys only, never for anything real."),
        "parties": {
            name: {"id": _did(name),
                   "secretKeyMultibase": secret_multikey(_secret(name)),
                   "sealingSecretMultibase":
                       sealing_secret_multikey(_sealing_secret(name)),
                   "sealingKeyMultibase":
                       sealing_multikey(_sealing_public(name))}
            for name in PARTIES},
        "records": [{"name": name, "record": record,
                     "hash": records.record_hash(record)}
                    for name, record in good.items()],
        "refusedRecords": _refused_records(good),
        "opens": opens,
        "refused": refused,
        "refusedEnvelopes": [{"name": n, "envelope": e, "why": w}
                             for n, e, w in shapes],
    }


def text(old: Optional[Dict[str, Any]] = None) -> str:
    return json.dumps(vectors(old), indent=1, ensure_ascii=False) + "\n"


def current() -> Optional[Dict[str, Any]]:
    """The file as it is now, if there is one."""
    if not FILE.exists():
        return None
    return json.loads(FILE.read_text(encoding="utf-8"))


def main() -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(text(current()), encoding="utf-8")
    print(f"wrote {FILE}")


if __name__ == "__main__":
    main()
