import pytest
from gallery_world import (
    GalleryWorld, GalleryMember,
    AtomicFractalMember, FractalGridMember,
    ChaosGameMember, CoupledCAMember,
    verify_seed_cert,
    verify_gallery_log, verify_gallery_members, verify_full,
    render_gallery, demo, HAS_CRYPTO,
)
from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
from fractal_grid_world import FractalGridWorld, GridParams
from chaos_game_world import ChaosGameWorld, SIERPINSKI
from coupled_ca_world import CoupledCAWorld
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _gallery():
    return GalleryWorld(_kp())


# -- Adapter interface --

def test_atomic_fractal_member():
    w = AtomicFractalWorld(
        template=WorldTemplate(
            template_id="t", branch_length=2, max_depth=2),
        pot=(0, 0, 10, 10),
        initial_tip=(5, 8, 0),
        keypair=_kp())
    m = AtomicFractalMember(w)
    assert m.kind == "atomic_fractal"
    assert m.steps() == 0
    assert m.grow() is not None
    assert m.steps() == 1


def test_fractal_grid_member():
    w = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp())
    m = FractalGridMember(w, max_gen=5)
    assert m.grow() is not None
    assert m.steps() == 1
    for _ in range(10):
        m.grow()
    assert m.steps() == 5  # capped


def test_chaos_game_member():
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="seeded_random",
        initial_point=(500, 500), keypair=_kp(),
        prng_seed=42)
    m = ChaosGameMember(w, max_steps=10)
    for _ in range(5):
        m.grow()
    assert m.steps() == 5


def test_chaos_rejects_external_mode():
    w = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=_kp(),
        input_authority="did:key:" + "00" * 32)
    with pytest.raises(ValueError):
        ChaosGameMember(w)


def test_coupled_ca_member():
    w = CoupledCAWorld(
        rule_a=90, rule_b=90,
        initial_a=[0], initial_b=[10],
        k_a=50, k_b=50, keypair=_kp())
    m = CoupledCAMember(w, max_gen=3)
    for _ in range(10):
        m.grow()
    assert m.steps() == 3


# -- Seed cert --

def test_seed_cert_verifies_for_all_kinds():
    worlds = [
        AtomicFractalWorld(
            template=WorldTemplate(
                template_id="t", branch_length=2, max_depth=2),
            pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
            keypair=_kp()),
        FractalGridWorld(
            params=GridParams(rule_number=90),
            initial_row=[0], keypair=_kp()),
        ChaosGameWorld(
            preset=SIERPINSKI, growth_mode="seeded_random",
            initial_point=(500, 500), keypair=_kp(),
            prng_seed=42),
        CoupledCAWorld(
            rule_a=90, rule_b=90,
            initial_a=[0], initial_b=[10],
            k_a=50, k_b=50, keypair=_kp()),
    ]
    for w in worlds:
        cert = {
            "kind": "x",
            "world_id": w.world_id,
            "seed_body": w.seed_body(),
            "seed_sig": w.seed_sig(),
        }
        assert verify_seed_cert(cert)


def test_seed_cert_tampered_rejected():
    w = AtomicFractalWorld(
        template=WorldTemplate(
            template_id="t", branch_length=2, max_depth=2),
        pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
        keypair=_kp())
    cert = {
        "kind": "atomic_fractal",
        "world_id": w.world_id,
        "seed_body": w.seed_body(),
        "seed_sig": "00" * 64,
    }
    assert not verify_seed_cert(cert)


# -- Gallery operations --

def test_add_and_retire():
    g = _gallery()
    w = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp())
    assert g.add(0, FractalGridMember(w)) is not None
    assert 0 in g.members()
    assert g.add(0, FractalGridMember(w)) is None  # occupied
    assert g.retire(0, "done") is not None
    assert 0 not in g.members()


def test_grow_advances_all():
    g = _gallery()
    w = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp())
    g.add(0, FractalGridMember(w))
    g.grow_n(5)
    assert g.cycle() == 5
    assert g.members()[0].steps() == 5


# -- Verification --

def test_gallery_log_verifies():
    g = _gallery()
    for slot, kind in enumerate(("plant", "grid", "chaos")):
        if kind == "plant":
            w = AtomicFractalWorld(
                template=WorldTemplate(
                    template_id="t", branch_length=2,
                    max_depth=2),
                pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
                keypair=_kp())
            g.add(slot, AtomicFractalMember(w))
        elif kind == "grid":
            w = FractalGridWorld(
                params=GridParams(rule_number=90),
                initial_row=[0], keypair=_kp())
            g.add(slot, FractalGridMember(w, max_gen=5))
        else:
            w = ChaosGameWorld(
                preset=SIERPINSKI, growth_mode="seeded_random",
                initial_point=(500, 500), keypair=_kp(),
                prng_seed=42)
            g.add(slot, ChaosGameMember(w, max_steps=5))
    g.grow_n(5)
    ok, reason = verify_gallery_log(g)
    assert ok, reason


def test_full_verifies_mixed_gallery():
    g = _gallery()
    plant = AtomicFractalWorld(
        template=WorldTemplate(
            template_id="t", branch_length=2, max_depth=2),
        pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
        keypair=_kp())
    grid = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp())
    chaos = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="seeded_random",
        initial_point=(500, 500), keypair=_kp(),
        prng_seed=42)
    ca = CoupledCAWorld(
        rule_a=90, rule_b=90,
        initial_a=[0], initial_b=[10],
        k_a=50, k_b=50, keypair=_kp())
    g.add(0, AtomicFractalMember(plant))
    g.add(1, FractalGridMember(grid, max_gen=5))
    g.add(2, ChaosGameMember(chaos, max_steps=5))
    g.add(3, CoupledCAMember(ca, max_gen=5))
    g.grow_n(10)
    ok, reason = verify_full(g)
    assert ok, reason


def test_cross_check_detects_mismatch():
    """If we drive a member directly, the cross-check fails."""
    g = _gallery()
    grid = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp())
    m = FractalGridMember(grid)
    g.add(0, m)
    g.grow_n(5)
    # Drive the grid directly, outside the gallery
    grid.grow()
    grid.grow()
    ok, reason = verify_gallery_members(g)
    assert not ok
    assert "5" in reason and "7" in reason


def test_cross_check_detects_tampered_gallery_log():
    g = _gallery()
    grid = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp())
    g.add(0, FractalGridMember(grid))
    g.grow_n(5)
    # Tamper a cycle record
    from gallery_world import GalleryCycleRecord
    tampered = list(g.records())
    for i, r in enumerate(tampered):
        if isinstance(r, GalleryCycleRecord):
            tampered[i] = GalleryCycleRecord(
                world_id=r.world_id, cycle=r.cycle,
                advances=tuple(
                    {**a, "steps_taken": 99} for a in r.advances),
                prev=r.prev, ts=r.ts, sig=r.sig)
            break
    g._records = tampered
    ok, _ = verify_gallery_log(g)
    assert not ok


# -- Rendering --

def test_render_gallery():
    g = _gallery()
    w = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp())
    g.add(0, FractalGridMember(w, max_gen=5))
    g.grow_n(5)
    text = render_gallery(g)
    assert "slot 0" in text
    assert "fractal_grid" in text


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verify_gallery_log"] is True
    assert audit["verify_gallery_members"] is True
    assert audit["verify_full"] is True
    assert len(audit["members"]) == 4
    kinds = {m["kind"] for m in audit["members"]}
    assert kinds == {"atomic_fractal", "fractal_grid",
                      "chaos_game", "coupled_ca"}
    assert (tmp_path / "gallery" /
            "gallery_demo.json").exists()
