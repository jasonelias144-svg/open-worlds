# multiverse_c15_test.py
import pytest

from multiverse_c1 import create_identity, same_identity
from multiverse_c2 import Passport, Admission as PlainAdmission
from multiverse_c3 import Petition
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, SignedWorld, SignedAdmission,
    canonical_bytes,
)
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import (
    PassportEntry, PassportV2, EntryVerdict, VerificationReport,
    InMemoryKeyResolver, add_signed_admission,
    entry_to_dict, entry_from_dict,
    passport_v2_to_dict, passport_v2_from_dict,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO,
    reason="cryptography not installed (pip install cryptography)")


# =====================================================================
# PassportEntry construction
# =====================================================================

def test_plain_entry():
    print("=== Plain entry ===")
    e = PassportEntry(entity_id="world:a",
                      timestamp="2024-01-01T00:00:00+00:00")
    assert not e.is_signed
    assert e.to_plain() == ("world:a", "2024-01-01T00:00:00+00:00")


def test_signed_entry():
    print("=== Signed entry ===")
    e = PassportEntry(
        entity_id="world:a",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token="alice:token",
        signature="ab" * 64,
    )
    assert e.is_signed


def test_entry_rejects_partial_signature():
    print("=== Entry rejects partial signature fields ===")
    with pytest.raises(ValueError):
        PassportEntry(entity_id="w", timestamp="t",
                      subject_token="x")  # missing signature
    with pytest.raises(ValueError):
        PassportEntry(entity_id="w", timestamp="t",
                      signature="x")  # missing subject_token


def test_entry_canonical_payload_matches_world_signing():
    print("=== canonical_payload matches C13 world signature ===")
    kp = KeyPair.generate()
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:a",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": "alice:token",
    })
    sig = kp.sign(canonical).hex()
    # Now reconstruct via PassportEntry
    entry = PassportEntry(
        entity_id="world:a",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token="alice:token",
        signature=sig,
    )
    assert entry.canonical_payload() == canonical


# =====================================================================
# PassportV2 basics
# =====================================================================

def test_new_passport_is_empty():
    print("=== New passport is empty ===")
    alice = create_identity("Alice")
    p = PassportV2.new(alice)
    assert len(p) == 0
    assert p.to_plain_entries() == ()


def test_with_entry_appends():
    print("=== with_entry appends ===")
    alice = create_identity("Alice")
    p = PassportV2.new(alice)
    e = PassportEntry(entity_id="world:a", timestamp="t1")
    p2 = p.with_entry(e)
    assert len(p) == 0      # original unchanged
    assert len(p2) == 1
    assert p2.entries[0] is e


def test_to_plain_entries():
    print("=== to_plain_entries drops signatures ===")
    alice = create_identity("Alice")
    p = PassportV2.new(alice).with_entry(
        PassportEntry(entity_id="world:a", timestamp="t1",
                      subject_token="x", signature="ab" * 64)
    ).with_entry(
        PassportEntry(entity_id="world:b", timestamp="t2")
    )
    pairs = p.to_plain_entries()
    print(f"  pairs: {pairs}")
    assert pairs == (("world:a", "t1"), ("world:b", "t2"))


def test_rename_preserves_entries():
    print("=== with_identity preserves entries ===")
    alice = create_identity("Alice")
    p = PassportV2.new(alice).with_entry(
        PassportEntry(entity_id="world:a", timestamp="t1"))
    renamed = create_identity("Alice2")  # different token
    # Use rename from C1 to preserve token
    from multiverse_c1 import rename
    alicia = rename(alice, "Alicia")
    p2 = p.with_identity(alicia)
    assert same_identity(p.identity, p2.identity)
    assert len(p2) == 1


# =====================================================================
# Conversion V1 ↔ V2
# =====================================================================

def test_convert_v1_to_v2():
    print("=== Convert V1 Passport → PassportV2 ===")
    alice = create_identity("Alice")
    v1 = Passport(identity=alice, admissions=(
        PlainAdmission(world_id="world:a", timestamp="t1"),
        PlainAdmission(world_id="world:b", timestamp="t2"),
    ))
    v2 = PassportV2.from_v1(v1)
    assert len(v2) == 2
    assert all(not e.is_signed for e in v2.entries)


def test_convert_v2_to_v1():
    print("=== Convert PassportV2 → V1 Passport ===")
    alice = create_identity("Alice")
    v2 = PassportV2.new(alice).with_entry(
        PassportEntry(entity_id="world:a", timestamp="t1",
                      subject_token="x", signature="ab" * 64)
    )
    v1 = v2.to_v1()
    assert len(v1) == 1
    assert v1.admissions[0].world_id == "world:a"
    # Signature is dropped
    assert not hasattr(v1.admissions[0], "signature")


# =====================================================================
# Verification — each status
# =====================================================================

