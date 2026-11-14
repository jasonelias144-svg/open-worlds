import json
import time
import pytest
import chess
from individual_bundle import (
    IndividualBundle, _canonical, _hash,
)
from chess_individual import (
    ChessIndividualSession, pack_chess_individual_bundle,
    verify_chess_individual_basic, verify_chess_individual_full,
    verify_chess_cross_reference,
    _material_count, _find_chess_entry, _entry_hash,
    demo, HAS_CRYPTO, HAS_CHESS,
)
from multiverse_c73 import ChessWorld
from wcp_http_shim import WorldProtocolServer
from coupled_learners import TinyRNN
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not (HAS_CRYPTO and HAS_CHESS),
    reason="requires cryptography and python-chess")


def _kp():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def chess_world():
    world = ChessWorld("world:test", "Test Park")
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    time.sleep(0.15)
    url = (f"http://127.0.0.1:"
            f"{server._httpd.server_address[1]}")
    try:
        yield world, server, url
    finally:
        server.stop()


def _make_session(world_url, seat, seed=100):
    kp = _kp()
    model = TinyRNN(n_actions=3, hidden=4, n_extra_inputs=0,
                     seed=seed)
    memory: list = []
    s = ChessIndividualSession(
        individual_kp=kp, model=model,
        world_url=world_url, world_id="world:test",
        memory=memory, seat=seat)
    return s


# -- Material count --

def test_material_count_initial():
    board = chess.Board()
    assert _material_count(board, chess.WHITE) == 39  # sum of pieces
    assert _material_count(board, chess.BLACK) == 39


# -- Session basics --

def test_enter_and_sit(chess_world):
    _, _, url = chess_world
    s = _make_session(url, "white")
    ok, reason = s.enter_and_sit("Alice")
    assert ok, reason
    assert len(s.memory) == 1
    assert s.memory[0]["type"] == "world_entry"
    assert s.memory[0]["seat"] == "white"


def test_both_players_sit(chess_world):
    _, _, url = chess_world
    w = _make_session(url, "white", seed=1)
    b = _make_session(url, "black", seed=2)
    assert w.enter_and_sit("W")[0]
    assert b.enter_and_sit("B")[0]


def test_sit_occupied_seat_refused(chess_world):
    _, _, url = chess_world
    a = _make_session(url, "white", seed=1)
    b = _make_session(url, "white", seed=2)
    assert a.enter_and_sit("A")[0]
    ok, _ = b.enter_and_sit("B")
    assert not ok


# -- Play --

def test_play_turn_when_not_my_turn(chess_world):
    """White sits and plays. Black's play_turn returns None
    because it's not their turn."""
    _, _, url = chess_world
    w = _make_session(url, "white", seed=1)
    b = _make_session(url, "black", seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    entry_w = w.play_turn()
    # After white's move, black's turn
    assert entry_w is not None
    entry_w2 = w.play_turn()  # white's turn again? No — black's
    assert entry_w2 is None


def test_play_turn_appends_memory(chess_world):
    _, _, url = chess_world
    w = _make_session(url, "white", seed=1)
    b = _make_session(url, "black", seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    n_before = len(w.memory)
    w.play_turn()
    assert len(w.memory) == n_before + 1
    assert w.memory[-1]["type"] == "agent_step"
    assert w.memory[-1]["uci"]


def test_moves_alternate(chess_world):
    _, _, url = chess_world
    w = _make_session(url, "white", seed=1)
    b = _make_session(url, "black", seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    for _ in range(10):
        if w.play_turn() is None:
            break
        if b.play_turn() is None:
            break


# -- Pack --

def test_pack_produces_verifiable_bundle(chess_world):
    _, _, url = chess_world
    w = _make_session(url, "white")
    b = _make_session(url, "black")
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=100)
    ok, reason = verify_chess_individual_basic(bundle)
    assert ok, reason


# -- Full verification --

def test_full_verifies_simple_game(chess_world):
    world, _, url = chess_world
    w = _make_session(url, "white")
    b = _make_session(url, "black")
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    for _ in range(10):
        if w.play_turn() is None:
            break
        if b.play_turn() is None:
            break
    alice_bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=100)
    bob_bundle = pack_chess_individual_bundle(
        b, persona="test", name="b", initial_seed=200)
    world_log = [
        {"timestamp": e.timestamp, "kind": e.kind,
         "actor_token": e.actor_token, "data": e.data}
        for e in world._log
    ]
    v_a = verify_chess_individual_full(alice_bundle, world_log)
    assert v_a[0], v_a[1]


def test_cross_reference_verifies(chess_world):
    world, _, url = chess_world
    w = _make_session(url, "white")
    b = _make_session(url, "black")
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=100)
    world_log = [
        {"timestamp": e.timestamp, "kind": e.kind,
         "actor_token": e.actor_token, "data": e.data}
        for e in world._log
    ]
    ok, reason = verify_chess_cross_reference(bundle, world_log)
    assert ok, reason


