"""Shared test vectors for a log whose fields are kept apart
(`world/apart.py`; course step 3b, parts two to four): `vectors/log-apart.json`,
written with the kernel's other vectors by `python3 -m world.vectors`
and read by `rust/world-log`.

Everything in it is a trial. The salts are fixed, so that the file is
the same on every run, and they are public to everyone: a real log's
salts come from the operating system and are never written anywhere but
its contents. The keys and names are plain made-up text.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any, Callable, Dict, List, Tuple

from . import apart
from .core import GENESIS, _digest

TABLE = {
    "entered": ["key", "name"],
    "entry_put_back": ["record"],
    "entry_removed": ["record"],
    "entry_restored": ["record"],
    "entry_taken_back": ["record"],
    "field_kept_public": ["reason"],
    "field_redacted": ["reason"],
    "field_stays_redacted": ["reason"],
    "said": ["key", "text", "time"],
    "showed": ["key", "thing"],
}

# The first entry's open data, before the form and the table are added.
FIRST = {"rules_version": "vectors-apart-1"}

OFFICE = "trial office"
MODERATOR = "trial moderator"
KEEPER = "trial keeper"
GROUND = {"kind": "law", "ref": "trial room law, part 3"}
# Why a field is redacted, in general terms, never what it said.
PRIVATE = {"kind": "rule", "ref": "trial room law, private information"}
APPEAL = {"kind": "rule", "ref": "trial appeal rule"}


def trial_decision(n: int) -> str:
    """A stand-in for a decision record's hash: 64 hex digits, public,
    and the hash of no record."""
    return hashlib.sha256(f"open-worlds trial decision {n}".encode()).hexdigest()


def trial_salt(n: int) -> str:
    """The n-th trial salt: public, fixed, and never for anything real."""
    text = f"open-worlds trial salt {n}"
    return hashlib.sha256(text.encode()).hexdigest()[:32]


def _salts() -> Callable[[], str]:
    count = [0]

    def next_salt() -> str:
        count[0] += 1
        return trial_salt(count[0] - 1)
    return next_salt


# What the trial room writes after its first entry: tick, kind, agent,
# open data, and the fields kept apart.
WRITTEN: List[Tuple[int, str, Any, dict, dict]] = [
    (0, "entered", None, {},
     {"key": "trial key of ada", "name": "ada"}),
    (0, "entered", None, {},
     {"key": "trial key of bo", "name": "bo"}),
    (1, "said", None, {},
     {"key": "trial key of ada", "text": "hello, room",
      "time": 1794787200}),
    (2, "said", None, {},
     {"key": "trial key of bo",
      "text": "café 中文 \U0001F642   \" \\ \n",
      "time": 1794787260}),
    (3, "said", None, {},
     {"key": "trial key of ada", "text": "my door is 1 Trial Street",
      "time": 1794787320}),
    (4, "showed", None, {"where": "the table"},
     {"key": "trial key of bo",
      "thing": {"words": ["a", "b"], "loud": True, "count": -3}}),
]


def _room() -> apart.Log:
    log = apart.Log(TABLE, FIRST, salt=_salts())
    for tick, kind, agent, data, kept in WRITTEN:
        log.append(tick, kind, agent, data, kept)
    return log


def _mark(log: apart.Log, tick: int, entry: str, field: str,
          reason: str) -> str:
    """A mark: the field is still in the contents until it is taken
    out."""
    return log.mark(tick, entry, field, OFFICE, PRIVATE,
                    apart={"reason": reason})


def _keep(log: apart.Log, tick: int, mark: str, reason: str,
          n: int = 1) -> str:
    """The decision to keep a field public, for a field that is still
    in the contents."""
    entry, field = log._scan.marks[mark]
    salt, value = log.contents[entry][field]
    return log.keep_public(tick, mark, salt, value, KEEPER, APPEAL,
                           trial_decision(n), apart={"reason": reason})


def _stays(log: apart.Log, tick: int, mark: str, reason: str,
           n: int = 1) -> str:
    """The decision that a field stays redacted, taking the field out
    first if it is still there."""
    entry, field = log._scan.marks[mark]
    if field in log.contents.get(entry, {}):
        log.take_out(mark)
    return log.stays_redacted(tick, mark, KEEPER, APPEAL,
                              trial_decision(n), apart={"reason": reason})


def _case(name: str, log: List[dict], contents: Any) -> dict:
    return {"name": name, "log": log, "contents": contents,
            "states": apart.check(log, contents),
            "incidents": apart.incidents(log),
            "redactions": apart.redactions(log),
            "joined": apart.join(log, contents)}


def _remove(log: apart.Log, tick: int, entry: str, n: int) -> str:
    return log.append(tick, apart.REMOVED, None,
                      {"entry": entry, "office": MODERATOR, "ground": GROUND,
                       "decision": trial_decision(n)},
                      {"record": f"trial decision record {n}, not a signed one"})


def _restore(log: apart.Log, tick: int, incident: str, n: int) -> str:
    return log.append(tick, apart.RESTORED, None,
                      {"incident": incident, "office": KEEPER,
                       "ground": {"kind": "rule", "ref": "trial appeal rule"},
                       "decision": trial_decision(n)},
                      {"record": f"trial decision record {n}, not a signed one"})


def _take_back(log: apart.Log, tick: int, entry: str) -> str:
    return log.append(tick, apart.TAKEN_BACK, None, {"entry": entry},
                      {"record": "trial record of taking back, not signed"})


def _put_back(log: apart.Log, tick: int, taking: str) -> str:
    return log.append(tick, apart.PUT_BACK, None, {"taken_back": taking},
                      {"record": "trial record of putting back, not signed"})


def acted_on() -> Tuple[apart.Log, Dict[str, str]]:
    """The trial room with every row of the table of what wins that
    holds (docs/research/REDACTION.md, decision 9), and what each entry
    is named in the tests."""
    room = _room()
    h = [e["hash"] for e in room.entries]
    names = {"hello": h[3], "cafe": h[4], "door": h[5], "thing": h[6]}
    # Removed, restored, and removed again: a new incident, a new id.
    first = _remove(room, 5, h[3], 1)
    _restore(room, 6, first, 2)
    names["second removal"] = _remove(room, 7, h[3], 3)
    # Taken back by its author, and put back: it shows again.
    taking = _take_back(room, 8, h[4])
    _put_back(room, 9, taking)
    # Removed by an office, then taken back by its author: allowed, and
    # it stays hidden whatever the office does next.
    names["removal of door"] = _remove(room, 10, h[5], 4)
    _take_back(room, 11, h[5])
    # Removed, and one of its fields redacted: the entry is hidden, and
    # the field stays redacted.
    _remove(room, 12, h[6], 5)
    _mark(room, 13, h[6], "thing", "it names a third person")
    # A removal whose own record has to be redacted: the removal still
    # stands, and still says its office and its ground in the open.
    _mark(room, 14, names["second removal"], "record",
          "the reasons repeated what was removed")
    # The removal of what its author then took back is restored: the
    # removal stops standing, and the entry stays taken back.
    _restore(room, 15, names["removal of door"], 6)
    # Removed and restored, and left so: restored, never again as
    # written. The ground is an earlier record, named by its hash.
    names["later"] = room.append(
        16, "said", None, {},
        {"key": "trial key of bo", "text": "a later word",
         "time": 1794787380})
    removal = room.append(
        17, apart.REMOVED, None,
        {"entry": names["later"], "office": MODERATOR,
         "ground": {"kind": "record", "ref": trial_decision(1)},
         "decision": trial_decision(7)},
        {"record": "trial decision record 7, not a signed one"})
    _restore(room, 18, removal, 8)
    # Removed, taken back and put back: the removal still stands, so
    # the entry is removed.
    names["last"] = room.append(
        19, "said", None, {},
        {"key": "trial key of ada", "text": "a last word",
         "time": 1794787440})
    _remove(room, 20, names["last"], 9)
    taking = _take_back(room, 21, names["last"])
    _put_back(room, 22, taking)
    return room, names


def holds() -> List[dict]:
    """Logs and contents that hold, each with every field's state and
    the entries as a reader uses them."""
    cases = []

    room = _room()
    cases.append(_case("every field is there", room.entries, room.contents))

    cases.append(_case("nothing is kept beside the log", room.entries, {}))

    contents = copy.deepcopy(room.contents)
    contents[room.entries[1]["hash"]] = {}
    contents[room.entries[0]["hash"]] = {}
    cases.append(_case("an entry's fields may be an empty map",
                       room.entries, contents))

    room = _room()
    h = [e["hash"] for e in room.entries]
    gone = []
    # Redacted: a mark is open, and the field is gone.
    first_mark = _mark(room, 5, h[5], "text", "private information")
    room.take_out(first_mark)
    # Unfinished: a mark is open, and the field is still there.
    _mark(room, 5, h[4], "text", "asked by its author")
    # Kept public: the mark was answered, and the field is there.
    mark = _mark(room, 6, h[3], "time", "asked by its author")
    _keep(room, 7, mark, "a time of day says nothing private here", 1)
    # Missing: gone, with no mark at all.
    gone.append((h[1], "name"))
    # Missing: the mark was answered, and the field is gone all the
    # same. The writer never leaves this; whoever published the log
    # lost the field afterwards.
    mark = _mark(room, 8, h[2], "name", "asked by its author")
    _keep(room, 9, mark, "the name is on the door", 2)
    gone.append((h[2], "name"))
    # Redacted: marked, kept public, and marked again.
    mark = _mark(room, 10, h[6], "thing", "asked by its author")
    _keep(room, 11, mark, "nothing private in it", 3)
    room.take_out(_mark(room, 12, h[6], "thing", "it names a third person"))
    # Redacted: a mark's own reason, which said what it should not.
    room.take_out(_mark(room, 13, first_mark, "reason",
                        "the reason repeated it"))
    # Redacted, and decided: the mark stands for good.
    mark = _mark(room, 14, h[5], "time", "asked by its author")
    _stays(room, 15, mark, "with the text, the time says where", 4)
    # Unfinished, though decided: whoever published the log left the
    # field in the contents after the decision that it stays redacted.
    mark = _mark(room, 16, h[3], "key", "asked by its author")
    left = copy.deepcopy(room.contents[h[3]]["key"])
    _stays(room, 17, mark, "a key that was never meant to be shown", 5)
    contents = copy.deepcopy(room.contents)
    contents[h[3]]["key"] = left
    for entry, field in gone:
        del contents[entry][field]
    cases.append(_case("the five states", room.entries, contents))

    # The open part at its edges: the largest tick and whole numbers,
    # the deepest nesting, an agent that is text, and text that needs
    # escaping.
    edge = apart.Log(TABLE, FIRST, salt=_salts())
    edge.append(apart.MAX_WHOLE, "measured", OFFICE,
                {"most": apart.MAX_WHOLE, "least": -apart.MAX_WHOLE,
                 "deep": _nested(apart.MAX_NESTING - 1),
                 "text": "caf\u00e9 \U0001F642 \" \\ \n",
                 "flags": [True, False], "empty": {}}, {})
    cases.append(_case("the open part at its edges", edge.entries,
                       edge.contents))

    room, names = acted_on()
    contents = copy.deepcopy(room.contents)
    del contents[names["thing"]]["thing"]
    del contents[names["second removal"]]["record"]
    cases.append(_case("removed, restored, taken back and put back",
                       room.entries, contents))

    # A ground's reference at its longest, in characters that each take
    # two UTF-16 units and four bytes: the limit counts code points.
    room = _room()
    room.append(5, apart.REMOVED, None,
                {"entry": room.entries[3]["hash"], "office": MODERATOR,
                 "ground": {"kind": "law",
                            "ref": "\U0001D11E" * apart.MAX_REF},
                 "decision": trial_decision(6)},
                {"record": "trial decision record 6, not a signed one"})
    cases.append(_case("a ground's reference at its longest",
                       room.entries, room.contents))
    return cases


def _raw(log: List[dict], tick: Any, kind: Any, agent: Any, data: Any,
         prints: Any, **more: Any) -> str:
    """Appends an entry as given, checking nothing: for logs that must
    be refused. `prints` is left out of the entry if it is None."""
    body = {"tick": tick, "kind": kind, "agent": agent, "data": data,
            "prev": log[-1]["hash"] if log else GENESIS, **more}
    if prints is not None:
        body["apart"] = prints
    log.append({**body, "hash": _digest(body)})
    return log[-1]["hash"]


def _start(table: Any = None, **first: Any) -> List[dict]:
    """A raw log holding only a first entry in this form."""
    data = {"form": apart.FORM,
            "kept_apart": TABLE if table is None else table, **FIRST}
    data.update(first)
    log: List[dict] = []
    _raw(log, 0, "world_created", None, data, {})
    return log


def _short() -> Tuple[List[dict], Dict[str, Dict[str, list]]]:
    """The first entry and ada's arrival, with their contents."""
    log = apart.Log(TABLE, FIRST, salt=_salts())
    log.append(*WRITTEN[0])
    return copy.deepcopy(log.entries), copy.deepcopy(log.contents)


