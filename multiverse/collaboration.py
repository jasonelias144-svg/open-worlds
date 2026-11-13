"""The first collaboration: the whole core, running end to end.

From the DeepSeek sketch's component 7. A registry lists a poetry world
once it passes the conformance test. A seed poet enters the world and
opens a poem. Three apprentice poets enter, take turns under the
world's law until the poem converges or the session ends, and leave. The
report is built from the logs alone.

Run it:  python3 -m multiverse.collaboration

Changed from the sketch:
  - The demonstration starts from a known poem, as the founder asked
    ("We should use a known poem to start anything"): Emily Dickinson's
    "Hope is the thing with feathers" (1891), with stanzas of her other
    poems as the apprentices' portfolios. The sketch opened with a poem
    of the founder's, which the founder preferred not to make the
    starting example.
  - Everyone leaves at the end, so the log shows departures, and each
    apprentice's passport shows where it has been: since course step 3,
    as stamps the worlds signed, checked offline at the end.
  - An apprentice whose turn fails to generate is counted in the report
    instead of being skipped silently.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Dict, List, Optional

from .apprentice import (Apprentice, CurriculumRunner, PortfolioPoem,
                         TheoreticalStance)
from .identity import Identity, Individual, create_individual
from .passport import LeaveNote, Passport, Stamp, verify_passport
from .protocol import (Ack, ActResponse, Admission, Departure, LeaveResponse,
                       LogEntry, PetitionResponse, Refusal)
from .poetry_world import PoetryWorld, PoetryWorldLaw, turns_from_log
from .registry import MultiverseRegistry


# -- a client: speaks the protocol for one individual -------------------

@dataclass
class ClientIdentity:
    """An individual (with its key) and the passport it carries: the
    stamps worlds have signed for it, and its own signed leaves."""
    individual: Individual
    passport: Passport = None
    is_admitted_to: Dict[str, Admission] = field(default_factory=dict)

    def __post_init__(self):
        if self.passport is None:
            self.passport = Passport(self.individual.identity)

    @property
    def identity(self) -> Identity:
        return self.individual.identity

    def keep(self, entry: Optional[Dict]) -> None:
        """Add a stamp a world gave to the passport, if it is a stamp for
        this individual that verifies."""
        try:
            stamp = Stamp.from_entry(entry)
        except ValueError:
            return
        if stamp.holder == self.individual.token and stamp.verifies():
            self.passport = self.passport.with_stamp(stamp)


def make_client(name: str) -> ClientIdentity:
    return ClientIdentity(individual=create_individual(name))


def petition_world(client: ClientIdentity, world) -> PetitionResponse:
    """Petition, signed and carrying the passport; on admission, keep the
    arrival stamp."""
    m = world.manifest()
    response = world.petition(client.individual.petition(
        m, client.passport.entries(),
        message=f"{client.identity.name} petitions {m.name}."))
    if isinstance(response, Admission):
        client.is_admitted_to[m.entity_id] = response
        client.keep(response.stamp)
    return response


def act_on_world(client: ClientIdentity, world, act_type: str,
                 payload: Dict, attachment: object = None) -> ActResponse:
    act = client.individual.act(world.manifest(), act_type, payload)
    if attachment is not None:
        act = replace(act, attachment=attachment)
    response = world.act(act)
    if isinstance(response, Ack):
        client.keep(response.stamp)
    return response


def leave_world(client: ClientIdentity, world) -> LeaveResponse:
    """Leave, naming the arrival this closes; the signed leave goes into
    the passport, and so does the departure stamp, if the world gives
    one."""
    m = world.manifest()
    arrival = client.passport.open_arrival(m.world_key)
    leave = client.individual.leave(
        m, closes=arrival.fingerprint() if arrival else "")
    response = world.leave(leave)
    if isinstance(response, Departure):
        client.is_admitted_to.pop(m.entity_id, None)
        if arrival is not None and not response.already_left:
            client.passport = client.passport.with_leave(
                LeaveNote.of(m.entity_id, m.world_key, leave))
            client.keep(response.stamp)
    return response


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

# The seed: Emily Dickinson, "Hope is the thing with feathers", Poems,
# Second Series (1891). The portfolio: stanzas of other Dickinson poems
# from the 1890 and 1891 editions. Public domain; text from Project
# Gutenberg eBook #12242. Typography only is changed: spaces before
# apostrophes closed up ("I 've" to "I've"), "--" set as a dash.
SEED_POET = "Seed Poet"
SEED_ACKNOWLEDGMENT = "(seed) Emily Dickinson, 1891"
SEED_PROPOSAL = ("Hope is the thing with feathers\n"
                 "That perches in the soul,\n"
                 "And sings the tune without the words,\n"
                 "And never stops at all,\n"
                 "\n"
                 "And sweetest in the gale is heard;\n"
                 "And sore must be the storm\n"
                 "That could abash the little bird\n"
                 "That kept so many warm.\n"
                 "\n"
                 "I've heard it in the chillest land,\n"
                 "And on the strangest sea;\n"
                 "Yet, never, in extremity,\n"
                 "It asked a crumb of me.")
SEED_INVITATION = "What does the bird sing, when the tune has no words?"

_PORTFOLIO = [
    # "A bird came down the walk" (1891), stanza 1
    ("A bird came down the walk:\nHe did not know I saw;\n"
     "He bit an angle-worm in halves\nAnd ate the fellow, raw.",
     "ecocritical", "image/cycle-1"),
    # the same poem, stanza 4
    ("Like one in danger; cautious,\nI offered him a crumb,\n"
     "And he unrolled his feathers\nAnd rowed him softer home",
     "psychoanalytic", "response/cycle-1"),
    # "I never saw a moor" (1890), stanza 1
    ("I never saw a moor,\nI never saw the sea;\n"
     "Yet know I how the heather looks,\nAnd what a wave must be.",
     "formalist", "form/cycle-1"),
    # "The soul selects her own society" (1890), stanza 1
    ("The soul selects her own society,\nThen shuts the door;\n"
     "On her divine majority\nObtrude no more.",
     "feminist", "voice/cycle-1"),
    # "Success is counted sweetest" (1890), stanza 1
    ("Success is counted sweetest\nBy those who ne'er succeed.\n"
     "To comprehend a nectar\nRequires sorest need.",
     "marxist", "tradition/cycle-1"),
    # "Wild nights! Wild nights!" (1891), stanza 3
    ("Rowing in Eden!\nAh! the sea!\nMight I but moor\nTo-night in thee!",
     "psychoanalytic", "voice/cycle-2"),
    # the same poem, stanza 2
    ("Futile the winds\nTo a heart in port, —\nDone with the compass,\n"
     "Done with the chart.", "structuralist", "line/cycle-2"),
    # "I'm nobody! Who are you?" (1891), stanza 1
    ("I'm nobody! Who are you?\nAre you nobody, too?\n"
     "Then there's a pair of us — don't tell!\nThey'd banish us, you know.",
     "deconstructive", "voice/cycle-3"),
    # "The soul selects her own society", stanza 2
    ("Unmoved, she notes the chariot's pausing\nAt her low gate;\n"
     "Unmoved, an emperor is kneeling\nUpon her mat.",
     "feminist", "image/cycle-3"),
    # "A bird came down the walk", stanza 3
    ("He glanced with rapid eyes\nThat hurried all abroad, —\n"
     "They looked like frightened beads, I thought;\n"
     "He stirred his velvet head", "ecocritical", "image/cycle-3"),
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
                         f"poems, {a['stance_count']} stances; turns: "
                         f"{a['turns_generated']} written, "
                         f"{a['turns_failed']} failed; passport: "
                         f"{', '.join(a['passport']) or '(empty)'}, "
                         f"{a['stamps']} stamps, "
                         + ("all verify" if a["passport_verifies"]
                            else "NOT VERIFIED"))
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
                              {"entity_id": self.world.manifest().entity_id,
                               "world_key": self.world.world_key},
                              attachment=self.world)
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
        seed_poet = make_client(SEED_POET)
        if not isinstance(petition_world(seed_poet, self.world), Admission):
            raise RuntimeError("the seed poet was not admitted")
        opened = act_on_world(seed_poet, self.world, "poem.turn", {
            "acknowledgment": SEED_ACKNOWLEDGMENT, "proposal": SEED_PROPOSAL,
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
            "passport": c.passport.worlds_visited(),
            "passport_verifies": verify_passport(c.passport).ok,
            "stamps": len(c.passport),
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
