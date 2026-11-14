import pytest
from gallery_revocation import (
    KeeperRotationRecord, WorldKeyRevokedRecord,
    RevocableGalleryWorld,
    verify_revocable_governed_log, verify_revocable_full,
    render_log_summary, demo, HAS_CRYPTO,
    _hash, _did_from_kp, _canonical, _now,
)
from gallery_governance import (
    GalleryPolicy, MemberAddedRecord, RequestRefusedRecord,
    PolicyChangeRecord,
    sign_add_member, sign_retire_member, sign_change_policy,
)
from gallery_world import (
    AtomicFractalMember, FractalGridMember,
)
from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
from fractal_grid_world import FractalGridWorld, GridParams
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _gallery(max_members=3):
    return RevocableGalleryWorld(
        _kp(), GalleryPolicy(
            max_members=max_members,
            allowed_kinds=("atomic_fractal", "fractal_grid")))


def _plant():
    return AtomicFractalMember(AtomicFractalWorld(
        template=WorldTemplate(
            template_id="t", branch_length=2, max_depth=2),
        pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
        keypair=_kp()))


def _grid():
    return FractalGridMember(FractalGridWorld(
        params=GridParams(rule_number=90, max_gen=3),
        initial_row=[0], keypair=_kp()), max_gen=3)


# -- Rotation --

def test_rotation_record_verifies():
    g = _gallery()
    g.add(0, _plant())
    k2 = _kp()
    rec = g.rotate_keeper(k2)
    assert isinstance(rec, KeeperRotationRecord)
    assert rec.old_keeper_id == g.world_id
    assert rec.new_keeper_id == _did_from_kp(k2)
    g.add(1, _grid())  # signed by K2
    g.grow_n(2)
    ok, reason = verify_revocable_governed_log(g)
    assert ok, reason


def test_rotation_updates_current_keeper():
    g = _gallery()
    k2 = _kp()
    g.rotate_keeper(k2)
    assert g.current_keeper_id == _did_from_kp(k2)


def test_rotation_rejects_same_keeper():
    g = _gallery()
    with pytest.raises(ValueError):
        g.rotate_keeper(g._keypair)


def test_record_signed_by_old_keeper_after_rotation_fails():
    """A record appended after rotation, but signed by K1, is
    detected by the verifier."""
    g = _gallery()
    k1 = g._keypair  # save old keeper
    k2 = _kp()
    g.rotate_keeper(k2)
    # Manually append a record signed by K1
    grid = _grid()
    cert = {"kind": grid.kind,
            "world_id": grid.world_id(),
            "seed_body": grid.seed_body(),
            "seed_sig": grid.seed_sig()}
    body = {
        "type": "member_added",
        "world_id": g.world_id,
        "slot": 0,
        "member_id": grid.world_id(),
        "member_kind": grid.kind,
        "seed_cert": cert,
        "request": None, "request_hash": None,
        "prev": g._last_hash, "ts": _now(),
    }
    from gallery_governance import MemberAddedRecord
    fake = MemberAddedRecord(
        world_id=g.world_id, slot=0,
        member_id=grid.world_id(),
        member_kind=grid.kind, seed_cert=cert,
        request=None, request_hash=None,
        prev=g._last_hash, ts=body["ts"],
        sig=k1.sign(_canonical(body)).hex(),  # K1 signs!
    )
    g._records.append(fake)
    ok, reason = verify_revocable_governed_log(g)
    assert not ok
    assert "signature invalid" in reason.lower()


# -- Revocation --

def test_revoke_world_key():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    rec = g.revoke_world_key(x_key, "test")
    assert isinstance(rec, WorldKeyRevokedRecord)
    assert g.is_key_revoked(x_key)


def test_revoke_rejects_foreign_key():
    """Keeper can only revoke keys they issued."""
    g = _gallery()
    other = _gallery()
    x_kp = _kp()
    foreign_key = other.issue_world_key(
        _did_from_kp(x_kp), "control")
    with pytest.raises(ValueError):
        g.revoke_world_key(foreign_key, "test")


def test_request_with_revoked_key_refused():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    g.revoke_world_key(x_key, "test")
    m = _plant()
    req = sign_add_member(g.world_id, 0, m, x_kp, x_key)
    r = g.request_add(req, m)
    assert isinstance(r, RequestRefusedRecord)


