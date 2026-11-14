import json
import time
import pytest
import chess
from individual_bundle import IndividualBundle, _canonical, _hash
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from unified_individual import (
    WorldLogEntry, UnifiedIndividualSession,
    pack_unified_bundle, verify_unified_individual_basic,
    verify_unified_individual_full,
    federated_world_log,
    demo, HAS_CRYPTO, HAS_CHESS,
)
from signed_world_log import (
    SignedLogWorld, SignedLogWorldServer, signed_entry_hash,
)
from chess_individual import ChessIndividualSession
from multiverse_c73 import ChessWorld
from coupled_learners import TinyRNN, SIERPINSKI
from world_agent_coupling import ScriptedWorld

pytestmark = pytest.mark.skipif(
    not (HAS_CRYPTO and HAS_CHESS),
    reason="requires cryptography and python-chess")


def _kp():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def signed_chess():
    world_kp = _kp()
    base = ChessWorld("world:test", "Test")
    signed = SignedLogWorld(base, world_kp)
    server = SignedLogWorldServer(signed, port=0)
    server.serve_in_thread()
    time.sleep(0.15)
    url = (f"http://127.0.0.1:"
            f"{server._httpd.server_address[1]}")
    try:
        yield signed, url, signed.world_signer
    finally:
        server.stop()


def _session(seed=100):
    kp = _kp()
    model = TinyRNN(n_actions=3, hidden=4,
                     n_extra_inputs=0, seed=seed)
    return UnifiedIndividualSession(
        individual_kp=kp, model=model)


def _world_logs(signed, fed_world):
    chess_log = [
        WorldLogEntry(hash=signed_entry_hash(e), payload=e)
        for e in signed.signed_log_since(None)
    ]
    fed_log = federated_world_log(fed_world)
    return {
        "world:test": chess_log,
        fed_world.world_id: fed_log,
    }


# -- Session basics --

def test_federated_only(signed_chess):
    _, url, signer = signed_chess
    s = _session()
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xAAAA, rule=SIERPINSKI)
    s.enter_federated_world(fed, initial_point=(200, 800))
    for _ in range(3):
        assert s.play_federated_turn() is not None
    assert len(s.memory) == 1 + 3


def test_chess_only(signed_chess):
    signed, url, signer = signed_chess
    b_kp = _kp()
    b_model = TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200)
    b = ChessIndividualSession(
        individual_kp=b_kp, model=b_model,
        world_url=url, world_id="world:test",
        world_signer=signer, memory=[], seat="black")
    b.enter_and_sit("B")

    w = _session(seed=100)
    w.enter_chess_world(url, "world:test", signer,
                         "white", "W")
    e = w.play_chess_turn()
    assert e is not None
    assert e["tier"] == "chess"


def test_mixed_memory(signed_chess):
    signed, url, signer = signed_chess
    b = ChessIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200),
        world_url=url, world_id="world:test",
        world_signer=signer, memory=[], seat="black")
    b.enter_and_sit("B")

    w = _session(seed=100)
    w.enter_chess_world(url, "world:test", signer,
                         "white", "W")
    assert w.play_chess_turn() is not None
    b.play_turn()
    assert w.play_chess_turn() is not None

    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xBBBB, rule=SIERPINSKI)
    w.enter_federated_world(fed, initial_point=(200, 800))
    for _ in range(3):
        assert w.play_federated_turn() is not None

    # Memory: 1 chess_entry + 1 chess_step + 1 fed_entry + 3 fed_steps + 1 chess_step from earlier = 
    # Actually: chess_entry, chess_step, chess_step, fed_entry, 3*fed_step
    # = 1 + 2 + 1 + 3 = 7
    tiers = [r.get("tier") for r in w.memory
             if r.get("type") == "agent_step"]
    assert "chess" in tiers
    assert "federated" in tiers


# -- Pack + verify --

def test_pack_and_basic(signed_chess):
    _, url, signer = signed_chess
    w = _session()
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xCCCC, rule=SIERPINSKI)
    w.enter_federated_world(fed, initial_point=(200, 800))
    for _ in range(3):
        w.play_federated_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    ok, reason = verify_unified_individual_basic(bundle)
    assert ok, reason


def test_full_federated_only(signed_chess):
    _, url, signer = signed_chess
    w = _session()
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xCCCC, rule=SIERPINSKI)
    w.enter_federated_world(fed, initial_point=(200, 800))
    for _ in range(5):
        w.play_federated_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    world_logs = {fed.world_id: federated_world_log(fed)}
    ok, reason = verify_unified_individual_full(bundle, world_logs)
    assert ok, reason


