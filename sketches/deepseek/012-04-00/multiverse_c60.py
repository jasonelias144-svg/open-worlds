"""
multiverse_c60.py — Component 60: Revocation Propagation.

C59 announced contract establishment; C60 announces contract
revocation. Same pattern, symmetric claim, same infrastructure.

Design:
  - RevocationAnnouncement: (announcer, embedded revocation,
    revoked_at, timestamp, signature).
  - verify_revocation_announcement: signature + announcer is a
    party + embedded revocation verifies (C57).
  - revocation_announcement_to_registry: populates a C57
    registry with the revocation.
  - C60_VERIFIER_REGISTRY: extends the C48 kind registry with
    "contract_revocation".

Extends C48's WITNESSED_KINDS additively, same as C59.

What the announcement is NOT:
  - It does not carry the contract's terms or offer/acceptance.
    The establishment announcement (C59) carries those. A reader
    who wants the full history needs both.
  - It does not enforce order relative to establishment. A
    reader who sees revocation first will refuse citations of
    the contract, which is correct behavior: a revoked contract
    cannot be validly cited.

Composition:
  - C57 for the underlying BilateralRevocation.
  - C48 for the attestation wrapper.
  - C54 for the attested-rumor format.
  - C56 for signed relay transport.
  - C58 for enforcement after the revocation is learned.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: sign, verify, tampered, non-party,
    one-sided revocation, wrap, dispatch, registry population,
    C56 propagation, C58 refusal after revocation, never raises.
  - "A world never raises on what a visitor sends" — verifiers
    return verdicts.
  - "History, not rank" — announcements are historical records.

Honest limits (documented, tested):
  - Ordering not enforced. A revocation announcement may arrive
    before or after the establishment announcement. Both are
    past-tense facts; the timestamps in the artifacts tell the
    true order. C60 does not arbitrate.
  - Revocation is bilateral (C57's rule). A one-sided revocation
    (only one party's signature) does not verify, so it cannot
    be announced validly. A future "unilateral revocation" or
    "emergency revocation" mechanism would be a distinct
    component.
  - Announcements are self-signed by one party. Both-party
    announcements are a strictly stronger claim not in C60.
  - No announcement revocation. Once signed, an announcement
    is a historical fact.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import multiverse_c48 as c48

# Extend C48's witnessed kinds. Same pattern as C59, additive.
if "contract_revocation" not in c48.WITNESSED_KINDS:
    c48.WITNESSED_KINDS = (
        c48.WITNESSED_KINDS | {"contract_revocation"})
    c48.ALL_KINDS = c48.DIRECT_KINDS | c48.WITNESSED_KINDS

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c48 import (
    FederationAttestation, AttestationVerdict,
    DEFAULT_VERIFIER_REGISTRY,
    verify_federation_attestation,
)
from multiverse_c55 import WorldCurator
from multiverse_c57 import (
    BilateralRevocation,
    verify_bilateral_revocation,
    ContractRegistry,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# RevocationAnnouncement
# =====================================================================

@dataclass(frozen=True)
class RevocationAnnouncement:
    """A signed claim: "at time T, these two worlds revoked
    contract X." Signed by one of the two worlds. Carries the full
    revocation artifact so a reader can verify offline.

    Does NOT carry the underlying contract's terms. A reader who
    wants the full history pairs this with the corresponding
    establishment announcement (C59) using the shared contract_id.
    """
    announcer_world_id: str
    announcer_public_key: str
    contract_id: str
    world_a_id: str
    world_b_id: str
    revocation: Dict
    revoked_at: str
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("announcer_world_id", "world_a_id",
                  "world_b_id", "revoked_at", "timestamp",
                  "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        for f in ("announcer_public_key", "contract_id"):
            if len(getattr(self, f)) != 64:
                raise ValueError(
                    f"{f} must be 64 hex chars")
        if not isinstance(self.revocation, dict):
            raise ValueError("revocation must be a dict")
        if self.world_a_id == self.world_b_id:
            raise ValueError(
                "announcement requires two distinct worlds")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "contract_revocation",
            "announcer_world_id": self.announcer_world_id,
            "announcer_public_key": self.announcer_public_key,
            "contract_id": self.contract_id,
            "world_a_id": self.world_a_id,
            "world_b_id": self.world_b_id,
            "revocation": self.revocation,
            "revoked_at": self.revoked_at,
            "timestamp": self.timestamp,
        })

    def announcement_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "announcer_world_id": self.announcer_world_id,
            "announcer_public_key": self.announcer_public_key,
            "contract_id": self.contract_id,
            "world_a_id": self.world_a_id,
            "world_b_id": self.world_b_id,
            "revocation": self.revocation,
            "revoked_at": self.revoked_at,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RevocationAnnouncement":
        return cls(
            announcer_world_id=d["announcer_world_id"],
            announcer_public_key=d["announcer_public_key"],
            contract_id=d["contract_id"],
            world_a_id=d["world_a_id"],
            world_b_id=d["world_b_id"],
            revocation=d["revocation"],
            revoked_at=d["revoked_at"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# Signing
# =====================================================================

def sign_revocation_announcement(
    revocation: BilateralRevocation,
    announcer_kp: KeyPair,
    timestamp: Optional[str] = None,
) -> RevocationAnnouncement:
    """Sign an announcement of a bilateral revocation.

    The announcer's key MUST be one of the two parties' declared
    public keys. Otherwise, the announcement is nonsensical.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_revocation_announcement requires cryptography")
    if timestamp is None:
        timestamp = _now()
    pk = announcer_kp.public_key_hex()
    if pk == revocation.world_a_public_key:
        announcer_world_id = revocation.world_a_id
    elif pk == revocation.world_b_public_key:
        announcer_world_id = revocation.world_b_id
    else:
        raise ValueError(
            "announcer key is not one of the revocation's parties")
    payload = canonical_bytes({
        "kind": "contract_revocation",
        "announcer_world_id": announcer_world_id,
        "announcer_public_key": pk,
        "contract_id": revocation.contract_id,
        "world_a_id": revocation.world_a_id,
        "world_b_id": revocation.world_b_id,
        "revocation": revocation.to_dict(),
        "revoked_at": revocation.timestamp,
        "timestamp": timestamp,
    })
    return RevocationAnnouncement(
        announcer_world_id=announcer_world_id,
        announcer_public_key=pk,
        contract_id=revocation.contract_id,
        world_a_id=revocation.world_a_id,
        world_b_id=revocation.world_b_id,
        revocation=revocation.to_dict(),
        revoked_at=revocation.timestamp,
        timestamp=timestamp,
        signature=announcer_kp.sign(payload).hex(),
    )


