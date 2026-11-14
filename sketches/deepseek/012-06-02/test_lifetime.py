import json
import pytest
from individual_bundle import (
    IndividualBundle, _canonical, _hash, _merkle_root,
    serialize_weights, _did_from_kp,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_full,
)
from resumable import (
    resume_from_bundle, pack_resumed_bundle,
    verify_resumed_from,
)
from delegated_resumption import (
    sign_resumption_delegation, resume_with_delegation,
    pack_delegated_bundle, verify_delegated_continuity,
)
from forking import (
    fork_from_bundle, sign_fork_record_with_parent,
    pack_fork_bundle,
)
from federated_spawn import _replay_federated_to_index
from lifetime import (
    LifetimeReport, verify_individual_lifetime,
    _verify_bundle_at_tier, _build_timeline,
    demo, HAS_CRYPTO, _entry_hash,
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


def _build_a(n_worlds=2, steps=8):
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
        persona="A", initial_seed=42, name="A")
    return kp, bundle, model


def _resume(bundle, kp, specs):
    sessions, reason = resume_from_bundle(bundle, kp, specs)
    assert sessions is not None, reason
    return pack_resumed_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=bundle, individual_kp=kp,
        persona="resumed", name="resumed")


def _delegated_resume(bundle, kp, delegate_kp, specs):
    delegate_id = _did_from_kp(delegate_kp)
    delegation = sign_resumption_delegation(
        individual_kp=kp, delegate_did=delegate_id,
        resume_at_entry=bundle.manifest["memory_entries"],
        resume_at_memory_root=bundle.manifest["memory_root"],
        max_resumed_steps=20)
    sessions, reason = resume_with_delegation(
        bundle, delegate_kp, delegation, specs)
    assert sessions is not None, reason
    return pack_delegated_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=bundle, delegation=delegation,
        delegate_kp=delegate_kp, persona="delegated",
        name="delegated")


# -- Tier dispatch --

def test_tier_dispatch_federated():
    kp, A, _ = _build_a()
    r = _verify_bundle_at_tier(A)
    assert r["tier"] == "federated"
    assert r["ok"]


def test_tier_dispatch_delegated():
    kp, A, _ = _build_a()
    delegate_kp = _kp()
    D = _delegated_resume(
        A, kp, delegate_kp, [(5, (300, 700), 25, 0xCCCC)])
    r = _verify_bundle_at_tier(D)
    assert r["tier"] == "delegated"
    assert r["ok"]


def test_tier_dispatch_forked():
    kp, A, _ = _build_a()
    K = A.manifest["memory_entries"]
    f_kp = _kp()
    f_id = _did_from_kp(f_kp)
    a_model_at_k, _ = _replay_federated_to_index(A, K)
    w_at_k = serialize_weights(a_model_at_k)
    from forking import _weights_hash
    prefix_root = _merkle_root(
        [_entry_hash(r) for r in A.memory[:K]])
    fork_record = sign_fork_record_with_parent(
        parent_kp=kp, parent=A, fork_id=f_id,
        fork_at_entry=K, fork_at_memory_root=prefix_root,
        fork_weights_hash=_weights_hash(w_at_k))
    sessions, _, _, reason = fork_from_bundle(
        parent=A, fork_kp=f_kp, fork_at_entry=K,
        world_specs=[(5, (300, 700), 25, 0xCCCC)])
    assert sessions is not None, reason
    F = pack_fork_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=A, fork_kp=f_kp,
        fork_record=fork_record, persona="fork", name="fork")
    r = _verify_bundle_at_tier(F)
    assert r["tier"] == "forked"
    assert r["ok"]


# -- Single-bundle lifetime --

def test_single_bundle_lifetime():
    kp, A, _ = _build_a()
    report = verify_individual_lifetime(
        {A.individual_id: A}, A.individual_id)
    assert report.ok
    assert report.origin_id == A.individual_id
    assert len(report.bundles) == 1
    assert len(report.edges) == 0
    assert len(report.timeline) == 1


# -- Chain of three --

def test_chain_of_three():
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    C = _resume(B, kp, [(10, (400, 600), 50, 0xDDDD)])
    bundles = {A.individual_id: A,
                B.individual_id: B,
                C.individual_id: C}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    assert report.ok
    assert len(report.bundles) == 3
    assert len(report.edges) == 2
    assert all(e["ok"] for e in report.edges)


# -- Mixed tiers --

def test_mixed_tier_chain():
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    curator_kp = _kp()
    C = _delegated_resume(
        B, kp, curator_kp, [(10, (400, 600), 50, 0xDDDD)])
    bundles = {A.individual_id: A,
                B.individual_id: B,
                C.individual_id: C}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    assert report.ok
    # Check tiers present
    tiers = {b["tier"] for b in report.bundles}
    assert "federated" in tiers
    assert "delegated" in tiers


