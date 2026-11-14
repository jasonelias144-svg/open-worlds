"""
fractal_world.py — A proposal sketch for the atomic fractal world.

Design proposal for a future course step. Not a course step itself.

Follows the new standard's shape: integer coordinates in records,
no floats in records, ASCII keys, signed records, deterministic
reconstruction. Uses Ed25519 via `cryptography` for signatures.

Simplifications relative to the standard, marked for review:
  - `sig` is a flat field, not a W3C DataIntegrityProof object.
  - Short keys are used; exact key names should be checked against
    schemas/records-v1.schema.json before merging.
  - No HPKE sealing; the log is public.
  - No template registry; templates are passed in directly.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import hashlib
import json
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True,
                      separators=(",", ":")).encode()


def _hash(obj) -> str:
    return hashlib.sha256(_canonical(obj)).hexdigest()


# N, NE, E, SE, S, SW, W, NW — integer unit vectors
DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1),
              (0, 1), (-1, 1), (-1, 0), (-1, -1)]


@dataclass(frozen=True)
class WorldTemplate:
    template_id: str
    branch_length: int
    max_depth: int

    def to_dict(self) -> Dict:
        return {"template_id": self.template_id,
                "branch_length": self.branch_length,
                "max_depth": self.max_depth}

    def template_hash(self) -> str:
        return _hash(self.to_dict())


@dataclass(frozen=True)
class WorldSeed:
    world_id: str
    template_hash: str
    pot: Tuple[int, int, int, int]
    initial_tip: Tuple[int, int, int]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {"type": "seed", "world_id": self.world_id,
                "template_hash": self.template_hash,
                "pot": list(self.pot),
                "initial_tip": list(self.initial_tip),
                "ts": self.ts}

    def record_hash(self) -> str:
        return _hash(self.body())


@dataclass(frozen=True)
class GrowthRecord:
    world_id: str
    step: int
    seed_hash: str
    prev: Optional[str]
    segs: List[Tuple[int, int, int, int]]
    tips: List[Tuple[int, int, int, int]]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {"type": "growth", "world_id": self.world_id,
                "step": self.step, "seed": self.seed_hash,
                "prev": self.prev,
                "segs": [list(s) for s in self.segs],
                "tips": [list(t) for t in self.tips],
                "ts": self.ts}

    def record_hash(self) -> str:
        return _hash(self.body())


def grow_tip(tip, template, pot):
    x, y, d, depth = tip
    if depth >= template.max_depth:
        return (None, [])
    dx, dy = DIRECTIONS[d]
    nx = x + dx * template.branch_length
    ny = y + dy * template.branch_length
    px, py, pw, ph = pot
    if not (px <= nx < px + pw and py <= ny < py + ph):
        return (None, [])
    seg = (x, y, nx, ny)
    return (seg, [(nx, ny, (d - 1) % 8, depth + 1),
                  (nx, ny, (d + 1) % 8, depth + 1)])


def advance(tips, template, pot):
    segs, new_frontier = [], []
    for tip in tips:
        seg, nt = grow_tip(tip, template, pot)
        if seg is not None:
            segs.append(seg)
            new_frontier.extend(nt)
    return segs, new_frontier


class AtomicFractalWorld:
    """The smallest interesting world: one plant, one pot, one log."""

    def __init__(self, template, pot, initial_tip, keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._template = template
        self._pot = pot
        self._keypair = keypair
        pub = keypair.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw).hex()
        self._world_id = f"did:key:{pub}"
        self._seed_body = {
            "type": "seed", "world_id": self._world_id,
            "template_hash": template.template_hash(),
            "pot": list(pot),
            "initial_tip": list(initial_tip),
            "ts": _now()}
        self._seed = WorldSeed(
            world_id=self._world_id,
            template_hash=template.template_hash(),
            pot=pot, initial_tip=initial_tip,
            ts=self._seed_body["ts"],
            sig=keypair.sign(_canonical(self._seed_body)).hex())
        self._records: List[GrowthRecord] = []
        self._frontier = [(initial_tip[0], initial_tip[1],
                           initial_tip[2], 0)]
        self._segments: List[Tuple[int, int, int, int]] = []

    @property
    def world_id(self) -> str:
        return self._world_id

    def seed(self) -> WorldSeed:
        return self._seed

    def records(self) -> List[GrowthRecord]:
        return list(self._records)

    def segments(self):
        return list(self._segments)

    def frontier(self):
        return list(self._frontier)

    def is_growing(self) -> bool:
        return bool(self._frontier)

    def grow(self) -> Optional[GrowthRecord]:
        if not self.is_growing():
            return None
        new_segs, new_frontier = advance(
            self._frontier, self._template, self._pot)
        if not new_segs and not new_frontier:
            self._frontier = []
            return None
        prev = (self._records[-1].record_hash()
                if self._records else None)
        body = {"type": "growth",
                "world_id": self._world_id,
                "step": len(self._records),
                "seed": self._seed.record_hash(),
                "prev": prev,
                "segs": [list(s) for s in new_segs],
                "tips": [list(t) for t in new_frontier],
                "ts": _now()}
        rec = GrowthRecord(
            world_id=self._world_id, step=body["step"],
            seed_hash=body["seed"], prev=prev,
            segs=new_segs, tips=new_frontier,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex())
        self._records.append(rec)
        self._segments.extend(new_segs)
        self._frontier = new_frontier
        return rec

    def grow_until_done(self, max_steps: int = 200) -> int:
        n = 0
        while self.is_growing() and n < max_steps:
            if self.grow() is None:
                break
            n += 1
        return n


def _verify_sig(world_id: str, body: Dict, sig: str) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        pub = Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(world_id[len("did:key:"):]))
        pub.verify(bytes.fromhex(sig), _canonical(body))
        return True
    except Exception:
        return False


def verify_log(seed: WorldSeed, records, expected_world_id):
    """Chain integrity + signatures. Never raises."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if seed.world_id != expected_world_id:
        return (False, "seed world_id mismatch")
    if not _verify_sig(seed.world_id, seed.body(), seed.sig):
        return (False, "seed signature invalid")
    prev = None
    for i, rec in enumerate(records):
        if rec.world_id != expected_world_id:
            return (False, f"record {i} world_id mismatch")
        if rec.seed_hash != seed.record_hash():
            return (False, f"record {i} seed_hash mismatch")
        if rec.prev != prev:
            return (False, f"record {i} prev mismatch")
        if not _verify_sig(rec.world_id, rec.body(), rec.sig):
            return (False, f"record {i} signature invalid")
        prev = rec.record_hash()
    return (True, "log verifies")


