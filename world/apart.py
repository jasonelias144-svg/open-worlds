"""A log whose fields are kept apart from the chain that commits to them
(course step 3b, part two; docs/research/REDACTION.md).

In the kernel's log (`world/core.py`) an entry's `data` is hashed whole,
so nothing can ever be taken out of it. In this form an entry holds,
for each field its world keeps apart, only a fingerprint; what the field
says is kept beside the log, in the contents. Taking a field out of the
contents leaves the log exactly as it was, and the chain still checks.

- **The form's name** is `open-worlds/log-apart/v1`. A log names it in
  its first entry (`data.form`), since a fingerprint can't be told from
  any other 64 hex digits. The first entry also holds the table
  (`data.kept_apart`): for each kind of entry, the names of the fields
  kept apart, in ascending order. The kernel's own form is unchanged,
  and worlds no one acts in keep it.
- **An entry** holds `tick`, `kind`, `agent`, `data`, `prev` and `hash`
  as the kernel's does, and `apart`: a map from a field's name to its
  fingerprint. It holds these seven and nothing else, so nothing sits
  beside `data` where the table doesn't reach. A field the table keeps
  apart for an entry's kind is never in its `data`: it is in `apart`,
  or not there at all. The hash covers `apart` like everything else, so
  the chain of a log in this form holds by the kernel's own
  `World.verify_log`, unchanged.
- **The open part is held to the same rule as a value kept apart.**
  `tick` is a whole number from 0 to 2^53 - 1, `kind` is text, `agent`
  is text or nothing, and `data` is a map a fingerprint would allow: no
  number with a fraction, no whole number beyond 2^53 - 1, nothing
  nested deeper than `MAX_NESTING`, every key text. So every log in
  this form can be written, and checked, in both languages.
- **A fingerprint** is the SHA-256, in lowercase hex, of the list
  `[salt, name, value]` written as the log writes everything
  (`json.dumps(..., sort_keys=True, separators=(",", ":"))`). The salt
  is 128 bits from the operating system, as 32 lowercase hex digits,
  fresh for each field of each entry. A value is text, a whole number
  from -(2^53 - 1) to 2^53 - 1, true or false, or a list or map of
  these nested at most `MAX_NESTING` deep; nothing else, so that Python
  never writes what Rust would refuse. No fingerprint may appear twice
  in a log.
- **The contents** are a map from an entry's hash to a map from a
  field's name to `[salt, value]`. They hold nothing the log doesn't
  commit to.
- **Two kinds of entry are the form's own.** A mark, kind
  `field_redacted`, names in the open an earlier entry by its hash
  (`data.entry`) and a field that entry keeps apart (`data.field`). A
  decision to keep a field public, kind `field_kept_public`, names an
  earlier mark by its hash (`data.mark`), and that mark then no longer
  stands. What else these entries say, and the act of redacting, are
  part three's.
- **Four more kinds are the form's own,** for what a room shows
  (docs/research/REDACTION.md, decisions 7 to 9). A removal, kind
  `entry_removed`, names in the open an earlier entry (`data.entry`),
  the office that acted (`data.office`), the ground it rests on
  (`data.ground`, a `kind` and a `ref`, as a decision record's grounds
  have) and the hash of its decision record (`data.decision`). A
  restoring, `entry_restored`, names a removal that stands
  (`data.incident`), with its office, ground and decision. A taking
  back, `entry_taken_back`, is the author's own: it names the entry
  (`data.entry`). A putting back, `entry_put_back`, undoes a taking
  back that stands (`data.taken_back`). None of them takes anything out
  of the log or the contents: they change what is shown. The signed
  records they carry are kept apart, like anything else a person
  gives, and are checked against these open fields elsewhere.
- **The state of an entry** is worked out from the open fields alone,
  never stored: `taken back` if a taking back of it stands; else
  `removed` if a removal of it stands; else `restored` if it was ever
  removed; else `as written`. What wins: an office can't remove what is
  already removed, or what its author took back; it can't restore what
  isn't removed, or what its author took back; an author can take back
  what an office removed, and it then stays hidden whatever the office
  does; a removal after a restoring is a new incident. An incident's id
  is the hash of the entry that carries the removal or the taking
  back, shown as the fewest hex digits, twelve or more, that no other
  incident in the log begins with.
- **The state of a field**, from the log and the contents together:
  `present`; `redacted` (a mark stands, and the field is gone);
  `unfinished` (a mark stands, and the field is still there); `kept
  public` (every mark on it was answered by a decision to keep it
  public, and it is there); `missing` (no mark stands, and it is gone:
  a fault in whoever published the log).

`check` holds the contents to the log and gives every field's state.
`incidents` gives every entry's state, with its incidents. `join`
gives each entry as a reader uses it. `Log` writes the form.
Every reason for refusing is in fixed words, and names the same place,
in Rust (`rust/world-log/src/apart.rs`), checked against
`vectors/log-apart.json`.

The order of the checks is part of the form, so that a log or contents
with two faults is refused for the same one in both languages. Entries
are read in the log's order; for each, its link to the entry before
(`prev`), then what it says, then its hash. The contents are read in
ascending order of entry hash, and of field name within an entry.

Limits. A field under a standing mark is never shown by `join`, even
while it is still in the contents. An entry that is removed or taken
back is still given whole by `join`, with its state: nothing has left
the record, and hiding it is for whatever shows a room. This module
does not check who may remove, restore or take back: that needs the
signed records and the keys, which are kept apart. Nothing can be the
value of an open field: a field with no value is left out. The check holds a world to its table
by name: it can't know that an open field of another name holds what
should have been kept apart. A fingerprint commits a log to a value,
and says nothing of who wrote it: that is a signature's work. JSON's
`-0` is read by Python as 0 and refused by Rust; nothing here writes
it. A file that isn't JSON as the standard has it (`NaN`, a number too
large to read, half of a surrogate pair) is refused here and can't be
read at all by Rust.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import secrets
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .core import GENESIS, _digest, _is_unicode

FORM = "open-worlds/log-apart/v1"
MARK = "field_redacted"
KEPT = "field_kept_public"

REMOVED = "entry_removed"
RESTORED = "entry_restored"
TAKEN_BACK = "entry_taken_back"
PUT_BACK = "entry_put_back"
# The form's own kinds: none of them can itself be removed or taken back.
OWN = (MARK, KEPT, REMOVED, RESTORED, TAKEN_BACK, PUT_BACK)
# What a ground can be, as in a decision record's grounds.
GROUNDS = ("charter", "law", "rule", "record")

MAX_WHOLE = 2 ** 53 - 1
MAX_NESTING = 32
# The longest a ground's reference can be, in characters (code points),
# as in a decision record's grounds (schemas/records-v1.schema.json).
MAX_REF = 512

PRESENT = "present"
REDACTED = "redacted"
UNFINISHED = "unfinished"
KEPT_PUBLIC = "kept public"
MISSING = "missing"
STATES = (PRESENT, REDACTED, UNFINISHED, KEPT_PUBLIC, MISSING)

AS_WRITTEN = "as written"
IS_REMOVED = "removed"
IS_TAKEN_BACK = "taken back"
IS_RESTORED = "restored"
ENTRY_STATES = (AS_WRITTEN, IS_REMOVED, IS_TAKEN_BACK, IS_RESTORED)
# The shortest an incident's id is ever shown.
SHORT = 12

CHAIN = "the chain does not hold"
NO_FORM = "the first entry does not name this form"
TABLE = "the table of fields kept apart is not well formed"
ENTRY = "an entry is not in this form"
UNTABLED = "a field is kept apart that the table does not name"
OPEN = "a field the table keeps apart is in the open"
TWICE = "a fingerprint appears twice"
BAD_MARK = "a mark does not name an earlier entry and a field it keeps apart"
BAD_KEPT = "a decision to keep a field public does not name an earlier mark"
BAD_REMOVAL = ("a removal does not name an earlier entry that can be "
               "removed, with its office, ground and decision")
BAD_RESTORING = ("a restoring does not name a removal that stands, with "
                 "its office, ground and decision")
BAD_TAKING_BACK = ("a taking back does not name an earlier entry that can "
                   "be taken back")
BAD_PUTTING_BACK = "a putting back does not name a taking back that stands"
CONTENTS = "the contents are not well formed"
UNKNOWN = "the contents name an entry or a field the log does not keep apart"
SALT = "a salt is not 32 lowercase hex digits"
SALT_TWICE = "a salt appears twice"
VALUE = "a value is not one a fingerprint allows"
FINGERPRINT = "the contents do not match the fingerprint"
REASONS = (CHAIN, NO_FORM, TABLE, ENTRY, UNTABLED, OPEN, TWICE, BAD_MARK,
           BAD_KEPT, BAD_REMOVAL, BAD_RESTORING, BAD_TAKING_BACK,
           BAD_PUTTING_BACK, CONTENTS, UNKNOWN, SALT, SALT_TWICE, VALUE,
           FINGERPRINT)

KEYS = frozenset(("tick", "kind", "agent", "data", "apart", "prev", "hash"))

_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}")
_SALT = re.compile(r"[0-9a-f]{32}")
_HASH = re.compile(r"[0-9a-f]{64}")


class Refused(Exception):
    """Why a log in this form, or its contents, does not hold. `reason`
    is one of `REASONS`; `where` says which entry (its place in the log,
    from 0) or which part of the contents, when there is one."""

    def __init__(self, reason: str, where: object = None):
        super().__init__(reason if where is None else f"{reason}: {where}")
        self.reason = reason
        self.where = where


def new_salt() -> str:
    """A fresh salt: 128 bits from the operating system's random source,
    as 32 lowercase hex digits. Never made from a world's seed."""
    return secrets.token_hex(16)


