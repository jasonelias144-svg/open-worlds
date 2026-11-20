import pytest
from fractal_garden import (
    SlotRect, PlantAssignment, GardenTemplate,
    FractalGarden, GardenTick, GardenBranchRecord,
    GardenRefusalRecord, GardenBranchRequest,
    sign_garden_branch_request, verify_garden_branch_request,
    verify_garden_log, verify_garden_replay,
    render_garden, HAS_CRYPTO, GARDEN_PARAM_NAMES)
from fractal_world_v3 import (
    verify_world_log, verify_growth, _did_from_kp)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _template(branchy=True):
    policy = {"control": {"light_level": (3, 10)},
              "terminal": {"rain_rate": (16, 128),
                           "light_level": (1, 10)}} if branchy else None
    return GardenTemplate(
        template_id="t-garden",
        slot_rects=[SlotRect("a", 1, 3, 8, 8),
                    SlotRect("b", 10, 3, 8, 8)],
        water_width=20, water_height=12,
        rain_rate=64, evap_rate=20,
        water_max=8, energy_cap=20, growth_cost=1,
        light_level=10,
        branch_policy=policy)


def _garden(template=None, plants=None):
    template = template or _template()
    if plants is None:
        plants = [
            PlantAssignment("a", (4, 10, 0),
                            {"branch_length": 2, "max_depth": 2,
                             "water": 10, "light": 10}),
            PlantAssignment("b", (14, 10, 0),
                            {"branch_length": 2, "max_depth": 2,
                             "water": 10, "light": 10}),
        ]
    return FractalGarden(template, plants, _kp())


# -- Layout --

def test_slot_rects_contain_plants():
    g = _garden()
    for sid, p in g.plants().items():
        slot = g._find_slot(sid)
        for (x1, y1, x2, y2) in p.segments():
            for (x, y) in [(x1, y1), (x2, y2)]:
                assert slot.x <= x < slot.x + slot.w
                assert slot.y <= y < slot.y + slot.h


def test_create_plant_rejects_occupied_slot():
    g = _garden()
    with pytest.raises(ValueError):
        g._create_plant(PlantAssignment(
            "a", (4, 10, 0),
            {"branch_length": 2, "max_depth": 2,
             "water": 10, "light": 10}))


def test_create_plant_rejects_unknown_slot():
    g = _garden()
    with pytest.raises(ValueError):
        g._create_plant(PlantAssignment(
            "z", (4, 10, 0),
            {"branch_length": 2, "max_depth": 2,
             "water": 10, "light": 10}))


# -- Water and energy --

def test_rain_fills_over_time():
    g = _garden()
    g.run(10)
    total = sum(sum(row) for row in g.grid.levels)
    assert total > 0


def test_soak_fills_energy():
    g = _garden()
    g.run(10)
    for sid in g.energy():
        assert g.energy(sid) >= 0


def test_plant_grows_when_water_positive():
    g = _garden()
    g.run(15)
    for sid, p in g.plants().items():
        assert len(p.records()) > 0


def test_plant_refuses_when_own_water_zero():
    plants = [
        PlantAssignment("a", (4, 10, 0),
                        {"branch_length": 2, "max_depth": 2,
                         "water": 0, "light": 10}),
    ]
    template = GardenTemplate(
        template_id="t",
        slot_rects=[SlotRect("a", 1, 3, 8, 8)],
        water_width=12, water_height=12,
        rain_rate=128, evap_rate=10,
        energy_cap=30, growth_cost=1,
        branch_policy=None)
    g = FractalGarden(template, plants, _kp())
    g.run(15)
    p = g.plants()["a"]
    # No growth records, despite water being available
    assert len(p.records()) == 0
    # Energy was still delivered (soak happens regardless)
    assert g.energy("a") > 0


# -- Log and replay --

def test_tick_chain():
    g = _garden()
    g.run(5)
    recs = g.records()
    assert len(recs) == 5
    assert recs[0].prev is None
    for i in range(1, len(recs)):
        assert recs[i].prev == recs[i - 1].record_hash()


def test_log_verifies():
    g = _garden()
    g.run(10)
    ok, r = verify_garden_log(g)
    assert ok, r


def test_replay_verifies():
    g = _garden()
    g.run(10)
    ok, r = verify_garden_replay(g)
    assert ok, r


def test_plants_log_verifies():
    g = _garden()
    g.run(15)
    for sid, p in g.plants().items():
        ok, r = verify_world_log(p)
        assert ok, r
        ok, r = verify_growth(p)
        assert ok, r


# -- Branch refusals --

def test_refuse_observe_tier():
    g = _garden()
    g.run(5)
    bob_kp = _kp()
    bob_key = g.issue_world_key(
        _did_from_kp(bob_kp), "observe")
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"light_level": 3}, bob_kp, bob_key)
    r = g.request_branch(req)
    assert isinstance(r, GardenRefusalRecord)
    assert r.reason == "insufficient_tier"


def test_refuse_sandbox():
    g = _garden(template=_template(branchy=False))
    g.run(5)
    alice_kp = _kp()
    alice_key = g.issue_world_key(
        _did_from_kp(alice_kp), "terminal")
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"light_level": 3}, alice_kp, alice_key)
    r = g.request_branch(req)
    assert isinstance(r, GardenRefusalRecord)
    assert r.reason == "sandboxed"


