"""The first collaboration: the whole core, running end to end.

From the DeepSeek sketch's component 7. A registry lists a poetry world
once it passes the conformance test. A seed poet enters the world and
opens a poem. Three apprentice poets enter, take turns under the
world's law until the poem converges or the session ends, and leave. The
report is built from the logs alone.

Run it:  python3 -m multiverse.collaboration

Changed from the sketch:
  - The seed poem and the apprentices' portfolios are new, written for
    this repository. The sketch opened with a poem of the founder's,
    which stays out until the founder decides it may be public (the
    repository is CC0).
  - Everyone leaves at the end, so the log shows departures, and each
    apprentice's passport shows where it has been.
  - An apprentice whose turn fails to generate is counted in the report
    instead of being skipped silently.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

from .apprentice import (Apprentice, CurriculumRunner, PortfolioPoem,
                         TheoreticalStance)
from .identity import Identity, create_identity
from .protocol import (Ack, Act, ActResponse, Admission, Departure,
                       LogEntry, Petition, PetitionResponse, Refusal)
from .poetry_world import PoetryWorld, PoetryWorldLaw, turns_from_log
from .registry import MultiverseRegistry


# -- a client: speaks the protocol for one identity --------------------

@dataclass
class ClientIdentity:
    identity: Identity
    passport_admissions: List[Tuple[str, str]] = field(default_factory=list)
    is_admitted_to: Dict[str, Admission] = field(default_factory=dict)


def make_client(name: str) -> ClientIdentity:
    return ClientIdentity(identity=create_identity(name))


def petition_world(client: ClientIdentity, world) -> PetitionResponse:
    """Petition, and on admission add the stamp to the client's passport."""
    response = world.petition(Petition(
        petitioner_token=client.identity.token,
        petitioner_name=client.identity.name,
        passport_admissions=tuple(client.passport_admissions),
        message=f"{client.identity.name} petitions {world.manifest().name}."))
    if isinstance(response, Admission):
        entity_id = world.manifest().entity_id
        client.is_admitted_to[entity_id] = response
        client.passport_admissions.append((entity_id, response.timestamp))
    return response


def act_on_world(client: ClientIdentity, world, act_type: str,
                 payload: Dict) -> ActResponse:
    return world.act(Act(actor_token=client.identity.token,
                         type=act_type, payload=payload))


def leave_world(client: ClientIdentity, world) -> Departure:
    departure = world.leave(client.identity.token)
    client.is_admitted_to.pop(world.manifest().entity_id, None)
    return departure


# -- a turn as an act's payload, and back -------------------------------

def turn_to_act_payload(turn) -> Dict:
    return {
        "acknowledgment": turn.acknowledgment,
        "proposal": turn.proposal,
        "invitation": turn.invitation,
        "holds_open": turn.holds_open,
        "stance_used": turn.stance_used.value if turn.stance_used else None,
    }


def log_entry_to_turn(entry: LogEntry) -> SimpleNamespace:
    d = entry.data
    return SimpleNamespace(
        acknowledgment=d["acknowledgment"], proposal=d["proposal"],
        invitation=d["invitation"], holds_open=d["holds_open"],
        stance_used=(TheoreticalStance(d["stance_used"])
                     if d.get("stance_used") else None))


# -- the demonstration's poems ------------------------------------------

SEED_PROPOSAL = ("The river keeps its shape\n"
                 "by never keeping its water.\n"
                 "The stone stays where it is,\n"
                 "and the river bends around it.")
SEED_INVITATION = "What does the stone give the river, by not moving?"

_PORTFOLIO = [
    ("The stone does not hold the river back.\n"
     "It gives the river a voice.", "psychoanalytic", "image/cycle-1"),
    ("What the water carries is not what the water is.",
     "deconstructive", "tradition/cycle-1"),
    ("The river is not around the stone —\n"
     "it is the stone, worn into water.", "psychoanalytic",
     "response/cycle-1"),
    ("Moss on the stone.\nThe river cold.\nThe heron waits.",
     "ecocritical", "voice/cycle-1"),
    ("Stay, said the river.\nBe the thing that stays.\n"
     "Be the thing I bend for.", "feminist", "theory/cycle-2"),
    ("The river's voice is the stone's mouth.\nThe stone opens to speak.",
     "psychoanalytic", "theory/cycle-2"),
    ("The stone wears down,\nand the sand goes on\n"
     "not knowing it was stone.", "ecocritical", "voice/cycle-2"),
    ("The bend is a home the river makes\n"
     "without knowing it is the stone's.", "feminist", "voice/cycle-3"),
    ("It bends, and the bending is the river,\n"
     "and the river is the bend.", "deconstructive", "response/cycle-3"),
    ("The shape is not the river's.\n"
     "It is what the river makes of the stone.", "formalist",
     "form/cycle-3"),
]


def demo_portfolio(apprentice_name: str) -> List[PortfolioPoem]:
    """Eight of the ten poems, a different slice for each apprentice."""
    poems = [PortfolioPoem(text, voice, f"{tag}/demo")
             for text, voice, tag in _PORTFOLIO]
    if apprentice_name.endswith("A"):
        return poems[:8]
    if apprentice_name.endswith("B"):
        return poems[1:9]
    return poems[2:10]


# -- the report ---------------------------------------------------------

