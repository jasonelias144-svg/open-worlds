import pytest
from elementary_ca_world import (
    ECAParams, rule_90, rule_30, rule_110,
    step, expected_rule90_cells,
    ElementaryCAWorld,
    ECAGenRecord, ECABranchRecord,
    verify_log, verify_growth, verify_sierpinski,
    render_2d, render_current_row,
    demo, HAS_CRYPTO,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(params=None, cells=(0,)):
    return ElementaryCAWorld(
        params=params or rule_90(),
        initial_cells=cells, keypair=_kp())


# -- Rule engine --

def test_step_rule90_matches_xor():
    # Rule 90: next[x] = current[x-1] XOR current[x+1]
    cells = frozenset({0})
    assert step(cells, 90) == frozenset({-1, 1})
    assert step(frozenset({-1, 1}), 90) == frozenset({-2, 2})
    assert step(frozenset({-2, 2}), 90) == frozenset({-3, -1, 1, 3})


def test_step_rule30_nonempty():
    # Rule 30 is chaotic; just check it runs
    cells = frozenset({0})
    for _ in range(5):
        cells = step(cells, 30)
    assert len(cells) > 0


def test_step_rejects_bad_rule():
    with pytest.raises(ValueError):
        step(frozenset({0}), 256)
    with pytest.raises(ValueError):
        step(frozenset({0}), -1)


# -- Sierpinski identity --

def test_expected_rule90_cells_matches_evolution():
    """The closed-form must agree with the actual step."""
    cells = frozenset({0})
    for gen in range(20):
        assert frozenset(expected_rule90_cells(gen)) == cells
        cells = step(cells, 90)


def test_expected_rule90_cells_gen_7():
    # gen 7 = 111_2 has 8 cells at positions -7, -5, -3, -1, 1, 3, 5, 7
    # (all odd positions from -7 to 7). Popcount(7)=3, 2^3 = 8 cells.
    expected = expected_rule90_cells(7)
    assert len(expected) == 8
    assert min(expected) == -7
    assert max(expected) == 7


def test_expected_rule90_cells_gen_31():
    # 31 = 11111_2, popcount 5, 2^5 = 32 cells
    assert len(expected_rule90_cells(31)) == 32


# -- Params --

def test_params_hash_stable():
    assert rule_90().param_hash() == rule_90().param_hash()


def test_params_hash_differs_by_rule():
    assert rule_90().param_hash() != rule_30().param_hash()


def test_params_reject_bad_rule():
    with pytest.raises(ValueError):
        ECAParams(rule_number=300)


def test_params_overrides():
    p = rule_90()
    q = p.with_overrides({"rule_number": 30})
    assert q.rule_number == 30
    assert q.param_hash() != p.param_hash()


# -- World --

def test_world_grows():
    w = _world()
    assert w.gen() == 0
    w.grow_n(10)
    assert w.gen() == 10


def test_history_length():
    w = _world()
    w.grow_n(5)
    h = w.history()
    assert len(h) == 6  # gen 0 + 5 gens


def test_history_2d():
    w = _world()
    w.grow_n(3)
    h2d = w.history_2d()
    # gen 0 has 1 cell, gen 1 has 2, gen 2 has 2, gen 3 has 4
    assert len(h2d) == 1 + 2 + 2 + 4


def test_growth_records_all_same_p():
    w = _world()
    w.grow_n(10)
    hashes = {r.p for r in w.records()
              if isinstance(r, ECAGenRecord)}
    assert len(hashes) == 1


# -- Verification --

def test_log_verifies():
    w = _world()
    w.grow_n(31)
    ok, reason = verify_log(w)
    assert ok, reason


def test_growth_verifies():
    w = _world()
    w.grow_n(31)
    ok, reason = verify_growth(w)
    assert ok, reason


def test_sierpinski_verifies():
    w = _world()
    w.grow_n(31)
    ok, reason = verify_sierpinski(w)
    assert ok, reason


def test_sierpinski_rejects_wrong_rule():
    w = _world(params=rule_30())
    w.grow_n(10)
    ok, reason = verify_sierpinski(w)
    assert not ok
    assert "not rule 90" in reason


def test_sierpinski_rejects_multi_seed():
    w = _world(cells=(0, 1, 2))
    w.grow_n(10)
    ok, reason = verify_sierpinski(w)
    assert not ok
    assert "not single-cell" in reason


def test_tampered_record_rejected():
    w = _world()
    w.grow_n(5)
    # Corrupt a growth record's cells
    tampered = list(w.records())
    orig = tampered[2]
    tampered[2] = ECAGenRecord(
        world_id=orig.world_id, gen=orig.gen,
        seed_hash=orig.seed_hash, prev=orig.prev,
        p=orig.p, cells=[999], ts=orig.ts,
        sig=orig.sig)
    w._records = tampered
    ok, _ = verify_growth(w)
    assert not ok


# -- Branching --

def test_branch_to_rule_30():
    w = _world()
    w.grow_n(5)
    cells_before = frozenset(w.cells())
    result = w.request_branch({"rule_number": 30})
    assert result is not None
    seed, child = result
    assert child.params.rule_number == 30
    assert frozenset(child.cells()) == cells_before
    assert w.params.rule_number == 90


def test_parent_unchanged_after_branch():
    w = _world()
    w.grow_n(5)
    cells_before = frozenset(w.cells())
    gen_before = w.gen()
    w.request_branch({"rule_number": 30})
    assert frozenset(w.cells()) == cells_before
    assert w.gen() == gen_before


def test_branch_child_verifies():
    w = _world()
    w.grow_n(5)
    seed, child = w.request_branch({"rule_number": 110})
    child.grow_n(10)
    ok, reason = verify_log(child)
    assert ok, reason
    ok, reason = verify_growth(child)
    assert ok, reason


def test_bad_branch_refused():
    w = _world()
    w.grow_n(5)
    assert w.request_branch({"rule_number": 300}) is None
    assert w.request_branch({"nonsense": 1}) is None


def test_parent_still_sierpinski_after_branch():
    w = _world()
    w.grow_n(10)
    w.request_branch({"rule_number": 30})
    w.grow_n(10)
    ok, reason = verify_sierpinski(w)
    assert ok, reason


# -- Rendering --

def test_render_2d():
    w = _world()
    w.grow_n(3)
    text = render_2d(w)
    assert "#" in text
    rows = text.split("\n")
    assert len(rows) == 4  # gen 0 through gen 3


def test_render_current_row():
    w = _world()
    w.grow_n(3)
    row = render_current_row(w)
    assert "#" in row


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    a = audit["scenario_a"]
    assert a["verify_log"] is True
    assert a["verify_growth"] is True
    assert a["verify_sierpinski"] is True
    assert a["final_cells"] == 32   # gen 31, 2^5
    b = audit["scenario_b"]
    assert b["parent_verify"]["sierpinski"] is True
    assert b["child_verify"]["growth"] is True
    c = audit["scenario_c"]
    assert c["child_verify"]["growth"] is True
    d = audit["scenario_d"]
    assert d["verify_growth"] is True
    assert d["verify_sierpinski"] is False
    assert (tmp_path / "elementary_ca" /
            "elementary_ca_demo.json").exists()
