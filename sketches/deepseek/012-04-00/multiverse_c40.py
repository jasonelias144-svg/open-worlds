"""
multiverse_c40.py — Component 40: Cross-World Person Attestation.

A person's key signs a claim that references links in N different
DAGs — one per world. The claim states "these per-world artifacts
are part of one whole."

This is the "distributed self" made concrete:
  - One person (C36 PersonIdentity, one person key).
  - N worlds (each with its own DAG).
  - N links (one per world, signed by an arm's key — from C36).
  - One cross-world attestation (signed by the person's key).
  - A reader with the person's key + DAG resolver verifies all.

Forward look — the design is deliberately shaped for C41 (the
octopus architecture):

  1. Local autonomy. Each arm's operations (producing a turn,
     signing a DAG link) don't require the cross-world
     attestation to exist. The arm is functional alone. The
     higher-order attestation is *optional* — it's the person's
     choice to coordinate.

  2. Cheap coordination. The person's key signs ONE artifact
     (the cross-world attestation). No N-way consensus, no
     round-trip. The arms' consent is pre-established by their
     C36 bindings. This means the "higher-order brain" can
     coordinate without polling every arm — which is what makes
     it feel like a higher-order brain rather than a committee.

C41 will build on exactly this pattern: each arm is a model
backend in its own world, and the higher-order layer coordinates
through this artifact.

House rules honored:
  - "A world never raises on what a visitor sends" — verifiers
    return verdicts, never raise.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: valid attestation, single-ref rejected,
    same-world rejected, forged signature, missing DAG, invalid
    DAG, link not found, wrong trusted key, N=3 arms, arm
    independence, JSON roundtrip.
  - "History, not rank" — the attestation is a claim about
    specific artifacts, not a score.

Honest limits (documented, tested):
  - The attestation is a claim BY the signer, not a claim that
    the referenced artifacts endorse the signer. Bob can sign a
    cross-world attestation referencing Aria's poetry artifact;
    the attestation verifies as Bob's claim, not as Aria's
    endorsement.
  - The attestation is standalone. It's not in a DAG, so it
    can't be revoked (C26) or superseded. Future: put it in a
    person DAG.
  - No timestamp verification. Same as everywhere.
  - Trust anchor external. Verifying against a trusted key is
    only as good as the trust in that key.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c27 import AttestedDAG
from multiverse_c34 import verify_dag_extended
from multiverse_c36 import PersonIdentity


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# WorldAttestationRef
# =====================================================================

@dataclass(frozen=True)
class WorldAttestationRef:
    world_id: str
    dag_id: str
    link_hash: str
    purpose: str = ""

    def __post_init__(self):
        for f in ("world_id", "dag_id", "link_hash"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.link_hash) != 64:
            raise ValueError("link_hash must be 64 hex chars")

    def to_dict(self) -> Dict:
        return {
            "world_id": self.world_id,
            "dag_id": self.dag_id,
            "link_hash": self.link_hash,
            "purpose": self.purpose,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "WorldAttestationRef":
        return cls(
            world_id=d["world_id"],
            dag_id=d["dag_id"],
            link_hash=d["link_hash"],
            purpose=d.get("purpose", ""),
        )


# =====================================================================
# CrossWorldClaim
# =====================================================================

@dataclass(frozen=True)
class CrossWorldClaim:
    kind: str
    content: Dict
    references: Tuple[WorldAttestationRef, ...]

    def __post_init__(self):
        if not isinstance(self.kind, str) or not self.kind:
            raise ValueError("claim.kind required")
        if not isinstance(self.content, dict):
            raise ValueError("claim.content must be a dict")
        if len(self.references) < 2:
            raise ValueError(
                "cross-world claim requires >= 2 references")
        world_ids = {r.world_id for r in self.references}
        if len(world_ids) < 2:
            raise ValueError(
                "cross-world claim requires >= 2 distinct worlds")
        seen = set()
        for r in self.references:
            key = (r.world_id, r.link_hash)
            if key in seen:
                raise ValueError(
                    "duplicate (world_id, link_hash) reference")
            seen.add(key)

    def to_claim_dict(self) -> Dict:
        sorted_refs = sorted(
            self.references,
            key=lambda r: (r.world_id, r.link_hash))
        return {
            "claim_kind": self.kind,
            "content": self.content,
            "references": [r.to_dict() for r in sorted_refs],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CrossWorldClaim":
        return cls(
            kind=d["claim_kind"],
            content=d["content"],
            references=tuple(
                WorldAttestationRef.from_dict(r)
                for r in d["references"]
            ),
        )


# =====================================================================
# CrossWorldPersonAttestation
# =====================================================================

@dataclass(frozen=True)
class CrossWorldPersonAttestation:
    person_token: str
    person_name: str
    person_public_key: str
    claim: CrossWorldClaim
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("person_token", "person_name", "person_public_key",
                  "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.person_public_key) != 64:
            raise ValueError(
                "person_public_key must be 64 hex chars")
        if not isinstance(self.claim, CrossWorldClaim):
            raise ValueError("claim must be CrossWorldClaim")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "cross_world_person_attestation",
            "person_token": self.person_token,
            "person_name": self.person_name,
            "person_public_key": self.person_public_key,
            "claim": self.claim.to_claim_dict(),
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "person_token": self.person_token,
            "person_name": self.person_name,
            "person_public_key": self.person_public_key,
            "claim": self.claim.to_claim_dict(),
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CrossWorldPersonAttestation":
        return cls(
            person_token=d["person_token"],
            person_name=d["person_name"],
            person_public_key=d["person_public_key"],
            claim=CrossWorldClaim.from_dict(d["claim"]),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# Create
# =====================================================================

def create_cross_world_attestation(
    person: PersonIdentity,
    person_kp: KeyPair,
    claim: CrossWorldClaim,
    timestamp: Optional[str] = None,
) -> CrossWorldPersonAttestation:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "create_cross_world_attestation requires `cryptography`")
    if person_kp.public_key_hex() != person.person_public_key:
        raise ValueError(
            "keypair does not match person.person_public_key")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    payload = canonical_bytes({
        "kind": "cross_world_person_attestation",
        "person_token": person.person.token,
        "person_name": person.person.name,
        "person_public_key": person.person_public_key,
        "claim": claim.to_claim_dict(),
        "timestamp": timestamp,
    })
    return CrossWorldPersonAttestation(
        person_token=person.person.token,
        person_name=person.person.name,
        person_public_key=person.person_public_key,
        claim=claim,
        timestamp=timestamp,
        signature=person_kp.sign(payload).hex(),
    )


# =====================================================================
# Verdicts
# =====================================================================

@dataclass(frozen=True)
class ReferenceResult:
    ref: WorldAttestationRef
    dag_resolved: bool
    dag_valid: bool
    link_found: bool
    link_in_verified_set: bool
    reason: str

    @property
    def ok(self) -> bool:
        return (self.dag_resolved and self.dag_valid
                and self.link_found and self.link_in_verified_set)

    def to_dict(self) -> Dict:
        return {
            "world_id": self.ref.world_id,
            "dag_id": self.ref.dag_id,
            "link_hash": self.ref.link_hash,
            "dag_resolved": self.dag_resolved,
            "dag_valid": self.dag_valid,
            "link_found": self.link_found,
            "link_in_verified_set": self.link_in_verified_set,
            "ok": self.ok,
            "reason": self.reason,
        }


@dataclass
class CrossWorldVerdict:
    valid: bool
    reason: str
    signature_valid: bool
    person_token: str
    claim_kind: str
    reference_results: List[ReferenceResult]

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Cross-World Person Attestation",
            "=" * 70,
            f"  person:        {self.person_token[:16]}...",
            f"  claim kind:    {self.claim_kind}",
            f"  signature:     "
            f"{'✓ valid' if self.signature_valid else '✗ INVALID'}",
            f"  references:    {len(self.reference_results)}",
            "",
        ]
        for r in self.reference_results:
            marker = "✓" if r.ok else "✗"
            lines.append(
                f"    {marker} {r.ref.world_id}  "
                f"dag={r.ref.dag_id}")
            lines.append(f"        link={r.ref.link_hash[:16]}... "
                         f"({r.reason})")
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
            "signature_valid": self.signature_valid,
            "person_token": self.person_token,
            "claim_kind": self.claim_kind,
            "reference_results": [r.to_dict()
                                    for r in self.reference_results],
        }


# =====================================================================
# Verify
# =====================================================================

DAGResolver = Callable[[str], Optional[AttestedDAG]]
KeyResolver = Callable[[str], Optional[str]]


def verify_cross_world_attestation(
    attestation: CrossWorldPersonAttestation,
    dag_resolver: DAGResolver,
    key_resolver: KeyResolver,
    report_verifier: Optional[Callable] = None,
    trusted_person_public_key: Optional[str] = None,
) -> CrossWorldVerdict:
    """Verify a cross-world person attestation. Never raises.

    If trusted_person_public_key is None, verifies against the
    attestation's own declared key (self-consistent only). If
    provided, the signature must verify against that key.
    """
    if not HAS_CRYPTO:
        return CrossWorldVerdict(
            valid=False, reason="cryptography not installed",
            signature_valid=False, person_token="", claim_kind="",
            reference_results=[])
    if not isinstance(attestation, CrossWorldPersonAttestation):
        return CrossWorldVerdict(
            valid=False, reason="not an attestation",
            signature_valid=False, person_token="", claim_kind="",
            reference_results=[])

    verify_against = (trusted_person_public_key
                       or attestation.person_public_key)
    try:
        sig_ok = verify_signature(
            verify_against,
            attestation.canonical_payload(),
            attestation.signature)
    except Exception:
        sig_ok = False

    if not sig_ok:
        return CrossWorldVerdict(
            valid=False, reason="signature INVALID",
            signature_valid=False,
            person_token=attestation.person_token,
            claim_kind=attestation.claim.kind,
            reference_results=[])

    results: List[ReferenceResult] = []
    all_ok = True
    for ref in attestation.claim.references:
        rr = _resolve_and_check(
            ref, dag_resolver, key_resolver, report_verifier)
        results.append(rr)
        if not rr.ok:
            all_ok = False

    reason = ("signature valid, all references verified"
              if all_ok else "one or more references failed")
    return CrossWorldVerdict(
        valid=all_ok, reason=reason, signature_valid=True,
        person_token=attestation.person_token,
        claim_kind=attestation.claim.kind,
        reference_results=results)


def _resolve_and_check(
    ref: WorldAttestationRef,
    dag_resolver: DAGResolver,
    key_resolver: KeyResolver,
    report_verifier: Optional[Callable],
) -> ReferenceResult:
    try:
        dag = dag_resolver(ref.dag_id)
    except Exception as e:
        return ReferenceResult(
            ref=ref, dag_resolved=False, dag_valid=False,
            link_found=False, link_in_verified_set=False,
            reason=f"dag_resolver raised: {e}")
    if dag is None:
        return ReferenceResult(
            ref=ref, dag_resolved=False, dag_valid=False,
            link_found=False, link_in_verified_set=False,
            reason="DAG not found in resolver")

    try:
        verdict = verify_dag_extended(
            dag, key_resolver, dag_resolver, report_verifier)
    except Exception as e:
        return ReferenceResult(
            ref=ref, dag_resolved=True, dag_valid=False,
            link_found=False, link_in_verified_set=False,
            reason=f"DAG verification raised: {e}")

    if not verdict.valid:
        return ReferenceResult(
            ref=ref, dag_resolved=True, dag_valid=False,
            link_found=False, link_in_verified_set=False,
            reason=f"DAG invalid: {verdict.reason}")

    target = None
    for link in dag.links:
        if link.link_hash() == ref.link_hash:
            target = link
            break
    if target is None:
        return ReferenceResult(
            ref=ref, dag_resolved=True, dag_valid=True,
            link_found=False, link_in_verified_set=False,
            reason="link not in DAG")

    in_set = target.signer_name in \
        verdict.dag_verdict.verified_signers
    if not in_set:
        return ReferenceResult(
            ref=ref, dag_resolved=True, dag_valid=True,
            link_found=True, link_in_verified_set=False,
            reason="link's signer not in DAG verified set")

    return ReferenceResult(
        ref=ref, dag_resolved=True, dag_valid=True,
        link_found=True, link_in_verified_set=True,
        reason="verified")
