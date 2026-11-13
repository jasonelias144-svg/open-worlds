import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import (
    Manifest, Petition, Route, Ack,
    Admission as WCPAdmission,
)
from multiverse_c13 import HAS_CRYPTO
from multiverse_c65 import FederationClient
from multiverse_c73 import ChessWorld, HAS_CHESS
from multiverse_c74 import RoomWorld, RoomEntry, ChatWorld
from multiverse_c75 import (
    follow_route as c75_follow_route,
    RouteFollowResult,
)
from multiverse_c77 import (
    resolve_manifest_urls, UrlResolvingRoomWorld,
    follow_route, walk_to, demo,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not (HAS_CRYPTO and HAS_CHESS),
    reason="cryptography and/or python-chess not installed")


def _serve(world):
    srv = WorldProtocolServer(world, port=0)
    srv.serve_in_thread()
    time.sleep(0.1)
    return srv, f"http://127.0.0.1:{srv._httpd.server_address[1]}"


def _client(tmp_path, name="Alice"):
    c = FederationClient(tmp_path / "c")
    c.create_identity(name)
    return c


# ---------------------------------------------------------------------
# resolve_manifest_urls
# ---------------------------------------------------------------------

def test_resolve_substitutes_uri_endpoints():
    print("=== resolve_manifest_urls: URI → HTTP ===")
    m = Manifest(
        entity_id="w", name="W", protocol_version="WCP/0.2",
        law_url="park://w/law",
        act_endpoint="park://w/act",
        log_endpoint="park://w/log",
        sub_registry_endpoint=None)
    resolved = resolve_manifest_urls(m, "http://host:1234")
    assert resolved.law_url == "http://host:1234/law"
    assert resolved.act_endpoint == "http://host:1234/act"
    assert resolved.log_endpoint == "http://host:1234/log"
    # entity_id, name unchanged
    assert resolved.entity_id == "w"
    # original untouched
    assert m.act_endpoint == "park://w/act"


def test_resolve_preserves_http_endpoints():
    print("=== resolve_manifest_urls: existing HTTP preserved ===")
    m = Manifest(
        entity_id="w", name="W", protocol_version="WCP/0.2",
        law_url="https://other/law",
        act_endpoint="https://other/act",
        log_endpoint="https://other/log",
        sub_registry_endpoint=None)
    resolved = resolve_manifest_urls(m, "http://host:1234")
    assert resolved.law_url == "https://other/law"
    assert resolved.act_endpoint == "https://other/act"


# ---------------------------------------------------------------------
# UrlResolvingRoomWorld
# ---------------------------------------------------------------------

def test_url_resolving_roomworld_route_has_http_urls():
    print("=== UrlResolvingRoomWorld: Route has HTTP URLs ===")
    inner = ChatWorld("world:inner", "Inner")
    s1, u1 = _serve(inner)
    games = UrlResolvingRoomWorld("world:games", "Games")
    s2, u2 = _serve(games)
    try:
        games.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:inner", base_url=u1,
            public_key="00" * 32, name="Inner"))
        alice = create_identity("Alice")
        games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message=""))
        route = games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message="",
            target="world:inner"))
        assert isinstance(route, Route)
        # The target manifest has HTTP URLs
        assert route.target_manifest.act_endpoint.startswith(
            u1.rstrip("/") + "/act")
        assert route.target_manifest.log_endpoint.startswith(
            u1.rstrip("/") + "/log")
        # Its declared (published) manifest still has URI scheme
        assert inner.manifest().act_endpoint.startswith("chat://")
    finally:
        s1.stop()
        s2.stop()


def test_plain_roomworld_route_has_uris():
    print("=== Plain RoomWorld: Route has URIs (unchanged) ===")
    inner = ChatWorld("world:inner", "Inner")
    s1, u1 = _serve(inner)
    games = RoomWorld("world:games", "Games")  # C74, not C77
    s2, u2 = _serve(games)
    try:
        games.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:inner", base_url=u1,
            public_key="00" * 32, name="Inner"))
        alice = create_identity("Alice")
        games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message=""))
        route = games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message="",
            target="world:inner"))
        assert isinstance(route, Route)
        assert route.target_manifest.act_endpoint.startswith("chat://")
    finally:
        s1.stop()
        s2.stop()


# ---------------------------------------------------------------------
# follow_route: optional base_url
# ---------------------------------------------------------------------

def test_follow_route_derives_base_url(tmp_path):
    print("=== follow_route: derives base_url from Route ===")
    inner = ChatWorld("world:inner", "Inner")
    s1, u1 = _serve(inner)
    games = UrlResolvingRoomWorld("world:games", "Games")
    s2, u2 = _serve(games)
    try:
        games.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:inner", base_url=u1,
            public_key="00" * 32, name="Inner"))
        alice = create_identity("Alice")
        games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message=""))
        route = games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message="",
            target="world:inner"))
        c = _client(tmp_path)
        # No base_url passed
        r = follow_route(c, route)
        assert r.ok, r.reason
        assert r.base_url == u1.rstrip("/")
        assert len(c.state.passport) == 1
    finally:
        s1.stop()
        s2.stop()