def _is_name(name: object) -> bool:
    return type(name) is str and _NAME.fullmatch(name) is not None


def _is_salt(salt: object) -> bool:
    return type(salt) is str and _SALT.fullmatch(salt) is not None


def _is_hash(text: object) -> bool:
    return type(text) is str and _HASH.fullmatch(text) is not None


def value_allowed(value: object, _depth: int = 0) -> bool:
    """True if `value` may be kept apart: text, a whole number from
    -(2^53 - 1) to 2^53 - 1, true or false, or a list or map of these,
    nested at most `MAX_NESTING` deep. Types are compared exactly, so
    nothing that only looks like one of these gets through."""
    t = type(value)
    if t is str:
        return _is_unicode(value)
    if t is bool:
        return True
    if t is int:
        return -MAX_WHOLE <= value <= MAX_WHOLE
    if t is list:
        return _depth < MAX_NESTING and all(
            value_allowed(v, _depth + 1) for v in value)
    if t is dict:
        return _depth < MAX_NESTING and all(
            type(k) is str and _is_unicode(k) and value_allowed(v, _depth + 1)
            for k, v in value.items())
    return False


def _open_ok(tick: object, kind: object, agent: object,
             data: object) -> bool:
    """True if an entry's open part is as the form has it: a tick from
    0 to 2^53 - 1, a kind that is text, an agent that is text or
    nothing, and data that is a map a fingerprint would allow."""
    return (type(tick) is int and 0 <= tick <= MAX_WHOLE
            and type(kind) is str and _is_unicode(kind)
            and (agent is None
                 or (type(agent) is str and _is_unicode(agent)))
            and type(data) is dict and value_allowed(data))


