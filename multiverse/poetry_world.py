"""The poetry world: poets take turns under the Polyphony protocol.

From the DeepSeek sketch's component 4, whose law comes from the poetry
framework in record 012-03-02. The world is thin: it admits, checks each
turn against its law, records everything, and notices when the poem has
converged. It never writes a line. The poets do.

A turn (act type "poem.turn") has four parts:
  acknowledgment   what it answers in the turn before
  proposal         the lines
  invitation       the question it leaves for the next poet
  holds_open       it does not close the question (Negative Capability)

Changed from the sketch:
  - An acknowledgment may answer the prior turn's invitation as well as
    its proposal. In the sketch only words of the proposal counted, so a
    poet who answered the question it was asked was refused.
  - Turn fields of the wrong type are refused instead of raising, and
    holds_open must be true or false (the sketch read "false" as true).
  - The log keeps its own copy of each turn.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .entity import (SIGNED_REQUESTS_LAW, STAMPS_LAW, UNSIGNED_ANSWERS_LIMIT,
                     Entity, now)
from .protocol import Ack, Act, ActResponse, LogEntry

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "i",
    "you", "he", "she", "we", "they", "my", "your", "his",
    "her", "our", "their", "not", "no", "so", "if", "as",
}
PUNCTUATION = ".,;:!?\"'()[]"


def content_words(text: str) -> Set[str]:
    """Lower-cased words longer than two letters, without stopwords."""
    words = set()
    for raw in text.split():
        word = raw.strip(PUNCTUATION).lower()
        if len(raw) > 2 and word and word not in STOPWORDS:
            words.add(word)
    return words


def all_words(text: str) -> Set[str]:
    return {w for w in (raw.strip(PUNCTUATION).lower()
                        for raw in text.split()) if w}


@dataclass(frozen=True)
class PoetryWorldLaw:
    """The published law. A document, and what the world enforces."""
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None
    required_act_type: str = "poem.turn"
    requires_acknowledgment: bool = True
    requires_invitation: bool = True
    requires_holds_open: bool = True
    requires_acknowledgment_references_prior: bool = True
    convergence_window: int = 3
    convergence_similarity: float = 0.6
    max_turns: int = 200

    def describe(self) -> str:
        return "\n".join([
            "# Poetry World Law v0.3",
            "",
            "## Entering and leaving",
            f"- Admits any identity: {self.admits_any_identity}",
            "- Max present: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "- Anyone may leave at any time.",
            SIGNED_REQUESTS_LAW,
            STAMPS_LAW,
            "",
            "## A turn (poem.turn)",
            f"- Act type: {self.required_act_type}",
            f"- Requires an acknowledgment: {self.requires_acknowledgment}",
            f"- Requires an invitation: {self.requires_invitation}",
            f"- Requires holding open: {self.requires_holds_open}",
            "- The acknowledgment must share a word with the prior turn's "
            "proposal or invitation: "
            f"{self.requires_acknowledgment_references_prior}",
            "",
            "## Convergence",
            f"- Window: the last {self.convergence_window} turns",
            "- Converged when their proposals echo each other "
            f"(word overlap at least {self.convergence_similarity:.0%}), "
            "or they all pose the same invitation",
            f"- At most {self.max_turns} turns",
            "",
            "## Limits",
            UNSIGNED_ANSWERS_LIMIT,
        ])


class PoetryWorld(Entity):
    scheme = "poetry"

    def __init__(self, entity_id: str, name: str,
                 law: Optional[PoetryWorldLaw] = None):
        super().__init__(entity_id, name, law or PoetryWorldLaw())
        self._turns: List[Dict] = []
        self._converged = False
        self._convergence_reason: Optional[str] = None

    def act(self, act: Act) -> ActResponse:
        timestamp = now()
        refusal = self._actor_problem(timestamp, act)
        if refusal:
            return refusal
        actor = act.actor_token
        if self._converged:
            return self._refuse(timestamp, actor,
                                "The collaboration has converged", "act")
        if len(self._turns) >= self._law.max_turns:
            return self._refuse(timestamp, actor,
                                "The World has reached its turn limit", "act")
        if act.type != self._law.required_act_type:
            return self._refuse(timestamp, actor,
                                f"Unknown act type: {act.type}", "act")

        payload = act.payload
        fields = {k: payload.get(k, "") for k in
                  ("acknowledgment", "proposal", "invitation")}
        for key, value in fields.items():
            if type(value) is not str:
                return self._refuse(timestamp, actor,
                                    f"The {key} must be text", "act")
        stance = payload.get("stance_used")
        if stance is not None and type(stance) is not str:
            return self._refuse(timestamp, actor,
                                "The stance must be text", "act")
        ack, proposal, invitation = (fields["acknowledgment"],
                                     fields["proposal"],
                                     fields["invitation"])
        holds_open = payload.get("holds_open", False)
        if type(holds_open) is not bool:
            return self._refuse(timestamp, actor,
                                "holds_open must be true or false", "act")

        if self._law.requires_acknowledgment and not ack:
            return self._refuse(timestamp, actor,
                                "Missing acknowledgment", "act")
        if self._law.requires_invitation and not invitation:
            return self._refuse(timestamp, actor,
                                "Missing invitation", "act")
        if self._law.requires_holds_open and not holds_open:
            return self._refuse(timestamp, actor,
                                "Turn does not hold open", "act")
        if not proposal:
            return self._refuse(timestamp, actor, "Missing proposal", "act")
        if self._law.requires_acknowledgment_references_prior and self._turns:
            prior = self._turns[-1]
            if not self._references(ack, prior):
                return self._refuse(timestamp, actor,
                                    "Acknowledgment does not reference "
                                    "the prior turn", "act")

        index = len(self._turns)
        turn = {
            "turn_index": index,
            "round": index,
            "actor_token": actor,
            "actor_name": self._passports[actor].identity.name,
            "acknowledgment": ack,
            "proposal": proposal,
            "invitation": invitation,
            "holds_open": holds_open,
            "stance_used": stance,
            "timestamp": timestamp,
        }
        self._turns.append(turn)
        self._log.append(LogEntry(timestamp=timestamp, kind="turn",
                                  actor_token=actor, data=dict(turn)))
        if self._check_convergence():
            self._converged = True
            self._log.append(LogEntry(
                timestamp=timestamp, kind="convergence",
                data={"turn_count": len(self._turns),
                      "window": self._law.convergence_window,
                      "reason": self._convergence_reason}))
        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp,
                   stamp=self._made(actor, timestamp, turn))

    # -- conveniences ---------------------------------------------------

    def turns(self) -> List[Dict]:
        """A copy of the turns. The log is the record."""
        return [dict(t) for t in self._turns]

    def is_converged(self) -> bool:
        return self._converged

    def convergence_reason(self) -> Optional[str]:
        return self._convergence_reason

    def describe(self) -> str:
        lines = [f"PoetryWorld: {self._manifest.name}",
                 f"  entity_id: {self._manifest.entity_id}",
                 f"  present:   {len(self._admitted)}",
                 f"  turns:     {len(self._turns)}",
                 f"  converged: {self._converged}"]
        if self._turns:
            lines.append(f"  last turn by: {self._turns[-1]['actor_name']}")
        return "\n".join(lines)

    # -- internals ------------------------------------------------------

    @staticmethod
    def _references(acknowledgment: str, prior: Dict) -> bool:
        """At least one content word shared with the prior turn's
        proposal or invitation."""
        prior_words = (content_words(prior["proposal"])
                       | content_words(prior["invitation"]))
        return bool(content_words(acknowledgment) & prior_words)

    def _check_convergence(self) -> bool:
        window = self._law.convergence_window
        if len(self._turns) < window + 1:
            return False
        recent = self._turns[-window:]
        similarities = []
        for a, b in zip(recent, recent[1:]):
            wa, wb = all_words(a["proposal"]), all_words(b["proposal"])
            similarities.append(len(wa & wb) / len(wa | wb)
                                if wa and wb else 0.0)
        if similarities and all(s >= self._law.convergence_similarity
                                for s in similarities):
            self._convergence_reason = (
                f"the last {window} turns echo each other (word overlap "
                f"at least {self._law.convergence_similarity:.0%})")
            return True
        if len({t["invitation"] for t in recent}) == 1:
            self._convergence_reason = (
                f"the last {window} turns pose the same invitation")
            return True
        return False


def turns_from_log(log: List[LogEntry]) -> List[Dict]:
    """The collaboration rebuilt from a poetry world's log, as any reader
    can do without the world's own cache."""
    return [dict(entry.data) for entry in log if entry.kind == "turn"]
