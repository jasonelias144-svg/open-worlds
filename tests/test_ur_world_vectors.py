"""The Ur-world's shared vectors, checked from Python.

The Ur-world is built in Rust (rust/ur-world), and the Rust kernel is its
reference. Python checks what it can independently:

- the garden's log (vectors/ur-garden-log.json) holds by the Python kernel's
  own check, World.verify_log, so both languages write and read one format;
- every arrival in it (open-worlds/arrival/v1) holds by formats/records.py,
  and names the log's world, its entry's tick, name and the entry before
  it, with each name kept to one key; and the head the garden's world
  signed (vectors/ur-garden-head.json) covers the whole log;
- the glasshouses (vectors/ur-garden-hosted.json): every plant world the
  garden hosts holds by the Python kernel's check and grows by the plant
  rule, its head and birth record hold, and the garden's log names each
  step it gave each plant, in order: its `hosted` entry names the plant's
  first entry, and each `tended` entry the plant's next one, to the last;
- the generator: written again below from its documented rules
  (rust/ur-world/src/generate.rs), it gives the same ground heights and the
  same chunk hashes as vectors/ur-chunks.json, and the same chunk for every
  chunk the garden's log says was explored.

Rewrite the vectors with:
    cd rust && cargo run -p ur-world --example garden -- --vectors ../vectors
"""
import hashlib
import json
import math
import unicodedata
import unittest
from pathlib import Path

from formats import records
from tests.test_plant_world_vectors import advance, trial_did
from world import World

VECTORS = Path(__file__).resolve().parent.parent / "vectors"
MASK = (1 << 64) - 1

# Generator version 1, as documented in rust/ur-world/src/generate.rs.
CHUNK = 16
SEA = -2
GARDEN_RADIUS = 8
BLEND = 16
FINE = 1023
SPRING = (2, 0, 3)
AIR, GRASS, SOIL, ROCK, WATER, WOOD, LEAVES = 0, 1, 2, 3, 4, 5, 6


def mix(z):
    z = ((z ^ (z >> 30)) * 0xbf58476d1ce4e5b9) & MASK
    z = ((z ^ (z >> 27)) * 0x94d049bb133111eb) & MASK
    return z ^ (z >> 31)


def lattice(seed, layer, a, b):
    start = mix(seed ^ ((layer * 0x9e3779b97f4a7c15) & MASK))
    return mix(mix(start ^ (a & MASK)) ^ (b & MASK))


