"""
life_world.py — Conway's Game of Life (and Life-like CAs) as an
atomic world.

The world's growth is generations. Its law is the rule. Params
determine birth/survival/boundary/grid. Params do not change in
place; a branch inherits current cells and applies new params.

Composition: same discipline as fractal_world_v3 — signed seed,
signed chain, param hash per record, offline verification.

Honest scoping (v0.1):
  - Branching is keeper-only. No world-keys, no signed refusals
    yet; v3's world-key and refusal protocols apply identically
    here and can be layered on later.
  - Two boundary modes: "infinite" (unbounded grid) and "wrap"
    (bounded torus). No dead-edge.
  - The classic Life patterns (r-pentomino, glider, gun) are
    included as seed builders. True fractal constructions
    (Sierpinski gliders, breeders) are known but complex to
    set up and are left as future seed builders. The
    "fractal" here is the structural kind — worlds whose
    rule can be re-parametrized into branches.
"""

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

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


def _did_from_kp(kp) -> str:
    return "did:key:" + kp.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()


def _pubkey_from_did(did: str) -> "Ed25519PublicKey":
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


NEIGHBORS = [(dx, dy) for dx in (-1, 0, 1)
              for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


# =====================================================================
# LifeParams — the rule
# =====================================================================

@dataclass(frozen=True)
class LifeParams:
    birth: Tuple[int, ...] = (3,)
    survival: Tuple[int, ...] = (2, 3)
    boundary: str = "infinite"
    width: int = 0
    height: int = 0

    def __post_init__(self):
        if self.boundary not in ("infinite", "wrap"):
            raise ValueError(
                f"bad boundary {self.boundary!r}")
        for v in self.birth:
            if not (0 <= int(v) <= 8):
                raise ValueError(
                    f"birth value {v} out of [0,8]")
        for v in self.survival:
            if not (0 <= int(v) <= 8):
                raise ValueError(
                    f"survival value {v} out of [0,8]")
        if self.boundary == "wrap":
            if self.width <= 0 or self.height <= 0:
                raise ValueError(
                    "wrap boundary needs width,height > 0")

    def to_dict(self):
        return {
            "birth": sorted(int(x) for x in self.birth),
            "survival": sorted(int(x) for x in self.survival),
            "boundary": self.boundary,
            "width": int(self.width),
            "height": int(self.height),
        }

    def param_hash(self):
        return _hash(self.to_dict())

    def with_overrides(self, overrides):
        d = self.to_dict()
        for k, v in overrides.items():
            if k in ("birth", "survival"):
                d[k] = tuple(sorted(int(x) for x in v))
            elif k == "boundary":
                d[k] = v
            elif k in ("width", "height"):
                d[k] = int(v)
            else:
                raise ValueError(f"unknown param {k!r}")
        return LifeParams(**d)

    def rule_string(self):
        b = "".join(str(x) for x in sorted(self.birth))
        s = "".join(str(x) for x in sorted(self.survival))
        return f"B{b}/S{s}"


def standard_life() -> LifeParams:
    return LifeParams()


def highlife() -> LifeParams:
    return LifeParams(birth=(3, 6), survival=(2, 3))


# =====================================================================
# The growth rule
# =====================================================================

def life_step(cells: Iterable[Tuple[int, int]],
              params: LifeParams) -> FrozenSet[Tuple[int, int]]:
    counts: Dict[Tuple[int, int], int] = defaultdict(int)
    for (x, y) in cells:
        for (dx, dy) in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if params.boundary == "wrap":
                nx %= params.width
                ny %= params.height
            counts[(nx, ny)] += 1
    new = set()
    for pos in cells:
        if counts.get(pos, 0) in params.survival:
            new.add(pos)
    for pos, c in counts.items():
        if pos not in cells and c in params.birth:
            new.add(pos)
    return frozenset(new)


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class LifeSeedRecord:
    world_id: str
    template_hash: str
    params: Dict
    cells: List[List[int]]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "life_seed",
            "world_id": self.world_id,
            "template_hash": self.template_hash,
            "params": dict(self.params),
            "cells": [list(c) for c in self.cells],
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class LifeGenRecord:
    world_id: str
    gen: int
    seed_hash: str
    prev: Optional[str]
    p: str
    cells: List[List[int]]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "life_gen",
            "world_id": self.world_id,
            "gen": self.gen,
            "seed": self.seed_hash,
            "prev": self.prev,
            "p": self.p,
            "cells": [list(c) for c in self.cells],
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class LifeBranchSeed:
    new_world_id: str
    parent_id: str
    parent_branch_hash: str
    template_hash: str
    params: Dict
    cells: List[List[int]]
    ts: str
    sig_parent: str
    sig_branch: str

    def body(self):
        return {
            "type": "life_branch_seed",
            "new_world_id": self.new_world_id,
            "parent_id": self.parent_id,
            "parent_branch_hash": self.parent_branch_hash,
            "template_hash": self.template_hash,
            "params": dict(self.params),
            "cells": [list(c) for c in self.cells],
            "ts": self.ts,
        }

    def to_dict(self):
        d = self.body()
        d["sig_parent"] = self.sig_parent
        d["sig_branch"] = self.sig_branch
        return d


@dataclass(frozen=True)
class LifeBranchRecord:
    world_id: str
    step: int
    branch_seed: Dict
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "life_branch",
            "world_id": self.world_id,
            "step": self.step,
            "branch_seed": dict(self.branch_seed),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# LifeWorld
# =====================================================================

class LifeWorld:
    def __init__(
        self, template_id: str, params: LifeParams,
        initial_cells: Iterable[Tuple[int, int]],
        keypair,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._params = params
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._cells = frozenset(tuple(c) for c in initial_cells)
        self._template_hash = _hash({"template_id": template_id})
        seed_body = {
            "type": "life_seed",
            "world_id": self._world_id,
            "template_hash": self._template_hash,
            "params": params.to_dict(),
            "cells": sorted([list(c) for c in self._cells]),
            "ts": _now(),
        }
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(
            _canonical(seed_body)).hex()
        self._records: List = []
        self._gen = 0
        self._last_hash: Optional[str] = None

    @classmethod
    def from_branch(cls, seed: LifeBranchSeed, keypair):
        obj = cls.__new__(cls)
        obj._params = LifeParams(**seed.params)
        obj._keypair = keypair
        obj._world_id = seed.new_world_id
        obj._cells = frozenset(tuple(c) for c in seed.cells)
        obj._template_hash = seed.template_hash
        obj._seed_body = seed.to_dict()   # full, includes both sigs
        obj._seed_sig = seed.sig_branch
        obj._records = []
        obj._gen = 0
        obj._last_hash = None
        return obj

    # -- Accessors ------------------------------------------

    @property
    def world_id(self):
        return self._world_id

    @property
    def params(self):
        return self._params

    def cells(self):
        return self._cells

    def gen(self):
        return self._gen

    def records(self):
        return list(self._records)

    def seed_body(self):
        return dict(self._seed_body)

    def seed_sig(self):
        return self._seed_sig

    def seed_hash(self):
        return _hash(self._seed_body)

    def last_hash(self):
        return self._last_hash

    # -- Growth ---------------------------------------------

    def grow(self) -> LifeGenRecord:
        new_cells = life_step(self._cells, self._params)
        cells_list = sorted([list(c) for c in new_cells])
        body = {
            "type": "life_gen",
            "world_id": self._world_id,
            "gen": self._gen,
            "seed": self.seed_hash(),
            "prev": self._last_hash,
            "p": self._params.param_hash(),
            "cells": cells_list,
            "ts": _now(),
        }
        rec = LifeGenRecord(
            world_id=self._world_id,
            gen=self._gen,
            seed_hash=self.seed_hash(),
            prev=self._last_hash,
            p=self._params.param_hash(),
            cells=cells_list,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._cells = new_cells
        self._gen += 1
        self._last_hash = rec.record_hash()
        return rec

    def grow_n(self, n: int):
        for _ in range(n):
            self.grow()

    # -- Branching ------------------------------------------

    def request_branch(
        self, requested_params: Dict,
        requester_kp=None,
    ) -> Optional[Tuple[LifeBranchSeed, "LifeWorld"]]:
        """Keeper-only branching. Returns (seed, child) or None.

        A branch inherits the world's cells at the moment of
        branching. New params apply from that point forward.
        The parent is unchanged and continues with its own
        params.
        """
        try:
            new_params = self._params.with_overrides(
                requested_params)
        except (ValueError, TypeError):
            return None
        child_kp = Ed25519PrivateKey.generate()
        child_id = _did_from_kp(child_kp)
        cells_list = sorted([list(c) for c in self._cells])
        unsigned = {
            "type": "life_branch_seed",
            "new_world_id": child_id,
            "parent_id": self._world_id,
            "parent_branch_hash": self._last_hash,
            "template_hash": self._template_hash,
            "params": new_params.to_dict(),
            "cells": cells_list,
            "ts": _now(),
        }
        sig_parent = self._keypair.sign(
            _canonical(unsigned)).hex()
        sig_branch = child_kp.sign(
            _canonical(unsigned)).hex()
        seed = LifeBranchSeed(
            new_world_id=child_id,
            parent_id=self._world_id,
            parent_branch_hash=self._last_hash,
            template_hash=self._template_hash,
            params=new_params.to_dict(),
            cells=cells_list,
            ts=unsigned["ts"],
            sig_parent=sig_parent,
            sig_branch=sig_branch,
        )
        rec_body = {
            "type": "life_branch",
            "world_id": self._world_id,
            "step": self._gen,
            "branch_seed": seed.to_dict(),
            "prev": self._last_hash,
            "ts": unsigned["ts"],
        }
        rec = LifeBranchRecord(
            world_id=self._world_id,
            step=self._gen,
            branch_seed=seed.to_dict(),
            prev=self._last_hash,
            ts=unsigned["ts"],
            sig=self._keypair.sign(_canonical(rec_body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        child = LifeWorld.from_branch(seed, child_kp)
        return seed, child


# =====================================================================
# Verification
# =====================================================================

def _verify_sig(world_id: str, body: Dict, sig: str) -> bool:
    try:
        pub = _pubkey_from_did(world_id)
        pub.verify(bytes.fromhex(sig), _canonical(body))
        return True
    except Exception:
        return False


def verify_life_log(world: LifeWorld) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed_body = world.seed_body()
    t = seed_body.get("type")
    if t == "life_seed":
        if not _verify_sig(world.world_id, seed_body,
                            world.seed_sig()):
            return (False, "seed signature invalid")
    elif t == "life_branch_seed":
        unsigned = {k: v for k, v in seed_body.items()
                     if k not in ("sig_parent", "sig_branch")}
        try:
            _pubkey_from_did(seed_body["parent_id"]).verify(
                bytes.fromhex(seed_body["sig_parent"]),
                _canonical(unsigned))
            _pubkey_from_did(seed_body["new_world_id"]).verify(
                bytes.fromhex(seed_body["sig_branch"]),
                _canonical(unsigned))
        except Exception as e:
            return (False, f"branch seed sig invalid: {e}")
    else:
        return (False, f"unknown seed type {t!r}")
    p_hash = world.params.param_hash()
    s_hash = world.seed_hash()
    prev = None
    for i, rec in enumerate(world.records()):
        if rec.world_id != world.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(world.world_id, rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, LifeGenRecord):
            if rec.seed_hash != s_hash:
                return (False, f"record {i}: seed_hash mismatch")
            if rec.p != p_hash:
                return (False, f"record {i}: params hash changed")
        elif isinstance(rec, LifeBranchRecord):
            bs = rec.branch_seed
            unsigned = {k: v for k, v in bs.items()
                         if k not in ("sig_parent", "sig_branch")}
            try:
                _pubkey_from_did(bs["parent_id"]).verify(
                    bytes.fromhex(bs["sig_parent"]),
                    _canonical(unsigned))
                _pubkey_from_did(bs["new_world_id"]).verify(
                    bytes.fromhex(bs["sig_branch"]),
                    _canonical(unsigned))
            except Exception:
                return (False,
                         f"record {i}: branch seed sig invalid")
            if bs["parent_branch_hash"] != rec.prev:
                return (False,
                         f"record {i}: branch parent hash")
        else:
            return (False, f"record {i}: unknown type")
        prev = rec.record_hash()
    return (True, "log verifies")


def verify_life_growth(world: LifeWorld) -> Tuple[bool, str]:
    ok, reason = verify_life_log(world)
    if not ok:
        return (False, reason)
    seed_body = world.seed_body()
    cells = frozenset(tuple(c) for c in seed_body["cells"])
    params = LifeParams(**seed_body["params"])
    for i, rec in enumerate(world.records()):
        if isinstance(rec, LifeGenRecord):
            expected = life_step(cells, params)
            recorded = frozenset(tuple(c) for c in rec.cells)
            if expected != recorded:
                return (False,
                         f"record {i}: cells do not match rule")
            cells = recorded
    return (True, "growth verifies")


# =====================================================================
# Rendering
# =====================================================================

def render_ascii(world: LifeWorld, padding: int = 1,
                  max_w: int = 60, max_h: int = 30) -> str:
    cells = world.cells()
    if not cells:
        return "(empty — no live cells)"
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    x_min, x_max = min(xs) - padding, max(xs) + padding
    y_min, y_max = min(ys) - padding, max(ys) + padding
    w = x_max - x_min + 1
    h = y_max - y_min + 1
    if w > max_w or h > max_h:
        return (f"({len(cells)} cells, bbox {w}x{h})")
    grid = [[" " for _ in range(w)] for _ in range(h)]
    for (x, y) in cells:
        grid[y - y_min][x - x_min] = "#"
    return "\n".join("".join(row) for row in grid)


def render_summary(world: LifeWorld) -> str:
    cells = world.cells()
    if not cells:
        return f"gen {world.gen()}: 0 cells (empty)"
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    w = max(xs) - min(xs) + 1
    h = max(ys) - min(ys) + 1
    return (f"gen {world.gen()}: {len(cells)} cells, "
            f"bbox {w}x{h}")


# =====================================================================
# Seed patterns
# =====================================================================

def r_pentomino() -> set:
    """The classic methuselah — 5 cells, grows for 1000+ gens."""
    return {(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)}


def glider() -> set:
    """Moves (1,1) every 4 generations."""
    return {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}


def blinker() -> set:
    """Period-2 oscillator."""
    return {(0, 1), (1, 1), (2, 1)}


def block() -> set:
    """Stable."""
    return {(0, 0), (1, 0), (0, 1), (1, 1)}


def offset(cells: set, dx: int, dy: int) -> set:
    return {(x + dx, y + dy) for (x, y) in cells}


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Three scenarios:
      A. One fractal (r-pentomino) in standard Life.
      B. Multiple fractals in one world: r-pentomino,
         glider, blinker, separated.
      C. Branching: same cells, different rules.
    """
    import json as _json
    from pathlib import Path
    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "life_world"
    path.mkdir(parents=True, exist_ok=True)

    # ---- A: single fractal ----
    seed_a = r_pentomino()
    world_a = LifeWorld(
        template_id="life-conway-v1",
        params=standard_life(),
        initial_cells=seed_a,
        keypair=Ed25519PrivateKey.generate())
    a_seed_render = render_ascii(world_a)
    world_a.grow_n(20)
    a_final_render = render_ascii(world_a)
    a_log = verify_life_log(world_a)
    a_growth = verify_life_growth(world_a)

    # ---- B: multiple fractals in one world ----
    multi = sorted(
        offset(r_pentomino(), 0, 0)
        | offset(glider(), 30, 30)
        | offset(blinker(), 60, 30))
    world_b = LifeWorld(
        template_id="life-conway-v1",
        params=standard_life(),
        initial_cells=multi,
        keypair=Ed25519PrivateKey.generate())
    b_start = render_summary(world_b)
    world_b.grow_n(20)
    b_end = render_summary(world_b)
    b_log = verify_life_log(world_b)
    b_growth = verify_life_growth(world_b)

    # ---- C: branching ----
    keeper_c = Ed25519PrivateKey.generate()
    parent = LifeWorld(
        template_id="life-conway-v1",
        params=standard_life(),
        initial_cells=r_pentomino(),
        keypair=keeper_c)
    parent.grow_n(5)
    branch_result = parent.request_branch(
        {"birth": (3, 6), "survival": (2, 3)})
    if branch_result is None:
        raise RuntimeError("branch refused unexpectedly")
    branch_seed, branch = branch_result
    parent.grow_n(10)    # parent at gen 15, standard Life
    branch.grow_n(10)    # branch at gen 10 from parent's gen 5
    parent_log = verify_life_log(parent)
    parent_growth = verify_life_growth(parent)
    branch_log = verify_life_log(branch)
    branch_growth = verify_life_growth(branch)
    parent_cells = frozenset(parent.cells())
    branch_cells = frozenset(branch.cells())
    divergence = len(parent_cells ^ branch_cells)

    # Print
    print("=" * 74)
    print("Conway's Life as an atomic world")
    print("=" * 74)
    print()
    print("  [A] One fractal — R-pentomino under standard Life")
    print(f"      rule: {world_a.params.rule_string()}  "
          f"(birth={world_a.params.birth}, "
          f"survival={world_a.params.survival})")
    print()
    print("      Gen 0:")
    for line in a_seed_render.split("\n"):
        print(f"        {line}")
    print()
    print("      Gen 20:")
    for line in a_final_render.split("\n"):
        print(f"        {line}")
    print()
    print(f"      verify_log:    {a_log[0]}  ({a_log[1]})")
    print(f"      verify_growth: {a_growth[0]}  "
          f"({a_growth[1]})")
    print()
    print("  [B] Multiple fractals in one world")
    print("      seeds: r-pentomino (0,0)  "
          "+ glider (30,30) + blinker (60,30)")
    print(f"      start: {b_start}")
    print(f"      after 20 gens: {b_end}")
    print(f"      verify_log:    {b_log[0]}")
    print(f"      verify_growth: {b_growth[0]}")
    print()
    print("  [C] Branching — same cells, different rules")
    print(f"      parent rule (B3/S23): grew 5 gens, then branched")
    print(f"      branch rule (B36/S23 HighLife): inherited "
          f"parent's 5-gen state")
    print(f"      after 10 more gens each:")
    print(f"        parent: {render_summary(parent)}")
    print(f"        branch: {render_summary(branch)}")
    print(f"        cells that differ: {divergence} "
          f"(symmetric difference)")
    print(f"      parent  verify: log={parent_log[0]}  "
          f"growth={parent_growth[0]}")
    print(f"      branch  verify: log={branch_log[0]}  "
          f"growth={branch_growth[0]}")
    print()
    print("      Parent at gen 15:")
    for line in render_ascii(parent, padding=1,
                              max_w=70, max_h=20).split("\n"):
        print(f"        {line}")
    print()
    print("      Branch at gen 10 (from same inherited state):")
    for line in render_ascii(branch, padding=1,
                              max_w=70, max_h=20).split("\n"):
        print(f"        {line}")
    print()
    print("  What this establishes:")
    print("    - A Life world is an atomic world. Its growth is")
    print("      one generation per call; its law is the rule;")
    print("      its params are B/S + boundary + grid.")
    print("    - Multiple patterns can live in one world. The")
    print("      world's log records the combined cell set each")
    print("      generation, and the rule replays it exactly.")
    print("    - Changing the rule is branching, not editing.")
    print("      The parent continues under its original rule;")
    print("      the branch inherits the current cells and")
    print("      grows under the new rule from that point on.")
    print("    - Both logs verify offline. Every generation is")
    print("      signed; the params hash is checked per record;")
    print("      the rule replay reconstructs every cell set.")
    print("    - Standard Life doesn't produce exact Sierpinski")
    print("      from small seeds — that needs glider-based")
    print("      constructions. It produces fractal-*like* growth")
    print("      (methuselahs, expanding patterns) which is the")
    print("      honest claim here. Life-like rules (B1/S, Seeds)")
    print("      can produce exact fractals and plug in via the")
    print("      same LifeParams.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {
        "scenario_a": {
            "rule": world_a.params.rule_string(),
            "gens": world_a.gen(),
            "final_cells": len(world_a.cells()),
            "verify_log": a_log[0],
            "verify_growth": a_growth[0],
        },
        "scenario_b": {
            "seeds": 3,
            "gens": world_b.gen(),
            "final_cells": len(world_b.cells()),
            "verify_log": b_log[0],
            "verify_growth": b_growth[0],
        },
        "scenario_c": {
            "parent_rule": parent.params.rule_string(),
            "branch_rule": branch.params.rule_string(),
            "parent_cells": len(parent.cells()),
            "branch_cells": len(branch.cells()),
            "divergence": divergence,
            "parent_verified_log": parent_log[0],
            "parent_verified_growth": parent_growth[0],
            "branch_verified_log": branch_log[0],
            "branch_verified_growth": branch_growth[0],
            "branch_seed_hash": _hash(branch_seed.to_dict()),
        },
    }
    (path / "life_world_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/life_world_demo.json")
    return audit
