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


# The eight small-order points, as encoded: the published list, checked
# here against the curve (test_the_eight_small_order_points).
SMALL_ORDER = [bytes.fromhex(h) for h in (
    "0100000000000000000000000000000000000000000000000000000000000000",
    "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
    "0000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000000000080",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85")]


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

    def test_the_eight_small_order_points(self):
        # The list is right: each decodes, and eight times it is neutral.
        for public in SMALL_ORDER:
            point = ed25519._decode(public)
            self.assertIsNotNone(point)
            self.assertTrue(ed25519._same(ed25519._multiply(8, point),
                                          ed25519.NEUTRAL))
        self.assertEqual(len(set(SMALL_ORDER)), 8)

    def test_small_order_keys_are_refused(self):
        for public in SMALL_ORDER:
            with self.subTest(public=public.hex()):
                self.assertIn("small-order",
                              ed25519.public_key_problem(public))
        self.assertEqual(ed25519.public_key_problem(self.public), "")
        # The forgery: for the neutral point as the key, R = rB and S = r
        # satisfy the verification equation with no secret at all.
        neutral = SMALL_ORDER[0]
        r = 12345
        r_encoded = ed25519._encode(ed25519._multiply(r, ed25519.BASE))
        forged = r_encoded + r.to_bytes(32, "little")
        k = ed25519._hash_int(r_encoded + neutral + self.message) \
            % ed25519.L
        self.assertTrue(ed25519._same(
            ed25519._multiply(r, ed25519.BASE),
            ed25519._add(ed25519._decode(r_encoded),
                         ed25519._multiply(k, ed25519._decode(neutral)))))
        self.assertFalse(ed25519.verify(neutral, self.message, forged))

    def test_x_zero_with_the_sign_bit_set_is_refused(self):
        # Only two points have x = 0, and neither may be encoded with
        # the sign bit set (RFC 8032, section 5.1.3, step 4).
        for public in (bytes.fromhex("01" + "00" * 30 + "80"),
                       bytes.fromhex("ec" + "ff" * 31)):
            with self.subTest(public=public.hex()):
                self.assertIsNone(ed25519._decode(public))
                self.assertNotEqual(ed25519.public_key_problem(public), "")

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
