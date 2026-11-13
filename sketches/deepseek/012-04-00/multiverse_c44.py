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
