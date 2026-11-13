import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c79 import ChainVerdict
from multiverse_c81 import (
    GROWTH_EVENT_TYPES,
    GrowthEvent, sign_growth_event, verify_growth_event,
    _plots_overlap, _plots_edge_adjacent,
    reconstruct_plots_from_events, reconstruct_at,
    extent_bbox, extent_area, render_map,
    verify_growth_chain, GrowingWorld, fetch_growth_events,
    demo,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# ---------------------------------------------------------------------
# GrowthEvent
# ---------------------------------------------------------------------

def _mk_event(kp, event_type="claimed", plot_id="plot:0001",
              prior=None, width=3, height=3, purpose="x"):
    return sign_growth_event(
        event_type=event_type, plot_id=plot_id,
        owner_token="alice", owner_name="Alice",
        x=4, y=0, width=width, height=height,
        purpose=purpose, prior_event_hash=prior,
        signer_id="world:c", signer_kp=kp)


def test_event_sign_verify():
    print("=== GrowthEvent: sign/verify ===")
    kp = KeyPair.generate()
    ev = _mk_event(kp)
    assert verify_growth_event(ev, kp.public_key_hex())


def test_event_wrong_key():
    print("=== GrowthEvent: wrong key ===")
    kp = KeyPair.generate()
    ev = _mk_event(kp)
    wrong = KeyPair.generate()
    assert not verify_growth_event(ev, wrong.public_key_hex())


def test_event_rejects_bad_type():
    print("=== GrowthEvent: bad type rejected ===")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        _mk_event(kp, event_type="bogus")


def test_event_rejects_bad_size():
    print("=== GrowthEvent: bad width/height rejected ===")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        _mk_event(kp, width=0)
    with pytest.raises(ValueError):
        _mk_event(kp, height=25)


# ---------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------

def test_overlap():
    print("=== _plots_overlap ===")
    assert _plots_overlap((0, 0, 4, 4), (2, 2, 4, 4))
    assert _plots_overlap((0, 0, 4, 4), (3, 3, 1, 1))
    assert not _plots_overlap((0, 0, 4, 4), (4, 0, 4, 4))
    assert not _plots_overlap((0, 0, 4, 4), (0, 4, 4, 4))
    assert not _plots_overlap((0, 0, 4, 4), (4, 4, 4, 4))


def test_edge_adjacent():
    print("=== _plots_edge_adjacent ===")
    assert _plots_edge_adjacent((0, 0, 4, 4), (4, 0, 3, 3))
    assert _plots_edge_adjacent((4, 0, 3, 3), (0, 0, 4, 4))
    assert _plots_edge_adjacent((0, 0, 4, 4), (0, 4, 3, 3))
    assert not _plots_edge_adjacent((0, 0, 4, 4), (4, 4, 3, 3))
    # Different heights, still adjacent on a shared edge
    assert _plots_edge_adjacent((0, 0, 4, 4), (4, 1, 3, 2))


# ---------------------------------------------------------------------
# Reconstruction
# ---------------------------------------------------------------------

def test_reconstruct_current():
    print("=== reconstruct_plots_from_events ===")
    kp = KeyPair.generate()
    e1 = _mk_event(kp, plot_id="plot:a")
    e2 = _mk_event(kp, plot_id="plot:b")
    state = reconstruct_plots_from_events([e1, e2])
    assert set(state) == {"plot:a", "plot:b"}


def test_reconstruct_with_retire():
    print("=== reconstruct: claim + retire ===")
    kp = KeyPair.generate()
    e1 = _mk_event(kp, plot_id="plot:a")
    e2 = _mk_event(kp, plot_id="plot:a",
                    event_type="retired",
                    prior=e1.event_hash())
    state = reconstruct_plots_from_events([e1, e2])
    assert "plot:a" not in state


def test_reconstruct_at_historical():
    print("=== reconstruct_at: historical ===")
    kp = KeyPair.generate()
    e1 = _mk_event(kp, plot_id="plot:a")
    e2 = _mk_event(kp, plot_id="plot:a",
                    event_type="retired",
                    prior=e1.event_hash())
    historical = reconstruct_at([e1, e2], e1.event_hash())
    assert "plot:a" in historical


# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------

def test_render_map_empty():
    print("=== render_map: empty ===")
    assert render_map({}) == "(empty canvas)"


def test_render_map_single():
    print("=== render_map: single seed ===")
    active = {"plot:seed": {
        "plot_id": "plot:seed",
        "owner_token": "w", "owner_name": "W",
        "x": 0, "y": 0, "width": 2, "height": 2,
        "purpose": "seed"}}
    text = render_map(active)
    assert text.count("S") == 4


# ---------------------------------------------------------------------
# Chain verification
# ---------------------------------------------------------------------

def test_chain_happy():
    print("=== verify_growth_chain: happy ===")
    kp = KeyPair.generate()
    seed = _mk_event(kp, plot_id="plot:seed")
    claim = _mk_event(kp, plot_id="plot:0001")
    v = verify_growth_chain(
        [seed, claim], kp.public_key_hex())
    assert v.valid


def test_chain_broken_link():
    print("=== verify_growth_chain: broken link ===")
    kp = KeyPair.generate()
    seed = _mk_event(kp, plot_id="plot:seed")
    e1 = _mk_event(kp, plot_id="plot:0001")
    e2 = _mk_event(kp, plot_id="plot:0001",
                    event_type="retired",
                    prior="00" * 32)
    v = verify_growth_chain(
        [seed, e1, e2], kp.public_key_hex())
    assert not v.valid


# ---------------------------------------------------------------------
# GrowingWorld
# ---------------------------------------------------------------------

def test_world_seed_exists():
    print("=== GrowingWorld: seed auto-created ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    assert "plot:seed" in w.current_plots()


def test_world_claim_accepted():
    print("=== GrowingWorld: contiguous claim accepted ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    w.petition(Petition(
        petitioner_token=a.token, petitioner_name=a.name,
        passport_admissions=(), message=""))
    r = w.act(Act(actor_token=a.token, type="canvas.claim",
                  payload={"x": 4, "y": 0, "width": 3,
                            "height": 3, "purpose": "studio"}))
    assert isinstance(r, Ack)
    assert "plot:0001" in w.current_plots()


def test_world_distant_claim_refused():
    print("=== GrowingWorld: non-contiguous claim refused ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    w.petition(Petition(
        petitioner_token=a.token, petitioner_name=a.name,
        passport_admissions=(), message=""))
    r = w.act(Act(actor_token=a.token, type="canvas.claim",
                  payload={"x": 100, "y": 100, "width": 3,
                            "height": 3, "purpose": "studio"}))
    assert isinstance(r, Refusal)
    assert "contiguous" in r.reason.lower()


