"""Signing a record so that standard tools can check it: a Data Integrity
proof with the `eddsa-jcs-2022` cryptosuite (W3C Recommendation, "Data
Integrity EdDSA Cryptosuites v1.0", 15 May 2025, section 3.3).

What is signed is not the record's bytes alone. The proof's options
(its type, suite, time, key and purpose) and the record are each written
in RFC 8785 form and hashed with SHA-256, and the Ed25519 signature is
over the options' hash followed by the record's hash. The proof goes
into the record as `proof`, with the signature in `proofValue`, base58-btc.

This module follows the specification's steps, and is checked against
the specification's own test vectors (Appendix B.3) and this project's
(vectors/formats). What it reads more narrowly than the specification:

- one proof per record, never a set or a chain;
- `verificationMethod` is a did:key, whose key is in the identifier, so
  nothing is looked up;
- `created` is written `YYYY-MM-DDTHH:MM:SSZ`, in UTC;
- every value keeps this project's rules (formats/canonical.py).

Signing and verifying are done by `cryptography`, through
multiverse/ed25519.py, which also refuses weak public keys.
"""
from __future__ import annotations

import datetime
import hashlib
import re
from typing import Any, Dict, Tuple

from multiverse import ed25519

from .canonical import FormatError, canonical
from .multikey import (KeyFormatError, base58btc_decode, base58btc_encode,
                       public_from_verification_method, verification_method)

TYPE = "DataIntegrityProof"
CRYPTOSUITE = "eddsa-jcs-2022"


class ProofError(ValueError):
    """A proof that can't be made, or doesn't hold."""


_TIME = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})Z")


def _check_created(created: Any) -> None:
    """The shape first, in ASCII digits only (`strptime` would also take
    other scripts' digits), then the calendar: years 0001 to 9999, as the
    Rust code reads them."""
    if type(created) is not str:
        raise ProofError("created must be text")
    shape = _TIME.fullmatch(created)
    try:
        if not shape:
            raise ValueError
        datetime.datetime(*(int(part) for part in shape.groups()))
    except ValueError:
        raise ProofError("created is written YYYY-MM-DDTHH:MM:SSZ") from None


def _check_options(options: Dict[str, Any]) -> None:
    if (options.get("type") != TYPE
            or options.get("cryptosuite") != CRYPTOSUITE):
        raise ProofError(f"not a {TYPE} with {CRYPTOSUITE}")
    _check_created(options.get("created"))
    if type(options.get("proofPurpose")) is not str:
        raise ProofError("proofPurpose must be text")


def _hash_data(document: Dict[str, Any], options: Dict[str, Any]) -> bytes:
    """Section 3.3.4: SHA-256 of the options, then SHA-256 of the record,
    each in RFC 8785 form."""
    try:
        return (hashlib.sha256(canonical(options)).digest()
                + hashlib.sha256(canonical(document)).digest())
    except FormatError as e:
        raise ProofError(str(e)) from None


def _same_values(a: Any, b: Any) -> bool:
    """Whether two values are the same JSON: compared in RFC 8785 form,
    since in Python True == 1 == 1.0."""
    try:
        return canonical(a) == canonical(b)
    except FormatError:
        return False


def sign(document: Dict[str, Any], secret: bytes, created: str,
         purpose: str = "assertionMethod") -> Dict[str, Any]:
    """`document` with an `eddsa-jcs-2022` proof by the holder of the
    32-byte Ed25519 `secret`, made at `created`. Section 3.3.1."""
    if type(document) is not dict or "proof" in document:
        raise ProofError("sign a record (an object) with no proof yet")
    if "@context" in document and type(document["@context"]) is not list:
        raise ProofError("an @context is read only as a list")
    proof: Dict[str, Any] = {
        "type": TYPE,
        "cryptosuite": CRYPTOSUITE,
        "created": created,
        "verificationMethod": verification_method(ed25519.public_key(secret)),
        "proofPurpose": purpose,
    }
    if "@context" in document:
        proof["@context"] = document["@context"]
    _check_options(proof)
    signature = ed25519.sign(secret, _hash_data(document, proof))
    value = "z" + base58btc_encode(signature)
    return {**document, "proof": {**proof, "proofValue": value}}


def verify(secured: Dict[str, Any]) -> Tuple[Dict[str, Any], bytes]:
    """The record without its proof, and the public key that signed it,
    if `secured`'s proof holds; otherwise ProofError. Section 3.3.2.

    Who signed is part of the answer: a proof shows that the holder of
    that key signed, and the caller decides whether that key was the one
    that should have. Use the record returned, never `secured` itself:
    the specification lets a record carry more @context entries than its
    proof, and those are dropped from what was verified."""
    if type(secured) is not dict or type(secured.get("proof")) is not dict:
        raise ProofError("a record with one proof (an object) is read")
    unsecured = {k: v for k, v in secured.items() if k != "proof"}
    options = {k: v for k, v in secured["proof"].items() if k != "proofValue"}
    value = secured["proof"].get("proofValue")
    if type(value) is not str or not value.startswith("z"):
        raise ProofError("proofValue must be base58-btc, starting with z")
    try:
        signature = base58btc_decode(value[1:])
    except KeyFormatError as e:
        raise ProofError(str(e)) from None
    if len(signature) != 64 or "z" + base58btc_encode(signature) != value:
        raise ProofError("proofValue isn't one 64-byte signature")
    if "@context" in options:
        context = options["@context"]
        held = secured.get("@context")
        if (type(context) is not list or type(held) is not list
                or not _same_values(held[:len(context)], context)):
            raise ProofError("the record's @context doesn't start with "
                             "the proof's")
        unsecured["@context"] = context
    _check_options(options)
    try:
        public = public_from_verification_method(
            options.get("verificationMethod"))
    except KeyFormatError as e:
        raise ProofError(str(e)) from None
    if not ed25519.verify(public, _hash_data(unsecured, options), signature):
        raise ProofError("the signature doesn't hold")
    return unsecured, public
