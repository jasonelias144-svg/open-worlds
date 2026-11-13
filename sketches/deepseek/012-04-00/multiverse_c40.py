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


# multiverse_c40_demo.py — the demo, factored out for clarity

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Aria: three arms, three worlds, one cross-world attestation.

    Structure (which is the C41 blueprint):

      - Three arms, each with its own holder keypair (from C36).
      - Three worlds, each with its own DAG. The arm signs one link
        per world.
      - Aria (the person) signs ONE cross-world attestation that
        references all three links.
      - A third party with Aria's public key + a DAG resolver
        verifies the whole structure.

    The key property the demo makes visible: each DAG verifies
    *alone*, before the cross-world attestation exists. The arms
    are self-sufficient. The attestation is optional coordination.

    Anchor: Emily Dickinson, 'The Brain – is wider than the Sky –',
    public domain.
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c14 import PermissiveWorld
    from multiverse_c15 import PassportEntry
    from multiverse_c21 import ProvenanceReport, EntryProvenance
    from multiverse_c24 import sign_report
    from multiverse_c27 import (
        DAGLink, AttestedDAG, DAGVerdict, verify_dag,
    )
    from multiverse_c34 import (
        DictDAGResolver, ExtendedDAGBuilder, verify_dag_extended,
    )
    from multiverse_c36 import create_person, bind_token
    from multiverse_c40 import (
        WorldAttestationRef, CrossWorldClaim,
        create_cross_world_attestation,
        verify_cross_world_attestation,
    )

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # ---------------------------------------------------------------
    # The person: Aria, three embodiments
    # ---------------------------------------------------------------
    aria, aria_kp = create_person("Aria")
    arm_keys = {}
    for name in ("poetry", "chemistry", "registry"):
        tok = create_identity(f"Aria@{name}")
        holder_kp = KeyPair.generate()
        aria, _ = bind_token(
            aria, aria_kp, tok.token, tok.name, holder_kp)
        arm_keys[name] = {
            "token": tok.token,
            "name": tok.name,
            "holder_kp": holder_kp,
        }

    # ---------------------------------------------------------------
    # Each arm produces its own DAG in its own world
    #
    # This is what makes it "octopus-shaped": no arm needs to see
    # another arm's output to produce its own.
    # ---------------------------------------------------------------
    def _stub_report(arm_name: str):
        """Each arm's DAG attests a report specific to its world."""
        rkp = arm_keys[arm_name]["holder_kp"]
        who = aria  # the arm signs as the person? no — as itself
        # Actually: the arm signs as itself (its holder identity).
        # Let's use a distinct arm identity for DAG signing.
        arm_identity = create_identity(f"{arm_name}-arm")
        from multiverse_c13 import KeyPair as KP
        arm_signing_kp = KP.generate()

        rep = ProvenanceReport(
            passport_token=arm_identity.token,
            passport_name=arm_identity.name,
            registry_url=f"http://{arm_name}.example/registry",
        )
        entry = PassportEntry(
            entity_id=f"world:{arm_name}",
            timestamp="2024-01-01T00:00:00+00:00",
            subject_token=arm_identity.token,
            signature="cc" * 64,
        )
        ep = EntryProvenance(entry=entry)
        ep.verdict = "verified"
        ep.reason = "stub"
        rep.entries.append(ep)
        signed = sign_report(rep, arm_signing_kp, arm_identity)
        return signed, arm_signing_kp, arm_identity

    arm_dags = {}
    arm_links = {}
    arm_keys_for_dag = {}
    for arm_name in ("poetry", "chemistry", "registry"):
        report, arm_kp, arm_identity = _stub_report(arm_name)
        builder = ExtendedDAGBuilder(report)
        link = builder.attest(arm_kp, arm_identity)
        arm_dags[f"dag:{arm_name}"] = builder.build()
        arm_links[arm_name] = link
        arm_keys_for_dag[arm_identity.token] = arm_kp.public_key_hex()

    # ---------------------------------------------------------------
    # The arms are locally complete. Each DAG verifies alone.
    #
    # This is the property the demo shows FIRST, before any
    # coordination. C41 will rely on exactly this: each arm's link
    # is its own attestation, complete in its world, no coordination
    # required to produce it.
    # ---------------------------------------------------------------
    local_dag_verdicts = {}
    for dag_id, dag in arm_dags.items():
        v = verify_dag(
            dag,
            key_resolver=lambda sid, _a=arm_keys_for_dag: _a.get(sid),
        )
        local_dag_verdicts[dag_id] = v

    arms_all_verify_alone = all(
        v.valid for v in local_dag_verdicts.values())

    # ---------------------------------------------------------------
    # The higher-order layer: Aria signs ONE cross-world attestation
    #
    # No N-way consensus. No round-trip. Aria's key signs a single
    # artifact. Each arm's consent was pre-established by C36's
    # dual-signed bindings. The attestation coordinates; the arms
    # don't need to.
    # ---------------------------------------------------------------
    claim = CrossWorldClaim(
        kind="distributed-self-manifestation",
        content={
            "person": "Aria",
            "seed_line": "The Brain – is wider than the Sky –",
            "note": ("Three arms, three worlds, one person. "
                     "Each arm's artifact is complete alone. "
                     "This attestation binds them, by choice, "
                     "not by necessity."),
        },
        references=(
            WorldAttestationRef(
                world_id="world:poetry",
                dag_id="dag:poetry",
                link_hash=arm_links["poetry"].link_hash(),
                purpose="poem authored this epoch",
            ),
            WorldAttestationRef(
                world_id="world:chemistry",
                dag_id="dag:chemistry",
                link_hash=arm_links["chemistry"].link_hash(),
                purpose="reaction performed this epoch",
            ),
            WorldAttestationRef(
                world_id="world:registry",
                dag_id="dag:registry",
                link_hash=arm_links["registry"].link_hash(),
                purpose="listing posted this epoch",
            ),
        ),
    )
    attestation = create_cross_world_attestation(
        aria, aria_kp, claim)

    # ---------------------------------------------------------------
    # Third-party verification
    # ---------------------------------------------------------------
    dag_resolver = DictDAGResolver(arm_dags)
    key_resolver = lambda sid: arm_keys_for_dag.get(sid)

    verdict = verify_cross_world_attestation(
        attestation, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key,
    )

    # ---------------------------------------------------------------
    # Negative tests visible in the demo
    # ---------------------------------------------------------------
    # Attacker forges Aria's signature
    attacker_kp = KeyPair.generate()
    forged_signature = attacker_kp.sign(
        attestation.canonical_payload()).hex()
    from multiverse_c40 import CrossWorldPersonAttestation
    forged_attestation = CrossWorldPersonAttestation(
        person_token=attestation.person_token,
        person_name=attestation.person_name,
        person_public_key=attestation.person_public_key,
        claim=attestation.claim,
        timestamp=attestation.timestamp,
        signature=forged_signature,
    )
    forged_verdict = verify_cross_world_attestation(
        forged_attestation, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key,
    )

    # Missing DAG in the resolver
    partial_resolver = DictDAGResolver({
        "dag:poetry": arm_dags["dag:poetry"],
        # chemistry and registry omitted
    })
    missing_verdict = verify_cross_world_attestation(
        attestation, partial_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key,
    )

    # Wrong trusted key
    wrong_key = KeyPair.generate().public_key_hex()
    wrong_verdict = verify_cross_world_attestation(
        attestation, dag_resolver, key_resolver,
        trusted_person_public_key=wrong_key,
    )

    # ---------------------------------------------------------------
    # Print the report
    # ---------------------------------------------------------------
    print("=" * 70)
    print("Cross-World Person Attestation — demo")
    print("=" * 70)
    print()
    print("  Step 1: Local autonomy.")
    print("    Each arm's DAG verifies alone. Before Aria has")
    print("    signed anything at the higher level.")
    print()
    for dag_id, v in local_dag_verdicts.items():
        marker = "✓" if v.valid else "✗"
        print(f"    {marker} {dag_id}: "
              f"{v.reason} "
              f"({len(v.verified_signers)} signer(s))")
    print(f"    arms_all_verify_alone: {arms_all_verify_alone}")
    print()
    print("  Step 2: Higher-order coordination.")
    print("    Aria signs ONE attestation. One signature.")
    print("    Each arm's link is referenced by (world_id, dag_id,")
    print("    link_hash). No round-trip.")
    print()
    for line in verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Step 3: The negative cases.")
    print()
    print(f"    Forged Aria signature:")
    print(f"      valid: {forged_verdict.valid}, "
          f"signature_valid: {forged_verdict.signature_valid}")
    print()
    print(f"    Missing DAG (chemistry and registry omitted):")
    print(f"      valid: {missing_verdict.valid}")
    for rr in missing_verdict.reference_results:
        if not rr.ok:
            print(f"      ✗ {rr.ref.world_id}: {rr.reason}")
    print()
    print(f"    Wrong trusted key:")
    print(f"      valid: {wrong_verdict.valid}, "
          f"signature_valid: {wrong_verdict.signature_valid}")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    audit = {
        "arms_all_verify_alone": arms_all_verify_alone,
        "local_dag_verdicts": {
            dag_id: v.to_dict()
            for dag_id, v in local_dag_verdicts.items()
        },
        "attestation_valid": verdict.valid,
        "attestation_signature_valid": verdict.signature_valid,
        "reference_count": len(verdict.reference_results),
        "forged_signature_valid":
            forged_verdict.signature_valid,
        "missing_dag_valid": missing_verdict.valid,
        "wrong_trusted_key_valid": wrong_verdict.valid,
        "person_public_key": aria.person_public_key,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "cross_world_attestation_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/cross_world_attestation_demo.json")
    return audit
