import json
import pytest
from individual_bundle import (
    IndividualBundle, verify_bundle_basic, serialize_weights,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_basic, verify_federated_full,
    verify_federated_with_world_logs,
    _merkle_root, demo, HAS_CRYPTO,
)
from world_agent_coupling import ScriptedWorld, WorldStepRecord
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


def _two_world_session(n_a=15, n_b=10):
    kp = _kp()
    model = TinyRNN(n_extra_inputs=0, seed=42)
    memory = []
    wa = _world(k_b=0)
    wb = _world(k_b=100, prng=0xFEED)
    sa = FederatedSession(
        individual_kp=kp, model=model, world=wa,
        initial_point=(200, 800), memory=memory)
    for _ in range(n_a):
        sa.step()
    sb = FederatedSession(
        individual_kp=kp, model=model, world=wb,
        initial_point=(300, 700), memory=memory)
    for _ in range(n_b):
        sb.step()
    return kp, model, [sa, sb], memory, [wa, wb]


# -- Session basics --

def test_session_appends_world_entry():
    kp = _kp()
    m = TinyRNN(seed=42)
    memory = []
    w = _world()
    FederatedSession(
        individual_kp=kp, model=m, world=w,
        initial_point=(0, 0), memory=memory)
    assert len(memory) == 1
    assert memory[0]["type"] == "world_entry"
    assert memory[0]["world_id"] == w.world_id


def test_session_step_appends_agent_step():
    kp = _kp()
    m = TinyRNN(seed=42)
    memory = []
    w = _world()
    s = FederatedSession(
        individual_kp=kp, model=m, world=w,
        initial_point=(0, 0), memory=memory)
    s.step()
    assert len(memory) == 2
    assert memory[1]["type"] == "agent_step"
    assert memory[1]["world_id"] == w.world_id
    assert memory[1]["step_in_world"] == 0


def test_session_context_counts_steps():
    kp = _kp()
    m = TinyRNN(seed=42)
    memory = []
    w = _world()
    s = FederatedSession(
        individual_kp=kp, model=m, world=w,
        initial_point=(0, 0), memory=memory)
    for _ in range(5):
        s.step()
    assert s.world_context["steps_in_world"] == 5


def test_rng_override():
    kp = _kp()
    m1 = TinyRNN(seed=42)
    m2 = TinyRNN(seed=42)
    w1 = _world()
    w2 = _world(k_b=100, prng=0xDEAD)
    s1 = FederatedSession(
        individual_kp=kp, model=m1, world=w1,
        initial_point=(0, 0), memory=[],
        rng_seed_override=12345)
    s2 = FederatedSession(
        individual_kp=kp, model=m2, world=w2,
        initial_point=(0, 0), memory=[],
        rng_seed_override=12345)
    assert s1._rng_seed == s2._rng_seed == 12345


# -- Two worlds --

def test_two_world_memory():
    kp, model, sessions, memory, worlds = _two_world_session()
    # 2 world_entry records + 15 + 10 agent_steps
    assert len(memory) == 2 + 25
    entry_count = sum(1 for r in memory
                        if r["type"] == "world_entry")
    step_count = sum(1 for r in memory
                       if r["type"] == "agent_step")
    assert entry_count == 2
    assert step_count == 25


def test_two_world_contexts():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    ctxs = bundle.manifest["world_contexts"]
    assert len(ctxs) == 2
    assert ctxs[0]["world_id"] == worlds[0].world_id
    assert ctxs[1]["world_id"] == worlds[1].world_id
    assert ctxs[0]["steps_in_world"] == 15
    assert ctxs[1]["steps_in_world"] == 10
    assert ctxs[0]["first_memory_index"] == 0
    assert ctxs[1]["first_memory_index"] == 1 + 15


# -- Verification tiers --

def test_basic_verifies():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    ok, reason = verify_federated_basic(bundle)
    assert ok, reason


def test_full_verifies():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    ok, reason = verify_federated_full(bundle)
    assert ok, reason


def test_with_world_logs_verifies():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    world_logs = {
        w.world_id: [r.body() for r in w.records
                      if isinstance(r, WorldStepRecord)]
        for w in worlds
    }
    ok, reason = verify_federated_with_world_logs(
        bundle, world_logs)
    assert ok, reason


def test_with_world_logs_missing_world():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    # Supply only world 1's log
    world_logs = {
        worlds[0].world_id: [r.body() for r in worlds[0].records
                              if isinstance(r, WorldStepRecord)]
    }
    ok, _ = verify_federated_with_world_logs(
        bundle, world_logs)
    assert not ok


def test_with_world_logs_mismatch():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    world_logs = {
        w.world_id: [r.body() for r in w.records
                      if isinstance(r, WorldStepRecord)]
        for w in worlds
    }
    # Tamper: change one world step's pick
    key = worlds[1].world_id
    world_logs[key][3] = dict(world_logs[key][3])
    world_logs[key][3]["pick_b"] = 99
    ok, _ = verify_federated_with_world_logs(
        bundle, world_logs)
    assert not ok


# -- Tampering --

def test_tampered_world_context_fails_basic():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    # Tamper: change world_contexts[0].steps_in_world
    bundle.manifest = dict(bundle.manifest)
    bundle.manifest["world_contexts"] = [
        dict(c) for c in bundle.manifest["world_contexts"]]
    bundle.manifest["world_contexts"][0]["steps_in_world"] = 99
    # Re-sign
    body = {k: v for k, v in bundle.manifest.items()
             if k != "sig"}
    from individual_bundle import _canonical
    bundle.manifest["sig"] = kp.sign(
        _canonical(body)).hex()
    ok, _ = verify_federated_basic(bundle)
    assert not ok


def test_tampered_memory_fails_basic():
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    # Tamper: change a memory entry action
    bundle.memory[5]["action"] = 99
    ok, _ = verify_federated_basic(bundle)
    assert not ok


# -- Save / load --

def test_save_load_roundtrip(tmp_path):
    kp, model, sessions, memory, worlds = _two_world_session()
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42)
    bundle.save(tmp_path / "b")
    loaded = IndividualBundle.load(tmp_path / "b")
    assert loaded.manifest["world_contexts"] == \
        bundle.manifest["world_contexts"]
    ok, _ = verify_federated_full(loaded)
    assert ok


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["basic"] is True
    assert audit["verification"]["full"] is True
    assert audit["verification"]["with_world_logs"] is True
    assert len(audit["worlds_visited"]) == 3
    # Behavioral difference between federated and fresh
    fd = audit["behavioral"]["federated_world3_first_100"]
    cd = audit["behavioral"]["fresh_world3_first_100"]
    assert fd != cd
    assert (tmp_path / "federated_bundle" /
            "federated_demo.json").exists()
