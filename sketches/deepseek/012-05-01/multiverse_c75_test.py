import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import (
    Petition, Act, Ack, Refusal, Route,
    Admission as WCPAdmission,
)
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c15 import PassportV2
from multiverse_c65 import FederationClient
from multiverse_c73 import ChessWorld, HAS_CHESS
from multiverse_c74 import RoomWorld, RoomEntry, ChatWorld
from multiverse_c75 import (
    follow_route, enter_path, snapshot_tree,
    WorldTreeSnapshot, RouteFollowResult,
    _enter_at_url, _default_room_loader,
    demo,
)
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


# =====================================================================
# _enter_at_url: the core step
# =====================================================================

def test_enter_at_url_happy(tmp_path):
    print("=== _enter_at_url: happy (no key) ===")
    plaza = ChatWorld("world:p", "P")
    srv, url = _serve(plaza)
    try:
        c = _client(tmp_path)
        r = _enter_at_url(c, url)
        assert r.ok
        # No expected key → unverified but entered
        assert not r.verified
        assert len(c.state.passport) == 1
    finally:
        srv.stop()


def test_enter_at_url_verified(tmp_path):
    print("=== _enter_at_url: verified against expected key ===")
    world = ChessWorld("world:c", "C")
    kp = KeyPair.generate()
    from multiverse_c13 import SignedWorld
    signed = SignedWorld(world, kp)
    srv, url = _serve(signed)
    try:
        c = _client(tmp_path)
        r = _enter_at_url(
            c, url, expected_public_key=kp.public_key_hex())
        assert r.ok
        assert r.verified
    finally:
        srv.stop()


def test_enter_at_url_wrong_key(tmp_path):
    print("=== _enter_at_url: wrong key → fail ===")
    world = ChessWorld("world:c", "C")
    kp = KeyPair.generate()
    from multiverse_c13 import SignedWorld
    signed = SignedWorld(world, kp)
    srv, url = _serve(signed)
    try:
        c = _client(tmp_path)
        wrong = KeyPair.generate().public_key_hex()
        r = _enter_at_url(c, url, expected_public_key=wrong)
        assert not r.ok
        assert "does not verify" in r.reason
    finally:
        srv.stop()


def test_enter_at_url_refused(tmp_path):
    print("=== _enter_at_url: refusal propagates ===")
    plaza = ChatWorld("world:p", "P")
    srv, url = _serve(plaza)
    try:
        c = _client(tmp_path)
        # First entry succeeds
        r1 = _enter_at_url(c, url)
        assert r1.ok
        # Second entry → "Already admitted"
        r2 = _enter_at_url(c, url)
        assert not r2.ok
        assert "refused" in r2.reason.lower()
    finally:
        srv.stop()


def test_enter_at_url_no_identity():
    print("=== _enter_at_url: no identity → fail ===")
    c = FederationClient(Path("/tmp/nonexistent_test_c75"))
    r = _enter_at_url(c, "http://127.0.0.1:1")
    assert not r.ok
    assert "identity" in r.reason.lower()


# =====================================================================
# follow_route: composes on _enter_at_url
# =====================================================================

def test_follow_route_happy(tmp_path):
    print("=== follow_route: happy ===")
    plaza = ChatWorld("world:p", "P")
    kp = KeyPair.generate()
    from multiverse_c13 import SignedWorld
    signed = SignedWorld(plaza, kp)
    srv, url = _serve(signed)
    try:
        c = _client(tmp_path)
        # Build a Route to the plaza
        m = signed.manifest()
        target_manifest = type(m)(
            entity_id=m.entity_id, name=m.name,
            protocol_version=m.protocol_version,
            law_url=m.law_url, act_endpoint=m.act_endpoint,
            log_endpoint=m.log_endpoint,
            sub_registry_endpoint=m.sub_registry_endpoint)
        route = Route(target_manifest=target_manifest,
                       reason="test")
        r = follow_route(
            c, route, url,
            expected_public_key=kp.public_key_hex())
        assert r.ok
        assert r.verified
        assert r.world_id == "world:p"
    finally:
        srv.stop()


def test_follow_route_rejects_non_route(tmp_path):
    print("=== follow_route: not a Route → fail ===")
    c = _client(tmp_path)
    r = follow_route(c, "not a route", "http://x")
    assert not r.ok


# =====================================================================
# enter_path: multiple hops
# =====================================================================

def test_enter_path_two_hops(tmp_path):
    print("=== enter_path: two hops ===")
    plaza = ChatWorld("world:p", "P")
    chess = ChessWorld("world:c", "C")
    s1, u1 = _serve(plaza)
    s2, u2 = _serve(chess)
    try:
        c = _client(tmp_path)
        results = enter_path(c, [(u1, None), (u2, None)])
        assert len(results) == 2
        assert all(r.ok for r in results)
        assert len(c.state.passport) == 2
    finally:
        s1.stop()
        s2.stop()


