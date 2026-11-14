import json
import pytest
from individual_bundle import (
    IndividualBundle, verify_bundle_basic, serialize_weights,
    _canonical, _hash, _merkle_root,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
)
from individual_spawn import spawn_child as spawn_fresh
from compact_ancestry import (
    CompactAncestry, compute_compact_ancestry, slim_bundle,
    verify_compact_ancestry,
)
from compact_inheritance import (
    verify_compact_ancestry_with_inheritance,
    verify_chain_compact_with_inheritance,
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


def _world(k_b=50, prng=0xCAFE):
    return ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)


def _build_inheriting_chain(depth=3, steps=8):
    """Full + slim bundles. Returns (kps, full, slim, fetcher)."""
    kps = []
    models = []
    memories = []
    sessions_list = []
    spawns = []
    inherited = []

    kp0 = _kp()
    m0 = TinyRNN(n_extra_inputs=0, seed=100)
    mem0: list = []
    s0 = FederatedSession(
        individual_kp=kp0, model=m0,
        world=_world(0, 0xAAAA),
        initial_point=(200, 800), memory=mem0,
        rule=SIERPINSKI)
    for _ in range(steps):
        s0.step()
    kps.append(kp0); models.append(m0)
    memories.append(mem0); sessions_list.append([s0])

    for i in range(1, depth + 1):
        parent_sessions = sessions_list[i - 1]
        child_kp, child_model, spawn_rec, inherited_w = \
            spawn_federated_child(
                parent_session=parent_sessions[-1],
                child_persona=f"g{i}",
                child_initial_seed=100 + i)
        parent_sessions[-1].step()
        kps.append(child_kp); models.append(child_model)
        spawns.append(spawn_rec)
        inherited.append(inherited_w)
        mem_i: list = []
        s_i = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=_world(i * 10, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 10, 800),
            memory=mem_i, rule=SIERPINSKI)
        for _ in range(steps):
            s_i.step()
        memories.append(mem_i); sessions_list.append([s_i])

    full = [pack_federated_bundle(
        individual_kp=kps[0], model=models[0],
        sessions=sessions_list[0], memory=memories[0],
        persona="g0", initial_seed=100, name="g0")]
    for i in range(1, depth + 1):
        full.append(pack_federated_child(
            child_kp=kps[i], child_model=models[i],
            child_sessions=sessions_list[i],
            child_memory=memories[i],
            child_persona=f"g{i}",
            child_initial_seed=100 + i,
            parent_bundle=full[i - 1],
            spawn_record=spawns[i - 1],
            inherited_weights=inherited[i - 1],
            name=f"g{i}"))

    slim = [full[0]]
    for i in range(1, depth + 1):
        compact = compute_compact_ancestry(
            full[i].individual_id, slim[i - 1],
            spawns[i - 1])
        slim.append(slim_bundle(full[i], compact, kps[i]))

    full_by_id = {b.individual_id: b for b in full}
    def fetcher(did):
        return full_by_id.get(did)
    return kps, full, slim, fetcher


def _build_fresh_chain(depth=2, steps=5):
    """Fresh-spawn chain (no inheritance). Returns full + slim."""
    kps = []
    models = []
    memories = []
    sessions_list = []
    spawns = []

    kp0 = _kp()
    m0 = TinyRNN(n_extra_inputs=0, seed=42)
    mem0: list = []
    s0 = FederatedSession(
        individual_kp=kp0, model=m0,
        world=_world(0, 0xAAAA),
        initial_point=(200, 800), memory=mem0,
        rule=SIERPINSKI)
    for _ in range(steps):
        s0.step()
    kps.append(kp0); models.append(m0)
    memories.append(mem0); sessions_list.append([s0])

    for i in range(1, depth + 1):
        parent_sessions = sessions_list[i - 1]
        # Fresh spawn — no inheritance
        child_sessions, spawn_rec = spawn_fresh(
            parent_session=parent_sessions[-1],
            child_persona=f"g{i}",
            child_initial_seed=100 + i,
            child_initial_point=(200 + i * 10, 800))
        parent_sessions[-1].step()
        # Extract child model and kp from the session
        child_kp = child_sessions.agent_kp
        child_model = child_sessions.agent_model
        kps.append(child_kp); models.append(child_model)
        spawns.append(spawn_rec)
        mem_i: list = []
        s_i = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=_world(i * 10, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 10, 800),
            memory=mem_i, rule=SIERPINSKI)
        for _ in range(steps):
            s_i.step()
        memories.append(mem_i); sessions_list.append([s_i])

    full = [pack_federated_bundle(
        individual_kp=kps[0], model=models[0],
        sessions=sessions_list[0], memory=memories[0],
        persona="g0", initial_seed=42, name="g0")]
    for i in range(1, depth + 1):
        full.append(pack_federated_child(
            child_kp=kps[i], child_model=models[i],
            child_sessions=sessions_list[i],
            child_memory=memories[i],
            child_persona=f"g{i}",
            child_initial_seed=100 + i,
            parent_bundle=full[i - 1],
            spawn_record=spawns[i - 1],
            inherited_weights=None,  # <-- fresh
            name=f"g{i}"))

    slim = [full[0]]
    for i in range(1, depth + 1):
        compact = compute_compact_ancestry(
            full[i].individual_id, slim[i - 1],
            spawns[i - 1])
        slim.append(slim_bundle(full[i], compact, kps[i]))

    full_by_id = {b.individual_id: b for b in full}
    def fetcher(did):
        return full_by_id.get(did)
    return slim, fetcher


