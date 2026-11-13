"""
multiverse_c56.py — Component 56: The Signed Relay Chain.

C54 named the honest limit: "no signed relay." C56 closes it.

Two artifact types per hop:
  - RelayAttestation (sender-signed):
      "I, unit S, transmitted attestation X to unit T at time Y."
  - ReceiptAttestation (receiver-signed):
      "I, unit T, received X from S at time Y.
       Verified: {yes|no}. Reason: {...}."

A confirmed hop is a (relay, receipt) pair matching on
(relayer==source AND target==receiver AND same attestation hash).
An unconfirmed hop has a relay but no matching receipt.

The SignedRelayChain wraps the original attestation plus all relays
and receipts. Verification reconstructs the DAG and checks:
  - The original attestation verifies (via C48)
  - Every relay and receipt signature verifies
  - Every receipt's source has a matching relay
  - The DAG is connected from the seed recipient
  - Every receipt-holder is reachable from the seed

Structural facts:
  - No changes to C54's VerifyingEpidemicUnit or
    AttestedEpidemicNetwork. SigningVerifyingUnit and
    SignedRelayNetwork are subclasses.
  - C52's architecture is unchanged: contacts, susceptibility,
    exposures, spreading — all still present.
  - No new primitive at the substrate level. The relay chain is
    a pattern of signed messages, verified by composition.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, plus structural tests (C56
    inherits C52 and C54 attrs; no other architecture's).
  - "A world never raises on what a visitor sends" — verifiers
    return verdicts; act refuses bad payloads.
  - "History, not rank" — the chain is a record.

Honest limits (documented, tested):
  - Unconfirmed hops are visible, not errors. A relay without
    a matching receipt is reported as `unconfirmed`, not as
    a failure of the chain.
  - Relay timestamp is sender's clock. Production would want
    a trusted time source. For the prototype, timestamps are
    claims, verified as part of the signature only.
  - Seed receipts have source="external". The seed is trusted
    by construction; there's no signature from "outside the
    system."
  - No transferability of relay chain across attestations. Each
    chain verifies one attestation.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c44 import QuorumRule
from multiverse_c45 import (
    Proposal, DeliberativeCouncil, DeliberativeMember,
)
from multiverse_c48 import (
    FederationAttestation,
    attest_deliberative_decision,
    verify_federation_attestation,
)
from multiverse_c52 import EpochResult
from multiverse_c54 import (
    AttestedRumor, VerifyingEpidemicUnit,
    AttestedEpidemicNetwork, build_audit_trail,
    _attestation_of,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# RelayAttestation
# =====================================================================

@dataclass(frozen=True)
class RelayAttestation:
    relayer_world_id: str
    relayer_public_key: str
    attestation_content_hash: str
    target_world_id: str
    epoch: int
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("relayer_world_id", "target_world_id",
                  "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.relayer_public_key) != 64:
            raise ValueError(
                "relayer_public_key must be 64 hex chars")
        if len(self.attestation_content_hash) != 64:
            raise ValueError(
                "attestation_content_hash must be 64 hex chars")
        if self.epoch < 0:
            raise ValueError("epoch must be >= 0")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "relay_attestation",
            "relayer_world_id": self.relayer_world_id,
            "relayer_public_key": self.relayer_public_key,
            "attestation_content_hash":
                self.attestation_content_hash,
            "target_world_id": self.target_world_id,
            "epoch": self.epoch,
            "timestamp": self.timestamp,
        })

    def relay_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "relayer_world_id": self.relayer_world_id,
            "relayer_public_key": self.relayer_public_key,
            "attestation_content_hash":
                self.attestation_content_hash,
            "target_world_id": self.target_world_id,
            "epoch": self.epoch,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RelayAttestation":
        return cls(
            relayer_world_id=d["relayer_world_id"],
            relayer_public_key=d["relayer_public_key"],
            attestation_content_hash=d[
                "attestation_content_hash"],
            target_world_id=d["target_world_id"],
            epoch=d["epoch"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_relay(
    relay: RelayAttestation,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = expected_public_key or relay.relayer_public_key
        return verify_signature(
            key, relay.canonical_payload(), relay.signature)
    except Exception:
        return False


# =====================================================================
# ReceiptAttestation
# =====================================================================

@dataclass(frozen=True)
class ReceiptAttestation:
    receiver_world_id: str
    receiver_public_key: str
    attestation_content_hash: str
    source_world_id: str
    verified: bool
    reason: str
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("receiver_world_id", "source_world_id",
                  "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.receiver_public_key) != 64:
            raise ValueError(
                "receiver_public_key must be 64 hex chars")
        if len(self.attestation_content_hash) != 64:
            raise ValueError(
                "attestation_content_hash must be 64 hex chars")
        if not isinstance(self.verified, bool):
            raise ValueError("verified must be bool")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "receipt_attestation",
            "receiver_world_id": self.receiver_world_id,
            "receiver_public_key": self.receiver_public_key,
            "attestation_content_hash":
                self.attestation_content_hash,
            "source_world_id": self.source_world_id,
            "verified": self.verified,
            "reason": self.reason,
            "timestamp": self.timestamp,
        })

    def receipt_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "receiver_world_id": self.receiver_world_id,
            "receiver_public_key": self.receiver_public_key,
            "attestation_content_hash":
                self.attestation_content_hash,
            "source_world_id": self.source_world_id,
            "verified": self.verified,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ReceiptAttestation":
        return cls(
            receiver_world_id=d["receiver_world_id"],
            receiver_public_key=d["receiver_public_key"],
            attestation_content_hash=d[
                "attestation_content_hash"],
            source_world_id=d["source_world_id"],
            verified=d["verified"],
            reason=d.get("reason", ""),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_receipt(
    receipt: ReceiptAttestation,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = expected_public_key or receipt.receiver_public_key
        return verify_signature(
            key, receipt.canonical_payload(),
            receipt.signature)
    except Exception:
        return False


# =====================================================================
# SigningVerifyingUnit — adds relay/receipt signing to C54
# =====================================================================

class SigningVerifyingUnit(VerifyingEpidemicUnit):
    """A C54 unit that produces signed relay and receipt artifacts.

    Inherits all C52 and C54 attributes. Adds:
      - _unit_kp: the unit's own signing key
      - _relay_attestations: relays the unit has produced
      - _receipt_attestations: receipts the unit has produced
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        unit_kp: KeyPair,
        contacts: Optional[List[str]] = None,
        susceptibility: int = 1,
        trust_context: Optional[Dict] = None,
    ):
        super().__init__(
            entity_id, name, contacts=contacts,
            susceptibility=susceptibility,
            trust_context=trust_context)
        self._unit_kp = unit_kp
        self._unit_public_key = unit_kp.public_key_hex()
        self._relay_attestations: List[RelayAttestation] = []
        self._receipt_attestations: List[ReceiptAttestation] = []

    @property
    def unit_public_key(self) -> str:
        return self._unit_public_key

    def relay_attestations(self) -> List[RelayAttestation]:
        return list(self._relay_attestations)

    def receipt_attestations(self) -> List[ReceiptAttestation]:
        return list(self._receipt_attestations)

    def act(self, act: Act):
        # Let the parent do its work
        result = super().act(act)
        # Sign a receipt if the parent recorded the exposure
        if (isinstance(result, Ack)
                and act.type == "infect"):
            payload = act.payload or {}
            attested_dict = payload.get("attested")
            rumor_id = payload.get("rumor_id")
            source = payload.get("source")
            if (isinstance(attested_dict, dict)
                    and isinstance(rumor_id, str)
                    and isinstance(source, str)):
                try:
                    attested = AttestedRumor.from_dict(
                        attested_dict)
                    verified = source in self.verified_exposures(
                        rumor_id)
                    reason = (self.exposure_reason(
                        rumor_id, source) or "")
                    receipt = self._sign_receipt(
                        attested, source, verified, reason)
                    self._receipt_attestations.append(receipt)
                except Exception:
                    pass
        return result

    def record_delivery(
        self, target_id: str, rumor_id: str, epoch: int,
    ) -> None:
        """Called by the network after delivering a transmission.
        Signs a relay attesting the sender's act."""
        attested = self._attestations.get(rumor_id)
        if attested is None:
            return
        ts = _now()
        payload = canonical_bytes({
            "kind": "relay_attestation",
            "relayer_world_id": self._manifest.entity_id,
            "relayer_public_key": self._unit_public_key,
            "attestation_content_hash": attested.content_hash,
            "target_world_id": target_id,
            "epoch": epoch,
            "timestamp": ts,
        })
        sig = self._unit_kp.sign(payload).hex()
        self._relay_attestations.append(RelayAttestation(
            relayer_world_id=self._manifest.entity_id,
            relayer_public_key=self._unit_public_key,
            attestation_content_hash=attested.content_hash,
            target_world_id=target_id,
            epoch=epoch,
            timestamp=ts,
            signature=sig,
        ))

    def _sign_receipt(
        self, attested: AttestedRumor, source: str,
        verified: bool, reason: str,
    ) -> ReceiptAttestation:
        ts = _now()
        payload = canonical_bytes({
            "kind": "receipt_attestation",
            "receiver_world_id": self._manifest.entity_id,
            "receiver_public_key": self._unit_public_key,
            "attestation_content_hash": attested.content_hash,
            "source_world_id": source,
            "verified": verified,
            "reason": reason,
            "timestamp": ts,
        })
        sig = self._unit_kp.sign(payload).hex()
        return ReceiptAttestation(
            receiver_world_id=self._manifest.entity_id,
            receiver_public_key=self._unit_public_key,
            attestation_content_hash=attested.content_hash,
            source_world_id=source,
            verified=verified,
            reason=reason,
            timestamp=ts,
            signature=sig,
        )


