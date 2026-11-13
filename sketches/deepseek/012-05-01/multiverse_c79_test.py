import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c74 import RoomEntry
from multiverse_c79 import (
    LIFECYCLE_EVENT_TYPES,
    RoomLifecycleEvent, sign_lifecycle_event,
    verify_lifecycle_event,
    TreeSubscription, sign_tree_subscription,
    verify_tree_subscription,
    RelayHop, TreeEventNotification,
    verify_tree_event_notification,
    build_direct_notification,
    verify_lifecycle_chain,
    reconstruct_rooms_from_events, reconstruct_at,
    LivingRoomWorld, LivingRoomWorldServer,
    TreeSubscriber, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# ---------- RoomLifecycleEvent ----------

def test_event_sign_verify():
    print("=== RoomLifecycleEvent: sign/verify ===")
    kp = KeyPair.generate()
    ev = sign_lifecycle_event(
        event_type="registered",
        parent_id="world:games",
        signer_id="world:games",
        signer_kp=kp,
        room_id="world:chess",
        room_url="http://chess.example",
        room_public_key="aa" * 32,
        room_name="Chess")
    assert verify_lifecycle_event(
        ev, kp.public_key_hex())


def test_event_wrong_key_rejected():
    print("=== RoomLifecycleEvent: wrong key ===")
    kp = KeyPair.generate()
    ev = sign_lifecycle_event(
        "registered", "world:games", "world:games", kp,
        "world:chess", room_url="http://x",
        room_public_key="aa" * 32, room_name="C")
    wrong = KeyPair.generate()
    assert not verify_lifecycle_event(
        ev, wrong.public_key_hex())


def test_event_rejects_bad_type():
    print("=== RoomLifecycleEvent: bad type rejected ===")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        sign_lifecycle_event(
            "bogus", "world:g", "world:g", kp,
            "world:c")


def test_event_json_roundtrip():
    print("=== RoomLifecycleEvent: JSON roundtrip ===")
    kp = KeyPair.generate()
    ev = sign_lifecycle_event(
        "registered", "world:g", "world:g", kp,
        "world:c", room_url="http://x",
        room_public_key="aa" * 32, room_name="C")
    ev2 = RoomLifecycleEvent.from_dict(ev.to_dict())
    assert ev2.event_hash() == ev.event_hash()


# ---------- Chain verification ----------

def _chain(kp, room="world:c"):
    """Return a 3-event chain: registered, updated, retired."""
    e1 = sign_lifecycle_event(
        "registered", "world:g", "world:g", kp,
        room, room_url="http://a",
        room_public_key="aa" * 32, room_name="A",
        prior_event_hash=None)
    e2 = sign_lifecycle_event(
        "updated", "world:g", "world:g", kp,
        room, room_url="http://b",
        room_public_key="aa" * 32, room_name="B",
        prior_event_hash=e1.event_hash())
    e3 = sign_lifecycle_event(
        "retired", "world:g", "world:g", kp,
        room, prior_event_hash=e2.event_hash())
    return [e1, e2, e3]


def test_chain_happy():
    print("=== verify_lifecycle_chain: happy ===")
    kp = KeyPair.generate()
    v = verify_lifecycle_chain(
        _chain(kp), kp.public_key_hex())
    assert v.valid


def test_chain_broken_link():
    print("=== verify_lifecycle_chain: broken link ===")
    kp = KeyPair.generate()
    chain = _chain(kp)
    # Tamper e2's prior_event_hash to point nowhere
    e2 = sign_lifecycle_event(
        "updated", "world:g", "world:g", kp,
        "world:c", room_url="http://b",
        room_public_key="aa" * 32, room_name="B",
        prior_event_hash="00" * 32)
    v = verify_lifecycle_chain(
        [chain[0], e2, chain[2]], kp.public_key_hex())
    assert not v.valid


def test_chain_fork_detected():
    print("=== verify_lifecycle_chain: fork detected ===")
    kp = KeyPair.generate()
    e1 = sign_lifecycle_event(
        "registered", "world:g", "world:g", kp,
        "world:c", room_url="http://a",
        room_public_key="aa" * 32, room_name="A")
    e2a = sign_lifecycle_event(
        "updated", "world:g", "world:g", kp,
        "world:c", room_url="http://b1",
        room_public_key="aa" * 32, room_name="B1",
        prior_event_hash=e1.event_hash())
    e2b = sign_lifecycle_event(
        "updated", "world:g", "world:g", kp,
        "world:c", room_url="http://b2",
        room_public_key="aa" * 32, room_name="B2",
        prior_event_hash=e1.event_hash())
    v = verify_lifecycle_chain(
        [e1, e2a, e2b], kp.public_key_hex())
    assert not v.valid
    assert v.forks


# ---------- Reconstruction ----------

def test_reconstruct_current():
    print("=== reconstruct_rooms_from_events ===")
    kp = KeyPair.generate()
    state = reconstruct_rooms_from_events(_chain(kp))
    # After register+update+retire, room is gone
    assert "world:c" not in state


def test_reconstruct_at_update():
    print("=== reconstruct_at: mid-chain ===")
    kp = KeyPair.generate()
    chain = _chain(kp)
    mid = reconstruct_at(
        chain, chain[1].event_hash())
    assert "world:c" in mid
    assert mid["world:c"]["name"] == "B"
    assert mid["world:c"]["base_url"] == "http://b"


# ---------- LivingRoomWorld ----------

def test_living_world_register_fires_event():
    print("=== LivingRoomWorld: register fires event ===")
    kp = KeyPair.generate()
    parent = LivingRoomWorld("world:g", "G", kp)
    ev = parent.register_room(RoomEntry(
        "world:g", "world:c", "http://x",
        "aa" * 32, "C"))
    assert isinstance(ev, RoomLifecycleEvent)
    assert ev.event_type == "registered"
    assert verify_lifecycle_event(ev, kp.public_key_hex())


def test_living_world_unregister_fires_event():
    print("=== LivingRoomWorld: unregister fires event ===")
    kp = KeyPair.generate()
    parent = LivingRoomWorld("world:g", "G", kp)
    parent.register_room(RoomEntry(
        "world:g", "world:c", "http://x",
        "aa" * 32, "C"))
    ev = parent.unregister_room("world:c")
    assert ev.event_type == "retired"


def test_living_world_duplicate_register_raises():
    print("=== LivingRoomWorld: duplicate register raises ===")
    kp = KeyPair.generate()
    parent = LivingRoomWorld("world:g", "G", kp)
    parent.register_room(RoomEntry(
        "world:g", "world:c", "http://x",
        "aa" * 32, "C"))
    with pytest.raises(ValueError):
        parent.register_room(RoomEntry(
            "world:g", "world:c", "http://y",
            "bb" * 32, "C2"))


def test_living_world_list_rooms_reconstructs():
    print("=== LivingRoomWorld: list_rooms from chain ===")
    kp = KeyPair.generate()
    parent = LivingRoomWorld("world:g", "G", kp)
    parent.register_room(RoomEntry(
        "world:g", "world:a", "http://a",
        "aa" * 32, "A"))
    parent.register_room(RoomEntry(
        "world:g", "world:b", "http://b",
        "bb" * 32, "B"))
    parent.unregister_room("world:a")
    rooms = parent.list_rooms()
    assert len(rooms) == 1
    assert rooms[0]["room_id"] == "world:b"


def test_living_world_events_since():
    print("=== LivingRoomWorld: events_since ===")
    kp = KeyPair.generate()
    parent = LivingRoomWorld("world:g", "G", kp)
    ev1 = parent.register_room(RoomEntry(
        "world:g", "world:a", "http://a",
        "aa" * 32, "A"))
    ev2 = parent.register_room(RoomEntry(
        "world:g", "world:b", "http://b",
        "bb" * 32, "B"))
    since_ev1 = parent.events_since(ev1.event_hash())
    assert len(since_ev1) == 1
    assert since_ev1[0].event_hash() == ev2.event_hash()


# ---------- Subscription + Notification ----------

def _subscriber_and_world():
    kp = KeyPair.generate()
    sub_kp = KeyPair.generate()
    sub = TreeSubscriber("sub:o", sub_kp, port=0)
    sub.start()
    time.sleep(0.1)
    parent = LivingRoomWorld("world:g", "G", kp)
    parent_server = LivingRoomWorldServer(parent, port=0)
    parent_server.serve_in_thread()
    time.sleep(0.1)
    parent_url = (
        f"http://127.0.0.1:"
        f"{parent_server._httpd.server_address[1]}")
    return (sub, parent, parent_server, parent_url, kp)


def test_subscribe_works():
    print("=== TreeSubscriber: subscribe ===")
    sub, parent, srv, url, kp = _subscriber_and_world()
    try:
        ok, reason = sub.subscribe_to(
            "world:g", url, kp.public_key_hex(), depth=1)
        assert ok, reason
        assert len(parent.subscribers()) == 1
    finally:
        sub.stop()
        srv.stop()


def test_live_events_delivered():
    print("=== Live events delivered to subscriber ===")
    sub, parent, srv, url, kp = _subscriber_and_world()
    try:
        sub.subscribe_to(
            "world:g", url, kp.public_key_hex(), depth=1)
        parent.register_room(RoomEntry(
            "world:g", "world:a", "http://a",
            "aa" * 32, "A"))
        time.sleep(0.1)
        assert len(sub.received_events()) == 1
        assert len(sub.notifications()) == 1
    finally:
        sub.stop()
        srv.stop()


def test_notification_verified():
    print("=== Notification: chain verifies ===")
    sub, parent, srv, url, kp = _subscriber_and_world()
    try:
        sub.subscribe_to(
            "world:g", url, kp.public_key_hex())
        parent.register_room(RoomEntry(
            "world:g", "world:a", "http://a",
            "aa" * 32, "A"))
        time.sleep(0.1)
        n = sub.notifications()[0]
        ok, reason = verify_tree_event_notification(
            n, kp.public_key_hex())
        assert ok, reason
    finally:
        sub.stop()
        srv.stop()


# ---------- Demo ----------

def test_demo(tmp_path):
    print("=== Demo: full lifecycle ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["chain_valid"] is True
    assert audit["event_count"] == 6  # 3 initial + 3 live
    assert set(audit["current_rooms"]) == {
        "world:chess", "world:reading", "world:music"}
    assert audit["subscriber"]["logs_match_parent"] is True
    assert "world:chess" in audit["subscriber"]["rooms_in_state"]
    assert (tmp_path / "living_tree" /
            "living_tree_demo.json").exists()
