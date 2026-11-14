import json
import pytest
from individual_bundle import (
    IndividualBundle, verify_bundle_basic, _canonical, _hash,
    _merkle_root, _did_from_kp,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_full,
)
from forking import (
    ForkRecord, fork_from_bundle,
    sign_fork_record_with_parent, pack_fork_bundle,
    verify_forked_basic, verify_forked_full,
    verify_fork_continuity,
    demo, HAS_CRYPTO, _entry_hash, _weights_hash,
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


def _build_parent(n_worlds=2, steps=10):
    kp = _kp()
    model = TinyRNN(n_extra_inputs=0, seed=42)
    memory: list = []
    sessions = []
    for i in range(n_worlds):
        s = FederatedSession(
            individual_kp=kp, model=model,
            world=_world(i * 10, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 20, 800),
            memory=memory, rule=SIERPINSKI)
        for _ in range(steps):
            s.step()
        sessions.append(s)
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="parent", initial_seed=42, name="parent")
    return kp, bundle, model


def _fork(parent, parent_kp, fork_kp, K, specs):
    from federated_spawn import _replay_federated_to_index
    parent_model_at_k, _ = _replay_federated_to_index(parent, K)
    weights_at_k = __import__(
        "individual_bundle").serialize_weights(parent_model_at_k)
    prefix_root = _merkle_root(
        [_entry_hash(r) for r in parent.memory[:K]])
    fork_record = sign_fork_record_with_parent(
        parent_kp=parent_kp, parent=parent,
        fork_id=_did_from_kp(fork_kp),
        fork_at_entry=K,
        fork_at_memory_root=prefix_root,
        fork_weights_hash=_weights_hash(weights_at_k),
    )
    sessions, _, _, reason = fork_from_bundle(
        parent=parent, fork_kp=fork_kp,
        fork_at_entry=K, world_specs=specs)
    assert sessions is not None, reason
    bundle = pack_fork_bundle(
        sessions=sessions,
        memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=parent,
        fork_kp=fork_kp,
        fork_record=fork_record,
        persona="fork", name="fork",
    )
    return bundle, fork_record


_SPECS = [(10, (300, 700), 50, 0xCCCC)]


# -- Fork record --

def test_fork_record_self_ref():
    with pytest.raises(ValueError):
        ForkRecord(
            original_id="did:key:aa",
            fork_id="did:key:aa",
            fork_at_entry=5,
            fork_at_memory_root="00" * 32,
            fork_weights_hash="11" * 32,
            ts="t", sig="s")


def test_fork_record_negative_K():
    with pytest.raises(ValueError):
        ForkRecord(
            original_id="did:key:aa",
            fork_id="did:key:bb",
            fork_at_entry=-1,
            fork_at_memory_root="00" * 32,
            fork_weights_hash="11" * 32,
            ts="t", sig="s")


# -- Fork op --

def test_fork_at_tip():
    kp, parent, _ = _build_parent()
    fork_kp = _kp()
    K = parent.manifest["memory_entries"]
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    assert fork_bundle.manifest["fork_at_entry"] == K


def test_fork_at_mid():
    kp, parent, _ = _build_parent(n_worlds=2, steps=15)
    K = parent.manifest["memory_entries"] // 2
    fork_kp = _kp()
    # Mid-world is allowed
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    ok, reason = verify_forked_full(fork_bundle)
    assert ok, reason


def test_fork_rejects_negative_K():
    kp, parent, _ = _build_parent()
    fork_kp = _kp()
    sessions, _, _, reason = fork_from_bundle(
        parent, fork_kp, -1, _SPECS)
    assert sessions is None


def test_fork_rejects_K_too_large():
    kp, parent, _ = _build_parent()
    fork_kp = _kp()
    sessions, _, _, reason = fork_from_bundle(
        parent, fork_kp,
        parent.manifest["memory_entries"] + 1, _SPECS)
    assert sessions is None


def test_fork_rejects_compacted_parent():
    kp, parent, _ = _build_parent()
    from compact_memory import compact_bundle
    compacted, _ = compact_bundle(parent, kp, keep_from_step=10)
    fork_kp = _kp()
    sessions, _, _, reason = fork_from_bundle(
        compacted, fork_kp, 10, _SPECS)
    assert sessions is None
    assert "compacted" in reason.lower()


def test_fork_rejects_empty_specs():
    kp, parent, _ = _build_parent()
    fork_kp = _kp()
    sessions, _, _, reason = fork_from_bundle(
        parent, fork_kp,
        parent.manifest["memory_entries"], [])
    assert sessions is None


# -- Verification --