# =====================================================================
# SignedRelayNetwork — drives signing
# =====================================================================

class SignedRelayNetwork(AttestedEpidemicNetwork):
    """An AttestedEpidemicNetwork that triggers signing on delivery."""

    def run_epoch(self) -> EpochResult:
        epoch = self._epoch
        self._epoch += 1
        transmissions: List[Tuple[str, str, str]] = []
        for name, unit in self._units.items():
            pending = unit.tick(epoch)
            for target_name, rumor_id in pending:
                target = self._units.get(target_name)
                if target is None:
                    continue
                attested = _attestation_of(unit, rumor_id)
                if attested is None:
                    continue
                r = target.act(Act(
                    actor_token=name, type="infect",
                    payload={
                        "rumor_id": rumor_id,
                        "source": name,
                        "attested": {
                            "rumor_id": rumor_id,
                            "attestation": attested.to_dict(),
                        },
                    }))
                # Sender signs relay REGARDLESS of the receiver's
                # structural response — the transmission happened
                if hasattr(unit, "record_delivery"):
                    unit.record_delivery(
                        target_name, rumor_id, epoch)
                if isinstance(r, Ack):
                    transmissions.append(
                        (name, target_name, rumor_id))
        return EpochResult(
            epoch=epoch,
            transmissions=transmissions,
            exposures_by_unit={
                n: {rid: len(u.exposures(rid))
                    for rid in u._exposures}
                for n, u in self._units.items()},
            spreading_by_unit={
                n: set(u._spreading)
                for n, u in self._units.items()})

    def seed_attested(
        self, unit_name: str, attested: AttestedRumor,
        source: str = "external",
    ) -> bool:
        """Inject an attested rumor. The seed recipient signs a
        receipt with source='external'."""
        unit = self._units.get(unit_name)
        if unit is None:
            return False
        r = unit.act(Act(
            actor_token=source, type="infect",
            payload={
                "rumor_id": attested.rumor_id,
                "source": source,
                "attested": attested.to_dict(),
            }))
        return isinstance(r, Ack)

    def collect_relay_chain(
        self, rumor_id: str,
    ) -> Optional["SignedRelayChain"]:
        """Collect all relay and receipt attestations for a rumor.
        Returns None if no unit has the attestation."""
        relays: List[RelayAttestation] = []
        receipts: List[ReceiptAttestation] = []
        original: Optional[FederationAttestation] = None
        for unit in self._units.values():
            if not isinstance(unit, SigningVerifyingUnit):
                continue
            for r in unit.relay_attestations():
                if r.attestation_content_hash == rumor_id:
                    relays.append(r)
            for rc in unit.receipt_attestations():
                if rc.attestation_content_hash == rumor_id:
                    receipts.append(rc)
            if original is None:
                att = unit._attestations.get(rumor_id)
                if att is not None:
                    original = att
        if original is None:
            return None
        return SignedRelayChain(
            attestation=original,
            relays=tuple(relays),
            receipts=tuple(receipts),
        )


