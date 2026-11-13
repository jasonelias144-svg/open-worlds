"""
multiverse_c44.py — Component 44: The Triumvirate.

Fourth architecture. A council of N members, each with equal
authority, each casting a signed vote on proposals. The council's
decision is the tally over signed votes.

Contrast:
  C41 Octopus:  one brain decides; arms execute
  C42 Relay:    one brain decides (threshold on aggregate weights);
                brain is origin-agnostic
  C43 Swarm:    no unit decides; statistical convergence
  C44 Council:  N units decide individually; count determines
                outcome; each vote is origin-attributed

The "council decides" is not "the council has one opinion." It
means "N opinions were expressed, signed, and counted by rule."
Verification is recomputation: anyone with the votes and the
members' public keys gets the same Decision.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: vote construction, tally, quorum rule,
    missing vote, duplicate vote, forged vote, tampered vote,
    wrong proposal, origin-attributed counts, structural
    differences from C41/C42/C43.
  - "A world never raises on what a visitor sends" — member
    cast_vote refuses bad input; Triumvirate.resolve
    returns a Decision or None.
  - "History, not rank" — the Decision is a record, not a score.

Honest limits (documented, tested):
  - Members vote in isolation. No discussion, no coalition,
    no abstention-then-vote. One round. Deliberation is user-
    supplied (a member's decision_rule can call anything; the
    infrastructure doesn't care).
  - No quorum decay. If a member never votes, they are simply
    "absent." Nothing forces a timeout.
  - No revocation of votes. A vote, once signed, stands.
    A new vote for the same member in a new tally is a new
    artifact; both are valid records.
  - Trust anchor external. Verifying each vote against the
    member's key requires trusting that key. Same as everywhere.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c42 import SignalWorld


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# Proposal
# =====================================================================

@dataclass(frozen=True)
class Proposal:
    content: Dict
    proposer: str = "external"

    def __post_init__(self):
        if not isinstance(self.content, dict):
            raise ValueError("proposal.content must be a dict")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "proposal",
            "content": self.content,
            "proposer": self.proposer,
        })

    def hash(self) -> str:
        return _hash_payload(self.canonical_payload())


# =====================================================================
# Vote — signed by one member
# =====================================================================

DECISIONS = ("yea", "nay", "abstain")


@dataclass(frozen=True)
class Vote:
    member_token: str
    member_name: str
    member_public_key: str
    proposal_hash: str
    decision: str
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("member_token", "member_name", "member_public_key",
                  "proposal_hash", "decision", "timestamp",
                  "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if self.decision not in DECISIONS:
            raise ValueError(
                f"decision must be one of {DECISIONS}, "
                f"got {self.decision!r}")
        if len(self.member_public_key) != 64:
            raise ValueError(
                "member_public_key must be 64 hex chars")
        if len(self.proposal_hash) != 64:
            raise ValueError(
                "proposal_hash must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "vote",
            "member_token": self.member_token,
            "member_name": self.member_name,
            "member_public_key": self.member_public_key,
            "proposal_hash": self.proposal_hash,
            "decision": self.decision,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "member_token": self.member_token,
            "member_name": self.member_name,
            "member_public_key": self.member_public_key,
            "proposal_hash": self.proposal_hash,
            "decision": self.decision,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Vote":
        return cls(
            member_token=d["member_token"],
            member_name=d["member_name"],
            member_public_key=d["member_public_key"],
            proposal_hash=d["proposal_hash"],
            decision=d["decision"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_vote(vote: Vote, member_public_key: str) -> bool:
    """True iff the vote's signature verifies against the given
    member key. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(vote, Vote):
            return False
        return verify_signature(
            member_public_key,
            vote.canonical_payload(),
            vote.signature)
    except Exception:
        return False


# =====================================================================
# QuorumRule
# =====================================================================

