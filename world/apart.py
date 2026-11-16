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
  the chain is checked by the kernel's own `World.verify_log`,
  unchanged.
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
- **The state of a field**, from the log and the contents together:
  `present`; `redacted` (a mark stands, and the field is gone);
  `unfinished` (a mark stands, and the field is still there); `kept
  public` (every mark on it was answered by a decision to keep it
  public, and it is there); `missing` (no mark stands, and it is gone:
  a fault in whoever published the log).

`check` holds the contents to the log and gives every field's state.
`join` gives each entry as a reader uses it. `Log` writes the form.
Every reason for refusing is in fixed words, the same in Rust
(`rust/world-log/src/apart.rs`), checked against
`vectors/log-apart.json`.

Limits. A field under a standing mark is never shown by `join`, even
while it is still in the contents. The check holds a world to its table
by name: it can't know that an open field of another name holds what
should have been kept apart. A fingerprint commits a log to a value,
and says nothing of who wrote it: that is a signature's work. JSON's
`-0` in a contents file is read by Python as 0 and refused by Rust;
nothing here writes it. The open `data` follows the kernel's rules, not
a fingerprint's: Rust can't check a log whose open data holds a float.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import secrets
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .core import GENESIS, World, _digest, _is_unicode

FORM = "open-worlds/log-apart/v1"
MARK = "field_redacted"
KEPT = "field_kept_public"

MAX_WHOLE = 2 ** 53 - 1
MAX_NESTING = 32

PRESENT = "present"
REDACTED = "redacted"
UNFINISHED = "unfinished"
KEPT_PUBLIC = "kept public"
MISSING = "missing"
STATES = (PRESENT, REDACTED, UNFINISHED, KEPT_PUBLIC, MISSING)

CHAIN = "the chain does not hold"
NO_FORM = "the first entry does not name this form"
TABLE = "the table of fields kept apart is not well formed"
ENTRY = "an entry is not in this form"
UNTABLED = "a field is kept apart that the table does not name"
OPEN = "a field the table keeps apart is in the open"
TWICE = "a fingerprint appears twice"
BAD_MARK = "a mark does not name an earlier entry and a field it keeps apart"
BAD_KEPT = "a decision to keep a field public does not name an earlier mark"
CONTENTS = "the contents are not well formed"
UNKNOWN = "the contents name an entry or a field the log does not keep apart"
SALT = "a salt is not 32 lowercase hex digits"
SALT_TWICE = "a salt appears twice"
VALUE = "a value is not one a fingerprint allows"
FINGERPRINT = "the contents do not match the fingerprint"
REASONS = (CHAIN, NO_FORM, TABLE, ENTRY, UNTABLED, OPEN, TWICE, BAD_MARK,
           BAD_KEPT, CONTENTS, UNKNOWN, SALT, SALT_TWICE, VALUE, FINGERPRINT)

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


class _Scan:
    """Reads a log's entries in order, keeping what later entries and
    the contents are checked against. `take` changes nothing unless the
    entry holds, so a writer can offer it an entry and keep going if it
    is refused."""

    def __init__(self) -> None:
        self.table: Dict[str, List[str]] = {}
        self.apart: Dict[str, Dict[str, str]] = {}   # entry -> name -> print
        self.marks: Dict[str, Tuple[str, str]] = {}  # mark -> (entry, name)
        self.answered: Set[str] = set()              # marks no longer standing
        self.seen: Set[str] = set()                  # every fingerprint
        self.count = 0

    def take(self, entry: Any) -> None:
        index = self.count
        if not isinstance(entry, dict):
            raise Refused(ENTRY, index)
        kind, data, apart = (entry.get("kind"), entry.get("data"),
                             entry.get("apart"))
        table = self.table
        if index == 0:
            if type(data) is not dict or data.get("form") != FORM:
                raise Refused(NO_FORM, index)
            table = data.get("kept_apart")
            if not _table_ok(table):
                raise Refused(TABLE, index)
        if (set(entry) != KEYS or type(kind) is not str
                or type(data) is not dict
                or type(apart) is not dict or not _is_hash(entry.get("hash"))
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
        # The entry holds: only now is anything kept.
        self.table = table
        self.apart[entry["hash"]] = dict(apart)
        self.seen.update(prints)
        if mark is not None:
            self.marks[entry["hash"]] = mark
        if answers is not None:
            self.answered.add(answers)
        self.count += 1


def _scan(log: Any) -> _Scan:
    if not World.verify_log(log):
        raise Refused(CHAIN)
    scan = _Scan()
    if not log:
        raise Refused(NO_FORM)
    for entry in log:
        scan.take(entry)
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
    apart that is `present` or `kept public`, and `fields` giving the
    state of each field kept apart. A field under a standing mark is
    left out even if it is still in the contents."""
    scan = _scan(log)
    held = _held(scan, contents)
    states = _states(scan, held)
    joined = []
    for entry in log:
        fields = states.get(entry["hash"], {})
        one = {k: copy.deepcopy(v) for k, v in entry.items() if k != "apart"}
        for name, state in fields.items():
            if state in (PRESENT, KEPT_PUBLIC):
                one["data"][name] = copy.deepcopy(held[entry["hash"]][name])
        one["fields"] = dict(fields)
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
        if type(apart) is not dict:
            raise Refused(ENTRY)
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