# =====================================================================
# SignedRelayChain
# =====================================================================

@dataclass(frozen=True)
class SignedRelayChain:
    attestation: FederationAttestation
    relays: Tuple[RelayAttestation, ...]
    receipts: Tuple[ReceiptAttestation, ...]

    def content_hash(self) -> str:
        return self.attestation.content_hash

    def to_dict(self) -> Dict:
        return {
            "attestation": self.attestation.to_dict(),
            "relays": [r.to_dict() for r in self.relays],
            "receipts": [r.to_dict() for r in self.receipts],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "SignedRelayChain":
        return cls(
            attestation=FederationAttestation.from_dict(
                d["attestation"]),
            relays=tuple(
                RelayAttestation.from_dict(r)
                for r in d.get("relays", [])),
            receipts=tuple(
                ReceiptAttestation.from_dict(r)
                for r in d.get("receipts", [])),
        )


# =====================================================================
# Hop reconstruction and verification
# =====================================================================

@dataclass(frozen=True)
class Hop:
    """One transmission in the chain, possibly confirmed."""
    relayer_world_id: str
    target_world_id: str
    attestation_content_hash: str
    relay: RelayAttestation
    receipt: Optional[ReceiptAttestation]

    @property
    def confirmed(self) -> bool:
        return self.receipt is not None

    @property
    def receipt_verified(self) -> Optional[bool]:
        return self.receipt.verified if self.receipt else None


@dataclass
class SignedRelayVerdict:
    valid: bool
    reason: str
    attestation_valid: bool
    all_relays_signed: bool
    all_receipts_signed: bool
    hops: List[Hop]
    confirmed_hops: int
    unconfirmed_hops: int
    seed_recipient: Optional[str]
    reached: List[str]
    unreachable: List[str]
    bad_relays: List[Tuple[str, str]] = field(
        default_factory=list)
    bad_receipts: List[Tuple[str, str]] = field(
        default_factory=list)

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Signed Relay Chain Verification",
            "=" * 70,
            f"  content_hash:     "
            f"{self.hops[0].attestation_content_hash[:16] + '...' if self.hops else '(no hops)'}",
            f"  attestation:      "
            f"{'✓ valid' if self.attestation_valid else '✗ INVALID'}",
            f"  relays signed:    "
            f"{'✓' if self.all_relays_signed else '✗'}",
            f"  receipts signed:  "
            f"{'✓' if self.all_receipts_signed else '✗'}",
            f"  seed recipient:   {self.seed_recipient}",
            f"  hops:             {len(self.hops)} "
            f"({self.confirmed_hops} confirmed, "
            f"{self.unconfirmed_hops} unconfirmed)",
            "",
            "  Hops:",
        ]
        for h in self.hops:
            if h.confirmed:
                if h.receipt_verified:
                    marker = "✓"
                    note = "verified"
                else:
                    marker = "✗"
                    note = f"refused: {h.receipt.reason}"
            else:
                marker = "·"
                note = "unconfirmed"
            lines.append(
                f"    {marker} {h.relayer_world_id} → "
                f"{h.target_world_id}  ({note})")
        lines.append("")
        lines.append(f"  reached from seed: {self.reached}")
        if self.unreachable:
            lines.append(
                f"  unreachable:       {self.unreachable}")
        if self.bad_relays:
            lines.append("  bad relays:")
            for w, reason in self.bad_relays:
                lines.append(f"    ✗ {w}: {reason}")
        if self.bad_receipts:
            lines.append("  bad receipts:")
            for w, reason in self.bad_receipts:
                lines.append(f"    ✗ {w}: {reason}")
        lines.append("")
        lines.append(f"  Result: "
                     f"{'✓ VALID' if self.valid else '✗ INVALID'}")
        if not self.valid:
            lines.append(f"  Reason: {self.reason}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "attestation_valid": self.attestation_valid,
            "all_relays_signed": self.all_relays_signed,
            "all_receipts_signed": self.all_receipts_signed,
            "hops": [
                {
                    "relayer": h.relayer_world_id,
                    "target": h.target_world_id,
                    "confirmed": h.confirmed,
                    "receipt_verified": h.receipt_verified,
                    "receipt_reason": (
                        h.receipt.reason if h.receipt else None),
                }
                for h in self.hops
            ],
            "confirmed_hops": self.confirmed_hops,
            "unconfirmed_hops": self.unconfirmed_hops,
            "seed_recipient": self.seed_recipient,
            "reached": self.reached,
            "unreachable": self.unreachable,
        }


