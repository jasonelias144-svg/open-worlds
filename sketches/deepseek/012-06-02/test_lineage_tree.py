import json
import pytest
from individual_bundle import IndividualBundle, _canonical, _hash
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_basic, verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
)
from lineage_tree import (
    verify_lineage_tree_structure, verify_lineage_tree,
    verify_lineage_tree_with_world_logs,
    tree_report, build_tree, render_tree,
    _detect_duplicate_spawns,
    demo, HAS_CRYPTO,
)
from world_agent_coupling import ScriptedWorld, WorldStepRecord
from coupled_learners import TinyRNN, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(k_b=50, prng=0xCAFE):
    return ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)


def _build_gp_p1_c1():
    """Three-level chain. Returns (gp, p1, c1, kp_gp, kp_p1)."""
    gp_kp = _kp()
    gp_model = TinyRNN(n_extra_inputs=0, seed=42)
    gp_mem: list = []
    s = FederatedSession(
        individual_kp=gp_kp, model=gp_model,
        world=_world(0, 0xAAAA), initial_point=(200, 800),
        memory=gp_mem, rule=SIERPINSKI)
    for _ in range(15):
        s.step()
    gp_sessions = [s]
    p_kp, p_model, spawn0, w0 = spawn_federated_child(
        parent_session=s, child_persona="p1",
        child_initial_seed=100)
    s.step()
    gp = pack_federated_bundle(
        individual_kp=gp_kp, model=gp_model,
        sessions=gp_sessions, memory=gp_mem,
        persona="gp", initial_seed=42, name="grandparent")

    p_mem: list = []
    s1 = FederatedSession(
        individual_kp=p_kp, model=p_model,
        world=_world(25, 0xDDDD), initial_point=(250, 750),
        memory=p_mem, rule=SIERPINSKI)
    for _ in range(10):
        s1.step()
    p_sessions = [s1]
    c_kp, c_model, spawn1, w1 = spawn_federated_child(
        parent_session=s1, child_persona="c1",
        child_initial_seed=101)
    s1.step()
    p1 = pack_federated_child(
        child_kp=p_kp, child_model=p_model,
        child_sessions=p_sessions, child_memory=p_mem,
        child_persona="p1", child_initial_seed=100,
        parent_bundle=gp, spawn_record=spawn0,
        inherited_weights=w0, name="parent1")

    c_mem: list = []
    s2 = FederatedSession(
        individual_kp=c_kp, model=c_model,
        world=_world(75, 0x1234), initial_point=(300, 700),
        memory=c_mem, rule=SIERPINSKI)
    for _ in range(10):
        s2.step()
    c1 = pack_federated_child(
        child_kp=c_kp, child_model=c_model,
        child_sessions=[s2], child_memory=c_mem,
        child_persona="c1", child_initial_seed=101,
        parent_bundle=p1, spawn_record=spawn1,
        inherited_weights=w1, name="child1")
    return gp, p1, c1, gp_kp, p_kp


# -- Structure --

def test_single_bundle_tree():
    gp, _, _, _, _ = _build_gp_p1_c1()
    bundles = {gp.individual_id: gp}
    ok, reason = verify_lineage_tree_structure(
        bundles, gp.individual_id)
    assert ok, reason


def test_chain_of_three_structure():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {b.individual_id: b for b in (gp, p1, c1)}
    ok, reason = verify_lineage_tree_structure(
        bundles, gp.individual_id)
    assert ok, reason


def test_missing_root_fails_structure():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {p1.individual_id: p1, c1.individual_id: c1}
    ok, _ = verify_lineage_tree_structure(
        bundles, gp.individual_id)
    assert not ok


def test_orphan_parent_fails_structure():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    # Remove p1 but keep c1 and gp
    bundles = {
        gp.individual_id: gp,
        c1.individual_id: c1,
    }
    ok, _ = verify_lineage_tree_structure(
        bundles, gp.individual_id)
    assert not ok


def test_root_with_ancestry_fails_structure():
    gp, _, _, _, _ = _build_gp_p1_c1()
    gp.ancestry = [{"type": "spawn"}]  # fake
    bundles = {gp.individual_id: gp}
    ok, _ = verify_lineage_tree_structure(
        bundles, gp.individual_id)
    assert not ok


# -- Full --

def test_chain_full_verifies():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {b.individual_id: b for b in (gp, p1, c1)}
    ok, reason = verify_lineage_tree(bundles, gp.individual_id)
    assert ok, reason


def test_missing_child_fails_structure_not_full():
    """A tree missing a child is still a valid tree — it's just
    smaller. Removing a leaf doesn't break anything."""
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {gp.individual_id: gp, p1.individual_id: p1}
    ok, reason = verify_lineage_tree_structure(
        bundles, gp.individual_id)
    assert ok, reason


def test_removing_middle_breaks_structure():
    """Removing p1 leaves c1 orphaned."""
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {gp.individual_id: gp, c1.individual_id: c1}
    ok, _ = verify_lineage_tree_structure(
        bundles, gp.individual_id)
    assert not ok


# -- Duplicate spawn detection --

def test_detect_duplicate_spawns_clean():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    assert _detect_duplicate_spawns(p1) == []


def test_detect_duplicate_spawns_forced():
    """Inject a duplicate spawn into parent's memory."""
    gp, p1, c1, _, p_kp = _build_gp_p1_c1()
    # Find p1's spawn for c1
    target = None
    for rec in p1.memory:
        if rec.get("type") == "spawn" \
                and rec.get("child_id") == c1.individual_id:
            target = dict(rec)
            break
    assert target is not None
    # Add a duplicate with a slightly different ts
    dup = {**target, "ts": "2026-11-15T99:99:99Z"}
    body = {k: v for k, v in dup.items() if k != "sig"}
    dup["sig"] = p_kp.sign(_canonical(body)).hex()
    p1.memory.append(dup)
    dups = _detect_duplicate_spawns(p1)
    assert len(dups) == 1
    assert dups[0]["child_id"] == c1.individual_id


# -- Report --

def test_report_aggregate():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {b.individual_id: b for b in (gp, p1, c1)}
    report = tree_report(bundles, gp.individual_id)
    assert report["verdict"] is True
    assert len(report["bundles"]) == 3
    assert len(report["edges"]) == 2


def test_build_tree_structure():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {b.individual_id: b for b in (gp, p1, c1)}
    tree = build_tree(bundles, gp.individual_id)
    assert len(tree) == 3
    assert p1.individual_id in tree[gp.individual_id]["children"]
    assert c1.individual_id in tree[p1.individual_id]["children"]


def test_render_tree():
    gp, p1, c1, _, _ = _build_gp_p1_c1()
    bundles = {b.individual_id: b for b in (gp, p1, c1)}
    text = render_tree(bundles, gp.individual_id)
    assert "grandparent" in text
    assert "parent1" in text
    assert "child1" in text


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["full"] is True
    assert audit["verification"]["report_aggregate"] is True
    assert audit["tampering"]["remove_child_detected"] is True
    assert audit["tampering"]["wrong_parent_detected"] is True
    assert audit["tampering"]["duplicate_spawn_detected"] is True
    assert audit["tree_size"] == 6
    assert audit["edge_count"] == 5
    assert (tmp_path / "lineage_tree" /
            "lineage_tree_demo.json").exists()
