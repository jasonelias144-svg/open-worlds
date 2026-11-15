import json
import time
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from map_world import (
    MapRegistry, WorldPin, MultiversalMap, MapServer,
    _resolve_impl, _recursive_resolve, _explain_resolve,
    _get_json, _post_json, MAX_DEPTH,
)
from lobby_server import LobbyServer
from signed_world_log import SignedLogWorld
from multiverse_c74 import ChatWorld
from multiverse_c3 import Petition, Route, Refusal
from lobby import HAS_CRYPTO


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _w(wid, name):
    kp = _kp()
    signed = SignedLogWorld(ChatWorld(wid, name), kp)
    srv = LobbyServer(signed, kp, port=0)
    srv.serve_in_thread()
    url = (f"http://127.0.0.1:"
            f"{srv._httpd.server_address[1]}")
    return srv, url, signed.world_signer


def _m(mid, direct=None, subs=None):
    kp = _kp()
    reg = MapRegistry()
    if direct:
        reg.add(WorldPin(
            direct[0], direct[1], direct[2],
            cluster="Direct"))
    for sub in (subs or []):
        reg.add(WorldPin(
            sub[0], sub[1], sub[2],
            cluster="Sub", kind="map"))
    mv = MultiversalMap(mid, mid, kp, reg)
    signed = SignedLogWorld(mv, kp)
    srv = MapServer(signed, kp, mv, port=0)
    srv.serve_in_thread()
    url = (f"http://127.0.0.1:"
            f"{srv._httpd.server_address[1]}")
    return srv, url, mv.world_signer(), mv, reg


def _count_nodes(node):
    if node is None:
        return 0
    return 1 + sum(_count_nodes(c)
                    for c in node.get("children", []))


# -- Direct explain --

def test_explain_direct_hit():
    w_srv, w_url, w_sig = _w("world:w", "W")
    m_srv, m_url, m_sig, m_mv, _ = _m(
        "map:m", direct=("world:w", w_url, w_sig))
    time.sleep(0.2)
    try:
        result, trace = _explain_resolve(m_mv, "world:w")
        assert result is not None
        assert trace["result"] == "found_directly"
        assert trace["found_via"] == []
        assert trace["children"] == []
    finally:
        w_srv.stop(); m_srv.stop()


def test_explain_three_hops():
    w_srv, w_url, w_sig = _w("world:w", "W")
    c_srv, c_url, c_sig, c_mv, _ = _m(
        "map:c", direct=("world:w", w_url, w_sig))
    b_srv, b_url, b_sig, b_mv, _ = _m(
        "map:b", subs=[("map:c", c_url, c_sig)])
    a_srv, a_url, a_sig, a_mv, _ = _m(
        "map:a", subs=[("map:b", b_url, b_sig)])
    time.sleep(0.2)
    try:
        result, trace = _explain_resolve(a_mv, "world:w")
        assert result is not None
        assert trace["result"] == "found_via_children"
        assert trace["found_via"] == ["map:b", "map:c"]
        # Three trace nodes total: a, b, c
        assert _count_nodes(trace) == 3
    finally:
        for s in (w_srv, c_srv, b_srv, a_srv):
            s.stop()


def test_explain_depth_exceeded():
    w_srv, w_url, w_sig = _w("world:w", "W")
    e_srv, e_url, e_sig, e_mv, _ = _m(
        "map:e", direct=("world:w", w_url, w_sig))
    d_srv, d_url, d_sig, d_mv, _ = _m(
        "map:d", subs=[("map:e", e_url, e_sig)])
    c_srv, c_url, c_sig, c_mv, _ = _m(
        "map:c", subs=[("map:d", d_url, d_sig)])
    b_srv, b_url, b_sig, b_mv, _ = _m(
        "map:b", subs=[("map:c", c_url, c_sig)])
    a_srv, a_url, a_sig, a_mv, _ = _m(
        "map:a", subs=[("map:b", b_url, b_sig)])
    time.sleep(0.2)
    try:
        result, trace = _explain_resolve(a_mv, "world:w")
        assert result is None
        assert trace["result"] == "not_found"
        # Walk children to find the depth_blocked leaf
        def find_depth_blocked(node):
            if node.get("result") == "depth_blocked":
                return True
            return any(find_depth_blocked(c)
                        for c in node.get("children", []))
        assert find_depth_blocked(trace)
    finally:
        for s in (w_srv, e_srv, d_srv, c_srv, b_srv, a_srv):
            s.stop()


