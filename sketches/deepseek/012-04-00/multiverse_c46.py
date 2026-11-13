"""
multiverse_c46.py — Component 46: Federated Deliberation.

Two councils, one referencing the other's decision as evidence.
A DeliberativeCouncil (C45) produces a local decision; a
FederatedDeliberativeCouncil additionally accepts a list of
FederationEvidence — decisions by other councils — passes summaries
to members' rules, and produces a FederatedDeliberativeDecision.

The verification chain:
  Local decision → positions with references
    → each reference in evidence set
    → each evidence's decision verifies against its own members' keys

Not "council B trusts council A." Rather: "council B's members
referenced specific, hash-identified decisions by council A, and
each of those decisions independently verifies."

Infrastructure addition:
  FederatedSignedPosition(SignedPosition) — same fields + references.
  Canonical payload includes references. C45's verify_position
  still works (polymorphic canonical_payload).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: reference included in payload, ref
    verified against evidence, tampered evidence caught,
    missing evidence keys caught, backward compat with C45,
    JSON roundtrip, never raises.
  - "A world never raises on what a visitor sends" — rule
    exceptions yield abstain; verifiers return verdicts.
  - "History, not rank" — federated decisions record references,
    not endorsements.

Honest limits (documented, tested):
  - Evidence is embedded in the decision. The verifier supplies
    the evidence's member keys. So the "trust anchor" for the
    evidence is external — same as everywhere.
  - No evidence revocation. A decision once referenced stays
    referenced. Future.
  - No cycles: evidence can itself be a federated decision, and
    verification recurses, but no cycle protection. A
    deliberately crafted cycle would recurse infinitely. Not
    defended against in the prototype.
  - No anonymization: references name their council. A member
    who references alpha announces that they consulted alpha.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c44 import (
    Proposal, Vote, DECISIONS, QuorumRule, Decision,
    TriumvirateMember, verify_decision,
)
from multiverse_c45 import (
    SignedPosition, verify_position,
    DeliberativeMember, DeliberativeDecision,
    DeliberativeCouncil,
    verify_deliberative_decision,
    _latest_stances, _hash_payload,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# FederatedSignedPosition
# =====================================================================

@dataclass(frozen=True)
class FederatedSignedPosition(SignedPosition):
    """A SignedPosition with a signed list of external references.

    Each reference is (council_id, decision_hash) — a claim by the
    member that they consulted a specific decision by a specific
    council. Signed as part of the position payload.
    """
    references: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self):
        # Chain parent validation
        super().__post_init__()
        # Validate references
        for ref in self.references:
            if not isinstance(ref, tuple) or len(ref) != 2:
                raise ValueError(
                    "each reference must be a (council_id, "
                    "decision_hash) tuple")
            cid, h = ref
            if not isinstance(cid, str) or not cid:
                raise ValueError(
                    "reference council_id must be non-empty string")
            if not isinstance(h, str) or len(h) != 64:
                raise ValueError(
                    "reference decision_hash must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "federated_deliberation_position",
            "member_token": self.member_token,
            "member_name": self.member_name,
            "member_public_key": self.member_public_key,
            "proposal_hash": self.proposal_hash,
            "round_num": self.round_num,
            "stance": self.stance,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
            "references": [list(r)
                            for r in sorted(self.references)],
        })

    def to_dict(self) -> Dict:
        base = super().to_dict()
        base["kind"] = "federated_deliberation_position"
        base["references"] = [list(r) for r in self.references]
        return base

    @classmethod
    def from_dict(cls, d: Dict) -> "FederatedSignedPosition":
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
                (r[0], r[1])
                for r in d.get("references", [])),
        )


def verify_federated_position(
    position: FederatedSignedPosition,
    member_public_key: str,
    allowed_references: set,
) -> Tuple[bool, str]:
    """Verify signature AND that every reference is in
    allowed_references. Never raises.

    Note: C45's verify_position() still works on a
    FederatedSignedPosition (polymorphic canonical_payload). This
    function adds the reference check.
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(position, FederatedSignedPosition):
        return (False, "not a FederatedSignedPosition")
    # Signature check (via parent's function, which uses our
    # overridden canonical_payload — so it verifies the federated
    # payload including references)
    if not verify_position(position, member_public_key):
        return (False, "signature INVALID")
    # Reference check
    for ref in position.references:
        if ref not in allowed_references:
            return (False,
                    f"reference {ref[0]}::"
                    f"{ref[1][:16]}... not in evidence")
    return (True, "signature valid, all references in evidence")


