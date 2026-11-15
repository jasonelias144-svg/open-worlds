import json
import time
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from individual_bundle import (
    IndividualBundle, _canonical, _hash, _did_from_kp,
)
from map_world import (
    MapRegistry, WorldPin, MultiversalMap, MapServer,
    _get_json, _post_json,
)
from lobby_server import LobbyServer
from worldline import (
    WorldVisit, WorldlineSummary, AnnotatedWorldline,
    worldline_from_bundle, verify_worldline_summary,
    annotate_worldline, verify_annotated_worldline,
    HAS_CRYPTO,
)
from signed_world_log import SignedLogWorld
from multiverse_c73 import ChessWorld
from multiverse_c81 import GrowingWorld
from multiverse_c3 import Petition, Route, Refusal
from unified_individual import (
    UnifiedIndividualSession, pack_unified_bundle,
)
from world_adapters import ChessAdapter, GrowingCanvasAdapter
from coupled_learners import TinyRNN

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


# -- Pin kind --

def test_pin_default_kind_is_world():
    p = WorldPin("w", "u", "s")
    assert p.kind == "world"


def test_pin_kind_map():
    p = WorldPin("m", "u", "s", kind="map")
    assert p.kind == "map"


def test_registry_map_pins():
    reg = MapRegistry()
    reg.add(WorldPin("w1", "u1", "s1", kind="world"))
    reg.add(WorldPin("m1", "u2", "s2", kind="map"))
    assert [p.world_id for p in reg.map_pins()] == ["m1"]


# -- Cross-federation routing --

def test_cross_map_route_happy():
    chess_kp = _kp()
    chess = SignedLogWorld(
        ChessWorld("world:chess", "C"), chess_kp)
    chess_srv = LobbyServer(chess, chess_kp, port=0)
    chess_srv.serve_in_thread()

    map_b_kp = _kp()
    reg_b = MapRegistry()
    reg_b.add(WorldPin(
        "world:chess",
        f"http://127.0.0.1:"
        f"{chess_srv._httpd.server_address[1]}",
        chess.world_signer))
    mv_b = MultiversalMap("map:b", "B", map_b_kp, reg_b)
    signed_b = SignedLogWorld(mv_b, map_b_kp)
    srv_b = MapServer(signed_b, map_b_kp, mv_b, port=0)
    srv_b.serve_in_thread()
    time.sleep(0.2)

    try:
        map_a_kp = _kp()
        reg_a = MapRegistry()
        reg_a.add(WorldPin(
            "map:b",
            f"http://127.0.0.1:"
            f"{srv_b._httpd.server_address[1]}",
            mv_b.world_signer(), kind="map"))
        mv_a = MultiversalMap("map:a", "A", map_a_kp, reg_a)
        # Petition with target in sub-map
        r = mv_a.petition(Petition(
            petitioner_token="v",
            petitioner_name="V",
            passport_admissions=(),
            message="",
            target="world:chess"))
        assert isinstance(r, Route), r
        assert r.target_manifest.entity_id == "world:chess"
    finally:
        chess_srv.stop()
        srv_b.stop()


def test_cross_map_route_unknown():
    map_a_kp = _kp()
    reg_a = MapRegistry()
    mv_a = MultiversalMap("map:a", "A", map_a_kp, reg_a)
    r = mv_a.petition(Petition(
        petitioner_token="v", petitioner_name="V",
        passport_admissions=(), message="",
        target="world:anywhere"))
    assert isinstance(r, Refusal)


def test_cross_map_route_unreachable_submap():
    """Sub-map is offline — A can't resolve, returns Refusal."""
    map_a_kp = _kp()
    reg_a = MapRegistry()
    reg_a.add(WorldPin(
        "map:ghost", "http://127.0.0.1:1",
        "did:key:" + "00" * 32, kind="map"))
    mv_a = MultiversalMap("map:a", "A", map_a_kp, reg_a)
    r = mv_a.petition(Petition(
        petitioner_token="v", petitioner_name="V",
        passport_admissions=(), message="",
        target="world:chess"))
    assert isinstance(r, Refusal)


