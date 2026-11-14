import json
import pytest
from individual_bundle import (
    IndividualBundle, serialize_weights, _merkle_root, _hash,
    _canonical,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_basic, verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
    verify_federated_spawn_ancestry,
)
from multi_generation_lineage import (
    verify_lineage_chain_full, lineage_report, render_chain,
    demo, HAS_CRYPTO,
)
from world_agent_coupling import ScriptedWorld
from coupled_learners import TinyRNN, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(k_b=0, prng=0xCAFE):
    return ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)


def _build_chain(gen0_steps=20, gen1_steps=15, gen2_steps=10):
    """Build a 3-generation chain: grandparent → parent → child.
    Each generation lives in one world then spawns."""
    # Gen 0
    gp_kp = _kp()
    gp_model = TinyRNN(n_extra_inputs=0, seed=42)
    gp_mem = []
    w = _world(k_b=0, prng=0xAAAA)
    s = FederatedSession(
        individual_kp=gp_kp, model=gp_model,
        world=w, initial_point=(200, 800),
        memory=gp_mem, rule=SIERPINSKI)
    for _ in range(gen0_steps):
        s.step()
    gp_sessions = [s]
    # Spawn gen1
    p_kp, p_model, spawn0, w0 = spawn_federated_child(
        parent_session=s, child_persona="p",
        child_initial_seed=200)
    s.step()  # one post-spawn step so spawn record isn't last
    gp_bundle = pack_federated_bundle(
        individual_kp=gp_kp, model=gp_model,
        sessions=gp_sessions, memory=gp_mem,
        persona="gp", initial_seed=42, name="grandparent")

    # Gen 1
    p_mem = []
    w1 = _world(k_b=25, prng=0xDDDD)
    s1 = FederatedSession(
        individual_kp=p_kp, model=p_model,
        world=w1, initial_point=(250, 750),
        memory=p_mem, rule=SIERPINSKI)
    for _ in range(gen1_steps):
        s1.step()
    p_sessions = [s1]
    # Spawn gen2
    c_kp, c_model, spawn1, w1_parent = spawn_federated_child(
        parent_session=s1, child_persona="c",
        child_initial_seed=300)
    s1.step()
    p_bundle = pack_federated_child(
        child_kp=p_kp, child_model=p_model,
        child_sessions=p_sessions, child_memory=p_mem,
        child_persona="p", child_initial_seed=200,
        parent_bundle=gp_bundle, spawn_record=spawn0,
        inherited_weights=w0, name="parent")

    # Gen 2
    c_mem = []
    w2 = _world(k_b=50, prng=0x1234)
    s2 = FederatedSession(
        individual_kp=c_kp, model=c_model,
        world=w2, initial_point=(300, 700),
        memory=c_mem, rule=SIERPINSKI)
    for _ in range(gen2_steps):
        s2.step()
    c_sessions = [s2]
    c_bundle = pack_federated_child(
        child_kp=c_kp, child_model=c_model,
        child_sessions=c_sessions, child_memory=c_mem,
        child_persona="c", child_initial_seed=300,
        parent_bundle=p_bundle, spawn_record=spawn1,
        inherited_weights=w1_parent, name="child")

    return (gp_bundle, p_bundle, c_bundle, gp_kp, p_kp, c_kp)


# -- Chain basics --

def test_chain_of_three_verifies():
    gp, p, c, *_ = _build_chain()
    ok, reason = verify_lineage_chain_full([gp, p, c])
    assert ok, reason


def test_chain_of_one_verifies():
    gp, *_ = _build_chain()
    ok, reason = verify_lineage_chain_full([gp])
    assert ok, reason


def test_chain_of_two_verifies():
    gp, p, *_ = _build_chain()
    ok, reason = verify_lineage_chain_full([gp, p])
    assert ok, reason


def test_empty_chain_fails():
    ok, reason = verify_lineage_chain_full([])
    assert not ok
    assert "empty" in reason.lower()


def test_non_bundle_fails():
    gp, p, c, *_ = _build_chain()
    ok, _ = verify_lineage_chain_full([gp, "not a bundle"])
    assert not ok


# -- Report --