def reconstruct_hops(
    chain: SignedRelayChain,
) -> List[Hop]:
    """Match each relay to a receipt. Confirmed = matched."""
    receipts_index: Dict[
        Tuple[str, str, str], ReceiptAttestation] = {}
    for rc in chain.receipts:
        key = (rc.receiver_world_id, rc.source_world_id,
                rc.attestation_content_hash)
        # First receipt wins if duplicates (a unit shouldn't
        # receive the same content from the same source twice,
        # but if it did, one is enough)
        receipts_index.setdefault(key, rc)
    hops: List[Hop] = []
    for r in chain.relays:
        key = (r.target_world_id, r.relayer_world_id,
                r.attestation_content_hash)
        receipt = receipts_index.get(key)
        hops.append(Hop(
            relayer_world_id=r.relayer_world_id,
            target_world_id=r.target_world_id,
            attestation_content_hash=r.attestation_content_hash,
            relay=r,
            receipt=receipt,
        ))
    return hops


def _compute_reached(
    hops: List[Hop], seed: Optional[str],
) -> List[str]:
    if seed is None:
        return []
    confirmed_by_relayer: Dict[str, List[str]] = {}
    for h in hops:
        if h.confirmed:
            confirmed_by_relayer.setdefault(
                h.relayer_world_id, []).append(h.target_world_id)
    reached = {seed}
    frontier = [seed]
    while frontier:
        cur = frontier.pop()
        for tgt in confirmed_by_relayer.get(cur, ()):
            if tgt not in reached:
                reached.add(tgt)
                frontier.append(tgt)
    return sorted(reached)