def test_full_chess_only(signed_chess):
    signed, url, signer = signed_chess
    b = ChessIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200),
        world_url=url, world_id="world:test",
        world_signer=signer, memory=[], seat="black")
    b.enter_and_sit("B")
    w = _session()
    w.enter_chess_world(url, "world:test", signer,
                         "white", "W")
    for _ in range(2):
        if w.play_chess_turn() is None:
            break
        b.play_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    chess_log = [
        WorldLogEntry(hash=signed_entry_hash(e), payload=e)
        for e in signed.signed_log_since(None)
    ]
    ok, reason = verify_unified_individual_full(
        bundle, {"world:test": chess_log})
    assert ok, reason


def test_full_mixed_tier(signed_chess):
    signed, url, signer = signed_chess
    b = ChessIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200),
        world_url=url, world_id="world:test",
        world_signer=signer, memory=[], seat="black")
    b.enter_and_sit("B")
    w = _session()
    w.enter_chess_world(url, "world:test", signer,
                         "white", "W")
    w.play_chess_turn()
    b.play_turn()
    w.play_chess_turn()
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xBBBB, rule=SIERPINSKI)
    w.enter_federated_world(fed, initial_point=(200, 800))
    for _ in range(3):
        w.play_federated_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    world_logs = _world_logs(signed, fed)
    ok, reason = verify_unified_individual_full(bundle, world_logs)
    assert ok, reason


# -- Tampering --

def test_tampered_chess_fen_detected(signed_chess):
    signed, url, signer = signed_chess
    b = ChessIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200),
        world_url=url, world_id="world:test",
        world_signer=signer, memory=[], seat="black")
    b.enter_and_sit("B")
    w = _session()
    w.enter_chess_world(url, "world:test", signer,
                         "white", "W")
    w.play_chess_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    chess_log = [
        WorldLogEntry(hash=signed_entry_hash(e), payload=e)
        for e in signed.signed_log_since(None)
    ]
    # Tamper
    tampered = IndividualBundle(
        manifest=dict(bundle.manifest),
        memory=list(bundle.memory),
        weights=dict(bundle.weights),
        initial_weights=None, observations=[],
        ancestry=[], checkpoint_weights=None,
    )
    for i, r in enumerate(tampered.memory):
        if r.get("tier") == "chess":
            tampered.memory[i] = {
                **r,
                "fen_before":
                    "8/8/8/8/8/8/8/K6k w - - 0 1",
            }
            break
    ok, _ = verify_unified_individual_full(
        tampered, {"world:test": chess_log})
    assert not ok


def test_tampered_federated_point_detected(signed_chess):
    _, url, signer = signed_chess
    w = _session()
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xCCCC, rule=SIERPINSKI)
    w.enter_federated_world(fed, initial_point=(200, 800))
    for _ in range(3):
        w.play_federated_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    tampered = IndividualBundle(
        manifest=dict(bundle.manifest),
        memory=list(bundle.memory),
        weights=dict(bundle.weights),
        initial_weights=None, observations=[],
        ancestry=[], checkpoint_weights=None,
    )
    for i, r in enumerate(tampered.memory):
        if r.get("tier") == "federated":
            tampered.memory[i] = {
                **r, "to_point": [999, 999]}
            break
    ok, _ = verify_unified_individual_full(
        tampered, {fed.world_id: federated_world_log(fed)})
    assert not ok


def test_missing_chess_log_detected(signed_chess):
    signed, url, signer = signed_chess
    b = ChessIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200),
        world_url=url, world_id="world:test",
        world_signer=signer, memory=[], seat="black")
    b.enter_and_sit("B")
    w = _session()
    w.enter_chess_world(url, "world:test", signer,
                         "white", "W")
    w.play_chess_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    # Empty world logs
    ok, _ = verify_unified_individual_full(bundle, {})
    assert not ok


# -- Save/load --

def test_save_load(signed_chess, tmp_path):
    signed, url, signer = signed_chess
    w = _session()
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xCCCC, rule=SIERPINSKI)
    w.enter_federated_world(fed, initial_point=(200, 800))
    for _ in range(3):
        w.play_federated_turn()
    bundle = pack_unified_bundle(
        w, persona="test", name="w", initial_seed=100)
    bundle.save(tmp_path / "b")
    loaded = IndividualBundle.load(tmp_path / "b")
    ok, reason = verify_unified_individual_full(
        loaded, {fed.world_id: federated_world_log(fed)})
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["basic"] is True
    assert audit["verification"]["full"] is True
    assert audit["chess_moves_played"] >= 1
    assert audit["federated_steps"] == 5
    assert audit["tampering"]["chess_fen_detected"] is True
    assert audit["tampering"]["federated_point_detected"] is True
    assert audit["tampering"]["missing_chess_log_detected"] is True
    assert (tmp_path / "unified_individual" /
            "unified_individual_demo.json").exists()
