import json
import pytest
from individual_bundle import (
    IndividualBundle, pack_bundle,
    verify_bundle_basic, verify_bundle_full, verify_bundle_exact,
    serialize_weights,
)
from individual_inheritance import (
    spawn_child_inheriting, pack_inheriting_child,
    verify_bundle_lineage_with_ancestry,
    _weights_hash, _find_spawn_index,
    _replay_parent_to_index,
    demo, HAS_CRYPTO,
)
from individual_spawn import (
    spawn_child, spawn_record_hash,
    verify_bundle_lineage,
)
from world_agent_coupling import WorldAgentSession, ScriptedWorld
from coupled_learners import TinyRNN, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _session(seed=1, steps=30):
    world = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=100, prng_seed_b=0xCAFE, rule=SIERPINSKI)
    model = TinyRNN(n_extra_inputs=0, seed=seed)
    s = WorldAgentSession(
        agent_kp=_kp(), agent_model=model,
        agent_observe=False, world=world,
        agent_initial_point=(200, 800),
        rule=SIERPINSKI, seed_a=seed + 100)
    s.agent_model_config_name = "test"
    for _ in range(steps):
        s.step()
    return s


# -- Spawn --

def test_inheriting_spawn_copies_weights():
    parent = _session(steps=20)
    parent_weights = serialize_weights(parent.agent_model)
    child, rec, init_w = spawn_child_inheriting(
        parent, "child", 42, (300, 700))
    assert init_w == parent_weights
    assert rec["mode"] == "inherit"
    assert rec["inherited_weights_hash"] == _weights_hash(parent_weights)


def test_inheriting_spawn_child_starts_from_inherited():
    parent = _session(steps=20)
    child, _, init_w = spawn_child_inheriting(
        parent, "child", 42, (300, 700))
    child_weights = serialize_weights(child.agent_model)
    assert child_weights == init_w


def test_inheriting_spawn_appends_to_parent():
    parent = _session(steps=10)
    before = len(parent.a_records)
    spawn_child_inheriting(parent, "c", 42, (300, 700))
    assert len(parent.a_records) == before + 1
    assert parent.a_records[-1]["type"] == "spawn"


def test_parent_continues_after_spawn():
    parent = _session(steps=10)
    weights_at_spawn = serialize_weights(parent.agent_model)
    spawn_child_inheriting(parent, "c", 42, (300, 700))
    for _ in range(20):
        parent.step()
    weights_after = serialize_weights(parent.agent_model)
    # Weights changed because parent kept learning
    assert weights_after != weights_at_spawn


# -- Pack / verify --

def test_inheriting_bundle_has_initial_weights():
    parent = _session(steps=20)
    gp_bundle = pack_bundle(parent, persona="p",
                              initial_seed=1)
    child, rec, init_w = spawn_child_inheriting(
        parent, "c", 42, (300, 700))
    for _ in range(20):
        child.step()
    child_bundle = pack_inheriting_child(
        child, "c", "persona",
        parent_bundle=gp_bundle,
        spawn_record=rec,
        child_initial_seed=42,
        initial_weights=init_w)
    assert child_bundle.initial_weights is not None
    assert child_bundle.initial_weights == init_w


def test_inheriting_bundle_verifies_all_tiers():
    parent = _session(steps=20)
    gp_bundle = pack_bundle(parent, persona="p",
                              initial_seed=1)
    child, rec, init_w = spawn_child_inheriting(
        parent, "c", 42, (300, 700))
    for _ in range(20):
        child.step()
    child_bundle = pack_inheriting_child(
        child, "c", "persona",
        parent_bundle=gp_bundle,
        spawn_record=rec,
        child_initial_seed=42,
        initial_weights=init_w)
    basic = verify_bundle_basic(child_bundle)
    assert basic[0], basic[1]
    full = verify_bundle_full(child_bundle)
    assert full[0], full[1]
    exact = verify_bundle_exact(child_bundle)
    assert exact[0], exact[1]


def test_fresh_bundle_still_verifies():
    """Old-style fresh bundles should not break."""
    s = _session(steps=20)
    bundle = pack_bundle(s, persona="p", initial_seed=1)
    assert bundle.initial_weights is None
    basic = verify_bundle_basic(bundle)
    assert basic[0]
    full = verify_bundle_full(bundle)
    assert full[0], full[1]


# -- Lineage --

def test_lineage_verifies_inherit():
    parent = _session(steps=20)
    gp = pack_bundle(parent, persona="p", initial_seed=1)
    child, rec, init_w = spawn_child_inheriting(
        parent, "c", 42, (300, 700))
    for _ in range(10):
        child.step()
    child_bundle = pack_inheriting_child(
        child, "c", "persona",
        parent_bundle=gp,
        spawn_record=rec,
        child_initial_seed=42,
        initial_weights=init_w)
    ok, reason = verify_bundle_lineage(child_bundle, gp)
    assert ok, reason


