"""
multiverse_c54.py — Component 54: The Rumor as Attestation.

C52's epidemic carries a rumor as an opaque label. C54 makes the
rumor's content a signed artifact from a different architecture,
and every hop verifies.

The flow:
  C44-46 council → Decision
    → FederationAttestation (C48 wrapper)
    → AttestedRumor (rumor_id = attestation.content_hash)
    → epidemic network → every hop verifies

What changes in the unit:
  C52 EpidemicUnit:  "I spread what I've heard >= susceptibility
                       times."
  C54 VerifyingUnit: "I spread what I've VERIFIED >=
                       susceptibility times."

What does NOT change:
  - Unit has own contacts (edges still decide reach).
  - No shared environment (still direct transmission).
  - No aggregate threshold (still local susceptibility).
  - The rumor either saturates the graph or dies on it.

The architecture is C52. The content has cryptographic provenance.
Composition, not a new architecture.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, plus structural tests (C54
    still has C52's attrs; no C41-C50 attrs).
  - "A world never raises on what a visitor sends" — act
    refuses bad payloads; verifiers return verdicts.
  - "History, not rank" — exposure logs record fact and reason.

Honest limits (documented, tested):
  - Trust anchors are external: the unit's context names which
    keys to trust. Same as everywhere.
  - Units with NO context refuse to relay. Policy choice:
    "I can only spread what I can check." A different policy
    (relay regardless) would be a one-line change.
  - The whole attestation travels in the payload. Production
    would use a hash + fetch. Prototype embeds.
  - No signed relay: units don't sign "I verified this." The
    audit trail is reconstructed from log entries, not from
    a signed relay chain. Signed relays would be C48's pattern
    (attestation of attestation) one layer down — future work.
  - A tampered attestation is refused at the seed and at every
    subsequent hop. Same content_hash check as C48.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c44 import Decision, QuorumRule
from multiverse_c45 import (
    DeliberativeCouncil, DeliberativeMember,
    DeliberativeDecision,
)
from multiverse_c48 import (
    FederationAttestation,
    attest_decision, attest_deliberative_decision,
    verify_federation_attestation,
    DEFAULT_VERIFIER_REGISTRY,
)
from multiverse_c52 import EpidemicUnit, EpidemicNetwork, EpochResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# AttestedRumor
# =====================================================================

@dataclass(frozen=True)
class AttestedRumor:
    """A rumor whose content is a signed FederationAttestation.

    `rumor_id` equals `attestation.content_hash`. That binding
    makes "same rumor" mean "same content, same signature" — so
    susceptibility counts *distinct sources of the same artifact*,
    not just repeated mentions.
    """
    rumor_id: str
    attestation: FederationAttestation

    def __post_init__(self):
        if not isinstance(self.rumor_id, str) or not self.rumor_id:
            raise ValueError("rumor_id required")
        if not isinstance(self.attestation, FederationAttestation):
            raise ValueError(
                "attestation must be FederationAttestation")
        if self.rumor_id != self.attestation.content_hash:
            raise ValueError(
                "rumor_id must equal attestation.content_hash "
                f"({self.attestation.content_hash[:16]}...)")

    @classmethod
    def from_attestation(
        cls, att: FederationAttestation,
    ) -> "AttestedRumor":
        return cls(rumor_id=att.content_hash, attestation=att)

    def to_dict(self) -> Dict:
        return {
            "rumor_id": self.rumor_id,
            "attestation": self.attestation.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "AttestedRumor":
        return cls(
            rumor_id=d["rumor_id"],
            attestation=FederationAttestation.from_dict(
                d["attestation"]),
        )


# =====================================================================
# VerifyingEpidemicUnit
# =====================================================================

class VerifyingEpidemicUnit(EpidemicUnit):
    """A C52 unit that verifies attested rumors at receipt.

    Adds over EpidemicUnit:
      - _trust_context: what to verify against (C48 context dict)
      - _verified_exposures: exposures that passed verification
      - _exposure_reasons: per-(rumor, source) reason string
      - _attestations: verified attestations, so we can re-send

    Only verified exposures count toward susceptibility. Only
    rumors that have reached susceptibility via verified exposures
    spread. A rumor the unit can't verify is refused and not
    relayed — the "courier, not editor" model taken seriously:
    the courier must be able to check that what it carries is
    genuine.
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        contacts: Optional[List[str]] = None,
        susceptibility: int = 1,
        trust_context: Optional[Dict] = None,
    ):
        super().__init__(
            entity_id, name, contacts=contacts,
            susceptibility=susceptibility)
        self._trust_context = dict(trust_context) if trust_context else {}
        self._verified_exposures: Dict[str, Set[str]] = {}
        self._exposure_reasons: Dict[Tuple[str, str], str] = {}
        self._attestations: Dict[str, FederationAttestation] = {}

    @property
    def trust_context(self) -> Dict:
        return dict(self._trust_context)

    def verified_exposures(self, rumor_id: str) -> Set[str]:
        return set(self._verified_exposures.get(rumor_id, set()))

    def exposure_reason(
        self, rumor_id: str, source: str,
    ) -> Optional[str]:
        return self._exposure_reasons.get((rumor_id, source))

    def attestation_for(
        self, rumor_id: str,
    ) -> Optional[FederationAttestation]:
        return self._attestations.get(rumor_id)

    def verify_attested(
        self, attested: AttestedRumor,
    ) -> Tuple[bool, str]:
        """Verify the attestation against our trust context.
        Never raises."""
        if not self._trust_context:
            return (False, "no trust context supplied")
        try:
            verdict = verify_federation_attestation(
                attested.attestation, self._trust_context)
        except Exception as e:
            return (False, f"verifier raised: {e}")
        if verdict.valid:
            return (True, "attestation verified")
        return (False, f"attestation invalid: {verdict.reason}")

    # -- WCP act handler ----------------------------------------

    def act(self, act: Act):
        if act.type != "infect":
            return super().act(act)
        payload = act.payload or {}
        rumor_id = payload.get("rumor_id")
        source = payload.get("source")
        attested_dict = payload.get("attested")
        if not isinstance(rumor_id, str) or not rumor_id:
            return Refusal(reason="infect requires rumor_id")
        if not isinstance(source, str) or not source:
            return Refusal(reason="infect requires source")
        if not isinstance(attested_dict, dict):
            return Refusal(
                reason="infect requires 'attested' payload")
        try:
            attested = AttestedRumor.from_dict(attested_dict)
        except (KeyError, ValueError, TypeError) as e:
            return Refusal(
                reason=f"malformed attested rumor: {e}")
        if attested.rumor_id != rumor_id:
            return Refusal(
                reason=("payload.rumor_id does not match "
                        "attested.rumor_id"))
        ok, reason = self.verify_attested(attested)
        # Record exposure regardless of verification; count only
        # verified ones toward susceptibility
        self._exposures.setdefault(rumor_id, set()).add(source)
        self._exposure_reasons[(rumor_id, source)] = reason
        if ok:
            self._verified_exposures.setdefault(
                rumor_id, set()).add(source)
            self._attestations[rumor_id] = attested.attestation
        self._log.append(type(self._log[0])(**{
            "timestamp": _now(),
            "kind": "exposure",
            "actor_token": source,
            "data": {
                "rumor_id": rumor_id,
                "verified": ok,
                "reason": reason,
                "verified_source_count":
                    len(self._verified_exposures.get(
                        rumor_id, set())),
                "susceptibility": self._susceptibility,
            },
        }))
        return Ack(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    # -- Local dynamics ----------------------------------------

    def tick(self, epoch: int) -> List[Tuple[str, str]]:
        """Same contract as C52, but susceptibility is over
        VERIFIED exposures only."""
        # 1. Start spreading on verified threshold
        for rumor_id, sources in self._verified_exposures.items():
            if (len(sources) >= self._susceptibility
                    and rumor_id not in self._spreading):
                self._spreading.add(rumor_id)
                self._spread_done.setdefault(rumor_id, set())
                self._log.append(type(self._log[0])(**{
                    "timestamp": _now(),
                    "kind": "spreading_start",
                    "actor_token": self._manifest.entity_id,
                    "data": {"rumor_id": rumor_id,
                              "epoch": epoch,
                              "verified_source_count":
                                  len(sources)},
                }))
        # 2. Spread to each contact once
        pending: List[Tuple[str, str]] = []
        for rumor_id in list(self._spreading):
            already = self._spread_done.setdefault(rumor_id, set())
            for contact in self._contacts:
                if contact not in already:
                    already.add(contact)
                    pending.append((contact, rumor_id))
        return pending


# =====================================================================
# AttestedEpidemicNetwork
# =====================================================================

class AttestedEpidemicNetwork(EpidemicNetwork):
    """A C52 network that carries the attestation with each
    transmission."""

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
                    # Non-verifying units can't supply; skip
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
                for n, u in self._units.items()},
        )

    def seed_attested(
        self, unit_name: str, attested: AttestedRumor,
        source: str = "external",
    ) -> bool:
        """Inject an attested rumor into a unit. Returns True iff
        accepted (signature check may still fail downstream)."""
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