def _entry_dict(e: LogEntry) -> Dict:
    return {"timestamp": e.timestamp, "kind": e.kind,
            "actor_token": e.actor_token, "data": e.data}


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
        lines = ["=" * 70, "The first collaboration", "=" * 70, "",
                 f"World:      {self.world_entity_id}",
                 f"Multiverse: {self.multiverse_entity_id}",
                 f"Converged:  {self.converged}"]
        if self.convergence_reason:
            lines.append(f"Reason:     {self.convergence_reason}")
        lines += ["", f"Apprentices ({len(self.apprentices)}):"]
        for a in self.apprentices:
            lines.append(f"  {a['name']:14s} {a['portfolio_size']} portfolio "
                         f"poems, {a['stance_count']} stances, "
                         f"{a['turns_generated']} turns written, "
                         f"{a['turns_failed']} failed; passport: "
                         f"{', '.join(a['passport']) or '(empty)'}")
        kinds: Dict[str, int] = {}
        for e in self.world_log:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        lines += ["", f"Registry log entries: {len(self.multiverse_log)}",
                  f"World log entries:    {len(self.world_log)}"]
        lines += [f"  {kind}: {n}" for kind, n in sorted(kinds.items())]
        lines += ["", "=" * 70, "The poem", "=" * 70, "",
                  self.final_collaboration_text]
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return dict(self.__dict__)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "CollaborationReport":
        with open(path) as f:
            return cls(**json.load(f))


# -- the orchestration --------------------------------------------------

class FirstCollaboration:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.multiverse: Optional[MultiverseRegistry] = None
        self.world: Optional[PoetryWorld] = None
        self.apprentices: List[Apprentice] = []
        self.apprentice_clients: List[ClientIdentity] = []
        self.turns_failed: Dict[str, int] = {}
        self.report: Optional[CollaborationReport] = None

    def setup(self) -> None:
        self.multiverse = MultiverseRegistry("multiverse:main",
                                             "The Main Multiverse")
        self.world = PoetryWorld(
            "world:poetry", "The Poetry World",
            law=PoetryWorldLaw(convergence_window=3,
                               convergence_similarity=0.5, max_turns=100))
        admin = make_client("multiverse-admin")
        petition_world(admin, self.multiverse)
        listed = act_on_world(admin, self.multiverse, "multiverse.admit",
                              {"entity": self.world})
        if not isinstance(listed, Ack):
            raise RuntimeError(f"the poetry world was not listed: {listed}")
        for i, suffix in enumerate("ABC"):
            apprentice = CurriculumRunner(
                f"Apprentice-{suffix}", seed=self.seed + i).build_apprentice()
            apprentice.voice.portfolio = demo_portfolio(apprentice.name)
            self.apprentices.append(apprentice)

    def run_collaboration(self, max_iterations: int = 30
                          ) -> CollaborationReport:
        if self.world is None:
            raise RuntimeError("call setup() first")
        start = datetime.now(timezone.utc).isoformat()
        seed_poet = make_client("Seed Poet")
        if not isinstance(petition_world(seed_poet, self.world), Admission):
            raise RuntimeError("the seed poet was not admitted")
        opened = act_on_world(seed_poet, self.world, "poem.turn", {
            "acknowledgment": "(seed)", "proposal": SEED_PROPOSAL,
            "invitation": SEED_INVITATION, "holds_open": True,
            "stance_used": None})
        if not isinstance(opened, Ack):
            raise RuntimeError(f"the seed turn was refused: {opened}")
        for apprentice in self.apprentices:
            client = make_client(apprentice.name)
            if not isinstance(petition_world(client, self.world), Admission):
                raise RuntimeError(f"{apprentice.name} was not admitted")
            self.apprentice_clients.append(client)
            self.turns_failed[apprentice.name] = 0

        for iteration in range(max_iterations):
            if self.world.is_converged():
                break
            idx = iteration % len(self.apprentices)
            apprentice = self.apprentices[idx]
            client = self.apprentice_clients[idx]
            last = next((e for e in reversed(self.world.log_since(None))
                         if e.kind == "turn"), None)
            if last is None:
                break
            try:
                turn = apprentice.generate_turn(log_entry_to_turn(last),
                                                iteration)
            except Exception:
                self.turns_failed[apprentice.name] += 1
                continue
            response = act_on_world(client, self.world, "poem.turn",
                                    turn_to_act_payload(turn))
            if (isinstance(response, Refusal)
                    and "converged" in response.reason.lower()):
                break

        for client in [seed_poet] + self.apprentice_clients:
            leave_world(client, self.world)
        end = datetime.now(timezone.utc).isoformat()
        self.report = self._build_report(start, end)
        return self.report

    def _build_report(self, start: str, end: str) -> CollaborationReport:
        world_log = self.world.log_since(None)
        apprentices = [{
            "name": a.name,
            "portfolio_size": len(a.voice.portfolio),
            "stance_count": len(a.voice.stances),
            "turns_generated": a.turns_generated,
            "turns_failed": self.turns_failed.get(a.name, 0),
            "passport": [w for w, _ in c.passport_admissions],
        } for a, c in zip(self.apprentices, self.apprentice_clients)]
        turns = turns_from_log(world_log)
        text: List[str] = []
        for turn in turns:
            text += [f"--- {turn['actor_name']} ---", turn["proposal"], "",
                     f"  → {turn['invitation']}", ""]
        reason = next((e.data.get("reason") for e in world_log
                       if e.kind == "convergence"), None)
        return CollaborationReport(
            multiverse_log=[_entry_dict(e)
                            for e in self.multiverse.log_since(None)],
            world_log=[_entry_dict(e) for e in world_log],
            apprentices=apprentices,
            converged=self.world.is_converged(),
            convergence_reason=reason,
            final_collaboration_text="\n".join(text) if turns
            else "(no turns)",
            world_entity_id=self.world.manifest().entity_id,
            multiverse_entity_id=self.multiverse.manifest().entity_id,
            session_start=start, session_end=end)


def main(argv: List[str]) -> int:
    fc = FirstCollaboration(seed=42)
    fc.setup()
    print(fc.run_collaboration(max_iterations=30).report())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
