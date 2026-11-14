import pytest
from coupled_ca_world import (
    CoupledCAWorld, CoupledCAStepRecord, CouplingChangeRecord,
    _active_at, verify_coupled_ca_log, verify_coupled_ca_growth,
    render_combined, _first_gen_with_overlap, demo, HAS_CRYPTO)
from elementary_ca_world import expected_rule90_cells
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _world(k_a=0, k_b=0, offset=20):
    return CoupledCAWorld(
        rule_a=90, rule_b=90, initial_a=[0],
        initial_b=[offset], k_a=k_a, k_b=k_b)


def test_active_at_k0():
    assert not any(_active_at(s, "A", 0) for s in range(20))


def test_active_at_k100():
    assert all(_active_at(s, "A", 100) for s in range(20))


def test_active_at_k50_mixed():
    count = sum(_active_at(s, "A", 50) for s in range(100))
    assert 30 < count < 70


def test_k0_is_pure_sierpinski():
    w = _world(k_a=0, k_b=0, offset=20)
    w.grow_n(20)
    assert w.cells_a() == expected_rule90_cells(20)


def test_k0_pure_even_with_overlap():
    w = _world(k_a=0, k_b=0, offset=20)
    w.grow_n(25)  # crosses overlap start
    assert w.cells_a() == expected_rule90_cells(25)
    expected_b = frozenset(x + 20 for x in expected_rule90_cells(25))
    assert w.cells_b() == expected_b


def test_k100_diverges():
    w = _world(k_a=100, k_b=100, offset=20)
    w.grow_n(25)
    pure_a = expected_rule90_cells(25)
    assert w.cells_a() != pure_a


def test_asymmetric_coupling():
    w = _world(k_a=100, k_b=0, offset=20)
    w.grow_n(25)
    expected_b = frozenset(x + 20 for x in expected_rule90_cells(25))
    assert w.cells_b() == expected_b  # B untouched


def test_overlap_appears():
    w = _world(offset=10)
    assert _first_gen_with_overlap(w) is None
    w.grow_n(15)
    assert _first_gen_with_overlap(w) is not None


def test_verification():
    w = _world(k_a=60, k_b=40, offset=15)
    w.grow_n(30)
    ok, reason = verify_coupled_ca_log(w)
    assert ok, reason
    ok, reason = verify_coupled_ca_growth(w)
    assert ok, reason


def test_mid_world_change():
    w = _world()
    w.grow_n(10)
    w.set_coupling(k_a=100, k_b=100)
    w.grow_n(20)
    ok, reason = verify_coupled_ca_growth(w)
    assert ok, reason


def test_tampered_cells_rejected():
    w = _world()
    w.grow_n(10)
    tampered = list(w.records())
    orig = tampered[5]
    tampered[5] = CoupledCAStepRecord(
        world_id=orig.world_id, gen=orig.gen, prev=orig.prev,
        rule_a=orig.rule_a, rule_b=orig.rule_b,
        k_a=orig.k_a, k_b=orig.k_b,
        cells_a_after=[999],
        cells_b_after=orig.cells_b_after,
        overlap_before=orig.overlap_before,
        active_a=orig.active_a, active_b=orig.active_b,
        ts=orig.ts, sig=orig.sig)
    w._records = tampered
    ok, _ = verify_coupled_ca_growth(w)
    assert not ok


def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for n in ("A", "B", "C", "D"):
        assert audit[n]["verify_log"] is True
        assert audit[n]["verify_growth"] is True
    assert audit["D"]["change_at_gen"] == 15