def _attestation_of(
    unit: EpidemicUnit, rumor_id: str,
) -> Optional[FederationAttestation]:
    if isinstance(unit, VerifyingEpidemicUnit):
        return unit.attestation_for(rumor_id)
    return None


# =====================================================================
# Audit trail
# =====================================================================

@dataclass
class ExposureRecord:
    source: str
    verified: bool
    reason: str


@dataclass
class UnitAudit:
    unit_name: str
    exposures: List[ExposureRecord]
    spreading: bool
    told_contacts: List[str]

    def reached_verified(self) -> bool:
        return any(e.verified for e in self.exposures)


@dataclass
class RumorAuditTrail:
    rumor_id: str
    units: List[UnitAudit]

    def reached(self) -> List[str]:
        return [u.unit_name for u in self.units if u.exposures]

    def verified(self) -> List[str]:
        return [u.unit_name for u in self.units
                if u.reached_verified()]

    def refused(self) -> List[Tuple[str, str]]:
        """[(unit, reason)] for units that received but refused."""
        out: List[Tuple[str, str]] = []
        for u in self.units:
            for e in u.exposures:
                if not e.verified:
                    out.append((u.unit_name, e.reason))
        return out

    def saturated(self) -> bool:
        return (len(self.units) > 0
                and all(u.reached_verified() for u in self.units))

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Rumor Audit Trail",
            "=" * 70,
            f"  rumor_id: {self.rumor_id[:16]}...",
            f"  units:    {len(self.units)}",
            f"  reached:  {len(self.reached())}",
            f"  verified: {len(self.verified())}",
            f"  saturated: {self.saturated()}",
            "",
        ]
        for u in self.units:
            if not u.exposures:
                lines.append(
                    f"  · {u.unit_name}: not reached")
                continue
            if u.reached_verified():
                marker = "✓"
                note = "spreading" if u.spreading else "quiet"
            else:
                marker = "✗"
                note = "refused"
            lines.append(
                f"  {marker} {u.unit_name}: {note}")
            for e in u.exposures:
                if e.verified:
                    lines.append(
                        f"      ← {e.source}  verified")
                else:
                    lines.append(
                        f"      ← {e.source}  REFUSED: "
                        f"{e.reason}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "rumor_id": self.rumor_id,
            "units": [
                {
                    "unit_name": u.unit_name,
                    "spreading": u.spreading,
                    "reached_verified": u.reached_verified(),
                    "told_contacts": u.told_contacts,
                    "exposures": [
                        {"source": e.source,
                         "verified": e.verified,
                         "reason": e.reason}
                        for e in u.exposures
                    ],
                }
                for u in self.units
            ],
            "reached": self.reached(),
            "verified": self.verified(),
            "refused": self.refused(),
            "saturated": self.saturated(),
        }


def build_audit_trail(
    network: AttestedEpidemicNetwork, rumor_id: str,
) -> RumorAuditTrail:
    """Reconstruct the audit from the network's unit logs."""
    units: List[UnitAudit] = []
    for name, unit in network._units.items():
        exposures: List[ExposureRecord] = []
        if isinstance(unit, VerifyingEpidemicUnit):
            for source in unit.exposures(rumor_id):
                reason = unit.exposure_reason(rumor_id, source) or ""
                verified = source in unit.verified_exposures(rumor_id)
                exposures.append(ExposureRecord(
                    source=source, verified=verified,
                    reason=reason))
            spreading = unit.is_spreading(rumor_id)
            told = sorted(unit._spread_done.get(rumor_id, set()))
        else:
            spreading = False
            told = []
        units.append(UnitAudit(
            unit_name=name, exposures=exposures,
            spreading=spreading, told_contacts=told))
    return RumorAuditTrail(rumor_id=rumor_id, units=units)
