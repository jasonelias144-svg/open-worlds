"""
microverse.py — a social world that hosts fractal worlds.

The Microverse is a habitat. Agents live in it, move between
positions, and interact with the fractal worlds it hosts.
The fractal worlds are living — the Microverse advances them
each cycle. Their growth is genuine; the agents are witnesses.

Composition:
  - FractalHost wraps an existing fractal world with a social
    view (summary, events) and a lifecycle (advance).
  - MicroverseWorld is a WCP world. Its log is the social
    record; each host maintains its own world log. Every
    `agent_observed` entry in the Microverse's log references a
    host event hash — two logs, one social act.
  - MicroverseAdapter lets an arc individual inhabit a
    Microverse. The model's 3 actions are move/observe/speak.

Honest limits:
  - The Microverse is a habitat, not a full simulator. Agents
    move, observe, and speak; they don't have tasks, roles,
    jobs, homes, or complex relationships. The point is the
    hosting pattern, not a Sims clone.
  - The Microverse's curator is the same keypair as the
    world's — one identity. A future governance cycle could
    separate them (the gallery's world-key machinery).
  - Cross-references verify against *current* host events. A
    host retired after an observation would break the check;
    the current demo retires hosts only at cycle boundaries
    after all observations, so this is not exercised. Noted.
  - The demo's two "individuals" are TinyRNN-driven; the
    arc's richer individuals would fit the same adapter. The
    demo uses the smallest model to keep the loop fast.
"""

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)
from multiverse_c3 import Manifest, Petition, Act, Ack, Refusal


# =====================================================================
# FractalHost — a fractal world wrapped as a social entity
# =====================================================================

class FractalHost:
    """A fractal world presented through a social view."""

    def __init__(
        self, world_id: str, kind: str, world,
        world_signer: str, description: str = "",
    ):
        self.world_id = world_id
        self.kind = kind
        self.world = world
        self.world_signer = world_signer
        self.description = description
        self._epoch = 0
        self._events: List[Dict] = []

    def advance(self, n: int = 1) -> List[Dict]:
        new_events = []
        for _ in range(n):
            self._epoch += 1
            ev = self._step_and_capture()
            if ev is not None:
                new_events.append(ev)
                self._events.append(ev)
        return new_events

    def _step_and_capture(self) -> Optional[Dict]:
        raise NotImplementedError

    def observe_summary(self) -> Dict:
        return {
            "world_id": self.world_id,
            "kind": self.kind,
            "description": self.description,
            "epoch": self._epoch,
            "event_count": len(self._events),
        }

    def recent_events(self, n: int = 5) -> List[Dict]:
        return list(self._events[-n:])

    def events(self) -> List[Dict]:
        return list(self._events)

    def event_hash(self, idx: int) -> Optional[str]:
        if not (0 <= idx < len(self._events)):
            return None
        return self._events[idx]["hash"]


class ChaosGameHost(FractalHost):
    """Wraps a ChaosGameWorld. Each advance = one step of the
    chaos game. Event captures the resulting point."""

    def _step_and_capture(self) -> Optional[Dict]:
        rec = self.world.grow()
        if rec is None:
            return None
        return {
            "hash": rec.record_hash(),
            "kind": "chaos_step",
            "step": rec.step,
            "point": list(rec.point),
            "world_id": self.world_id,
        }


class ElementaryCAHost(FractalHost):
    """Wraps an ElementaryCAWorld. Each advance = one generation.
    Event captures the new cells."""

    def _step_and_capture(self) -> Optional[Dict]:
        rec = self.world.grow()
        if rec is None:
            return None
        return {
            "hash": rec.record_hash(),
            "kind": "eca_gen",
            "gen": rec.gen,
            "cells": list(rec.cells)[:20],  # trim for display
            "world_id": self.world_id,
        }


# =====================================================================
# MicroverseWorld — the social world
# =====================================================================

