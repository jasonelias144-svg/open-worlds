"""
multiverse_c15_demo.py — Wire two signed worlds into a passport.

Shows the full happy path:
  1. Client creates identity + empty PassportV2
  2. Client petitions signed World A, receives SignedAdmission
  3. Client adds admission to passport, registers World A's key
  4. Client petitions signed World B (with passport shown to B)
  5. Client receives SignedAdmission from B
  6. Client verifies the whole passport offline
"""

from multiverse_c1 import create_identity
from multiverse_c3 import Petition
from multiverse_c13 import SignedWorld, SignedAdmission
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import (
    PassportV2, PassportEntry, InMemoryKeyResolver,
    add_signed_admission,
)


def run_demo() -> PassportV2:
    """Run the demo and return the verified passport."""
    # Two signed worlds with distinct keypairs
    world_a = SignedWorld(PermissiveWorld("world:a", "World A"))
    world_b = SignedWorld(PermissiveWorld("world:b", "World B"))

    # Client
    alice = create_identity("Alice")
    passport = PassportV2.new(alice)
    resolver = InMemoryKeyResolver()

    # Petition World A
    resp_a = world_a.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=(),
        message="Let me in.",
    ))
    assert isinstance(resp_a, SignedAdmission)
    passport = add_signed_admission(passport, resp_a)
    resolver.register(resp_a.entity_id,
                      world_a.keypair.public_key_hex())

    # Petition World B, carrying the passport-as-plain-entries
    resp_b = world_b.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=passport.to_plain_entries(),
        message="I have been to A.",
    ))
    assert isinstance(resp_b, SignedAdmission)
    passport = add_signed_admission(passport, resp_b)
    resolver.register(resp_b.entity_id,
                      world_b.keypair.public_key_hex())

    # Verify the whole passport offline
    report = passport.verify(resolver)
    print(report.format())
    return passport
