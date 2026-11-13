# multiverse_c2_test.py
from datetime import datetime, timezone
import pytest
from multiverse_c1 import create_identity, rename, same_identity
from multiverse_c2 import (
    Admission, Passport, make_admission,
    to_dict, from_dict,
)


def _passport(name: str = "Alice") -> Passport:
    return Passport(identity=create_identity(name))


def test_empty_passport():
    print("=== Empty passport ===")
    p = _passport()
    print(f"  {p.identity}")
    print(f"  admissions: {len(p)}")
    assert len(p) == 0
    assert p.last_admission() is None
    assert p.worlds_visited() == []


def test_single_admission():
    print("=== One admission ===")
    p = _passport()
    a = make_admission("world:poetry-2024", "2024-03-15T12:00:00+00:00")
    p2 = p.with_admission(a)
    print(f"  before: {len(p)} admissions")
    print(f"  after:  {len(p2)} admissions")
    print(f"  admissions: {p2.admissions}")
    # p is unchanged; p2 is a new passport
    assert len(p) == 0
    assert len(p2) == 1
    assert p2.last_admission() == a


def test_multiple_admissions_preserve_order():
    print("=== Multiple admissions preserve order ===")
    p = _passport()
    a = make_admission("world:A", "2024-01-01T00:00:00+00:00")
    b = make_admission("world:B", "2024-02-01T00:00:00+00:00")
    c = make_admission("world:A", "2024-03-01T00:00:00+00:00")
    p = p.with_admission(a).with_admission(b).with_admission(c)
    print(f"  worlds_visited: {p.worlds_visited()}")
    assert p.worlds_visited() == ["world:A", "world:B", "world:A"]


def test_admission_immutability():
    print("=== Admissions are immutable ===")
    a = make_admission("world:A", "2024-01-01T00:00:00+00:00")
    try:
        a.world_id = "world:B"
        assert False, "should not allow world_id mutation"
    except Exception as e:
        print(f"  ✓ world_id mutation rejected: {type(e).__name__}")
    try:
        a.timestamp = "2025-01-01T00:00:00+00:00"
        assert False, "should not allow timestamp mutation"
    except Exception as e:
        print(f"  ✓ timestamp mutation rejected: {type(e).__name__}")


def test_passport_immutability():
    print("=== Passport is immutable ===")
    p = _passport()
    try:
        p.identity = create_identity("Bob")
        assert False, "should not allow identity replacement"
    except Exception as e:
        print(f"  ✓ identity mutation rejected: {type(e).__name__}")


def test_rename_via_with_identity():
    print("=== Rename via with_identity ===")
    p = _passport("Alice")
    p = p.with_admission(
        make_admission("world:A", "2024-01-01T00:00:00+00:00"))
    new_identity = rename(p.identity, "Alicia")
    p2 = p.with_identity(new_identity)
    print(f"  old name: {p.identity.name}")
    print(f"  new name: {p2.identity.name}")
    print(f"  same token: {same_identity(p.identity, p2.identity)}")
    print(f"  admissions preserved: {len(p2)}")
    assert p2.identity.name == "Alicia"
    assert same_identity(p.identity, p2.identity)
    assert len(p2) == len(p)


def test_rename_rejects_new_token():
    print("=== with_identity rejects a different token ===")
    p = _passport("Alice")
    other = create_identity("Bob")  # different token
    try:
        p.with_identity(other)
        assert False, "should reject a different token"
    except ValueError as e:
        print(f"  ✓ rejected: {e}")


def test_serialization_roundtrip():
    print("=== Serialization roundtrip ===")
    p = _passport()
    p = p.with_admission(
        make_admission("world:A", "2024-01-01T00:00:00+00:00")
    ).with_admission(
        make_admission("world:B", "2024-02-01T00:00:00+00:00")
    )
    d = to_dict(p)
    p2 = from_dict(d)
    print(f"  original:    {len(p)} admissions")
    print(f"  roundtripped: {len(p2)} admissions")
    print(f"  same token:  {same_identity(p.identity, p2.identity)}")
    assert same_identity(p.identity, p2.identity)
    assert p.identity.name == p2.identity.name
    assert len(p) == len(p2)
    assert p.worlds_visited() == p2.worlds_visited()
    for a, b in zip(p.admissions, p2.admissions):
        assert a.world_id == b.world_id
        assert a.timestamp == b.timestamp


def test_admission_validation():
    print("=== Admission validation ===")
    # Empty world_id
    for bad in [
        {"world_id": "", "timestamp": "2024-01-01T00:00:00+00:00"},
        {"world_id": "abc", "timestamp": "2024-01-01T00:00:00+00:00"},
        {"world_id": "world:A", "timestamp": ""},
        {"world_id": "world:A", "timestamp": "not-a-date"},
    ]:
        try:
            Admission(**bad)
            assert False, f"should have rejected: {bad}"
        except ValueError:
            pass
    print("  ✓ empty/short world_id and bad timestamps rejected")


def test_honest_limitation():
    """This test explicitly demonstrates the limitation of Component 2.

    In this component, admissions are unsigned. Any holder of a
    passport could forge an admission by claiming a world admitted
    them. The recipient CANNOT tell a real admission from a forged
    one — because there is no signature, no reference, no query
    protocol.

    This is the *honest* limitation of Component 2. It is the
    component's job to be structurally correct; cryptographic
    verification is Component 3's job.
    """
    print("=== Honest limitation: forged admissions are structurally "
          "indistinguishable from real ones ===")
    real = _passport("Alice")
    real = real.with_admission(
        make_admission("world:A", "2024-01-01T00:00:00+00:00"))

    forged = _passport("Bob")
    forged = forged.with_admission(
        make_admission("world:A", "2024-01-01T00:00:00+00:00"))
    # ^ Bob forges an admission to world:A

    # Structurally, both are valid passports with one admission to
    # world:A. A recipient of the passport cannot tell which is real.
    print(f"  real:   {len(real)} admission to {real.worlds_visited()}")
    print(f"  forged: {len(forged)} admission to {forged.worlds_visited()}")
    print("  ✓ Both structurally valid")
    print("  → Recipient must trust the presenter, or wait for Component 3")
    assert len(real) == len(forged) == 1
    assert real.worlds_visited() == forged.worlds_visited()


def test_identity_is_preserved_across_admissions():
    print("=== Identity is preserved across admissions ===")
    p = _passport("Alice")
    original_token = p.identity.token
    for i in range(10):
        p = p.with_admission(
            make_admission(f"world:{i}",
                            f"2024-01-{i+1:02d}T00:00:00+00:00"))
    print(f"  after 10 admissions:")
    print(f"    token: {p.identity.token[:8]}... (unchanged)")
    print(f"    name:  {p.identity.name}")
    print(f"    count: {len(p)}")
    assert p.identity.token == original_token
    assert p.identity.name == "Alice"
    assert len(p) == 10


if __name__ == "__main__":
    test_empty_passport()
    test_single_admission()
    test_multiple_admissions_preserve_order()
    test_admission_immutability()
    test_passport_immutability()
    test_rename_via_with_identity()
    test_rename_rejects_new_token()
    test_serialization_roundtrip()
    test_admission_validation()
    test_honest_limitation()
    test_identity_is_preserved_across_admissions()
