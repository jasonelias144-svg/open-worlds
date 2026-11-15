"""The plant worlds' shared vectors, checked from Python.

The plant world is built in Rust (rust/plant-world). Its rule is
DeepSeek's, and sketches/deepseek/012-06-02/plant_world_vectors_test.py
checks every step against the sketch's own `advance`. Here Python checks
the rest independently, without importing anything from sketches/:

- each world's log holds by the Python kernel's own check,
  World.verify_log, so both languages write and read one format;
- each world grows by the rule as rust/plant-world/src/rule.rs documents
  it, written again below, and finishes when nothing more can grow;
- each head the world signed holds by formats/records.py and covers the
  whole log; each birth record holds, names the template by hash and the
  law by hash, and its dials agree with the template's ranges;
- every key is the trial key its seed makes.

Rewrite the vectors with:
    cd rust && cargo run -p plant-world --example plant -- --vectors ../vectors
"""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat)

from formats import multikey, records
from formats.canonical import canonical
from world import World

VECTORS = Path(__file__).resolve().parent.parent / "vectors"
DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1),
              (0, 1), (-1, 1), (-1, 0), (-1, -1)]


def advance(tips, dials, pot):
    """One step of the plant's rule, as rust/plant-world/src/rule.rs
    documents it."""
    if dials["water"] <= 0:
        return [], list(tips)
    depth = (dials["maxDepth"] if dials["light"] >= 3
             else dials["maxDepth"] // 2)
    segments, frontier = [], []
    for x, y, d, n in tips:
        if n >= depth:
            continue
        dx, dy = DIRECTIONS[d]
        nx, ny = x + dx * dials["branchLength"], y + dy * dials["branchLength"]
        if pot is not None:
            px, py, pw, ph = pot
            if not (px <= nx < px + pw and py <= ny < py + ph):
                continue
        segments.append([x, y, nx, ny])
        frontier.append([nx, ny, (d - 1) % 8, n + 1])
        frontier.append([nx, ny, (d + 1) % 8, n + 1])
    return segments, frontier


def trial_did(seed, label):
    secret = hashlib.sha256(
        f"open-worlds trial key, never for anything real: {seed}: {label}"
        .encode()).digest()
    public = Ed25519PrivateKey.from_private_bytes(secret).public_key()
    return multikey.did_key(public.public_bytes(Encoding.Raw,
                                                PublicFormat.Raw))


class PlantWorldVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(VECTORS / "plant-world.json", encoding="utf-8") as f:
            cls.v = json.load(f)
        cls.worlds = cls.v["worlds"]

    def test_there_are_worlds_of_every_kind(self):
        names = [w["name"] for w in self.worlds]
        self.assertEqual(len(names), 5)
        pots = [w["log"][0]["data"]["pot"] for w in self.worlds]
        self.assertTrue(any(p is None for p in pots))
        self.assertTrue(any(p is not None for p in pots))

    def test_every_log_holds_by_the_python_kernels_check(self):
        for w in self.worlds:
            self.assertTrue(World.verify_log(w["log"]), w["name"])
            changed = copy.deepcopy(w["log"])
            changed[0]["data"]["dials"]["water"] = 9
            self.assertFalse(World.verify_log(changed))

    def test_every_world_grows_by_its_rule_and_finishes(self):
        for w in self.worlds:
            log = w["log"]
            first = log[0]
            self.assertEqual(first["kind"], "world_created")
            data = first["data"]
            self.assertEqual(data["rule"], "open-worlds/plant-rule/v1")
            self.assertEqual(data["tip"], [0, 0, 0, 0])
            tips = [data["tip"]]
            for tick, entry in enumerate(log[1:-1], start=1):
                self.assertEqual((entry["kind"], entry["tick"]),
                                 ("grew", tick))
                segments, tips = advance(tips, data["dials"], data["pot"])
                self.assertEqual(entry["data"],
                                 {"segments": segments, "tips": tips})
            last = log[-1]
            self.assertEqual((last["kind"], last["tick"]),
                             ("finished", len(log) - 1))
            # Nothing more could grow: no water, or no branch left.
            nothing = (data["dials"]["water"] <= 0
                       or advance(tips, data["dials"], data["pot"])[0] == [])
            self.assertTrue(nothing, w["name"])

    def test_every_key_is_the_trial_key_its_seed_makes(self):
        self.assertEqual(self.v["template"]["issuer"],
                         trial_did(0, "template keeper"))
        for w in self.worlds:
            self.assertEqual(w["log"][0]["data"]["world"],
                             trial_did(w["seed"], "plant world"))

    def test_the_head_each_world_signed_covers_its_whole_log(self):
        for w in self.worlds:
            head = records.check(w["head"])
            log = w["log"]
            self.assertEqual(head["format"], "open-worlds/log-head/v1")
            self.assertEqual(head["world"], log[0]["data"]["world"])
            self.assertEqual(head["length"], len(log))
            self.assertEqual(head["last"], log[-1]["hash"])
            self.assertEqual(head["tick"], log[-1]["tick"])

    def test_each_birth_names_its_template_law_and_dials(self):
        template = self.v["template"]
        records.check(template)
        template_hash = records.record_hash(template)
        self.assertEqual(self.v["templateHash"], template_hash)
        law_hash = hashlib.sha256(canonical(self.v["law"])).hexdigest()
        self.assertEqual(self.v["lawHash"], law_hash)
        defaults = {name: p["value"]
                    for name, p in template["parameters"].items()}
        for w in self.worlds:
            birth = records.check(w["birth"])
            self.assertEqual(birth["world"], w["log"][0]["data"]["world"])
            self.assertEqual(birth["template"], template_hash)
            self.assertEqual(birth["law"], law_hash)
            self.assertEqual(w["log"][0]["data"]["template"],
                             template_hash)
            self.assertEqual(records.dial_problems(w["birth"], template),
                             [])
            dials = w["log"][0]["data"]["dials"]
            changed = {k: v for k, v in dials.items() if v != defaults[k]}
            self.assertEqual(birth.get("dials", {}), changed)

    def test_a_birth_signed_by_another_key_is_refused(self):
        birth = copy.deepcopy(self.worlds[0]["birth"])
        birth["world"] = trial_did(99, "plant world")
        with self.assertRaises(records.RecordError):
            records.check(birth)


if __name__ == "__main__":
    unittest.main()
