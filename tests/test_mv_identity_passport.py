"""Identity and passport: the sketch's tests for components 1 and 2,
and the identity as a key (course step 2).

Ported from the DeepSeek sketch. Five checks there could never fail:
they caught their own failure as an error. They use assertRaises here.
One check required world ids of at least 8 characters while six others
used "world:A"; the rule is gone (multiverse/passport.py).
"""
import dataclasses
import unittest
from unittest import mock

from multiverse.identity import (Identity, Individual, canonical,
                                 create_individual, from_dict, rename,
                                 same_identity, signature_valid, to_dict)
from multiverse.passport import Admission, Passport, make_admission
from multiverse.passport import from_dict as passport_from_dict
from multiverse.passport import to_dict as passport_to_dict

T1 = "2024-01-01T00:00:00+00:00"
T2 = "2024-02-01T00:00:00+00:00"
T3 = "2024-03-01T00:00:00+00:00"


def create_identity(name: str) -> Identity:
    return create_individual(name).identity


def _passport(name: str = "Alice") -> Passport:
    return Passport(identity=create_identity(name))


class TestIdentity(unittest.TestCase):

    def test_identity_is_a_token_and_a_name(self):
        i = create_identity("Alice")
        self.assertEqual(i.name, "Alice")
        self.assertEqual(len(i.token), 64)  # an Ed25519 public key, in hex

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
            a.token = "ab" * 32
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.name = "Bob"

    def test_serialization_roundtrip(self):
        a = create_identity("Alice")
        b = from_dict(to_dict(a))
        self.assertTrue(same_identity(a, b))
        self.assertEqual(a.name, b.name)

    def test_validation(self):
        good = create_identity("Alice").token
        for bad in [{"token": "", "name": "Alice"},
                    {"token": "abc", "name": "Alice"},  # too short
                    {"token": "x" * 64, "name": "Alice"},  # not hex
                    {"token": good.upper(), "name": "Alice"},
                    {"token": "ff" * 32, "name": "Alice"},  # not on the curve
                    {"token": good, "name": ""},
                    {"token": 12345678901234567, "name": "Alice"}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Identity(**bad)

    def test_token_uniqueness_over_many_creates(self):
        tokens = {create_identity("x").token for _ in range(200)}
        self.assertEqual(len(tokens), 200)


class TestIndividual(unittest.TestCase):
    """The private key stays with the individual; what goes out is the
    identity and signatures."""

    def setUp(self):
        self.alice = Individual("Alice")
        self.doc = {"kind": "act", "world": "world:poetry", "seq": 1,
                    "payload": {"lines": ["Hope is the thing with feathers"]}}

    def test_signature_verifies_against_the_token(self):
        signature = self.alice.sign(self.doc)
        self.assertEqual(len(signature), 128)
        self.assertTrue(signature_valid(self.alice.token, self.doc,
                                        signature))

    def test_anything_else_does_not(self):
        signature = self.alice.sign(self.doc)
        bob = Individual("Bob")
        altered = {**self.doc, "seq": 2}
        flipped = signature[:-1] + ("0" if signature[-1] != "0" else "1")
        for token, doc, sig in ((bob.token, self.doc, signature),
                                (self.alice.token, altered, signature),
                                (self.alice.token, self.doc, flipped),
                                (self.alice.token, self.doc, ""),
                                (self.alice.token, self.doc, None),
                                (self.alice.token, self.doc, "zz" * 64),
                                ("not a key", self.doc, signature)):
            with self.subTest(token=token[:8] if isinstance(token, str)
                              else token, sig=str(sig)[:8]):
                self.assertFalse(signature_valid(token, doc, sig))

    def test_canonical_is_exact(self):
        self.assertEqual(canonical({"b": 1, "a": [True, None, "é"]}),
                         '{"a":[true,null,"é"],"b":1}'.encode("utf-8"))
        with self.assertRaises(ValueError):
            canonical({"x": float("nan")})
        self.assertFalse(signature_valid(self.alice.token,
                                         {"x": float("inf")},
                                         self.alice.sign({"x": 1})))

    def test_the_key_stays_inside(self):
        secret_hex = self.alice._secret.hex()
        for public in (repr(self.alice), str(to_dict(self.alice.identity)),
                       repr(self.alice.identity)):
            self.assertNotIn(secret_hex, public)

    def test_same_secret_same_individual(self):
        again = Individual("Alicia", secret=self.alice._secret)
        self.assertTrue(same_identity(again.identity, self.alice.identity))

    def test_seq_grows_per_world(self):
        seqs = [self.alice.next_seq("world:a") for _ in range(5)]
        self.assertEqual(seqs, sorted(set(seqs)))

    def test_seq_comes_from_the_clock(self):
        clock = "multiverse.identity.time.time_ns"
        with mock.patch(clock, return_value=5_000_000_000):
            first = [self.alice.next_seq("world:a") for _ in range(3)]
        self.assertEqual(first, [5_000_000, 5_000_001, 5_000_002])
        # The same key in a new object, as after a restart, a second later:
        # its numbers are larger, because the clock has moved on.
        again = Individual("Alice", secret=self.alice._secret)
        with mock.patch(clock, return_value=6_000_000_000):
            self.assertEqual(again.next_seq("world:a"), 6_000_000)
        # If the clock goes back, the same object still counts up.
        with mock.patch(clock, return_value=1_000):
            self.assertEqual(self.alice.next_seq("world:a"), 5_000_003)

    def test_requests_are_signed_for_their_world(self):
        from multiverse.protocol import (act_document, leave_document,
                                         petition_document)
        p = self.alice.petition("world:a", message="hi")
        a = self.alice.act("world:a", "poem.turn", {"x": 1})
        l = self.alice.leave("world:a")
        for document, request in ((petition_document, p),
                                  (act_document, a), (leave_document, l)):
            with self.subTest(request=type(request).__name__):
                self.assertTrue(signature_valid(
                    self.alice.token, document("world:a", request),
                    request.signature))
                self.assertFalse(signature_valid(
                    self.alice.token, document("world:b", request),
                    request.signature))
        self.assertLess(p.seq, a.seq)
        self.assertLess(a.seq, l.seq)


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
