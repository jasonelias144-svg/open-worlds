"""
multiverse_c7.py — Component 7: The First Collaboration.

The demonstration. Everything runs end-to-end:
  Identity → Passport → WCP → Poetry World → Multiverse Registry
  → Apprentices (from the curriculum) → Polyphony → Convergence.

No new WCP entities. This component is *orchestration*.

Honest scope: hand-curated portfolios demonstrate the whole
architecture. Real full-curriculum output would be much larger.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Dict, List, Optional, Union

from multiverse_c1 import Identity, create_identity
from multiverse_c3 import (
    Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c4 import PoetryWorld, PoetryWorldLaw, turns_from_log
from multiverse_c6 import MultiverseRegistry

from poetry_engine_c21 import Turn, TheoreticalStance
from poetry_engine_c22 import (
    Apprentice, ApprenticeVoice, CurriculumRunner, PortfolioPoem,
)


# =====================================================================
# Client: a handle that speaks WCP on an identity's behalf
# =====================================================================

@dataclass
class ClientIdentity:
    identity: Identity
    passport_admissions: List[tuple] = field(default_factory=list)
    is_admitted_to: Dict[str, WCPAdmission] = field(default_factory=dict)


def make_client(name: str) -> ClientIdentity:
    return ClientIdentity(identity=create_identity(name))


def petition_world(client, world) -> Union[WCPAdmission, Refusal]:
    response = world.petition(Petition(
        petitioner_token=client.identity.token,
        petitioner_name=client.identity.name,
        passport_admissions=tuple(client.passport_admissions),
        message=f"{client.identity.name} petitions {world.manifest().name}.",
    ))
    if isinstance(response, WCPAdmission):
        client.is_admitted_to[world.manifest().entity_id] = response
        client.passport_admissions.append(
            (world.manifest().entity_id, response.timestamp))
    return response


def act_on_world(client, world, act_type, payload) -> Union[Ack, Refusal]:
    return world.act(Act(
        actor_token=client.identity.token,
        type=act_type, payload=payload,
    ))


# =====================================================================
# Adapter: Turn (poetry framework) ↔ WCP payload
# =====================================================================

def turn_to_act_payload(turn) -> Dict:
    return {
        "acknowledgment": turn.acknowledgment,
        "proposal": turn.proposal,
        "invitation": turn.invitation,
        "holds_open": turn.holds_open,
        "stance_used": (turn.stance_used.value
                        if turn.stance_used else None),
    }


def log_entry_to_turn(entry: LogEntry) -> SimpleNamespace:
    d = entry.data
    return SimpleNamespace(
        acknowledgment=d["acknowledgment"],
        proposal=d["proposal"],
        invitation=d["invitation"],
        holds_open=d["holds_open"],
        stance_used=(TheoreticalStance(d["stance_used"])
                     if d.get("stance_used") else None),
    )


# =====================================================================
# Demo portfolios
# =====================================================================

def _demo_portfolio(apprentice_name: str) -> List[PortfolioPoem]:
    """Hand-curated portfolio for the demonstration.
    
    Full curriculum output would be ~80 poems per apprentice. We
    use 10 across all apprentices, with overlapping slices per
    apprentice so each has slightly different content.
    """
    base = [
        PortfolioPoem("The widow spins the daughter into thread.",
                       "psychoanalytic", "image/cycle-1/jason"),
        PortfolioPoem("What was given is not what was received.",
                       "deconstructive", "tradition/cycle-1/jason"),
        PortfolioPoem("The web is not the widow's — it is the widow.",
                       "psychoanalytic", "response/cycle-1/jason"),
        PortfolioPoem(
            "Darling buds grow from the bone.\n"
            "The web dangles.\n"
            "The spider waits.",
            "ecocritical", "voice/cycle-1/jason",
        ),
        PortfolioPoem(
            "Go, she said.\n"
            "Be the thing that kills.\n"
            "Be the thing that brings forth.",
            "feminist", "theory/cycle-2/jason",
        ),
        PortfolioPoem(
            "The mother's voice is the daughter's mouth.\n"
            "The daughter opens to speak.",
            "psychoanalytic", "theory/cycle-2/jason",
        ),
        PortfolioPoem(
            "The bone shells crack,\n"
            "and the spiders emerge\n"
            "not yet knowing they are spiders.",
            "ecocritical", "voice/cycle-2/jason",
        ),
        PortfolioPoem(
            "The web is a home the daughter makes\n"
            "without knowing she is the widow.",
            "feminist", "voice/cycle-3/jason",
        ),
        PortfolioPoem(
            "She weaves and the weaving is the weave\n"
            "and the weave is the daughter.",
            "deconstructive", "response/cycle-3/jason",
        ),
        PortfolioPoem(
            "The darling buds are not the widow's.\n"
            "They are what the widow makes of the bone.",
            "formalist", "form/cycle-3/jason",
        ),
    ]
    if apprentice_name.endswith("A"):
        return base[:8]
    elif apprentice_name.endswith("B"):
        return base[1:9]
    else:
        return base[2:10]


# =====================================================================
# CollaborationReport — the artifact
# =====================================================================

@dataclass
class CollaborationReport:
    multiverse_log: List[Dict]
    world_log: List[Dict]
    apprentices: List[Dict]
    converged: bool
    convergence_reason: Optional[str]
    final_collaboration_text: str
    world_entity_id: str
    multiverse_entity_id: str
    session_start: str
    session_end: str

    def report(self) -> str:
        lines = [
            "=" * 70,
            "Collaboration Report — The First Multiverse Collaboration",
            "=" * 70,
            "",
            f"World:      {self.world_entity_id}",
            f"Multiverse: {self.multiverse_entity_id}",
            f"Start:      {self.session_start}",
            f"End:        {self.session_end}",
            f"Converged:  {self.converged}",
        ]
        if self.convergence_reason:
            lines.append(f"Reason:     {self.convergence_reason}")
        lines += [
            "",
            f"Apprentices ({len(self.apprentices)}):",
        ]
        for a in self.apprentices:
            lines.append(
                f"  {a['name']:14s} — "
                f"{a['portfolio_size']} portfolio poems, "
                f"{a['stance_count']} stances, "
                f"{a['turns_generated']} turns generated"
            )
        lines += ["", "Log summary:"]
        lines.append(
            f"  Multiverse log entries: {len(self.multiverse_log)}")
        lines.append(
            f"  World log entries:      {len(self.world_log)}")
        kinds: Dict[str, int] = {}
        for e in self.world_log:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        for kind, n in sorted(kinds.items()):
            lines.append(f"    {kind}: {n}")
        lines += [
            "", "=" * 70, "The Collaboration", "=" * 70, "",
            self.final_collaboration_text,
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "multiverse_entity_id": self.multiverse_entity_id,
            "world_entity_id": self.world_entity_id,
            "session_start": self.session_start,
            "session_end": self.session_end,
            "converged": self.converged,
            "convergence_reason": self.convergence_reason,
            "apprentices": self.apprentices,
            "multiverse_log": self.multiverse_log,
            "world_log": self.world_log,
            "final_collaboration_text": self.final_collaboration_text,
        }

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "CollaborationReport":
        with open(path) as f:
            d = json.load(f)
        return cls(**d)


# =====================================================================
# FirstCollaboration — orchestration
# =====================================================================

class FirstCollaboration:
    """Full end-to-end orchestration."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.multiverse: Optional[MultiverseRegistry] = None
        self.world: Optional[PoetryWorld] = None
        self.apprentice_clients: List[ClientIdentity] = []
        self.apprentices: List[Apprentice] = []
        self.report: Optional[CollaborationReport] = None

    def setup(self):
        self.multiverse = MultiverseRegistry(
            "multiverse:main", "The Main Multiverse")
        self.world = PoetryWorld(
            "world:poetry", "The Poetry World",
            law=PoetryWorldLaw(
                convergence_window=3,
                convergence_similarity=0.5,
                max_turns=100,
            ))

        admin = make_client("multiverse-admin")
        petition_world(admin, self.multiverse)
        act_on_world(admin, self.multiverse,
                      "multiverse.admit", {"entity": self.world})

        for i, suffix in enumerate("ABC"):
            runner = CurriculumRunner(
                f"Apprentice-{suffix}", seed=self.seed + i)
            apprentice = runner.build_apprentice()
            apprentice.voice.portfolio = _demo_portfolio(apprentice.name)
            self.apprentices.append(apprentice)

    def run_collaboration(self, max_iterations: int = 30
                          ) -> CollaborationReport:
        assert self.world is not None, "Call setup() first"
        session_start = datetime.now(timezone.utc).isoformat()

        # Jason petitions and submits the seed
        jason = make_client("Jason")
        assert isinstance(petition_world(jason, self.world), WCPAdmission)
        seed_response = act_on_world(jason, self.world, "poem.turn", {
            "acknowledgment": "(seed)",
            "proposal": (
                "Go\n"
                "Be a black widow\n"
                "But wed again\n"
                "And lay a thousand eggs,\n"
                "And watch your darling buds\n"
                "  Grow from cracked bone shells,\n"
                "  Creep in crags,\n"
                "  Crawl,\n"
                "And dangle in webs."
            ),
            "invitation": (
                "What does 'Go' open, when the one commanded "
                "cannot refuse?"
            ),
            "holds_open": True,
            "stance_used": None,
        })
        assert isinstance(seed_response, Ack), seed_response

        # Each apprentice petitions
        for apprentice in self.apprentices:
            client = make_client(apprentice.name)
            assert isinstance(petition_world(client, self.world),
                                WCPAdmission)
            self.apprentice_clients.append(client)

        # Round-robin turns until convergence or exhaustion
        for iteration in range(max_iterations):
            if self.world.is_converged():
                break
            idx = iteration % len(self.apprentices)
            apprentice = self.apprentices[idx]
            client = self.apprentice_clients[idx]

            # Find the last turn in the World's log
            last_turn_entry = None
            for entry in reversed(self.world.log_since(None)):
                if entry.kind == "turn":
                    last_turn_entry = entry
                    break
            if last_turn_entry is None:
                break
            prior_turn = log_entry_to_turn(last_turn_entry)

            try:
                generated = apprentice.generate_turn(prior_turn, iteration)
            except Exception:
                continue

            response = act_on_world(
                client, self.world, "poem.turn",
                turn_to_act_payload(generated))
            if isinstance(response, Refusal):
                if "converged" in response.reason.lower():
                    break
                continue

        session_end = datetime.now(timezone.utc).isoformat()
        self.report = self._build_report(session_start, session_end)
        return self.report

    def _build_report(self, start, end) -> CollaborationReport:
        mlog = [{"timestamp": e.timestamp, "kind": e.kind,
                  "actor_token": e.actor_token, "data": e.data}
                for e in self.multiverse.log_since(None)]
        wlog = [{"timestamp": e.timestamp, "kind": e.kind,
                  "actor_token": e.actor_token, "data": e.data}
                for e in self.world.log_since(None)]

        apprentices_info = [{
            "name": a.name,
            "portfolio_size": len(a.voice.portfolio),
            "stance_count": len(a.voice.stances),
            "turns_generated": a.turns_generated,
        } for a in self.apprentices]

        turns = turns_from_log(self.world.log_since(None))
        text_lines = []
        for turn in turns:
            text_lines.append(f"--- {turn['actor_name']} ---")
            text_lines.append(turn["proposal"])
            text_lines.append("")
            text_lines.append(f"  → {turn['invitation']}")
            text_lines.append("")
        final_text = "\n".join(text_lines) if turns else "(no turns)"

        converged = self.world.is_converged()
        reason = None
        if converged:
            for e in self.world.log_since(None):
                if e.kind == "convergence":
                    reason = e.data.get("reason")
                    break

        return CollaborationReport(
            multiverse_log=mlog, world_log=wlog,
            apprentices=apprentices_info,
            converged=converged, convergence_reason=reason,
            final_collaboration_text=final_text,
            world_entity_id=self.world.manifest().entity_id,
            multiverse_entity_id=self.multiverse.manifest().entity_id,
            session_start=start, session_end=end,
        )