def test_refuse_out_of_range():
    g = _garden()
    g.run(5)
    alice_kp = _kp()
    alice_key = g.issue_world_key(
        _did_from_kp(alice_kp), "control",
        param_scopes={"light_level": (3, 10)})
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"light_level": 99}, alice_kp, alice_key)
    r = g.request_branch(req)
    assert isinstance(r, GardenRefusalRecord)
    assert r.reason == "template_range:light_level"


def test_refuse_unknown_param():
    g = _garden()
    g.run(5)
    alice_kp = _kp()
    alice_key = g.issue_world_key(
        _did_from_kp(alice_kp), "control")
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"nonsense": 3}, alice_kp, alice_key)
    r = g.request_branch(req)
    assert isinstance(r, GardenRefusalRecord)
    assert r.reason == "unknown_param:nonsense"


def test_refusal_is_in_log():
    g = _garden()
    g.run(5)
    bob_kp = _kp()
    bob_key = g.issue_world_key(
        _did_from_kp(bob_kp), "observe")
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"light_level": 3}, bob_kp, bob_key)
    g.request_branch(req)
    refusals = [r for r in g.records()
                if isinstance(r, GardenRefusalRecord)]
    assert len(refusals) == 1
    assert refusals[0].requester_id == _did_from_kp(bob_kp)


# -- Branch acceptance --

def test_accept_branch():
    g = _garden()
    g.run(8)
    alice_kp = _kp()
    alice_key = g.issue_world_key(
        _did_from_kp(alice_kp), "control",
        param_scopes={"light_level": (3, 10)})
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"light_level": 3}, alice_kp, alice_key)
    r = g.request_branch(req)
    assert isinstance(r, tuple)
    seed, branch = r
    assert branch.template.light_level == 3
    # Parent's template unchanged
    assert g.template.light_level == 10


def test_branch_inherits_water_and_plants():
    g = _garden()
    g.run(8)
    parent_water = [list(row) for row in g.grid.levels]
    alice_kp = _kp()
    alice_key = g.issue_world_key(
        _did_from_kp(alice_kp), "control")
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"light_level": 3}, alice_kp, alice_key)
    seed, branch = g.request_branch(req)
    # Water inherited
    assert branch.grid.levels == parent_water
    # Plants inherited (same slot ids, same geometry)
    assert set(branch.plants().keys()) == set(g.plants().keys())
    for sid in g.plants():
        p = g.plants()[sid]
        q = branch.plants()[sid]
        assert sorted(p.segments()) == sorted(q.segments())


def test_branch_continues_independently():
    g = _garden()
    g.run(8)
    alice_kp = _kp()
    alice_key = g.issue_world_key(
        _did_from_kp(alice_kp), "control")
    req = sign_garden_branch_request(
        g.world_id, g.last_hash(),
        {"light_level": 3}, alice_kp, alice_key)
    seed, branch = g.request_branch(req)
    parent_log_len = len(g.records())
    branch_log_len = len(branch.records())
    # Advance both
    g.run(5)
    branch.run(5)
    # Each has grown its own log by exactly 5 ticks
    assert len(g.records()) == parent_log_len + 5
    assert len(branch.records()) == branch_log_len + 5


# -- Verification catches tampering --

def test_tampered_level_hash_rejected():
    g = _garden()
    g.run(5)
    # Tamper the last tick's level_hash and re-sign with the
    # garden's key. The chain stays valid (re-signed), but replay
    # must catch the wrong level_hash.
    orig = g.records()[-1]
    bad_body = {**orig.body(), "level_hash": "00" * 32}
    bad_sig = g._keypair.sign(
        __import__("json").dumps(
            bad_body, sort_keys=True,
            separators=(",", ":")).encode()).hex()
    bad = GardenTick(
        world_id=orig.world_id, step=orig.step, t=orig.t,
        prev=orig.prev, rain=orig.rain, moves=orig.moves,
        soak=orig.soak, evap=orig.evap,
        energy_delta=orig.energy_delta,
        plant_growths=orig.plant_growths,
        plant_hashes=orig.plant_hashes,
        level_hash="00" * 32, ts=orig.ts, sig=bad_sig)
    g._records[-1] = bad
    g._last_hash = bad.record_hash()
    ok_log, _ = verify_garden_log(g)
    ok_rep, r = verify_garden_replay(g)
    assert ok_log
    assert not ok_rep


# -- Demo --

def test_demo(tmp_path):
    from fractal_garden import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["branch_id"] is not None
    assert audit["parent_params"]["light_level"] == 10
    assert audit["branch_params"]["light_level"] == 3
    # Both plants' own logs verify in both gardens
    for name in ("parent", "branch"):
        c = audit["verification"][name]
        assert c["log_valid"]
        assert c["replay_valid"]
        for sid in ("slot-a", "slot-b"):
            lk = f"plant_{sid}_log"
            gk = f"plant_{sid}_growth"
            assert c[lk], (name, sid, "log")
            assert c[gk], (name, sid, "growth")