# =====================================================================
# Verification
# =====================================================================

@dataclass
class RevocationAnnouncementVerdict:
    valid: bool
    reason: str
    signature_valid: bool
    announcer_is_party: bool
    revocation_valid: bool
    contract_id_matches: bool

    def format(self) -> str:
        return "\n".join([
            "Revocation Announcement Verification",
            "=" * 50,
            f"  valid:              {self.valid}",
            f"  signature_valid:    {self.signature_valid}",
            f"  announcer_is_party: {self.announcer_is_party}",
            f"  revocation_valid:   {self.revocation_valid}",
            f"  contract_id_matches: {self.contract_id_matches}",
            f"  reason:             {self.reason}",
        ])

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "signature_valid": self.signature_valid,
            "announcer_is_party": self.announcer_is_party,
            "revocation_valid": self.revocation_valid,
            "contract_id_matches": self.contract_id_matches,
        }


def verify_revocation_announcement(
    announcement: RevocationAnnouncement,
    expected_announcer_key: Optional[str] = None,
) -> RevocationAnnouncementVerdict:
    """Verify a revocation announcement. Never raises.

    Checks:
      1. Announcement signature verifies.
      2. Announcer is one of the two revocation parties.
      3. Embedded revocation verifies (both signatures, per C57).
      4. contract_id matches the embedded revocation's.

    Like C59, this verifies a HISTORICAL FACT ("at T, X was
    revoked"). It does not arbitrate ordering versus establishment.
    """
    if not HAS_CRYPTO:
        return RevocationAnnouncementVerdict(
            valid=False, reason="cryptography not installed",
            signature_valid=False, announcer_is_party=False,
            revocation_valid=False, contract_id_matches=False)
    if not isinstance(announcement, RevocationAnnouncement):
        return RevocationAnnouncementVerdict(
            valid=False, reason="not a RevocationAnnouncement",
            signature_valid=False, announcer_is_party=False,
            revocation_valid=False, contract_id_matches=False)

    # 1. Signature
    key = expected_announcer_key or \
        announcement.announcer_public_key
    try:
        sig_ok = verify_signature(
            key, announcement.canonical_payload(),
            announcement.signature)
    except Exception:
        sig_ok = False
    if not sig_ok:
        return RevocationAnnouncementVerdict(
            valid=False, reason="signature INVALID",
            signature_valid=False, announcer_is_party=False,
            revocation_valid=False, contract_id_matches=False)

    # 2. Announcer is a party
    try:
        rev = BilateralRevocation.from_dict(
            announcement.revocation)
    except (KeyError, ValueError, TypeError) as e:
        return RevocationAnnouncementVerdict(
            valid=False,
            reason=f"malformed embedded revocation: {e}",
            signature_valid=True, announcer_is_party=False,
            revocation_valid=False, contract_id_matches=False)
    party_keys = {rev.world_a_public_key,
                    rev.world_b_public_key}
    if announcement.announcer_public_key not in party_keys:
        return RevocationAnnouncementVerdict(
            valid=False,
            reason="announcer is not a party to the revocation",
            signature_valid=True, announcer_is_party=False,
            revocation_valid=False, contract_id_matches=False)

    # 3. Embedded revocation verifies
    ok_rev, reason_rev = verify_bilateral_revocation(
        rev,
        rev.world_a_public_key,
        rev.world_b_public_key)
    if not ok_rev:
        return RevocationAnnouncementVerdict(
            valid=False,
            reason=f"embedded revocation invalid: {reason_rev}",
            signature_valid=True, announcer_is_party=True,
            revocation_valid=False, contract_id_matches=False)

    # 4. contract_id matches
    if announcement.contract_id != rev.contract_id:
        return RevocationAnnouncementVerdict(
            valid=False,
            reason="contract_id does not match embedded revocation",
            signature_valid=True, announcer_is_party=True,
            revocation_valid=True, contract_id_matches=False)

    return RevocationAnnouncementVerdict(
        valid=True,
        reason=("signature valid; announcer is a party; "
                 "embedded revocation verifies"),
        signature_valid=True, announcer_is_party=True,
        revocation_valid=True, contract_id_matches=True)


