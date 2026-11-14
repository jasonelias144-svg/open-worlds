import pytest
from life_world import (
    LifeParams, standard_life, highlife,
    life_step, LifeWorld, LifeGenRecord, LifeBranchRecord,
    verify_life_log, verify_life_growth,
    render_ascii, render_summary,
    r_pentomino, glider, blinker, block, offset,
    demo, HAS_CRYPTO)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(cells, params=None):
    return LifeWorld(
        template_id="t", params=params or standard_life(),
        initial_cells=cells, keypair=_kp())


# -- Params --

def test_params_hash_stable():
    a = LifeParams((3,), (2, 3))
    b = LifeParams([3], [2, 3])
    assert a.param_hash() == b.param_hash()


def test_params_reject_bad_birth():
    with pytest.raises(ValueError):
        LifeParams(birth=(9,))


def test_params_reject_wrap_without_grid():
    with pytest.raises(ValueError):
        LifeParams(boundary="wrap")


def test_params_overrides():
    p = standard_life()
    q = p.with_overrides({"birth": (3, 6)})
    assert q.birth == (3, 6)
    assert q.param_hash() != p.param_hash()


def test_rule_string():
    assert standard_life().rule_string() == "B3/S23"
    assert highlife().rule_string() == "B36/S23"


# -- The rule --

def test_blinker_oscillates():
    h = blinker()
    v = life_step(h, standard_life())
    assert v == {(1, 0), (1, 1), (1, 2)}
    back = life_step(v, standard_life())
    assert back == h


def test_block_stable():
    b = block()
    assert life_step(b, standard_life()) == b


def test_glider_moves_one_cell_every_four_gens():
    g = glider()
    cur = g
    for _ in range(4):
        cur = life_step(cur, standard_life())
    assert cur == offset(g, 1, 1)


def test_life_like_rule():
    # Under B36/S23 the same glider has different behavior
    g = glider()
    a = life_step(g, standard_life())
    b = life_step(g, highlife())
    assert a != b


# -- Growth and verification --

def test_world_grows():
    w = _world(r_pentomino())
    assert w.gen() == 0
    w.grow_n(5)
    assert w.gen() == 5
    assert len(w.cells()) > 0


def test_log_verifies():
    w = _world(r_pentomino())
    w.grow_n(10)
    ok, reason = verify_life_log(w)
    assert ok, reason


def test_growth_verifies():
    w = _world(r_pentomino())
    w.grow_n(10)
    ok, reason = verify_life_growth(w)
    assert ok, reason


def test_params_hash_constant_across_generations():
    w = _world(r_pentomino())
    w.grow_n(10)
    hashes = {r.p for r in w.records()
              if isinstance(r, LifeGenRecord)}
    assert len(hashes) == 1


def test_seed_hash_constant():
    w = _world(r_pentomino())
    w.grow_n(5)
    sh = w.seed_hash()
    for r in w.records():
        if isinstance(r, LifeGenRecord):
            assert r.seed_hash == sh


# -- Branching --

def test_branch_inherits_cells():
    w = _world(r_pentomino())
    w.grow_n(5)
    inherited = frozenset(w.cells())
    result = w.request_branch({"birth": (3, 6)})
    assert result is not None
    seed, child = result
    assert frozenset(child.cells()) == inherited


def test_branch_has_new_params():
    w = _world(r_pentomino())
    w.grow_n(5)
    seed, child = w.request_branch({"birth": (3, 6)})
    assert child.params.birth == (3, 6)
    assert w.params.birth == (3,)   # parent unchanged


def test_parent_unchanged_after_branch():
    w = _world(r_pentomino())
    w.grow_n(5)
    parent_cells_before = frozenset(w.cells())
    seed, child = w.request_branch({"birth": (3, 6)})
    assert frozenset(w.cells()) == parent_cells_before
    # Parent still grows under its own rule
    w.grow_n(3)
    assert w.gen() == 8


def test_branch_verifies():
    w = _world(r_pentomino())
    w.grow_n(5)
    seed, child = w.request_branch({"birth": (3, 6)})
    child.grow_n(10)
    ok, reason = verify_life_log(child)
    assert ok, reason
    ok, reason = verify_life_growth(child)
    assert ok, reason


def test_bad_branch_params_refused():
    w = _world(r_pentomino())
    assert w.request_branch({"birth": (9,)}) is None
    assert w.request_branch({"nonsense": 1}) is None


def test_divergent_growth_from_same_state():
    w = _world(r_pentomino())
    w.grow_n(5)
    seed, child = w.request_branch({"birth": (3, 6)})
    w.grow_n(10)
    child.grow_n(10)
    # Same origin, different rule, different futures
    assert frozenset(w.cells()) != frozenset(child.cells())


# -- Rendering --

def test_render_ascii():
    w = _world(blinker())
    text = render_ascii(w)
    assert "#" in text


def test_render_summary():
    w = _world(r_pentomino())
    s = render_summary(w)
    assert "gen 0" in s
    assert "5 cells" in s


def test_render_empty():
    w = _world([])
    assert "empty" in render_ascii(w).lower()


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for scen in ("scenario_a", "scenario_b"):
        s = audit[scen]
        assert s["verify_log"] is True
        assert s["verify_growth"] is True
    c = audit["scenario_c"]
    assert c["parent_verified_log"] is True
    assert c["parent_verified_growth"] is True
    assert c["branch_verified_log"] is True
    assert c["branch_verified_growth"] is True
    assert c["divergence"] > 0
    assert (tmp_path / "life_world" /
            "life_world_demo.json").exists()
