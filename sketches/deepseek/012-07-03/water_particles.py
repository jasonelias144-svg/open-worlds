"""
water_particles.py — Water as particles in the endless plant's world.

Proposal sketch for FRACTALS.md stage 3 (water). Not a course step.

Design summary:

  - The state is an integer level array W[x][y] in [0, W_MAX].
    One unit of level = one particle. Particles are
    indistinguishable for physics; the level array is the state.
  - Each tick is a fixed pipeline: rain, fall, soak, flow,
    evaporate. Fixed order => verifiable by replay.
  - Each tick is one signed WaterTick record. The record carries
    the delta and the resulting level_hash; a verifier can check
    the hash directly or replay the rules.

Simplifications marked for the standard's review:

  - `sig` is a flat field, not a W3C DataIntegrityProof object.
    The real implementation must use the proof format from
    schemas/records-v1.schema.json.
  - Key names in body() should be checked against the schema
    before merging.
  - Flow is a single ordered sweep with a per-tick lock, not a
    full cellular automaton iterating to convergence. One cell
    of sideways motion per particle per tick.
  - Evaporation is per cell, gated by a hash. Not per particle.
  - Soaking and drinking are combined: a root cell absorbs and
    the plant gains energy. A two-stage model (soil water →
    plant water → energy) is a future refinement.
  - No wind, no temperature, no shade. The plant does not yet
    feed back into water (transpiration, leaf drip).
  - The moves list makes the record O(particles moved). If log
    size becomes a concern, moves can be elided and the verifier
    can re-derive them from the rules (the level_hash still
    anchors the result).
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

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


def _hash_int(*parts) -> int:
    """Deterministic integer in [0, 256) from any parts."""
    return hashlib.sha256(_canonical(list(parts))).digest()[0]


def _did_from_kp(kp) -> str:
    return "did:key:" + kp.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()


def _pubkey_from_did(did) -> "Ed25519PublicKey":
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


# =====================================================================
# Constants
# =====================================================================

W_MAX     = 8     # max water units per cell
SOAK_RATE = 1     # units soaked per root cell per tick
EVAP_RATE = 24    # out of 256; ~9% of exposed cells lose 1 unit/tick
RAIN_RATE = 64    # out of 256; ~25% of top cells gain 1 unit/tick


# =====================================================================
# WaterGrid — integer levels, [x][y], y=0 top, y=H-2 bottom fluid row
# =====================================================================

@dataclass
class WaterGrid:
    width: int
    height: int
    levels: List[List[int]]

    @classmethod
    def empty(cls, width: int, height: int) -> "WaterGrid":
        return cls(width=width, height=height,
                   levels=[[0] * (height - 1) for _ in range(width)])

    def get(self, x: int, y: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height - 1):
            return 0
        return self.levels[x][y]

    def set(self, x: int, y: int, v: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height - 1:
            self.levels[x][y] = max(0, min(W_MAX, v))

    def add(self, x: int, y: int, n: int) -> int:
        cur = self.get(x, y)
        placed = min(W_MAX - cur, n)
        if placed > 0:
            self.set(x, y, cur + placed)
        return placed

    def remove(self, x: int, y: int, n: int) -> int:
        cur = self.get(x, y)
        taken = min(cur, n)
        if taken > 0:
            self.set(x, y, cur - taken)
        return taken

    def is_ground(self, y: int) -> bool:
        return y >= self.height - 1


# =====================================================================
# Rules
# =====================================================================

def _rain_columns(world_id: str, t: int, width: int) -> List[Tuple[int, int]]:
    return [(x, 1) for x in range(width)
            if _hash_int(world_id, "rain", x, t) < RAIN_RATE]


def _fall(grid: WaterGrid, world_id: str, t: int) -> List[Tuple[int, int, int, int, int]]:
    moves = []
    for y in range(grid.height - 2, -1, -1):  # bottom-up
        for x in range(grid.width):
            n = grid.get(x, y)
            if n == 0:
                continue
            below_y = y + 1
            if grid.is_ground(below_y) or grid.get(x, below_y) >= W_MAX:
                continue
            moved = grid.remove(x, y, min(n, W_MAX - grid.get(x, below_y)))
            if moved > 0:
                grid.add(x, below_y, moved)
                moves.append((x, y, 0, 1, moved))
    return moves


def _soak(grid: WaterGrid, roots: List[Tuple[int, int]],
          energy_remaining: int) -> Tuple[List[Tuple[int, int, int]], int]:
    soak, gained = [], 0
    if energy_remaining <= 0:
        return soak, gained
    for (rx, ry) in roots:
        if gained >= energy_remaining:
            break
        take = grid.remove(rx, ry,
                            min(grid.get(rx, ry), SOAK_RATE,
                                energy_remaining - gained))
        if take > 0:
            soak.append((rx, ry, take))
            gained += take
    return soak, gained


def _flow(grid: WaterGrid, world_id: str, t: int) -> List[Tuple[int, int, int, int, int]]:
    moves = []
    locked = [[False] * (grid.height - 1) for _ in range(grid.width)]
    for y in range(grid.height - 2, -1, -1):
        for x in range(grid.width):
            if locked[x][y] or grid.get(x, y) == 0:
                continue
            below_y = y + 1
            if not grid.is_ground(below_y) and grid.get(x, below_y) < W_MAX:
                continue  # can still fall; fall sweep handled it
            order = (-1, 1) if _hash_int(world_id, "flow", x, y, t) % 2 == 0 else (1, -1)
            for dx in order:
                nx = x + dx
                if not (0 <= nx < grid.width) or locked[nx][y]:
                    continue
                if grid.get(nx, y) >= W_MAX:
                    continue
                moved = grid.remove(x, y,
                                    min(grid.get(x, y), W_MAX - grid.get(nx, y)))
                if moved > 0:
                    grid.add(nx, y, moved)
                    moves.append((x, y, dx, 0, moved))
                    locked[nx][y] = True
                    break
    return moves


def _evaporate(grid: WaterGrid, world_id: str, t: int) -> List[Tuple[int, int, int]]:
    evap = []
    for y in range(grid.height - 1):
        for x in range(grid.width):
            if grid.get(x, y) == 0:
                continue
            if y > 0 and grid.get(x, y - 1) > 0:
                continue  # not exposed
            if _hash_int(world_id, "evap", x, y, t) < EVAP_RATE:
                if grid.remove(x, y, 1) > 0:
                    evap.append((x, y, 1))
    return evap


# =====================================================================
# WaterTick record
# =====================================================================

@dataclass(frozen=True)
class WaterTick:
    world_id: str
    step: int
    t: int
    prev: Optional[str]
    rain: List[Tuple[int, int, int]]
    moves: List[Tuple[int, int, int, int, int]]
    soak: List[Tuple[int, int, int]]
    evap: List[Tuple[int, int, int]]
    level_hash: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "water_tick",
            "world_id": self.world_id,
            "step": self.step,
            "t": self.t,
            "prev": self.prev,
            "rain": [list(r) for r in self.rain],
            "moves": [list(m) for m in self.moves],
            "soak": [list(s) for s in self.soak],
            "evap": [list(e) for e in self.evap],
            "level_hash": self.level_hash,
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


# =====================================================================
# WaterWorld
# =====================================================================

class WaterWorld:
    def __init__(self, width: int, height: int,
                 roots: List[Tuple[int, int]],
                 energy_cap: int, keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        if height < 2 or width < 1:
            raise ValueError("world must be at least 1x2")
        self._width = width
        self._height = height
        self._roots = list(roots)
        self._energy_cap = energy_cap
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._grid = WaterGrid.empty(width, height)
        self._records: List[WaterTick] = []
        self._energy = 0
        self._last_hash: Optional[str] = None
        body = {
            "type": "water_seed",
            "world_id": self._world_id,
            "width": width,
            "height": height,
            "roots": [list(r) for r in self._roots],
            "energy_cap": energy_cap,
            "ts": _now(),
        }
        self._seed = {**body, "sig": keypair.sign(_canonical(body)).hex()}

    @property
    def world_id(self) -> str:
        return self._world_id

    @property
    def grid(self) -> WaterGrid:
        return self._grid

    @property
    def energy(self) -> int:
        return self._energy

    def records(self) -> List[WaterTick]:
        return list(self._records)

    def seed(self) -> Dict:
        return dict(self._seed)

    def seed_hash(self) -> str:
        body = {k: v for k, v in self._seed.items() if k != "sig"}
        return _hash(body)

    def tick(self) -> WaterTick:
        t = len(self._records)
        rain = []
        for (x, n) in _rain_columns(self._world_id, t, self._width):
            if self._grid.add(x, 0, n) > 0:
                rain.append((x, 0, n))
        moves = _fall(self._grid, self._world_id, t)
        soak, gained = _soak(self._grid, self._roots,
                              self._energy_cap - self._energy)
        self._energy += gained
        moves += _flow(self._grid, self._world_id, t)
        evap = _evaporate(self._grid, self._world_id, t)
        body = {
            "type": "water_tick",
            "world_id": self._world_id,
            "step": t,
            "t": t,
            "prev": self._last_hash,
            "rain": [list(r) for r in rain],
            "moves": [list(m) for m in moves],
            "soak": [list(s) for s in soak],
            "evap": [list(e) for e in evap],
            "level_hash": _hash(self._grid.levels),
            "ts": _now(),
        }
        rec = WaterTick(
            world_id=self._world_id, step=t, t=t,
            prev=self._last_hash,
            rain=rain, moves=moves, soak=soak, evap=evap,
            level_hash=body["level_hash"],
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex())
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        return rec

    def run(self, ticks: int = 100) -> int:
        for _ in range(ticks):
            self.tick()
        return ticks


# =====================================================================
# Verification
# =====================================================================

def verify_water_log(world: WaterWorld) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = world.seed()
    seed_body = {k: v for k, v in seed.items() if k != "sig"}
    try:
        _pubkey_from_did(world.world_id).verify(
            bytes.fromhex(seed["sig"]), _canonical(seed_body))
    except Exception as e:
        return (False, f"seed signature invalid: {e}")
    pub = _pubkey_from_did(world.world_id)
    prev = None
    for i, rec in enumerate(world.records()):
        if rec.world_id != world.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        try:
            pub.verify(bytes.fromhex(rec.sig), _canonical(rec.body()))
        except Exception as e:
            return (False, f"record {i}: signature invalid: {e}")
        prev = rec.record_hash()
    return (True, "log verifies")


def verify_water_replay(world: WaterWorld) -> Tuple[bool, str]:
    """Replay the rules from seed + records. Catches tampering
    that keeps signatures valid (re-signed wrong state)."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    ok, reason = verify_water_log(world)
    if not ok:
        return (False, reason)
    seed = world.seed()
    grid = WaterGrid.empty(seed["width"], seed["height"])
    roots = [tuple(r) for r in seed["roots"]]
    energy = 0
    cap = seed["energy_cap"]
    for i, rec in enumerate(world.records()):
        for (x, y, n) in rec.rain:
            grid.add(x, y, n)
        _fall(grid, world.world_id, rec.t)
        exp_soak, gained = _soak(grid, roots, cap - energy)
        energy += gained
        if sorted(rec.soak) != sorted(exp_soak):
            return (False, f"record {i}: soak mismatch")
        _flow(grid, world.world_id, rec.t)
        exp_evap = _evaporate(grid, world.world_id, rec.t)
        if sorted(rec.evap) != sorted(exp_evap):
            return (False, f"record {i}: evap mismatch")
        if _hash(grid.levels) != rec.level_hash:
            return (False, f"record {i}: level_hash mismatch")
    if energy != world.energy:
        return (False, f"energy mismatch: replay={energy}, "
                       f"world={world.energy}")
    return (True, "replay verifies")


