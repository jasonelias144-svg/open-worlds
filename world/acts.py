"""Who may act on a log whose fields are kept apart, held to the signed
records (course step 3b, part four, the records' side;
docs/research/REDACTION.md, decisions 7 to 9).

`world/apart.py` holds an act to its shape: what a removal, a restoring,
a taking back, a putting back and a decision on a redaction say in the
open, and what each can be done to. It can't say who may do them. That
needs the signed record each act carries, which is kept apart like
anything else a person gives, and the grants. This module holds every
act in a log to its record:

- **An office's act carries a decision record** (`open-worlds/decision/v1`,
  formats/records.py), in the field `record`, kept apart. Four kinds of
  entry are an office's act and carry one: a removal, a restoring, the
  decision to keep a redacted field public, and the decision that it
  stays redacted. The record must hold as a record; its hash must be
  the one the entry names in the open; its kind of act must be the one
  the rules fix for that kind of entry (`ACTS`); the records it is on
  must be exactly the one thing the entry acts on (the entry removed,
  the removal restored, the mark answered); its office's key must be
  the office the entry shows; its first ground must be the ground the
  entry shows; and it can't be dated, by its tick, after the entry that
  carries it. A restoring's decision supersedes the removal's. A
  removal and a restoring name the one who wrote the entry among those
  they affect, where that key is still there to read.
- **The office must hold a grant for the act.** The decision names a
  grant by its hash. That grant must be among the grants given, hold as
  a record, name the office's key as its holder, allow that kind of
  act, be for this room, and have been in force when the decision was
  signed. If it narrows another grant, the one above must be among the
  grants given too, be held by the one who issued the grant below, and
  allow the same act, in this room, at that time; and so on, at most
  `MAX_CHAIN` grants, up to a grant that narrows nothing, which must
  come from the room's key.
- **An author's act carries a record of its own,** signed by the author
  (`open-worlds/taking-back/v1`, `open-worlds/putting-back/v1`). No
  office acts, so there is no grant. A taking back names the entry, and
  the putting back that last put that entry back, if there was one; a
  putting back names the taking back it undoes. The signer must be the
  one who wrote the entry: the key in the field the rules name for that
  kind of entry. If that key is gone, redacted or under a mark, the
  act is reported as held with its signer not checked, since no
  reader can check it again; if the entry never held one, the act is
  refused. A key under a mark is not read even while a copy of the
  contents still holds it: the mark is in the log, and every reader
  is to get the same state from the same log, whichever copy of the
  contents they hold.
- **A decision is carried by one entry.** No two entries of a log name
  the same decision. So a removal that was restored can't be written a
  second time from the old record: a new removal needs a new decision.
  An author's taking back can't be written again either, once they have
  put the entry back: the record names the place in the entry's own
  history where it holds.
- **Which kinds of entry an act may be on** is for the room's rules: a
  mark, a removal and a taking back are each allowed on the kinds the
  rules list for them, and on no other. A field of one of the form's
  own entries, such as a decision's record, can always be marked: the
  form allows it, and the rules list only what persons write.
- **A mark carries no record.** It is made at once and decided after
  (decision 4). Who marked is checked where the field's sealed copy is
  opened: each copy is signed by the office that redacted, and names
  its grant. `office_may` holds that office to its grant.

The rules are given with the log, and are the room's. `room` is the
room's did:key, from which every grant here must descend; `authors`
gives, for each kind of entry a person writes, the name of the field
that holds the key that wrote it, which the log's table must keep
apart; `on` gives, for a mark, a removal and a taking back, the kinds
of entry each may be on, in ascending order.

`check` gives, for each entry that carries a record, one of `STATES`:
held; held with its signer not checked; its record redacted (a mark on
the record is open or stands, and nothing can be held to it); or its
record missing (gone with no mark, which is a fault in whoever
published the log). It raises `apart.Refused` for a log or contents
that do not hold, and `ActError` for the first act, in the log's
order, that is not allowed, with one of `REASONS`. The order of the
checks is part of this module, so that Python and Rust (`rust/acts`)
refuse a log with two faults for the same one, checked against
`vectors/acts.json`.

Limits. A world checks an act when it writes the entry; this module is
that check, and a reader can make it again only while the records are
still there. The room's key is the rules' word: a log in this form
carries no signature of its own until the room signs its heads (course
step 3c). A grant is held to be in force by the time its decision says
it was signed, which is the signer's own word; nothing here revokes a
grant before its end. Only the path from the office's grant up to the
room is checked, for the one act: that a grant claims no more than the
grant it narrows, for other acts, is not. That a decision's inputs are
in the log, and that its reasons are sound, is not checked. An office
is shown in the open by its key; its name is for the office's own
record (course step 3d). An author whose key was signed over to a new
one can't take back with the new key: successions are not in records-v1
yet (course step 8a), and until then only the key that wrote an entry
takes it back. Nothing here writes a log: the room's steps that refuse
to write an act its records do not allow are step 3c's, and call this.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from formats import records
from formats.canonical import FormatError

from . import apart
from .apart import (KEPT, MARK, PUT_BACK, REMOVED, RESTORED, STAYS,
                    TAKEN_BACK)

# The field, kept apart, that holds an act's signed record.
RECORD = "record"

DECISION = "open-worlds/decision/v1"
GRANT = "open-worlds/grant/v1"
TAKING_BACK = "open-worlds/taking-back/v1"
PUTTING_BACK = "open-worlds/putting-back/v1"
# A redacted field's record (world/redact.py), which names its office
# and grant as a decision does.
COPY = "open-worlds/redacted-field/v1"

# The kinds of act the rules fix for a log in this form: for each kind
# of entry that is an office's act, the kind of act its decision record
# says, and its office's grant must allow. A mark carries no decision:
# its kind of act is the one the grant of the office that redacts must
# allow.
ACTS = {
    MARK: "redact-field",
    KEPT: "keep-field-public",
    STAYS: "keep-field-redacted",
    REMOVED: "remove-comment",
    RESTORED: "restore-comment",
}
# The author's own acts, which are no office's: the kind of entry, and
# the format of the record the author signs.
OWN_ACTS = {TAKEN_BACK: TAKING_BACK, PUT_BACK: PUTTING_BACK}
# The kinds of entry the rules say what they may be on.
RULED = (MARK, REMOVED, TAKEN_BACK)

# The longest chain of grants, from an office's own up to the room's.
MAX_CHAIN = 8

HELD = "held"
UNCHECKED = "held, signer not checked"
REDACTED = "record redacted"
MISSING = "record missing"
STATES = (HELD, UNCHECKED, REDACTED, MISSING)

RULES = ("the rules are not well formed, do not fit the log's table, or "
         "the grants are not a list")
NOT_ON = "an act is on a kind of entry the rules do not allow it on"
TWICE = "a decision is named by two entries"
NO_RECORD = "an act carries no record"
NOT_A_RECORD = "an act's record does not hold, or is of another kind"
OTHER_HASH = "a decision is not the one its entry names"
OTHER_ACT = "a record is for another kind of act than the one it is held to"
OTHER_ENTRY = "a record is on another thing than its entry acts on"
OTHER_OFFICE = "a decision's office is not the one its entry shows"
OTHER_GROUND = "a decision's first ground is not the one its entry shows"
LATER = "a decision is dated after the entry that carries it"
NOT_SUPERSEDING = "a restoring's decision does not supersede the removal's"
NOT_AFFECTED = ("a decision does not name the one who wrote the entry "
                "among those it affects")
NO_GRANT = "a grant named is not among the grants given"
BAD_GRANT = "a grant named does not hold"
NOT_HOLDER = "an office does not hold the grant it names"
NOT_ALLOWED = "a grant does not allow the act"
ELSEWHERE = "a grant is not for this room"
NOT_IN_FORCE = "a grant was not in force when the record was signed"
NOT_NARROWING = ("a grant was not issued by the holder of the grant it "
                 "narrows")
NOT_ROOMS = "a grant that narrows nothing does not come from the room's key"
TOO_DEEP = "a chain of grants is too long"
OTHER_PLACE = ("a taking back does not follow the entry's last putting "
               "back")
NOT_AUTHOR = "a record is not signed by the one who wrote the entry"
REASONS = (RULES, NOT_ON, TWICE, NO_RECORD, NOT_A_RECORD, OTHER_HASH,
           OTHER_ACT, OTHER_ENTRY, OTHER_OFFICE, OTHER_GROUND, LATER,
           NOT_SUPERSEDING, NOT_AFFECTED, NO_GRANT, BAD_GRANT, NOT_HOLDER,
           NOT_ALLOWED, ELSEWHERE, NOT_IN_FORCE, NOT_NARROWING, NOT_ROOMS,
           TOO_DEEP, OTHER_PLACE, NOT_AUTHOR)

_DID = re.compile(r"did:key:z6Mk[1-9A-HJ-NP-Za-km-z]{44}")
# A field under a mark is not read, even while a copy of the contents
# still holds it: the state comes from the log alone.
_READABLE = (apart.PRESENT, apart.KEPT_PUBLIC)


class ActError(ValueError):
    """Why an act in a log is not allowed. `reason` is one of
    `REASONS`; `where` is the place in the log, from 0, of the entry
    that carries the act, when there is one."""

    def __init__(self, reason: str, where: Optional[int] = None):
        super().__init__(reason if where is None else f"{reason}: {where}")
        self.reason = reason
        self.where = where


def _kinds_ok(kinds: object) -> bool:
    """True for a list of kinds of entry, none of them the form's own,
    in ascending order."""
    return (type(kinds) is list
            and all(type(k) is str and k not in apart.OWN for k in kinds)
            and all(a < b for a, b in zip(kinds, kinds[1:])))


def rules_ok(rules: object) -> bool:
    """True if `rules` are well formed: the room's did:key, the field
    that holds the key that wrote each kind of entry, and the kinds of
    entry a mark, a removal and a taking back may each be on. A kind
    that can be taken back names who wrote it. Whether they fit a
    log's table is checked with the log."""
    if type(rules) is not dict or set(rules) != {"room", "authors", "on"}:
        return False
    room, authors, on = rules["room"], rules["authors"], rules["on"]
    if type(room) is not str or _DID.fullmatch(room) is None:
        return False
    if type(authors) is not dict or not all(
            type(kind) is str and kind not in apart.OWN
            and apart._is_name(field) for kind, field in authors.items()):
        return False
    if type(on) is not dict or set(on) != set(RULED):
        return False
    if not all(_kinds_ok(kinds) for kinds in on.values()):
        return False
    return all(kind in authors for kind in on[TAKEN_BACK])


