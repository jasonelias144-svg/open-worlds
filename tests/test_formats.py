"""Records signed so that standard tools can check them (formats/): RFC
8785 with this project's three rules, Multikey and did:key, and
`eddsa-jcs-2022` proofs, checked step by step against the W3C
specification's own example and against this project's vectors."""
import hashlib
import json
import unittest

from formats import canonical, multikey, proof
from formats.vectors import FILE, TEST_SECRET, text
from multiverse import ed25519

VECTORS = json.loads(FILE.read_text(encoding="utf-8"))


class TestTheVectorFile(unittest.TestCase):

    def test_the_file_is_what_this_code_writes_now(self):
        self.assertEqual(FILE.read_text(encoding="utf-8"), text(),
                         "rewrite with: python3 -m formats.vectors")


class TestTheW3CExample(unittest.TestCase):
    """Appendix B.3 of the specification, each step."""

    w3c = VECTORS["w3c"]

    def test_the_document_in_rfc_8785_form_and_its_hash(self):
        form = canonical.canonical(self.w3c["document"])
        self.assertEqual(form.decode("utf-8"), self.w3c["canonicalDocument"])
        self.assertEqual(hashlib.sha256(form).hexdigest(),
                         self.w3c["documentHash"])

    def test_the_options_in_rfc_8785_form_and_their_hash(self):
        options = json.loads(self.w3c["canonicalOptions"])
        form = canonical.canonical(options)
        self.assertEqual(form.decode("utf-8"), self.w3c["canonicalOptions"])
        self.assertEqual(hashlib.sha256(form).hexdigest(),
                         self.w3c["optionsHash"])

    def test_the_keys(self):
        secret = multikey.secret_from_multikey(self.w3c["secretKeyMultibase"])
        public = ed25519.public_key(secret)
        self.assertEqual(multikey.public_multikey(public),
                         self.w3c["publicKeyMultibase"])

    def test_signing_gives_the_specifications_signature(self):
        secret = multikey.secret_from_multikey(self.w3c["secretKeyMultibase"])
        signed = proof.sign(self.w3c["document"], secret, self.w3c["created"])
        value = signed["proof"]["proofValue"]
        self.assertEqual(value, self.w3c["proofValue"])
        self.assertEqual(multikey.base58btc_decode(value[1:]).hex(),
                         self.w3c["signature"])

    def test_the_specifications_signed_credential_verifies(self):
        secret = multikey.secret_from_multikey(self.w3c["secretKeyMultibase"])
        signed = proof.sign(self.w3c["document"], secret, self.w3c["created"])
        document, public = proof.verify(signed)
        self.assertEqual(document, self.w3c["document"])
        self.assertEqual(multikey.public_multikey(public),
                         self.w3c["publicKeyMultibase"])


class TestOurVectors(unittest.TestCase):

    def test_each_record_signs_and_verifies_as_written(self):
        for case in VECTORS["signed"]:
            with self.subTest(case["name"]):
                secret = multikey.secret_from_multikey(
                    case["secretKeyMultibase"])
                self.assertEqual(
                    canonical.canonical(case["document"]).decode("utf-8"),
                    case["canonicalDocument"])
                self.assertEqual(
                    proof.sign(case["document"], secret, case["created"]),
                    case["signed"])
                document, public = proof.verify(case["signed"])
                self.assertEqual(document, case["document"])
                self.assertEqual(multikey.public_multikey(public),
                                 case["publicKeyMultibase"])

    def test_each_refused_proof_is_refused(self):
        for case in VECTORS["refused"]:
            with self.subTest(case["name"]):
                with self.assertRaises(proof.ProofError):
                    proof.verify(case["secured"])

    def test_each_value_that_breaks_a_rule_is_refused(self):
        for case in VECTORS["refusedValues"]:
            with self.subTest(case["name"]):
                value = json.loads(case["json"])
                self.assertTrue(canonical.check(value))
                with self.assertRaises(canonical.FormatError):
                    canonical.canonical(value)