def test_follow_route_fails_with_uri_only_route(tmp_path):
    print("=== follow_route: URI-only Route → fail ===")
    inner = ChatWorld("world:inner", "Inner")
    games = RoomWorld("world:games", "Games")
    alice = create_identity("Alice")
    games.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=(), message=""))
    games.register_room(RoomEntry(
        parent_world_id="world:games",
        room_id="world:inner", base_url="http://example",
        public_key="00" * 32, name="Inner"))
    # NOTE: we can't actually serve the inner world for this test,
    # but the Route is constructed from the declared (URI) manifest
    route = games.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=(), message="",
        target="world:inner"))
    # Try to follow without base_url — should fail with a clear
    # message about needing base_url
    c = _client(tmp_path)
    # But the URI route can't be followed without a URL. This
    # exercises follow_route's URI guard.
    from multiverse_c77 import follow_route as c77_follow
    # Force a URI-only Route by using RoomWorld's declared manifest
    # (still URI scheme)
    from multiverse_c3 import Route as R
    uri_route = R(
        target_manifest=inner.manifest(),
        reason="test")
    r = c77_follow(c, uri_route)
    assert not r.ok
    assert "room_base_url" in r.reason or "HTTP URL" in r.reason


def test_follow_route_with_explicit_base_url_still_works(tmp_path):
    print("=== follow_route: explicit base_url (C75 compat) ===")
    inner = ChatWorld("world:inner", "Inner")
    s1, u1 = _serve(inner)
    games = UrlResolvingRoomWorld("world:games", "Games")
    s2, u2 = _serve(games)
    try:
        games.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:inner", base_url=u1,
            public_key="00" * 32, name="Inner"))
        alice = create_identity("Alice")
        games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message=""))
        route = games.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message="",
            target="world:inner"))
        c = _client(tmp_path)
        # Explicit base_url — the C75 way
        r = follow_route(c, route, room_base_url=u1)
        assert r.ok
        assert r.base_url == u1.rstrip("/")
    finally:
        s1.stop()
        s2.stop()


# ---------------------------------------------------------------------
# walk_to
# ---------------------------------------------------------------------

def test_walk_to_full_chain(tmp_path):
    print("=== walk_to: full chain, URL-only ===")
    inner = ChatWorld("world:inner", "Inner")
    middle = UrlResolvingRoomWorld("world:mid", "Mid")
    outer = UrlResolvingRoomWorld("world:out", "Out")
    s1, u1 = _serve(inner)
    s2, u2 = _serve(middle)
    s3, u3 = _serve(outer)
    try:
        middle.register_room(RoomEntry(
            parent_world_id="world:mid",
            room_id="world:inner", base_url=u1,
            public_key="00" * 32, name="Inner"))
        outer.register_room(RoomEntry(
            parent_world_id="world:out",
            room_id="world:mid", base_url=u2,
            public_key="00" * 32, name="Mid"))
        c = _client(tmp_path)
        # Client knows ONLY u3 (the root URL) and the path.
        walk = walk_to(c, u3, ["world:mid", "world:inner"])
        assert all(r.ok for r in walk), [r.reason for r in walk]
        assert len(walk) == 3  # root + 2 rooms
        assert walk[0].world_id == "world:out"
        assert walk[1].world_id == "world:mid"
        assert walk[2].world_id == "world:inner"
        assert len(c.state.passport) == 3
    finally:
        s1.stop()
        s2.stop()
        s3.stop()


def test_walk_to_stops_on_failure(tmp_path):
    print("=== walk_to: stops on unreachable room ===")
    outer = UrlResolvingRoomWorld("world:out", "Out")
    s3, u3 = _serve(outer)
    try:
        outer.register_room(RoomEntry(
            parent_world_id="world:out",
            room_id="world:gone", base_url="http://127.0.0.1:1",
            public_key="00" * 32, name="Gone"))
        c = _client(tmp_path)
        walk = walk_to(c, u3, ["world:gone"])
        # root ok, room fail
        assert walk[0].ok
        assert not walk[-1].ok
    finally:
        s3.stop()


def test_walk_to_unknown_room(tmp_path):
    print("=== walk_to: unknown room → stop ===")
    outer = UrlResolvingRoomWorld("world:out", "Out")
    s3, u3 = _serve(outer)
    try:
        c = _client(tmp_path)
        walk = walk_to(c, u3, ["world:nonexistent"])
        assert walk[0].ok
        assert not walk[-1].ok
        assert "expected route" in walk[-1].reason.lower() \
            or "unknown" in walk[-1].reason.lower()
    finally:
        s3.stop()


def test_walk_to_empty_path(tmp_path):
    print("=== walk_to: empty path → just root ===")
    outer = UrlResolvingRoomWorld("world:out", "Out")
    s3, u3 = _serve(outer)
    try:
        c = _client(tmp_path)
        walk = walk_to(c, u3, [])
        assert len(walk) == 1
        assert walk[0].ok
    finally:
        s3.stop()


# ---------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------

def test_demo(tmp_path):
    print("=== Demo: walk tree by URL alone ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["reached_chess"] is True
    assert len(audit["walk"]) == 3
    assert all(r["ok"] for r in audit["walk"])
    # The client never saw the intermediate URLs
    assert audit["hidden_urls"]["world:games"] != audit["nexus_url"]
    assert audit["hidden_urls"]["world:chess"] != audit["nexus_url"]
    # But the walk results expose them
    assert audit["walk"][1]["base_url"] == audit["hidden_urls"]["world:games"]
    assert audit["walk"][2]["base_url"] == audit["hidden_urls"]["world:chess"]
