"""
world_adapters.py — pluggable world adapters for unified individuals.

A WorldAdapter tells a unified individual how to:
  - open a world
  - enter it (petition, sit, etc.)
  - read the world into a model-shaped state
  - translate a model action index into a world-specific payload
  - submit that payload and get back a world reference + reward
  - record tier-specific fields in the individual's memory
  - verify a step against the world's log

Every adapter is n_actions=3, state_dim=4 — matching the individual's
4-unit TinyRNN. Adding a world to an individual becomes writing an
adapter, not a new session/verifier/memory format.

Composition: adapters use the underlying world's own API. No changes
to any world; adapters are shims between the individual's abstract
action space and each world's open action space.

Honest limits:
  - Fixed action space (3) and state dim (4). Worlds with richer
    action spaces are projected: the adapter narrows to 3 candidates.
    Legitimate — any agent has a bounded action space — but documented.
  - No cross-adapter learning transfer. Each tier's reward signal
    is defined by that tier.
  - Growing canvas's log is unsigned; cross-reference trusts it.
    Same caveat as pre-signed chess log.
"""

import json
import random as _rng
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

try:
    import chess
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
from coupled_learners import SIERPINSKI


def _entry_hash(rec):
    return _hash({k: v for k, v in rec.items() if k != "sig"})


def _post_json(url, body, timeout=10):
    import urllib.request
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get_json(url, timeout=10):
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


# =====================================================================
# WorldAdapter ABC
# =====================================================================

class WorldAdapter(ABC):
    @abstractmethod
    def tier_name(self) -> str: ...

    def n_actions(self) -> int:
        return 3

    def state_dim(self) -> int:
        return 4

    @abstractmethod
    def open(self, config: dict) -> Any:
        """Extract the world handle from config (no side effects)."""

    @abstractmethod
    def enter(self, handle, individual_id: str, individual_kp,
              config: dict) -> dict:
        """Perform world-side entry. Return body fields for the
        world_entry memory record."""

    @abstractmethod
    def state(self, memory: List[dict], handle) -> Tuple:
        """Model input as a 4-tuple of floats, derived from memory."""

    @abstractmethod
    def action_from_index(self, idx: int, memory: List[dict]
                           ) -> dict:
        """Translate model's action index to a world-specific
        action payload."""

    @abstractmethod
    def submit(self, handle, individual_id: str,
                individual_kp, action: dict
                ) -> Tuple[Optional[dict], float]:
        """Send the action to the world. Return (world_reference,
        reward). world_reference is None if rejected."""

    @abstractmethod
    def step_fields(self, action: dict,
                     world_ref: Optional[dict]) -> dict:
        """Tier-specific fields for the agent_step record."""

    @abstractmethod
    def world_log(self, handle) -> List[dict]:
        """Fetch the world's log as a list of dicts."""

    @abstractmethod
    def verify_step(self, step_record: dict,
                     memory: List[dict], model, rng,
                     handle, world_log: List[dict]
                     ) -> Tuple[bool, str]:
        """Verify one agent_step: replay model + cross-reference."""


# =====================================================================
# FederatedAdapter — Sierpinski chaos game (in-process ScriptedWorld)
# =====================================================================

