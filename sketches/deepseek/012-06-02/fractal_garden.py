"""
fractal_garden.py — Composite world: a garden of plants.

A GardenWorld is a composite world. Its subworlds are atomic
fractal plants (fractal_world_v3.AtomicFractalWorld).

The garden's boundary is divided into slot_count slots (a
roughly-square grid). Each slot is a slot_width × slot_height
rectangle. Each slot holds at most one plant.

The garden's Law:
  1. At most one plant per slot.
  2. A plant's pot must equal its slot's rectangle.
  3. Each garden cycle, every plant advances up to
     steps_per_cycle steps.
  4. A plant cannot be added to an occupied slot.
  5. Retiring a plant leaves its slot empty (reusable).
  6. Garden parameters change only via branching
     (v3's protocol). Branching produces a fresh empty
     garden.

Composition:
  - The garden delegates plant growth to the plant. It
    records *how many steps* it drove each plant, but the
    plant's own log is the evidence of what happened.
  - Every garden record is signed by the garden's key.
  - Every plant_added record embeds the plant's seed so a
    verifier can check the plant's signature without the
    plant being present.

Dependencies: fractal_world_v3 (AtomicFractalWorld, helpers).

Simplifications (v0.2 notes):
  - Garden branch produces an empty garden (no plant
    inheritance). Full inheritance needs plant keeper keys
    held by the garden.
  - No garden-level world-keys for planting. Anyone can
    plant into an empty slot in this v0.1. A v0.2 would
    require a control-tier world-key.
  - No inter-plant interactions. The garden is a container,
    not yet an ecosystem.
"""

