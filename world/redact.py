"""The act of redacting a field of a log, and of deciding on it after
(course step 3b, part three; docs/research/REDACTION.md, decisions 4 and
5).

Redacting is three things, in this order:

1. **The field is sealed.** What was hashed for it, the list of its
   salt, its name and its value as the log writes it, goes into a
   signed record (`open-worlds/redacted-field/v1`, formats/records.py)
   that names the log, the entry and the field. One copy is made for
   each person the field is about and one for the office that decides,
   each naming the one it is for and sealed to them alone
   (`open-worlds/redacted/v1`, formats/sealed.py). Someone with no key
   gets no copy: none is kept for them.
2. **The mark is appended** (world/apart.py): which entry and which
   field, by which office, and why in general terms, never what.
3. **The field is taken out of the contents.** The log then holds
   neither the value nor its salt, anywhere.

`redact` does the three. If a copy can't be made, nothing is marked. If
the mark is refused, nothing is taken out, and the copies made are not
given back. If the work stopped after the mark, the log shows a field
that is marked and still there, and `finish` seals it and takes it out.

**The copies are handed over before the mark is written.** Once the
field is out, the copies are all that is left of it. So whoever keeps
them is given them first (`store`), while the field is still in the
contents and nothing is marked; if they can't be kept, nothing is
marked. If the mark is then refused, they have been handed over all
the same: whatever keeps copies must expect some with no mark.

**A copy carries exactly what was hashed,** as text, and not the value
written a second way. So anything a log can keep apart can be redacted,
whatever a signed record could hold as a value of its own; and nothing
is lost between two ways of writing JSON.

Deciding comes after. The office that decides opens its copy, holds it
to the log and, to keep the field public, puts it back with the
decision in one step (`keep_public`). Only the deciding office's own
copy does: every copy names the deciding office, and the one that names
its own reader as that office is the office's. Or it decides that the
field stays redacted (`stays_redacted`), and deletes its copy.

**What binds a copy to its place** is the log, not the signature.
Whoever opens a copy hashes what it carries and finds that fingerprint
in the entry the copy names, in the log the copy names (`held_to`). A
copy that does not match is refused, whoever signed it. A copy does not
name its mark, which is written after it: its mark is the one in the
log on the same entry and field.

**A copy is padded** (`pad`), so that a sealed box is one of a few
sizes and its length says little about the length of what was there.

Limits. This module does not check who may redact or decide: that the
office holds the grant it names is for the checks across records. Until
then, who signed a copy, which office it names and who its deciding
office is are the record's own word: whoever holds a field's salt and
value can write a record that this module takes. That is no way to
learn a field, and it is why the log's writer must not decide on a copy
alone. It does not find a person's sealing key: the caller gives each
key, as everywhere a record is sealed (formats/sealed.py). It can't
delete anything: that the office's copy is gone once a redaction stands
is the office's word, until keys can be destroyed (course step 8a). An
envelope says in the clear that it holds a redacted field and whom it
is for, so it is not placed in the open. A log is named by the hash of
its first entry, which holds its form and its table. Two logs begun
with the same first entry share that name. What no two logs share is
an entry's hash, once a field with a fresh salt is behind it, and a
copy names its entry.
"""
from __future__ import annotations

import hashlib
import json
from typing import (Any, Callable, Dict, List, NamedTuple, Optional,
                    Sequence, Tuple)

from formats import records, sealed
from formats.canonical import FormatError, canonical
from formats.multikey import did_key
from multiverse import ed25519

from . import apart
from .apart import Refused

FORMAT = "open-worlds/redacted-field/v1"
LABEL = "open-worlds/redacted/v1"
# The smallest a padded record is, in bytes of its RFC 8785 form before
# it is signed. Above that, a record is padded to the next power of two.
PADDED = 1024

# Every reason this module refuses for, in fixed words, the same in Rust
# (rust/redact). A log's own refusals (apart.Refused) and a sealed
# record's (formats.sealed.SealedError) pass through as they are.
NOT_THERE = "the field is not in the contents"
TWICE = "a copy is asked for the same one twice"
NOT_A_COPY = "not a redacted field's record"
OTHER_LOG = "the copy names another log"
NO_ENTRY = "the copy names an entry the log does not have"
NO_FIELD = "the copy names a field the entry does not keep apart"
NOT_HELD = "the copy is not what the log held"
NOT_DECIDERS = "the copy is not the deciding office's own"
OTHER_FIELD = "the copy is of another field than the mark's"
NO_MARK = "not a mark that is open or stands"
REASONS = (NOT_THERE, TWICE, NOT_A_COPY, OTHER_LOG, NO_ENTRY, NO_FIELD,
           NOT_HELD, NOT_DECIDERS, OTHER_FIELD, NO_MARK)

# Called with the copies for the persons and the deciding office's copy.
Store = Callable[[List[Dict[str, Any]], Dict[str, Any]], None]


