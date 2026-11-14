import pytest
from gallery_meta_coupling import (
    MetaKChangeRecord, MetaCoupledGalleryWorld,
    verify_meta_coupled_log, verify_meta_coupled_full,
    render_step_table, demo, HAS_CRYPTO,
)
from gallery_governance import GalleryPolicy, GalleryCycleRecord
from gallery_world import AtomicFractalMember, FractalGridMember
from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
from fractal_grid_world import FractalGridWorld, GridParams
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _gallery(meta_k=0, n_members=4):
    policy = GalleryPolicy(
        max_members=n_members,
        allowed_kinds=("atomic_fractal", "fractal_grid"))
    g = MetaCoupledGalleryWorld(_kp(), policy, meta_k=meta_k)
    for slot in range(n_members):
        if slot % 2 == 0:
            plant = AtomicFractalMember(AtomicFractalWorld(
                template=WorldTemplate(
                    template_id="t", branch_length=2,
                    max_depth=3),
                pot=(0, 0, 12, 12),
                initial_tip=(6, 10, 0), keypair=_kp()))
            g.add(slot, plant)
        else:
            grid = FractalGridMember(FractalGridWorld(
                params=GridParams(rule_number=90),
                initial_row=[0], keypair=_kp()))
            g.add(slot, grid)
    return g


# -- Scheduling math --

def test_k0_all_grow():
    g = _gallery(meta_k=0)
    g.grow()
    rec = g.records()[-1]
    assert all(a["selected"] for a in rec.advances)
    assert all(a["steps_taken"] == 1 for a in rec.advances)


def test_k100_one_grows():
    g = _gallery(meta_k=100)
    g.grow()
    rec = g.records()[-1]
    selected = [a for a in rec.advances if a["selected"]]
    assert len(selected) == 1
    assert selected[0]["slot"] == 0  # tie-break by slot


def test_k50_half_grow():
    g = _gallery(meta_k=50, n_members=4)
    g.grow()
    rec = g.records()[-1]
    selected = [a for a in rec.advances if a["selected"]]
    assert len(selected) == 2
    assert {a["slot"] for a in selected} == {0, 1}


def test_k100_rotates():
    """After N cycles, all N members have grown exactly once."""
    g = _gallery(meta_k=100, n_members=4)
    g.grow_n(4)
    steps = {slot: m.steps()
             for slot, m in g.members().items()}
    # Each member has exactly 1 step (fair rotation)
    assert all(s == 1 for s in steps.values()), steps


def test_k0_lockstep():
    g = _gallery(meta_k=0, n_members=4)
    g.grow_n(10)
    steps = {slot: m.steps()
             for slot, m in g.members().items()}
    # All advance equally (modulo cap-dependent non-growth)
    assert len(set(steps.values())) <= 2


def test_k100_fair_over_time():
    """Over N cycles at k=100, each of N members gets 1 step."""
    g = _gallery(meta_k=100, n_members=4)
    g.grow_n(8)
    steps = [m.steps() for m in g.members().values()]
    assert sum(steps) == 8
    # Fair: each has 2
    assert all(s == 2 for s in steps), steps


# -- meta_k change --

def test_set_meta_k():
    g = _gallery(meta_k=0)
    rec = g.set_meta_k(100)
    assert isinstance(rec, MetaKChangeRecord)
    assert g.meta_k() == 100


def test_meta_k_change_mid_run():
    g = _gallery(meta_k=0)
    g.grow_n(5)
    g.set_meta_k(100)
    g.grow_n(5)
    # First 5 cycles: all 4 grew 5 times each = 20 total
    # Last 5 cycles: 1 grew per cycle = 5 more
    # Total 25 steps across all members
    total = sum(m.steps() for m in g.members().values())
    assert total == 25


def test_set_meta_k_rejects_out_of_range():
    g = _gallery()
    with pytest.raises(ValueError):
        g.set_meta_k(200)
    with pytest.raises(ValueError):
        g.set_meta_k(-1)


# -- Verification --

def test_verify_k0():
    g = _gallery(meta_k=0)
    g.grow_n(5)
    ok, reason = verify_meta_coupled_full(g)
    assert ok, reason


def test_verify_k100():
    g = _gallery(meta_k=100)
    g.grow_n(8)
    ok, reason = verify_meta_coupled_full(g)
    assert ok, reason


def test_verify_k_change():
    g = _gallery(meta_k=0)
    g.grow_n(5)
    g.set_meta_k(100)
    g.grow_n(5)
    ok, reason = verify_meta_coupled_full(g)
    assert ok, reason


def test_verify_tampered_selection():
    """If we manually change a cycle record's `selected` flags,
    verification catches it."""
    g = _gallery(meta_k=100, n_members=4)
    g.grow_n(2)
    # Tamper: the first cycle selected slot 0; change it to slot 3
    tampered = list(g.records())
    for i, r in enumerate(tampered):
        if isinstance(r, GalleryCycleRecord):
            new_advs = tuple(
                {**a, "selected": a["slot"] == 3}
                for a in r.advances)
            tampered[i] = GalleryCycleRecord(
                world_id=r.world_id, cycle=r.cycle,
                advances=new_advs, prev=r.prev,
                ts=r.ts, sig=r.sig)
            break
    g._records = tampered
    ok, _ = verify_meta_coupled_log(g)
    assert not ok


def test_verify_tampered_meta_k_change():
    """If old_k doesn't match accumulated state, verification
    fails."""
    g = _gallery(meta_k=0)
    g.grow_n(3)
    g.set_meta_k(100)
    # Tamper: change old_k
    tampered = list(g.records())
    for i, r in enumerate(tampered):
        if isinstance(r, MetaKChangeRecord):
            tampered[i] = MetaKChangeRecord(
                world_id=r.world_id,
                old_k=50, new_k=r.new_k,
                prev=r.prev, ts=r.ts, sig=r.sig)
            break
    g._records = tampered
    ok, _ = verify_meta_coupled_log(g)
    assert not ok


# -- Rendering --

def test_step_table():
    g = _gallery(meta_k=100, n_members=4)
    g.grow_n(4)
    text = render_step_table(g, max_cycles=10)
    assert "cycle" in text
    assert "slot 0" in text
    lines = text.split("\n")
    # header + separator + 4 data rows
    assert len([l for l in lines if "|" in l]) >= 6


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["k_0"]["verify"] is True
    assert audit["k_50"]["verify"] is True
    assert audit["k_100"]["verify"] is True
    assert audit["k_change"]["verify"] is True
    # k=0 gives higher per-member steps than k=100
    k0_total = sum(m["steps"] for m in audit["k_0"]["members"])
    k100_total = sum(m["steps"] for m in audit["k_100"]["members"])
    assert k0_total > k100_total
    # k=100 is perfectly fair
    k100_steps = [m["steps"] for m in audit["k_100"]["members"]]
    assert len(set(k100_steps)) == 1, k100_steps
    assert (tmp_path / "gallery_meta_coupling" /
            "meta_coupling_demo.json").exists()
