import json
import time
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from individual_bundle import _canonical, _hash, _did_from_kp
from map_world import (
    MapRegistry, WorldPin, MultiversalMap, MapServer,
    _recursive_resolve, _get_json, _post_json, MAX_DEPTH,
)
from lobby_server import LobbyServer
from signed_world_log import SignedLogWorld
from multiverse_c74 import ChatWorld
from multiverse_c3 import Petition, Route, Refusal
from worldline import (
    WorldlineSummary, WorldVisit,
    worldline_from_bundle, annotate_worldline,
    verify_annotated_worldline,
)
from unified_individual import (
    UnifiedIndividualSession, pack_unified_bundle,
)
from coupled_learners import TinyRNN
from world_adapters import FederatedAdapter
from world_agent_coupling import ScriptedWorld
from coupled_learners import SIERPINSKI
from lobby import HAS_CRYPTO


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _make_world_server(wid, name):
    kp = _kp()
    signed = SignedLogWorld(ChatWorld(wid, name), kp)
    srv = LobbyServer(signed, kp, port=0)
    srv.serve_in_thread()
    url = (f"http://127.0.0.1:"
            f"{srv._httpd.server_address[1]}")
    return srv, url, signed.world_signer


def _make_map_server(mid, direct_world=None, sub_map=None):
    """Build a map server. direct_world = (wid, url, signer).
    sub_map = (mid, url, signer)."""
    map_kp = _kp()
    reg = MapRegistry()
    if direct_world:
        reg.add(WorldPin(
            direct_world[0], direct_world[1],
            direct_world[2], cluster="Direct"))
    if sub_map:
        reg.add(WorldPin(
            sub_map[0], sub_map[1], sub_map[2],
            cluster="Sub-Map", kind="map"))
    mv = MultiversalMap(mid, mid, map_kp, reg)
    signed = SignedLogWorld(mv, map_kp)
    srv = MapServer(signed, map_kp, mv, port=0)
    srv.serve_in_thread()
    url = (f"http://127.0.0.1:"
            f"{srv._httpd.server_address[1]}")
    return srv, url, mv.world_signer(), mv, reg


def _query(map_url, target):
    return _post_json(f"{map_url}/petition", {
        "petitioner_token": "v",
        "petitioner_name": "V",
        "passport_admissions": [],
        "message": "",
        "target": target,
    })


# -- Recursion depth --

def test_one_hop():
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    m_srv, m_url, m_sig, _, _ = _make_map_server(
        "map:m", direct_world=("world:w", w_url, w_sig))
    time.sleep(0.2)
    try:
        r = _query(m_url, "world:w")
        assert r["kind"] == "route"
        assert r["target_manifest"]["entity_id"] == "world:w"
    finally:
        w_srv.stop(); m_srv.stop()


def test_two_hops():
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    b_srv, b_url, b_sig, _, _ = _make_map_server(
        "map:b", direct_world=("world:w", w_url, w_sig))
    a_srv, a_url, a_sig, _, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        r = _query(a_url, "world:w")
        assert r["kind"] == "route"
        # Reason names the sub-map
        assert "map:b" in r["reason"]
    finally:
        for s in (w_srv, b_srv, a_srv):
            s.stop()


def test_four_hops_at_max_depth():
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    d_srv, d_url, d_sig, _, _ = _make_map_server(
        "map:d", direct_world=("world:w", w_url, w_sig))
    c_srv, c_url, c_sig, _, _ = _make_map_server(
        "map:c", sub_map=("map:d", d_url, d_sig))
    b_srv, b_url, b_sig, _, _ = _make_map_server(
        "map:b", sub_map=("map:c", c_url, c_sig))
    a_srv, a_url, a_sig, _, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        r = _query(a_url, "world:w")
        assert r["kind"] == "route"
        assert r["target_manifest"]["entity_id"] == "world:w"
    finally:
        for s in (w_srv, d_srv, c_srv, b_srv, a_srv):
            s.stop()