def fingerprint_text(salt: str, name: str, value: object) -> str:
    """The exact text a fingerprint is the hash of."""
    if not _is_salt(salt):
        raise Refused(SALT)
    if not _is_name(name):
        raise Refused(ENTRY)
    if not value_allowed(value):
        raise Refused(VALUE)
    return json.dumps([salt, name, value], sort_keys=True,
                      separators=(",", ":"))


def fingerprint(salt: str, name: str, value: object) -> str:
    """The fingerprint of one field: the SHA-256, in lowercase hex, of
    `[salt, name, value]` as the log writes it."""
    text = fingerprint_text(salt, name, value)
    return hashlib.sha256(text.encode()).hexdigest()


def _table_ok(table: object) -> bool:
    if type(table) is not dict:
        return False
    for kind, names in table.items():
        if type(kind) is not str or type(names) is not list:
            return False
        if not all(_is_name(n) for n in names):
            return False
        if any(a >= b for a, b in zip(names, names[1:])):
            return False
    return True


def _office_ok(data: dict) -> bool:
    """True if an office's act says, in the open, which office acted,
    the ground it rests on, and the hash of its decision record."""
    ground = data.get("ground")
    return (type(data.get("office")) is str and data["office"] != ""
            and type(ground) is dict and set(ground) == {"kind", "ref"}
            and ground["kind"] in GROUNDS
            and type(ground["ref"]) is str
            and 0 < len(ground["ref"]) <= MAX_REF
            and _is_hash(data.get("decision")))


