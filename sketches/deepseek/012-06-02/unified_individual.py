"""
unified_individual.py — one individual, many worlds, many tiers.

A UnifiedIndividualSession lives across multiple worlds of
different tiers (chess, federated) with one model, one key,
one memory chain.

Memory format:
  - world_entry: {type, agent_id, world_id, tier, world_signer,
                  first_memory_index, [seat|initial_point], ts, sig}
  - agent_step:  {type, agent_id, world_id, tier, action_idx,
                  reward_micros, [tier-specific fields], ts, sig}

Tier-specific fields:
  chess:     uci, fen_before, chess_world_signed_entry_hash
  federated: from_point, to_point, world_step_hash

World logs (for verification):
  Dict[world_id, List[WorldLogEntry]] where each entry carries
  a hash (matched against the memory reference) and a payload
  (tier-specific; chess = {body, sig}, federated = full body
  with sig inside).

Verification:
  basic: sig chain + required tier fields per step
  full:  per-step model replay + world cross-reference

Honest limits:
  - One model architecture across worlds (TinyRNN with 3 actions).
    Different worlds need the same action space. Chess moves and
    Sierpinski transforms both fit n_actions=3, which is a
    coincidence of the demo's world choices, not a general rule.
  - No re-entry into the same world in one session (each world
    entered once). Re-entry would need world_state carry-over
    across entries; not supported here.
  - Cross-tier resume (an individual whose life resumes into a
    chess bundle mid-chain) needs the resume tier's verifier to
    understand mixed-tier memory. Not built; the unified verifier
    is a self-contained tier in its own right.
  - Reward is fixed at 0.1 in federated mode (no novelty signal).
    Sufficient for the demo; a real deployment would compute
    novelty against the world's recent points.
"""

import json
import random as _rng
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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
    IndividualBundle, build_model, apply_weights, serialize_weights,
    verify_bundle_basic,
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)
from coupled_learners import TinyRNN, SIERPINSKI
from world_agent_coupling import ScriptedWorld
from signed_world_log import (
    verify_signed_entry, signed_entry_hash,
)
from chess_individual import (
    _post_json, _get_json, _material_count,
)


def _entry_hash(rec):
    return _hash({k: v for k, v in rec.items() if k != "sig"})


def _merkle(hashes):
    if not hashes:
        return _hash("")
    level = list(hashes)
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [_hash((level[i] + level[i+1]).encode())
                 for i in range(0, len(level), 2)]
    return level[0]


# =====================================================================
# WorldLogEntry — uniform wrapper for world log entries
# =====================================================================

@dataclass(frozen=True)
class WorldLogEntry:
    """A world log entry, wrapped uniformly for cross-tier access.

    hash: what the individual's memory references.
    payload: tier-specific content.
      chess:     {"body": ..., "sig": ...} (signed world entry)
      federated: {**world_step_body, "sig": ...} (signed record)
    """
    hash: str
    payload: dict


def federated_world_log(
    world: ScriptedWorld,
) -> List[WorldLogEntry]:
    """Build WorldLogEntry list from a ScriptedWorld."""
    out = []
    for rec in world.records:
        body = rec.body()
        payload = {**body, "sig": rec.sig}
        out.append(WorldLogEntry(
            hash=rec.record_hash(),
            payload=payload,
        ))
    return out


# =====================================================================
# UnifiedIndividualSession
# =====================================================================

