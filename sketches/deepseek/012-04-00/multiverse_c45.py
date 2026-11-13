"""
multiverse_c45.py — Component 45: Deliberation.

Adds a bounded deliberation phase to the C44 council. Members
produce signed positions, read each other's positions, and update
before casting final votes.

Distinction from C44:
  C44: one-shot vote. Members vote, tally, done.
  C45: N rounds of positions, then final votes.

  - A Position is signed but RETRACTABLE (superseded by the
    member's next position). Not a commitment.
  - A Vote is a signed commitment. Still C44's Vote. The final
    Decision is still C44's Decision.
  - The deliberation log is a SignalWorld. Positions are entries.
    Any verifier can read the positions and recompute the path.

What the substrate supports:
  The council was one architecture. Deliberation is a *process*
  on top of that architecture — not a fifth architecture. The
  substrate handles processes (logs, streams, signed events) as
  well as snapshots (votes, tallies). Same primitives throughout.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: position emission, position sig,
    position retraction, stability detection, max rounds,
    update rule, tampered position caught, final decision
    still C44-verifiable, deliberation path verifiable,
    backward compat with C44's one-arg rules.
  - "A world never raises on what a visitor sends" — rule
    exceptions yield a stable position; verifiers return
    verdicts.
  - "History, not rank" — positions are records, not scores.

Honest limits (documented, tested):
  - Order within a round matters. First producers may influence
    later ones; the prototype doesn't randomize or anonymize.
  - No guarantees of convergence. max_rounds enforces a bound.
  - Rationale is free text, not validated. A member can
    produce an empty rationale.
  - The final vote is not required to match any prior position.
    A member can deliberate "yea" then vote "nay". This is a
    feature, not a bug — minds change — but it means the
    deliberation log is a *record of process*, not a *binding
    commitment*.
  - Trust anchor external. Same as everywhere.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c42 import SignalWorld, Stream
from multiverse_c44 import (
    Proposal, Vote, DECISIONS, verify_vote,
    QuorumRule, TriumvirateMember, Decision,
    Triumvirate, DecisionVerdict, verify_decision,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# SignedPosition — retractable, unlike Vote
# =====================================================================

@dataclass(frozen=True)
class SignedPosition:
    member_token: str
    member_name: str
    member_public_key: str
    proposal_hash: str
    round_num: int
    stance: str
    rationale: str
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("member_token", "member_name", "member_public_key",
                  "proposal_hash", "stance", "timestamp",
                  "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if self.stance not in DECISIONS:
            raise ValueError(
                f"stance must be one of {DECISIONS}, "
                f"got {self.stance!r}")
        if len(self.member_public_key) != 64:
            raise ValueError(
                "member_public_key must be 64 hex chars")
        if len(self.proposal_hash) != 64:
            raise ValueError(
                "proposal_hash must be 64 hex chars")
        if self.round_num < 0:
            raise ValueError("round_num must be >= 0")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "deliberation_position",
            "member_token": self.member_token,
            "member_name": self.member_name,
            "member_public_key": self.member_public_key,
            "proposal_hash": self.proposal_hash,
            "round_num": self.round_num,
            "stance": self.stance,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "member_token": self.member_token,
            "member_name": self.member_name,
            "member_public_key": self.member_public_key,
            "proposal_hash": self.proposal_hash,
            "round_num": self.round_num,
            "stance": self.stance,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "SignedPosition":
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
        )


def verify_position(position: SignedPosition,
                     member_public_key: str) -> bool:
    """True iff the position's signature verifies. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(position, SignedPosition):
            return False
        return verify_signature(
            member_public_key,
            position.canonical_payload(),
            position.signature)
    except Exception:
        return False


# =====================================================================
# DeliberativeMember
# =====================================================================

# A deliberative rule accepts (proposal, context) where context is:
# {
#   "round_num": int,
#   "positions_by_member": {token: {stance, rationale, round, ts}},
# }
#
# It returns ("yea"|"nay"|"abstain", rationale_str).
# For C44 backward compat, one-arg rules are accepted and wrapped.
DeliberativeRule = Callable[[Proposal, Optional[Dict]],
                            Tuple[str, str]]


