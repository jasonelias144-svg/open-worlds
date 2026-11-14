"""The records the offices keep (formats/records.py): one JSON Schema,
schemas/records-v1.schema.json, read by Python and by Rust, and the
shared vectors in vectors/formats/records-v1.json."""
import json
import re
import unittest

import jsonschema

from formats import record_vectors, records
from formats.multikey import secret_from_multikey

VECTORS = json.loads(record_vectors.FILE.read_text(encoding="utf-8"))


class TestTheSchema(unittest.TestCase):

    def test_it_is_a_valid_2020_12_schema(self):
        jsonschema.Draft202012Validator.check_schema(records.SCHEMA)

    def test_every_kind_has_a_schema_and_a_signer(self):
        for fmt, (name, path) in records.KINDS.items():
            with self.subTest(fmt):
                definition = records.SCHEMA["$defs"][name]
                self.assertEqual(definition["properties"]["format"],
                                 {"const": fmt})
                self.assertIn("proof", definition["required"])
                self.assertIn(path[0], definition["required"])

    def test_why_patterns_end_in_backslash_z_in_python(self):
        # Python's $ also matches before a final line break; ECMA-262's,
        # which JSON Schema uses and Rust follows, doesn't.
        self.assertTrue(re.search("^a$", "a\n"))
        self.assertTrue(records.problems({
            "format": "open-worlds/rating/v1",
            "author": VECTORS["parties"]["ALICE"]["didKey"] + "\n"}))


class TestTheVectors(unittest.TestCase):

    def test_the_file_is_what_this_code_writes_now(self):
        self.assertEqual(
            record_vectors.FILE.read_text(encoding="utf-8"),
            record_vectors.text(),
            "rewrite with: python3 -m formats.record_vectors")

    def test_each_valid_record_holds_with_its_hash_and_signature(self):
        for case in VECTORS["valid"]:
            with self.subTest(case["name"]):
                record = case["record"]
                unsecured = records.check(record)
                self.assertEqual(records.record_hash(record), case["hash"])
                secret = secret_from_multikey(
                    VECTORS["parties"][case["signer"]]["secretKeyMultibase"])
                self.assertEqual(
                    records.sign(unsecured, secret, VECTORS["created"]),
                    record)

    def test_every_kind_has_a_valid_record(self):
        # The offices' kinds here; the sealed kinds in
        # sealed-records-v1.json, beside the boxes they travel in.
        from formats import sealed_vectors
        sealed_records = json.loads(
            sealed_vectors.FILE.read_text(encoding="utf-8"))["records"]
        self.assertEqual(
            {c["record"]["format"] for c in VECTORS["valid"]}
            | {c["record"]["format"] for c in sealed_records},
            set(records.KINDS))

    def test_each_refused_record_is_refused(self):
        for case in VECTORS["refused"]:
            with self.subTest(case["name"]):
                with self.assertRaises(records.RecordError):
                    records.check(case["record"])


class TestSigning(unittest.TestCase):

    def test_only_the_one_who_must_sign_can_sign(self):
        grant = {k: v for k, v in VECTORS["valid"][0]["record"].items()
                 if k != "proof"}
        holder = secret_from_multikey(VECTORS["parties"][
            "the Ur-world's Keeper"]["secretKeyMultibase"])
        with self.assertRaises(records.RecordError):
            records.sign(grant, holder, VECTORS["created"])

    def test_a_record_that_doesnt_fit_is_not_signed(self):
        alice = secret_from_multikey(
            VECTORS["parties"]["ALICE"]["secretKeyMultibase"])
        with self.assertRaises(records.RecordError):
            records.sign({"format": "open-worlds/rating/v1", "score": 9},
                         alice, VECTORS["created"])

    def test_anything_that_isnt_a_record_is_refused_never_a_crash(self):
        for value in [None, "x", 1, [], {}, {"format": []}, {"format": {}},
                      {"format": None}, {"format": "open-worlds/grant/v9"}]:
            with self.subTest(value=value):
                self.assertTrue(records.problems(value))
                with self.assertRaises(records.RecordError):
                    records.check(value)

    def test_problems_name_every_place(self):
        found = records.problems({"format": "open-worlds/rating/v1",
                                  "score": 9})
        self.assertIn("$.score: 9 is greater than the maximum of 5", found)
        self.assertIn("$: 'author' is a required property", found)


if __name__ == "__main__":
    unittest.main()
