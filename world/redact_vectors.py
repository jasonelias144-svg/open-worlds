"""Test vectors for the act of redacting (world/redact.py), in
vectors/redaction.json, which rust/redact reads too.

    python3 -m world.redact_vectors     rewrite the file from this code

It holds, for the trial room of vectors/log-apart.json:

- parties (test keys, public to everyone, never for anything real): two
  persons a field is about, the office that redacts, and the office
  that decides;
- one act of redacting, and the log and its contents after it;
- the sealed copies it made, each with the record inside in the clear,
  so anyone can check that it is what its name says;
- the log and its contents after the deciding office keeps the field
  public from its copy, and after it decides that the field stays
  redacted;
- records that must be refused when held to the log, each signed, so
  that only its place in the log is at fault.

Sealing is random, so this code keeps each box already in the file if it
still opens, with the key stated, to exactly the record stated;
otherwise it seals a new one. Everything else is the same on every run:
the salts are the trial salts, and a signature over the same record at
the same time is the same. tests/test_redact.py checks that the file is
still exactly what this code writes.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from formats import records, seal, sealed
from formats import sealed_vectors as parties
from formats.canonical import canonical
from formats.multikey import (sealing_multikey, sealing_secret_multikey,
                              secret_multikey)

from . import apart, apart_vectors, redact

FILE = Path(__file__).resolve().parent.parent / "vectors" / "redaction.json"
CREATED = "2026-11-17T12:00:00Z"
ABOUT = ["ALICE", "BOB"]
REDACTS = "an apprentice Keeper"
DECIDES = "the Ur-world's Keeper"
PARTIES = ABOUT + [REDACTS, DECIDES]
GRANT = parties._stand_in("a grant to redact")
TICK = 5
FIELD = "text"
WHY = {"reason": "private information"}


def office() -> redact.Office:
    return redact.Office(apart_vectors.OFFICE, parties._secret(REDACTS),
                         GRANT)


def _to(name: str) -> Tuple[str, bytes]:
    return parties._did(name), parties._sealing_public(name)


def redacted() -> Tuple[apart.Log, redact.Redaction, str]:
    """The trial room with what ada said redacted, the redaction, and
    the hash of the entry."""
    room = apart_vectors._room()
    entry = room.entries[3]["hash"]
    made = redact.redact(room, TICK, entry, FIELD, office(),
                         apart_vectors.PRIVATE, CREATED,
                         about=[_to(name) for name in ABOUT],
                         decider=_to(DECIDES), apart_fields=WHY)
    return room, made, entry


def _opens_to(box_hex: str, name: str, inside: bytes) -> bool:
    try:
        return seal.open_box(bytes.fromhex(box_hex),
                             parties._sealing_secret(name),
                             redact.LABEL) == inside
    except (seal.SealError, ValueError):
        return False


def _signed(record: Dict[str, Any], by: str = REDACTS) -> Dict[str, Any]:
    return records.sign(record, parties._secret(by), CREATED)


def _refused(room: apart.Log, inside: Dict[str, Any]) -> List[dict]:
    """Records that hold as records and are refused when held to the
    log."""
    plain = {k: v for k, v in inside.items() if k != "proof"}
    hashes = [e["hash"] for e in room.entries]
    out = []

    def add(name: str, record: Any, reason: str) -> None:
        try:
            redact.held_to(record, room.entries)
        except redact.RedactError as e:
            assert e.reason == reason, (name, e.reason)
        else:
            raise AssertionError(f"{name}: held")
        out.append({"name": name, "record": record, "reason": reason})

    add("a copy that names another log",
        _signed(dict(plain, log=hashes[1])), redact.OTHER_LOG)
    add("a copy that names an entry the log does not have",
        _signed(dict(plain, entry=parties._stand_in("an entry"))),
        redact.NO_ENTRY)
    add("a copy that names a field the entry does not keep apart",
        _signed(dict(plain, field="name")), redact.NO_FIELD)
    add("a copy that names a field of another entry",
        _signed(dict(plain, entry=hashes[4])), redact.NOT_HELD)
    add("a copy with another value",
        _signed(dict(plain, value=plain["value"] + "!")), redact.NOT_HELD)
    add("a copy with another field's salt",
        _signed(dict(plain,
                     salt=room.contents[plain["entry"]]["time"][0])),
        redact.NOT_HELD)
    deep: Any = "v"
    for _ in range(apart.MAX_NESTING + 1):
        deep = [deep]
    add("a copy whose value nests deeper than a log allows",
        _signed(dict(plain, value=deep)), redact.NOT_HELD)
    add("a record of another kind",
        parties._records()["ALICE's journal entry"], redact.NOT_A_COPY)
    return out


def vectors(old: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    old_copies = {c["to"]: c for c in (old or {}).get("copies", [])}
    room, made, entry = redacted()
    after = {"mark": made.mark, "log": copy.deepcopy(room.entries),
             "contents": copy.deepcopy(room.contents)}

    copies = []
    for name, envelope in zip(ABOUT + [DECIDES],
                              made.copies + [made.office_copy]):
        inside = redact.open_copy(envelope, parties._sealing_secret(name),
                                  parties._did(name), room.entries)
        was = old_copies.get(name)
        if was and _opens_to(was["envelope"]["box"], name,
                             canonical(inside)):
            envelope = dict(envelope, box=was["envelope"]["box"])
        copies.append({"to": name, "envelope": envelope, "inside": inside,
                       "record": records.record_hash(inside),
                       "fingerprint": sealed.fingerprint(envelope)})
    office_copy = copies[-1]["envelope"]

    keeps = {"tick": 6, "office": apart_vectors.KEEPER,
             "ground": apart_vectors.APPEAL,
             "decision": apart_vectors.trial_decision(1),
             "apart": {"reason": "nothing private in it"}}
    redact.keep_public(room, keeps["tick"], made.mark, office_copy,
                       parties._sealing_secret(DECIDES),
                       parties._did(DECIDES), keeps["office"],
                       keeps["ground"], keeps["decision"],
                       apart_fields=keeps["apart"])
    kept = dict(keeps, log=copy.deepcopy(room.entries),
                contents=copy.deepcopy(room.contents))

    room, made, _ = redacted()
    stays = {"tick": 6, "office": apart_vectors.KEEPER,
             "ground": apart_vectors.APPEAL,
             "decision": apart_vectors.trial_decision(2),
             "apart": {"reason": "it is a private number"}}
    redact.stays_redacted(room, stays["tick"], made.mark, stays["office"],
                          stays["ground"], stays["decision"],
                          apart_fields=stays["apart"])
    stayed = dict(stays, log=copy.deepcopy(room.entries),
                  contents=copy.deepcopy(room.contents))

    room, _, _ = redacted()
    return {
        "about": (
            "The act of redacting (world/redact.py, rust/redact), on the "
            "trial room of vectors/log-apart.json: one field sealed, "
            "marked and taken out, the copies made, and what the "
            "deciding office then writes. Written by python3 -m "
            "world.redact_vectors; test keys and trial salts only, "
            "never for anything real."),
        "format": redact.FORMAT,
        "label": redact.LABEL,
        "reasons": list(redact.REASONS),
        "parties": {
            name: {"id": parties._did(name),
                   "secretKeyMultibase":
                       secret_multikey(parties._secret(name)),
                   "sealingSecretMultibase": sealing_secret_multikey(
                       parties._sealing_secret(name)),
                   "sealingKeyMultibase": sealing_multikey(
                       parties._sealing_public(name))}
            for name in PARTIES},
        "created": CREATED,
        "act": {"tick": TICK, "entry": entry, "field": FIELD,
                "office": apart_vectors.OFFICE, "grant": GRANT,
                "ground": apart_vectors.PRIVATE, "apart": WHY,
                "by": REDACTS, "about": ABOUT, "decider": DECIDES},
        "redacted": after,
        "copies": copies,
        "kept": kept,
        "stays": stayed,
        "refused": _refused(room, copies[0]["inside"]),
    }


def text(old: Optional[Dict[str, Any]] = None) -> str:
    return json.dumps(vectors(old), indent=1, ensure_ascii=False) + "\n"


def current() -> Optional[Dict[str, Any]]:
    """The file as it is now, if there is one."""
    if not FILE.exists():
        return None
    return json.loads(FILE.read_text(encoding="utf-8"))


def main() -> None:
    FILE.write_text(text(current()), encoding="utf-8")
    print(f"wrote {FILE}")


if __name__ == "__main__":
    main()
