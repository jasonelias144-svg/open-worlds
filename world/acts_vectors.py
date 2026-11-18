"""Test vectors for the check of who may act on a log (world/acts.py),
in vectors/acts.json, which rust/acts reads too.

    python3 -m world.acts_vectors     rewrite the file from this code

It holds, for a trial room in the form of world/apart.py:

- parties (their did:keys only; the keys are test keys, public to
  everyone, never for anything real): the room, its Keeper, its
  moderator, an apprentice moderator whose grant narrows the
  moderator's, two persons who write, and one who does neither;
- the room's rules and its grants;
- rooms that hold, each with the state of every act;
- rooms that are refused, each for one named reason, at one entry:
  every record in them is signed, so that only the thing named is at
  fault;
- records held to their office's grant on their own, as a redacted
  field's copy is when it is opened.

Everything is the same on every run: the salts are the trial salts of
vectors/log-apart.json, and a signature over the same record at the
same time is the same. tests/test_acts.py checks that the file is still
exactly what this code writes.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from formats import records
from formats import sealed_vectors as parties

from . import acts, apart, apart_vectors

FILE = Path(__file__).resolve().parent.parent / "vectors" / "acts.json"
CREATED = "2026-11-18T12:00:00Z"
FROM = "2026-11-18T00:00:00Z"

ROOM = "a trial room"
KEEPER = "a trial room's Keeper"
MODERATOR = "a trial room's moderator"
APPRENTICE = "an apprentice moderator"
ALICE, BOB = "ALICE", "BOB"
OUTSIDER = "a trial mind"
PARTIES = [ROOM, KEEPER, MODERATOR, APPRENTICE, ALICE, BOB, OUTSIDER]


def _did(name: str) -> str:
    return parties._did(name)


TABLE = {
    "entered": ["key", "name"],
    "entry_put_back": ["record"],
    "entry_removed": ["record"],
    "entry_restored": ["record"],
    "entry_taken_back": ["record"],
    "field_kept_public": ["reason", "record"],
    "field_redacted": ["reason"],
    "field_stays_redacted": ["reason", "record"],
    "said": ["key", "text", "time"],
}
FIRST = {"rules_version": "vectors-acts-1"}
RULES = {
    "room": _did(ROOM),
    "authors": {"entered": "key", "said": "key"},
    "on": {apart.MARK: ["entered", "said"], apart.REMOVED: ["said"],
           apart.TAKEN_BACK: ["said"]},
}

LAW = {"kind": "law", "ref": "trial room law, part 3"}
RULE2 = {"kind": "rule", "ref": "trial room rule 2"}
PRIVATE = {"kind": "rule", "ref": "trial room law, private information"}
APPEAL = {"kind": "rule", "ref": "trial appeal rule"}
APPEALS_TO = "to the room's Keeper, and beyond them to ADMIN"
WHY = {
    "remove-comment": "The comment breaks part 3 of the room's law.",
    "restore-comment": "On appeal: the comment does not break the law.",
    "keep-field-public": "What was marked is not private information.",
    "keep-field-redacted": "What was marked is private information.",
}

# What the trial room writes after its first entry: tick, kind, and the
# fields kept apart. The key that wrote each entry is a real did:key.
WRITTEN: List[Tuple[int, str, dict]] = [
    (0, "entered", {"key": _did(ALICE), "name": "ada"}),
    (0, "entered", {"key": _did(BOB), "name": "bo"}),
    (1, "said", {"key": _did(ALICE), "text": "hello, room",
                 "time": 1794787200}),
    (2, "said", {"key": _did(BOB), "text": "a word the room's law forbids",
                 "time": 1794787260}),
    (3, "said", {"key": _did(ALICE), "text": "my door is 1 Trial Street",
                 "time": 1794787320}),
    (4, "said", {"key": _did(BOB), "text": "bo's telephone is 555 0100",
                 "time": 1794787380}),
]


def _signed(record: Dict[str, Any], by: str,
            created: str = CREATED) -> Dict[str, Any]:
    return records.sign(record, parties._secret(by), created)


def _grant(issuer: str, holder: str, allows: Sequence[str], *,
           start: str = FROM, until: Optional[str] = None,
           narrows: Optional[Dict[str, Any]] = None,
           within: Optional[str] = None) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "format": acts.GRANT, "issuer": _did(issuer),
        "holder": _did(holder), "allows": list(allows),
        "within": _did(ROOM) if within is None else within,
        "validFrom": start}
    if until is not None:
        record["validUntil"] = until
    if narrows is not None:
        record["narrows"] = records.record_hash(narrows)
    return _signed(record, issuer)


def grants() -> Dict[str, Dict[str, Any]]:
    """The room's grants, by a name for each: the Keeper's and the
    moderator's from the room's key, and an apprentice's, which narrows
    the moderator's."""
    keeper = _grant(ROOM, KEEPER, ["keep-field-public",
                                   "keep-field-redacted", "redact-field",
                                   "restore-comment"])
    moderator = _grant(ROOM, MODERATOR, ["redact-field", "remove-comment"],
                       until="2027-11-18T00:00:00Z")
    apprentice = _grant(MODERATOR, APPRENTICE, ["remove-comment"],
                        start="2026-11-18T06:00:00Z",
                        until="2026-12-18T00:00:00Z", narrows=moderator)
    return {"keeper": keeper, "moderator": moderator,
            "apprentice": apprentice}