def _by_hash(grants: object) -> Dict[str, Any]:
    """The records given, each under its hash. What can't be hashed as
    a record can't be named by one, and is left out."""
    if type(grants) is not list:
        raise ActError(RULES)
    found: Dict[str, Any] = {}
    for grant in grants:
        if type(grant) is not dict:
            continue
        try:
            found[records.record_hash(grant)] = grant
        except FormatError:
            continue
    return found


def _holds(record: object, kind: str) -> bool:
    """True if `record` is a record of `kind` that holds."""
    if type(record) is not dict or record.get("format") != kind:
        return False
    try:
        records.check(record)
    except (records.RecordError, FormatError):
        return False
    return True


def _may(office: Dict[str, str], act: str, at: str, grants: Dict[str, Any],
         room: str, where: Optional[int]) -> None:
    """Follows the office's grant up to the room's key. Each grant on
    the way must hold, be held by the one below's issuer (the first, by
    the office), allow the act, be for the room, and have been in
    force at `at`."""
    name, holder = office["grant"], office["key"]
    for depth in range(MAX_CHAIN):
        grant = grants.get(name)
        if grant is None:
            raise ActError(NO_GRANT, where)
        if not _holds(grant, GRANT):
            raise ActError(BAD_GRANT, where)
        if grant["holder"] != holder:
            raise ActError(NOT_HOLDER if depth == 0 else NOT_NARROWING,
                           where)
        if act not in grant["allows"]:
            raise ActError(NOT_ALLOWED, where)
        if grant["within"] != room:
            raise ActError(ELSEWHERE, where)
        # Times are compared as text. records-v1 fixes a time to UTC,
        # to the second (`$defs/time`), so the order of the text is the
        # order of time; a schema that allowed fractions or offsets
        # would break this.
        if not (grant["validFrom"] <= at
                and ("validUntil" not in grant
                     or at < grant["validUntil"])):
            raise ActError(NOT_IN_FORCE, where)
        if "narrows" not in grant:
            if grant["issuer"] != room:
                raise ActError(NOT_ROOMS, where)
            return
        name, holder = grant["narrows"], grant["issuer"]
    raise ActError(TOO_DEEP, where)