def test_report_aggregate():
    gp, p, c, *_ = _build_chain()
    report = lineage_report([gp, p, c])
    assert report["aggregate"] is True
    assert report["chain_length"] == 3
    assert len(report["bundles"]) == 3
    assert len(report["links"]) == 2
    assert all(b["basic"] for b in report["bundles"])
    assert all(b["full"] for b in report["bundles"])
    assert all(l["verified"] for l in report["links"])


def test_render_chain():
    gp, p, c, *_ = _build_chain()
    text = render_chain([gp, p, c])
    assert "Gen 0" in text
    assert "Gen 1" in text
    assert "Gen 2" in text
    assert "(none — origin)" in text  # grandparent


# -- Tampering --

def test_tampered_parent_spawn_breaks_chain():
    gp, p, c, gp_kp, p_kp, _ = _build_chain()
    # Tamper parent's spawn record: change child_id
    for i, rec in enumerate(p.memory):
        if rec.get("type") == "spawn":
            body = {k: v for k, v in rec.items() if k != "sig"}
            body["child_id"] = "did:key:" + "00" * 32
            sig = p_kp.sign(_canonical(body)).hex()
            p.memory[i] = {**body, "sig": sig}
            break
    p.manifest = dict(p.manifest)
    p.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in p.memory])
    body = {k: v for k, v in p.manifest.items() if k != "sig"}
    p.manifest["sig"] = p_kp.sign(_canonical(body)).hex()
    # Parent passes its own basic+full (spawns skipped in full)
    assert verify_federated_basic(p)[0]
    assert verify_federated_full(p)[0]
    # But chain fails at link 1→2
    ok, reason = verify_lineage_chain_full([gp, p, c])
    assert not ok
    assert "link 1" in reason or "link 1→2" in reason


def test_tampered_child_parent_did_breaks_chain():
    gp, p, c, _, _, c_kp = _build_chain()
    # Tamper child's parent_did to point to grandparent
    c.manifest = dict(c.manifest)
    c.manifest["parent_did"] = gp.manifest["individual_id"]
    body = {k: v for k, v in c.manifest.items() if k != "sig"}
    c.manifest["sig"] = c_kp.sign(_canonical(body)).hex()
    # Child still passes its own basic (sig is valid)
    assert verify_federated_basic(c)[0]
    # Chain fails at link 1→2 (child claims GP, but GP isn't
    # in position 1)
    ok, reason = verify_lineage_chain_full([gp, p, c])
    assert not ok
    assert "link" in reason.lower()


def test_tampered_grandparent_memory_breaks_chain():
    gp, p, c, *_ = _build_chain()
    # Tamper a memory entry → grandparent's basic fails → chain
    # fails at bundle 0
    gp.memory[3]["action"] = 99
    ok, reason = verify_lineage_chain_full([gp, p, c])
    assert not ok
    assert "chain[0]" in reason


# -- Save / load --

def test_save_load_chain(tmp_path):
    gp, p, c, *_ = _build_chain()
    gp.save(tmp_path / "gp")
    p.save(tmp_path / "p")
    c.save(tmp_path / "c")
    gp_loaded = IndividualBundle.load(tmp_path / "gp")
    p_loaded = IndividualBundle.load(tmp_path / "p")
    c_loaded = IndividualBundle.load(tmp_path / "c")
    ok, reason = verify_lineage_chain_full(
        [gp_loaded, p_loaded, c_loaded])
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["chain_length"] == 3
    assert audit["verification"]["aggregate"] is True
    assert all(b["basic"] and b["full"]
                for b in audit["verification"]["bundles"])
    assert all(l["verified"]
                for l in audit["verification"]["links"])
    assert audit["tampering"]["tampered_spawn_detected"] is True
    assert audit["tampering"]["tampered_parent_did_detected"] is True
    # Behavioral difference
    assert audit["behavioral"]["child_first_50"] != \
        audit["behavioral"]["fresh_first_50"]
    # Files exist
    assert (tmp_path / "multi_generation" /
            "gen0_grandparent" / "manifest.json").exists()
    assert (tmp_path / "multi_generation" /
            "gen1_parent" / "initial_weights.json").exists()
    assert (tmp_path / "multi_generation" /
            "gen2_child" / "initial_weights.json").exists()
