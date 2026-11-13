"""The corridor world: Cycle 0's corridor, behind the protocol.

Course step 5. The corridor of Cycle 0 (docs/cycles/cycle-000.md) runs on
the world kernel (`world/core.py`): a grid where each tick every agent
sees what is around it and acts, and every event goes into a hash-chained
log. This module puts that kernel behind the protocol, so an individual
from anywhere can enter, walk, speak and leave, with a passport like in
any other world.

- **Entering** puts the individual in the first free cell of the west
  end, the entrance. Someone coming back from a world this corridor has a
  door to arrives at that door instead, if it is free: by the latest
  visit their passport shows (a holder chooses which stamps to show).
- **Acts:** `corridor.move` {"dx", "dy"}: one step to a neighbouring cell;
  `corridor.say` {"text"}: spoken to everyone present (the kernel puts
  it in everyone's next observation; visitors can't read observations
  through the protocol yet);
  `corridor.wait` {}. Each accepted act runs one tick of the kernel, in
  which the one who acted does what it asked and everyone else waits. A
  move into a wall or an occupied cell is recorded as blocked.
- **Leaving** removes the individual from the grid, as the kernel's own
  exit does. It can't be refused.
- **Doors.** The law publishes doors: a cell, and the world beyond it, by
  id and key. Going through is the individual's own doing: its signed
  leave here, then its petition there, carrying its passport. The worlds
  on either side know each other's keys (`Entity.know`), so each checks
  the stamps in the other's name against the right key.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from world.core import MAX_SAY_CHARS, Move, Say, Wait, World

from .entity import (SIGNED_REQUESTS_LAW, STAMPS_LAW, UNSIGNED_ANSWERS_LIMIT,
                     Entity, now)
from .identity import token_problem
from .passport import verify_passport
from .protocol import Ack, Act, ActResponse, LogEntry

MOVE, SAY, WAIT = "corridor.move", "corridor.say", "corridor.wait"
Cell = Tuple[int, int]


@dataclass(frozen=True)
class Door:
    """A cell of the corridor, and the world beyond it."""
    cell: Cell
    world_id: str
    world_key: str
    name: str = ""


@dataclass(frozen=True)
class CorridorWorldLaw:
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None
    width: int = 12
    height: int = 3
    seed: int = 0
    doors: Tuple[Door, ...] = ()

    def __post_init__(self):
        for n in (self.width, self.height):
            if type(n) is not int or not 1 <= n <= 1000:
                raise ValueError("width and height must be whole numbers "
                                 "from 1 to 1000")
        if type(self.seed) is not int:
            raise ValueError("seed must be a whole number")
        cells, ids = set(), set()
        for d in self.doors:
            if type(d) is not Door:
                raise ValueError("doors must be Door entries")
            x, y = d.cell
            if not (type(x) is int and type(y) is int
                    and 0 < x < self.width and 0 <= y < self.height):
                raise ValueError(f"a door must be inside the corridor, and "
                                 f"not at its entrance: {d.cell}")
            if token_problem(d.world_key):
                raise ValueError(f"the door to {d.world_id} needs a key")
            if d.cell in cells or d.world_id in ids:
                raise ValueError("one door per cell, and per world")
            cells.add(d.cell)
            ids.add(d.world_id)

    def describe(self) -> str:
        lines = [
            "# Corridor World Law v0.1",
            "",
            "## Entering and leaving",
            f"- Admits any identity: {self.admits_any_identity}",
            "- Max present: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "- Anyone may leave at any time.",
            SIGNED_REQUESTS_LAW,
            STAMPS_LAW,
            "- Newcomers enter at the west end (x = 0), in its first free "
            "cell; if none is free, they are asked to try again. Someone "
            "whose latest visit, as their passport shows it, was to a "
            "world beyond one of the doors arrives at that door, if it is "
            "free.",
            "",
            "## The corridor",
            f"- {self.width} cells east to west, {self.height} north to "
            "south, walled on every side. One individual per cell.",
            f"- Ticks: each accepted act runs one tick of the world kernel "
            f"(seed {self.seed}), in which the one who acted does what it "
            "asked and everyone else waits.",
            f"- {MOVE} {{dx, dy}}: one step to a neighbouring cell; "
            "blocked by walls and by others.",
            f"- {SAY} {{text}}: up to {MAX_SAY_CHARS} characters, spoken "
            "to everyone present, and recorded in the kernel's log. "
            "Visitors can't yet read what others say through the protocol.",
            f"- {WAIT} {{}}: one tick, standing still.",
            "",
            "## Doors",
        ]
        if not self.doors:
            lines.append("- None.")
        for d in self.doors:
            lines.append(f"- At {list(d.cell)}: {d.name or d.world_id} "
                         f"({d.world_id}, key {d.world_key}).")
        lines += [
            "- Going through a door is your own doing: leave here, then "
            "petition the world beyond with your passport.",
            "",
            "## Limits",
            UNSIGNED_ANSWERS_LIMIT,
            "- Ticks happen only when someone acts.",
        ]
        return "\n".join(lines)


class _Proxy:
    """A protocol member, as the kernel sees it: it does what its latest
    accepted act asked, once, and otherwise waits."""

    def __init__(self):
        self.next = Wait()

    def act(self, obs):
        action, self.next = self.next, Wait()
        return action


class CorridorWorld(Entity):
    scheme = "corridor"
    noun = "Corridor"

    def __init__(self, entity_id: str, name: str,
                 law: Optional[CorridorWorldLaw] = None):
        law = law or CorridorWorldLaw()
        super().__init__(entity_id, name, law)
        self._kernel = World(law.width, law.height, seed=law.seed,
                             orientation=law.describe(),
                             rules_version="corridor/0.1")
        self._agents: Dict[str, str] = {}      # token -> kernel agent id
        self._proxies: Dict[str, _Proxy] = {}
        self._entries = 0
        self._place: Dict[str, Cell] = {}      # where the next entry goes
        self._doors = {d.world_id: d for d in law.doors}
        for d in law.doors:
            if d.world_id == entity_id:
                raise ValueError("a door can't lead to the corridor itself")
            self._known[d.world_id] = d.world_key

    # -- entering and leaving --------------------------------------------

    def _entry_problem(self, token: str, passport) -> str:
        cell = self._arrival_cell(passport)
        if cell is None:
            return "the entrance is crowded; try again after a tick"
        self._place[token] = cell
        return ""

    def _entered(self, token: str, timestamp: str) -> None:
        self._entries += 1
        agent_id = f"{token[:12]}-{self._entries}"
        proxy = _Proxy()
        self._kernel.add(agent_id, proxy, self._place.pop(token))
        self._agents[token] = agent_id
        self._proxies[token] = proxy
        self._note(timestamp, token, "entered")

    def _left(self, token: str, timestamp: str) -> None:
        agent_id = self._agents.pop(token, None)
        self._proxies.pop(token, None)
        if agent_id is not None:
            self._kernel.leave(agent_id)

    def _arrival_cell(self, passport) -> Optional[Cell]:
        """The door of the world the passport's latest visit was to, if
        this corridor has one and it is free; else the first free cell of
        the entrance; else None."""
        visits = verify_passport(passport, dict(self._known)).visits
        if visits:
            door = self._doors.get(visits[-1].world_id)
            if door is not None and self._kernel.occupant(door.cell) is None:
                return door.cell
        for y in range(self._law.height):
            if self._kernel.occupant((0, y)) is None:
                return (0, y)
        return None

    # -- acts -------------------------------------------------------------

    def act(self, act: Act) -> ActResponse:
        timestamp = now()
        refusal = self._actor_problem(timestamp, act)
        if refusal:
            return refusal
        actor = act.actor_token
        p = act.payload
        if act.type == MOVE:
            dx, dy = p.get("dx"), p.get("dy")
            if not (type(dx) is int and type(dy) is int
                    and abs(dx) + abs(dy) == 1):
                return self._refuse(timestamp, actor,
                                    "dx and dy must be whole numbers, one "
                                    "of them 1 or -1 and the other 0", "act")
            action = Move(dx, dy)
        elif act.type == SAY:
            text = p.get("text")
            if type(text) is not str or not text or len(text) > MAX_SAY_CHARS:
                return self._refuse(timestamp, actor,
                                    f"text must be 1 to {MAX_SAY_CHARS} "
                                    "characters", "act")
            action = Say(text)
        elif act.type == WAIT:
            action = Wait()
        else:
            return self._refuse(timestamp, actor,
                                f"Unknown act type: {act.type}", "act")
        self._proxies[actor].next = action
        self._kernel.step()
        self._note(timestamp, actor, act.type)
        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp)

    # -- reading ----------------------------------------------------------

    def where(self, token: str) -> Optional[Dict]:
        """Where someone present is, and the door they stand at, if any."""
        agent_id = self._agents.get(token)
        if agent_id is None:
            return None
        cell = self._kernel.position(agent_id)
        door = next((d for d in self._doors.values() if d.cell == cell),
                    None)
        return {"cell": cell, "door": door}

    def doors(self) -> List[Door]:
        return list(self._law.doors)

    @property
    def kernel(self) -> World:
        """The kernel's world, for reading (its log). Changing it directly
        bypasses this world's law."""
        return self._kernel

    def _note(self, timestamp: str, token: str, what: str) -> None:
        where = self.where(token)
        self._log.append(LogEntry(
            timestamp=timestamp, kind="walk", actor_token=token,
            data={"what": what, "tick": self._kernel.tick,
                  "cell": list(where["cell"]),
                  "door": where["door"].world_id if where["door"] else None,
                  "kernel_head": self._kernel.log_head()}))