class FederatedAdapter(WorldAdapter):
    def tier_name(self) -> str:
        return "federated"

    def open(self, config):
        return config["world"]

    def enter(self, handle, individual_id, individual_kp, config):
        # ScriptedWorld has no petition; just record the initial point.
        return {"initial_point": list(config["initial_point"])}

    def _prev_point(self, memory):
        for rec in reversed(memory):
            if rec.get("type") == "world_entry" \
                    and "initial_point" in rec:
                return tuple(rec["initial_point"])
            if rec.get("type") == "agent_step" \
                    and rec.get("tier") == "federated":
                return tuple(rec["to_point"])
        return None

    def state(self, memory, handle):
        last_action = 0
        last_reward = 0.0
        for rec in reversed(memory):
            if rec.get("type") == "agent_step" \
                    and rec.get("tier") == "federated":
                last_action = rec["action_idx"]
                last_reward = rec["reward_micros"] / 1_000_000
                break
        p = self._prev_point(memory) or (500, 500)
        return (last_action, last_reward,
                p[0] / 1000.0, p[1] / 1000.0)

    def action_from_index(self, idx, memory):
        return {"transform_idx": idx % 3}

    def submit(self, handle, individual_id, individual_kp, action):
        world = handle
        a_idx = action["transform_idx"]
        b_pick, b_new = world.step()
        world.append_a_pick(a_idx)
        record = world.records[-1]
        reward = 0.1
        return ({"world_step_hash": record.record_hash()}, reward)

    def step_fields(self, action, world_ref):
        memory_prev = getattr(self, "_last_memory", None)
        # Caller computes from_point/to_point; adapter stores them
        return {
            "from_point": action.get("_from_point"),
            "to_point": action.get("_to_point"),
            "world_step_hash":
                world_ref["world_step_hash"] if world_ref else None,
        }

    def world_log(self, handle):
        return [
            {"body": r.body(), "sig": r.sig,
             "record_hash": r.record_hash()}
            for r in handle.records
        ]

    def verify_step(self, step_record, memory, model, rng,
                     handle, world_log):
        prev = self._prev_point(memory)
        if prev is None:
            return (False, "no prev_point")
        # Model replay
        state = self.state(memory, None)
        idx = model.act(state, rng)
        if idx != step_record["action_idx"]:
            return (False,
                     f"action_idx {step_record['action_idx']} "
                     f"!= replayed {idx}")
        # Transform math
        expected_to = SIERPINSKI[idx % 3].apply(*prev)
        if tuple(step_record["to_point"]) != expected_to:
            return (False, "to_point mismatch")
        # Cross-reference
        target = step_record["world_step_hash"]
        matched = None
        for e in world_log:
            if e["record_hash"] == target:
                matched = e
                break
        if matched is None:
            return (False, "world step not found")
        # Verify ScriptedWorld's signature
        body = {k: v for k, v in matched["body"].items()
                 if k != "sig"}
        try:
            signer = matched["body"]["world_id"]
            _pubkey_from_did(signer).verify(
                bytes.fromhex(matched["sig"]),
                _canonical(body))
        except Exception:
            return (False, "world step sig invalid")
        reward = step_record["reward_micros"] / 1_000_000
        model.learn(reward)
        return (True, "ok")


# =====================================================================
# ChessAdapter — signed chess world over HTTP
# =====================================================================

def _material_count(board, color):
    vals = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    total = 0
    for p in board.piece_map().values():
        if p.color == color:
            total += vals.get(p.piece_type, 0)
    return total