def test_forked_basic():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    ok, reason = verify_forked_basic(fork_bundle)
    assert ok, reason


def test_forked_full():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    ok, reason = verify_forked_full(fork_bundle)
    assert ok, reason


def test_fork_continuity():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    ok, reason = verify_fork_continuity(fork_bundle, parent)
    assert ok, reason


def test_non_fork_passes_base():
    kp, parent, _ = _build_parent()
    ok, _ = verify_forked_basic(parent)
    assert ok


# -- Tampering --

def test_shifted_K_breaks_basic():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    # Shift K by -5 (still valid prefix but wrong length)
    fork_bundle.manifest = dict(fork_bundle.manifest)
    fork_bundle.manifest["fork_at_entry"] = K - 5
    body = {k: v for k, v in fork_bundle.manifest.items()
             if k != "sig"}
    fork_bundle.manifest["sig"] = fork_kp.sign(
        _canonical(body)).hex()
    ok, _ = verify_forked_basic(fork_bundle)
    assert not ok


def test_forged_weights_hash_breaks_basic():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    # Tamper initial_weights_hash
    fork_bundle.manifest = dict(fork_bundle.manifest)
    fork_bundle.manifest["initial_weights_hash"] = "00" * 32
    body = {k: v for k, v in fork_bundle.manifest.items()
             if k != "sig"}
    fork_bundle.manifest["sig"] = fork_kp.sign(
        _canonical(body)).hex()
    ok, _ = verify_forked_basic(fork_bundle)
    assert not ok


def test_wrong_parent_breaks_continuity():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    # Build another parent
    _, other_parent, _ = _build_parent(n_worlds=1, steps=5)
    ok, _ = verify_fork_continuity(fork_bundle, other_parent)
    assert not ok


def test_altered_parent_memory_breaks_continuity():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    # Alter parent's past memory (breaks its own verification
    # AND fork's prefix comparison)
    parent.memory = list(parent.memory)
    for i, r in enumerate(parent.memory[:K]):
        if r.get("type") == "agent_step":
            parent.memory[i] = {**r, "action": 99}
            break
    ok, _ = verify_fork_continuity(fork_bundle, parent)
    assert not ok


def test_tampered_fork_record_sig():
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, fork_rec = _fork(parent, kp, fork_kp, K, _SPECS)
    # Tamper fork_record sig
    fork_bundle.manifest = dict(fork_bundle.manifest)
    fork_bundle.manifest["fork_record"] = {
        **fork_bundle.manifest["fork_record"],
        "sig": "00" * 64}
    body = {k: v for k, v in fork_bundle.manifest.items()
             if k != "sig"}
    fork_bundle.manifest["sig"] = fork_kp.sign(
        _canonical(body)).hex()
    ok, _ = verify_forked_basic(fork_bundle)
    assert not ok


# -- Save/load --

def test_save_load_fork(tmp_path):
    kp, parent, _ = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    fork_bundle.save(tmp_path / "f")
    parent.save(tmp_path / "p")
    loaded_f = IndividualBundle.load(tmp_path / "f")
    loaded_p = IndividualBundle.load(tmp_path / "p")
    ok, reason = verify_fork_continuity(loaded_f, loaded_p)
    assert ok, reason


# -- Parent continues after fork --

def test_parent_continues_independently():
    kp, parent, model = _build_parent()
    K = parent.manifest["memory_entries"]
    fork_kp = _kp()
    fork_bundle, _ = _fork(parent, kp, fork_kp, K, _SPECS)
    # Parent continues in a new world
    s = FederatedSession(
        individual_kp=kp, model=model,
        world=_world(75, 0xEEEE),
        initial_point=(400, 600),
        memory=list(parent.memory),
        rule=SIERPINSKI)
    for _ in range(10):
        s.step()
    # Parent still verifies
    parent_after = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=[s], memory=s.memory,
        persona="parent", initial_seed=42, name="parent")
    ok, _ = verify_federated_full(parent_after)
    assert ok
    # Fork still verifies independently
    ok, _ = verify_forked_full(fork_bundle)
    assert ok


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["parent_federated_full"] is True
    assert audit["verification"]["fork_basic"] is True
    assert audit["verification"]["fork_full"] is True
    assert audit["verification"]["fork_continuity"] is True
    assert audit["tampering"]["shifted_fork_at_entry_detected"] is True
    assert audit["tampering"]["forged_weights_hash_detected"] is True
    assert audit["tampering"]["wrong_parent_detected"] is True
    assert audit["tampering"]["altered_parent_detected"] is True
    assert (tmp_path / "forking" /
            "forking_demo.json").exists()