class _Scan:
    """Reads a log's entries in order, keeping what later entries and
    the contents are checked against. `take` changes nothing unless the
    entry holds, so a writer can offer it an entry and keep going if it
    is refused. It is given a map whose `hash` is text: its two callers
    see to that, and to the chain."""

    def __init__(self) -> None:
        self.table: Dict[str, List[str]] = {}
        self.apart: Dict[str, Dict[str, str]] = {}   # entry -> name -> print
        self.marks: Dict[str, Tuple[str, str]] = {}  # mark -> (entry, name)
        self.answered: Set[str] = set()              # marks no longer standing
        self.seen: Set[str] = set()                  # every fingerprint
        self.kinds: Dict[str, str] = {}              # entry -> its kind
        # Every removal and taking back, in the log's order:
        # (the incident's entry, the entry it is on, which of the two).
        self.incidents: List[Tuple[str, str, str]] = []
        self.removals: Dict[str, str] = {}           # removal -> entry
        self.takings: Dict[str, str] = {}            # taking back -> entry
        self.removed: Dict[str, str] = {}   # entry -> removal that stands
        self.taken: Dict[str, str] = {}     # entry -> taking back that stands
        self.count = 0

    def _can_be_acted_on(self, target: object) -> bool:
        """True for an earlier entry that is not one of the form's own."""
        return (type(target) is str and target in self.kinds
                and self.kinds[target] not in OWN)

    def take(self, entry: Any) -> None:
        index = self.count
        if not isinstance(entry, dict):
            raise Refused(ENTRY, index)
        kind, data, apart = (entry.get("kind"), entry.get("data"),
                             entry.get("apart"))
        table = self.table
        if index == 0:
            if type(data) is not dict or data.get("form") != FORM:
                raise Refused(NO_FORM)
            table = data.get("kept_apart")
            if not _table_ok(table):
                raise Refused(TABLE)
        if (set(entry) != KEYS
                or not _open_ok(entry["tick"], kind, entry["agent"], data)
                or type(apart) is not dict
                or not all(_is_name(n) and _is_hash(p)
                           for n, p in apart.items())):
            raise Refused(ENTRY, index)
        named = table.get(kind, [])
        if any(name not in named for name in apart):
            raise Refused(UNTABLED, index)
        if any(name in data for name in named):
            raise Refused(OPEN, index)
        prints = [apart[name] for name in sorted(apart)]
        if len(set(prints)) != len(prints) or self.seen.intersection(prints):
            raise Refused(TWICE, index)
        mark: Optional[Tuple[str, str]] = None
        answers: Optional[str] = None
        if kind == MARK:
            target, field = data.get("entry"), data.get("field")
            if (type(target) is not str or type(field) is not str
                    or field not in self.apart.get(target, {})):
                raise Refused(BAD_MARK, index)
            mark = (target, field)
        elif kind == KEPT:
            answers = data.get("mark")
            if type(answers) is not str or answers not in self.marks:
                raise Refused(BAD_KEPT, index)
        # What wins, among removing, restoring, taking back and putting
        # back (docs/research/REDACTION.md, decision 9).
        on: Optional[str] = None
        if kind == REMOVED:
            on = data.get("entry")
            if (not self._can_be_acted_on(on) or on in self.removed
                    or on in self.taken or not _office_ok(data)):
                raise Refused(BAD_REMOVAL, index)
        elif kind == RESTORED:
            incident = data.get("incident")
            on = self.removals.get(incident) if type(incident) is str else None
            if (on is None or self.removed.get(on) != incident
                    or on in self.taken or not _office_ok(data)):
                raise Refused(BAD_RESTORING, index)
        elif kind == TAKEN_BACK:
            on = data.get("entry")
            if not self._can_be_acted_on(on) or on in self.taken:
                raise Refused(BAD_TAKING_BACK, index)
        elif kind == PUT_BACK:
            taking = data.get("taken_back")
            on = self.takings.get(taking) if type(taking) is str else None
            if on is None or self.taken.get(on) != taking:
                raise Refused(BAD_PUTTING_BACK, index)
        # The entry holds: only now is anything kept.
        here = entry["hash"]
        self.table = table
        self.apart[here] = dict(apart)
        self.kinds[here] = kind
        self.seen.update(prints)
        if mark is not None:
            self.marks[here] = mark
        if answers is not None:
            self.answered.add(answers)
        if kind == REMOVED:
            self.removals[here] = on
            self.removed[on] = here
            self.incidents.append((here, on, IS_REMOVED))
        elif kind == RESTORED:
            del self.removed[on]
        elif kind == TAKEN_BACK:
            self.takings[here] = on
            self.taken[on] = here
            self.incidents.append((here, on, IS_TAKEN_BACK))
        elif kind == PUT_BACK:
            del self.taken[on]
        self.count += 1