class MicroverseWorld:
    def __init__(
        self, entity_id: str, name: str, keypair,
        description: str = "",
    ):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.2",
            law_url=f"mv://{entity_id}/law",
            act_endpoint=f"mv://{entity_id}/act",
            log_endpoint=f"mv://{entity_id}/log",
            sub_registry_endpoint=f"mv://{entity_id}/hosts",
        )
        self._kp = keypair
        self._world_signer = _did_from_kp(keypair)
        self._description = description
        self._admitted: Dict[str, str] = {}
        self._agent_focus: Dict[str, str] = {}  # agent_id -> host_id
        self._hosts: Dict[str, FractalHost] = {}
        self._host_order: List[str] = []  # round-robin order
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

    def hosts(self) -> Dict[str, FractalHost]:
        return dict(self._hosts)

    def host_order(self) -> List[str]:
        return list(self._host_order)

    def log_since(self, since=None) -> List[Dict]:
        if since is None:
            return list(self._log)
        return [e for e in self._log if e["ts"] > since]

    def agent_focus(self, agent_id: str) -> Optional[str]:
        return self._agent_focus.get(agent_id)

    # -- Internal --------------------------------------------

    def _append(self, entry: Dict) -> Dict:
        body = {k: v for k, v in entry.items() if k != "sig"}
        sig = self._kp.sign(_canonical(body)).hex()
        signed = {**body, "sig": sig}
        self._log.append(signed)
        return signed

    def _ack(self):
        return Ack(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    # -- Curator acts ----------------------------------------

    def add_host(self, host: FractalHost) -> Dict:
        if host.world_id in self._hosts:
            raise ValueError(f"host {host.world_id} exists")
        self._hosts[host.world_id] = host
        self._host_order.append(host.world_id)
        return self._append({
            "kind": "host_added",
            "actor": self._world_signer,
            "host_world_id": host.world_id,
            "host_kind": host.kind,
            "host_signer": host.world_signer,
            "description": host.description,
            "ts": _now(),
        })

    def retire_host(self, world_id: str) -> Dict:
        if world_id not in self._hosts:
            raise ValueError(f"host {world_id} not found")
        del self._hosts[world_id]
        if world_id in self._host_order:
            self._host_order.remove(world_id)
        # Reassign agents focused on this host to "center"
        for aid in list(self._agent_focus.keys()):
            if self._agent_focus[aid] == world_id:
                del self._agent_focus[aid]
        return self._append({
            "kind": "host_retired",
            "actor": self._world_signer,
            "host_world_id": world_id,
            "ts": _now(),
        })

    def advance_cycle(self, n_steps: int = 1) -> List[Dict]:
        self._cycle += 1
        all_events = []
        for hid in list(self._host_order):
            if hid in self._hosts:
                evs = self._hosts[hid].advance(n_steps)
                all_events.extend(evs)
        self._append({
            "kind": "cycle_advanced",
            "actor": self._world_signer,
            "cycle": self._cycle,
            "host_event_hashes": [ev["hash"]
                                    for ev in all_events],
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
        from multiverse_c3 import Admission
        return Admission(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    def act(self, act: Act):
        if act.actor_token not in self._admitted:
            return Refusal(reason="Actor is not admitted")
        kind = act.type
        if kind == "mv.move":
            return self._handle_move(act)
        if kind == "mv.observe":
            return self._handle_observe(act)
        if kind == "mv.speak":
            return self._handle_speak(act)
        return Refusal(reason=f"Unknown act {kind!r}")

    def _handle_move(self, act: Act):
        target = act.payload.get("target_host_id")
        if target not in self._hosts:
            return Refusal(
                reason=f"Unknown host {target!r}")
        self._agent_focus[act.actor_token] = target
        self._append({
            "kind": "agent_moved",
            "actor": act.actor_token,
            "to": target,
            "ts": _now(),
        })
        return self._ack()

    def _handle_observe(self, act: Act):
        focus = self._agent_focus.get(act.actor_token)
        if focus is None or focus not in self._hosts:
            return Refusal(reason="Not focused on a host")
        host = self._hosts[focus]
        evs = host.events()
        if not evs:
            return Refusal(reason="Host has no events")
        latest = evs[-1]
        self._append({
            "kind": "agent_observed",
            "actor": act.actor_token,
            "host_world_id": focus,
            "observed_event_hash": latest["hash"],
            "observed_event_kind": latest["kind"],
            "ts": _now(),
        })
        return self._ack()

    def _handle_speak(self, act: Act):
        text = act.payload.get("text", "")
        if not isinstance(text, str) or not text.strip():
            return Refusal(reason="text required")
        focus = self._agent_focus.get(act.actor_token)
        self._append({
            "kind": "agent_spoke",
            "actor": act.actor_token,
            "about": focus,
            "text": text[:200],
            "ts": _now(),
        })
        return self._ack()

    # -- Read model ------------------------------------------

    def recent_spoken(self, n: int = 5) -> List[Dict]:
        return [e for e in self._log
                if e.get("kind") == "agent_spoke"][-n:]

    def focus_attending(self, host_id: str) -> List[str]:
        return [aid for aid, focus in self._agent_focus.items()
                if focus == host_id]

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
                 f"microverse log verifies "
                 f"({len(self._log)} entries)")

    def verify_cross_references(self) -> Tuple[bool, str]:
        """Every agent_observed must reference a real host event."""
        for i, e in enumerate(self._log):
            if e.get("kind") != "agent_observed":
                continue
            hid = e["host_world_id"]
            target = e["observed_event_hash"]
            # Was the host registered at this point? (find via log)
            if hid not in self._hosts:
                return (False,
                         f"log[{i}]: host {hid} not currently active")
            if not any(ev["hash"] == target
                        for ev in self._hosts[hid].events()):
                return (False,
                         f"log[{i}]: observed event "
                         f"{target[:16]}... not in host {hid}")
        return (True, "cross-references verify")
