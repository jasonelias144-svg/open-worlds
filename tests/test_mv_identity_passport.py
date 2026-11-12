"""Identity and passport: the sketch's tests for components 1 and 2.

Ported from the DeepSeek sketch. Five checks there could never fail:
they caught their own failure as an error. They use assertRaises here.
One check required world ids of at least 8 characters while six others
used "world:A"; the rule is gone (multiverse/passport.py).
"""
import dataclasses
import unittest

from multiverse.identity import (Identity, create_identity, from_dict,
                                 rename, same_identity, to_dict)
from multiverse.passport import Admission, Passport, make_admission
from multiverse.passport import from_dict as passport_from_dict
from multiverse.passport import to_dict as passport_to_dict

T1 = "2024-01-01T00:00:00+00:00"
T2 = "2024-02-01T00:00:00+00:00"
T3 = "2024-03-01T00:00:00+00:00"


def _passport(name: str = "Alice") -> Passport:
    return Passport(identity=create_identity(name))


class TestIdentity(unittest.TestCase):

    def test_identity_is_a_token_and_a_name(self):
        i = create_identity("Alice")
        self.assertEqual(i.name, "Alice")
        self.assertEqual(len(i.token), 32)  # uuid4 hex

    def test_same_name_is_not_same_identity(self):
        a, b = create_identity("Alice"), create_identity("Alice")
        self.assertFalse(same_identity(a, b))
        self.assertNotEqual(a.token, b.token)

    def test_same_token_is_same_identity(self):
        a = create_identity("Alice")
        self.assertTrue(same_identity(a, Identity(a.token, "Alicia")))

    def test_rename_preserves_identity(self):
        a = create_identity("Alice")
        b = rename(a, "Bob")
        self.assertEqual(a.token, b.token)
        self.assertNotEqual(a.name, b.name)
        self.assertTrue(same_identity(a, b))

    def test_identity_is_immutable(self):
        a = create_identity("Alice")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.token = "x" * 32
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.name = "Bob"

    def test_serialization_roundtrip(self):
        a = create_identity("Alice")
        b = from_dict(to_dict(a))
        self.assertTrue(same_identity(a, b))
        self.assertEqual(a.name, b.name)

    def test_validation(self):
        for bad in [{"token": "", "name": "Alice"},
                    {"token": "abc", "name": "Alice"},  # too short
                    {"token": "x" * 32, "name": ""},
                    {"token": 12345678901234567, "name": "Alice"}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Identity(**bad)

    def test_token_uniqueness_over_many_creates(self):
        tokens = {create_identity("x").token for _ in range(1000)}
        self.assertEqual(len(tokens), 1000)


class TestPassport(unittest.TestCase):

    def test_empty_passport(self):
        p = _passport()
        self.assertEqual(len(p), 0)
        self.assertIsNone(p.last_admission())
        self.assertEqual(p.worlds_visited(), [])

    def test_single_admission(self):
        p = _passport()
        a = make_admission("world:poetry-2024", "2024-03-15T12:00:00+00:00")
        p2 = p.with_admission(a)
        self.assertEqual(len(p), 0)  # p is unchanged
        self.assertEqual(len(p2), 1)
        self.assertEqual(p2.last_admission(), a)

    def test_multiple_admissions_preserve_order(self):
        p = _passport()
        for world, t in (("world:A", T1), ("world:B", T2), ("world:A", T3)):
            p = p.with_admission(make_admission(world, t))
        self.assertEqual(p.worlds_visited(),
                         ["world:A", "world:B", "world:A"])

    def test_admission_immutability(self):
        a = make_admission("world:A", T1)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.world_id = "world:B"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.timestamp = T2

    def test_passport_immutability(self):
        p = _passport()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            p.identity = create_identity("Bob")

    def test_rename_via_with_identity(self):
        p = _passport("Alice").with_admission(make_admission("world:A", T1))
        p2 = p.with_identity(rename(p.identity, "Alicia"))
        self.assertEqual(p2.identity.name, "Alicia")
        self.assertTrue(same_identity(p.identity, p2.identity))
        self.assertEqual(len(p2), len(p))

    def test_rename_rejects_new_token(self):
        with self.assertRaises(ValueError):
            _passport("Alice").with_identity(create_identity("Bob"))

    def test_serialization_roundtrip(self):
        p = (_passport().with_admission(make_admission("world:A", T1))
             .with_admission(make_admission("world:B", T2)))
        p2 = passport_from_dict(passport_to_dict(p))
        self.assertTrue(same_identity(p.identity, p2.identity))
        self.assertEqual(p.identity.name, p2.identity.name)
        self.assertEqual(p.admissions, p2.admissions)

    def test_admission_validation(self):
        for bad in [{"world_id": "", "timestamp": T1},
                    {"world_id": "world:A", "timestamp": ""},
                    {"world_id": "world:A", "timestamp": "not-a-date"},
                    {"world_id": None, "timestamp": T1}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Admission(**bad)

    def test_short_world_ids_are_allowed(self):
        # The protocol puts no length rule on a world's id, so neither
        # does the passport (the sketch's world "world:A" crashed here).
        self.assertEqual(Admission("w", T1).world_id, "w")

    def test_honest_limitation_unsigned_admissions(self):
        # Admissions are not signed yet (course step 3). A forged
        # admission looks exactly like a real one.
        real = _passport("Alice").with_admission(make_admission("world:A", T1))
        forged = _passport("Bob").with_admission(make_admission("world:A", T1))
        self.assertEqual(real.admissions, forged.admissions)

    def test_identity_is_preserved_across_admissions(self):
        p = _passport("Alice")
        token = p.identity.token
        for i in range(10):
            p = p.with_admission(make_admission(
                f"world:{i}", f"2024-01-{i + 1:02d}T00:00:00+00:00"))
        self.assertEqual(p.identity.token, token)
        self.assertEqual(p.identity.name, "Alice")
        self.assertEqual(len(p), 10)


if __name__ == "__main__":
    unittest.main()
