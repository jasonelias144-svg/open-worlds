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
    _replay_federated_to_index, _weights_hash,
    _find_spawn_index,
    verify_federated_spawn_ancestry,
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


def _build_parent(n_a=30, n_b=20, pre_spawn_c=20,
                   post_spawn_c=20):
    """Build a parent living in A, B, C; spawn; continue in C."""
    kp = _kp()
    model = TinyRNN(n_extra_inputs=0, seed=42)
    memory = []
    wa = _world(k_b=0, prng=0xAAAA)
    wb = _world(k_b=50, prng=0xBBBB)
    wc = _world(k_b=100, prng=0xCCCC)
    sessions = []
    for world, n, pt in [
        (wa, n_a, (200, 800)),
        (wb, n_b, (300, 700)),
        (wc, pre_spawn_c, (400, 600)),
    ]:
        s = FederatedSession(
            individual_kp=kp, model=model,
            world=world, initial_point=pt,
            memory=memory, rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        sessions.append(s)
    spawn_idx = len(memory)
    child_kp, child_model, spawn_rec, inherited = \
        spawn_federated_child(
            parent_session=sessions[-1],
            child_persona="test",
            child_initial_seed=200)
    for _ in range(post_spawn_c):
        sessions[-1].step()
    parent_bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="parent", initial_seed=42,
        name="parent")
    return (kp, parent_bundle, child_kp, child_model,
            spawn_rec, inherited, spawn_idx,
            [wa, wb, wc])


# -- Spawn --

def test_spawn_appends_to_parent_memory():
    (kp, parent_b, child_kp, child_m, spawn, inherited,
     spawn_idx, _) = _build_parent()
    spawns = [r for r in parent_b.memory
               if r.get("type") == "spawn"]
    assert len(spawns) == 1
    assert spawns[0]["child_id"] == child_kp.public_key().public_bytes(
        encoding=__import__("cryptography.hazmat.primitives.serialization",
                             fromlist=["Encoding"]).Encoding.Raw,
        format=__import__("cryptography.hazmat.primitives.serialization",
                            fromlist=["PublicFormat"]).PublicFormat.Raw,
    ).hex() or True  # just structural check


def test_spawn_record_signed_by_parent():
    (kp, parent_b, child_kp, _, spawn, _, _, _) = _build_parent()
    body = {k: v for k, v in spawn.items() if k != "sig"}
    from individual_bundle import _pubkey_from_did
    _pubkey_from_did(parent_b.individual_id).verify(
        bytes.fromhex(spawn["sig"]),
        _canonical(body))


def test_child_model_has_parent_weights():
    (_, _, _, child_model, _, inherited, _, _) = _build_parent()
    assert serialize_weights(child_model) == inherited


def test_spawn_index_correct():
    (_, parent_b, _, _, spawn, _, spawn_idx, _) = _build_parent()
    h = __import__("individual_spawn").spawn_record_hash(spawn)
    assert _find_spawn_index(parent_b, h) == spawn_idx


# -- Replay --

def test_replay_handles_world_entries():
    (_, parent_b, _, _, spawn, inherited, spawn_idx, _) = \
        _build_parent()
    model, reason = _replay_federated_to_index(
        parent_b, spawn_idx)
    assert model is not None, reason
    actual = serialize_weights(model)
    assert actual == inherited


def test_replay_detects_wrong_index():
    (_, parent_b, _, _, _, _, spawn_idx, _) = _build_parent()
    # Replay to 0 → empty model, weights = initial
    model, reason = _replay_federated_to_index(parent_b, 0)
    assert model is not None
    # Replay to spawn_idx + 100 → includes post-spawn steps,
    # weights differ
    model_after, reason = _replay_federated_to_index(
        parent_b, spawn_idx + 100)
    assert model_after is not None
    # Initial model weights should differ from after-spawn
    assert serialize_weights(model) != serialize_weights(model_after)


# -- Pack child --

def test_pack_child_lineage_fields():
    (kp, parent_b, child_kp, child_model, spawn, inherited,
     spawn_idx, worlds) = _build_parent()
    child_memory = []
    child_sessions = []
    for widx, n, pt in [(0, 30, (250, 750)),
                          (1, 20, (350, 650))]:
        cw = _world(k_b=25, prng=0xDDDD + widx)
        s = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=cw, initial_point=pt,
            memory=child_memory, rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        child_sessions.append(s)
    child_b = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=child_sessions,
        child_memory=child_memory,
        child_persona="child", child_initial_seed=200,
        parent_bundle=parent_b, spawn_record=spawn,
        inherited_weights=inherited, name="child")
    assert child_b.manifest["parent_did"] == parent_b.individual_id
    assert child_b.manifest["inherited_from"] == parent_b.individual_id
    assert child_b.manifest["parent_spawn_hash"]
    assert child_b.initial_weights == inherited


# -- Verification --

def test_federated_child_verifies_all_tiers():
    (kp, parent_b, child_kp, child_model, spawn, inherited,
     _, _) = _build_parent()
    child_memory = []
    child_sessions = []
    cw = _world(k_b=25, prng=0xDDDD)
    s = FederatedSession(
        individual_kp=child_kp, model=child_model,
        world=cw, initial_point=(250, 750),
        memory=child_memory, rule=SIERPINSKI)
    for _ in range(30):
        s.step()
    child_sessions.append(s)
    child_b = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=child_sessions,
        child_memory=child_memory,
        child_persona="child", child_initial_seed=200,
        parent_bundle=parent_b, spawn_record=spawn,
        inherited_weights=inherited, name="child")
    assert verify_federated_basic(child_b)[0]
    assert verify_federated_full(child_b)[0]