def verify_signed_relay_chain(
    chain: SignedRelayChain,
    context: Optional[Dict] = None,
    relay_public_keys: Optional[Dict[str, str]] = None,
    receipt_public_keys: Optional[Dict[str, str]] = None,
) -> SignedRelayVerdict:
    """Verify a SignedRelayChain. Never raises.

    Checks, in order:
      1. The wrapped attestation verifies (via C48), if a context
         is supplied.
      2. Every relay's signature verifies (against the caller's
         key if supplied, else the declared key).
      3. Every receipt's signature verifies (same discipline).
      4. Hops are reconstructed by (relayer, target, hash) matching.
      5. Seed recipient identified from receipts with
         source_world_id == "external".
      6. Reached set computed by walking confirmed hops from seed.
      7. All receipt-holders are reachable.

    A chain is VALID if:
      - The attestation verified (if context supplied)
      - All signatures verified
      - Every receipt's source has a matching relay
      - Every receipt-holder is reachable from the seed
    Unconfirmed hops do NOT invalidate the chain — they are
    honest gaps, reported separately.
    """
    if not HAS_CRYPTO:
        return SignedRelayVerdict(
            valid=False, reason="cryptography not installed",
            attestation_valid=False,
            all_relays_signed=False,
            all_receipts_signed=False,
            hops=[], confirmed_hops=0, unconfirmed_hops=0,
            seed_recipient=None, reached=[], unreachable=[])
    if not isinstance(chain, SignedRelayChain):
        return SignedRelayVerdict(
            valid=False, reason="not a SignedRelayChain",
            attestation_valid=False,
            all_relays_signed=False,
            all_receipts_signed=False,
            hops=[], confirmed_hops=0, unconfirmed_hops=0,
            seed_recipient=None, reached=[], unreachable=[])

    # 1. Attestation
    attestation_valid = True
    if context is not None:
        try:
            av = verify_federation_attestation(
                chain.attestation, context)
            attestation_valid = av.valid
        except Exception:
            attestation_valid = False

    # 2. Relays
    bad_relays: List[Tuple[str, str]] = []
    for r in chain.relays:
        expected = (relay_public_keys or {}).get(
            r.relayer_world_id)
        if relay_public_keys is not None and expected is None:
            bad_relays.append(
                (r.relayer_world_id, "no relay public key"))
            continue
        if not verify_relay(r, expected):
            bad_relays.append(
                (r.relayer_world_id, "signature INVALID"))
    all_relays_signed = not bad_relays

    # 3. Receipts
    bad_receipts: List[Tuple[str, str]] = []
    for rc in chain.receipts:
        expected = (receipt_public_keys or {}).get(
            rc.receiver_world_id)
        if receipt_public_keys is not None and expected is None:
            bad_receipts.append(
                (rc.receiver_world_id,
                  "no receipt public key"))
            continue
        if not verify_receipt(rc, expected):
            bad_receipts.append(
                (rc.receiver_world_id, "signature INVALID"))
    all_receipts_signed = not bad_receipts

    # 4. Hops
    hops = reconstruct_hops(chain)

    # 5. Seed
    seed_recipient: Optional[str] = None
    for rc in chain.receipts:
        if rc.source_world_id == "external":
            seed_recipient = rc.receiver_world_id
            break

    # 6. Reached
    reached = _compute_reached(hops, seed_recipient)

    # 7. Unreachable: receipt holders not in reached and not seed
    receipt_holders = {rc.receiver_world_id
                        for rc in chain.receipts}
    unreachable = sorted(receipt_holders - set(reached))

    # Orphan receipts: sources that never signed a matching relay
    relays_set = {(r.relayer_world_id, r.target_world_id,
                    r.attestation_content_hash)
                   for r in chain.relays}
    for rc in chain.receipts:
        if rc.source_world_id == "external":
            continue  # seed receipt
        key = (rc.source_world_id, rc.receiver_world_id,
                rc.attestation_content_hash)
        if key not in relays_set:
            bad_receipts.append(
                (rc.receiver_world_id,
                  f"no matching relay from {rc.source_world_id}"))

    confirmed = sum(1 for h in hops if h.confirmed)
    unconfirmed = len(hops) - confirmed

    all_valid = (
        attestation_valid
        and all_relays_signed
        and all_receipts_signed
        and seed_recipient is not None
        and not unreachable
        and not bad_receipts
    )
    if all_valid:
        reason = ("attestation valid, all signatures verify, "
                   "all hops reachable from seed")
    else:
        parts = []
        if not attestation_valid:
            parts.append("attestation invalid")
        if not all_relays_signed:
            parts.append(f"{len(bad_relays)} bad relay(s)")
        if not all_receipts_signed:
            parts.append(f"{len(bad_receipts)} bad receipt(s)")
        if seed_recipient is None:
            parts.append("no seed receipt")
        if unreachable:
            parts.append(f"{len(unreachable)} unreachable")
        reason = "; ".join(parts)

    return SignedRelayVerdict(
        valid=all_valid, reason=reason,
        attestation_valid=attestation_valid,
        all_relays_signed=all_relays_signed,
        all_receipts_signed=all_receipts_signed,
        hops=hops,
        confirmed_hops=confirmed,
        unconfirmed_hops=unconfirmed,
        seed_recipient=seed_recipient,
        reached=reached,
        unreachable=unreachable,
        bad_relays=bad_relays,
        bad_receipts=bad_receipts,
    )