# -- Root case --

def test_root_passes():
    kps, full, slim, fetcher = _build_inheriting_chain(depth=1, steps=5)
    ok, reason = verify_compact_ancestry_with_inheritance(
        slim[0], fetcher)
    assert ok, reason
    assert "root" in reason.lower()


def test_root_with_initial_weights_fails():
    """A root that claims inheritance is inconsistent."""
    kps, full, slim, fetcher = _build_inheriting_chain(depth=1, steps=5)
    tampered = IndividualBundle(
        manifest=dict(slim[0].manifest),
        memory=list(slim[0].memory),
        weights=slim[0].weights,
        initial_weights={"stub": True},
        observations=slim[0].observations,
        ancestry=list(slim[0].ancestry),
    )
    tampered.manifest["initial_weights_hash"] = "00" * 32
    body = {k: v for k, v in tampered.manifest.items() if k != "sig"}
    tampered.manifest["sig"] = kps[0].sign(
        _canonical(body)).hex()
    ok, _ = verify_compact_ancestry_with_inheritance(
        tampered, fetcher)
    assert not ok


# -- Happy path --

def test_inheriting_chain_verifies():
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    for b in slim:
        ok, reason = verify_compact_ancestry_with_inheritance(
            b, fetcher)
        assert ok, f"{b.manifest['name']}: {reason}"


def test_chain_level_verifies():
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    ok, reason = verify_chain_compact_with_inheritance(slim)
    assert ok, reason


# -- Fresh chain --

def test_fresh_chain_verifies():
    """Fresh spawns (no inheritance) also pass — the
    verifier detects 'no inheritance claimed' and skips
    that check."""
    slim, fetcher = _build_fresh_chain(depth=2, steps=5)
    for b in slim:
        ok, reason = verify_compact_ancestry_with_inheritance(
            b, fetcher)
        assert ok, f"{b.manifest['name']}: {reason}"


# -- Inheritance tampering --

def test_tampered_child_initial_hash_fails():
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    # Tamper deepest child's initial_weights_hash
    target = slim[-1]
    tampered = IndividualBundle(
        manifest=dict(target.manifest),
        memory=list(target.memory),
        weights=dict(target.weights),
        initial_weights=(dict(target.initial_weights)
                          if target.initial_weights else None),
        observations=list(target.observations),
        ancestry=[],
    )
    tampered.manifest["initial_weights_hash"] = "00" * 32
    body = {k: v for k, v in tampered.manifest.items() if k != "sig"}
    tampered.manifest["sig"] = kps[-1].sign(
        _canonical(body)).hex()
    ok, reason = verify_compact_ancestry_with_inheritance(
        tampered, fetcher)
    assert not ok
    assert "hash mismatch" in reason.lower() or \
           "inheritance" in reason.lower()


def test_tampered_parent_spawn_hash_fails():
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    target = slim[-1]
    parent_id = target.manifest["compact_ancestry"]["parent_did"]
    parent = full[-2]
    # Tamper the spawn record for target in parent's memory
    tampered_parent = IndividualBundle(
        manifest=dict(parent.manifest),
        memory=list(parent.memory),
        weights=parent.weights,
        initial_weights=parent.initial_weights,
        observations=parent.observations,
        ancestry=parent.ancestry,
    )
    for idx, rec in enumerate(tampered_parent.memory):
        if rec.get("type") == "spawn" \
                and rec.get("child_id") == target.individual_id:
            body = {k: v for k, v in rec.items() if k != "sig"}
            body["inherited_weights_hash"] = "ff" * 32
            sig = kps[-2].sign(_canonical(body)).hex()
            tampered_parent.memory[idx] = {**body, "sig": sig}
            break
    tampered_parent.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in tampered_parent.memory])
    body = {k: v for k, v in tampered_parent.manifest.items()
             if k != "sig"}
    tampered_parent.manifest["sig"] = kps[-2].sign(
        _canonical(body)).hex()
    def bad_fetcher(did):
        if did == parent.individual_id:
            return tampered_parent
        return fetcher(did)
    ok, _ = verify_compact_ancestry_with_inheritance(
        target, bad_fetcher)
    assert not ok


