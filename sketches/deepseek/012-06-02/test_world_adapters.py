import json
import time
import pytest
import chess
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from individual_bundle import IndividualBundle, _hash
from world_adapters import (
    WorldAdapter, FederatedAdapter, ChessAdapter,
    GrowingCanvasAdapter, DEFAULT_ADAPTERS,
    HAS_CHESS, HAS_CRYPTO,
)
from unified_individual import (
    UnifiedIndividualSession, pack_unified_bundle,
    verify_unified_individual_with_adapters,
)
from coupled_learners import TinyRNN, SIERPINSKI
from world_agent_coupling import ScriptedWorld
from multiverse_c73 import ChessWorld
from multiverse_c81 import GrowingWorld
from signed_world_log import (
    SignedLogWorld, SignedLogWorldServer,
)

pytestmark = pytest.mark.skipif(
    not (HAS_CRYPTO and HAS_CHESS),
    reason="requires cryptography and python-chess")


def _kp():
    return Ed25519PrivateKey.generate()


def test_adapter_defaults():
    assert set(DEFAULT_ADAPTERS.keys()) == {
        "federated", "chess", "canvas"}
    for adapter in DEFAULT_ADAPTERS.values():
        assert adapter.n_actions() == 3
        assert adapter.state_dim() == 4


def test_federated_adapter_roundtrip():
    world = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xAAAA, rule=SIERPINSKI)
    adapter = FederatedAdapter()
    handle = adapter.open({"world": world})
    entry = adapter.enter(handle, "did:key:" + "00" * 32,
                            _kp(), {"initial_point": (200, 800)})
    assert entry["initial_point"] == [200, 800]


def test_canvas_adapter_roundtrip():
    world = GrowingWorld("world:c", "Canvas", _kp())
    adapter = GrowingCanvasAdapter()
    handle = adapter.open({"world": world})
    entry = adapter.enter(handle, "did:key:" + "00" * 32,
                            _kp(), {"display_name": "bot"})
    assert entry["display_name"] == "bot"


@pytest.fixture
def chess_setup():
    world_kp = _kp()
    base = ChessWorld("world:test", "Test")
    signed = SignedLogWorld(base, world_kp)
    server = SignedLogWorldServer(signed, port=0)
    server.serve_in_thread()
    time.sleep(0.15)
    url = (f"http://127.0.0.1:"
            f"{server._httpd.server_address[1]}")
    try:
        yield signed, url
    finally:
        server.stop()


def test_chess_adapter_enter(chess_setup):
    signed, url = chess_setup
    adapter = ChessAdapter()
    handle = adapter.open({"world_url": url})
    entry = adapter.enter(
        handle, "did:key:" + "00" * 32, _kp(),
        {"seat": "white", "display_name": "W"})
    assert entry["seat"] == "white"


def test_unified_session_three_worlds(chess_setup):
    signed, url = chess_setup
    from chess_individual import ChessIndividualSession

    # Black
    b = ChessIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200),
        world_url=url, world_id="world:test",
        world_signer=signed.world_signer, memory=[], seat="black")
    b.enter_and_sit("B")

    # Federated
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xBBBB, rule=SIERPINSKI)
    # Canvas
    canvas = GrowingWorld("world:canvas", "Canvas", _kp())

    # Unified
    session = UnifiedIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=100))

    # Chess
    session.enter_world_via_adapter(ChessAdapter(), {
        "world_id": "world:test", "world_url": url,
        "world_signer": signed.world_signer,
        "seat": "white", "display_name": "W"})
    for _ in range(2):
        if session.step_via_adapter() is None:
            break
        b.play_turn()

    # Federated
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": fed.world_id, "world": fed,
        "world_signer": fed.world_id,
        "initial_point": (200, 800)})
    for _ in range(3):
        session.step_via_adapter()

    # Canvas
    session.enter_world_via_adapter(GrowingCanvasAdapter(), {
        "world_id": "world:canvas", "world": canvas,
        "world_signer": canvas.curator_public_key,
        "display_name": "W"})
    for _ in range(3):
        session.step_via_adapter()

    # Pack + verify
    bundle = pack_unified_bundle(
        session, persona="test", name="W",
        initial_seed=100)
    world_logs = {
        "world:test": signed.signed_log_since(None),
        fed.world_id: [
            {"body": r.body(), "sig": r.sig,
             "record_hash": r.record_hash()}
            for r in fed.records],
        "world:canvas": [
            {"event_hash": e.event_hash(),
             "event_dict": e.to_dict()}
            for e in canvas.events()],
    }
    ok, reason = verify_unified_individual_with_adapters(
        bundle, world_logs)
    assert ok, reason


def test_tampered_canvas_coords(chess_setup):
    signed, url = chess_setup
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xBBBB, rule=SIERPINSKI)
    canvas = GrowingWorld("world:canvas", "Canvas", _kp())

    session = UnifiedIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=100))

    session.enter_world_via_adapter(GrowingCanvasAdapter(), {
        "world_id": "world:canvas", "world": canvas,
        "world_signer": canvas.curator_public_key,
        "display_name": "W"})
    for _ in range(3):
        session.step_via_adapter()

    bundle = pack_unified_bundle(
        session, persona="test", name="W", initial_seed=100)
    world_logs = {
        "world:canvas": [
            {"event_hash": e.event_hash(),
             "event_dict": e.to_dict()}
            for e in canvas.events()],
    }

    # Tamper
    tampered = IndividualBundle(
        manifest=dict(bundle.manifest),
        memory=list(bundle.memory),
        weights=dict(bundle.weights),
        initial_weights=None, observations=[],
        ancestry=[], checkpoint_weights=None,
    )
    for i, r in enumerate(tampered.memory):
        if r.get("tier") == "canvas":
            tampered.memory[i] = {**r, "x": 999, "y": 999}
            break
    ok, _ = verify_unified_individual_with_adapters(
        tampered, world_logs)
    assert not ok


def test_demo(tmp_path):
    from world_adapters import demo  # imported lazily if defined
    # (If demo lives in unified_individual or world_adapters)
    pass