def _scan(log: Any) -> _Scan:
    """Reads a whole log. For each entry in turn: its link to the entry
    before, then what it says, then its hash. The chain is the kernel's
    (a log that passes here passes `World.verify_log`); the checks are
    taken an entry at a time so that the first fault in the log's order
    is the one named, in Python and in Rust, and so that Rust is never
    asked to hash an entry it could not write."""
    if not isinstance(log, list):
        raise Refused(CHAIN)
    if not log:
        raise Refused(NO_FORM)
    scan = _Scan()
    prev = GENESIS
    for index, entry in enumerate(log):
        if (not isinstance(entry, dict)
                or type(entry.get("hash")) is not str
                or entry.get("prev") != prev):
            raise Refused(CHAIN, index)
        scan.take(entry)
        body = {k: v for k, v in entry.items() if k != "hash"}
        if _digest(body) != entry["hash"]:
            raise Refused(CHAIN, index)
        prev = entry["hash"]
    return scan


def _held(scan: _Scan, contents: Any) -> Dict[str, Dict[str, Any]]:
    """The contents, held to the log: for each entry, each field's value
    that is there and matches its fingerprint."""
    if type(contents) is not dict:
        raise Refused(CONTENTS)
    held: Dict[str, Dict[str, Any]] = {}
    salts: Set[str] = set()
    # Only Python can hold a key that isn't text; JSON can't.
    if not all(type(entry) is str for entry in contents):
        raise Refused(CONTENTS)
    for entry in sorted(contents):
        if entry not in scan.apart:
            raise Refused(UNKNOWN, entry)
        fields = contents[entry]
        if type(fields) is not dict or not all(
                type(name) is str for name in fields):
            raise Refused(CONTENTS, entry)
        held[entry] = {}
        for name in sorted(fields):
            where = (entry, name)
            if name not in scan.apart[entry]:
                raise Refused(UNKNOWN, where)
            pair = fields[name]
            if type(pair) is not list or len(pair) != 2:
                raise Refused(CONTENTS, where)
            salt, value = pair
            if not _is_salt(salt):
                raise Refused(SALT, where)
            if not value_allowed(value):
                raise Refused(VALUE, where)
            if fingerprint(salt, name, value) != scan.apart[entry][name]:
                raise Refused(FINGERPRINT, where)
            # Only once both match: so this always means a salt that was
            # truly used for two fields, never a field copied elsewhere.
            if salt in salts:
                raise Refused(SALT_TWICE, where)
            salts.add(salt)
            held[entry][name] = value
    return held


