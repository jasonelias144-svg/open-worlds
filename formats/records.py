"""The records the offices keep (course step 2): a grant, a decision
record, a suggestion, a rating, and a signed log head.

Each record's shape is in one JSON Schema (2020-12) that Python and Rust
both read, schemas/records-v1.schema.json, and each is signed with
`eddsa-jcs-2022` (formats/proof.py). A record holds when:

1. it fits the schema for the kind its `format` names;
2. its proof verifies;
3. it was signed by the one who must sign that kind: a grant by its
   issuer, a decision by the office's key, a suggestion and a rating by
   their author, a log head by its world.

What the schema can't say (that a grant only narrows the grant it names,
that a decision's inputs are in the log) is checked where the records
meet the kernel, at course step 4.

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

from . import proof
from .canonical import canonical
from .multikey import did_key

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
    if pattern.endswith("$") and not pattern.endswith("\\$"):
        pattern = pattern[:-1] + "\\Z"
    if not re.search(pattern, instance):
        yield ValidationError(f"{instance!r} doesn't match {pattern!r}")


_Validator = jsonschema.validators.extend(
    jsonschema.Draft202012Validator, {"pattern": _ecma_pattern})


def _validator(name: str) -> Any:
    return _Validator({"$schema": SCHEMA["$schema"],
                       "$defs": SCHEMA["$defs"],
                       "$ref": f"#/$defs/{name}"})


_VALIDATORS = {fmt: _validator(name) for fmt, (name, _) in KINDS.items()}


def problems(record: Any) -> List[str]:
    """Where `record` doesn't fit its kind's schema, or [] if it does."""
    if type(record) is not dict or record.get("format") not in KINDS:
        return ["$: not a record of a kind in records-v1"]
    errors = _VALIDATORS[record["format"]].iter_errors(record)
    return sorted(
        f"$.{'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
        if e.absolute_path else f"$: {e.message}" for e in errors)


def signer_field(record: Dict[str, Any]) -> Any:
    """The value of the field that names who must sign `record`."""
    value: Any = record
    for key in KINDS[record["format"]][1]:
        value = value[key]
    return value


def check(record: Any) -> Dict[str, Any]:
    """`record` without its proof, if it holds; otherwise RecordError."""
    found = problems(record)
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