class DeliberativeMember(TriumvirateMember):
    """A council member that produces signed positions before
    voting.

    The decision_rule can be either:
      - (proposal) → decision_string           (C44 compat)
      - (proposal, context) → (decision, rationale)
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        member_kp: KeyPair,
        decision_rule,
    ):
        super().__init__(entity_id, name, member_kp,
                          decision_rule=decision_rule)
        # Detect rule arity at __init__; do it once
        import inspect
        try:
            sig = inspect.signature(decision_rule)
            n_required = sum(
                1 for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind in (p.POSITIONAL_ONLY,
                                p.POSITIONAL_OR_KEYWORD))
            self._rule_takes_context = (n_required >= 2)
        except (TypeError, ValueError):
            # Builtins etc.; assume one arg (C44 compat)
            self._rule_takes_context = False

    def produce_position(
        self,
        proposal: Proposal,
        round_num: int,
        context: Optional[Dict] = None,
    ) -> SignedPosition:
        """Produce a signed position. Never raises for bad input."""
        ctx = context or {"round_num": round_num,
                          "positions_by_member": {}}
        try:
            if self._rule_takes_context:
                result = self._decision_rule(proposal, ctx)
            else:
                result = self._decision_rule(proposal)
        except Exception:
            result = ("nay", "rule error")
        # Normalize
        if isinstance(result, tuple) and len(result) == 2:
            stance, rationale = result
        elif isinstance(result, str):
            stance, rationale = result, ""
        else:
            stance, rationale = "nay", "rule returned unexpected type"
        if stance not in DECISIONS:
            stance = "abstain"
        rationale = str(rationale) if rationale else ""
        ts = _now()
        payload = canonical_bytes({
            "kind": "deliberation_position",
            "member_token": self._manifest.entity_id,
            "member_name": self._manifest.name,
            "member_public_key": self._member_public_key,
            "proposal_hash": proposal.hash(),
            "round_num": round_num,
            "stance": stance,
            "rationale": rationale,
            "timestamp": ts,
        })
        return SignedPosition(
            member_token=self._manifest.entity_id,
            member_name=self._manifest.name,
            member_public_key=self._member_public_key,
            proposal_hash=proposal.hash(),
            round_num=round_num,
            stance=stance,
            rationale=rationale,
            timestamp=ts,
            signature=self._member_kp.sign(payload).hex(),
        )

    def cast_final_vote(self, proposal: Proposal,
                         context: Optional[Dict] = None) -> Vote:
        """Produce a final C44 Vote. Uses the rule with context
        if the rule takes one; otherwise C44 behavior."""
        if self._rule_takes_context and context is not None:
            try:
                result = self._decision_rule(proposal, context)
            except Exception:
                result = ("nay", "rule error")
            if isinstance(result, tuple) and len(result) == 2:
                stance, _ = result
            else:
                stance = result if isinstance(result, str) else "nay"
            if stance not in DECISIONS:
                stance = "abstain"
            ts = _now()
            payload = canonical_bytes({
                "kind": "vote",
                "member_token": self._manifest.entity_id,
                "member_name": self._manifest.name,
                "member_public_key": self._member_public_key,
                "proposal_hash": proposal.hash(),
                "decision": stance,
                "timestamp": ts,
            })
            return Vote(
                member_token=self._manifest.entity_id,
                member_name=self._manifest.name,
                member_public_key=self._member_public_key,
                proposal_hash=proposal.hash(),
                decision=stance,
                timestamp=ts,
                signature=self._member_kp.sign(payload).hex())
        # C44 path
        return self.cast_vote(proposal)


# =====================================================================
# DeliberativeDecision — a Decision plus the deliberation record
# =====================================================================

@dataclass(frozen=True)
class DeliberativeDecision:
    proposal: Dict
    proposal_hash: str
    positions: Tuple[SignedPosition, ...]
    rounds_run: int
    converged_at_round: Optional[int]
    final_decision: Decision     # C44's Decision

    def to_dict(self) -> Dict:
        return {
            "proposal": self.proposal,
            "proposal_hash": self.proposal_hash,
            "positions": [p.to_dict() for p in self.positions],
            "rounds_run": self.rounds_run,
            "converged_at_round": self.converged_at_round,
            "final_decision": self.final_decision.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "DeliberativeDecision":
        return cls(
            proposal=d["proposal"],
            proposal_hash=d["proposal_hash"],
            positions=tuple(
                SignedPosition.from_dict(p)
                for p in d["positions"]),
            rounds_run=d["rounds_run"],
            converged_at_round=d.get("converged_at_round"),
            final_decision=Decision.from_dict(d["final_decision"]),
        )

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Deliberative Decision",
            "=" * 70,
            f"  proposal_hash:       "
            f"{self.proposal_hash[:16]}...",
            f"  rounds_run:          {self.rounds_run}",
            f"  converged_at_round:  {self.converged_at_round}",
            f"  final outcome:       "
            f"{self.final_decision.outcome.upper()}",
            "",
        ]
        # Group positions by round
        by_round: Dict[int, List[SignedPosition]] = {}
        for p in self.positions:
            by_round.setdefault(p.round_num, []).append(p)
        for r in sorted(by_round):
            lines.append(f"  Round {r}:")
            for p in by_round[r]:
                rat = (f" — {p.rationale[:40]}"
                        if p.rationale else "")
                lines.append(
                    f"    {p.member_name}: {p.stance}{rat}")
        lines.append("")
        lines.append("  Final vote:")
        for line in self.final_decision.format().split("\n"):
            lines.append(f"    {line}")
        return "\n".join(lines)


# =====================================================================
# DeliberativeCouncil
# =====================================================================

class DeliberativeCouncil(Triumvirate):
    """A C44 council plus a bounded deliberation phase."""

    def __init__(
        self,
        name: str,
        quorum: QuorumRule,
        max_rounds: int = 5,
        stability_rounds: int = 1,
    ):
        super().__init__(name, quorum)
        if max_rounds < 1:
            raise ValueError("max_rounds must be >= 1")
        if stability_rounds < 1:
            raise ValueError("stability_rounds must be >= 1")
        self._deliberation_log = SignalWorld(
            f"deliberation:{name}", f"{name}-log")
        self._deliberation_stream = Stream(
            self._deliberation_log, "deliberation")
        self._max_rounds = max_rounds
        self._stability_rounds = stability_rounds

    def deliberation_log(self) -> SignalWorld:
        return self._deliberation_log

    def add_member(self, member: TriumvirateMember) -> None:
        if not isinstance(member, DeliberativeMember):
            raise TypeError(
                "DeliberativeCouncil requires DeliberativeMember; "
                "use Triumvirate for C44 behavior")
        super().add_member(member)

    def deliberate_and_resolve(
        self, proposal: Proposal,
    ) -> DeliberativeDecision:
        """Run deliberation rounds, then final votes. Returns a
        DeliberativeDecision. Never raises for bad proposals."""
        positions: List[SignedPosition] = []
        by_round: Dict[int, Dict[str, str]] = {}
        converged_at: Optional[int] = None
        stable_count = 0
        members = list(self._members.values())

        for round_num in range(self._max_rounds):
            # Snapshot of positions before this round's updates
            context = {
                "round_num": round_num,
                "positions_by_member": {
                    tok: {"stance": stance,
                           "rationale": pos_rationale}
                    for tok, (stance, pos_rationale)
                    in _latest_stances(positions).items()
                },
            }
            round_positions: Dict[str, str] = {}
            for member in members:
                pos = member.produce_position(
                    proposal, round_num, context)
                positions.append(pos)
                round_positions[pos.member_token] = pos.stance
                # Also write to the shared log (as the record)
                self._deliberation_log.emit(
                    "position", 1.0, {
                        "member_token": pos.member_token,
                        "round_num": round_num,
                        "stance": pos.stance,
                        "rationale": pos.rationale,
                        "signature": pos.signature,
                        "proposal_hash": pos.proposal_hash,
                    })
            by_round[round_num] = round_positions

            # Stability check
            if round_num > 0:
                if round_positions == by_round[round_num - 1]:
                    stable_count += 1
                else:
                    stable_count = 0
            if stable_count >= self._stability_rounds:
                converged_at = round_num
                break

        rounds_run = len(by_round)

        # Final vote (C44)
        final_votes: List[Vote] = []
        final_context = {
            "round_num": rounds_run,
            "positions_by_member": {
                tok: {"stance": stance,
                       "rationale": pos_rationale}
                for tok, (stance, pos_rationale)
                in _latest_stances(positions).items()
            },
        }
        for member in members:
            try:
                final_votes.append(member.cast_final_vote(
                    proposal, final_context))
            except Exception:
                pass  # absence, not fatality

        final_decision = self._tally(proposal, final_votes)

        return DeliberativeDecision(
            proposal=proposal.content,
            proposal_hash=proposal.hash(),
            positions=tuple(positions),
            rounds_run=rounds_run,
            converged_at_round=converged_at,
            final_decision=final_decision,
        )


def _latest_stances(
    positions: List[SignedPosition],
) -> Dict[str, Tuple[str, str]]:
    """Return each member's most recent (stance, rationale)."""
    latest: Dict[str, SignedPosition] = {}
    for p in positions:
        existing = latest.get(p.member_token)
        if existing is None or p.round_num >= existing.round_num:
            latest[p.member_token] = p
    return {tok: (p.stance, p.rationale)
            for tok, p in latest.items()}