# =====================================================================
# Wrap as FederationAttestation
# =====================================================================

def revocation_announcement_to_attestation_signed(
    announcement: RevocationAnnouncement,
    announcer_kp: KeyPair,
) -> FederationAttestation:
    """Sign a C48 FederationAttestation wrapping the revocation
    announcement. Same pattern as C59's announcement wrapper."""
    if not HAS_CRYPTO:
        raise RuntimeError(
            "revocation_announcement_to_attestation_signed "
            "requires cryptography")
    if announcer_kp.public_key_hex() != \
            announcement.announcer_public_key:
        raise ValueError(
            "announcer_kp does not match announcement's "
            "announcer_public_key")
    content = announcement.to_dict()
    content_hash = _hash_payload(canonical_bytes(content))
    source_id = f"revocation:{announcement.contract_id[:16]}"
    timestamp = _now()
    public_key = announcer_kp.public_key_hex()
    payload = canonical_bytes({
        "kind": "federation_witness",
        "source_id": source_id,
        "source_kind": "contract_revocation",
        "content_hash": content_hash,
        "witness_token": announcement.announcer_world_id,
        "witness_name": announcement.announcer_world_id,
        "witness_public_key": public_key,
        "witness_timestamp": timestamp,
    })
    return FederationAttestation(
        source_id=source_id,
        source_kind="contract_revocation",
        content=content,
        content_hash=content_hash,
        witness_token=announcement.announcer_world_id,
        witness_name=announcement.announcer_world_id,
        witness_public_key=public_key,
        witness_signature=announcer_kp.sign(payload).hex(),
        witness_timestamp=timestamp,
    )