class RedactError(ValueError):
    """A redaction that can't be made, or a copy that doesn't hold to
    its log. `reason` is one of REASONS."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class Office(NamedTuple):
    """The office that redacts: its name as the log shows it, its
    signing key (32 bytes, Ed25519), and the hash of the grant it acts
    under."""
    name: str
    secret: bytes
    grant: str

    @property
    def key(self) -> str:
        """The office's did:key."""
        return did_key(ed25519.public_key(self.secret))


class Redaction(NamedTuple):
    """What `redact` gives back: the mark's hash, which is the
    redaction's id; the sealed copies for the persons the field is
    about, in the order asked; and the sealed copy for the office that
    decides."""
    mark: str
    copies: List[Dict[str, Any]]
    office_copy: Dict[str, Any]


def log_id(log: Sequence[dict]) -> str:
    """What names a log: the hash of its first entry."""
    return log[0]["hash"]


def redact(log: apart.Log, tick: int, entry: str, field: str, by: Office,
           ground: dict, created: str, *,
           about: Sequence[Tuple[str, bytes]] = (),
           decider: Tuple[str, bytes], store: Optional[Store] = None,
           agent: Optional[str] = None,
           apart_fields: Optional[Dict[str, Any]] = None) -> Redaction:
    """Redacts `field` of `entry`: seals it, marks it, takes it out.

    `about` names each person the field is about who has a key, and
    `decider` the office that decides, each as a did:key and the
    sealing key (32 bytes, X25519) that belongs to it. `created` is the
    time the copies are signed at. `apart_fields` are the mark's own
    fields kept apart, such as a reason.

    `store`, if given, is called with the persons' copies and the
    deciding office's copy once they are sealed and before the mark is
    written: whatever keeps them, keeps them there. If it raises,
    nothing is marked.

    Raises `RedactError` if the field is not in the contents or one is
    named twice; `formats.sealed.SealedError` if a copy can't be made;
    whatever `store` raises; `apart.Refused` if the mark does not hold.
    Then nothing has changed. No error's text holds any of the field."""
    copies = _copies(log, entry, field, by, created, about, decider)
    if store is not None:
        store(copies[:-1], copies[-1])
    mark = log.mark(tick, entry, field, by.name, ground, agent=agent,
                    apart=apart_fields)
    log.take_out(mark)
    return Redaction(mark, copies[:-1], copies[-1])


def finish(log: apart.Log, mark: str, by: Office, created: str, *,
           about: Sequence[Tuple[str, bytes]] = (),
           decider: Tuple[str, bytes],
           store: Optional[Store] = None) -> Redaction:
    """Finishes a redaction that stopped after its mark: seals the
    field, which is still in the contents, hands the copies to `store`
    as `redact` does, and takes the field out. The log is not touched.
    Raises `RedactError` if `mark` is not a mark that is open or
    stands, or its field is no longer in the contents."""
    where = _marked(log.entries, mark)
    state = None
    if where is not None:
        state = [r["state"] for r in
                 apart.redactions(log.entries)[where[0]][where[1]]
                 if r["id"] == mark][0]
    if where is None or state == apart.KEPT_PUBLIC:
        raise RedactError(NO_MARK)
    copies = _copies(log, where[0], where[1], by, created, about, decider)
    if store is not None:
        store(copies[:-1], copies[-1])
    log.take_out(mark)
    return Redaction(mark, copies[:-1], copies[-1])


def _padding(record: Dict[str, Any]) -> str:
    """The filler that brings `record`, which has none yet, to its
    padded size: `PADDED` bytes of its RFC 8785 form, or the next power
    of two above that."""
    size = len(canonical(record))
    padded = max(PADDED, 1 << (size - 1).bit_length())
    return "0" * (padded - size)


def _copies(log: apart.Log, entry: Any, field: Any, by: Office,
            created: str, about: Sequence[Tuple[str, bytes]],
            decider: Tuple[str, bytes]) -> List[Dict[str, Any]]:
    """A sealed copy of a field that is in the contents, for each one
    named in `about` and then for `decider`. Changes nothing."""
    held = log.contents.get(entry) if type(entry) is str else None
    if (type(held) is not dict or type(field) is not str
            or field not in held):
        raise RedactError(NOT_THERE)
    salt, value = held[field]
    hashed = apart.fingerprint_text(salt, field, value)
    to = list(about) + [decider]
    if len({key for key, _ in to}) != len(to):
        raise RedactError(TWICE)
    office = {"key": by.key, "grant": by.grant}
    sealed_copies = []
    for key, sealing_public in to:
        record = {"format": FORMAT, "office": office, "to": key,
                  "decider": decider[0], "log": log_id(log.entries),
                  "entry": entry, "field": field, "hashed": hashed,
                  "pad": ""}
        # What can fail here is what the caller gave: a key, a grant, a
        # time. `hashed` is text and `pad` is zeros, whatever the field
        # held, so no error's text holds any of the field.
        try:
            record["pad"] = _padding(record)
            signed = records.sign(record, by.secret, created)
        except (records.RecordError, FormatError) as e:
            raise sealed.SealedError(
                f"only a record that holds is sealed: {e}") from None
        sealed_copies.append(sealed.seal_record(signed, sealing_public))
    return sealed_copies


