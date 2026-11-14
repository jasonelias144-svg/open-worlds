"""
gallery_world.py — a composite world containing heterogeneous
subworlds.

Four kinds of world, one container:

  "atomic_fractal"  AtomicFractalWorld (fractal_world_v3)
  "fractal_grid"    FractalGridWorld    (fractal_grid_world)
  "chaos_game"      ChaosGameWorld      (chaos_game_world)
  "coupled_ca"      CoupledCAWorld      (coupled_ca_world)

Each is wrapped in a GalleryMember adapter exposing a uniform
interface: grow(), steps(), seed_body(), seed_sig(), verify_log(),
verify_growth(), render().

The gallery:
  - holds members by slot
  - grows every member once per cycle
  - embeds each member's seed certificate at add time
  - cross-checks: sum of steps_taken in the gallery's advances
    must equal the member's own step count

Design note (post-Rust review): the four member kinds share a
single seed-signature discipline — canonical JSON, Ed25519 over
it, did:key identifier — which is the same discipline as the
standard's eddsa-jcs-2022 record proof. That is the unification
point at which port to Rust is mechanical.
"""

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from fractal_world_v3 import (
    AtomicFractalWorld, WorldTemplate, GrowthRecord,
    verify_world_log,
    verify_growth as verify_fractal_growth,
    reconstruct as reconstruct_fractal,
    render_ascii as render_fractal_ascii,
)
from fractal_grid_world import (
    FractalGridWorld, GridParams, GridRowRecord,
    verify_log as verify_grid_log,
    verify_growth as verify_grid_growth,
    render_ascii as render_grid_ascii,
)
from chaos_game_world import (
    ChaosGameWorld, SIERPINSKI, ChaosStepRecord,
    verify_chaos_log, verify_chaos_growth,
    render_ascii as render_chaos_ascii,
)
from coupled_ca_world import (
    CoupledCAWorld, CoupledCAStepRecord,
    verify_coupled_ca_log, verify_coupled_ca_growth,
    render_combined as render_coupled_ca,
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj):
    return json.dumps(obj, sort_keys=True,
                      separators=(",", ":")).encode()


def _hash(obj):
    return hashlib.sha256(_canonical(obj)).hexdigest()


def _did_from_kp(kp):
    return "did:key:" + kp.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()


def _pubkey_from_did(did):
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


def _verify_sig(did, body, sig):
    try:
        _pubkey_from_did(did).verify(
            bytes.fromhex(sig), _canonical(body))
        return True
    except (InvalidSignature, KeyError, ValueError, Exception):
        return False


# =====================================================================
# Member adapters
# =====================================================================

class GalleryMember(ABC):
    kind: str = ""

    @abstractmethod
    def world_id(self) -> str: ...
    @abstractmethod
    def steps(self) -> int: ...
    @abstractmethod
    def grow(self) -> Optional[Dict]: ...
    @abstractmethod
    def seed_body(self) -> Dict: ...
    @abstractmethod
    def seed_sig(self) -> str: ...
    @abstractmethod
    def verify_log(self) -> Tuple[bool, str]: ...
    @abstractmethod
    def verify_growth(self) -> Tuple[bool, str]: ...
    @abstractmethod
    def render(self) -> str: ...


class AtomicFractalMember(GalleryMember):
    kind = "atomic_fractal"

    def __init__(self, world):
        self._world = world

    def world_id(self):
        return self._world.world_id

    def steps(self):
        return sum(1 for r in self._world.records()
                    if isinstance(r, GrowthRecord))

    def grow(self):
        rec = self._world.grow()
        if rec is None:
            return None
        return {"segments": len(rec.segs)}

    def seed_body(self):
        return self._world.seed_body()

    def seed_sig(self):
        return self._world.seed_sig()

    def verify_log(self):
        return verify_world_log(self._world)

    def verify_growth(self):
        return verify_fractal_growth(self._world)

    def render(self):
        return render_fractal_ascii(
            reconstruct_fractal(self._world))


class FractalGridMember(GalleryMember):
    kind = "fractal_grid"

    def __init__(self, world, max_gen=None):
        self._world = world
        self._max_gen = max_gen

    def world_id(self):
        return self._world.world_id

    def steps(self):
        return sum(1 for r in self._world.records()
                    if isinstance(r, GridRowRecord))

    def grow(self):
        if self._max_gen is not None and \
                self._world.gen() >= self._max_gen:
            return None
        rec = self._world.grow()
        if rec is None:
            return None
        return {"row_size": len(rec.row_x)}

    def seed_body(self):
        return self._world.seed_body()

    def seed_sig(self):
        return self._world.seed_sig()

    def verify_log(self):
        return verify_grid_log(self._world)

    def verify_growth(self):
        return verify_grid_growth(self._world)

    def render(self):
        return render_grid_ascii(self._world, flip=False)