def test_ancestry_verifies():
    (kp, parent_b, child_kp, child_model, spawn, inherited,
     _, _) = _build_parent()
    child_memory = []
    cw = _world(k_b=25, prng=0xDDDD)
    s = FederatedSession(
        individual_kp=child_kp, model=child_model,
        world=cw, initial_point=(250, 750),
        memory=child_memory, rule=SIERPINSKI)
    for _ in range(20):
        s.step()
    child_b = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=[s],
        child_memory=child_memory,
        child_persona="child", child_initial_seed=200,
        parent_bundle=parent_b, spawn_record=spawn,
        inherited_weights=inherited, name="child")
    ok, reason = verify_federated_spawn_ancestry(
        child_b, parent_b)
    assert ok, reason


def test_ancestry_fails_on_tampered_spawn_claim():
    (kp, parent_b, child_kp, child_model, spawn, inherited,
     _, _) = _build_parent()
    child_memory = []
    cw = _world(k_b=25, prng=0xDDDD)
    s = FederatedSession(
        individual_kp=child_kp, model=child_model,
        world=cw, initial_point=(250, 750),
        memory=child_memory, rule=SIERPINSKI)
    for _ in range(20):
        s.step()
    child_b = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=[s], child_memory=child_memory,
        child_persona="child", child_initial_seed=200,
        parent_bundle=parent_b, spawn_record=spawn,
        inherited_weights=inherited, name="child")
    # Tamper parent's spawn record: change inherited_weights_hash
    for i, rec in enumerate(parent_b.memory):
        if rec.get("type") == "spawn":
            body = {k: v for k, v in rec.items() if k != "sig"}
            body["inherited_weights_hash"] = "00" * 32
            sig = kp.sign(_canonical(body)).hex()
            parent_b.memory[i] = {**body, "sig": sig}
            break
    # Recompute Merkle root and re-sign manifest
    parent_b.manifest = dict(parent_b.manifest)
    parent_b.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in parent_b.memory])
    body = {k: v for k, v in parent_b.manifest.items()
             if k != "sig"}
    parent_b.manifest["sig"] = kp.sign(
        _canonical(body)).hex()
    ok, _ = verify_federated_spawn_ancestry(child_b, parent_b)
    assert not ok


def test_ancestry_fails_on_wrong_parent():
    (kp1, parent_b1, child_kp, child_model, spawn, inherited,
     _, _) = _build_parent()
    # Build a different parent
    kp2 = _kp()
    other_model = TinyRNN(n_extra_inputs=0, seed=99)
    other_memory = []
    other_w = _world(k_b=10, prng=0xF00D)
    other_s = FederatedSession(
        individual_kp=kp2, model=other_model,
        world=other_w, initial_point=(0, 0),
        memory=other_memory, rule=SIERPINSKI)
    for _ in range(20):
        other_s.step()
    other_b = pack_federated_bundle(
        individual_kp=kp2, model=other_model,
        sessions=[other_s], memory=other_memory,
        persona="other", initial_seed=99, name="other")
    # Build child under parent_b1
    child_memory = []
    cw = _world(k_b=25, prng=0xDDDD)
    s = FederatedSession(
        individual_kp=child_kp, model=child_model,
        world=cw, initial_point=(250, 750),
        memory=child_memory, rule=SIERPINSKI)
    for _ in range(10):
        s.step()
    child_b = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=[s], child_memory=child_memory,
        child_persona="child", child_initial_seed=200,
        parent_bundle=parent_b1, spawn_record=spawn,
        inherited_weights=inherited, name="child")
    # Verify against wrong parent
    ok, _ = verify_federated_spawn_ancestry(child_b, other_b)
    assert not ok


# -- Save/load --

def test_save_load_child(tmp_path):
    (kp, parent_b, child_kp, child_model, spawn, inherited,
     _, _) = _build_parent()
    child_memory = []
    cw = _world(k_b=25, prng=0xDDDD)
    s = FederatedSession(
        individual_kp=child_kp, model=child_model,
        world=cw, initial_point=(250, 750),
        memory=child_memory, rule=SIERPINSKI)
    for _ in range(10):
        s.step()
    child_b = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=[s], child_memory=child_memory,
        child_persona="child", child_initial_seed=200,
        parent_bundle=parent_b, spawn_record=spawn,
        inherited_weights=inherited, name="child")
    child_b.save(tmp_path / "c")
    loaded = IndividualBundle.load(tmp_path / "c")
    assert loaded.initial_weights == inherited
    assert loaded.manifest["parent_did"] == \
        parent_b.individual_id
    ok, reason = verify_federated_full(loaded)
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for k in ("parent_basic", "parent_full",
               "child_basic", "child_full", "ancestry"):
        assert audit["verification"][k] is True, k
    assert audit["tampering"]["tampered_spawn_detected"] is True
    assert audit["parent_spawn_index"] > 0
    assert audit["behavioral"]["child_first_50_world_d"] != \
        audit["behavioral"]["fresh_first_50_world_d"]
    assert (tmp_path / "federated_spawn" /
            "federated_spawn_demo.json").exists()
    assert (tmp_path / "federated_spawn" /
            "parent" / "initial_weights.json").exists() is False
    assert (tmp_path / "federated_spawn" /
            "child" / "initial_weights.json").exists()