# =====================================================================
# Verifier for the new kind
# =====================================================================

def _verify_revocation_announcement_attestation(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    recomputed = _hash_payload(canonical_bytes(att.content))
    if recomputed != att.content_hash:
        return (False, "content_hash does not match content")
    try:
        sig_ok = verify_signature(
            att.witness_public_key,
            att.witness_canonical_payload(),
            att.witness_signature)
    except Exception as e:
        return (False, f"witness signature check raised: {e}")
    if not sig_ok:
        return (False, "witness signature INVALID")
    try:
        announcement = RevocationAnnouncement.from_dict(att.content)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed announcement: {e}")
    v = verify_revocation_announcement(announcement)
    if not v.valid:
        return (False,
                 f"announcement invalid: {v.reason}")
    return (True,
             "witness signature and announcement valid")


C60_VERIFIER_REGISTRY: Dict[str, any] = dict(
    DEFAULT_VERIFIER_REGISTRY)
# Also carry C59's verifier if C59 was imported
try:
    from multiverse_c59 import _verify_announcement_attestation
    C60_VERIFIER_REGISTRY["contract_announcement"] = (
        _verify_announcement_attestation)
except ImportError:
    pass
C60_VERIFIER_REGISTRY["contract_revocation"] = (
    _verify_revocation_announcement_attestation)


def verify_revocation_announcement_attestation(
    att: FederationAttestation,
    context: Optional[Dict] = None,
) -> AttestationVerdict:
    """Verify a revocation-wrapped attestation. Never raises."""
    return verify_federation_attestation(
        att, context, registry=C60_VERIFIER_REGISTRY)


# =====================================================================
# Registry population
# =====================================================================

def revocation_announcement_to_registry(
    announcement: RevocationAnnouncement,
    registry: ContractRegistry,
) -> None:
    """Populate a C57 registry with the embedded revocation.

    Raises ValueError if the announcement doesn't verify.

    The registry is populated with the revocation. If the registry
    already has the contract's offer/acceptance (from a prior C59
    announcement or C57 negotiation), the record's state goes from
    established → revoked. If the registry has no record yet, a
    partial record is created (revocation only) — future
    establishment artifacts will fill in the rest.
    """
    v = verify_revocation_announcement(announcement)
    if not v.valid:
        raise ValueError(
            f"cannot populate registry from invalid "
            f"revocation announcement: {v.reason}")
    rev = BilateralRevocation.from_dict(announcement.revocation)
    registry.register_revocation(rev)


# =====================================================================
# Publisher
# =====================================================================

class RevocationPublisher:
    """Convenience wrapper around a WorldCurator for publishing
    revocation announcements."""

    def __init__(self, curator: WorldCurator):
        self._curator = curator

    @property
    def world_id(self) -> str:
        return self._curator.world_id

    @property
    def public_key(self) -> str:
        return self._curator.public_key

    def announce_revocation(
        self, revocation: BilateralRevocation,
    ) -> RevocationAnnouncement:
        return sign_revocation_announcement(
            revocation, self._curator._world_kp)

    def wrap_as_attestation(
        self, announcement: RevocationAnnouncement,
    ) -> FederationAttestation:
        return revocation_announcement_to_attestation_signed(
            announcement, self._curator._world_kp)
