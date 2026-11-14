import json
import pytest
from individual_bundle import (
    IndividualBundle, verify_bundle_basic, _canonical, _hash,
    _merkle_root,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_full,
)
from compact_memory import (
    CheckpointRecord, compact_bundle,
    verify_compacted_basic, verify_compacted_full,
    verify_compacted_continuity,
    verify_bundle_for_resume,
    demo, HAS_CRYPTO, _find_checkpoint, _entry_hash,
)
from world_agent_coupling import ScriptedWorld
from coupled_learners import TinyRNN, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(k_b, prng):
    return ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)


def _build_individual(n_worlds=3, steps=15):
    kp = _kp()
    model = TinyRNN(n_extra_inputs=0, seed=42)
    memory: list = []
    sessions = []
    for i in range(n_worlds):
        s = FederatedSession(
            individual_kp=kp, model=model,
            world=_world(i * 25, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 20, 800),
            memory=memory, rule=SIERPINSKI)
        for _ in range(steps):
            s.step()
        sessions.append(s)
    return kp, model, sessions, memory


def _build_bundle(n_worlds=3, steps=15):
    kp, model, sessions, memory = _build_individual(n_worlds, steps)
    bundle = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="test", initial_seed=42, name="test")
    return kp, bundle


# -- Checkpoint record --

def test_checkpoint_record_roundtrip():
    kp = _kp()
    body = {
        "type": "checkpoint",
        "individual_id": "did:key:aa",
        "checkpoint_step": 10,
        "pre_checkpoint_merkle_root": "11" * 32,
        "pre_checkpoint_entry_count": 10,
        "weights_at_checkpoint_hash": "22" * 32,
        "action_distribution": {"0": 5, "1": 3, "2": 2},
        "total_reward_micros": 1500000,
        "ts": "t",
    }
    sig = kp.sign(_canonical(body)).hex()
    cp = CheckpointRecord(
        individual_id=body["individual_id"],
        checkpoint_step=10,
        pre_checkpoint_merkle_root=body[
            "pre_checkpoint_merkle_root"],
        pre_checkpoint_entry_count=10,
        weights_at_checkpoint_hash=body[
            "weights_at_checkpoint_hash"],
        action_distribution=body["action_distribution"],
        total_reward_micros=1500000,
        ts="t", sig=sig)
    cp2 = CheckpointRecord.from_dict(cp.to_dict())
    assert cp2.record_hash() == cp.record_hash()


# -- Compaction --

def test_compact_creates_checkpoint():
    kp, bundle = _build_bundle(n_worlds=2, steps=15)
    compacted, reason = compact_bundle(bundle, kp, keep_from_step=20)
    assert compacted is not None, reason
    assert compacted.manifest["compacted_at"] == \
           bundle.manifest["memory_entries"] - 20
    assert compacted.memory[0]["type"] == "checkpoint"
    assert compacted.checkpoint_weights is not None


def test_compact_reduces_memory():
    kp, bundle = _build_bundle(n_worlds=3, steps=15)
    orig_entries = bundle.manifest["memory_entries"]
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=20)
    assert compacted.manifest["memory_entries"] == 1 + 20
    assert compacted.manifest["memory_entries"] < orig_entries


def test_compact_preserves_tail():
    kp, bundle = _build_bundle(n_worlds=2, steps=15)
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=15)
    # Last 15 entries of compacted (after checkpoint) ==
    # last 15 of bundle
    kept = compacted.memory[1:]
    assert kept == bundle.memory[-15:]


def test_compact_requires_matching_key():
    kp, bundle = _build_bundle()
    wrong_kp = _kp()
    compacted, reason = compact_bundle(
        bundle, wrong_kp, keep_from_step=10)
    assert compacted is None
    assert "keypair" in reason.lower()


def test_compact_rejects_too_many_kept():
    kp, bundle = _build_bundle()
    compacted, reason = compact_bundle(
        bundle, kp,
        keep_from_step=bundle.manifest["memory_entries"])
    assert compacted is None


def test_compact_rejects_empty_checkpoint():
    kp, bundle = _build_bundle()
    # keep_from_step >= memory length → checkpoint_step = 0
    compacted, _ = compact_bundle(
        bundle, kp,
        keep_from_step=bundle.manifest["memory_entries"] - 1)
    # checkpoint_step = 1, valid
    assert compacted is not None


# -- Verification --

def test_compacted_basic_passes():
    kp, bundle = _build_bundle()
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=15)
    ok, reason = verify_compacted_basic(compacted)
    assert ok, reason


def test_compacted_full_passes():
    kp, bundle = _build_bundle(n_worlds=2, steps=15)
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=15)
    ok, reason = verify_compacted_full(compacted)
    assert ok, reason


