import pytest
from gallery_governance import (
    GalleryPolicy, GalleryWorldKey, verify_world_key,
    world_key_has_tier,
    AddMemberRequest, RetireMemberRequest, ChangePolicyRequest,
    sign_add_member, sign_retire_member, sign_change_policy,
    GovernedGalleryWorld,
    GallerySeedRecord, PolicyChangeRecord, MemberAddedRecord,
    MemberRetiredRecord, GalleryCycleRecord,
    RequestRefusedRecord,
    verify_governed_log, verify_governed_members,
    verify_governed_full, render_governed, demo,
    HAS_CRYPTO, TIER_RANK, _did_from_kp, _hash,
)
from gallery_world import (
    AtomicFractalMember, FractalGridMember,
    ChaosGameMember, CoupledCAMember,
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


def _gallery(max_members=3):
    return GovernedGalleryWorld(
        _kp(), GalleryPolicy(
            max_members=max_members,
            allowed_kinds=("atomic_fractal", "fractal_grid",
                            "chaos_game", "coupled_ca")))


def _plant():
    return AtomicFractalMember(AtomicFractalWorld(
        template=WorldTemplate(
            template_id="t", branch_length=2, max_depth=2),
        pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
        keypair=_kp()))


def _grid():
    return FractalGridMember(FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=_kp()), max_gen=3)


def _chaos():
    return ChaosGameMember(ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="seeded_random",
        initial_point=(500, 500), keypair=_kp(),
        prng_seed=42), max_steps=3)


def _ca():
    return CoupledCAMember(CoupledCAWorld(
        rule_a=90, rule_b=90,
        initial_a=[0], initial_b=[10],
        k_a=50, k_b=50, keypair=_kp()), max_gen=3)


# -- Policy --

def test_policy_hash_stable():
    a = GalleryPolicy(3, ("x", "y"))
    b = GalleryPolicy(3, ("y", "x"))
    assert a.policy_hash() == b.policy_hash()


def test_policy_rejects_negative_capacity():
    with pytest.raises(ValueError):
        GalleryPolicy(-1, ("x",))


def test_policy_allows_kind():
    p = GalleryPolicy(3, ("x",))
    assert p.allows_kind("x")
    assert not p.allows_kind("y")


# -- World-key --

def test_world_key_sign_verify():
    g = _gallery()
    subject = _did_from_kp(_kp())
    wk = g.issue_world_key(subject, "control")
    assert verify_world_key(wk, g.world_id)
    assert verify_world_key(wk)  # no expected issuer


def test_world_key_wrong_issuer():
    g = _gallery()
    other = _gallery()
    wk = g.issue_world_key(_did_from_kp(_kp()), "control")
    assert not verify_world_key(wk, other.world_id)


def test_world_key_rejects_bad_tier():
    g = _gallery()
    with pytest.raises(ValueError):
        g.issue_world_key(_did_from_kp(_kp()), "god")


def test_tier_rank():
    assert TIER_RANK["terminal"] > TIER_RANK["control"]
    assert TIER_RANK["control"] > TIER_RANK["observe"]


# -- Keeper-direct --

def test_keeper_add():
    g = _gallery()
    r = g.add(0, _plant())
    assert isinstance(r, MemberAddedRecord)
    assert r.request is None


def test_keeper_add_capacity():
    g = _gallery(max_members=1)
    g.add(0, _plant())
    assert g.add(1, _grid()) is None


def test_keeper_add_kind_disallowed():
    g = GovernedGalleryWorld(
        _kp(), GalleryPolicy(
            max_members=3, allowed_kinds=("atomic_fractal",)))
    assert g.add(0, _grid()) is None  # grid not allowed


def test_keeper_retire():
    g = _gallery()
    g.add(0, _plant())
    r = g.retire(0, "done")
    assert isinstance(r, MemberRetiredRecord)


