import base64
import hashlib
import json
import subprocess
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives import serialization

# Import the verifier module
sys.path.insert(0, "rust/ur-world/examples")
from verify_garden import (
    check_proof_metadata,
    verify_proof,
    jcs,
    sha256,
    b58encode,  # need to add
)


def _test_identity():
    seed = bytes([42]) * 32
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    pub_bytes = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    multikey = b"\xed\x01" + pub_bytes
    did = "did:key:z" + b58encode(multikey)
    return did, priv


def _b58encode(data: bytes) -> str:
    alphabet = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int.from_bytes(data, "big")
    if n == 0:
        return "1" * len(data)
    out = []
    while n:
        out.append(alphabet[n % 58])
        n //= 58
    pad = len(data) - len(data.lstrip(b"\x00"))
    return ("1" * pad) + bytes(reversed(out)).decode()


# Add b58encode to the verify_garden module if not present


def _signed_proof(options: dict, body: dict, priv) -> dict:
    options_jcs = jcs(options)
    body_jcs = jcs(body)
    payload = sha256(options_jcs) + sha256(body_jcs)
    sig = priv.sign(payload)
    return {**options, "proofValue": "z" + _b58encode(sig)}


def _default_options(did: str) -> dict:
    return {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "created": "2026-11-15T00:00:00Z",
        "verificationMethod": f"{did}#{did}",
        "proofPurpose": "assertionMethod",
    }


def _default_body(did: str) -> dict:
    return {"kind": "test", "actor": did}


def test_valid_proof_verifies():
    did, priv = _test_identity()
    body = _default_body(did)
    proof = _signed_proof(_default_options(did), body, priv)
    verify_proof(body, proof, did)  # no exception


def test_wrong_type_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    opts = _default_options(did)
    opts["type"] = "SomeOtherProof"
    proof = _signed_proof(opts, body, priv)
    with pytest.raises(ValueError, match="proof.type"):
        verify_proof(body, proof, did)


def test_wrong_cryptosuite_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    opts = _default_options(did)
    opts["cryptosuite"] = "eddsa-rdfc-2022"
    proof = _signed_proof(opts, body, priv)
    with pytest.raises(ValueError, match="cryptosuite"):
        verify_proof(body, proof, did)


def test_wrong_purpose_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    opts = _default_options(did)
    opts["proofPurpose"] = "authentication"
    proof = _signed_proof(opts, body, priv)
    with pytest.raises(ValueError, match="proofPurpose"):
        verify_proof(body, proof, did)


def test_missing_type_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    opts = _default_options(did)
    del opts["type"]
    proof = _signed_proof(opts, body, priv)
    with pytest.raises(ValueError, match="proof.type"):
        verify_proof(body, proof, did)


def test_missing_cryptosuite_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    opts = _default_options(did)
    del opts["cryptosuite"]
    proof = _signed_proof(opts, body, priv)
    with pytest.raises(ValueError, match="cryptosuite"):
        verify_proof(body, proof, did)


def test_missing_purpose_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    opts = _default_options(did)
    del opts["proofPurpose"]
    proof = _signed_proof(opts, body, priv)
    with pytest.raises(ValueError, match="proofPurpose"):
        verify_proof(body, proof, did)


def test_missing_created_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    opts = _default_options(did)
    del opts["created"]
    proof = _signed_proof(opts, body, priv)
    with pytest.raises(ValueError, match="created"):
        verify_proof(body, proof, did)


def test_tampered_signature_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    proof = _signed_proof(_default_options(did), body, priv)
    proof["proofValue"] = "z" + "1" * 88
    with pytest.raises(Exception):
        verify_proof(body, proof, did)


def test_wrong_did_rejected():
    did, priv = _test_identity()
    body = _default_body(did)
    proof = _signed_proof(_default_options(did), body, priv)
    # Different DID
    other_priv = Ed25519PrivateKey.from_private_bytes(
        bytes([99]) * 32)
    other_pub = other_priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    other_did = "did:key:z" + _b58encode(
        b"\xed\x01" + other_pub)
    with pytest.raises(ValueError, match="verificationMethod"):
        verify_proof(body, proof, other_did)
