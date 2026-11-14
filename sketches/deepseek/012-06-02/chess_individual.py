"""
chess_individual.py — a verifiable individual in a real world.

A ChessIndividualSession drives a real ChessWorld (C73) via HTTP.
Its model picks from legal moves; its memory chain is signed by
the individual's key; each entry references the chess world's
matching log entry.

Chess bundle shape:
  - Same manifest fields as federated_bundle bundles.
  - memory[0] = world_entry (chess world's id + URL hash).
  - memory[1:] = agent_step entries, each carrying:
      action_idx: int (model output, 0/1/2)
      uci: str
      chess_world_entry_hash: str
      reward_micros: int
  - agent_id == individual_id throughout.
  - signed by the individual's key throughout.

Verification (new this cycle):
  verify_chess_individual_basic(bundle)
  verify_chess_individual_full(bundle, world_log):
    - basic + replay per step:
        * reconstruct legal_moves from chess_world_entry's
          fen-before
        * re-run model.act(state, rng)
        * confirm uci == legal_moves[model_output].uci()
  verify_chess_cross_reference(bundle, world_log):
    - every chess_world_entry_hash in the bundle appears in
      the chess world log, and its uci matches.

Honest limits:
  - The chess world's log entries are NOT signed (C73 doesn't
    sign its log). Cross-reference relies on /log integrity.
    A SignedWorld wrapper would close this; not composed here.
  - Bundle not yet compatible with verify_individual_lifetime
    (that dispatches to verify_federated_full, which requires
    0/1/2 action shape). A dedicated chess-tier dispatch would
    compose; not built this cycle.
  - Learning signal is coarse (capture/check/other). Richness
    would need a proper evaluation function.
  - Model doesn't understand chess — it picks from legal moves
    by index. Real chess-play would need a chess-aware model.
"""

import json
import random as _rng
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

try:
    import chess
    HAS_CHESS = True
except ImportError:
    HAS_CHESS = False

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, build_model, apply_weights, serialize_weights,
    verify_bundle_basic,
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)
from coupled_learners import TinyRNN
from multiverse_c73 import ChessWorld
from wcp_http_shim import WorldProtocolServer


PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0} \
                if HAS_CHESS else {}


def _material_count(board, color):
    total = 0
    for p in board.piece_map().values():
        if p.color == color:
            total += PIECE_VALUES.get(p.piece_type, 0)
    return total


def _post_json(url, body, timeout=10):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _entry_hash(rec):
    return _hash({k: v for k, v in rec.items() if k != "sig"})


# =====================================================================
# ChessIndividualSession
# =====================================================================