def test_stripped_parent_initial_fails():
    """Parent appears fresh but child claims inheritance."""
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    target = slim[-1]
    parent = full[-2]
    stripped = IndividualBundle(
        manifest=dict(parent.manifest),
        memory=list(parent.memory),
        weights=parent.weights,
        initial_weights=None,  # stripped
        observations=parent.observations,
        ancestry=parent.ancestry,
    )
    if "initial_weights_hash" in stripped.manifest:
        del stripped.manifest["initial_weights_hash"]
    body = {k: v for k, v in stripped.manifest.items() if k != "sig"}
    stripped.manifest["sig"] = kps[-2].sign(
        _canonical(body)).hex()
    def strip_fetcher(did):
        if did == parent.individual_id:
            return stripped
        return fetcher(did)
    ok, reason = verify_compact_ancestry_with_inheritance(
        target, strip_fetcher)
    assert not ok
    # The failure should be caught either at "spawn claims
    # inheritance but child doesn't" (if child was also stripped
    # by association) or at "child declares initial_weights
    # but spawn doesn't claim inheritance"
    assert "inheritance" in reason.lower()


# -- Replay failure --

def test_corrupt_parent_memory_fails():
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    target = slim[-1]
    parent = full[-2]
    # Remove a non-spawn, non-world_entry record so replay fails
    corrupt = IndividualBundle(
        manifest=dict(parent.manifest),
        memory=[r for r in parent.memory
                 if not (r.get("type") == "agent_step"
                          and r.get("step_in_world") == 1)],
        weights=parent.weights,
        initial_weights=parent.initial_weights,
        observations=parent.observations,
        ancestry=parent.ancestry,
    )
    corrupt.manifest["memory_entries"] = len(corrupt.memory)
    corrupt.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in corrupt.memory])
    body = {k: v for k, v in corrupt.manifest.items() if k != "sig"}
    corrupt.manifest["sig"] = kps[-2].sign(
        _canonical(body)).hex()
    def corrupt_fetcher(did):
        if did == parent.individual_id:
            return corrupt
        return fetcher(did)
    ok, _ = verify_compact_ancestry_with_inheritance(
        target, corrupt_fetcher)
    assert not ok


# -- Backward compat --

def test_descent_only_verifier_still_works():
    """verify_compact_ancestry (previous cycle) still passes."""
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    for b in slim:
        ok, reason = verify_compact_ancestry(b, fetcher)
        assert ok, f"{b.manifest['name']}: {reason}"


def test_full_bundles_still_verify_federated():
    kps, full, slim, fetcher = _build_inheriting_chain(depth=3, steps=5)
    for b in full:
        ok, reason = verify_federated_full(b)
        assert ok, reason


# -- Save/load --

def test_save_load_slim_with_inheritance(tmp_path):
    kps, full, slim, fetcher = _build_inheriting_chain(depth=2, steps=5)
    slim[-1].save(tmp_path / "s")
    loaded = IndividualBundle.load(tmp_path / "s")
    ok, reason = verify_compact_ancestry_with_inheritance(
        loaded, fetcher)
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["chain_length"] == 6
    for v in audit["verification"]:
        assert v["federated_full"] is True, v["name"]
        assert v["compact_inheritance"] is True, v["name"]
    assert audit["chain_verdict"]["ok"] is True
    assert audit["tampering"]["child_initial_hash"]["detected"]
    assert audit["tampering"]["parent_spawn_hash"]["detected"]
    assert audit["tampering"]["parent_stripped_initial"]["detected"]
    # Size growth
    sizes = audit["sizes"]
    assert sizes[-1]["full_ancestry_bytes"] > \
           sizes[0]["full_ancestry_bytes"]
    compact_sizes = [s["compact_ancestry_bytes"] for s in sizes]
    assert max(compact_sizes) - min(compact_sizes) < 100
