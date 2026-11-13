"""
multiverse_c48.py — Component 48: Cross-Architecture Federation.

C46 federated councils with councils. C48 federates FIVE kinds of
architecture in one federation:

  Architecture          Produces              Verification kind
  --------------------  --------------------  -----------------
  C44 Council           Decision              direct
  C45 Deliberation      DeliberativeDecision  direct
  C46 Federated Council FederatedDelibDecision direct
  C40 Cross-World       CrossWorldPersonAtt.  direct
  C41 Octopus           ArmReport (epoch)     witnessed
  C42 Relay             SignalWindow          witnessed
  C43 Swarm             ConvergenceLog        witnessed
  C47 Autonomic         StateTrace            witnessed

Design:
  - FederationAttestation wraps ANY artifact in a uniform shape:
    source_id, source_kind, content, content_hash, witness fields.
  - Direct kinds: the content verifies itself. The attestation
    carries no witness; the verifier re-runs the architecture's
    own verifier.
  - Witnessed kinds: an observer signs (source_id, source_kind,
    content_hash, timestamp). The verifier trusts the observer
    (external) and checks the hash matches.
  - CrossKindPosition references attestations by (source_id,
    source_kind, artifact_hash). The verifier dispatches.
  - CrossKindCouncil consumes attestations and produces a
    CrossKindFederatedDecision.

What's new versus C46:
  C46 references were (council_id, decision_hash) — homogeneous.
  C48 references are (source_id, source_kind, artifact_hash) —
  heterogeneous. The federation layer dispatches on source_kind.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, one per kind, plus structural
    tests (five kinds in one registry) and never-raises.
  - "A world never raises on what a visitor sends" — verifiers
    return verdicts; registry dispatch returns verdicts.
  - "History, not rank" — attestations are records.

Honest limits (documented, tested):
  - Witness keys are external trust anchors. Same as everywhere.
  - No anonymous witnessing: a witness names itself.
  - No cycle protection: a federation can reference another
    federation. Verification would recurse. Not defended.
  - Direct attestation content is embedded in the federation
    decision; witnessed content is embedded too (in the
    FederationAttestation), so the verifier has everything.
  - The direct-kinds set is closed; adding a sixth direct kind
    requires the caller to register a verifier. Witnessed kinds
    don't need registration (all use the same verifier).
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple, Union

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c40 import (
    CrossWorldPersonAttestation, verify_cross_world_attestation,
)
from multiverse_c44 import (
    Proposal, Vote, DECISIONS, QuorumRule, Decision,
    TriumvirateMember, verify_decision,
)
from multiverse_c45 import (
    SignedPosition, verify_position,
    DeliberativeMember, DeliberativeDecision,
    DeliberativeCouncil,
    verify_deliberative_decision, _latest_stances,
)
from multiverse_c46 import (
    FederatedDeliberativeDecision,
    FederatedDeliberativeMember,
    FederatedDeliberativeCouncil,
    verify_federated_deliberation,
)
from multiverse_c1 import Identity


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# Kinds
# =====================================================================

DIRECT_KINDS = frozenset({
    "decision",
    "deliberative_decision",
    "federated_deliberation",
    "cross_world_attestation",
})

WITNESSED_KINDS = frozenset({
    "octopus_epoch",
    "signal_window",
    "swarm_log",
    "autonomic_trace",
})

ALL_KINDS = DIRECT_KINDS | WITNESSED_KINDS


# =====================================================================
# FederationAttestation
# =====================================================================

@dataclass(frozen=True)
class FederationAttestation:
    """A uniform wrapper around any architecture's signed output.

    For DIRECT_KINDS: witness_* fields are None; the content
    carries its own evidence.
    For WITNESSED_KINDS: witness_* fields are populated; the
    witness signs the content hash.
    """
    source_id: str
    source_kind: str
    content: Dict
    content_hash: str
    # Witness fields (populated only for WITNESSED_KINDS)
    witness_token: Optional[str] = None
    witness_name: Optional[str] = None
    witness_public_key: Optional[str] = None
    witness_signature: Optional[str] = None
    witness_timestamp: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id required")
        if self.source_kind not in ALL_KINDS:
            raise ValueError(
                f"source_kind must be one of {sorted(ALL_KINDS)}; "
                f"got {self.source_kind!r}")
        if not isinstance(self.content, dict):
            raise ValueError("content must be a dict")
        if len(self.content_hash) != 64:
            raise ValueError(
                "content_hash must be 64 hex chars")
        # Witness consistency: either all witness fields present or
        # all absent
        witness_fields = (
            self.witness_token, self.witness_name,
            self.witness_public_key, self.witness_signature,
            self.witness_timestamp,
        )
        present = [f is not None for f in witness_fields]
        if any(present) and not all(present):
            raise ValueError(
                "witness_* fields must be all present or all absent")
        if self.source_kind in WITNESSED_KINDS and not all(present):
            raise ValueError(
                f"{self.source_kind} requires witness_* fields")
        if self.source_kind in DIRECT_KINDS and any(present):
            raise ValueError(
                f"{self.source_kind} must not have witness_* fields")

    @property
    def is_witnessed(self) -> bool:
        return self.source_kind in WITNESSED_KINDS

    def witness_canonical_payload(self) -> bytes:
        """The bytes a witness signs. Not used for direct kinds."""
        return canonical_bytes({
            "kind": "federation_witness",
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "content_hash": self.content_hash,
            "witness_token": self.witness_token,
            "witness_name": self.witness_name,
            "witness_public_key": self.witness_public_key,
            "witness_timestamp": self.witness_timestamp,
        })

    def to_dict(self) -> Dict:
        d = {
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "content": self.content,
            "content_hash": self.content_hash,
        }
        if self.is_witnessed:
            d["witness"] = {
                "token": self.witness_token,
                "name": self.witness_name,
                "public_key": self.witness_public_key,
                "signature": self.witness_signature,
                "timestamp": self.witness_timestamp,
            }
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "FederationAttestation":
        w = d.get("witness", {})
        return cls(
            source_id=d["source_id"],
            source_kind=d["source_kind"],
            content=d["content"],
            content_hash=d["content_hash"],
            witness_token=w.get("token"),
            witness_name=w.get("name"),
            witness_public_key=w.get("public_key"),
            witness_signature=w.get("signature"),
            witness_timestamp=w.get("timestamp"),
        )


# =====================================================================
# Factories
# =====================================================================

def attest_decision(
    source_id: str, decision: Decision,
) -> FederationAttestation:
    """Wrap a C44 Decision as a direct federation attestation."""
    content = decision.to_dict()
    h = _hash_payload(canonical_bytes(content))
    return FederationAttestation(
        source_id=source_id,
        source_kind="decision",
        content=content,
        content_hash=h,
    )


def attest_deliberative_decision(
    source_id: str, decision: DeliberativeDecision,
) -> FederationAttestation:
    """Wrap a C45 DeliberativeDecision."""
    content = decision.to_dict()
    h = _hash_payload(canonical_bytes(content))
    return FederationAttestation(
        source_id=source_id,
        source_kind="deliberative_decision",
        content=content,
        content_hash=h,
    )


def attest_federated_deliberation(
    source_id: str, decision: FederatedDeliberativeDecision,
) -> FederationAttestation:
    """Wrap a C46 FederatedDeliberativeDecision."""
    content = decision.to_dict()
    h = _hash_payload(canonical_bytes(content))
    return FederationAttestation(
        source_id=source_id,
        source_kind="federated_deliberation",
        content=content,
        content_hash=h,
    )


def attest_cross_world(
    source_id: str, attestation: CrossWorldPersonAttestation,
) -> FederationAttestation:
    """Wrap a C40 CrossWorldPersonAttestation."""
    content = attestation.to_dict()
    h = _hash_payload(canonical_bytes(content))
    return FederationAttestation(
        source_id=source_id,
        source_kind="cross_world_attestation",
        content=content,
        content_hash=h,
    )


def witness_artifact(
    source_id: str,
    source_kind: str,
    content: Dict,
    witness_kp: KeyPair,
    witness_identity: Identity,
    timestamp: Optional[str] = None,
) -> FederationAttestation:
    """Produce a WITNESSED federation attestation.

    The witness signs (source_id, source_kind, content_hash,
    witness_token, witness_name, witness_public_key, timestamp).
    Any log-shaped artifact (swarm log, autonomic trace, signal
    window) can be wrapped this way.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "witness_artifact requires `cryptography`")
    if source_kind not in WITNESSED_KINDS:
        raise ValueError(
            f"witness_artifact only for witnessed kinds; "
            f"got {source_kind!r}")
    if timestamp is None:
        timestamp = _now()
    h = _hash_payload(canonical_bytes(content))
    public_key = witness_kp.public_key_hex()
    payload = canonical_bytes({
        "kind": "federation_witness",
        "source_id": source_id,
        "source_kind": source_kind,
        "content_hash": h,
        "witness_token": witness_identity.token,
        "witness_name": witness_identity.name,
        "witness_public_key": public_key,
        "witness_timestamp": timestamp,
    })
    return FederationAttestation(
        source_id=source_id,
        source_kind=source_kind,
        content=content,
        content_hash=h,
        witness_token=witness_identity.token,
        witness_name=witness_identity.name,
        witness_public_key=public_key,
        witness_signature=witness_kp.sign(payload).hex(),
        witness_timestamp=timestamp,
    )