def test_compacted_full_rejects_non_compacted():
    kp, bundle = _build_bundle()
    ok, reason = verify_compacted_full(bundle)
    assert not ok
    assert "not compacted" in reason.lower()


def test_continuity_passes():
    kp, bundle = _build_bundle(n_worlds=2, steps=15)
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=15)
    ok, reason = verify_compacted_continuity(compacted, bundle)
    assert ok, reason


def test_continuity_wrong_original():
    kp1, bundle1 = _build_bundle()
    kp2, bundle2 = _build_bundle()
    compacted, _ = compact_bundle(bundle1, kp1, keep_from_step=10)
    ok, _ = verify_compacted_continuity(compacted, bundle2)
    assert not ok


# -- Tampering --

def test_tampered_checkpoint_breaks_continuity():
    kp, bundle = _build_bundle()
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=15)
    # Tamper the checkpoint's weights hash, re-sign everything
    tampered = IndividualBundle(
        manifest=dict(compacted.manifest),
        memory=list(compacted.memory),
        weights=dict(compacted.weights),
        initial_weights=compacted.initial_weights,
        observations=list(compacted.observations),
        ancestry=list(compacted.ancestry),
        checkpoint_weights=compacted.checkpoint_weights,
    )
    cp_body = {k: v for k, v in tampered.memory[0].items()
                if k != "sig"}
    cp_body["weights_at_checkpoint_hash"] = "ff" * 32
    tampered.memory[0] = {
        **cp_body, "sig": kp.sign(_canonical(cp_body)).hex()}
    tampered.manifest["memory_root"] = _merkle_root(
        [_entry_hash(r) for r in tampered.memory])
    body = {k: v for k, v in tampered.manifest.items()
             if k != "sig"}
    tampered.manifest["sig"] = kp.sign(
        _canonical(body)).hex()
    # Basic still passes (attacker holds the key)
    ok_basic, _ = verify_compacted_basic(tampered)
    assert ok_basic
    # Continuity fails (derived weights != tampered hash)
    ok_cont, _ = verify_compacted_continuity(tampered, bundle)
    assert not ok_cont


def test_tampered_tail_breaks_full():
    kp, bundle = _build_bundle(n_worlds=2, steps=15)
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=10)
    # Tamper a step in the kept tail
    for i, r in enumerate(compacted.memory):
        if r.get("type") == "agent_step":
            compacted.memory[i] = {**r, "action": 99}
            break
    ok, _ = verify_compacted_full(compacted)
    assert not ok


# -- Resume composition --

def test_resume_from_compacted():
    from resumable import resume_from_bundle, pack_resumed_bundle
    kp, bundle = _build_bundle(n_worlds=2, steps=15)
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=10)
    specs = [(10, (300, 700), 25, 0x9999)]
    sessions, reason = resume_from_bundle(
        compacted, kp, specs, verify_tier="compacted")
    assert sessions is not None, reason
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=compacted, individual_kp=kp,
        persona="resumed", name="resumed")
    ok, reason = verify_compacted_full(resumed)
    assert ok, reason


# -- Bundle for resume dispatch --

def test_bundle_for_resume_auto():
    kp, bundle = _build_bundle()
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=10)
    # Non-compacted: federated_full
    ok, _ = verify_bundle_for_resume(bundle)
    assert ok
    # Compacted: compacted_full
    ok, _ = verify_bundle_for_resume(compacted)
    assert ok


# -- Save/load --

def test_save_load_compacted(tmp_path):
    kp, bundle = _build_bundle()
    compacted, _ = compact_bundle(bundle, kp, keep_from_step=10)
    compacted.save(tmp_path / "c")
    assert (tmp_path / "c" / "checkpoint_weights.json").exists()
    loaded = IndividualBundle.load(tmp_path / "c")
    assert loaded.checkpoint_weights is not None
    ok, reason = verify_compacted_full(loaded)
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["original_federated_full"] is True
    assert audit["verification"]["compacted_basic"] is True
    assert audit["verification"]["compacted_full"] is True
    assert audit["verification"]["compacted_continuity"] is True
    assert audit["verification"]["resumed_basic"] is True
    assert audit["verification"]["resumed_full"] is True
    assert audit["verification"]["resumed_from"] is True
    assert audit["tampering"]["tampered_checkpoint_basic"] is True
    assert audit["tampering"]["tampered_checkpoint_continuity"] is False
    assert audit["sizes"]["compaction_ratio"] < 0.7
    assert (tmp_path / "compact_memory" /
            "compact_memory_demo.json").exists()