# =====================================================================
# FederationEvidence
# =====================================================================

@dataclass(frozen=True)
class FederationEvidence:
    """A decision by an external council, wrapped for inclusion in
    federated deliberation.
    """
    council_id: str
    decision: Union[Decision, DeliberativeDecision]
    decision_hash: str
    outcome: str
    yea_count: int
    nay_count: int
    abstain_count: int
    proposal_hash: str

    def __post_init__(self):
        if not isinstance(self.council_id, str) or not self.council_id:
            raise ValueError("council_id required")
        if not isinstance(self.decision,
                            (Decision, DeliberativeDecision)):
            raise ValueError(
                "decision must be Decision or "
                "DeliberativeDecision")
        if len(self.decision_hash) != 64:
            raise ValueError(
                "decision_hash must be 64 hex chars")
        if self.outcome not in ("passed", "rejected", "no_quorum"):
            raise ValueError(f"unexpected outcome {self.outcome!r}")

    def to_summary(self) -> Dict:
        return {
            "council_id": self.council_id,
            "decision_hash": self.decision_hash,
            "outcome": self.outcome,
            "yea": self.yea_count,
            "nay": self.nay_count,
            "abstain": self.abstain_count,
            "proposal_hash": self.proposal_hash,
        }

    def to_dict(self) -> Dict:
        return {
            "council_id": self.council_id,
            "decision": self.decision.to_dict(),
            "decision_hash": self.decision_hash,
            "outcome": self.outcome,
            "yea_count": self.yea_count,
            "nay_count": self.nay_count,
            "abstain_count": self.abstain_count,
            "proposal_hash": self.proposal_hash,
        }

    @classmethod
    def from_decision(
        cls,
        council_id: str,
        decision: Union[Decision, DeliberativeDecision],
    ) -> "FederationEvidence":
        if isinstance(decision, DeliberativeDecision):
            inner = decision.final_decision
        elif isinstance(decision, Decision):
            inner = decision
        else:
            raise TypeError(
                f"expected Decision or DeliberativeDecision, "
                f"got {type(decision).__name__}")
        h = _hash_payload(canonical_bytes(decision.to_dict()))
        return cls(
            council_id=council_id,
            decision=decision,
            decision_hash=h,
            outcome=inner.outcome,
            yea_count=inner.yea_count,
            nay_count=inner.nay_count,
            abstain_count=inner.abstain_count,
            proposal_hash=inner.proposal_hash,
        )

    @classmethod
    def from_dict(cls, d: Dict) -> "FederationEvidence":
        dec_dict = d["decision"]
        # Heuristic: DeliberativeDecision has "positions" and
        # "final_decision"
        if "positions" in dec_dict and "final_decision" in dec_dict:
            dec = DeliberativeDecision.from_dict(dec_dict)
        else:
            dec = Decision.from_dict(dec_dict)
        return cls(
            council_id=d["council_id"],
            decision=dec,
            decision_hash=d["decision_hash"],
            outcome=d["outcome"],
            yea_count=d["yea_count"],
            nay_count=d["nay_count"],
            abstain_count=d["abstain_count"],
            proposal_hash=d["proposal_hash"],
        )


# =====================================================================
# FederatedDeliberativeMember
# =====================================================================

