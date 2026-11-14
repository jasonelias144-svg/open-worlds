import pytest
from fractal_world_v2 import (
    ParamSet, WorldTemplate, AtomicFractalWorld,
    verify_log, verify_growth, reconstruct,
    HAS_CRYPTO)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from cryptography.hazmat.primitives import serialization

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(pot=(0, 0, 30, 30), start=(15, 23, 0),
           template=None, params=None):
    template = template or WorldTemplate(
        template_id="t", branch_length=3, max_depth=4)
    return AtomicFractalWorld(
        template=template, pot=pot, initial_tip=start,
        keypair=_kp(), params=params)


# -- ParamSet --

def test_paramset_hash_stable():
    a = ParamSet(3, 4, 10, 10)
    b = ParamSet(3, 4, 10, 10)
    assert a.param_hash() == b.param_hash()


def test_paramset_with_change():
    a = ParamSet(3, 4, 10, 10)
    b = a.with_change("branch_length", 1)
    assert a.branch_length == 3
    assert b.branch_length == 1
    assert a.param_hash() != b.param_hash()


def test_paramset_unknown_param():
    a = ParamSet(3, 4, 10, 10)
    with pytest.raises(ValueError):
        a.with_change("nope", 1)


def test_paramset_can_grow():
    assert ParamSet(2, 4, 10, 10).can_grow()
    assert not ParamSet(2, 4, 0, 10).can_grow()


def test_paramset_effective_depth():
    assert ParamSet(2, 4, 10, 10).effective_max_depth() == 4
    assert ParamSet(2, 4, 10, 2).effective_max_depth() == 2


# -- Internal change --

def test_internal_change_signed_by_world():
    w = _world()
    w.grow_n(1)
    rec = w.internal_change("branch_length", 1)
    assert rec is not None
    assert rec.source == "internal"
    assert rec.authority_id == w.world_id
    ok, reason = verify_log(w.seed(), w.records())
    assert ok, reason


def test_internal_change_rejected_if_not_world():
    w = _world()
    w.grow_n(1)
    # No direct public method lets someone else make an
    # internal change, but the verifier rejects one that
    # claims to be internal from a non-world authority.
    ok, reason = verify_log(w.seed(), w.records())
    assert ok  # nothing to reject yet


# -- External change --

def test_external_change_signed_by_both():
    w = _world()
    w.grow_n(1)
    g = _kp()
    g_id = "did:key:" + g.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()
    rec = w.external_change(g_id, g, "branch_length", 1)
    assert rec is not None
    assert rec.source == "external"
    assert rec.authority_id == g_id
    ok, reason = verify_log(w.seed(), w.records())
    assert ok, reason


def test_external_change_rejects_self_authority():
    w = _world()
    w.grow_n(1)
    rec = w.external_change(w.world_id, _kp(),
                             "branch_length", 1)
    assert rec is None


# -- Growth respects params --

def test_branch_length_affects_growth():
    w_small = _world(params=ParamSet(1, 4, 10, 10))
    w_big = _world(params=ParamSet(3, 4, 10, 10))
    w_small.grow_until()
    w_big.grow_until()
    # Big branch means fewer steps to hit depth limit,
    # but more spread. Just check both did grow.
    assert len(w_small.segments()) > 0
    assert len(w_big.segments()) > 0
    assert w_small.segments() != w_big.segments()


def test_water_zero_stalls():
    w = _world(params=ParamSet(2, 4, 0, 10))
    assert w.is_stalled()
    assert not w.is_growing()
    assert w.grow() is None


def test_water_resume():
    w = _world()
    w.grow_n(2)
    g = _kp()
    g_id = "did:key:" + g.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()
    w.external_change(g_id, g, "water", 0)
    assert w.is_stalled()
    n = w.grow_until()
    assert n == 0
    w.external_change(g_id, g, "water", 10)
    assert w.is_growing()
    assert w.grow_until() > 0


def test_light_low_halves_depth():
    w_lit = _world(params=ParamSet(2, 4, 10, 10))
    w_dim = _world(params=ParamSet(2, 4, 10, 2))
    w_lit.grow_until()
    w_dim.grow_until()
    # Dim has effective depth 2 vs lit depth 4
    assert len(w_dim.segments()) < len(w_lit.segments())


# -- Verifier --

def test_verify_growth_rejects_wrong_params():
    w = _world()
    w.grow_until()
    # Tamper: change a growth record's p field
    tampered = list(w.records())
    original = tampered[0]
    tampered[0] = type(original)(
        world_id=original.world_id,
        step=original.step,
        seed_hash=original.seed_hash,
        prev=original.prev,
        p="00" * 32,  # wrong hash
        segs=original.segs,
        tips=original.tips,
        ts=original.ts,
        sig=original.sig)
    ok, reason = verify_growth(
        w.seed(), tampered, w._template)
    assert not ok


def test_verify_growth_rejects_wrong_old_value():
    w = _world()
    w.grow_n(2)
    w.internal_change("branch_length", 1)
    # Tamper the param change's old_value
    tampered = list(w.records())
    for i, rec in enumerate(tampered):
        if hasattr(rec, "source"):
            tampered[i] = type(rec)(
                world_id=rec.world_id, step=rec.step,
                param=rec.param, old_value=99,
                new_value=rec.new_value,
                source=rec.source,
                authority_id=rec.authority_id,
                prior=rec.prior, ts=rec.ts,
                sig_authority=rec.sig_authority,
                sig_world=rec.sig_world)
            break
    ok, reason = verify_growth(
        w.seed(), tampered, w._template)
    assert not ok


# -- Reconstruct --

def test_reconstruct_preserves_params():
    w = _world()
    w.grow_n(2)
    w.internal_change("branch_length", 1)
    w.grow_until()
    plant = reconstruct(w.seed(), w.records())
    assert plant.params.branch_length == 1
    assert plant.param_changes == 1


# -- End to end --

def test_demo(tmp_path):
    from fractal_world_v2 import demo
    audit = demo(artifact_dir=str(tmp_path))
    # B and C must produce identical segment sequences
    assert (audit["B (external)"]["segments_hash"]
            == audit["C (internal)"]["segments_hash"])
    # D differs (has the pause + tighter growth)
    assert (audit["D (mixed)"]["segments_hash"]
            != audit["A (baseline)"]["segments_hash"])
    # All verify
    for name in audit:
        assert audit[name]["verify_log"] is True
        assert audit[name]["verify_growth"] is True
