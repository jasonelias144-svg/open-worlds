# multiverse_c33_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import (
    Petition, Act, Ack, Refusal,
)
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import PassportV2
from multiverse_c22 import (
    LeavePetition, Leave, SignedLeave,
    SignedLeaveWorld, PassportV2WithDepartures,
    verify_departure,
)
from multiverse_c33 import (
    LeaveCapableMixin,
    LeaveCapablePoetryWorld,
    LeaveCapableChemistryWorld,
    LeaveCapableRegistry,
    demo,
)


# =====================================================================
# Chemistry World: leave
# =====================================================================

def test_chem_leave_without_admission():
    print("=== Chemistry: leave without admission → Refusal ===")
    world = LeaveCapableChemistryWorld("world:chem", "Chem")
    alice = create_identity("Alice")
    r = world.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(r, Refusal)
    assert r.reason == "not admitted"


def test_chem_leave_after_admission():
    print("=== Chemistry: leave after admission → Leave ===")
    world = LeaveCapableChemistryWorld("world:chem", "Chem")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    r = world.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(r, Leave)
    assert r.entity_id == "world:chem"


def test_chem_act_after_leave_refused():
    print("=== Chemistry: act after leave refused ===")
    world = LeaveCapableChemistryWorld("world:chem", "Chem")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    world.leave(LeavePetition(leaver_token=alice.token))
    r = world.act(Act(
        actor_token=alice.token, type="chemistry.react",
        payload={"substrates": [], "products": []}))
    assert isinstance(r, Refusal)
    assert "not admitted" in r.reason


def test_chem_reenter_after_leave():
    print("=== Chemistry: re-petition works ===")
    world = LeaveCapableChemistryWorld("world:chem", "Chem")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    world.leave(LeavePetition(leaver_token=alice.token))
    r = world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="back"))
    assert r is not None
    assert world.is_resident(alice.token)


def test_chem_leave_logged():
    print("=== Chemistry: leave logged ===")
    world = LeaveCapableChemistryWorld("world:chem", "Chem")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    world.leave(LeavePetition(leaver_token=alice.token))
    kinds = [e.kind for e in world.log_since(None)]
    assert "leave" in kinds


@pytest.mark.skipif(not HAS_CRYPTO,
                     reason="cryptography not installed")
def test_chem_signed_leave_verifies():
    print("=== Chemistry: signed leave verifies ===")
    kp = KeyPair.generate()
    world = SignedLeaveWorld(
        LeaveCapableChemistryWorld("world:chem", "Chem"), kp)
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    leave = world.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(leave, SignedLeave)
    from multiverse_c13 import verify_signature
    assert verify_signature(kp.public_key_hex(),
                             leave.canonical_payload(),
                             leave.signature)


# =====================================================================
# Registry: leave
# =====================================================================

def test_reg_leave_without_admission():
    print("=== Registry: leave without admission → Refusal ===")
    reg = LeaveCapableRegistry("multiverse:main", "Main")
    alice = create_identity("Alice")
    r = reg.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(r, Refusal)
    assert r.reason == "not admitted"


def test_reg_leave_after_admission():
    print("=== Registry: leave after admission → Leave ===")
    reg = LeaveCapableRegistry("multiverse:main", "Main")
    alice = create_identity("Alice")
    reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    r = reg.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(r, Leave)


def test_reg_act_after_leave_refused():
    print("=== Registry: act after leave refused ===")
    reg = LeaveCapableRegistry("multiverse:main", "Main")
    alice = create_identity("Alice")
    reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    # Admit a world first
    world = PermissiveWorld("world:a", "A")
    reg.act(Act(actor_token=alice.token,
                type="multiverse.admit",
                payload={"entity": world}))
    # Leave
    reg.leave(LeavePetition(leaver_token=alice.token))
    # Act is now refused
    r = reg.act(Act(actor_token=alice.token,
                     type="multiverse.remove",
                     payload={"entity_id": "world:a"}))
    assert isinstance(r, Refusal)
    assert "not admitted" in r.reason


def test_reg_leave_preserves_listings():
    """The key semantic: leaving the registry does NOT remove the
    listings the leaver proposed. The registry keeps its record."""
    print("=== Registry: leaving preserves listings ===")
    reg = LeaveCapableRegistry("multiverse:main", "Main")
    alice = create_identity("Alice")
    reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    # Alice proposes two worlds
    reg.act(Act(actor_token=alice.token,
                type="multiverse.admit",
                payload={"entity": PermissiveWorld(
                    "world:a", "A")}))
    reg.act(Act(actor_token=alice.token,
                type="multiverse.admit",
                payload={"entity": PermissiveWorld(
                    "world:b", "B")}))
    assert set(reg.entity_ids()) == {"world:a", "world:b"}

    # Alice leaves
    reg.leave(LeavePetition(leaver_token=alice.token))

    # Listings survive
    assert set(reg.entity_ids()) == {"world:a", "world:b"}
    listed = [m.entity_id for m in reg.list_sub_entities()]
    assert set(listed) == {"world:a", "world:b"}


