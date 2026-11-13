"""
multiverse_c13.py — Component 13: WCP/0.2 Signatures.

Extends WCP/0.1 with Ed25519 signatures on Admissions and Acks.
Every signing entity publishes a `public_key` in its manifest;
every response carries a `signature` verifiable against it.

The property that changes: forged admissions are now DETECTABLE.
Component 2's limitation — "forged is indistinguishable from real"
— is closed for signing entities. WCP/0.1 entities remain valid;
their responses are simply unverified.

The ONLY external dependency in the whole framework: `cryptography`.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Route, Ack,
)


def require_crypto():
    if not HAS_CRYPTO:
        raise ImportError(
            "WCP/0.2 requires the `cryptography` package. "
            "Install with: pip install cryptography")


# =====================================================================
# Canonical JSON — the one place the signing payload is defined
# =====================================================================

def canonical_bytes(obj: Any) -> bytes:
    """Stable JSON: sorted keys, no spaces, UTF-8."""
    return json.dumps(obj, sort_keys=True,
                      separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


# =====================================================================
# KeyPair
# =====================================================================

class KeyPair:
    """An Ed25519 keypair. The world holds the private key and
    publishes the public key. Clients verify signatures against it.
    """
    def __init__(self, private: Any):
        self._private = private
        self._public = private.public_key()

    @classmethod
    def generate(cls) -> "KeyPair":
        require_crypto()
        return cls(private=Ed25519PrivateKey.generate())

    def sign(self, payload: bytes) -> bytes:
        require_crypto()
        return self._private.sign(payload)

    def public_key_hex(self) -> str:
        require_crypto()
        return self._public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()


def verify_signature(public_key_hex: str, payload: bytes,
                     signature_hex: str) -> bool:
    """Verify an Ed25519 signature. True iff valid."""
    if not HAS_CRYPTO:
        return False
    try:
        pub = Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(public_key_hex))
        pub.verify(bytes.fromhex(signature_hex), payload)
        return True
    except (InvalidSignature, ValueError):
        return False


# =====================================================================
# Signed response types
# =====================================================================

@dataclass(frozen=True)
class SignedAdmission:
    entity_id: str
    timestamp: str
    subject_token: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "admission",
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "subject_token": self.subject_token,
        })

    def to_wcp_0_1(self) -> WCPAdmission:
        """Strip the signature for WCP/0.1 compatibility."""
        return WCPAdmission(entity_id=self.entity_id,
                            timestamp=self.timestamp)


@dataclass(frozen=True)
class SignedAck:
    entity_id: str
    timestamp: str
    subject_token: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "ack",
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "subject_token": self.subject_token,
        })

    def to_wcp_0_1(self) -> Ack:
        return Ack(entity_id=self.entity_id,
                   timestamp=self.timestamp)


# =====================================================================
# Verification functions — the client-side check
# =====================================================================

def verify_signed_admission(public_key_hex: str,
                             adm: SignedAdmission) -> bool:
    return verify_signature(public_key_hex, adm.canonical_payload(),
                            adm.signature)


def verify_signed_ack(public_key_hex: str, ack: SignedAck) -> bool:
    return verify_signature(public_key_hex, ack.canonical_payload(),
                            ack.signature)


# =====================================================================
# Signed manifest — the world publishes its public key
# =====================================================================

def signed_manifest_dict(manifest: Manifest,
                          keypair: KeyPair) -> Dict:
    """Return the manifest as a dict with `public_key` added and
    `protocol_version` bumped to 'WCP/0.2'. The Manifest type
    itself is unchanged — the extension lives at the wire level.
    """
    return {
        "entity_id": manifest.entity_id,
        "name": manifest.name,
        "protocol_version": "WCP/0.2",
        "law_url": manifest.law_url,
        "act_endpoint": manifest.act_endpoint,
        "log_endpoint": manifest.log_endpoint,
        "sub_registry_endpoint": manifest.sub_registry_endpoint,
        "public_key": keypair.public_key_hex(),
    }


# =====================================================================
# SignedWorld — wrapper that adds signatures to any WCP world
# =====================================================================

class SignedWorld:
    """Wraps any WCP/0.1 entity and produces WCP/0.2 signed responses.

    The base entity is unchanged. The wrapper handles only the
    signing. Any world — Poetry, Chemistry, Multiverse — can be
    signed by wrapping it.
    """
    def __init__(self, base: Any, keypair: Optional[KeyPair] = None):
        if keypair is None:
            keypair = KeyPair.generate()
        self.base = base
        self.keypair = keypair

    def manifest_dict(self) -> Dict:
        return signed_manifest_dict(self.base.manifest(), self.keypair)

    def petition(self, petition: Petition) -> Union[
            SignedAdmission, Refusal, Route]:
        response = self.base.petition(petition)
        if isinstance(response, WCPAdmission):
            return self._sign_admission(
                response, petition.petitioner_token)
        return response

    def act(self, act: Act) -> Union[SignedAck, Refusal]:
        response = self.base.act(act)
        if isinstance(response, Ack):
            return self._sign_ack(response, act.actor_token)
        return response

    def log_since(self, timestamp: Optional[str] = None
                  ) -> list:
        return self.base.log_since(timestamp)

    def _sign_admission(self, adm: WCPAdmission,
                        subject_token: str) -> SignedAdmission:
        payload = canonical_bytes({
            "kind": "admission",
            "entity_id": adm.entity_id,
            "timestamp": adm.timestamp,
            "subject_token": subject_token,
        })
        return SignedAdmission(
            entity_id=adm.entity_id,
            timestamp=adm.timestamp,
            subject_token=subject_token,
            signature=self.keypair.sign(payload).hex(),
        )

    def _sign_ack(self, ack: Ack, subject_token: str) -> SignedAck:
        payload = canonical_bytes({
            "kind": "ack",
            "entity_id": ack.entity_id,
            "timestamp": ack.timestamp,
            "subject_token": subject_token,
        })
        return SignedAck(
            entity_id=ack.entity_id,
            timestamp=ack.timestamp,
            subject_token=subject_token,
            signature=self.keypair.sign(payload).hex(),
        )


# =====================================================================
# SignedClient — petition/act with signature verification
# =====================================================================

@dataclass
class VerifiedResponse:
    """The base response, plus the verification outcome."""
    response: Any
    verified: Optional[bool]   # None if world is WCP/0.1 (unsigned)
    reason: str


class SignedClient:
    """A client that petitions and acts, verifying signed responses."""
    def __init__(self, world: SignedWorld):
        self.world = world
        self.public_key_hex = world.keypair.public_key_hex()

    def petition(self, petition: Petition) -> VerifiedResponse:
        response = self.world.petition(petition)
        if isinstance(response, SignedAdmission):
            ok = verify_signed_admission(
                self.public_key_hex, response)
            return VerifiedResponse(
                response=response, verified=ok,
                reason="signature valid" if ok
                        else "signature INVALID")
        return VerifiedResponse(response=response, verified=None,
                                 reason="unsigned refusal/route")

    def act(self, act: Act) -> VerifiedResponse:
        response = self.world.act(act)
        if isinstance(response, SignedAck):
            ok = verify_signed_ack(
                self.public_key_hex, response)
            return VerifiedResponse(
                response=response, verified=ok,
                reason="signature valid" if ok
                        else "signature INVALID")
        return VerifiedResponse(response=response, verified=None,
                                 reason="unsigned refusal")
