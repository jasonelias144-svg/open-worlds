"""
multiverse_c83.py — Component 83: Governance of Growth.

The last piece of the growth story. C82 produces signed
RuleProposals. C83 makes them actionable: participants vote,
quorum decides, the winning proposal becomes a signed
LawAmendment, and the world's Law — its size limits, in v0.1 —
updates for all future claims.

What this adds:

  - GrowingWorldLaw — the mutable, signable state of a
    GrowingWorld's Law (max_width, max_height, plus
    immutables: contiguity, overlap, purpose).

  - RuleVote — a voter-signed choice (yes/no/abstain) on a
    specific proposal_id. Voters must be current plot owners
    at vote time.

  - VotingPolicy — quorum rule + pass fraction.

  - LawAmendment — a curator-signed event that names the
    proposal, the old and new law hashes, and the tally
    that justified it. Applied to the world's state, and
    recorded in the log so history is reconstructible.

  - GovernedGrowingWorld — extends ObservingGrowingWorld.
    Adds `rule.vote` and `rule.tally` acts. Reads its
    current law via `_law_limits()` (a small hook added to
    C81 — see "Composition").

  - verify_governance_log — a third party's reconstruction
    and verification. For each LawAmendment in the log:
    - amendment signature valid
    - the votes preceding it match its tally_summary
    - applying the proposal's suggested_rule yields its
      new_law_hash
    - the old_law_hash matches the accumulated state

Composition: C3 (world/act), C13 (signatures), C55
(curator identity), C81 (GrowingWorld — extended only
through a `_law_limits()` hook that defaults to (20,20)),
C82 (ObservingGrowingWorld, RuleProposal). No new
primitives beyond the two new artifacts.

The single change to a prior component:

  C81's `_handle_claim` reads `self._law_limits()` instead
  of hardcoded 20. The default implementation returns
  (20, 20), preserving existing behavior exactly. A subclass
  overrides it to read from mutable law state. This is a
  *hook*, not a behavior change; every C81 test still
  passes.

Honest limits (documented, tested):
  - Only size limits are governable in v0.1. Contiguity,
    overlap, and purpose are fixed. Making them governable
    would need to amend the claim algorithm itself — out of
    scope.
  - Voters must be current plot owners. A participant who
    has only ever been refused cannot vote. This is a
    deliberate policy: "skin in the game." A v0.2 could
    allow a broader electorate.
  - Tally is deterministic. Anyone admitted can tally at
    any time; the tally either passes or fails based on
    the current vote count. A tally after a successful one
    is a no-op.
  - No proposal expiry. A proposal with insufficient votes
    stays pending forever unless it's superseded or the
    world is torn down.
  - No cross-world governance. A world's amendments are
    local. C72's federation could propagate them; C83
    doesn't.
  - The tally_summary is verified by recount from the log.
    If the amendment lies about the count, the log
    verification fails. If the log is lost and only the
    amendment survives, the amendment's claim is
    unverifiable.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import hashlib
import json
import time
import urllib.error
import urllib.request

from multiverse_c3 import Act, Ack, Refusal, LogEntry, Petition
from multiverse_c1 import Identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes,
    verify_signature,
)
from multiverse_c79 import ChainVerdict
from multiverse_c81 import GrowthEvent, GrowingWorld
from multiverse_c82 import (
    ObservingGrowingWorld, GrowingWorldCurator,
    RuleProposal, verify_rule_proposal,
)
from wcp_http_shim import WorldProtocolServer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


VOTE_CHOICES = frozenset({"yes", "no", "abstain"})


# =====================================================================
# GrowingWorldLaw
# =====================================================================

@dataclass(frozen=True)
class GrowingWorldLaw:
    """The mutable state of a GrowingWorld's Law. Governable
    fields only; immutables are documented but not carried."""
    max_width: int = 20
    max_height: int = 20

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "growing_world_law",
            "max_width": self.max_width,
            "max_height": self.max_height,
        })

    def law_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    @classmethod
    def initial(cls) -> "GrowingWorldLaw":
        return cls()


INITIAL_LAW = GrowingWorldLaw.initial()
INITIAL_LAW_HASH = INITIAL_LAW.law_hash()


# =====================================================================
# RuleVote
# =====================================================================

@dataclass(frozen=True)
class RuleVote:
    proposal_id: str
    voter_token: str
    voter_name: str
    voter_public_key: str
    choice: str
    timestamp: str
    signature: str

    def __post_init__(self):
        if self.choice not in VOTE_CHOICES:
            raise ValueError(
                f"choice must be one of "
                f"{sorted(VOTE_CHOICES)}; got {self.choice!r}")
        for f in ("proposal_id", "voter_token", "voter_name",
                  "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.voter_public_key) != 64:
            raise ValueError(
                "voter_public_key must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "rule_vote",
            "proposal_id": self.proposal_id,
            "voter_token": self.voter_token,
            "voter_name": self.voter_name,
            "voter_public_key": self.voter_public_key,
            "choice": self.choice,
            "timestamp": self.timestamp,
        })

    def vote_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        d = json.loads(self.canonical_payload().decode())
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "RuleVote":
        return cls(
            proposal_id=d["proposal_id"],
            voter_token=d["voter_token"],
            voter_name=d["voter_name"],
            voter_public_key=d["voter_public_key"],
            choice=d["choice"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_rule_vote(
    vote: RuleVote,
    expected_voter_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = expected_voter_key or vote.voter_public_key
        return verify_signature(
            key, vote.canonical_payload(), vote.signature)
    except Exception:
        return False


# =====================================================================
# VotingPolicy
# =====================================================================

@dataclass(frozen=True)
class VotingPolicy:
    """Quorum + pass threshold."""
    min_votes: int = 2
    pass_fraction: float = 0.5

    def evaluate(
        self, votes: List[RuleVote],
    ) -> Tuple[bool, str]:
        if len(votes) < self.min_votes:
            return (False,
                    f"only {len(votes)} votes, need "
                    f"{self.min_votes}")
        yes = sum(1 for v in votes if v.choice == "yes")
        no = sum(1 for v in votes if v.choice == "no")
        if yes + no == 0:
            return (False, "no yes/no votes")
        fraction = yes / (yes + no)
        if fraction >= self.pass_fraction:
            return (True,
                    f"passed ({yes} yes, {no} no)")
        return (False,
                f"failed ({yes} yes, {no} no)")


# =====================================================================
# LawAmendment
# =====================================================================

@dataclass(frozen=True)
class LawAmendment:
    proposal_id: str
    old_law_hash: str
    new_law: Dict
    new_law_hash: str
    tally_summary: Dict
    timestamp: str
    signer_id: str
    signer_public_key: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "law_amendment",
            "proposal_id": self.proposal_id,
            "old_law_hash": self.old_law_hash,
            "new_law": self.new_law,
            "new_law_hash": self.new_law_hash,
            "tally_summary": self.tally_summary,
            "timestamp": self.timestamp,
            "signer_id": self.signer_id,
            "signer_public_key": self.signer_public_key,
        })

    def amendment_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        d = json.loads(self.canonical_payload().decode())
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "LawAmendment":
        return cls(
            proposal_id=d["proposal_id"],
            old_law_hash=d["old_law_hash"],
            new_law=d["new_law"],
            new_law_hash=d["new_law_hash"],
            tally_summary=d["tally_summary"],
            timestamp=d["timestamp"],
            signer_id=d["signer_id"],
            signer_public_key=d["signer_public_key"],
            signature=d["signature"],
        )

    def new_law_object(self) -> GrowingWorldLaw:
        return GrowingWorldLaw(
            max_width=int(self.new_law["max_width"]),
            max_height=int(self.new_law["max_height"]),
        )


def verify_law_amendment(
    amendment: LawAmendment,
    expected_curator_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = (expected_curator_key
               or amendment.signer_public_key)
        if not verify_signature(
                key, amendment.canonical_payload(),
                amendment.signature):
            return False
        # new_law_hash must match the new_law content
        law = amendment.new_law_object()
        return law.law_hash() == amendment.new_law_hash
    except Exception:
        return False


# =====================================================================
# GovernedGrowingWorld
# =====================================================================

class GovernedGrowingWorld(ObservingGrowingWorld):
    """A GrowingWorld whose size limits are governable."""

    ACT_VOTE = "rule.vote"
    ACT_TALLY = "rule.tally"

    def __init__(
        self, entity_id: str, name: str, curator_kp: KeyPair,
        voting_policy: Optional[VotingPolicy] = None,
        seed_extent: Tuple[int, int, int, int] = (0, 0, 4, 4),
    ):
        super().__init__(
            entity_id, name, curator_kp,
            seed_extent=seed_extent)
        self._law = GrowingWorldLaw.initial()
        self._voting_policy = voting_policy or VotingPolicy()
        self._votes: Dict[str, List[RuleVote]] = {}
        self._applied: Dict[str, LawAmendment] = {}
        # Pending proposals come from C82's record_proposal

    @property
    def law(self) -> GrowingWorldLaw:
        return self._law

    @property
    def voting_policy(self) -> VotingPolicy:
        return self._voting_policy

    def _law_limits(self) -> Tuple[int, int]:
        return (self._law.max_width, self._law.max_height)

    def act(self, act: Act):
        if act.type == self.ACT_VOTE:
            return self._handle_vote(act)
        if act.type == self.ACT_TALLY:
            return self._handle_tally(act)
        return super().act(act)

    # -- Votes ---------------------------------------------------

    def votes(self, proposal_id: str) -> List[RuleVote]:
        return list(self._votes.get(proposal_id, []))

    def applied_amendment(
        self, proposal_id: str,
    ) -> Optional[LawAmendment]:
        return self._applied.get(proposal_id)

    def _handle_vote(self, act: Act):
        if act.actor_token not in self._admitted:
            return self._refuse(
                act.actor_token, "Actor is not admitted")
        current = self.current_plots()
        is_owner = any(
            p["owner_token"] == act.actor_token
            for p in current.values())
        if not is_owner:
            return self._refuse(
                act.actor_token,
                "only current plot owners may vote")
        payload = act.payload or {}
        proposal_id = payload.get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id:
            return self._refuse(
                act.actor_token, "proposal_id required")
        if proposal_id in self._applied:
            return self._refuse(
                act.actor_token,
                "proposal already decided")
        pending = self._pending_proposals()
        if proposal_id not in pending:
            return self._refuse(
                act.actor_token,
                f"unknown pending proposal: {proposal_id}")
        choice = payload.get("choice")
        if choice not in VOTE_CHOICES:
            return self._refuse(
                act.actor_token,
                "choice must be yes/no/abstain")
        existing = self._votes.get(proposal_id, [])
        if any(v.voter_token == act.actor_token
                for v in existing):
            return self._refuse(
                act.actor_token,
                "already voted on this proposal")
        vote = self._sign_vote(
            act.actor_token,
            self._admitted[act.actor_token],
            proposal_id, choice)
        self._votes.setdefault(proposal_id, []).append(vote)
        self._log.append(LogEntry(
            timestamp=vote.timestamp, kind="rule_vote",
            actor_token=vote.voter_token,
            data=vote.to_dict()))
        return self._ack()

    def _sign_vote(
        self, voter_token: str, voter_name: str,
        proposal_id: str, choice: str,
    ) -> RuleVote:
        # We hold the world's curator key; a real deploy would
        # have each voter sign with their own key. Here the
        # voter's public key is the world's curator key so that
        # third-party verification works without re-deriving
        # voter keys — documented as a v0.1 simplification.
        timestamp = _now()
        pk_hex = self._curator_kp.public_key_hex()
        payload = canonical_bytes({
            "kind": "rule_vote",
            "proposal_id": proposal_id,
            "voter_token": voter_token,
            "voter_name": voter_name,
            "voter_public_key": pk_hex,
            "choice": choice,
            "timestamp": timestamp,
        })
        sig = self._curator_kp.sign(payload).hex()
        return RuleVote(
            proposal_id=proposal_id,
            voter_token=voter_token,
            voter_name=voter_name,
            voter_public_key=pk_hex,
            choice=choice,
            timestamp=timestamp,
            signature=sig,
        )

    # -- Tally ---------------------------------------------------

    def _handle_tally(self, act: Act):
        if act.actor_token not in self._admitted:
            return self._refuse(
                act.actor_token, "Actor is not admitted")
        payload = act.payload or {}
        proposal_id = payload.get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id:
            return self._refuse(
                act.actor_token, "proposal_id required")
        if proposal_id in self._applied:
            return self._refuse(
                act.actor_token,
                "proposal already applied")
        pending = self._pending_proposals()
        proposal = pending.get(proposal_id)
        if proposal is None:
            return self._refuse(
                act.actor_token,
                f"unknown pending proposal: {proposal_id}")
        votes = self._votes.get(proposal_id, [])
        passed, reason = self._voting_policy.evaluate(votes)
        if not passed:
            return self._refuse(
                act.actor_token,
                f"tally failed: {reason}")
        # Apply the amendment
        suggested = proposal.get("suggested_rule", {})
        new_law = GrowingWorldLaw(
            max_width=int(suggested.get(
                "max_width", self._law.max_width)),
            max_height=int(suggested.get(
                "max_height", self._law.max_height)),
        )
        counts = {"yes": 0, "no": 0, "abstain": 0}
        for v in votes:
            counts[v.choice] += 1
        amendment = self._sign_amendment(
            proposal_id, self._law, new_law, counts)
        self._applied[proposal_id] = amendment
        self._law = new_law
        self._log.append(LogEntry(
            timestamp=amendment.timestamp,
            kind="law_amendment",
            actor_token=amendment.signer_id,
            data=amendment.to_dict()))
        return self._ack()

    def _sign_amendment(
        self, proposal_id: str, old_law: GrowingWorldLaw,
        new_law: GrowingWorldLaw, tally_summary: Dict,
    ) -> LawAmendment:
        timestamp = _now()
        pk_hex = self._curator_kp.public_key_hex()
        payload = canonical_bytes({
            "kind": "law_amendment",
            "proposal_id": proposal_id,
            "old_law_hash": old_law.law_hash(),
            "new_law": {
                "max_width": new_law.max_width,
                "max_height": new_law.max_height,
            },
            "new_law_hash": new_law.law_hash(),
            "tally_summary": tally_summary,
            "timestamp": timestamp,
            "signer_id": self._manifest.entity_id,
            "signer_public_key": pk_hex,
        })
        sig = self._curator_kp.sign(payload).hex()
        return LawAmendment(
            proposal_id=proposal_id,
            old_law_hash=old_law.law_hash(),
            new_law={
                "max_width": new_law.max_width,
                "max_height": new_law.max_height,
            },
            new_law_hash=new_law.law_hash(),
            tally_summary=tally_summary,
            timestamp=timestamp,
            signer_id=self._manifest.entity_id,
            signer_public_key=pk_hex,
            signature=sig,
        )

    def _pending_proposals(self) -> Dict[str, Dict]:
        pending: Dict[str, Dict] = {}
        for p in self.proposals():
            pid = p.get("proposal_id")
            if pid and pid not in self._applied:
                pending[pid] = p
        return pending


# =====================================================================
# Log verification
# =====================================================================

@dataclass
class GovernanceLogVerdict:
    valid: bool
    reason: str
    amendments_verified: int
    final_law: Optional[GrowingWorldLaw]
    errors: List[str] = field(default_factory=list)

    def format(self) -> str:
        lines = ["Governance Log Verification", "=" * 50]
        lines.append(f"  valid:                {self.valid}")
        lines.append(f"  amendments_verified:  "
                     f"{self.amendments_verified}")
        if self.final_law is not None:
            lines.append(
                f"  final_law:            "
                f"max_width={self.final_law.max_width}, "
                f"max_height={self.final_law.max_height}")
        for e in self.errors:
            lines.append(f"  ! {e}")
        if not self.valid:
            lines.append(f"  reason: {self.reason}")
        return "\n".join(lines)


def verify_governance_log(
    events: List[Any],
    curator_public_key: str,
) -> GovernanceLogVerdict:
    """Verify a governance log. Never raises.

    Events are typed: GrowthEvent, RuleVote, LawAmendment,
    and (optionally) RuleProposal dicts.

    Checks:
      1. Every GrowthEvent and LawAmendment signature
         verifies against the curator's key.
      2. Every RuleVote signature verifies against its
         declared voter_public_key.
      3. For each LawAmendment:
         a. Its proposal_id names a RuleProposal in the log
            (before it).
         b. old_law_hash matches the accumulated law state.
         c. Applying the proposal's suggested_rule to the
            prior law yields new_law_hash.
         d. Votes for that proposal_id in the log, strictly
            before the amendment, match tally_summary.
      4. Final law is reconstructed after all amendments.
    """
    if not HAS_CRYPTO:
        return GovernanceLogVerdict(
            valid=False, reason="cryptography not installed",
            amendments_verified=0, final_law=None)
    if not isinstance(events, list):
        return GovernanceLogVerdict(
            valid=False, reason="events must be a list",
            amendments_verified=0, final_law=None)

    # Extract components in order
    sequence: List[Tuple[int, str, Any]] = []
    for i, ev in enumerate(events):
        if isinstance(ev, GrowthEvent):
            if not verify_signature(
                    curator_public_key,
                    ev.canonical_payload(), ev.signature):
                return GovernanceLogVerdict(
                    False,
                    f"GrowthEvent {i} signature INVALID",
                    0, None)
            sequence.append((i, "growth", ev))
        elif isinstance(ev, RuleVote):
            if not verify_rule_vote(ev):
                return GovernanceLogVerdict(
                    False,
                    f"RuleVote {i} signature INVALID",
                    0, None)
            sequence.append((i, "vote", ev))
        elif isinstance(ev, LawAmendment):
            if not verify_law_amendment(ev, curator_public_key):
                return GovernanceLogVerdict(
                    False,
                    f"LawAmendment {i} signature INVALID",
                    0, None)
            sequence.append((i, "amendment", ev))
        elif isinstance(ev, dict):
            # Allow raw RuleProposal dicts
            if ev.get("kind") == "rule_proposal":
                try:
                    RuleProposal.from_dict(ev)
                except (KeyError, ValueError, TypeError):
                    return GovernanceLogVerdict(
                        False,
                        f"RuleProposal {i} malformed",
                        0, None)
                sequence.append((i, "proposal", ev))
            else:
                continue
        else:
            return GovernanceLogVerdict(
                False,
                f"entry {i} has unknown type "
                f"{type(ev).__name__}", 0, None)

    # Walk the sequence, accumulating law + votes + proposals
    law = INITIAL_LAW
    votes_seen: Dict[str, List[RuleVote]] = {}
    proposals_seen: Dict[str, Dict] = {}
    amendments_verified = 0
    errors: List[str] = []
    for i, kind, obj in sequence:
        if kind == "proposal":
            pid = obj.get("proposal_id")
            if pid:
                proposals_seen[pid] = obj
        elif kind == "vote":
            votes_seen.setdefault(obj.proposal_id, []).append(obj)
        elif kind == "amendment":
            a: LawAmendment = obj
            if a.old_law_hash != law.law_hash():
                errors.append(
                    f"amendment {i}: old_law_hash does not "
                    f"match accumulated law")
                continue
            prop = proposals_seen.get(a.proposal_id)
            if prop is None:
                errors.append(
                    f"amendment {i}: proposal_id "
                    f"{a.proposal_id!r} not seen")
                continue
            suggested = prop.get("suggested_rule", {})
            expected = GrowingWorldLaw(
                max_width=int(suggested.get(
                    "max_width", law.max_width)),
                max_height=int(suggested.get(
                    "max_height", law.max_height)),
            )
            if expected.law_hash() != a.new_law_hash:
                errors.append(
                    f"amendment {i}: new_law_hash does not "
                    f"match proposal's suggested_rule")
                continue
            # Recount votes strictly before this amendment
            counted = {"yes": 0, "no": 0, "abstain": 0}
            for v in votes_seen.get(a.proposal_id, []):
                if v.choice in counted:
                    counted[v.choice] += 1
            if counted != a.tally_summary:
                errors.append(
                    f"amendment {i}: tally_summary {a.tally_summary} "
                    f"!= recounted {counted}")
                continue
            law = expected
            amendments_verified += 1
            # Zero out counted votes so subsequent amendments
            # on the same proposal can't double-count
            votes_seen[a.proposal_id] = []

    if errors:
        return GovernanceLogVerdict(
            valid=False,
            reason=f"{len(errors)} verification error(s)",
            amendments_verified=amendments_verified,
            final_law=law, errors=errors)
    return GovernanceLogVerdict(
        valid=True,
        reason="all amendments verified",
        amendments_verified=amendments_verified,
        final_law=law)


def extract_governance_events(
    log_entries: List[LogEntry],
) -> List[Any]:
    """Extract typed governance artifacts from a log."""
    out: List[Any] = []
    for e in log_entries:
        try:
            if e.kind == "growth_event":
                out.append(GrowthEvent.from_dict(e.data))
            elif e.kind == "rule_vote":
                out.append(RuleVote.from_dict(e.data))
            elif e.kind == "law_amendment":
                out.append(LawAmendment.from_dict(e.data))
            elif e.kind == "rule_proposal":
                out.append(e.data)  # raw dict
        except (KeyError, ValueError, TypeError):
            continue
    return out


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """The full governance loop:

    1. Alice, Bob claim plots. Carol's oversized claim is
       refused (over the initial 20-cell limit).
    2. Curator observes size_limit refusals (C82) and
       proposes raising the limit to 40.
    3. Alice, Bob, Carol vote yes.
    4. Curator tallies: quorum met, amendment signed,
       world's law updates.
    5. Carol's oversized claim is now accepted under the
       new law.
    6. Third party fetches /log, verifies all events,
       reconstructs final law.
    """
    from multiverse_c1 import create_identity
    from multiverse_c82 import MockGrowthModel

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "governance"
    path.mkdir(parents=True, exist_ok=True)

    curator_kp = KeyPair.generate()
    world = GovernedGrowingWorld(
        "world:canvas", "Governed Canvas", curator_kp,
        voting_policy=VotingPolicy(
            min_votes=2, pass_fraction=0.5),
        seed_extent=(0, 0, 4, 4))
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    time.sleep(0.2)
    url = (f"http://127.0.0.1:"
           f"{server._httpd.server_address[1]}")

    alice = create_identity("Alice")
    bob = create_identity("Bob")
    carol = create_identity("Carol")
    for who in (alice, bob, carol):
        world.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(),
            message=f"{who.name} enters"))

    def claim(who, x, y, w, h, purpose):
        return world.act(Act(
            actor_token=who.token, type="canvas.claim",
            payload={"x": x, "y": y, "width": w,
                     "height": h, "purpose": purpose}))

    try:
        # 1. Plots
        claim(alice, 4, 0, 3, 3, "studio")
        claim(bob, 4, 3, 3, 3, "gallery")
        carol_over = claim(carol, 0, 4, 30, 30, "mural")
        assert isinstance(carol_over, Refusal)

        # 2. Curator proposes (C82)
        curator = GrowingWorldCurator(
            world, curator_kp, MockGrowthModel())
        obs = curator.observe_growth()
        proposal = curator.observe_and_propose_growth()
        assert proposal is not None
        pid = proposal.proposal_id

        # 3. Votes
        def vote(who, choice):
            return world.act(Act(
                actor_token=who.token, type="rule.vote",
                payload={"proposal_id": pid,
                         "choice": choice}))
        v_a = vote(alice, "yes")
        v_b = vote(bob, "yes")
        v_c = vote(carol, "yes")
        all_votes_ok = all(
            isinstance(v, Ack) for v in (v_a, v_b, v_c))

        # 4. Tally
        law_before = world.law
        tally = world.act(Act(
            actor_token=alice.token, type="rule.tally",
            payload={"proposal_id": pid}))
        law_after = world.law
        amendment = world.applied_amendment(pid)

        # 5. Retry Carol's oversized claim
        carol_retry = claim(carol, 0, 4, 30, 30, "mural")
        carol_accepted = isinstance(carol_retry, Ack)

        # 6. Third-party verification
        fetched = world.log_since(None)
        typed = extract_governance_events(fetched)
        verdict = verify_governance_log(
            typed, curator_kp.public_key_hex())

        # -- Print -----------------------------------------
        print("=" * 70)
        print("Governance of Growth — vote decides, law changes")
        print("=" * 70)
        print()
        print(f"  World: world:canvas")
        print(f"  Key:   {curator_kp.public_key_hex()[:16]}...")
        print()
        print(f"  Proposal: {proposal.title!r}")
        print(f"    suggested_rule:  {proposal.suggested_rule}")
        print(f"    signed_by:       "
              f"{proposal.signer_public_key[:16]}...")
        print()
        print(f"  Votes:")
        for who, choice, r in [
            ("Alice", "yes", v_a),
            ("Bob", "yes", v_b),
            ("Carol", "yes", v_c),
        ]:
            marker = "✓" if isinstance(r, Ack) else "✗"
            note = (f"  — {r.reason}"
                    if isinstance(r, Refusal) else "")
            print(f"    {marker} {who}: {choice}{note}")
        print()
        print(f"  Tally: {type(tally).__name__}")
        print(f"  Law before: max_width={law_before.max_width},"
              f" max_height={law_before.max_height}")
        print(f"  Law after:  max_width={law_after.max_width},"
              f" max_height={law_after.max_height}")
        if amendment:
            print(f"  Amendment:")
            print(f"    proposal_id:  {amendment.proposal_id}")
            print(f"    old_law_hash: "
                  f"{amendment.old_law_hash[:16]}...")
            print(f"    new_law_hash: "
                  f"{amendment.new_law_hash[:16]}...")
            print(f"    tally_summary: {amendment.tally_summary}")
        print()
        print(f"  Carol's oversized claim (30x30):")
        print(f"    Before amendment: refused")
        print(f"    After amendment:  "
              f"{'accepted' if carol_accepted else 'refused'}")
        print()
        print(f"  Third-party verification:")
        print(f"    Events typed:       {len(typed)}")
        print(f"    Amendments verified: "
              f"{verdict.amendments_verified}")
        print(f"    Final law:          max_width="
              f"{verdict.final_law.max_width if verdict.final_law else '?'},"
              f" max_height="
              f"{verdict.final_law.max_height if verdict.final_law else '?'}")
        print(f"    Valid:              {verdict.valid}")
        print()
        print("  What this demonstrates:")
        print("    - A proposal is just a recommendation. Without")
        print("      votes, nothing changes.")
        print("    - Votes are signed artifacts. Voters must be")
        print("      plot owners. Duplicates refused.")
        print("    - Tally verifies quorum + pass fraction,")
        print("      signs a LawAmendment, and updates the law.")
        print("    - The world's behavior changes: Carol's")
        print("      retry succeeds under the new limit.")
        print("    - A third party reconstructs law history from")
        print("      the log alone: proposals, votes, amendments.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Soul selects her own Society –'")
        print("    'Then – shuts the Door –'")

        audit = {
            "proposal_id": pid,
            "proposal_type": proposal.proposal_type,
            "proposal_suggested_rule": proposal.suggested_rule,
            "votes": {"alice": "yes", "bob": "yes",
                       "carol": "yes"},
            "all_votes_ok": all_votes_ok,
            "tally_ok": isinstance(tally, Ack),
            "law_before": {
                "max_width": law_before.max_width,
                "max_height": law_before.max_height,
            },
            "law_after": {
                "max_width": law_after.max_width,
                "max_height": law_after.max_height,
            },
            "amendment_tally_summary":
                amendment.tally_summary if amendment else None,
            "carol_retry_accepted": carol_accepted,
            "third_party": {
                "events_typed": len(typed),
                "amendments_verified":
                    verdict.amendments_verified,
                "final_law": (
                    {"max_width": verdict.final_law.max_width,
                     "max_height": verdict.final_law.max_height}
                    if verdict.final_law else None),
                "valid": verdict.valid,
            },
        }
        (path / "governance_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/governance_demo.json")
        return audit
    finally:
        server.stop()
