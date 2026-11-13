import json
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import (
    Act, Ack, Refusal, Petition,
    Admission as WCPAdmission,
)
from multiverse_c13 import HAS_CRYPTO
from multiverse_c65 import FederationClient
from multiverse_c73 import ChessWorld, HAS_CHESS
from multiverse_c74 import RoomWorld, RoomEntry, ChatWorld
from multiverse_c75 import (
    snapshot_tree, _default_room_loader,
)
from multiverse_c76 import demo
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not (HAS_CRYPTO and HAS_CHESS),
    reason="cryptography and/or python-chess not installed")


# =====================================================================
# Helpers
# =====================================================================

def _serve(world):
    srv = WorldProtocolServer(world, port=0)
    srv.serve_in_thread()
    time.sleep(0.1)
    return srv, f"http://127.0.0.1:{srv._httpd.server_address[1]}"


def _client(tmp_path, name="Alice"):
    c = FederationClient(tmp_path / "c")
    c.create_identity(name)
    return c


def _get_json(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode())


# =====================================================================
# Shim: /rooms endpoint
# =====================================================================

def test_shim_serves_rooms_for_roomworld():
    print("=== Shim: /rooms serves RoomWorld's rooms ===")
    games = RoomWorld("world:games", "Games")
    games.register_room(RoomEntry(
        parent_world_id="world:games",
        room_id="world:a", base_url="http://a",
        public_key="00" * 32, name="A"))
    games.register_room(RoomEntry(
        parent_world_id="world:games",
        room_id="world:b", base_url="http://b",
        public_key="00" * 32, name="B"))
    srv, url = _serve(games)
    try:
        data = _get_json(f"{url}/rooms")
        assert isinstance(data, dict)
        assert "rooms" in data
        rooms = data["rooms"]
        assert isinstance(rooms, list)
        assert len(rooms) == 2
        ids = {r["room_id"] for r in rooms}
        assert ids == {"world:a", "world:b"}
    finally:
        srv.stop()


def test_shim_404_for_non_roomworld():
    print("=== Shim: /rooms 404 for ChatWorld ===")
    plaza = ChatWorld("world:p", "P")
    srv, url = _serve(plaza)
    try:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(
                f"{url}/rooms", timeout=5)
        assert exc_info.value.code == 404
    finally:
        srv.stop()


def test_shim_rooms_empty_roomworld():
    print("=== Shim: /rooms on empty RoomWorld returns [] ===")
    empty = RoomWorld("world:e", "Empty")
    srv, url = _serve(empty)
    try:
        data = _get_json(f"{url}/rooms")
        assert data == {"rooms": []}
    finally:
        srv.stop()


