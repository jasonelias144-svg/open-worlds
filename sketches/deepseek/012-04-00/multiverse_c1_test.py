# multiverse_c1_test.py
import pytest
from multiverse_c1 import (
    Identity, create_identity, same_identity, rename,
    to_dict, from_dict,
)


def test_identity_is_a_token_and_a_name():
    print("=== Identity: token + name ===")
    i = create_identity("Alice")
    print(f"  {i}")
    assert i.name == "Alice"
    assert len(i.token) == 32  # uuid4 hex


def test_distinct_tokens_are_distinct_identities():
    print("=== Distinct tokens → distinct identities ===")
    a = create_identity("Alice")
    b = create_identity("Alice")  # same name, different token
    print(f"  a = {a}")
    print(f"  b = {b}")
    print(f"  same_identity(a, b) = {same_identity(a, b)}")
    assert not same_identity(a, b)
    # Same name does not mean same individual
    assert a.name == b.name
    assert a.token != b.token


def test_same_token_is_same_identity():
    print("=== Same token → same identity (regardless of name) ===")
    a = create_identity("Alice")
    a_renamed = Identity(token=a.token, name="Alicia")
    print(f"  a       = {a}")
    print(f"  renamed = {a_renamed}")
    print(f"  same_identity(a, a_renamed) = {same_identity(a, a_renamed)}")
    assert same_identity(a, a_renamed)


def test_rename_preserves_identity():
    print("=== Rename preserves token ===")
    a = create_identity("Alice")
    b = rename(a, "Bob")
    print(f"  a = {a}")
    print(f"  b = {b}")
    assert a.token == b.token
    assert a.name != b.name
    assert same_identity(a, b)


def test_identity_is_immutable():
    print("=== Identity is frozen ===")
    a = create_identity("Alice")
    try:
        a.token = "x" * 32
        assert False, "should not allow token mutation"
    except Exception as e:
        print(f"  ✓ mutation rejected: {type(e).__name__}")
    try:
        a.name = "Bob"
        assert False, "should not allow name mutation"
    except Exception as e:
        print(f"  ✓ mutation rejected: {type(e).__name__}")


def test_self_sovereign():
    print("=== Identity is self-issued ===")
    # No registry, no authority, no world
    a = create_identity("Alice")
    b = create_identity("Bob")
    print(f"  Created without any world or registry:")
    print(f"    {a}")
    print(f"    {b}")
    # There is no place to look up "is this a valid token" —
    # token validity is not a property the system can check.
    # The only property the system can check is "have I seen it before."
    assert a.token != b.token


def test_serialization_roundtrip():
    print("=== Serialization roundtrip ===")
    a = create_identity("Alice")
    d = to_dict(a)
    b = from_dict(d)
    print(f"  a = {a}")
    print(f"  d = {d}")
    print(f"  b = {b}")
    assert same_identity(a, b)
    assert a.name == b.name


def test_validation():
    print("=== Validation ===")
    for bad in [
        {"token": "", "name": "Alice"},
        {"token": "abc", "name": "Alice"},  # too short
        {"token": "x" * 32, "name": ""},
    ]:
        try:
            Identity(**bad)
            assert False, f"should have rejected: {bad}"
        except ValueError:
            pass
    print("  ✓ empty or short fields rejected")


def test_token_uniqueness_over_many_creates():
    print("=== Token uniqueness across many creates ===")
    tokens = {create_identity("x").token for _ in range(1000)}
    print(f"  Created 1000 identities, {len(tokens)} distinct tokens")
    assert len(tokens) == 1000


if __name__ == "__main__":
    test_identity_is_a_token_and_a_name()
    test_distinct_tokens_are_distinct_identities()
    test_same_token_is_same_identity()
    test_rename_preserves_identity()
    test_identity_is_immutable()
    test_self_sovereign()
    test_serialization_roundtrip()
    test_validation()
    test_token_uniqueness_over_many_creates()
