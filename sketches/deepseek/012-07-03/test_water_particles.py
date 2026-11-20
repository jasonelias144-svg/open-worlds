import pytest
from water_particles import (
    WaterGrid, WaterWorld, WaterTick, W_MAX, SOAK_RATE,
    verify_water_log, verify_water_replay,
    render_ascii, HAS_CRYPTO, _canonical)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(**kw):
    defaults = dict(width=20, height=10,
                    roots=[(10, 8)], energy_cap=50)
    defaults.update(kw)
    return WaterWorld(keypair=_kp(), **defaults)


# -- Grid --

def test_empty_grid_zero():
    g = WaterGrid.empty(5, 4)
    for x in range(5):
        for y in range(3):
            assert g.get(x, y) == 0

def test_add_caps():
    g = WaterGrid.empty(1, 2)
    assert g.add(0, 0, W_MAX + 5) == W_MAX
    assert g.get(0, 0) == W_MAX

def test_remove_caps():
    g = WaterGrid.empty(1, 2)
    g.add(0, 0, 3)
    assert g.remove(0, 0, 10) == 3
    assert g.get(0, 0) == 0

def test_out_of_bounds_safe():
    g = WaterGrid.empty(5, 4)
    for (x, y) in [(-1, 0), (0, -1), (5, 0), (0, 99)]:
        assert g.get(x, y) == 0


# -- Falling and pooling --

def test_water_falls_one_cell():
    w = _world(width=5, height=6)
    w.grid.add(2, 0, 3)
    # Disable rain influence by checking the next tick's shape
    w.tick()
    # The initial 3 either fell to y=1, or were joined by rain
    # at y=0 and the column now spans y=0 and y=1. Just check
    # that some water is below y=0.
    assert any(w.grid.get(2, y) > 0 for y in range(1, 5))

def test_water_pools_at_bottom():
    w = _world(width=10, height=6)
    w.grid.add(5, 0, W_MAX)
    for _ in range(6):
        w.tick()
    bottom = w.grid.height - 2
    assert w.grid.get(5, bottom) > 0


# -- Soaking --

def test_root_soaks():
    w = _world(roots=[(5, 3)], energy_cap=20, width=10, height=6)
    # Prevent the root-cell water from falling by filling below.
    w.grid.add(5, 4, W_MAX)
    w.grid.add(5, 3, 1)
    e0 = w.energy
    w.tick()
    assert w.energy > e0

def test_soak_capped_by_energy_cap():
    w = _world(roots=[(5, 3)], energy_cap=1, width=10, height=6)
    w.grid.add(5, 4, W_MAX)
    w.grid.add(5, 3, W_MAX)
    w.tick()
    assert w.energy <= 1

def test_root_soaks_before_flow():
    # Water at a root cell should soak before it can flow away.
    w = _world(roots=[(5, 3)], energy_cap=20, width=10, height=6)
    w.grid.add(5, 4, W_MAX)
    w.grid.add(5, 3, 1)
    # Leave neighbors empty so flow would take it if soak didn't.
    w.tick()
    assert w.energy >= 1


# -- Evaporation --

def test_evaporation_never_negative():
    w = _world(width=3, height=3)
    w.grid.add(1, 1, 1)
    for _ in range(200):
        w.tick()
    assert 0 <= w.grid.get(1, 1) <= W_MAX

def test_covered_water_does_not_evaporate():
    # A cell with water above it is not exposed. With no rain
    # (small world, short run), the buried unit should survive
    # at least one tick's evaporation.
    w = _world(width=1, height=4)
    # Build a column: y=0 and y=1 full, y=2 has one unit.
    w.grid.add(0, 0, W_MAX)
    w.grid.add(0, 1, W_MAX)
    w.grid.add(0, 2, 1)
    before_buried = w.grid.get(0, 1)
    w.tick()
    # y=1 is covered by y=0 (still wet), so it should not
    # evaporate; allow the top (y=0) to evaporate.
    assert w.grid.get(0, 1) >= 1 or before_buried == 0


# -- Log and chain --

def test_records_chain():
    w = _world()
    w.run(5)
    recs = w.records()
    assert len(recs) == 5
    assert recs[0].prev is None
    for i in range(1, len(recs)):
        assert recs[i].prev == recs[i - 1].record_hash()

def test_log_verifies():
    w = _world()
    w.run(10)
    ok, r = verify_water_log(w)
    assert ok, r

def test_replay_verifies():
    w = _world()
    w.run(10)
    ok, r = verify_water_replay(w)
    assert ok, r


# -- Tampering --

def test_tampered_level_hash_rejected_by_replay():
    w = _world()
    w.run(3)
    orig = w.records()[-1]
    bad_body = {**orig.body(), "level_hash": "00" * 32}
    bad_sig = w._keypair.sign(_canonical(bad_body)).hex()
    bad = WaterTick(
        world_id=orig.world_id, step=orig.step, t=orig.t,
        prev=orig.prev, rain=orig.rain, moves=orig.moves,
        soak=orig.soak, evap=orig.evap,
        level_hash="00" * 32, ts=orig.ts, sig=bad_sig)
    w._records[-1] = bad
    w._last_hash = bad.record_hash()
    ok_log, _ = verify_water_log(w)
    ok_rep, r = verify_water_replay(w)
    assert ok_log            # signature is valid
    assert not ok_rep        # but the rules catch it
    assert "level_hash" in r


# -- Determinism --

def test_same_keypair_same_replay():
    w1 = _world()
    w1.run(5)
    h1 = [r.level_hash for r in w1.records()]
    w2 = WaterWorld(
        width=w1._width, height=w1._height,
        roots=w1._roots, energy_cap=w1._energy_cap,
        keypair=w1._keypair)
    w2.run(5)
    h2 = [r.level_hash for r in w2.records()]
    assert h1 == h2


# -- Render --

def test_render_shape():
    w = _world(width=6, height=4)
    w.tick()
    text = render_ascii(w)
    lines = text.split("\n")
    assert len(lines) == 4          # 3 fluid rows + ground
    assert all(len(line) == 6 for line in lines[:3])
    assert lines[3] == "=" * 6


# -- Demo --

def test_demo(tmp_path):
    from water_particles import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["log_valid"]
    assert audit["replay_valid"]
    assert audit["records"] > 0
    assert 0 < audit["energy"] <= 50
