"""The records the offices keep (course step 2): a grant, a decision
record, a suggestion, a rating, and a signed log head; the records an
individual is given or keeps sealed: a world-key and a journal entry
(sealed with formats/sealed.py); the records of who an individual and a
world are: identity, birth records and the mind record; a world's
template, with its dials; and the project's key list.

Each record's shape is in one JSON Schema (2020-12) that Python and Rust
both read, schemas/records-v1.schema.json, and each is signed with
`eddsa-jcs-2022` (formats/proof.py). A record holds when:

1. it fits the schema for the kind its `format` names;
2. its proof verifies;
3. it was signed by the one who must sign that kind: a grant, a
   world-key, a mind record and a template by their issuer, a decision by the
   office's key, a suggestion, a rating and a journal entry by their
   author, a log head and a birth record (an individual's or a world's)
   by its world, and an identity by its own key.

What the schema can't say is checked where the records meet the kernel,
at course step 4: that a grant only narrows the grant it names; that a
decision's inputs are in the log, its office holds the grant it names,
and that grant allows its kind of act; that a rating's author wrote the
suggestion it names, and its outcome is a decision that names that
suggestion; that a world-key's issuer is a world that places paths,
its path was placed in that world's log and walked to its end by its
holder, and it hasn't already been used to found a world
(docs/WORLD-KEY.md: "It is marked as used at the founding"); that an
identity's `birth` is a birth record of the same individual and name;
that a birth record's `mind` is a mind record of the one born, and its
`world` is a world; that a mind record's issuer is the project's key
for mind records, and a template's the project's key for templates,
both published at course step 3; and that a world's
founding is confirmed by its founders and its parent world, in records
of their own (course step 12).

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
    "open-worlds/template/v1": ("template", ("issuer",)),
    "open-worlds/key-list/v1": ("keyList", ("issuer",)),
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
    and a mind record's engines are in the order they began, each naming
    a file once; the schema checks only their shape."""
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
        for i, engine in enumerate(engines):
            paths = [f["path"] for f in engine["files"]]
            if len(set(paths)) != len(paths):
                found.append(f"$.engines.{i}.files: a path named twice")
    return found


def _sealing_key_problem(where: str, text: str) -> List[str]:
    try:
        seal.check_public(sealing_from_multikey(text))
    except (KeyFormatError, seal.SealError) as e:
        return [f"{where}: {e}"]
    return []


def _key_problems(record: Dict[str, Any]) -> List[str]:
    """A sealing key must be one it is safe to seal to (formats/seal.py),
    and a key list must name one root, each key once, and, in its first
    version, be signed by that root; the schema checks only shapes."""
    fmt = record.get("format")
    if fmt == "open-worlds/identity/v1":
        return _sealing_key_problem("$.sealingKey", record["sealingKey"])
    if fmt != "open-worlds/key-list/v1":
        return []
    found = []
    entries = record["keys"]
    roots = [e for e in entries if e["role"] == "root"]
    if len(roots) != 1:
        found.append("$.keys: not exactly one root")
    elif record["version"] == 1 and record["issuer"] != roots[0]["signing"]:
        found.append("$.issuer: the first version must be signed by its "
                     "own root")
    seen = set()
    for i, e in enumerate(entries):
        for what in ((e["role"], e["name"]), e["signing"],
                     e.get("sealing")):
            if what is None:
                continue
            if what in seen:
                found.append(f"$.keys.{i}: a role, name or key named "
                             "twice")
            seen.add(what)
        if "sealing" in e:
            found += _sealing_key_problem(f"$.keys.{i}.sealing",
                                          e["sealing"])
    return found


def _range_problems(record: Dict[str, Any]) -> List[str]:
    """A template's dial must have room to turn, and its value must be
    within its range; the schema checks only that min and max come
    together."""
    if record.get("format") != "open-worlds/template/v1":
        return []
    found = []
    for name, p in sorted(record["parameters"].items()):
        if "min" not in p:
            continue
        if p["min"] >= p["max"]:
            found.append(f"$.parameters.{name}: min is not below max")
        elif not p["min"] <= p["value"] <= p["max"]:
            found.append(f"$.parameters.{name}: value is outside its range")
    return found


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
        found = (_time_problems(record) + _key_problems(record)
                 + _range_problems(record))
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


def key_list_root(key_list: Dict[str, Any]) -> str:
    """The did:key of the root a key list names."""
    return next(e["signing"] for e in key_list["keys"]
                if e["role"] == "root")


def key_list_problems(new: Dict[str, Any],
                      previous: Dict[str, Any]) -> List[str]:
    """Where a key list fails to follow the version before it, or []: it
    must name that version by hash, be the next number, and be signed by
    that version's root. So a new root is named by the old one, and signs
    the version after. Both lists must hold."""
    for record in (new, previous):
        check(record)
        if record["format"] != "open-worlds/key-list/v1":
            raise RecordError("$.format: not open-worlds/key-list/v1")
    found = []
    if new.get("previous") != record_hash(previous):
        found.append("$.previous: names another version")
    if new["version"] != previous["version"] + 1:
        found.append("$.version: not the next version")
    if new["issuer"] != key_list_root(previous):
        found.append("$.issuer: not the root of the version before")
    return found


def dial_problems(world_birth: Dict[str, Any],
                  template: Dict[str, Any]) -> List[str]:
    """Where a world's birth record and the template it names disagree,
    or [] if they agree: it must name that template by hash, and each
    dial it set must be one of the template's dials, within its range,
    and changed from the template's own value, so two worlds made the
    same way have the same dials. Both records must hold."""
    for record, kind in ((world_birth, "open-worlds/world-birth/v1"),
                         (template, "open-worlds/template/v1")):
        check(record)
        if record["format"] != kind:
            raise RecordError(f"$.format: not {kind}")
    if "template" not in world_birth:
        return ["$.template: names no template"]
    if world_birth["template"] != record_hash(template):
        return ["$.template: names another template"]
    found = []
    parameters = template["parameters"]
    for name, value in sorted(world_birth.get("dials", {}).items()):
        p = parameters.get(name)
        if p is None:
            found.append(f"$.dials.{name}: not a parameter of the template")
        elif "min" not in p:
            found.append(f"$.dials.{name}: fixed in the template, not a dial")
        elif not p["min"] <= value <= p["max"]:
            found.append(f"$.dials.{name}: outside the dial's range")
        elif value == p["value"]:
            found.append(f"$.dials.{name}: set to the template's own value")
    return found
