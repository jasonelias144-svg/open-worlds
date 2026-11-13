"""
multiverse_c37.py — Component 37: Person Worlds and Coordination.

C36 let a person hold world-level tokens. C37 opens the layer
above the world: a PersonWorld is a WCP entity where persons
meet to coordinate their world-level projections.

The primitive: a coordination attestation. Two or more persons
co-sign a claim of their choosing. The PersonWorld records it if
and only if every signature verifies against an admitted person's
registered key.

Design:
  - CoordinationClaim: (kind, content dict). Free-form.
  - CoSigner: (person_token, person_public_key, signature).
  - CoordinationAttestation: claim + co_signers + timestamp.
  - create_coordination_attestation: builds and signs one.
  - verify_coordination_attestation: verifies signatures only.
  - PersonWorld: WCP entity. Petitions require extra.public_key.
    Only valid act: coordination.attest. Supports leave.

The World does NOT verify claim content. It records who said
what about what. Same discipline as C4.

House rules honored:
  - "A world never raises on what a visitor sends" — PersonWorld
    refuses bad input; verifiers return verdicts.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: unadmitted actor, unadmitted co-signer,
    forged signature, tampered claim, dup co-signers, actor not
    in co-signers, conformance, leave, JSON roundtrip.
  - "History, not rank" — attestation is a record, not a score.

Honest limits (documented, tested):
  - The World trusts its admission records. It verifies that
    each co-signer's key matches what was registered at
    admission. First admission is TOFU for the person's key.
    C36's binding layer sits above; this component doesn't
    verify person bindings (that's a caller-level check).
  - The claim's content is not verified. A person can co-sign a
    claim that references a passport entry that doesn't exist.
    A reader with the referenced artifacts can check; the
    PersonWorld cannot.
  - No forks/merges of persons. That's the lineage layer,
    future work.
  - No key rotation. Same TOFU limit as C28 and C36.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity
from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c36 import PersonIdentity


# =====================================================================
# CoordinationClaim — what is being co-attested
# =====================================================================

@dataclass(frozen=True)
class CoordinationClaim:
    kind: str
    content: Dict

    def __post_init__(self):
        if not isinstance(self.kind, str) or not self.kind:
            raise ValueError("claim.kind must be non-empty string")
        if not isinstance(self.content, dict):
            raise ValueError("claim.content must be a dict")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "coordination_claim",
            "claim_kind": self.kind,
            "content": self.content,
        })

    def to_dict(self) -> Dict:
        return {"claim_kind": self.kind, "content": self.content}

    @classmethod
    def from_dict(cls, d: Dict) -> "CoordinationClaim":
        return cls(kind=d["claim_kind"], content=d["content"])


# =====================================================================
# CoSigner — one person's signature
# =====================================================================

@dataclass(frozen=True)
class CoSigner:
    person_token: str
    person_public_key: str
    signature: str

    def __post_init__(self):
        for f in ("person_token", "person_public_key", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.person_public_key) != 64:
            raise ValueError("person_public_key must be 64 hex chars")

    def to_dict(self) -> Dict:
        return {
            "person_token": self.person_token,
            "person_public_key": self.person_public_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CoSigner":
        return cls(
            person_token=d["person_token"],
            person_public_key=d["person_public_key"],
            signature=d["signature"],
        )


# =====================================================================
# CoordinationAttestation
# =====================================================================

@dataclass(frozen=True)
class CoordinationAttestation:
    claim: CoordinationClaim
    co_signers: Tuple[CoSigner, ...]
    timestamp: str

    def __post_init__(self):
        if not isinstance(self.claim, CoordinationClaim):
            raise ValueError("claim must be CoordinationClaim")
        if len(self.co_signers) < 2:
            raise ValueError(
                "coordination requires at least 2 co-signers")
        tokens = [cs.person_token for cs in self.co_signers]
        if len(tokens) != len(set(tokens)):
            raise ValueError("co-signers must be distinct persons")
        if not self.timestamp:
            raise ValueError("timestamp required")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "coordination_attestation",
            "claim": self.claim.to_dict(),
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "claim": self.claim.to_dict(),
            "co_signers": [cs.to_dict() for cs in self.co_signers],
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CoordinationAttestation":
        return cls(
            claim=CoordinationClaim.from_dict(d["claim"]),
            co_signers=tuple(
                CoSigner.from_dict(cs) for cs in d["co_signers"]),
            timestamp=d["timestamp"],
        )


# =====================================================================
# Create an attestation
# =====================================================================

def create_coordination_attestation(
    claim: CoordinationClaim,
    signers: List[Tuple[PersonIdentity, KeyPair]],
    timestamp: Optional[str] = None,
) -> CoordinationAttestation:
    """Sign the claim with each (person, keypair)."""
    if not HAS_CRYPTO:
        raise RuntimeError(
            "create_coordination_attestation requires "
            "`cryptography`")
    if len(signers) < 2:
        raise ValueError("at least 2 signers required")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    payload = canonical_bytes({
        "kind": "coordination_attestation",
        "claim": claim.to_dict(),
        "timestamp": timestamp,
    })
    co_signers: List[CoSigner] = []
    seen = set()
    for person, kp in signers:
        if kp.public_key_hex() != person.person_public_key:
            raise ValueError(
                f"keypair for {person.person.name} does not match "
                f"person_public_key")
        if person.person.token in seen:
            raise ValueError(
                f"duplicate signer: {person.person.token[:16]}...")
        seen.add(person.person.token)
        co_signers.append(CoSigner(
            person_token=person.person.token,
            person_public_key=person.person_public_key,
            signature=kp.sign(payload).hex(),
        ))
    return CoordinationAttestation(
        claim=claim,
        co_signers=tuple(co_signers),
        timestamp=timestamp,
    )


# =====================================================================
# Verify an attestation (signatures only)
# =====================================================================

@dataclass(frozen=True)
class SignerVerdict:
    person_token: str
    person_public_key: str
    signature_valid: bool
    reason: str


@dataclass
class AttestationVerdict:
    valid: bool
    reason: str
    signer_verdicts: List[SignerVerdict]

    def format(self) -> str:
        lines = ["Coordination Attestation Verification",
                 "=" * 50]
        for v in self.signer_verdicts:
            marker = "✓" if v.signature_valid else "✗"
            lines.append(
                f"  {marker} {v.person_token[:16]}... ({v.reason})")
        lines.append("")
        lines.append(f"  valid: {self.valid}")
        if not self.valid:
            lines.append(f"  reason: {self.reason}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "signer_verdicts": [
                {"person_token": v.person_token,
                 "person_public_key": v.person_public_key,
                 "signature_valid": v.signature_valid,
                 "reason": v.reason}
                for v in self.signer_verdicts
            ],
        }


def verify_coordination_attestation(
    attestation: CoordinationAttestation,
) -> AttestationVerdict:
    """Verify each co-signer's signature over the claim payload.

    Checks cryptography only — takes each co-signer's public key
    at face value. Admission checking (does this key belong to the
    claimed person in this World?) is the PersonWorld's job.
    Never raises.
    """
    if not HAS_CRYPTO:
        return AttestationVerdict(
            valid=False, reason="cryptography not installed",
            signer_verdicts=[])
    try:
        if not isinstance(attestation, CoordinationAttestation):
            return AttestationVerdict(
                valid=False, reason="not a CoordinationAttestation",
                signer_verdicts=[])
        payload = canonical_bytes({
            "kind": "coordination_attestation",
            "claim": attestation.claim.to_dict(),
            "timestamp": attestation.timestamp,
        })
    except Exception as e:
        return AttestationVerdict(
            valid=False, reason=f"canonicalization failed: {e}",
            signer_verdicts=[])
    verdicts: List[SignerVerdict] = []
    all_valid = True
    for cs in attestation.co_signers:
        try:
            ok = verify_signature(
                cs.person_public_key, payload, cs.signature)
        except Exception:
            ok = False
        verdicts.append(SignerVerdict(
            person_token=cs.person_token,
            person_public_key=cs.person_public_key,
            signature_valid=ok,
            reason="signature valid" if ok
                    else "signature INVALID",
        ))
        if not ok:
            all_valid = False
    return AttestationVerdict(
        valid=all_valid,
        reason="all signatures valid" if all_valid
                else "one or more signatures invalid",
        signer_verdicts=verdicts,
    )


# =====================================================================
# PersonWorld — the meeting place
# =====================================================================

@dataclass(frozen=True)
class PersonWorldLaw:
    entity_id: str = "collaboratory:main"
    name: str = "Collaboratory"
    admits_any_person: bool = True
    min_co_signers: int = 2
    max_co_signers: int = 64

    def describe(self) -> str:
        return "\n".join([
            f"# PersonWorld Law v0.1 — {self.name}",
            "",
            "## Petition",
            "- Requires extra.public_key (64 hex chars)",
            f"- Admits any person: {self.admits_any_person}",
            "",
            "## Act: coordination.attest",
            "- Payload: {claim, co_signers}",
            f"- Min co-signers: {self.min_co_signers}",
            f"- Max co-signers: {self.max_co_signers}",
            "- All co-signers must be admitted",
            "- All signatures must verify against admitted keys",
            "- actor_token must be among the co-signers",
            "",
            "## Leave",
            "- Leaving cannot be refused by an admitted person",
        ])


class PersonWorld:
    """A WCP entity where persons meet to coordinate."""

    def __init__(self, law: Optional[PersonWorldLaw] = None):
        self._law = law or PersonWorldLaw()
        self._manifest = Manifest(
            entity_id=self._law.entity_id,
            name=self._law.name,
            protocol_version="WCP/0.1",
            law_url=f"personworld://{self._law.entity_id}/law",
            act_endpoint=f"personworld://{self._law.entity_id}/act",
            log_endpoint=f"personworld://{self._law.entity_id}/log",
            sub_registry_endpoint=None,
        )
        self._log: List[LogEntry] = []
        self._admitted_persons: Dict[str, str] = {}
        self._left_at: Dict[str, str] = {}
        self._attestations: List[CoordinationAttestation] = []

    def manifest(self) -> Manifest:
        return self._manifest

    def law(self) -> PersonWorldLaw:
        return self._law

    def describe(self) -> str:
        return self._law.describe()

    def petition(self, petition: Petition):
        ts = datetime.now(timezone.utc).isoformat()
        extra = petition.extra or {}
        pk = extra.get("public_key")
        if not isinstance(pk, str) or len(pk) != 64:
            return self._refuse(
                ts, petition.petitioner_token,
                "petition.extra.public_key required (64 hex)",
                "petition")
        if not self._law.admits_any_person:
            return self._refuse(
                ts, petition.petitioner_token,
                "This PersonWorld does not admit strangers",
                "petition")
        if petition.petitioner_token in self._admitted_persons:
            return self._refuse(
                ts, petition.petitioner_token,
                "Already admitted", "petition")
        self._admitted_persons[petition.petitioner_token] = pk
        self._log.append(LogEntry(
            timestamp=ts, kind="admission",
            actor_token=petition.petitioner_token,
            data={"name": petition.petitioner_name,
                  "public_key": pk},
        ))
        return WCPAdmission(
            entity_id=self._manifest.entity_id, timestamp=ts)

    def act(self, act: Act):
        ts = datetime.now(timezone.utc).isoformat()
        if act.actor_token not in self._admitted_persons:
            return self._refuse(ts, act.actor_token,
                                 "Actor is not admitted", "act")
        if act.type != "coordination.attest":
            return self._refuse(ts, act.actor_token,
                                 f"Unknown act type: {act.type}", "act")
        payload = act.payload or {}
        try:
            claim_obj = CoordinationClaim.from_dict(payload["claim"])
            cs_objs = tuple(
                CoSigner.from_dict(cs)
                for cs in payload["co_signers"])
        except (KeyError, ValueError, TypeError) as e:
            return self._refuse(ts, act.actor_token,
                                 f"Malformed payload: {e}", "act")
        if len(cs_objs) < self._law.min_co_signers:
            return self._refuse(
                ts, act.actor_token,
                f"Too few co-signers ({len(cs_objs)})", "act")
        if len(cs_objs) > self._law.max_co_signers:
            return self._refuse(
                ts, act.actor_token, "Too many co-signers", "act")
        tokens = [cs.person_token for cs in cs_objs]
        if len(tokens) != len(set(tokens)):
            return self._refuse(ts, act.actor_token,
                                 "Duplicate co-signer", "act")
        if act.actor_token not in tokens:
            return self._refuse(
                ts, act.actor_token,
                "Actor must be among the co-signers", "act")
        # Every co-signer must be admitted, with a matching key
        for cs in cs_objs:
            if cs.person_token not in self._admitted_persons:
                return self._refuse(
                    ts, act.actor_token,
                    f"Co-signer {cs.person_token[:16]}... "
                    f"not admitted", "act")
            if cs.person_public_key != \
                    self._admitted_persons[cs.person_token]:
                return self._refuse(
                    ts, act.actor_token,
                    f"Co-signer {cs.person_token[:16]}... "
                    f"key mismatch with admitted key", "act")
        attestation = CoordinationAttestation(
            claim=claim_obj, co_signers=cs_objs, timestamp=ts)
        verdict = verify_coordination_attestation(attestation)
        if not verdict.valid:
            return self._refuse(
                ts, act.actor_token,
                f"Attestation invalid: {verdict.reason}", "act")
        self._attestations.append(attestation)
        self._log.append(LogEntry(
            timestamp=ts, kind="coordination_attestation",
            actor_token=act.actor_token,
            data=attestation.to_dict(),
        ))
        return Ack(entity_id=self._manifest.entity_id, timestamp=ts)

    def leave(self, petition):
        from multiverse_c22 import LeavePetition, Leave
        token = petition.leaver_token
        ts = datetime.now(timezone.utc).isoformat()
        if token in self._admitted_persons:
            del self._admitted_persons[token]
            self._left_at[token] = ts
            self._log.append(LogEntry(
                timestamp=ts, kind="leave",
                actor_token=token, data={}))
            return Leave(entity_id=self._manifest.entity_id,
                         timestamp=ts)
        if token in self._left_at:
            return Leave(entity_id=self._manifest.entity_id,
                         timestamp=self._left_at[token])
        return Refusal(reason="not admitted")

    def log_since(self, since=None):
        if since is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > since]

    def attestations(self):
        return list(self._attestations)

    def is_admitted(self, token):
        return token in self._admitted_persons

    def _refuse(self, ts, actor, reason, kind):
        self._log.append(LogEntry(
            timestamp=ts, kind=f"{kind}_refused",
            actor_token=actor, data={"reason": reason}))
        return Refusal(reason=reason)


# =====================================================================
# Demo — Aria and Bob co-attest a shared collaboration
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Aria and Bob both participated in a poetry collaboration.
    They meet in a PersonWorld and co-attest it. A third party
    verifies.

    Anchor: Dickinson, 'If I can stop one Heart from breaking,',
    public domain.
    """
    from pathlib import Path
    from multiverse_c36 import create_person

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # Aria: distributed AI, three embodiments (from C36's pattern)
    aria, aria_kp = create_person("Aria")
    # Bob: two embodiments
    bob, bob_kp = create_person("Bob")

    # They meet in a PersonWorld
    world = PersonWorld(PersonWorldLaw(
        entity_id="collaboratory:main",
        name="Collaboratory"))

    # Both petition with their public keys
    for person in (aria, bob):
        resp = world.petition(Petition(
            petitioner_token=person.person.token,
            petitioner_name=person.person.name,
            passport_admissions=(),
            message="May I join the collaboratory?",
            extra={"public_key": person.person_public_key},
        ))
        assert isinstance(resp, WCPAdmission), resp

    # They co-sign a claim about a shared collaboration
    claim = CoordinationClaim(
        kind="shared-collaboration",
        content={
            "world": "world:poetry",
            "poem_title": "On Dickinson",
            "seed_line": "If I can stop one Heart from breaking,",
            "narrator": "Aria and Bob, together",
        },
    )
    attestation = create_coordination_attestation(
        claim, [(aria, aria_kp), (bob, bob_kp)])

    # Aria submits it (she's among the co-signers — required)
    act_resp = world.act(Act(
        actor_token=aria.person.token,
        type="coordination.attest",
        payload={
            "claim": claim.to_dict(),
            "co_signers": [
                cs.to_dict() for cs in attestation.co_signers],
        },
    ))
    assert isinstance(act_resp, Ack), act_resp

    # Third-party verification: Charlie, with the persons' public keys
    verdict = verify_coordination_attestation(attestation)

    # Negative test: Carol tries to forge Aria's signature
    from multiverse_c36 import create_person as cp
    carol, carol_kp = cp("Carol")
    forged = CoSigner(
        person_token=aria.person.token,
        person_public_key=aria.person_public_key,
        signature=carol_kp.sign(
            attestation.canonical_payload()).hex())
    forged_attestation = CoordinationAttestation(
        claim=claim,
        co_signers=(forged, attestation.co_signers[1]),
        timestamp=attestation.timestamp)
    forged_verdict = verify_coordination_attestation(
        forged_attestation)

    print("=" * 70)
    print("PersonWorld — Aria and Bob co-attest")
    print("=" * 70)
    print()
    print(f"  world:       {world.manifest().entity_id}")
    print(f"  admitted:    {sorted(world._admitted_persons.keys())[:1] and len(world._admitted_persons)}")
    print(f"  attestations: {len(world.attestations())}")
    print()
    print(f"  Claim kind:  {claim.kind}")
    print(f"  Claim:       {claim.content}")
    print()
    print("  Verification (third party, has both public keys):")
    for line in verdict.format().split("\n"):
        print(f"  {line}")
    print()
    print("  Forged attestation (Carol pretending to be Aria):")
    for line in forged_verdict.format().split("\n"):
        print(f"  {line}")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'If I can stop one Heart from breaking,'")
    print("    'I shall not live in vain;'")

    audit = {
        "world_entity_id": world.manifest().entity_id,
        "attestations_recorded": len(world.attestations()),
        "claim_kind": claim.kind,
        "co_signers": [cs.person_token for cs in attestation.co_signers],
        "verification_valid": verdict.valid,
        "forged_attestation_valid": forged_verdict.valid,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "person_world_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/person_world_demo.json")
    return audit