def test_five_hops_exceeds_max_depth():
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    e_srv, e_url, e_sig, _, _ = _make_map_server(
        "map:e", direct_world=("world:w", w_url, w_sig))
    d_srv, d_url, d_sig, _, _ = _make_map_server(
        "map:d", sub_map=("map:e", e_url, e_sig))
    c_srv, c_url, c_sig, _, _ = _make_map_server(
        "map:c", sub_map=("map:d", d_url, d_sig))
    b_srv, b_url, b_sig, _, _ = _make_map_server(
        "map:b", sub_map=("map:c", c_url, c_sig))
    a_srv, a_url, a_sig, _, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        r = _query(a_url, "world:w")
        assert r["kind"] == "refusal"
    finally:
        for s in (w_srv, e_srv, d_srv, c_srv, b_srv, a_srv):
            s.stop()


def test_via_chain_preserved():
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    c_srv, c_url, c_sig, _, _ = _make_map_server(
        "map:c", direct_world=("world:w", w_url, w_sig))
    b_srv, b_url, b_sig, _, _ = _make_map_server(
        "map:b", sub_map=("map:c", c_url, c_sig))
    a_srv, a_url, a_sig, _, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        # Query via HTTP for the pin
        data = _get_json(f"{a_url}/pin/world:w")
        assert data["status"] != "not_registered"
        # via chain lists b then c
        assert data["via"] == ["map:b", "map:c"]
        assert data["in_this_map"] is False
    finally:
        for s in (w_srv, c_srv, b_srv, a_srv):
            s.stop()


# -- Cycle prevention --

def test_cycle_prevented():
    """A → B and B → A. Querying A for unknown terminates."""
    a_kp = _kp()
    reg_a = MapRegistry()
    mv_a = MultiversalMap("map:a", "A", a_kp, reg_a)
    signed_a = SignedLogWorld(mv_a, a_kp)
    srv_a = MapServer(signed_a, a_kp, mv_a, port=0)
    srv_a.serve_in_thread()

    b_kp = _kp()
    reg_b = MapRegistry()
    mv_b = MultiversalMap("map:b", "B", b_kp, reg_b)
    signed_b = SignedLogWorld(mv_b, b_kp)
    srv_b = MapServer(signed_b, b_kp, mv_b, port=0)
    srv_b.serve_in_thread()
    time.sleep(0.2)

    a_url = (f"http://127.0.0.1:"
              f"{srv_a._httpd.server_address[1]}")
    b_url = (f"http://127.0.0.1:"
              f"{srv_b._httpd.server_address[1]}")

    # A → B
    reg_a.add(WorldPin(
        "map:b", b_url, mv_b.world_signer(), kind="map"))
    # B → A
    reg_b.add(WorldPin(
        "map:a", a_url, mv_a.world_signer(), kind="map"))

    try:
        r = _query(a_url, "world:nonexistent")
        assert r["kind"] == "refusal"
        # And the whole cycle terminates within a bounded time
    finally:
        srv_a.stop(); srv_b.stop()


# -- Direct recursion (without HTTP) --

def test_recursive_resolve_function_direct():
    """The core function works when called directly, not just
    via HTTP."""
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    c_srv, c_url, c_sig, c_mv, _ = _make_map_server(
        "map:c", direct_world=("world:w", w_url, w_sig))
    b_srv, b_url, b_sig, b_mv, _ = _make_map_server(
        "map:b", sub_map=("map:c", c_url, c_sig))
    a_srv, a_url, a_sig, a_mv, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        result = _recursive_resolve(a_mv, "world:w")
        assert result is not None
        assert result["via"] == ["map:b", "map:c"]
        assert result["in_this_map"] is False
    finally:
        for s in (w_srv, c_srv, b_srv, a_srv):
            s.stop()


def test_recursive_resolve_depth_limit_direct():
    """Direct call respects MAX_DEPTH."""
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    e_srv, e_url, e_sig, e_mv, _ = _make_map_server(
        "map:e", direct_world=("world:w", w_url, w_sig))
    d_srv, d_url, d_sig, d_mv, _ = _make_map_server(
        "map:d", sub_map=("map:e", e_url, e_sig))
    c_srv, c_url, c_sig, c_mv, _ = _make_map_server(
        "map:c", sub_map=("map:d", d_url, d_sig))
    b_srv, b_url, b_sig, b_mv, _ = _make_map_server(
        "map:b", sub_map=("map:c", c_url, c_sig))
    a_srv, a_url, a_sig, a_mv, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        result = _recursive_resolve(a_mv, "world:w")
        assert result is None  # exceeds depth
    finally:
        for s in (w_srv, e_srv, d_srv, c_srv, b_srv, a_srv):
            s.stop()


