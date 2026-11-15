"""Test vectors for a council's count (formats/council.py), in
vectors/formats/council-v1.json, which rust/formats reads too.

    python3 -m formats.council_vectors     rewrite the file from this code

It holds a council's proposal, the birth records of five trial persons
(three born in worlds the proposal trusts, one in a world it doesn't,
one with no birth), and cases of votes, each with the count it must
give: votes that count, a vote changed, two or three votes at one time,
the same vote given twice, a person born twice, a tie, no quorum, and
votes that don't count, each named for why. Every key is
made from a label, public to everyone and never for anything real.
tests/test_council.py checks that the file is still exactly what this
code writes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from . import council, proof, records
from .record_vectors import _did, _h, _secret

FILE = (Path(__file__).resolve().parent.parent
        / "vectors" / "formats" / "council-v1.json")
CREATED = "2026-11-15T02:00:00Z"
COUNCIL = "a trial council"
TRUSTED = ["a trial world", "another trial world"]
UNTRUSTED = "an untrusted trial world"
# Each person, and the world of their birth (None: no birth record).
PERSONS = [("a trial voter: one", TRUSTED[0]),
           ("a trial voter: two", TRUSTED[0]),
           ("a trial voter: three", TRUSTED[1]),
           ("a trial voter: four", UNTRUSTED),
           ("a trial voter: five", None)]
OPENS, CLOSES = "2026-11-15T03:00:00Z", "2026-11-15T05:00:00Z"
DURING, LATER = "2026-11-15T04:00:00Z", "2026-11-15T04:30:00Z"


def _proposal(**changes: Any) -> Dict[str, Any]:
    record = {
        "format": council.PROPOSAL,
        "council": _did(COUNCIL),
        "title": "The north bed",
        "text": "Plant the north bed with flowers this season.",
        "choices": ["yes", "no", "wait a season"],
        "trusts": [_did(w) for w in TRUSTED],
        "quorum": 3,
        "opens": OPENS,
        "closes": CLOSES,
    }
    record.update(changes)
    return records.sign(record, _secret(COUNCIL), CREATED)


PROPOSAL = _proposal()


def _birth(person: str, world: str) -> Dict[str, Any]:
    return records.sign({
        "format": council.BIRTH,
        "world": _did(world),
        "individual": _did(person),
        "name": person.split(": ")[1].upper(),
        "tick": 0,
        "time": CREATED,
        "mind": _h(f"a trial mind record for {person}"),
        "words": f"You came into being in {world}. A trial, for the "
                 "council's vectors.",
    }, _secret(world), CREATED)


def _births() -> List[Dict[str, Any]]:
    return [_birth(p, w) for p, w in PERSONS if w is not None]


def _vote(who: int, choice: int, time: str = DURING,
          proposal: Dict[str, Any] = PROPOSAL,
          signer: str = "") -> Dict[str, Any]:
    """The person at `who`'s place in PERSONS votes `choice`. With
    `signer`, a forgery: signed by the signer as their own, then given the
    person's key, so the proof is the signer's."""
    person = PERSONS[who][0]
    signed = records.sign({
        "format": council.VOTE,
        "proposal": records.record_hash(proposal),
        "person": _did(signer or person),
        "choice": choice,
        "time": time,
    }, _secret(signer or person), time)
    return dict(signed, person=_did(person)) if signer else signed


def _cases() -> List[Dict[str, Any]]:
    births = _births()
    tampered = dict(_vote(2, 0), choice=1)
    other = _proposal(title="The south bed")
    bad_birth = dict(births[2], world=births[0]["world"])
    cases = [
        ("three persons, each voting once",
         [_vote(0, 0), _vote(1, 0), _vote(2, 1)], births),
        ("a person changes their vote before the proposal closes",
         [_vote(0, 0), _vote(0, 1, LATER), _vote(1, 1), _vote(2, 0)], births),
        ("two votes by one person at one time count for neither",
         [_vote(0, 0), _vote(0, 1), _vote(1, 0), _vote(2, 1)], births),
        ("three votes by one person at one time count for none",
         [_vote(0, 0), _vote(0, 1), _vote(0, 2), _vote(1, 0), _vote(2, 1)],
         births),
        ("the same vote given twice counts once",
         [_vote(0, 0), _vote(0, 0), _vote(1, 0), _vote(2, 1)], births),
        ("a person born in two trusted worlds counts once",
         [_vote(0, 0), _vote(1, 0), _vote(2, 1)],
         births + [_birth(PERSONS[0][0], TRUSTED[1])]),
        ("a tie decides nothing",
         [_vote(0, 0), _vote(1, 1), _vote(2, 2)], births),
        ("too few persons decide nothing",
         [_vote(0, 0), _vote(1, 0)], births),
        ("votes that don't count, each named for why",
         [_vote(0, 0), _vote(1, 0), _vote(2, 1),
          _vote(3, 1),
          _vote(4, 1),
          _vote(0, 1, proposal=other),
          _vote(1, 3),
          _vote(1, 1, "2026-11-15T02:59:59Z"),
          _vote(1, 1, "2026-11-15T05:00:01Z"),
          _vote(2, 0, signer="a trial voter: four"),
          tampered], births),
        ("votes at the opening and the closing count",
         [_vote(0, 2, OPENS), _vote(1, 2, CLOSES), _vote(2, 2)], births),
        ("a birth record that doesn't hold counts no one",
         [_vote(0, 0), _vote(1, 0), _vote(2, 1)],
         births[:2] + [bad_birth]),
        ("a proposal that doesn't hold counts nothing",
         [_vote(0, 0)], births, dict(PROPOSAL, quorum=1)),
    ]
    out = []
    for case in cases:
        name, votes, given = case[0], case[1], case[2]
        proposal = case[3] if len(case) > 3 else PROPOSAL
        entry = {"name": name, "votes": votes, "births": given,
                 "tally": council.tally(proposal, votes, given)}
        if proposal is not PROPOSAL:
            entry["proposal"] = proposal
        out.append(entry)
    return out


def _proposals() -> List[Dict[str, Any]]:
    """Proposals as records: one that holds, and ones records-v1 must
    refuse, each named for why. Each refused one is signed as it is, by
    its council, so only what is named refuses it, but the last, which is
    signed by another key."""
    unsigned = {k: v for k, v in PROPOSAL.items() if k != "proof"}

    def made(by: str = COUNCIL, **changes: Any) -> Dict[str, Any]:
        return proof.sign(dict(unsigned, **changes), _secret(by), CREATED)

    cases = [
        ("a proposal that holds", PROPOSAL, True),
        ("a proposal that closes when it opens", made(closes=OPENS), False),
        ("a proposal with one choice", made(choices=["yes"]), False),
        ("a proposal with a choice twice", made(choices=["yes", "yes"]),
         False),
        ("a proposal trusting no world", made(trusts=[]), False),
        ("a proposal with a quorum of 0", made(quorum=0), False),
        ("a proposal signed by another key than its council's",
         made(by=TRUSTED[0]), False),
    ]
    return [{"name": n, "record": r, "holds": h} for n, r, h in cases]


def vectors() -> Dict[str, Any]:
    return {
        "description": (
            "A council's count (course step 3a, part four): a proposal, "
            "the birth records of trial persons, and cases of votes, each "
            "with the count formats/council.py gives. Every key here is "
            "made from a label, public to everyone and never for anything "
            "real. Written by `python3 -m formats.council_vectors`."),
        "parties": {name: _did(name) for name in
                    [COUNCIL, *TRUSTED, UNTRUSTED, *(p for p, _ in PERSONS)]},
        "proposal": PROPOSAL,
        "proposalHash": records.record_hash(PROPOSAL),
        "cases": _cases(),
        "proposals": _proposals(),
    }


def text() -> str:
    return json.dumps(vectors(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    FILE.write_text(text(), encoding="utf-8")


if __name__ == "__main__":
    main()
