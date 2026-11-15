"""Test vectors for persons (formats/persons.py), in
vectors/formats/persons-v1.json, which rust/formats reads too.

    python3 -m formats.persons_vectors     rewrite the file from this code

It holds a trial presence seed and the presence keys it gives, with each
derivation's `info`; RFC 5869's first test case, so each language checks
its HKDF; links that hold and links that don't; and versions and
histories of a person's list. Every key here is made from a label, public
to everyone and never for anything real. tests/test_persons.py checks
that the file is still exactly what this code writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from multiverse import ed25519

from . import persons, proof, records
from .record_vectors import _did, _secret

FILE = (Path(__file__).resolve().parent.parent
        / "vectors" / "formats" / "persons-v1.json")
CREATED = "2026-11-15T01:00:00Z"
SEED_LABEL = ("open-worlds trial presence seed: a trial person; "
              "never for anything real")
SEED = hashlib.sha256(SEED_LABEL.encode()).digest()
PERSON = "a trial person"
UR = _did("the Ur-world")
TRIAL = _did("a trial world")
OTHER = "another trial person"

# RFC 5869, Appendix A.1, test case 1 (HKDF-SHA256).
RFC5869 = {
    "ikm": "0b" * 22,
    "salt": "000102030405060708090a0b0c",
    "info": "f0f1f2f3f4f5f6f7f8f9",
    "length": 42,
    "okm": ("3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
            "34007208d5b887185865"),
}


def _presences() -> List[Dict[str, Any]]:
    out = []
    for world, counter in ((UR, 0), (UR, 1), (TRIAL, 0), (TRIAL, 1),
                           (TRIAL, persons.COUNTERS - 1)):
        out.append({"world": world, "counter": counter,
                    "info": persons.presence_info(world, counter).hex(),
                    "key": persons.presence_key(SEED, world, counter)})
    return out


def _refused_derivations() -> List[Dict[str, Any]]:
    cases = [
        ("a counter below 0", SEED.hex(), UR, -1),
        ("a counter of four bytes and more", SEED.hex(), UR, persons.COUNTERS),
        ("a world that isn't a did:key", SEED.hex(), "the Ur-world", 0),
        ("a world whose did:key isn't an Ed25519 key", SEED.hex(),
         "did:key:z6LSbysY2xFMRpGMhb7tFTLMpeuPRaqaWM1yECx2AtzE3KCc", 0),
        ("a seed of 31 bytes", SEED[:31].hex(), UR, 0),
    ]
    out = []
    for name, seed, world, counter in cases:
        try:
            persons.presence_secret(bytes.fromhex(seed), world, counter)
        except ValueError as e:
            out.append({"name": name, "seed": seed, "world": world,
                        "counter": counter, "why": str(e)})
        else:
            raise AssertionError(f"not refused: {name}")
    return out


def _presence_secret(world: str, counter: int) -> bytes:
    return persons.presence_secret(SEED, world, counter)


def _link(world: str, counter: int, **changes: Any) -> Dict[str, Any]:
    """A link's two halves, the presence `counter` in `world`, each signed
    by the one who must sign it."""
    presence = persons.presence_key(SEED, world, counter)
    base = {"person": _did(PERSON), "presence": presence, "world": world,
            "time": CREATED}
    holds = {"format": persons.HOLDS, **base, **changes.get("holds", {})}
    held = {"format": persons.HELD_BY, **base, **changes.get("heldBy", {})}
    holds_by = changes.get("holdsSignedBy", _secret(PERSON))
    held_by = changes.get("heldBySignedBy", _presence_secret(world, counter))
    return {"holds": proof.sign(holds, holds_by, CREATED),
            "heldBy": proof.sign(held, held_by, CREATED)}


def _links() -> List[Dict[str, Any]]:
    other_presence = persons.presence_key(SEED, UR, 1)
    cases = [
        ("a person and their first presence in the Ur-world", _link(UR, 0)),
        ("a person and their second presence in a trial world",
         _link(TRIAL, 1)),
        ("held-by naming another world",
         _link(UR, 0, heldBy={"world": TRIAL})),
        ("holds naming another presence",
         _link(UR, 0, holds={"presence": other_presence})),
        ("held-by naming another person",
         _link(UR, 0, heldBy={"person": _did(OTHER)})),
        ("held-by signed by the person, not the presence",
         _link(UR, 0, heldBySignedBy=_secret(PERSON))),
        ("holds signed by the presence, not the person",
         _link(UR, 0, holdsSignedBy=_presence_secret(UR, 0))),
        ("holds with a field its format doesn't have",
         _link(UR, 0, holds={"note": "mine"})),
        ("held-by at a time that doesn't exist",
         _link(UR, 0, heldBy={"time": "2026-02-30T00:00:00Z"})),
        ("the person's own identity key as the presence",
         {"holds": proof.sign({"format": persons.HOLDS,
                               "person": _did(PERSON),
                               "presence": _did(PERSON), "world": UR,
                               "time": CREATED}, _secret(PERSON), CREATED),
          "heldBy": proof.sign({"format": persons.HELD_BY,
                                "presence": _did(PERSON),
                                "person": _did(PERSON), "world": UR,
                                "time": CREATED}, _secret(PERSON), CREATED)}),
    ]
    swapped = _link(UR, 0)
    cases.append(("the two halves given the other way round",
                  {"holds": swapped["heldBy"], "heldBy": swapped["holds"]}))
    out = []
    for name, link in cases:
        found = persons.link_problems(link["holds"], link["heldBy"])
        out.append({"name": name, **link, "linked": not found,
                    "problems": found})
    return out


def _list(version: int, entries: List[tuple], previous: Any = None,
          person: str = PERSON, time: str = CREATED) -> Dict[str, Any]:
    record = {"format": persons.PERSON_LIST, "person": _did(person),
              "version": version, "time": time,
              "presences": [{"world": w, "counter": c,
                             "key": persons.presence_key(SEED, w, c),
                             "name": n} for w, c, n in entries]}
    if previous is not None:
        record["previous"] = records.record_hash(previous)
    return records.sign(record, _secret(person), CREATED)


def _person_lists() -> Dict[str, Any]:
    v1 = _list(1, [(UR, 0, "Wren"), (TRIAL, 0, "Moss")])
    v2 = _list(2, [(UR, 0, "Wren"), (TRIAL, 0, "Moss"), (TRIAL, 1, "Fern")],
               previous=v1, time="2026-11-15T02:00:00Z")
    versions = {"version 1": v1, "version 2, adding a presence": v2}
    later = {
        "version 2 naming another version": _list(
            2, [(UR, 0, "Wren")], previous=_list(1, [(UR, 1, "Wren")])),
        "version 3 after version 1": _list(3, [(UR, 0, "Wren")], previous=v1),
        "version 2 by another person": _list(
            2, [(UR, 0, "Wren")], previous=v1, person=OTHER),
        "version 2 earlier than version 1": _list(
            2, [(UR, 0, "Wren")], previous=v1, time="2026-11-14T23:00:00Z"),
        "version 2 with one world and counter twice": _list(
            2, [(UR, 0, "Wren"), (UR, 0, "Wren again")], previous=v1),
        "version 2 dropping a presence": _list(
            2, [(UR, 0, "Wren")], previous=v1),
    }
    versions.update(later)
    histories = [
        ("versions 1 and 2", ["version 1", "version 2, adding a presence"]),
        ("version 1 alone", ["version 1"]),
        ("version 2 alone", ["version 2, adding a presence"]),
        ("a version naming another before it",
         ["version 1", "version 2 naming another version"]),
        ("a version skipped", ["version 1", "version 3 after version 1"]),
        ("another person's version",
         ["version 1", "version 2 by another person"]),
        ("a version earlier than the one before",
         ["version 1", "version 2 earlier than version 1"]),
        ("a version that repeats a presence",
         ["version 1", "version 2 with one world and counter twice"]),
        ("a version dropping a presence, which shows but holds",
         ["version 1", "version 2 dropping a presence"]),
        ("no versions", []),
    ]
    wrong_key = _list(1, [(UR, 0, "Wren")])
    wrong_key = records.sign(
        {**{k: v for k, v in wrong_key.items() if k != "proof"},
         "presences": [{"world": UR, "counter": 0, "name": "Wren",
                        "key": persons.presence_key(SEED, UR, 1)}]},
        _secret(PERSON), CREATED)
    return {
        "versions": [{"name": n, "record": r} for n, r in versions.items()],
        "histories": [{"name": n, "versions": vs,
                       "problems": persons.person_list_chain_problems(
                           [versions[v] for v in vs])}
                      for n, vs in histories],
        "seedChecks": [
            {"name": "version 2, each key from its world and counter",
             "version": "version 2, adding a presence",
             "problems": persons.seed_problems(v2, SEED)},
            {"name": "a list whose key is another counter's",
             "record": wrong_key,
             "problems": persons.seed_problems(wrong_key, SEED)},
        ],
    }


def vectors() -> Dict[str, Any]:
    return {
        "about": ("Persons (formats/persons.py, rust/formats/src/persons.rs): "
                  "presence keys from a trial seed, links both ways, and a "
                  "person's list. Written by `python3 -m "
                  "formats.persons_vectors`. Every key is made from a label, "
                  "public to everyone and never for anything real."),
        "created": CREATED,
        "hkdf": RFC5869,
        "seed": {"label": SEED_LABEL, "hex": SEED.hex()},
        "person": _did(PERSON),
        "presences": _presences(),
        "refusedDerivations": _refused_derivations(),
        "links": _links(),
        "personLists": _person_lists(),
    }


def text() -> str:
    """The file's exact text."""
    return json.dumps(vectors(), indent=1, ensure_ascii=False) + "\n"


def main() -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(text(), encoding="utf-8")
    print(f"wrote {FILE}")


if __name__ == "__main__":
    main()