# -- Broken edge --

def test_broken_resume_edge_detected():
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    # Tamper B's resumed_from
    B.manifest = dict(B.manifest)
    B.manifest["resumed_from"] = "00" * 32
    body = {k: v for k, v in B.manifest.items() if k != "sig"}
    B.manifest["sig"] = kp.sign(_canonical(body)).hex()
    bundles = {A.individual_id: A,
                B.individual_id: B}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    assert not report.ok
    # Should be a gap, not an edge break
    assert any("not in bundle set" in e
                for e in report.errors)


# -- Missing intermediate --

def test_missing_intermediate_detected():
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    C = _resume(B, kp, [(10, (400, 600), 50, 0xDDDD)])
    # Remove B
    bundles = {A.individual_id: A,
                C.individual_id: C}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    assert not report.ok
    assert any("not in bundle set" in e
                for e in report.errors)


# -- Multiple origins --

def test_multiple_origins_warning():
    """Two bundles claim to be origins (malformed but should
    be caught as warning, not error)."""
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    # Remove A → B has no resumed_from parent in set → gap error
    bundles = {B.individual_id: B}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    # B has individual_id == A.individual_id (resumed), so
    # included in filter, but its resumed_from points to A
    # which isn't in the set
    assert not report.ok


# -- Branches --

def test_fork_reported_as_branch():
    kp, A, _ = _build_a()
    K = A.manifest["memory_entries"]
    f_kp = _kp()
    f_id = _did_from_kp(f_kp)
    a_model_at_k, _ = _replay_federated_to_index(A, K)
    w_at_k = serialize_weights(a_model_at_k)
    from forking import _weights_hash
    prefix_root = _merkle_root(
        [_entry_hash(r) for r in A.memory[:K]])
    fork_record = sign_fork_record_with_parent(
        parent_kp=kp, parent=A, fork_id=f_id,
        fork_at_entry=K, fork_at_memory_root=prefix_root,
        fork_weights_hash=_weights_hash(w_at_k))
    sessions, _, _, _ = fork_from_bundle(
        parent=A, fork_kp=f_kp, fork_at_entry=K,
        world_specs=[(5, (300, 700), 25, 0xCCCC)])
    F = pack_fork_bundle(
        sessions=sessions, memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=A, fork_kp=f_kp,
        fork_record=fork_record, persona="fork", name="fork")
    bundles = {A.individual_id: A,
                F.individual_id: F}
    report = verify_individual_lifetime(
        bundles, A.individual_id, include_branches=True)
    assert report.ok
    assert len(report.branches) == 1
    assert report.branches[0]["id"] == F.individual_id
    assert report.branches[0]["ok"]


# -- Save/load --

def test_save_load_lifetime(tmp_path):
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    A.save(tmp_path / "a")
    B.save(tmp_path / "b")
    A_loaded = IndividualBundle.load(tmp_path / "a")
    B_loaded = IndividualBundle.load(tmp_path / "b")
    bundles = {A_loaded.individual_id: A_loaded,
                B_loaded.individual_id: B_loaded}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    assert report.ok
    assert len(report.bundles) == 2


# -- Timeline --

def test_timeline_events():
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    bundles = {A.individual_id: A,
                B.individual_id: B}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    assert len(report.timeline) == 2
    assert report.timeline[0]["event"] == "origin"
    assert report.timeline[1]["event"] == "resume"


# -- Cycle detection --

def test_no_cycle_in_valid_chain():
    kp, A, _ = _build_a()
    B = _resume(A, kp, [(10, (300, 700), 25, 0xCCCC)])
    C = _resume(B, kp, [(10, (400, 600), 50, 0xDDDD)])
    bundles = {A.individual_id: A,
                B.individual_id: B,
                C.individual_id: C}
    report = verify_individual_lifetime(
        bundles, A.individual_id)
    assert report.ok
    assert not any("cycle" in e for e in report.errors)


# -- Non-existent individual --

def test_nonexistent_individual():
    kp, A, _ = _build_a()
    report = verify_individual_lifetime(
        {A.individual_id: A},
        "did:key:" + "00" * 32)
    assert not report.ok
    assert any("no bundles" in e for e in report.errors)


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["lifetime_a"]["ok"] is True
    assert audit["lifetime_f"]["ok"] is True
    assert len(audit["lifetime_a"]["bundles"]) == 3
    assert len(audit["lifetime_a"]["edges"]) == 2
    assert len(audit["lifetime_a"]["branches"]) == 1
    assert audit["tampering"]["broken_edge_ok"] is False
    assert audit["tampering"]["missing_b_ok"] is False
    assert (tmp_path / "lifetime" /
            "lifetime_demo.json").exists()
