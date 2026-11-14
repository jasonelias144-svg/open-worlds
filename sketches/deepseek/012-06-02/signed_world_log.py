"""
signed_world_log.py — world log entries signed by the world's key.

A SignedLogWorld wraps a base world and provides signed log
entries. Ed25519 is deterministic, so re-signing the same entry
produces the same signature — sign-on-read is safe.

The signed entry:
  body  = {timestamp, kind, actor_token, data, world_signer}
  sig   = sign(body) with world's keypair
  entry = {body, sig}

The signer (world_signer, a did:key) is included in the body, so
verification is: reconstruct body, look up signer's pubkey,
verify sig over body.

SignedLogWorldServer extends WorldProtocolServer with
GET /signed-log (standard /log still serves unsigned entries
for backward compat).
"""

import json
import threading
from http.server import BaseHTTPRequestHandler
from typing import List, Optional

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from multiverse_c13 import _canonical, _did_from_kp, _pubkey_from_did
from individual_bundle import _hash
from wcp_http_shim import WorldProtocolServer


def _sign_entry(world_kp, world_signer: str, e) -> dict:
    body = {
        "timestamp": e.timestamp,
        "kind": e.kind,
        "actor_token": e.actor_token,
        "data": e.data,
        "world_signer": world_signer,
    }
    sig = world_kp.sign(_canonical(body)).hex()
    return {"body": body, "sig": sig}


def verify_signed_entry(
    entry: dict,
    expected_world_signer: Optional[str] = None,
) -> tuple:
    """Verify the world's signature on a signed log entry.
    Never raises."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    try:
        body = entry["body"]
        sig = entry["sig"]
        signer = body["world_signer"]
    except (KeyError, TypeError):
        return (False, "malformed signed entry")
    if expected_world_signer is not None \
            and signer != expected_world_signer:
        return (False,
                 f"signer {signer[:16]}... != expected "
                 f"{expected_world_signer[:16]}...")
    try:
        _pubkey_from_did(signer).verify(
            bytes.fromhex(sig), _canonical(body))
        return (True, "signed entry verifies")
    except Exception:
        return (False, "signature invalid")


def signed_entry_hash(entry: dict) -> str:
    return _hash(entry)


class SignedLogWorld:
    def __init__(self, base_world, signer_kp):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._base = base_world
        self._kp = signer_kp
        self._world_signer = _did_from_kp(signer_kp)

    @property
    def world_signer(self) -> str:
        return self._world_signer

    # -- Delegation ------------------------------------------

    def manifest(self):
        return self._base.manifest()

    def petition(self, p):
        return self._base.petition(p)

    def act(self, a):
        return self._base.act(a)

    def log_since(self, since=None):
        return self._base.log_since(since)

    # -- Signed log ------------------------------------------

    def signed_log_since(self, since=None) -> List[dict]:
        raw = self._base.log_since(since)
        return [_sign_entry(self._kp, self._world_signer, e)
                for e in raw]


class SignedLogWorldServer(WorldProtocolServer):
    def __init__(self, signed_world: SignedLogWorld,
                 port: int = 0):
        self._signed_world = signed_world
        super().__init__(signed_world, port=port)

    def _make_handler(self):
        base_handler = super()._make_handler()
        signed = self._signed_world

        class Handler(base_handler):
            def do_GET(self):
                from urllib.parse import urlparse, parse_qs
                url = urlparse(self.path)
                if url.path == "/signed-log":
                    qs = parse_qs(url.query)
                    since = qs.get("since", [None])[0]
                    try:
                        entries = signed.signed_log_since(since)
                        body = json.dumps(
                            {"entries": entries}).encode()
                        self.send_response(200)
                        self.send_header(
                            "Content-Type", "application/json")
                        self.send_header("Content-Length",
                                          str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                    except Exception as e:
                        body = json.dumps(
                            {"error": str(e)}).encode()
                        self.send_response(500)
                        self.send_header(
                            "Content-Type", "application/json")
                        self.send_header("Content-Length",
                                          str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                    return
                super().do_GET()

        return Handler
