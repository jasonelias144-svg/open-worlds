"""A log whose fields are kept apart from the chain that commits to them
(course step 3b, parts two to four; docs/research/REDACTION.md).

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
- **Three kinds of entry are the form's own,** for a field that is
  redacted (docs/research/REDACTION.md, decisions 4 and 5): redacted
  first, decided after. A mark, kind `field_redacted`, names in the
  open an earlier entry by its hash (`data.entry`), a field that entry
  keeps apart (`data.field`), the office that made it (`data.office`)
  and the ground it rests on (`data.ground`, a `kind` and a `ref`): why
  in general terms, never what. It holds no decision: the mark comes
  first. A field has at most one mark that is open or stands. The mark
  is **open** until one of two entries answers it, each naming the
  mark (`data.mark`), its office, its ground and the hash of its
  decision record (`data.decision`). A decision to keep the field
  public, kind `field_kept_public`: the mark is answered, and the
  field may be marked again. Or a decision that the field stays
  redacted, kind `field_stays_redacted`: the mark **stands** for good,
  and nothing answers it again. A redaction's id is its mark's hash,
  shown as an incident's is (below).
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
  isn't removed; it can restore a removal of what its author has since
  taken back, and the entry stays taken back; an author can take back
  what an office removed, and it then stays hidden whatever the office
  does; a removal after a restoring is a new incident. An incident's id
  is the hash of the entry that carries the removal or the taking
  back, shown as the fewest hex digits, twelve or more, that no other
  incident or redaction in the log begins with.
- **The state of a field**, from the log and the contents together:
  `present`; `redacted` (a mark on it is open or stands, and the field
  is gone); `unfinished` (a mark on it is open or stands, and the field
  is still there); `kept public` (every mark on it was answered by a
  decision to keep it public, and it is there); `missing` (no mark on
  it is open or stands, and it is gone: a fault in whoever published
  the log).
- **What the form's own kinds say in the open is fixed** (`SAYS`): each
  holds exactly the keys named above for it, and nothing else. So a
  mark can hold no decision, and nothing beside its ground about what
  was redacted. What else such an entry carries is kept apart, as the
  table allows. And no table can keep one of those keys apart: a table
  that did would make every mark, or every decision, impossible to
  write.

`check` holds the contents to the log and gives every field's state.
`incidents` gives every entry's state, with its incidents.
`redactions` gives every field's redactions, each open, standing or
answered by a decision to keep the field public. `join` gives each
entry as a reader uses it. `Log` writes the form: a mark and the
decision that answers it only through `mark`, `take_out`,
`keep_public` and `stays_redacted`, which change the contents in the
same step, so that a field is never said to be public while it is
gone. `Log.open` opens a writer on a log and contents that were
written before.
Every reason for refusing is in fixed words, and names the same place,
in Rust (`rust/world-log/src/apart.rs`), checked against
`vectors/log-apart.json`.

The order of the checks is part of the form, so that a log or contents
with two faults is refused for the same one in both languages. Entries
are read in the log's order; for each, its link to the entry before
(`prev`), then what it says, then its hash. The contents are read in
ascending order of entry hash, and of field name within an entry.

Limits. A field under a mark that is open or stands is never shown by
`join`, even while it is still in the contents. An entry that is removed or taken
back is still given whole by `join`, with its state: nothing has left
the record, and hiding it is for whatever shows a room. This module
does not check who may redact, decide, remove, restore or take back:
that needs the signed records and the keys, which are kept apart. Nor
does it seal what is redacted: that is the act of redacting, beside
this module. Nothing can be the value of an open field: a field with
no value is left out. The check holds a world to its table by name:
it can't know that an open field of another name holds what should
have been kept apart. A fingerprint commits a log to a value, and
says nothing of who wrote it: that is a signature's work. JSON's
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
STAYS = "field_stays_redacted"

REMOVED = "entry_removed"
RESTORED = "entry_restored"
TAKEN_BACK = "entry_taken_back"
PUT_BACK = "entry_put_back"
# The form's own kinds: none of them can itself be removed or taken back.
OWN = (MARK, KEPT, STAYS, REMOVED, RESTORED, TAKEN_BACK, PUT_BACK)
# What each of them says in the open: exactly these keys. No table can
# keep one of them apart.
SAYS = {
    MARK: ("entry", "field", "office", "ground"),
    KEPT: ("mark", "office", "ground", "decision"),
    STAYS: ("mark", "office", "ground", "decision"),
    REMOVED: ("entry", "office", "ground", "decision"),
    RESTORED: ("incident", "office", "ground", "decision"),
    TAKEN_BACK: ("entry",),
    PUT_BACK: ("taken_back",),
}
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

# A redaction: its mark, and what answered it.
IS_OPEN = "open"
STANDS = "stands"
REDACTION_STATES = (IS_OPEN, STANDS, KEPT_PUBLIC)

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
BAD_MARK = ("a mark does not name an earlier entry and a field it keeps "
            "apart that is free to be marked, with its office and ground")
BAD_KEPT = ("a decision to keep a field public does not name an open "
            "mark, with its office, ground and decision")
BAD_STAYS = ("a decision that a field stays redacted does not name an "
             "open mark, with its office, ground and decision")
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
           BAD_KEPT, BAD_STAYS, BAD_REMOVAL, BAD_RESTORING, BAD_TAKING_BACK,
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


def _used(salt: str) -> str:
    """What a writer remembers of a salt it has used: its hash."""
    return hashlib.sha256(salt.encode()).hexdigest()


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
        # What one of the form's own kinds says in the open can't be
        # kept apart: no such entry could then be written.
        if any(name in SAYS.get(kind, ()) for name in names):
            return False
    return True


def _says_only(kind: str, data: dict) -> bool:
    """True if an entry of one of the form's own kinds holds, in the
    open, exactly the keys its kind says."""
    return set(data) == set(SAYS[kind])


def _office_and_ground_ok(data: dict) -> bool:
    """True if an office's act says, in the open, which office acted
    and the ground it rests on. The ground is one a decision record can
    hold: an earlier record is named by its hash."""
    ground = data.get("ground")
    return (type(data.get("office")) is str and data["office"] != ""
            and type(ground) is dict and set(ground) == {"kind", "ref"}
            and ground["kind"] in GROUNDS
            and type(ground["ref"]) is str
            and 0 < len(ground["ref"]) <= MAX_REF
            and (ground["kind"] != "record" or _is_hash(ground["ref"])))


def _office_ok(data: dict) -> bool:
    """True if an office's act says its office and its ground, and the
    hash of its decision record."""
    return _office_and_ground_ok(data) and _is_hash(data.get("decision"))


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
        self.stays: Set[str] = set()                # marks that stand for good
        # (entry, name) -> its mark that is open or stands, if any.
        self.marked: Dict[Tuple[str, str], str] = {}
        self.redactions: List[str] = []             # marks, in the log's order
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
                    or field not in self.apart.get(target, {})
                    or (target, field) in self.marked
                    or not _office_and_ground_ok(data)
                    or not _says_only(kind, data)):
                raise Refused(BAD_MARK, index)
            mark = (target, field)
        elif kind in (KEPT, STAYS):
            # Redacted first, decided after: one answer to a mark, and
            # only while it is open.
            answers = data.get("mark")
            if (type(answers) is not str or answers not in self.marks
                    or answers in self.answered or answers in self.stays
                    or not _office_ok(data)
                    or not _says_only(kind, data)):
                raise Refused(BAD_KEPT if kind == KEPT else BAD_STAYS, index)
        # What wins, among removing, restoring, taking back and putting
        # back (docs/research/REDACTION.md, decision 9).
        on: Optional[str] = None
        if kind == REMOVED:
            on = data.get("entry")
            if (not self._can_be_acted_on(on) or on in self.removed
                    or on in self.taken or not _office_ok(data)
                    or not _says_only(kind, data)):
                raise Refused(BAD_REMOVAL, index)
        elif kind == RESTORED:
            incident = data.get("incident")
            on = self.removals.get(incident) if type(incident) is str else None
            # Allowed while the author's taking back stands: the removal
            # stops standing, and the entry stays taken back.
            if (on is None or self.removed.get(on) != incident
                    or not _office_ok(data)
                    or not _says_only(kind, data)):
                raise Refused(BAD_RESTORING, index)
        elif kind == TAKEN_BACK:
            on = data.get("entry")
            if (not self._can_be_acted_on(on) or on in self.taken
                    or not _says_only(kind, data)):
                raise Refused(BAD_TAKING_BACK, index)
        elif kind == PUT_BACK:
            taking = data.get("taken_back")
            on = self.takings.get(taking) if type(taking) is str else None
            if (on is None or self.taken.get(on) != taking
                    or not _says_only(kind, data)):
                raise Refused(BAD_PUTTING_BACK, index)
        # The entry holds: only now is anything kept.
        here = entry["hash"]
        self.table = table
        self.apart[here] = dict(apart)
        self.kinds[here] = kind
        self.seen.update(prints)
        if mark is not None:
            self.marks[here] = mark
            self.marked[mark] = here
            self.redactions.append(here)
        if answers is not None and kind == KEPT:
            self.answered.add(answers)
            del self.marked[self.marks[answers]]
        elif answers is not None:
            self.stays.add(answers)
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
    or more, that no other incident in the log begins with. The ids
    are hex digits, as an entry's hash is. Sorted, an id shares its
    longest beginning with one of its two neighbours, so each is held
    against those two alone. An id is never cut longer than it is."""
    def shared(a: str, b: str) -> int:
        n = 0
        while n < len(a) and n < len(b) and a[n] == b[n]:
            n += 1
        return n

    order = sorted(set(ids))
    short = {}
    for i, one in enumerate(order):
        most = 0
        if i > 0:
            most = shared(one, order[i - 1])
        if i + 1 < len(order):
            most = max(most, shared(one, order[i + 1]))
        short[one] = one[:max(SHORT, most + 1)]
    return short


