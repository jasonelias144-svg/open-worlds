"""A council's count (course step 3a, part four; docs/research/PERSONS.md,
decision 8, and "Part four, second half, built").

Persons vote on a council's proposal, each vote signed by the person's
identity key, and anyone can count the votes again from the records:
the proposal, the votes, and the birth records that show who is a
person a council trusts.

- **A proposal** (`open-worlds/proposal/v1`), signed by its council,
  names the choices, when votes count (from `opens` to `closes`, both
  included), the fewest distinct persons who must be counted (`quorum`),
  and the worlds whose births it trusts (`trusts`).
- **A vote** (`open-worlds/vote/v1`), signed by the person, names the
  proposal by its hash and a choice by its place, from 0.
- **A vote counts** only if it holds, isn't a copy of a vote given
  before it, names this proposal, names a choice it has, is dated from
  `opens` to `closes`, and its person's birth was signed by a world the
  proposal trusts (decision 8: a world can't count persons by their
  presences, and any world can sign births).
- **Each person counts once.** Of a person's votes that count, the
  latest is theirs: a person can change their vote, by its date, up to
  the close. Two or more at the latest time are refused, all of them,
  since none can be said to be the later.
- **A vote is public, and the person's.** It is signed by their identity
  key, so it shows who voted, and how: there is no secret ballot here.
- **A vote's date is the voter's own claim.** Nothing here witnesses
  when a vote was made, so a vote signed after the close but dated
  before it counts, and replaces the person's earlier one. A count is
  final only once the votes are fixed by something that saw them before
  the close, such as entries in a log signed before `closes`; that
  witness isn't built (docs/research/PERSONS.md, "Its limits").
- **The outcome** is the choice with the most persons, if at least
  `quorum` persons were counted and no other choice has as many;
  otherwise there is none.

Every problem is written in fixed words, the same in Python and Rust
(rust/formats/src/council.rs), checked against
vectors/formats/council-v1.json.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import records

PROPOSAL = "open-worlds/proposal/v1"
VOTE = "open-worlds/vote/v1"
BIRTH = "open-worlds/birth/v1"


def _holds(record: Any, fmt: str) -> bool:
    if not isinstance(record, dict) or record.get("format") != fmt:
        return False
    try:
        records.check(record)
    except records.RecordError:
        return False
    return True


def tally(proposal: Any, votes: List[Any], births: List[Any]) -> Dict[str, Any]:
    """The count of `votes` on `proposal`, given the birth records
    `births`: how many persons chose each choice, how many persons were
    counted, the outcome (a choice's place, or None), which votes were
    counted (by their place in `votes`), and every problem found."""
    result: Dict[str, Any] = {"counts": [], "persons": 0, "outcome": None,
                              "counted": [], "problems": []}
    if not _holds(proposal, PROPOSAL):
        result["problems"].append("proposal: not a proposal that holds")
        return result
    problems = result["problems"]
    trusted = set(proposal["trusts"])
    born = set()
    for i, birth in enumerate(births):
        if not _holds(birth, BIRTH):
            problems.append(f"births[{i}]: not a birth record that holds")
        elif birth["world"] in trusted:
            born.add(birth["individual"])
    this = records.record_hash(proposal)
    choices = len(proposal["choices"])
    # Each person's votes that count so far: (time, place in votes).
    by_person: Dict[str, List[tuple]] = {}
    # The place of each vote that holds, by its record's hash: a copy
    # given again is refused, so it can't cancel its person's vote.
    first: Dict[str, int] = {}
    for i, vote in enumerate(votes):
        where = f"votes[{i}]"
        if not _holds(vote, VOTE):
            problems.append(f"{where}: not a vote that holds")
            continue
        digest = records.record_hash(vote)
        if digest in first:
            problems.append(f"{where}: the same vote as "
                            f"votes[{first[digest]}]")
            continue
        first[digest] = i
        if vote["proposal"] != this:
            problems.append(f"{where}: names another proposal")
        elif vote["choice"] >= choices:
            problems.append(f"{where}: a choice the proposal doesn't have")
        elif vote["time"] < proposal["opens"]:
            problems.append(f"{where}: dated before the proposal opens")
        elif vote["time"] > proposal["closes"]:
            problems.append(f"{where}: dated after the proposal closes")
        elif vote["person"] not in born:
            problems.append(f"{where}: by one whose birth no trusted world "
                            "signed")
        else:
            by_person.setdefault(vote["person"], []).append((vote["time"], i))
    counts = [0] * choices
    counted = []
    for person in sorted(by_person):
        latest = max(t for t, _ in by_person[person])
        last = [i for t, i in by_person[person] if t == latest]
        if len(last) > 1:
            problems.extend(f"votes[{i}]: one of several votes by one "
                            "person at one time" for i in last)
            continue
        counts[votes[last[0]]["choice"]] += 1
        counted.append(last[0])
    result["counts"] = counts
    result["persons"] = len(counted)
    result["counted"] = sorted(counted)
    result["outcome"] = _outcome(counts, len(counted), proposal["quorum"])
    return result


def _outcome(counts: List[int], persons: int, quorum: int) -> Optional[int]:
    if persons < quorum:
        return None
    most = max(counts)
    leaders = [i for i, n in enumerate(counts) if n == most]
    return leaders[0] if len(leaders) == 1 else None