class TestTheRules(unittest.TestCase):

    def test_values_that_keep_the_rules(self):
        for value in [None, True, False, 0, 2 ** 53 - 1, -(2 ** 53 - 1),
                      "", "\U0001f642", [], {}, {"a": [1, {"b": None}]}]:
            with self.subTest(value=value):
                self.assertEqual(canonical.check(value), "")

    def test_values_that_break_them(self):
        for value in [2 ** 53, -(2 ** 53), 0.5, float("nan"), (1, 2),
                      {1: "a"}, {"é": 1}, "\ud800", b"bytes", {1, 2}]:
            with self.subTest(value=value):
                self.assertTrue(canonical.check(value))

    def test_the_place_of_a_problem_is_named(self):
        self.assertEqual(canonical.check({"a": [0, {"b": 1.5}]}),
                         "$.a[1].b: a float; use an integer in a stated unit")


class TestMultikey(unittest.TestCase):

    def test_base58btc_round_trips_with_leading_zeros(self):
        for data in [b"", b"\0", b"\0\0\1", bytes(range(256)), b"\xff" * 40]:
            with self.subTest(data=data[:4]):
                self.assertEqual(
                    multikey.base58btc_decode(
                        multikey.base58btc_encode(data)), data)

    def test_characters_outside_the_alphabet_are_refused(self):
        for bad in ["0", "O", "I", "l", "+", " "]:
            with self.subTest(bad=bad):
                with self.assertRaises(multikey.KeyFormatError):
                    multikey.base58btc_decode("2" + bad)

    def test_a_key_has_one_written_form(self):
        key = multikey.public_multikey(ed25519.public_key(TEST_SECRET))
        with self.assertRaises(multikey.KeyFormatError):
            multikey.public_from_multikey("z1" + key[1:])

    def test_a_public_key_is_not_read_as_a_secret_or_the_reverse(self):
        public = multikey.public_multikey(ed25519.public_key(TEST_SECRET))
        secret = multikey.secret_multikey(TEST_SECRET)
        with self.assertRaises(multikey.KeyFormatError):
            multikey.secret_from_multikey(public)
        with self.assertRaises(multikey.KeyFormatError):
            multikey.public_from_multikey(secret)

    def test_a_key_must_be_32_bytes(self):
        with self.assertRaises(multikey.KeyFormatError):
            multikey.public_multikey(bytes(31))
        with self.assertRaises(multikey.KeyFormatError):
            multikey.public_from_multikey(
                "z" + multikey.base58btc_encode(b"\xed\x01" + bytes(33)))


class TestSigning(unittest.TestCase):

    def test_a_record_with_a_proof_is_not_signed_again(self):
        with self.assertRaises(proof.ProofError):
            proof.sign({"proof": {}}, TEST_SECRET, "2026-11-14T00:00:00Z")

    def test_created_is_a_real_time_in_one_form(self):
        for created in ["2026-02-30T00:00:00Z", "2026-11-14T00:00:00+00:00",
                        "2026-11-14T00:00:00.000Z", "2026-11-14 00:00:00Z",
                        "2026-11-14", 1794624600]:
            with self.subTest(created=created):
                with self.assertRaises(proof.ProofError):
                    proof.sign({"a": 1}, TEST_SECRET, created)

    def test_an_at_context_that_isnt_a_list_is_not_signed(self):
        # verify reads @context only as a list, so sign refuses anything
        # else rather than make a proof that can't be verified.
        with self.assertRaises(proof.ProofError):
            proof.sign({"@context": "https://example.org"}, TEST_SECRET,
                       "2026-11-14T00:00:00Z")

    def test_a_record_that_breaks_the_rules_is_not_signed(self):
        with self.assertRaises(proof.ProofError):
            proof.sign({"a": 0.5}, TEST_SECRET, "2026-11-14T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
