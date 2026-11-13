"""
multiverse_c59.py — Component 59: Contract Propagation.

C57 made contracts verifiable. C58 made them enforceable. C59
makes them discoverable.

A world that is party to an established contract can publish a
signed announcement. The announcement carries the full contract
artifacts (offer + acceptance), so a reader can verify offline.
The announcement flows through C56's signed relay, letting
third-party worlds learn of the contract without contacting the
establishing parties.

Design:
  - ContractAnnouncement: (announcer, contract artifacts,
    established_at, timestamp, signature). Signed by one of the
    two parties.
  - verify_announcement: signature + announcer is a party +
    embedded contract verifies (C57).
  - announcement_to_attestation: wraps an announcement as a
    C48 FederationAttestation with source_kind="contract_announcement".
  - announcement_to_registry: populates a C57 ContractRegistry
    with the offer and acceptance from a verified announcement.
  - C59_VERIFIER_REGISTRY: extends C48's default registry to
    verify contract_announcement attestations.

The C48 extension:
  C48's WITNESSED_KINDS is extended (additively) to include
  "contract_announcement". Existing C48 mechanisms — dispatch,
  verification, relay through C54/C56 — all work unchanged
  once the extension is done. This is the "witnessed kinds are
  extensible" claim from C48's docstring, made concrete.

Composition:
  - C57 for the underlying contract.
  - C48 for the attestation wrapper.
  - C54 for the attested-rumor format.
  - C56 for signed relay transport.
  - C58 for enforcement in the receiving world.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: sign, verify, tampered, non-party,
    revoked underlying, wrap-as-attestation, dispatch, registry
    population, C56 propagation, never raises.
  - "A world never raises on what a visitor sends" — verifiers
    return verdicts.
  - "History, not rank" — announcements are historical records.

Honest limits (documented, tested):
  - No revocation status in the announcement. A reader learns
    "a contract was established"; whether it's currently active
    requires the revocation record. Announcements are about
    events, not current state.
  - No announcement of revocation. A separate component could
    add signed revocation announcements; C59 only announces
    establishment.
  - Announcement carries full contract artifacts. Heavier than
    a hash + fetch. Self-contained is the right tradeoff for
    a prototype.
  - No announcement revocation. Once signed, an announcement
    is a historical fact.
  - Announcements are self-signed by one party. Both parties
    signing would be a "stronger" claim; not in C59.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import multiverse_c48 as c48

# Extend C48's witnessed kinds with our new kind.
# This is a documented, additive, backward-compatible extension.
if "contract_announcement" not in c48.WITNESSED_KINDS:
    c48.WITNESSED_KINDS = (
        c48.WITNESSED_KINDS | {"contract_announcement"})
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
    ContractOffer, ContractAcceptance, EstablishedContract,
    verify_established_contract, ContractRegistry,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# ContractAnnouncement
# =====================================================================

@dataclass(frozen=True)
class ContractAnnouncement:
    """A signed claim: "at time T, these two worlds established
    this contract." Signed by one of the two worlds. Carries the
    full offer and acceptance so a reader can verify offline.
    """
    announcer_world_id: str
    announcer_public_key: str
    world_a_id: str
    world_b_id: str
    terms_hash: str
    offer: Dict
    acceptance: Dict
    established_at: str
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("announcer_world_id", "world_a_id", "world_b_id",
                  "established_at", "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        for f in ("announcer_public_key", "terms_hash"):
            if len(getattr(self, f)) != 64:
                raise ValueError(
                    f"{f} must be 64 hex chars")
        if not isinstance(self.offer, dict):
            raise ValueError("offer must be dict")
        if not isinstance(self.acceptance, dict):
            raise ValueError("acceptance must be dict")
        if self.world_a_id == self.world_b_id:
            raise ValueError(
                "announcement requires two distinct worlds")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "contract_announcement",
            "announcer_world_id": self.announcer_world_id,
            "announcer_public_key": self.announcer_public_key,
            "world_a_id": self.world_a_id,
            "world_b_id": self.world_b_id,
            "terms_hash": self.terms_hash,
            "offer": self.offer,
            "acceptance": self.acceptance,
            "established_at": self.established_at,
            "timestamp": self.timestamp,
        })

    def announcement_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "announcer_world_id": self.announcer_world_id,
            "announcer_public_key": self.announcer_public_key,
            "world_a_id": self.world_a_id,
            "world_b_id": self.world_b_id,
            "terms_hash": self.terms_hash,
            "offer": self.offer,
            "acceptance": self.acceptance,
            "established_at": self.established_at,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ContractAnnouncement":
        return cls(
            announcer_world_id=d["announcer_world_id"],
            announcer_public_key=d["announcer_public_key"],
            world_a_id=d["world_a_id"],
            world_b_id=d["world_b_id"],
            terms_hash=d["terms_hash"],
            offer=d["offer"],
            acceptance=d["acceptance"],
            established_at=d["established_at"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# Signing and verification
# =====================================================================

def sign_announcement(
    contract: EstablishedContract,
    announcer_kp: KeyPair,
    timestamp: Optional[str] = None,
) -> ContractAnnouncement:
    """Sign an announcement of an established contract.

    The announcer's public key MUST be one of the two parties'
    declared public keys. Otherwise, the announcement is
    nonsensical (a stranger announcing someone else's contract).
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_announcement requires `cryptography`")
    if timestamp is None:
        timestamp = _now()
    pk = announcer_kp.public_key_hex()
    if pk not in (contract.offer.proposer_public_key,
                    contract.acceptance.acceptor_public_key):
        raise ValueError(
            "announcer key is not one of the contract's parties")
    payload = canonical_bytes({
        "kind": "contract_announcement",
        "announcer_world_id": (
            contract.offer.proposer_world_id
            if pk == contract.offer.proposer_public_key
            else contract.acceptance.acceptor_world_id),
        "announcer_public_key": pk,
        "world_a_id": contract.world_a_id,
        "world_b_id": contract.world_b_id,
        "terms_hash": contract.terms_hash,
        "offer": contract.offer.to_dict(),
        "acceptance": contract.acceptance.to_dict(),
        "established_at": contract.established_at,
        "timestamp": timestamp,
    })
    announcer_world_id = (
        contract.offer.proposer_world_id
        if pk == contract.offer.proposer_public_key
        else contract.acceptance.acceptor_world_id)
    return ContractAnnouncement(
        announcer_world_id=announcer_world_id,
        announcer_public_key=pk,
        world_a_id=contract.world_a_id,
        world_b_id=contract.world_b_id,
        terms_hash=contract.terms_hash,
        offer=contract.offer.to_dict(),
        acceptance=contract.acceptance.to_dict(),
        established_at=contract.established_at,
        timestamp=timestamp,
        signature=announcer_kp.sign(payload).hex(),
    )


@dataclass
class AnnouncementVerdict:
    valid: bool
    reason: str
    signature_valid: bool
    announcer_is_party: bool
    contract_valid: bool
    terms_hash_matches: bool

    def format(self) -> str:
        return "\n".join([
            "Contract Announcement Verification",
            "=" * 50,
            f"  valid:              {self.valid}",
            f"  signature_valid:    {self.signature_valid}",
            f"  announcer_is_party: {self.announcer_is_party}",
            f"  contract_valid:     {self.contract_valid}",
            f"  terms_hash_matches: {self.terms_hash_matches}",
            f"  reason:             {self.reason}",
        ])

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "signature_valid": self.signature_valid,
            "announcer_is_party": self.announcer_is_party,
            "contract_valid": self.contract_valid,
            "terms_hash_matches": self.terms_hash_matches,
        }