def test_enter_path_partial_failure(tmp_path):
    print("=== enter_path: one step fails, others succeed ===")
    plaza = ChatWorld("world:p", "P")
    s1, u1 = _serve(plaza)
    try:
        c = _client(tmp_path)
        results = enter_path(c, [
            (u1, None),
            ("http://127.0.0.1:1", None),  # unreachable
        ])
        assert len(results) == 2
        assert results[0].ok
        assert not results[1].ok
    finally:
        s1.stop()


# =====================================================================
# snapshot_tree: observation
# =====================================================================

def test_snapshot_tree_single_world(tmp_path):
    print("=== snapshot_tree: single world ===")
    plaza = ChatWorld("world:p", "Plaza")
    srv, url = _serve(plaza)
    try:
        c = _client(tmp_path)
        snap = snapshot_tree(c, url, max_depth=3)
        assert len(snap.nodes) == 1
        assert snap.nodes[0].entity_id == "world:p"
        assert not snap.nodes[0].has_sub_registry
    finally:
        srv.stop()


def test_snapshot_tree_with_subregistry(tmp_path):
    print("=== snapshot_tree: sub-registry walked ===")
    chess = ChessWorld("world:c", "Chess")
    games = RoomWorld("world:games", "Games")
    s1, u1 = _serve(chess)
    s2, u2 = _serve(games)
    try:
        games.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:c", base_url=u1,
            public_key="00" * 32, name="Chess"))
        c = _client(tmp_path)
        def loader(url: str):
            if url.rstrip("/") == u2.rstrip("/"):
                return games.list_rooms()
            return None
        snap = snapshot_tree(c, u2, room_loader=loader,
                              max_depth=3)
        assert len(snap.nodes) == 2
        ids = {n.entity_id for n in snap.nodes}
        assert ids == {"world:games", "world:c"}
        assert len(snap.edges) == 1
    finally:
        s1.stop()
        s2.stop()


def test_snapshot_tree_depth_limit(tmp_path):
    print("=== snapshot_tree: depth limit respected ===")
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
        def loader(url: str):
            if url.rstrip("/") == u2.rstrip("/"):
                return outer.list_rooms()
            return None
        # max_depth=0 → only root
        snap0 = snapshot_tree(c, u2, room_loader=loader,
                                max_depth=0)
        assert len(snap0.nodes) == 1
        # max_depth=1 → root + inner
        snap1 = snapshot_tree(c, u2, room_loader=loader,
                                max_depth=1)
        assert len(snap1.nodes) == 2
    finally:
        s1.stop()
        s2.stop()


def test_snapshot_tree_no_loader(tmp_path):
    print("=== snapshot_tree: default loader returns None → no children ===")
    outer = RoomWorld("world:outer", "Outer")
    srv, url = _serve(outer)
    try:
        c = _client(tmp_path)
        # Default loader tries GET /rooms; RoomWorld doesn't
        # serve it, so it returns None.
        snap = snapshot_tree(c, url, max_depth=3)
        assert len(snap.nodes) == 1
        assert snap.nodes[0].has_sub_registry  # declares one
        assert snap.nodes[0].rooms == []       # but not queryable
    finally:
        srv.stop()


def test_snapshot_tree_unreachable_root(tmp_path):
    print("=== snapshot_tree: unreachable root → empty ===")
    c = _client(tmp_path)
    snap = snapshot_tree(c, "http://127.0.0.1:1")
    assert len(snap.nodes) == 0


def test_snapshot_tree_json_serializable(tmp_path):
    print("=== snapshot_tree: to_dict JSON-serializable ===")
    plaza = ChatWorld("world:p", "P")
    srv, url = _serve(plaza)
    try:
        c = _client(tmp_path)
        snap = snapshot_tree(c, url)
        wire = json.dumps(snap.to_dict())
        parsed = json.loads(wire)
        assert parsed["root_base_url"] == url
    finally:
        srv.stop()


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: tree walk + snapshot ===")
    audit = demo(artifact_dir=str(tmp_path))
    # All three walk steps succeeded
    assert len(audit["walk_results"]) == 3
    assert all(r["ok"] for r in audit["walk_results"])
    # Passport has 3 admissions
    assert audit["passport_admissions"] == 3
    # Snapshot saw the whole tree
    nodes = audit["snapshot"]["nodes"]
    assert len(nodes) == 6  # nexus + games + chess + plaza + poetry-hall + reading
    ids = {n["entity_id"] for n in nodes}
    assert ids == {
        "world:nexus", "world:games", "world:chess",
        "world:plaza", "world:poetry-hall", "world:reading",
    }
