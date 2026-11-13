import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c81 import GrowingWorld
from multiverse_c82 import (
    REFUSAL_KINDS, _classify_refusal,
    GrowthObservation,
    MockGrowthModel, GrowthModelBackend,
    RuleProposal, verify_rule_proposal,
    ObservingGrowingWorld, GrowingWorldCurator,
    fetch_rule_proposals,
    demo,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# ---------------------------------------------------------------------
# Refusal classification
# ---------------------------------------------------------------------

def test_classify_refusal():
    print("=== _classify_refusal ===")
    assert _classify_refusal(
        "width must be in [1, 20]") == "size_limit"
    assert _classify_refusal(
        "height must be in [1, 20]") == "size_limit"
    assert _classify_refusal(
        "overlaps plot plot:0001") == "overlap"
    assert _classify_refusal(
        "not contiguous with the current extent") == "contiguity"
    assert _classify_refusal(
        "only the owner can retire") == "owner"
    assert _classify_refusal("something else") == "other"


# ---------------------------------------------------------------------
# MockGrowthModel triggers
# ---------------------------------------------------------------------

def test_mock_trigger_size_limit():
    print("=== MockGrowthModel: size_limit trigger ===")
    m = MockGrowthModel()
    p = m.generate_growth({
        "refusals_by_kind": {"size_limit": 2,
                              "overlap": 0, "contiguity": 0,
                              "owner": 0, "other": 0},
        "plot_count": 2, "mean_area": 10,
    })
    assert p is not None
    assert p["proposal_type"] == "raise_size_limit"
    assert p["suggested_rule"]["max_width"] == 40


def test_mock_trigger_overlap():
    print("=== MockGrowthModel: overlap trigger ===")
    m = MockGrowthModel()
    p = m.generate_growth({
        "refusals_by_kind": {"size_limit": 0,
                              "overlap": 3, "contiguity": 0,
                              "owner": 0, "other": 0},
        "plot_count": 2, "mean_area": 10,
    })
    assert p is not None
    assert p["proposal_type"] == "zoning_assistance"


def test_mock_trigger_fragmentation():
    print("=== MockGrowthModel: fragmentation trigger ===")
    m = MockGrowthModel()
    p = m.generate_growth({
        "refusals_by_kind": {k: 0 for k in REFUSAL_KINDS},
        "plot_count": 5, "mean_area": 4.0,
    })
    assert p is not None
    assert p["proposal_type"] == "growth_incentive"


def test_mock_no_trigger():
    print("=== MockGrowthModel: no trigger → None ===")
    m = MockGrowthModel()
    p = m.generate_growth({
        "refusals_by_kind": {k: 0 for k in REFUSAL_KINDS},
        "plot_count": 2, "mean_area": 20,
    })
    assert p is None


# ---------------------------------------------------------------------
# RuleProposal
# ---------------------------------------------------------------------

def _mk_proposal(kp):
    payload = {
        "kind": "rule_proposal",
        "proposal_id": "test-id",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "world_id": "world:c",
        "observation_summary": {"plot_count": 1},
        "proposal_type": "raise_size_limit",
        "title": "T",
        "rationale": "R",
        "suggested_rule": {"max_width": 40},
        "signer_id": "world:c",
        "signer_public_key": kp.public_key_hex(),
    }
    from multiverse_c13 import canonical_bytes
    sig = kp.sign(canonical_bytes(payload)).hex()
    return RuleProposal(
        proposal_id="test-id",
        timestamp="2024-01-01T00:00:00+00:00",
        world_id="world:c",
        observation_summary={"plot_count": 1},
        proposal_type="raise_size_limit",
        title="T",
        rationale="R",
        suggested_rule={"max_width": 40},
        signer_id="world:c",
        signer_public_key=kp.public_key_hex(),
        signature=sig,
    )


def test_proposal_sign_verify():
    print("=== RuleProposal: sign/verify ===")
    kp = KeyPair.generate()
    p = _mk_proposal(kp)
    assert verify_rule_proposal(p, kp.public_key_hex())


def test_proposal_wrong_key():
    print("=== RuleProposal: wrong key → False ===")
    kp = KeyPair.generate()
    p = _mk_proposal(kp)
    wrong = KeyPair.generate()
    assert not verify_rule_proposal(p, wrong.public_key_hex())


def test_proposal_json_roundtrip():
    print("=== RuleProposal: JSON roundtrip ===")
    kp = KeyPair.generate()
    p = _mk_proposal(kp)
    p2 = RuleProposal.from_dict(p.to_dict())
    assert verify_rule_proposal(p2, kp.public_key_hex())


def test_verify_never_raises():
    print("=== verify_rule_proposal: never raises ===")
    assert not verify_rule_proposal(None)  # type: ignore
    assert not verify_rule_proposal("not a proposal")  # type: ignore
    assert not verify_rule_proposal({})  # type: ignore


# ---------------------------------------------------------------------
# ObservingGrowingWorld
# ---------------------------------------------------------------------

def test_world_records_proposals():
    print("=== ObservingGrowingWorld: record and list ===")
    kp = KeyPair.generate()
    w = ObservingGrowingWorld("world:c", "C", kp)
    p = _mk_proposal(kp)
    w.record_proposal(p.to_dict())
    proposals = w.proposals()
    assert len(proposals) == 1
    assert proposals[0]["proposal_id"] == "test-id"


def test_world_still_grows():
    """Recording proposals does not affect the canvas."""
    print("=== ObservingGrowingWorld: growth unaffected ===")
    kp = KeyPair.generate()
    w = ObservingGrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    w.petition(Petition(
        petitioner_token=a.token, petitioner_name=a.name,
        passport_admissions=(), message=""))
    p = _mk_proposal(kp)
    w.record_proposal(p.to_dict())
    before = w.current_extent_bbox()
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 4, "y": 0, "width": 2,
                        "height": 2, "purpose": "studio"}))
    after = w.current_extent_bbox()
    assert before != after  # world still grows


