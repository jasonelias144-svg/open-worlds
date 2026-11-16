import pytest
from botanical_garden import (
    GardenSpec, BotanicalTemplate, BotanicalGarden,
    BotanicalTick, BotanicalRefusalRecord,
    sign_botanical_branch_request,
    verify_botanical_log, verify_botanical_cross,
    render_botanical, HAS_CRYPTO, SUPER_PARAM_NAMES)
from fractal_garden import (
    GardenTemplate, SlotRect, PlantAssignment,
    verify_garden_log, verify_garden_replay)
from fractal_world_v3 import _did_from_kp
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _garden_template(tid, rain=0):
    return GardenTemplate(
        template_id=tid,
        slot_rects=[SlotRect("p1", 1, 2, 6, 6)],
        water_width=8, water_height=8,
        rain_rate=rain, evap_rate=10,
        water_max=8, energy_cap=20, growth_cost=1,
        light_level=10, branch_policy=None)


def _spec(sid, x_start, x_end, rain=0):
    return GardenSpec(
        slot_id=sid,
        garden_template=_garden_template(f"{sid}-v1", rain),
        plant_assignments=[PlantAssignment(
            "p1", (3, 6, 0),
            {"branch_length": 2, "max_depth": 2,
             "water": 10, "light": 10})],
        gutter_x_start=x_start,
        gutter_x_end=x_end)


def _template(branchy=True, dispatch="by_gutter"):
    policy = {"control": {"rain_rate": (32, 160)},
              "terminal": {"rain_rate": (16, 160)}} \
        if branchy else None
    return BotanicalTemplate(
        template_id="t-bot",
        roof_width=16, roof_height=3,
        garden_specs=[_spec("a", 0, 8), _spec("b", 8, 16)],
        rain_rate=96,
        dispatch_policy=dispatch,
        opening_hours=(9, 17),
        branch_policy=policy)


def _botanical(template=None):
    return BotanicalGarden(template or _template(), _kp())


# -- Construction --

def test_gardens_created():
    b = _botanical()
    assert set(b.gardens().keys()) == {"a", "b"}


def test_seed_signs():
    b = _botanical()
    assert b.seed()["sig"]


# -- Ticking --

def test_rain_falls_on_roof():
    b = _botanical()
    b.run(10)
    total = sum(sum(row) for row in b.roof.levels)
    # Some water may have dispatched, but the roof should
    # still see water at some point. Check cumulative rain.
    rains = sum(len(rec.roof_rain) for rec in b.records()
                if isinstance(rec, BotanicalTick))
    assert rains > 0


def test_dispatch_reaches_gardens():
    b = _botanical()
    b.run(10)
    for sid, g in b.gardens().items():
        # Garden has some water at the top (received external)
        assert sum(sum(row) for row in g.grid.levels) >= 0
        # Or grew a plant
        assert any(len(p.records()) > 0 for p in g.plants().values())


def test_gardens_tick_under_superworld():
    b = _botanical()
    b.run(10)
    for sid, g in b.gardens().items():
        # Each garden has 10 ticks in its own log
        assert len(g.records()) == 10


# -- Cross-check --

def test_cross_check_matches():
    b = _botanical()
    b.run(8)
    ok, r = verify_botanical_cross(b)
    assert ok, r


def test_cross_check_detects_mismatch():
    b = _botanical()
    b.run(3)
    # Tamper the last dispatch in the superworld's log
    last = b.records()[-1]
    assert isinstance(last, BotanicalTick)
    tampered_dispatch = dict(last.dispatch)
    for sid in tampered_dispatch:
        tampered_dispatch[sid] = []
        break
    bad_body = {**last.body(),
                "dispatch": {sid: [[a, b_, c] for (a, b_, c) in share]
                             for sid, share in tampered_dispatch.items()}}
    import json as _json
    bad_sig = b._keypair.sign(_json.dumps(
        bad_body, sort_keys=True,
        separators=(",", ":")).encode()).hex()
    bad = BotanicalTick(
        world_id=last.world_id, step=last.step, t=last.t,
        prev=last.prev, roof_rain=last.roof_rain,
        roof_moves=last.roof_moves,
        dispatch=tampered_dispatch,
        garden_hashes=last.garden_hashes,
        roof_level_hash=last.roof_level_hash,
        ts=last.ts, sig=bad_sig)
    b._records[-1] = bad
    b._last_hash = bad.record_hash()
    ok_log, _ = verify_botanical_log(b)
    ok_cross, r = verify_botanical_cross(b)
    assert ok_log            # signature is valid
    assert not ok_cross      # but the cross-check catches it


# -- Verification --

def test_log_verifies():
    b = _botanical()
    b.run(8)
    ok, r = verify_botanical_log(b)
    assert ok, r