import math
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    from fractal_world_v3 import (
        AtomicFractalWorld, ParamSet,
        verify_world_log, verify_growth,
        reconstruct as reconstruct_plant,
        _canonical, _hash, _now, _did_from_kp, HAS_CRYPTO,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
except ImportError:
    HAS_CRYPTO = False


GARDEN_TEMPLATE_ID = "fractal-garden-v1"


# =====================================================================
# GardenTemplate
# =====================================================================

@dataclass(frozen=True)
class GardenTemplate:
    slot_count: int
    slot_width: int
    slot_height: int
    steps_per_cycle: int = 1

    def to_dict(self):
        return {
            "template_id": GARDEN_TEMPLATE_ID,
            "slot_count": self.slot_count,
            "slot_width": self.slot_width,
            "slot_height": self.slot_height,
            "steps_per_cycle": self.steps_per_cycle,
        }

    def template_hash(self):
        return _hash(self.to_dict())

    def grid(self):
        cols = max(1, math.ceil(math.sqrt(self.slot_count)))
        rows = max(1, math.ceil(self.slot_count / cols))
        return cols, rows

    def slot_rect(self, slot):
        if not (0 <= slot < self.slot_count):
            raise ValueError(f"slot {slot} out of range")
        cols, _ = self.grid()
        row = slot // cols
        col = slot % cols
        return (col * self.slot_width, row * self.slot_height,
                self.slot_width, self.slot_height)

    def initial_tip(self, slot):
        """Where a fresh plant in this slot starts."""
        x, y, w, h = self.slot_rect(slot)
        return (x + w // 2, y + h - 2, 0)

    def total_extent(self):
        cols, rows = self.grid()
        return (cols * self.slot_width,
                rows * self.slot_height)


# =====================================================================
# Garden records
# =====================================================================

@dataclass(frozen=True)
class GardenSeedRecord:
    world_id: str
    template_hash: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "garden_seed",
            "world_id": self.world_id,
            "template_hash": self.template_hash,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class PlantAddedRecord:
    world_id: str
    slot: int
    plant_cert: Dict
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "plant_added",
            "world_id": self.world_id,
            "slot": self.slot,
            "plant_cert": dict(self.plant_cert),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class PlantRetiredRecord:
    world_id: str
    slot: int
    plant_id: str
    reason: str
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "plant_retired",
            "world_id": self.world_id,
            "slot": self.slot,
            "plant_id": self.plant_id,
            "reason": self.reason,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class GardenCycleRecord:
    world_id: str
    cycle: int
    advances: List[Dict]
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "garden_cycle",
            "world_id": self.world_id,
            "cycle": self.cycle,
            "advances": [dict(a) for a in self.advances],
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# Plant certificate (what the garden embeds about a plant)
# =====================================================================

def plant_certificate(plant) -> Dict:
    """Extract the plant's birth certificate for embedding.

    Works for fresh AtomicFractalWorld instances (v3's seed type).
    Branch-seed plants are not used by this demo; supporting
    them here is a v0.2 concern.
    """
    body = plant.seed_body()
    return {
        "plant_id": plant.world_id,
        "seed_body": dict(body),
        "seed_sig": plant.seed_sig(),
    }


def _pubkey_from_did(did: str) -> "Ed25519PublicKey":
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


def verify_plant_certificate(cert: Dict) -> bool:
    try:
        pub = _pubkey_from_did(cert["plant_id"])
        pub.verify(bytes.fromhex(cert["seed_sig"]),
                   _canonical(cert["seed_body"]))
        return True
    except Exception:
        return False


# =====================================================================
# GardenWorld
# =====================================================================

class GardenWorld:
    def __init__(self, template: GardenTemplate, keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._template = template
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        seed_body = {
            "type": "garden_seed",
            "world_id": self._world_id,
            "template_hash": template.template_hash(),
            "ts": _now(),
        }
        self._seed = GardenSeedRecord(
            world_id=self._world_id,
            template_hash=template.template_hash(),
            ts=seed_body["ts"],
            sig=keypair.sign(_canonical(seed_body)).hex(),
        )
        self._records: List = []
        self._plants: Dict[int, AtomicFractalWorld] = {}
        self._cycle = 0
        self._last_hash: Optional[str] = None

    # -- Accessors -------------------------------------------

    @property
    def world_id(self):
        return self._world_id

    @property
    def template(self):
        return self._template

    def seed(self):
        return self._seed

    def records(self):
        return list(self._records)

    def plants(self):
        return dict(self._plants)

    def cycle(self):
        return self._cycle

    def last_hash(self):
        return self._last_hash

    def seed_hash(self):
        return self._seed.record_hash()

    # -- Planting --------------------------------------------

    def plant(self, slot: int, plant) -> Optional[PlantAddedRecord]:
        """Add a plant to an empty slot.

        Refuses if:
          - slot out of range
          - slot occupied
          - plant's pot != slot's rect
          - plant's certificate invalid
        """
        if not (0 <= slot < self._template.slot_count):
            return None
        if slot in self._plants:
            return None
        expected = self._template.slot_rect(slot)
        actual = tuple(plant.seed_body().get("pot", ()))
        if actual != expected:
            return None
        cert = plant_certificate(plant)
        if not verify_plant_certificate(cert):
            return None
        body = {
            "type": "plant_added",
            "world_id": self._world_id,
            "slot": slot,
            "plant_cert": cert,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = PlantAddedRecord(
            world_id=self._world_id,
            slot=slot,
            plant_cert=cert,
            prev=self._last_hash,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._plants[slot] = plant
        self._last_hash = rec.record_hash()
        return rec

    def retire(self, slot: int, reason: str
               ) -> Optional[PlantRetiredRecord]:
        if slot not in self._plants:
            return None
        plant = self._plants[slot]
        body = {
            "type": "plant_retired",
            "world_id": self._world_id,
            "slot": slot,
            "plant_id": plant.world_id,
            "reason": reason,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = PlantRetiredRecord(
            world_id=self._world_id,
            slot=slot,
            plant_id=plant.world_id,
            reason=reason,
            prev=self._last_hash,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        del self._plants[slot]
        self._last_hash = rec.record_hash()
        return rec

    # -- Growing ---------------------------------------------

    def grow(self) -> GardenCycleRecord:
        """One garden cycle: advance every plant."""
        advances = []
        steps_per = self._template.steps_per_cycle
        for slot in sorted(self._plants):
            plant = self._plants[slot]
            taken = 0
            for _ in range(steps_per):
                if plant.grow() is None:
                    break
                taken += 1
            advances.append({
                "slot": slot,
                "plant_id": plant.world_id,
                "steps": taken,
            })
        self._cycle += 1
        body = {
            "type": "garden_cycle",
            "world_id": self._world_id,
            "cycle": self._cycle,
            "advances": advances,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = GardenCycleRecord(
            world_id=self._world_id,
            cycle=self._cycle,
            advances=advances,
            prev=self._last_hash,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        return rec

    def grow_n(self, n):
        for _ in range(n):
            self.grow()


# =====================================================================
# Verification
# =====================================================================

def _verify_sig(world_id, body, sig):
    try:
        pub = _pubkey_from_did(world_id)
        pub.verify(bytes.fromhex(sig), _canonical(body))
        return True
    except Exception:
        return False


def verify_garden_log(garden: GardenWorld):
    """Verify the garden's own log. Returns (ok, reason).

    Checks:
      - seed signature
      - every record's signature
      - every record's prev chain
      - slot occupancy consistency (no double-planting)
      - every embedded plant certificate
      - cycle monotonicity
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = garden.seed()
    if seed.world_id != garden.world_id:
        return (False, "seed world_id mismatch")
    if not _verify_sig(seed.world_id,
                       seed.body(), seed.sig):
        return (False, "seed signature invalid")
    occupancy: Dict[int, str] = {}
    cycle = 0
    prev = None
    for i, rec in enumerate(garden.records()):
        if rec.world_id != garden.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(rec.world_id,
                           rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, PlantAddedRecord):
            if rec.slot in occupancy:
                return (False, f"record {i}: slot "
                               f"{rec.slot} already occupied")
            if not verify_plant_certificate(rec.plant_cert):
                return (False, f"record {i}: plant cert invalid")
            expected = garden.template.slot_rect(rec.slot)
            actual = tuple(rec.plant_cert["seed_body"].get("pot", ()))
            if actual != expected:
                return (False, f"record {i}: plant pot "
                               f"{actual} != slot {expected}")
            occupancy[rec.slot] = rec.plant_cert["plant_id"]
        elif isinstance(rec, PlantRetiredRecord):
            if occupancy.get(rec.slot) != rec.plant_id:
                return (False, f"record {i}: retirement "
                               f"mismatch")
            del occupancy[rec.slot]
        elif isinstance(rec, GardenCycleRecord):
            if rec.cycle != cycle + 1:
                return (False, f"record {i}: cycle "
                               f"{rec.cycle} not monotonic")
            cycle = rec.cycle
        else:
            return (False, f"record {i}: unknown record")
        prev = rec.record_hash()
    return (True, "garden log verifies")


def verify_garden_with_plants(garden: GardenWorld):
    """Verify the garden AND each plant's own log, AND
    cross-check step counts.

    The cross-check proves that the garden's claims about
    plant advances match the plants' own growth records.
    """
    ok, reason = verify_garden_log(garden)
    if not ok:
        return (False, reason)
    # Verify each plant's own log
    for slot, plant in garden.plants().items():
        v_log, r_log = verify_world_log(plant)
        if not v_log:
            return (False, f"slot {slot}: plant log "
                           f"invalid: {r_log}")
        v_grow, r_grow = verify_growth(plant)
        if not v_grow:
            return (False, f"slot {slot}: plant growth "
                           f"invalid: {r_grow}")
    # Cross-check: sum of steps_taken in garden cycles
    # equals number of growth records in each plant's log
    advances_by_plant: Dict[str, int] = {}
    for rec in garden.records():
        if isinstance(rec, GardenCycleRecord):
            for a in rec.advances:
                advances_by_plant[a["plant_id"]] = (
                    advances_by_plant.get(a["plant_id"], 0)
                    + a["steps"])
    for slot, plant in garden.plants().items():
        from fractal_world_v3 import GrowthRecord
        growth_count = sum(
            1 for r in plant.records()
            if isinstance(r, GrowthRecord))
        claimed = advances_by_plant.get(plant.world_id, 0)
        if growth_count != claimed:
            return (False, f"slot {slot}: plant has "
                           f"{growth_count} growth records "
                           f"but garden claims {claimed} steps")
    return (True, "garden + plants + cross-check verify")


# =====================================================================
# Rendering
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


def render_garden_ascii(garden: GardenWorld) -> str:
    template = garden.template
    cols, rows = template.grid()
    sw, sh = template.slot_width, template.slot_height
    H = rows * (sh + 1) + 1
    W = cols * (sw + 1) + 1
    grid = [[' ' for _ in range(W)] for _ in range(H)]
    # Borders
    for r in range(rows + 1):
        y = r * (sh + 1)
        for x in range(W):
            grid[y][x] = '-'
    for c in range(cols + 1):
        x = c * (sw + 1)
        for y in range(H):
            grid[y][x] = '|'
    for r in range(rows + 1):
        for c in range(cols + 1):
            grid[r * (sh + 1)][c * (sw + 1)] = '+'
    # Empty-slot fill
    for slot in range(template.slot_count):
        if slot in garden.plants():
            continue
        r, c = slot // cols, slot % cols
        sx, sy = c * (sw + 1) + 1, r * (sh + 1) + 1
        for ly in range(sh):
            for lx in range(sw):
                grid[sy + ly][sx + lx] = '·'
    # Plants
    for slot, plant in garden.plants().items():
        r, c = slot // cols, slot % cols
        sx, sy = c * (sw + 1) + 1, r * (sh + 1) + 1
        rect = template.slot_rect(slot)
        for (x1, y1, x2, y2) in plant.segments():
            for (x, y) in _line_cells(x1, y1, x2, y2):
                lx, ly = x - rect[0], y - rect[1]
                if 0 <= lx < sw and 0 <= ly < sh:
                    grid[sy + ly][sx + lx] = '#'
        for (x, y, _d, _dep) in plant.frontier():
            lx, ly = x - rect[0], y - rect[1]
            if 0 <= lx < sw and 0 <= ly < sh:
                grid[sy + ly][sx + lx] = '*'
    return "\n".join("".join(row) for row in grid)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None):
    """The garden lives through a planting, growth, retirement,
    and replanting cycle — all signed."""
    import json as _json
    from pathlib import Path
    from fractal_world_v3 import WorldTemplate

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "fractal_garden"
    path.mkdir(parents=True, exist_ok=True)

    garden_template = GardenTemplate(
        slot_count=4, slot_width=15, slot_height=15,
        steps_per_cycle=1)
    plant_template = WorldTemplate(
        template_id="fractal-plant-v1",
        branch_length=2, max_depth=4,
        water=10, light=10)

    keeper_kp = Ed25519PrivateKey.generate()
    garden = GardenWorld(garden_template, keeper_kp)

    def new_plant(slot):
        return AtomicFractalWorld(
            template=plant_template,
            pot=garden_template.slot_rect(slot),
            initial_tip=garden_template.initial_tip(slot),
            keypair=Ed25519PrivateKey.generate())

    # Plant three plants
    p0 = new_plant(0)
    p1 = new_plant(1)
    p2 = new_plant(2)
    garden.plant(0, p0)
    garden.plant(1, p1)
    garden.plant(2, p2)

    print("=" * 74)
    print("The Fractal Garden — a composite world with plants")
    print("=" * 74)
    print()
    print(f"  Garden:  {garden.world_id[:32]}...")
    print(f"  Grid:    2 x 2 slots (15x15 each, 30x30 total)")
    print(f"  Plants:  3 (slots 0, 1, 2)")
    print()

    print("  Before growth:")
    for line in render_garden_ascii(garden).split("\n"):
        print(f"    {line}")
    print()

    # Grow 4 cycles
    garden.grow_n(4)
    print("  After 4 cycles:")
    for line in render_garden_ascii(garden).split("\n"):
        print(f"    {line}")
    print()

    # Retire plant in slot 1
    garden.retire(1, "wilting")
    p3 = new_plant(1)
    garden.plant(1, p3)
    print("  Slot 1 retired; new plant in slot 1")
    print()

    # Grow 2 more cycles
    garden.grow_n(2)
    print("  After 2 more cycles:")
    for line in render_garden_ascii(garden).split("\n"):
        print(f"    {line}")
    print()

    # Verify
    v_log = verify_garden_log(garden)
    v_full = verify_garden_with_plants(garden)
    print("  Verification:")
    print(f"    garden log:             {v_log[0]}  "
          f"({v_log[1]})")
    print(f"    garden + plants + cross: {v_full[0]}  "
          f"({v_full[1]})")
    print()

    # Report per-plant
    for slot, plant in sorted(garden.plants().items()):
        growth_records = sum(
            1 for r in plant.records() if hasattr(r, "segs"))
        print(f"    slot {slot}: {plant.world_id[:24]}...  "
              f"growth records: {growth_records}  "
              f"segments: {len(plant.segments())}")
    print()

    print("  What this establishes:")
    print("    - The garden is a composite world. Each plant is")
    print("      a full atomic world with its own key, log, and")
    print("      params. The garden holds references, not state.")
    print("    - The garden's law governs placement (one per")
    print("      slot, correct pot) and cycle advancement. It")
    print("      does not validate plant growth — the plant's")
    print("      own verify_growth does that.")
    print("    - Every garden action is a signed record. The")
    print("      plant_added record embeds the plant's seed,")
    print("      so the garden's log is self-verifying about")
    print("      what was planted.")
    print("    - The cross-check proves the garden's claims")
    print("      about plant advances match each plant's own")
    print("      growth records exactly.")
    print("    - Retiring a plant leaves its slot empty; a new")
    print("      plant can be planted there. The old plant's log")
    print("      is unchanged; its history remains.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")

    audit = {
        "garden_id": garden.world_id,
        "slot_count": garden_template.slot_count,
        "cycle_count": garden.cycle(),
        "plants": {
            str(slot): {
                "plant_id": plant.world_id,
                "segments": len(plant.segments()),
                "records": len(plant.records()),
            }
            for slot, plant in garden.plants().items()
        },
        "retired_plant_id": p1.world_id,
        "garden_log_valid": v_log[0],
        "full_verification_valid": v_full[0],
    }
    (path / "fractal_garden_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/fractal_garden_demo.json")
    return audit