def noise(seed, layer, spacing, height, x, z):
    gx, fx = divmod(x, spacing)     # Python's divmod rounds down, as
    gz, fz = divmod(z, spacing)     # div_euclid does for a positive divisor
    fine = lambda a, b: lattice(seed, layer, a, b) % 1024  # noqa: E731
    whole = spacing ** 3
    weight = lambda f: 3 * f * f * spacing - 2 * f ** 3  # noqa: E731
    wx, wz = weight(fx), weight(fz)
    north = fine(gx, gz) * (whole - wx) + fine(gx + 1, gz) * wx
    south = fine(gx, gz + 1) * (whole - wx) + fine(gx + 1, gz + 1) * wx
    total = north * (whole - wz) + south * wz
    out_of = whole * whole * FINE
    return (total * height + out_of // 2) // out_of


def ground(seed, x, z):
    hills = (-12 + noise(seed, 1, 128, 16, x, z)
             + noise(seed, 2, 32, 8, x, z) + noise(seed, 3, 8, 2, x, z))
    reach = GARDEN_RADIUS + BLEND
    if abs(x) >= reach or abs(z) >= reach:
        return hills
    d = math.isqrt(x * x + z * z)
    if d <= GARDEN_RADIUS:
        return 0
    if d >= reach:
        return hills
    return (hills * (d - GARDEN_RADIUS) + BLEND // 2) // BLEND


def natural(g, y):
    if y > g:
        return WATER if y <= SEA else AIR
    if y == g:
        return SOIL if g < SEA else GRASS
    return SOIL if y > g - 3 else ROCK


def garden_piece(x, y, z):
    if (x, y, z) == SPRING:
        return WATER
    ax, az = abs(x), abs(z)
    if ax == 0 and az == 0 and 1 <= y <= 4:
        return WOOD
    crown = y in (4, 5) and ax <= 2 and az <= 2 and not (ax == 2 and az == 2)
    top = y == 6 and ax + az <= 1
    return LEAVES if crown or top else None


def chunk_hash(seed, cx, cy, cz):
    ox, oy, oz = cx * CHUNK, cy * CHUNK, cz * CHUNK
    heights = {(lx, lz): ground(seed, ox + lx, oz + lz)
               for lz in range(CHUNK) for lx in range(CHUNK)}
    cells = bytearray()
    for ly in range(CHUNK):
        for lz in range(CHUNK):
            for lx in range(CHUNK):
                x, y, z = ox + lx, oy + ly, oz + lz
                piece = garden_piece(x, y, z)
                cells.append(piece if piece is not None
                             else natural(heights[lx, lz], y))
    return hashlib.sha256(bytes(cells)).hexdigest()


class TestTheGardensLog(unittest.TestCase):

    def setUp(self):
        self.log = json.loads((VECTORS / "ur-garden-log.json").read_text())

    def test_it_holds_by_the_python_kernels_check(self):
        self.assertTrue(World.verify_log(self.log))
        changed = [dict(e, data={**e["data"], "seed": 1})
                   if e["kind"] == "world_created" else e for e in self.log]
        self.assertFalse(World.verify_log(changed))

    def test_it_begins_with_a_garden_and_two(self):
        first = self.log[0]
        self.assertEqual(first["kind"], "world_created")
        self.assertEqual(first["data"]["seed"], 20261113)
        entered = [e["agent"] for e in self.log if e["kind"] == "entered"]
        # The scripted stand-ins: ALICE and BOB enter only at their birth.
        self.assertEqual(entered, ["WALKER", "GARDENER"])
        said = [(e["agent"], e["data"]["text"])
                for e in self.log if e["kind"] == "said"]
        self.assertEqual(said, [("WALKER", "Hello, world."),
                                ("GARDENER", "Hello, WALKER.")])

    def test_every_arrival_holds_and_keeps_each_name_to_one_key(self):
        world = self.log[0]["data"]["world"]
        bound = {}
        entered = [e for e in self.log if e["kind"] == "entered"]
        self.assertEqual(len(entered), 2)
        for e in entered:
            with self.subTest(name=e["agent"]):
                arrival = e["data"]["arrival"]
                records.check(arrival)
                self.assertEqual(arrival["format"], "open-worlds/arrival/v1")
                self.assertEqual(arrival["world"], world)
                self.assertEqual(arrival["tick"], e["tick"])
                self.assertEqual(arrival["previous"], e["prev"])
                self.assertEqual(arrival["name"], e["agent"])
                # A name the world allows: 1 to 64 characters, no control
                # character (Unicode's Cc), as rust/ur-world's good_name.
                self.assertTrue(1 <= len(arrival["name"]) <= 64)
                self.assertFalse(any(unicodedata.category(c) == "Cc"
                                     for c in arrival["name"]))
                key = bound.setdefault(arrival["name"], arrival["individual"])
                self.assertEqual(key, arrival["individual"])
        self.assertEqual(len(set(bound.values())), len(bound))
        # Changed after signing, an arrival no longer holds.
        changed = dict(entered[0]["data"]["arrival"], name="GARDENER")
        with self.assertRaises(records.RecordError):
            records.check(changed)

    def test_the_head_its_world_signed_covers_the_whole_log(self):
        head = json.loads((VECTORS / "ur-garden-head.json").read_text())
        records.check(head)
        self.assertEqual(head["format"], "open-worlds/log-head/v1")
        self.assertEqual(head["world"], self.log[0]["data"]["world"])
        self.assertEqual(head["length"], len(self.log))
        self.assertEqual(head["last"], self.log[-1]["hash"])
        self.assertGreaterEqual(head["tick"], self.log[-1]["tick"])

    def test_every_explored_chunk_regenerates_here(self):
        seed = self.log[0]["data"]["seed"]
        explored = [e for e in self.log if e["kind"] == "explored"]
        self.assertGreater(len(explored), 50)
        for e in explored:
            with self.subTest(chunk=e["data"]["chunk"]):
                self.assertEqual(e["data"]["generator"], 1)
                self.assertEqual(chunk_hash(seed, *e["data"]["chunk"]),
                                 e["data"]["hash"])


class TestTheGardensGlasshouses(unittest.TestCase):

    def setUp(self):
        self.log = json.loads((VECTORS / "ur-garden-log.json").read_text())
        self.hosted = json.loads(
            (VECTORS / "ur-garden-hosted.json").read_text())
        self.worlds = self.hosted["worlds"]

    def test_three_plants_each_a_world_of_its_own(self):
        self.assertEqual(len(self.worlds), 3)
        plants = json.loads((VECTORS / "plant-world.json").read_text())
        self.assertEqual(self.hosted["templateHash"], plants["templateHash"])
        for w in self.worlds:
            log = w["log"]
            self.assertTrue(World.verify_log(log), w["name"])
            data = log[0]["data"]
            self.assertEqual(data["world"],
                             trial_did(20261113, "plant world: " + w["name"]))
            self.assertEqual(data["template"], self.hosted["templateHash"])
            # It grows by the plant rule, step by step, and finishes.
            tips = [data["tip"]]
            for entry in log[1:-1]:
                segments, tips = advance(tips, data["dials"], data["pot"])
                self.assertEqual(entry["data"],
                                 {"segments": segments, "tips": tips})
            self.assertEqual(log[-1]["kind"], "finished")
            self.assertEqual(advance(tips, data["dials"], data["pot"])[0], [])

    def test_each_head_and_birth_holds(self):
        for w in self.worlds:
            head = records.check(w["head"])
            self.assertEqual((head["length"], head["last"]),
                             (len(w["log"]), w["log"][-1]["hash"]))
            birth = records.check(w["birth"])
            self.assertEqual(birth["world"], w["log"][0]["data"]["world"])
            self.assertEqual(birth["template"], self.hosted["templateHash"])
            self.assertEqual(records.dial_problems(w["birth"],
                                                   self.hosted["template"]),
                             [])

    def test_the_gardens_log_names_every_step_it_gave(self):
        by_key = {w["log"][0]["data"]["world"]: w for w in self.worlds}
        at = {}
        for entry in self.log:
            data = entry["data"]
            if entry["kind"] == "hosted":
                w = by_key[data["world"]]
                self.assertNotIn(data["world"], at)
                self.assertEqual(data["first"], w["log"][0]["hash"])
                self.assertEqual(data["kind"], "open-worlds/plant-rule/v1")
                self.assertEqual(data["at"], w["at"])
                hashes = [e["hash"] for e in w["log"]]
                at[data["world"]] = hashes.index(data["from"])
            elif entry["kind"] == "tended":
                for key, hash_ in data["worlds"]:
                    at[key] += 1
                    self.assertEqual(by_key[key]["log"][at[key]]["hash"],
                                     hash_)
            self.assertNotEqual(entry["kind"], "untended")
        for key, w in by_key.items():
            self.assertEqual(at[key], len(w["log"]) - 1, w["name"])

    def test_each_glasshouse_stands_on_the_gardens_ground(self):
        for w in self.worlds:
            x, y, z = w["at"]
            self.assertEqual(y, 1)
            self.assertLessEqual(math.isqrt(x * x + z * z), GARDEN_RADIUS)
            self.assertNotEqual((x, z), (0, 0))
            self.assertNotEqual((x, z), (SPRING[0], SPRING[2]))


class TestTheGenerator(unittest.TestCase):

    def setUp(self):
        self.vectors = json.loads((VECTORS / "ur-chunks.json").read_text())

    def test_mix_is_splitmix64(self):
        self.assertEqual(mix(0x9e3779b97f4a7c15), 0xe220a8397b1dcdaf)

    def test_the_same_heights_and_chunks_as_rust(self):
        self.assertEqual(self.vectors["generator"], 1)
        self.assertEqual(self.vectors["chunk"], CHUNK)
        for per_seed in self.vectors["seeds"]:
            seed = per_seed["seed"]
            for g in per_seed["ground"]:
                with self.subTest(seed=seed, column=(g["x"], g["z"])):
                    self.assertEqual(ground(seed, g["x"], g["z"]), g["height"])
            for c in per_seed["chunks"]:
                with self.subTest(seed=seed, chunk=c["chunk"]):
                    self.assertEqual(chunk_hash(seed, *c["chunk"]), c["hash"])


if __name__ == "__main__":
    unittest.main()