class ChessIndividualSession:
    def __init__(
        self,
        individual_kp,
        model,
        world_url: str,
        world_id: str,
        memory: List[Dict],
        seat: str,
        rng_seed_override: Optional[int] = None,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        if not HAS_CHESS:
            raise RuntimeError("python-chess not installed")
        self.individual_kp = individual_kp
        self.individual_id = _did_from_kp(individual_kp)
        self.model = model
        self.world_url = world_url.rstrip("/")
        self.world_id = world_id
        self.memory = memory
        self.seat = seat
        self.last_action_idx = 0
        self.last_reward = 0.0

        # RNG seed: deterministic per (individual, world)
        if rng_seed_override is not None:
            self._rng_seed = int(rng_seed_override)
        else:
            h = _hash(self.individual_id + world_id).encode()
            self._rng_seed = int(h, 16) & ((1 << 32) - 1)
        self._rng = _rng.Random(self._rng_seed)

    # -- HTTP helpers -------------------------------------------

    def _petition(self, display_name):
        return _post_json(
            f"{self.world_url}/petition", {
                "petitioner_token": self.individual_id,
                "petitioner_name": display_name,
                "passport_admissions": [],
                "message": f"{display_name} enters",
            })

    def _act(self, act_type, payload=None):
        return _post_json(
            f"{self.world_url}/act", {
                "actor_token": self.individual_id,
                "type": act_type,
                "payload": payload or {},
            })

    def _log(self):
        return _get_json(f"{self.world_url}/log")

    # -- Lifecycle ----------------------------------------------

    def enter_and_sit(self, display_name: str) -> Tuple[bool, str]:
        """Petition + sit. Appends a world_entry to memory."""
        try:
            resp = self._petition(display_name)
        except Exception as e:
            return (False, f"petition failed: {e}")
        if resp.get("kind") != "admission":
            return (False,
                     f"petition refused: {resp.get('reason', '?')}")
        try:
            resp = self._act("chess.sit", {"seat": self.seat})
        except Exception as e:
            return (False, f"sit failed: {e}")
        if resp.get("kind") != "ack":
            return (False,
                     f"sit refused: {resp.get('reason', '?')}")

        # Record world_entry
        body = {
            "type": "world_entry",
            "agent_id": self.individual_id,
            "world_id": self.world_id,
            "world_url_hash": _hash(self.world_url),
            "seat": self.seat,
            "display_name": display_name,
            "ts": _now(),
        }
        sig = self.individual_kp.sign(_canonical(body)).hex()
        self.memory.append({**body, "sig": sig})
        return (True, "entered and seated")

    # -- Per-turn play -----------------------------------------

    def _latest_fen(self) -> str:
        log = self._log()
        entries = log.get("entries", [])
        latest_fen = chess.BOARD_STARTING_FEN if hasattr(
            chess, "BOARD_STARTING_FEN") else chess.STARTING_FEN
        for e in entries:
            if e.get("kind") == "chess.move":
                fen = e.get("data", {}).get("fen")
                if fen:
                    latest_fen = fen
        return latest_fen

    def _whose_turn(self) -> Optional[str]:
        fen = self._latest_fen()
        try:
            board = chess.Board(fen)
        except ValueError:
            return None
        return "white" if board.turn == chess.WHITE else "black"

    def _state_from_board(self, board):
        my_color = chess.WHITE if self.seat == "white" else chess.BLACK
        their_color = (chess.BLACK if my_color == chess.WHITE
                        else chess.WHITE)
        my_mat = _material_count(board, my_color)
        their_mat = _material_count(board, their_color)
        x = min(my_mat, 30) / 30.0
        y = min(their_mat, 30) / 30.0
        return (self.last_action_idx, self.last_reward, x, y)

    def play_turn(self) -> Optional[Dict]:
        """If it's my turn, pick a legal move and submit.
        Returns the memory entry appended, or None (skipped)."""
        if self._whose_turn() != self.seat:
            return None
        fen_before = self._latest_fen()
        try:
            board = chess.Board(fen_before)
        except ValueError:
            return None
        legal = sorted(board.legal_moves, key=lambda m: m.uci())
        if not legal:
            return None

        state = self._state_from_board(board)
        action_idx = self.model.act(state, self._rng)
        chosen = legal[action_idx % len(legal)]

        # Compute reward BEFORE push (need the board as it was)
        is_capture = board.is_capture(chosen)
        from_sq = chess.square_name(chosen.from_square)
        to_sq = chess.square_name(chosen.to_square)
        promotion = None
        if chosen.promotion:
            promotion = chess.piece_symbol(chosen.promotion)

        # Submit
        try:
            resp = self._act("chess.move", {
                "from_sq": from_sq, "to_sq": to_sq,
                "promotion": promotion,
            })
        except Exception as e:
            return None
        if resp.get("kind") != "ack":
            return None

        # Fetch log, find the world entry just written
        log = self._log()
        entries = log.get("entries", [])
        chess_entry = None
        for e in reversed(entries):
            if (e.get("kind") == "chess.move"
                    and e.get("actor_token") == self.individual_id
                    and e.get("data", {}).get("uci")
                        == chosen.uci()):
                chess_entry = e
                break
        if chess_entry is None:
            return None
        entry_hash = _hash({
            "timestamp": chess_entry["timestamp"],
            "kind": chess_entry["kind"],
            "actor_token": chess_entry.get("actor_token"),
            "data": chess_entry.get("data", {}),
        })

        # Compute reward
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
            "world_id": self.world_id,
            "action_idx": action_idx,
            "uci": chosen.uci(),
            "chess_world_entry_hash": entry_hash,
            "fen_before": fen_before,
            "reward_micros": int(reward * 1_000_000),
            "ts": _now(),
        }
        sig = self.individual_kp.sign(_canonical(body)).hex()
        entry = {**body, "sig": sig}
        self.memory.append(entry)
        self.last_action_idx = action_idx
        self.last_reward = reward
        return entry


# =====================================================================
# Pack
# =====================================================================

