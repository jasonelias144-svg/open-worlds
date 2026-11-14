"""The records the offices keep (course step 2): a grant, a decision
record, a suggestion, a rating, and a signed log head; and the records an
individual is given or keeps sealed: a world-key and a journal entry
(sealed with formats/sealed.py).

Each record's shape is in one JSON Schema (2020-12) that Python and Rust
both read, schemas/records-v1.schema.json, and each is signed with
`eddsa-jcs-2022` (formats/proof.py). A record holds when:

1. it fits the schema for the kind its `format` names;
2. its proof verifies;
3. it was signed by the one who must sign that kind: a grant, a
   world-key and a mind record by their issuer, a decision by the
   office's key, a suggestion, a rating and a journal entry by their
   author, a log head and a birth record (an individual's or a world's)
   by its world, and an identity by its own key.

What the schema can't say is checked where the records meet the kernel,
at course step 4: that a grant only narrows the grant it names; that a
decision's inputs are in the log, its office holds the grant it names,
and that grant allows its kind of act; that a rating's author wrote the
suggestion it names, and its outcome is a decision that names that
suggestion; and that a world-key's issuer is a world that places paths,
its path was placed in that world's log and walked to its end by its
holder, and it hasn't already been used to found a world
(docs/WORLD-KEY.md: "It is marked as used at the founding").

A record's hash, which other records name it by, is the SHA-256 of its
RFC 8785 form, proof included, in lowercase hex.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

import jsonschema
from jsonschema.exceptions import ValidationError

from . import proof, seal
from .canonical import canonical
from .multikey import KeyFormatError, did_key, sealing_from_multikey

SCHEMA_FILE = (Path(__file__).resolve().parent.parent
               / "schemas" / "records-v1.schema.json")
SCHEMA = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))

#: Each format: its schema's name in $defs, and the field naming its signer.
KINDS: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "open-worlds/grant/v1": ("grant", ("issuer",)),
    "open-worlds/decision/v1": ("decision", ("office", "key")),
    "open-worlds/suggestion/v1": ("suggestion", ("author",)),
    "open-worlds/rating/v1": ("rating", ("author",)),
    "open-worlds/log-head/v1": ("logHead", ("world",)),
    "open-worlds/world-key/v1": ("worldKey", ("issuer",)),
    "open-worlds/journal-entry/v1": ("journalEntry", ("author",)),
    "open-worlds/identity/v1": ("identity", ("id",)),
    "open-worlds/birth/v1": ("birth", ("world",)),
    "open-worlds/world-birth/v1": ("worldBirth", ("world",)),
    "open-worlds/mind/v1": ("mind", ("issuer",)),
}


class RecordError(ValueError):
    """A record that doesn't hold, with every reason."""


def _ecma_pattern(validator: Any, pattern: str, instance: Any,
                  schema: Any) -> Iterator[ValidationError]:
    """JSON Schema's `pattern` is an ECMA-262 regular expression. In
    Python, `$` also matches before a final line break, where ECMA-262's
    `$` doesn't, so a pattern ending in `$` is read with `\\Z`; the
    schema's patterns use nothing else on which the two differ."""
    if not validator.is_type(instance, "string"):
        return
    # (A pattern ending in an escaped backslash and then $, \\\\$, would be
    # misread here; no pattern in records-v1 ends so.)
    if pattern.endswith("$") and not pattern.endswith("\\$"):
        pattern = pattern[:-1] + "\\Z"
    if not re.search(pattern, instance):
        yield ValidationError(f"{instance!r} doesn't match {pattern!r}")


_Validator = jsonschema.validators.extend(
    jsonschema.Draft202012Validator, {"pattern": _ecma_pattern})


def validator(name: str) -> Any:
    """A validator for the schema's `$defs/<name>`."""
    return _Validator({"$schema": SCHEMA["$schema"],
                       "$defs": SCHEMA["$defs"],
                       "$ref": f"#/$defs/{name}"})


_VALIDATORS = {fmt: validator(name) for fmt, (name, _) in KINDS.items()}


def problems(record: Any) -> List[str]:
    """Where `record` doesn't fit its kind's schema, or [] if it does."""
    if (type(record) is not dict or type(record.get("format")) is not str
            or record["format"] not in KINDS):
        return ["$: not a record of a kind in records-v1"]
    errors = _VALIDATORS[record["format"]].iter_errors(record)
    return sorted(
        f"$.{'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
        if e.absolute_path else f"$: {e.message}" for e in errors)


def _times(record: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """Each UTC time in `record`, with where it is."""
    fmt = record.get("format")
    if fmt == "open-worlds/grant/v1":
        return [(f"$.{f}", record[f]) for f in ("validFrom", "validUntil")
                if f in record]
    if fmt in ("open-worlds/birth/v1", "open-worlds/world-birth/v1"):
        return [("$.time", record["time"])]
    if fmt == "open-worlds/mind/v1":
        return [(f"$.engines.{i}.from", e["from"])
                for i, e in enumerate(record["engines"])]
    return []


def _time_problems(record: Dict[str, Any]) -> List[str]:
    """Every time must be a real one, a grant must end after it starts,
    and a mind record's engines are in the order they began; the schema
    checks only their shape."""
    found = []
    for where, value in _times(record):
        try:
            proof.check_time(value)
        except proof.ProofError:
            found.append(f"{where}: not a real UTC time")
    if (not found and record.get("format") == "open-worlds/grant/v1"
            and "validUntil" in record
            and record["validUntil"] <= record["validFrom"]):
        found.append("$.validUntil: not after validFrom")
    if not found and record.get("format") == "open-worlds/mind/v1":
        engines = record["engines"]
        found = [f"$.engines.{i}.from: not after the engine before"
                 for i in range(1, len(engines))
                 if engines[i]["from"] <= engines[i - 1]["from"]]
    return found


def _key_problems(record: Dict[str, Any]) -> List[str]:
    """An identity's sealing key must be one it is safe to seal to
    (formats/seal.py); the schema checks only its shape."""
    if record.get("format") != "open-worlds/identity/v1":
        return []
    try:
        seal.check_public(sealing_from_multikey(record["sealingKey"]))
    except (KeyFormatError, seal.SealError) as e:
        return [f"$.sealingKey: {e}"]
    return []


def signer_field(record: Dict[str, Any]) -> Any:
    """The value of the field that names who must sign `record`."""
    value: Any = record
    for key in KINDS[record["format"]][1]:
        value = value[key]
    return value


def check(record: Any) -> Dict[str, Any]:
    """`record` without its proof, if it holds; otherwise RecordError."""
    found = problems(record)
    if not found:
        found = _time_problems(record) + _key_problems(record)
    if found:
        raise RecordError("; ".join(found))
    try:
        unsecured, public = proof.verify(record)
    except proof.ProofError as e:
        raise RecordError(f"$.proof: {e}") from None
    if did_key(public) != signer_field(record):
        raise RecordError(
            "$.proof: signed by another key than the one that must sign")
    return unsecured


def sign(record: Dict[str, Any], secret: bytes,
         created: str) -> Dict[str, Any]:
    """`record` signed by the holder of `secret`, who must be the one its
    kind names; RecordError if the result doesn't hold."""
    try:
        signed = proof.sign(record, secret, created)
    except proof.ProofError as e:
        raise RecordError(str(e)) from None
    check(signed)
    return signed


def record_hash(record: Dict[str, Any]) -> str:
    """SHA-256 of `record`'s RFC 8785 form, proof included."""
    return hashlib.sha256(canonical(record)).hexdigest()
