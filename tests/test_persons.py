"""Persons (formats/persons.py): presence keys from a seed, links that hold
only both ways, and a person's list, against vectors/formats/persons-v1.json,
which rust/formats checks too."""
import json
import unittest

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from formats import persons, persons_vectors

VECTORS = json.loads(persons_vectors.FILE.read_text(encoding="utf-8"))
SEED = bytes.fromhex(VECTORS["seed"]["hex"])


class TheVectors(unittest.TestCase):
    def test_the_file_is_what_the_code_writes(self):
        self.assertEqual(persons_vectors.FILE.read_text(encoding="utf-8"),
                         persons_vectors.text())

    def test_the_seed_is_made_from_its_label(self):
        self.assertEqual(SEED, persons_vectors.SEED)


class PresenceKeys(unittest.TestCase):
    def test_hkdf_gives_rfc_5869s_first_test_case(self):
        case = VECTORS["hkdf"]
        okm = HKDF(algorithm=hashes.SHA256(), length=case["length"],
                   salt=bytes.fromhex(case["salt"]),
                   info=bytes.fromhex(case["info"])
                   ).derive(bytes.fromhex(case["ikm"]))
        self.assertEqual(okm.hex(), case["okm"])

    def test_each_presence_has_its_info_and_its_key(self):
        for p in VECTORS["presences"]:
            self.assertEqual(
                persons.presence_info(p["world"], p["counter"]).hex(),
                p["info"])
            self.assertEqual(
                persons.presence_key(SEED, p["world"], p["counter"]),
                p["key"])

    def test_no_two_presences_share_a_key(self):
        keys = [p["key"] for p in VECTORS["presences"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertNotIn(VECTORS["person"], keys)

    def test_info_is_the_label_the_world_and_four_bytes(self):
        p = VECTORS["presences"][1]
        info = bytes.fromhex(p["info"])
        self.assertEqual(info, b"open-worlds/presence/v1\x00"
                         + p["world"].encode() + b"\x00"
                         + p["counter"].to_bytes(4, "big"))

    def test_what_cant_be_a_presence_is_refused_with_the_reason(self):
        cases = VECTORS["refusedDerivations"]
        self.assertTrue(cases)
        for case in cases:
            with self.assertRaises(ValueError, msg=case["name"]) as caught:
                persons.presence_secret(bytes.fromhex(case["seed"]),
                                        case["world"], case["counter"])
            self.assertEqual(str(caught.exception), case["why"])

    def test_a_bool_isnt_a_counter(self):
        with self.assertRaises(ValueError):
            persons.presence_info(VECTORS["presences"][0]["world"], True)


class Links(unittest.TestCase):
    def test_each_link_holds_or_not_with_its_reasons(self):
        links = VECTORS["links"]
        self.assertTrue(any(l["linked"] for l in links))
        self.assertTrue(any(not l["linked"] for l in links))
        for link in links:
            found = persons.link_problems(link["holds"], link["heldBy"])
            self.assertEqual(found, link["problems"], link["name"])
            self.assertEqual(not found, link["linked"], link["name"])

    def test_what_isnt_a_record_is_refused(self):
        link = VECTORS["links"][0]
        self.assertEqual(persons.link_problems(None, link["heldBy"]),
                         ["holds: not a record of the format "
                          "open-worlds/holds/v1"])
        self.assertTrue(persons.link_problems(link["holds"], "held"))


class PersonLists(unittest.TestCase):
    def setUp(self):
        lists = VECTORS["personLists"]
        self.by = {v["name"]: v["record"] for v in lists["versions"]}
        self.lists = lists

    def test_each_history_holds_or_not_with_its_reasons(self):
        for case in self.lists["histories"]:
            found = persons.person_list_chain_problems(
                [self.by[v] for v in case["versions"]])
            self.assertEqual(found, case["problems"], case["name"])

    def test_each_seed_check_finds_what_it_says(self):
        for case in self.lists["seedChecks"]:
            record = case.get("record") or self.by[case["version"]]
            self.assertEqual(persons.seed_problems(record, SEED),
                             case["problems"], case["name"])

    def test_a_list_is_signed_by_its_person(self):
        v1 = self.by["version 1"]
        changed = dict(v1, person=VECTORS["presences"][0]["key"])
        self.assertTrue(persons.person_list_chain_problems([changed]))


if __name__ == "__main__":
    unittest.main()
