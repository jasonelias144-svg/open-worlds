"""
fractal_world_v2.py — Parametric fractal world.

Extends the earlier sketch with two parameter channels:

  - Internal parameters: the world changes its own params
    (e.g., near-boundary self-reduction of branch_length).
  - External parameters: someone else requests a change;
    the world applies it if the request is valid.

Both produce a `ParamChange` record in the log. The
uniformity is the point: the same record type, the same
chain, the same verifier — the only difference is who
signed.

The inertia: between param changes, growth follows the
current params exactly. A verifier can check every
growth record was produced by the params in effect at
that point in the chain.

Parameters:
  branch_length (int, 1-10)  — segment length
  max_depth     (int, 1-8)   — max tree depth
  water         (int, 0-10)  — 0 stalls growth
  light         (int, 0-10)  — <3 halves effective max_depth
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

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


DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1),
              (0, 1), (-1, 1), (-1, 0), (-1, -1)]
PARAM_NAMES = ("branch_length", "max_depth", "water", "light")


# =====================================================================
# ParamSet — immutable, hashable
# =====================================================================

@dataclass(frozen=True)
class ParamSet:
    branch_length: int
    max_depth: int
    water: int
    light: int

    def to_dict(self):
        return {
            "branch_length": self.branch_length,
            "max_depth": self.max_depth,
            "water": self.water,
            "light": self.light,
        }

    def param_hash(self):
        return _hash(self.to_dict())

    def with_change(self, param, value):
        if param not in PARAM_NAMES:
            raise ValueError(f"unknown param: {param}")
        d = self.to_dict()
        d[param] = value
        return ParamSet(**d)

    def effective_max_depth(self):
        return (self.max_depth if self.light >= 3
                else self.max_depth // 2)

    def can_grow(self):
        return self.water > 0


# =====================================================================
# Template, Seed
# =====================================================================

@dataclass(frozen=True)
class WorldTemplate:
    template_id: str
    branch_length: int = 2
    max_depth: int = 4
    water: int = 10
    light: int = 10

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "branch_length": self.branch_length,
            "max_depth": self.max_depth,
            "water": self.water,
            "light": self.light,
        }

    def template_hash(self):
        return _hash(self.to_dict())

    def initial_params(self):
        return ParamSet(
            branch_length=self.branch_length,
            max_depth=self.max_depth,
            water=self.water,
            light=self.light,
        )


@dataclass(frozen=True)
class WorldSeed:
    world_id: str
    template_hash: str
    pot: Tuple[int, int, int, int]
    initial_tip: Tuple[int, int, int]
    p0: Dict
    ts: str
    sig: str

    def body(self):
        return {
            "type": "seed",
            "world_id": self.world_id,
            "template_hash": self.template_hash,
            "pot": list(self.pot),
            "initial_tip": list(self.initial_tip),
            "p0": dict(self.p0),
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# ParamChange and GrowthRecord
# =====================================================================

@dataclass(frozen=True)
class ParamChange:
    world_id: str
    step: int
    param: str
    old_value: int
    new_value: int
    source: str           # "internal" | "external"
    authority_id: str
    prior: Optional[str]
    ts: str
    sig_authority: str
    sig_world: str

    def body(self):
        return {
            "type": "param",
            "world_id": self.world_id,
            "step": self.step,
            "param": self.param,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "source": self.source,
            "authority_id": self.authority_id,
            "prior": self.prior,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class GrowthRecord:
    world_id: str
    step: int
    seed_hash: str
    prev: Optional[str]
    p: str
    segs: List[Tuple[int, int, int, int]]
    tips: List[Tuple[int, int, int, int]]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "growth",
            "world_id": self.world_id,
            "step": self.step,
            "seed": self.seed_hash,
            "prev": self.prev,
            "p": self.p,
            "segs": [list(s) for s in self.segs],
            "tips": [list(t) for t in self.tips],
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


Record = Union[GrowthRecord, ParamChange]


# =====================================================================
# Growth rule
# =====================================================================

def advance(tips, params, pot):
    if not params.can_grow():
        return [], tips
    eff_max = params.effective_max_depth()
    segs, new_frontier = [], []
    px, py, pw, ph = pot
    for (x, y, d, depth) in tips:
        if depth >= eff_max:
            continue
        dx, dy = DIRECTIONS[d]
        nx = x + dx * params.branch_length
        ny = y + dy * params.branch_length
        if not (px <= nx < px + pw and py <= ny < py + ph):
            continue
        segs.append((x, y, nx, ny))
        new_frontier.append((nx, ny, (d - 1) % 8, depth + 1))
        new_frontier.append((nx, ny, (d + 1) % 8, depth + 1))
    return segs, new_frontier


# =====================================================================
# AtomicFractalWorld
# =====================================================================

class AtomicFractalWorld:
    def __init__(self, template, pot, initial_tip, keypair,
                 params=None):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._template = template
        self._pot = pot
        self._keypair = keypair
        self._params = params or template.initial_params()
        pub = keypair.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()
        self._world_id = f"did:key:{pub}"
        seed_body = {
            "type": "seed",
            "world_id": self._world_id,
            "template_hash": template.template_hash(),
            "pot": list(pot),
            "initial_tip": list(initial_tip),
            "p0": self._params.to_dict(),
            "ts": _now(),
        }
        self._seed = WorldSeed(
            world_id=self._world_id,
            template_hash=template.template_hash(),
            pot=pot, initial_tip=initial_tip,
            p0=self._params.to_dict(),
            ts=seed_body["ts"],
            sig=keypair.sign(_canonical(seed_body)).hex(),
        )
        self._records: List[Record] = []
        self._frontier = [(initial_tip[0], initial_tip[1],
                           initial_tip[2], 0)]
        self._segments: List[Tuple[int, int, int, int]] = []
        self._steps = 0
        self._last_record_hash: Optional[str] = None
        self._internal_policy = self._default_internal_policy

    # -- Accessors ---------------------------------------------

    @property
    def world_id(self):
        return self._world_id

    @property
    def params(self):
        return self._params

    def seed(self):
        return self._seed

    def records(self):
        return list(self._records)

    def segments(self):
        return list(self._segments)

    def frontier(self):
        return list(self._frontier)

    def is_growing(self):
        return bool(self._frontier) and self._params.can_grow()

    def is_stalled(self):
        return bool(self._frontier) and not self._params.can_grow()

    def is_done(self):
        return not self._frontier

    # -- Growth ------------------------------------------------

    def grow(self) -> Optional[GrowthRecord]:
        if not self.is_growing():
            return None
        segs, new_frontier = advance(
            self._frontier, self._params, self._pot)
        if not segs:
            self._frontier = []
            return None
        body = {
            "type": "growth",
            "world_id": self._world_id,
            "step": self._steps,
            "seed": self._seed.record_hash(),
            "prev": self._last_record_hash,
            "p": self._params.param_hash(),
            "segs": [list(s) for s in segs],
            "tips": [list(t) for t in new_frontier],
            "ts": _now(),
        }
        rec = GrowthRecord(
            world_id=self._world_id,
            step=self._steps,
            seed_hash=self._seed.record_hash(),
            prev=self._last_record_hash,
            p=self._params.param_hash(),
            segs=segs, tips=new_frontier,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._segments.extend(segs)
        self._frontier = new_frontier
        self._steps += 1
        self._last_record_hash = rec.record_hash()
        self._maybe_internal_change()
        return rec

    def grow_until(self, max_steps=200):
        n = 0
        while self.is_growing() and n < max_steps:
            if self.grow() is None:
                break
            n += 1
        return n

    def grow_n(self, n):
        for _ in range(n):
            if not self.is_growing():
                break
            if self.grow() is None:
                break

    # -- Internal change ---------------------------------------

    def _default_internal_policy(self):
        if self._params.branch_length <= 1:
            return None
        if not self._frontier:
            return None
        px, py, pw, ph = self._pot
        margin = self._params.branch_length * 2
        for (x, y, d, depth) in self._frontier:
            if (x - px < margin or (px + pw - x) < margin
                    or y - py < margin or (py + ph - y) < margin):
                return ("branch_length",
                        self._params.branch_length - 1)
        return None

    def _maybe_internal_change(self):
        result = self._internal_policy()
        if result is None:
            return
        param, new_value = result
        self.internal_change(param, new_value)

    def internal_change(self, param, new_value):
        """The world decides to change its own parameter.
        Signed only by the world."""
        if param not in PARAM_NAMES:
            return None
        if getattr(self._params, param) == new_value:
            return None
        body = {
            "type": "param",
            "world_id": self._world_id,
            "step": self._steps,
            "param": param,
            "old_value": getattr(self._params, param),
            "new_value": new_value,
            "source": "internal",
            "authority_id": self._world_id,
            "prior": self._last_record_hash,
            "ts": _now(),
        }
        sig = self._keypair.sign(_canonical(body)).hex()
        return self._apply_param_change(
            param, new_value, source="internal",
            authority_id=self._world_id,
            sig_authority=sig)

    # -- External change ---------------------------------------

    def external_change(self, authority_id, authority_kp,
                        param, new_value):
        """External authority requests a change; the world
        countersigns and applies it."""
        if param not in PARAM_NAMES:
            return None
        if getattr(self._params, param) == new_value:
            return None
        if authority_id == self._world_id:
            return None  # external authority must be distinct
        body = {
            "type": "param",
            "world_id": self._world_id,
            "step": self._steps,
            "param": param,
            "old_value": getattr(self._params, param),
            "new_value": new_value,
            "source": "external",
            "authority_id": authority_id,
            "prior": self._last_record_hash,
            "ts": _now(),
        }
        sig_auth = authority_kp.sign(_canonical(body)).hex()
        return self._apply_param_change(
            param, new_value, source="external",
            authority_id=authority_id,
            sig_authority=sig_auth)

    # -- Shared apply ------------------------------------------

    def _apply_param_change(self, param, new_value, source,
                            authority_id, sig_authority):
        body = {
            "type": "param",
            "world_id": self._world_id,
            "step": self._steps,
            "param": param,
            "old_value": getattr(self._params, param),
            "new_value": new_value,
            "source": source,
            "authority_id": authority_id,
            "prior": self._last_record_hash,
            "ts": _now(),
        }
        sig_world = self._keypair.sign(_canonical(body)).hex()
        rec = ParamChange(
            world_id=self._world_id,
            step=self._steps,
            param=param,
            old_value=getattr(self._params, param),
            new_value=new_value,
            source=source,
            authority_id=authority_id,
            prior=self._last_record_hash,
            ts=body["ts"],
            sig_authority=sig_authority,
            sig_world=sig_world,
        )
        self._records.append(rec)
        self._params = self._params.with_change(param, new_value)
        self._last_record_hash = rec.record_hash()
        return rec


# =====================================================================
# Verification
# =====================================================================

def _pubkey_from_did(did):
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


def verify_log(seed, records, expected_world_id=None):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if expected_world_id is None:
        expected_world_id = seed.world_id
    if seed.world_id != expected_world_id:
        return (False, "seed world_id mismatch")
    try:
        world_pub = _pubkey_from_did(seed.world_id)
        world_pub.verify(bytes.fromhex(seed.sig),
                         _canonical(seed.body()))
    except Exception as e:
        return (False, f"seed signature invalid: {e}")
    prev = None
    for i, rec in enumerate(records):
        if rec.world_id != expected_world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prior != prev:
            return (False, f"record {i}: prior mismatch")
        try:
            if isinstance(rec, GrowthRecord):
                world_pub.verify(bytes.fromhex(rec.sig),
                                 _canonical(rec.body()))
            elif isinstance(rec, ParamChange):
                world_pub.verify(bytes.fromhex(rec.sig_world),
                                 _canonical(rec.body()))
                if rec.source == "external":
                    if rec.authority_id == rec.world_id:
                        return (False, f"record {i}: external "
                                       f"change by world itself")
                    auth_pub = _pubkey_from_did(rec.authority_id)
                    auth_pub.verify(
                        bytes.fromhex(rec.sig_authority),
                        _canonical(rec.body()))
                elif rec.source == "internal":
                    if rec.authority_id != rec.world_id:
                        return (False, f"record {i}: internal "
                                       f"change by non-world")
                    world_pub.verify(
                        bytes.fromhex(rec.sig_authority),
                        _canonical(rec.body()))
                else:
                    return (False, f"record {i}: unknown "
                                   f"source {rec.source!r}")
            else:
                return (False, f"record {i}: unknown type")
        except Exception as e:
            return (False, f"record {i}: signature invalid: {e}")
        prev = rec.record_hash()
    return (True, "log verifies")


def verify_growth(seed, records, template,
                   expected_world_id=None):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if expected_world_id is None:
        expected_world_id = seed.world_id
    ok, reason = verify_log(seed, records, expected_world_id)
    if not ok:
        return (False, reason)
    current = ParamSet(**seed.p0)
    expected_tips = [(seed.initial_tip[0], seed.initial_tip[1],
                       seed.initial_tip[2], 0)]
    for i, rec in enumerate(records):
        if isinstance(rec, ParamChange):
            cur_val = getattr(current, rec.param)
            if cur_val != rec.old_value:
                return (False, f"record {i}: old_value mismatch "
                               f"(expected {cur_val}, "
                               f"record says {rec.old_value})")
            try:
                current = current.with_change(
                    rec.param, rec.new_value)
            except ValueError as e:
                return (False, f"record {i}: {e}")
        elif isinstance(rec, GrowthRecord):
            if rec.p != current.param_hash():
                return (False, f"record {i}: params hash "
                               f"mismatch")
            exp_segs, exp_tips = advance(
                expected_tips, current, seed.pot)
            if sorted(rec.segs) != sorted(exp_segs):
                return (False, f"record {i}: segs mismatch")
            if sorted(rec.tips) != sorted(exp_tips):
                return (False, f"record {i}: tips mismatch")
            expected_tips = exp_tips
    return (True, "growth verifies")


# =====================================================================
# Reconstruction
# =====================================================================

@dataclass
class Plant:
    pot: Tuple[int, int, int, int]
    segments: List[Tuple[int, int, int, int]]
    frontier: List[Tuple[int, int, int, int]]
    params: ParamSet
    steps: int
    param_changes: int


def reconstruct(seed, records):
    frontier = [(seed.initial_tip[0], seed.initial_tip[1],
                 seed.initial_tip[2], 0)]
    segments = []
    current = ParamSet(**seed.p0)
    steps = 0
    pc = 0
    for rec in records:
        if isinstance(rec, ParamChange):
            current = current.with_change(rec.param,
                                          rec.new_value)
            pc += 1
        elif isinstance(rec, GrowthRecord):
            segments.extend(rec.segs)
            frontier = rec.tips
            steps += 1
    return Plant(pot=seed.pot, segments=segments,
                 frontier=frontier, params=current,
                 steps=steps, param_changes=pc)


# =====================================================================
# Render
# =====================================================================

def _line_cells(x1, y1, x2, y2):
    cells = []
    dx = abs(x2 - x1); dy = -abs(y2 - y1)
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


def render_ascii(plant):
    px, py, pw, ph = plant.pot
    grid = [["." for _ in range(pw)] for _ in range(ph)]
    for (x1, y1, x2, y2) in plant.segments:
        for (x, y) in _line_cells(x1, y1, x2, y2):
            if px <= x < px + pw and py <= y < py + ph:
                grid[y - py][x - px] = "#"
    for (x, y, _d, _dep) in plant.frontier:
        if px <= x < px + pw and py <= y < py + ph:
            grid[y - py][x - px] = "*"
    return "\n".join("".join(r) for r in grid)


def render_svg(plant, size=400):
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
    for (x, y, _d, _dep) in plant.frontier:
        lines.append(
            f'<circle cx="{x}" cy="{y}" r="0.4" '
            f'fill="#f0a202"/>')
    lines.append("</svg>")
    return "\n".join(lines)
