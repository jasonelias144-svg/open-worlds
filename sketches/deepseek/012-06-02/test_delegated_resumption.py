import json
import pytest
from individual_bundle import (
    IndividualBundle, _canonical, _hash,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_full,
)
from resumable import verify_resumed_from
from delegated_resumption import (
    ResumptionDelegation, sign_resumption_delegation,
    verify_delegation, resume_with_delegation,
    pack_delegated_bundle, verify_delegated_basic,
    verify_delegated_full, verify_delegated_continuity,
    _split_memory, _verify_invariants,
    demo, HAS_CRYPTO, VALID_SCOPES,
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
        persona="test", initial_seed=42, name="test")
    return kp, bundle, model


def _delegate(bundle, kp, delegate_kp, n_specs=None):
    if n_specs is None:
        n_specs = [(10, (300, 700), 50, 0xCCCC)]
    delegation = sign_resumption_delegation(
        individual_kp=kp,
        delegate_did=__import__("individual_bundle")._did_from_kp(
            delegate_kp),
        resume_at_entry=bundle.manifest["memory_entries"],
        resume_at_memory_root=bundle.manifest["memory_root"],
        max_resumed_steps=20,
    )
    sessions, reason = resume_with_delegation(
        bundle, delegate_kp, delegation, n_specs)
    assert sessions is not None, reason
    return delegation, sessions


def _pack(bundle, sessions, delegation, delegate_kp):
    return pack_delegated_bundle(
        sessions=sessions,
        memory=sessions[-1].memory,
        model=sessions[-1].model,
        parent_bundle=bundle,
        delegation=delegation,
        delegate_kp=delegate_kp,
        persona="delegated", name="delegated")


# -- Record tests --

def test_delegation_signed():
    kp = _kp()
    target = "did:key:" + "01" * 32
    rec = sign_resumption_delegation(
        kp, target, resume_at_entry=10,
        resume_at_memory_root="00" * 32,
        max_resumed_steps=20)
    ok, _ = verify_delegation(rec)
    assert ok


def test_delegation_self_reference():
    kp = _kp()
    self_did = __import__("individual_bundle")._did_from_kp(kp)
    with pytest.raises(ValueError):
        sign_resumption_delegation(
            kp, self_did, resume_at_entry=0,
            resume_at_memory_root="00" * 32,
            max_resumed_steps=10)


def test_delegation_bad_scope():
    kp = _kp()
    with pytest.raises(ValueError):
        sign_resumption_delegation(
            kp, "did:key:" + "01" * 32,
            resume_at_entry=0,
            resume_at_memory_root="00" * 32,
            max_resumed_steps=10,
            scopes=["god"])


def test_delegation_zero_steps():
    kp = _kp()
    with pytest.raises(ValueError):
        sign_resumption_delegation(
            kp, "did:key:" + "01" * 32,
            resume_at_entry=0,
            resume_at_memory_root="00" * 32,
            max_resumed_steps=0)


def test_delegation_wrong_individual_rejected():
    kp = _kp()
    target = "did:key:" + "01" * 32
    rec = sign_resumption_delegation(
        kp, target, resume_at_entry=5,
        resume_at_memory_root="11" * 32,
        max_resumed_steps=10)
    ok, _ = verify_delegation(
        rec, expected_individual="did:key:" + "ff" * 32)
    assert not ok


def test_delegation_scope_requirement():
    kp = _kp()
    target = "did:key:" + "01" * 32
    rec = sign_resumption_delegation(
        kp, target, resume_at_entry=5,
        resume_at_memory_root="11" * 32,
        max_resumed_steps=10)
    ok, _ = verify_delegation(rec, required_scopes={"resume"})
    assert ok
    ok, _ = verify_delegation(rec, required_scopes={"compact"})
    assert not ok


# -- Resume --

def test_resume_with_delegation_happy():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    assert len(sessions) == 1


def test_resume_with_wrong_delegate_fails():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    other_kp = _kp()
    delegation = sign_resumption_delegation(
        individual_kp=kp,
        delegate_did=__import__("individual_bundle")._did_from_kp(
            delegate_kp),
        resume_at_entry=bundle.manifest["memory_entries"],
        resume_at_memory_root=bundle.manifest["memory_root"],
        max_resumed_steps=20)
    sessions, reason = resume_with_delegation(
        bundle, other_kp, delegation,
        [(5, (300, 700), 50, 0xCCCC)])
    assert sessions is None
    assert "does not match" in reason.lower()


def test_resume_stale_delegation_fails():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation = sign_resumption_delegation(
        individual_kp=kp,
        delegate_did=__import__("individual_bundle")._did_from_kp(
            delegate_kp),
        resume_at_entry=5,  # wrong: actual is bundle.memory_entries
        resume_at_memory_root=bundle.manifest["memory_root"],
        max_resumed_steps=20)
    sessions, _ = resume_with_delegation(
        bundle, delegate_kp, delegation,
        [(5, (300, 700), 50, 0xCCCC)])
    assert sessions is None