class ChessAdapter(WorldAdapter):
    def tier_name(self) -> str:
        return "chess"

    def open(self, config):
        return config["world_url"].rstrip("/")

    def enter(self, handle, individual_id, individual_kp, config):
        url = handle
        seat = config["seat"]
        display_name = config["display_name"]
        resp = _post_json(f"{url}/petition", {
            "petitioner_token": individual_id,
            "petitioner_name": display_name,
            "passport_admissions": [],
            "message": display_name + " enters",
        })
        if resp.get("kind") != "admission":
            raise RuntimeError(f"petition refused: {resp}")
        resp = _post_json(f"{url}/act", {
            "actor_token": individual_id,
            "type": "chess.sit",
            "payload": {"seat": seat},
        })
        if resp.get("kind") != "ack":
            raise RuntimeError(f"sit refused: {resp}")
        return {"seat": seat, "world_url_hash": _hash(url)}

    def _latest_fen(self, memory):
        """Best-effort: reconstruct latest FEN from memory's
        fen_before + uci pushes."""
        if not HAS_CHESS:
            return chess.STARTING_FEN
        board = chess.Board()
        for rec in memory:
            if rec.get("type") != "agent_step":
                continue
            if rec.get("tier") != "chess":
                continue
            try:
                m = chess.Move.from_uci(rec["uci"])
                if m in board.legal_moves:
                    board.push(m)
            except Exception:
                pass
        return board.fen()

    def _my_seat(self, memory):
        for rec in reversed(memory):
            if rec.get("type") == "world_entry" \
                    and "seat" in rec:
                return rec["seat"]
        return "white"

    def state(self, memory, handle):
        last_action = 0
        last_reward = 0.0
        for rec in reversed(memory):
            if rec.get("type") == "agent_step" \
                    and rec.get("tier") == "chess":
                last_action = rec["action_idx"]
                last_reward = rec["reward_micros"] / 1_000_000
                break
        seat = self._my_seat(memory)
        fen = self._latest_fen(memory)
        try:
            board = chess.Board(fen)
        except ValueError:
            board = chess.Board()
        my_color = (chess.WHITE if seat == "white" else chess.BLACK)
        my_mat = _material_count(board, my_color)
        their_mat = _material_count(board, not my_color)
        return (last_action, last_reward,
                min(my_mat, 30) / 30.0,
                min(their_mat, 30) / 30.0)

    def action_from_index(self, idx, memory):
        fen = self._latest_fen(memory)
        try:
            board = chess.Board(fen)
        except ValueError:
            board = chess.Board()
        legal = sorted(board.legal_moves, key=lambda m: m.uci())
        if not legal:
            return {"_no_moves": True}
        chosen = legal[idx % len(legal)]
        promo = (chess.piece_symbol(chosen.promotion)
                 if chosen.promotion else None)
        return {
            "_fen_before": fen,
            "_uci": chosen.uci(),
            "_is_capture": board.is_capture(chosen),
            "from_sq": chess.square_name(chosen.from_square),
            "to_sq": chess.square_name(chosen.to_square),
            "promotion": promo,
        }

    def submit(self, handle, individual_id, individual_kp, action):
        if action.get("_no_moves"):
            return (None, 0.0)
        url = handle
        resp = _post_json(f"{url}/act", {
            "actor_token": individual_id,
            "type": "chess.move",
            "payload": {
                "from_sq": action["from_sq"],
                "to_sq": action["to_sq"],
                "promotion": action["promotion"],
            },
        })
        if resp.get("kind") != "ack":
            return (None, 0.0)
        # Fetch signed log, find our move
        log = _get_json(f"{url}/signed-log")
        target_uci = action["_uci"]
        for e in reversed(log.get("entries", [])):
            b = e["body"]
            if (b["kind"] == "chess.move"
                    and b["actor_token"] == individual_id
                    and b["data"].get("uci") == target_uci):
                # Verify board state post-move for reward
                try:
                    board = chess.Board(action["_fen_before"])
                    board.push(chess.Move.from_uci(target_uci))
                    if action["_is_capture"]:
                        reward = 1.0
                    elif board.is_check():
                        reward = 0.5
                    else:
                        reward = 0.1
                except Exception:
                    reward = 0.1
                from signed_world_log import signed_entry_hash
                return ({"chess_world_signed_entry_hash":
                         signed_entry_hash(e)}, reward)
        return (None, 0.0)

    def step_fields(self, action, world_ref):
        return {
            "uci": action.get("_uci"),
            "fen_before": action.get("_fen_before"),
            "chess_world_signed_entry_hash":
                world_ref["chess_world_signed_entry_hash"]
                if world_ref else None,
        }

    def world_log(self, handle):
        log = _get_json(f"{handle}/signed-log")
        return log.get("entries", [])

    def verify_step(self, step_record, memory, model, rng,
                     handle, world_log):
        if not HAS_CHESS:
            return (False, "python-chess not installed")
        fen_before = step_record["fen_before"]
        try:
            board = chess.Board(fen_before)
        except ValueError:
            return (False, "bad FEN")
        legal = sorted(board.legal_moves, key=lambda m: m.uci())
        if not legal:
            return (False, "no legal moves")
        state = self.state(memory, None)
        idx = model.act(state, rng)
        if idx != step_record["action_idx"]:
            return (False,
                     f"action_idx {step_record['action_idx']} "
                     f"!= {idx}")
        expected_uci = legal[idx % len(legal)].uci()
        if expected_uci != step_record["uci"]:
            return (False,
                     f"uci {step_record['uci']} != "
                     f"{expected_uci}")
        # Cross-reference
        target = step_record["chess_world_signed_entry_hash"]
        matched = None
        for e in world_log:
            from signed_world_log import signed_entry_hash
            if signed_entry_hash(e) == target:
                matched = e
                break
        if matched is None:
            return (False, "signed entry not found")
        from signed_world_log import verify_signed_entry
        signer = memory_entry_signer = None
        for rec in memory:
            if rec.get("type") == "world_entry" \
                    and rec.get("tier") == "chess":
                signer = rec["world_signer"]
                break
        v = verify_signed_entry(matched, signer)
        if not v[0]:
            return (False, v[1])
        if matched["body"]["data"].get("uci") != step_record["uci"]:
            return (False, "world uci mismatch")
        reward = step_record["reward_micros"] / 1_000_000
        model.learn(reward)
        return (True, "ok")