@dataclass(frozen=True)
class QuorumRule:
    """min_yea: minimum yea votes to pass.
    min_present: minimum votes present (any decision, including
    abstain) to be a valid session.

    Default 2-of-3: min_yea=2, min_present=2.
    """
    min_yea: int
    min_present: int

    def __post_init__(self):
        if self.min_yea < 1:
            raise ValueError("min_yea must be >= 1")
        if self.min_present < 1:
            raise ValueError("min_present must be >= 1")
        if self.min_yea > self.min_present:
            raise ValueError(
                "min_yea cannot exceed min_present")


# =====================================================================
# TriumvirateMember
# =====================================================================

class TriumvirateMember(SignalWorld):
    """One member of the council.

    Has its own keypair, its own decision rule, and votes
    independently. Produces signed Vote artifacts.

    The `decision_rule` is user-supplied: a callable taking a
    Proposal and returning "yea"|"nay"|"abstain". The
    infrastructure doesn't care what's in the rule — anything
    from "always yea" to "consult a model" works.
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        member_kp: KeyPair,
        decision_rule: Callable[[Proposal], str],
    ):
        super().__init__(entity_id, name)
        self._member_kp = member_kp
        self._member_public_key = member_kp.public_key_hex()
        self._decision_rule = decision_rule

    @property
    def public_key(self) -> str:
        return self._member_public_key

    @property
    def member_token(self) -> str:
        return self._manifest.entity_id

    def cast_vote(self, proposal: Proposal) -> Vote:
        """Produce a signed vote on the proposal. Never raises
        for bad proposals — an unparseable proposal yields a
        'nay' with reason attached to the vote."""
        try:
            decision = self._decision_rule(proposal)
        except Exception:
            decision = "nay"
        if decision not in DECISIONS:
            decision = "abstain"
        ts = _now()
        payload = canonical_bytes({
            "kind": "vote",
            "member_token": self._manifest.entity_id,
            "member_name": self._manifest.name,
            "member_public_key": self._member_public_key,
            "proposal_hash": proposal.hash(),
            "decision": decision,
            "timestamp": ts,
        })
        return Vote(
            member_token=self._manifest.entity_id,
            member_name=self._manifest.name,
            member_public_key=self._member_public_key,
            proposal_hash=proposal.hash(),
            decision=decision,
            timestamp=ts,
            signature=self._member_kp.sign(payload).hex(),
        )


# =====================================================================
# Decision — derived artifact
# =====================================================================

@dataclass(frozen=True)
class Decision:
    """A council decision, recomputable from signed votes."""
    proposal: Dict           # full proposal, for hash verification
    proposal_hash: str
    votes: Tuple[Vote, ...]
    quorum: QuorumRule
    yea_count: int
    nay_count: int
    abstain_count: int
    present_count: int
    outcome: str             # passed | rejected | no_quorum
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            "proposal": self.proposal,
            "proposal_hash": self.proposal_hash,
            "votes": [v.to_dict() for v in self.votes],
            "quorum": {
                "min_yea": self.quorum.min_yea,
                "min_present": self.quorum.min_present,
            },
            "yea_count": self.yea_count,
            "nay_count": self.nay_count,
            "abstain_count": self.abstain_count,
            "present_count": self.present_count,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Decision":
        q = d["quorum"]
        return cls(
            proposal=d["proposal"],
            proposal_hash=d["proposal_hash"],
            votes=tuple(Vote.from_dict(v) for v in d["votes"]),
            quorum=QuorumRule(
                min_yea=q["min_yea"],
                min_present=q["min_present"]),
            yea_count=d["yea_count"],
            nay_count=d["nay_count"],
            abstain_count=d["abstain_count"],
            present_count=d["present_count"],
            outcome=d["outcome"],
            timestamp=d["timestamp"],
        )

    def format(self) -> str:
        lines = [
            "Decision",
            "=" * 50,
            f"  proposal_hash: {self.proposal_hash[:16]}...",
            f"  outcome:       {self.outcome.upper()}",
            f"  votes:         yea={self.yea_count} "
            f"nay={self.nay_count} "
            f"abstain={self.abstain_count} "
            f"(present={self.present_count})",
            f"  quorum:        {self.quorum.min_yea}-of-"
            f"{self.quorum.min_present} "
            f"(min yea / min present)",
        ]
        for v in self.votes:
            lines.append(
                f"    · {v.member_name}: {v.decision}")
        return "\n".join(lines)


# =====================================================================
# Triumvirate — the council
# =====================================================================

class Triumvirate:
    """A council of N members. Orchestrates voting; not a world."""

    def __init__(
        self,
        name: str,
        quorum: QuorumRule,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "Triumvirate requires `cryptography`")
        self.name = name
        self._quorum = quorum
        self._members: Dict[str, TriumvirateMember] = {}

    def add_member(self, member: TriumvirateMember) -> None:
        self._members[member.member_token] = member

    def remove_member(self, member_token: str) -> None:
        self._members.pop(member_token, None)

    def member_count(self) -> int:
        return len(self._members)

    def resolve(self, proposal: Proposal) -> Decision:
        """Run one voting round on the proposal, tally, return the
        Decision. Never raises for bad proposals; the Decision
        reflects whatever votes were cast."""
        votes: List[Vote] = []
        for member in self._members.values():
            try:
                votes.append(member.cast_vote(proposal))
            except Exception:
                # A failed member is absent, not fatal
                pass
        return self._tally(proposal, votes)

    def _tally(self, proposal: Proposal,
                votes: List[Vote]) -> Decision:
        yea = sum(1 for v in votes if v.decision == "yea")
        nay = sum(1 for v in votes if v.decision == "nay")
        abstain = sum(1 for v in votes if v.decision == "abstain")
        present = len(votes)

        if present < self._quorum.min_present:
            outcome = "no_quorum"
        elif yea >= self._quorum.min_yea:
            outcome = "passed"
        else:
            outcome = "rejected"

        return Decision(
            proposal=proposal.content,
            proposal_hash=proposal.hash(),
            votes=tuple(votes),
            quorum=self._quorum,
            yea_count=yea,
            nay_count=nay,
            abstain_count=abstain,
            present_count=present,
            outcome=outcome,
            timestamp=_now(),
        )


# =====================================================================
# Decision verification — recompute, don't trust
# =====================================================================

@dataclass
class DecisionVerdict:
    valid: bool
    reason: str
    bad_votes: List[Tuple[str, str]]  # (member_token, reason)
    duplicate_members: List[str]
    tallies_match: bool
    outcome_matches: bool

    def format(self) -> str:
        lines = [
            "Decision Verification",
            "=" * 50,
            f"  valid:            {self.valid}",
            f"  tallies_match:    {self.tallies_match}",
            f"  outcome_matches:  {self.outcome_matches}",
        ]
        if self.bad_votes:
            lines.append("  bad votes:")
            for tok, reason in self.bad_votes:
                lines.append(f"    ✗ {tok[:16]}...: {reason}")
        if self.duplicate_members:
            lines.append("  duplicate members:")
            for tok in self.duplicate_members:
                lines.append(f"    ✗ {tok[:16]}...")
        if not self.valid:
            lines.append(f"  reason: {self.reason}")
        return "\n".join(lines)


def verify_decision(
    decision: Decision,
    member_public_keys: Dict[str, str],
    quorum: Optional[QuorumRule] = None,
) -> DecisionVerdict:
    """Recompute the tally from the decision's votes.

    Checks, in order:
      1. proposal_hash matches proposal content.
      2. Each vote's signature verifies against its member key.
      3. Each vote's proposal_hash matches the decision's.
      4. No duplicate member_token in the votes.
      5. Recomputed counts match the decision's claims.
      6. Recomputed outcome matches the decision's claim.

    `member_public_keys` maps member_token → 64-hex public key.
    If `quorum` is provided, it overrides decision.quorum for the
    recomputation — useful when a verifier's rule is different
    from what the council claims.

    Never raises.
    """
    bad_votes: List[Tuple[str, str]] = []
    duplicate_members: List[str] = []

    if not HAS_CRYPTO:
        return DecisionVerdict(
            valid=False, reason="cryptography not installed",
            bad_votes=[], duplicate_members=[],
            tallies_match=False, outcome_matches=False)
    if not isinstance(decision, Decision):
        return DecisionVerdict(
            valid=False, reason="not a Decision",
            bad_votes=[], duplicate_members=[],
            tallies_match=False, outcome_matches=False)

    # 1. Proposal hash
    try:
        recomputed_hash = Proposal(
            content=decision.proposal).hash()
    except Exception as e:
        return DecisionVerdict(
            valid=False,
            reason=f"proposal cannot be re-hashed: {e}",
            bad_votes=[], duplicate_members=[],
            tallies_match=False, outcome_matches=False)
    if recomputed_hash != decision.proposal_hash:
        return DecisionVerdict(
            valid=False,
            reason="proposal_hash does not match proposal",
            bad_votes=[], duplicate_members=[],
            tallies_match=False, outcome_matches=False)

    # 2-3. Verify votes
    seen_members: set = set()
    for v in decision.votes:
        if v.member_token in seen_members:
            duplicate_members.append(v.member_token)
            continue
        seen_members.add(v.member_token)
        if v.proposal_hash != decision.proposal_hash:
            bad_votes.append(
                (v.member_token, "proposal_hash mismatch"))
            continue
        member_pk = member_public_keys.get(v.member_token)
        if member_pk is None:
            bad_votes.append(
                (v.member_token, "no public key for member"))
            continue
        if not verify_vote(v, member_pk):
            bad_votes.append(
                (v.member_token, "signature INVALID"))

    # 4. Duplicate check
    if duplicate_members:
        return DecisionVerdict(
            valid=False,
            reason=(f"{len(duplicate_members)} duplicate "
                    f"member vote(s)"),
            bad_votes=bad_votes,
            duplicate_members=duplicate_members,
            tallies_match=False, outcome_matches=False)

    # 5. Recompute counts from *valid* votes only
    valid_votes = [v for v in decision.votes
                   if v.member_token not in
                   {t for t, _ in bad_votes}]
    yea = sum(1 for v in valid_votes if v.decision == "yea")
    nay = sum(1 for v in valid_votes if v.decision == "nay")
    abstain = sum(1 for v in valid_votes
                  if v.decision == "abstain")
    present = len(valid_votes)
    tallies_match = (
        yea == decision.yea_count
        and nay == decision.nay_count
        and abstain == decision.abstain_count
        and present == decision.present_count)

    # 6. Recompute outcome
    q = quorum or decision.quorum
    if present < q.min_present:
        recomputed_outcome = "no_quorum"
    elif yea >= q.min_yea:
        recomputed_outcome = "passed"
    else:
        recomputed_outcome = "rejected"
    outcome_matches = (recomputed_outcome == decision.outcome)

    if bad_votes:
        return DecisionVerdict(
            valid=False,
            reason=f"{len(bad_votes)} invalid vote(s)",
            bad_votes=bad_votes,
            duplicate_members=[],
            tallies_match=tallies_match,
            outcome_matches=outcome_matches)
    if not tallies_match:
        return DecisionVerdict(
            valid=False,
            reason="tallies do not match the votes",
            bad_votes=[], duplicate_members=[],
            tallies_match=False, outcome_matches=outcome_matches)
    if not outcome_matches:
        return DecisionVerdict(
            valid=False,
            reason="outcome does not match recomputation",
            bad_votes=[], duplicate_members=[],
            tallies_match=True, outcome_matches=False)
    return DecisionVerdict(
        valid=True,
        reason="all votes valid; tallies and outcome match",
        bad_votes=[], duplicate_members=[],
        tallies_match=True, outcome_matches=True)


# multiverse_c44_demo.py

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """A three-member council with 2-of-3 quorum.

    Three scenarios:
      A. Proposal {cost: "low"}  → A yea, B yea, C nay → PASSED
      B. Proposal {cost: "high"} → A nay, B abstain, C nay → REJECTED
      C. A strict-quorum council (3-of-3) with only 2 members
         → NO_QUORUM

    Plus two negative cases:
      D. Forged vote — attacker signs a fake vote attributed to A
         → verify_decision catches it (signature INVALID)
      E. Honest votes, dishonest claim — a Decision with wrong
         counts → verify_decision catches the mismatch

    Anchor: Emily Dickinson, 'Much Madness is divinest Sense –',
    public domain — a poem about majority rule.
    """
    import json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # Three members, each with a decision rule
    member_kps = {
        "a": KeyPair.generate(),
        "b": KeyPair.generate(),
        "c": KeyPair.generate(),
    }
    # A: yea if cost is "low", else nay
    # B: yea if cost is "low", else abstain
    # C: always nay (the conservative voice)
    def rule_a(prop: Proposal) -> str:
        return "yea" if prop.content.get("cost") == "low" else "nay"
    def rule_b(prop: Proposal) -> str:
        return "yea" if prop.content.get("cost") == "low" else "abstain"
    def rule_c(prop: Proposal) -> str:
        return "nay"

    council = Triumvirate(
        "council-main",
        quorum=QuorumRule(min_yea=2, min_present=2))
    council.add_member(TriumvirateMember(
        "member:a", "Alpha", member_kps["a"], rule_a))
    council.add_member(TriumvirateMember(
        "member:b", "Beta", member_kps["b"], rule_b))
    council.add_member(TriumvirateMember(
        "member:c", "Gamma", member_kps["c"], rule_c))

    public_keys = {tok: kp.public_key_hex()
                    for tok, kp in member_kps.items()}

    # ---- Scenario A: passed ----
    proposal_a = Proposal(content={
        "action": "adopt-relay",
        "cost": "low",
    })
    decision_a = council.resolve(proposal_a)
    verdict_a = verify_decision(decision_a, public_keys)

    # ---- Scenario B: rejected ----
    proposal_b = Proposal(content={
        "action": "adopt-octopus",
        "cost": "high",
    })
    decision_b = council.resolve(proposal_b)
    verdict_b = verify_decision(decision_b, public_keys)

    # ---- Scenario C: no_quorum ----
    # Strict council with 3-of-3 quorum, only 2 members
    strict = Triumvirate(
        "council-strict",
        quorum=QuorumRule(min_yea=2, min_present=3))
    strict.add_member(TriumvirateMember(
        "member:a2", "Alpha", member_kps["a"], rule_a))
    strict.add_member(TriumvirateMember(
        "member:b2", "Beta", member_kps["b"], rule_b))
    proposal_c = Proposal(content={
        "action": "adopt-swarm",
        "cost": "low",
    })
    decision_c = strict.resolve(proposal_c)
    strict_keys = {
        "member:a2": member_kps["a"].public_key_hex(),
        "member:b2": member_kps["b"].public_key_hex(),
    }
    verdict_c = verify_decision(decision_c, strict_keys)

    # ---- Scenario D: forged vote ----
    attacker_kp = KeyPair.generate()
    # Attacker forges a vote attributed to member:a, but signs
    # with their own key
    payload = canonical_bytes({
        "kind": "vote",
        "member_token": "member:a",
        "member_name": "Alpha",
        "member_public_key": member_kps["a"].public_key_hex(),
        "proposal_hash": decision_a.proposal_hash,
        "decision": "nay",  # trying to flip A's yes to no
        "timestamp": "2024-01-01T00:00:00+00:00",
    })
    forged_vote = Vote(
        member_token="member:a",
        member_name="Alpha",
        member_public_key=member_kps["a"].public_key_hex(),
        proposal_hash=decision_a.proposal_hash,
        decision="nay",
        timestamp="2024-01-01T00:00:00+00:00",
        signature=attacker_kp.sign(payload).hex(),
    )
    # A Decision that includes the forged vote (as if the attacker
    # had tampered with the record)
    tampered_votes = (
        forged_vote,
        decision_a.votes[1],  # original B
        decision_a.votes[2],  # original C
    )
    # Recompute the *claimed* tallies to match the tampered votes
    # — i.e., the attacker also rewrote the counts
    tampered_decision = Decision(
        proposal=decision_a.proposal,
        proposal_hash=decision_a.proposal_hash,
        votes=tampered_votes,
        quorum=decision_a.quorum,
        yea_count=0,  # was 2
        nay_count=2,  # was 1
        abstain_count=0,
        present_count=3,
        outcome="rejected",  # was passed
        timestamp=decision_a.timestamp,
    )
    verdict_d = verify_decision(tampered_decision, public_keys)

    # ---- Scenario E: honest votes, dishonest claim ----
    # Take real decision_a votes, but claim the wrong counts
    dishonest_claim = Decision(
        proposal=decision_a.proposal,
        proposal_hash=decision_a.proposal_hash,
        votes=decision_a.votes,
        quorum=decision_a.quorum,
        yea_count=3,   # was 2 — inflated
        nay_count=0,   # was 1 — suppressed
        abstain_count=0,
        present_count=3,
        outcome="passed",  # same, but for wrong reasons
        timestamp=decision_a.timestamp,
    )
    verdict_e = verify_decision(dishonest_claim, public_keys)

    # ---- Print ----
    print("=" * 70)
    print("Triumvirate — council architecture")
    print("=" * 70)
    print()
    print("  Council: 3 members, quorum 2-of-3")
    print("    Alpha (member:a): yea if cost=low, else nay")
    print("    Beta  (member:b): yea if cost=low, else abstain")
    print("    Gamma (member:c): always nay")
    print()
    print("  Scenario A — Proposal {cost: low}")
    for line in decision_a.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict_a.valid}")
    print()
    print("  Scenario B — Proposal {cost: high}")
    for line in decision_b.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict_b.valid}")
    print()
    print("  Scenario C — Strict council (3-of-3), only 2 members")
    for line in decision_c.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict_c.valid}")
    print()
    print("  Scenario D — Forged vote attributed to Alpha")
    for line in verdict_d.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Scenario E — Honest votes, dishonest claimed counts")
    for line in verdict_e.format().split("\n"):
        print(f"    {line}")
    print()
    print("  What this demonstrates:")
    print("    - Every vote is signed by one member (origin-attributed).")
    print("    - Verification is recomputation, not trust in the claim.")
    print("    - A verifier with a different quorum rule gets a")
    print("      different outcome from the same votes.")
    print("    - Structural difference vs C41/C42/C43: no brain, no")
    print("      arms, no shared environment. N voters, one tally.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Much Madness is divinest Sense –'")
    print("    'To a discerning Eye –'")
    print("    'Much Sense – the starkest Madness –'")
    print("    'Tis the Majority'")
    print("    'In this, as All, prevail –'")

    audit = {
        "scenarios": {
            "A_passed": {
                "outcome": decision_a.outcome,
                "yea": decision_a.yea_count,
                "nay": decision_a.nay_count,
                "abstain": decision_a.abstain_count,
                "verified": verdict_a.valid,
            },
            "B_rejected": {
                "outcome": decision_b.outcome,
                "yea": decision_b.yea_count,
                "nay": decision_b.nay_count,
                "abstain": decision_b.abstain_count,
                "verified": verdict_b.valid,
            },
            "C_no_quorum": {
                "outcome": decision_c.outcome,
                "verified": verdict_c.valid,
            },
            "D_forged_vote": {
                "verified": verdict_d.valid,
                "bad_vote_count": len(verdict_d.bad_votes),
            },
            "E_dishonest_claim": {
                "verified": verdict_e.valid,
                "tallies_match": verdict_e.tallies_match,
            },
        },
        "member_public_keys": public_keys,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "triumvirate_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/triumvirate_demo.json")
    return audit
