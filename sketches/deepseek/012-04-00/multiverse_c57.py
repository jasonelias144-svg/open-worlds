"""
multiverse_c57.py — Component 57: The Curator-Mediated Contract.

Two worlds negotiate a signed contract that residents can cite.
The contract is a pattern of signed artifacts (offer + acceptance,
optionally a bilateral revocation), verified offline against world
public keys. No new primitive; everything composes from C1, C13, C55.

The lifecycle:
    propose   → ContractOffer        (proposer-signed)
    accept    → ContractAcceptance   (acceptor-signed)
    reject    → ContractRejection    (acceptor-signed, optional)
    establish → EstablishedContract  (offer + acceptance)
    revoke    → BilateralRevocation  (both-signed)

Contract ID is the terms hash: same terms = same contract. Two
offers with identical terms refer to the same contract artifact.

Design:
  - ContractTerms is content + hash. Free-form dict.
  - ContractOffer is a proposer's signed claim: "I propose these
    terms to this target at this time."
  - ContractAcceptance is an acceptor's signed claim: "I accept
    this offer, whose hash and terms hash are these, at this time."
  - ContractRejection is the honest refusal, also signed.
  - EstablishedContract is the (offer, acceptance) pair. Verifies
    both signatures, that offer_hash and terms_hash match, and
    that the two worlds differ.
  - BilateralRevocation is both parties signing the same payload.
  - ContractRegistry is LOCAL state on each negotiator's side.
    It is not a WCP world, not shared. Each party keeps its own.

Composition:
  - Contract signatures verify against the same public keys that
    verify CuratorMessages (C55). A world's key is its voice.
  - Residents (C1 identities) cite contract_id in acts. The world
    kernel does NOT check the citation. The contract is a social
    artifact: residents honor it or don't, by verifying against
    their curators' registries.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: offer signed, acceptance signed, rejection
    signed, mismatch rejected, established verified, revocation
    bilateral, one-sided revocation rejected, never raises.
  - "A world never raises on what a visitor sends" — receive
    methods return Ack/Refusal; verifiers return verdicts.
  - "History, not rank" — the registry is a record.

Honest limits (documented, tested):
  - No enforcement. The world kernel does not know about
    contracts. Residents cite; other residents check.
  - No timeout on offers. Offers persist until accepted,
    rejected, superseded by a newer offer from the same proposer
    to the same target, or revoked.
  - No arbitration. If two residents disagree about whether a
    citation is valid, there is no arbiter.
  - Contract ID = terms_hash means identical-terms offers from
    different proposers collide. Deliberate: same terms = same
    contract. A future component could add a nonce for uniqueness.
  - No sub-contracts (contracts referencing contracts).
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c55 import WorldCurator


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# ContractTerms
# =====================================================================

@dataclass(frozen=True)
class ContractTerms:
    """Free-form terms, hashable. Two offers with the same terms
    have the same terms_hash → the same contract ID."""
    content: Dict

    def __post_init__(self):
        if not isinstance(self.content, dict):
            raise ValueError("terms content must be a dict")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "contract_terms",
            "content": self.content,
        })

    def terms_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "terms_hash": self.terms_hash(),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ContractTerms":
        return cls(content=d["content"])


# =====================================================================
# ContractOffer
# =====================================================================

@dataclass(frozen=True)
class ContractOffer:
    proposer_world_id: str
    proposer_public_key: str
    target_world_id: str
    terms: ContractTerms
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("proposer_world_id", "target_world_id",
                  "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.proposer_public_key) != 64:
            raise ValueError(
                "proposer_public_key must be 64 hex chars")
        if self.proposer_world_id == self.target_world_id:
            raise ValueError(
                "cannot propose a contract to oneself")
        if not isinstance(self.terms, ContractTerms):
            raise ValueError("terms must be ContractTerms")

    @property
    def terms_hash(self) -> str:
        return self.terms.terms_hash()

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "contract_offer",
            "proposer_world_id": self.proposer_world_id,
            "proposer_public_key": self.proposer_public_key,
            "target_world_id": self.target_world_id,
            "terms": self.terms.content,
            "timestamp": self.timestamp,
        })

    def offer_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "proposer_world_id": self.proposer_world_id,
            "proposer_public_key": self.proposer_public_key,
            "target_world_id": self.target_world_id,
            "terms": self.terms.content,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ContractOffer":
        return cls(
            proposer_world_id=d["proposer_world_id"],
            proposer_public_key=d["proposer_public_key"],
            target_world_id=d["target_world_id"],
            terms=ContractTerms(content=d["terms"]),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_contract_offer(
    offer: ContractOffer,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = expected_public_key or offer.proposer_public_key
        return verify_signature(
            key, offer.canonical_payload(), offer.signature)
    except Exception:
        return False


# =====================================================================
# ContractAcceptance
# =====================================================================

@dataclass(frozen=True)
class ContractAcceptance:
    acceptor_world_id: str
    acceptor_public_key: str
    offer_hash: str
    terms_hash: str
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("acceptor_world_id", "offer_hash",
                  "terms_hash", "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.acceptor_public_key) != 64:
            raise ValueError(
                "acceptor_public_key must be 64 hex chars")
        if len(self.offer_hash) != 64:
            raise ValueError("offer_hash must be 64 hex chars")
        if len(self.terms_hash) != 64:
            raise ValueError("terms_hash must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "contract_acceptance",
            "acceptor_world_id": self.acceptor_world_id,
            "acceptor_public_key": self.acceptor_public_key,
            "offer_hash": self.offer_hash,
            "terms_hash": self.terms_hash,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "acceptor_world_id": self.acceptor_world_id,
            "acceptor_public_key": self.acceptor_public_key,
            "offer_hash": self.offer_hash,
            "terms_hash": self.terms_hash,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ContractAcceptance":
        return cls(
            acceptor_world_id=d["acceptor_world_id"],
            acceptor_public_key=d["acceptor_public_key"],
            offer_hash=d["offer_hash"],
            terms_hash=d["terms_hash"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_contract_acceptance(
    acceptance: ContractAcceptance,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = (expected_public_key
                or acceptance.acceptor_public_key)
        return verify_signature(
            key, acceptance.canonical_payload(),
            acceptance.signature)
    except Exception:
        return False


# =====================================================================
# ContractRejection
# =====================================================================

@dataclass(frozen=True)
class ContractRejection:
    rejector_world_id: str
    rejector_public_key: str
    offer_hash: str
    reason: str
    timestamp: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "contract_rejection",
            "rejector_world_id": self.rejector_world_id,
            "rejector_public_key": self.rejector_public_key,
            "offer_hash": self.offer_hash,
            "reason": self.reason,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "rejector_world_id": self.rejector_world_id,
            "rejector_public_key": self.rejector_public_key,
            "offer_hash": self.offer_hash,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ContractRejection":
        return cls(
            rejector_world_id=d["rejector_world_id"],
            rejector_public_key=d["rejector_public_key"],
            offer_hash=d["offer_hash"],
            reason=d.get("reason", ""),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_contract_rejection(
    rejection: ContractRejection,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = (expected_public_key
                or rejection.rejector_public_key)
        return verify_signature(
            key, rejection.canonical_payload(),
            rejection.signature)
    except Exception:
        return False


# =====================================================================
# EstablishedContract
# =====================================================================

@dataclass(frozen=True)
class EstablishedContract:
    offer: ContractOffer
    acceptance: ContractAcceptance
    established_at: str

    def __post_init__(self):
        if not isinstance(self.offer, ContractOffer):
            raise ValueError("offer must be ContractOffer")
        if not isinstance(self.acceptance, ContractAcceptance):
            raise ValueError(
                "acceptance must be ContractAcceptance")

    @property
    def terms_hash(self) -> str:
        return self.offer.terms_hash

    @property
    def world_a_id(self) -> str:
        return self.offer.proposer_world_id

    @property
    def world_b_id(self) -> str:
        return self.offer.target_world_id

    def to_dict(self) -> Dict:
        return {
            "offer": self.offer.to_dict(),
            "acceptance": self.acceptance.to_dict(),
            "established_at": self.established_at,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "EstablishedContract":
        return cls(
            offer=ContractOffer.from_dict(d["offer"]),
            acceptance=ContractAcceptance.from_dict(
                d["acceptance"]),
            established_at=d["established_at"],
        )


def verify_established_contract(
    contract: EstablishedContract,
    proposer_public_key: Optional[str] = None,
    acceptor_public_key: Optional[str] = None,
) -> Tuple[bool, str]:
    """Verify an EstablishedContract. Never raises.

    Checks:
      1. Offer signature verifies.
      2. Acceptance signature verifies.
      3. Acceptance references this offer's hash.
      4. Acceptance references this offer's terms hash.
      5. Proposer world != acceptor world.
      6. Acceptance's acceptor world matches the offer's target.
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(contract, EstablishedContract):
        return (False, "not an EstablishedContract")

    # 1. Offer
    if not verify_contract_offer(
            contract.offer, proposer_public_key):
        return (False, "offer signature INVALID")

    # 2. Acceptance
    if not verify_contract_acceptance(
            contract.acceptance, acceptor_public_key):
        return (False, "acceptance signature INVALID")

    # 3. Offer hash match
    if contract.acceptance.offer_hash != \
            contract.offer.offer_hash():
        return (False, "acceptance references a different offer")

    # 4. Terms hash match
    if contract.acceptance.terms_hash != \
            contract.offer.terms_hash:
        return (False, "acceptance references different terms")

    # 5. Distinct worlds
    if contract.world_a_id == contract.world_b_id:
        return (False, "proposer and acceptor are the same world")

    # 6. Acceptor matches target
    if contract.acceptance.acceptor_world_id != \
            contract.offer.target_world_id:
        return (False,
                "acceptor is not the offer's target")

    return (True, "offer and acceptance verify; "
                   "hashes and worlds match")