def _print(n: int, name: str, value: Any) -> str:
    return apart.fingerprint(trial_salt(n), name, value)


def place(e: apart.Refused) -> Any:
    """Where a refusal points, as the vectors write it: nothing; an
    entry's place in the log, from 0; or, in the contents, an entry's
    hash alone or with a field's name."""
    if isinstance(e.where, tuple):
        return list(e.where)
    if isinstance(e.where, str):
        return [e.where]
    return e.where


def refused() -> List[dict]:
    """Logs and contents that must be refused, each for one reason and
    at one place. Most hold one fault; those named "two faults" hold
    two, and say which is met first."""
    cases: List[dict] = []

    def add(reason: str, name: str, log: Any, contents: Any) -> None:
        try:
            apart.check(log, contents)
        except apart.Refused as e:
            if e.reason != reason:
                raise AssertionError(f"{name}: {e.reason}") from None
            where = place(e)
        else:
            raise AssertionError(f"{name}: not refused")
        cases.append({"name": name, "log": log, "contents": contents,
                      "reason": reason, "where": where})

    # -- the chain --
    log, contents = _short()
    log[1]["apart"]["name"] = "0" * 64
    add(apart.CHAIN, "an entry was changed after it was written",
        log, contents)
    add(apart.CHAIN, "the log is a map", {}, {})

    # -- the form --
    add(apart.NO_FORM, "an empty log", [], {})
    log = []
    _raw(log, 0, "world_created", None, {"rules_version": "1"}, None)
    add(apart.NO_FORM, "the kernel's own form", log, {})
    log = []
    _raw(log, 0, "world_created", None,
         {"form": "open-worlds/log-apart/v2", "kept_apart": TABLE}, {})
    add(apart.NO_FORM, "another version of the form", log, {})
    log = []
    _raw(log, 0, "world_created", None, None, {})
    add(apart.NO_FORM, "a first entry whose data is not a map", log, {})

    # -- the table --
    for name, table in [
            ("the table is a list", [["entered", ["key", "name"]]]),
            ("a kind's fields are text", {"entered": "name"}),
            ("names out of order", {"entered": ["name", "key"]}),
            ("a name twice", {"entered": ["key", "key"]}),
            ("a name in capitals", {"entered": ["Key"]}),
            ("an empty name", {"entered": [""]}),
            ("a name of 65 characters", {"entered": ["k" * 65]}),
            ("a name that is a number", {"entered": [5]})]:
        add(apart.TABLE, name, _start(table), {})
    log = []
    _raw(log, 0, "world_created", None, {"form": apart.FORM}, {})
    add(apart.TABLE, "no table at all", log, {})

    # -- an entry's shape --
    key, name_ = _print(0, "key", "k"), _print(1, "name", "n")
    log = _start()
    _raw(log, 0, "entered", None, {}, None)
    add(apart.ENTRY, "an entry without its apart", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, [key])
    add(apart.ENTRY, "an entry whose apart is a list", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, {"key": key.upper()})
    add(apart.ENTRY, "a fingerprint in capitals", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, {"key": key[:63]})
    add(apart.ENTRY, "a fingerprint of 63 digits", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, {"key": 7})
    add(apart.ENTRY, "a fingerprint that is a number", log, {})
    log = _start()
    _raw(log, 0, "entered", None, None, {})
    add(apart.ENTRY, "data that is not a map", log, {})
    log = _start()
    _raw(log, 0, 5, None, {}, {})
    add(apart.ENTRY, "a kind that is not text", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, {"Name": name_})
    add(apart.ENTRY, "a field's name in capitals", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, {"name": name_}, text="in the open")
    add(apart.ENTRY, "an entry with a field of its own beside its data",
        log, {})
    for missing in ("tick", "agent"):
        log = _start()
        _raw(log, 0, "entered", None, {}, {"name": name_})
        del log[1][missing]
        body = {k: v for k, v in log[1].items() if k != "hash"}
        log[1]["hash"] = _digest(body)
        add(apart.ENTRY, f"an entry without its {missing}", log, {})

    # -- an entry's open part --
    for name, tick, agent, data in [
            ("a number with a fraction in the open data", 0, None,
             {"height": 1.5}),
            ("nothing as a value in the open data", 0, None, {"where": None}),
            ("two to the 53 in the open data", 0, None,
             {"count": apart.MAX_WHOLE + 1}),
            ("open data nested one too deep", 0, None,
             {"deep": _nested(apart.MAX_NESTING)}),
            ("a tick with a fraction", 1.5, None, {}),
            ("a tick that is text", "1", None, {}),
            ("a tick below zero", -1, None, {}),
            ("a tick of two to the 53", apart.MAX_WHOLE + 1, None, {}),
            ("an agent that is a number", 0, 7, {}),
            ("an agent that is a list", 0, ["trial office"], {})]:
        log = _start()
        _raw(log, tick, "entered", agent, data, {})
        add(apart.ENTRY, name, log, {})

    # -- two faults in a log: the first in the log's order is named, and
    # within an entry its link, then what it says, then its hash --
    log = _start()
    _raw(log, 0, "entered", None, {"height": 1.5}, {})
    _raw(log, 1, "entered", None, {}, {})
    log[2]["prev"] = "f" * 64
    add(apart.ENTRY, "two faults: a number with a fraction, then a broken "
        "link", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {"height": 1.5}, {})
    log[1]["hash"] = "f" * 64
    add(apart.ENTRY, "two faults: a number with a fraction in an entry "
        "whose hash is wrong", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, {})
    _raw(log, 1, "entered", None, {"height": 1.5}, {})
    log[1]["prev"] = "f" * 64
    add(apart.CHAIN, "two faults: a broken link, then a number with a "
        "fraction", log, {})
    log = _start()
    _raw(log, 0, "entered", None, {"height": 1.5}, {})
    log[1]["prev"] = "f" * 64
    add(apart.CHAIN, "two faults: a broken link in an entry that holds a "
        "number with a fraction", log, {})

    # -- the table, entry by entry --
    log = _start()
    _raw(log, 0, "entered", None, {}, {"text": _print(0, "text", "t")})
    add(apart.UNTABLED, "a field the table does not name for this kind",
        log, {})
    log = _start()
    _raw(log, 0, "waved", None, {}, {"name": name_})
    add(apart.UNTABLED, "a kind the table does not name keeps a field apart",
        log, {})
    log = _start()
    _raw(log, 0, "entered", None, {"name": "ada"}, {"key": key})
    add(apart.OPEN, "a field the table keeps apart is in the open",
        log, {})
    log = _start()
    _raw(log, 0, "entered", None, {"name": "ada"},
         {"key": key, "name": name_})
    add(apart.OPEN, "a field both kept apart and in the open", log, {})

    # -- a fingerprint twice --
    log = _start()
    _raw(log, 0, "entered", None, {}, {"name": name_})
    _raw(log, 1, "entered", None, {}, {"name": name_})
    add(apart.TWICE, "the same salt, name and value in two entries",
        log, {})
    log = _start()
    _raw(log, 0, "entered", None, {}, {"key": key, "name": key})
    add(apart.TWICE, "one fingerprint under two names in one entry",
        log, {})

    # -- marks --
    said_by = {"office": OFFICE, "ground": PRIVATE}
    for name, data in [
            ("a mark that names no entry of the log",
             {"entry": "f" * 64, "field": "name"}),
            ("a mark on a field its entry does not keep apart",
             {"entry": None, "field": "text"}),
            ("a mark without a field", {"entry": None}),
            ("a mark whose field is a list",
             {"entry": None, "field": ["name"]}),
            ("a mark without an entry", {"field": "name"}),
            ("a mark whose entry is a number",
             {"entry": 1, "field": "name"})]:
        log, contents = _short()
        if "entry" in data and data["entry"] is None:
            data = {**data, "entry": log[1]["hash"]}
        _raw(log, 1, apart.MARK, None, {**data, **said_by}, {})
        add(apart.BAD_MARK, name, log, contents)
    log, contents = _short()
    _raw(log, 1, apart.MARK, None,
         {"entry": log[0]["hash"], "field": "form", **said_by}, {})
    add(apart.BAD_MARK, "a mark on a field that is in the open",
        log, contents)
    for name, change in [
            ("a mark without an office", {"office": None}),
            ("a mark whose office is empty", {"office": ""}),
            ("a mark whose office is a list", {"office": [OFFICE]}),
            ("a mark without a ground", {"ground": None}),
            ("a mark whose ground is text", {"ground": "it was private"}),
            ("a mark whose ground is of no known kind",
             {"ground": {"kind": "whim", "ref": "trial"}}),
            ("a mark whose ground names nothing",
             {"ground": {"kind": "rule", "ref": ""}}),
            ("a mark whose ground holds more than a kind and a ref",
             {"ground": {**PRIVATE, "more": "x"}}),
            ("a mark whose ground is a record not named by its hash",
             {"ground": {"kind": "record", "ref": "an earlier decision"}}),
            ("a mark whose ground's reference is one character too long",
             {"ground": {"kind": "rule",
                         "ref": "\U0001D11E" * (apart.MAX_REF + 1)}})]:
        log, contents = _short()
        data = {"entry": log[1]["hash"], "field": "name", **said_by, **change}
        _raw(log, 1, apart.MARK, None,
             {k: v for k, v in data.items() if v is not None}, {})
        add(apart.BAD_MARK, name, log, contents)

    # -- what answers a mark: kept public, or stays redacted --
    decided = {"office": KEEPER, "ground": APPEAL,
               "decision": trial_decision(1)}
    for kind, reason, what in [
            (apart.KEPT, apart.BAD_KEPT, "a decision to keep a field public"),
            (apart.STAYS, apart.BAD_STAYS,
             "a decision that a field stays redacted")]:
        log, contents = _short()
        _raw(log, 1, kind, None, {"mark": log[1]["hash"], **decided}, {})
        add(reason, what + " that names an entry that is not a mark",
            log, contents)
        log, contents = _short()
        _raw(log, 1, kind, None, dict(decided), {})
        add(reason, what + " that names nothing", log, contents)
        log, contents = _short()
        _raw(log, 1, kind, None, {"mark": "f" * 64, **decided}, {})
        add(reason, what + " that names no entry of the log", log, contents)
        log, contents = _short()
        _raw(log, 1, kind, None, {"mark": [log[1]["hash"]], **decided}, {})
        add(reason, what + " whose mark is a list", log, contents)

    # -- removing, restoring, taking back and putting back --
    def acted(*steps: Any) -> Tuple[List[dict], Any, Dict[str, str]]:
        """The trial room, with the steps that hold, as a raw log."""
        room = _room()
        made: Dict[str, str] = {}
        for name, step, *args in steps:
            made[name] = step(room, 5, *[made.get(a, a) if isinstance(a, str)
                                         else a for a in args])
        return (copy.deepcopy(room.entries), copy.deepcopy(room.contents),
                made)

    said = _room().entries[3]["hash"]
    removal = {"entry": said, "office": MODERATOR, "ground": GROUND,
               "decision": trial_decision(9)}

    def refuse(reason: str, name: str, kind: str, data: Any,
               *steps: Any) -> None:
        log, contents, made = acted(*steps)
        data = {k: made.get(v, v) if isinstance(v, str) else v
                for k, v in data.items()}
        _raw(log, 9, kind, None, data, {})
        add(reason, name, log, contents)

    # -- redacted first, decided after: one mark, one answer --
    marking = {"entry": said, "field": "text", "office": OFFICE,
               "ground": PRIVATE}
    refuse(apart.BAD_MARK, "a second mark on a field whose mark is open",
           apart.MARK, marking, ("m", _mark, said, "text", "asked"))
    refuse(apart.BAD_MARK, "a mark on a field whose redaction stands",
           apart.MARK, marking, ("m", _mark, said, "text", "asked"),
           ("s", _stays, "m", "it stays"))
    answer = {"mark": "m", "office": KEEPER, "ground": APPEAL,
              "decision": trial_decision(2)}
    for kind, reason, what in [
            (apart.KEPT, apart.BAD_KEPT, "a decision to keep a field public"),
            (apart.STAYS, apart.BAD_STAYS,
             "a decision that a field stays redacted")]:
        refuse(reason, what + " on a mark already answered by one to keep "
               "it public", kind, answer,
               ("m", _mark, said, "text", "asked"),
               ("k", _keep, "m", "nothing private"))
        refuse(reason, what + " on a mark that stands", kind, answer,
               ("m", _mark, said, "text", "asked"),
               ("s", _stays, "m", "it stays"))
        refuse(reason, what + " on an earlier mark of a field that was "
               "marked again", kind, answer,
               ("m", _mark, said, "text", "asked"),
               ("k", _keep, "m", "nothing private"),
               ("again", _mark, said, "text", "asked again"))
        for name, change in [
                ("without an office", {"office": None}),
                ("whose office is empty", {"office": ""}),
                ("without a ground", {"ground": None}),
                ("whose ground is a record not named by its hash",
                 {"ground": {"kind": "record", "ref": "an earlier one"}}),
                ("without a decision", {"decision": None}),
                ("whose decision is 63 digits",
                 {"decision": trial_decision(2)[:63]}),
                ("whose decision is in capitals",
                 {"decision": trial_decision(2).upper()})]:
            data = {k: v for k, v in {**answer, **change}.items()
                    if v is not None}
            refuse(reason, what + " " + name, kind, data,
                   ("m", _mark, said, "text", "asked"))

    refuse(apart.BAD_REMOVAL, "a removal that names no entry of the log",
           apart.REMOVED, {**removal, "entry": "f" * 64})
    refuse(apart.BAD_REMOVAL, "a removal whose entry is a number",
           apart.REMOVED, {**removal, "entry": 3})
    refuse(apart.BAD_REMOVAL, "a removal of a removal", apart.REMOVED,
           {**removal, "entry": "r"}, ("r", _remove, said, 1))
    refuse(apart.BAD_REMOVAL, "a removal of a taking back", apart.REMOVED,
           {**removal, "entry": "t"}, ("t", _take_back, said))
    refuse(apart.BAD_REMOVAL, "a second removal of a removed entry",
           apart.REMOVED, removal, ("r", _remove, said, 1))
    refuse(apart.BAD_REMOVAL, "a removal of an entry its author took back",
           apart.REMOVED, removal, ("t", _take_back, said))
    for name, change in [
            ("a removal without an office", {"office": None}),
            ("a removal whose office is empty", {"office": ""}),
            ("a removal without a ground", {"ground": None}),
            ("a removal whose ground is text", {"ground": "the law"}),
            ("a removal whose ground is of no known kind",
             {"ground": {"kind": "whim", "ref": "trial"}}),
            ("a removal whose ground names nothing",
             {"ground": {"kind": "law", "ref": ""}}),
            ("a removal whose ground holds more than a kind and a ref",
             {"ground": {**GROUND, "more": "x"}}),
            ("a removal whose ground is a record not named by its hash",
             {"ground": {"kind": "record", "ref": "an earlier decision"}}),
            ("a removal whose ground's reference is one character too long",
             {"ground": {"kind": "law",
                         "ref": "\U0001D11E" * (apart.MAX_REF + 1)}}),
            ("a removal without a decision", {"decision": None}),
            ("a removal whose decision is 63 digits",
             {"decision": trial_decision(9)[:63]})]:
        data = {k: v for k, v in {**removal, **change}.items()
                if v is not None}
        refuse(apart.BAD_REMOVAL, name, apart.REMOVED, data)

    restoring = {"incident": "r", "office": KEEPER, "ground": GROUND,
                 "decision": trial_decision(8)}
    refuse(apart.BAD_RESTORING, "a restoring of an entry that is not removed",
           apart.RESTORED, {**restoring, "incident": said})
    refuse(apart.BAD_RESTORING, "a restoring that names no entry of the log",
           apart.RESTORED, {**restoring, "incident": "f" * 64})
    refuse(apart.BAD_RESTORING, "a restoring of a removal already restored",
           apart.RESTORED, restoring, ("r", _remove, said, 1),
           ("back", _restore, "r", 2))
    refuse(apart.BAD_RESTORING, "a restoring of an earlier removal, "
           "already restored, of an entry that is removed again",
           apart.RESTORED, restoring, ("r", _remove, said, 1),
           ("back", _restore, "r", 2), ("again", _remove, said, 3))
    refuse(apart.BAD_RESTORING, "a restoring of a taking back",
           apart.RESTORED, {**restoring, "incident": "t"},
           ("t", _take_back, said))
    refuse(apart.BAD_RESTORING, "a restoring without an office",
           apart.RESTORED, {k: v for k, v in restoring.items()
                            if k != "office"}, ("r", _remove, said, 1))
    refuse(apart.BAD_RESTORING, "a restoring whose incident is a list",
           apart.RESTORED, {**restoring, "incident": ["r"]},
           ("r", _remove, said, 1))

    refuse(apart.BAD_TAKING_BACK, "a taking back that names no entry of the "
           "log", apart.TAKEN_BACK, {"entry": "f" * 64})
    refuse(apart.BAD_TAKING_BACK, "a taking back that names nothing",
           apart.TAKEN_BACK, {})
    refuse(apart.BAD_TAKING_BACK, "a second taking back", apart.TAKEN_BACK,
           {"entry": said}, ("t", _take_back, said))
    refuse(apart.BAD_TAKING_BACK, "a taking back of a removal",
           apart.TAKEN_BACK, {"entry": "r"}, ("r", _remove, said, 1))
    refuse(apart.BAD_TAKING_BACK, "a taking back of a mark",
           apart.TAKEN_BACK, {"entry": "m"},
           ("m", _mark, said, "text", "asked"))
    refuse(apart.BAD_REMOVAL, "a removal of a decision that a field stays "
           "redacted", apart.REMOVED, {**removal, "entry": "s"},
           ("m", _mark, said, "text", "asked"),
           ("s", _stays, "m", "it stays"))

    refuse(apart.BAD_PUTTING_BACK, "a putting back of an entry that was not "
           "taken back", apart.PUT_BACK, {"taken_back": said})
    refuse(apart.BAD_PUTTING_BACK, "a putting back of a removal",
           apart.PUT_BACK, {"taken_back": "r"}, ("r", _remove, said, 1))
    refuse(apart.BAD_PUTTING_BACK, "a putting back of a taking back already "
           "put back", apart.PUT_BACK, {"taken_back": "t"},
           ("t", _take_back, said), ("p", _put_back, "t"))
    refuse(apart.BAD_PUTTING_BACK, "a putting back of an earlier taking "
           "back, already put back, when a new one stands",
           apart.PUT_BACK, {"taken_back": "t"}, ("t", _take_back, said),
           ("p", _put_back, "t"), ("again", _take_back, said))
    refuse(apart.BAD_PUTTING_BACK, "a putting back that names nothing",
           apart.PUT_BACK, {}, ("t", _take_back, said))

    # -- the contents' shape --
    log, contents = _short()
    arrival = log[1]["hash"]
    add(apart.CONTENTS, "the contents are a list", log, [contents])
    add(apart.CONTENTS, "an entry's fields are a list", log,
        {arrival: [contents[arrival]["name"]]})
    add(apart.CONTENTS, "a field given as three things", log,
        {arrival: {"name": contents[arrival]["name"] + ["more"]}})
    add(apart.CONTENTS, "a field given as one thing", log,
        {arrival: {"name": contents[arrival]["name"][:1]}})
    add(apart.CONTENTS, "a field given as a map", log,
        {arrival: {"name": {"salt": contents[arrival]["name"][0],
                            "value": contents[arrival]["name"][1]}}})

    # -- contents the log does not commit to --
    add(apart.UNKNOWN, "an entry the log does not hold", log,
        {**contents, "f" * 64: {"name": [trial_salt(9), "eve"]}})
    add(apart.UNKNOWN, "a field the entry does not keep apart", log,
        {arrival: {**contents[arrival], "text": [trial_salt(9), "hello"]}})
    add(apart.UNKNOWN, "a field of an entry that keeps nothing apart", log,
        {**contents, log[0]["hash"]: {"form": [trial_salt(9), apart.FORM]}})

    # -- salts --
    salt, value = contents[arrival]["name"]
    for name, bad in [("a salt of 31 digits", salt[:31]),
                      ("a salt of 33 digits", salt + "0"),
                      ("a salt in capitals", salt.upper()),
                      ("a salt that is a number", 7),
                      ("a salt that is not hex", "g" * 32)]:
        add(apart.SALT, name, log, {arrival: {"name": [bad, value]}})
    log = _start()
    _raw(log, 0, "entered", None, {},
         {"key": _print(0, "key", "k"), "name": _print(0, "name", "n")})
    add(apart.SALT_TWICE, "one salt for two fields of an entry", log,
        {log[1]["hash"]: {"key": [trial_salt(0), "k"],
                          "name": [trial_salt(0), "n"]}})
    log = _start()
    _raw(log, 0, "entered", None, {}, {"name": _print(0, "name", "n")})
    _raw(log, 1, "entered", None, {}, {"name": _print(0, "name", "m")})
    add(apart.SALT_TWICE, "one salt in two entries", log,
        {log[1]["hash"]: {"name": [trial_salt(0), "n"]},
         log[2]["hash"]: {"name": [trial_salt(0), "m"]}})

    # -- values --
    for name, bad in VALUES_REFUSED:
        log = _start()
        # The value has no fingerprint, so the entry holds one of
        # something else: the value is refused before it is compared.
        _raw(log, 0, "entered", None, {}, {"name": name_})
        add(apart.VALUE, name, log,
            {log[1]["hash"]: {"name": [trial_salt(1), bad]}})

    # -- contents that do not match --
    log, contents = _short()
    salt, value = contents[arrival]["name"]
    add(apart.FINGERPRINT, "the value was changed", log,
        {arrival: {"name": [salt, value + "!"]}})
    add(apart.FINGERPRINT, "the salt was changed", log,
        {arrival: {"name": [trial_salt(9), value]}})
    add(apart.FINGERPRINT, "two fields' contents the wrong way round", log,
        {arrival: {"name": contents[arrival]["key"],
                   "key": contents[arrival]["name"]}})
    room = _room()
    one, two = room.entries[1]["hash"], room.entries[2]["hash"]
    swapped = copy.deepcopy(room.contents)
    swapped[one]["name"], swapped[two]["name"] = (
        swapped[two]["name"], swapped[one]["name"])
    add(apart.FINGERPRINT, "another entry's contents", room.entries, swapped)
    add(apart.FINGERPRINT, "text where the log has a number", room.entries,
        {room.entries[3]["hash"]: {
            "time": [room.contents[room.entries[3]["hash"]]["time"][0],
                     "1794787200"]}})

    # -- two faults in the contents: entries are read in ascending order
    # of their hashes, and an entry's fields in ascending order of their
    # names, so the first met is the one named --
    low, high = sorted([one, two])

    def changed(entry: str, field: str) -> list:
        salt, value = room.contents[entry][field]
        return [salt, value + "!"]

    def capitals(entry: str, field: str) -> list:
        salt, value = room.contents[entry][field]
        return [salt.upper(), value]

    add(apart.FINGERPRINT, "two faults: a changed value in the lower "
        "entry, a salt in capitals in the higher", room.entries,
        {low: {"name": changed(low, "name")},
         high: {"name": capitals(high, "name")}})
    add(apart.SALT, "two faults: a salt in capitals in the lower entry, "
        "a changed value in the higher", room.entries,
        {low: {"name": capitals(low, "name")},
         high: {"name": changed(high, "name")}})
    add(apart.FINGERPRINT, "two faults in one entry: a changed key, a "
        "name's salt in capitals", room.entries,
        {one: {"key": changed(one, "key"),
               "name": capitals(one, "name")}})
    add(apart.SALT, "two faults in one entry: a key's salt in capitals, "
        "a changed name", room.entries,
        {one: {"key": capitals(one, "key"),
               "name": changed(one, "name")}})
    return cases