def _shown(scan: _Scan) -> Dict[str, str]:
    """Every id a room may show, as it is shown: incidents and
    redactions together, so that no two begin alike."""
    return _short_ids([incident for incident, _, _ in scan.incidents]
                      + scan.redactions)


def _redactions(scan: _Scan) -> Dict[str, Dict[str, List[dict]]]:
    """Every field's redactions, in the log's order."""
    short = _shown(scan)
    found: Dict[str, Dict[str, List[dict]]] = {}
    for mark in scan.redactions:
        entry, name = scan.marks[mark]
        state = (KEPT_PUBLIC if mark in scan.answered
                 else STANDS if mark in scan.stays else IS_OPEN)
        found.setdefault(entry, {}).setdefault(name, []).append(
            {"id": mark, "short": short[mark], "state": state})
    return found


def _entry_states(scan: _Scan) -> Dict[str, dict]:
    """The state of every entry that has an incident, with them."""
    short = _shown(scan)
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


def redactions(log: Any) -> Dict[str, Dict[str, List[dict]]]:
    """Checks a log in this form and gives every redaction in it: a map
    from an entry's hash to a map from a field's name to that field's
    redactions, in the log's order, each with its `id` (its mark's
    hash), its `short` id as shown, and its `state`: `open` (marked,
    and not decided yet), `stands` (decided: it stays redacted) or
    `kept public` (decided: the mark was answered). It needs no
    contents. Whether a redacted field is in fact gone is a field's
    state, which `check` gives."""
    return _redactions(_scan(log))


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
    of each field kept apart, `redactions` giving each field's
    redactions (as `redactions` gives them; none, for most), and the
    entry's own `state` and `incidents` (as `incidents` gives them; `as
    written` and none, for most). A field under a mark that is open or
    stands is left out even if it is
    still in the contents. An entry that is removed or taken back is
    given whole: hiding it is for whatever shows the room."""
    scan = _scan(log)
    held = _held(scan, contents)
    states = _states(scan, held)
    acted_on = _entry_states(scan)
    redacted = _redactions(scan)
    joined = []
    for entry in log:
        fields = states.get(entry["hash"], {})
        one = {k: copy.deepcopy(v) for k, v in entry.items() if k != "apart"}
        for name, state in fields.items():
            if state in (PRESENT, KEPT_PUBLIC):
                one["data"][name] = copy.deepcopy(held[entry["hash"]][name])
        one["fields"] = dict(fields)
        one["redactions"] = copy.deepcopy(redacted.get(entry["hash"], {}))
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
        # Every salt used, as its hash: enough to refuse a source that
        # repeats, and nothing a fingerprint could be guessed with. A
        # salt itself is kept in the contents only, and leaves with its
        # field.
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

    @classmethod
    def open(cls, entries: Any, contents: Any, *,
             salt: Callable[[], str] = new_salt) -> "Log":
        """A writer opened on a log and its contents as they were
        written before, to go on from the log's head. The two are
        checked together first, as `check` checks them: raises
        `Refused`, for the same reason and at the same place, if they
        do not hold.

        The writer keeps copies of both, so what was given is not
        touched afterwards. An entry whose map of fields is empty is
        left out of the contents, as this writer leaves it. A field
        that is missing or unfinished is not refused: those are states,
        and the writer goes on from them. An unfinished redaction is
        finished with `take_out`, also one that was decided while its
        field was left in.

        What it can't know is the salt of a field that was taken out
        before. So a source of salts that repeats one of those is not
        refused here, as it is by the writer that used that salt."""
        scan = _scan(entries)
        _held(scan, contents)
        log = cls.__new__(cls)
        log.entries = copy.deepcopy(entries)
        log.contents = {entry: copy.deepcopy(fields)
                        for entry, fields in contents.items() if fields}
        log._scan = scan
        log._salt = salt
        log._salts = {_used(pair[0]) for fields in contents.values()
                      for pair in fields.values()}
        return log

    def head(self) -> str:
        return self.entries[-1]["hash"]

    def append(self, tick: int, kind: str, agent: Optional[str], data: dict,
               apart: Optional[Dict[str, Any]] = None) -> str:
        """Appends one entry and returns its hash. `data` holds the open
        fields, `apart` the fields kept apart, by name. Raises `Refused`,
        and appends nothing, if the entry would not hold.

        A mark and the decision that answers it are not written here:
        `mark`, `keep_public` and `stays_redacted` write them, with the
        contents changed in the same step."""
        if kind in (MARK, KEPT, STAYS):
            raise ValueError("a mark and the decision that answers it are "
                             "written by mark, keep_public and "
                             "stays_redacted")
        return self._append(tick, kind, agent, data, apart)

    def mark(self, tick: int, entry: str, field: str, office: str,
             ground: dict, *, agent: Optional[str] = None,
             apart: Optional[Dict[str, Any]] = None) -> str:
        """Appends a mark on `field` of `entry` and returns its hash:
        the redaction's id. The field is still in the contents, so its
        state is `unfinished` until `take_out`; it is never shown
        meanwhile. Whatever is sealed of it is sealed before this."""
        return self._append(tick, MARK, agent,
                            {"entry": entry, "field": field,
                             "office": office, "ground": ground}, apart)

    def take_out(self, mark: str) -> list:
        """Takes the field under `mark` out of the contents and returns
        its `[salt, value]`, which this writer then keeps nowhere:
        neither in the entries, nor in the contents, nor in what it
        remembers of the salts it has used. The log itself is not
        touched.

        The mark is one that is open or stands. A writer that wrote the
        whole log never has a field left under a mark that stands,
        since `stays_redacted` is refused while the field is there. A
        writer opened on a published log can: whoever published it may
        have left the field in."""
        if (type(mark) is not str or mark not in self._scan.marks
                or mark in self._scan.answered):
            raise ValueError("no mark of that hash is open or stands")
        entry, field = self._scan.marks[mark]
        fields = self.contents.get(entry, {})
        if field not in fields:
            raise ValueError("the field is not in the contents")
        pair = fields.pop(field)
        if not fields:
            del self.contents[entry]
        return pair

    def keep_public(self, tick: int, mark: str, salt: str, value: Any,
                    office: str, ground: dict, decision: str, *,
                    agent: Optional[str] = None,
                    apart: Optional[Dict[str, Any]] = None) -> str:
        """The decision to keep a field public: puts `[salt, value]`
        back into the contents and appends the entry that answers
        `mark`, in one step, and returns that entry's hash. Raises
        `Refused`, and changes nothing, if the mark is not open, if the
        salt and value are not the ones the log commits to, or if the
        entry would not hold."""
        if (type(mark) is not str or mark not in self._scan.marks
                or mark in self._scan.answered or mark in self._scan.stays):
            raise Refused(BAD_KEPT, len(self.entries))
        entry, field = self._scan.marks[mark]
        where = (entry, field)
        if not _is_salt(salt):
            raise Refused(SALT, where)
        if not value_allowed(value):
            raise Refused(VALUE, where)
        if fingerprint(salt, field, value) != self._scan.apart[entry][field]:
            raise Refused(FINGERPRINT, where)
        kept = self._append(tick, KEPT, agent,
                            {"mark": mark, "office": office,
                             "ground": ground, "decision": decision}, apart)
        self.contents.setdefault(entry, {})[field] = [
            salt, copy.deepcopy(value)]
        return kept

    def stays_redacted(self, tick: int, mark: str, office: str,
                       ground: dict, decision: str, *,
                       agent: Optional[str] = None,
                       apart: Optional[Dict[str, Any]] = None) -> str:
        """The decision that a field stays redacted: appends the entry
        that answers `mark` for good, and returns its hash. The field
        must be out of the contents already. Whoever held a copy for
        the decision deletes it when this is written."""
        scan = self._scan
        if (type(mark) is str and mark in scan.marks
                and mark not in scan.answered and mark not in scan.stays):
            entry, field = scan.marks[mark]
            if field in self.contents.get(entry, {}):
                raise ValueError("the field is still in the contents: "
                                 "take it out first")
        return self._append(tick, STAYS, agent,
                            {"mark": mark, "office": office,
                             "ground": ground, "decision": decision}, apart)

    def _append(self, tick: int, kind: str, agent: Optional[str], data: dict,
                apart: Optional[Dict[str, Any]] = None) -> str:
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
            if _used(salt) in self._salts or salt in salts:
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
        self._salts.update(_used(salt) for salt in salts)
        if kept:
            self.contents[entry["hash"]] = kept
        return entry["hash"]