# -- Annotation with recursion --

def test_annotation_chain():
    """Annotate worldline for a world reached via 2-hop chain."""
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    c_srv, c_url, c_sig, _, _ = _make_map_server(
        "map:c", direct_world=("world:w", w_url, w_sig))
    b_srv, b_url, b_sig, _, _ = _make_map_server(
        "map:b", sub_map=("map:c", c_url, c_sig))
    a_srv, a_url, a_sig, a_mv, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        # Build an individual who visited world:w
        kp = _kp()
        fed = ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=50, prng_seed_b=0xAAAA, rule=SIERPINSKI)
        session = UnifiedIndividualSession(
            individual_kp=kp,
            model=TinyRNN(n_actions=3, hidden=4,
                           n_extra_inputs=0, seed=1))
        session.enter_world_via_adapter(FederatedAdapter(), {
            "world_id": "world:w", "world": fed,
            "world_signer": fed.world_id,
            "initial_point": (200, 800)})
        # Manually override the world_id in the entry to match
        # our test world. (Hack for the test.)
        session.memory[-1]["world_id"] = "world:w"
        bundle = pack_unified_bundle(
            session, persona="t", name="t", initial_seed=1)
        from worldline import worldline_from_bundle
        summary = worldline_from_bundle(bundle, kp)

        aw = annotate_worldline(a_mv, summary, fetch_live=True)
        assert len(aw.annotated_visits) == 1
        v = aw.annotated_visits[0]
        assert v["in_this_map"] is False
        assert v["resolved_via"] == ["map:b", "map:c"]
        assert v["current_status"] == "live"
        ok, reason = verify_annotated_worldline(aw)
        assert ok, reason
    finally:
        for s in (w_srv, c_srv, b_srv, a_srv):
            s.stop()


# -- Backward compat --

def test_one_hop_annotation_via_still_works():
    """resolved_via is now a list, not a string."""
    w_srv, w_url, w_sig = _make_world_server(
        "world:w", "W")
    b_srv, b_url, b_sig, _, _ = _make_map_server(
        "map:b", direct_world=("world:w", w_url, w_sig))
    a_srv, a_url, a_sig, a_mv, _ = _make_map_server(
        "map:a", sub_map=("map:b", b_url, b_sig))
    time.sleep(0.2)
    try:
        kp = _kp()
        fed = ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=50, prng_seed_b=0xBBBB, rule=SIERPINSKI)
        session = UnifiedIndividualSession(
            individual_kp=kp,
            model=TinyRNN(n_actions=3, hidden=4,
                           n_extra_inputs=0, seed=1))
        session.enter_world_via_adapter(FederatedAdapter(), {
            "world_id": "world:w", "world": fed,
            "world_signer": fed.world_id,
            "initial_point": (200, 800)})
        session.memory[-1]["world_id"] = "world:w"
        bundle = pack_unified_bundle(
            session, persona="t", name="t", initial_seed=1)
        from worldline import worldline_from_bundle
        summary = worldline_from_bundle(bundle, kp)
        aw = annotate_worldline(a_mv, summary, fetch_live=False)
        # ONE hop → via == ["map:b"] (list of one)
        assert aw.annotated_visits[0]["resolved_via"] == ["map:b"]
    finally:
        for s in (w_srv, b_srv, a_srv):
            s.stop()


# -- Demo --

def test_demo(tmp_path):
    from map_world import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["queries"]["world:chess"]["routed"] is True
    assert audit["queries"]["world:canvas"]["routed"] is True
    assert audit["queries"]["world:garden"]["routed"] is True
    assert audit["queries"]["world:park"]["routed"] is True
    assert audit["queries"]["world:archives"]["routed"] is False
    assert audit["cycle_prevented"] is True
    assert (tmp_path / "recursive_map" /
            "recursive_map_demo.json").exists()
