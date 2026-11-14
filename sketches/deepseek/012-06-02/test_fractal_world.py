import pytest
from fractal_world import (
    WorldTemplate, AtomicFractalWorld,
    verify_log, verify_growth, reconstruct,
    render_ascii, render_svg, HAS_CRYPTO)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    return Ed25519PrivateKey.generate()


def _world():
    return AtomicFractalWorld(
        template=WorldTemplate(
            template_id="fractal-plant-v1",
            branch_length=2, max_depth=4),
        pot=(0, 0, 20, 20),
        initial_tip=(10, 18, 0),
        keypair=_kp())


def test_seed_signed():
    w = _world()
    assert w.seed().sig
    assert w.seed().world_id == w.world_id


def test_grow_produces_record():
    w = _world()
    rec = w.grow()
    assert rec is not None
    assert rec.step == 0
    assert rec.prev is None


def test_grow_chain():
    w = _world()
    r0 = w.grow()
    r1 = w.grow()
    assert r1.prev == r0.record_hash()


def test_grow_until_done():
    w = _world()
    n = w.grow_until_done()
    assert n > 0
    assert not w.is_growing()


def test_boundary_respected():
    w = _world()
    w.grow_until_done()
    px, py, pw, ph = w.seed().pot
    for (x1, y1, x2, y2) in w.segments():
        for (x, y) in [(x1, y1), (x2, y2)]:
            assert px <= x < px + pw
            assert py <= y < py + ph


def test_verify_log_happy():
    w = _world()
    w.grow_until_done()
    ok, reason = verify_log(w.seed(), w.records(), w.world_id)
    assert ok, reason


def test_verify_growth_happy():
    w = _world()
    w.grow_until_done()
    ok, reason = verify_growth(
        w.seed(), w.records(), w._template)
    assert ok, reason


def test_verify_growth_rejects_wrong_template():
    w = _world()
    w.grow_until_done()
    bad = WorldTemplate(
        template_id="fractal-plant-v1",
        branch_length=3,  # different from the one used
        max_depth=4)
    ok, _ = verify_growth(w.seed(), w.records(), bad)
    assert not ok


def test_reconstruct_matches_live():
    w = _world()
    w.grow_until_done()
    p = reconstruct(w.seed(), w.records())
    assert sorted(p.segments) == sorted(w.segments())
    assert sorted(p.frontier) == sorted(w.frontier())


def test_render_ascii():
    w = _world()
    w.grow_until_done()
    p = reconstruct(w.seed(), w.records())
    text = render_ascii(p)
    assert "#" in text
    assert len(text.split("\n")) == 20


def test_render_svg():
    w = _world()
    w.grow_until_done()
    p = reconstruct(w.seed(), w.records())
    svg = render_svg(p)
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert "<line" in svg