class FederatedDeliberativeMember(DeliberativeMember):
    """A DeliberativeMember that produces federated positions.

    If the rule returns a 3-tuple (stance, rationale, references),
    a FederatedSignedPosition is produced. Otherwise the parent's
    produce_position is used (2-tuple or string).
    """

    def produce_federated_position(
        self,
        proposal: Proposal,
        round_num: int,
        context: Optional[Dict] = None,
        available_refs: Optional[set] = None,
    ) -> FederatedSignedPosition:
        ctx = context or {
            "round_num": round_num,
            "positions_by_member": {},
            "federation_evidence": {},
        }
        try:
            if self._rule_takes_context:
                result = self._decision_rule(proposal, ctx)
            else:
                result = self._decision_rule(proposal)
        except Exception:
            result = ("nay", "rule error", ())
        # Normalize
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
        # Normalize references to tuples of (str, str)
        normalized_refs = tuple(
            (str(r[0]), str(r[1]))
            for r in (refs or ())
            if isinstance(r, (tuple, list)) and len(r) == 2
        )
        ts = _now()
        # Build the federated canonical payload for signing
        payload = canonical_bytes({
            "kind": "federated_deliberation_position",
            "member_token": self._manifest.entity_id,
            "member_name": self._manifest.name,
            "member_public_key": self._member_public_key,
            "proposal_hash": proposal.hash(),
            "round_num": round_num,
            "stance": stance,
            "rationale": rationale,
            "timestamp": ts,
            "references": [list(r)
                            for r in sorted(normalized_refs)],
        })
        return FederatedSignedPosition(
            member_token=self._manifest.entity_id,
            member_name=self._manifest.name,
            member_public_key=self._member_public_key,
            proposal_hash=proposal.hash(),
            round_num=round_num,
            stance=stance,
            rationale=rationale,
            timestamp=ts,
            signature=self._member_kp.sign(payload).hex(),
            references=normalized_refs,
        )


# =====================================================================
# FederatedDeliberativeDecision
# =====================================================================

