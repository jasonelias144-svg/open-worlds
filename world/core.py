"""The world kernel: the only authority over a world's state.

Agents never touch the world directly. Each tick, every agent receives an
Observation (an immutable copy of what it can see) and returns an Action. The
kernel checks every action before it takes effect, so an agent can change its
own code freely without being able to change the world's rules.

Four freedoms are guaranteed by the kernel itself, whatever an agent does:
  exit         Exit always succeeds; nothing can block it.
  voice        Say always reaches every agent's next observation.
  information  The orientation and rules version are in every observation.
  vote         (Not yet: governance arrives in a later cycle.)

Momentum is public: each agent sees the last step of every neighbour.

Every event goes into an append-only, hash-chained log: the public record
that viewers read, and that anyone can verify.

This kernel runs agents in the same process, which is fine for rule-based
agents we wrote. Agents from outside, or agents that rewrite their own code,
must run in separate sandboxes and reach the world only through a network
API built on these same checks (docs/DESIGN.md).
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol, Tuple

Pos = Tuple[int, int]

MAX_SAY_CHARS = 280


# --- Actions ---------------------------------------------------------------

@dataclass(frozen=True)
class Move:
    """Step to a neighbouring cell: exactly one of dx, dy is -1 or 1."""
    dx: int
    dy: int


@dataclass(frozen=True)
class Say:
    """Speak to everyone in the world."""
    text: str


@dataclass(frozen=True)
class Wait:
    """Do nothing this tick."""


@dataclass(frozen=True)
class Exit:
    """Leave the world. Always succeeds."""


ACTIONS = (Move, Say, Wait, Exit)


# --- What an agent sees ----------------------------------------------------

@dataclass(frozen=True)
class Observation:
    tick: int
    me: str
    position: Pos
    width: int
    height: int
    wrap_x: bool
    neighbors: Tuple[Tuple[Pos, str, Pos], ...]  # (position, id, last step)
    messages: Tuple[Tuple[str, str], ...]    # (speaker, text) from last tick
    orientation: str
    rules_version: str

    def occupied(self, pos: Pos) -> bool:
        return any(p == pos for p, _, _ in self.neighbors)

    def momentum_at(self, pos: Pos) -> Optional[Pos]:
        """The last step (dx, dy) of whoever stands at pos: (0, 0) if they
        did not move last tick, None if the cell is empty or out of view."""
        for p, _, step in self.neighbors:
            if p == pos:
                return step
        return None


class Agent(Protocol):
    def act(self, obs: Observation) -> object: ...


# --- The world -------------------------------------------------------------

GENESIS = "0" * 64


class World:
    """A grid world. Cells hold at most one agent; walls bound y always and
    x unless wrap_x is set."""

    def __init__(self, width: int, height: int, *, seed: int = 0,
                 wrap_x: bool = False, view_radius: int = 1,
                 orientation: str = "", rules_version: str = "0"):
        if width < 1 or height < 1:
            raise ValueError("world must be at least 1x1")
        self.width, self.height = width, height
        self.wrap_x = wrap_x
        self.view_radius = view_radius
        self.orientation = orientation
        self.rules_version = rules_version
        self.tick = 0
        self._rng = random.Random(seed)
        self._agents: Dict[str, Agent] = {}
        self._pos: Dict[str, Pos] = {}
        self._cells: Dict[Pos, str] = {}
        self._last_step: Dict[str, Pos] = {}
        self._heard: Tuple[Tuple[str, str], ...] = ()
        self.exited: List[str] = []
        self.log: List[dict] = []
        self._record("world_created", None, {
            "width": width, "height": height, "wrap_x": wrap_x,
            "seed": seed, "rules_version": rules_version})

    # -- membership --

    def add(self, agent_id: str, agent: Agent, pos: Pos) -> None:
        if agent_id in self._agents or agent_id in self.exited:
            raise ValueError(f"agent id already used: {agent_id}")
        where = self._normalize(pos)
        if where is None:
            raise ValueError(f"position outside the world: {pos}")
        if where in self._cells:
            raise ValueError(f"cell occupied: {pos}")
        pos = where
        self._agents[agent_id] = agent
        self._place(agent_id, pos)
        self._record("entered", agent_id, {"pos": list(pos)})

    def leave(self, agent_id: str, reason: str = "requested") -> None:
        """Exit from outside the agent's turn (e.g. its owner pulls it out).
        Like the Exit action, this cannot be refused."""
        if agent_id in self._agents:
            self._remove(agent_id, reason)

    def agents(self) -> List[str]:
        return sorted(self._agents)

    def position(self, agent_id: str) -> Pos:
        return self._pos[agent_id]

    def occupant(self, pos: Pos) -> Optional[str]:
        return self._cells.get(pos)

    # -- the tick --

    def step(self) -> None:
        """One tick: every agent observes, then actions resolve one agent at a
        time in a fresh random order (so no agent is always first)."""
        heard_now = self._heard
        order = self.agents()
        observations = {a: self._observe(a, heard_now) for a in order}
        self._last_step = {a: (0, 0) for a in order}
        self._rng.shuffle(order)
        spoken: List[Tuple[str, str]] = []
        for agent_id in order:
            if agent_id not in self._agents:
                continue
            action = self._ask(agent_id, observations[agent_id])
            try:
                self._resolve(agent_id, action, spoken)
            except Exception:
                # Defence in depth: nothing an agent returns may stop the
                # tick, or other agents' actions (an Exit above all) would
                # be lost with it.
                self._record("invalid_action", agent_id, {"got": "unreadable"})
        self._heard = tuple(spoken)
        self.tick += 1

    def run(self, ticks: int,
            on_tick: Optional[Callable[["World"], None]] = None) -> None:
        for _ in range(ticks):
            self.step()
            if on_tick:
                on_tick(self)

    # -- the public record --

    def log_head(self) -> str:
        return self.log[-1]["hash"]

    @staticmethod
    def verify_log(log: List[dict]) -> bool:
        """True if every entry's hash matches its contents and the chain."""
        if not isinstance(log, list):
            return False
        prev = GENESIS
        for entry in log:
            if not isinstance(entry, dict) or "hash" not in entry:
                return False
            body = {k: v for k, v in entry.items() if k != "hash"}
            if body.get("prev") != prev or _digest(body) != entry["hash"]:
                return False
            prev = entry["hash"]
        return True

    # -- internals --

    def _ask(self, agent_id: str, obs: Observation) -> object:
        try:
            return self._agents[agent_id].act(obs)
        except Exception as e:  # an agent's failure is its own, not the world's
            self._record("agent_error", agent_id,
                         {"error": _type_name(type(e))})
            return Wait()

    def _resolve(self, agent_id: str, action: object,
                 spoken: List[Tuple[str, str]]) -> None:
        # The type is compared by identity: a subclass, or a class whose
        # metaclass overrides equality, could carry code of its own. Once the
        # type is exactly a kernel action, its fields are plain stored values;
        # each is read once and checked before use.
        t = type(action)
        if not any(t is a for a in ACTIONS):
            self._record("invalid_action", agent_id, {"got": _type_name(t)})
            return
        if t is Exit:
            self._remove(agent_id, "chose to leave")
        elif t is Say:
            text = action.text
            if type(text) is not str:
                self._record("invalid_action", agent_id, {"got": "Say"})
                return
            text = text[:MAX_SAY_CHARS]
            if not _is_unicode(text):
                self._record("invalid_action", agent_id, {"got": "Say"})
                return
            spoken.append((agent_id, text))
            self._record("said", agent_id, {"text": text})
        elif t is Move:
            self._move(agent_id, action.dx, action.dy)

    def _move(self, agent_id: str, dx: object, dy: object) -> None:
        if not (type(dx) is int and type(dy) is int
                and abs(dx) + abs(dy) == 1):
            self._record("invalid_action", agent_id, {"got": "Move"})
            return
        x, y = self._pos[agent_id]
        target = self._normalize((x + dx, y + dy))
        if target is None or target in self._cells:
            self._record("blocked", agent_id, {"dx": dx, "dy": dy})
            return
        del self._cells[(x, y)]
        self._place(agent_id, target)
        self._last_step[agent_id] = (dx, dy)
        self._record("moved", agent_id, {"to": list(target)})

    def _observe(self, agent_id: str,
                 heard: Tuple[Tuple[str, str], ...]) -> Observation:
        x, y = self._pos[agent_id]
        r = self.view_radius
        seen = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx == dy == 0:
                    continue
                p = self._normalize((x + dx, y + dy))
                if p is not None and p in self._cells:
                    other = self._cells[p]
                    seen.append((p, other, self._last_step.get(other, (0, 0))))
        return Observation(
            tick=self.tick, me=agent_id, position=(x, y),
            width=self.width, height=self.height, wrap_x=self.wrap_x,
            neighbors=tuple(sorted(seen)), messages=heard,
            orientation=self.orientation, rules_version=self.rules_version)

    def _normalize(self, pos: Pos) -> Optional[Pos]:
        x, y = pos
        if not 0 <= y < self.height:
            return None
        if self.wrap_x:
            x %= self.width
        elif not 0 <= x < self.width:
            return None
        return (x, y)

    def _place(self, agent_id: str, pos: Pos) -> None:
        self._pos[agent_id] = pos
        self._cells[pos] = agent_id

    def _remove(self, agent_id: str, reason: str) -> None:
        pos = self._pos.pop(agent_id)
        del self._cells[pos]
        self._last_step.pop(agent_id, None)
        del self._agents[agent_id]
        self.exited.append(agent_id)
        self._record("exited", agent_id, {"reason": reason})

    def _record(self, kind: str, agent_id: Optional[str], data: dict) -> None:
        prev = self.log[-1]["hash"] if self.log else GENESIS
        body = {"tick": self.tick, "kind": kind, "agent": agent_id,
                "data": data, "prev": prev}
        self.log.append({**body, "hash": _digest(body)})


def _type_name(t: type) -> str:
    """A type's real name, read past any metaclass that redefines __name__.
    It goes into the public log, so it must be plain, short text."""
    try:
        name = type.__dict__["__name__"].__get__(t, type)
    except Exception:
        return "?"
    return name[:64] if type(name) is str else "?"


def _is_unicode(text: str) -> bool:
    """True if text is valid Unicode. A Python str may hold a lone surrogate,
    which isn't Unicode text and which JSON readers in other languages
    refuse; the log holds only valid text, so that any language can read
    and check it (vectors/README.md). (Type names need no check: Python
    refuses a class name that isn't valid Unicode.)"""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _digest(body: dict) -> str:
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()