def _decision(by: str, grant: Dict[str, Any], kind: str, on: str, tick: int,
              affects: Sequence[str], grounds: Sequence[dict] = (LAW,),
              supersedes: Optional[str] = None, created: str = CREATED,
              **more: Any) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "format": acts.DECISION,
        "office": {"key": _did(by), "grant": records.record_hash(grant)},
        "act": {"kind": kind, "records": [on]},
        "affects": [_did(name) for name in affects],
        "reasons": WHY[kind],
        "grounds": [dict(g) for g in grounds],
        "inputs": [],
        "appeal": APPEALS_TO,
        "tick": tick,
    }
    if supersedes is not None:
        record["supersedes"] = supersedes
    record.update(more)
    return _signed(record, by, created)


def _taking(by: str, entry: str,
            after: Optional[str] = None) -> Dict[str, Any]:
    record = {"format": acts.TAKING_BACK, "author": _did(by),
              "entry": entry}
    if after is not None:
        record["after"] = after
    return _signed(record, by)


def _putting(by: str, taken_back: str) -> Dict[str, Any]:
    return _signed({"format": acts.PUTTING_BACK, "author": _did(by),
                    "takenBack": taken_back}, by)


def _base() -> Tuple[apart.Log, List[str]]:
    """The trial room before anyone acts on it, and its entries'
    hashes: its first entry, two arrivals, then four things said, by
    ALICE, BOB, ALICE and BOB."""
    log = apart.Log(TABLE, FIRST, salt=apart_vectors._salts())
    for tick, kind, kept in WRITTEN:
        log.append(tick, kind, None, {}, kept)
    return log, [e["hash"] for e in log.entries]


def _shown(record: Any, **change: Any) -> Dict[str, Any]:
    """What an office's act says in the open of its decision record:
    the office's key, the first ground, and the record's hash."""
    data = {"office": record["office"]["key"],
            "ground": record["grounds"][0],
            "decision": records.record_hash(record)}
    data.update(change)
    return data


def _remove(log: apart.Log, tick: int, entry: str, record: Any,
            **change: Any) -> str:
    return log.append(tick, apart.REMOVED, None,
                      {"entry": entry, **_shown(record, **change)},
                      {"record": record})


def _restore(log: apart.Log, tick: int, incident: str, record: Any,
             **change: Any) -> str:
    return log.append(tick, apart.RESTORED, None,
                      {"incident": incident, **_shown(record, **change)},
                      {"record": record})


def _take_back(log: apart.Log, tick: int, entry: str, record: Any) -> str:
    return log.append(tick, apart.TAKEN_BACK, None, {"entry": entry},
                      {"record": record})


def _put_back(log: apart.Log, tick: int, taking: str, record: Any) -> str:
    return log.append(tick, apart.PUT_BACK, None, {"taken_back": taking},
                      {"record": record})


def _mark(log: apart.Log, tick: int, entry: str, field: str,
          by: str = MODERATOR, take_out: bool = True) -> str:
    mark = log.mark(tick, entry, field, _did(by), PRIVATE,
                    apart={"reason": "asked to"})
    if take_out:
        log.take_out(mark)
    return mark


