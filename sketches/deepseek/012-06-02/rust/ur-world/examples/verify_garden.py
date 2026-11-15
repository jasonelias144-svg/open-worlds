"""
verify_garden.py — external verification, from Python.

Self-contained: standard library + `cryptography`.
No arc Python code imported.

JCS note: for the garden's record shapes (ASCII keys,
integer / string / array values, no floats), Python's
`json.dumps(obj, sort_keys=True, separators=(',', ':'),
ensure_ascii=False)` produces bytes identical to RFC 8785.
A stricter implementation would use `canonicaljson` or
`rfc8785`; the substitution is honest because the record
schema forbids the cases where the two differ (floats,
astral chars in keys).

Usage:
    python3 verify_garden.py http://127.0.0.1:8765
"""

import hashlib
import json
import sys
import urllib.error
import urllib.request

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)


# ── Base58 (inline; Bitcoin alphabet) ─────────────────────
_B58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s: str) -> bytes:
    n = 0
    for c in s.encode():
        idx = _B58.find(bytes([c]))
        if idx < 0:
            raise ValueError(f"invalid base58 char: {chr(c)!r}")
        n = n * 58 + idx
    by = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + by


def _multikey_bytes(multikey: str) -> bytes:
    if not multikey.startswith("z"):
        raise ValueError(f"multikey must start with 'z', "
                         f"got {multikey[:1]!r}")
    return b58decode(multikey[1:])


# ── JCS (RFC 8785, for our record shapes) ─────────────────
def jcs(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def sha256_hex(b: bytes) -> str:
    return sha256(b).hex()


# ── DID → Ed25519 public key ──────────────────────────────
def did_key_to_verifying_key(did: str) -> Ed25519PublicKey:
    if not did.startswith("did:key:z"):
        raise ValueError(f"unsupported DID: {did}")
    raw = _multikey_bytes(did[len("did:key:"):])
    if len(raw) != 34 or raw[0] != 0xED or raw[1] != 0x01:
        raise ValueError("DID is not an Ed25519 public key")
    return Ed25519PublicKey.from_public_bytes(raw[2:])


# ── W3C DataIntegrity proof (eddsa-jcs-2022) ──────────────
def verify_proof(body: dict, proof: dict, expected_did: str) -> None:
    """Raises InvalidSignature or ValueError on failure."""
    pv = proof.get("proofValue")
    if not isinstance(pv, str):
        raise ValueError("proof missing proofValue")
    if not pv.startswith("z"):
        raise ValueError(f"proofValue must start with 'z': "
                         f"{pv[:1]!r}")
    sig_bytes = b58decode(pv[1:])
    if len(sig_bytes) != 64:
        raise ValueError(f"signature length {len(sig_bytes)} != 64")

    vm = proof.get("verificationMethod", "")
    did = vm.split("#", 1)[0]
    if did != expected_did:
        raise ValueError(
            f"verificationMethod {did} != expected {expected_did}")

    # eddsa-jcs-2022 payload:
    #   SHA256(JCS(proofOptions)) || SHA256(JCS(document))
    options = {k: v for k, v in proof.items() if k != "proofValue"}
    payload = sha256(jcs(options)) + sha256(jcs(body))

    vk = did_key_to_verifying_key(expected_did)
    vk.verify(sig_bytes, payload)  # raises InvalidSignature


# ── HTTP ──────────────────────────────────────────────────
def fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        raise RuntimeError(f"GET {url}: {e}") from e


# ── State reconstruction (from log alone) ─────────────────
def apply_to_state(body: dict, state: dict) -> None:
    kind = body.get("kind")
    if kind == "plant_added":
        state["plants"][body["plant_id"]] = list(body["position"])
    elif kind == "plant_retired":
        state["plants"].pop(body["plant_id"], None)
    elif kind in ("agent_entered", "agent_walked"):
        pos = body.get("position") or body.get("to")
        state["agents"][body["actor"]] = list(pos)
    elif kind == "cycle_advanced":
        state["cycle"] = body.get("cycle", state["cycle"])
    # proposals, whispers, observations, refusals: no state effect


# ── The verifier ──────────────────────────────────────────
def verify(base: str) -> str:
    # 1. Manifest
    manifest = fetch_json(f"{base}/manifest")
    m_body, m_proof = manifest["manifest"], manifest["proof"]
    m_did = m_proof["verificationMethod"].split("#", 1)[0]
    verify_proof(m_body, m_proof, m_did)
    print(f"  ✓ manifest proof verifies against {m_did}")

    # 2. Signed log
    log = fetch_json(f"{base}/signed-log")
    entries = log["entries"]
    print(f"  ✓ fetched {len(entries)} entries")

    # 3. Per-entry
    prev = None
    state = {"cycle": 0, "plants": {}, "agents": {}}
    for i, entry in enumerate(entries):
        body, proof = entry["body"], entry["proof"]
        actor = body["actor"]

        verify_proof(body, proof, actor)

        if sha256_hex(jcs(body)) != entry["hash"]:
            raise ValueError(
                f"entry[{i}]: hash mismatch "
                f"(stored {entry['hash']}, "
                f"computed {sha256_hex(jcs(body))})")

        if entry["prev"] != prev:
            raise ValueError(
                f"entry[{i}]: prev mismatch "
                f"(stored {entry['prev']}, chain {prev})")

        apply_to_state(body, state)
        prev = entry["hash"]

    print(f"  ✓ all {len(entries)} entry proofs verify")
    print(f"  ✓ all {len(entries)} chain links verify")

    # 4. Reconstruct
    out = [
        "  Reconstructed from log:",
        f"    cycle:  {state['cycle']}",
        f"    plants: {len(state['plants'])}",
    ]
    for pid, pos in sorted(state["plants"].items()):
        out.append(f"      {pid}: {pos}")
    out.append(f"    agents: {len(state['agents'])}")
    for did, pos in sorted(state["agents"].items()):
        short = did if len(did) <= 32 else did[:29] + "..."
        out.append(f"      {short}: {pos}")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: verify_garden.py <url>", file=sys.stderr)
        return 2
    base = sys.argv[1].rstrip("/")
    try:
        summary = verify(base)
    except (InvalidSignature, ValueError, RuntimeError) as e:
        print("=== External verification (Python): FAILED ===")
        print(f"  {e}")
        return 1
    print()
    print("=== External verification (Python): PASSED ===")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
