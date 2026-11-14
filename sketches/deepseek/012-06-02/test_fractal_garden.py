import pytest
from fractal_garden import (
    GardenTemplate, GardenWorld,
    PlantAddedRecord, PlantRetiredRecord, GardenCycleRecord,
    plant_certificate, verify_plant_certificate,
    verify_garden_log, verify_garden_with_plants,
    render_garden_ascii, demo, HAS_CRYPTO)
from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _garden_template():
    return GardenTemplate(
        slot_count=4, slot_width=15, slot_height=15)


def _plant_template():
    return WorldTemplate(
        template_id="t", branch_length=2, max_depth=4)


def _new_plant(garden_template, slot, plant_template=None):
    plant_template = plant_template or _plant_template()
    return AtomicFractalWorld(
        template=plant_template,
        pot=garden_template.slot_rect(slot),
        initial_tip=garden_template.initial_tip(slot),
        keypair=Ed25519PrivateKey.generate())


def _garden():
    return GardenWorld(_garden_template(),
                       Ed25519PrivateKey.generate())


# -- Template geometry --

def test_slot_rect_grid():
    t = GardenTemplate(slot_count=4, slot_width=10,
                        slot_height=10)
    assert t.slot_rect(0) == (0, 0, 10, 10)
    assert t.slot_rect(1) == (10, 0, 10, 10)
    assert t.slot_rect(2) == (0, 10, 10, 10)
    assert t.slot_rect(3) == (10, 10, 10, 10)


def test_slot_rect_3x2():
    t = GardenTemplate(slot_count=6, slot_width=10,
                        slot_height=10)
    cols, rows = t.grid()
    assert cols == 3
    assert rows == 2
    assert t.slot_rect(5) == (20, 10, 10, 10)


def test_slot_rect_out_of_range():
    t = GardenTemplate(slot_count=4, slot_width=10,
                        slot_height=10)
    with pytest.raises(ValueError):
        t.slot_rect(4)


# -- Planting --

def test_plant_in_empty_slot():
    g = _garden()
    p = _new_plant(_garden_template(), 0)
    r = g.plant(0, p)
    assert isinstance(r, PlantAddedRecord)
    assert 0 in g.plants()


def test_plant_refuses_occupied_slot():
    g = _garden()
    p = _new_plant(_garden_template(), 0)
    g.plant(0, p)
    p2 = _new_plant(_garden_template(), 0)
    assert g.plant(0, p2) is None


def test_plant_refuses_wrong_pot():
    g = _garden()
    # Make a plant whose pot is slot 1's rect, but plant in slot 0
    p = _new_plant(_garden_template(), 1)
    assert g.plant(0, p) is None


def test_plant_refuses_out_of_range():
    g = _garden()
    p = _new_plant(_garden_template(), 0)
    assert g.plant(99, p) is None


def test_plant_cert_verifies():
    g = _garden()
    p = _new_plant(_garden_template(), 0)
    cert = plant_certificate(p)
    assert verify_plant_certificate(cert)


def test_tampered_plant_cert_rejected():
    g = _garden()
    p = _new_plant(_garden_template(), 0)
    cert = plant_certificate(p)
    cert["seed_sig"] = "00" * 64
    assert not verify_plant_certificate(cert)


# -- Growth --

def test_grow_advances_plants():
    g = _garden()
    p0 = _new_plant(_garden_template(), 0)
    g.plant(0, p0)
    segs_before = len(p0.segments())
    g.grow()
    assert len(p0.segments()) > segs_before


def test_grow_records_cycle():
    g = _garden()
    g.plant(0, _new_plant(_garden_template(), 0))
    g.grow()
    g.grow()
    assert g.cycle() == 2
    cycles = [r for r in g.records()
              if isinstance(r, GardenCycleRecord)]
    assert len(cycles) == 2
    assert cycles[0].cycle == 1
    assert cycles[1].cycle == 2


def test_grow_records_steps_per_plant():
    g = _garden()
    p0 = _new_plant(_garden_template(), 0)
    g.plant(0, p0)
    g.grow()
    last = g.records()[-1]
    assert last.advances[0]["plant_id"] == p0.world_id
    assert last.advances[0]["steps"] == 1


def test_grow_with_empty_slots():
    g = _garden()
    # No plants
    g.grow()
    last = g.records()[-1]
    assert last.advances == []


# -- Retirement --

def test_retire_clears_slot():
    g = _garden()
    p = _new_plant(_garden_template(), 0)
    g.plant(0, p)
    r = g.retire(0, "wilting")
    assert isinstance(r, PlantRetiredRecord)
    assert 0 not in g.plants()


def test_retire_empty_slot_returns_none():
    g = _garden()
    assert g.retire(0, "x") is None


def test_replant_after_retire():
    g = _garden()
    p1 = _new_plant(_garden_template(), 0)
    g.plant(0, p1)
    g.retire(0, "x")
    p2 = _new_plant(_garden_template(), 0)
    r = g.plant(0, p2)
    assert isinstance(r, PlantAddedRecord)


# -- Verification --

def test_verify_empty_garden():
    g = _garden()
    ok, reason = verify_garden_log(g)
    assert ok, reason


def test_verify_with_plants():
    g = _garden()
    for slot in (0, 1):
        g.plant(slot, _new_plant(_garden_template(), slot))
    g.grow_n(2)
    ok, reason = verify_garden_log(g)
    assert ok, reason


def test_verify_full_with_plants_and_cross_check():
    g = _garden()
    for slot in (0, 1, 2):
        g.plant(slot, _new_plant(_garden_template(), slot))
    g.grow_n(4)
    ok, reason = verify_garden_with_plants(g)
    assert ok, reason


def test_verify_detects_tampered_garden_record():
    g = _garden()
    g.plant(0, _new_plant(_garden_template(), 0))
    g.grow()
    # Tamper: break a record's signature
    tampered = list(g.records())
    orig = tampered[-1]
    tampered[-1] = GardenCycleRecord(
        world_id=orig.world_id, cycle=orig.cycle,
        advances=orig.advances, prev=orig.prev,
        ts=orig.ts, sig="00" * 64)
    g._records = tampered  # test-only surgery
    ok, _ = verify_garden_log(g)
    assert not ok


def test_verify_detects_cross_check_failure():
    """If a plant's log doesn't match what the garden claims
    it drove, the cross-check fails."""
    g = _garden()
    p = _new_plant(_garden_template(), 0)
    g.plant(0, p)
    g.grow_n(2)
    # Drive the plant directly without telling the garden
    p.grow()
    p.grow()
    ok, reason = verify_garden_with_plants(g)
    assert not ok
    assert "growth records" in reason or "cross" in reason.lower()


# -- Rendering --

def test_render_empty():
    g = _garden()
    text = render_garden_ascii(g)
    assert "·" in text
    assert "|" in text
    assert "+" in text


def test_render_with_plants():
    g = _garden()
    g.plant(0, _new_plant(_garden_template(), 0))
    g.grow_n(2)
    text = render_garden_ascii(g)
    assert "#" in text


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["garden_log_valid"] is True
    assert audit["full_verification_valid"] is True
    assert "0" in audit["plants"]
    assert "1" in audit["plants"]
    assert "2" in audit["plants"]
    assert "3" not in audit["plants"]  # never planted
    assert (tmp_path / "fractal_garden" /
            "fractal_garden_demo.json").exists()
