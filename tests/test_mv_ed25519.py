"""Ed25519 (multiverse/ed25519.py) against the standard's own test values,
and the properties a signature scheme must have.

The test values are RFC 8032 section 7.1, parsed from the RFC's text into
tests/fixtures/rfc8032_ed25519.json. A cross-check against the
`cryptography` package runs in CI (tests/test_mv_ed25519_crosscheck.py).
"""
import json
import os
import random
import unittest

from multiverse import ed25519

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                       "rfc8032_ed25519.json")


def _vectors():
    with open(FIXTURE) as f:
        return json.load(f)["vectors"]


class TestRFC8032(unittest.TestCase):

    def test_there_are_five_vectors(self):
        self.assertEqual([v["name"] for v in _vectors()],
                         ["1", "2", "3", "1024", "SHA(abc)"])

    def test_vectors(self):
        for v in _vectors():
            secret, public, message, signature = (
                bytes.fromhex(v[k])
                for k in ("secret", "public", "message", "signature"))
            with self.subTest(vector=v["name"]):
                self.assertEqual(ed25519.public_key(secret), public)
                self.assertEqual(ed25519.sign(secret, message), signature)
                self.assertTrue(ed25519.verify(public, message, signature))


class TestProperties(unittest.TestCase):

    def setUp(self):
        rng = random.Random(8032)
        self.secret = bytes(rng.randrange(256) for _ in range(32))
        self.public = ed25519.public_key(self.secret)
        self.message = b"Hope is the thing with feathers"
        self.signature = ed25519.sign(self.secret, self.message)

    def test_deterministic(self):
        self.assertEqual(ed25519.sign(self.secret, self.message),
                         self.signature)

    def test_any_change_is_caught(self):
        sig = bytearray(self.signature)
        for i in range(0, 64, 7):
            changed = bytearray(sig)
            changed[i] ^= 1
            with self.subTest(byte=i):
                self.assertFalse(ed25519.verify(self.public, self.message,
                                                bytes(changed)))
        self.assertFalse(ed25519.verify(self.public, self.message + b".",
                                        self.signature))
        other = ed25519.public_key(bytes(32))
        self.assertFalse(ed25519.verify(other, self.message,
                                        self.signature))

    def test_non_canonical_s_is_refused(self):
        # s and s + L verify the same equation; the standard requires
        # refusing the second, or signatures could be altered.
        s = int.from_bytes(self.signature[32:], "little")
        bent = self.signature[:32] + (s + ed25519.L).to_bytes(32, "little")
        self.assertFalse(ed25519.verify(self.public, self.message, bent))

    def test_malformed_input_is_false_not_an_error(self):
        for public, message, signature in (
                (self.public[:31], self.message, self.signature),
                (self.public, self.message, self.signature[:63]),
                (b"\xff" * 32, self.message, self.signature),
                (self.public, "text", self.signature),
                (None, self.message, self.signature),
                (self.public, self.message, bytearray(self.signature))):
            with self.subTest(public=public, signature=signature):
                self.assertFalse(ed25519.verify(public, message, signature))

    def test_secret_must_be_32_bytes(self):
        for secret in (b"", bytes(31), bytes(33), "x" * 32):
            with self.subTest(secret=secret), self.assertRaises(ValueError):
                ed25519.public_key(secret)

    def test_round_trip_on_random_keys(self):
        rng = random.Random(25519)
        for _ in range(10):
            secret = bytes(rng.randrange(256) for _ in range(32))
            message = bytes(rng.randrange(256)
                            for _ in range(rng.randrange(200)))
            public = ed25519.public_key(secret)
            self.assertTrue(ed25519.verify(
                public, message, ed25519.sign(secret, message)))


if __name__ == "__main__":
    unittest.main()