# -- Worldline --

def test_worldline_summary_signs():
    bundle = IndividualBundle(
        manifest={"kind": "x", "individual_id": "did:key:" + "00" * 32,
                   "memory_entries": 0, "memory_root": _hash(""),
                   "sig": "00" * 64},
        memory=[], weights={},
        initial_weights=None, observations=[],
        ancestry=[], checkpoint_weights=None)
    kp = _kp()
    # Can't sign with mismatched kp
    with pytest.raises(ValueError):
        worldline_from_bundle(bundle, kp)


def test_worldline_round_trip():
    """Build from a real bundle, verify the summary."""
    chess_kp = _kp()
    chess_signed = SignedLogWorld(
        ChessWorld("world:chess", "C"), chess_kp)
    chess_srv = LobbyServer(chess_signed, chess_kp, port=0)
    chess_srv.serve_in_thread()
    time.sleep(0.15)
    try:
        chess_url = (f"http://127.0.0.1:"
                      f"{chess_srv._httpd.server_address[1]}")
        individual_kp = _kp()
        session = UnifiedIndividualSession(
            individual_kp=individual_kp,
            model=TinyRNN(n_actions=3, hidden=4,
                           n_extra_inputs=0, seed=42))
        session.enter_world_via_adapter(ChessAdapter(), {
            "world_id": "world:chess",
            "world_url": chess_url,
            "world_signer": chess_signed.world_signer,
            "seat": "white",
            "display_name": "V",
        })
        bundle = pack_unified_bundle(
            session, persona="v", name="v", initial_seed=42)
        summary = worldline_from_bundle(bundle, individual_kp)
        ok, reason = verify_worldline_summary(summary)
        assert ok, reason
        assert len(summary.visits) == 1
        assert summary.visits[0].world_id == "world:chess"
        assert summary.visits[0].tier == "chess"
    finally:
        chess_srv.stop()


def test_worldline_tampered():
    chess_kp = _kp()
    chess_signed = SignedLogWorld(
        ChessWorld("world:chess", "C"), chess_kp)
    chess_srv = LobbyServer(chess_signed, chess_kp, port=0)
    chess_srv.serve_in_thread()
    time.sleep(0.15)
    try:
        chess_url = (f"http://127.0.0.1:"
                      f"{chess_srv._httpd.server_address[1]}")
        individual_kp = _kp()
        session = UnifiedIndividualSession(
            individual_kp=individual_kp,
            model=TinyRNN(n_actions=3, hidden=4,
                           n_extra_inputs=0, seed=42))
        session.enter_world_via_adapter(ChessAdapter(), {
            "world_id": "world:chess",
            "world_url": chess_url,
            "world_signer": chess_signed.world_signer,
            "seat": "white",
            "display_name": "V"})
        bundle = pack_unified_bundle(
            session, persona="v", name="v", initial_seed=42)
        summary = worldline_from_bundle(bundle, individual_kp)
        # Tamper
        tampered = WorldlineSummary(
            individual_id=summary.individual_id,
            visits=(WorldVisit(
                world_id="world:forged", tier="chess",
                first_memory_index=0, entered_at_ts=""),),
            ts=summary.ts, sig=summary.sig)
        ok, _ = verify_worldline_summary(tampered)
        assert not ok
    finally:
        chess_srv.stop()