def _states(scan: _Scan,
            held: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    marked = set(scan.marks.values())
    standing = {field for mark, field in scan.marks.items()
                if mark not in scan.answered}
    states: Dict[str, Dict[str, str]] = {}
    for entry, apart in scan.apart.items():
        for name in sorted(apart):
            there = name in held.get(entry, {})
            if (entry, name) in standing:
                state = UNFINISHED if there else REDACTED
            elif there:
                state = KEPT_PUBLIC if (entry, name) in marked else PRESENT
            else:
                state = MISSING
            states.setdefault(entry, {})[name] = state
    return states


def _short_ids(ids: List[str]) -> Dict[str, str]:
    """Each incident's id as it is shown: the fewest hex digits, `SHORT`
    or more, that no other incident in the log begins with."""
    short = {}
    for one in ids:
        n = SHORT
        while any(other != one and other.startswith(one[:n])
                  for other in ids):
            n += 1
        short[one] = one[:n]
    return short


def _entry_states(scan: _Scan) -> Dict[str, dict]:
    """The state of every entry that has an incident, with them."""
    short = _short_ids([incident for incident, _, _ in scan.incidents])
    states: Dict[str, dict] = {}
    for incident, on, which in scan.incidents:
        stands = (scan.removed.get(on) == incident
                  or scan.taken.get(on) == incident)
        states.setdefault(on, {"state": AS_WRITTEN, "incidents": []})
        states[on]["incidents"].append(
            {"id": incident, "short": short[incident], "kind": which,
             "stands": stands})
    for on, state in states.items():
        if on in scan.taken:
            state["state"] = IS_TAKEN_BACK
        elif on in scan.removed:
            state["state"] = IS_REMOVED
        elif any(i["kind"] == IS_REMOVED for i in state["incidents"]):
            state["state"] = IS_RESTORED
    return states


def incidents(log: Any) -> Dict[str, dict]:
    """Checks a log in this form and gives the state of every entry
    that was ever removed or taken back: a map from the entry's hash to
    its `state` (one of `ENTRY_STATES`) and its `incidents`, in the
    log's order, each with its `id` (the hash of the entry that carries
    it), its `short` id as shown, its `kind` (`removed` or `taken
    back`), and whether it `stands`. Every other entry is `as written`.
    It needs no contents: what is shown is worked out from the open
    fields alone."""
    return _entry_states(_scan(log))


def check(log: Any, contents: Any) -> Dict[str, Dict[str, str]]:
    """Checks a log in this form and its contents together, and gives
    the state of every field kept apart: a map from an entry's hash to a
    map from a field's name to one of `STATES`. Entries that keep
    nothing apart are left out. Raises `Refused` with the reason if the
    chain doesn't hold, the log isn't in this form, or the contents
    hold anything the log doesn't commit to.

    A missing field is not refused: it is a state, so that a reader can
    say which fields a copy of a log has lost."""
    scan = _scan(log)
    return _states(scan, _held(scan, contents))


def join(log: Any, contents: Any) -> List[dict]:
    """Each entry as a reader uses it, after `check`: the entry without
    its `apart`, its `data` holding the open fields and every field kept
    apart that is `present` or `kept public`, `fields` giving the state
    of each field kept apart, and the entry's own `state` and
    `incidents` (as `incidents` gives them; `as written` and none, for
    most). A field under a standing mark is left out even if it is
    still in the contents. An entry that is removed or taken back is
    given whole: hiding it is for whatever shows the room."""
    scan = _scan(log)
    held = _held(scan, contents)
    states = _states(scan, held)
    acted_on = _entry_states(scan)
    joined = []
    for entry in log:
        fields = states.get(entry["hash"], {})
        one = {k: copy.deepcopy(v) for k, v in entry.items() if k != "apart"}
        for name, state in fields.items():
            if state in (PRESENT, KEPT_PUBLIC):
                one["data"][name] = copy.deepcopy(held[entry["hash"]][name])
        one["fields"] = dict(fields)
        its = acted_on.get(entry["hash"], {})
        one["state"] = its.get("state", AS_WRITTEN)
        one["incidents"] = copy.deepcopy(its.get("incidents", []))
        joined.append(one)
    return joined


class Log:
    """Writes a log in this form: `entries` is the chain, `contents`
    what is kept beside it. Every entry is offered to the same check a
    reader runs before it is appended, so this never writes a log that
    `check` would refuse.

    `table` gives, for each kind of entry, the names of the fields kept
    apart, in ascending order. `salt` is called once for each field
    kept apart; leave it as it is for anything real. The shared test
    vectors pass fixed salts, which are public to everyone."""

    def __init__(self, table: Dict[str, List[str]],
                 data: Optional[dict] = None, *, kind: str = "world_created",
                 salt: Callable[[], str] = new_salt):
        self.entries: List[dict] = []
        self.contents: Dict[str, Dict[str, list]] = {}
        self._scan = _Scan()
        self._salt = salt
        self._salts: Set[str] = set()
        first = dict(data or {})
        if "form" in first or "kept_apart" in first:
            raise ValueError("the first entry's form and table are written "
                             "here, not given")
        # Before the entry is looked at as a whole, as the check does: so
        # a table that isn't one is refused as that, whatever it holds.
        if not _table_ok(table):
            raise Refused(TABLE)
        first["form"] = FORM
        first["kept_apart"] = table
        self.append(0, kind, None, first)

    def head(self) -> str:
        return self.entries[-1]["hash"]

    def append(self, tick: int, kind: str, agent: Optional[str], data: dict,
               apart: Optional[Dict[str, Any]] = None) -> str:
        """Appends one entry and returns its hash. `data` holds the open
        fields, `apart` the fields kept apart, by name. Raises `Refused`,
        and appends nothing, if the entry would not hold."""
        prints: Dict[str, str] = {}
        kept: Dict[str, list] = {}
        salts: Set[str] = set()
        apart = {} if apart is None else apart
        # Before anything is copied or hashed: what Python can hold and
        # JSON can't (a key that isn't text, a set, a map nested too deep
        # to write) is refused here, not written or left to crash.
        if type(apart) is not dict or not _open_ok(tick, kind, agent, data):
            raise Refused(ENTRY, len(self.entries))
        for name in sorted(apart, key=str):
            salt = self._salt()
            if not _is_salt(salt):
                raise Refused(SALT)
            if salt in self._salts or salt in salts:
                raise Refused(SALT_TWICE)
            # Checked before it is copied: a value nested too deep to
            # copy is refused, not a crash.
            prints[name] = fingerprint(salt, name, apart[name])
            kept[name] = [salt, copy.deepcopy(apart[name])]
            salts.add(salt)
        prev = self.entries[-1]["hash"] if self.entries else GENESIS
        body = {"tick": tick, "kind": kind, "agent": agent,
                "data": copy.deepcopy(data), "apart": prints, "prev": prev}
        entry = {**body, "hash": _digest(body)}
        self._scan.take(entry)
        self.entries.append(entry)
        self._salts.update(salts)
        if kept:
            self.contents[entry["hash"]] = kept
        return entry["hash"]
