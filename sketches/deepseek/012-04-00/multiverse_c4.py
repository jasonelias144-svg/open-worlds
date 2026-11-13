"""
multiverse_c4.py — Component 4: The Poetry World.

The first real WCP-conforming world. It implements the Polyphony
protocol from the poetry framework (C21) as its Law.

A design commitment: the World is *thin*. It admits identities,
validates turns against the Law, records everything, and detects
convergence. The *clients* (the Runnable Apprentices from C22)
generate the turns. The World never generates.

Depends on Components 1, 2, 3.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

from multiverse_c1 import Identity
from multiverse_c2 import Passport, Admission as PassportAdmission
from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Route, Ack,
)


# =====================================================================
# The Law: the Polyphony protocol, published
# =====================================================================

@dataclass(frozen=True)
class PoetryWorldLaw:
    """The published Law of the Poetry World.

    This is a *document*, not a mechanism. It is readable by any
    developer who wants to understand what this World does. The
    World *enforces* this Law — nothing more, nothing less.

    Any developer building their own poetry world should either
    adopt this Law verbatim (and pass the conformance test) or
    publish their own Law and note the differences.
    """
    # Petition rules
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None

    # Act rules
    required_act_type: str = "poem.turn"
    requires_acknowledgment: bool = True
    requires_invitation: bool = True
    requires_holds_open: bool = True
    requires_acknowledgment_references_prior: bool = True

    # Convergence rules
    convergence_window: int = 3
    convergence_similarity: float = 0.6
    max_turns: int = 200

    def describe(self) -> str:
        """Return the Law as a readable document.
        The Law is published — this is the publication."""
        lines = [
            "# Poetry World Law v0.1",
            "",
            "## Petition",
            f"- Admits any identity: {self.admits_any_identity}",
            f"- Max admitted: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "",
            "## Act (poem.turn)",
            f"- Required act type: {self.required_act_type}",
            f"- Requires acknowledgment: {self.requires_acknowledgment}",
            f"- Requires invitation: {self.requires_invitation}",
            f"- Requires holds open: {self.requires_holds_open}",
            f"- Acknowledgment must reference prior turn: "
            f"{self.requires_acknowledgment_references_prior}",
            "",
            "## Convergence",
            f"- Window: last {self.convergence_window} turns",
            f"- Similarity threshold: {self.convergence_similarity:.0%}",
            f"- Max turns: {self.max_turns}",
            "",
            "## Limits",
            "- Petitions are not signed (WCP/0.1 has no signature).",
            "- Sub-registries are not enumerable (WCP/0.1).",
        ]
        return "\n".join(lines)


# =====================================================================
# The World: a WCP entity that enforces the Law
# =====================================================================

class PoetryWorld:
    """The first real WCP-conforming world.

    The World is *thin*. It admits identities, validates turns
    against the Law, records everything, and detects convergence.
    It does not generate turns. It does not manage voices. It does
    not know about the curriculum.

    The World's canonical state is *the log*. Any client can read
    the log to reconstruct the full collaboration history. The
    World maintains an internal cache for efficiency; if the cache
    and the log ever disagree, the log wins.
    """

    def __init__(self,
                 entity_id: str,
                 name: str,
                 law: Optional[PoetryWorldLaw] = None):
        self._law = law or PoetryWorldLaw()
        self._manifest = Manifest(
            entity_id=entity_id,
            name=name,
            protocol_version="WCP/0.1",
            law_url=f"poetry://{entity_id}/law",
            act_endpoint=f"poetry://{entity_id}/act",
            log_endpoint=f"poetry://{entity_id}/log",
        )
        # Canonical: the log
        self._log: List[LogEntry] = []
        # Cache (kept in sync with log)
        self._admitted: Dict[str, WCPAdmission] = {}
        self._passports: Dict[str, Passport] = {}
        self._turns: List[Dict] = []  # each turn as a plain dict
        self._converged = False
        self._convergence_reason: Optional[str] = None

    # -- WCP interface ---------------------------------------------

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> Union[
            WCPAdmission, Refusal, Route]:
        """The Law: admits_any_identity.

        Every petition from a stranger is admitted, subject to
        max_admitted. Returns an Admission the petitioner can carry
        back in their passport.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if not self._law.admits_any_identity:
            return self._refuse(
                timestamp,
                petition.petitioner_token,
                "This World does not admit strangers",
                "petition",
            )

        if (self._law.max_admitted is not None
                and len(self._admitted) >= self._law.max_admitted):
            return self._refuse(
                timestamp,
                petition.petitioner_token,
                "The World is full",
                "petition",
            )

        if petition.petitioner_token in self._admitted:
            return self._refuse(
                timestamp,
                petition.petitioner_token,
                "Already admitted",
                "petition",
            )

        # Admit
        admission = WCPAdmission(
            entity_id=self._manifest.entity_id,
            timestamp=timestamp,
        )
        self._admitted[petition.petitioner_token] = admission

        # Update the petitioner's passport with the new admission
        passport = Passport(
            identity=Identity(
                token=petition.petitioner_token,
                name=petition.petitioner_name,
            ),
            admissions=tuple(
                PassportAdmission(world_id=w, timestamp=t)
                for w, t in petition.passport_admissions
            ),
        )
        passport = passport.with_admission(
            PassportAdmission(
                world_id=self._manifest.entity_id,
                timestamp=timestamp,
            )
        )
        self._passports[petition.petitioner_token] = passport

        self._log.append(LogEntry(
            timestamp=timestamp,
            kind="admission",
            actor_token=petition.petitioner_token,
            data={"name": petition.petitioner_name},
        ))
        return admission

    def act(self, act: Act) -> Union[Ack, Refusal]:
        """The Law: validate the turn against the Polyphony protocol."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # -- gate checks --
        if not self._is_admitted(act.actor_token):
            return self._refuse(timestamp, act.actor_token,
                                 "Actor is not admitted", "act")

        if self._converged:
            return self._refuse(timestamp, act.actor_token,
                                 "The collaboration has converged", "act")

        if len(self._turns) >= self._law.max_turns:
            return self._refuse(timestamp, act.actor_token,
                                 "The World has reached its turn limit",
                                 "act")

        if act.type != self._law.required_act_type:
            return self._refuse(timestamp, act.actor_token,
                                 f"Unknown act type: {act.type}", "act")

        # -- validate the turn against the Law --
        payload = act.payload
        ack = payload.get("acknowledgment", "")
        proposal = payload.get("proposal", "")
        invitation = payload.get("invitation", "")
        holds_open = bool(payload.get("holds_open", False))
        stance = payload.get("stance_used")

        if self._law.requires_acknowledgment and not ack:
            return self._refuse(timestamp, act.actor_token,
                                 "Missing acknowledgment", "act")
        if self._law.requires_invitation and not invitation:
            return self._refuse(timestamp, act.actor_token,
                                 "Missing invitation", "act")
        if self._law.requires_holds_open and not holds_open:
            return self._refuse(timestamp, act.actor_token,
                                 "Turn does not hold open", "act")
        if not proposal:
            return self._refuse(timestamp, act.actor_token,
                                 "Missing proposal", "act")

        if (self._law.requires_acknowledgment_references_prior
                and self._turns):
            prior_proposal = self._turns[-1]["proposal"]
            if not self._references(ack, prior_proposal):
                return self._refuse(timestamp, act.actor_token,
                                     "Acknowledgment does not reference "
                                     "the prior turn", "act")

        # -- accept --
        turn_index = len(self._turns)
        self._turns.append({
            "turn_index": turn_index,
            "round": turn_index,
            "actor_token": act.actor_token,
            "actor_name": self._passports[act.actor_token].identity.name,
            "acknowledgment": ack,
            "proposal": proposal,
            "invitation": invitation,
            "holds_open": holds_open,
            "stance_used": stance,
            "timestamp": timestamp,
        })

        self._log.append(LogEntry(
            timestamp=timestamp,
            kind="turn",
            actor_token=act.actor_token,
            data=self._turns[-1],
        ))

        # -- convergence check --
        if self._check_convergence():
            self._converged = True
            self._log.append(LogEntry(
                timestamp=timestamp,
                kind="convergence",
                data={
                    "turn_count": len(self._turns),
                    "window": self._law.convergence_window,
                    "reason": self._convergence_reason,
                },
            ))

        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp)

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        if timestamp is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > timestamp]

    # -- convenience (not part of WCP) ----------------------------

    def turns(self) -> List[Dict]:
        """Current turn cache. Canonical source is the log."""
        return list(self._turns)

    def is_converged(self) -> bool:
        return self._converged

    def describe(self) -> str:
        lines = [
            f"PoetryWorld: {self._manifest.name}",
            f"  entity_id: {self._manifest.entity_id}",
            f"  admitted:  {len(self._admitted)}",
            f"  turns:     {len(self._turns)}",
            f"  converged: {self._converged}",
        ]
        if self._turns:
            last = self._turns[-1]
            lines.append(f"  last turn by: {last['actor_name']}")
        return "\n".join(lines)

    def law(self) -> PoetryWorldLaw:
        return self._law

    # -- internals -------------------------------------------------

    def _is_admitted(self, token: str) -> bool:
        return token in self._admitted

    def _references(self, acknowledgment: str, prior_proposal: str) -> bool:
        """Loose reference check: at least one non-trivial token overlap."""
        stopwords = {
            "the", "a", "an", "and", "or", "but", "of", "to", "in",
            "is", "am", "are", "was", "were", "be", "been", "being",
            "this", "that", "these", "those", "it", "its", "i",
            "you", "he", "she", "we", "they", "my", "your", "his",
            "her", "our", "their", "not", "no", "so", "if", "as",
        }
        prior_tokens = {
            t.strip(".,;:!?\"'()[]").lower()
            for t in prior_proposal.split()
            if t.strip(".,;:!?\"'()[]").lower() not in stopwords
            and len(t) > 2
        }
        ack_tokens = {
            t.strip(".,;:!?\"'()[]").lower()
            for t in acknowledgment.split()
            if t.strip(".,;:!?\"'()[]").lower() not in stopwords
            and len(t) > 2
        }
        return bool(prior_tokens & ack_tokens)

    def _check_convergence(self) -> bool:
        window = self._law.convergence_window
        if len(self._turns) < window + 1:
            return False
        recent = self._turns[-window:]

        # Reason 1: proposals echo each other
        similarities = []
        for i in range(len(recent) - 1):
            a = {
                t.strip(".,;:!?\"'()[]").lower()
                for t in recent[i]["proposal"].split()
                if t.strip(".,;:!?\"'()[]")
            }
            b = {
                t.strip(".,;:!?\"'()[]").lower()
                for t in recent[i + 1]["proposal"].split()
                if t.strip(".,;:!?\"'()[]")
            }
            if a and b:
                similarities.append(len(a & b) / len(a | b))
            else:
                similarities.append(0.0)
        if (similarities
                and all(s >= self._law.convergence_similarity
                        for s in similarities)):
            self._convergence_reason = (
                f"last {window} turns are echo "
                f"(similarity ≥ {self._law.convergence_similarity:.0%})"
            )
            return True

        # Reason 2: all recent invitations are the same
        invitations = [t["invitation"] for t in recent]
        if invitations and len(set(invitations)) == 1:
            self._convergence_reason = (
                f"last {window} turns pose the same invitation"
            )
            return True

        return False

    def _refuse(self, timestamp: str, actor: str, reason: str,
                 kind: str) -> Refusal:
        self._log.append(LogEntry(
            timestamp=timestamp,
            kind=f"{kind}_refused",
            actor_token=actor,
            data={"reason": reason},
        ))
        return Refusal(reason=reason)