def what_was_there(record: Any) -> Optional[List[Any]]:
    """The `[salt, value]` a redacted field's record carries, or
    nothing if what it carries is not a field as a log hashes one: the
    list of a salt, the record's own field name and a value, written
    exactly as the log writes it."""
    if type(record) is not dict:
        return None
    hashed, field = record.get("hashed"), record.get("field")
    if type(hashed) is not str or type(field) is not str:
        return None
    try:
        parts = json.loads(hashed)
    except (ValueError, RecursionError):
        return None
    if type(parts) is not list or len(parts) != 3:
        return None
    # Written again with the record's own field name: a text that
    # names another field is not the same text.
    salt, _, value = parts
    try:
        if apart.fingerprint_text(salt, field, value) != hashed:
            return None
    except Refused:
        return None
    return [salt, value]


def held_to(record: Any, log: Any) -> None:
    """Holds a redacted field's record to a log: the log is in its form
    and holds, the record names it, the entry is in it, the entry keeps
    that field apart, the text the record carries hashes to the
    fingerprint the entry holds, and that text is the field as a log
    writes one. Raises `apart.Refused` for the log and `RedactError`
    for the record. It does not check the record's signature, whom it
    is for or which office it names: `formats.records.check` checks the
    first, and opening a sealed copy checks the first two."""
    apart.redactions(log)            # the log holds, or Refused
    if type(record) is not dict or record.get("format") != FORMAT:
        raise RedactError(NOT_A_COPY)
    if record.get("log") != log_id(log):
        raise RedactError(OTHER_LOG)
    found = [e for e in log if e["hash"] == record.get("entry")]
    if not found:
        raise RedactError(NO_ENTRY)
    field = record.get("field")
    kept = found[0]["apart"]
    if type(field) is not str or field not in kept:
        raise RedactError(NO_FIELD)
    hashed = record.get("hashed")
    try:
        print_ = (hashlib.sha256(hashed.encode()).hexdigest()
                  if type(hashed) is str else None)
    except UnicodeEncodeError:
        print_ = None
    if print_ != kept[field] or what_was_there(record) is None:
        raise RedactError(NOT_HELD)


def open_copy(envelope: Any, sealing_secret: bytes, opener: str,
              log: Any) -> Dict[str, Any]:
    """The record in a sealed copy, opened by `opener` (a did:key) with
    their sealing key, and held to `log`. Raises
    `formats.sealed.SealedError` if it does not open to a record that
    holds and names the opener, and what `held_to` raises.
    `what_was_there` then gives the salt and the value."""
    record = sealed.open_record(envelope, sealing_secret, opener, LABEL)
    held_to(record, log)
    return record


def _marked(log: Sequence[dict], mark: Any) -> Optional[Tuple[str, str]]:
    """The entry and the field a mark names, if `mark` is one."""
    for entry in log:
        if entry["hash"] == mark and entry["kind"] == apart.MARK:
            return entry["data"]["entry"], entry["data"]["field"]
    return None


def keep_public(log: apart.Log, tick: int, mark: str, envelope: Any,
                sealing_secret: bytes, opener: str, office: str,
                ground: dict, decision: str, *,
                agent: Optional[str] = None,
                apart_fields: Optional[Dict[str, Any]] = None) -> str:
    """The decision to keep a field public, by the office that holds
    the copy made for it: opens the copy, holds it to the log and to
    the mark, and puts the field back with the decision in one step.
    Returns the decision's entry's hash. `opener` is the office's
    did:key, and `office` its name as the log shows it.

    Raises `apart.Refused` if `mark` is not an open mark or the
    decision does not hold; `formats.sealed.SealedError` if the copy
    does not open; `RedactError` if it is not what the log held, not
    the deciding office's own copy, or not of the field the mark is
    on. Then nothing has changed.

    That the copy is the deciding office's own is the copy's word, as
    the module's limits say: a person's copy names another deciding
    office and is refused, and a record written by whoever holds the
    salt and the value is not. Who may decide is for the checks across
    records, with the decision this entry names."""
    where = _marked(log.entries, mark)
    if where is None:
        raise Refused(apart.BAD_KEPT, len(log.entries))
    record = open_copy(envelope, sealing_secret, opener, log.entries)
    if record["decider"] != record["to"]:
        raise RedactError(NOT_DECIDERS)
    if (record["entry"], record["field"]) != where:
        raise RedactError(OTHER_FIELD)
    salt, value = what_was_there(record)
    return log.keep_public(tick, mark, salt, value, office, ground,
                           decision, agent=agent, apart=apart_fields)


def stays_redacted(log: apart.Log, tick: int, mark: str, office: str,
                   ground: dict, decision: str, *,
                   agent: Optional[str] = None,
                   apart_fields: Optional[Dict[str, Any]] = None) -> str:
    """The decision that a field stays redacted: appends it, and
    returns its entry's hash. The office then deletes the copy made for
    it. This function can't: that the copy is gone is the office's
    word."""
    return log.stays_redacted(tick, mark, office, ground, decision,
                              agent=agent, apart=apart_fields)