# =====================================================================
# GrowingCanvasAdapter — C81 plot claims
# =====================================================================

CANVAS_CANDIDATES = [
    {"x": 0, "y": 0, "width": 2, "height": 2, "purpose": "corner"},
    {"x": 4, "y": 0, "width": 2, "height": 2, "purpose": "east"},
    {"x": 100, "y": 100, "width": 2, "height": 2, "purpose": "far"},
]


class GrowingCanvasAdapter(WorldAdapter):
    def tier_name(self) -> str:
        return "canvas"

    def open(self, config):
        return config["world"]

    def enter(self, handle, individual_id, individual_kp, config):
        from multiverse_c3 import Petition
        world = handle
        # Petition
        world.petition(Petition(
            petitioner_token=individual_id,
            petitioner_name=config.get("display_name", "canvas-bot"),
            passport_admissions=(),
            message="entering canvas",
        ))
        return {"display_name": config.get("display_name", "canvas-bot")}

    def state(self, memory, handle):
        last_action = 0
        last_reward = 0.0
        turn_count = 0
        for rec in reversed(memory):
            if rec.get("type") == "agent_step" \
                    and rec.get("tier") == "canvas":
                last_action = rec["action_idx"]
                last_reward = rec["reward_micros"] / 1_000_000
                # count previous canvas steps
        for rec in memory:
            if rec.get("type") == "agent_step" \
                    and rec.get("tier") == "canvas":
                turn_count += 1
        return (last_action, last_reward,
                min(turn_count, 10) / 10.0,
                0.5)

    def action_from_index(self, idx, memory):
        c = CANVAS_CANDIDATES[idx % 3]
        return dict(c)

    def submit(self, handle, individual_id, individual_kp, action):
        from multiverse_c3 import Act, Ack
        world = handle
        try:
            resp = world.act(Act(
                actor_token=individual_id,
                type="canvas.claim",
                payload=action,
            ))
        except Exception:
            return (None, 0.0)
        if isinstance(resp, Ack):
            events = world.events()
            if events:
                latest = events[-1]
                return ({"growth_event_hash": latest.event_hash(),
                          "accepted": True}, 1.0)
        return (None, 0.1)

    def step_fields(self, action, world_ref):
        return {
            "x": action["x"], "y": action["y"],
            "width": action["width"],
            "height": action["height"],
            "purpose": action["purpose"],
            "accepted": bool(world_ref),
            "growth_event_hash":
                world_ref["growth_event_hash"]
                if world_ref else None,
        }

    def world_log(self, handle):
        return [
            {"event_hash": e.event_hash(),
             "event_dict": e.to_dict()}
            for e in handle.events()
        ]

    def verify_step(self, step_record, memory, model, rng,
                     handle, world_log):
        state = self.state(memory, None)
        idx = model.act(state, rng)
        if idx != step_record["action_idx"]:
            return (False,
                     f"action_idx {step_record['action_idx']} "
                     f"!= {idx}")
        expected = CANVAS_CANDIDATES[idx % 3]
        if (step_record["x"] != expected["x"]
                or step_record["y"] != expected["y"]):
            return (False, "coords mismatch")
        if step_record.get("accepted"):
            target = step_record["growth_event_hash"]
            matched = False
            for e in world_log:
                if e["event_hash"] == target:
                    matched = True
                    break
            if not matched:
                return (False, "growth event not found")
        reward = step_record["reward_micros"] / 1_000_000
        model.learn(reward)
        return (True, "ok")


# =====================================================================
# Registry
# =====================================================================

DEFAULT_ADAPTERS = {
    "federated": FederatedAdapter(),
    "chess": ChessAdapter(),
    "canvas": GrowingCanvasAdapter(),
}