class ChaosGameMember(GalleryMember):
    kind = "chaos_game"

    def __init__(self, world, max_steps=None):
        if world.growth_mode != "seeded_random":
            raise ValueError(
                "Gallery accepts only seeded_random chaos games")
        self._world = world
        self._max_steps = max_steps

    def world_id(self):
        return self._world.world_id

    def steps(self):
        return self._world.step()

    def grow(self):
        if self._max_steps is not None and \
                self._world.step() >= self._max_steps:
            return None
        rec = self._world.grow()
        if rec is None:
            return None
        return {"point": list(rec.point)}

    def seed_body(self):
        return self._world.seed_body()

    def seed_sig(self):
        return self._world.seed_sig()

    def verify_log(self):
        return verify_chaos_log(self._world)

    def verify_growth(self):
        return verify_chaos_growth(self._world)

    def render(self):
        return render_chaos_ascii(
            self._world, width=40, height=12)


class CoupledCAMember(GalleryMember):
    kind = "coupled_ca"

    def __init__(self, world, max_gen=None):
        self._world = world
        self._max_gen = max_gen

    def world_id(self):
        return self._world.world_id

    def steps(self):
        return self._world.gen()

    def grow(self):
        if self._max_gen is not None and \
                self._world.gen() >= self._max_gen:
            return None
        rec = self._world.grow()
        return {"overlap": rec.overlap_before}

    def seed_body(self):
        return self._world.seed_body()

    def seed_sig(self):
        return self._world.seed_sig()

    def verify_log(self):
        return verify_coupled_ca_log(self._world)

    def verify_growth(self):
        return verify_coupled_ca_growth(self._world)

    def render(self):
        return render_coupled_ca(self._world)


# =====================================================================
# Seed certificate verification (unified across all kinds)
# =====================================================================

def verify_seed_cert(cert: Dict) -> bool:
    try:
        pub = _pubkey_from_did(cert["world_id"])
        pub.verify(bytes.fromhex(cert["seed_sig"]),
                    _canonical(cert["seed_body"]))
        return True
    except Exception:
        return False


# =====================================================================
# Gallery records
# =====================================================================

@dataclass(frozen=True)
class GallerySeedRecord:
    world_id: str
    ts: str
    sig: str

    def body(self):
        return {"type": "gallery_seed",
                "world_id": self.world_id, "ts": self.ts}

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class GalleryMemberAddedRecord:
    world_id: str
    slot: int
    member_id: str
    member_kind: str
    seed_cert: Dict
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "gallery_member_added",
            "world_id": self.world_id,
            "slot": self.slot,
            "member_id": self.member_id,
            "member_kind": self.member_kind,
            "seed_cert": dict(self.seed_cert),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class GalleryCycleRecord:
    world_id: str
    cycle: int
    advances: Tuple[Dict, ...]
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "gallery_cycle",
            "world_id": self.world_id,
            "cycle": self.cycle,
            "advances": [dict(a) for a in self.advances],
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class GalleryMemberRetiredRecord:
    world_id: str
    slot: int
    member_id: str
    reason: str
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "gallery_member_retired",
            "world_id": self.world_id,
            "slot": self.slot,
            "member_id": self.member_id,
            "reason": self.reason,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# GalleryWorld
# =====================================================================