def _nested(depth: int) -> Any:
    value: Any = "deep"
    for _ in range(depth):
        value = [value]
    return value


# Values a fingerprint allows, at their edges.
VALUES_ALLOWED: List[Any] = [
    "", "plain text", "café 中文 \U0001F642   \U0010FFFF",
    'quote " backslash \\ tab \t newline \n', "\x00\x1f\x7f",
    0, 1, -1, apart.MAX_WHOLE, -apart.MAX_WHOLE, True, False,
    [], {}, ["a", 1, True, [], {}],
    {"b": 1, "a": 2, "B": 3, "_": 4, "é": 5, "aa": 6, "a b": 7},
    {"words": ["a", "b"], "loud": True, "count": -3},
    _nested(apart.MAX_NESTING),
]

# Values it refuses, as far as a JSON file can hold them.
VALUES_REFUSED: List[Tuple[str, Any]] = [
    ("a number with a fraction", 1.5),
    ("a whole number written with a fraction", 1.0),
    ("nothing", None),
    ("two to the 53", apart.MAX_WHOLE + 1),
    ("minus two to the 53", -apart.MAX_WHOLE - 1),
    ("two to the 64", 2 ** 64),
    ("a list holding nothing", ["a", None]),
    ("a map holding a number with a fraction", {"a": 0.5}),
    ("a list nested one too deep", _nested(apart.MAX_NESTING + 1)),
]