def office_may(record: Any, act: str, grants: Any, rules: Any) -> None:
    """Holds the office that signed `record` to its grant, for `act`:
    a decision, or a redacted field's record, whose act is
    `ACTS[MARK]`. The record must hold as a record, and `act` must be
    the act it is for: a decision's own kind of act, or `ACTS[MARK]`.
    Raises `ActError` with the reason; `where` is nothing, since no log
    is read."""
    if not rules_ok(rules):
        raise ActError(RULES)
    by_hash = _by_hash(grants)
    if (type(record) is not dict
            or record.get("format") not in (DECISION, COPY)
            or not _holds(record, record["format"])):
        raise ActError(NOT_A_RECORD)
    claimed = (record["act"]["kind"] if record["format"] == DECISION
               else ACTS[MARK])
    if act != claimed:
        raise ActError(OTHER_ACT)
    _may(record["office"], act, record["proof"]["created"], by_hash,
         rules["room"], None)


def check(log: Any, contents: Any, grants: Any,
          rules: Any) -> Dict[str, str]:
    """Checks a log in the form of `world/apart.py` and its contents,
    then holds every act in it to its signed record, and every office
    to its grant. Gives a map from the hash of each entry that carries
    a record to one of `STATES`. Raises `apart.Refused` if the log or
    its contents do not hold, and `ActError` for the first act, in the
    log's order, that is not allowed."""
    states = apart.check(log, contents)
    table = log[0]["data"]["kept_apart"]
    if (not rules_ok(rules)
            or any(field not in table.get(kind, [])
                   for kind, field in rules["authors"].items())):
        raise ActError(RULES)
    by_hash = _by_hash(grants)
    room, authors, on = rules["room"], rules["authors"], rules["on"]
    entries = {entry["hash"]: entry for entry in log}

    def readable(entry: str, field: str) -> bool:
        return states.get(entry, {}).get(field) in _READABLE

    def author(entry: str) -> Tuple[str, Any]:
        """Who wrote `entry`, as far as it can be read: `never` if the
        entry holds no key at all, `gone` if the key is no longer in
        the contents, or `there` with the key."""
        field = authors.get(entries[entry]["kind"])
        if field is None or field not in entries[entry]["apart"]:
            return "never", None
        if not readable(entry, field):
            return "gone", None
        return "there", contents[entry][field][1]

    found: Dict[str, str] = {}
    named: set = set()                    # every decision named so far
    put_back: Dict[str, str] = {}         # entry -> its last putting back
    for index, entry in enumerate(log):
        kind, data, here = entry["kind"], entry["data"], entry["hash"]
        if kind not in apart.OWN:
            continue
        if kind in RULED:
            on_kind = entries[data["entry"]]["kind"]
            if on_kind not in apart.OWN and on_kind not in on[kind]:
                raise ActError(NOT_ON, index)
        if kind == MARK:
            continue
        # The entry the act is, in the end, about: the one a person
        # wrote. A decision on a redaction is about a field, not an
        # entry's author.
        if kind in (REMOVED, TAKEN_BACK):
            comment = data["entry"]
        elif kind == RESTORED:
            comment = entries[data["incident"]]["data"]["entry"]
        elif kind == PUT_BACK:
            comment = entries[data["taken_back"]]["data"]["entry"]
        else:
            comment = None
        after = put_back.get(comment) if kind == TAKEN_BACK else None
        if kind == PUT_BACK:
            put_back[comment] = here
        if kind in ACTS:
            if data["decision"] in named:
                raise ActError(TWICE, index)
            named.add(data["decision"])
        if RECORD not in entry["apart"]:
            raise ActError(NO_RECORD, index)
        if not readable(here, RECORD):
            found[here] = (MISSING if states[here][RECORD] == apart.MISSING
                           else REDACTED)
            continue
        record = contents[here][RECORD][1]
        if not _holds(record, DECISION if kind in ACTS else OWN_ACTS[kind]):
            raise ActError(NOT_A_RECORD, index)
        if kind in ACTS:
            target = (data["entry"] if kind == REMOVED
                      else data["incident"] if kind == RESTORED
                      else data["mark"])
            if records.record_hash(record) != data["decision"]:
                raise ActError(OTHER_HASH, index)
            if record["act"]["kind"] != ACTS[kind]:
                raise ActError(OTHER_ACT, index)
            if record["act"]["records"] != [target]:
                raise ActError(OTHER_ENTRY, index)
            if record["office"]["key"] != data["office"]:
                raise ActError(OTHER_OFFICE, index)
            if record["grounds"][0] != data["ground"]:
                raise ActError(OTHER_GROUND, index)
            if record["tick"] > entry["tick"]:
                raise ActError(LATER, index)
            if (kind == RESTORED and record.get("supersedes")
                    != entries[data["incident"]]["data"]["decision"]):
                raise ActError(NOT_SUPERSEDING, index)
            if comment is not None:
                where, wrote = author(comment)
                if where == "there" and wrote not in record["affects"]:
                    raise ActError(NOT_AFFECTED, index)
            _may(record["office"], ACTS[kind], record["proof"]["created"],
                 by_hash, room, index)
            found[here] = HELD
            continue
        if kind == TAKEN_BACK:
            if record["entry"] != comment:
                raise ActError(OTHER_ENTRY, index)
            if record.get("after") != after:
                raise ActError(OTHER_PLACE, index)
        elif record["takenBack"] != data["taken_back"]:
            raise ActError(OTHER_ENTRY, index)
        where, wrote = author(comment)
        if where == "never" or (where == "there"
                                and wrote != record["author"]):
            raise ActError(NOT_AUTHOR, index)
        found[here] = HELD if where == "there" else UNCHECKED
    return found


def kinds_of_act() -> List[str]:
    """The kinds of act the rules fix for a log in this form, in
    ascending order: what a grant for a room can allow."""
    return sorted(ACTS.values())
