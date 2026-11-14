"""Test vectors for records signed with `eddsa-jcs-2022`, kept in
vectors/formats so that code in any language can check itself against
them (vectors/README.md; the Rust crate in rust/formats reads them).

    python3 -m formats.vectors      rewrite vectors/formats from this code

tests/test_formats.py checks that the file is still exactly what this
code writes. It holds:

- `w3c`: the specification's own example (Appendix B.3), each step's
  value as the specification gives it;
- `signed`: records this project signs, each with its RFC 8785 form;
- `refused`: secured records whose proof must not hold, each with why;
- `refusedValues`: JSON texts that break this project's three rules.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from multiverse import ed25519

from . import proof
from .canonical import canonical
from .multikey import (base58btc_encode, public_multikey, secret_multikey,
                       verification_method)

FILE = (Path(__file__).resolve().parent.parent
        / "vectors" / "formats" / "eddsa-jcs-2022.json")

#: A key for test vectors only, public to everyone, never for anything real.
TEST_SECRET = hashlib.sha256(
    b"open-worlds: a key for test vectors only, never for anything real"
).digest()
CREATED = "2026-11-14T00:00:00Z"

W3C_CONTEXT = ["https://www.w3.org/ns/credentials/v2",
               "https://www.w3.org/ns/credentials/examples/v2"]
W3C_DOCUMENT = {
    "@context": W3C_CONTEXT,
    "id": "urn:uuid:58172aac-d8ba-11ed-83dd-0b3aef56cc33",
    "type": ["VerifiableCredential", "AlumniCredential"],
    "name": "Alumni Credential",
    "description": "A minimum viable example of an Alumni Credential.",
    "issuer": "https://vc.example/issuers/5678",
    "validFrom": "2023-01-01T00:00:00Z",
    "credentialSubject": {"id": "did:example:abcdefgh",
                          "alumniOf": "The School of Examples"},
}


def _w3c() -> Dict[str, Any]:
    """The specification's example, every value as Appendix B.3 prints
    it; tests/test_formats.py checks that this code reproduces each."""
    return {
        "source": ("W3C, Data Integrity EdDSA Cryptosuites v1.0, "
                   "Recommendation of 15 May 2025, Appendix B.3, "
                   "https://www.w3.org/TR/vc-di-eddsa/ ; W3C Software and "
                   "Document License, "
                   "https://www.w3.org/copyright/software-license-2023/"),
        "publicKeyMultibase":
            "z6MkrJVnaZkeFzdQyMZu1cgjg7k1pZZ6pvBQ7XJPt4swbTQ2",
        "secretKeyMultibase":
            "z3u2en7t5LR2WtQH5PfFqMqwVHBeXouLzo6haApm8XHqvjxq",
        "document": W3C_DOCUMENT,
        "created": "2023-02-24T23:36:38Z",
        "canonicalDocument": (
            '{"@context":["https://www.w3.org/ns/credentials/v2",'
            '"https://www.w3.org/ns/credentials/examples/v2"],'
            '"credentialSubject":{"alumniOf":"The School of Examples",'
            '"id":"did:example:abcdefgh"},"description":"A minimum viable '
            'example of an Alumni Credential.","id":"urn:uuid:58172aac-'
            'd8ba-11ed-83dd-0b3aef56cc33","issuer":"https://vc.example/'
            'issuers/5678","name":"Alumni Credential","type":'
            '["VerifiableCredential","AlumniCredential"],"validFrom":'
            '"2023-01-01T00:00:00Z"}'),
        "documentHash":
            "59b7cb6251b8991add1ce0bc83107e3db9dbbab5bd2c28f687db1a03abc92f19",
        "canonicalOptions": (
            '{"@context":["https://www.w3.org/ns/credentials/v2",'
            '"https://www.w3.org/ns/credentials/examples/v2"],"created":'
            '"2023-02-24T23:36:38Z","cryptosuite":"eddsa-jcs-2022",'
            '"proofPurpose":"assertionMethod","type":"DataIntegrityProof",'
            '"verificationMethod":"did:key:z6MkrJVnaZkeFzdQyMZu1cgjg7k1pZZ6'
            'pvBQ7XJPt4swbTQ2#z6MkrJVnaZkeFzdQyMZu1cgjg7k1pZZ6pvBQ7XJPt4sw'
            'bTQ2"}'),
        "optionsHash":
            "66ab154f5c2890a140cb8388a22a160454f80575f6eae09e5a097cabe539a1db",
        "signature": (
            "407cd12654b33d718ecbb99179a1506daaa849450bf3fc523cce3e1c96f8b8"
            "0351da3f253d725c6f00b07c9e5448d50b3ef78012b9ab54255116d069c6dd"
            "2808"),
        "proofValue": ("z2HnFSSPPBzR36zdDgK8PbEHeXbR56YF24jwMpt3R1eHXQzJDMWS93"
                       "FCzpvJpwTWd3GAVFuUfjoJdcnTMuVor51aX"),
    }


def _records() -> List[Dict[str, Any]]:
    return [
        {"name": "text outside ASCII, integers at the bounds, nesting",
         "document": {
             "format": "open-worlds/example/v1",
             "text": "Café, \U0001f642, a line separator, a "
                     "tab\tand a quote \"",
             "most": 2 ** 53 - 1,
             "least": -(2 ** 53 - 1),
             "list": [True, False, None, {"b": 1, "a": 2}, []],
             "empty": {}}},
        {"name": "a record with an @context, copied into its proof",
         "document": {"@context": ["https://example.org/a",
                                   "https://example.org/b"],
                      "format": "open-worlds/example/v1",
                      "text": "Hello, ALICE."}},
        {"name": "made on a leap day, at the last second of it",
         "created": "2000-02-29T23:59:59Z",
         "document": {"format": "open-worlds/example/v1",
                      "text": "Hello, BOB."}},
    ]


def _signed() -> List[Dict[str, Any]]:
    out = []
    for case in _records():
        doc = case["document"]
        created = case.get("created", CREATED)
        out.append({
            "name": case["name"],
            "secretKeyMultibase": secret_multikey(TEST_SECRET),
            "publicKeyMultibase": public_multikey(
                ed25519.public_key(TEST_SECRET)),
            "created": created,
            "document": doc,
            "canonicalDocument": canonical(doc).decode("utf-8"),
            "signed": proof.sign(doc, TEST_SECRET, created),
        })
    return out


def _resign(secured: Dict[str, Any], **changes: Any) -> Dict[str, Any]:
    """`secured` with its proof options changed and signed again over the
    changed options, so only the change is wrong, not the signature."""
    options = {k: v for k, v in secured["proof"].items() if k != "proofValue"}
    options.update(changes)
    unsecured = {k: v for k, v in secured.items() if k != "proof"}
    data = proof._hash_data(unsecured, options)
    sig = ed25519.sign(TEST_SECRET, data)
    return {**unsecured,
            "proof": {**options, "proofValue": "z" + base58btc_encode(sig)}}


def _refused() -> List[Dict[str, Any]]:
    good = proof.sign(_records()[0]["document"], TEST_SECRET, CREATED)
    ctx = proof.sign(_records()[1]["document"], TEST_SECRET, CREATED)
    other = hashlib.sha256(b"open-worlds: another test key").digest()
    weak = bytes([1]) + bytes(31)   # the neutral point: a key of small order

    def changed(base: Dict[str, Any], **fields: Any) -> Dict[str, Any]:
        return {**base, **fields}

    def proof_changed(base: Dict[str, Any], **fields: Any) -> Dict[str, Any]:
        return {**base, "proof": {**base["proof"], **fields}}

    return [
        {"name": "a value changed after signing",
         "secured": changed(good, text="Cafe")},
        {"name": "a value added after signing",
         "secured": changed(good, extra=1)},
        {"name": "signed by another key than the one it names",
         "secured": proof_changed(
             good, verificationMethod=verification_method(
                 ed25519.public_key(other)))},
        {"name": "another cryptosuite",
         "secured": _resign(good, cryptosuite="eddsa-rdfc-2022")},
        {"name": "another proof type",
         "secured": _resign(good, type="Ed25519Signature2020")},
        {"name": "created with fractions of a second (this project's "
                 "narrower rule)",
         "secured": _resign(good, created="2026-11-14T00:00:00.000Z")},
        {"name": "a verification method that isn't did:key",
         "secured": _resign(good, verificationMethod="https://example.org/k")},
        {"name": "a did:key method whose fragment names another key",
         "secured": _resign(good, verificationMethod=(
             "did:key:" + public_multikey(ed25519.public_key(TEST_SECRET))
             + "#" + public_multikey(ed25519.public_key(other))))},
        {"name": "a weak key of small order, which anyone can sign for",
         "secured": proof_changed(
             good, verificationMethod=verification_method(weak),
             proofValue="z" + base58btc_encode(weak + bytes(32)))},
        {"name": "proofValue not in base58-btc",
         "secured": proof_changed(good, proofValue="u" + "A" * 86)},
        {"name": "proofValue one character short",
         "secured": proof_changed(
             good, proofValue=good["proof"]["proofValue"][:-1])},
        {"name": "the record's @context doesn't start with the proof's",
         "secured": changed(ctx, **{"@context": ["https://example.org/b",
                                                 "https://example.org/a"]})},
        {"name": "a proof set instead of one proof",
         "secured": changed(good, proof=[good["proof"]])},
        {"name": "no proofPurpose",
         "secured": proof_changed(
             _resign(good), proofPurpose=None)},
    ] + [
        {"name": f"created {created}: {why}",
         "secured": _resign(good, created=created)}
        for created, why in [
            ("2025-02-29T00:00:00Z", "no 29 February in 2025"),
            ("2100-02-29T00:00:00Z", "2100 isn't a leap year"),
            ("2026-13-01T00:00:00Z", "no thirteenth month"),
            ("2026-11-14T24:00:00Z", "no hour 24"),
            ("2026-11-14T00:00:60Z", "no leap seconds here"),
            ("0000-01-01T00:00:00Z", "no year 0"),
            ("2026-11-14T00:00:00z", "Z is upper case"),
            ("2026-11-14T00:00Z", "seconds are written"),
        ]
    ]


def _refused_values() -> List[Dict[str, str]]:
    return [
        {"name": "a float", "json": '{"a":1.5}'},
        {"name": "a float with no fraction", "json": '{"a":1.0}'},
        {"name": "an exponent", "json": '{"a":1e3}'},
        {"name": "an integer above 2^53 - 1",
         "json": '{"a":9007199254740992}'},
        {"name": "an integer below -(2^53 - 1)",
         "json": '{"a":-9007199254740992}'},
        {"name": "a key outside ASCII", "json": '{"café":1}'},
        {"name": "a nested float", "json": '{"a":[{"b":[0.5]}]}'},
    ]


def vectors() -> Dict[str, Any]:
    return {"w3c": _w3c(), "signed": _signed(), "refused": _refused(),
            "refusedValues": _refused_values()}


def text() -> str:
    """The file's exact text."""
    return json.dumps(vectors(), indent=1, ensure_ascii=False) + "\n"


def main() -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(text(), encoding="utf-8")
    print(f"wrote {FILE}")


if __name__ == "__main__":
    main()
