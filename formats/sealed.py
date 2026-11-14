"""Sealed records (course step 2): a signed record, sealed to the one it
names.

Two kinds of record are sealed, each with its own label (formats/seal.py):

- **a world-key** (`open-worlds/world-key/v1`), signed by the world that
  placed the path, sealed to its holder (docs/WORLD-KEY.md);
- **a journal entry** (`open-worlds/journal-entry/v1`), signed by its
  author, sealed to its author alone (docs/MINDS.md, "Memory").

A sealed record travels in an envelope (`open-worlds/sealed/v1`): the
label, the one it is addressed to, and the box in hex. The envelope isn't
signed; what is inside is. Its fingerprint, the hash of its RFC 8785 form,
is what may be made public of a sealed self.

Sealing checks the record first: only a record that holds is sealed, and
only to the one it names. Opening checks everything again, in this order:

1. the envelope fits its schema, was sealed for the purpose the opener
   names, and is addressed to the opener;
2. the box opens with the opener's sealing key, under the opener's label;
3. what is inside is a record in its one RFC 8785 form, and it holds
   (formats/records.py);
4. it is a kind sealed under that label, and it names the opener.

So a world-key sealed again to someone else is refused by the one who
opens it: the box opens, but the record names another (docs/WORLD-KEY.md,
"The world-key").

Which sealing key belongs to which did:key is the identity record's to
say, from course step 9 (until then the key list publishes the ones made
at step 3); here the caller gives both.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from . import records, seal
from .canonical import FormatError, canonical

ENVELOPE = "open-worlds/sealed/v1"

#: Each sealed kind: the label it is sealed under, and the field naming
#: the one it is sealed to.
SEALED: Dict[str, Any] = {
    "open-worlds/world-key/v1": ("open-worlds/world-key/v1", "holder"),
    "open-worlds/journal-entry/v1": ("open-worlds/journal/v1", "author"),
}

_ENVELOPE = records.validator("sealed")


class SealedError(ValueError):
    """A sealed record that can't be made or opened as asked."""


def envelope_problems(envelope: Any) -> List[str]:
    """Where `envelope` doesn't fit its schema, or [] if it does."""
    if type(envelope) is not dict:
        return ["$: not an envelope"]
    return sorted(
        f"$.{'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
        if e.absolute_path else f"$: {e.message}"
        for e in _ENVELOPE.iter_errors(envelope))


def seal_record(record: Dict[str, Any], sealing_public: bytes
                ) -> Dict[str, Any]:
    """`record`, which must hold and be of a sealed kind, sealed to the
    one it names, whose sealing key is `sealing_public`."""
    try:
        records.check(record)
    except records.RecordError as e:
        raise SealedError(f"only a record that holds is sealed: {e}") from None
    if record["format"] not in SEALED:
        raise SealedError(f"{record['format']} isn't a kind that is sealed")
    label, field = SEALED[record["format"]]
    try:
        box = seal.seal(canonical(record), sealing_public, label)
    except seal.SealError as e:
        raise SealedError(str(e)) from None
    return {"format": ENVELOPE, "label": label, "to": record[field],
            "box": box.hex()}


def open_record(envelope: Any, sealing_secret: bytes, opener: str,
                label: str) -> Dict[str, Any]:
    """The record in `envelope`, if it holds, was sealed under `label` to
    `opener` (a did:key) and names them; otherwise SealedError."""
    if label not in seal.LABELS:
        raise SealedError(f"{label!r} isn't a sealing label in use")
    found = envelope_problems(envelope)
    if found:
        raise SealedError("; ".join(found))
    if envelope["label"] != label:
        raise SealedError("sealed for another purpose")
    if envelope["to"] != opener:
        raise SealedError("addressed to someone else")
    try:
        inside = seal.open_box(bytes.fromhex(envelope["box"]),
                               sealing_secret, label)
    except seal.SealError as e:
        raise SealedError(str(e)) from None
    try:
        record = json.loads(inside.decode("utf-8"))
        same = canonical(record) == inside
    except (UnicodeDecodeError, ValueError, RecursionError, FormatError):
        raise SealedError("what is inside isn't a record") from None
    if not same:
        raise SealedError("what is inside isn't in its one RFC 8785 form")
    try:
        records.check(record)
    except records.RecordError as e:
        raise SealedError(f"what is inside doesn't hold: {e}") from None
    kind = SEALED.get(record["format"])
    if kind is None or kind[0] != label:
        raise SealedError("what is inside isn't a kind sealed under "
                          f"{label}")
    if record[kind[1]] != opener:
        raise SealedError("what is inside names someone else")
    return record


def fingerprint(envelope: Dict[str, Any]) -> str:
    """The hash of `envelope`'s RFC 8785 form: what may be made public of
    a sealed record."""
    return records.record_hash(envelope)