def test_accepted_with_revoked_key_fails_verification():
    """Manually append an accepted record that uses a revoked key.
    The verifier must catch it."""
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    g.revoke_world_key(x_key, "test")
    m = _plant()
    req = sign_add_member(g.world_id, 0, m, x_kp, x_key)
    cert = {"kind": m.kind, "world_id": m.world_id(),
            "seed_body": m.seed_body(),
            "seed_sig": m.seed_sig()}
    body = {
        "type": "member_added",
        "world_id": g.world_id,
        "slot": 0,
        "member_id": m.world_id(),
        "member_kind": m.kind,
        "seed_cert": cert,
        "request": req.body(),
        "request_hash": req.request_hash(),
        "prev": g._last_hash, "ts": _now(),
    }
    from gallery_governance import MemberAddedRecord
    fake = MemberAddedRecord(
        world_id=g.world_id, slot=0,
        member_id=m.world_id(), member_kind=m.kind,
        seed_cert=cert, request=req.body(),
        request_hash=req.request_hash(),
        prev=g._last_hash, ts=body["ts"],
        sig=g._keypair.sign(_canonical(body)).hex(),
    )
    g._records.append(fake)
    ok, reason = verify_revocable_governed_log(g)
    assert not ok
    assert "revoked" in reason.lower()


def test_pre_revocation_acceptance_still_verifies():
    """A request accepted *before* revocation stays valid."""
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    m = _plant()
    req = sign_add_member(g.world_id, 0, m, x_kp, x_key)
    g.request_add(req, m)  # accepted while key valid
    g.revoke_world_key(x_key, "later")
    g.grow_n(2)
    ok, reason = verify_revocable_governed_log(g)
    assert ok, reason


# -- Combined --

def test_rotation_and_revocation_together():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    g.add(0, _plant())
    m = _grid()
    req = sign_add_member(g.world_id, 1, m, x_kp, x_key)
    g.request_add(req, m)
    # Rotation
    k2 = _kp()
    g.rotate_keeper(k2)
    # Revoke under new keeper — but K2 didn't issue x_key
    # So we need K1 to revoke before rotation, or accept that
    # K2 can only revoke its own issued keys.
    # Here: verify the old key still works under K2
    m2 = _grid()
    req = sign_add_member(g.world_id, 2, m2, x_kp, x_key)
    r = g.request_add(req, m2)
    assert isinstance(r, MemberAddedRecord)
    g.grow_n(2)
    ok, reason = verify_revocable_governed_log(g)
    assert ok, reason


def test_full_verifies():
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    g.add(0, _plant())
    k2 = _kp()
    g.rotate_keeper(k2)
    m = _grid()
    req = sign_add_member(g.world_id, 1, m, x_kp, x_key)
    g.request_add(req, m)
    g.grow_n(2)
    ok, reason = verify_revocable_full(g)
    assert ok, reason


def test_tampered_rotation_old_keeper_fails():
    g = _gallery()
    k2 = _kp()
    rec = g.rotate_keeper(k2)
    # Tamper: change old_keeper_id
    tampered = KeeperRotationRecord(
        world_id=rec.world_id,
        old_keeper_id="did:key:" + "00" * 32,
        new_keeper_id=rec.new_keeper_id,
        prev=rec.prev, ts=rec.ts,
        sig_old=rec.sig_old, sig_new=rec.sig_new)
    g._records[-1] = tampered
    ok, reason = verify_revocable_governed_log(g)
    assert not ok
    assert "old keeper" in reason.lower()


def test_tampered_revocation_effective_at_fails():
    """If the effective_at is tampered, the verifier's check
    against record.ts will diverge."""
    g = _gallery()
    x_kp = _kp()
    x_key = g.issue_world_key(_did_from_kp(x_kp), "control")
    rec = g.revoke_world_key(x_key, "test")
    # Tamper effective_at to be far in the future
    tampered = WorldKeyRevokedRecord(
        world_id=rec.world_id,
        revoked_subject_id=rec.revoked_subject_id,
        key_hash=rec.key_hash, reason=rec.reason,
        effective_at="2099-01-01T00:00:00+00:00",
        prev=rec.prev, ts=rec.ts, sig=rec.sig)
    g._records[-1] = tampered
    ok, _ = verify_revocable_governed_log(g)
    # The record's sig won't verify (tampered body), so it fails
    assert not ok


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["revocable_log"] is True
    assert audit["verification"]["full"] is True
    assert audit["rotated"] is True
    assert audit["revoked_key_count"] == 1
    assert (tmp_path / "gallery_revocation" /
            "gallery_revocation_demo.json").exists()