def test_verify_unsigned_entry():
    print("=== verify: unsigned → unverified ===")
    alice = create_identity("Alice")
    p = PassportV2.new(alice).with_entry(
        PassportEntry(entity_id="world:a", timestamp="t1"))
    report = p.verify(InMemoryKeyResolver())
    assert len(report.unverified()) == 1
    assert len(report.verified()) == 0
    assert len(report.invalid()) == 0


def test_verify_signed_entry_valid():
    print("=== verify: signed + valid → verified ===")
    kp = KeyPair.generate()
    alice = create_identity("Alice")
    entry = _make_signed_entry(kp, "world:a", alice.token)
    p = PassportV2.new(alice).with_entry(entry)
    resolver = InMemoryKeyResolver()
    resolver.register("world:a", kp.public_key_hex())
    report = p.verify(resolver)
    assert len(report.verified()) == 1
    assert report.verified()[0].reason == "signature valid"


def test_verify_signed_entry_wrong_key():
    print("=== verify: signed + wrong key → invalid ===")
    real_kp = KeyPair.generate()
    attacker_kp = KeyPair.generate()
    alice = create_identity("Alice")
    # Attacker signs as world:a but with attacker's key
    entry = _make_signed_entry(attacker_kp, "world:a", alice.token)
    p = PassportV2.new(alice).with_entry(entry)
    resolver = InMemoryKeyResolver()
    resolver.register("world:a", real_kp.public_key_hex())
    report = p.verify(resolver)
    assert len(report.invalid()) == 1
    assert "INVALID" in report.invalid()[0].reason


def test_verify_signed_entry_no_key():
    print("=== verify: signed + no key → unverifiable ===")
    kp = KeyPair.generate()
    alice = create_identity("Alice")
    entry = _make_signed_entry(kp, "world:unknown", alice.token)
    p = PassportV2.new(alice).with_entry(entry)
    report = p.verify(InMemoryKeyResolver())
    assert len(report.unverifiable()) == 1


def test_verify_rejects_stolen_admission():
    """The key security test: Bob's signed admission in Alice's passport."""
    print("=== verify: stolen admission → invalid ===")
    bob_kp = KeyPair.generate()
    bob = create_identity("Bob")
    alice = create_identity("Alice")
    # Bob's admission, correctly signed by a real world
    bob_entry = _make_signed_entry(bob_kp, "world:a", bob.token)
    # Attacker pastes it into Alice's passport
    alice_passport = PassportV2.new(alice).with_entry(bob_entry)
    resolver = InMemoryKeyResolver()
    resolver.register("world:a", bob_kp.public_key_hex())
    report = alice_passport.verify(resolver)
    print(f"  verdict: {report.verdicts[0].status}")
    assert len(report.invalid()) == 1
    assert "subject_token" in report.invalid()[0].reason


def test_verify_mixed_passport():
    print("=== verify: mixed passport → mixed verdicts ===")
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    alice = create_identity("Alice")
    p = (PassportV2.new(alice)
         .with_entry(PassportEntry(entity_id="world:x", timestamp="t0"))
         .with_entry(_make_signed_entry(kp_a, "world:a", alice.token))
         .with_entry(_make_signed_entry(kp_b, "world:b", alice.token)))
    resolver = InMemoryKeyResolver()
    resolver.register("world:a", kp_a.public_key_hex())
    # NOT registering world:b
    report = p.verify(resolver)
    assert len(report.unverified()) == 1   # world:x
    assert len(report.verified()) == 1     # world:a
    assert len(report.unverifiable()) == 1 # world:b


def test_all_verified_requires_signatures():
    print("=== all_verified: true only if all signed+verified ===")
    kp = KeyPair.generate()
    alice = create_identity("Alice")
    # All signed
    p1 = (PassportV2.new(alice)
          .with_entry(_make_signed_entry(kp, "w:a", alice.token))
          .with_entry(_make_signed_entry(kp, "w:b", alice.token)))
    resolver = InMemoryKeyResolver()
    resolver.register("w:a", kp.public_key_hex())
    resolver.register("w:b", kp.public_key_hex())
    r1 = p1.verify(resolver)
    assert r1.all_verified is True
    assert r1.all_valid_or_verified is True

    # One unsigned
    p2 = p1.with_entry(PassportEntry(entity_id="w:c", timestamp="t"))
    r2 = p2.verify(resolver)
    assert r2.all_verified is False
    assert r2.all_valid_or_verified is True  # no forgery

    # One forged
    attacker = KeyPair.generate()
    bad = _make_signed_entry(attacker, "w:a", alice.token)
    p3 = p1.with_entry(bad)
    r3 = p3.verify(resolver)
    assert r3.all_verified is False
    assert r3.all_valid_or_verified is False  # forgery detected


