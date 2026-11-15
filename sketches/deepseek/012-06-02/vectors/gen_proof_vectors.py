"""
gen_proof_vectors.py — generate vectors/proof_cases.json.

Uses a fixed Ed25519 seed so the output is deterministic.
Each case's proof is signed over its own (possibly malformed)
options; the signature is *valid* for what's there. Only
metadata checking (or DID/body matching) rejects the case.

Usage:
    python3 vectors/gen_proof_vectors.py
"""

import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives import serialization


_B58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    if n == 0:
        return "1" * len(data)
    out = []
    while n:
        out.append(_B58[n % 58])
        n //= 58
    pad = len(data) - len(data.lstrip(b"\x00"))
    return ("1" * pad) + bytes(reversed(out)).decode()


def jcs(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def sha256(b: bytes) -> bytes:
    import hashlib
    return hashlib.sha256(b).digest()


def _make_did(pub_bytes: bytes) -> str:
    return "did:key:z" + b58encode(b"\xed\x01" + pub_bytes)


def _sign_over(options: dict, body: dict, priv) -> str:
    payload = sha256(jcs(options)) + sha256(jcs(body))
    return "z" + b58encode(priv.sign(payload))


def make_case(
    case_id: str, description: str,
    body: dict, options: dict, signer,
    expected: str, expected_did: str,
) -> dict:
    proof = dict(options)
    proof["proofValue"] = _sign_over(options, body, signer)
    return {
        "id": case_id,
        "description": description,
        "body": body,
        "proof": proof,
        "expected_did": expected_did,
        "expected": expected,
    }


def generate() -> dict:
    seed = bytes([42]) * 32
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    did = _make_did(pub)
    base_options = {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "created": "2026-11-15T00:00:00Z",
        "verificationMethod": f"{did}#{did}",
        "proofPurpose": "assertionMethod",
    }
    body = {"kind": "test", "value": 42}

    cases = [make_case(
        "valid", "Well-formed proof", body,
        base_options, priv, "pass", did)]

    for case_id, description, mutate in [
        ("wrong_type", "type is not DataIntegrityProof",
            lambda o: o.update(type="SomeOtherProof")),
        ("wrong_cryptosuite",
            "cryptosuite is not eddsa-jcs-2022",
            lambda o: o.update(cryptosuite="eddsa-rdfc-2022")),
        ("wrong_purpose",
            "proofPurpose is authentication",
            lambda o: o.update(proofPurpose="authentication")),
    ]:
        opts = dict(base_options)
        mutate(opts)
        cases.append(make_case(
            case_id, description, body, opts, priv,
            "fail", did))

    for case_id, key in [
        ("missing_type", "type"),
        ("missing_cryptosuite", "cryptosuite"),
        ("missing_purpose", "proofPurpose"),
        ("missing_created", "created"),
    ]:
        opts = dict(base_options)
        del opts[key]
        cases.append(make_case(
            case_id, f"{key} missing", body, opts, priv,
            "fail", did))

    # Signature-level failures
    c = make_case(
        "tampered_signature", "signature replaced with zeros",
        body, base_options, priv, "pass", did)
    c["proof"]["proofValue"] = "z" + b58encode(bytes(64))
    c["expected"] = "fail"
    cases.append(c)

    c = make_case(
        "tampered_body", "body mutated after signing",
        body, base_options, priv, "pass", did)
    c["body"] = {"kind": "test", "value": 999}
    c["expected"] = "fail"
    cases.append(c)

    # DID-binding failures
    other_priv = Ed25519PrivateKey.from_private_bytes(
        bytes([99]) * 32)
    other_pub = other_priv.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    other_did = _make_did(other_pub)
    c = make_case(
        "wrong_did", "expected_did differs from verificationMethod",
        body, base_options, priv, "pass", did)
    c["expected_did"] = other_did
    c["expected"] = "fail"
    cases.append(c)

    # Encoding failures
    c = make_case(
        "no_z_prefix", "proofValue missing 'z' prefix",
        body, base_options, priv, "pass", did)
    c["proof"]["proofValue"] = c["proof"]["proofValue"][1:]
    c["expected"] = "fail"
    cases.append(c)

    return {
        "kind": "proof_vector",
        "version": "1.0",
        "description": (
            "Cross-implementation test cases for "
            "eddsa-jcs-2022. Every verify_proof implementation "
            "must produce the verdict in 'expected'."),
        "identity": {
            "seed_hex": seed.hex(),
            "did": did,
        },
        "cases": cases,
    }


def main():
    out = Path(__file__).parent / "proof_cases.json"
    out.write_text(json.dumps(generate(), indent=2))
    print(f"wrote {out}")
    print(f"  cases: {len(generate()['cases'])}")


if __name__ == "__main__":
    main()
