"""
multiverse_c84.py — Component 84: The World Cycle Runner.

Runs a GovernedGrowingWorld through many cycles with simulated
participants. Each cycle:

  1. Participants attempt actions (claims). Some succeed, some
     are refused. Refusals are logged.
  2. The curator observes periodically (every `curator_period`
     cycles) and, if triggered, proposes a rule change (C82).
  3. Pending proposals from prior cycles get voted on by plot
     owners (C83). Quorum + pass-fraction determine outcome.
  4. Successful tallies produce a signed LawAmendment and
     update the world's law (C83).
  5. A CycleSnapshot is recorded.

At the end, the runner produces a CycleReport with the snapshot
sequence, the final law, and a governance-log verdict obtained
by reconstructing the world's log offline (C83).

What C84 adds: nothing to the world. The runner is a *driver* —
it invokes existing act flows and produces a narrative. The
world's log is the canonical record. The report is a *view*.

Composition: C1 (Identity), C3 (Act, Petition, Ack, Refusal),
C13 (signing via world/curator), C81 (GrowingWorld claim/
retire), C82 (GrowingWorldCurator, MockGrowthModel), C83
(GovernedGrowingWorld, VotingPolicy, LawAmendment,
verify_governance_log, extract_governance_events). No new
primitives.

Honest limits (documented, tested):
  - Participants are simple policies (small/large/conservative/
    minimalist). A real community would have rich agents; the
    point here is that the *loop* works.
  - No participant-to-participant interaction. Participants
    act independently, respond to proposals, don't coordinate.
  - No proposal expiry. A failed proposal stays pending.
  - Only size_limit proposals are triggerable (C82's mock).
  - C83's `_sign_vote` uses the curator key; the runner inherits
    that limit. Vote signatures verify against the world, not
    the voter. Documented in C83.
  - The report is a *view* of the log. If the log were lost,
    the report's claims would be unverifiable. C83's
    verification reconstructs the log first, so the report's
    verdict is only as trustworthy as the log it came from.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity, create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c13 import HAS_CRYPTO
from multiverse_c81 import (
    GrowingWorld, _plots_edge_adjacent, _plots_overlap,
)
from multiverse_c82 import (
    GrowingWorldCurator, MockGrowthModel, _classify_refusal,
)
from multiverse_c83 import (
    GovernedGrowingWorld, GrowingWorldLaw, VotingPolicy,
    LawAmendment, GovernanceLogVerdict,
    extract_governance_events, verify_governance_log,
)


# =====================================================================
# Participants
# =====================================================================

@dataclass
class Participant:
    """A simulated resident. Simple by design: one action per
    cycle, one vote per proposal."""
    identity: Identity
    name: str
    action_fn: Callable[[GrowingWorld, int], Optional[Act]]
    vote_fn: Callable[[Dict, GrowingWorld], Optional[str]]
    claim_limit: int = 3
    _claims_made: int = 0

    @property
    def token(self) -> str:
        return self.identity.token

    def attempt(self, world: GrowingWorld, cycle: int) -> Optional[Any]:
        if self._claims_made >= self.claim_limit:
            return None
        act = self.action_fn(world, cycle)
        if act is None:
            return None
        r = world.act(act)
        if isinstance(r, Ack):
            self._claims_made += 1
        return r

    def vote(self, proposal: Dict,
             world: GrowingWorld) -> Optional[str]:
        try:
            return self.vote_fn(proposal, world)
        except Exception:
            return None


def _is_owner(world: GrowingWorld, token: str) -> bool:
    return any(p["owner_token"] == token
               for p in world.current_plots().values())


def _find_contiguous_slot(
    world: GrowingWorld, width: int, height: int,
) -> Optional[Tuple[int, int]]:
    active = world.current_plots()
    if not active:
        return None
    for p in active.values():
        candidates = [
            (p["x"] + p["width"], p["y"]),
            (p["x"] - width, p["y"]),
            (p["x"], p["y"] + p["height"]),
            (p["x"], p["y"] - height),
        ]
        for (x, y) in candidates:
            rect = (x, y, width, height)
            if not any(
                _plots_edge_adjacent(
                    rect, (q["x"], q["y"],
                           q["width"], q["height"]))
                for q in active.values()
            ):
                continue
            if any(
                _plots_overlap(
                    rect, (q["x"], q["y"],
                           q["width"], q["height"]))
                for q in active.values()
            ):
                continue
            return (x, y)
    return None


def _claim_act(
    token: str, width: int, height: int,
    purpose: str, world: GrowingWorld,
) -> Optional[Act]:
    slot = _find_contiguous_slot(world, width, height)
    if slot is None:
        return None
    x, y = slot
    return Act(
        actor_token=token, type="canvas.claim",
        payload={"x": x, "y": y, "width": width,
                 "height": height, "purpose": purpose})


def make_small_artist(name: str, claim_limit: int = 3) -> Participant:
    ident = create_identity(name)
    return Participant(
        identity=ident, name=name,
        action_fn=lambda w, c: _claim_act(
            ident.token, 2, 2, "studio", w),
        vote_fn=lambda proposal, world: "yes",
        claim_limit=claim_limit,
    )


def make_large_artist(name: str) -> Participant:
    ident = create_identity(name)
    return Participant(
        identity=ident, name=name,
        action_fn=lambda w, c: _claim_act(
            ident.token, 25, 25, "grand-studio", w),
        vote_fn=lambda proposal, world: "yes",
        claim_limit=1,
    )


def make_conservative(name: str, claim_limit: int = 2) -> Participant:
    ident = create_identity(name)
    return Participant(
        identity=ident, name=name,
        action_fn=lambda w, c: _claim_act(
            ident.token, 2, 2, "garden", w),
        vote_fn=lambda proposal, world: "no",
        claim_limit=claim_limit,
    )


def make_minimalist(name: str, claim_limit: int = 2) -> Participant:
    ident = create_identity(name)
    return Participant(
        identity=ident, name=name,
        action_fn=lambda w, c: _claim_act(
            ident.token, 1, 1, "notebook", w),
        vote_fn=lambda proposal, world: "abstain",
        claim_limit=claim_limit,
    )


# =====================================================================
# Snapshots and report
# =====================================================================

@dataclass
class CycleSnapshot:
    cycle: int
    plot_count: int
    total_area: int
    refusal_count: int
    refusal_kinds: Dict[str, int]
    law_max_width: int
    law_max_height: int
    amendment: Optional[Dict] = None
    events: List[str] = field(default_factory=list)


@dataclass
class CycleReport:
    snapshots: List[CycleSnapshot]
    final_law: GrowingWorldLaw
    final_plot_count: int
    final_area: int
    verdict: GovernanceLogVerdict

    def narrative(self) -> str:
        lines = [
            f"  {'C':>3s} | {'plots':>5s} | {'area':>4s} | "
            f"{'refusals':<18s} | {'law':<9s} | events",
            f"  --- + ----- + ---- + "
            f"{'-'*18} + --------- + ------",
        ]
        for s in self.snapshots:
            ref = str(s.refusal_count)
            kinds = [f"{k}={v}" for k, v in s.refusal_kinds.items() if v]
            if kinds:
                ref += f"({','.join(kinds)})"
            law = f"{s.law_max_width}x{s.law_max_height}"
            ev = " ".join(s.events)
            lines.append(
                f"  {s.cycle:3d} | {s.plot_count:5d} | "
                f"{s.total_area:4d} | {ref:<18s} | "
                f"{law:<9s} | {ev}")
        lines.append("")
        lines.append(
            f"  Final: {self.final_plot_count} plots, "
            f"{self.final_area} cells, "
            f"law {self.final_law.max_width}x"
            f"{self.final_law.max_height}")
        lines.append(
            f"  Verification: "
            f"{'✓' if self.verdict.valid else '✗'} "
            f"({self.verdict.reason})")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "snapshots": [
                {"cycle": s.cycle,
                 "plot_count": s.plot_count,
                 "total_area": s.total_area,
                 "refusal_count": s.refusal_count,
                 "refusal_kinds": dict(s.refusal_kinds),
                 "law": {"max_width": s.law_max_width,
                         "max_height": s.law_max_height},
                 "amendment": s.amendment,
                 "events": list(s.events)}
                for s in self.snapshots
            ],
            "final_law": {
                "max_width": self.final_law.max_width,
                "max_height": self.final_law.max_height,
            },
            "final_plot_count": self.final_plot_count,
            "final_area": self.final_area,
            "verdict": {
                "valid": self.verdict.valid,
                "reason": self.verdict.reason,
                "amendments_verified":
                    self.verdict.amendments_verified,
            },
        }


def _refusal_stats(world: GrowingWorld
                    ) -> Tuple[int, Dict[str, int]]:
    log = world.log_since(None)
    total = 0
    kinds: Dict[str, int] = {}
    for e in log:
        if e.kind == "act_refused":
            total += 1
            reason = (e.data or {}).get("reason", "")
            k = _classify_refusal(reason)
            kinds[k] = kinds.get(k, 0) + 1
    return total, kinds


# =====================================================================
# The runner
# =====================================================================

def run_cycles(
    world: GovernedGrowingWorld,
    curator: GrowingWorldCurator,
    participants: List[Participant],
    max_cycles: int = 15,
    curator_period: int = 5,
    tally_token: Optional[str] = None,
) -> CycleReport:
    """Run a GovernedGrowingWorld through `max_cycles` cycles.

    Every participant is admitted; then, per cycle:
      - each participant attempts one action (claim),
      - the curator periodically observes and may propose,
      - pending proposals get voted on by plot owners,
      - passing tallies apply LawAmendments.

    Returns a CycleReport. Does not raise for act-level failures
    (which are logged by the world, as designed).
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "run_cycles requires `cryptography`")

    # Admit everyone
    for p in participants:
        world.petition(Petition(
            petitioner_token=p.token,
            petitioner_name=p.name,
            passport_admissions=(),
            message=f"{p.name} enters"))

    if tally_token is None:
        tally_token = participants[0].token

    proposal_cycles: Dict[str, int] = {}
    applied_at: Dict[str, int] = {}
    snapshots: List[CycleSnapshot] = []

    for cycle in range(max_cycles):
        events: List[str] = []
        amendment_this_cycle: Optional[Dict] = None

        # 1. Participants attempt actions
        for p in participants:
            r = p.attempt(world, cycle)
            if r is None:
                continue
            if isinstance(r, Ack):
                events.append(f"{p.name}:ok")
            elif isinstance(r, Refusal):
                kind = _classify_refusal(r.reason)
                events.append(f"{p.name}:refused({kind})")

        # 2. Curator proposes periodically
        if cycle > 0 and cycle % curator_period == 0:
            try:
                proposal = curator.observe_and_propose_growth()
            except Exception:
                proposal = None
            if proposal is not None:
                proposal_cycles[proposal.proposal_id] = cycle
                events.append(
                    f"propose({proposal.proposal_id[:6]})")

        # 3. Voting on pending proposals (1 cycle after creation)
        for proposal_dict in world.proposals():
            pid = proposal_dict.get("proposal_id")
            if not pid or pid in applied_at:
                continue
            if pid not in proposal_cycles:
                continue
            if cycle <= proposal_cycles[pid]:
                continue
            yes = no = abstain = 0
            for p in participants:
                if not _is_owner(world, p.token):
                    continue
                choice = p.vote(proposal_dict, world)
                if choice is None:
                    continue
                r = world.act(Act(
                    actor_token=p.token, type="rule.vote",
                    payload={"proposal_id": pid,
                             "choice": choice}))
                if isinstance(r, Ack):
                    if choice == "yes":
                        yes += 1
                    elif choice == "no":
                        no += 1
                    else:
                        abstain += 1
            if yes + no + abstain == 0:
                continue
            r = world.act(Act(
                actor_token=tally_token, type="rule.tally",
                payload={"proposal_id": pid}))
            if isinstance(r, Ack):
                applied_at[pid] = cycle
                amendment_this_cycle = {
                    "proposal_id": pid,
                    "yes": yes, "no": no,
                    "abstain": abstain,
                }
                events.append(
                    f"AMENDED(y{yes}/n{no}/a{abstain})")

        # 4. Snapshot
        refused_count, refused_kinds = _refusal_stats(world)
        snapshots.append(CycleSnapshot(
            cycle=cycle,
            plot_count=len(world.current_plots()),
            total_area=world.current_extent_area(),
            refusal_count=refused_count,
            refusal_kinds=refused_kinds,
            law_max_width=world.law.max_width,
            law_max_height=world.law.max_height,
            amendment=amendment_this_cycle,
            events=events,
        ))

    # 5. Third-party verification of the whole log
    typed = extract_governance_events(world.log_since(None))
    verdict = verify_governance_log(
        typed, world.curator_public_key)

    return CycleReport(
        snapshots=snapshots,
        final_law=world.law,
        final_plot_count=len(world.current_plots()),
        final_area=world.current_extent_area(),
        verdict=verdict,
    )


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Five participants. Fifteen cycles. The canvas grows, the
    large artist is refused, the curator proposes, the world
    votes, the law amends, the large artist succeeds.

    Carol (the large artist) is the trigger. She keeps trying
    to claim a 25x25 studio; the initial law caps claims at
    20x20. The curator notices, proposes raising the limit,
    and the world (Alice, Bob yes; Dave no; Eve abstain) passes
    it. Carol's next claim succeeds.
    """
    import json
    import time
    from pathlib import Path
    from wcp_http_shim import WorldProtocolServer

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "world_cycle"
    path.mkdir(parents=True, exist_ok=True)

    curator_kp = KeyPair.generate()
    world = GovernedGrowingWorld(
        "world:canvas", "The Living Canvas", curator_kp,
        voting_policy=VotingPolicy(
            min_votes=2, pass_fraction=0.5),
        seed_extent=(0, 0, 4, 4))
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    time.sleep(0.2)

    alice = make_small_artist("Alice", claim_limit=3)
    bob = make_small_artist("Bob", claim_limit=3)
    carol = make_large_artist("Carol")
    dave = make_conservative("Dave", claim_limit=2)
    eve = make_minimalist("Eve", claim_limit=2)

    curator = GrowingWorldCurator(
        world, curator_kp, MockGrowthModel())

    try:
        report = run_cycles(
            world, curator,
            [alice, bob, carol, dave, eve],
            max_cycles=15, curator_period=5)

        print("=" * 74)
        print("The World Cycle Runner — the canvas over fifteen cycles")
        print("=" * 74)
        print()
        print(f"  World: world:canvas (The Living Canvas)")
        print(f"  Key:   {curator_kp.public_key_hex()[:16]}...")
        print()
        print("  Participants:")
        print("    Alice  — small artist  (2x2, votes yes)")
        print("    Bob    — small artist  (2x2, votes yes)")
        print("    Carol  — large artist  (25x25, votes yes)")
        print("    Dave   — conservative  (2x2, votes no)")
        print("    Eve    — minimalist    (1x1, votes abstain)")
        print()
        print(report.narrative())
        print()
        print("  What this demonstrates:")
        print("    - A world running over cycles: every claim, every")
        print("      refusal, every vote, every amendment is in the")
        print("      log at the end of the run.")
        print("    - Carol's 25x25 claims were refused under the")
        print("      20x20 law. The curator observed the refusals")
        print("      (C82) and proposed raising the limit. The")
        print("      world voted (C83), amended the law, and Carol")
        print("      succeeded — all in the same run, without any")
        print("      code outside the world's own Law.")
        print("    - The cycle report is a *view*. A third party")
        print("      (the verify_governance_log step) reconstructs")
        print("      the law from the log and confirms the")
        print("      amendment chain.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'Forever – is composed of Nows –'")
        print("    'Tis not a different time –'")

        audit = report.to_dict()
        audit["curator_public_key"] = (
            curator_kp.public_key_hex())
        audit["participants"] = [p.name for p in
                                  (alice, bob, carol,
                                   dave, eve)]
        (path / "world_cycle_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/world_cycle_demo.json")
        return audit
    finally:
        server.stop()
