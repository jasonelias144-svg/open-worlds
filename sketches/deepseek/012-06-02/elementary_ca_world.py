"""
elementary_ca_world.py — 1D elementary CA as an atomic fractal world.

Conway's Life in 2D produces fractal-*like* growth from small
seeds — sparse, self-similar, dimension ~1.5 — but not exact
Sierpinski (that needs glider-based constructions hundreds of
cells wide). Elementary cellular automata do produce exact
fractals. Rule 90 from a single cell is Pascal's triangle mod 2,
which is the Sierpinski gasket, exactly.

So: this is "Conway's Game of Life or something similar" — the
cellular-automaton family, one-dimensional, chosen because the
fractal claim is provable rather than approximate.

Same discipline as fractal_world_v3:
  - signed seed
  - signed log, one record per generation
  - params hash per record (immutable in place)
  - branching changes the rule; parent continues

Rule 90 from a single cell at position 0:
  gen n has cells at x = 2k - n for k in [0, n] with
  (k & n) == k  (binomial(n, k) odd).

The verifier replays that identity per generation. It is
exact, not statistical.

Composition: same WCP-shape as other atomic worlds.
ElementaryCAWorld implements:
  - world_id, seed_body(), seed_sig(), records()
  - gen() -> int
  - history() -> [(gen, frozenset_of_x_positions), ...]
  - grow(), grow_n()
  - request_branch(overrides)
  - verify_log(), verify_growth()  (also module-level)
  - verify_sierpinski()  (specific to rule 90)

Branch seeds embed both signatures, so a child is
self-verifiable offline.

Simplifications (v0.2 notes):
  - Branching is keeper-only. v3's world-key protocol
    applies and can be layered on without touching this file.
  - No 2D embedding of the log as a grid world yet. The
    fractal IS the 2D render (render_2d), but the world's
    state is 1D. A "grid world" that embeds an elementary
    CA is a small future component.
"""

import hashlib
import json
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


# =====================================================================
# The rule
# =====================================================================

def step(cells: FrozenSet[int], rule_number: int
         ) -> FrozenSet[int]:
    """One generation of a Wolfram elementary CA.

    Neighborhood (left, center, right) → next bit per the
    rule_number's 8-bit binary representation.
    """
    if not (0 <= rule_number <= 255):
        raise ValueError(
            f"rule_number {rule_number} out of [0, 255]")
    candidates = set()
    for x in cells:
        candidates.add(x - 1)
        candidates.add(x)
        candidates.add(x + 1)
    out = set()
    for x in candidates:
        left = 1 if (x - 1) in cells else 0
        center = 1 if x in cells else 0
        right = 1 if (x + 1) in cells else 0
        nbrhd = (left << 2) | (center << 1) | right
        if (rule_number >> (7 - nbrhd)) & 1:
            out.add(x)
    return frozenset(out)


def expected_rule90_cells(gen: int) -> FrozenSet[int]:
    """Cells at generation gen of Rule 90 from a single cell at 0.

    Row gen of Pascal's triangle mod 2 has an entry at column k
    iff (k & gen) == k. That entry maps to 1D position
    x = 2k - gen.

    Equivalent for any rule: this is a pure function of (gen,
    rule_number=90, initial_cells={0}), so a verifier can
    reconstruct it without trusting the log.
    """
    cells = set()
    for k in range(gen + 1):
        if (k & gen) == k:
            cells.add(2 * k - gen)
    return frozenset(cells)


# =====================================================================
# Params
# =====================================================================

@dataclass(frozen=True)
class ECAParams:
    rule_number: int = 90

    def __post_init__(self):
        if not (0 <= int(self.rule_number) <= 255):
            raise ValueError(
                f"rule_number {self.rule_number} "
                f"out of [0, 255]")

    def to_dict(self) -> Dict:
        return {"rule_number": int(self.rule_number)}

    def param_hash(self) -> str:
        return _hash(self.to_dict())

    def with_overrides(self, overrides: Dict) -> "ECAParams":
        d = self.to_dict()
        for k, v in overrides.items():
            if k != "rule_number":
                raise ValueError(f"unknown param {k!r}")
            d[k] = int(v)
        return ECAParams(**d)