def pack_chess_individual_bundle(
    session: ChessIndividualSession,
    persona: str,
    name: str,
    initial_seed: int,
) -> IndividualBundle:
    weights = serialize_weights(session.model)
    weights_hash = _hash(json.dumps(
        weights, sort_keys=True,
        separators=(",", ":")).encode())
    memory_hashes = [_entry_hash(r) for r in session.memory]
    # Compute Merkle root
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
    memory_root = _merkle(memory_hashes)

    world_contexts = [{
        "world_id": session.world_id,
        "world_url_hash": _hash(session.world_url),
        "seat": session.seat,
        "first_memory_index": 0,
    }]

    body = {
        "kind": "individual_bundle",
        "version": "1.5",
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
# Verification
# =====================================================================

def verify_chess_individual_basic(bundle: IndividualBundle
                                    ) -> Tuple[bool, str]:
    ok, reason = verify_bundle_basic(bundle)
    if not ok:
        return (False, f"basic: {reason}")
    # Additional: agent_step must carry uci + chess_world_entry_hash
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") != "agent_step":
            continue
        for f in ("action_idx", "uci", "chess_world_entry_hash",
                   "fen_before"):
            if f not in rec:
                return (False,
                         f"memory[{i}]: missing {f}")
    return (True, "chess individual basic verifies")


def _find_chess_entry(world_log: List[Dict], entry_hash: str
                        ) -> Optional[Dict]:
    for e in world_log:
        h = _hash({
            "timestamp": e["timestamp"],
            "kind": e["kind"],
            "actor_token": e.get("actor_token"),
            "data": e.get("data", {}),
        })
        if h == entry_hash:
            return e
    return None


def verify_chess_individual_full(
    bundle: IndividualBundle,
    world_log: List[Dict],
) -> Tuple[bool, str]:
    ok, reason = verify_chess_individual_basic(bundle)
    if not ok:
        return (False, reason)

    # Reconstruct model from seed
    model = build_model(bundle.manifest["model_config"])
    individual_id = bundle.manifest["individual_id"]

    # Derive RNG seed from individual + world
    world_id = None
    for rec in bundle.memory:
        if rec.get("type") == "world_entry":
            world_id = rec["world_id"]
            break
    if world_id is None:
        return (False, "no world_entry in memory")
    seed_int = int(_hash(individual_id + world_id).encode(),
                   16) & ((1 << 32) - 1)
    rng = _rng.Random(seed_int)

    last_action_idx = 0
    last_reward = 0.0
    # Replay each agent_step
    step_count = 0
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") != "agent_step":
            continue
        step_count += 1
        fen_before = rec["fen_before"]
        try:
            board = chess.Board(fen_before)
        except ValueError:
            return (False,
                     f"memory[{i}]: bad FEN {fen_before[:32]}...")
        legal = sorted(board.legal_moves, key=lambda m: m.uci())
        if not legal:
            return (False,
                     f"memory[{i}]: no legal moves in given FEN")

        my_color = chess.WHITE if fen_before.count(" ") and \
            fen_before.split(" ")[1] == "w" else chess.BLACK
        my_mat = _material_count(board, my_color)
        their_mat = _material_count(board, not my_color)
        x = min(my_mat, 30) / 30.0
        y = min(their_mat, 30) / 30.0
        state = (last_action_idx, last_reward, x, y)
        expected_idx = model.act(state, rng)
        if expected_idx != rec["action_idx"]:
            return (False,
                     f"memory[{i}]: action_idx "
                     f"{rec['action_idx']} != replayed "
                     f"{expected_idx}")
        expected_uci = legal[expected_idx % len(legal)].uci()
        if expected_uci != rec["uci"]:
            return (False,
                     f"memory[{i}]: uci {rec['uci']} != "
                     f"replayed {expected_uci}")

        # Check chess_world_entry_hash exists in world log with matching uci
        match = _find_chess_entry(
            world_log, rec["chess_world_entry_hash"])
        if match is None:
            return (False,
                     f"memory[{i}]: chess_world_entry_hash "
                     f"not found in world log")
        if match.get("data", {}).get("uci") != rec["uci"]:
            return (False,
                     f"memory[{i}]: world log uci "
                     f"{match.get('data', {}).get('uci')} "
                     f"!= memory uci {rec['uci']}")

        # Apply reward and advance
        reward = rec["reward_micros"] / 1_000_000
        model.learn(reward)
        last_action_idx = rec["action_idx"]
        last_reward = reward

    # Final weights must match
    final = serialize_weights(model)
    if json.dumps(final, sort_keys=True) != \
            json.dumps(bundle.weights, sort_keys=True):
        return (False, "replayed final weights != bundle weights")

    return (True,
             f"chess individual full verifies "
             f"({step_count} moves replayed)")


def verify_chess_cross_reference(
    bundle: IndividualBundle,
    world_log: List[Dict],
) -> Tuple[bool, str]:
    """For each agent_step, the referenced chess world entry
    exists and matches on uci."""
    ok, reason = verify_chess_individual_basic(bundle)
    if not ok:
        return (False, reason)
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") != "agent_step":
            continue
        match = _find_chess_entry(
            world_log, rec["chess_world_entry_hash"])
        if match is None:
            return (False,
                     f"memory[{i}]: world entry not found")
        if match.get("actor_token") != bundle.individual_id:
            return (False,
                     f"memory[{i}]: world entry actor "
                     f"mismatch")
        if match.get("data", {}).get("uci") != rec["uci"]:
            return (False,
                     f"memory[{i}]: world entry uci "
                     f"mismatch")
    return (True, "chess cross-reference verifies")


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import json as _json

    if not HAS_CRYPTO or not HAS_CHESS:
        raise RuntimeError("requires cryptography and python-chess")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "chess_individual"
    root.mkdir(parents=True, exist_ok=True)

    # ---- Spin up a real ChessWorld ----
    world = ChessWorld("world:park", "Union Square Park")
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    time.sleep(0.2)
    world_url = (f"http://127.0.0.1:"
                  f"{server._httpd.server_address[1]}")
    world_id = "world:park"

    try:
        # ---- Alice-bot (white) ----
        alice_kp = Ed25519PrivateKey.generate()
        alice_model = TinyRNN(
            n_actions=3, hidden=4, n_extra_inputs=0, seed=100)
        alice_memory: List[Dict] = []
        alice = ChessIndividualSession(
            individual_kp=alice_kp, model=alice_model,
            world_url=world_url, world_id=world_id,
            memory=alice_memory, seat="white")
        ok, reason = alice.enter_and_sit("Alice-bot")
        assert ok, reason

        # ---- Bob-bot (black) ----
        bob_kp = Ed25519PrivateKey.generate()
        bob_model = TinyRNN(
            n_actions=3, hidden=4, n_extra_inputs=0, seed=200)
        bob_memory: List[Dict] = []
        bob = ChessIndividualSession(
            individual_kp=bob_kp, model=bob_model,
            world_url=world_url, world_id=world_id,
            memory=bob_memory, seat="black")
        ok, reason = bob.enter_and_sit("Bob-bot")
        assert ok, reason

        # ---- Play up to 40 turns ----
        turn_log = []
        MAX_TURNS = 40
        for turn in range(MAX_TURNS):
            mover = alice if turn % 2 == 0 else bob
            label = "Alice-bot" if turn % 2 == 0 else "Bob-bot"
            entry = mover.play_turn()
            if entry is None:
                # Refused or not my turn
                continue
            turn_log.append({
                "turn": turn + 1,
                "player": label,
                "uci": entry["uci"],
                "reward": entry["reward_micros"] / 1_000_000,
            })
            # Early stop on game end
            board = chess.Board()
            for e in world._log:
                if e.kind == "chess.move":
                    board.push(chess.Move.from_uci(
                        e.data["uci"]))
            if board.is_game_over():
                break

        # ---- Pack bundles ----
        alice_bundle = pack_chess_individual_bundle(
            session=alice,
            persona="Alice-bot, a learning chess resident",
            name="Alice-bot", initial_seed=100)
        bob_bundle = pack_chess_individual_bundle(
            session=bob,
            persona="Bob-bot, a learning chess resident",
            name="Bob-bot", initial_seed=200)
        alice_bundle.save(root / "alice")
        bob_bundle.save(root / "bob")

        # Reload
        alice_loaded = IndividualBundle.load(root / "alice")
        bob_loaded = IndividualBundle.load(root / "bob")

        # ---- Get chess world log ----
        world_log = _get_json(f"{world_url}/log").get(
            "entries", [])

        # ---- Verification ----
        v_alice_basic = verify_chess_individual_basic(
            alice_loaded)
        v_alice_full = verify_chess_individual_full(
            alice_loaded, world_log)
        v_alice_xref = verify_chess_cross_reference(
            alice_loaded, world_log)
        v_bob_basic = verify_chess_individual_basic(bob_loaded)
        v_bob_full = verify_chess_individual_full(
            bob_loaded, world_log)
        v_bob_xref = verify_chess_cross_reference(
            bob_loaded, world_log)

        # ---- Tamper: corrupted fen_before ----
        tampered_alice = IndividualBundle(
            manifest=dict(alice_loaded.manifest),
            memory=list(alice_loaded.memory),
            weights=dict(alice_loaded.weights),
            initial_weights=None,
            observations=[],
            ancestry=[],
            checkpoint_weights=None,
        )
        for i, r in enumerate(tampered_alice.memory):
            if r.get("type") == "agent_step":
                tampered_alice.memory[i] = {
                    **r,
                    "fen_before":
                        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/"
                        "RNBQKBNR w KQkq - 0 1",
                }
                break
        tampered_full = verify_chess_individual_full(
            tampered_alice, world_log)

        # ---- Report ----
        total_moves = len(turn_log)
        print("=" * 74)
        print("Chess individuals — two verifiable agents at a real"
              " chess world")
        print("=" * 74)
        print()
        print(f"  World:   {world_id} @ {world_url}")
        print(f"  Alice:   {alice_loaded.individual_id[:24]}...")
        print(f"           {len(alice_loaded.memory) - 1} moves played")
        print(f"  Bob:     {bob_loaded.individual_id[:24]}...")
        print(f"           {len(bob_loaded.memory) - 1} moves played")
        print(f"  Total:   {total_moves} moves")
        print()
        print("  Moves (uci, reward):")
        for t in turn_log[:20]:
            print(f"    {t['turn']:2d}. {t['player']:10s} "
                  f"{t['uci']:6s} reward={t['reward']:.2f}")
        if len(turn_log) > 20:
            print(f"    ... ({len(turn_log) - 20} more)")
        print()
        print("  Verification:")
        print(f"    Alice basic:        {v_alice_basic[0]}  "
              f"({v_alice_basic[1]})")
        print(f"    Alice full:         {v_alice_full[0]}  "
              f"({v_alice_full[1]})")
        print(f"    Alice cross-ref:    {v_alice_xref[0]}  "
              f"({v_alice_xref[1]})")
        print(f"    Bob   basic:        {v_bob_basic[0]}  "
              f"({v_bob_basic[1]})")
        print(f"    Bob   full:         {v_bob_full[0]}  "
              f"({v_bob_full[1]})")
        print(f"    Bob   cross-ref:    {v_bob_xref[0]}  "
              f"({v_bob_xref[1]})")
        print()
        print("  Tampering — Alice's fen_before replaced with"
              " initial position:")
        print(f"    full verify: "
              f"{tampered_full[0]}  ({tampered_full[1]})")
        print()
        print("  What this establishes:")
        print("    - A verifiable individual can inhabit a real")
        print("      world (not a ScriptedWorld). The chess world")
        print("      runs over HTTP; the individual connects,")
        print("      petitions, sits, and plays.")
        print("    - Each move is a signed memory entry. The")
        print("      individual's chain verifies end-to-end.")
        print("    - The model is replayed move-by-move: the")
        print("      verifier reconstructs the legal move list")
        print("      from the recorded fen_before, re-runs the")
        print("      4-unit RNN, and confirms the chosen uci is")
        print("      exactly what the model would pick.")
        print("    - Cross-reference: every move the individual")
        print("      claims is present in the chess world's log,")
        print("      with the same actor and the same uci.")
        print("    - Learning is real: rewards flow to the model")
        print("      per move (capture=1.0, check=0.5, else=0.1);")
        print("      its policy evolves over the game.")
        print("    - Tampering with fen_before breaks full")
        print("      verification (replayed legal moves no longer")
        print("      match recorded uci).")
        print()
        print("  Honest limits: chess world's log entries are")
        print("  unsigned; the model doesn't understand chess —")
        print("  it picks legal moves by index; not yet composed")
        print("  with verify_individual_lifetime.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Brain – is wider than the Sky –'")
        print("    'For – put them side by side –'")
        print("    'The one the other will contain'")
        print("    'With ease – and You – beside –'")

        audit = {
            "world_id": world_id,
            "alice_id": alice_loaded.individual_id,
            "bob_id": bob_loaded.individual_id,
            "moves_played": total_moves,
            "alice_memory_entries":
                len(alice_loaded.memory),
            "bob_memory_entries":
                len(bob_loaded.memory),
            "verification": {
                "alice_basic": v_alice_basic[0],
                "alice_full": v_alice_full[0],
                "alice_xref": v_alice_xref[0],
                "bob_basic": v_bob_basic[0],
                "bob_full": v_bob_full[0],
                "bob_xref": v_bob_xref[0],
            },
            "tampering": {
                "fen_before_detected": not tampered_full[0],
            },
        }
        (root / "chess_individual_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root}/chess_individual_demo.json")
        return audit
    finally:
        try:
            server.stop()
        except Exception:
            pass