def fingerprints() -> List[dict]:
    """Each allowed value under a trial salt: the exact text that is
    hashed, and the fingerprint."""
    return [{"salt": trial_salt(n), "name": "thing", "value": value,
             "text": apart.fingerprint_text(trial_salt(n), "thing", value),
             "fingerprint": apart.fingerprint(trial_salt(n), "thing", value)}
            for n, value in enumerate(VALUES_ALLOWED)]


def _id(start: str, n: int) -> str:
    """A made-up incident id: `start`, then filled out to 64 hex digits."""
    fill = hashlib.sha256(f"open-worlds trial id {n}".encode()).hexdigest()
    return (start + fill)[:64]


def short_ids() -> List[dict]:
    """Made-up incident ids that begin alike, and each as it is shown.
    Real ids that begin alike for twelve digits can't be made here: it
    would take about 2^48 hashes."""
    groups = [
        [_id("", 1), _id("", 2), _id("", 3)],
        [_id("abcdef012345", 1), _id("abcdef012345", 2)],
        [_id("abcdef0123456789ab", 1), _id("abcdef0123456789ab", 2),
         _id("abcdef012345", 3), _id("0123", 4)],
        [_id("f" * 63, 1), ("f" * 63 + "0") if not _id("f" * 63, 1).endswith(
            "0") else ("f" * 63 + "1")],
        [],
    ]
    return [{"ids": ids, "short": apart._short_ids(ids)} for ids in groups]