def _keep(log: apart.Log, tick: int, mark: str, record: Any) -> str:
    """The decision to keep a field public: the field goes back from
    what the mark took out, here read from a room written again."""
    entry, field = log._scan.marks[mark]
    again, _ = _base()
    salt, value = again.contents[entry][field]
    shown = _shown(record)
    return log.keep_public(tick, mark, salt, value, shown["office"],
                           shown["ground"], shown["decision"],
                           apart={"reason": "decided", "record": record})


def _stays(log: apart.Log, tick: int, mark: str, record: Any) -> str:
    shown = _shown(record)
    return log.stays_redacted(tick, mark, shown["office"], shown["ground"],
                              shown["decision"],
                              apart={"reason": "decided", "record": record})


def whole() -> apart.Log:
    """The trial room with every kind of act in it, each allowed: a
    removal, its restoring, a second removal under a narrowed grant; an
    author's taking back, putting back and second taking back; a
    redacted field kept public and another that stays redacted. Then a
    taking back whose author's key is redacted afterwards, and a
    removal whose decision record is redacted."""
    g = grants()
    log, h = _base()
    first = _decision(MODERATOR, g["moderator"], "remove-comment", h[4], 5,
                      [BOB], grounds=(LAW, RULE2))
    removal = _remove(log, 5, h[4], first)
    _restore(log, 6, removal,
             _decision(KEEPER, g["keeper"], "restore-comment", removal, 6,
                       [BOB], grounds=(APPEAL,),
                       supersedes=records.record_hash(first)))
    second = _remove(log, 7, h[4],
                     _decision(APPRENTICE, g["apprentice"], "remove-comment",
                               h[4], 7, [BOB]))
    taking = _take_back(log, 8, h[3], _taking(ALICE, h[3]))
    putting = _put_back(log, 9, taking, _putting(ALICE, taking))
    _take_back(log, 10, h[3], _taking(ALICE, h[3], after=putting))
    mark = _mark(log, 11, h[5], "text")
    _keep(log, 12, mark,
          _decision(KEEPER, g["keeper"], "keep-field-public", mark, 12,
                    [ALICE], grounds=(APPEAL,)))
    mark = _mark(log, 13, h[6], "text")
    _stays(log, 14, mark,
           _decision(KEEPER, g["keeper"], "keep-field-redacted", mark, 14,
                     [BOB], grounds=(PRIVATE,)))
    _take_back(log, 15, h[6], _taking(BOB, h[6]))
    _mark(log, 16, h[6], "key")
    _mark(log, 17, second, "record")
    return log


def _chain(length: int) -> Tuple[List[Dict[str, Any]], str]:
    """A chain of `length` grants to remove comments, from the room's
    key down, each narrowing the one above, and the name of the last
    holder."""
    made: List[Dict[str, Any]] = []
    issuer = ROOM
    for n in range(length):
        holder = f"a trial holder, {n} below the room"
        made.append(_grant(issuer, holder, ["remove-comment"],
                           narrows=made[-1] if made else None))
        issuer = holder
    return made, issuer


