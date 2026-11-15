"""
microverse_adapter.py — inhabit a Microverse as an arc individual.

The adapter bridges a unified individual's 3-action TinyRNN
to the Microverse's move/observe/speak acts.
"""

from typing import Dict, List, Optional, Tuple

from individual_bundle import _now, _hash
from world_adapters import WorldAdapter


class MicroverseAdapter(WorldAdapter):
    def tier_name(self) -> str:
        return "microverse"

    def open(self, config):
        return config["world"]

    def enter(self, handle, individual_id, individual_kp, config):
        from multiverse_c3 import Petition
        world = handle
        resp = world.petition(Petition(
            petitioner_token=individual_id,
            petitioner_name=config.get(
                "display_name", "resident"),
            passport_admissions=(),
            message="entering the microverse",
        ))
        return {
            "world_url_hash": _hash(
                config.get("world_url", "mv://local")),
            "display_name": config.get(
                "display_name", "resident"),
        }

    def state(self, memory, handle):
        # Extract last action + focus from memory
        last_action = 0
        last_reward = 0.0
        for rec in reversed(memory):
            if rec.get("type") == "agent_step" \
                    and rec.get("tier") == "microverse":
                last_action = rec["action_idx"]
                last_reward = rec["reward_micros"] / 1_000_000
                break

        # Focus host
        world = handle
        focus = None
        for rec in reversed(memory):
            if rec.get("kind") == "agent_moved" \
                    or rec.get("kind") == "agent_observed":
                focus = rec.get("to") or rec.get("host_world_id")
                break

        # State dims (4):
        #  0: last_action_idx
        #  1: last_reward
        #  2: focus position (0..1 by host index, 0.5 if none)
        #  3: log activity (0..1 by recent count)
        host_order = world.host_order()
        if focus and focus in host_order:
            x = host_order.index(focus) / max(
                len(host_order) - 1, 1)
        else:
            x = 0.5
        recent = len(world.log_since(None))
        y = min(recent, 100) / 100.0
        return (last_action, last_reward, x, y)

    def action_from_index(self, idx, memory):
        world = self._handle_for_memory(memory)
        host_order = (world.host_order()
                       if world else [])
        # Determine current focus
        current_focus = None
        for rec in reversed(memory):
            if rec.get("kind") == "agent_moved":
                current_focus = rec.get("to")
                break
            if rec.get("kind") == "agent_observed":
                current_focus = rec.get("host_world_id")
                break
        # If no focus yet, we must move first
        if current_focus is None and host_order:
            return {"act": "move",
                     "target_host_id": host_order[0]}
        # 0=move to next host, 1=observe, 2=speak
        if idx == 0 and host_order:
            i = host_order.index(current_focus) \
                if current_focus in host_order else 0
            next_host = host_order[(i + 1) % len(host_order)]
            return {"act": "move", "target_host_id": next_host}
        if idx == 1:
            return {"act": "observe"}
        # speak
        phrase = _pick_phrase(current_focus, memory)
        return {"act": "speak", "text": phrase}

    def _handle_for_memory(self, memory):
        # The adapter doesn't know the world; state() got it from
        # the caller. For action_from_index, we need it. The
        # caller (step_via_adapter) handles this; this method
        # returns a placeholder that step_via_adapter
        # overrides with the actual world.
        return None

    def submit(self, handle, individual_id, individual_kp, action):
        from multiverse_c3 import Act
        world = handle
        act_kind = action["act"]
        if act_kind == "move":
            target = action["target_host_id"]
            resp = world.act(Act(
                actor_token=individual_id,
                type="mv.move",
                payload={"target_host_id": target},
            ))
            from multiverse_c3 import Ack
            if not isinstance(resp, Ack):
                return (None, 0.0)
            # Reward: small for movement
            reward = 0.05
            # Find the log entry
            latest = world.log_since(None)[-1]
            entry_hash = _hash(latest)
            return ({"microverse_entry_hash": entry_hash,
                      "act": "move", "to": target}, reward)

        if act_kind == "observe":
            resp = world.act(Act(
                actor_token=individual_id,
                type="mv.observe",
                payload={},
            ))
            from multiverse_c3 import Ack
            if not isinstance(resp, Ack):
                return (None, 0.0)
            latest = world.log_since(None)[-1]
            entry_hash = _hash(latest)
            observed_hash = latest.get("observed_event_hash")
            # Reward: high for fresh observation
            reward = 0.5
            return ({
                "microverse_entry_hash": entry_hash,
                "act": "observe",
                "observed_host":
                    latest.get("host_world_id"),
                "observed_event_hash": observed_hash,
            }, reward)

        # speak
        text = action["text"]
        resp = world.act(Act(
            actor_token=individual_id,
            type="mv.speak",
            payload={"text": text},
        ))
        from multiverse_c3 import Ack
        if not isinstance(resp, Ack):
            return (None, 0.0)
        latest = world.log_since(None)[-1]
        entry_hash = _hash(latest)
        reward = 0.3
        return ({
            "microverse_entry_hash": entry_hash,
            "act": "speak",
            "text": text,
        }, reward)

    def step_fields(self, action, world_ref):
        if world_ref is None:
            return {"act": action.get("act")}
        return dict(world_ref)

    def world_log(self, handle):
        return list(handle.log_since(None))

    def verify_step(self, step_record, memory, model, rng,
                     handle, world_log):
        """Verify the act against the Microverse log AND any
        cross-referenced host event."""
        # Reconstruct state
        state = self.state(memory, handle)
        idx = model.act(state, rng)
        if idx != step_record["action_idx"]:
            return (False,
                     f"action_idx {step_record['action_idx']} "
                     f"!= replayed {idx}")
        # Find the referenced Microverse log entry
        target = step_record.get("microverse_entry_hash")
        matched = None
        for e in world_log:
            if _hash(e) == target:
                matched = e
                break
        if matched is None:
            return (False, "microverse entry not found")
        # Verify act kind matches model output semantics
        expected_act = {0: "move", 1: "observe", 2: "speak"}[idx]
        if matched.get("kind") != f"agent_{expected_act}ed":
            # agent_moved, agent_observed, agent_spoke
            return (False,
                     f"act kind {matched.get('kind')} does "
                     f"not match expected {expected_act}")
        # If observe, cross-reference the host event
        if expected_act == "observe":
            host_id = matched.get("host_world_id")
            ev_hash = matched.get("observed_event_hash")
            if host_id not in handle.hosts():
                return (False,
                         f"host {host_id} not active")
            host = handle.hosts()[host_id]
            if not any(ev["hash"] == ev_hash
                        for ev in host.events()):
                return (False,
                         f"observed event {ev_hash[:16]}... "
                         f"not found in host")
        reward = step_record["reward_micros"] / 1_000_000
        model.learn(reward)
        return (True, "ok")


_PHRASE_BANK = [
    "the garden grows",
    "the pattern is beautiful",
    "I wonder what it becomes",
    "the cells keep shifting",
    "the chaos finds a shape",
    "come see this",
    "it's grown since I last looked",
]


def _pick_phrase(host_id, memory):
    # Deterministic by counter
    n = sum(1 for r in memory
             if r.get("type") == "agent_step")
    return _PHRASE_BANK[n % len(_PHRASE_BANK)]