def test_keeper_change_policy():
    g = _gallery(max_members=2)
    new = GalleryPolicy(5, g.policy().allowed_kinds)
    r = g.change_policy(new)
    assert isinstance(r, PolicyChangeRecord)
    assert g.policy().max_members == 5


# -- Request path --

def test_request_add_accepted():
    g = _gallery()
    x_kp = _kp()
    x_id = _did_from_kp(x_kp)
    x_key = g.issue_world_key(x_id, "control")
    member = _plant()
    req = sign_add_member(g.world_id, 0, member, x_kp, x_key)
    r = g.request_add(req, member)
    assert isinstance(r, MemberAddedRecord)
    assert r.request_hash is not None


def test_request_add_insufficient_tier():
    g = _gallery()
    y_kp = _kp()
    y_id = _did_from_kp(y_kp)
    y_key = g.issue_world_key(y_id, "observe")
    member = _plant()
    req = sign_add_member(g.world_id, 0, member, y_kp, y_key)
    r = g.request_add(req, member)
    assert isinstance(r, RequestRefusedRecord)
    assert "tier" in r.reason.lower()


def test_request_add_capacity_exceeded():
    g = _gallery(max_members=1)
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    g.add(0, _plant())
    member = _grid()
    req = sign_add_member(g.world_id, 1, member, x_kp, x_key)
    r = g.request_add(req, member)
    assert isinstance(r, RequestRefusedRecord)
    assert "capacity" in r.reason.lower()


def test_request_add_wrong_member():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    real_member = _plant()
    different_member = _plant()
    req = sign_add_member(g.world_id, 0, real_member,
                            x_kp, x_key)
    r = g.request_add(req, different_member)
    assert isinstance(r, RequestRefusedRecord)


def test_request_retire():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    member = _plant()
    g.add(0, member)
    req = sign_retire_member(
        g.world_id, 0, member.world_id(), "done",
        x_kp, x_key)
    r = g.request_retire(req)
    assert isinstance(r, MemberRetiredRecord)


def test_request_change_policy_terminal_only():
    g = _gallery(max_members=2)
    # control tier — should fail
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    new = GalleryPolicy(5, g.policy().allowed_kinds).to_dict()
    req = sign_change_policy(g.world_id, new, x_kp, x_key)
    r = g.request_change_policy(req)
    assert isinstance(r, RequestRefusedRecord)
    assert "tier" in r.reason.lower()
    # terminal tier — should succeed
    z_kp = _kp()
    z_key = g.issue_world_key(_did_from_kp(z_kp), "terminal")
    req = sign_change_policy(g.world_id, new, z_kp, z_key)
    r = g.request_change_policy(req)
    assert isinstance(r, PolicyChangeRecord)


def test_expired_world_key():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(
        _did_from_kp(x_kp), "control",
        valid_until="2000-01-01T00:00:00+00:00")
    member = _plant()
    req = sign_add_member(g.world_id, 0, member, x_kp, x_key)
    r = g.request_add(req, member)
    assert isinstance(r, RequestRefusedRecord)
    assert "expired" in r.reason.lower()


def test_foreign_world_key():
    g = _gallery()
    other = _gallery()
    x_kp = _kp()
    x_key = other.issue_world_key(
        _did_from_kp(x_kp), "terminal")
    member = _plant()
    req = sign_add_member(g.world_id, 0, member, x_kp, x_key)
    r = g.request_add(req, member)
    assert isinstance(r, RequestRefusedRecord)


# -- Verification --

def test_full_verifies_with_requests():
    g = _gallery(max_members=3)
    g.add(0, _plant())
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    member = _grid()
    req = sign_add_member(g.world_id, 1, member, x_kp, x_key)
    g.request_add(req, member)
    g.grow_n(3)
    ok, reason = verify_governed_full(g)
    assert ok, reason


def test_full_verifies_with_refusals():
    g = _gallery()
    y_kp = _kp()
    y_key = g.issue_world_key(_did_from_kp(y_kp), "observe")
    member = _plant()
    req = sign_add_member(g.world_id, 0, member, y_kp, y_key)
    g.request_add(req, member)  # refused
    g.grow_n(2)
    ok, reason = verify_governed_full(g)
    assert ok, reason


