"""Sealing (formats/seal.py): HPKE base mode with a label, checked against
RFC 9180's example and the vectors Rust reads too
(vectors/formats/hpke-base-v1.json)."""
from __future__ import annotations

import json
import unittest

from formats import seal, seal_vectors
from formats.multikey import (KeyFormatError, sealing_from_multikey,
                              sealing_multikey, sealing_secret_from_multikey,
                              sealing_secret_multikey)

VECTORS = json.loads(seal_vectors.FILE.read_text(encoding="utf-8"))
LABEL = "open-worlds/world-key/v1"


def _secret(name: str) -> bytes:
    return sealing_secret_from_multikey(
        VECTORS["recipients"][name]["secretKeyMultibase"])


class TestSealing(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = seal.new_secret()
        self.public = seal.public_from_secret(self.secret)

    def test_round_trip(self) -> None:
        box = seal.seal(b"hello", self.public, LABEL)
        self.assertEqual(seal.open_box(box, self.secret, LABEL), b"hello")
        self.assertEqual(len(box), 32 + 5 + 16)

    def test_each_box_is_new(self) -> None:
        self.assertNotEqual(seal.seal(b"x", self.public, LABEL),
                            seal.seal(b"x", self.public, LABEL))

    def test_only_its_key_opens_it(self) -> None:
        box = seal.seal(b"hello", self.public, LABEL)
        with self.assertRaises(seal.SealError):
            seal.open_box(box, seal.new_secret(), LABEL)

    def test_a_box_opens_only_under_its_own_label(self) -> None:
        # Sealed for another purpose (a label not in use, so made directly
        # with the suite), it doesn't open as a world-key.
        from cryptography.hazmat.primitives.asymmetric import x25519
        key = x25519.X25519PublicKey.from_public_bytes(self.public)
        other = seal.SUITE.encrypt(b"hello", key,
                                   info=b"open-worlds/journal/v1")
        with self.assertRaises(seal.SealError):
            seal.open_box(other, self.secret, LABEL)

    def test_the_label_is_named_by_the_opener(self) -> None:
        box = seal.seal(b"hello", self.public, LABEL)
        for label in (None, b"open-worlds/world-key/v1", "world-key",
                      "open-worlds/world-key/v2"):
            with self.subTest(label=label):
                with self.assertRaises(seal.SealError):
                    seal.open_box(box, self.secret, label)
                with self.assertRaises(seal.SealError):
                    seal.seal(b"hello", self.public, label)

    def test_wrong_types_are_refused(self) -> None:
        with self.assertRaises(seal.SealError):
            seal.seal("hello", self.public, LABEL)
        with self.assertRaises(seal.SealError):
            seal.seal(b"hello", self.public[:31], LABEL)
        with self.assertRaises(seal.SealError):
            seal.open_box(bytearray(48), self.secret, LABEL)
        with self.assertRaises(seal.SealError):
            seal.open_box(bytes(48), self.secret[:31], LABEL)

    def test_sealing_keys_as_multikey(self) -> None:
        text = sealing_multikey(self.public)
        self.assertTrue(text.startswith("z6LS"))
        self.assertEqual(sealing_from_multikey(text), self.public)
        secret = sealing_secret_multikey(self.secret)
        self.assertTrue(secret.startswith("z3we"))
        self.assertEqual(sealing_secret_from_multikey(secret), self.secret)
        with self.assertRaises(KeyFormatError):
            sealing_from_multikey(secret)


class TestVectors(unittest.TestCase):
    def test_the_file_is_what_the_code_writes(self) -> None:
        self.assertEqual(
            seal_vectors.FILE.read_text(encoding="utf-8"),
            seal_vectors.text(seal_vectors.current()),
            "rewrite with: python3 -m formats.seal_vectors")

    def test_labels(self) -> None:
        self.assertEqual(VECTORS["labels"], sorted(seal.LABELS))

    def test_recipients(self) -> None:
        for name, who in VECTORS["recipients"].items():
            with self.subTest(name=name):
                secret = sealing_secret_from_multikey(
                    who["secretKeyMultibase"])
                public = sealing_from_multikey(who["publicKeyMultibase"])
                self.assertEqual(seal.public_from_secret(secret), public)
                seal.check_public(public)

    def test_every_box_opens(self) -> None:
        made_by = set()
        for entry in VECTORS["opens"]:
            with self.subTest(name=entry["name"]):
                message = seal.open_box(bytes.fromhex(entry["box"]),
                                        _secret(entry["to"]), entry["label"])
                self.assertEqual(message.hex(), entry["message"])
                made_by.add(entry["madeBy"])
        self.assertEqual(made_by, {"python", "rust"})

    def test_what_must_be_refused_is(self) -> None:
        for entry in VECTORS["refused"]:
            with self.subTest(name=entry["name"]):
                with self.assertRaises(seal.SealError):
                    seal.open_box(bytes.fromhex(entry["box"]),
                                  _secret(entry["to"]), entry["label"])
        first = VECTORS["opens"][0]
        box, secret = bytes.fromhex(first["box"]), _secret(first["to"])
        for label in VECTORS["refusedLabels"]:
            with self.subTest(label=label):
                with self.assertRaises(seal.SealError):
                    seal.open_box(box, secret, label)
                with self.assertRaises(seal.SealError):
                    seal.seal(b"x", seal.public_from_secret(secret), label)
        for entry in VECTORS["refusedKeys"]:
            with self.subTest(key=entry["name"]):
                key = bytes.fromhex(entry["key"])
                with self.assertRaises(seal.SealError):
                    seal.check_public(key)
                with self.assertRaises(seal.SealError):
                    seal.seal(b"x", key, LABEL)
        for entry in VECTORS["refusedSealingMultikeys"]:
            with self.subTest(multikey=entry["name"]):
                with self.assertRaises(KeyFormatError):
                    sealing_from_multikey(entry["multikey"])

    def test_kept_refusals_are_what_their_names_say(self) -> None:
        refused = {e["name"]: e for e in VECTORS["refused"]}
        short = b"a world-key, signed by the Ur-world"
        earner = _secret("the earner")
        box = bytes.fromhex(refused["sealed for another purpose"]["box"])
        self.assertEqual(seal_vectors._raw_open(
            box, earner, seal_vectors.OTHER_PURPOSE), short)
        box = bytes.fromhex(refused["sealed with no label"]["box"])
        self.assertEqual(seal_vectors._raw_open(box, earner, b""), short)
        box = bytes.fromhex(refused["sealed to someone else"]["box"])
        self.assertEqual(
            seal.open_box(box, _secret("someone else"), LABEL), short)

    def test_junk_is_not_kept_as_a_refusal(self) -> None:
        # A box that merely fails to open is not kept: it must still open
        # as its name says, or a new one is made.
        old = json.loads(json.dumps(VECTORS))
        for entry in old["refused"]:
            if entry["name"] == "sealed for another purpose":
                entry["box"] = "00" * 80
        new = seal_vectors.vectors(old)
        box = next(e["box"] for e in new["refused"]
                   if e["name"] == "sealed for another purpose")
        self.assertNotEqual(box, "00" * 80)
        self.assertEqual(
            seal_vectors._raw_open(bytes.fromhex(box), _secret("the earner"),
                                   seal_vectors.OTHER_PURPOSE),
            b"a world-key, signed by the Ur-world")

    def test_small_order_keys_really_are(self) -> None:
        # The listed points give zero with any secret, not just the probe.
        from cryptography.hazmat.primitives.asymmetric import x25519
        for name, point in seal_vectors.SMALL_ORDER.items():
            for _ in range(3):
                key = x25519.X25519PrivateKey.generate()
                with self.subTest(name=name), self.assertRaises(ValueError):
                    key.exchange(x25519.X25519PublicKey.from_public_bytes(
                        bytes.fromhex(point)))


class TestRFC9180(unittest.TestCase):
    """RFC 9180, Appendix A.2.1: this suite's own example."""

    rfc = VECTORS["rfc9180"]

    def test_the_recipient_key(self) -> None:
        self.assertEqual(
            seal.public_from_secret(bytes.fromhex(self.rfc["skRm"])).hex(),
            self.rfc["pkRm"])

    def test_the_example_opens(self) -> None:
        # The example has associated data, which cryptography's public API
        # doesn't take; its private function does. Used only here, and
        # only if it exists. Rust reproduces the example in full.
        from cryptography.hazmat.bindings._rust import openssl
        decrypt = getattr(openssl.hpke, "_decrypt_with_aad", None)
        if decrypt is None:
            self.skipTest("this cryptography has no _decrypt_with_aad")
        from cryptography.hazmat.primitives.asymmetric import x25519
        key = x25519.X25519PrivateKey.from_private_bytes(
            bytes.fromhex(self.rfc["skRm"]))
        box = bytes.fromhex(self.rfc["enc"] + self.rfc["ct"])
        self.assertEqual(
            decrypt(seal.SUITE, box, key, info=bytes.fromhex(self.rfc["info"]),
                    aad=bytes.fromhex(self.rfc["aad"])).hex(),
            self.rfc["pt"])

    def test_its_info_is_not_a_label_in_use(self) -> None:
        with self.assertRaises(seal.SealError):
            seal.open_box(bytes.fromhex(self.rfc["enc"] + self.rfc["ct"]),
                          bytes.fromhex(self.rfc["skRm"]),
                          bytes.fromhex(self.rfc["info"]).decode())


if __name__ == "__main__":
    unittest.main()