# =====================================================================
# Render
# =====================================================================

def render_ascii(world: WaterWorld) -> str:
    out = []
    for y in range(world.grid.height - 1):
        row = []
        for x in range(world.grid.width):
            v = world.grid.get(x, y)
            row.append("." if v == 0 else
                       ("W" if v >= W_MAX else str(v)))
        out.append("".join(row))
    out.append("=" * world.grid.width)
    return "\n".join(out)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    """Rain on a flat pot. Water falls, pools, soaks the root,
    evaporates. Verify the whole log offline. Render at a few
    ticks so the progression is visible."""
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "water_particles"
    path.mkdir(parents=True, exist_ok=True)

    w = WaterWorld(
        width=20, height=10,
        roots=[(10, 8)], energy_cap=50,
        keypair=Ed25519PrivateKey.generate())

    snapshots = {}
    for i in range(60):
        w.tick()
        if i + 1 in (10, 30, 60):
            snapshots[i + 1] = render_ascii(w)

    ok_log, log_r = verify_water_log(w)
    ok_replay, replay_r = verify_water_replay(w)

    print("=" * 74)
    print("Water as particles — rain, pool, soak, evaporate")
    print("=" * 74)
    print()
    for t in sorted(snapshots):
        print(f"  tick {t}:")
        for line in snapshots[t].split("\n"):
            print(f"    {line}")
        print()
    print(f"  energy: {w.energy}/{w._energy_cap}  "
          f"records: {len(w.records())}")
    print(f"  log:    {ok_log}  ({log_r})")
    print(f"  replay: {ok_replay}  ({replay_r})")
    print()
    print("  What this establishes:")
    print("    - Water falls one cell per tick, pools at the bottom.")
    print("    - The root cell soaks; the plant's energy rises,")
    print("      capped by the energy cap.")
    print("    - Exposed water evaporates by a hash gate; the log")
    print("      records each loss.")
    print("    - The whole log verifies offline, and a full replay")
    print("      from seed + records reproduces every level_hash.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")

    audit = {
        "world_id": w.world_id,
        "energy": w.energy,
        "records": len(w.records()),
        "log_valid": ok_log,
        "replay_valid": ok_replay,
        "final_level_hash": w.records()[-1].level_hash,
        "snapshots": {str(k): v for k, v in snapshots.items()},
    }
    (path / "water_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/water_demo.json")
    return audit
