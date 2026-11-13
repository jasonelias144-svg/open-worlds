"""The Ur-world's shared vectors, checked from Python.

The Ur-world is built in Rust (rust/ur-world), and the Rust kernel is its
reference. Python checks what it can independently:

- the garden's log (vectors/ur-garden-log.json) holds by the Python kernel's
  own check, World.verify_log, so both languages write and read one format;
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
import unittest
from pathlib import Path

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
        self.assertEqual(entered, ["ALICE", "BOB"])
        said = [(e["agent"], e["data"]["text"])
                for e in self.log if e["kind"] == "said"]
        self.assertEqual(said, [("ALICE", "Hello, world."),
                                ("BOB", "Hello, ALICE.")])

    def test_every_explored_chunk_regenerates_here(self):
        seed = self.log[0]["data"]["seed"]
        explored = [e for e in self.log if e["kind"] == "explored"]
        self.assertGreater(len(explored), 50)
        for e in explored:
            with self.subTest(chunk=e["data"]["chunk"]):
                self.assertEqual(e["data"]["generator"], 1)
                self.assertEqual(chunk_hash(seed, *e["data"]["chunk"]),
                                 e["data"]["hash"])


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