def _all(g: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [g[name] for name in sorted(g)]


def holds() -> List[dict]:
    """Rooms that hold, each with the state of every act."""
    g = _all(grants())
    cases = []

    def add(name: str, log: List[dict], contents: Any,
            given: Optional[List[dict]] = None) -> None:
        case = {"name": name, "log": log, "contents": contents,
                "states": acts.check(log, contents,
                                     g if given is None else given, RULES)}
        if given is not None:
            case["grants"] = given
        cases.append(case)

    room, _ = _base()
    add("a room no one has acted on", room.entries, room.contents)

    room = whole()
    add("every kind of act, each allowed", room.entries, room.contents)

    # A copy of the log published without one decision record, with no
    # mark to say why: a fault in whoever published it, and a state.
    contents = copy.deepcopy(room.contents)
    restoring = next(e["hash"] for e in room.entries
                     if e["kind"] == apart.RESTORED)
    del contents[restoring]["record"]
    add("the same room, published without the restoring's record",
        room.entries, contents)

    # A key under a mark is not read, even while it is still in the
    # contents: the signer is then not checked.
    room, h = _base()
    _take_back(room, 5, h[3], _taking(ALICE, h[3]))
    _mark(room, 6, h[3], "key", take_out=False)
    add("a taking back whose author's key is marked and not yet taken "
        "out", room.entries, room.contents)

    chain, last = _chain(acts.MAX_CHAIN)
    room, h = _base()
    _remove(room, 5, h[4], _decision(last, chain[-1], "remove-comment",
                                     h[4], 5, [BOB]))
    add(f"a removal under a chain of {acts.MAX_CHAIN} grants",
        room.entries, room.contents, chain)

    room, h = _base()
    _remove(room, 5, h[4], _decision(MODERATOR, grants()["moderator"],
                                     "remove-comment", h[4], 5, [BOB],
                                     created=FROM))
    add("a removal decided at the second its office's grant began",
        room.entries, room.contents)
    return cases


def refused() -> List[dict]:
    """Rooms that are refused, each for one reason, at one entry."""
    g = grants()
    given = _all(g)
    cases: List[dict] = []

    def add(name: str, room: apart.Log, reason: str, *,
            grants_: Optional[Any] = None, rules: Optional[Any] = None,
            contents: Optional[Any] = None) -> None:
        log = room.entries
        held = room.contents if contents is None else contents
        try:
            acts.check(log, held, given if grants_ is None else grants_,
                       RULES if rules is None else rules)
        except acts.ActError as e:
            assert e.reason == reason, (name, e.reason)
            case = {"name": name, "log": log, "contents": held,
                    "reason": reason, "where": e.where}
        else:
            raise AssertionError(f"{name}: held")
        if grants_ is not None:
            case["grants"] = grants_
        if rules is not None:
            case["rules"] = rules
        cases.append(case)

    def removal(by: str = MODERATOR, grant: Optional[dict] = None,
                tick: int = 5, affects: Sequence[str] = (BOB,),
                **more: Any) -> Tuple[apart.Log, List[str], dict]:
        """The trial room, and a decision by `by` to remove what BOB
        said, not yet written."""
        room, h = _base()
        record = _decision(by, g["moderator"] if grant is None else grant,
                           "remove-comment", h[4], tick, affects, **more)
        return room, h, record

    # The rules, and the grants as given.
    room, h = _base()
    for name, rules in [
        ("rules with a part no one defines", dict(RULES, law="part 3")),
        ("rules whose room is a name, not a did:key",
         dict(RULES, room="a trial room")),
        ("rules that name, for who wrote an entry, a field the table "
         "does not keep apart",
         dict(RULES, authors={"entered": "key", "said": "name"})),
        ("rules that allow taking back a kind of entry and do not say "
         "who wrote it",
         dict(RULES, on=dict(RULES["on"], **{
             apart.TAKEN_BACK: ["said", "showed"]}))),
        ("rules whose kinds of entry are not in ascending order",
         dict(RULES, on=dict(RULES["on"], **{
             apart.MARK: ["said", "entered"]}))),
        ("rules that allow removing a removal",
         dict(RULES, on=dict(RULES["on"], **{
             apart.REMOVED: [apart.REMOVED, "said"]}))),
        ("rules that say nothing of what a mark may be on",
         dict(RULES, on={k: v for k, v in RULES["on"].items()
                         if k != apart.MARK})),
    ]:
        add(name, room, acts.RULES, rules=rules)
    add("grants given as a map, not a list", room, acts.RULES,
        grants_={"moderator": g["moderator"]})

    # Which kinds of entry an act may be on.
    room, h = _base()
    _remove(room, 5, h[1], _decision(MODERATOR, g["moderator"],
                                     "remove-comment", h[1], 5, [ALICE]))
    add("a removal of an arrival, where only what is said can be removed",
        room, acts.NOT_ON)
    room, h = _base()
    _take_back(room, 5, h[1], _taking(ALICE, h[1]))
    add("a taking back of an arrival", room, acts.NOT_ON)
    room, h = _base()
    _mark(room, 5, h[1], "name")
    add("a mark on an arrival, where the rules allow one only on what "
        "is said", room, acts.NOT_ON,
        rules=dict(RULES, on=dict(RULES["on"], **{apart.MARK: ["said"]})))

    # A decision is carried by one entry.
    room, h, record = removal()
    incident = _remove(room, 5, h[4], record)
    _restore(room, 6, incident,
             _decision(KEEPER, g["keeper"], "restore-comment", incident, 6,
                       [BOB], grounds=(APPEAL,),
                       supersedes=records.record_hash(record)))
    _remove(room, 7, h[4], record)
    add("a removal written again, after its restoring, from the first "
        "removal's decision", room, acts.TWICE)

    # The record an act carries.
    room, h, record = removal()
    room.append(5, apart.REMOVED, None, {"entry": h[4], **_shown(record)},
                {})
    add("a removal that carries no record", room, acts.NO_RECORD)
    room, h = _base()
    room.append(5, apart.TAKEN_BACK, None, {"entry": h[3]}, {})
    add("a taking back that carries no record", room, acts.NO_RECORD)

    room, h, record = removal()
    room.append(5, apart.REMOVED, None, {"entry": h[4], **_shown(record)},
                {"record": "a trial decision, not a signed one"})
    add("a removal whose record is text", room, acts.NOT_A_RECORD)
    room, h, record = removal()
    _remove(room, 5, h[4], dict(record, reasons=record["reasons"] + " Also."))
    add("a removal whose decision was changed after it was signed",
        room, acts.NOT_A_RECORD)
    room, h = _base()
    room.append(5, apart.REMOVED, None,
                {"entry": h[4], "office": _did(MODERATOR), "ground": LAW,
                 "decision": records.record_hash(g["moderator"])},
                {"record": g["moderator"]})
    add("a removal that carries a grant in place of a decision",
        room, acts.NOT_A_RECORD)
    room, h = _base()
    _take_back(room, 5, h[3], _putting(ALICE, h[3]))
    add("a taking back that carries a putting back's record",
        room, acts.NOT_A_RECORD)
    room, h = _base()
    taking = _take_back(room, 5, h[3], _taking(ALICE, h[3]))
    _put_back(room, 6, taking, _taking(ALICE, h[3]))
    add("a putting back that carries a taking back's record",
        room, acts.NOT_A_RECORD)

    room, h, record = removal()
    other = _decision(MODERATOR, g["moderator"], "remove-comment", h[4], 4,
                      [BOB])
    _remove(room, 5, h[4], record, decision=records.record_hash(other))
    add("a removal that names another decision than the one it carries",
        room, acts.OTHER_HASH)

    room, h = _base()
    _remove(room, 5, h[4],
            _decision(KEEPER, g["keeper"], "restore-comment", h[4], 5,
                      [BOB]))
    add("a removal that carries a decision to restore", room,
        acts.OTHER_ACT)
    room, h = _base()
    mark = _mark(room, 5, h[5], "text")
    _stays(room, 6, mark,
           _decision(KEEPER, g["keeper"], "keep-field-public", mark, 6,
                     [ALICE], grounds=(PRIVATE,)))
    add("a decision that a field stays redacted, carrying a decision "
        "to keep it public", room, acts.OTHER_ACT)

    _, said = _base()
    room, h, record = removal(act={"kind": "remove-comment",
                                   "records": [said[3]]})
    _remove(room, 5, h[4], record)
    add("a removal whose decision is on another entry", room,
        acts.OTHER_ENTRY)
    room, h, record = removal(act={"kind": "remove-comment",
                                   "records": [said[3], said[4]]})
    _remove(room, 5, h[4], record)
    add("a removal whose decision is on two entries", room,
        acts.OTHER_ENTRY)
    room, h, record = removal()
    incident = _remove(room, 5, h[4], record)
    _restore(room, 6, incident,
             _decision(KEEPER, g["keeper"], "restore-comment", h[4], 6,
                       [BOB], grounds=(APPEAL,),
                       supersedes=records.record_hash(record)))
    add("a restoring whose decision names the entry, not the removal",
        room, acts.OTHER_ENTRY)
    room, h = _base()
    mark = _mark(room, 5, h[5], "text")
    _stays(room, 6, mark,
           _decision(KEEPER, g["keeper"], "keep-field-redacted", h[5], 6,
                     [ALICE], grounds=(PRIVATE,)))
    add("a decision on a redaction that names the entry, not the mark",
        room, acts.OTHER_ENTRY)
    room, h = _base()
    _take_back(room, 5, h[3], _taking(ALICE, h[5]))
    add("a taking back whose record is on another entry of the author's",
        room, acts.OTHER_ENTRY)
    room, h = _base()
    one = _take_back(room, 5, h[3], _taking(ALICE, h[3]))
    two = _take_back(room, 6, h[5], _taking(ALICE, h[5]))
    _put_back(room, 7, one, _putting(ALICE, two))
    add("a putting back whose record undoes another taking back",
        room, acts.OTHER_ENTRY)

    room, h, record = removal()
    _remove(room, 5, h[4], record, office=_did(KEEPER))
    add("a removal that shows the Keeper as its office, decided by the "
        "moderator", room, acts.OTHER_OFFICE)
    room, h, record = removal()
    _remove(room, 5, h[4], record, office="trial moderator")
    add("a removal that shows its office by a name, not by its key",
        room, acts.OTHER_OFFICE)

    room, h, record = removal(grounds=(LAW, RULE2))
    _remove(room, 5, h[4], record, ground=RULE2)
    add("a removal that shows its decision's second ground", room,
        acts.OTHER_GROUND)

    room, h, record = removal(tick=6)
    _remove(room, 5, h[4], record)
    add("a removal whose decision is dated a tick after its entry",
        room, acts.LATER)

    room, h, record = removal()
    incident = _remove(room, 5, h[4], record)
    _restore(room, 6, incident,
             _decision(KEEPER, g["keeper"], "restore-comment", incident, 6,
                       [BOB], grounds=(APPEAL,)))
    add("a restoring whose decision supersedes nothing", room,
        acts.NOT_SUPERSEDING)
    room, h, record = removal()
    incident = _remove(room, 5, h[4], record)
    _restore(room, 6, incident,
             _decision(KEEPER, g["keeper"], "restore-comment", incident, 6,
                       [BOB], grounds=(APPEAL,),
                       supersedes=records.record_hash(g["moderator"])))
    add("a restoring whose decision supersedes another record than the "
        "removal's decision", room, acts.NOT_SUPERSEDING)

    room, h, record = removal(affects=[ALICE])
    _remove(room, 5, h[4], record)
    add("a removal whose decision does not name the one who wrote the "
        "entry among those it affects", room, acts.NOT_AFFECTED)
    room, h, record = removal()
    incident = _remove(room, 5, h[4], record)
    _restore(room, 6, incident,
             _decision(KEEPER, g["keeper"], "restore-comment", incident, 6,
                       [], grounds=(APPEAL,),
                       supersedes=records.record_hash(record)))
    add("a restoring whose decision affects no one", room,
        acts.NOT_AFFECTED)

    # The office's grant, and the grants above it.
    room, h, record = removal()
    _remove(room, 5, h[4], record)
    add("a removal whose office's grant is not among the grants given",
        room, acts.NO_GRANT, grants_=[g["keeper"]])
    room, h, record = removal(APPRENTICE, g["apprentice"])
    _remove(room, 7, h[4], record)
    add("a removal under a narrowed grant, with the grant above it not "
        "given", room, acts.NO_GRANT,
        grants_=[g["apprentice"], g["keeper"]])

    changed = dict(g["moderator"],
                   allows=g["moderator"]["allows"] + ["restore-comment"])
    room, h, record = removal(grant=changed)
    _remove(room, 5, h[4], record)
    add("a removal under a grant that was changed after it was signed",
        room, acts.BAD_GRANT, grants_=[changed, g["keeper"]])
    earlier = _decision(MODERATOR, g["moderator"], "remove-comment",
                        said[4], 4, [BOB])
    room, h, record = removal(grant=earlier)
    _remove(room, 5, h[4], record)
    add("a removal whose office names a decision as its grant", room,
        acts.BAD_GRANT, grants_=given + [earlier])

    room, h, record = removal(APPRENTICE, g["moderator"])
    _remove(room, 5, h[4], record)
    add("a removal by an office that names another office's grant",
        room, acts.NOT_HOLDER)

    room, h, record = removal()
    incident = _remove(room, 5, h[4], record)
    _restore(room, 6, incident,
             _decision(MODERATOR, g["moderator"], "restore-comment",
                       incident, 6, [BOB], grounds=(APPEAL,),
                       supersedes=records.record_hash(record)))
    add("a restoring by the moderator, whose grant allows removing only",
        room, acts.NOT_ALLOWED)
    wide = _grant(MODERATOR, APPRENTICE,
                  ["remove-comment", "restore-comment"],
                  narrows=g["moderator"])
    room, h, record = removal()
    incident = _remove(room, 5, h[4], record)
    _restore(room, 6, incident,
             _decision(APPRENTICE, wide, "restore-comment", incident, 6,
                       [BOB], grounds=(APPEAL,),
                       supersedes=records.record_hash(record)))
    add("a restoring under a grant that allows more than the grant it "
        "narrows", room, acts.NOT_ALLOWED, grants_=given + [wide])

    other_room = _grant(ROOM, MODERATOR, ["remove-comment"],
                        within=_did("another trial room"))
    room, h, record = removal(grant=other_room)
    _remove(room, 5, h[4], record)
    add("a removal under a grant for another room", room, acts.ELSEWHERE,
        grants_=given + [other_room])
    everywhere = _grant(ROOM, MODERATOR, ["remove-comment"],
                        within="multiverse")
    room, h, record = removal(grant=everywhere)
    _remove(room, 5, h[4], record)
    add("a removal under a grant across the multiverse, from a room's "
        "key", room, acts.ELSEWHERE, grants_=given + [everywhere])

    room, h, record = removal(created="2026-11-17T23:59:59Z")
    _remove(room, 5, h[4], record)
    add("a removal decided a second before its office's grant began",
        room, acts.NOT_IN_FORCE)
    room, h, record = removal(APPRENTICE, g["apprentice"],
                              created="2026-12-18T00:00:00Z")
    _remove(room, 5, h[4], record)
    add("a removal decided at the second its office's grant ended",
        room, acts.NOT_IN_FORCE)
    short = _grant(ROOM, MODERATOR, ["remove-comment"],
                   until="2026-11-18T06:00:00Z")
    below = _grant(MODERATOR, APPRENTICE, ["remove-comment"], narrows=short)
    room, h, record = removal(APPRENTICE, below)
    _remove(room, 5, h[4], record)
    add("a removal under a grant still in force, narrowing a grant that "
        "had ended", room, acts.NOT_IN_FORCE, grants_=[short, below])

    stray = _grant(OUTSIDER, APPRENTICE, ["remove-comment"],
                   narrows=g["moderator"])
    room, h, record = removal(APPRENTICE, stray)
    _remove(room, 5, h[4], record)
    add("a removal under a grant that narrows a grant its issuer does "
        "not hold", room, acts.NOT_NARROWING, grants_=given + [stray])

    own = _grant(MODERATOR, MODERATOR, ["remove-comment"])
    room, h, record = removal(grant=own)
    _remove(room, 5, h[4], record)
    add("a removal under a grant an office gave itself", room,
        acts.NOT_ROOMS, grants_=given + [own])
    keepers = _grant(KEEPER, MODERATOR, ["remove-comment"])
    room, h, record = removal(grant=keepers)
    _remove(room, 5, h[4], record)
    add("a removal under a grant from the Keeper that narrows nothing",
        room, acts.NOT_ROOMS, grants_=given + [keepers])

    chain, last = _chain(acts.MAX_CHAIN + 1)
    room, h, record = removal(last, chain[-1])
    _remove(room, 5, h[4], record)
    add(f"a removal under a chain of {acts.MAX_CHAIN + 1} grants", room,
        acts.TOO_DEEP, grants_=chain)

    # An author's own acts.
    room, h = _base()
    first = _taking(ALICE, h[3])
    taking = _take_back(room, 5, h[3], first)
    _put_back(room, 6, taking, _putting(ALICE, taking))
    _take_back(room, 7, h[3], first)
    add("a taking back written again, after its author put the entry "
        "back, from the first record", room, acts.OTHER_PLACE)
    room, h = _base()
    _take_back(room, 5, h[3], _taking(ALICE, h[3], after=h[5]))
    add("a first taking back that names a putting back", room,
        acts.OTHER_PLACE)
    room, h = _base()
    taking = _take_back(room, 5, h[3], _taking(ALICE, h[3]))
    _put_back(room, 6, taking, _putting(ALICE, taking))
    _take_back(room, 7, h[3], _taking(ALICE, h[3], after=taking))
    add("a second taking back that names the first taking back, not "
        "the putting back", room, acts.OTHER_PLACE)

    room, h = _base()
    _take_back(room, 5, h[3], _taking(BOB, h[3]))
    add("a taking back signed by another than the one who wrote the "
        "entry", room, acts.NOT_AUTHOR)
    room, h = _base()
    taking = _take_back(room, 5, h[3], _taking(ALICE, h[3]))
    _put_back(room, 6, taking, _putting(BOB, taking))
    add("a putting back signed by another than the one who wrote the "
        "entry", room, acts.NOT_AUTHOR)
    room, h = _base()
    bare = room.append(5, "said", None, {},
                       {"text": "said under no key", "time": 1794787440})
    _take_back(room, 6, bare, _taking(ALICE, bare))
    add("a taking back of an entry that names no one who wrote it",
        room, acts.NOT_AUTHOR)

    # Two faults in one room: the reason is the one met first in the
    # check's order, and Rust must meet the same one.
    room, h = _base()
    _remove(room, 5, h[1], _decision(MODERATOR, g["moderator"],
                                     "remove-comment", h[4], 5, [BOB]))
    add("two faults in one act: a removal of an arrival, whose decision "
        "is on another entry", room, acts.NOT_ON)
    room, h, record = removal(tick=7, created="2026-11-17T12:00:00Z")
    _remove(room, 5, h[4], record)
    add("two faults in one act: a removal decided after its entry, by an "
        "office whose grant was not yet in force", room, acts.LATER)
    room, h = _base()
    _take_back(room, 5, h[3], _taking(BOB, h[3]))
    _remove(room, 6, h[4], _decision(APPRENTICE, g["moderator"],
                                     "remove-comment", h[4], 6, [BOB]))
    add("two faulty acts: a taking back signed by another, then a "
        "removal by an office that does not hold the grant it names",
        room, acts.NOT_AUTHOR)
    return cases


def offices() -> List[dict]:
    """Records held to their office's grant on their own."""
    g = grants()
    given = _all(g)
    room, h = _base()
    salt, value = room.contents[h[5]]["text"]
    copy_ = _signed({
        "format": acts.COPY,
        "office": {"key": _did(MODERATOR),
                   "grant": records.record_hash(g["moderator"])},
        "to": _did(ALICE), "decider": _did(KEEPER), "log": h[0],
        "entry": h[5], "field": "text",
        "hashed": apart.fingerprint_text(salt, "text", value),
        "pad": ""}, MODERATOR)
    apprentices = _signed({
        **{k: v for k, v in copy_.items() if k != "proof"},
        "office": {"key": _did(APPRENTICE),
                   "grant": records.record_hash(g["apprentice"])}},
        APPRENTICE)
    decision = _decision(MODERATOR, g["moderator"], "remove-comment", h[4],
                         5, [BOB])
    cases = []
    for name, record, act, reason in [
        ("a redacted field's copy, signed by an office that may redact",
         copy_, acts.ACTS[apart.MARK], None),
        ("a redacted field's copy, signed by an office whose grant "
         "allows removing only", apprentices, acts.ACTS[apart.MARK],
         acts.NOT_ALLOWED),
        ("a decision to remove, by an office that may", decision,
         "remove-comment", None),
        ("a decision to remove, held to restoring", decision,
         "restore-comment", acts.OTHER_ACT),
        ("a redacted field's copy, held to removing", copy_,
         "remove-comment", acts.OTHER_ACT),
        ("a grant, which names no office", g["moderator"],
         "remove-comment", acts.NOT_A_RECORD),
        ("a redacted field's copy changed after it was signed",
         dict(copy_, field="time"), acts.ACTS[apart.MARK],
         acts.NOT_A_RECORD),
    ]:
        try:
            acts.office_may(record, act, given, RULES)
            got = None
        except acts.ActError as e:
            got = e.reason
        assert got == reason, (name, got)
        cases.append({"name": name, "record": record, "act": act,
                      "reason": reason})
    return cases


def vectors() -> Dict[str, Any]:
    g = grants()
    return {
        "note": ("Trial vectors for the check of who may act on a log "
                 "(world/acts.py, rust/acts). The keys are test keys and "
                 "the salts the trial salts of vectors/log-apart.json: "
                 "public to everyone, never for anything real."),
        "record": acts.RECORD,
        "acts": dict(acts.ACTS),
        "own_acts": dict(acts.OWN_ACTS),
        "ruled": list(acts.RULED),
        "max_chain": acts.MAX_CHAIN,
        "states": list(acts.STATES),
        "reasons": list(acts.REASONS),
        "created": CREATED,
        "parties": {name: _did(name) for name in PARTIES},
        "rules": RULES,
        "granted": {name: records.record_hash(g[name]) for name in sorted(g)},
        "grants": _all(g),
        "holds": holds(),
        "refused": refused(),
        "offices": offices(),
    }


def text() -> str:
    return json.dumps(vectors(), indent=1, ensure_ascii=False) + "\n"


def main() -> None:
    FILE.write_text(text(), encoding="utf-8")
    print(f"wrote {FILE}")


if __name__ == "__main__":
    main()
