import json
import pytest
from pathlib import Path
from individual_bundle import (
    IndividualBundle, verify_bundle_basic, _hash, _canonical,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_basic, verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
)
from lineage_root import (
    verify_lineage_root, verify_lineage_root_is_origin, demo,
    HAS_CRYPTO,
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


def _build_chain(gen0_steps=20, gen1_steps=15, gen2_steps=10):
    """3-gen chain, lineage_root propagated."""
    gp_kp = _kp()
    gp_model = TinyRNN(n_extra_inputs=0, seed=42)
    gp_mem: list = []
    s = FederatedSession(
        individual_kp=gp_kp, model=gp_model,
        world=_world(0, 0xAAAA), initial_point=(200, 800),
        memory=gp_mem, rule=SIERPINSKI)
    for _ in range(gen0_steps):
        s.step()
    gp_sessions = [s]
    p_kp, p_model, spawn0, w0 = spawn_federated_child(
        parent_session=s, child_persona="p",
        child_initial_seed=200)
    s.step()
    gp_b = pack_federated_bundle(
        individual_kp=gp_kp, model=gp_model,
        sessions=gp_sessions, memory=gp_mem,
        persona="gp", initial_seed=42, name="grandparent")

    p_mem: list = []
    s1 = FederatedSession(
        individual_kp=p_kp, model=p_model,
        world=_world(25, 0xDDDD), initial_point=(250, 750),
        memory=p_mem, rule=SIERPINSKI)
    for _ in range(gen1_steps):
        s1.step()
    p_sessions = [s1]
    c_kp, c_model, spawn1, w1 = spawn_federated_child(
        parent_session=s1, child_persona="c",
        child_initial_seed=300)
    s1.step()
    p_b = pack_federated_child(
        child_kp=p_kp, child_model=p_model,
        child_sessions=p_sessions, child_memory=p_mem,
        child_persona="p", child_initial_seed=200,
        parent_bundle=gp_b, spawn_record=spawn0,
        inherited_weights=w0, name="parent")

    c_mem: list = []
    s2 = FederatedSession(
        individual_kp=c_kp, model=c_model,
        world=_world(75, 0x1234), initial_point=(300, 700),
        memory=c_mem, rule=SIERPINSKI)
    for _ in range(gen2_steps):
        s2.step()
    c_b = pack_federated_child(
        child_kp=c_kp, child_model=c_model,
        child_sessions=[s2], child_memory=c_mem,
        child_persona="c", child_initial_seed=300,
        parent_bundle=p_b, spawn_record=spawn1,
        inherited_weights=w1, name="child")

    return gp_b, p_b, c_b, gp_kp, p_kp, c_kp


# -- Basic lineage_root --

def test_origin_is_self_root():
    gp, _, _, *_ = _build_chain()
    assert gp.manifest["lineage_root"] == gp.individual_id
    assert gp.ancestry == []
    ok, reason = verify_lineage_root(gp)
    assert ok, reason


def test_descendant_carries_ancestry():
    _, p, c, *_ = _build_chain()
    assert len(p.ancestry) == 1
    assert len(c.ancestry) == 2
    assert p.ancestry[0]["child_id"] == p.individual_id
    assert c.ancestry[0]["child_id"] == c.individual_id
    assert c.ancestry[1]["child_id"] == p.individual_id


def test_descendant_lineage_root_points_to_origin():
    gp, p, c, *_ = _build_chain()
    assert p.manifest["lineage_root"] == gp.individual_id
    assert c.manifest["lineage_root"] == gp.individual_id


def test_single_bundle_proves_descent():
    gp, p, c, *_ = _build_chain()
    ok, reason = verify_lineage_root(c)
    assert ok, reason
    assert "descends" in reason.lower()


def test_parent_single_bundle_proves_descent():
    gp, p, c, *_ = _build_chain()
    ok, reason = verify_lineage_root(p)
    assert ok, reason


# -- Full origin verification --

def test_child_descends_from_verified_origin():
    gp, p, c, *_ = _build_chain()
    ok, reason = verify_lineage_root_is_origin(c, gp)
    assert ok, reason


def test_origin_check_fails_wrong_root_bundle():
    gp, p, c, *_ = _build_chain()
    # Supply parent as "root" — its lineage_root != itself
    ok, _ = verify_lineage_root_is_origin(c, p)
    assert not ok


def test_origin_check_fails_non_self_root():
    gp, p, c, *_ = _build_chain()
    # Build a "fake origin" that claims to descend from someone
    from federated_bundle import pack_federated_bundle
    fake_kp = _kp()
    fake_model = TinyRNN(n_extra_inputs=0, seed=1)
    fake_mem: list = []
    s = FederatedSession(
        individual_kp=fake_kp, model=fake_model,
        world=_world(0, 0xBAD), initial_point=(0, 0),
        memory=fake_mem, rule=SIERPINSKI)
    for _ in range(5):
        s.step()
    fake_b = pack_federated_bundle(
        individual_kp=fake_kp, model=fake_model,
        sessions=[s], memory=fake_mem,
        persona="fake", initial_seed=1, name="fake",
        lineage_root="did:key:" + "00" * 32,  # fake root
    )
    ok, _ = verify_lineage_root_is_origin(c, fake_b)
    assert not ok


# -- Save / load --

def test_ancestry_saved_and_loaded(tmp_path):
    gp, p, c, *_ = _build_chain()
    c.save(tmp_path / "c")
    assert (tmp_path / "c" / "ancestry.json").exists()
    loaded = IndividualBundle.load(tmp_path / "c")
    assert len(loaded.ancestry) == 2
    ok, _ = verify_lineage_root(loaded)
    assert ok


def test_origin_bundle_has_no_ancestry_file(tmp_path):
    gp, p, c, *_ = _build_chain()
    gp.save(tmp_path / "gp")
    assert not (tmp_path / "gp" / "ancestry.json").exists()
    loaded = IndividualBundle.load(tmp_path / "gp")
    assert loaded.ancestry == []


# -- Tampering --

def test_removed_ancestry_breaks_basic():
    gp, p, c, *_ = _build_chain()
    c.ancestry = []
    ok, reason = verify_bundle_basic(c)
    assert not ok
    assert "ancestry" in reason.lower()


def test_removed_ancestry_breaks_lineage_root():
    gp, p, c, *_ = _build_chain()
    c.ancestry = []
    ok, _ = verify_lineage_root(c)
    assert not ok


def test_corrupted_ancestry_sig_breaks_lineage():
    gp, p, c, *_ = _build_chain()
    c.ancestry = [dict(r) for r in c.ancestry]
    c.ancestry[0]["sig"] = "00" * 64
    # basic should fail (ancestry_hash mismatch)
    ok_basic, _ = verify_bundle_basic(c)
    assert not ok_basic
    # and lineage_root should fail (sig invalid)
    ok_root, reason = verify_lineage_root(c)
    assert not ok_root
    assert "invalid" in reason.lower() or "sig" in reason.lower()


def test_wrong_lineage_root_breaks_verification():
    gp, p, c, *_ = _build_chain()
    c.manifest = dict(c.manifest)
    c.manifest["lineage_root"] = "did:key:" + "00" * 32
    # Re-sign so basic passes
    body = {k: v for k, v in c.manifest.items() if k != "sig"}
    c.manifest["sig"] = _kp().sign(_canonical(body)).hex()
    # Basic fails (bad signer) — good, but even if signature
    # were valid, lineage_root would fail
    ok_basic, _ = verify_bundle_basic(c)
    assert not ok_basic


# -- Composability --

def test_federated_full_still_works():
    """lineage_root addition doesn't break federated full."""
    gp, p, c, *_ = _build_chain()
    for b in (gp, p, c):
        ok, reason = verify_federated_full(b)
        assert ok, reason


def test_no_lineage_root_old_bundle():
    """An old-style bundle (no lineage_root) doesn't crash."""
    from federated_bundle import pack_federated_bundle
    kp = _kp()
    model = TinyRNN(n_extra_inputs=0, seed=1)
    mem: list = []
    s = FederatedSession(
        individual_kp=kp, model=model,
        world=_world(0, 0xBEEF), initial_point=(0, 0),
        memory=mem, rule=SIERPINSKI)
    for _ in range(5):
        s.step()
    # Build via pack_federated_bundle — it defaults
    # lineage_root to individual_id
    b = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=[s], memory=mem,
        persona="old", initial_seed=1)
    # Actually — pack sets lineage_root = individual_id, so it
    # is self-root. Testing the "no lineage_root" case requires
    # deleting the field from the manifest.
    b.manifest = dict(b.manifest)
    del b.manifest["lineage_root"]
    ok, reason = verify_lineage_root(b)
    assert not ok
    assert "no lineage_root" in reason.lower()


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["gp_root"] is True
    assert audit["verification"]["parent_root"] is True
    assert audit["verification"]["child_root"] is True
    assert audit["verification"]["child_root_is_origin"] is True
    assert all(audit["verification"]["federated_full"].values())
    assert audit["tampering"]["removed_ancestry_detected"] is True
    assert audit["tampering"]["corrupt_sig_detected_basic"] is True
    assert audit["tampering"]["corrupt_sig_detected_root"] is True
    assert audit["ancestry_lengths"]["grandparent"] == 0
    assert audit["ancestry_lengths"]["parent"] == 1
    assert audit["ancestry_lengths"]["child"] == 2
    assert (tmp_path / "lineage_root" /
            "lineage_root_demo.json").exists()
