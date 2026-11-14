import pytest
from chaos_game_world import (
    xorshift64_star_step, pick_weighted,
    ChaosTransform, ChaosPreset,
    SIERPINSKI, BARNSLEY,
    ChaosGameWorld, ChaosStepRecord, ChaosChoice,
    sign_choice, verify_choice,
    verify_chaos_log, verify_chaos_growth,
    render_ascii, demo, HAS_CRYPTO,
    _did_from_kp,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _seeded(preset=SIERPINSKI, seed=42, start=(500, 500)):
    return ChaosGameWorld(
        preset=preset, growth_mode="seeded_random",
        initial_point=start, keypair=_kp(),
        prng_seed=seed)


# -- PRNG --

def test_prng_deterministic():
    s1, o1 = xorshift64_star_step(12345)
    s2, o2 = xorshift64_star_step(12345)
    assert s1 == s2 and o1 == o2


def test_prng_produces_distinct_outputs():
    s = 12345
    outputs = set()
    for _ in range(100):
        s, o = xorshift64_star_step(s)
        outputs.add(o)
    assert len(outputs) == 100


def test_pick_weighted_distribution():
    # 1:1:1 weights → roughly equal
    weights = (1, 1, 1)
    counts = [0, 0, 0]
    s = 12345
    for _ in range(3000):
        s, o = xorshift64_star_step(s)
        counts[pick_weighted(o, weights)] += 1
    for c in counts:
        assert 800 < c < 1200   # roughly 1000 each


def test_pick_weighted_skewed():
    # 85:7:7:1 weights → 'main' dominates
    weights = (1, 7, 7, 85)
    counts = [0, 0, 0, 0]
    s = 42
    for _ in range(10000):
        s, o = xorshift64_star_step(s)
        counts[pick_weighted(o, weights)] += 1
    assert counts[3] > 8000  # 'main' > 80%


# -- Presets --

def test_sierpinski_preset():
    assert len(SIERPINSKI.transforms) == 3
    assert SIERPINSKI.weights() == (1, 1, 1)


def test_barnsley_preset():
    assert len(BARNSLEY.transforms) == 4
    assert BARNSLEY.weights() == (1, 7, 7, 85)


def test_preset_hash_differs():
    assert (SIERPINSKI.preset_hash()
            != BARNSLEY.preset_hash())


def test_preset_rejects_empty():
    with pytest.raises(ValueError):
        ChaosPreset(preset_id="x", transforms=())


def test_transform_apply_sierpinski():
    # T1 (vertex (1000, 0)): (x + 1000) // 2
    t = SIERPINSKI.transforms[1]
    assert t.apply((0, 0)) == (500, 0)
    assert t.apply((500, 500)) == (750, 250)


# -- Growth modes --

def test_seeded_growth():
    w = _seeded()
    assert w.step() == 0
    w.grow()
    assert w.step() == 1


def test_seeded_grow_n():
    w = _seeded()
    n = w.grow_n(100)
    assert n == 100
    assert w.step() == 100


def test_seeded_deterministic():
    w1 = _seeded(seed=99)
    w2 = _seeded(seed=99)
    w1.grow_n(50)
    w2.grow_n(50)
    assert w1.points() == w2.points()


def test_seeded_different_seeds_diverge():
    w1 = _seeded(seed=1)
    w2 = _seeded(seed=2)
    w1.grow_n(50)
    w2.grow_n(50)
    assert w1.points() != w2.points()


def test_external_growth_requires_input():
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=_kp(),
        input_authority=_did_from_kp(_kp()))
    assert w.grow() is None   # no PRNG in this mode


def test_external_growth_with_choice():
    gardener = _kp()
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=_kp(),
        input_authority=_did_from_kp(gardener))
    choice = sign_choice(w.world_id, 0, 1, gardener)
    r = w.grow_with_input(choice)
    assert r is not None
    assert w.step() == 1


def test_external_rejects_wrong_signer():
    gardener = _kp()
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=_kp(),
        input_authority=_did_from_kp(gardener))
    wrong = sign_choice(w.world_id, 0, 1, _kp())
    assert w.grow_with_input(wrong) is None


def test_external_rejects_wrong_step():
    gardener = _kp()
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=_kp(),
        input_authority=_did_from_kp(gardener))
    choice = sign_choice(w.world_id, 99, 0, gardener)
    assert w.grow_with_input(choice) is None


def test_external_rejects_bad_idx():
    gardener = _kp()
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=_kp(),
        input_authority=_did_from_kp(gardener))
    choice = sign_choice(w.world_id, 0, 99, gardener)
    assert w.grow_with_input(choice) is None


# -- Verification --

def test_seeded_log_verifies():
    w = _seeded()
    w.grow_n(100)
    ok, reason = verify_chaos_log(w)
    assert ok, reason


def test_seeded_growth_verifies():
    w = _seeded()
    w.grow_n(100)
    ok, reason = verify_chaos_growth(w)
    assert ok, reason


def test_external_growth_verifies():
    gardener = _kp()
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=_kp(),
        input_authority=_did_from_kp(gardener))
    for i in range(50):
        choice = sign_choice(w.world_id, w.step(), i % 3, gardener)
        w.grow_with_input(choice)
    ok, reason = verify_chaos_growth(w)
    assert ok, reason


def test_tampered_transform_idx_rejected():
    w = _seeded()
    w.grow_n(10)
    tampered = list(w.records())
    orig = tampered[3]
    tampered[3] = ChaosStepRecord(
        world_id=orig.world_id, step=orig.step,
        prev=orig.prev, p=orig.p,
        transform_idx=(orig.transform_idx + 1) % 3,
        point=orig.point, input_sig=orig.input_sig,
        ts=orig.ts, sig=orig.sig)
    w._records = tampered
    ok, _ = verify_chaos_growth(w)
    assert not ok


# -- Branching --

def test_branch_inherits_point():
    w = _seeded()
    w.grow_n(50)
    parent_point = w.point()
    seed, child = w.request_branch(prng_seed=999)
    assert child.point() == parent_point
    assert child.step() == 0


def test_branch_different_seed():
    w = _seeded()
    w.grow_n(50)
    seed, child = w.request_branch(prng_seed=999)
    assert child._prng_seed == 999


def test_branch_verifies():
    w = _seeded()
    w.grow_n(50)
    seed, child = w.request_branch(prng_seed=999)
    child.grow_n(50)
    ok, reason = verify_chaos_log(child)
    assert ok, reason
    ok, reason = verify_chaos_growth(child)
    assert ok, reason


def test_branch_diverges_from_parent():
    w = _seeded()
    w.grow_n(50)
    seed, child = w.request_branch(prng_seed=999)
    w.grow_n(100)
    child.grow_n(100)
    assert w.points() != child.points()


def test_parent_unchanged_after_branch():
    w = _seeded()
    w.grow_n(50)
    before = w.point()
    w.request_branch(prng_seed=999)
    assert w.point() == before


# -- Rendering --

def test_render_produces_ascii():
    w = _seeded()
    w.grow_n(500)
    text = render_ascii(w, width=40, height=10)
    assert "#" in text
    assert len(text.split("\n")) == 10


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for s in ("scenario_a", "scenario_b", "scenario_c"):
        assert audit[s]["verify_log"] is True, s
        assert audit[s]["verify_growth"] is True, s
    assert audit["scenario_b"]["rejects_wrong_sig"] is True
    d = audit["scenario_d"]
    assert d["branch_verified_log"] is True
    assert d["branch_verified_growth"] is True
    assert d["parent_verified_growth"] is True
    assert (tmp_path / "chaos_game" /
            "chaos_game_demo.json").exists()