# =====================================================================
# Verification: registry + dispatch
# =====================================================================

# A verifier is (attestation, context) → (ok, reason).
AttestationVerifier = Callable[
    [FederationAttestation, Dict], Tuple[bool, str]]


@dataclass
class AttestationVerdict:
    valid: bool
    reason: str
    source_id: str
    source_kind: str

    def format(self) -> str:
        marker = "✓" if self.valid else "✗"
        return (f"  {marker} {self.source_id} ({self.source_kind}): "
                f"{self.reason}")


def _verify_witnessed(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    """Verify a witnessed attestation: signature + content hash."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    # Content hash matches the content
    recomputed = _hash_payload(canonical_bytes(att.content))
    if recomputed != att.content_hash:
        return (False, "content_hash does not match content")
    # Signature verifies against witness key
    try:
        ok = verify_signature(
            att.witness_public_key,
            att.witness_canonical_payload(),
            att.witness_signature)
    except Exception as e:
        return (False, f"witness signature check raised: {e}")
    if not ok:
        return (False, "witness signature INVALID")
    return (True, "witness signature valid, content hash matches")


def _verify_direct_decision(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    """Verify a 'decision' attestation via C44's verify_decision."""
    try:
        decision = Decision.from_dict(att.content)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed Decision: {e}")
    # content_hash matches the parsed decision
    recomputed = _hash_payload(canonical_bytes(decision.to_dict()))
    if recomputed != att.content_hash:
        return (False, "content_hash mismatch")
    keys = context.get("member_keys", {}).get(att.source_id)
    if keys is None:
        return (False, "no member keys for source")
    quorum = context.get("quorum_by_source", {}).get(att.source_id)
    v = verify_decision(decision, keys, quorum)
    return (v.valid, v.reason)


def _verify_direct_deliberative(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    try:
        decision = DeliberativeDecision.from_dict(att.content)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed DeliberativeDecision: {e}")
    recomputed = _hash_payload(canonical_bytes(decision.to_dict()))
    if recomputed != att.content_hash:
        return (False, "content_hash mismatch")
    keys = context.get("member_keys", {}).get(att.source_id)
    if keys is None:
        return (False, "no member keys for source")
    quorum = context.get("quorum_by_source", {}).get(att.source_id)
    v = verify_deliberative_decision(decision, keys, quorum)
    return (v.valid, v.reason)


def _verify_direct_federated(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    try:
        decision = FederatedDeliberativeDecision.from_dict(att.content)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed FederatedDeliberativeDecision: {e}")
    recomputed = _hash_payload(canonical_bytes(decision.to_dict()))
    if recomputed != att.content_hash:
        return (False, "content_hash mismatch")
    local_keys = context.get("member_keys", {}).get(att.source_id)
    ev_keys = context.get("evidence_member_keys", {}).get(
        att.source_id, {})
    if local_keys is None:
        return (False, "no member keys for source")
    quorum = context.get("quorum_by_source", {}).get(att.source_id)
    v = verify_federated_deliberation(
        decision, local_keys, ev_keys, quorum)
    return (v.valid, v.reason)


def _verify_direct_cross_world(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    try:
        cwa = CrossWorldPersonAttestation.from_dict(att.content)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed CrossWorldPersonAttestation: {e}")
    recomputed = _hash_payload(canonical_bytes(cwa.to_dict()))
    if recomputed != att.content_hash:
        return (False, "content_hash mismatch")
    dag_resolver = context.get("dag_resolvers", {}).get(att.source_id)
    key_resolver = context.get("dag_key_resolvers", {}).get(
        att.source_id)
    trusted_key = context.get("trusted_person_keys", {}).get(
        att.source_id)
    if dag_resolver is None or key_resolver is None:
        return (False, "no resolvers for source")
    v = verify_cross_world_attestation(
        cwa, dag_resolver, key_resolver,
        trusted_person_public_key=trusted_key)
    return (v.valid, v.reason)


DEFAULT_VERIFIER_REGISTRY: Dict[str, AttestationVerifier] = {
    "decision": _verify_direct_decision,
    "deliberative_decision": _verify_direct_deliberative,
    "federated_deliberation": _verify_direct_federated,
    "cross_world_attestation": _verify_direct_cross_world,
    "octopus_epoch": _verify_witnessed,
    "signal_window": _verify_witnessed,
    "swarm_log": _verify_witnessed,
    "autonomic_trace": _verify_witnessed,
}


def verify_federation_attestation(
    attestation: FederationAttestation,
    context: Optional[Dict] = None,
    registry: Optional[Dict[str, AttestationVerifier]] = None,
) -> AttestationVerdict:
    """Dispatch by source_kind. Never raises."""
    if not isinstance(attestation, FederationAttestation):
        return AttestationVerdict(
            valid=False, reason="not a FederationAttestation",
            source_id="", source_kind="")
    reg = registry or DEFAULT_VERIFIER_REGISTRY
    verifier = reg.get(attestation.source_kind)
    if verifier is None:
        return AttestationVerdict(
            valid=False,
            reason=f"no verifier for kind "
                   f"{attestation.source_kind!r}",
            source_id=attestation.source_id,
            source_kind=attestation.source_kind)
    try:
        ok, reason = verifier(attestation, context or {})
    except Exception as e:
        return AttestationVerdict(
            valid=False, reason=f"verifier raised: {e}",
            source_id=attestation.source_id,
            source_kind=attestation.source_kind)
    return AttestationVerdict(
        valid=ok, reason=reason,
        source_id=attestation.source_id,
        source_kind=attestation.source_kind)


# =====================================================================
# CrossKindReference / CrossKindPosition
# =====================================================================

@dataclass(frozen=True)
class CrossKindReference:
    source_id: str
    source_kind: str
    artifact_hash: str

    def __post_init__(self):
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id required")
        if self.source_kind not in ALL_KINDS:
            raise ValueError(
                f"source_kind must be one of {sorted(ALL_KINDS)}; "
                f"got {self.source_kind!r}")
        if len(self.artifact_hash) != 64:
            raise ValueError(
                "artifact_hash must be 64 hex chars")

    def key(self) -> Tuple[str, str, str]:
        return (self.source_id, self.source_kind,
                self.artifact_hash)


@dataclass(frozen=True)
class CrossKindPosition(SignedPosition):
    """A SignedPosition that references cross-kind attestations.

    C46's FederatedSignedPosition references (council_id,
    decision_hash) tuples. C48's CrossKindPosition references
    (source_id, source_kind, artifact_hash) triples — one element
    per dimension of heterogeneity.
    """
    references: Tuple[CrossKindReference, ...] = ()

    def __post_init__(self):
        super().__post_init__()
        for r in self.references:
            if not isinstance(r, CrossKindReference):
                raise ValueError(
                    "each reference must be a CrossKindReference")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "cross_kind_position",
            "member_token": self.member_token,
            "member_name": self.member_name,
            "member_public_key": self.member_public_key,
            "proposal_hash": self.proposal_hash,
            "round_num": self.round_num,
            "stance": self.stance,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
            "references": [
                {"source_id": r.source_id,
                 "source_kind": r.source_kind,
                 "artifact_hash": r.artifact_hash}
                for r in sorted(self.references,
                                 key=lambda r: r.key())
            ],
        })

    def to_dict(self) -> Dict:
        base = super().to_dict()
        base["kind"] = "cross_kind_position"
        base["references"] = [
            {"source_id": r.source_id,
             "source_kind": r.source_kind,
             "artifact_hash": r.artifact_hash}
            for r in self.references
        ]
        return base

    @classmethod
    def from_dict(cls, d: Dict) -> "CrossKindPosition":
        return cls(
            member_token=d["member_token"],
            member_name=d["member_name"],
            member_public_key=d["member_public_key"],
            proposal_hash=d["proposal_hash"],
            round_num=d["round_num"],
            stance=d["stance"],
            rationale=d.get("rationale", ""),
            timestamp=d["timestamp"],
            signature=d["signature"],
            references=tuple(
                CrossKindReference(
                    source_id=r["source_id"],
                    source_kind=r["source_kind"],
                    artifact_hash=r["artifact_hash"])
                for r in d.get("references", [])),
        )


# =====================================================================
# CrossKindDeliberativeMember
# =====================================================================

class CrossKindDeliberativeMember(FederatedDeliberativeMember):
    """A DeliberativeMember whose rule can return cross-kind
    references.

    Rule return shape: (stance, rationale, refs) where refs is
    either:
      - iterable of CrossKindReference
      - iterable of (source_id, source_kind, artifact_hash) triples
    The rule sees `ctx["cross_kind_attestations"]` — a summary
    dict mapping source_id → {source_kind, content_hash, summary}.
    """

    def produce_cross_kind_position(
        self,
        proposal: Proposal,
        round_num: int,
        context: Optional[Dict] = None,
        available_refs: Optional[set] = None,
    ) -> CrossKindPosition:
        ctx = context or {
            "round_num": round_num,
            "positions_by_member": {},
            "cross_kind_attestations": {},
        }
        try:
            if self._rule_takes_context:
                result = self._decision_rule(proposal, ctx)
            else:
                result = self._decision_rule(proposal)
        except Exception:
            result = ("nay", "rule error", ())
        if isinstance(result, tuple) and len(result) == 3:
            stance, rationale, refs = result
        elif isinstance(result, tuple) and len(result) == 2:
            stance, rationale = result
            refs = ()
        elif isinstance(result, str):
            stance, rationale, refs = result, "", ()
        else:
            stance, rationale, refs = "nay", "bad return", ()
        if stance not in DECISIONS:
            stance = "abstain"
        rationale = str(rationale) if rationale else ""
        # Normalize refs
        normalized: List[CrossKindReference] = []
        for r in (refs or ()):
            if isinstance(r, CrossKindReference):
                normalized.append(r)
                continue
            if isinstance(r, (tuple, list)) and len(r) == 3:
                try:
                    normalized.append(CrossKindReference(
                        source_id=str(r[0]),
                        source_kind=str(r[1]),
                        artifact_hash=str(r[2])))
                except (ValueError, TypeError):
                    continue
        ts = _now()
        payload = canonical_bytes({
            "kind": "cross_kind_position",
            "member_token": self._manifest.entity_id,
            "member_name": self._manifest.name,
            "member_public_key": self._member_public_key,
            "proposal_hash": proposal.hash(),
            "round_num": round_num,
            "stance": stance,
            "rationale": rationale,
            "timestamp": ts,
            "references": [
                {"source_id": r.source_id,
                 "source_kind": r.source_kind,
                 "artifact_hash": r.artifact_hash}
                for r in sorted(normalized, key=lambda r: r.key())
            ],
        })
        return CrossKindPosition(
            member_token=self._manifest.entity_id,
            member_name=self._manifest.name,
            member_public_key=self._member_public_key,
            proposal_hash=proposal.hash(),
            round_num=round_num,
            stance=stance,
            rationale=rationale,
            timestamp=ts,
            signature=self._member_kp.sign(payload).hex(),
            references=tuple(normalized),
        )


# =====================================================================
# CrossKindFederatedDecision
# =====================================================================

@dataclass(frozen=True)
class CrossKindFederatedDecision:
    """A DeliberativeDecision plus the cross-kind attestations it
    consumed, embedded for the verifier."""
    inner: DeliberativeDecision
    attestations: Tuple[FederationAttestation, ...]

    def to_dict(self) -> Dict:
        return {
            "inner": self.inner.to_dict(),
            "attestations": [
                a.to_dict() for a in self.attestations],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CrossKindFederatedDecision":
        return cls(
            inner=DeliberativeDecision.from_dict(d["inner"]),
            attestations=tuple(
                FederationAttestation.from_dict(a)
                for a in d.get("attestations", [])),
        )

    def attestation_by_source(
        self, source_id: str,
    ) -> Optional[FederationAttestation]:
        for a in self.attestations:
            if a.source_id == source_id:
                return a
        return None


# =====================================================================
# CrossKindCouncil
# =====================================================================

class CrossKindCouncil(FederatedDeliberativeCouncil):
    """A FederatedDeliberativeCouncil that consumes cross-kind
    attestations and produces a CrossKindFederatedDecision.
    """

    def deliberate_and_resolve_cross_kind(
        self,
        proposal: Proposal,
        attestations: List[FederationAttestation],
    ) -> CrossKindFederatedDecision:
        attestation_by_source = {
            a.source_id: a for a in attestations}
        # Summaries passed to rules via context
        summaries = {
            a.source_id: {
                "source_kind": a.source_kind,
                "content_hash": a.content_hash,
                "is_witnessed": a.is_witnessed,
            }
            for a in attestations
        }
        available_refs = {
            (a.source_id, a.source_kind, a.content_hash)
            for a in attestations
        }
        members = list(self._members.values())
        positions: List[CrossKindPosition] = []
        by_round: Dict[int, Dict[str, str]] = {}
        converged_at: Optional[int] = None
        stable_count = 0

        for round_num in range(self._max_rounds):
            context = {
                "round_num": round_num,
                "positions_by_member": {
                    tok: {"stance": stance,
                          "rationale": rationale}
                    for tok, (stance, rationale)
                    in _latest_stances(positions).items()
                },
                "cross_kind_attestations": summaries,
            }
            round_positions: Dict[str, str] = {}
            for member in members:
                if isinstance(member, CrossKindDeliberativeMember):
                    pos = member.produce_cross_kind_position(
                        proposal, round_num, context,
                        available_refs)
                else:
                    # Fall back to C45/C46 position if the member
                    # isn't cross-kind-aware
                    base = member.produce_position(
                        proposal, round_num, context)
                    pos = CrossKindPosition(
                        member_token=base.member_token,
                        member_name=base.member_name,
                        member_public_key=base.member_public_key,
                        proposal_hash=base.proposal_hash,
                        round_num=base.round_num,
                        stance=base.stance,
                        rationale=base.rationale,
                        timestamp=base.timestamp,
                        signature=base.signature,
                        references=(),
                    )
                positions.append(pos)
                round_positions[pos.member_token] = pos.stance
                self._deliberation_log.emit(
                    "position", 1.0, {
                        "member_token": pos.member_token,
                        "round_num": round_num,
                        "stance": pos.stance,
                        "rationale": pos.rationale,
                        "signature": pos.signature,
                        "proposal_hash": pos.proposal_hash,
                        "references": [
                            {"source_id": r.source_id,
                             "source_kind": r.source_kind,
                             "artifact_hash": r.artifact_hash}
                            for r in pos.references
                        ],
                    })
            by_round[round_num] = round_positions
            if round_num > 0:
                if round_positions == by_round[round_num - 1]:
                    stable_count += 1
                else:
                    stable_count = 0
            if stable_count >= self._stability_rounds:
                converged_at = round_num
                break

        rounds_run = len(by_round)
        final_votes: List[Vote] = []
        final_context = {
            "round_num": rounds_run,
            "positions_by_member": {
                tok: {"stance": stance,
                      "rationale": rationale}
                for tok, (stance, rationale)
                in _latest_stances(positions).items()
            },
            "cross_kind_attestations": summaries,
        }
        for member in members:
            try:
                final_votes.append(member.cast_final_vote(
                    proposal, final_context))
            except Exception:
                pass
        final_decision = self._tally(proposal, final_votes)

        inner = DeliberativeDecision(
            proposal=proposal.content,
            proposal_hash=proposal.hash(),
            positions=tuple(positions),
            rounds_run=rounds_run,
            converged_at_round=converged_at,
            final_decision=final_decision,
        )
        return CrossKindFederatedDecision(
            inner=inner,
            attestations=tuple(attestations),
        )


# =====================================================================
# Verification
# =====================================================================

@dataclass
class CrossKindFederatedVerdict:
    valid: bool
    reason: str
    local_valid: bool
    attestation_verdicts: List[AttestationVerdict]
    reference_errors: List[Tuple[str, str]] = field(
        default_factory=list)

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Cross-Kind Federation Verification",
            "=" * 70,
            f"  local_valid:      {self.local_valid}",
            f"  attestations:     {len(self.attestation_verdicts)}",
            f"  reference errors: {len(self.reference_errors)}",
            "",
        ]
        lines.append("  Attestations:")
        for v in self.attestation_verdicts:
            lines.append(v.format())
        if self.reference_errors:
            lines.append("  Reference errors:")
            for tok, reason in self.reference_errors:
                lines.append(f"    ✗ {tok[:16]}...: {reason}")
        lines.append("")
        lines.append(
            f"  Overall valid: {self.valid}")
        if not self.valid:
            lines.append(f"  Reason: {self.reason}")
        return "\n".join(lines)


def verify_cross_kind_federation(
    decision: CrossKindFederatedDecision,
    local_member_keys: Dict[str, str],
    context: Optional[Dict] = None,
    registry: Optional[Dict[str, AttestationVerifier]] = None,
    quorum: Optional[QuorumRule] = None,
) -> CrossKindFederatedVerdict:
    """Verify a CrossKindFederatedDecision. Never raises.

    Checks, in order:
      1. Local decision verifies (C45's
         verify_deliberative_decision on the inner).
      2. Each CrossKindPosition's signature verifies (via C45's
         verify_position on the polymorphic payload).
      3. Each CrossKindPosition's references are in the
         attestation set.
      4. Each referenced attestation verifies via the kind
         dispatch.

    Never raises. Bad inputs, missing keys, forged signatures all
    return verdicts with named errors.
    """
    if not HAS_CRYPTO:
        return CrossKindFederatedVerdict(
            valid=False, reason="cryptography not installed",
            local_valid=False, attestation_verdicts=[],
            reference_errors=[])
    if not isinstance(decision, CrossKindFederatedDecision):
        return CrossKindFederatedVerdict(
            valid=False, reason="not a CrossKindFederatedDecision",
            local_valid=False, attestation_verdicts=[],
            reference_errors=[])

    # 1. Local decision (C45)
    local_verdict = verify_deliberative_decision(
        decision.inner, local_member_keys, quorum)
    local_valid = local_verdict.valid

    # 2-3. Verify each position's signature (via C45 verify_position
    # on polymorphic payload) and check its references
    attestation_by_source = {
        a.source_id: a for a in decision.attestations}
    available_refs = {
        (a.source_id, a.source_kind, a.content_hash)
        for a in decision.attestations
    }
    reference_errors: List[Tuple[str, str]] = []
    for p in decision.inner.positions:
        if not isinstance(p, CrossKindPosition):
            continue
        mpk = local_member_keys.get(p.member_token)
        if mpk is None:
            continue  # local verifier already flagged
        # Signature over the cross-kind payload
        if not verify_position(p, mpk):
            reference_errors.append(
                (p.member_token,
                 "signature over cross-kind payload INVALID"))
            continue
        # Every reference must be in the attestation set
        for ref in p.references:
            if ref.key() not in available_refs:
                reference_errors.append(
                    (p.member_token,
                     f"reference {ref.source_kind}::"
                     f"{ref.source_id} not in attestations"))

    # 4. Verify each attestation via dispatch
    ctx = context or {}
    attestation_verdicts: List[AttestationVerdict] = []
    for a in decision.attestations:
        v = verify_federation_attestation(a, ctx, registry)
        attestation_verdicts.append(v)

    all_attestations_valid = all(
        v.valid for v in attestation_verdicts)
    references_valid = not reference_errors
    all_valid = (local_valid and all_attestations_valid
                 and references_valid)

    if all_valid:
        reason = ("local decision valid; "
                  "all attestations valid; "
                  "all references valid")
    else:
        parts = []
        if not local_valid:
            parts.append("local decision invalid")
        if not all_attestations_valid:
            failed = [
                v for v in attestation_verdicts if not v.valid]
            parts.append(
                f"{len(failed)} attestation(s) failed")
        if not references_valid:
            parts.append(
                f"{len(reference_errors)} reference error(s)")
        reason = "; ".join(parts)

    return CrossKindFederatedVerdict(
        valid=all_valid, reason=reason,
        local_valid=local_valid,
        attestation_verdicts=attestation_verdicts,
        reference_errors=reference_errors)


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Five architectures, one federation, one meta-decision.

    Produces:
      - A C44 council Decision ("alpha")
      - A C45 deliberation Decision ("beta")
      - A C43 swarm convergence log, witnessed
      - A C47 autonomic state trace, witnessed
      - A CrossKindCouncil ("meta") whose members see all four,
        reference them, and produce a meta-decision

    Verification: meta decision valid iff local votes valid AND
    each referenced attestation verifies per its own contract.

    Anchor: Dickinson, 'The Brain – is wider than the Sky –'
    (the closing of the five-architecture arc on that poem).
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity, Identity
    from multiverse_c43 import SwarmUnit, SwarmNetwork
    from multiverse_c47 import AutonomicUnit, AutonomicNetwork

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # -------------------------------------------------------------
    # Source 1: a C44 council decision
    # -------------------------------------------------------------
    alpha_kps = [KeyPair.generate() for _ in range(3)]
    alpha = DeliberativeCouncil(
        "alpha", QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(alpha_kps):
        alpha.add_member(DeliberativeMember(
            entity_id=f"alpha:m{i}", name=f"Alpha-{i}",
            member_kp=kp,
            decision_rule=lambda p, c: ("yea", "approve")))
    alpha_keys = {
        f"alpha:m{i}": kp.public_key_hex()
        for i, kp in enumerate(alpha_kps)
    }
    alpha_decision = alpha.deliberate_and_resolve(
        Proposal(content={"action": "adopt-relay"}))
    a_decision_att = attest_decision(
        "council-alpha", alpha_decision.final_decision)

    # -------------------------------------------------------------
    # Source 2: a C45 deliberative decision
    # -------------------------------------------------------------
    beta_kps = [KeyPair.generate() for _ in range(3)]
    beta = DeliberativeCouncil(
        "beta", QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(beta_kps):
        beta.add_member(DeliberativeMember(
            entity_id=f"beta:m{i}", name=f"Beta-{i}",
            member_kp=kp,
            decision_rule=lambda p, c: ("yea", "yes")))
    beta_keys = {
        f"beta:m{i}": kp.public_key_hex()
        for i, kp in enumerate(beta_kps)
    }
    beta_decision = beta.deliberate_and_resolve(
        Proposal(content={"action": "adopt-octopus"}))
    b_deliberative_att = attest_deliberative_decision(
        "council-beta", beta_decision)

    # -------------------------------------------------------------
    # Source 3: a C43 swarm convergence log
    # -------------------------------------------------------------
    swarm_net = SwarmNetwork(food_target=(5, 5), max_epochs=20)
    for i in range(3):
        swarm_net.add_unit(f"ant-{i}", SwarmUnit(
            entity_id=f"world:ant-{i}", name=f"ant-{i}",
            env_stream=swarm_net.stream,
            initial_position=(i, i),
            seed=42 + i, sample_probability=1.0))
    swarm_net.unit_by_name("ant-0").act(
        __import__("multiverse_c3", fromlist=["Act"]).Act(
            actor_token="ext", type="find_food",
            payload={"location": [5, 5]}))
    swarm_epochs = []
    for _ in range(10):
        r = swarm_net.run_epoch()
        swarm_epochs.append({
            "epoch": r.epoch,
            "units_at_food": r.statistics["units_at_food"],
            "converged": r.statistics["converged"],
        })
        if r.statistics["converged"]:
            break
    swarm_content = {"epochs": swarm_epochs,
                      "final_converged": swarm_net.converged()}

    witness_kp = KeyPair.generate()
    witness_id = create_identity("swarm-recorder")
    c_swarm_att = witness_artifact(
        "swarm-1", "swarm_log", swarm_content,
        witness_kp, witness_id)
    witness_keys = {witness_id.token: witness_kp.public_key_hex()}

    # -------------------------------------------------------------
    # Source 4: a C47 autonomic state trace
    # -------------------------------------------------------------
    auto_net = AutonomicNetwork()
    auto_net.set_coupling_heat(0.2)
    for name in ("A", "B", "C"):
        auto_net.add_unit(name, AutonomicUnit(
            entity_id=f"world:{name.lower()}", name=name,
            target=22.0, initial_state=20.0,
            correction_strength=3.0, ambient_drift=0.5))
    auto_trace = []
    for _ in range(10):
        r = auto_net.run_epoch()
        auto_trace.append({
            "epoch": r.epoch,
            "states": dict(r.states),
            "fires": dict(r.fires),
        })
    auto_content = {"trace": auto_trace,
                     "within_tolerance":
                        auto_net.all_within_tolerance(4.0)}
    monitor_kp = KeyPair.generate()
    monitor_id = create_identity("autonomic-monitor")
    d_autonomic_att = witness_artifact(
        "autonomic-1", "autonomic_trace", auto_content,
        monitor_kp, monitor_id)
    witness_keys[monitor_id.token] = monitor_kp.public_key_hex()

    # -------------------------------------------------------------
    # The meta-council: consumes all four
    # -------------------------------------------------------------
    meta_kps = [KeyPair.generate() for _ in range(3)]
    def meta_rule(p, ctx):
        attestations = ctx.get("cross_kind_attestations", {})
        refs = []
        for sid, summary in attestations.items():
            refs.append(CrossKindReference(
                source_id=sid,
                source_kind=summary["source_kind"],
                artifact_hash=summary["content_hash"]))
        return ("yea",
                f"considered {len(refs)} cross-kind attestations",
                refs)
    meta = CrossKindCouncil(
        "meta", QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(meta_kps):
        meta.add_member(CrossKindDeliberativeMember(
            entity_id=f"meta:m{i}", name=f"Meta-{i}",
            member_kp=kp, decision_rule=meta_rule))
    meta_keys = {
        f"meta:m{i}": kp.public_key_hex()
        for i, kp in enumerate(meta_kps)
    }
    meta_proposal = Proposal(content={
        "action": "federate-all-four",
        "note": "cross-architecture federation",
    })
    meta_decision = meta.deliberate_and_resolve_cross_kind(
        meta_proposal,
        attestations=[
            a_decision_att,
            b_deliberative_att,
            c_swarm_att,
            d_autonomic_att,
        ])

    # -------------------------------------------------------------
    # Verify
    # -------------------------------------------------------------
    verification_context = {
        "member_keys": {
            "council-alpha": alpha_keys,
            "council-beta": beta_keys,
        },
        "witness_public_keys": witness_keys,
    }
    meta_verdict = verify_cross_kind_federation(
        meta_decision,
        local_member_keys=meta_keys,
        context=verification_context,
    )

    # -------------------------------------------------------------
    # Negative: tampered swarm log
    # -------------------------------------------------------------
    tampered_swarm = FederationAttestation(
        source_id=c_swarm_att.source_id,
        source_kind=c_swarm_att.source_kind,
        content={**c_swarm_att.content, "final_converged": False},
        content_hash=c_swarm_att.content_hash,  # doesn't match new content
        witness_token=c_swarm_att.witness_token,
        witness_name=c_swarm_att.witness_name,
        witness_public_key=c_swarm_att.witness_public_key,
        witness_signature=c_swarm_att.witness_signature,
        witness_timestamp=c_swarm_att.witness_timestamp,
    )
    tampered_decision = CrossKindFederatedDecision(
        inner=meta_decision.inner,
        attestations=(
            a_decision_att,
            b_deliberative_att,
            tampered_swarm,
            d_autonomic_att,
        ),
    )
    tampered_verdict = verify_cross_kind_federation(
        tampered_decision,
        local_member_keys=meta_keys,
        context=verification_context,
    )

    # -------------------------------------------------------------
    # Print
    # -------------------------------------------------------------
    print("=" * 70)
    print("Cross-Architecture Federation — five architectures,")
    print("one meta-decision")
    print("=" * 70)
    print()
    print("  Source attestations:")
    for a in [a_decision_att, b_deliberative_att,
              c_swarm_att, d_autonomic_att]:
        mode = "witnessed" if a.is_witnessed else "direct"
        print(f"    {a.source_id:20s} kind={a.source_kind:25s} "
              f"({mode})")
        print(f"    {'':20s} hash={a.content_hash[:16]}...")
    print()
    print("  Meta decision:")
    print(f"    proposal: {meta_decision.inner.proposal}")
    print(f"    outcome:  "
          f"{meta_decision.inner.final_decision.outcome.upper()}")
    print(f"    votes:    "
          f"{meta_decision.inner.final_decision.yea_count} yea, "
          f"{meta_decision.inner.final_decision.nay_count} nay")
    print()
    print("  Verification (happy path):")
    for line in meta_verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Verification (tampered swarm content, hash mismatch):")
    for line in tampered_verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  What this demonstrates:")
    print("    - Direct attestations verify via their own")
    print("      architecture's verifier (C44, C45, C46, C40).")
    print("    - Witnessed attestations verify via a witness")
    print("      signature over the content hash (C41, C42, C43,")
    print("      C47).")
    print("    - A meta-council references both kinds by")
    print("      (source_id, source_kind, artifact_hash).")
    print("    - Tampering with any source is caught by the")
    print("      corresponding verifier, not by the meta-council.")
    print("    - Five architectures, one federation. The substrate")
    print("      holds them simultaneously.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    (the closing of the five-architecture arc)")

    audit = {
        "sources": [
            {"source_id": a.source_id, "kind": a.source_kind,
             "mode": "witnessed" if a.is_witnessed else "direct",
             "hash": a.content_hash}
            for a in [a_decision_att, b_deliberative_att,
                      c_swarm_att, d_autonomic_att]
        ],
        "meta_outcome":
            meta_decision.inner.final_decision.outcome,
        "meta_reference_count":
            sum(len(p.references) for p in
                meta_decision.inner.positions
                if isinstance(p, CrossKindPosition)),
        "happy_verdict": {
            "valid": meta_verdict.valid,
            "local_valid": meta_verdict.local_valid,
            "attestations_all_valid": all(
                v.valid for v in meta_verdict.attestation_verdicts),
            "reference_error_count":
                len(meta_verdict.reference_errors),
        },
        "tampered_verdict": {
            "valid": tampered_verdict.valid,
            "attestation_verdicts": [
                {"source_id": v.source_id, "valid": v.valid,
                 "reason": v.reason}
                for v in tampered_verdict.attestation_verdicts
            ],
        },
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "cross_architecture_federation_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/cross_architecture_federation_demo.json")
    return audit