def verify_announcement(
    announcement: ContractAnnouncement,
    expected_announcer_key: Optional[str] = None,
) -> AnnouncementVerdict:
    """Verify an announcement. Never raises.

    Checks:
      1. Announcement signature verifies.
      2. Announcer is one of the two parties (by public key).
      3. Embedded contract verifies (via C57's
         verify_established_contract).
      4. terms_hash matches the embedded contract's terms.

    A NOTE on current status: this function verifies the
    announcement as a HISTORICAL FACT. It does NOT check whether
    the contract is currently active (not revoked). A reader who
    cares about current status must check the revocation layer
    independently.
    """
    if not HAS_CRYPTO:
        return AnnouncementVerdict(
            valid=False, reason="cryptography not installed",
            signature_valid=False, announcer_is_party=False,
            contract_valid=False, terms_hash_matches=False)
    if not isinstance(announcement, ContractAnnouncement):
        return AnnouncementVerdict(
            valid=False, reason="not a ContractAnnouncement",
            signature_valid=False, announcer_is_party=False,
            contract_valid=False, terms_hash_matches=False)

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
        return AnnouncementVerdict(
            valid=False, reason="signature INVALID",
            signature_valid=False, announcer_is_party=False,
            contract_valid=False, terms_hash_matches=False)

    # 2. Announcer is a party
    party_keys = set()
    try:
        offer = ContractOffer.from_dict(announcement.offer)
        acceptance = ContractAcceptance.from_dict(
            announcement.acceptance)
        party_keys.add(offer.proposer_public_key)
        party_keys.add(acceptance.acceptor_public_key)
    except (KeyError, ValueError, TypeError) as e:
        return AnnouncementVerdict(
            valid=False,
            reason=f"malformed embedded contract: {e}",
            signature_valid=True, announcer_is_party=False,
            contract_valid=False, terms_hash_matches=False)
    if announcement.announcer_public_key not in party_keys:
        return AnnouncementVerdict(
            valid=False,
            reason="announcer is not a party to the contract",
            signature_valid=True, announcer_is_party=False,
            contract_valid=False, terms_hash_matches=False)

    # 3. Embedded contract verifies
    contract = EstablishedContract(
        offer=offer, acceptance=acceptance,
        established_at=announcement.established_at)
    ok_contract, reason_contract = verify_established_contract(
        contract,
        offer.proposer_public_key,
        acceptance.acceptor_public_key)
    if not ok_contract:
        return AnnouncementVerdict(
            valid=False,
            reason=f"embedded contract invalid: {reason_contract}",
            signature_valid=True, announcer_is_party=True,
            contract_valid=False, terms_hash_matches=False)

    # 4. terms_hash matches
    if announcement.terms_hash != contract.terms_hash:
        return AnnouncementVerdict(
            valid=False,
            reason="terms_hash does not match embedded contract",
            signature_valid=True, announcer_is_party=True,
            contract_valid=True, terms_hash_matches=False)

    return AnnouncementVerdict(
        valid=True,
        reason=("signature valid; announcer is a party; "
                 "embedded contract verifies"),
        signature_valid=True, announcer_is_party=True,
        contract_valid=True, terms_hash_matches=True)


