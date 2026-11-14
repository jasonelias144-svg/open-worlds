"""
coupled_ca_world.py — two elementary CAs in shared space.

Two fractal CAs (default rule 90) grow in a common 1D coordinate
space, offset from each other. When their extents meet, the
coupling parameter k governs what happens: overlap cells are
removed before rule application (if k is active), or kept (if not).

Design note (post-Rust review):
  This sketch is Python-first for design fluidity. When porting to
  Rust, the following will need to change to satisfy the standard:
    1. Signatures are hex here; standard uses base58 (Multikey) and
       W3C DataIntegrity proofs.
    2. Records are bespoke; standard uses records-v1.schema.json.
    3. 1D coordinates are i32 here; ur-world Cell is i64 3D.
    4. No HPKE sealing; no world-key tiers.
  None of these affect the design; they are mechanical at port time.

Composition: same discipline as other atomic worlds (signed seed,
signed chain, offline verification). No new primitives.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, FrozenSet, List, Optional

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from elementary_ca_world import step, expected_rule90_cells


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


def _active_at(step_n, which, k):
    """k=0 → never; k=100 → always; else hash(step, which, k) % 100 < k."""
    if k <= 0:
        return False
    if k >= 100:
        return True
    data = f"{step_n}|{which}|{k}".encode()
    h = hashlib.sha256(data).digest()
    return int.from_bytes(h[:4], 'big') % 100 < k


@dataclass(frozen=True)
class CoupledCASeedRecord:
    world_id: str
    subworld_a_id: str
    subworld_b_id: str
    rule_a: int
    rule_b: int
    k_a: int
    k_b: int
    initial_a: List[int]
    initial_b: List[int]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "coupled_ca_seed",
            "world_id": self.world_id,
            "subworld_a_id": self.subworld_a_id,
            "subworld_b_id": self.subworld_b_id,
            "rule_a": self.rule_a,
            "rule_b": self.rule_b,
            "k_a": self.k_a,
            "k_b": self.k_b,
            "initial_a": sorted(self.initial_a),
            "initial_b": sorted(self.initial_b),
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class CoupledCAStepRecord:
    world_id: str
    gen: int
    prev: Optional[str]
    rule_a: int
    rule_b: int
    k_a: int
    k_b: int
    cells_a_after: List[int]
    cells_b_after: List[int]
    overlap_before: int
    active_a: bool
    active_b: bool
    ts: str
    sig: str

    def body(self):
        return {
            "type": "coupled_ca_step",
            "world_id": self.world_id,
            "gen": self.gen,
            "prev": self.prev,
            "rule_a": self.rule_a,
            "rule_b": self.rule_b,
            "k_a": self.k_a,
            "k_b": self.k_b,
            "cells_a_after": sorted(self.cells_a_after),
            "cells_b_after": sorted(self.cells_b_after),
            "overlap_before": self.overlap_before,
            "active_a": self.active_a,
            "active_b": self.active_b,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class CouplingChangeRecord:
    world_id: str
    gen: int
    prev: Optional[str]
    k_a_old: int
    k_a_new: int
    k_b_old: int
    k_b_new: int
    ts: str
    sig: str

    def body(self):
        return {
            "type": "coupling_change",
            "world_id": self.world_id,
            "gen": self.gen,
            "prev": self.prev,
            "k_a_old": self.k_a_old,
            "k_a_new": self.k_a_new,
            "k_b_old": self.k_b_old,
            "k_b_new": self.k_b_new,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


class CoupledCAWorld:
    def __init__(self, rule_a, rule_b, initial_a, initial_b,
                 k_a=0, k_b=0, keypair=None):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        if not (0 <= int(rule_a) <= 255):
            raise ValueError("rule_a must be [0,255]")
        if not (0 <= int(rule_b) <= 255):
            raise ValueError("rule_b must be [0,255]")
        if not (0 <= int(k_a) <= 100):
            raise ValueError("k_a must be [0,100]")
        if not (0 <= int(k_b) <= 100):
            raise ValueError("k_b must be [0,100]")
        if keypair is None:
            keypair = Ed25519PrivateKey.generate()
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._sub_a_kp = Ed25519PrivateKey.generate()
        self._sub_b_kp = Ed25519PrivateKey.generate()
        self._rule_a = int(rule_a)
        self._rule_b = int(rule_b)
        self._k_a = int(k_a)
        self._k_b = int(k_b)
        self._cells_a = frozenset(int(x) for x in initial_a)
        self._cells_b = frozenset(int(x) for x in initial_b)
        self._gen = 0
        self._records = []
        self._last_hash = None
        seed_body = {
            "type": "coupled_ca_seed",
            "world_id": self._world_id,
            "subworld_a_id": _did_from_kp(self._sub_a_kp),
            "subworld_b_id": _did_from_kp(self._sub_b_kp),
            "rule_a": self._rule_a,
            "rule_b": self._rule_b,
            "k_a": self._k_a,
            "k_b": self._k_b,
            "initial_a": sorted(self._cells_a),
            "initial_b": sorted(self._cells_b),
            "ts": _now(),
        }
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(
            _canonical(seed_body)).hex()

    @property
    def world_id(self):
        return self._world_id

    def gen(self): return self._gen
    def rule_a(self): return self._rule_a
    def rule_b(self): return self._rule_b
    def k_a(self): return self._k_a
    def k_b(self): return self._k_b
    def cells_a(self): return self._cells_a
    def cells_b(self): return self._cells_b
    def records(self): return list(self._records)
    def seed_body(self): return dict(self._seed_body)
    def seed_sig(self): return self._seed_sig
    def seed_hash(self): return _hash(self._seed_body)
    def last_hash(self): return self._last_hash

    def grow(self):
        step_n = self._gen
        overlap = self._cells_a & self._cells_b
        active_a = _active_at(step_n, "A", self._k_a)
        active_b = _active_at(step_n, "B", self._k_b)
        eff_a = self._cells_a - overlap if active_a else self._cells_a
        eff_b = self._cells_b - overlap if active_b else self._cells_b
        next_a = step(eff_a, self._rule_a)
        next_b = step(eff_b, self._rule_b)
        new_gen = step_n + 1
        body = {
            "type": "coupled_ca_step",
            "world_id": self._world_id,
            "gen": new_gen,
            "prev": self._last_hash,
            "rule_a": self._rule_a,
            "rule_b": self._rule_b,
            "k_a": self._k_a,
            "k_b": self._k_b,
            "cells_a_after": sorted(next_a),
            "cells_b_after": sorted(next_b),
            "overlap_before": len(overlap),
            "active_a": active_a,
            "active_b": active_b,
            "ts": _now(),
        }
        rec = CoupledCAStepRecord(
            world_id=self._world_id, gen=new_gen,
            prev=self._last_hash,
            rule_a=self._rule_a, rule_b=self._rule_b,
            k_a=self._k_a, k_b=self._k_b,
            cells_a_after=sorted(next_a),
            cells_b_after=sorted(next_b),
            overlap_before=len(overlap),
            active_a=active_a, active_b=active_b,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._cells_a = next_a
        self._cells_b = next_b
        self._gen = new_gen
        self._last_hash = rec.record_hash()
        return rec

    def grow_n(self, n):
        for _ in range(n):
            self.grow()

    def set_coupling(self, k_a=None, k_b=None):
        new_a = self._k_a if k_a is None else int(k_a)
        new_b = self._k_b if k_b is None else int(k_b)
        if not (0 <= new_a <= 100) or not (0 <= new_b <= 100):
            raise ValueError("k must be [0,100]")
        body = {
            "type": "coupling_change",
            "world_id": self._world_id,
            "gen": self._gen,
            "prev": self._last_hash,
            "k_a_old": self._k_a, "k_a_new": new_a,
            "k_b_old": self._k_b, "k_b_new": new_b,
            "ts": _now(),
        }
        rec = CouplingChangeRecord(
            world_id=self._world_id, gen=self._gen,
            prev=self._last_hash,
            k_a_old=self._k_a, k_a_new=new_a,
            k_b_old=self._k_b, k_b_new=new_b,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._k_a = new_a
        self._k_b = new_b
        self._last_hash = rec.record_hash()
        return rec


def _verify_sig(did, body, sig):
    try:
        _pubkey_from_did(did).verify(
            bytes.fromhex(sig), _canonical(body))
        return True
    except Exception:
        return False


def verify_coupled_ca_log(world):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = world.seed_body()
    if not _verify_sig(world.world_id, seed, world.seed_sig()):
        return (False, "seed signature invalid")
    prev = None
    prev_gen = 0
    k_a = seed["k_a"]
    k_b = seed["k_b"]
    for i, rec in enumerate(world.records()):
        if rec.world_id != world.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(world.world_id, rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, CoupledCAStepRecord):
            if rec.gen != prev_gen + 1:
                return (False, f"record {i}: gen not monotonic")
            if rec.k_a != k_a or rec.k_b != k_b:
                return (False, f"record {i}: k mismatch")
            prev_gen = rec.gen
        elif isinstance(rec, CouplingChangeRecord):
            if rec.gen != prev_gen:
                return (False, f"record {i}: change at wrong gen")
            if rec.k_a_old != k_a or rec.k_b_old != k_b:
                return (False, f"record {i}: old k mismatch")
            k_a = rec.k_a_new
            k_b = rec.k_b_new
        else:
            return (False, f"record {i}: unknown type")
        prev = rec.record_hash()
    return (True, "coupled CA log verifies")


def verify_coupled_ca_growth(world):
    ok, reason = verify_coupled_ca_log(world)
    if not ok:
        return (False, reason)
    seed = world.seed_body()
    A = frozenset(int(x) for x in seed["initial_a"])
    B = frozenset(int(x) for x in seed["initial_b"])
    rule_a = seed["rule_a"]
    rule_b = seed["rule_b"]
    k_a = seed["k_a"]
    k_b = seed["k_b"]
    gen = 0
    for i, rec in enumerate(world.records()):
        if isinstance(rec, CouplingChangeRecord):
            k_a = rec.k_a_new
            k_b = rec.k_b_new
            continue
        if not isinstance(rec, CoupledCAStepRecord):
            continue
        if rec.gen != gen + 1:
            return (False, f"record {i}: gen skip")
        if rec.rule_a != rule_a or rec.rule_b != rule_b:
            return (False, f"record {i}: rule mismatch")
        if rec.k_a != k_a or rec.k_b != k_b:
            return (False, f"record {i}: k mismatch")
        overlap = A & B
        active_a = _active_at(gen, "A", k_a)
        active_b = _active_at(gen, "B", k_b)
        if rec.overlap_before != len(overlap):
            return (False, f"record {i}: overlap mismatch")
        if rec.active_a != active_a:
            return (False, f"record {i}: active_a mismatch")
        if rec.active_b != active_b:
            return (False, f"record {i}: active_b mismatch")
        eff_a = A - overlap if active_a else A
        eff_b = B - overlap if active_b else B
        exp_a = step(eff_a, rule_a)
        exp_b = step(eff_b, rule_b)
        if frozenset(int(x) for x in rec.cells_a_after) != exp_a:
            return (False, f"record {i} (gen {rec.gen}): A mismatch")
        if frozenset(int(x) for x in rec.cells_b_after) != exp_b:
            return (False, f"record {i} (gen {rec.gen}): B mismatch")
        A, B = exp_a, exp_b
        gen = rec.gen
    return (True, "coupled CA growth verifies")


def render_combined(world, max_gen=None):
    records = [r for r in world.records()
               if isinstance(r, CoupledCAStepRecord)]
    if max_gen is not None:
        records = records[:max_gen]
    seed = world.seed_body()
    A_by_gen = {0: frozenset(seed["initial_a"])}
    B_by_gen = {0: frozenset(seed["initial_b"])}
    for r in records:
        A_by_gen[r.gen] = frozenset(r.cells_a_after)
        B_by_gen[r.gen] = frozenset(r.cells_b_after)
    all_xs = []
    for g, cs in A_by_gen.items(): all_xs.extend(cs)
    for g, cs in B_by_gen.items(): all_xs.extend(cs)
    if not all_xs:
        return "(empty)"
    x_min, x_max = min(all_xs), max(all_xs)
    y_max = max(A_by_gen.keys())
    grid = [[" " for _ in range(x_max - x_min + 1)]
             for _ in range(y_max + 1)]
    for g in range(y_max + 1):
        a = A_by_gen.get(g, frozenset())
        b = B_by_gen.get(g, frozenset())
        for x in a | b:
            ch = "#" if (x in a and x in b) else ("A" if x in a else "B")
            grid[g][x - x_min] = ch
    return "\n".join("".join(r) for r in grid)


def _first_gen_with_overlap(world):
    seed = world.seed_body()
    A = frozenset(seed["initial_a"])
    B = frozenset(seed["initial_b"])
    if A & B:
        return 0
    for r in world.records():
        if isinstance(r, CoupledCAStepRecord):
            A = frozenset(r.cells_a_after)
            B = frozenset(r.cells_b_after)
            if A & B:
                return r.gen
    return None


def demo(artifact_dir=None):
    import json as _json
    from pathlib import Path
    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "coupled_ca"
    path.mkdir(parents=True, exist_ok=True)

    OFFSET, N, RULE = 30, 30, 90

    def make(k_a, k_b):
        return CoupledCAWorld(
            rule_a=RULE, rule_b=RULE,
            initial_a=[0], initial_b=[OFFSET],
            k_a=k_a, k_b=k_b)

    w_a = make(0, 0); w_a.grow_n(N)
    w_b = make(100, 100); w_b.grow_n(N)
    w_c = make(100, 0); w_c.grow_n(N)
    w_d = make(0, 0); w_d.grow_n(N // 2)
    change = w_d.set_coupling(k_a=100, k_b=100)
    w_d.grow_n(N - N // 2)

    for name, w in (("A", w_a), ("B", w_b), ("C", w_c), ("D", w_d)):
        vlog = verify_coupled_ca_log(w)
        vgrow = verify_coupled_ca_growth(w)
        assert vlog[0] and vgrow[0], (name, vlog, vgrow)

    print("=" * 74)
    print("Coupled CAs — two fractal worlds in shared space")
    print("=" * 74)
    print()
    print(f"  rule_a = {RULE}, rule_b = {RULE}")
    print(f"  A at x=0, B at x={OFFSET}   gen 0..{N}")
    print()

    for name, w, label in (
        ("A", w_a, "k_a=0, k_b=0 — independent"),
        ("B", w_b, "k_a=100, k_b=100 — full coupling"),
        ("C", w_c, "k_a=100, k_b=0 — A listens only"),
        ("D", w_d, "k_a=0→100 at gen 15 — mid-world change"),
    ):
        first = _first_gen_with_overlap(w)
        print(f"  [{name}] {label}")
        print(f"       first overlap in state at gen: {first}")
        print()
        for line in render_combined(w).split("\n"):
            print(f"       {line}")
        print()

    print("  What this establishes:")
    print("    - Two CAs in shared 1D space. Overlap is geometric.")
    print("    - k modulates what happens at overlap.")
    print("    - Asymmetric k affects only one side.")
    print("    - Mid-world k change is a signed record; replay")
    print("      crosses it.")
    print("    - Composite is the unit of verification, because")
    print("      coupling makes the two worlds jointly")
    print("      constraining — unlike the chaos-game case, where")
    print("      each side could evolve alone.")
    print()
    print("  Honest limit: 'communication' here = shared-space")
    print("  collision, not message-passing. A density-mediated")
    print("  channel is a future component.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    audit = {}
    for name, w in (("A", w_a), ("B", w_b), ("C", w_c), ("D", w_d)):
        audit[name] = {
            "k_a": w.k_a(), "k_b": w.k_b(), "gen": w.gen(),
            "first_overlap_gen": _first_gen_with_overlap(w),
            "verify_log": verify_coupled_ca_log(w)[0],
            "verify_growth": verify_coupled_ca_growth(w)[0],
        }
    audit["D"]["change_at_gen"] = change.gen
    (path / "coupled_ca_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/coupled_ca_demo.json")
    return audit