def test_explain_unreachable_submap():
    w_srv, w_url, w_sig = _w("world:w", "W")
    c_srv, c_url, c_sig, c_mv, _ = _m(
        "map:c", direct=("world:w", w_url, w_sig))
    a_srv, a_url, a_sig, a_mv, _ = _m(
        "map:a",
        subs=[
            ("map:ghost", "http://127.0.0.1:1",
             "did:key:" + "00" * 32),
            ("map:c", c_url, c_sig),
        ])
    time.sleep(0.2)
    try:
        result, trace = _explain_resolve(a_mv, "world:w")
        assert result is not None
        # Ghost tried first, unreachable, then C found it
        assert len(trace["children"]) == 2
        assert trace["children"][0]["map_id"] == "map:ghost"
        assert trace["children"][0]["result"] == "unreachable"
        assert trace["children"][1]["result"] == "found_via_children"
    finally:
        for s in (w_srv, c_srv, a_srv):
            s.stop()


def test_explain_cycle_blocked():
    """A → B, B → A. Query A for unknown."""
    a_srv, a_url, a_sig, a_mv, a_reg = _m("map:a")
    b_srv, b_url, b_sig, b_mv, b_reg = _m("map:b")
    time.sleep(0.2)
    a_reg.add(WorldPin(
        "map:b", b_url, b_sig, kind="map"))
    b_reg.add(WorldPin(
        "map:a", a_url, a_sig, kind="map"))
    try:
        result, trace = _explain_resolve(a_mv, "world:nonexistent")
        assert result is None
        # A → B → A(cycle_blocked)
        assert len(trace["children"]) == 1
        b_node = trace["children"][0]
        assert b_node["map_id"] == "map:b"
        # B tried A, which was cycle_blocked
        assert len(b_node.get("children", [])) == 1
        cycle_node = b_node["children"][0]
        assert cycle_node["result"] == "cycle_blocked"
    finally:
        a_srv.stop(); b_srv.stop()


# -- /explain HTTP endpoint --

def test_explain_http_endpoint():
    w_srv, w_url, w_sig = _w("world:w", "W")
    m_srv, m_url, m_sig, m_mv, _ = _m(
        "map:m", direct=("world:w", w_url, w_sig))
    time.sleep(0.2)
    try:
        data = _get_json(f"{m_url}/explain/world:w")
        assert data["found"] is True
        assert data["trace"]["result"] == "found_directly"
        # Unknown
        miss = _get_json(f"{m_url}/explain/world:none")
        assert miss["found"] is False
        assert miss["trace"]["result"] == "not_found"
    finally:
        w_srv.stop(); m_srv.stop()


def test_pin_with_trace():
    w_srv, w_url, w_sig = _w("world:w", "W")
    c_srv, c_url, c_sig, c_mv, _ = _m(
        "map:c", direct=("world:w", w_url, w_sig))
    b_srv, b_url, b_sig, b_mv, _ = _m(
        "map:b", subs=[("map:c", c_url, c_sig)])
    a_srv, a_url, a_sig, a_mv, _ = _m(
        "map:a", subs=[("map:b", b_url, b_sig)])
    time.sleep(0.2)
    try:
        # Without trace
        no_trace = _get_json(f"{a_url}/pin/world:w")
        assert "trace" not in no_trace
        assert no_trace["status"] != "not_registered"
        # With trace
        with_trace = _get_json(
            f"{a_url}/pin/world:w?trace=1")
        assert "trace" in with_trace
        assert with_trace["trace"]["result"] == \
            "found_via_children"
    finally:
        for s in (w_srv, c_srv, b_srv, a_srv):
            s.stop()


# -- Backward compat: normal /pin and /petition still work --

def test_normal_pin_still_works():
    w_srv, w_url, w_sig = _w("world:w", "W")
    m_srv, m_url, m_sig, m_mv, _ = _m(
        "map:m", direct=("world:w", w_url, w_sig))
    time.sleep(0.2)
    try:
        data = _get_json(f"{m_url}/pin/world:w")
        assert data["status"] == "live"
    finally:
        w_srv.stop(); m_srv.stop()


def test_petition_still_works():
    w_srv, w_url, w_sig = _w("world:w", "W")
    m_srv, m_url, m_sig, m_mv, _ = _m(
        "map:m", direct=("world:w", w_url, w_sig))
    time.sleep(0.2)
    try:
        resp = _post_json(f"{m_url}/petition", {
            "petitioner_token": "v",
            "petitioner_name": "V",
            "passport_admissions": [],
            "message": "",
            "target": "world:w",
        })
        assert resp["kind"] == "route"
    finally:
        w_srv.stop(); m_srv.stop()


# -- Demo --

def test_demo(tmp_path):
    from map_world import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["explain"]["world:park"]["found"] is True
    assert audit["explain"]["world:park"]["via"] == \
        ["map:b", "map:c", "map:d"]
    assert audit["explain"]["world:archives"]["found"] is False
    assert audit["explain"]["world:nonexistent"]["found"] is False
    assert audit["explain"]["world:chess"]["found"] is True
    assert audit["explain"]["world:park"]["trace_nodes"] == 4
    assert audit["pin_with_trace_matches_explain"] is True
    assert audit["pin_without_trace_has_no_trace"] is True
    assert (tmp_path / "explain_map" /
            "explain_map_demo.json").exists()
