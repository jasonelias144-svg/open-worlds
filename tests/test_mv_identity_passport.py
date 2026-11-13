"""Identity and passport: the sketch's tests for components 1 and 2,
and the identity as a key (course step 2).

Ported from the DeepSeek sketch. Five checks there could never fail:
they caught their own failure as an error. They use assertRaises here.
Since course step 3 a passport holds signed stamps; those are tested in
test_mv_passport.py.
"""
import dataclasses
import unittest
from unittest import mock

from multiverse.identity import (Identity, Individual, canonical,
                                 create_individual, from_dict, rename,
                                 same_identity, signature_valid, to_dict)
from multiverse.passport import Passport
from multiverse.passport import from_dict as passport_from_dict
from multiverse.passport import to_dict as passport_to_dict

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
                    {"token": "01" + "00" * 31, "name": "Alice"},  # weak
                    {"token": "ec" + "ff" * 30 + "7f", "name": "Alice"},
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
        from multiverse.protocol import (PROTOCOL_VERSION, NullWorld,
                                         act_document, leave_document,
                                         petition_document)
        world = NullWorld("world:a", "A").manifest()
        other_key = NullWorld("world:a", "Copy of A").manifest().world_key
        p = self.alice.petition(world, message="hi")
        a = self.alice.act(world, "poem.turn", {"x": 1})
        l = self.alice.leave(world)
        for document, request in ((petition_document, p),
                                  (act_document, a), (leave_document, l)):
            with self.subTest(request=type(request).__name__):
                self.assertTrue(signature_valid(
                    self.alice.token,
                    document("world:a", world.world_key, request),
                    request.signature))
                # Not for another id, nor for a world that copied the id.
                self.assertFalse(signature_valid(
                    self.alice.token,
                    document("world:b", world.world_key, request),
                    request.signature))
                self.assertFalse(signature_valid(
                    self.alice.token, document("world:a", other_key, request),
                    request.signature))
        self.assertLess(p.seq, a.seq)
        self.assertLess(a.seq, l.seq)
        # Each signed document names the protocol, its kind, and its world
        # by id and key.
        for document, request, kind in ((petition_document, p, "petition"),
                                        (act_document, a, "act"),
                                        (leave_document, l, "leave")):
            d = document("world:a", world.world_key, request)
            self.assertEqual(
                (d["wcp"], d["kind"], d["world"], d["world_key"], d["seq"]),
                (PROTOCOL_VERSION, kind, "world:a", world.world_key,
                 request.seq))


class TestPassport(unittest.TestCase):
    """What a passport is as a value. Its stamps, and checking them, are
    tested in test_mv_passport.py."""

    def test_empty_passport(self):
        p = _passport()
        self.assertEqual(len(p), 0)
        self.assertEqual(p.worlds_visited(), [])
        self.assertEqual(p.entries(), ())

    def test_passport_immutability(self):
        p = _passport()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            p.identity = create_identity("Bob")

    def test_rename_via_with_identity(self):
        p = _passport("Alice")
        p2 = p.with_identity(rename(p.identity, "Alicia"))
        self.assertEqual(p2.identity.name, "Alicia")
        self.assertTrue(same_identity(p.identity, p2.identity))
        self.assertEqual(len(p2), len(p))

    def test_rename_rejects_new_token(self):
        with self.assertRaises(ValueError):
            _passport("Alice").with_identity(create_identity("Bob"))

    def test_serialization_roundtrip(self):
        p = _passport()
        p2 = passport_from_dict(passport_to_dict(p))
        self.assertTrue(same_identity(p.identity, p2.identity))
        self.assertEqual(p.identity.name, p2.identity.name)
        self.assertEqual(p2.entries(), ())


if __name__ == "__main__":
    unittest.main()
