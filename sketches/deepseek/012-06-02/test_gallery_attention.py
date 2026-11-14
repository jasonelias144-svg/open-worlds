import pytest
from gallery_attention import (
    DefaultAttentionChangeRecord, MemberAttentionChangeRecord,
    AttentiveGalleryWorld,
    verify_attention_log, verify_attention_full,
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


def _gallery(default_attn=100, n=4):
    policy = GalleryPolicy(
        max_members=n,
        allowed_kinds=("atomic_fractal", "fractal_grid"))
    g = AttentiveGalleryWorld(_kp(), policy,
                                default_attention=default_attn)
    for slot in range(n):
        if slot % 2 == 0:
            m = AtomicFractalMember(AtomicFractalWorld(
                template=WorldTemplate(
                    template_id="t", branch_length=2,
                    max_depth=2),
                pot=(0, 0, 10, 10),
                initial_tip=(5, 8, 0), keypair=_kp()))
        else:
            m = FractalGridMember(FractalGridWorld(
                params=GridParams(rule_number=90),
                initial_row=[0], keypair=_kp()))
        g.add(slot, m)
    return g


# -- DRR basics --

def test_attention_100_every_cycle():
    g = _gallery(default_attn=100)
    g.grow_n(10)
    for m in g.members().values():
        assert m.steps() == 10


def test_attention_50_every_other():
    g = _gallery(default_attn=50)
    g.grow_n(10)
    for m in g.members().values():
        assert m.steps() == 5


def test_attention_33_approx_third():
    g = _gallery(default_attn=33)
    g.grow_n(30)
    for m in g.members().values():
        assert 9 <= m.steps() <= 11


def test_attention_0_never():
    g = _gallery(default_attn=0)
    g.grow_n(10)
    for m in g.members().values():
        assert m.steps() == 0


# -- Per-member override --

def test_member_override():
    g = _gallery(default_attn=50)
    slot0 = g.members()[0].world_id()
    g.set_member_attention(slot0, 100)
    g.grow_n(10)
    assert g.members()[0].steps() == 10   # 100%
    for s in (1, 2, 3):
        assert g.members()[s].steps() == 5   # 50%


def test_member_attention_change_mid_run():
    g = _gallery(default_attn=50)
    g.grow_n(10)
    # After 10 cycles at 50%, each has 5 steps
    for m in g.members().values():
        assert m.steps() == 5
    slot0 = g.members()[0].world_id()
    g.set_member_attention(slot0, 100)
    g.grow_n(10)
    # Now slot 0 got 10 more (total 15), others 5 more (total 10)
    assert g.members()[0].steps() == 15
    for s in (1, 2, 3):
        assert g.members()[s].steps() == 10


def test_default_attention_change():
    g = _gallery(default_attn=100)
    g.grow_n(5)
    g.set_default_attention(50)
    g.grow_n(10)
    # First 5 at 100%, next 10 at 50%: 5 + 5 = 10 per member
    for m in g.members().values():
        assert m.steps() == 10


def test_rejects_bad_attention():
    g = _gallery()
    with pytest.raises(ValueError):
        g.set_default_attention(200)
    with pytest.raises(ValueError):
        g.set_member_attention(g.members()[0].world_id(), -1)


# -- Verification --

def test_verify_homogeneous():
    g = _gallery(default_attn=50)
    g.grow_n(10)
    ok, reason = verify_attention_full(g)
    assert ok, reason


def test_verify_per_member_override():
    g = _gallery(default_attn=50)
    g.set_member_attention(g.members()[0].world_id(), 100)
    g.grow_n(10)
    ok, reason = verify_attention_full(g)
    assert ok, reason


def test_verify_mid_run_change():
    g = _gallery(default_attn=50)
    g.grow_n(5)
    g.set_member_attention(g.members()[1].world_id(), 100)
    g.grow_n(5)
    ok, reason = verify_attention_full(g)
    assert ok, reason


def test_verify_tampered_selected_flag():
    g = _gallery(default_attn=50)
    g.grow_n(4)
    # Find a cycle where slot 0 was NOT selected and flip it
    tampered = list(g.records())
    for i, r in enumerate(tampered):
        if isinstance(r, GalleryCycleRecord):
            new_advs = tuple(
                {**a, "selected": True}
                if a["slot"] == 0 and not a.get("selected")
                else a
                for a in r.advances)
            if new_advs != r.advances:
                tampered[i] = GalleryCycleRecord(
                    world_id=r.world_id, cycle=r.cycle,
                    advances=new_advs, prev=r.prev,
                    ts=r.ts, sig=r.sig)
                break
    g._records = tampered
    ok, _ = verify_attention_log(g)
    assert not ok


def test_verify_tampered_attention_change():
    g = _gallery(default_attn=50)
    g.set_member_attention(g.members()[0].world_id(), 100)
    g.grow_n(3)
    # Tamper: change old_attention
    tampered = list(g.records())
    for i, r in enumerate(tampered):
        if isinstance(r, MemberAttentionChangeRecord):
            tampered[i] = MemberAttentionChangeRecord(
                world_id=r.world_id, member_id=r.member_id,
                old_attention=75, new_attention=r.new_attention,
                prev=r.prev, ts=r.ts, sig=r.sig)
            break
    g._records = tampered
    ok, _ = verify_attention_log(g)
    assert not ok


def test_verify_detects_tampered_grow_record():
    """If a cycle claims a member grew but DRR wouldn't have
    selected it, verification fails."""
    g = _gallery(default_attn=50)
    g.grow_n(2)
    tampered = list(g.records())
    for i, r in enumerate(tampered):
        if isinstance(r, GalleryCycleRecord):
            new_advs = tuple(
                {**a, "steps_taken": 1,
                 "selected": True}
                if a["slot"] == 0 and a["steps_taken"] == 0
                else a
                for a in r.advances)
            if new_advs != r.advances:
                tampered[i] = GalleryCycleRecord(
                    world_id=r.world_id, cycle=r.cycle,
                    advances=new_advs, prev=r.prev,
                    ts=r.ts, sig=r.sig)
                break
    g._records = tampered
    ok, _ = verify_attention_log(g)
    assert not ok


def test_verify_full_with_mixed_rates():
    g = _gallery(default_attn=100, n=4)
    g.set_member_attention(g.members()[0].world_id(), 25)
    g.set_member_attention(g.members()[1].world_id(), 50)
    g.set_member_attention(g.members()[2].world_id(), 75)
    g.grow_n(20)
    ok, reason = verify_attention_full(g)
    assert ok, reason
    # Rates roughly match
    assert g.members()[0].steps() == 5    # 25%
    assert g.members()[1].steps() == 10   # 50%
    assert g.members()[2].steps() == 15   # 75%
    assert g.members()[3].steps() == 20   # 100%


# -- Rendering --

def test_step_table():
    g = _gallery(default_attn=50)
    g.grow_n(4)
    text = render_step_table(g, max_cycles=10)
    assert "cycle" in text
    assert "slot 0" in text
    assert "attention" in text


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for k in ("A", "B", "C", "D"):
        assert audit[k]["verify"] is True, k
    # A: all members at 15 steps
    assert all(m["steps"] == 15
                for m in audit["A"]["members"])
    # B: all at 7 (50% over 15 cycles)
    b_steps = [m["steps"] for m in audit["B"]["members"]]
    assert all(s in (7, 8) for s in b_steps), b_steps
    # C: slot 0 at 15, rest at 7-8
    c_steps = {m["slot"]: m["steps"]
                for m in audit["C"]["members"]}
    assert c_steps[0] == 15
    assert all(c_steps[s] in (7, 8) for s in (1, 2, 3))
    assert (tmp_path / "gallery_attention" /
            "gallery_attention_demo.json").exists()