def test_reg_reenter_after_leave():
    print("=== Registry: re-petition works ===")
    reg = LeaveCapableRegistry("multiverse:main", "Main")
    alice = create_identity("Alice")
    reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    reg.leave(LeavePetition(leaver_token=alice.token))
    r = reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="back"))
    assert r is not None
    assert reg.is_resident(alice.token)


@pytest.mark.skipif(not HAS_CRYPTO,
                     reason="cryptography not installed")
def test_reg_signed_leave_verifies():
    print("=== Registry: signed leave verifies ===")
    kp = KeyPair.generate()
    reg = SignedLeaveWorld(
        LeaveCapableRegistry("multiverse:main", "Main"), kp)
    alice = create_identity("Alice")
    reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    leave = reg.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(leave, SignedLeave)
    from multiverse_c13 import verify_signature
    assert verify_signature(kp.public_key_hex(),
                             leave.canonical_payload(),
                             leave.signature)


# =====================================================================
# Mixin — API symmetry
# =====================================================================

def test_leave_capable_poetry_world():
    print("=== LeaveCapablePoetryWorld (mixin-based) works ===")
    world = LeaveCapablePoetryWorld("world:poetry", "Poetry")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    r = world.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(r, Leave)


def test_mixin_applies_to_all_three():
    """The mixin works on all three base worlds — the property
    that makes it a mixin rather than three copies."""
    print("=== Mixin applies to all three world types ===")
    for cls, eid in [
        (LeaveCapablePoetryWorld, "world:poetry"),
        (LeaveCapableChemistryWorld, "world:chem"),
        (LeaveCapableRegistry, "multiverse:main"),
    ]:
        world = cls(eid, eid.upper())
        assert isinstance(world, LeaveCapableMixin)
        assert hasattr(world, "leave")
        alice = create_identity(f"A-{eid}")
        world.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message="hi"))
        r = world.leave(LeavePetition(leaver_token=alice.token))
        assert isinstance(r, Leave)
        print(f"  ✓ {cls.__name__} ({eid})")


# =====================================================================
# End-to-end: all three worlds in one passport
# =====================================================================

@pytest.mark.skipif(not HAS_CRYPTO,
                     reason="cryptography not installed")
def test_three_worlds_one_passport():
    """Alice visits all three worlds and leaves all three. Her
    passport has three departures, all signed and verified."""
    print("=== Three worlds, one passport ===")
    kp_poetry = KeyPair.generate()
    kp_chem = KeyPair.generate()
    kp_reg = KeyPair.generate()
    poetry = SignedLeaveWorld(
        LeaveCapablePoetryWorld("world:poetry", "Poetry"), kp_poetry)
    chemistry = SignedLeaveWorld(
        LeaveCapableChemistryWorld("world:chem", "Chem"), kp_chem)
    reg = SignedLeaveWorld(
        LeaveCapableRegistry("multiverse:main", "Main"), kp_reg)

    alice = create_identity("Alice")
    passport = PassportV2WithDepartures(PassportV2.new(alice))

    for world in (poetry, chemistry, reg):
        adm = world.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(),
            message="hi"))
        passport = passport.with_admission(adm)

    for world in (poetry, chemistry, reg):
        leave = world.leave(LeavePetition(leaver_token=alice.token))
        passport = passport.with_departure(leave)

    assert len(passport.entries) == 3
    assert len(passport.departures) == 3

    keys = {
        "world:poetry": kp_poetry.public_key_hex(),
        "world:chem": kp_chem.public_key_hex(),
        "multiverse:main": kp_reg.public_key_hex(),
    }
    for eid, pk in keys.items():
        dep = passport.departure_for(eid)
        assert dep is not None
        assert verify_departure(dep, alice.token, pk)
        print(f"  ✓ {eid}: departure verified")


# =====================================================================
# Demo
# =====================================================================

@pytest.mark.skipif(not HAS_CRYPTO,
                     reason="cryptography not installed")
def test_demo(tmp_path):
    print("=== Demo: three worlds, one leave each, listings survive ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["passport_admissions"] == 3
    assert audit["passport_departures"] == 3
    assert all(r["signature_valid"]
               for r in audit["departures"].values())
    assert audit["listing_survives"] is True
    assert (tmp_path / "leave_demo.json").exists()


if __name__ == "__main__":
    test_chem_leave_without_admission()
    test_chem_leave_after_admission()
    test_chem_act_after_leave_refused()
    test_chem_reenter_after_leave()
    test_chem_leave_logged()
    if HAS_CRYPTO:
        test_chem_signed_leave_verifies()
    test_reg_leave_without_admission()
    test_reg_leave_after_admission()
    test_reg_act_after_leave_refused()
    test_reg_leave_preserves_listings()
    test_reg_reenter_after_leave()
    if HAS_CRYPTO:
        test_reg_signed_leave_verifies()
    test_leave_capable_poetry_world()
    test_mixin_applies_to_all_three()
    if HAS_CRYPTO:
        test_three_worlds_one_passport()
        with tempfile.TemporaryDirectory() as tmp:
            test_demo(Path(tmp))