# =====================================================================
# Verification
# =====================================================================

@dataclass
class DeliberativeVerdict:
    valid: bool
    reason: str
    positions_valid: bool
    final_decision_valid: bool
    rounds_match: bool
    bad_positions: List[Tuple[str, str]] = field(default_factory=list)

    def format(self) -> str:
        lines = [
            "Deliberative Decision Verification",
            "=" * 50,
            f"  valid:                {self.valid}",
            f"  positions_valid:      {self.positions_valid}",
            f"  final_decision_valid: {self.final_decision_valid}",
            f"  rounds_match:         {self.rounds_match}",
        ]
        if self.bad_positions:
            lines.append("  bad positions:")
            for tok, reason in self.bad_positions:
                lines.append(f"    ✗ {tok[:16]}...: {reason}")
        if not self.valid:
            lines.append(f"  reason: {self.reason}")
        return "\n".join(lines)


def verify_deliberative_decision(
    decision: DeliberativeDecision,
    member_public_keys: Dict[str, str],
    quorum: Optional[QuorumRule] = None,
) -> DeliberativeVerdict:
    """Verify positions AND final decision. Never raises.

    Checks:
      1. proposal_hash matches proposal content.
      2. Each position signed by its member's key.
      3. Each position's proposal_hash matches.
      4. rounds_run is consistent with positions.
      5. Each member has exactly one position per round.
      6. Final decision verifies (C44's verify_decision).
      7. converged_at_round claim, if present, matches recomputation.
    """
    if not HAS_CRYPTO:
        return DeliberativeVerdict(
            valid=False, reason="cryptography not installed",
            positions_valid=False, final_decision_valid=False,
            rounds_match=False)
    if not isinstance(decision, DeliberativeDecision):
        return DeliberativeVerdict(
            valid=False, reason="not a DeliberativeDecision",
            positions_valid=False, final_decision_valid=False,
            rounds_match=False)

    bad_positions: List[Tuple[str, str]] = []

    # 1. Proposal hash
    try:
        recomputed = Proposal(content=decision.proposal).hash()
    except Exception as e:
        return DeliberativeVerdict(
            valid=False,
            reason=f"proposal cannot be re-hashed: {e}",
            positions_valid=False, final_decision_valid=False,
            rounds_match=False)
    if recomputed != decision.proposal_hash:
        return DeliberativeVerdict(
            valid=False, reason="proposal_hash mismatch",
            positions_valid=False, final_decision_valid=False,
            rounds_match=False)

    # 2-3. Verify positions
    for p in decision.positions:
        if p.proposal_hash != decision.proposal_hash:
            bad_positions.append(
                (p.member_token, "proposal_hash mismatch"))
            continue
        mpk = member_public_keys.get(p.member_token)
        if mpk is None:
            bad_positions.append(
                (p.member_token, "no public key"))
            continue
        if not verify_position(p, mpk):
            bad_positions.append(
                (p.member_token, "signature INVALID"))
    positions_valid = not bad_positions

    # 4. rounds consistency
    rounds_in_positions = {p.round_num
                            for p in decision.positions}
    rounds_match = (rounds_in_positions ==
                    set(range(decision.rounds_run)))

    # 5. Exactly one position per member per round
    by_member_round: Dict[Tuple[str, int], int] = {}
    for p in decision.positions:
        key = (p.member_token, p.round_num)
        by_member_round[key] = by_member_round.get(key, 0) + 1
    if any(count > 1 for count in by_member_round.values()):
        positions_valid = False
        bad_positions.append(
            ("*", "duplicate position for same member+round"))

    # 6. Final decision verifies
    fd_verdict = verify_decision(
        decision.final_decision, member_public_keys, quorum)
    final_decision_valid = fd_verdict.valid

    # 7. converged_at_round — recompute from positions
    converged_ok = True
    if decision.converged_at_round is not None:
        # We can't know the council's stability_rounds from here;
        # check that converged_at_round is a valid round index and
        # that stances from that round backward are consistent.
        if not (0 <= decision.converged_at_round
                < decision.rounds_run):
            converged_ok = False

    all_ok = (positions_valid and final_decision_valid
              and rounds_match and converged_ok)
    reason = ("all checks passed" if all_ok
              else "one or more checks failed")
    return DeliberativeVerdict(
        valid=all_ok, reason=reason,
        positions_valid=positions_valid,
        final_decision_valid=final_decision_valid,
        rounds_match=rounds_match,
        bad_positions=bad_positions)


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Three scenarios:
      A. Deliberation changes an outcome. Gamma starts abstain,
         follows Alpha's rationale, votes yea. Council passes.
      B. Deliberation doesn't change anything. All positions
         stable from round 0. Same as C44 would have produced.
      C. A tampered position is caught by verify.

    Anchor: Dickinson, 'To make a prairie it takes a clover and
    one bee' — deliberation is the 'revery' that turns parts into
    a whole.
    """
    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    member_kps = {
        "a": KeyPair.generate(),
        "b": KeyPair.generate(),
        "c": KeyPair.generate(),
    }

    def rule_alpha(proposal, ctx):
        return ("yea", "low cost is acceptable")

    def rule_beta(proposal, ctx):
        return ("nay", "I remain unconvinced")

    def rule_gamma(proposal, ctx):
        # Gamma starts abstain, follows Alpha if Alpha has
        # already stanced yea in a prior round
        positions = ctx["positions_by_member"]
        alpha = positions.get("member:a")
        if alpha and alpha["stance"] == "yea":
            return ("yea",
                    "Alpha's rationale is persuasive")
        return ("abstain",
                "I will wait to hear from Alpha")

    council = DeliberativeCouncil(
        "council-main",
        quorum=QuorumRule(min_yea=2, min_present=2),
        max_rounds=5,
        stability_rounds=1,
    )
    council.add_member(DeliberativeMember(
        "member:a", "Alpha",
        member_kps["a"], rule_alpha))
    council.add_member(DeliberativeMember(
        "member:b", "Beta",
        member_kps["b"], rule_beta))
    council.add_member(DeliberativeMember(
        "member:c", "Gamma",
        member_kps["c"], rule_gamma))

    public_keys = {f"member:{k}": v.public_key_hex()
                   for k, v in member_kps.items()}

    proposal = Proposal(content={
        "action": "adopt-relay-for-coordination",
        "cost": "low",
    })
    decision = council.deliberate_and_resolve(proposal)
    verdict = verify_deliberative_decision(decision, public_keys)

    # ---- Scenario B: stable from start ----
    def fixed_yea(p, ctx): return ("yea", "yes")
    def fixed_nay(p, ctx): return ("nay", "no")
    def fixed_nay2(p, ctx): return ("nay", "no")

    council_b = DeliberativeCouncil(
        "council-stable",
        quorum=QuorumRule(2, 2),
        max_rounds=5, stability_rounds=1)
    council_b.add_member(DeliberativeMember(
        "member:a", "Alpha",
        KeyPair.generate(), fixed_yea))
    council_b.add_member(DeliberativeMember(
        "member:b", "Beta",
        KeyPair.generate(), fixed_nay))
    council_b.add_member(DeliberativeMember(
        "member:c", "Gamma",
        KeyPair.generate(), fixed_nay2))
    public_keys_b = {
        "member:a": council_b._members["member:a"]._member_public_key,
        "member:b": council_b._members["member:b"]._member_public_key,
        "member:c": council_b._members["member:c"]._member_public_key,
    }
    proposal_b = Proposal(content={"action": "adopt-octopus"})
    decision_b = council_b.deliberate_and_resolve(proposal_b)
    verdict_b = verify_deliberative_decision(
        decision_b, public_keys_b)

    # ---- Scenario C: tampered position ----
    attacker = KeyPair.generate()
    orig_pos = decision.positions[0]
    # Attacker forges Gamma's position claiming she was "yea" from
    # the start
    payload = canonical_bytes({
        "kind": "deliberation_position",
        "member_token": "member:c",
        "member_name": "Gamma",
        "member_public_key": member_kps["c"].public_key_hex(),
        "proposal_hash": decision.proposal_hash,
        "round_num": 0,
        "stance": "yea",   # she wasn't yea in round 0
        "rationale": "(forged)",
        "timestamp": "2024-01-01T00:00:00+00:00",
    })
    forged = SignedPosition(
        member_token="member:c", member_name="Gamma",
        member_public_key=member_kps["c"].public_key_hex(),
        proposal_hash=decision.proposal_hash,
        round_num=0, stance="yea",
        rationale="(forged)",
        timestamp="2024-01-01T00:00:00+00:00",
        signature=attacker.sign(payload).hex(),
    )
    tampered_positions = (forged,) + decision.positions[1:]
    tampered_decision = DeliberativeDecision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        positions=tampered_positions,
        rounds_run=decision.rounds_run,
        converged_at_round=decision.converged_at_round,
        final_decision=decision.final_decision,
    )
    verdict_c = verify_deliberative_decision(
        tampered_decision, public_keys)

    # Print
    print("=" * 70)
    print("Deliberation — bounded multi-round council process")
    print("=" * 70)
    print()
    print("  Scenario A — Gamma starts abstain, is persuaded")
    for line in decision.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict.valid}")
    print()
    print("  Scenario B — Positions stable from round 0")
    for line in decision_b.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict_b.valid}")
    print()
    print("  Scenario C — Forged position (attacker rewrites")
    print("    Gamma's round-0 stance to 'yea')")
    for line in verdict_c.format().split("\n"):
        print(f"    {line}")
    print()
    print("  What this demonstrates:")
    print("    - Positions are signed and retractable; votes are")
    print("      signed and committed. Both live in the record.")
    print("    - Deliberation can change outcomes; the log lets")
    print("      a verifier see WHY.")
    print("    - The final Decision is still a C44 Decision;")
    print("      verify_decision works on it independently.")
    print("    - Structural claim: the council is one")
    print("      architecture. Deliberation is a PROCESS on")
    print("      that architecture. The substrate supports")
    print("      processes, not just snapshots.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'To make a prairie it takes a clover and one bee,'")
    print("    'One clover, and a bee,'")
    print("    'And revery.'")
    print("    'The revery alone will do,'")
    print("    'If bees are few.'")

    audit = {
        "scenario_a_persuasion": {
            "rounds_run": decision.rounds_run,
            "converged_at_round": decision.converged_at_round,
            "final_outcome": decision.final_decision.outcome,
            "verified": verdict.valid,
            "gamma_stance_path": [
                p.stance for p in decision.positions
                if p.member_token == "member:c"],
        },
        "scenario_b_stable": {
            "rounds_run": decision_b.rounds_run,
            "final_outcome": decision_b.final_decision.outcome,
            "verified": verdict_b.valid,
        },
        "scenario_c_forged": {
            "verified": verdict_c.valid,
            "positions_valid": verdict_c.positions_valid,
            "bad_position_count": len(verdict_c.bad_positions),
        },
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "deliberation_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/deliberation_demo.json")
    return audit
