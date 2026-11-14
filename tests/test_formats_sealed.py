"""Sealed records (formats/sealed.py): world-keys and journal entries,
signed and sealed to the one they name, checked against the vectors Rust
reads too (vectors/formats/sealed-records-v1.json)."""
from __future__ import annotations

import json
import unittest

from formats import records, seal, sealed, sealed_vectors
from formats.multikey import sealing_secret_from_multikey

VECTORS = json.loads(sealed_vectors.FILE.read_text(encoding="utf-8"))
PARTIES = VECTORS["parties"]


def _sealing_secret(name: str) -> bytes:
    return sealing_secret_from_multikey(
        PARTIES[name]["sealingSecretMultibase"])


def _record(name: str):
    return next(e["record"] for e in VECTORS["records"] if e["name"] == name)


class TestVectors(unittest.TestCase):
    def test_the_file_is_what_the_code_writes(self) -> None:
        self.assertEqual(
            sealed_vectors.FILE.read_text(encoding="utf-8"),
            sealed_vectors.text(sealed_vectors.current()),
            "rewrite with: python3 -m formats.sealed_vectors")

    def test_the_envelope_schema_names_the_labels_in_use(self) -> None:
        enum = records.SCHEMA["$defs"]["sealed"]["properties"]["label"]
        self.assertEqual(enum["enum"], sorted(seal.LABELS))
        self.assertEqual({label for label, _ in sealed.SEALED.values()},
                         set(seal.LABELS))

    def test_records(self) -> None:
        for entry in VECTORS["records"]:
            with self.subTest(name=entry["name"]):
                records.check(entry["record"])
                self.assertEqual(records.record_hash(entry["record"]),
                                 entry["hash"])
        for entry in VECTORS["refusedRecords"]:
            with self.subTest(name=entry["name"]):
                with self.assertRaises(records.RecordError):
                    records.check(entry["record"])

    def test_what_opens(self) -> None:
        for entry in VECTORS["opens"]:
            with self.subTest(name=entry["name"]):
                opener = entry["opener"]
                record = sealed.open_record(
                    entry["envelope"], _sealing_secret(opener),
                    PARTIES[opener]["id"], entry["label"])
                self.assertEqual(records.record_hash(record),
                                 entry["record"])
                self.assertEqual(sealed.fingerprint(entry["envelope"]),
                                 entry["fingerprint"])

    def test_what_must_be_refused_is_what_its_name_says(self) -> None:
        for entry in VECTORS["refused"]:
            with self.subTest(name=entry["name"]):
                inside = seal.open_box(
                    bytes.fromhex(entry["envelope"]["box"]),
                    _sealing_secret(entry["sealedFor"]),
                    entry["sealedUnder"])
                self.assertEqual(inside.hex(), entry["inside"])

    def test_what_must_be_refused_is(self) -> None:
        for entry in VECTORS["refused"]:
            with self.subTest(name=entry["name"]):
                opener = entry["opener"]
                with self.assertRaises(sealed.SealedError):
                    sealed.open_record(
                        entry["envelope"], _sealing_secret(opener),
                        PARTIES[opener]["id"], entry["label"])
        for entry in VECTORS["refusedEnvelopes"]:
            with self.subTest(name=entry["name"]):
                self.assertTrue(sealed.envelope_problems(entry["envelope"]))

    def test_junk_is_not_kept(self) -> None:
        # A kept box must still open, with the key and label stated, to
        # exactly what is stated; junk is replaced with a new box.
        old = json.loads(json.dumps(VECTORS))
        name = "ALICE's world-key, sealed again to BOB"
        for entry in old["refused"]:
            if entry["name"] == name:
                entry["envelope"]["box"] = "00" * 200
        new = sealed_vectors.vectors(old)
        entry = next(e for e in new["refused"] if e["name"] == name)
        self.assertNotEqual(entry["envelope"]["box"], "00" * 200)
        self.assertEqual(
            seal.open_box(bytes.fromhex(entry["envelope"]["box"]),
                          _sealing_secret("BOB"),
                          "open-worlds/world-key/v1").hex(),
            entry["inside"])


class TestSealing(unittest.TestCase):
    def setUp(self) -> None:
        self.world_key = _record("ALICE's world-key")
        self.alice = PARTIES["ALICE"]["id"]
        self.secret = _sealing_secret("ALICE")
        self.public = seal.public_from_secret(self.secret)

    def test_round_trip(self) -> None:
        envelope = sealed.seal_record(self.world_key, self.public)
        self.assertEqual(envelope["to"], self.alice)
        self.assertEqual(envelope["label"], "open-worlds/world-key/v1")
        self.assertEqual(sealed.envelope_problems(envelope), [])
        self.assertEqual(
            sealed.open_record(envelope, self.secret, self.alice,
                               "open-worlds/world-key/v1"),
            self.world_key)

    def test_a_journal_entry_is_sealed_to_its_author(self) -> None:
        entry = _record("ALICE's journal entry")
        envelope = sealed.seal_record(entry, self.public)
        self.assertEqual(envelope["label"], "open-worlds/journal/v1")
        with self.assertRaises(sealed.SealedError):
            sealed.open_record(envelope, self.secret, self.alice,
                               "open-worlds/world-key/v1")
        self.assertEqual(
            sealed.open_record(envelope, self.secret, self.alice,
                               "open-worlds/journal/v1"), entry)

    def test_only_a_record_that_holds_is_sealed(self) -> None:
        bad = VECTORS["refusedRecords"][0]["record"]
        with self.assertRaises(sealed.SealedError):
            sealed.seal_record(bad, self.public)

    def test_only_a_sealed_kind_is_sealed(self) -> None:
        log_head = json.loads(bytes.fromhex(next(
            e["inside"] for e in VECTORS["refused"]
            if e["name"] == "inside, a record of a kind that isn't sealed")))
        records.check(log_head)
        with self.assertRaises(sealed.SealedError):
            sealed.seal_record(log_head, self.public)

    def test_the_opener_names_a_label_in_use(self) -> None:
        envelope = sealed.seal_record(self.world_key, self.public)
        with self.assertRaises(sealed.SealedError):
            sealed.open_record(envelope, self.secret, self.alice,
                               "open-worlds/world-key/v2")

    def test_not_an_envelope(self) -> None:
        for value in (None, [], "envelope", 3):
            with self.subTest(value=value):
                self.assertTrue(sealed.envelope_problems(value))
                with self.assertRaises(sealed.SealedError):
                    sealed.open_record(value, self.secret, self.alice,
                                       "open-worlds/world-key/v1")


if __name__ == "__main__":
    unittest.main()