def test_full_verifies_policy_change():
    g = _gallery(max_members=2)
    g.add(0, _plant())
    z_kp = _kp()
    z_key = g.issue_world_key(_did_from_kp(z_kp), "terminal")
    new = GalleryPolicy(5, g.policy().allowed_kinds).to_dict()
    req = sign_change_policy(g.world_id, new, z_kp, z_key)
    g.request_change_policy(req)
    g.add(1, _grid())  # now allowed
    g.grow_n(2)
    ok, reason = verify_governed_full(g)
    assert ok, reason


def test_tampered_policy_hash_rejected():
    g = _gallery(max_members=2)
    z_kp = _kp()
    z_key = g.issue_world_key(_did_from_kp(z_kp), "terminal")
    new = GalleryPolicy(5, g.policy().allowed_kinds).to_dict()
    req = sign_change_policy(g.world_id, new, z_kp, z_key)
    g.request_change_policy(req)
    # Tamper: change old_policy_hash
    for i, r in enumerate(g.records()):
        if isinstance(r, PolicyChangeRecord):
            g._records[i] = PolicyChangeRecord(
                world_id=r.world_id,
                old_policy_hash="00" * 32,
                new_policy=r.new_policy,
                new_policy_hash=r.new_policy_hash,
                request=r.request, request_hash=r.request_hash,
                prev=r.prev, ts=r.ts, sig=r.sig)
            break
    ok, _ = verify_governed_log(g)
    assert not ok


def test_tampered_request_sig_rejected():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    member = _plant()
    req = sign_add_member(g.world_id, 0, member, x_kp, x_key)
    g.request_add(req, member)
    # Tamper: change request's sig in the record
    for i, r in enumerate(g.records()):
        if isinstance(r, MemberAddedRecord) \
                and r.request is not None:
            new_req = dict(r.request)
            new_req["sig"] = "00" * 64
            g._records[i] = MemberAddedRecord(
                world_id=r.world_id, slot=r.slot,
                member_id=r.member_id,
                member_kind=r.member_kind,
                seed_cert=r.seed_cert,
                request=new_req,
                request_hash=r.request_hash,
                prev=r.prev, ts=r.ts, sig=r.sig)
            break
    ok, _ = verify_governed_log(g)
    assert not ok


def test_duplicate_request_hash_rejected():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    member = _plant()
    req = sign_add_member(g.world_id, 0, member, x_kp, x_key)
    g.request_add(req, member)
    # Manually append a duplicate record reusing the request hash
    for i, r in enumerate(g.records()):
        if isinstance(r, MemberAddedRecord):
            fake = MemberAddedRecord(
                world_id=r.world_id, slot=1,
                member_id=_plant().world_id(),
                member_kind="atomic_fractal",
                seed_cert=_plant().seed_body(),  # placeholder
                request=r.request,
                request_hash=r.request_hash,
                prev=g._last_hash,
                ts=r.ts,
                sig=g._keypair.sign(
                    _canonical({
                        "type": "member_added",
                        "world_id": r.world_id, "slot": 1,
                        "member_id": "x", "member_kind":
                        "atomic_fractal", "seed_cert": {},
                        "request": r.request,
                        "request_hash": r.request_hash,
                        "prev": g._last_hash, "ts": r.ts,
                    })).hex())
            g._records.append(fake)
            break
    ok, reason = verify_governed_log(g)
    assert not ok
    assert "reused" in reason.lower()


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["log"] is True
    assert audit["verification"]["members"] is True
    assert audit["verification"]["full"] is True
    assert audit["refusal_count"] >= 2  # at least tier + capacity
    assert audit["policy_final"]["max_members"] == 5
    assert (tmp_path / "gallery_governance" /
            "gallery_governance_demo.json").exists()
