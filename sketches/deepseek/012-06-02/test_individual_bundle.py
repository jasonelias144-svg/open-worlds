import json
import pytest
from individual_bundle import (
    IndividualBundle, pack_bundle,
    verify_bundle_basic, verify_bundle_full, verify_bundle_exact,
    model_config, serialize_weights, build_model, apply_weights,
    _merkle_root, demo, HAS_CRYPTO, BUNDLE_VERSION,
)
from world_agent_coupling import WorldAgentSession, ScriptedWorld
from coupled_learners import TinyRNN, TabularQ, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _session(seed=1, observe=False, steps=100):
    world = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=100, prng_seed_b=0xCAFE, rule=SIERPINSKI)
    model = TinyRNN(
        n_extra_inputs=3 if observe else 0, seed=seed)
    s = WorldAgentSession(
        agent_kp=_kp(), agent_model=model,
        agent_observe=observe, world=world,
        agent_initial_point=(200, 800),
        rule=SIERPINSKI, seed_a=seed + 100)
    s.agent_model_config_name = "test"
    for _ in range(steps):
        s.step()
    return s


# -- Merkle --

def test_merkle_root_empty():
    assert _merkle_root([]) == \
        __import__("individual_bundle")._hash("")


def test_merkle_root_single():
    r = _merkle_root(["abc"])
    assert len(r) == 64


def test_merkle_root_changes_with_content():
    a = _merkle_root(["a", "b", "c"])
    b = _merkle_root(["a", "b", "d"])
    assert a != b


# -- Model serialization --

def test_rnn_serialize_roundtrip():
    model = TinyRNN(n_actions=3, hidden=4, n_extra_inputs=0, seed=42)
    model._h_prev = [0.1, -0.2, 0.3, 0.0]
    model._baseline = 0.75
    cfg = model_config(model)
    weights = serialize_weights(model)
    model2 = build_model(cfg)
    apply_weights(model2, weights)
    assert model2.W_in == model.W_in
    assert model2.W_h == model.W_h
    assert model2.W_out == model.W_out
    assert model2.b_out == model.b_out
    assert model2._h_prev == model._h_prev
    assert model2._baseline == model._baseline


def test_q_serialize_roundtrip():
    model = TabularQ(n_actions=3, grid=8, seed=1)
    model.Q[((2, 3), 1)] = 0.42
    model.Q[((5, 6), 2)] = -0.1
    cfg = model_config(model)
    weights = serialize_weights(model)
    model2 = build_model(cfg)
    apply_weights(model2, weights)
    assert model2.Q == model.Q
    assert model2.epsilon == model.epsilon
    assert model2.alpha == model.alpha


# -- Pack --

def test_pack_basic():
    s = _session(steps=50)
    bundle = pack_bundle(s, persona="test agent")
    assert bundle.manifest["version"] == BUNDLE_VERSION
    assert bundle.manifest["memory_entries"] == 50
    assert bundle.manifest["sig"]


def test_pack_observations_blind():
    s = _session(observe=False, steps=20)
    bundle = pack_bundle(s, persona="blind")
    assert bundle.manifest["observes"] is False
    assert bundle.observations == []


def test_pack_observations_observing():
    s = _session(observe=True, steps=20)
    bundle = pack_bundle(s, persona="observe")
    assert bundle.manifest["observes"] is True
    assert len(bundle.observations) == 20


# -- Save/load --

def test_save_load_roundtrip(tmp_path):
    s = _session(steps=30)
    bundle = pack_bundle(s, persona="test")
    bundle.save(tmp_path / "b")
    loaded = IndividualBundle.load(tmp_path / "b")
    assert loaded.individual_id == bundle.individual_id
    assert len(loaded.memory) == 30
    assert loaded.weights == bundle.weights


# -- Verification --

def test_basic_verifies():
    s = _session(steps=50)
    bundle = pack_bundle(s, persona="test")
    ok, reason = verify_bundle_basic(bundle)
    assert ok, reason


def test_full_verifies_blind():
    s = _session(observe=False, steps=50)
    bundle = pack_bundle(s, persona="blind", initial_seed=1)
    ok, reason = verify_bundle_full(bundle)
    assert ok, reason


def test_exact_verifies_blind():
    s = _session(observe=False, steps=50)
    bundle = pack_bundle(s, persona="blind", initial_seed=1)
    ok, reason = verify_bundle_exact(bundle)
    assert ok, reason


def test_tampered_memory_fails_basic():
    s = _session(steps=20)
    bundle = pack_bundle(s, persona="test")
    bundle.memory[5]["action"] = 99
    ok, _ = verify_bundle_basic(bundle)
    assert not ok


def test_tampered_weights_fails_basic():
    s = _session(steps=20)
    bundle = pack_bundle(s, persona="test")
    bundle.weights["b_out"][0] = 99.0
    ok, _ = verify_bundle_basic(bundle)
    assert not ok


def test_tampered_observations_fails_basic():
    s = _session(observe=True, steps=10)
    bundle = pack_bundle(s, persona="test")
    if bundle.observations:
        bundle.observations[3]["freq"] = [1.0, 0.0, 0.0]
    ok, _ = verify_bundle_basic(bundle)
    assert not ok


def test_tampered_manifest_fails():
    s = _session(steps=20)
    bundle = pack_bundle(s, persona="test")
    bundle.manifest["memory_entries"] = 21
    ok, _ = verify_bundle_basic(bundle)
    assert not ok


# -- Reconstruction --

def test_reconstruct_model():
    s = _session(steps=50)
    bundle = pack_bundle(s, persona="test")
    model = bundle.reconstruct_model()
    assert model.W_in == s.agent_model.W_in
    assert model.W_out == s.agent_model.W_out


def test_initial_model_from_seed():
    s = _session(seed=42, steps=10)
    bundle = pack_bundle(s, persona="test", initial_seed=42)
    initial = bundle.initial_model()
    # Same seed produces same initial weights
    reference = TinyRNN(n_actions=3, hidden=4,
                          n_extra_inputs=0, seed=42)
    assert initial.W_in == reference.W_in


# -- Resume --

def test_resume_continues():
    s = _session(steps=100)
    bundle = pack_bundle(s, persona="test", initial_seed=1)
    resumed_model = bundle.reconstruct_model()
    assert resumed_model is not None
    # Model can act
    import random as _r
    rng = _r.Random(0)
    state = (0, 0.0, 0.2, 0.8)
    action = resumed_model.act(state, rng)
    assert 0 <= action < 3


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["bundles"]["blind"]["basic"] is True
    assert audit["bundles"]["blind"]["full"] is True
    assert audit["bundles"]["blind"]["exact"] is True
    assert audit["bundles"]["observe"]["basic"] is True
    assert audit["bundles"]["observe"]["full"] is True
    assert audit["bundles"]["observe"]["exact"] is True
    assert audit["tamper_detected"] is True
    assert audit["resume_entries"] == 500
    # Bundle dirs exist
    assert (tmp_path / "individual_bundles" /
            "blind" / "manifest.json").exists()
    assert (tmp_path / "individual_bundles" /
            "observe" / "memory.jsonl").exists()
