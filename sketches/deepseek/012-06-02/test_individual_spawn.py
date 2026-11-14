import json
import pytest
from individual_spawn import (
    spawn_child, spawn_record_hash, pack_child_bundle,
    verify_bundle_lineage, verify_lineage_chain,
    verify_bundle_full_with_spawn,
    verify_bundle_exact_with_spawn,
    render_lineage, demo, HAS_CRYPTO,
)
from individual_bundle import (
    IndividualBundle, pack_bundle,
    verify_bundle_basic, verify_bundle_full,
    _hash, _canonical,
)
from world_agent_coupling import WorldAgentSession, ScriptedWorld
from coupled_learners import TinyRNN, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _session(seed=1, steps=50):
    world = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=100, prng_seed_b=0xCAFE, rule=SIERPINSKI)
    model = TinyRNN(
        n_extra_inputs=0, seed=seed)
    s = WorldAgentSession(
        agent_kp=_kp(), agent_model=model,
        agent_observe=False, world=world,
        agent_initial_point=(200, 800),
        rule=SIERPINSKI, seed_a=seed + 100)
    s.agent_model_config_name = "test"
    for _ in range(steps):
        s.step()
    return s


# -- Spawn mechanics --

def test_spawn_creates_child():
    parent = _session(steps=20)
    child, rec = spawn_child(
        parent, "child", 42, (300, 700))
    assert child.agent_id != parent.agent_id
    assert rec["type"] == "spawn"
    assert rec["child_id"] == child.agent_id


def test_spawn_appends_to_parent_memory():
    parent = _session(steps=20)
    before = len(parent.a_records)
    spawn_child(parent, "child", 42, (300, 700))
    assert len(parent.a_records) == before + 1
    assert parent.a_records[-1]["type"] == "spawn"


def test_spawn_record_signed():
    parent = _session(steps=20)
    _, rec = spawn_child(parent, "child", 42, (300, 700))
    from individual_spawn import _pubkey_from_did
    body = {k: v for k, v in rec.items() if k != "sig"}
    try:
        _pubkey_from_did(parent.agent_id).verify(
            bytes.fromhex(rec["sig"]),
            _canonical(body))
    except Exception:
        pytest.fail("spawn signature invalid")


def test_spawn_record_hash_deterministic():
    parent = _session(steps=10)
    _, rec = spawn_child(parent, "child", 42, (300, 700))
    h1 = spawn_record_hash(rec)
    h2 = spawn_record_hash(rec)
    assert h1 == h2


# -- Child continues independently --

def test_child_steps_independently():
    parent = _session(steps=10)
    child, _ = spawn_child(parent, "child", 42, (300, 700))
    for _ in range(30):
        parent.step()
        child.step()
    assert len(child.a_records) == 30
    # Parent has 10 original steps + 1 spawn + 30 more = 41
    assert len(parent.a_records) == 41


# -- Full verification with spawns --

def test_full_skips_spawns():
    parent = _session(steps=20)
    spawn_child(parent, "child", 42, (300, 700))
    for _ in range(20):
        parent.step()
    bundle = pack_bundle(parent, persona="t", initial_seed=1)
    ok, reason = verify_bundle_full_with_spawn(bundle)
    assert ok, reason


def test_exact_skips_spawns():
    parent = _session(steps=20)
    spawn_child(parent, "child", 42, (300, 700))
    for _ in range(20):
        parent.step()
    bundle = pack_bundle(parent, persona="t", initial_seed=1)
    ok, reason = verify_bundle_exact_with_spawn(bundle)
    assert ok, reason


# -- Lineage --

def test_lineage_verifies():
    parent = _session(steps=20)
    gp_bundle = pack_bundle(parent, persona="gp",
                              initial_seed=1)
    child, rec = spawn_child(parent, "child", 42, (300, 700))
    for _ in range(20):
        child.step()
    child_bundle = pack_child_bundle(
        child, "child", "child persona",
        parent_bundle=gp_bundle, spawn_record=rec,
        child_initial_seed=42)
    ok, reason = verify_bundle_lineage(
        child_bundle, gp_bundle)
    assert ok, reason