class UnifiedIndividualSession:
    def __init__(
        self,
        individual_kp,
        model,
        memory: Optional[List[Dict]] = None,
        rng_seed_override: Optional[int] = None,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self.individual_kp = individual_kp
        self.individual_id = _did_from_kp(individual_kp)
        self.model = model
        self.memory = memory if memory is not None else []
        self.last_action_idx = 0
        self.last_reward = 0.0
        self._rng_seed_override = rng_seed_override
        self._current_world_id: Optional[str] = None
        self._current_tier: Optional[str] = None
        self._current_world_signer: Optional[str] = None
        self._rng = None
        self._prev_point: Optional[Tuple[int, int]] = None
        self._scripted_world: Optional[ScriptedWorld] = None
        self._world_url: Optional[str] = None
        self._seat: Optional[str] = None

    def _reseed_rng(self, world_id: str):
        if self._rng_seed_override is not None:
            seed = int(self._rng_seed_override)
        else:
            h = _hash(self.individual_id + world_id).encode()
            seed = int(h, 16) & ((1 << 32) - 1)
        self._rng = _rng.Random(seed)

    def _append_entry(self, body: dict) -> dict:
        sig = self.individual_kp.sign(_canonical(body)).hex()
        entry = {**body, "sig": sig}
        self.memory.append(entry)
        return entry

    # -- Enter worlds -----------------------------------------

    def enter_federated_world(
        self,
        scripted_world: ScriptedWorld,
        initial_point: Tuple[int, int],
    ):
        self._current_world_id = scripted_world.world_id
        self._current_tier = "federated"
        self._current_world_signer = scripted_world.world_id
        self._scripted_world = scripted_world
        self._reseed_rng(self._current_world_id)
        self._prev_point = tuple(initial_point)
        body = {
            "type": "world_entry",
            "agent_id": self.individual_id,
            "world_id": self._current_world_id,
            "tier": "federated",
            "world_signer": scripted_world.world_id,
            "initial_point": list(initial_point),
            "first_memory_index": len(self.memory),
            "ts": _now(),
        }
        self._append_entry(body)

    def enter_chess_world(
        self,
        world_url: str,
        world_id: str,
        world_signer: str,
        seat: str,
        display_name: str,
    ):
        if not HAS_CHESS:
            raise RuntimeError("python-chess not installed")
        world_url = world_url.rstrip("/")
        resp = _post_json(f"{world_url}/petition", {
            "petitioner_token": self.individual_id,
            "petitioner_name": display_name,
            "passport_admissions": [],
            "message": display_name + " enters",
        })
        if resp.get("kind") != "admission":
            raise RuntimeError(f"petition refused: {resp}")
        resp = _post_json(f"{world_url}/act", {
            "actor_token": self.individual_id,
            "type": "chess.sit",
            "payload": {"seat": seat},
        })
        if resp.get("kind") != "ack":
            raise RuntimeError(f"sit refused: {resp}")
        self._current_world_id = world_id
        self._current_tier = "chess"
        self._current_world_signer = world_signer
        self._world_url = world_url
        self._seat = seat
        self._reseed_rng(world_id)
        self._prev_point = None
        body = {
            "type": "world_entry",
            "agent_id": self.individual_id,
            "world_id": world_id,
            "tier": "chess",
            "world_signer": world_signer,
            "seat": seat,
            "world_url_hash": _hash(world_url),
            "first_memory_index": len(self.memory),
            "ts": _now(),
        }
        self._append_entry(body)

    # -- Play -------------------------------------------------

    def play_federated_turn(self) -> Optional[dict]:
        if self._current_tier != "federated":
            return None
        x, y = self._prev_point
        state = (self.last_action_idx, self.last_reward,
                  x / 1000.0, y / 1000.0)
        action_idx = self.model.act(state, self._rng)
        b_pick, b_new = self._scripted_world.step()
        a_new = SIERPINSKI[action_idx % 3].apply(*self._prev_point)
        reward = 0.1
        self.model.learn(reward)
        world_step_record = self._scripted_world.records[-1]
        body = {
            "type": "agent_step",
            "agent_id": self.individual_id,
            "world_id": self._current_world_id,
            "tier": "federated",
            "action_idx": action_idx,
            "from_point": list(self._prev_point),
            "to_point": list(a_new),
            "world_step_hash": world_step_record.record_hash(),
            "reward_micros": int(reward * 1_000_000),
            "ts": _now(),
        }
        entry = self._append_entry(body)
        self._scripted_world.append_a_pick(action_idx)
        self._prev_point = a_new
        self.last_action_idx = action_idx
        self.last_reward = reward
        return entry

    def play_chess_turn(self) -> Optional[dict]:
        if self._current_tier != "chess":
            return None
        # Get current signed log
        log = _get_json(f"{self._world_url}/signed-log")
        entries = log.get("entries", [])
        latest_fen = chess.STARTING_FEN
        for e in entries:
            if e["body"]["kind"] == "chess.move":
                fen = e["body"]["data"].get("fen")
                if fen:
                    latest_fen = fen
        board = chess.Board(latest_fen)
        if (board.turn == chess.WHITE) != (self._seat == "white"):
            return None
        legal = sorted(board.legal_moves, key=lambda m: m.uci())
        if not legal:
            return None
        my_color = chess.WHITE if self._seat == "white" else chess.BLACK
        my_mat = _material_count(board, my_color)
        their_mat = _material_count(board, not my_color)
        state = (self.last_action_idx, self.last_reward,
                  min(my_mat, 30) / 30.0,
                  min(their_mat, 30) / 30.0)
        action_idx = self.model.act(state, self._rng)
        chosen = legal[action_idx % len(legal)]
        is_capture = board.is_capture(chosen)
        from_sq = chess.square_name(chosen.from_square)
        to_sq = chess.square_name(chosen.to_square)
        promotion = (chess.piece_symbol(chosen.promotion)
                     if chosen.promotion else None)
        resp = _post_json(f"{self._world_url}/act", {
            "actor_token": self.individual_id,
            "type": "chess.move",
            "payload": {
                "from_sq": from_sq, "to_sq": to_sq,
                "promotion": promotion,
            },
        })
        if resp.get("kind") != "ack":
            return None
        # Find signed log entry
        log = _get_json(f"{self._world_url}/signed-log")
        signed_entries = log.get("entries", [])
        signed_entry = None
        for e in reversed(signed_entries):
            b = e["body"]
            if (b["kind"] == "chess.move"
                    and b["actor_token"] == self.individual_id
                    and b["data"].get("uci") == chosen.uci()):
                signed_entry = e
                break
        if signed_entry is None:
            return None
        entry_hash = signed_entry_hash(signed_entry)
        board_push = board.copy()
        board_push.push(chosen)
        if is_capture:
            reward = 1.0
        elif board_push.is_check():
            reward = 0.5
        else:
            reward = 0.1
        self.model.learn(reward)
        body = {
            "type": "agent_step",
            "agent_id": self.individual_id,
            "world_id": self._current_world_id,
            "tier": "chess",
            "action_idx": action_idx,
            "uci": chosen.uci(),
            "fen_before": latest_fen,
            "chess_world_signed_entry_hash": entry_hash,
            "reward_micros": int(reward * 1_000_000),
            "ts": _now(),
        }
        entry = self._append_entry(body)
        self.last_action_idx = action_idx
        self.last_reward = reward
        return entry


# =====================================================================
# Pack
# =====================================================================

def pack_unified_bundle(
    session: UnifiedIndividualSession,
    persona: str,
    name: str,
    initial_seed: int,
) -> IndividualBundle:
    weights = serialize_weights(session.model)
    weights_hash = _hash(json.dumps(
        weights, sort_keys=True,
        separators=(",", ":")).encode())
    memory_root = _merkle(
        [_entry_hash(r) for r in session.memory])

    world_contexts = []
    for i, rec in enumerate(session.memory):
        if rec.get("type") == "world_entry":
            ctx = {
                "world_id": rec["world_id"],
                "tier": rec["tier"],
                "world_signer": rec["world_signer"],
                "first_memory_index": i,
            }
            if "seat" in rec:
                ctx["seat"] = rec["seat"]
            if "initial_point" in rec:
                ctx["initial_point"] = rec["initial_point"]
            world_contexts.append(ctx)

    body = {
        "kind": "unified_individual",
        "version": "1.7",
        "individual_id": session.individual_id,
        "name": name,
        "persona": persona,
        "created_at": _now(),
        "parent_did": None,
        "lineage_root": session.individual_id,
        "model_config": {
            "kind": "rnn", "hidden": 4,
            "n_actions": 3, "n_extra_inputs": 0,
        },
        "model_initial_seed": int(initial_seed),
        "model_weights_hash": weights_hash,
        "observes": False,
        "memory_entries": len(session.memory),
        "memory_root": memory_root,
        "observations_hash": _hash("[]"),
        "world_contexts": world_contexts,
        "ts": _now(),
    }
    sig = session.individual_kp.sign(_canonical(body)).hex()
    return IndividualBundle(
        manifest={**body, "sig": sig},
        memory=list(session.memory),
        weights=weights,
        initial_weights=None,
        observations=[],
        ancestry=[],
        checkpoint_weights=None,
    )


# =====================================================================
# Verify
# =====================================================================

def verify_unified_individual_basic(
    bundle: IndividualBundle,
) -> Tuple[bool, str]:
    ok, reason = verify_bundle_basic(bundle)
    if not ok:
        return (False, f"basic: {reason}")
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") != "agent_step":
            continue
        tier = rec.get("tier")
        if tier not in ("chess", "federated"):
            return (False,
                     f"memory[{i}]: unknown tier {tier!r}")
        if "action_idx" not in rec:
            return (False, f"memory[{i}]: missing action_idx")
        if "reward_micros" not in rec:
            return (False, f"memory[{i}]: missing reward_micros")
        if tier == "chess":
            for f in ("uci", "fen_before",
                       "chess_world_signed_entry_hash"):
                if f not in rec:
                    return (False, f"memory[{i}]: missing {f}")
        elif tier == "federated":
            for f in ("from_point", "to_point",
                       "world_step_hash"):
                if f not in rec:
                    return (False, f"memory[{i}]: missing {f}")
    return (True, "unified basic verifies")


def verify_unified_individual_full(
    bundle: IndividualBundle,
    world_logs: Dict[str, List[WorldLogEntry]],
) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    ok, reason = verify_unified_individual_basic(bundle)
    if not ok:
        return (False, reason)

    model = build_model(bundle.manifest["model_config"])
    if bundle.initial_weights is not None:
        apply_weights(model, bundle.initial_weights)

    individual_id = bundle.manifest["individual_id"]
    rng = None
    prev_action_idx = 0
    prev_reward = 0.0
    prev_point = None
    current_world_id = None
    current_tier = None
    current_signer = None
    step_count = 0

    for i, rec in enumerate(bundle.memory):
        if rec.get("type") == "world_entry":
            current_world_id = rec["world_id"]
            current_tier = rec["tier"]
            current_signer = rec["world_signer"]
            h = _hash(individual_id + current_world_id).encode()
            seed = int(h, 16) & ((1 << 32) - 1)
            rng = _rng.Random(seed)
            prev_point = (tuple(rec["initial_point"])
                          if "initial_point" in rec else None)
            continue

        if rec.get("type") != "agent_step":
            continue
        step_count += 1

        tier = rec["tier"]
        if tier != current_tier:
            return (False,
                     f"memory[{i}]: tier {tier!r} != "
                     f"current world tier {current_tier!r}")

        if tier == "chess":
            if not HAS_CHESS:
                return (False, "python-chess not installed")
            try:
                board = chess.Board(rec["fen_before"])
            except ValueError:
                return (False, f"memory[{i}]: bad FEN")
            legal = sorted(board.legal_moves,
                            key=lambda m: m.uci())
            if not legal:
                return (False,
                         f"memory[{i}]: no legal moves")
            my_color = (chess.WHITE
                         if rec["fen_before"].split(" ")[1] == "w"
                         else chess.BLACK)
            my_mat = _material_count(board, my_color)
            their_mat = _material_count(board, not my_color)
            state = (prev_action_idx, prev_reward,
                      min(my_mat, 30) / 30.0,
                      min(their_mat, 30) / 30.0)
            expected_idx = model.act(state, rng)
            if expected_idx != rec["action_idx"]:
                return (False,
                         f"memory[{i}]: action_idx "
                         f"{rec['action_idx']} != "
                         f"replayed {expected_idx}")
            expected_uci = legal[expected_idx % len(legal)].uci()
            if expected_uci != rec["uci"]:
                return (False,
                         f"memory[{i}]: uci {rec['uci']} != "
                         f"replayed {expected_uci}")
            target = rec["chess_world_signed_entry_hash"]
            matched = None
            for e in world_logs.get(current_world_id, []):
                if e.hash == target:
                    matched = e
                    break
            if matched is None:
                return (False,
                         f"memory[{i}]: signed entry "
                         f"not found")
            v = verify_signed_entry(
                matched.payload, current_signer)
            if not v[0]:
                return (False, f"memory[{i}]: {v[1]}")
            if matched.payload["body"]["data"].get("uci") \
                    != rec["uci"]:
                return (False,
                         f"memory[{i}]: world uci mismatch")
            prev_point = None

        elif tier == "federated":
            if prev_point is None:
                return (False,
                         f"memory[{i}]: no prev_point for "
                         f"federated step")
            x, y = prev_point
            state = (prev_action_idx, prev_reward,
                      x / 1000.0, y / 1000.0)
            expected_idx = model.act(state, rng)
            if expected_idx != rec["action_idx"]:
                return (False,
                         f"memory[{i}]: action_idx "
                         f"{rec['action_idx']} != "
                         f"replayed {expected_idx}")
            expected_to = SIERPINSKI[
                expected_idx % 3].apply(*prev_point)
            if tuple(rec["to_point"]) != expected_to:
                return (False,
                         f"memory[{i}]: to_point mismatch")
            target = rec["world_step_hash"]
            matched = None
            for e in world_logs.get(current_world_id, []):
                if e.hash == target:
                    matched = e
                    break
            if matched is None:
                return (False,
                         f"memory[{i}]: world step not found")
            # Verify ScriptedWorld signature on the record
            body = {k: v for k, v in matched.payload.items()
                     if k != "sig"}
            try:
                _pubkey_from_did(current_signer).verify(
                    bytes.fromhex(matched.payload["sig"]),
                    _canonical(body))
            except Exception:
                return (False,
                         f"memory[{i}]: world step sig "
                         f"invalid")
            prev_point = tuple(rec["to_point"])

        reward = rec["reward_micros"] / 1_000_000
        model.learn(reward)
        prev_action_idx = rec["action_idx"]
        prev_reward = reward

    final = serialize_weights(model)
    if json.dumps(final, sort_keys=True) != \
            json.dumps(bundle.weights, sort_keys=True):
        return (False, "replayed final weights != bundle weights")
    return (True,
             f"unified individual full verifies "
             f"({step_count} steps across "
             f"{len(bundle.manifest['world_contexts'])} worlds)")


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    from multiverse_c73 import ChessWorld
    from signed_world_log import (
        SignedLogWorld, SignedLogWorldServer,
    )
    from chess_individual import ChessIndividualSession
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import time
    import json as _json

    if not HAS_CRYPTO or not HAS_CHESS:
        raise RuntimeError(
            "requires cryptography and python-chess")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "unified_individual"
    root.mkdir(parents=True, exist_ok=True)

    # ---- Chess world (signed) ----
    world_kp = Ed25519PrivateKey.generate()
    base = ChessWorld("world:park", "Union Square")
    signed = SignedLogWorld(base, world_kp)
    server = SignedLogWorldServer(signed, port=0)
    server.serve_in_thread()
    time.sleep(0.2)
    world_url = (f"http://127.0.0.1:"
                  f"{server._httpd.server_address[1]}")

    try:
        # ---- Black opponent ----
        black_kp = Ed25519PrivateKey.generate()
        black_model = TinyRNN(
            n_actions=3, hidden=4, n_extra_inputs=0, seed=300)
        black_memory: List[Dict] = []
        black = ChessIndividualSession(
            individual_kp=black_kp, model=black_model,
            world_url=world_url, world_id="world:park",
            world_signer=signed.world_signer,
            memory=black_memory, seat="black")
        black.enter_and_sit("Black-bot")

        # ---- Unified individual (white) ----
        white_kp = Ed25519PrivateKey.generate()
        white_model = TinyRNN(
            n_actions=3, hidden=4, n_extra_inputs=0, seed=100)
        white = UnifiedIndividualSession(
            individual_kp=white_kp, model=white_model)

        # Enter chess, play 2 moves
        white.enter_chess_world(
            world_url, "world:park", signed.world_signer,
            "white", "White-bot")
        chess_moves_played = 0
        for _ in range(3):
            e = white.play_chess_turn()
            if e is None:
                break
            chess_moves_played += 1
            black.play_turn()

        # Enter federated world, do 5 steps
        fed_kp = Ed25519PrivateKey.generate()
        fed_world = ScriptedWorld(
            kp=fed_kp, initial_point_b=(800, 800),
            k_b=50, prng_seed_b=0xBBBB, rule=SIERPINSKI)
        white.enter_federated_world(
            fed_world, initial_point=(200, 800))
        fed_steps = 0
        for _ in range(5):
            e = white.play_federated_turn()
            if e is not None:
                fed_steps += 1

        # ---- Pack bundle ----
        bundle = pack_unified_bundle(
            white,
            persona="White-bot, a chess player who stepped into "
                    "the chaos game",
            name="White-bot", initial_seed=100)
        bundle.save(root / "unified")
        loaded = IndividualBundle.load(root / "unified")

        # ---- Build world logs ----
        chess_signed_log = signed.signed_log_since(None)
        chess_world_log = [
            WorldLogEntry(hash=signed_entry_hash(e), payload=e)
            for e in chess_signed_log
        ]
        federated_log = federated_world_log(fed_world)

        world_logs = {
            "world:park": chess_world_log,
            fed_world.world_id: federated_log,
        }

        # ---- Verify ----
        v_basic = verify_unified_individual_basic(loaded)
        v_full = verify_unified_individual_full(
            loaded, world_logs)

        # ---- Tamper: chess fen_before ----
        tampered_chess = IndividualBundle(
            manifest=dict(loaded.manifest),
            memory=list(loaded.memory),
            weights=dict(loaded.weights),
            initial_weights=None, observations=[],
            ancestry=[], checkpoint_weights=None,
        )
        for i, r in enumerate(tampered_chess.memory):
            if r.get("tier") == "chess":
                tampered_chess.memory[i] = {
                    **r,
                    "fen_before":
                        "8/8/8/8/8/8/8/K6k w - - 0 1",
                }
                break
        t1 = verify_unified_individual_full(
            tampered_chess, world_logs)

        # ---- Tamper: federated to_point ----
        tampered_fed = IndividualBundle(
            manifest=dict(loaded.manifest),
            memory=list(loaded.memory),
            weights=dict(loaded.weights),
            initial_weights=None, observations=[],
            ancestry=[], checkpoint_weights=None,
        )
        for i, r in enumerate(tampered_fed.memory):
            if r.get("tier") == "federated":
                tampered_fed.memory[i] = {
                    **r,
                    "to_point": [999, 999],
                }
                break
        t2 = verify_unified_individual_full(
            tampered_fed, world_logs)

        # ---- Missing chess world log ----
        t3 = verify_unified_individual_full(
            loaded, {fed_world.world_id: federated_log})

        # ---- Print ----
        print("=" * 74)
        print("Unified individual — one life, two worlds, two tiers")
        print("=" * 74)
        print()
        print(f"  Individual: {loaded.individual_id[:32]}...")
        print(f"  World contexts: "
              f"{len(loaded.manifest['world_contexts'])}")
        for ctx in loaded.manifest["world_contexts"]:
            print(f"    {ctx['tier']:10s}  {ctx['world_id'][:24]}...  "
                  f"@ idx {ctx['first_memory_index']}")
        print()
        print(f"  Chess moves:      {chess_moves_played}")
        print(f"  Federated steps:  {fed_steps}")
        print(f"  Memory entries:   {len(loaded.memory)}")
        print()
        print("  Verification:")
        print(f"    basic:  {v_basic[0]}  ({v_basic[1]})")
        print(f"    full:   {v_full[0]}  ({v_full[1]})")
        print()
        print("  Tampering:")
        print(f"    chess fen_before altered:   "
              f"{t1[0]}  ({t1[1]})")
        print(f"    federated to_point altered: "
              f"{t2[0]}  ({t2[1]})")
        print(f"    chess world log missing:    "
              f"{t3[0]}  ({t3[1]})")
        print()
        print("  What this establishes:")
        print("    - One individual, one model, one key, one chain.")
        print("      The individual lives in a chess world then a")
        print("      federated world, with all memory in a single")
        print("      signed Merkle chain.")
        print("    - The model carries across worlds. Weights and")
        print("      RNN hidden state persist; only RNG reseeds")
        print("      at each world_entry (exploration is per-")
        print("      world, learning is per-individual).")
        print("    - Per-step dispatch. Each agent_step carries")
        print("      a tier; the verifier dispatches to the")
        print("      tier's replay logic. Chess steps re-derive")
        print("      legal moves from fen_before; federated steps")
        print("      re-derive transforms from prev_point.")
        print("    - World logs are cross-referenced uniformly.")
        print("      Each entry is a {hash, payload} wrapper;")
        print("      chess payloads carry {body, sig}, federated")
        print("      payloads carry {body..., sig}. Both are")
        print("      signature-verified against the world's key.")
        print("    - Tampering is caught per-tier: altered chess")
        print("      FEN breaks chess replay; altered federated")
        print("      to_point breaks federated replay; missing")
        print("      chess log breaks cross-reference.")
        print()
        print("  Honest limit: both worlds use n_actions=3 — a")
        print("  coincidence of the demo, not a general rule.")
        print("  A production system would need action spaces to")
        print("  agree, or a projection layer between them.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I dwell in Possibility –'")
        print("    'A fairer House than Prose –'")

        audit = {
            "individual_id": loaded.individual_id,
            "worlds": [
                {"world_id": c["world_id"],
                 "tier": c["tier"],
                 "first_memory_index":
                     c["first_memory_index"]}
                for c in loaded.manifest["world_contexts"]
            ],
            "chess_moves_played": chess_moves_played,
            "federated_steps": fed_steps,
            "memory_entries": len(loaded.memory),
            "verification": {
                "basic": v_basic[0],
                "full": v_full[0],
            },
            "tampering": {
                "chess_fen_detected": not t1[0],
                "federated_point_detected": not t2[0],
                "missing_chess_log_detected": not t3[0],
            },
        }
        (root / "unified_individual_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root}/unified_individual_demo.json")
        return audit
    finally:
        try:
            server.stop()
        except Exception:
            pass