def test_lineage_with_ancestry_verifies():
    parent = _session(steps=20)
    gp = pack_bundle(parent, persona="p", initial_seed=1)
    child, rec, init_w = spawn_child_inheriting(
        parent, "c", 42, (300, 700))
    for _ in range(10):
        child.step()
    child_bundle = pack_inheriting_child(
        child, "c", "persona",
        parent_bundle=gp,
        spawn_record=rec,
        child_initial_seed=42,
        initial_weights=init_w)
    ok, reason = verify_bundle_lineage_with_ancestry(
        child_bundle, gp)
    assert ok, reason


def test_ancestry_rejects_tampered_initial_hash():
    parent = _session(steps=20)
    gp = pack_bundle(parent, persona="p", initial_seed=1)
    child, rec, init_w = spawn_child_inheriting(
        parent, "c", 42, (300, 700))
    for _ in range(10):
        child.step()
    child_bundle = pack_inheriting_child(
        child, "c", "persona",
        parent_bundle=gp,
        spawn_record=rec,
        child_initial_seed=42,
        initial_weights=init_w)
    # Tamper: change child's claimed initial_weights_hash
    child_bundle.manifest = dict(child_bundle.manifest)
    child_bundle.manifest["initial_weights_hash"] = "00" * 32
    body = {k: v for k, v in child_bundle.manifest.items()
             if k != "sig"}
    child_bundle.manifest["sig"] = child.agent_kp.sign(
        __import__("individual_bundle")._canonical(body)).hex()
    ok, _ = verify_bundle_lineage_with_ancestry(child_bundle, gp)
    assert not ok


def test_ancestry_rejects_wrong_parent():
    """Child claims parent A, actually spawned by B."""
    parent_a = _session(seed=1, steps=15)
    parent_b = _session(seed=2, steps=15)
    bundle_a = pack_bundle(parent_a, persona="a", initial_seed=1)
    bundle_b = pack_bundle(parent_b, persona="b", initial_seed=2)
    # B spawns child
    child, rec, init_w = spawn_child_inheriting(
        parent_b, "c", 42, (300, 700))
    for _ in range(10):
        child.step()
    child_bundle = pack_inheriting_child(
        child, "c", "persona",
        parent_bundle=bundle_b,
        spawn_record=rec,
        child_initial_seed=42,
        initial_weights=init_w)
    # Try to verify against A (wrong parent)
    ok, _ = verify_bundle_lineage_with_ancestry(
        child_bundle, bundle_a)
    assert not ok


# -- Save/load --

def test_save_load_preserves_initial_weights(tmp_path):
    parent = _session(steps=10)
    gp = pack_bundle(parent, persona="p", initial_seed=1)
    child, rec, init_w = spawn_child_inheriting(
        parent, "c", 42, (300, 700))
    for _ in range(10):
        child.step()
    child_bundle = pack_inheriting_child(
        child, "c", "persona",
        parent_bundle=gp,
        spawn_record=rec,
        child_initial_seed=42,
        initial_weights=init_w)
    child_bundle.save(tmp_path / "c")
    loaded = IndividualBundle.load(tmp_path / "c")
    assert loaded.initial_weights is not None
    assert loaded.initial_weights == init_w


# -- Replay --

def test_replay_to_index():
    parent = _session(steps=20)
    gp = pack_bundle(parent, persona="p", initial_seed=1)
    # Spawn at step 20 (all memory is agent_step)
    child, rec, init_w = spawn_child_inheriting(
        parent, "c", 42, (300, 700))
    idx = _find_spawn_index(gp, spawn_record_hash(rec))
    # gp was packed before spawn, so idx should be None
    assert idx is None
    # Re-pack after spawn
    gp2 = pack_bundle(parent, persona="p", initial_seed=1)
    idx2 = _find_spawn_index(gp2, spawn_record_hash(rec))
    assert idx2 is not None
    # Replay parent to that index
    model = _replay_parent_to_index(gp2, idx2)
    replayed_weights = serialize_weights(model)
    # Should match init_w
    assert replayed_weights == init_w


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for name in ("grandparent", "child_fresh",
                  "child_inherit"):
        assert audit["tiers"][name]["basic"] is True, name
        assert audit["tiers"][name]["full"] is True, name
        assert audit["tiers"][name]["exact"] is True, name
    assert audit["lineage"]["fresh"] is True
    assert audit["lineage"]["inherit"] is True
    assert audit["lineage"]["fresh_ancestry"] is True
    assert audit["lineage"]["inherit_ancestry"] is True
    assert audit["tampering"]["fake_inherited_hash_detected"] is True
    # Inheriting child's early distribution is closer to gp's
    # than the fresh child's is
    gp_late = audit["behavioral"]["grandparent_late"]
    fresh_early = audit["behavioral"]["child_fresh_early"]
    inherit_early = audit["behavioral"]["child_inherit_early"]
    def dist(a, b):
        return sum(abs(x - y) for x, y in zip(a, b))
    assert dist(inherit_early, gp_late) < dist(fresh_early, gp_late)
    assert (tmp_path / "individual_inheritance" /
            "child_inherit" / "initial_weights.json").exists()