def test_shim_regression_other_endpoints():
    print("=== Shim: other endpoints still work ===")
    plaza = ChatWorld("world:p", "P")
    srv, url = _serve(plaza)
    try:
        # /manifest
        m = _get_json(f"{url}/manifest")
        assert m["entity_id"] == "world:p"
        # /log
        log = _get_json(f"{url}/log")
        assert "entries" in log
        # /petition + /act
        req = urllib.request.Request(
            f"{url}/petition",
            data=json.dumps({
                "petitioner_token": "alice",
                "petitioner_name": "Alice",
                "passport_admissions": [],
                "message": "hi",
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            resp = json.loads(r.read().decode())
        assert resp["kind"] == "admission"
    finally:
        srv.stop()


def test_shim_rooms_for_chessworld_404():
    print("=== Shim: /rooms 404 for ChessWorld (has no list_rooms) ===")
    chess = ChessWorld("world:c", "C")
    srv, url = _serve(chess)
    try:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(
                f"{url}/rooms", timeout=5)
        assert exc_info.value.code == 404
    finally:
        srv.stop()


# =====================================================================
# Default loader
# =====================================================================

def test_default_loader_works():
    print("=== _default_room_loader: returns rooms ===")
    games = RoomWorld("world:games", "Games")
    games.register_room(RoomEntry(
        parent_world_id="world:games",
        room_id="world:a", base_url="http://a",
        public_key="00" * 32, name="A"))
    srv, url = _serve(games)
    try:
        rooms = _default_room_loader(url)
        assert rooms is not None
        assert len(rooms) == 1
        assert rooms[0]["room_id"] == "world:a"
    finally:
        srv.stop()


def test_default_loader_empty_roomworld():
    print("=== _default_room_loader: empty RoomWorld → [] ===")
    empty = RoomWorld("world:e", "E")
    srv, url = _serve(empty)
    try:
        rooms = _default_room_loader(url)
        assert rooms == []
    finally:
        srv.stop()


def test_default_loader_returns_none_for_non_roomworld():
    print("=== _default_room_loader: ChatWorld → None ===")
    plaza = ChatWorld("world:p", "P")
    srv, url = _serve(plaza)
    try:
        rooms = _default_room_loader(url)
        assert rooms is None
    finally:
        srv.stop()


def test_default_loader_unreachable():
    print("=== _default_room_loader: unreachable → None ===")
    assert _default_room_loader("http://127.0.0.1:1") is None


# =====================================================================
# snapshot_tree with default loader
# =====================================================================

def test_snapshot_tree_no_callback_single_roomworld(tmp_path):
    print("=== snapshot_tree: single RoomWorld, default loader ===")
    games = RoomWorld("world:games", "Games")
    srv, url = _serve(games)
    try:
        c = _client(tmp_path)
        snap = snapshot_tree(c, url, max_depth=3)
        assert len(snap.nodes) == 1
        assert snap.nodes[0].entity_id == "world:games"
        assert snap.nodes[0].has_sub_registry
        assert snap.nodes[0].rooms == []  # empty RoomWorld
    finally:
        srv.stop()


def test_snapshot_tree_no_callback_with_children(tmp_path):
    print("=== snapshot_tree: RoomWorld with children, no callback ===")
    plaza = ChatWorld("world:p", "P")
    games = RoomWorld("world:games", "Games")
    s1, u1 = _serve(plaza)
    s2, u2 = _serve(games)
    try:
        games.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:p", base_url=u1,
            public_key="00" * 32, name="Plaza"))
        c = _client(tmp_path)
        # NO callback — relies on shim's /rooms
        snap = snapshot_tree(c, u2, max_depth=3)
        ids = {n.entity_id for n in snap.nodes}
        assert ids == {"world:games", "world:p"}
        assert len(snap.edges) == 1
    finally:
        s1.stop()
        s2.stop()


def test_snapshot_tree_deep_nesting(tmp_path):
    print("=== snapshot_tree: deep nesting without callback ===")
    # A → B → C (two RoomWorlds, then a ChatWorld)
    inner = ChatWorld("world:c", "C")
    middle = RoomWorld("world:b", "B")
    outer = RoomWorld("world:a", "A")
    s1, u1 = _serve(inner)
    s2, u2 = _serve(middle)
    s3, u3 = _serve(outer)
    try:
        middle.register_room(RoomEntry(
            parent_world_id="world:b",
            room_id="world:c", base_url=u1,
            public_key="00" * 32, name="C"))
        outer.register_room(RoomEntry(
            parent_world_id="world:a",
            room_id="world:b", base_url=u2,
            public_key="00" * 32, name="B"))
        c = _client(tmp_path)
        snap = snapshot_tree(c, u3, max_depth=3)
        ids = {n.entity_id for n in snap.nodes}
        assert ids == {"world:a", "world:b", "world:c"}
        assert len(snap.edges) == 2
    finally:
        s1.stop()
        s2.stop()
        s3.stop()


def test_snapshot_tree_depth_limits_without_callback(tmp_path):
    print("=== snapshot_tree: max_depth respected, no callback ===")
    inner = ChatWorld("world:inner", "Inner")
    outer = RoomWorld("world:outer", "Outer")
    s1, u1 = _serve(inner)
    s2, u2 = _serve(outer)
    try:
        outer.register_room(RoomEntry(
            parent_world_id="world:outer",
            room_id="world:inner", base_url=u1,
            public_key="00" * 32, name="Inner"))
        c = _client(tmp_path)
        # max_depth=0 → only root
        snap0 = snapshot_tree(c, u2, max_depth=0)
        assert len(snap0.nodes) == 1
        # max_depth=1 → root + inner
        snap1 = snapshot_tree(c, u2, max_depth=1)
        assert len(snap1.nodes) == 2
    finally:
        s1.stop()
        s2.stop()


def test_snapshot_tree_custom_loader_still_works(tmp_path):
    print("=== snapshot_tree: custom loader still works (regression) ===")
    inner = ChatWorld("world:i", "I")
    outer = RoomWorld("world:o", "O")
    s1, u1 = _serve(inner)
    s2, u2 = _serve(outer)
    try:
        outer.register_room(RoomEntry(
            parent_world_id="world:o",
            room_id="world:i", base_url=u1,
            public_key="00" * 32, name="I"))
        c = _client(tmp_path)
        def custom_loader(url):
            if url.rstrip("/") == u2.rstrip("/"):
                return outer.list_rooms()
            return None
        snap = snapshot_tree(c, u2, room_loader=custom_loader,
                              max_depth=3)
        ids = {n.entity_id for n in snap.nodes}
        assert ids == {"world:o", "world:i"}
    finally:
        s1.stop()
        s2.stop()


def test_snapshot_tree_same_result_with_and_without_loader(tmp_path):
    print("=== snapshot_tree: default and custom loaders agree ===")
    inner = ChatWorld("world:i", "I")
    outer = RoomWorld("world:o", "O")
    s1, u1 = _serve(inner)
    s2, u2 = _serve(outer)
    try:
        outer.register_room(RoomEntry(
            parent_world_id="world:o",
            room_id="world:i", base_url=u1,
            public_key="00" * 32, name="I"))
        c = _client(tmp_path)
        snap_default = snapshot_tree(
            c, u2, max_depth=3)
        def custom(url):
            if url.rstrip("/") == u2.rstrip("/"):
                return outer.list_rooms()
            return None
        snap_custom = snapshot_tree(
            c, u2, room_loader=custom, max_depth=3)
        # Same nodes, same edges (ordering preserved)
        assert ([(n.entity_id, n.depth)
                 for n in snap_default.nodes]
                == [(n.entity_id, n.depth)
                    for n in snap_custom.nodes])
        assert snap_default.edges == snap_custom.edges
    finally:
        s1.stop()
        s2.stop()


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: tree walk without callback ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["node_count"] == 6
    assert audit["edge_count"] == 4
    ids = {n["entity_id"]
           for n in audit["snapshot_default_loader"]["nodes"]}
    assert ids == {
        "world:nexus", "world:games", "world:chess",
        "world:plaza", "world:poetry-hall", "world:reading",
    }
    assert all(r["ok"] for r in audit["walk_results"])
    assert audit["passport_admissions"] == 3
    assert audit["snapshots_match"] is True