def test_annotated_worldline_verifies():
    chess_kp = _kp()
    chess_signed = SignedLogWorld(
        ChessWorld("world:chess", "C"), chess_kp)
    chess_srv = LobbyServer(chess_signed, chess_kp, port=0)
    chess_srv.serve_in_thread()
    time.sleep(0.15)
    try:
        chess_url = (f"http://127.0.0.1:"
                      f"{chess_srv._httpd.server_address[1]}")
        individual_kp = _kp()
        session = UnifiedIndividualSession(
            individual_kp=individual_kp,
            model=TinyRNN(n_actions=3, hidden=4,
                           n_extra_inputs=0, seed=42))
        session.enter_world_via_adapter(ChessAdapter(), {
            "world_id": "world:chess",
            "world_url": chess_url,
            "world_signer": chess_signed.world_signer,
            "seat": "white",
            "display_name": "V"})
        bundle = pack_unified_bundle(
            session, persona="v", name="v", initial_seed=42)
        summary = worldline_from_bundle(bundle, individual_kp)

        map_kp = _kp()
        reg = MapRegistry()
        reg.add(WorldPin(
            "world:chess", chess_url,
            chess_signed.world_signer, cluster="Games"))
        mv = MultiversalMap("map:m", "M", map_kp, reg)
        aw = annotate_worldline(mv, summary, fetch_live=True)
        ok, reason = verify_annotated_worldline(
            aw, expected_map=mv.world_signer(),
            expected_individual=bundle.individual_id)
        assert ok, reason
        assert aw.annotated_visits[0]["current_status"] == "live"
        assert aw.annotated_visits[0]["in_this_map"] is True
        assert aw.annotated_visits[0]["cluster"] == "Games"
    finally:
        chess_srv.stop()


def test_annotated_worldline_altered_annotation():
    chess_kp = _kp()
    chess_signed = SignedLogWorld(
        ChessWorld("world:chess", "C"), chess_kp)
    chess_srv = LobbyServer(chess_signed, chess_kp, port=0)
    chess_srv.serve_in_thread()
    time.sleep(0.15)
    try:
        chess_url = (f"http://127.0.0.1:"
                      f"{chess_srv._httpd.server_address[1]}")
        individual_kp = _kp()
        session = UnifiedIndividualSession(
            individual_kp=individual_kp,
            model=TinyRNN(n_actions=3, hidden=4,
                           n_extra_inputs=0, seed=42))
        session.enter_world_via_adapter(ChessAdapter(), {
            "world_id": "world:chess",
            "world_url": chess_url,
            "world_signer": chess_signed.world_signer,
            "seat": "white", "display_name": "V"})
        bundle = pack_unified_bundle(
            session, persona="v", name="v", initial_seed=42)
        summary = worldline_from_bundle(bundle, individual_kp)
        map_kp = _kp()
        reg = MapRegistry()
        reg.add(WorldPin(
            "world:chess", chess_url,
            chess_signed.world_signer, cluster="Games"))
        mv = MultiversalMap("map:m", "M", map_kp, reg)
        aw = annotate_worldline(mv, summary, fetch_live=False)
        # Tamper: change cluster in annotation
        tampered = AnnotatedWorldline(
            individual_id=aw.individual_id,
            map_id=aw.map_id,
            annotated_visits=tuple(
                {**dict(v), "cluster": "Forged"}
                for v in aw.annotated_visits),
            original_summary=aw.original_summary,
            ts=aw.ts, sig=aw.sig)
        ok, _ = verify_annotated_worldline(tampered)
        assert not ok
    finally:
        chess_srv.stop()


def test_annotated_worldline_altered_summary():
    chess_kp = _kp()
    chess_signed = SignedLogWorld(
        ChessWorld("world:chess", "C"), chess_kp)
    chess_srv = LobbyServer(chess_signed, chess_kp, port=0)
    chess_srv.serve_in_thread()
    time.sleep(0.15)
    try:
        chess_url = (f"http://127.0.0.1:"
                      f"{chess_srv._httpd.server_address[1]}")
        individual_kp = _kp()
        session = UnifiedIndividualSession(
            individual_kp=individual_kp,
            model=TinyRNN(n_actions=3, hidden=4,
                           n_extra_inputs=0, seed=42))
        session.enter_world_via_adapter(ChessAdapter(), {
            "world_id": "world:chess",
            "world_url": chess_url,
            "world_signer": chess_signed.world_signer,
            "seat": "white", "display_name": "V"})
        bundle = pack_unified_bundle(
            session, persona="v", name="v", initial_seed=42)
        summary = worldline_from_bundle(bundle, individual_kp)
        map_kp = _kp()
        reg = MapRegistry()
        reg.add(WorldPin(
            "world:chess", chess_url,
            chess_signed.world_signer, cluster="Games"))
        mv = MultiversalMap("map:m", "M", map_kp, reg)
        aw = annotate_worldline(mv, summary, fetch_live=False)
        # Tamper: alter world_id in original_summary
        tampered_orig = {
            **aw.original_summary,
            "visits": [
                {**v, "world_id": "world:forged"}
                for v in aw.original_summary["visits"]
            ]}
        tampered = AnnotatedWorldline(
            individual_id=aw.individual_id,
            map_id=aw.map_id,
            annotated_visits=aw.annotated_visits,
            original_summary=tampered_orig,
            ts=aw.ts, sig=aw.sig)
        ok, _ = verify_annotated_worldline(tampered)
        assert not ok
    finally:
        chess_srv.stop()


