"""
ur_garden.py — the Ur-world as a signed microverse garden.

The Ur-world, in the arc's idiom. A small 2D garden where
fractal plants grow, residents walk between them, and the
garden's keeper tends it. ALICE and BOB are real individuals
— DIDs, bundles, verifiable memory — not scripted characters.

Correspondence to rust/ur-world (per COLLABORATING.md):

  Python                         Rust (ur-world crate)
  ─────────────────────────────  ────────────────────────────
  Cell(x, y)                     Cell { x: i64, y: i64, z: i64 }
  Plant.position: Cell           Plant position on chunk grid
  GardenWorld._log: List[Dict]   world-log's signed-entry chain
  GardenWorld.world_kp           formats::signing_key
  Agent (UnifiedIndividual)      Mind trait implementation
  garden.walk/observe/speak      Mind::Action variants
  Plant (FractalHost)            hosted sub-world

  The port would:
    1. Move Cell to i64 (3D) — trivial geometry change.
    2. Use formats::proof for every log entry — replaces _append_log.
    3. Use world-log's chain verification — replaces verify_log.
    4. Implement Mind for ALICE and BOB — replaces UnifiedIndividualSession.
    5. Port the WorldAdapter protocol — the largest chunk.

  The Python version is the reference. The Rust version is
  the deployment. This module is designed to be read by
  whoever does that port.

Design commitments:
  - Garden, not park. Small and walkable. The point is the walk.
  - Spatial observation. An agent only sees a plant if it's
    adjacent. Only hears another agent if it's within radius.
  - 3 actions, spatial: wander / attend / gesture. TinyRNN's
    3 outputs are dispositions, not directions; the adapter
    translates to movement.
  - Keeper acts are logged and signed. Adding or retiring a
    plant is a garden event, not a code change.
  - Cross-references bind the garden's log to the plants'
    logs. Every "agent observed" entry names a specific
    plant event hash.

Honest limits:
  - 2D grid, not 3D. The Rust port is where 3D lives. This
    version prioritizes the composition over the geometry.
  - No pathfinding. "Wander" moves one cell in a direction
    chosen by the adapter's heuristic, not A*. Garden is
    small enough that wandering suffices.
  - Plants don't interact. Each grows on its own schedule
    driven by advance_cycle. Cross-plant interaction is a
    natural extension.
  - Keeper doesn't observe. The garden's keeper can add and
    retire plants, but doesn't yet have a curator that
    watches and proposes. That's the next natural addition
    (MicroverseCurator-style).
"""

import json
import random as _rng
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    import chess  # noqa — not used, just checking env
    HAS_CHESS = True
except ImportError:
    HAS_CHESS = False

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)
from multiverse_c3 import (
    Manifest, Petition, Act, Ack, Refusal,
    Admission as WCPAdmission,
)
from microverse import (
    FractalHost, ChaosGameHost, ElementaryCAHost,
)


# =====================================================================
# Cell
# =====================================================================

@dataclass(frozen=True)
class Cell:
    """A 2D garden coordinate. Rust port: {x: i64, y: i64}."""
    x: int
    y: int

    def step(self, direction: str) -> "Cell":
        dx, dy = {
            "N": (0, -1), "S": (0, 1),
            "E": (1, 0), "W": (-1, 0),
        }[direction]
        return Cell(self.x + dx, self.y + dy)

    def adjacent(self, other: "Cell") -> bool:
        return abs(self.x - other.x) + abs(self.y - other.y) == 1

    def distance(self, other: "Cell") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def within(self, other: "Cell", radius: int) -> bool:
        return self.distance(other) <= radius

    def to_list(self) -> List[int]:
        return [self.x, self.y]


# =====================================================================
# Plant — a FractalHost on the grid
# =====================================================================

@dataclass
class Plant:
    plant_id: str
    kind: str  # "fern" | "tree" | "vine" | ...
    host: FractalHost
    position: Cell
    description: str = ""

    def to_summary(self) -> Dict:
        return {
            "plant_id": self.plant_id,
            "kind": self.kind,
            "position": self.position.to_list(),
            "description": self.description,
            "event_count": len(self.host.events()),
            "epoch": self.host._epoch,
        }


# =====================================================================
# GardenWorld — the spatial microverse
# =====================================================================

