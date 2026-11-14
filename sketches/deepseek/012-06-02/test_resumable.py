import json
import pytest
from individual_bundle import (
    IndividualBundle, verify_bundle_basic, _canonical, _hash,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
)
from compact_ancestry import (
    compute_compact_ancestry, slim_bundle,
    verify_compact_ancestry,
)
from compact_inheritance import (
    verify_compact_ancestry_with_inheritance,
)
from resumable import (
    resume_from_bundle, pack_resumed_bundle,
    verify_resumed_from, verify_resumed_bundle,
    demo, HAS_CRYPTO, WorldSpec,
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


def _build_chain(depth=2, steps=5):
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
                child_initial_seed=100 + i * 100)
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
            child_initial_seed=100 + i * 100,
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


_SPECS = [(15, (250, 750), 25, 0x1111),
           (10, (350, 650), 75, 0x2222)]


# -- Resume basics --

def test_resume_happy_path():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions, reason = resume_from_bundle(
        target, target_kp, _SPECS)
    assert sessions is not None, reason
    assert len(sessions) == 2


def test_resume_preserves_memory():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    n_before = len(target.memory)
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    n_after = len(sessions[-1].memory)
    # 2 world_entries + 25 agent_steps added
    assert n_after == n_before + 2 + 25
    # First n_before entries unchanged
    assert sessions[-1].memory[:n_before] == target.memory