def test_world_overlap_refused():
    print("=== GrowingWorld: overlapping claim refused ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    b = create_identity("Bob")
    for who in (a, b):
        w.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(), message=""))
    # Alice claims a spot adjacent to seed
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 4, "y": 0, "width": 3,
                        "height": 3, "purpose": "studio"}))
    # Bob tries to overlap
    r = w.act(Act(actor_token=b.token, type="canvas.claim",
                  payload={"x": 5, "y": 0, "width": 2,
                            "height": 2, "purpose": "gallery"}))
    assert isinstance(r, Refusal)
    assert "overlap" in r.reason.lower()


def test_world_retire_happy():
    print("=== GrowingWorld: owner retire ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    w.petition(Petition(
        petitioner_token=a.token, petitioner_name=a.name,
        passport_admissions=(), message=""))
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 4, "y": 0, "width": 3,
                        "height": 3, "purpose": "studio"}))
    r = w.act(Act(actor_token=a.token, type="canvas.retire",
                  payload={"plot_id": "plot:0001"}))
    assert isinstance(r, Ack)
    assert "plot:0001" not in w.current_plots()


def test_world_retire_by_other_refused():
    print("=== GrowingWorld: non-owner retire refused ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    b = create_identity("Bob")
    for who in (a, b):
        w.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(), message=""))
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 4, "y": 0, "width": 3,
                        "height": 3, "purpose": "studio"}))
    r = w.act(Act(actor_token=b.token, type="canvas.retire",
                  payload={"plot_id": "plot:0001"}))
    assert isinstance(r, Refusal)
    assert "owner" in r.reason.lower()


def test_world_retire_seed_refused():
    print("=== GrowingWorld: cannot retire seed ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    w.petition(Petition(
        petitioner_token=a.token, petitioner_name=a.name,
        passport_admissions=(), message=""))
    r = w.act(Act(actor_token=a.token, type="canvas.retire",
                  payload={"plot_id": "plot:seed"}))
    assert isinstance(r, Refusal)
    assert "seed" in r.reason.lower()


# ---------------------------------------------------------------------
# Chain verification on live world
# ---------------------------------------------------------------------

def test_full_chain_verifies():
    print("=== verify_growth_chain: live world ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    b = create_identity("Bob")
    for who in (a, b):
        w.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(), message=""))
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 4, "y": 0, "width": 3,
                        "height": 3, "purpose": "studio"}))
    w.act(Act(actor_token=b.token, type="canvas.claim",
              payload={"x": 7, "y": 0, "width": 3,
                        "height": 3, "purpose": "gallery"}))
    w.act(Act(actor_token=a.token, type="canvas.retire",
              payload={"plot_id": "plot:0001"}))
    events = w.events()
    v = verify_growth_chain(
        events, kp.public_key_hex())
    assert v.valid


# ---------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------

def test_demo(tmp_path):
    print("=== Demo: full lifecycle ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["chain_valid"] is True
    assert audit["retire_ok"] is True
    assert "plot:seed" in audit["current_plots"]
    assert "plot:0001" not in audit["current_plots"]
    assert "plot:0002" in audit["current_plots"]
    assert "plot:0003" in audit["current_plots"]
    assert audit["historical_area"] > audit["current_area"]
    assert (tmp_path / "growing_world" /
            "growing_world_demo.json").exists()