def test_resume_wrong_memory_root_fails():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation = sign_resumption_delegation(
        individual_kp=kp,
        delegate_did=__import__("individual_bundle")._did_from_kp(
            delegate_kp),
        resume_at_entry=bundle.manifest["memory_entries"],
        resume_at_memory_root="00" * 32,
        max_resumed_steps=20)
    sessions, _ = resume_with_delegation(
        bundle, delegate_kp, delegation,
        [(5, (300, 700), 50, 0xCCCC)])
    assert sessions is None


# -- Pack + verify --

def test_delegated_basic_verifies():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    ok, reason = verify_delegated_basic(delegated)
    assert ok, reason


def test_delegated_full_verifies():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    ok, reason = verify_delegated_full(delegated)
    assert ok, reason


def test_delegated_continuity_verifies():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    ok, reason = verify_delegated_continuity(delegated, bundle)
    assert ok, reason


# -- Scope enforcement --

def test_exceed_max_steps_detected():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation = sign_resumption_delegation(
        individual_kp=kp,
        delegate_did=__import__("individual_bundle")._did_from_kp(
            delegate_kp),
        resume_at_entry=bundle.manifest["memory_entries"],
        resume_at_memory_root=bundle.manifest["memory_root"],
        max_resumed_steps=5)
    # Request 10 steps — exceeds 5
    sessions, reason = resume_with_delegation(
        bundle, delegate_kp, delegation,
        [(10, (300, 700), 50, 0xCCCC)])
    assert sessions is not None, reason
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    ok, reason = verify_delegated_basic(delegated)
    assert not ok
    assert "max_resumed_steps" in reason.lower()


def test_disallowed_world_detected():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    # Restrict to a world id that won't match
    delegation = sign_resumption_delegation(
        individual_kp=kp,
        delegate_did=__import__("individual_bundle")._did_from_kp(
            delegate_kp),
        resume_at_entry=bundle.manifest["memory_entries"],
        resume_at_memory_root=bundle.manifest["memory_root"],
        max_resumed_steps=20,
        allowed_world_ids=["did:key:" + "ff" * 32])
    sessions, _ = resume_with_delegation(
        bundle, delegate_kp, delegation,
        [(5, (300, 700), 50, 0xCCCC)])
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    ok, reason = verify_delegated_basic(delegated)
    assert not ok
    assert "allowed_world_ids" in reason.lower()


def test_expired_delegation_detected():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    # Delegation with valid_until in the past — resume succeeds
    # (no time check during resume), but verification catches it
    delegation = sign_resumption_delegation(
        individual_kp=kp,
        delegate_did=__import__("individual_bundle")._did_from_kp(
            delegate_kp),
        resume_at_entry=bundle.manifest["memory_entries"],
        resume_at_memory_root=bundle.manifest["memory_root"],
        max_resumed_steps=20,
        valid_from="2020-01-01T00:00:00+00:00",
        valid_until="2020-12-31T23:59:59+00:00")
    sessions, _ = resume_with_delegation(
        bundle, delegate_kp, delegation,
        [(5, (300, 700), 50, 0xCCCC)])
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    ok, reason = verify_delegated_basic(delegated)
    assert not ok
    assert "expired" in reason.lower()


# -- Tampering with memory --

def test_tampered_pre_boundary_memory_fails():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    # Tamper an entry in the pre-boundary range
    K = delegation.resume_at_entry
    for i in range(K):
        if delegated.memory[i].get("type") == "agent_step":
            delegated.memory[i] = {
                **delegated.memory[i], "action": 99}
            break
    ok, _ = verify_delegated_basic(delegated)
    assert not ok


def test_tampered_post_boundary_memory_fails():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    K = delegation.resume_at_entry
    for i in range(K, len(delegated.memory)):
        if delegated.memory[i].get("type") == "agent_step":
            delegated.memory[i] = {
                **delegated.memory[i], "action": 99}
            break
    ok, _ = verify_delegated_basic(delegated)
    assert not ok


# -- Continuity tampering --

def test_stale_continuity_fails():
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    # Build a different parent to compare against
    _, other_parent, _ = _build_parent()
    ok, _ = verify_delegated_continuity(delegated, other_parent)
    assert not ok


# -- Save/load --

def test_save_load_delegated(tmp_path):
    kp, bundle, _ = _build_parent()
    delegate_kp = _kp()
    delegation, sessions = _delegate(bundle, kp, delegate_kp)
    delegated = _pack(bundle, sessions, delegation, delegate_kp)
    delegated.save(tmp_path / "d")
    bundle.save(tmp_path / "p")
    loaded_d = IndividualBundle.load(tmp_path / "d")
    loaded_p = IndividualBundle.load(tmp_path / "p")
    ok, reason = verify_delegated_continuity(loaded_d, loaded_p)
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["basic"] is True
    assert audit["verification"]["full"] is True
    assert audit["verification"]["continuity"] is True
    assert audit["tampering"]["wrong_delegate_refused"] is True
    assert audit["tampering"]["over_scope_detected"] is True
    assert audit["tampering"]["stale_delegation_refused"] is True
    assert audit["tampering"]["expired_delegation_detected"] is True
    assert (tmp_path / "delegated_resumption" /
            "delegated_resumption_demo.json").exists()
