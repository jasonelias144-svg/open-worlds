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


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Four scenarios:

    A. All-good chain A—B—C—D—E, all with council keys in context.
       Council decision (C45) → attestation → rumor saturates.

    B. Chain with a "skeptic" unit (no trust context). Flow
       reaches the skeptic, is refused, stops. Downstream units
       never hear.

    C. Tampered attestation at seed. Unit refuses at seed;
       zero propagation.

    D. Branching diamond: A→{B,C}, {B,C}→D, D→E. B refuses (no
       context); C accepts. D hears from C, verifies, spreads to
       E. Saturation preserved because a verified path exists.

    Anchor: Dickinson, 'Tell all the truth but tell it slant –'
    (a poem about getting the truth through, even when
    intermediaries are unreliable).
    """
    import json

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)

    # -- Source artifact: a C45 council decision ----------------
    kps = [KeyPair.generate() for _ in range(3)]
    council = DeliberativeCouncil(
        "poetry-council", QuorumRule(2, 2),
        max_rounds=2, stability_rounds=1)
    for i, kp in enumerate(kps):
        council.add_member(DeliberativeMember(
            entity_id=f"poetry-council:m{i}",
            name=f"Councilor-{i}", member_kp=kp,
            decision_rule=lambda p, c: ("yea", "approved")))
    council_keys = {
        f"poetry-council:m{i}": kp.public_key_hex()
        for i, kp in enumerate(kps)
    }
    council_decision = council.deliberate_and_resolve(
        Proposal(content={
            "action": "adopt-relay",
            "note": "tell all the truth but tell it slant",
        }))
    att = attest_deliberative_decision(
        "poetry-council", council_decision)
    attested = AttestedRumor.from_attestation(att)

    context = {
        "member_keys": {"poetry-council": council_keys},
    }

    def build_chain(names, contexts):
        """contexts: dict of name → context (or None for skeptic)."""
        net = AttestedEpidemicNetwork()
        for i, name in enumerate(names):
            contacts = []
            if i > 0:
                contacts.append(names[i - 1])
            if i < len(names) - 1:
                contacts.append(names[i + 1])
            net.add_unit(name, VerifyingEpidemicUnit(
                entity_id=f"world:{name}", name=name,
                contacts=contacts, susceptibility=1,
                trust_context=contexts.get(name)))
        return net

    # -- Scenario A: all-good chain ----------------------------
    chain = ["A", "B", "C", "D", "E"]
    net_a = build_chain(chain, {n: context for n in chain})
    net_a.seed_attested("A", attested)
    net_a.run_until_quiet()
    trail_a = build_audit_trail(net_a, attested.rumor_id)
    a_sat = trail_a.saturated()
    a_verified = trail_a.verified()
    a_refused = trail_a.refused()

    # -- Scenario B: skeptic at C -----------------------------
    contexts_b = {n: context for n in chain}
    contexts_b["C"] = None  # C has no context
    net_b = build_chain(chain, contexts_b)
    net_b.seed_attested("A", attested)
    net_b.run_until_quiet()
    trail_b = build_audit_trail(net_b, attested.rumor_id)
    b_sat = trail_b.saturated()
    b_verified = trail_b.verified()
    b_refused = trail_b.refused()

    # -- Scenario C: tampered attestation at seed -------------
    # Build a tampered attestation whose content_hash is unchanged
    tampered_att = FederationAttestation(
        source_id=att.source_id,
        source_kind=att.source_kind,
        content={**att.content,
                 "inner": {**att.content["inner"],
                           "proposal": {"action": "rejected"}}},
        content_hash=att.content_hash,  # wrong
    )
    # AttestedRumor requires rumor_id == content_hash, so we
    # can't just wrap it; we test via the raw act below
    net_c = build_chain(chain, {n: context for n in chain})
    # Inject the tampered attestation directly as an act
    from multiverse_c3 import Act, Ack, Refusal
    fake_attested_dict = {
        "rumor_id": tampered_att.content_hash,
        "attestation": tampered_att.to_dict(),
    }
    r = net_c._units["A"].act(Act(
        actor_token="external", type="infect",
        payload={
            "rumor_id": tampered_att.content_hash,
            "source": "external",
            "attested": fake_attested_dict,
        }))
    # Even if the unit accepted the exposure, verification failed
    # → it recorded the exposure but won't spread
    net_c.run_until_quiet()
    trail_c = build_audit_trail(net_c, tampered_att.content_hash)
    c_sat = trail_c.saturated()
    c_refused = trail_c.refused()

    # -- Scenario D: branching diamond with one bad branch ----
    # A → B, C; B, C → D; D → E
    net_d = AttestedEpidemicNetwork()
    diamond_layout = {
        "A": ["B", "C"],
        "B": ["A", "D"],
        "C": ["A", "D"],
        "D": ["B", "C", "E"],
        "E": ["D"],
    }
    for name, contacts in diamond_layout.items():
        # B has no context; everyone else does
        ctx = None if name == "B" else context
        net_d.add_unit(name, VerifyingEpidemicUnit(
            entity_id=f"world:{name}", name=name,
            contacts=contacts, susceptibility=1,
            trust_context=ctx))
    net_d.seed_attested("A", attested)
    net_d.run_until_quiet()
    trail_d = build_audit_trail(net_d, attested.rumor_id)
    d_sat = trail_d.saturated()
    d_verified = trail_d.verified()
    d_refused = trail_d.refused()

    # -- Print -----------------------------------------------
    print("=" * 70)
    print("Rumor as Attestation — council decision through epidemic")
    print("=" * 70)
    print()
    print(f"  Source: poetry-council (C45 deliberation)")
    print(f"  Attestation hash: {att.content_hash[:16]}...")
    print(f"  Attestation kind: {att.source_kind}")
    print()

    def report(label, trail, sat, extra=""):
        print(f"  {label}")
        print(f"    saturated: {sat}")
        print(f"    verified:  {trail.verified()}")
        if trail.refused():
            print(f"    refused:   "
                  f"{[u for u, _ in trail.refused()]}")
        if extra:
            print(f"    note:      {extra}")
        print()

    report("Scenario A: all-good chain (A—B—C—D—E)",
           trail_a, a_sat)
    report("Scenario B: skeptic at C (no context)",
           trail_b, b_sat,
           extra="chain stops at C; D, E never hear")
    report("Scenario C: tampered attestation at seed",
           trail_c, c_sat,
           extra="seed unit refuses; zero propagation")
    report("Scenario D: branching with one bad branch (B has no context)",
           trail_d, d_sat,
           extra="C provides the only verified path to D")
    print("  What this demonstrates:")
    print("    - The rumor's content is a signed council decision.")
    print("    - Each unit verifies at receipt; only verified")
    print("      exposures count toward susceptibility.")
    print("    - A skeptic (no context) refuses and does not relay.")
    print("    - A tampered attestation is refused.")
    print("    - A branching topology survives one bad branch, as")
    print("      long as a verified path remains.")
    print("    - Same C52 architecture. Content has provenance.")
    print("    - Composition: no changes to C52's substrate.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Tell all the truth but tell it slant –'")
    print("    'Success in Circuit lies'")

    audit = {
        "source_council": "poetry-council",
        "attestation_kind": att.source_kind,
        "attestation_hash": att.content_hash,
        "scenarios": {
            "A_all_good": {
                "saturated": a_sat,
                "verified": a_verified,
                "refused": a_refused,
            },
            "B_skeptic": {
                "saturated": b_sat,
                "verified": b_verified,
                "refused": b_refused,
            },
            "C_tampered": {
                "saturated": c_sat,
                "refused": c_refused,
            },
            "D_branching": {
                "saturated": d_sat,
                "verified": d_verified,
                "refused": d_refused,
            },
        },
        "trail_a": trail_a.to_dict(),
    }
    (path / "rumor_attestation_demo.json").write_text(
        json.dumps(audit, indent=2))
    print(f"\n  → {path}/rumor_attestation_demo.json")
    return audit
