import pytest
from coupled_chaos_world import (
    CoupledChaosWorld, CoupledStepRecord, CouplingChangeRecord,
    coupling_weights,
    verify_coupled_log, verify_coupled_growth,
    verify_subworlds, verify_full,
    render_coupled, render_trajectory, same_pick_rate,
    MIN_WEIGHT, demo, HAS_CRYPTO,
)
from chaos_game_world import SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(k_a=0, k_b=0, seed=42, window=20):
    return CoupledChaosWorld(
        preset=SIERPINSKI,
        initial_point_a=(500, 500),
        initial_point_b=(500, 500),
        prng_seed=seed, keypair=_kp(),
        k_a=k_a, k_b=k_b, window=window)


# -- Coupling math --

def test_coupling_k0_returns_base():
    assert coupling_weights((1, 1, 1), [0, 0, 0, 0],
                             k_self=0, n_vertices=3) == (1, 1, 1)


def test_coupling_k100_penalizes():
    eff = coupling_weights((100, 100, 100), [0, 0, 0, 0],
                            k_self=100, n_vertices=3)
    assert eff[0] == MIN_WEIGHT
    assert eff[1] == 100
    assert eff[2] == 100


def test_coupling_partial():
    eff = coupling_weights((100, 100, 100),
                            [0, 0, 1, 1],
                            k_self=100, n_vertices=3)
    assert eff[0] < eff[2]
    assert eff[1] < eff[2]
    assert eff[0] == eff[1]


def test_coupling_empty_recent():
    assert coupling_weights((1, 1, 1), [], 100, 3) == (1, 1, 1)


# -- Growth --

def test_grow_produces_record():
    w = _world()
    assert isinstance(w.grow(), CoupledStepRecord)
    assert w.step() == 1


def test_both_subworlds_grow():
    w = _world()
    w.grow_n(10)
    assert w.subworld_a().step() == 10
    assert w.subworld_b().step() == 10


def test_deterministic():
    w1 = _world(seed=99)
    w2 = _world(seed=99)
    w1.grow_n(30)
    w2.grow_n(30)
    assert w1.points_a() == w2.points_a()
    assert w1.points_b() == w2.points_b()


def test_different_seeds_diverge():
    w1 = _world(seed=1)
    w2 = _world(seed=2)
    w1.grow_n(30)
    w2.grow_n(30)
    assert w1.points_a() != w2.points_a()


# -- Coupling effects --

def test_k0_independent():
    """At k=0, both worlds visit all three vertices."""
    w = _world(k_a=0, k_b=0)
    w.grow_n(200)
    recent_a = [r.pick_a for r in w.records()
                 if isinstance(r, CoupledStepRecord)][-20:]
    recent_b = [r.pick_b for r in w.records()
                 if isinstance(r, CoupledStepRecord)][-20:]
    assert set(recent_a) == {0, 1, 2}
    assert set(recent_b) == {0, 1, 2}


def test_k100_reduces_same_pick_rate():
    w0 = _world(k_a=0, k_b=0, seed=42)
    w0.grow_n(500)
    w100 = _world(k_a=100, k_b=100, seed=42)
    w100.grow_n(500)
    assert same_pick_rate(w100) < same_pick_rate(w0)


def test_asymmetric_coupling():
    """When only A listens, A's choices anti-correlate with B's
    but not necessarily the reverse."""
    w = _world(k_a=100, k_b=0, seed=7)
    w.grow_n(500)
    steps = [r for r in w.records()
             if isinstance(r, CoupledStepRecord)]
    # B's recent picks should create a biased eff_a; A's don't
    # create a biased eff_b. Check last step.
    last = steps[-1]
    assert last.k_a == 100 and last.k_b == 0


# -- Verification --

def test_log_verifies():
    w = _world()
    w.grow_n(50)
    ok, reason = verify_coupled_log(w)
    assert ok, reason


def test_growth_verifies():
    w = _world(k_a=50, k_b=50)
    w.grow_n(100)
    ok, reason = verify_coupled_growth(w)
    assert ok, reason


def test_subworlds_verify():
    w = _world()
    w.grow_n(50)
    ok, reason = verify_subworlds(w)
    assert ok, reason


def test_full_verifies():
    w = _world(k_a=50, k_b=50)
    w.grow_n(100)
    ok, reason = verify_full(w)
    assert ok, reason


def test_tampered_raw_rejected():
    w = _world()
    w.grow_n(10)
    tampered = list(w.records())
    orig = tampered[3]
    tampered[3] = CoupledStepRecord(
        world_id=orig.world_id, step=orig.step,
        prev=orig.prev, k_a=orig.k_a, k_b=orig.k_b,
        raw_a=(orig.raw_a + 1) % 3, raw_b=orig.raw_b,
        eff_a=orig.eff_a, eff_b=orig.eff_b,
        pick_a=orig.pick_a, pick_b=orig.pick_b,
        point_a=orig.point_a, point_b=orig.point_b,
        sig_a=orig.sig_a, sig_b=orig.sig_b,
        ts=orig.ts, sig=orig.sig)
    w._records = tampered
    ok, _ = verify_coupled_growth(w)
    assert not ok


def test_tampered_pick_rejected():
    w = _world()
    w.grow_n(10)
    tampered = list(w.records())
    orig = tampered[3]
    tampered[3] = CoupledStepRecord(
        world_id=orig.world_id, step=orig.step,
        prev=orig.prev, k_a=orig.k_a, k_b=orig.k_b,
        raw_a=orig.raw_a, raw_b=orig.raw_b,
        eff_a=orig.eff_a, eff_b=orig.eff_b,
        pick_a=(orig.pick_a + 1) % 3, pick_b=orig.pick_b,
        point_a=orig.point_a, point_b=orig.point_b,
        sig_a=orig.sig_a, sig_b=orig.sig_b,
        ts=orig.ts, sig=orig.sig)
    w._records = tampered
    ok, _ = verify_coupled_growth(w)
    assert not ok


# -- Coupling change --

def test_set_coupling():
    w = _world(k_a=0, k_b=0)
    w.grow_n(10)
    rec = w.set_coupling(k_a=80, k_b=20)
    assert isinstance(rec, CouplingChangeRecord)
    assert w.k_a() == 80 and w.k_b() == 20


def test_coupling_change_verifies():
    w = _world()
    w.grow_n(50)
    w.set_coupling(k_a=100, k_b=100)
    w.grow_n(50)
    ok, reason = verify_coupled_log(w)
    assert ok, reason
    ok, reason = verify_coupled_growth(w)
    assert ok, reason


def test_coupling_change_rejects_bad_value():
    w = _world()
    with pytest.raises(ValueError):
        w.set_coupling(k_a=200)


# -- Rendering --

def test_render_coupled():
    w = _world()
    w.grow_n(200)
    text = render_coupled(w, width=40, height=15)
    assert len(text.split("\n")) == 15
    assert text.strip() != ""


def test_render_trajectory():
    w = _world()
    w.grow_n(200)
    text = render_trajectory(w, n=20, width=40, height=12)
    assert len(text.split("\n")) == 12


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for name in ("A", "B", "C", "D"):
        assert audit[name]["verify_log"] is True
        assert audit[name]["verify_growth"] is True
        assert audit[name]["verify_full"] is True
    # k=100 mutual yields lower same-pick rate than k=0
    assert (audit["C"]["same_pick_rate"]
            < audit["A"]["same_pick_rate"])
    assert audit["D"]["change_at_step"] == 1000
    assert (tmp_path / "coupled_chaos" /
            "coupled_chaos_demo.json").exists()