class GardenWorld:
    WIDTH = 9
    HEIGHT = 8

    def __init__(
        self, entity_id: str, name: str, keypair,
        description: str = "",
    ):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.2",
            law_url=f"garden://{entity_id}/law",
            act_endpoint=f"garden://{entity_id}/act",
            log_endpoint=f"garden://{entity_id}/log",
            sub_registry_endpoint=f"garden://{entity_id}/plants",
        )
        self._kp = keypair
        self._world_signer = _did_from_kp(keypair)
        self._description = description
        self._admitted: Dict[str, str] = {}
        self._agent_position: Dict[str, Cell] = {}
        self._agent_visited: Dict[str, set] = {}
        self._plants_active: Dict[str, Plant] = {}
        self._plants_all: Dict[str, Plant] = {}
        self._log: List[Dict] = []
        self._cycle = 0

    # -- Identity --------------------------------------------

    def manifest(self) -> Manifest:
        return self._manifest

    def world_signer(self) -> str:
        return self._world_signer

    def world_kp(self):
        return self._kp

    def description(self) -> str:
        return self._description

    def cycle(self) -> int:
        return self._cycle

    def log_since(self, since=None) -> List[Dict]:
        if since is None:
            return list(self._log)
        return [e for e in self._log if e["ts"] > since]

    # -- Read model ------------------------------------------

    def position_of(self, agent_id: str) -> Optional[Cell]:
        return self._agent_position.get(agent_id)

    def plants(self) -> Dict[str, Plant]:
        return dict(self._plants_active)

    def all_plants(self) -> Dict[str, Plant]:
        return dict(self._plants_all)

    def plant_at(self, cell: Cell) -> Optional[Plant]:
        for p in self._plants_active.values():
            if p.position == cell:
                return p
        return None

    def adjacent_plants(self, cell: Cell) -> List[Plant]:
        return [p for p in self._plants_active.values()
                if p.position.adjacent(cell)]

    def nearby_agents(
        self, cell: Cell, radius: int = 2,
        exclude: Optional[str] = None,
    ) -> List[str]:
        return [aid for aid, pos in self._agent_position.items()
                if aid != exclude
                and pos.within(cell, radius)]

    # -- Internal --------------------------------------------

    def _append(self, entry: Dict) -> Dict:
        body = {k: v for k, v in entry.items() if k != "sig"}
        sig = self._kp.sign(_canonical(body)).hex()
        signed = {**body, "sig": sig}
        self._log.append(signed)
        return signed

    def _ack(self) -> Ack:
        return Ack(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    # -- Keeper acts -----------------------------------------

    def add_plant(
        self, plant_id: str, kind: str, host: FractalHost,
        position: Cell, description: str = "",
    ) -> Dict:
        if plant_id in self._plants_all:
            raise ValueError(f"plant {plant_id} exists")
        if not (0 <= position.x < self.WIDTH
                and 0 <= position.y < self.HEIGHT):
            raise ValueError(
                f"position {position} out of bounds")
        if self.plant_at(position) is not None:
            raise ValueError(
                f"position {position} occupied")
        plant = Plant(
            plant_id=plant_id, kind=kind, host=host,
            position=position, description=description,
        )
        self._plants_active[plant_id] = plant
        self._plants_all[plant_id] = plant
        return self._append({
            "kind": "plant_added",
            "actor": self._world_signer,
            "plant_id": plant_id,
            "plant_kind": kind,
            "position": position.to_list(),
            "host_world_id": host.world_id,
            "description": description,
            "ts": _now(),
        })

    def retire_plant(
        self, plant_id: str, reason: str = "wilted",
    ) -> Dict:
        if plant_id not in self._plants_active:
            raise ValueError(
                f"plant {plant_id} not active")
        plant = self._plants_active.pop(plant_id)
        return self._append({
            "kind": "plant_retired",
            "actor": self._world_signer,
            "plant_id": plant_id,
            "position": plant.position.to_list(),
            "reason": reason,
            "ts": _now(),
        })

    def advance_cycle(self, n_steps: int = 1) -> List[Dict]:
        self._cycle += 1
        all_events = []
        for plant in self._plants_active.values():
            evs = plant.host.advance(n_steps)
            all_events.extend(evs)
        self._append({
            "kind": "cycle_advanced",
            "actor": self._world_signer,
            "cycle": self._cycle,
            "plant_event_hashes":
                [ev["hash"] for ev in all_events],
            "ts": _now(),
        })
        return all_events

    # -- Agent interface -------------------------------------

    def petition(self, p: Petition):
        if p.petitioner_token in self._admitted:
            return Refusal(reason="Already admitted")
        self._admitted[p.petitioner_token] = p.petitioner_name
        self._append({
            "kind": "admission",
            "actor": p.petitioner_token,
            "name": p.petitioner_name,
            "ts": _now(),
        })
        return WCPAdmission(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    def act(self, act: Act):
        if act.actor_token not in self._admitted:
            return Refusal(reason="Actor is not admitted")
        kind = act.type
        if kind == "garden.walk":
            return self._handle_walk(act)
        if kind == "garden.observe":
            return self._handle_observe(act)
        if kind == "garden.speak":
            return self._handle_speak(act)
        return Refusal(reason=f"Unknown act {kind!r}")

    def _handle_walk(self, act: Act):
        # First-time agents are placed at their given position;
        # subsequent walks move from current position.
        pos = self._agent_position.get(act.actor_token)
        if pos is None:
            start = act.payload.get("start")
            if start is None:
                return Refusal(
                    reason="first walk requires start [x,y]")
            try:
                pos = Cell(int(start[0]), int(start[1]))
            except (ValueError, TypeError, IndexError):
                return Refusal(reason="bad start position")
            if not (0 <= pos.x < self.WIDTH
                    and 0 <= pos.y < self.HEIGHT):
                return Refusal(reason="start out of bounds")
            self._agent_position[act.actor_token] = pos
            self._agent_visited.setdefault(
                act.actor_token, set()).add((pos.x, pos.y))
            self._append({
                "kind": "agent_entered",
                "actor": act.actor_token,
                "position": pos.to_list(),
                "ts": _now(),
            })
            return self._ack()

        direction = act.payload.get("direction", "N")
        if direction not in ("N", "S", "E", "W"):
            return Refusal(reason=f"bad direction {direction!r}")
        new_pos = pos.step(direction)
        if not (0 <= new_pos.x < self.WIDTH
                and 0 <= new_pos.y < self.HEIGHT):
            return Refusal(reason="out of bounds")
        if self.plant_at(new_pos) is not None:
            return Refusal(reason="plant occupies that cell")
        self._agent_position[act.actor_token] = new_pos
        self._agent_visited.setdefault(
            act.actor_token, set()).add((new_pos.x, new_pos.y))
        self._append({
            "kind": "agent_walked",
            "actor": act.actor_token,
            "from": pos.to_list(),
            "to": new_pos.to_list(),
            "direction": direction,
            "ts": _now(),
        })
        return self._ack()

    def _handle_observe(self, act: Act):
        pos = self._agent_position.get(act.actor_token)
        if pos is None:
            return Refusal(reason="agent has not entered")
        nearby = self.adjacent_plants(pos)
        if not nearby:
            self._append({
                "kind": "agent_observed",
                "actor": act.actor_token,
                "position": pos.to_list(),
                "result": "nothing_adjacent",
                "ts": _now(),
            })
            return self._ack()
        plant = nearby[0]  # observe the first adjacent
        evs = plant.host.events()
        if not evs:
            return Refusal(reason="plant has no events yet")
        latest = evs[-1]
        self._append({
            "kind": "agent_observed",
            "actor": act.actor_token,
            "position": pos.to_list(),
            "result": "observed_plant",
            "plant_id": plant.plant_id,
            "plant_event_hash": latest["hash"],
            "plant_event_kind": latest["kind"],
            "ts": _now(),
        })
        return self._ack()

    def _handle_speak(self, act: Act):
        text = act.payload.get("text", "")
        if not isinstance(text, str) or not text.strip():
            return Refusal(reason="text required")
        pos = self._agent_position.get(act.actor_token)
        if pos is None:
            return Refusal(reason="agent has not entered")
        nearby = self.nearby_agents(
            pos, radius=2, exclude=act.actor_token)
        self._append({
            "kind": "agent_spoke",
            "actor": act.actor_token,
            "position": pos.to_list(),
            "heard_by": nearby,
            "text": text[:200],
            "ts": _now(),
        })
        return self._ack()

    # -- Verification ----------------------------------------

    def verify_log(self) -> Tuple[bool, str]:
        if not HAS_CRYPTO:
            return (False, "cryptography not installed")
        for i, e in enumerate(self._log):
            actor = e.get("actor")
            if not actor:
                return (False, f"log[{i}]: missing actor")
            body = {k: v for k, v in e.items() if k != "sig"}
            try:
                _pubkey_from_did(actor).verify(
                    bytes.fromhex(e["sig"]),
                    _canonical(body))
            except Exception:
                return (False,
                         f"log[{i}]: sig invalid "
                         f"({actor[:16]}...)")
        return (True,
                 f"garden log verifies ({len(self._log)} entries)")

    def verify_cross_references(self) -> Tuple[bool, str]:
        """Every observation of a plant must reference a real
        plant event."""
        for i, e in enumerate(self._log):
            if e.get("kind") != "agent_observed":
                continue
            if e.get("result") != "observed_plant":
                continue
            pid = e["plant_id"]
            target = e["plant_event_hash"]
            plant = self._plants_all.get(pid)
            if plant is None:
                return (False,
                         f"log[{i}]: plant {pid} not in all_plants")
            if not any(ev["hash"] == target
                        for ev in plant.host.events()):
                return (False,
                         f"log[{i}]: event {target[:16]}... "
                         f"not in plant {pid}")
        return (True, "cross-references verify")