def verify_growth(seed: WorldSeed, records, template):
    """Verify that each record is a valid application of the
    growth rule. Never raises."""
    ok, reason = verify_log(seed, records, seed.world_id)
    if not ok:
        return (False, reason)
    expected = [(seed.initial_tip[0], seed.initial_tip[1],
                 seed.initial_tip[2], 0)]
    for i, rec in enumerate(records):
        exp_segs, exp_tips = advance(expected, template, seed.pot)
        if sorted(rec.segs) != sorted(exp_segs):
            return (False, f"record {i} segs do not match rule")
        if sorted(rec.tips) != sorted(exp_tips):
            return (False, f"record {i} tips do not match rule")
        expected = exp_tips
    return (True, "growth verifies")


@dataclass
class Plant:
    pot: Tuple[int, int, int, int]
    segments: List[Tuple[int, int, int, int]]
    frontier: List[Tuple[int, int, int, int]]
    depth: int


def reconstruct(seed: WorldSeed, records) -> Plant:
    segs, frontier, depth = [], [], 0
    frontier = [(seed.initial_tip[0], seed.initial_tip[1],
                 seed.initial_tip[2], 0)]
    for rec in records:
        segs.extend(rec.segs)
        frontier = rec.tips
        depth = rec.step + 1
    return Plant(pot=seed.pot, segments=segs,
                 frontier=frontier, depth=depth)


def render_ascii(plant: Plant) -> str:
    px, py, pw, ph = plant.pot
    grid = [["." for _ in range(pw)] for _ in range(ph)]
    for (x1, y1, x2, y2) in plant.segments:
        for (x, y) in _line_cells(x1, y1, x2, y2):
            if px <= x < px + pw and py <= y < py + ph:
                grid[y - py][x - px] = "#"
    for (x, y, _d, _depth) in plant.frontier:
        if px <= x < px + pw and py <= y < py + ph:
            grid[y - py][x - px] = "*"
    return "\n".join("".join(row) for row in grid)


def _line_cells(x1, y1, x2, y2):
    cells, dx, dy = [], abs(x2 - x1), -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx + dy
    x, y = x1, y1
    while True:
        cells.append((x, y))
        if x == x2 and y == y2:
            return cells
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x += sx
        if e2 <= dx:
            err += dx; y += sy


def render_svg(plant: Plant, size: int = 400) -> str:
    px, py, pw, ph = plant.pot
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" '
        f'viewBox="{px} {py} {pw} {ph}">',
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" '
        f'fill="#f7f3ec" stroke="#c8b899" stroke-width="0.5"/>',
    ]
    for (x1, y1, x2, y2) in plant.segments:
        lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#3a5a40" stroke-width="0.5" '
            f'stroke-linecap="round"/>')
    for (x, y, _d, _depth) in plant.frontier:
        lines.append(
            f'<circle cx="{x}" cy="{y}" r="0.4" '
            f'fill="#f0a202"/>')
    lines.append("</svg>")
    return "\n".join(lines)
