"""Persons: one individual across worlds (docs/research/PERSONS.md), course
step 3a, part two: the formats.

- **Presence keys.** A presence's key is made from the person's presence
  seed (32 random bytes) with HKDF-SHA256 (RFC 5869): the seed is the
  input key material, there is no salt, and `info` is the label
  `open-worlds/presence/v1`, a zero byte, the world's did:key in ASCII, a
  zero byte, and the counter as four bytes, big-endian. Its 32 bytes out
  are the presence's Ed25519 secret key (RFC 8032 takes any 32 bytes).
  The same seed, world and counter always give the same key; without the
  seed, no one can relate two presences' keys.
- **A link holds only both ways.** `open-worlds/holds/v1`, signed by the
  person, and `open-worlds/held-by/v1`, signed by the presence, each name
  the person, the presence and the presence's world; a link holds only
  when both hold and name the same three (`link_problems`).
- **The person's list** (`open-worlds/person-list/v1`): their presences,
  each with its world, counter, key and name, in versions that each name
  the one before by hash, all signed by the person's identity key
  (`person_list_problems`, `person_list_chain_problems`). It is never
  shown whole.

Rust (`rust/formats/src/persons.rs`) does the same, and both are checked
against `vectors/formats/persons-v1.json` (formats/persons_vectors.py).
"""
from __future__ import annotations

from typing import Any, Dict, List

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from multiverse import ed25519

from . import records
from .multikey import KeyFormatError, did_key, public_from_multikey

LABEL = b"open-worlds/presence/v1"
#: Counters are four bytes: from 0 to this, less one.
COUNTERS = 2 ** 32
HOLDS = "open-worlds/holds/v1"
HELD_BY = "open-worlds/held-by/v1"
PERSON_LIST = "open-worlds/person-list/v1"


def presence_info(world: str, counter: int) -> bytes:
    """HKDF's `info` for the presence `counter` in `world` (a did:key):
    the label, a zero byte, the world's did:key in ASCII, a zero byte,
    and the counter as four bytes, big-endian. ValueError if the world
    isn't an Ed25519 did:key or the counter is out of range."""
    if not isinstance(world, str) or not world.startswith("did:key:"):
        raise ValueError("the world isn't a did:key")
    try:
        public_from_multikey(world[len("did:key:"):])
    except KeyFormatError as e:
        raise ValueError(f"the world isn't an Ed25519 did:key: {e}") from None
    if (not isinstance(counter, int) or isinstance(counter, bool)
            or not 0 <= counter < COUNTERS):
        raise ValueError(f"the counter must be from 0 to {COUNTERS - 1}")
    return (LABEL + b"\x00" + world.encode("ascii") + b"\x00"
            + counter.to_bytes(4, "big"))


def presence_secret(seed: bytes, world: str, counter: int) -> bytes:
    """The Ed25519 secret key of the presence `counter` in `world`, made
    from the person's presence `seed` (32 bytes)."""
    if not isinstance(seed, bytes) or len(seed) != 32:
        raise ValueError("a presence seed is 32 bytes")
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=presence_info(world, counter)).derive(seed)


def presence_key(seed: bytes, world: str, counter: int) -> str:
    """The did:key of the presence `counter` in `world`."""
    return did_key(ed25519.public_key(presence_secret(seed, world, counter)))


def link_problems(holds: Any, held_by: Any) -> List[str]:
    """Why the two halves don't make a link, or []: each must hold, as its
    kind, signed by the one it must be (the person, the presence), and
    both must name the same person, presence and world; a person's
    identity key is never one of their presences."""
    found = []
    for name, record, fmt in (("holds", holds, HOLDS),
                              ("held-by", held_by, HELD_BY)):
        if not isinstance(record, dict) or record.get("format") != fmt:
            found.append(f"{name}: not a record of the format {fmt}")
            continue
        try:
            records.check(record)
        except records.RecordError as e:
            found.append(f"{name}: {e}")
    if found:
        return found
    for field in ("person", "presence", "world"):
        if holds[field] != held_by[field]:
            found.append(f"the two halves name another {field}")
    if holds["person"] == holds["presence"]:
        found.append("the presence is the person's own identity key")
    return found


def _person_list(record: Any) -> Dict[str, Any]:
    if not isinstance(record, dict) or record.get("format") != PERSON_LIST:
        raise records.RecordError(f"not a record of the format {PERSON_LIST}")
    return records.check(record)


def entries_problems(person_list: Dict[str, Any]) -> List[str]:
    """Where a person's list repeats itself, or lists the person, or []:
    no two presences with the same world and counter, or the same key,
    and no presence whose key is the person's own identity key, which
    never enters a world (docs/research/PERSONS.md, decision 1)."""
    found, places, keys = [], set(), set()
    for i, entry in enumerate(person_list["presences"]):
        if entry["key"] == person_list["person"]:
            found.append(f"$.presences.{i}: the person's own identity key")
        place = (entry["world"], entry["counter"])
        if place in places:
            found.append(f"$.presences.{i}: a second presence with this "
                         "world and counter")
        if entry["key"] in keys:
            found.append(f"$.presences.{i}: a second presence with this key")
        places.add(place)
        keys.add(entry["key"])
    return found


def person_list_problems(new: Any, previous: Any) -> List[str]:
    """Where a version of a person's list fails to follow the one before,
    or []: both must hold; it must name that version by hash, be the next
    number, be the same person's, and be no earlier; and it must not
    repeat itself. A presence dropped or added between the two is shown
    by comparing them, not refused."""
    found = []
    for name, record in (("new", new), ("previous", previous)):
        try:
            _person_list(record)
        except records.RecordError as e:
            found.append(f"{name}: {e}")
    if found:
        return found
    if new.get("previous") != records.record_hash(previous):
        found.append("$.previous: names another version")
    if new["version"] != previous["version"] + 1:
        found.append("$.version: not the next version")
    if new["person"] != previous["person"]:
        found.append("$.person: another person's list")
    if new["time"] < previous["time"]:
        found.append("$.time: earlier than the version before")
    return found + entries_problems(new)


def person_list_chain_problems(versions: List[Any]) -> List[str]:
    """Where a person's list's history fails, or []: from version 1, each
    version following the one before. Each problem names the version's
    place in `versions`."""
    if not versions:
        return ["[]: no versions"]
    found = []
    for i, record in enumerate(versions):
        try:
            _person_list(record)
        except records.RecordError as e:
            found.append(f"[{i}] {e}")
    if found:
        return found
    if versions[0]["version"] != 1:
        found.append("[0] $.version: the history doesn't start at 1")
    found += [f"[0] {p}" for p in entries_problems(versions[0])]
    for i in range(1, len(versions)):
        found += [f"[{i}] {p}" for p in
                  person_list_problems(versions[i], versions[i - 1])]
    return found


def seed_problems(person_list: Dict[str, Any], seed: bytes) -> List[str]:
    """Which presences in a person's list weren't made from `seed` with
    their world and counter, or []: what the person's own client checks.
    The list must hold (`person_list_chain_problems`); given one that
    doesn't, a counter out of range raises ValueError."""
    return [f"$.presences.{i}: its key isn't the one its world and counter "
            "give" for i, e in enumerate(person_list["presences"])
            if presence_key(seed, e["world"], e["counter"]) != e["key"]]
