import pytest
from fractal_grid_world import (
    GridParams, FractalGridWorld,
    GridSeedRecord, GridRowRecord,
    GridBranchSeed, GridBranchRecord,
    verify_log, verify_growth, verify_sierpinski,
    render_ascii, demo, HAS_CRYPTO,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(rule=90, max_gen=None, cells=(0,)):
    return FractalGridWorld(
        params=GridParams(rule_number=rule, max_gen=max_gen),
        initial_row=list(cells), keypair=_kp())


# -- Params --

def test_params_hash_stable():
    assert (GridParams(90).param_hash()
            == GridParams(90).param_hash())


def test_params_hash_differs_with_max_gen():
    assert (GridParams(90, None).param_hash()
            != GridParams(90, 10).param_hash())


def test_params_overrides():
    p = GridParams(90)
    q = p.with_overrides({"rule_number": 30})
    assert q.rule_number == 30


def test_params_reject_bad_rule():
    with pytest.raises(ValueError):
        GridParams(rule_number=300)


def test_params_reject_negative_max_gen():
    with pytest.raises(ValueError):
        GridParams(max_gen=-1)


# -- 2D state --

def test_initial_cells_2d():
    w = _world()
    cells = w.cells()
    assert (0, 0) in cells
    assert len(cells) == 1


def test_cells_after_one_gen():
    w = _world()
    w.grow()
    cells = w.cells()
    assert (0, 0) in cells       # gen 0
    assert (-1, 1) in cells       # gen 1
    assert (1, 1) in cells        # gen 1
    assert len(cells) == 3


def test_rows():
    w = _world()
    w.grow_n(2)
    rows = w.rows()
    assert len(rows) == 3   # gen 0, 1, 2
    assert rows[0] == (0, frozenset({0}))
    assert rows[1][0] == 1
    assert rows[2][0] == 2


def test_bbox():
    w = _world()
    w.grow_n(3)
    bbox = w.bbox()
    # gen 3 has cells at x = -3, -1, 1, 3 → all gens bbox
    # x from -3 to 3, y from 0 to 3
    assert bbox == (-3, 0, 3, 3)


# -- Growth and verification --

def test_log_verifies():
    w = _world(max_gen=31)
    w.grow_n(31)
    ok, reason = verify_log(w)
    assert ok, reason


def test_growth_verifies():
    w = _world(max_gen=31)
    w.grow_n(31)
    ok, reason = verify_growth(w)
    assert ok, reason


def test_sierpinski_verifies():
    w = _world(max_gen=31)
    w.grow_n(31)
    ok, reason = verify_sierpinski(w)
    assert ok, reason


def test_sierpinski_rejects_wrong_rule():
    w = _world(rule=30, max_gen=10)
    w.grow_n(10)
    ok, reason = verify_sierpinski(w)
    assert not ok
    assert "not rule 90" in reason


def test_sierpinski_rejects_multi_seed():
    w = _world(max_gen=10, cells=(0, 1, 2))
    w.grow_n(10)
    ok, reason = verify_sierpinski(w)
    assert not ok
    assert "not single-cell" in reason


def test_growth_records_all_same_p():
    w = _world(max_gen=10)
    w.grow_n(10)
    hashes = {r.p for r in w.records()
              if isinstance(r, GridRowRecord)}
    assert len(hashes) == 1


# -- max_gen boundary --

def test_grow_stops_at_max():
    w = _world(max_gen=5)
    steps = w.grow_n(20)
    assert steps == 5
    assert w.gen() == 5
    assert w.at_max()


def test_grow_returns_none_at_max():
    w = _world(max_gen=3)
    w.grow_n(3)
    assert w.grow() is None


def test_max_gen_still_verifies():
    w = _world(max_gen=3)
    w.grow_n(20)
    ok, reason = verify_growth(w)
    assert ok, reason


# -- Branching --

def test_branch_inherits_pattern():
    w = _world(max_gen=15)
    w.grow_n(15)
    inherited = w.cells()
    result = w.request_branch(
        {"rule_number": 30, "max_gen": 30})
    assert result is not None
    seed, child = result
    assert frozenset(child.cells()) == inherited


def test_branch_has_new_rule():
    w = _world(max_gen=15)
    w.grow_n(15)
    seed, child = w.request_branch({"rule_number": 30})
    assert child.params.rule_number == 30
    assert w.params.rule_number == 90


def test_parent_unchanged():
    w = _world(max_gen=15)
    w.grow_n(15)
    before_cells = w.cells()
    before_gen = w.gen()
    w.request_branch({"rule_number": 30})
    assert w.cells() == before_cells
    assert w.gen() == before_gen


def test_branch_verifies():
    w = _world(max_gen=15)
    w.grow_n(15)
    seed, child = w.request_branch(
        {"rule_number": 30, "max_gen": 30})
    child.grow_n(15)
    ok, reason = verify_log(child)
    assert ok, reason
    ok, reason = verify_growth(child)
    assert ok, reason


def test_branch_is_not_sierpinski():
    """A chimera's verify_sierpinski is False — the top half is
    Sierpinski, the bottom half isn't. Honest."""
    w = _world(max_gen=15)
    w.grow_n(15)
    seed, child = w.request_branch(
        {"rule_number": 30, "max_gen": 30})
    child.grow_n(15)
    ok, reason = verify_sierpinski(child)
    assert not ok
    assert "branch" in reason.lower() or \
           "fresh seed" in reason.lower()


def test_branch_extends_max_gen():
    w = _world(max_gen=5)
    w.grow_n(20)   # stops at 5
    seed, child = w.request_branch({"max_gen": 20})
    child.grow_n(30)   # should stop at 20
    assert child.gen() == 20


def test_tampered_row_rejected():
    w = _world(max_gen=5)
    w.grow_n(5)
    tampered = list(w.records())
    orig = tampered[2]
    tampered[2] = GridRowRecord(
        world_id=orig.world_id, gen=orig.gen,
        seed_hash=orig.seed_hash, prev=orig.prev,
        p=orig.p, row_x=[999], ts=orig.ts,
        sig=orig.sig)
    w._records = tampered
    ok, _ = verify_growth(w)
    assert not ok


# -- Rendering --

def test_render():
    w = _world(max_gen=3)
    w.grow_n(3)
    text = render_ascii(w)
    assert "#" in text
    rows = text.split("\n")
    assert len(rows) == 4   # gen 0 through gen 3


def test_render_flip():
    w = _world(max_gen=3)
    w.grow_n(3)
    normal = render_ascii(w, flip=False).split("\n")
    flipped = render_ascii(w, flip=True).split("\n")
    assert normal == list(reversed(flipped))


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    a = audit["scenario_a"]
    assert a["verify_log"] is True
    assert a["verify_growth"] is True
    assert a["verify_sierpinski"] is True
    assert a["gens_grown"] == 31
    b = audit["scenario_b"]
    assert b["parent_verified"]["sierpinski"] is True
    assert b["child_verified"]["growth"] is True
    assert b["child_sierpinski"] is False   # chimera, not Sierpinski
    assert "branch" in b["child_sierpinski_reason"].lower() \
           or "fresh seed" in b["child_sierpinski_reason"].lower()
    c = audit["scenario_c"]
    assert c["child_verified"]["growth"] is True
    d = audit["scenario_d"]
    assert d["stopped_at_boundary"] is True
    assert d["extended_gens"] == 20
    assert d["extended_verify"] is True