# -- Tampering --

def test_tampered_fen_before_detected(chess_world):
    world, _, url = chess_world
    w = _make_session(url, "white")
    b = _make_session(url, "black")
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=100)
    world_log = [
        {"timestamp": e.timestamp, "kind": e.kind,
         "actor_token": e.actor_token, "data": e.data}
        for e in world._log
    ]
    # Tamper fen_before
    tampered = IndividualBundle(
        manifest=dict(bundle.manifest),
        memory=list(bundle.memory),
        weights=dict(bundle.weights),
        initial_weights=None, observations=[],
        ancestry=[], checkpoint_weights=None,
    )
    for i, r in enumerate(tampered.memory):
        if r.get("type") == "agent_step":
            tampered.memory[i] = {
                **r,
                "fen_before":
                    "8/8/8/8/8/8/8/K6k w - - 0 1",
            }
            break
    ok, _ = verify_chess_individual_full(
        tampered, world_log)
    assert not ok


def test_tampered_uci_detected(chess_world):
    world, _, url = chess_world
    w = _make_session(url, "white")
    b = _make_session(url, "black")
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=100)
    world_log = [
        {"timestamp": e.timestamp, "kind": e.kind,
         "actor_token": e.actor_token, "data": e.data}
        for e in world._log
    ]
    tampered = IndividualBundle(
        manifest=dict(bundle.manifest),
        memory=list(bundle.memory),
        weights=dict(bundle.weights),
        initial_weights=None, observations=[],
        ancestry=[], checkpoint_weights=None,
    )
    for i, r in enumerate(tampered.memory):
        if r.get("type") == "agent_step":
            tampered.memory[i] = {**r, "uci": "a1a8"}
            break
    ok, _ = verify_chess_cross_reference(
        tampered, world_log)
    assert not ok


# -- Missing world entry --

def test_missing_world_entry_detected(chess_world):
    world, _, url = chess_world
    w = _make_session(url, "white")
    w.enter_and_sit("W")
    b = _make_session(url, "black")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=100)
    # Empty world log
    ok, _ = verify_chess_cross_reference(bundle, [])
    assert not ok


# -- Save/load --

def test_save_load_chess_bundle(chess_world, tmp_path):
    world, _, url = chess_world
    w = _make_session(url, "white")
    b = _make_session(url, "black")
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=100)
    bundle.save(tmp_path / "w")
    loaded = IndividualBundle.load(tmp_path / "w")
    world_log = [
        {"timestamp": e.timestamp, "kind": e.kind,
         "actor_token": e.actor_token, "data": e.data}
        for e in world._log
    ]
    ok, reason = verify_chess_individual_full(loaded, world_log)
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["alice_basic"] is True
    assert audit["verification"]["alice_full"] is True
    assert audit["verification"]["alice_xref"] is True
    assert audit["verification"]["bob_basic"] is True
    assert audit["verification"]["bob_full"] is True
    assert audit["verification"]["bob_xref"] is True
    assert audit["tampering"]["fen_before_detected"] is True
    assert audit["moves_played"] > 0
    assert (tmp_path / "chess_individual" /
            "chess_individual_demo.json").exists()