# ---------------------------------------------------------------------
# GrowingWorldCurator
# ---------------------------------------------------------------------

def _setup_world():
    kp = KeyPair.generate()
    w = ObservingGrowingWorld("world:c", "C", kp)
    a = create_identity("Alice")
    b = create_identity("Bob")
    for who in (a, b):
        w.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(), message=""))
    return w, kp, a, b


def test_observe_growth_empty():
    print("=== observe_growth: empty (seed only) ===")
    w, kp, _, _ = _setup_world()
    c = GrowingWorldCurator(w, kp, MockGrowthModel())
    obs = c.observe_growth()
    assert obs.plot_count == 1  # seed
    assert obs.refusals_total == 0


def test_observe_growth_with_claims():
    print("=== observe_growth: after a claim ===")
    w, kp, a, _ = _setup_world()
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 4, "y": 0, "width": 3,
                        "height": 3, "purpose": "studio"}))
    c = GrowingWorldCurator(w, kp, MockGrowthModel())
    obs = c.observe_growth()
    assert obs.plot_count == 2
    assert obs.purposes.get("studio") == 1
    assert obs.owner_count == 2  # seed owner + Alice


def test_observe_growth_refusals_classified():
    print("=== observe_growth: refusals classified ===")
    w, kp, a, _ = _setup_world()
    # Too-big claim
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 0, "y": 0, "width": 30,
                        "height": 30, "purpose": "too-big"}))
    # Non-contiguous claim
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 100, "y": 100, "width": 2,
                        "height": 2, "purpose": "far"}))
    c = GrowingWorldCurator(w, kp, MockGrowthModel())
    obs = c.observe_growth()
    assert obs.refusals_by_kind["size_limit"] == 1
    assert obs.refusals_by_kind["contiguity"] == 1


def test_propose_none_on_empty():
    print("=== propose: empty canvas → None ===")
    w, kp, _, _ = _setup_world()
    c = GrowingWorldCurator(w, kp, MockGrowthModel())
    p = c.observe_and_propose_growth()
    # No refusals, one plot (seed) → no trigger
    assert p is None


def test_propose_size_limit():
    print("=== propose: size_limit refusal triggers ===")
    w, kp, a, _ = _setup_world()
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 0, "y": 0, "width": 30,
                        "height": 30, "purpose": "too-big"}))
    c = GrowingWorldCurator(w, kp, MockGrowthModel())
    p = c.observe_and_propose_growth()
    assert p is not None
    assert p.proposal_type == "raise_size_limit"
    assert verify_rule_proposal(p, kp.public_key_hex())


def test_proposal_does_not_modify_world():
    """KEY: proposals are recommendations. World unchanged."""
    print("=== proposal: does not modify the world ===")
    w, kp, a, _ = _setup_world()
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 0, "y": 0, "width": 30,
                        "height": 30, "purpose": "too-big"}))
    before_bbox = w.current_extent_bbox()
    before_plots = set(w.current_plots().keys())
    c = GrowingWorldCurator(w, kp, MockGrowthModel())
    p = c.observe_and_propose_growth()
    assert p is not None  # proposal happened
    after_bbox = w.current_extent_bbox()
    after_plots = set(w.current_plots().keys())
    assert before_bbox == after_bbox
    assert before_plots == after_plots
    # But the proposal IS in the log
    assert len(w.proposals()) == 1


def test_proposal_no_op_on_non_growth_model():
    print("=== propose: no growth model → None ===")
    w, kp, a, _ = _setup_world()
    w.act(Act(actor_token=a.token, type="canvas.claim",
              payload={"x": 0, "y": 0, "width": 30,
                        "height": 30, "purpose": "too-big"}))
    class NonGrowthModel:
        def generate(self, summary):
            return None
        def model_id(self):
            return "non-growth"
    c = GrowingWorldCurator(w, kp, NonGrowthModel())
    p = c.observe_and_propose_growth()
    assert p is None


# ---------------------------------------------------------------------
# fetch_rule_proposals
# ---------------------------------------------------------------------

def test_fetch_unreachable():
    print("=== fetch_rule_proposals: unreachable → [] ===")
    assert fetch_rule_proposals("http://127.0.0.1:1") == []


def test_fetch_over_http():
    print("=== fetch_rule_proposals: via /log ===")
    kp = KeyPair.generate()
    w = ObservingGrowingWorld("world:c", "C", kp)
    server = WorldProtocolServer(w, port=0)
    server.serve_in_thread()
    time.sleep(0.2)
    url = f"http://127.0.0.1:{server._httpd.server_address[1]}"
    try:
        p = _mk_proposal(kp)
        w.record_proposal(p.to_dict())
        fetched = fetch_rule_proposals(url)
        assert len(fetched) == 1
        assert verify_rule_proposal(
            fetched[0], kp.public_key_hex())
    finally:
        server.stop()


# ---------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------

def test_demo(tmp_path):
    print("=== Demo: three scenarios ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["scenario_a"]["proposal_generated"] is False
    assert audit["scenario_b"]["proposal_generated"] is True
    assert audit["scenario_b"]["no_auto_apply"] is True
    assert audit["scenario_c"]["proposal_generated"] is True
    assert audit["scenario_d"]["fetched_count"] == 1
    assert audit["scenario_d"]["verified_count"] == 1
    assert audit["scenario_d"]["in_process_count"] == 1
    assert (tmp_path / "observing_curator" /
            "observing_curator_demo.json").exists()
