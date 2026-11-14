import json
import time
import pytest
import chess
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from individual_bundle import IndividualBundle, _canonical, _hash
from signed_world_log import (
    SignedLogWorld, SignedLogWorldServer,
    verify_signed_entry, signed_entry_hash,
    HAS_CRYPTO,
)
from chess_individual import (
    ChessIndividualSession, pack_chess_individual_bundle,
    verify_chess_individual_basic, verify_chess_individual_full,
    HAS_CHESS,
)
from lifetime import verify_individual_lifetime
from multiverse_c73 import ChessWorld
from coupled_learners import TinyRNN

pytestmark = pytest.mark.skipif(
    not (HAS_CRYPTO and HAS_CHESS),
    reason="requires cryptography and python-chess")


def _kp():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def signed_world():
    world_kp = _kp()
    base = ChessWorld("world:test", "Test Park")
    signed = SignedLogWorld(base, world_kp)
    server = SignedLogWorldServer(signed, port=0)
    server.serve_in_thread()
    time.sleep(0.15)
    url = (f"http://127.0.0.1:"
            f"{server._httpd.server_address[1]}")
    try:
        yield signed, world_kp, url
    finally:
        server.stop()


def _session(url, seat, world_signer, seed=100):
    kp = _kp()
    model = TinyRNN(n_actions=3, hidden=4, n_extra_inputs=0,
                     seed=seed)
    memory: list = []
    s = ChessIndividualSession(
        individual_kp=kp, model=model,
        world_url=url, world_id="world:test",
        world_signer=world_signer,
        memory=memory, seat=seat)
    return s


# -- Signed log --

def test_signed_entry_verifies(signed_world):
    signed, world_kp, url = signed_world
    s = _session(url, "white", signed.world_signer)
    s.enter_and_sit("A")
    from signed_world_log import _sign_entry
    raw = signed.log_since(None)
    entries = signed.signed_log_since(None)
    assert len(entries) == len(raw)
    for e in entries:
        ok, reason = verify_signed_entry(
            e, signed.world_signer)
        assert ok, reason


def test_signed_entry_wrong_signer(signed_world):
    signed, world_kp, url = signed_world
    s = _session(url, "white", signed.world_signer)
    s.enter_and_sit("A")
    entries = signed.signed_log_since(None)
    wrong = _did_from_kp(_kp())
    ok, _ = verify_signed_entry(entries[0], wrong)
    assert not ok


def test_signed_entry_tampered(signed_world):
    signed, _, url = signed_world
    s = _session(url, "white", signed.world_signer)
    s.enter_and_sit("A")
    entries = signed.signed_log_since(None)
    tampered = {
        "body": {**entries[0]["body"],
                 "actor_token": "did:key:" + "00" * 32},
        "sig": entries[0]["sig"],
    }
    ok, _ = verify_signed_entry(tampered, signed.world_signer)
    assert not ok


# -- Chess individual --

def test_chess_individual_full_verifies(signed_world):
    signed, world_kp, url = signed_world
    w = _session(url, "white", signed.world_signer, seed=1)
    b = _session(url, "black", signed.world_signer, seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    for _ in range(10):
        if w.play_turn() is None:
            break
        if b.play_turn() is None:
            break
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=1)
    signed_log = signed.signed_log_since(None)
    ok, reason = verify_chess_individual_full(bundle, signed_log)
    assert ok, reason


def test_chess_full_detects_missing_signed_entry(signed_world):
    signed, world_kp, url = signed_world
    w = _session(url, "white", signed.world_signer, seed=1)
    b = _session(url, "black", signed.world_signer, seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=1)
    ok, _ = verify_chess_individual_full(bundle, [])
    assert not ok


def test_chess_full_detects_tampered_world_entry(signed_world):
    signed, world_kp, url = signed_world
    w = _session(url, "white", signed.world_signer, seed=1)
    b = _session(url, "black", signed.world_signer, seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=1)
    signed_log = signed.signed_log_since(None)
    # Tamper a signed entry's body
    tampered = []
    for e in signed_log:
        if e["body"]["kind"] == "chess.move":
            tampered.append({
                "body": {**e["body"],
                          "data": {**e["body"]["data"],
                                    "uci": "a1a8"}},
                "sig": e["sig"],
            })
        else:
            tampered.append(e)
    ok, _ = verify_chess_individual_full(bundle, tampered)
    assert not ok


# -- Lifetime composition --

def test_lifetime_with_chess_world_logs(signed_world):
    signed, world_kp, url = signed_world
    w = _session(url, "white", signed.world_signer, seed=1)
    b = _session(url, "black", signed.world_signer, seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    for _ in range(6):
        if w.play_turn() is None:
            break
        if b.play_turn() is None:
            break
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=1)
    signed_log = signed.signed_log_since(None)
    bundles = {bundle.individual_id: bundle}
    report = verify_individual_lifetime(
        bundles, bundle.individual_id,
        world_logs={"world:test": signed_log})
    assert report.ok, report.errors
    # tier is "chess"
    assert any(b["tier"] == "chess" for b in report.bundles)


def test_lifetime_chess_basic_without_logs(signed_world):
    signed, _, url = signed_world
    w = _session(url, "white", signed.world_signer, seed=1)
    b = _session(url, "black", signed.world_signer, seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=1)
    bundles = {bundle.individual_id: bundle}
    # No world_logs → basic tier only
    report = verify_individual_lifetime(
        bundles, bundle.individual_id, world_logs=None)
    assert report.ok  # basic passes
    assert any(b["tier"] == "chess-basic"
                for b in report.bundles)


def test_lifetime_chess_fails_without_tamper_detected(signed_world):
    """If logs are missing and it dispatches to basic, tampering
    isn't caught. With logs, it is."""
    signed, _, url = signed_world
    w = _session(url, "white", signed.world_signer, seed=1)
    b = _session(url, "black", signed.world_signer, seed=2)
    w.enter_and_sit("W")
    b.enter_and_sit("B")
    w.play_turn()
    bundle = pack_chess_individual_bundle(
        w, persona="test", name="w", initial_seed=1)
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
    signed_log = signed.signed_log_since(None)
    bundles = {tampered.individual_id: tampered}
    # Without logs: passes basic (tampering only breaks full)
    report_basic = verify_individual_lifetime(
        bundles, tampered.individual_id, world_logs=None)
    assert report_basic.ok
    # With logs: fails at full
    report_full = verify_individual_lifetime(
        bundles, tampered.individual_id,
        world_logs={"world:test": signed_log})
    assert not report_full.ok
