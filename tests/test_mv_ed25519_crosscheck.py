"""Ed25519 cross-checked against the `cryptography` package.

`cryptography` isn't standard library, so this runs in its own CI job
(.github/workflows/test.yml), as the chemistry is cross-checked against
RDKit. Locally it skips when the package can't be imported, unless
OPEN_WORLDS_REQUIRE_CRYPTOGRAPHY is set, as it is in CI.
"""
import os
import random
import unittest

from multiverse import ed25519

REQUIRED = bool(os.environ.get("OPEN_WORLDS_REQUIRE_CRYPTOGRAPHY"))

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    AVAILABLE = True
except BaseException:   # a broken install can raise a non-Exception panic
    if REQUIRED:
        raise
    AVAILABLE = False

RAW = (serialization.Encoding.Raw, serialization.PublicFormat.Raw) \
    if AVAILABLE else None


@unittest.skipUnless(AVAILABLE, "the cryptography package isn't available")
class TestAgainstCryptography(unittest.TestCase):

    def test_same_keys_and_signatures_both_ways(self):
        rng = random.Random(2026)
        for _ in range(50):
            secret = bytes(rng.randrange(256) for _ in range(32))
            message = bytes(rng.randrange(256)
                            for _ in range(rng.randrange(300)))
            theirs = Ed25519PrivateKey.from_private_bytes(secret)
            their_public = theirs.public_key().public_bytes(*RAW)
            self.assertEqual(ed25519.public_key(secret), their_public)
            their_signature = theirs.sign(message)
            ours = ed25519.sign(secret, message)
            self.assertEqual(ours, their_signature)
            # each accepts the other's signature, and refuses a changed one
            self.assertTrue(ed25519.verify(their_public, message,
                                           their_signature))
            Ed25519PublicKey.from_public_bytes(their_public).verify(
                ours, message)
            changed = bytes([ours[0] ^ 1]) + ours[1:]
            self.assertFalse(ed25519.verify(their_public, message, changed))
            with self.assertRaises(InvalidSignature):
                Ed25519PublicKey.from_public_bytes(their_public).verify(
                    changed, message)


if __name__ == "__main__":
    unittest.main()