def test_resume_preserves_weights_then_learns():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target = slim[-1]
    from individual_bundle import serialize_weights
    weights_before = serialize_weights(target)
    # Reconstruct the model the same way resume does
    from individual_bundle import build_model, apply_weights
    model = build_model(target.manifest["model_config"])
    apply_weights(model, target.weights)
    weights_at_start = serialize_weights(model)
    assert weights_at_start == weights_before
    # Now resume and learn — weights should change
    target_kp = kps[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    weights_after = serialize_weights(sessions[-1].model)
    assert weights_after != weights_before


# -- Keypair check --

def test_resume_wrong_keypair_fails():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target = slim[-1]
    wrong_kp = _kp()
    sessions, reason = resume_from_bundle(
        target, wrong_kp, _SPECS)
    assert sessions is None
    assert "does not match" in reason.lower()


# -- Tampered bundle --

def test_resume_tampered_bundle_fails():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target = slim[-1]
    # Tamper a memory entry
    tampered = IndividualBundle(
        manifest=dict(target.manifest),
        memory=[dict(r) for r in target.memory],
        weights=dict(target.weights),
        initial_weights=(dict(target.initial_weights)
                          if target.initial_weights else None),
        observations=list(target.observations),
        ancestry=list(target.ancestry),
    )
    for i, r in enumerate(tampered.memory):
        if r.get("type") == "agent_step":
            tampered.memory[i] = {**r, "action": 99}
            break
    sessions, reason = resume_from_bundle(
        tampered, kps[-1], _SPECS)
    assert sessions is None
    assert "basic" in reason.lower() or "full" in reason.lower()


# -- Empty specs --

def test_resume_empty_specs():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    sessions, reason = resume_from_bundle(
        slim[-1], kps[-1], [])
    assert sessions is None
    assert "empty" in reason.lower()


# -- Packing --

def test_packed_bundle_verifies():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    memory = sessions[-1].memory
    model = sessions[-1].model
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=memory, model=model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    v = verify_resumed_bundle(resumed, target)
    assert v[0], v[1]


def test_packed_bundle_has_merged_contexts():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    parent_contexts = target.manifest["world_contexts"]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    merged = resumed.manifest["world_contexts"]
    assert len(merged) == len(parent_contexts) + 2
    assert merged[:len(parent_contexts)] == parent_contexts


def test_packed_bundle_preserves_initial_weights():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target = slim[-1]
    target_kp = kps[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    # In this chain, gen2 is inheriting, so initial_weights
    # should be present
    if target.initial_weights is not None:
        assert resumed.initial_weights == target.initial_weights
    assert resumed.manifest.get("initial_weights_hash") == \
           target.manifest.get("initial_weights_hash")


# -- Continuity --

def test_verify_resumed_from_happy():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    ok, reason = verify_resumed_from(resumed, target)
    assert ok, reason


def test_verify_resumed_from_tampered():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    # Tamper resumed_from
    resumed.manifest = dict(resumed.manifest)
    resumed.manifest["resumed_from"] = "00" * 32
    body = {k: v for k, v in resumed.manifest.items()
             if k != "sig"}
    resumed.manifest["sig"] = target_kp.sign(
        _canonical(body)).hex()
    ok, _ = verify_resumed_from(resumed, target)
    assert not ok


def test_verify_resumed_from_tampered_prefix():
    """If the resumed memory's prefix is altered, verification
    fails even if resumed_from is unchanged."""
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    # Tamper a prefix entry (resumed_from stays the same)
    n = target.manifest["memory_entries"]
    for i in range(n):
        if resumed.memory[i].get("type") == "agent_step":
            resumed.memory[i] = {
                **resumed.memory[i], "action": 99}
            break
    ok, _ = verify_resumed_from(resumed, target)
    assert not ok


def test_verify_non_resumed_bundle():
    """A bundle without resumed_from passes trivially."""
    kps, full, slim, fetcher = _build_chain(depth=1, steps=5)
    ok, reason = verify_resumed_from(slim[0], slim[0])
    assert ok
    assert "not a resumed" in reason.lower()


# -- Compact tier still works --

def test_resumed_bundle_compact_ancestry():
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    # The resumed bundle preserved compact_ancestry from the
    # parent — verify_compact_ancestry_with_inheritance should
    # still pass
    ok, reason = verify_compact_ancestry_with_inheritance(
        resumed, fetcher)
    assert ok, reason


# -- Resume twice --

def test_resume_twice():
    """Resuming a resumed bundle: continuing the chain."""
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions1, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed1 = pack_resumed_bundle(
        sessions=sessions1, memory=sessions1[-1].memory,
        model=sessions1[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed1", name="resumed1")
    # Resume the resumed bundle
    more_specs = [(8, (300, 700), 50, 0x3333)]
    sessions2, reason = resume_from_bundle(
        resumed1, target_kp, more_specs)
    assert sessions2 is not None, reason
    resumed2 = pack_resumed_bundle(
        sessions=sessions2, memory=sessions2[-1].memory,
        model=sessions2[-1].model,
        parent_bundle=resumed1, individual_kp=target_kp,
        persona="resumed2", name="resumed2")
    v = verify_resumed_bundle(resumed2, resumed1)
    assert v[0], v[1]


# -- Save/load --

def test_save_load_resumed(tmp_path):
    kps, full, slim, fetcher = _build_chain(depth=2, steps=5)
    target_kp = kps[-1]
    target = slim[-1]
    sessions, _ = resume_from_bundle(target, target_kp, _SPECS)
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=target, individual_kp=target_kp,
        persona="resumed", name="resumed")
    resumed.save(tmp_path / "r")
    target.save(tmp_path / "p")
    loaded_r = IndividualBundle.load(tmp_path / "r")
    loaded_p = IndividualBundle.load(tmp_path / "p")
    v = verify_resumed_bundle(loaded_r, loaded_p)
    assert v[0], v[1]
    # resumed_from is preserved
    assert loaded_r.manifest["resumed_from"] == \
           loaded_p.manifest["memory_root"]


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["basic"] is True
    assert audit["verification"]["federated_full"] is True
    assert audit["verification"]["resumed_from"] is True
    assert audit["verification"]["compact_ancestry_with_inheritance"] is True
    assert audit["verification"]["composite"] is True
    assert audit["continuity"]["prefix_matches_parent"] is True
    assert audit["continuity"]["resumed_from_equals_parent_root"] is True
    assert audit["tampering"]["wrong_keypair_refused"] is True
    assert audit["tampering"]["tampered_parent_refused"] is True
    assert audit["tampering"]["tampered_resumed_from_detected"] is True
    assert audit["new_worlds_added"] == 2
    assert (tmp_path / "resumable" /
            "resumable_demo.json").exists()
    assert (tmp_path / "resumable" /
            "resumed" / "manifest.json").exists()
