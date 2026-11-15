import json
import time
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from individual_bundle import _canonical, _hash, _did_from_kp
from map_governance import (
    MapWorldKey, sign_world_key, verify_world_key,
    PinAddedRequest, PinRemovedRequest,
    sign_pin_added_request, sign_pin_removed_request,
    verify_request_signature, verify_request_authorization,
    tier_covers, TIERS,
)
from map_world import (
    MapRegistry, WorldPin, MultiversalMap,
    _get_json, _post_json,
)
from map_governance import HAS_CRYPTO


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _empty_map():
    kp = _kp()
    return MultiversalMap("map:m", "M", kp), kp


def _pin(wid, url="u", signer=None, cluster="X"):
    return WorldPin(
        wid, url,
        signer or ("did:key:" + "00" * 32),
        cluster=cluster)


# -- World key --

def test_world_key_sign_verify():
    kp = _kp()
    from individual_bundle import _did_from_kp
    map_id = _did_from_kp(kp)
    wk = sign_world_key(kp, map_id, "did:key:" + "aa" * 32,
                          "edit")
    ok, reason = verify_world_key(wk, map_id)
    assert ok, reason


def test_world_key_wrong_issuer():
    kp = _kp()
    from individual_bundle import _did_from_kp
    map_id = _did_from_kp(kp)
    wk = sign_world_key(kp, map_id, "did:key:" + "aa" * 32,
                          "edit")
    wrong = "did:key:" + "bb" * 32
    ok, _ = verify_world_key(wk, wrong)
    assert not ok


def test_world_key_rejects_bad_tier():
    kp = _kp()
    from individual_bundle import _did_from_kp
    map_id = _did_from_kp(kp)
    with pytest.raises(ValueError):
        sign_world_key(kp, map_id, "did:key:" + "aa" * 32,
                         "admin")


def test_tier_covers():
    assert tier_covers("edit", "edit")
    assert tier_covers("edit", "observe")
    assert not tier_covers("observe", "edit")


# -- Keeper acts --

def test_keeper_add_logs():
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    assert len(mv._log) == 1
    assert mv._log[0]["kind"] == "pin_added"
    assert mv._log[0]["world_key"] is None
    assert mv._registry.get_pin("world:a") is not None


def test_keeper_add_duplicate_raises():
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    with pytest.raises(ValueError):
        mv.add(_pin("world:a"))


def test_keeper_remove():
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    mv.remove("world:a")
    assert mv._registry.get_pin("world:a") is None


def test_keeper_remove_unknown_raises():
    mv, _ = _empty_map()
    with pytest.raises(ValueError):
        mv.remove("world:nonexistent")


# -- External requests --

def test_edit_key_adds_pin():
    mv, kp = _empty_map()
    actor_kp = _kp()
    actor_id = _did_from_kp(actor_kp)
    wk = mv.issue_world_key(actor_id, "edit")
    req = sign_pin_added_request(actor_kp, wk, {
        "world_id": "world:new",
        "url": "http://x",
        "world_signer": "did:key:" + "cc" * 32,
        "description": "d", "cluster": "c", "kind": "world",
    })
    ok, reason = mv.pin_added_request(req)
    assert ok, reason
    assert mv._registry.get_pin("world:new") is not None
    # Check the log entry has the world_key
    entry = [e for e in mv._log if e["kind"] == "pin_added"][-1]
    assert entry["world_key"] is not None
    assert entry["actor"] == actor_id


def test_observe_key_cannot_add():
    mv, _ = _empty_map()
    actor_kp = _kp()
    actor_id = _did_from_kp(actor_kp)
    wk = mv.issue_world_key(actor_id, "observe")
    req = sign_pin_added_request(actor_kp, wk, {
        "world_id": "world:new",
        "url": "http://x",
        "world_signer": "did:key:" + "cc" * 32,
        "description": "", "cluster": "", "kind": "world"})
    ok, reason = mv.pin_added_request(req)
    assert not ok
    assert "tier" in reason.lower()
    assert mv._registry.get_pin("world:new") is None


def test_observe_key_cannot_remove():
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    actor_kp = _kp()
    actor_id = _did_from_kp(actor_kp)
    wk = mv.issue_world_key(actor_id, "observe")
    req = sign_pin_removed_request(actor_kp, wk, "world:a")
    ok, _ = mv.pin_removed_request(req)
    assert not ok
    assert mv._registry.get_pin("world:a") is not None


def test_bad_request_sig():
    mv, _ = _empty_map()
    actor_kp = _kp()
    actor_id = _did_from_kp(actor_kp)
    wk = mv.issue_world_key(actor_id, "edit")
    req = sign_pin_added_request(actor_kp, wk, {
        "world_id": "world:new", "url": "http://x",
        "world_signer": "did:key:" + "cc" * 32,
        "description": "", "cluster": "", "kind": "world"})
    tampered = PinAddedRequest(
        actor_id=req.actor_id, pin={"world_id": "different"},
        world_key=req.world_key, ts=req.ts, sig=req.sig)
    ok, reason = mv.pin_added_request(tampered)
    assert not ok
    assert "sig" in reason.lower()