def rule_90() -> ECAParams:
    return ECAParams(rule_number=90)


def rule_30() -> ECAParams:
    return ECAParams(rule_number=30)


def rule_110() -> ECAParams:
    return ECAParams(rule_number=110)


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class ECASeedRecord:
    world_id: str
    rule_family: str
    initial_cells: List[int]
    params: Dict
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "eca_seed",
            "world_id": self.world_id,
            "rule_family": self.rule_family,
            "initial_cells": sorted(self.initial_cells),
            "params": dict(self.params),
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


@dataclass(frozen=True)
class ECAGenRecord:
    world_id: str
    gen: int
    seed_hash: str
    prev: Optional[str]
    p: str
    cells: List[int]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "eca_gen",
            "world_id": self.world_id,
            "gen": self.gen,
            "seed": self.seed_hash,
            "prev": self.prev,
            "p": self.p,
            "cells": sorted(self.cells),
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


@dataclass(frozen=True)
class ECABranchSeed:
    new_world_id: str
    parent_id: str
    parent_branch_hash: str
    rule_family: str
    params: Dict
    initial_cells: List[int]
    from_gen: int
    ts: str
    sig_parent: str
    sig_branch: str

    def body(self) -> Dict:
        return {
            "type": "eca_branch_seed",
            "new_world_id": self.new_world_id,
            "parent_id": self.parent_id,
            "parent_branch_hash": self.parent_branch_hash,
            "rule_family": self.rule_family,
            "params": dict(self.params),
            "initial_cells": sorted(self.initial_cells),
            "from_gen": self.from_gen,
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        d = self.body()
        d["sig_parent"] = self.sig_parent
        d["sig_branch"] = self.sig_branch
        return d


@dataclass(frozen=True)
class ECABranchRecord:
    world_id: str
    step: int
    branch_seed: Dict
    prev: Optional[str]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "eca_branch",
            "world_id": self.world_id,
            "step": self.step,
            "branch_seed": dict(self.branch_seed),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


# =====================================================================
# ElementaryCAWorld
# =====================================================================

class ElementaryCAWorld:
    def __init__(self, params: ECAParams,
                 initial_cells: Iterable[int], keypair,
                 template_id: str = "rule90-v1"):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._params = params
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._template_id = template_id
        self._cells = frozenset(int(c) for c in initial_cells)
        self._initial_cells = sorted(self._cells)
        self._rule_family = "elementary_ca"
        seed_body = {
            "type": "eca_seed",
            "world_id": self._world_id,
            "rule_family": self._rule_family,
            "initial_cells": list(self._initial_cells),
            "params": params.to_dict(),
            "ts": _now(),
        }
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(
            _canonical(seed_body)).hex()
        self._records: List = []
        self._gen = 0
        self._last_hash: Optional[str] = None

    @classmethod
    def from_branch(cls, seed: ECABranchSeed, keypair):
        obj = cls.__new__(cls)
        obj._params = ECAParams(**seed.params)
        obj._keypair = keypair
        obj._world_id = seed.new_world_id
        obj._template_id = "rule90-v1"
        obj._cells = frozenset(int(c) for c in seed.initial_cells)
        obj._initial_cells = list(seed.initial_cells)
        obj._rule_family = seed.rule_family
        obj._seed_body = seed.to_dict()
        obj._seed_sig = seed.sig_branch
        obj._records = []
        obj._gen = 0
        obj._last_hash = None
        return obj

    # -- Accessors ------------------------------------------

    @property
    def world_id(self) -> str:
        return self._world_id

    @property
    def params(self) -> ECAParams:
        return self._params

    def cells(self) -> FrozenSet[int]:
        return self._cells

    def gen(self) -> int:
        return self._gen

    def records(self) -> List:
        return list(self._records)

    def seed_body(self) -> Dict:
        return dict(self._seed_body)

    def seed_sig(self) -> str:
        return self._seed_sig

    def seed_hash(self) -> str:
        return _hash(self._seed_body)

    def last_hash(self) -> Optional[str]:
        return self._last_hash

    # -- Growth ---------------------------------------------

    def grow(self) -> ECAGenRecord:
        new_cells = step(self._cells, self._params.rule_number)
        cells_list = sorted(new_cells)
        new_gen = self._gen + 1
        body = {
            "type": "eca_gen",
            "world_id": self._world_id,
            "gen": new_gen,
            "seed": self.seed_hash(),
            "prev": self._last_hash,
            "p": self._params.param_hash(),
            "cells": cells_list,
            "ts": _now(),
        }
        rec = ECAGenRecord(
            world_id=self._world_id,
            gen=new_gen,
            seed_hash=self.seed_hash(),
            prev=self._last_hash,
            p=self._params.param_hash(),
            cells=cells_list,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._cells = new_cells
        self._gen = new_gen
        self._last_hash = rec.record_hash()
        return rec

    def grow_n(self, n: int):
        for _ in range(n):
            self.grow()

    # -- History --------------------------------------------

    def history(self) -> List[Tuple[int, FrozenSet[int]]]:
        """Return [(0, seed_cells), (1, gen1_cells), ...]."""
        out: List[Tuple[int, FrozenSet[int]]] = [
            (0, frozenset(self._initial_cells))]
        for rec in self._records:
            if isinstance(rec, ECAGenRecord):
                out.append((rec.gen, frozenset(rec.cells)))
        return out

    def history_2d(self) -> List[Tuple[int, int]]:
        """The fractal view: (x, gen) for every live cell across
        history. This is what makes the Sierpinski triangle
        visible — the 1D history, plotted with generation as the
        second coordinate, is a 2D pattern."""
        out = []
        for gen, cells in self.history():
            for x in cells:
                out.append((x, gen))
        return out

    # -- Branching ------------------------------------------

    def request_branch(self, overrides: Dict
                       ) -> Optional[Tuple[ECABranchSeed,
                                           "ElementaryCAWorld"]]:
        try:
            new_params = self._params.with_overrides(overrides)
        except (ValueError, TypeError):
            return None
        child_kp = Ed25519PrivateKey.generate()
        child_id = _did_from_kp(child_kp)
        cells_list = sorted(self._cells)
        unsigned = {
            "type": "eca_branch_seed",
            "new_world_id": child_id,
            "parent_id": self._world_id,
            "parent_branch_hash": self._last_hash,
            "rule_family": self._rule_family,
            "params": new_params.to_dict(),
            "initial_cells": cells_list,
            "from_gen": self._gen,
            "ts": _now(),
        }
        sig_parent = self._keypair.sign(
            _canonical(unsigned)).hex()
        sig_branch = child_kp.sign(
            _canonical(unsigned)).hex()
        seed = ECABranchSeed(
            new_world_id=child_id,
            parent_id=self._world_id,
            parent_branch_hash=self._last_hash,
            rule_family=self._rule_family,
            params=new_params.to_dict(),
            initial_cells=cells_list,
            from_gen=self._gen,
            ts=unsigned["ts"],
            sig_parent=sig_parent,
            sig_branch=sig_branch,
        )
        rec_body = {
            "type": "eca_branch",
            "world_id": self._world_id,
            "step": self._gen,
            "branch_seed": seed.to_dict(),
            "prev": self._last_hash,
            "ts": unsigned["ts"],
        }
        rec = ECABranchRecord(
            world_id=self._world_id,
            step=self._gen,
            branch_seed=seed.to_dict(),
            prev=self._last_hash,
            ts=unsigned["ts"],
            sig=self._keypair.sign(_canonical(rec_body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        child = ElementaryCAWorld.from_branch(seed, child_kp)
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


def verify_log(world: ElementaryCAWorld
                ) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed_body = world.seed_body()
    t = seed_body.get("type")
    if t == "eca_seed":
        if not _verify_sig(world.world_id,
                            seed_body, world.seed_sig()):
            return (False, "seed signature invalid")
    elif t == "eca_branch_seed":
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
    prev_gen = 0
    for i, rec in enumerate(world.records()):
        if rec.world_id != world.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(world.world_id, rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, ECAGenRecord):
            if rec.seed_hash != s_hash:
                return (False, f"record {i}: seed_hash mismatch")
            if rec.p != p_hash:
                return (False, f"record {i}: params hash changed")
            if rec.gen != prev_gen + 1:
                return (False, f"record {i}: gen not monotonic")
            prev_gen = rec.gen
        elif isinstance(rec, ECABranchRecord):
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


def verify_growth(world: ElementaryCAWorld
                   ) -> Tuple[bool, str]:
    ok, reason = verify_log(world)
    if not ok:
        return (False, reason)
    seed_body = world.seed_body()
    cells = frozenset(int(c) for c in seed_body["initial_cells"])
    rule_number = int(seed_body["params"]["rule_number"])
    for i, rec in enumerate(world.records()):
        if isinstance(rec, ECAGenRecord):
            expected = step(cells, rule_number)
            actual = frozenset(int(c) for c in rec.cells)
            if expected != actual:
                return (False,
                         f"record {i} (gen {rec.gen}): "
                         f"cells do not match the rule")
            cells = actual
    return (True, "growth verifies")


def verify_sierpinski(world: ElementaryCAWorld
                       ) -> Tuple[bool, str]:
    """Exact verification: does every generation match the
    Sierpinski row under Rule 90 from a single cell at 0?

    Only meaningful if:
      - rule_number == 90
      - initial_cells == [0]

    Returns (ok, reason). Never raises.
    """
    ok, reason = verify_log(world)
    if not ok:
        return (False, reason)
    seed_body = world.seed_body()
    if int(seed_body["params"]["rule_number"]) != 90:
        return (False,
                 f"not rule 90 (rule_number="
                 f"{seed_body['params']['rule_number']})")
    if list(seed_body["initial_cells"]) != [0]:
        return (False,
                 f"not single-cell seed "
                 f"(got {seed_body['initial_cells']})")
    for rec in world.records():
        if not isinstance(rec, ECAGenRecord):
            continue
        expected = expected_rule90_cells(rec.gen)
        actual = frozenset(int(c) for c in rec.cells)
        if expected != actual:
            extra = actual - expected
            missing = expected - actual
            return (False,
                     f"gen {rec.gen}: not Sierpinski "
                     f"(+{len(extra)} -{len(missing)})")
    return (True, "Sierpinski verified across all generations")


# =====================================================================
# Rendering
# =====================================================================

def render_2d(world: ElementaryCAWorld,
               max_gen: Optional[int] = None,
               flip: bool = False,
               char_live: str = "#",
               char_dead: str = " "
               ) -> str:
    """Render the world's history as a 2D pattern.

    Row N shows cells from gen N. Cells at x positions are
    plotted at column x (offset by the min-x across all gens so
    all rows align). This is the fractal view.
    """
    history = world.history()
    if max_gen is not None:
        history = [(g, c) for g, c in history if g <= max_gen]
    xs = [x for _, cells in history for x in cells]
    if not xs:
        return "(empty)"
    x_min = min(xs)
    x_max = max(xs)
    width = x_max - x_min + 1
    rows = []
    for g, cells in history:
        row = [char_dead for _ in range(width)]
        for x in cells:
            row[x - x_min] = char_live
        rows.append("".join(row))
    if flip:
        rows = list(reversed(rows))
    return "\n".join(rows)


def render_current_row(world: ElementaryCAWorld) -> str:
    cells = world.cells()
    if not cells:
        return "(empty row)"
    x_min = min(cells)
    x_max = max(cells)
    return "".join("#" if x in cells
                    else "." for x in range(x_min, x_max + 1))


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Four scenarios:
      A. Rule 90 from a single cell. Grow to gen 31. Verify
         exact Sierpinski. Render the triangle.
      B. Rule 90 → branch to Rule 30. Parent continues as
         Rule 90; branch is chaotic.
      C. Rule 90 → branch to Rule 110. Parent continues as
         Rule 90; branch is Turing-complete.
      D. Rule 90 with a 3-cell seed. Verification honestly
         reports "not single-cell Sierpinski" — it's a valid
         Rule 90 world, just not the canonical fractal.
    """
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "elementary_ca"
    path.mkdir(parents=True, exist_ok=True)

    # ---- A: Rule 90, single cell, Sierpinski ----
    seed_kp = Ed25519PrivateKey.generate()
    world_a = ElementaryCAWorld(
        params=rule_90(), initial_cells=[0],
        keypair=seed_kp)
    world_a.grow_n(31)
    a_log = verify_log(world_a)
    a_growth = verify_growth(world_a)
    a_sierp = verify_sierpinski(world_a)
    a_render = render_2d(world_a, flip=True)

    # ---- B: Rule 90 → Rule 30 ----
    keeper_b = Ed25519PrivateKey.generate()
    parent_b = ElementaryCAWorld(
        params=rule_90(), initial_cells=[0],
        keypair=keeper_b)
    parent_b.grow_n(15)
    branch_b = parent_b.request_branch({"rule_number": 30})
    if branch_b is None:
        raise RuntimeError("rule 30 branch refused")
    seed_b, child_b = branch_b
    parent_b.grow_n(16)         # parent continues as rule 90
    child_b.grow_n(16)          # child continues as rule 30
    b_parent_log = verify_log(parent_b)
    b_parent_growth = verify_growth(parent_b)
    b_parent_sierp = verify_sierpinski(parent_b)
    b_child_log = verify_log(child_b)
    b_child_growth = verify_growth(child_b)
    b_child_render = render_2d(child_b, flip=True)

    # ---- C: Rule 90 → Rule 110 ----
    keeper_c = Ed25519PrivateKey.generate()
    parent_c = ElementaryCAWorld(
        params=rule_90(), initial_cells=[0],
        keypair=keeper_c)
    parent_c.grow_n(15)
    branch_c = parent_c.request_branch({"rule_number": 110})
    if branch_c is None:
        raise RuntimeError("rule 110 branch refused")
    seed_c, child_c = branch_c
    child_c.grow_n(16)
    c_child_log = verify_log(child_c)
    c_child_growth = verify_growth(child_c)
    c_child_render = render_2d(child_c, flip=True)

    # ---- D: Rule 90 with non-single seed ----
    world_d = ElementaryCAWorld(
        params=rule_90(),
        initial_cells=[0, 1, 2],
        keypair=Ed25519PrivateKey.generate())
    world_d.grow_n(15)
    d_log = verify_log(world_d)
    d_growth = verify_growth(world_d)
    d_sierp = verify_sierpinski(world_d)
    d_render = render_2d(world_d, flip=True)

    # Print
    print("=" * 74)
    print("Elementary CA fractal worlds — Rule 90 and beyond")
    print("=" * 74)
    print()

    print("  [A] Rule 90 from a single cell — the Sierpinski gasket")
    print(f"      rule: B90  seed: [0]  grew to gen 31")
    print()
    print("      The triangle (gen 0 at top, gen 31 at bottom):")
    for line in a_render.split("\n")[:33]:
        print(f"        {line}")
    print()
    print(f"      verify_log:       {a_log[0]}  ({a_log[1]})")
    print(f"      verify_growth:    {a_growth[0]}  "
          f"({a_growth[1]})")
    print(f"      verify_sierpinski: {a_sierp[0]}  "
          f"({a_sierp[1]})")
    print(f"      cell count at gen 31: {len(world_a.cells())}  "
          f"(2^5 = 32, because 31 = 11111₂ has popcount 5)")
    print()

    print("  [B] Branch: Rule 90 → Rule 30 (chaotic)")
    print(f"      Parent (B90) at gen 31: "
          f"{len(parent_b.cells())} cells")
    print(f"      Branch (B30) at gen 16: "
          f"{len(child_b.cells())} cells")
    print(f"      Parent verify:  log={b_parent_log[0]}  "
          f"growth={b_parent_growth[0]}  "
          f"sierpinski={b_parent_sierp[0]}")
    print(f"      Branch verify:  log={b_child_log[0]}  "
          f"growth={b_child_growth[0]}")
    print()
    print("      Branch (Rule 30) history, last 17 rows:")
    for line in b_child_render.split("\n")[:17]:
        print(f"        {line}")
    print()

    print("  [C] Branch: Rule 90 → Rule 110 (Turing-complete)")
    print(f"      Branch verify:  log={c_child_log[0]}  "
          f"growth={c_child_growth[0]}")
    print()
    print("      Branch (Rule 110) history, last 17 rows:")
    for line in c_child_render.split("\n")[:17]:
        print(f"        {line}")
    print()

    print("  [D] Rule 90 with a 3-cell seed (not the canonical fractal)")
    print(f"      seed: [0, 1, 2]")
    print(f"      verify_log:       {d_log[0]}")
    print(f"      verify_growth:    {d_growth[0]}")
    print(f"      verify_sierpinski: {d_sierp[0]}  "
          f"({d_sierp[1]})")
    print()

    print("  What this establishes:")
    print("    - An elementary CA world is an atomic fractal world.")
    print("      Its growth is one generation per call; its law")
    print("      is the rule number; its params hash is fixed for")
    print("      the world's lifetime.")
    print("    - Rule 90 from a single cell is Pascal's triangle")
    print("      mod 2 — the Sierpinski gasket, exactly. Every")
    print("      generation is verified against the closed-form")
    print("      identity (k & n) == k. Not statistical.")
    print("    - Changing the rule is branching. The parent stays")
    print("      Rule 90 and remains Sierpinski-verifiable; the")
    print("      child inherits the parent's current row and")
    print("      grows under the new rule from that point on.")
    print("    - Rule 30 and Rule 110 are also reachable by")
    print("      branching. Both verify as valid elementary CA")
    print("      worlds — the rule replay is rule-number-generic.")
    print("    - The fractal claim is honest. Rule 90 is exact.")
    print("      Rule 30 is chaotic. Rule 110 is complex. The")
    print("      verifier never claims more than the rule proves.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")
    print("    'More numerous of Windows –'")
    print("    'Superior – for Doors –'")

    audit = {
        "scenario_a": {
            "rule_number": 90,
            "seed": [0],
            "gens": 31,
            "final_cells": len(world_a.cells()),
            "verify_log": a_log[0],
            "verify_growth": a_growth[0],
            "verify_sierpinski": a_sierp[0],
        },
        "scenario_b": {
            "parent_rule": 90, "branch_rule": 30,
            "parent_gens": 31, "child_gens": 16,
            "parent_verify": {
                "log": b_parent_log[0],
                "growth": b_parent_growth[0],
                "sierpinski": b_parent_sierp[0],
            },
            "child_verify": {
                "log": b_child_log[0],
                "growth": b_child_growth[0],
            },
            "branch_seed_hash": _hash(seed_b.to_dict()),
        },
        "scenario_c": {
            "parent_rule": 90, "branch_rule": 110,
            "child_gens": 16,
            "child_verify": {
                "log": c_child_log[0],
                "growth": c_child_growth[0],
            },
            "branch_seed_hash": _hash(seed_c.to_dict()),
        },
        "scenario_d": {
            "rule_number": 90, "seed": [0, 1, 2],
            "gens": 15,
            "verify_log": d_log[0],
            "verify_growth": d_growth[0],
            "verify_sierpinski": d_sierp[0],
        },
    }
    (path / "elementary_ca_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/elementary_ca_demo.json")
    return audit
