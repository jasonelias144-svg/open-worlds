"""The first journey (course step 5): from the corridor into the chemistry
world, on to the poetry world, and back, with the passport checked at
every door.

Three worlds, each a key, each knowing the others' keys: the corridor
through its doors, and the chemistry and poetry worlds because they share
a door with it (`Entity.know`). An individual walks the corridor to its
chemistry door, goes through (its signed leave here, its petition there),
makes a dipeptide out of two glycines, goes on to the poetry world, adds
a line, and comes back to the corridor, arriving at the poetry door, and
walks back to the entrance. Every world it enters checks its passport,
offline, against the keys it knows.

    python3 -m multiverse.journey
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from world.core import World

from .chemistry_world import ChemistryWorld
from .collaboration import (ClientIdentity, act_on_world, leave_world,
                            make_client, petition_world)
from .corridor_world import CorridorWorld, CorridorWorldLaw, Door
from .passport import verify_passport
from .poetry_world import PoetryWorld
from .protocol import Ack, Admission

# Emily Dickinson, "Hope is the thing with feathers" (1891).
LINE = "Hope is the thing with feathers"


def build_worlds(seed: int = 0) -> Tuple[CorridorWorld, ChemistryWorld,
                                         PoetryWorld]:
    """The corridor, with a door at its east end to each of the other two,
    and all three knowing each other's keys."""
    chemistry = ChemistryWorld("world:chemistry", "The Chemistry World")
    poetry = PoetryWorld("world:poetry", "The Poetry World")
    law = CorridorWorldLaw(seed=seed, doors=(
        Door((11, 0), chemistry.manifest().entity_id, chemistry.world_key,
             "the chemistry world"),
        Door((11, 2), poetry.manifest().entity_id, poetry.world_key,
             "the poetry world")))
    corridor = CorridorWorld("world:corridor", "The Corridor", law)
    for a, b in ((chemistry, corridor), (poetry, corridor),
                 (chemistry, poetry), (poetry, chemistry)):
        a.know(b.manifest())
    return corridor, chemistry, poetry


def walk_to(client: ClientIdentity, corridor: CorridorWorld,
            cell: Tuple[int, int], max_steps: int = 200) -> Tuple[int, int]:
    """Step towards `cell`, east-west first, until there (or stuck)."""
    token = client.individual.token
    for _ in range(max_steps):
        x, y = corridor.where(token)["cell"]
        if (x, y) == cell:
            break
        if x != cell[0]:
            step = {"dx": 1 if cell[0] > x else -1, "dy": 0}
        else:
            step = {"dx": 0, "dy": 1 if cell[1] > y else -1}
        if not isinstance(act_on_world(client, corridor, "corridor.move",
                                       step), Ack):
            break
    return corridor.where(token)["cell"]


def journey(seed: int = 0) -> Dict:
    """The whole journey. Returns what happened, step by step, and the
    worlds, for checking."""
    corridor, chemistry, poetry = build_worlds(seed)
    alice = make_client("Alice")
    token = alice.individual.token
    steps: List[str] = []

    assert isinstance(petition_world(alice, corridor), Admission)
    steps.append(f"enters the corridor at {corridor.where(token)['cell']}")
    door = corridor.doors()[0]
    steps.append(f"walks to {walk_to(alice, corridor, door.cell)}, the "
                 f"door to {door.name}")

    leave_world(alice, corridor)
    shown = len(alice.passport)
    assert isinstance(petition_world(alice, chemistry), Admission)
    steps.append("goes through; the chemistry world checks her passport "
                 f"({shown} stamps) and admits her")
    made = act_on_world(alice, chemistry, "chemistry.react", {
        "rule": "amide formation (condensation)",
        "reactants": ["glycine", "glycine"]})
    assert isinstance(made, Ack)
    steps.append("joins two glycines into glycylglycine, and gets a made "
                 "stamp")

    leave_world(alice, chemistry)
    shown = len(alice.passport)
    assert isinstance(petition_world(alice, poetry), Admission)
    steps.append("goes on to the poetry world, which checks her passport "
                 f"({shown} stamps) and admits her")
    turn = act_on_world(alice, poetry, "poem.turn", {
        "acknowledgment": "(seed)", "proposal": LINE,
        "invitation": "What perches in the soul?", "holds_open": True})
    assert isinstance(turn, Ack)
    steps.append(f'adds a line: "{LINE}"')

    leave_world(alice, poetry)
    shown = len(alice.passport)
    assert isinstance(petition_world(alice, corridor), Admission)
    back = corridor.where(token)
    steps.append(f"comes back to the corridor, which checks her passport "
                 f"({shown} stamps) and puts her at {back['cell']}, the "
                 f"door to {back['door'].name}")
    steps.append(f"walks back to {walk_to(alice, corridor, (0, 2))}, the "
                 "entrance, and leaves")
    leave_world(alice, corridor)

    check = verify_passport(alice.passport, corridor.known_keys())
    return {"steps": steps, "passport": alice.passport, "check": check,
            "worlds": (corridor, chemistry, poetry), "client": alice}


def main() -> None:
    result = journey()
    print("The first journey\n")
    for i, step in enumerate(result["steps"], 1):
        print(f"  {i:2d}. Alice {step}")
    check = result["check"]
    print(f"\nHer passport: {len(result['passport'])} stamps, "
          f"{len(result['passport'].leaves)} signed leaves, "
          f"{'all verify' if check.ok else 'PROBLEMS: ' + str(check.problems)}")
    for v in check.visits:
        print(f"  {v.world_id:18s} left: {v.left or 'still there':9s} "
              f"made: {v.made}")
    corridor = result["worlds"][0]
    print(f"\nThe corridor's kernel log: {len(corridor.kernel.log)} entries, "
          f"{'verifies' if World.verify_log(corridor.kernel.log) else 'BROKEN'}")


if __name__ == "__main__":
    main()
