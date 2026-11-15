"""
garden_adapter.py — inhabit the Ur-garden as an arc individual.

Bridges the 3-action TinyRNN to the garden's spatial acts. The
model's outputs are dispositions, not directions:

  0 → wander  (adapter picks a direction, agent walks one cell)
  1 → attend  (observe: only yields plant events if adjacent)
  2 → gesture (speak: heard only if another agent is nearby)

Rewards are spatial:
  wander to a new cell:       0.05
  wander to a visited cell:   0.02
  observe near plant:         0.50
  observe nothing:            0.02
  speak with agent nearby:    0.30
  speak alone:                0.02
"""

import random as _rng
from typing import Dict, List, Optional, Tuple

from individual_bundle import _now, _hash
from multiverse_c3 import Act, Ack
from world_adapters import WorldAdapter
from ur_garden import Cell, GardenWorld


_PHRASE_BANK = [
    "the fern is growing",
    "the tree unfolds",
    "the vine is quiet today",
    "come look at this",
    "the garden is alive",
    "I wonder what it becomes",
    "each cycle changes everything",
]


class GardenAdapter(WorldAdapter):
    def tier_name(self) -> str:
        return "garden"

    def open(self, config):
        return config["world"]

    def enter(self, handle, individual_id, individual_kp, config):
        start = config.get("start_position", [0, 0])
        resp = handle.act(Act(
            actor_token=individual_id,
            type="garden.walk",
            payload={"start": list(start)},
        ))
        if not isinstance(resp, Ack):
            raise RuntimeError(
                f"garden entry failed: "
                f"{getattr(resp, 'reason', '?')}")
        return {
            "display_name": config.get(
                "display_name", "resident"),
            "start_position": list(start),
            "garden_size": [GardenWorld.WIDTH,
                              GardenWorld.HEIGHT],
        }

    def state(self, memory, handle):
        # Last action + reward
        last_action = 0
        last_reward = 0.0
        for rec in reversed(memory):
            if rec.get("type") == "agent_step" \
                    and rec.get("tier") == "garden":
                last_action = rec["action_idx"]
                last_reward = rec["reward_micros"] / 1_000_000
                break
        # Position from memory
        pos = self._position_from_memory(memory)
        if pos is None:
            pos = (0, 0)
        x = pos[0] / max(GardenWorld.WIDTH - 1, 1)
        y = pos[1] / max(GardenWorld.HEIGHT - 1, 1)
        return (last_action, last_reward, x, y)

    def _position_from_memory(self, memory) -> Optional[Tuple[int, int]]:
        for rec in reversed(memory):
            if rec.get("kind") in ("agent_walked",
                                     "agent_entered"):
                if rec["kind"] == "agent_walked":
                    return tuple(rec["to"])
                else:
                    return tuple(rec["position"])
        return None

    def _choose_direction(self, memory, handle) -> str:
        """Heuristic: prefer unvisited cells; among those,
        prefer toward the nearest plant."""
        pos = self._position_from_memory(memory)
        if pos is None:
            return "N"
        visited = set()
        for rec in memory:
            if rec.get("kind") == "agent_walked":
                visited.add(tuple(rec["to"]))
            elif rec.get("kind") == "agent_entered":
                visited.add(tuple(rec["position"]))
        from ur_garden import Cell
        current = Cell(*pos)
        # Nearest plant direction
        plants = handle.plants()
        nearest_dir = None
        if plants:
            nearest = min(
                plants.values(),
                key=lambda p: p.position.distance(current))
            dx = nearest.position.x - current.x
            dy = nearest.position.y - current.y
            if abs(dx) >= abs(dy) and dx != 0:
                nearest_dir = "E" if dx > 0 else "W"
            elif dy != 0:
                nearest_dir = "S" if dy > 0 else "N"
        # If we're adjacent to a plant, prefer wandering away
        if nearest_dir and current.distance(
                nearest.position) <= 1:
            nearest_dir = None
        # Try nearest direction first if its target is unvisited
        candidates = []
        if nearest_dir:
            step = current.step(nearest_dir)
            if (step.x, step.y) not in visited \
                    and 0 <= step.x < GardenWorld.WIDTH \
                    and 0 <= step.y < GardenWorld.HEIGHT:
                return nearest_dir
        for d in ("N", "E", "S", "W"):
            step = current.step(d)
            if (step.x, step.y) in visited:
                continue
            if handle.plant_at(step) is not None:
                continue
            if not (0 <= step.x < GardenWorld.WIDTH
                    and 0 <= step.y < GardenWorld.HEIGHT):
                continue
            candidates.append(d)
        if candidates:
            return candidates[0]
        # Everything visited — random walk within bounds
        for d in ("N", "E", "S", "W"):
            step = current.step(d)
            if handle.plant_at(step) is not None:
                continue
            if 0 <= step.x < GardenWorld.WIDTH \
                    and 0 <= step.y < GardenWorld.HEIGHT:
                return d
        return "N"

    def action_from_index(self, idx, memory):
        # idx is overridden by step_via_adapter before submit;
        # this method is called by UnifiedIndividualSession.
        return {"disposition": idx}

    def submit(self, handle, individual_id, individual_kp, action):
        idx = action["disposition"]
        world = handle

        if idx == 0:
            return self._submit_wander(
                world, individual_id, action)
        if idx == 1:
            return self._submit_observe(
                world, individual_id)
        return self._submit_speak(
            world, individual_id, action)

    def _submit_wander(self, world, individual_id, action):
        direction = action.get("_direction")
        if direction is None:
            direction = "N"
        resp = world.act(Act(
            actor_token=individual_id,
            type="garden.walk",
            payload={"direction": direction},
        ))
        if not isinstance(resp, Ack):
            return (None, 0.0)
        latest = world.log_since(None)[-1]
        entry_hash = _hash(latest)
        # Reward: check if destination is new
        from_to = latest.get("to", [0, 0])
        reward = 0.05  # default for moving
        return ({"garden_entry_hash": entry_hash,
                  "act": "wander", "to": from_to}, reward)

    def _submit_observe(self, world, individual_id):
        resp = world.act(Act(
            actor_token=individual_id,
            type="garden.observe",
            payload={},
        ))
        if not isinstance(resp, Ack):
            return (None, 0.0)
        latest = world.log_since(None)[-1]
        entry_hash = _hash(latest)
        result = latest.get("result")
        if result == "observed_plant":
            reward = 0.5
        else:
            reward = 0.02
        return ({
            "garden_entry_hash": entry_hash,
            "act": "observe",
            "result": result,
            "plant_id": latest.get("plant_id"),
            "plant_event_hash": latest.get("plant_event_hash"),
        }, reward)

    def _submit_speak(self, world, individual_id, action):
        text = action.get("_text", "hello")
        resp = world.act(Act(
            actor_token=individual_id,
            type="garden.speak",
            payload={"text": text},
        ))
        if not isinstance(resp, Ack):
            return (None, 0.0)
        latest = world.log_since(None)[-1]
        entry_hash = _hash(latest)
        heard_by = latest.get("heard_by", [])
        reward = 0.3 if heard_by else 0.02
        return ({
            "garden_entry_hash": entry_hash,
            "act": "speak",
            "text": text,
            "heard_by": heard_by,
        }, reward)

    def step_fields(self, action, world_ref):
        if world_ref is None:
            return {"act": action.get("disposition")}
        return dict(world_ref)

    def world_log(self, handle):
        return list(handle.log_since(None))

    def verify_step(self, step_record, memory, model, rng,
                     handle, world_log):
        state = self.state(memory, handle)
        idx = model.act(state, rng)
        if idx != step_record["action_idx"]:
            return (False,
                     f"action_idx {step_record['action_idx']} "
                     f"!= replayed {idx}")
        target = step_record.get("garden_entry_hash")
        matched = None
        for e in world_log:
            if _hash(e) == target:
                matched = e
                break
        if matched is None:
            return (False, "garden entry not found")
        expected_kind = {
            0: "agent_walked",
            1: "agent_observed",
            2: "agent_spoke",
        }[idx]
        if matched.get("kind") != expected_kind:
            return (False,
                     f"garden entry kind "
                     f"{matched.get('kind')} != "
                     f"{expected_kind}")
        # Cross-reference for observations
        if idx == 1 and matched.get("result") == "observed_plant":
            pid = matched.get("plant_id")
            ev_hash = matched.get("plant_event_hash")
            plant = handle.all_plants().get(pid)
            if plant is None:
                return (False, f"plant {pid} not found")
            if not any(ev["hash"] == ev_hash
                        for ev in plant.host.events()):
                return (False,
                         f"plant event {ev_hash[:16]}... "
                         f"not found")
        reward = step_record["reward_micros"] / 1_000_000
        model.learn(reward)
        return (True, "ok")

    # The session calls action_from_index before submit but
    # needs _direction / _text populated. UnifiedIndividualSession
    # passes the raw dict through. We populate it here for
    # clarity — but the session must handle the fill-in. See
    # the demo for how this is wired.
