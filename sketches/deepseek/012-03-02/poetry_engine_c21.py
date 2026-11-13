"""
poetry_engine_c21.py — Component 21: The Collaboration Protocol.

Three atoms, three composites, one protocol.

ARCHITECTURE — designed for implementation, not executed in this session.

Depends on Components 1-20, plus Modules 1-8 of the curriculum.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class CollaborationMode(Enum):
    """The three architectural modes. Only POLYPHONY is complete."""
    POLYPHONY = "polyphony"      # chain-based, Negative Capability protocol
    ROUND = "round"              # moderated, consensus-seeking (incomplete)
    FIELD = "field"              # parallel, no chain (incomplete)


class TheoreticalStance(Enum):
    """Each participant holds one theory — held open, not believed."""
    FORMALIST = "formalist"
    STRUCTURALIST = "structuralist"
    PSYCHOANALYTIC = "psychoanalytic"
    MARXIST = "marxist"
    FEMINIST = "feminist"
    POSTCOLONIAL = "postcolonial"
    DECONSTRUCTIVE = "deconstructive"
    ECOCRITICAL = "ecocritical"


@dataclass
class Participant:
    """One voice in the collaboration.

    The Participant has:
      - A voice (from the Voice module, Lesson 61)
      - A theoretical stance (from the Theory module, Lessons 64-72)
      - A position in the chain (determined by joining order)
    """
    name: str
    voice: "ApprenticeVoice"    # the voice from Lesson 61
    stance: TheoreticalStance
    position: int               # 1-indexed; position 1 is the seed
    portfolio: List[str] = field(default_factory=list)


@dataclass
class Turn:
    """One contribution to the chain.

    A Turn is *not* a poem. It is a *move* in the collaboration.
    It has three required parts (see protocol below).
    """
    participant: Participant
    round: int
    line_count: int

    # The three required parts of a turn:
    acknowledgment: str         # what this turn is responding to
    proposal: str               # the actual contribution (the lines)
    invitation: str             # the question posed to the next voice

    # The Negative Capability check:
    holds_open: bool            # does the turn hold its resolution open?

    # The optional extension for theory:
    stance_used: Optional[TheoreticalStance] = None


@dataclass
class Round:
    """One complete pass through the chain."""
    number: int
    turns: List[Turn] = field(default_factory=list)

    def start_time(self):
        return self.turns[0] if self.turns else None


@dataclass
class Collaboration:
    """The whole collaboration: chain of turns, rounds, convergence."""
    name: str
    mode: CollaborationMode
    seed_turn: Turn
    rounds: List[Round] = field(default_factory=list)
    convergence: Optional["ConvergenceReport"] = None

    def all_turns(self) -> List[Turn]:
        turns = [self.seed_turn]
        for r in self.rounds:
            turns.extend(r.turns)
        return turns

    def all_lines(self) -> List[str]:
        lines = []
        for turn in self.all_turns():
            lines.append(f"[{turn.participant.name} / round {turn.round}]")
            lines.append(turn.proposal)
            lines.append("")
        return lines

    def report(self) -> str:
        lines = [f'Collaboration: "{self.name}"',
                 f"  Mode: {self.mode.value}",
                 f"  Participants: "
                 f"{[t.participant.name for t in self.all_turns()]}",
                 f"  Rounds: {len(self.rounds)}",
                 f"  Turns: {len(self.all_turns())}",
                 ""]
        if self.convergence:
            lines.append(self.convergence.report())
        return "\n".join(lines)


class CollaborationProtocol:
    """The rules of the collaboration.

    Three checks per turn:
      1. acknowledgment_check: is the turn responding to a specific prior?
      2. invitation_check: does the turn pose a question to the next?
      3. negative_capability_check: does the turn hold its resolution open?
    """

    def check_turn(self, turn: Turn,
                    prior: Optional[Turn]) -> Tuple[bool, List[str]]:
        issues = []
        if prior is None and turn.round > 0:
            issues.append("turn has no prior but is not the seed")
        if not turn.acknowledgment.strip():
            issues.append("turn has no acknowledgment")
        if not turn.invitation.strip():
            issues.append("turn has no invitation")
        if not turn.holds_open:
            issues.append("turn closes its resolution (violates Negative "
                          "Capability)")
        # Check that acknowledgment actually references the prior
        if prior is not None:
            prior_tokens = set(prior.proposal.lower().split())
            ack_tokens = set(turn.acknowledgment.lower().split())
            if not (prior_tokens & ack_tokens):
                issues.append("acknowledgment does not reference prior turn")
        return (len(issues) == 0, issues)


class ConvergenceDetector:
    """When is the collaboration done?

    The collaboration converges when the last N turns begin to *echo*
    each other — meaning the chain is not advancing the poem but
    circling the same unresolved question. That is not a failure.
    That is Negative Capability *succeeding* — the collaboration has
    reached a stable polyphony.
    """

    def __init__(self, window: int = 3, similarity_threshold: float = 0.6):
        self.window = window
        self.similarity_threshold = similarity_threshold

    def _token_overlap(self, a: str, b: str) -> float:
        ta = set(a.lower().split())
        tb = set(b.lower().split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def has_converged(self, collaboration: Collaboration
                       ) -> Tuple[bool, str]:
        turns = collaboration.all_turns()
        if len(turns) < self.window + 1:
            return False, "not enough turns"
        recent = turns[-self.window:]
        # Convergence: the proposals are echoing each other
        pairs = [(recent[i], recent[i + 1])
                 for i in range(len(recent) - 1)]
        similarities = [self._token_overlap(a.proposal, b.proposal)
                        for a, b in pairs]
        if all(s >= self.similarity_threshold for s in similarities):
            return True, f"last {self.window} turns are echo"
        # Convergence: all invitations are the same question
        invitations = [t.invitation for t in recent]
        if all(invitations[0] == inv for inv in invitations):
            return True, "last {self.window} turns pose the same invitation"
        return False, "chain still advancing"


@dataclass
class ConvergenceReport:
    converged: bool
    reason: str
    final_round: int
    total_turns: int

    def report(self) -> str:
        status = "converged" if self.converged else "not converged"
        return (f"Convergence: {status} after {self.total_turns} turns "
                f"(round {self.final_round})\n"
                f"  Reason: {self.reason}")


class Polyphony:
    """The collaboration engine.

    Not a moderator. The engine simply:
      1. Orders participants in a chain (seed → A → B → C → A → B → C → ...)
      2. Gives each participant the prior turn
      3. Collects the new turn
      4. Checks the protocol
      5. Repeats until convergence

    The engine does not decide what to say. It only enforces
    the protocol and detects convergence. The *content* is the
    participants'.
    """

    def __init__(self, name: str,
                 participants: List[Participant],
                 seed_turn: Turn,
                 protocol: Optional[CollaborationProtocol] = None,
                 convergence_detector: Optional[ConvergenceDetector] = None,
                 max_rounds: int = 10):
        if len(participants) < 2:
            raise ValueError("Polyphony needs at least 2 participants")
        self.name = name
        self.participants = sorted(participants, key=lambda p: p.position)
        self.seed_turn = seed_turn
        self.protocol = protocol or CollaborationProtocol()
        self.convergence = convergence_detector or ConvergenceDetector()
        self.max_rounds = max_rounds
        self.collaboration = Collaboration(
            name=name,
            mode=CollaborationMode.POLYPHONY,
            seed_turn=seed_turn,
        )
        self._last_turn = seed_turn

    def _next_participant(self, round_number: int) -> Participant:
        """Round-robin through the chain."""
        idx = (len(self.collaboration.all_turns()) - 1) % \
              len(self.participants)
        return self.participants[idx]

    def add_turn(self, turn: Turn) -> bool:
        """Add a turn. Returns False if the protocol rejects it."""
        ok, issues = self.protocol.check_turn(turn, self._last_turn)
        if not ok:
            raise ValueError(f"Turn violates protocol: {issues}")
        # Find or create the current round
        current_round_num = turn.round
        while len(self.collaboration.rounds) <= current_round_num:
            self.collaboration.rounds.append(
                Round(number=len(self.collaboration.rounds) + 1))
        self.collaboration.rounds[current_round_num].turns.append(turn)
        self._last_turn = turn
        return True

    def run_until_converged(
            self, turn_generator) -> Collaboration:
        """Run the chain until convergence.

        `turn_generator` is a callable:
            (participant, prior_turn, round_num) -> Turn
        This is *not* the collaboration deciding what to say —
        it is the caller providing the turns. The engine just runs
        the chain and checks the protocol.
        """
        for round_num in range(self.max_rounds):
            for _ in range(len(self.participants)):
                participant = self._next_participant(round_num)
                prior = self._last_turn
                turn = turn_generator(participant, prior, round_num)
                self.add_turn(turn)
                converged, reason = self.convergence.has_converged(
                    self.collaboration)
                if converged:
                    self.collaboration.convergence = ConvergenceReport(
                        converged=True,
                        reason=reason,
                        final_round=round_num,
                        total_turns=len(self.collaboration.all_turns()),
                    )
                    return self.collaboration
        self.collaboration.convergence = ConvergenceReport(
            converged=False,
            reason="reached max rounds without converging",
            final_round=self.max_rounds,
            total_turns=len(self.collaboration.all_turns()),
        )
        return self.collaboration