def log_apart() -> dict:
    """Everything in `vectors/log-apart.json`."""
    return {
        "note": ("Trial vectors for open-worlds/log-apart/v1. The salts "
                 "are fixed and public: salt n is the first 32 hex digits "
                 "of the SHA-256 of 'open-worlds trial salt n'. Never for "
                 "anything real."),
        "form": apart.FORM,
        "mark": apart.MARK,
        "kept": apart.KEPT,
        "stays": apart.STAYS,
        "redaction_states": list(apart.REDACTION_STATES),
        "removed": apart.REMOVED,
        "restored": apart.RESTORED,
        "taken_back": apart.TAKEN_BACK,
        "put_back": apart.PUT_BACK,
        "grounds": list(apart.GROUNDS),
        "entry_states": list(apart.ENTRY_STATES),
        "short": apart.SHORT,
        "short_ids": short_ids(),
        "max_whole": apart.MAX_WHOLE,
        "max_nesting": apart.MAX_NESTING,
        "max_ref": apart.MAX_REF,
        "states": list(apart.STATES),
        "reasons": list(apart.REASONS),
        "table": TABLE,
        "first": FIRST,
        "written": [{"tick": tick, "kind": kind, "agent": agent,
                     "data": data, "apart": kept}
                    for tick, kind, agent, data, kept in WRITTEN],
        "fingerprints": fingerprints(),
        "values_refused": [{"name": name, "value": value}
                           for name, value in VALUES_REFUSED],
        "holds": holds(),
        "refused": refused(),
    }