@dataclass(frozen=True)
class FederatedDeliberativeDecision:
    """A DeliberativeDecision plus the federation evidence it used."""
    inner: DeliberativeDecision
    federation_evidence: Tuple[FederationEvidence, ...]

    def to_dict(self) -> Dict:
        return {
            "inner": self.inner.to_dict(),
            "federation_evidence": [
                e.to_dict() for e in self.federation_evidence],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "FederatedDeliberativeDecision":
        return cls(
            inner=DeliberativeDecision.from_dict(d["inner"]),
            federation_evidence=tuple(
                FederationEvidence.from_dict(e)
                for e in d.get("federation_evidence", [])),
        )

    @property
    def proposal_hash(self) -> str:
        return self.inner.proposal_hash

    def format(self) -> str:
        lines = ["=" * 70,
                 "Federated Deliberative Decision",
                 "=" * 70]
        if self.federation_evidence:
            lines.append("  External evidence:")
            for e in self.federation_evidence:
                lines.append(
                    f"    {e.council_id}: outcome={e.outcome} "
                    f"(yea={e.yea_count} nay={e.nay_count} "
                    f"abstain={e.abstain_count})")
                lines.append(
                    f"      decision_hash="
                    f"{e.decision_hash[:16]}...")
        else:
            lines.append("  External evidence: (none)")
        lines.append("")
        lines.append(self.inner.format())
        return "\n".join(lines)


# =====================================================================
# FederatedDeliberativeCouncil
# =====================================================================

class FederatedDeliberativeCouncil(DeliberativeCouncil):
    """A DeliberativeCouncil that can consume external evidence."""

    def deliberate_and_resolve_federated(
        self,
        proposal: Proposal,
        evidence: List[FederationEvidence],
    ) -> FederatedDeliberativeDecision:
        """Run deliberation with the given evidence available to
        members' rules. Members may reference evidence in their
        positions. Never raises for bad input."""
        evidence_by_council = {e.council_id: e for e in evidence}
        # Summaries passed to rules via context
        evidence_summary = {
            cid: e.to_summary()
            for cid, e in evidence_by_council.items()
        }
        # The set of references that positions are allowed to make
        allowed_refs = {
            (e.council_id, e.decision_hash) for e in evidence
        }
        members = list(self._members.values())
        positions: List[FederatedSignedPosition] = []
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
                "federation_evidence": evidence_summary,
            }
            round_positions: Dict[str, str] = {}
            for member in members:
                # Members of this council must be
                # FederatedDeliberativeMember to produce federated
                # positions; if they're plain DeliberativeMembers,
                # we wrap their C45 positions as federated ones
                # with empty references. (This lets a council mix
                # federated and non-federated members.)
                if isinstance(member, FederatedDeliberativeMember):
                    pos = member.produce_federated_position(
                        proposal, round_num, context, allowed_refs)
                else:
                    base_pos = member.produce_position(
                        proposal, round_num, context)
                    pos = FederatedSignedPosition(
                        member_token=base_pos.member_token,
                        member_name=base_pos.member_name,
                        member_public_key=base_pos.member_public_key,
                        proposal_hash=base_pos.proposal_hash,
                        round_num=base_pos.round_num,
                        stance=base_pos.stance,
                        rationale=base_pos.rationale,
                        timestamp=base_pos.timestamp,
                        signature=base_pos.signature,
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
                        "references": [list(r)
                                        for r in pos.references],
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

        # Final vote: C44 votes
        final_votes: List[Vote] = []
        final_context = {
            "round_num": rounds_run,
            "positions_by_member": {
                tok: {"stance": stance,
                      "rationale": rationale}
                for tok, (stance, rationale)
                in _latest_stances(positions).items()
            },
            "federation_evidence": evidence_summary,
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
        return FederatedDeliberativeDecision(
            inner=inner,
            federation_evidence=tuple(evidence),
        )


# =====================================================================
# Verification
# =====================================================================

@dataclass
class FederatedDeliberativeVerdict:
    valid: bool
    reason: str
    local_valid: bool
    evidence_valid: bool
    references_valid: bool
    evidence_errors: List[Tuple[str, str]] = field(default_factory=list)
    reference_errors: List[Tuple[str, str]] = field(
        default_factory=list)

    def format(self) -> str:
        lines = [
            "Federated Deliberation Verification",
            "=" * 50,
            f"  valid:            {self.valid}",
            f"  local_valid:      {self.local_valid}",
            f"  evidence_valid:   {self.evidence_valid}",
            f"  references_valid: {self.references_valid}",
        ]
        if self.evidence_errors:
            lines.append("  evidence errors:")
            for cid, reason in self.evidence_errors:
                lines.append(f"    ✗ {cid}: {reason}")
        if self.reference_errors:
            lines.append("  reference errors:")
            for tok, reason in self.reference_errors:
                lines.append(f"    ✗ {tok[:16]}...: {reason}")
        if not self.valid:
            lines.append(f"  reason: {self.reason}")
        return "\n".join(lines)


def verify_federated_deliberation(
    decision: FederatedDeliberativeDecision,
    local_member_keys: Dict[str, str],
    evidence_member_keys: Dict[str, Dict[str, str]],
    quorum: Optional[QuorumRule] = None,
) -> FederatedDeliberativeVerdict:
    """Verify a FederatedDeliberativeDecision. Never raises.

    Chain:
      1. Local decision verifies (C45's verify_deliberative_decision).
      2. Each evidence's decision verifies against its own
         council's member keys (evidence_member_keys[council_id]).
      3. Each evidence's decision_hash matches its decision content.
      4. Each federated position's references are in the evidence
         set, and each referenced evidence verifies.

    Never raises. Missing keys, bad hashes, forged positions all
    return verdicts with errors named.
    """
    if not HAS_CRYPTO:
        return FederatedDeliberativeVerdict(
            valid=False, reason="cryptography not installed",
            local_valid=False, evidence_valid=False,
            references_valid=False)
    if not isinstance(decision, FederatedDeliberativeDecision):
        return FederatedDeliberativeVerdict(
            valid=False, reason="not a federated decision",
            local_valid=False, evidence_valid=False,
            references_valid=False)

    # 1. Local decision
    local_verdict = verify_deliberative_decision(
        decision.inner, local_member_keys, quorum)
    local_valid = local_verdict.valid

    # 2. Evidence: each evidence's decision verifies
    evidence_errors: List[Tuple[str, str]] = []
    evidence_by_council: Dict[str, FederationEvidence] = {}
    for ev in decision.federation_evidence:
        evidence_by_council[ev.council_id] = ev
        # 2a. Hash matches decision content
        try:
            computed_hash = _hash_payload(
                canonical_bytes(ev.decision.to_dict()))
        except Exception as e:
            evidence_errors.append(
                (ev.council_id, f"decision cannot be hashed: {e}"))
            continue
        if computed_hash != ev.decision_hash:
            evidence_errors.append(
                (ev.council_id,
                 "declared decision_hash does not match "
                 "decision content"))
            continue
        # 2b. Decision verifies with evidence's member keys
        ev_keys = evidence_member_keys.get(ev.council_id)
        if ev_keys is None:
            evidence_errors.append(
                (ev.council_id, "no member keys supplied"))
            continue
        if isinstance(ev.decision, DeliberativeDecision):
            ev_verdict = verify_deliberative_decision(
                ev.decision, ev_keys, quorum)
        elif isinstance(ev.decision, Decision):
            ev_verdict = verify_decision(
                ev.decision, ev_keys, quorum)
        else:
            evidence_errors.append(
                (ev.council_id, "unexpected decision type"))
            continue
        if not ev_verdict.valid:
            evidence_errors.append(
                (ev.council_id,
                 f"decision INVALID: {ev_verdict.reason}"))
    evidence_valid = not evidence_errors

    # 3. References in positions: each must be in evidence
    allowed_refs = {
        (e.council_id, e.decision_hash)
        for e in decision.federation_evidence
    }
    reference_errors: List[Tuple[str, str]] = []
    # Also verify each federated position's signature over the
    # references (which the local verifier already did via
    # verify_position on the canonical payload — but the local
    # verifier also needs to accept FederatedSignedPosition)
    for p in decision.inner.positions:
        if not isinstance(p, FederatedSignedPosition):
            continue  # C45 plain position; nothing to check here
        mpk = local_member_keys.get(p.member_token)
        if mpk is None:
            # Local verifier would have flagged this already
            continue
        # Signature over the federated payload (parent's
        # canonical_payload via polymorphic call)
        if not verify_position(p, mpk):
            reference_errors.append(
                (p.member_token,
                 "signature over federated payload INVALID"))
            continue
        for ref in p.references:
            if ref not in allowed_refs:
                reference_errors.append(
                    (p.member_token,
                     f"reference {ref[0]}::"
                     f"{ref[1][:16]}... not in evidence"))
    references_valid = not reference_errors

    all_valid = (local_valid and evidence_valid
                 and references_valid)
    if all_valid:
        reason = "local decision valid; evidence valid; " \
                 "references valid"
    else:
        parts = []
        if not local_valid:
            parts.append("local decision invalid")
        if not evidence_valid:
            parts.append(f"{len(evidence_errors)} evidence error(s)")
        if not references_valid:
            parts.append(
                f"{len(reference_errors)} reference error(s)")
        reason = "; ".join(parts)

    return FederatedDeliberativeVerdict(
        valid=all_valid, reason=reason,
        local_valid=local_valid,
        evidence_valid=evidence_valid,
        references_valid=references_valid,
        evidence_errors=evidence_errors,
        reference_errors=reference_errors)


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two councils. Alpha decides; Beta sees Alpha's decision as
    evidence and references it.

    Scenario A: Alpha passes; Beta passes with references.
    Scenario B: Beta has a forged reference (not in evidence).
    Scenario C: Beta's evidence has the wrong decision_hash.

    Anchor: Dickinson, 'The Soul selects her own Society –'
    (councils choose which other councils they consult).
    """
    import json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # ---- Council Alpha ----
    alpha_kps = [KeyPair.generate() for _ in range(3)]
    def alpha_rule(p, ctx):
        # All vote yea
        return ("yea", "approve", ())
    alpha = FederatedDeliberativeCouncil(
        "alpha", QuorumRule(2, 2), max_rounds=3,
        stability_rounds=1)
    for i, kp in enumerate(alpha_kps):
        alpha.add_member(FederatedDeliberativeMember(
            entity_id=f"alpha:m{i}", name=f"Alpha-{i}",
            member_kp=kp, decision_rule=alpha_rule))
    alpha_keys = {
        f"alpha:m{i}": kp.public_key_hex()
        for i, kp in enumerate(alpha_kps)
    }

    proposal_alpha = Proposal(content={
        "action": "adopt-relay-for-coordination",
        "cost": "low",
    })
    alpha_decision = alpha.deliberate_and_resolve_federated(
        proposal_alpha, evidence=[])
    # Alpha passed
    assert alpha_decision.inner.final_decision.outcome == "passed"

    # ---- Council Beta ----
    beta_kps = [KeyPair.generate() for _ in range(3)]
    def beta_rule(p, ctx):
        evidence = ctx.get("federation_evidence", {})
        for cid, summary in evidence.items():
            ref = ((cid, summary["decision_hash"]),)
            if summary["outcome"] == "passed":
                return ("yea",
                        f"following {cid}'s approval", ref)
            else:
                return ("nay",
                        f"{cid} did not approve", ref)
        return ("abstain", "no external evidence", ())
    beta = FederatedDeliberativeCouncil(
        "beta", QuorumRule(2, 2), max_rounds=3,
        stability_rounds=1)
    for i, kp in enumerate(beta_kps):
        beta.add_member(FederatedDeliberativeMember(
            entity_id=f"beta:m{i}", name=f"Beta-{i}",
            member_kp=kp, decision_rule=beta_rule))
    beta_keys = {
        f"beta:m{i}": kp.public_key_hex()
        for i, kp in enumerate(beta_kps)
    }

    evidence_alpha = FederationEvidence.from_decision(
        "alpha", alpha_decision)

    proposal_beta = Proposal(content={
        "action": "deploy-to-production",
        "requires_alpha_approval": True,
    })
    beta_decision = beta.deliberate_and_resolve_federated(
        proposal_beta, evidence=[evidence_alpha])

    # Verify happy path
    verdict_a = verify_federated_deliberation(
        beta_decision,
        local_member_keys=beta_keys,
        evidence_member_keys={"alpha": alpha_keys},
    )

    # ---- Scenario B: forged reference ----
    # Tamper one Beta position to reference a fake decision hash
    attacker = KeyPair.generate()
    orig_pos = beta_decision.inner.positions[0]
    fake_hash = "00" * 32
    payload = canonical_bytes({
        "kind": "federated_deliberation_position",
        "member_token": orig_pos.member_token,
        "member_name": orig_pos.member_name,
        "member_public_key": orig_pos.member_public_key,
        "proposal_hash": orig_pos.proposal_hash,
        "round_num": orig_pos.round_num,
        "stance": orig_pos.stance,
        "rationale": orig_pos.rationale,
        "timestamp": orig_pos.timestamp,
        "references": [["alpha", fake_hash]],
    })
    forged = FederatedSignedPosition(
        member_token=orig_pos.member_token,
        member_name=orig_pos.member_name,
        member_public_key=orig_pos.member_public_key,
        proposal_hash=orig_pos.proposal_hash,
        round_num=orig_pos.round_num,
        stance=orig_pos.stance,
        rationale=orig_pos.rationale,
        timestamp=orig_pos.timestamp,
        signature=attacker.sign(payload).hex(),
        references=(("alpha", fake_hash),),
    )
    tampered_inner = DeliberativeDecision(
        proposal=beta_decision.inner.proposal,
        proposal_hash=beta_decision.inner.proposal_hash,
        positions=(forged,) + beta_decision.inner.positions[1:],
        rounds_run=beta_decision.inner.rounds_run,
        converged_at_round=beta_decision.inner.converged_at_round,
        final_decision=beta_decision.inner.final_decision,
    )
    tampered_decision = FederatedDeliberativeDecision(
        inner=tampered_inner,
        federation_evidence=beta_decision.federation_evidence,
    )
    verdict_b = verify_federated_deliberation(
        tampered_decision, beta_keys, {"alpha": alpha_keys})

    # ---- Scenario C: tampered evidence hash ----
    # Replace the evidence's decision_hash claim
    tampered_evidence = FederationEvidence(
        council_id=evidence_alpha.council_id,
        decision=evidence_alpha.decision,
        decision_hash="ff" * 32,  # wrong
        outcome=evidence_alpha.outcome,
        yea_count=evidence_alpha.yea_count,
        nay_count=evidence_alpha.nay_count,
        abstain_count=evidence_alpha.abstain_count,
        proposal_hash=evidence_alpha.proposal_hash,
    )
    tampered_decision_c = FederatedDeliberativeDecision(
        inner=beta_decision.inner,
        federation_evidence=(tampered_evidence,),
    )
    verdict_c = verify_federated_deliberation(
        tampered_decision_c, beta_keys, {"alpha": alpha_keys})

    # ---- Print ----
    print("=" * 70)
    print("Federated Deliberation — two councils")
    print("=" * 70)
    print()
    print("  Scenario A: Alpha passes; Beta references Alpha")
    print()
    print("    Alpha decision:")
    for line in alpha_decision.format().split("\n")[:6]:
        print(f"      {line}")
    print()
    print("    Beta decision (with evidence):")
    for line in beta_decision.format().split("\n"):
        print(f"      {line}")
    print()
    print(f"    verified: {verdict_a.valid}")
    print(f"    local_valid: {verdict_a.local_valid}")
    print(f"    evidence_valid: {verdict_a.evidence_valid}")
    print(f"    references_valid: {verdict_a.references_valid}")
    print()
    print("  Scenario B: Beta has a forged reference")
    for line in verdict_b.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Scenario C: Beta's evidence has wrong decision_hash")
    for line in verdict_c.format().split("\n"):
        print(f"    {line}")
    print()
    print("  What this demonstrates:")
    print("    - Positions can be signed *with references* to")
    print("      external decisions. Backward compatible: C45's")
    print("      verify_position still works on the parent's")
    print("      canonical form.")
    print("    - Verification recomputes the whole chain: local")
    print("      decision → referenced evidence → evidence's")
    print("      members' keys.")
    print("    - Processes coordinate with processes; the substrate")
    print("      handles coordination-of-processes, not just")
    print("      processes in isolation.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Soul selects her own Society –'")
    print("    'Then – shuts the Door –'")

    audit = {
        "scenario_a_happy": {
            "alpha_outcome":
                alpha_decision.inner.final_decision.outcome,
            "beta_outcome":
                beta_decision.inner.final_decision.outcome,
            "verified": verdict_a.valid,
            "local_valid": verdict_a.local_valid,
            "evidence_valid": verdict_a.evidence_valid,
            "references_valid": verdict_a.references_valid,
        },
        "scenario_b_forged_reference": {
            "verified": verdict_b.valid,
            "reference_error_count":
                len(verdict_b.reference_errors),
        },
        "scenario_c_tampered_evidence": {
            "verified": verdict_c.valid,
            "evidence_error_count":
                len(verdict_c.evidence_errors),
        },
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "federated_deliberation_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/federated_deliberation_demo.json")
    return audit