class GalleryWorld:
    def __init__(self, keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._members: Dict[int, GalleryMember] = {}
        self._records: List = []
        self._cycle = 0
        self._last_hash: Optional[str] = None
        seed_body = {"type": "gallery_seed",
                      "world_id": self._world_id, "ts": _now()}
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(
            _canonical(seed_body)).hex()

    @property
    def world_id(self):
        return self._world_id

    def cycle(self):
        return self._cycle

    def members(self):
        return dict(self._members)

    def records(self):
        return list(self._records)

    def seed_body(self):
        return dict(self._seed_body)

    def seed_sig(self):
        return self._seed_sig

    def last_hash(self):
        return self._last_hash

    def add(self, slot: int, member: GalleryMember
            ) -> Optional[GalleryMemberAddedRecord]:
        if slot in self._members:
            return None
        cert = {
            "kind": member.kind,
            "world_id": member.world_id(),
            "seed_body": member.seed_body(),
            "seed_sig": member.seed_sig(),
        }
        body = {
            "type": "gallery_member_added",
            "world_id": self._world_id,
            "slot": slot,
            "member_id": member.world_id(),
            "member_kind": member.kind,
            "seed_cert": cert,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = GalleryMemberAddedRecord(
            world_id=self._world_id, slot=slot,
            member_id=member.world_id(),
            member_kind=member.kind, seed_cert=cert,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._members[slot] = member
        self._last_hash = rec.record_hash()
        return rec

    def retire(self, slot: int, reason: str = ""
                ) -> Optional[GalleryMemberRetiredRecord]:
        if slot not in self._members:
            return None
        member = self._members[slot]
        body = {
            "type": "gallery_member_retired",
            "world_id": self._world_id,
            "slot": slot,
            "member_id": member.world_id(),
            "reason": reason,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = GalleryMemberRetiredRecord(
            world_id=self._world_id, slot=slot,
            member_id=member.world_id(), reason=reason,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        del self._members[slot]
        self._last_hash = rec.record_hash()
        return rec

    def grow(self):
        advances = []
        for slot in sorted(self._members):
            member = self._members[slot]
            result = member.grow()
            steps_taken = 0 if result is None else 1
            advances.append({
                "slot": slot,
                "member_id": member.world_id(),
                "member_kind": member.kind,
                "steps_taken": steps_taken,
                "info": result or {},
            })
        self._cycle += 1
        body = {
            "type": "gallery_cycle",
            "world_id": self._world_id,
            "cycle": self._cycle,
            "advances": advances,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = GalleryCycleRecord(
            world_id=self._world_id, cycle=self._cycle,
            advances=tuple(advances), prev=self._last_hash,
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

def verify_gallery_log(gallery):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = gallery.seed_body()
    if not _verify_sig(gallery.world_id, seed,
                        gallery.seed_sig()):
        return (False, "seed signature invalid")
    prev = None
    occupied: Dict[int, str] = {}
    cycle = 0
    for i, rec in enumerate(gallery.records()):
        if rec.world_id != gallery.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(gallery.world_id,
                            rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, GalleryMemberAddedRecord):
            if rec.slot in occupied:
                return (False,
                         f"record {i}: slot {rec.slot} occupied")
            if not verify_seed_cert(rec.seed_cert):
                return (False,
                         f"record {i}: seed cert invalid")
            if rec.seed_cert["world_id"] != rec.member_id:
                return (False,
                         f"record {i}: cert/member mismatch")
            if rec.seed_cert["kind"] != rec.member_kind:
                return (False,
                         f"record {i}: cert kind mismatch")
            occupied[rec.slot] = rec.member_id
        elif isinstance(rec, GalleryMemberRetiredRecord):
            if occupied.get(rec.slot) != rec.member_id:
                return (False,
                         f"record {i}: retirement mismatch")
            del occupied[rec.slot]
        elif isinstance(rec, GalleryCycleRecord):
            if rec.cycle != cycle + 1:
                return (False,
                         f"record {i}: cycle not monotonic")
            cycle = rec.cycle
            mentioned = {a["slot"] for a in rec.advances}
            if mentioned != set(occupied.keys()):
                return (False,
                         f"record {i}: advances do not match "
                         f"occupied slots")
            for adv in rec.advances:
                if occupied.get(adv["slot"]) != adv["member_id"]:
                    return (False,
                             f"record {i}: advance/member "
                             f"mismatch")
        else:
            return (False, f"record {i}: unknown type")
        prev = rec.record_hash()
    return (True, "gallery log verifies")


def verify_gallery_members(gallery):
    """Verify every currently held member's own log and growth,
    plus the cross-check that the gallery's claimed advances
    match each member's own step count."""
    claimed: Dict[str, int] = {}
    for rec in gallery.records():
        if isinstance(rec, GalleryCycleRecord):
            for adv in rec.advances:
                claimed[adv["member_id"]] = (
                    claimed.get(adv["member_id"], 0)
                    + adv["steps_taken"])
    for slot, member in gallery.members().items():
        vlog = member.verify_log()
        if not vlog[0]:
            return (False,
                     f"slot {slot} ({member.kind}): "
                     f"log: {vlog[1]}")
        vgrow = member.verify_growth()
        if not vgrow[0]:
            return (False,
                     f"slot {slot} ({member.kind}): "
                     f"growth: {vgrow[1]}")
        claim = claimed.get(member.world_id(), 0)
        actual = member.steps()
        if claim != actual:
            return (False,
                     f"slot {slot} ({member.kind}): "
                     f"gallery claims {claim} steps, "
                     f"member has {actual}")
    return (True, "all members verify + cross-check passes")


def verify_full(gallery):
    v = verify_gallery_log(gallery)
    if not v[0]:
        return (False, f"gallery log: {v[1]}")
    v = verify_gallery_members(gallery)
    if not v[0]:
        return (False, f"members: {v[1]}")
    return (True, "full verification passes")


# =====================================================================
# Rendering
# =====================================================================

def render_gallery(gallery) -> str:
    if not gallery.members():
        return "(empty gallery)"
    lines = []
    for slot in sorted(gallery.members()):
        member = gallery.members()[slot]
        lines.append(f"  slot {slot}: {member.kind}  "
                      f"steps={member.steps()}")
        for line in member.render().split("\n"):
            lines.append(f"    {line}")
        lines.append("")
    return "\n".join(lines)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None):
    from pathlib import Path
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "gallery"
    path.mkdir(parents=True, exist_ok=True)

    keeper_kp = Ed25519PrivateKey.generate()
    gallery = GalleryWorld(keeper_kp)

    # Slot 0: fractal plant
    plant = AtomicFractalWorld(
        template=WorldTemplate(
            template_id="gallery-plant-v1",
            branch_length=2, max_depth=3),
        pot=(0, 0, 15, 15),
        initial_tip=(7, 13, 0),
        keypair=Ed25519PrivateKey.generate())
    gallery.add(0, AtomicFractalMember(plant))

    # Slot 1: grid Sierpinski
    grid_world = FractalGridWorld(
        params=GridParams(rule_number=90, max_gen=12),
        initial_row=[0],
        keypair=Ed25519PrivateKey.generate())
    gallery.add(1, FractalGridMember(grid_world, max_gen=12))

    # Slot 2: chaos game Sierpinski
    chaos = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="seeded_random",
        initial_point=(500, 500),
        keypair=Ed25519PrivateKey.generate(),
        prng_seed=0xBEEFCAFE)
    gallery.add(2, ChaosGameMember(chaos, max_steps=40))

    # Slot 3: coupled CAs (rule 90, offset 20, k=50/50)
    coupled = CoupledCAWorld(
        rule_a=90, rule_b=90,
        initial_a=[0], initial_b=[20],
        k_a=50, k_b=50,
        keypair=Ed25519PrivateKey.generate())
    gallery.add(3, CoupledCAMember(coupled, max_gen=15))

    gallery.grow_n(20)

    v_log = verify_gallery_log(gallery)
    v_mem = verify_gallery_members(gallery)
    v_full = verify_full(gallery)

    print("=" * 74)
    print("The Gallery — four kinds of subworlds, one composite")
    print("=" * 74)
    print()
    print(f"  Gallery: {gallery.world_id[:32]}...")
    print(f"  Cycles:  {gallery.cycle()}")
    print(f"  Members: {len(gallery.members())}")
    print()
    print("  Verification:")
    print(f"    gallery log:    {v_log[0]}  ({v_log[1]})")
    print(f"    members:        {v_mem[0]}  ({v_mem[1]})")
    print(f"    full:           {v_full[0]}  ({v_full[1]})")
    print()
    print("  The gallery:")
    print(render_gallery(gallery))
    print("  What this establishes:")
    print("    - Four kinds of worlds coexist in one composite.")
    print("      The gallery doesn't know what each does — only")
    print("      that it exposes grow(), steps(), and a")
    print("      verifiable seed cert.")
    print("    - Each member's own log is the evidence. The")
    print("      gallery embeds each member's seed cert at add")
    print("      time, so a third party can check authenticity")
    print("      without the member being present.")
    print("    - The cross-check proves the gallery drove each")
    print("      member exactly as many times as the member's")
    print("      own log says. Sum of steps_taken == member's")
    print("      own step count.")
    print("    - No shared coordinate space. The plant lives")
    print("      in 2D Cartesian; the grid in (x, gen); the")
    print("      chaos game in scaled-integer 2D; the CA in")
    print("      1D. The gallery reports each member's view as")
    print("      its own thing.")
    print("    - This is what 'any world in any world' means")
    print("      concretely: the protocol is what the worlds")
    print("      share; not their geometry.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")
    print("    'More numerous of Windows –'")
    print("    'Superior – for Doors –'")

    audit = {
        "gallery_id": gallery.world_id,
        "cycles": gallery.cycle(),
        "members": [
            {"slot": slot,
             "kind": gallery.members()[slot].kind,
             "member_id": gallery.members()[slot].world_id(),
             "steps": gallery.members()[slot].steps()}
            for slot in sorted(gallery.members())
        ],
        "verify_gallery_log": v_log[0],
        "verify_gallery_members": v_mem[0],
        "verify_full": v_full[0],
    }
    (path / "gallery_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/gallery_demo.json")
    return audit
