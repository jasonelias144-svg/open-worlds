import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import (
    Petition, Act, Ack, Refusal, Route, Admission,
)
from multiverse_c73 import HAS_CHESS
from multiverse_c74 import (
    RoomEntry, RoomWorld, ChatWorld, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CHESS, reason="python-chess not installed")


def test_room_entry_validates():
    print("=== RoomEntry: validates fields ===")
    with pytest.raises(ValueError):
        RoomEntry("", "r", "http://x", "aa" * 32, "n")
    with pytest.raises(ValueError):
        RoomEntry("p", "", "http://x", "aa" * 32, "n")
    with pytest.raises(ValueError):
        RoomEntry("p", "r", "not-a-url", "aa" * 32, "n")
    with pytest.raises(ValueError):
        RoomEntry("p", "r", "http://x", "short", "n")


def test_manifest_has_sub_registry():
    print("=== RoomWorld manifest has sub_registry_endpoint ===")
    mall = RoomWorld("world:u", "U")
    assert mall.manifest().sub_registry_endpoint is not None


def test_petition_admits():
    print("=== RoomWorld: petition admits ===")
    mall = RoomWorld("world:u", "U")
    r = mall.petition(Petition(
        petitioner_token="alice", petitioner_name="Alice",
        passport_admissions=(), message=""))
    assert isinstance(r, Admission)


def test_register_and_list():
    print("=== RoomWorld: register and list ===")
    mall = RoomWorld("world:u", "U")
    mall.register_room(RoomEntry(
        "world:u", "world:r", "http://r",
        "aa" * 32, "R"))
    assert mall.list_rooms() == [{
        "room_id": "world:r", "base_url": "http://r",
        "public_key": "aa" * 32, "name": "R",
        "description": ""}]


def test_unregister():
    print("=== RoomWorld: unregister removes ===")
    mall = RoomWorld("world:u", "U")
    mall.register_room(RoomEntry(
        "world:u", "world:r", "http://r",
        "aa" * 32, "R"))
    mall.unregister_room("world:r")
    assert mall.list_rooms() == []


def test_route_requires_lobby_admission():
    print("=== Route: requires lobby admission ===")
    mall = RoomWorld("world:u", "U")
    mall.register_room(RoomEntry(
        "world:u", "world:r", "http://r",
        "aa" * 32, "R"))
    r = mall.petition(Petition(
        petitioner_token="alice", petitioner_name="Alice",
        passport_admissions=(), message="",
        target="world:r"))
    assert isinstance(r, Refusal)


def test_unknown_room_refused():
    print("=== Route: unknown room → Refusal ===")
    mall = RoomWorld("world:u", "U")
    mall.petition(Petition(
        petitioner_token="alice", petitioner_name="Alice",
        passport_admissions=(), message=""))
    r = mall.petition(Petition(
        petitioner_token="alice", petitioner_name="Alice",
        passport_admissions=(), message="",
        target="world:nope"))
    assert isinstance(r, Refusal)


def test_route_over_http():
    print("=== Route: live HTTP fetch → Route response ===")
    from wcp_http_shim import WorldProtocolServer
    plaza = ChatWorld("world:p", "Plaza")
    srv = WorldProtocolServer(plaza, port=0)
    srv.serve_in_thread()
    time.sleep(0.2)
    url = f"http://127.0.0.1:{srv._httpd.server_address[1]}"
    try:
        mall = RoomWorld("world:u", "U")
        mall.register_room(RoomEntry(
            "world:u", "world:p", url,
            "aa" * 32, "Plaza"))
        mall.petition(Petition(
            petitioner_token="alice",
            petitioner_name="Alice",
            passport_admissions=(), message=""))
        r = mall.petition(Petition(
            petitioner_token="alice",
            petitioner_name="Alice",
            passport_admissions=(), message="",
            target="world:p"))
        assert isinstance(r, Route)
        assert r.target_manifest.entity_id == "world:p"
    finally:
        srv.stop()


def test_route_fetch_failure():
    print("=== Route: fetch failure → Refusal ===")
    mall = RoomWorld("world:u", "U")
    mall.register_room(RoomEntry(
        "world:u", "world:none", "http://127.0.0.1:1",
        "aa" * 32, "N"))
    mall.petition(Petition(
        petitioner_token="alice",
        petitioner_name="Alice",
        passport_admissions=(), message=""))
    r = mall.petition(Petition(
        petitioner_token="alice",
        petitioner_name="Alice",
        passport_admissions=(), message="",
        target="world:none"))
    assert isinstance(r, Refusal)


def test_room_can_be_roomworld():
    """Recursive nesting: a RoomWorld can be a room."""
    print("=== Nesting: a RoomWorld can be a room ===")
    from wcp_http_shim import WorldProtocolServer
    inner = RoomWorld("world:inner", "Inner")
    srv = WorldProtocolServer(inner, port=0)
    srv.serve_in_thread()
    time.sleep(0.2)
    url = f"http://127.0.0.1:{srv._httpd.server_address[1]}"
    try:
        outer = RoomWorld("world:outer", "Outer")
        outer.register_room(RoomEntry(
            "world:outer", "world:inner", url,
            "aa" * 32, "Inner RoomWorld"))
        outer.petition(Petition(
            petitioner_token="alice",
            petitioner_name="Alice",
            passport_admissions=(), message=""))
        r = outer.petition(Petition(
            petitioner_token="alice",
            petitioner_name="Alice",
            passport_admissions=(), message="",
            target="world:inner"))
        assert isinstance(r, Route)
        assert r.target_manifest.entity_id == "world:inner"
        assert r.target_manifest.sub_registry_endpoint is not None
    finally:
        srv.stop()


def test_chatworld_say():
    print("=== ChatWorld: say ===")
    plaza = ChatWorld("world:p", "Plaza")
    plaza.petition(Petition(
        petitioner_token="alice", petitioner_name="Alice",
        passport_admissions=(), message=""))
    r = plaza.act(Act(
        actor_token="alice", type="chat.say",
        payload={"text": "hello"}))
    assert isinstance(r, Ack)


def test_chatworld_refusals():
    print("=== ChatWorld: empty text and unknown act refused ===")
    plaza = ChatWorld("world:p", "Plaza")
    plaza.petition(Petition(
        petitioner_token="alice", petitioner_name="Alice",
        passport_admissions=(), message=""))
    r = plaza.act(Act(
        actor_token="alice", type="chat.say",
        payload={"text": "   "}))
    assert isinstance(r, Refusal)
    r = plaza.act(Act(
        actor_token="alice", type="bogus", payload={}))
    assert isinstance(r, Refusal)
    r = plaza.act(Act(
        actor_token="other", type="chat.say",
        payload={"text": "hi"}))
    assert isinstance(r, Refusal)


def test_demo(tmp_path):
    print("=== Demo: Union Square ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["mall_id"] == "world:union-square"
    assert set(audit["rooms"]) == {
        "world:park-chess", "world:park-plaza"}
    assert audit["alice_route_type"] == "Route"
    assert audit["alice_route_target"] == "world:park-chess"
    assert audit["carol_route_type"] == "Route"
    assert audit["carol_route_target"] == "world:park-plaza"
    assert audit["mall_log_entries"] >= 2
    assert audit["chess_log_entries"] >= 1
    assert audit["plaza_log_entries"] >= 2