def test_annotated_worldline_cross_map_visit():
    """Individual visits a world in federation B; map A annotates
    it as resolved_via map B."""
    chess_kp = _kp()
    chess_signed = SignedLogWorld(
        ChessWorld("world:chess", "C"), chess_kp)
    chess_srv = LobbyServer(chess_signed, chess_kp, port=0)
    chess_srv.serve_in_thread()
    time.sleep(0.15)
    try:
        chess_url = (f"http://127.0.0.1:"
                      f"{chess_srv._httpd.server_address[1]}")
        map_b_kp = _kp()
        reg_b = MapRegistry()
        reg_b.add(WorldPin(
            "world:chess", chess_url,
            chess_signed.world_signer, cluster="Games"))
        mv_b = MultiversalMap("map:b", "B", map_b_kp, reg_b)
        signed_b = SignedLogWorld(mv_b, map_b_kp)
        srv_b = MapServer(signed_b, map_b_kp, mv_b, port=0)
        srv_b.serve_in_thread()
        time.sleep(0.15)
        try:
            map_b_url = (f"http://127.0.0.1:"
                          f"{srv_b._httpd.server_address[1]}")
            map_a_kp = _kp()
            reg_a = MapRegistry()
            reg_a.add(WorldPin(
                "map:b", map_b_url, mv_b.world_signer(),
                kind="map"))
            mv_a = MultiversalMap("map:a", "A", map_a_kp, reg_a)

            individual_kp = _kp()
            session = UnifiedIndividualSession(
                individual_kp=individual_kp,
                model=TinyRNN(n_actions=3, hidden=4,
                               n_extra_inputs=0, seed=42))
            session.enter_world_via_adapter(ChessAdapter(), {
                "world_id": "world:chess",
                "world_url": chess_url,
                "world_signer": chess_signed.world_signer,
                "seat": "white", "display_name": "V"})
            bundle = pack_unified_bundle(
                session, persona="v", name="v", initial_seed=42)
            summary = worldline_from_bundle(bundle, individual_kp)

            aw = annotate_worldline(mv_a, summary, fetch_live=False)
            assert aw.annotated_visits[0]["in_this_map"] is False
            assert aw.annotated_visits[0]["resolved_via"] == "map:b"
            assert aw.annotated_visits[0]["cluster"] == "Games"
            v = verify_annotated_worldline(aw)
            assert v[0], v[1]
        finally:
            srv_b.stop()
    finally:
        chess_srv.stop()


# -- Demo --

def test_demo(tmp_path):
    from map_world import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["cross_federation"]["direct_route_ok"] is True
    assert audit["cross_federation"]["via_submap_route_ok"] is True
    assert audit["cross_federation"]["unknown_target_refused"] is True
    assert audit["worldline"]["verified"] is True
    assert audit["tampering"]["altered_annotation_detected"] is True
    assert audit["tampering"]["altered_summary_detected"] is True
    # Two visits, one direct (chess), one via sub-map (canvas)
    assert len(audit["worldline"]["visits"]) == 2
    assert any(v["resolved_via"] is not None
                for v in audit["worldline"]["visits"])
    assert (tmp_path / "cross_federation_map" /
            "cross_federation_demo.json").exists()