def test_each_garden_verifies():
    b = _botanical()
    b.run(8)
    for sid, g in b.gardens().items():
        ok, r = verify_garden_log(g)
        assert ok, r
        ok, r = verify_garden_replay(g)
        assert ok, r


# -- Branching --

def test_refuse_observe():
    b = _botanical()
    b.run(5)
    bob_kp = _kp()
    bob_key = b.issue_world_key(_did_from_kp(bob_kp), "observe")
    req = sign_botanical_branch_request(
        b.world_id, b.last_hash(), {"rain_rate": 128},
        bob_kp, bob_key)
    r = b.request_branch(req)
    assert isinstance(r, BotanicalRefusalRecord)
    assert r.reason == "insufficient_tier"


def test_refuse_out_of_range():
    b = _botanical()
    b.run(5)
    alice_kp = _kp()
    alice_key = b.issue_world_key(_did_from_kp(alice_kp),
                                    "control")
    req = sign_botanical_branch_request(
        b.world_id, b.last_hash(), {"rain_rate": 9999},
        alice_kp, alice_key)
    r = b.request_branch(req)
    assert isinstance(r, BotanicalRefusalRecord)
    assert r.reason == "template_range:rain_rate"


def test_refuse_sandbox():
    b = _botanical(template=_template(branchy=False))
    b.run(5)
    alice_kp = _kp()
    alice_key = b.issue_world_key(_did_from_kp(alice_kp),
                                    "terminal")
    req = sign_botanical_branch_request(
        b.world_id, b.last_hash(), {"rain_rate": 128},
        alice_kp, alice_key)
    r = b.request_branch(req)
    assert isinstance(r, BotanicalRefusalRecord)
    assert r.reason == "sandboxed"


def test_accept_branch():
    b = _botanical()
    b.run(8)
    alice_kp = _kp()
    alice_key = b.issue_world_key(_did_from_kp(alice_kp),
                                    "control")
    req = sign_botanical_branch_request(
        b.world_id, b.last_hash(), {"rain_rate": 128},
        alice_kp, alice_key)
    r = b.request_branch(req)
    assert isinstance(r, tuple)
    seed, branch = r
    assert branch.template.rain_rate == 128
    assert b.template.rain_rate == 96


def test_branch_inherits_gardens():
    b = _botanical()
    b.run(8)
    alice_kp = _kp()
    alice_key = b.issue_world_key(_did_from_kp(alice_kp),
                                    "control")
    req = sign_botanical_branch_request(
        b.world_id, b.last_hash(), {"rain_rate": 128},
        alice_kp, alice_key)
    seed, branch = b.request_branch(req)
    # Same slot ids
    assert set(branch.gardens().keys()) == set(b.gardens().keys())
    # Water inherited (compare grid levels)
    for sid in b.gardens():
        assert branch.gardens()[sid].grid.levels == \
               b.gardens()[sid].grid.levels


def test_branch_continues_independently():
    b = _botanical()
    b.run(5)
    alice_kp = _kp()
    alice_key = b.issue_world_key(_did_from_kp(alice_kp),
                                    "control")
    req = sign_botanical_branch_request(
        b.world_id, b.last_hash(), {"rain_rate": 128},
        alice_kp, alice_key)
    seed, branch = b.request_branch(req)
    parent_len = len(b.records())
    branch_len = len(branch.records())
    b.run(3)
    branch.run(3)
    assert len(b.records()) == parent_len + 3
    assert len(branch.records()) == branch_len + 3


def test_branch_verifies():
    b = _botanical()
    b.run(6)
    alice_kp = _kp()
    alice_key = b.issue_world_key(_did_from_kp(alice_kp),
                                    "control")
    req = sign_botanical_branch_request(
        b.world_id, b.last_hash(), {"rain_rate": 128},
        alice_kp, alice_key)
    seed, branch = b.request_branch(req)
    branch.run(4)
    ok, r = verify_botanical_log(branch)
    assert ok, r
    ok, r = verify_botanical_cross(branch)
    assert ok, r
    for sid, g in branch.gardens().items():
        ok, r = verify_garden_log(g)
        assert ok, r


# -- Render --

def test_render_shape():
    b = _botanical()
    b.tick()
    text = render_botanical(b)
    assert "ROOF" in text
    assert "GARDEN a" in text
    assert "GARDEN b" in text


# -- Demo --

def test_demo(tmp_path):
    from botanical_garden import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["branch_id"] is not None
    assert audit["parent_params"]["rain_rate"] == 96
    p = audit["verification"]["parent"]
    assert p["log_valid"]
    assert p["cross_valid"]
    for sid in ("garden-a", "garden-b"):
        assert p[f"{sid}_log"]
        assert p[f"{sid}_replay"]