# =====================================================================
# Wrap as C48 FederationAttestation
# =====================================================================

def announcement_to_attestation(
    announcement: ContractAnnouncement,
) -> FederationAttestation:
    """Wrap an announcement as a C48 FederationAttestation.

    The announcement is a WITNESSED kind: the announcer is the
    witness. The content is the announcement dict; the content
    hash is the announcement's own hash. This lets C54/C56 carry
    announcements through signed relay, exactly like any other
    witnessed artifact.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "announcement_to_attestation requires cryptography")
    content = announcement.to_dict()
    content_hash = _hash_payload(canonical_bytes(content))
    # Sign a witness payload over (source_id, source_kind,
    # content_hash). Since we don't have the announcer's private
    # key here, we re-use the announcement's signature — but the
    # witness signature must be over the witness payload, not the
    # announcement payload. So the caller needs to provide a
    # KeyPair if they want a proper witness signature.
    # For the prototype, we produce a "self-witness" where the
    # announced signature IS the witness signature — but we sign
    # the witness payload with the same key. To do that, we need
    # the key. Callers who have the key should use
    # announcement_to_attestation_signed; this function produces
    # a "hash-only" attestation (content + content_hash, no
    # witness signature) that C48 won't fully verify.
    raise RuntimeError(
        "use announcement_to_attestation_signed(...) with the "
        "announcer's keypair")


def announcement_to_attestation_signed(
    announcement: ContractAnnouncement,
    announcer_kp: KeyPair,
) -> FederationAttestation:
    """Sign a C48 FederationAttestation wrapping the announcement.

    The witness payload is (source_id, source_kind,
    content_hash, witness_token, witness_name, witness_public_key,
    witness_timestamp). The announcer's key signs it.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "announcement_to_attestation_signed requires "
            "cryptography")
    if announcer_kp.public_key_hex() != \
            announcement.announcer_public_key:
        raise ValueError(
            "announcer_kp does not match announcement's "
            "announcer_public_key")
    content = announcement.to_dict()
    content_hash = _hash_payload(canonical_bytes(content))
    source_id = f"announce:{announcement.terms_hash[:16]}"
    timestamp = _now()
    public_key = announcer_kp.public_key_hex()
    payload = canonical_bytes({
        "kind": "federation_witness",
        "source_id": source_id,
        "source_kind": "contract_announcement",
        "content_hash": content_hash,
        "witness_token": announcement.announcer_world_id,
        "witness_name": announcement.announcer_world_id,
        "witness_public_key": public_key,
        "witness_timestamp": timestamp,
    })
    return FederationAttestation(
        source_id=source_id,
        source_kind="contract_announcement",
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

def _verify_announcement_attestation(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    """Verify a 'contract_announcement' FederationAttestation.

    The attestation's content is a ContractAnnouncement. Verify
    the witness signature (C48 pattern), then verify the
    announcement itself.
    """
    # Content hash check
    recomputed = _hash_payload(canonical_bytes(att.content))
    if recomputed != att.content_hash:
        return (False, "content_hash does not match content")
    # Witness signature
    try:
        sig_ok = verify_signature(
            att.witness_public_key,
            att.witness_canonical_payload(),
            att.witness_signature)
    except Exception as e:
        return (False, f"witness signature check raised: {e}")
    if not sig_ok:
        return (False, "witness signature INVALID")
    # Parse and verify the announcement
    try:
        announcement = ContractAnnouncement.from_dict(att.content)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed announcement: {e}")
    v = verify_announcement(announcement)
    if not v.valid:
        return (False, f"announcement invalid: {v.reason}")
    return (True, "witness signature and announcement valid")


# Extended registry
C59_VERIFIER_REGISTRY: Dict[str, any] = dict(
    DEFAULT_VERIFIER_REGISTRY)
C59_VERIFIER_REGISTRY["contract_announcement"] = (
    _verify_announcement_attestation)


def verify_announcement_attestation(
    att: FederationAttestation,
    context: Optional[Dict] = None,
) -> AttestationVerdict:
    """Verify an announcement-wrapped attestation. Never raises."""
    return verify_federation_attestation(
        att, context, registry=C59_VERIFIER_REGISTRY)


# =====================================================================
# Registry population
# =====================================================================

def announcement_to_registry(
    announcement: ContractAnnouncement,
    registry: ContractRegistry,
) -> None:
    """Populate a C57 ContractRegistry with the embedded
    offer and acceptance. After this, the registry knows about
    the contract; C58's enforcement can cite it.

    Raises ValueError if the announcement doesn't verify.
    """
    v = verify_announcement(announcement)
    if not v.valid:
        raise ValueError(
            f"cannot populate registry from invalid "
            f"announcement: {v.reason}")
    offer = ContractOffer.from_dict(announcement.offer)
    acceptance = ContractAcceptance.from_dict(
        announcement.acceptance)
    registry.register_offer(offer)
    registry.register_acceptance(acceptance)


# =====================================================================
# Announcement builder on top of C55
# =====================================================================

class AnnouncementPublisher:
    """Convenience wrapper around a WorldCurator for publishing
    announcements."""

    def __init__(self, curator: WorldCurator):
        self._curator = curator

    @property
    def world_id(self) -> str:
        return self._curator.world_id

    @property
    def public_key(self) -> str:
        return self._curator.public_key

    def announce(
        self, contract: EstablishedContract,
    ) -> ContractAnnouncement:
        announcement = sign_announcement(
            contract, self._curator._world_kp)
        return announcement

    def wrap_as_attestation(
        self, announcement: ContractAnnouncement,
    ) -> FederationAttestation:
        return announcement_to_attestation_signed(
            announcement, self._curator._world_kp)


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """A (Poetry) and B (Chemistry) establish a contract via C57.
    A announces it via C59. The announcement is wrapped as a
    FederationAttestation, flows through C56's signed relay
    A→C, and C learns of the contract without contacting B.

    Scenarios:
      A. Happy path: A announces, announcement verifies.
      B. Propagation: announcement flows A→C via C56, C's
         registry is populated, C can cite the contract.
      C. Non-party announcement: B tries to announce, works
         (B is also a party). But if X (a stranger) tries, it
         refuses at signing time.
      D. Tampered announcement: flip a term in the embedded
         offer; verification fails.

    Anchor: Dickinson, 'Tell all the truth but tell it slant –'
    (the announcement is the truth told slant — a signed claim
    about a signed claim).
    """
    import json
    from pathlib import Path
    from multiverse_c3 import Act
    from multiverse_c4 import PoetryWorld
    from multiverse_c5 import ChemistryWorld
    from multiverse_c13 import KeyPair
    from multiverse_c54 import AttestedRumor
    from multiverse_c56 import (
        SigningVerifyingUnit, SignedRelayNetwork,
        verify_signed_relay_chain,
    )
    from multiverse_c57 import (
        ContractTerms, ContractRegistry, ContractNegotiator,
        sign_offer, sign_acceptance,
        verify_established_contract,
    )
    from multiverse_c58 import ContractAwarePoetryWorld
    from multiverse_c55 import WorldCurator

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)

    # -- Two worlds establish a contract (C57) ------------------
    world_a = PoetryWorld("world:poetry", "Poetry")
    world_b = ChemistryWorld("world:chemistry", "Chemistry")
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()

    terms = ContractTerms(content={
        "kind": "mutual-recognition",
        "poetry_recognizes": "chem-turns",
        "chemistry_recognizes": "poetry-turns",
    })
    offer = sign_offer(
        world_a.manifest().entity_id, kp_a,
        world_b.manifest().entity_id, terms)
    acceptance = sign_acceptance(
        world_b.manifest().entity_id, kp_b, offer)
    contract = EstablishedContract(
        offer=offer, acceptance=acceptance,
        established_at=_now())
    ok_contract, _ = verify_established_contract(
        contract,
        kp_a.public_key_hex(), kp_b.public_key_hex())

    # -- A announces it (C59) ----------------------------------
    curator_a = WorldCurator(world_a, kp_a)
    publisher_a = AnnouncementPublisher(curator_a)
    announcement = publisher_a.announce(contract)
    verdict_a = verify_announcement(announcement)
    a_valid = verdict_a.valid

    # -- Non-party cannot announce -----------------------------
    stranger_kp = KeyPair.generate()
    stranger_cannot_announce = False
    try:
        sign_announcement(contract, stranger_kp)
    except ValueError:
        stranger_cannot_announce = True

    # -- Tampered announcement ---------------------------------
    tampered_content = dict(announcement.to_dict())
    tampered_offer = dict(tampered_content["offer"])
    tampered_terms = dict(tampered_offer["terms"])
    tampered_terms["poetry_recognizes"] = "TAMPERED"
    tampered_offer["terms"] = tampered_terms
    tampered_content["offer"] = tampered_offer
    tampered_ann = ContractAnnouncement.from_dict(tampered_content)
    verdict_tamper = verify_announcement(tampered_ann)

    # -- Wrap as attestation, propagate A→C via C56 -----------
    wrapped = publisher_a.wrap_as_attestation(announcement)
    dispatch_v = verify_announcement_attestation(wrapped)

    # C is a contract-aware poetry world
    reg_c = ContractRegistry()
    world_c = ContractAwarePoetryWorld(
        "world:poetry-C", "Poetry C",
        registry=reg_c)
    kp_c = KeyPair.generate()

    # Set up C56 signed relay: A → C
    net = SignedRelayNetwork()
    unit_a_kp = KeyPair.generate()
    unit_c_kp = KeyPair.generate()
    # A and C are the same world-signing key? No — the C56
    # units have their own unit_kp; the announcement's witness
    # is the world key. C56 relays the attestation; the
    # announcement verification is separate.
    net.add_unit("A", SigningVerifyingUnit(
        entity_id="world:relay-A", name="Relay A",
        unit_kp=unit_a_kp,
        contacts=["C"],
        trust_context={}))
    net.add_unit("C", SigningVerifyingUnit(
        entity_id="world:relay-C", name="Relay C",
        unit_kp=unit_c_kp,
        contacts=["A"],
        trust_context={}))
    attested = AttestedRumor.from_attestation(wrapped)
    # Seed the announcement at A
    net.seed_attested("A", attested)
    net.run_until_quiet()
    relay_chain = net.collect_relay_chain(attested.rumor_id)
    relay_verdict = verify_signed_relay_chain(relay_chain)

    # -- C verifies the announcement and populates its registry
    c_verdict = verify_announcement(announcement)
    c_learned = c_verdict.valid
    if c_learned:
        announcement_to_registry(announcement, reg_c)

    # C can now cite the contract
    from multiverse_c3 import Petition
    from multiverse_c1 import create_identity
    resident_c = create_identity("Resident-C")
    world_c.petition(Petition(
        petitioner_token=resident_c.token,
        petitioner_name=resident_c.name,
        passport_admissions=(),
        message="hi"))
    cite_act = Act(
        actor_token=resident_c.token,
        type="poem.turn",
        payload={
            "acknowledgment": "(seed)",
            "proposal": "a line",
            "invitation": "?",
            "holds_open": True,
            "cites_contract": terms.terms_hash(),
            "cites_world": "world:chemistry",
        })
    cite_result = world_c.act(cite_act)
    from multiverse_c3 import Ack
    c_can_cite = isinstance(cite_result, Ack)

    # -- Print -----------------------------------------------
    print("=" * 70)
    print("Contract Propagation — announce, relay, learn")
    print("=" * 70)
    print()
    print(f"  Contract: {terms.content.get('kind')}")
    print(f"  Contract ID: {terms.terms_hash()[:16]}...")
    print(f"  Offline verification: "
          f"{'✓' if ok_contract else '✗'}")
    print()
    print(f"  Scenario A: A announces")
    print(f"    Announcement verifies: {'✓' if a_valid else '✗'}")
    print(f"    Stranger cannot sign:  "
          f"{'✓ refused' if stranger_cannot_announce else '✗'}")
    print()
    print(f"  Scenario B: propagation A→C via C56")
    print(f"    Wrapped as attestation: "
          f"{'✓' if dispatch_v.valid else '✗'}")
    print(f"    Relay chain verifies:   "
          f"{'✓' if relay_verdict.valid else '✗'}")
    print(f"    C verified announcement: "
          f"{'✓' if c_learned else '✗'}")
    print(f"    C's registry populated:  "
          f"{reg_c.get(terms.terms_hash()) is not None}")
    print(f"    C can cite the contract: "
          f"{'✓' if c_can_cite else '✗'}")
    print()
    print(f"  Scenario C: tampered announcement")
    print(f"    Verification: {'✓' if verdict_tamper.valid else '✗'} "
          f"({verdict_tamper.reason})")
    print()
    print("  What this demonstrates:")
    print("    - A party to a contract can sign an announcement.")
    print("    - The announcement carries the full contract artifacts")
    print("      and verifies offline.")
    print("    - Announcements flow through C56 signed relay like")
    print("      any other witnessed artifact.")
    print("    - A receiving world can populate its own registry")
    print("      from a verified announcement, then cite the")
    print("      contract in acts (C58).")
    print("    - Tampering with the announcement is caught.")
    print("    - The announcement is a HISTORICAL FACT ('at T, a")
    print("      contract existed'). Current status (revoked or")
    print("      not) requires checking the revocation layer.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Tell all the truth but tell it slant –'")
    print("    'Success in Circuit lies'")

    audit = {
        "contract_id": terms.terms_hash(),
        "offline_verified": ok_contract,
        "scenarios": {
            "A_announce": {
                "valid": a_valid,
                "stranger_refused": stranger_cannot_announce,
            },
            "B_propagation": {
                "wrapped_valid": dispatch_v.valid,
                "relay_valid": relay_verdict.valid,
                "c_learned": c_learned,
                "registry_populated":
                    reg_c.get(terms.terms_hash()) is not None,
                "c_can_cite": c_can_cite,
            },
            "C_tampered": {
                "valid": verdict_tamper.valid,
                "reason": verdict_tamper.reason,
            },
        },
    }
    (path / "contract_propagation_demo.json").write_text(
        json.dumps(audit, indent=2))
    print(f"\n  → {path}/contract_propagation_demo.json")
    return audit