# =====================================================================
# Client helper
# =====================================================================

def test_add_signed_admission_happy():
    print("=== add_signed_admission: happy path ===")
    kp = KeyPair.generate()
    alice = create_identity("Alice")
    p = PassportV2.new(alice)
    adm = _make_signed_admission(kp, "world:a", alice.token)
    p2 = add_signed_admission(p, adm)
    assert len(p2) == 1
    assert p2.entries[0].is_signed


def test_add_signed_admission_rejects_mismatched_subject():
    print("=== add_signed_admission: rejects wrong subject ===")
    kp = KeyPair.generate()
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    p = PassportV2.new(alice)
    bob_adm = _make_signed_admission(kp, "world:a", bob.token)
    with pytest.raises(ValueError):
        add_signed_admission(p, bob_adm)


# =====================================================================
# Serialization
# =====================================================================

def test_serialization_roundtrip():
    print("=== Serialization roundtrip ===")
    kp = KeyPair.generate()
    alice = create_identity("Alice")
    p = (PassportV2.new(alice)
         .with_entry(PassportEntry(entity_id="w:x", timestamp="t0"))
         .with_entry(_make_signed_entry(kp, "w:a", alice.token)))
    d = passport_v2_to_dict(p)
    p2 = passport_v2_from_dict(d)
    assert same_identity(p.identity, p2.identity)
    assert len(p2) == 2
    assert not p2.entries[0].is_signed
    assert p2.entries[1].is_signed
    assert p2.entries[1].signature == p.entries[1].signature


# =====================================================================
# End-to-end
# =====================================================================

def test_end_to_end_two_signed_worlds():
    print("=== End-to-end: two signed worlds ===")
    world_a = SignedWorld(PermissiveWorld("world:a", "World A"))
    world_b = SignedWorld(PermissiveWorld("world:b", "World B"))
    alice = create_identity("Alice")
    passport = PassportV2.new(alice)
    resolver = InMemoryKeyResolver()

    # Admit to A
    r_a = world_a.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=(),
        message="hi A",
    ))
    passport = add_signed_admission(passport, r_a)
    resolver.register(r_a.entity_id,
                      world_a.keypair.public_key_hex())

    # Admit to B
    r_b = world_b.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=passport.to_plain_entries(),
        message="hi B",
    ))
    passport = add_signed_admission(passport, r_b)
    resolver.register(r_b.entity_id,
                      world_b.keypair.public_key_hex())

    # Verify
    report = passport.verify(resolver)
    print(report.format())
    assert report.all_verified is True


def test_end_to_end_offline_verification():
    """The passport travels alone; verification needs only the resolver."""
    print("=== Passport travels; verification is offline ===")
    world = SignedWorld(PermissiveWorld("world:far", "Far World"))
    alice = create_identity("Alice")
    passport = PassportV2.new(alice)

    # Client A petitions and captures the passport
    r = world.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=(),
        message="hi",
    ))
    passport = add_signed_admission(passport, r)

    # "Travel": serialize, move to a different process
    wire = passport_v2_to_dict(passport)
    passport_received = passport_v2_from_dict(wire)

    # Verify with a resolver that was populated from public sources
    resolver = InMemoryKeyResolver({
        "world:far": world.keypair.public_key_hex(),
    })
    report = passport_received.verify(resolver)
    assert report.all_verified is True
    print("  ✓ verified offline — no world re-query needed")


# =====================================================================
# Helpers
# =====================================================================

def _make_signed_entry(kp, entity_id, subject_token):
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": entity_id,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject_token,
    })
    return PassportEntry(
        entity_id=entity_id,
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token=subject_token,
        signature=kp.sign(canonical).hex(),
    )


def _make_signed_admission(kp, entity_id, subject_token):
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": entity_id,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject_token,
    })
    return SignedAdmission(
        entity_id=entity_id,
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token=subject_token,
        signature=kp.sign(canonical).hex(),
    )


if __name__ == "__main__":
    test_plain_entry()
    test_signed_entry()
    test_entry_rejects_partial_signature()
    test_entry_canonical_payload_matches_world_signing()
    test_new_passport_is_empty()
    test_with_entry_appends()
    test_to_plain_entries()
    test_rename_preserves_entries()
    test_convert_v1_to_v2()
    test_convert_v2_to_v1()
    test_verify_unsigned_entry()
    test_verify_signed_entry_valid()
    test_verify_signed_entry_wrong_key()
    test_verify_signed_entry_no_key()
    test_verify_rejects_stolen_admission()
    test_verify_mixed_passport()
    test_all_verified_requires_signatures()
    test_add_signed_admission_happy()
    test_add_signed_admission_rejects_mismatched_subject()
    test_serialization_roundtrip()
    test_end_to_end_two_signed_worlds()
    test_end_to_end_offline_verification()
