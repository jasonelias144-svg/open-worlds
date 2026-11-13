"""
multiverse_c31.py — Component 31: The Signed Verdict.

C30 runs the federation and saves federation_verdict.json. That
file is unsigned — anyone with file access could modify it. C31
fixes this: the client that ran the verification signs the verdict.

The claim the signature makes:
    "<signer> verified the following at <timestamp>:
     registry R, world W, checks C, results V."

Not: "the federation is real." Not: "these are the true keys."
Only: "this client said this, at this time." Trusting the client
is external to the signature.

Composes with C24 (same signing primitive), C13 (same Ed25519),
and C30 (the runner).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — tamper on every field, wrong key, malformed input.
  - "A world never raises on what a visitor sends" — verifier
    returns False on any bad input. Never raises.
  - "History, not rank" — the verdict is a snapshot of checks,
    not a score. `all_pass` is AND, not sum.

Honest limits (documented, tested):
  - Authorship, not truth. A dishonest client can sign a
    fabricated verdict; signature valid, content false. Same
    trust model as C24.
  - Snapshot, not continuous. The verdict is about THIS run,
    at THIS timestamp, with THESE keys. Later runs are
    different verdicts.
  - Trust anchor external. The verifier's public key must come
    from somewhere other than the file that contains the
    signature (or the trust is "whoever controls this file").
    For the demo, the key is saved alongside; a real
    deployment publishes it via a registry or pins it.
  - No timestamp verification. A signer can backdate. Same as
    C24/C25/C26.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from multiverse_c1 import Identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)


# =====================================================================
# FederationVerdict — the abstract claim
# =====================================================================

@dataclass(frozen=True)
class FederationVerdict:
    """The result of a federation verification.

    Snapshot semantics: this is about ONE run, with THESE keys,
    at this timestamp. Later runs produce different verdicts.
    """
    conformance_passed: bool
    world_admitted: bool
    world_offline_at_verification: bool
    listing_count: int
    passport_verified_without_world: bool
    world_public_key: str
    registry_public_key: str

    def __post_init__(self):
        for f in ("conformance_passed", "world_admitted",
                  "world_offline_at_verification",
                  "passport_verified_without_world"):
            v = getattr(self, f)
            if not isinstance(v, bool):
                raise ValueError(f"{f} must be a bool")
        if not isinstance(self.listing_count, int) \
                or self.listing_count < 0:
            raise ValueError(
                "listing_count must be a non-negative int")
        for f in ("world_public_key", "registry_public_key"):
            v = getattr(self, f)
            if not isinstance(v, str) or len(v) != 64:
                raise ValueError(f"{f} must be 64 hex chars")

    @property
    def all_pass(self) -> bool:
        return (self.conformance_passed
                and self.world_admitted
                and self.world_offline_at_verification
                and self.passport_verified_without_world)

    def to_dict(self) -> Dict:
        return {
            "conformance_passed": self.conformance_passed,
            "world_admitted": self.world_admitted,
            "world_offline_at_verification":
                self.world_offline_at_verification,
            "listing_count": self.listing_count,
            "passport_verified_without_world":
                self.passport_verified_without_world,
            "world_public_key": self.world_public_key,
            "registry_public_key": self.registry_public_key,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "FederationVerdict":
        return cls(
            conformance_passed=d["conformance_passed"],
            world_admitted=d["world_admitted"],
            world_offline_at_verification=d[
                "world_offline_at_verification"],
            listing_count=d["listing_count"],
            passport_verified_without_world=d[
                "passport_verified_without_world"],
            world_public_key=d["world_public_key"],
            registry_public_key=d["registry_public_key"],
        )


# =====================================================================
# SignedFederationVerdict
# =====================================================================

@dataclass(frozen=True)
class SignedFederationVerdict:
    """A verdict, plus the signature of the client that produced it."""
    signer_id: str
    signer_name: str
    verdict: FederationVerdict
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("signer_id", "signer_name", "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if not isinstance(self.verdict, FederationVerdict):
            raise ValueError(
                "verdict must be a FederationVerdict")

    def canonical_payload(self) -> bytes:
        """The exact bytes the client signed.

        Includes the signer's token, name, the whole verdict, and
        the timestamp. Tampering with any of them breaks the
        signature.
        """
        return canonical_bytes({
            "kind": "signed_federation_verdict",
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "verdict": self.verdict.to_dict(),
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "kind": "signed_federation_verdict",
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "verdict": self.verdict.to_dict(),
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "SignedFederationVerdict":
        return cls(
            signer_id=d["signer_id"],
            signer_name=d["signer_name"],
            verdict=FederationVerdict.from_dict(d["verdict"]),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# Sign / verify
# =====================================================================

def sign_federation_verdict(
    verdict: FederationVerdict,
    keypair: KeyPair,
    signer: Identity,
    timestamp: Optional[str] = None,
) -> SignedFederationVerdict:
    """Sign a federation verdict.

    Raises RuntimeError on missing cryptography (a configuration
    error, not a visitor-input error). Raises TypeError on
    non-FederationVerdict input — that's a caller bug.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_federation_verdict requires `cryptography`. "
            "Install with: pip install cryptography")
    if not isinstance(verdict, FederationVerdict):
        raise TypeError(
            f"expected FederationVerdict, got "
            f"{type(verdict).__name__}")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    payload = canonical_bytes({
        "kind": "signed_federation_verdict",
        "signer_id": signer.token,
        "signer_name": signer.name,
        "verdict": verdict.to_dict(),
        "timestamp": timestamp,
    })
    return SignedFederationVerdict(
        signer_id=signer.token,
        signer_name=signer.name,
        verdict=verdict,
        timestamp=timestamp,
        signature=keypair.sign(payload).hex(),
    )


def verify_signed_federation_verdict(
    signed: SignedFederationVerdict,
    public_key_hex: str,
) -> bool:
    """True iff the signature verifies against public_key_hex.

    Never raises. Malformed input, missing cryptography, or invalid
    signature all return False.
    """
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(signed, SignedFederationVerdict):
            return False
        return verify_signature(
            public_key_hex,
            signed.canonical_payload(),
            signed.signature,
        )
    except Exception:
        return False