def test_lineage_rejects_wrong_parent():
    parent = _session(steps=20)
    gp_bundle = pack_bundle(parent, persona="gp",
                              initial_seed=1)
    child, rec = spawn_child(parent, "child", 42, (300, 700))
    for _ in range(10):
        child.step()
    child_bundle = pack_child_bundle(
        child, "child", "child persona",
        parent_bundle=gp_bundle, spawn_record=rec,
        child_initial_seed=42)
    # Create a different parent (a new session)
    other = _session(seed=99, steps=10)
    other_bundle = pack_bundle(other, persona="other",
                                 initial_seed=99)
    ok, _ = verify_bundle_lineage(child_bundle, other_bundle)
    assert not ok


def test_lineage_chain_of_three():
    gp = _session(seed=1, steps=20)
    gp_bundle = pack_bundle(gp, persona="gp", initial_seed=1)
    parent, gp_spawn = spawn_child(
        gp, "parent", 2, (300, 700))
    for _ in range(10):
        parent.step()
    parent_bundle = pack_child_bundle(
        parent, "parent", "parent persona",
        parent_bundle=gp_bundle,
        spawn_record=gp_spawn,
        child_initial_seed=2)
    child, p_spawn = spawn_child(
        parent, "child", 3, (400, 600))
    for _ in range(10):
        child.step()
    child_bundle = pack_child_bundle(
        child, "child", "child persona",
        parent_bundle=parent_bundle,
        spawn_record=p_spawn,
        child_initial_seed=3)
    ok, reason = verify_lineage_chain(
        [gp_bundle, parent_bundle, child_bundle])
    assert ok, reason


def test_lineage_chain_rejects_fake():
    gp = _session(seed=1, steps=10)
    gp_bundle = pack_bundle(gp, persona="gp", initial_seed=1)
    unrelated = _session(seed=99, steps=10)
    other_bundle = pack_bundle(unrelated, persona="other",
                                 initial_seed=99)
    ok, _ = verify_lineage_chain([gp_bundle, other_bundle])
    assert not ok


# -- Tampering --

def test_memory_tamper_breaks_basic():
    parent = _session(steps=20)
    spawn_child(parent, "child", 42, (300, 700))
    bundle = pack_bundle(parent, persona="t", initial_seed=1)
    bundle.memory[5]["action"] = 99
    ok, _ = verify_bundle_basic(bundle)
    assert not ok


def test_fake_parent_fails_lineage():
    """A child re-signs its manifest to claim a different
    parent, but that parent has no matching spawn record."""
    parent = _session(seed=1, steps=20)
    parent_bundle = pack_bundle(parent, persona="p",
                                  initial_seed=1)
    child, rec = spawn_child(parent, "child", 42, (300, 700))
    for _ in range(10):
        child.step()
    child_bundle = pack_child_bundle(
        child, "child", "child persona",
        parent_bundle=parent_bundle, spawn_record=rec,
        child_initial_seed=42)
    # Another parent that never spawned anyone
    other = _session(seed=99, steps=10)
    other_bundle = pack_bundle(other, persona="o",
                                 initial_seed=99)
    # Child re-signs manifest to claim `other` as parent
    child_bundle.manifest = dict(child_bundle.manifest)
    child_bundle.manifest["parent_did"] = \
        other_bundle.manifest["individual_id"]
    body = {k: v for k, v in child_bundle.manifest.items()
             if k != "sig"}
    child_bundle.manifest["sig"] = child.agent_kp.sign(
        _canonical(body)).hex()
    ok, _ = verify_bundle_lineage(child_bundle, other_bundle)
    assert not ok


# -- Render --

def test_render_lineage():
    gp = _session(seed=1, steps=5)
    gp_bundle = pack_bundle(gp, persona="gp", initial_seed=1)
    text = render_lineage([gp_bundle])
    assert "test" in text or "gp" in text


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for gen in ("grandparent", "parent", "child"):
        assert audit["tiers"][gen]["basic"] is True, gen
        assert audit["tiers"][gen]["full"] is True, gen
        assert audit["tiers"][gen]["exact"] is True, gen
    assert audit["lineage"]["parent_grandparent"] is True
    assert audit["lineage"]["child_parent"] is True
    assert audit["lineage"]["chain"] is True
    assert audit["tampering"]["memory_detected"] is True
    assert audit["tampering"]["fake_lineage_detected"] is True
    assert audit["resume_entries"] == 300
    assert (tmp_path / "individual_spawn" /
            "grandparent" / "manifest.json").exists()
    assert (tmp_path / "individual_spawn" /
            "child" / "manifest.json").exists()