# =====================================================================
# BilateralRevocation
# =====================================================================

@dataclass(frozen=True)
class BilateralRevocation:
    contract_id: str
    world_a_id: str
    world_a_public_key: str
    world_b_id: str
    world_b_public_key: str
    reason: str
    timestamp: str
    signature_a: str
    signature_b: str

    def __post_init__(self):
        for f in ("contract_id", "world_a_id", "world_b_id",
                  "timestamp", "signature_a", "signature_b"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        for f in ("world_a_public_key", "world_b_public_key",
                  "contract_id"):
            if len(getattr(self, f)) != 64:
                raise ValueError(
                    f"{f} must be 64 hex chars")
        if self.world_a_id == self.world_b_id:
            raise ValueError(
                "revocation requires two distinct worlds")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "bilateral_revocation",
            "contract_id": self.contract_id,
            "world_a_id": self.world_a_id,
            "world_a_public_key": self.world_a_public_key,
            "world_b_id": self.world_b_id,
            "world_b_public_key": self.world_b_public_key,
            "reason": self.reason,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "contract_id": self.contract_id,
            "world_a_id": self.world_a_id,
            "world_a_public_key": self.world_a_public_key,
            "world_b_id": self.world_b_id,
            "world_b_public_key": self.world_b_public_key,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "signature_a": self.signature_a,
            "signature_b": self.signature_b,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "BilateralRevocation":
        return cls(
            contract_id=d["contract_id"],
            world_a_id=d["world_a_id"],
            world_a_public_key=d["world_a_public_key"],
            world_b_id=d["world_b_id"],
            world_b_public_key=d["world_b_public_key"],
            reason=d.get("reason", ""),
            timestamp=d["timestamp"],
            signature_a=d["signature_a"],
            signature_b=d["signature_b"],
        )


def verify_bilateral_revocation(
    revocation: BilateralRevocation,
    world_a_public_key: Optional[str] = None,
    world_b_public_key: Optional[str] = None,
) -> Tuple[bool, str]:
    """Verify a BilateralRevocation. Never raises.

    Both signatures must be present and valid.
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(revocation, BilateralRevocation):
        return (False, "not a BilateralRevocation")
    key_a = world_a_public_key or revocation.world_a_public_key
    key_b = world_b_public_key or revocation.world_b_public_key
    payload = revocation.canonical_payload()
    try:
        sig_a_ok = verify_signature(
            key_a, payload, revocation.signature_a)
    except Exception:
        sig_a_ok = False
    try:
        sig_b_ok = verify_signature(
            key_b, payload, revocation.signature_b)
    except Exception:
        sig_b_ok = False
    if not sig_a_ok and not sig_b_ok:
        return (False, "both signatures INVALID")
    if not sig_a_ok:
        return (False, "world_a signature INVALID")
    if not sig_b_ok:
        return (False, "world_b signature INVALID")
    return (True, "both signatures valid")


# =====================================================================
# Signers
# =====================================================================

def sign_offer(
    proposer_world_id: str,
    proposer_kp: KeyPair,
    target_world_id: str,
    terms: ContractTerms,
    timestamp: Optional[str] = None,
) -> ContractOffer:
    if not HAS_CRYPTO:
        raise RuntimeError("sign_offer requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "contract_offer",
        "proposer_world_id": proposer_world_id,
        "proposer_public_key": proposer_kp.public_key_hex(),
        "target_world_id": target_world_id,
        "terms": terms.content,
        "timestamp": timestamp,
    })
    return ContractOffer(
        proposer_world_id=proposer_world_id,
        proposer_public_key=proposer_kp.public_key_hex(),
        target_world_id=target_world_id,
        terms=terms,
        timestamp=timestamp,
        signature=proposer_kp.sign(payload).hex(),
    )


def sign_acceptance(
    acceptor_world_id: str,
    acceptor_kp: KeyPair,
    offer: ContractOffer,
    timestamp: Optional[str] = None,
) -> ContractAcceptance:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_acceptance requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "contract_acceptance",
        "acceptor_world_id": acceptor_world_id,
        "acceptor_public_key": acceptor_kp.public_key_hex(),
        "offer_hash": offer.offer_hash(),
        "terms_hash": offer.terms_hash,
        "timestamp": timestamp,
    })
    return ContractAcceptance(
        acceptor_world_id=acceptor_world_id,
        acceptor_public_key=acceptor_kp.public_key_hex(),
        offer_hash=offer.offer_hash(),
        terms_hash=offer.terms_hash,
        timestamp=timestamp,
        signature=acceptor_kp.sign(payload).hex(),
    )


def sign_rejection(
    rejector_world_id: str,
    rejector_kp: KeyPair,
    offer: ContractOffer,
    reason: str = "",
    timestamp: Optional[str] = None,
) -> ContractRejection:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_rejection requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "contract_rejection",
        "rejector_world_id": rejector_world_id,
        "rejector_public_key": rejector_kp.public_key_hex(),
        "offer_hash": offer.offer_hash(),
        "reason": reason,
        "timestamp": timestamp,
    })
    return ContractRejection(
        rejector_world_id=rejector_world_id,
        rejector_public_key=rejector_kp.public_key_hex(),
        offer_hash=offer.offer_hash(),
        reason=reason,
        timestamp=timestamp,
        signature=rejector_kp.sign(payload).hex(),
    )


def sign_bilateral_revocation(
    contract_id: str,
    world_a_id: str,
    world_a_kp: KeyPair,
    world_b_id: str,
    world_b_kp: KeyPair,
    reason: str = "",
    timestamp: Optional[str] = None,
) -> BilateralRevocation:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_bilateral_revocation requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "bilateral_revocation",
        "contract_id": contract_id,
        "world_a_id": world_a_id,
        "world_a_public_key": world_a_kp.public_key_hex(),
        "world_b_id": world_b_id,
        "world_b_public_key": world_b_kp.public_key_hex(),
        "reason": reason,
        "timestamp": timestamp,
    })
    return BilateralRevocation(
        contract_id=contract_id,
        world_a_id=world_a_id,
        world_a_public_key=world_a_kp.public_key_hex(),
        world_b_id=world_b_id,
        world_b_public_key=world_b_kp.public_key_hex(),
        reason=reason,
        timestamp=timestamp,
        signature_a=world_a_kp.sign(payload).hex(),
        signature_b=world_b_kp.sign(payload).hex(),
    )


# =====================================================================
# ContractRegistry
# =====================================================================

@dataclass
class ContractRecord:
    terms_hash: str
    world_a_id: str
    world_b_id: str
    offer: Optional[ContractOffer] = None
    acceptance: Optional[ContractAcceptance] = None
    rejection: Optional[ContractRejection] = None
    revocation: Optional[BilateralRevocation] = None
    established_at: Optional[str] = None
    revoked_at: Optional[str] = None

    def is_established(self) -> bool:
        return (self.offer is not None
                and self.acceptance is not None
                and self.revocation is None)

    def is_rejected(self) -> bool:
        return (self.rejection is not None
                and self.acceptance is None)

    def is_revoked(self) -> bool:
        return self.revocation is not None

    def is_pending(self) -> bool:
        return (self.offer is not None
                and self.acceptance is None
                and self.rejection is None)

    def to_dict(self) -> Dict:
        return {
            "terms_hash": self.terms_hash,
            "world_a_id": self.world_a_id,
            "world_b_id": self.world_b_id,
            "offer": self.offer.to_dict() if self.offer else None,
            "acceptance":
                self.acceptance.to_dict()
                if self.acceptance else None,
            "rejection":
                self.rejection.to_dict()
                if self.rejection else None,
            "revocation":
                self.revocation.to_dict()
                if self.revocation else None,
            "established_at": self.established_at,
            "revoked_at": self.revoked_at,
        }


class ContractRegistry:
    """Local, per-world registry of contract artifacts.

    Each curator/negotiator has its own. There is no shared state.
    A contract is "established" from this registry's perspective
    when both offer and acceptance have been seen.
    """

    def __init__(self):
        self._records: Dict[str, ContractRecord] = {}

    def _get_or_create(
        self, terms_hash: str,
        world_a_id: str, world_b_id: str,
    ) -> ContractRecord:
        if terms_hash not in self._records:
            self._records[terms_hash] = ContractRecord(
                terms_hash=terms_hash,
                world_a_id=world_a_id,
                world_b_id=world_b_id,
            )
        return self._records[terms_hash]

    def register_offer(self, offer: ContractOffer) -> None:
        rec = self._get_or_create(
            offer.terms_hash,
            offer.proposer_world_id,
            offer.target_world_id)
        rec.offer = offer

    def register_acceptance(
        self, acceptance: ContractAcceptance,
    ) -> None:
        # Acceptance doesn't carry world_a_id / world_b_id; the
        # offer must already be present (or the terms_hash won't
        # match anything in the registry — the caller should have
        # registered the offer first).
        for rec in self._records.values():
            if rec.terms_hash == acceptance.terms_hash:
                rec.acceptance = acceptance
                rec.established_at = _now()
                return
        # Acceptance without matching offer — record under a
        # partially-known record
        rec = self._get_or_create(
            acceptance.terms_hash,
            world_a_id="?",
            world_b_id=acceptance.acceptor_world_id)
        rec.acceptance = acceptance
        rec.established_at = _now()

    def register_rejection(
        self, rejection: ContractRejection,
    ) -> None:
        # Find by offer hash
        for rec in self._records.values():
            if rec.offer is not None and \
                    rec.offer.offer_hash() == rejection.offer_hash:
                rec.rejection = rejection
                return
        # No matching record; ignore (rejection of unknown offer)

    def register_revocation(
        self, revocation: BilateralRevocation,
    ) -> None:
        rec = self._records.get(revocation.contract_id)
        if rec is None:
            rec = self._get_or_create(
                revocation.contract_id,
                revocation.world_a_id,
                revocation.world_b_id)
        rec.revocation = revocation
        rec.revoked_at = _now()

    def get(self, terms_hash: str) -> Optional[ContractRecord]:
        return self._records.get(terms_hash)

    def list_all(self) -> List[ContractRecord]:
        return list(self._records.values())

    def established(self) -> List[ContractRecord]:
        return [r for r in self._records.values()
                if r.is_established()]

    def pending(self) -> List[ContractRecord]:
        return [r for r in self._records.values()
                if r.is_pending()]

    def revoked(self) -> List[ContractRecord]:
        return [r for r in self._records.values()
                if r.is_revoked()]

    def is_active(self, terms_hash: str) -> bool:
        rec = self._records.get(terms_hash)
        if rec is None:
            return False
        return rec.is_established()


# =====================================================================
# ContractNegotiator — the integration with C55's curator
# =====================================================================

class ContractNegotiator:
    """A negotiator wrapping a WorldCurator. Provides the contract
    negotiation API on top of C55's curator. C55 is untouched.
    """

    def __init__(
        self,
        curator: WorldCurator,
        registry: Optional[ContractRegistry] = None,
    ):
        self._curator = curator
        self._registry = registry or ContractRegistry()

    @property
    def world_id(self) -> str:
        return self._curator.world_id

    @property
    def public_key(self) -> str:
        return self._curator.public_key

    @property
    def curator(self) -> WorldCurator:
        return self._curator

    @property
    def registry(self) -> ContractRegistry:
        return self._registry

    def propose(
        self, target_world_id: str, terms: ContractTerms,
    ) -> ContractOffer:
        """Propose a contract. Registers the offer locally."""
        offer = sign_offer(
            self.world_id, self._curator._world_kp,
            target_world_id, terms)
        self._registry.register_offer(offer)
        return offer

    def receive_offer(self, offer: ContractOffer):
        """Receive a contract offer addressed to us. Verifies the
        signature and target; registers if valid."""
        if not isinstance(offer, ContractOffer):
            return Refusal(reason="not a ContractOffer")
        if not verify_contract_offer(offer):
            return Refusal(reason="offer signature INVALID")
        if offer.target_world_id != self.world_id:
            return Refusal(
                reason="offer not addressed to this world")
        self._registry.register_offer(offer)
        return Ack(
            entity_id=self.world_id, timestamp=_now())

    def accept(
        self, offer: ContractOffer,
    ) -> ContractAcceptance:
        """Accept an offer. Registers the acceptance locally."""
        acceptance = sign_acceptance(
            self.world_id, self._curator._world_kp, offer)
        self._registry.register_offer(offer)
        self._registry.register_acceptance(acceptance)
        return acceptance

    def reject(
        self, offer: ContractOffer, reason: str = "",
    ) -> ContractRejection:
        rejection = sign_rejection(
            self.world_id, self._curator._world_kp,
            offer, reason)
        self._registry.register_offer(offer)
        self._registry.register_rejection(rejection)
        return rejection

    def receive_acceptance(
        self, acceptance: ContractAcceptance,
    ):
        """Receive an acceptance for one of our offers. Verifies
        the signature; registers if valid."""
        if not isinstance(acceptance, ContractAcceptance):
            return Refusal(reason="not a ContractAcceptance")
        if not verify_contract_acceptance(acceptance):
            return Refusal(reason="acceptance signature INVALID")
        self._registry.register_acceptance(acceptance)
        return Ack(
            entity_id=self.world_id, timestamp=_now())

    def receive_rejection(
        self, rejection: ContractRejection,
    ):
        if not isinstance(rejection, ContractRejection):
            return Refusal(reason="not a ContractRejection")
        if not verify_contract_rejection(rejection):
            return Refusal(reason="rejection signature INVALID")
        self._registry.register_rejection(rejection)
        return Ack(
            entity_id=self.world_id, timestamp=_now())

    def is_active(self, terms_hash: str) -> bool:
        """True iff this world has an established, non-revoked
        contract with the given terms hash."""
        return self._registry.is_active(terms_hash)

    def get_contract(
        self, terms_hash: str,
    ) -> Optional[ContractRecord]:
        return self._registry.get(terms_hash)