def test_expired_world_key():
    mv, _ = _empty_map()
    actor_kp = _kp()
    actor_id = _did_from_kp(actor_kp)
    wk = mv.issue_world_key(
        actor_id, "edit",
        valid_until="2020-01-01T00:00:00+00:00")
    req = sign_pin_added_request(actor_kp, wk, {
        "world_id": "world:new", "url": "http://x",
        "world_signer": "did:key:" + "cc" * 32,
        "description": "", "cluster": "", "kind": "world"})
    ok, reason = mv.pin_added_request(req)
    assert not ok
    assert "expired" in reason.lower()


# -- Log verification --

def test_verify_log_clean():
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    mv.add(_pin("world:b"))
    mv.remove("world:a")
    ok, reason = mv.verify_log()
    assert ok, reason


def test_verify_log_detects_tamper():
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    # Tamper an entry
    mv._log[0] = {**mv._log[0],
                   "pin": {**mv._log[0]["pin"],
                           "url": "http://evil"}}
    ok, _ = mv.verify_log()
    assert not ok


def test_verify_log_detects_duplicate_add():
    """If the log has two pin_added for the same world, reject."""
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    # Force a duplicate
    mv._log.append(dict(mv._log[0]))
    ok, _ = mv.verify_log()
    assert not ok


# -- Historical replay --

def test_registry_at():
    mv, _ = _empty_map()
    mv.add(_pin("world:a"))
    mv.add(_pin("world:b"))
    mv.remove("world:a")
    mv.add(_pin("world:c"))
    # After 0: empty
    r0 = mv.registry_at(0)
    assert len(r0.all_pins()) == 0
    # After 1: {a}
    r1 = mv.registry_at(1)
    assert {p.world_id for p in r1.all_pins()} == {"world:a"}
    # After 2: {a, b}
    r2 = mv.registry_at(2)
    assert {p.world_id for p in r2.all_pins()} == \
        {"world:a", "world:b"}
    # After 3: {b}
    r3 = mv.registry_at(3)
    assert {p.world_id for p in r3.all_pins()} == {"world:b"}
    # After 4: {b, c}
    r4 = mv.registry_at(4)
    assert {p.world_id for p in r4.all_pins()} == \
        {"world:b", "world:c"}


# -- HTTP endpoints --

def test_registry_endpoint():
    from signed_world_log import SignedLogWorld
    from lobby_server import LobbyServer
    from map_world import MapServer
    from multiverse_c74 import ChatWorld

    map_kp = _kp()
    mv = MultiversalMap("map:m", "M", map_kp)
    mv.add(_pin("world:a", url="http://a"))
    signed = SignedLogWorld(mv, map_kp)
    srv = MapServer(signed, map_kp, mv, port=0)
    srv.serve_in_thread()
    time.sleep(0.15)
    try:
        url = (f"http://127.0.0.1:"
                f"{srv._httpd.server_address[1]}")
        reg = _get_json(f"{url}/registry")
        assert len(reg["pins"]) == 1
        assert reg["pins"][0]["world_id"] == "world:a"
        hist = _get_json(f"{url}/registry_at/0")
        assert hist["pins"] == []
    finally:
        srv.stop()


# -- Backward compat --

def test_backward_compat_petition():
    from signed_world_log import SignedLogWorld
    from lobby_server import LobbyServer
    from map_world import MapServer
    from multiverse_c74 import ChatWorld
    from multiverse_c3 import Petition, Route

    # Build a real world to route to
    w_kp = _kp()
    w_signed = SignedLogWorld(
        ChatWorld("world:x", "X"), w_kp)
    w_srv = LobbyServer(w_signed, w_kp, port=0)
    w_srv.serve_in_thread()
    time.sleep(0.15)
    w_url = (f"http://127.0.0.1:"
              f"{w_srv._httpd.server_address[1]}")

    try:
        map_kp = _kp()
        mv = MultiversalMap("map:m", "M", map_kp)
        mv.add(_pin(
            "world:x", url=w_url,
            signer=w_signed.world_signer))
        r = mv.petition(Petition(
            petitioner_token="v",
            petitioner_name="V",
            passport_admissions=(),
            message="", target="world:x"))
        assert isinstance(r, Route)
    finally:
        w_srv.stop()


# -- Demo --

def test_demo(tmp_path):
    from map_governance import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["requests"]["edit_pin_added_garden"] is True
    assert audit["requests"]["observe_pin_added_park"] is False
    assert audit["requests"]["observe_pin_removed_chess"] is False
    assert audit["requests"]["edit_pin_removed_garden"] is True
    assert audit["log_verified"] is True
    assert audit["tampering"]["url_altered_detected"] is True
    assert audit["historical"]["at_0"] == []
    assert set(audit["historical"]["at_2"]) == \
        {"world:chess", "world:canvas"}
    # After edit-key add, three pins in history
    assert len(audit["historical"]["at_4"]) == 3
    # Current: keeper's two minus canvas (removed) = chess only
    assert audit["current_registry"] == ["world:chess"]
    assert (tmp_path / "map_governance" /
            "map_governance_demo.json").exists()
