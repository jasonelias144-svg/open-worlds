"""
fractal_grid_world.py — a grid-embedded fractal world.

Where ElementaryCAWorld presents a 1D row per generation, this
presents the cumulative 2D pattern. The world's cells() are
(x, y) points, where y is the generation that produced x.

Rule is unchanged — step(frontier, rule_number). Growth applies
it to the current frontier (last row's x-positions) and adds a
new row at y = gen + 1.

New params vs ElementaryCAWorld: `max_gen` — an optional
boundary. When set, grow() returns None after reaching it. This
is what lets a garden know the world's eventual extent without
simulating to infinity.

Branching: the branch seed carries the full 2D pattern inherited
from the parent (inherited_rows) plus the current frontier plus
the branch point (from_gen). The child continues with the new
rule from the frontier. Result: parent's fractal shape topped
with the child's. Both halves verify.

Composition: same WCP-shape as other atomic worlds.
FractalGridWorld implements: world_id, seed_body(), seed_sig(),
records(), gen(), cells() [2D], rows(), grow(), grow_n(),
request_branch(), verify_log(), verify_growth(),
verify_sierpinski(), bbox().

Honest limits (documented, tested):
  - Branch seed carries the full inherited pattern. For gen 1000,
    that's ~1M cells. A v0.2 would use a compact Merkle proof
    instead. Documented as a scale concern.
  - verify_sierpinski is only for fresh-rule-90-single-cell. A
    chimera returns False with the specific reason. No partial
    "contains Sierpinski" check — that would be a separate
    function.
  - No 3D. The grid is 2D. A 3D extension (Sierpinski
    tetrahedron from a 2D CA rule) is a future rule + renderer.
  - No interaction. The world grows by generation; visitors
    observe. Tend/grow-interrupt is a future extension.
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

from elementary_ca_world import (
    step, expected_rule90_cells,
    rule_90, rule_30, rule_110,
)


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
# Params
# =====================================================================

@dataclass(frozen=True)
class GridParams:
    rule_number: int = 90
    max_gen: Optional[int] = None

    def __post_init__(self):
        if not (0 <= int(self.rule_number) <= 255):
            raise ValueError(
                f"rule_number {self.rule_number} out of [0,255]")
        if self.max_gen is not None:
            if int(self.max_gen) < 0:
                raise ValueError(
                    f"max_gen must be >= 0 or None; "
                    f"got {self.max_gen}")

    def to_dict(self) -> Dict:
        return {
            "rule_number": int(self.rule_number),
            "max_gen": (int(self.max_gen)
                        if self.max_gen is not None else None),
        }

    def param_hash(self) -> str:
        return _hash(self.to_dict())

    def with_overrides(self, overrides: Dict) -> "GridParams":
        d = self.to_dict()
        for k, v in overrides.items():
            if k == "rule_number":
                d[k] = int(v)
            elif k == "max_gen":
                d[k] = v if v is None else int(v)
            else:
                raise ValueError(f"unknown param {k!r}")
        return GridParams(**d)


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class GridSeedRecord:
    world_id: str
    initial_row: List[int]
    params: Dict
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "grid_seed",
            "world_id": self.world_id,
            "initial_row": sorted(self.initial_row),
            "params": dict(self.params),
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


@dataclass(frozen=True)
class GridRowRecord:
    world_id: str
    gen: int
    seed_hash: str
    prev: Optional[str]
    p: str
    row_x: List[int]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "grid_row",
            "world_id": self.world_id,
            "gen": self.gen,
            "seed": self.seed_hash,
            "prev": self.prev,
            "p": self.p,
            "row_x": sorted(self.row_x),
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


@dataclass(frozen=True)
class GridBranchSeed:
    new_world_id: str
    parent_id: str
    parent_branch_hash: Optional[str]
    inherited_rows: List[Dict]
    frontier_x: List[int]
    from_gen: int
    params: Dict
    ts: str
    sig_parent: str
    sig_branch: str

    def body(self) -> Dict:
        return {
            "type": "grid_branch_seed",
            "new_world_id": self.new_world_id,
            "parent_id": self.parent_id,
            "parent_branch_hash": self.parent_branch_hash,
            "inherited_rows": [dict(r)
                                for r in self.inherited_rows],
            "frontier_x": sorted(self.frontier_x),
            "from_gen": self.from_gen,
            "params": dict(self.params),
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        d = self.body()
        d["sig_parent"] = self.sig_parent
        d["sig_branch"] = self.sig_branch
        return d


@dataclass(frozen=True)
class GridBranchRecord:
    world_id: str
    step: int
    branch_seed: Dict
    prev: Optional[str]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "grid_branch",
            "world_id": self.world_id,
            "step": self.step,
            "branch_seed": dict(self.branch_seed),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


# =====================================================================
# World
# =====================================================================

class FractalGridWorld:
    def __init__(self, params: GridParams,
                 initial_row: Iterable[int], keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._params = params
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._initial_row = frozenset(int(x) for x in initial_row)
        self._gen = 0
        self._frontier = frozenset(self._initial_row)
        self._rows: List[Tuple[int, FrozenSet[int]]] = [
            (0, frozenset(self._initial_row))]
        self._records: List = []
        self._last_hash: Optional[str] = None
        seed_body = {
            "type": "grid_seed",
            "world_id": self._world_id,
            "initial_row": sorted(self._initial_row),
            "params": params.to_dict(),
            "ts": _now(),
        }
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(
            _canonical(seed_body)).hex()

    @classmethod
    def from_branch(cls, seed: GridBranchSeed, keypair):
        obj = cls.__new__(cls)
        obj._params = GridParams(**seed.params)
        obj._keypair = keypair
        obj._world_id = seed.new_world_id
        obj._rows = [(int(r["gen"]),
                       frozenset(int(x) for x in r["row_x"]))
                      for r in seed.inherited_rows]
        obj._frontier = frozenset(int(x)
                                   for x in seed.frontier_x)
        obj._gen = int(seed.from_gen)
        obj._initial_row = (
            frozenset(obj._rows[0][1]) if obj._rows
            else frozenset())
        obj._seed_body = seed.to_dict()
        obj._seed_sig = seed.sig_branch
        obj._records = []
        obj._last_hash = None
        return obj

    # -- Accessors ------------------------------------------

    @property
    def world_id(self) -> str:
        return self._world_id

    @property
    def params(self) -> GridParams:
        return self._params

    def gen(self) -> int:
        return self._gen

    def rows(self) -> List[Tuple[int, FrozenSet[int]]]:
        return list(self._rows)

    def frontier(self) -> FrozenSet[int]:
        return self._frontier

    def cells(self) -> FrozenSet[Tuple[int, int]]:
        """The 2D pattern as (x, y) points."""
        out = set()
        for gen, row in self._rows:
            for x in row:
                out.add((int(x), int(gen)))
        return frozenset(out)

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

    def at_max(self) -> bool:
        return (self._params.max_gen is not None
                and self._gen >= self._params.max_gen)

    def bbox(self) -> Optional[Tuple[int, int, int, int]]:
        """(x_min, y_min, x_max, y_max) of the current pattern."""
        if not self._rows:
            return None
        xs = [x for _, row in self._rows for x in row]
        if not xs:
            return None
        return (min(xs), 0, max(xs), self._gen)

    # -- Growth ---------------------------------------------

    def grow(self) -> Optional[GridRowRecord]:
        if self.at_max():
            return None
        new_row = step(self._frontier, self._params.rule_number)
        new_gen = self._gen + 1
        body = {
            "type": "grid_row",
            "world_id": self._world_id,
            "gen": new_gen,
            "seed": self.seed_hash(),
            "prev": self._last_hash,
            "p": self._params.param_hash(),
            "row_x": sorted(new_row),
            "ts": _now(),
        }
        rec = GridRowRecord(
            world_id=self._world_id,
            gen=new_gen,
            seed_hash=self.seed_hash(),
            prev=self._last_hash,
            p=self._params.param_hash(),
            row_x=sorted(new_row),
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._rows.append((new_gen, new_row))
        self._frontier = new_row
        self._gen = new_gen
        self._last_hash = rec.record_hash()
        return rec

    def grow_n(self, n: int) -> int:
        steps = 0
        for _ in range(n):
            if self.grow() is None:
                break
            steps += 1
        return steps

    # -- Branching ------------------------------------------

    def request_branch(self, overrides: Dict
                       ) -> Optional[Tuple[GridBranchSeed,
                                           "FractalGridWorld"]]:
        try:
            new_params = self._params.with_overrides(overrides)
        except (ValueError, TypeError):
            return None
        child_kp = Ed25519PrivateKey.generate()
        child_id = _did_from_kp(child_kp)
        inherited = [
            {"gen": int(g), "row_x": sorted(int(x) for x in row)}
            for g, row in self._rows
        ]
        frontier_x = sorted(int(x) for x in self._frontier)
        unsigned = {
            "type": "grid_branch_seed",
            "new_world_id": child_id,
            "parent_id": self._world_id,
            "parent_branch_hash": self._last_hash,
            "inherited_rows": inherited,
            "frontier_x": frontier_x,
            "from_gen": self._gen,
            "params": new_params.to_dict(),
            "ts": _now(),
        }
        sig_parent = self._keypair.sign(
            _canonical(unsigned)).hex()
        sig_branch = child_kp.sign(
            _canonical(unsigned)).hex()
        seed = GridBranchSeed(
            new_world_id=child_id,
            parent_id=self._world_id,
            parent_branch_hash=self._last_hash,
            inherited_rows=inherited,
            frontier_x=frontier_x,
            from_gen=self._gen,
            params=new_params.to_dict(),
            ts=unsigned["ts"],
            sig_parent=sig_parent,
            sig_branch=sig_branch,
        )
        rec_body = {
            "type": "grid_branch",
            "world_id": self._world_id,
            "step": self._gen,
            "branch_seed": seed.to_dict(),
            "prev": self._last_hash,
            "ts": unsigned["ts"],
        }
        rec = GridBranchRecord(
            world_id=self._world_id,
            step=self._gen,
            branch_seed=seed.to_dict(),
            prev=self._last_hash,
            ts=unsigned["ts"],
            sig=self._keypair.sign(_canonical(rec_body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        child = FractalGridWorld.from_branch(seed, child_kp)
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


def verify_log(world: FractalGridWorld) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed_body = world.seed_body()
    t = seed_body.get("type")
    if t == "grid_seed":
        if not _verify_sig(world.world_id,
                            seed_body, world.seed_sig()):
            return (False, "seed signature invalid")
        start_gen = 0
    elif t == "grid_branch_seed":
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
        start_gen = int(seed_body["from_gen"])
        # Inherited frontier must match the last inherited row
        if seed_body["inherited_rows"]:
            last = seed_body["inherited_rows"][-1]
            if int(last["gen"]) != start_gen:
                return (False,
                         "branch seed: from_gen != "
                         "last inherited row gen")
            if sorted(int(x) for x in last["row_x"]) \
                    != sorted(int(x)
                               for x in seed_body["frontier_x"]):
                return (False,
                         "branch seed: frontier_x != "
                         "last inherited row_x")
    else:
        return (False, f"unknown seed type {t!r}")
    p_hash = world.params.param_hash()
    s_hash = world.seed_hash()
    prev = None
    prev_gen = start_gen
    for i, rec in enumerate(world.records()):
        if rec.world_id != world.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(world.world_id,
                            rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, GridRowRecord):
            if rec.seed_hash != s_hash:
                return (False, f"record {i}: seed_hash mismatch")
            if rec.p != p_hash:
                return (False, f"record {i}: params hash changed")
            if rec.gen != prev_gen + 1:
                return (False, f"record {i}: gen not monotonic "
                                f"({rec.gen} != {prev_gen + 1})")
            prev_gen = rec.gen
        elif isinstance(rec, GridBranchRecord):
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
                return (False, f"record {i}: branch parent hash")
        else:
            return (False, f"record {i}: unknown type")
        prev = rec.record_hash()
    return (True, "log verifies")


def verify_growth(world: FractalGridWorld) -> Tuple[bool, str]:
    ok, reason = verify_log(world)
    if not ok:
        return (False, reason)
    seed_body = world.seed_body()
    t = seed_body.get("type")
    if t == "grid_seed":
        frontier = frozenset(int(x)
                              for x in seed_body["initial_row"])
        current_gen = 0
    else:
        frontier = frozenset(int(x)
                              for x in seed_body["frontier_x"])
        current_gen = int(seed_body["from_gen"])
    rule_number = int(seed_body["params"]["rule_number"])
    for i, rec in enumerate(world.records()):
        if isinstance(rec, GridRowRecord):
            if rec.gen != current_gen + 1:
                return (False, f"record {i}: gen mismatch")
            expected = step(frontier, rule_number)
            actual = frozenset(int(x) for x in rec.row_x)
            if expected != actual:
                return (False,
                         f"record {i} (gen {rec.gen}): "
                         f"row_x does not match rule")
            frontier = actual
            current_gen = rec.gen
    return (True, "growth verifies")


def verify_sierpinski(world: FractalGridWorld
                       ) -> Tuple[bool, str]:
    """Exact Sierpinski check.

    Only meaningful for a fresh world (not a branch) with
    rule_number=90 and initial_row=[0]. A chimera returns
    False with the specific reason.
    """
    ok, reason = verify_log(world)
    if not ok:
        return (False, reason)
    seed_body = world.seed_body()
    if seed_body.get("type") != "grid_seed":
        return (False,
                 "not a fresh seed (this world is a branch; "
                 "its inherited half came from the parent, "
                 "not from a Rule 90 seed)")
    if int(seed_body["params"]["rule_number"]) != 90:
        return (False,
                 f"not rule 90 (rule_number="
                 f"{seed_body['params']['rule_number']})")
    if list(seed_body["initial_row"]) != [0]:
        return (False,
                 f"not single-cell seed "
                 f"(got {seed_body['initial_row']})")
    for rec in world.records():
        if not isinstance(rec, GridRowRecord):
            continue
        expected = expected_rule90_cells(rec.gen)
        actual = frozenset(int(x) for x in rec.row_x)
        if expected != actual:
            return (False,
                     f"gen {rec.gen}: not Sierpinski "
                     f"(expected {len(expected)} cells, "
                     f"found {len(actual)})")
    return (True,
             f"Sierpinski verified across {world.gen()} generations")


# =====================================================================
# Rendering
# =====================================================================

def render_ascii(world: FractalGridWorld,
                  flip: bool = False,
                  max_gen: Optional[int] = None,
                  char_live: str = "#",
                  char_dead: str = " ") -> str:
    """Render the pattern. Gen 0 at top by default.

    max_gen caps the rows shown (useful when the world is very
    tall)."""
    rows = world.rows()
    if max_gen is not None:
        rows = [(g, r) for g, r in rows if g <= max_gen]
    if not rows:
        return "(empty)"
    xs = [x for _, row in rows for x in row]
    if not xs:
        return "(empty)"
    x_min, x_max = min(xs), max(xs)
    y_max = rows[-1][0]
    width = x_max - x_min + 1
    height = y_max + 1
    grid = [[char_dead for _ in range(width)]
            for _ in range(height)]
    for gen, row in rows:
        for x in row:
            grid[gen][x - x_min] = char_live
    if flip:
        grid = list(reversed(grid))
    return "\n".join("".join(r) for r in grid)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Four scenarios:
      A. Rule 90, single cell. Grow to gen 15 for the visual,
         grow to gen 31 for the verification. Verify Sierpinski.
      B. Branch: Rule 90 → Rule 30. Chimera. Both halves verify.
      C. Branch: Rule 90 → Rule 110. Chimera.
      D. max_gen boundary. Growth stops at the boundary; a
         branch with a larger max_gen continues.
    """
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "fractal_grid_world"
    path.mkdir(parents=True, exist_ok=True)

    # ---- A: Rule 90, single cell ----
    seed_kp = Ed25519PrivateKey.generate()
    world_a = FractalGridWorld(
        params=GridParams(rule_number=90, max_gen=31),
        initial_row=[0], keypair=seed_kp)
    world_a.grow_n(31)
    a_log = verify_log(world_a)
    a_growth = verify_growth(world_a)
    a_sierp = verify_sierpinski(world_a)
    a_visual = render_ascii(world_a, max_gen=15)
    a_bbox = world_a.bbox()

    # ---- B: Rule 90 → Rule 30 ----
    keeper_b = Ed25519PrivateKey.generate()
    parent_b = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=keeper_b)
    parent_b.grow_n(15)
    branch_b = parent_b.request_branch(
        {"rule_number": 30, "max_gen": 30})
    if branch_b is None:
        raise RuntimeError("rule 30 branch refused")
    seed_b, child_b = branch_b
    parent_b.grow_n(15)
    child_b.grow_n(15)
    b_parent_log = verify_log(parent_b)
    b_parent_growth = verify_growth(parent_b)
    b_parent_sierp = verify_sierpinski(parent_b)
    b_child_log = verify_log(child_b)
    b_child_growth = verify_growth(child_b)
    b_child_sierp = verify_sierpinski(child_b)
    b_child_visual = render_ascii(child_b)

    # ---- C: Rule 90 → Rule 110 ----
    keeper_c = Ed25519PrivateKey.generate()
    parent_c = FractalGridWorld(
        params=GridParams(rule_number=90),
        initial_row=[0], keypair=keeper_c)
    parent_c.grow_n(15)
    branch_c = parent_c.request_branch(
        {"rule_number": 110, "max_gen": 30})
    seed_c, child_c = branch_c
    child_c.grow_n(15)
    c_child_log = verify_log(child_c)
    c_child_growth = verify_growth(child_c)
    c_child_visual = render_ascii(child_c)

    # ---- D: max_gen boundary ----
    keeper_d = Ed25519PrivateKey.generate()
    world_d = FractalGridWorld(
        params=GridParams(rule_number=90, max_gen=10),
        initial_row=[0], keypair=keeper_d)
    stopped_at = world_d.grow_n(30)   # try to grow 30, should stop at 10
    d_at_boundary = world_d.gen()
    d_growth_at_boundary = verify_growth(world_d)
    # Branch to extend
    branch_d = world_d.request_branch({"max_gen": 20})
    seed_d, extended_d = branch_d
    extended_d.grow_n(30)  # should stop at 20
    d_extended_gen = extended_d.gen()
    d_extended_growth = verify_growth(extended_d)

    # Print
    print("=" * 74)
    print("Fractal Grid World — the Sierpinski triangle as a world")
    print("=" * 74)
    print()

    print("  [A] Rule 90, single cell — the world IS the fractal")
    print(f"      max_gen: 31  grown to gen: {world_a.gen()}")
    print()
    print("      Gen 0 at top, gen 15 at bottom (full triangle "
          f"has {len(world_a.cells())} cells, "
          f"bbox {a_bbox}):")
    for line in a_visual.split("\n"):
        print(f"        {line}")
    print()
    print(f"      verify_log:        {a_log[0]}  ({a_log[1]})")
    print(f"      verify_growth:     {a_growth[0]}  "
          f"({a_growth[1]})")
    print(f"      verify_sierpinski: {a_sierp[0]}  "
          f"({a_sierp[1]})")
    print()

    print("  [B] Branch: Rule 90 → Rule 30 (chimera)")
    print(f"      Parent: Rule 90, gen 30")
    print(f"      Child:  inherited gen 0-15 (Sierpinski), "
          f"continued with Rule 30 to gen 30")
    print()
    print("      The chimera (Sierpinski top, Rule 30 bottom):")
    for line in b_child_visual.split("\n"):
        print(f"        {line}")
    print()
    print(f"      Parent verify:  log={b_parent_log[0]}  "
          f"growth={b_parent_growth[0]}  "
          f"sierpinski={b_parent_sierp[0]}")
    print(f"      Child  verify:  log={b_child_log[0]}  "
          f"growth={b_child_growth[0]}")
    print(f"      Child sierpinski: {b_child_sierp[0]}  "
          f"({b_child_sierp[1]})")
    print()

    print("  [C] Branch: Rule 90 → Rule 110")
    print(f"      Child verify: log={c_child_log[0]}  "
          f"growth={c_child_growth[0]}")
    print()
    print("      The chimera (Sierpinski top, Rule 110 bottom):")
    for line in c_child_visual.split("\n"):
        print(f"        {line}")
    print()

    print("  [D] max_gen boundary")
    print(f"      World started with max_gen=10; tried to grow 30")
    print(f"      stopped at gen {d_at_boundary} (as expected)")
    print(f"      verify_growth at boundary: "
          f"{d_growth_at_boundary[0]}")
    print(f"      Branched with max_gen=20; child grew to gen "
          f"{d_extended_gen}")
    print(f"      verify_growth after extension: "
          f"{d_extended_growth[0]}")
    print()

    print("  What this establishes:")
    print("    - The world's state is a 2D pattern: (x, y) where")
    print("      x is the CA cell position and y is the generation.")
    print("      A garden can treat the world's extent as a")
    print("      triangle, not a rectangle, and can ask for its")
    print("      bbox to know if it fits in a slot.")
    print("    - Growth is one row per call. The rule is the same")
    print("      CA step as ElementaryCAWorld; the presentation")
    print("      is different.")
    print("    - Branching produces a chimera: the child inherits")
    print("      the parent's 2D pattern, then continues downward")
    print("      from the frontier with the new rule. Both halves")
    print("      verify. The child is not itself a Sierpinski")
    print("      triangle (verify_sierpinski says so, with the")
    print("      specific reason) — it CONTAINS one on its top")
    print("      half, which is a stronger claim than 'it is one.'")
    print("    - max_gen is a boundary. Growth stops. A branch")
    print("      with a larger max_gen extends. The boundary is")
    print("      a param, so it's part of the param hash and the")
    print("      branch signature.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    audit = {
        "scenario_a": {
            "rule_number": 90,
            "seed": [0],
            "max_gen": 31,
            "gens_grown": world_a.gen(),
            "cells": len(world_a.cells()),
            "bbox": list(a_bbox) if a_bbox else None,
            "verify_log": a_log[0],
            "verify_growth": a_growth[0],
            "verify_sierpinski": a_sierp[0],
        },
        "scenario_b": {
            "parent_rule": 90, "child_rule": 30,
            "parent_verified": {
                "log": b_parent_log[0],
                "growth": b_parent_growth[0],
                "sierpinski": b_parent_sierp[0],
            },
            "child_verified": {
                "log": b_child_log[0],
                "growth": b_child_growth[0],
            },
            "child_sierpinski": b_child_sierp[0],
            "child_sierpinski_reason": b_child_sierp[1],
            "branch_seed_hash": _hash(seed_b.to_dict()),
        },
        "scenario_c": {
            "parent_rule": 90, "child_rule": 110,
            "child_verified": {
                "log": c_child_log[0],
                "growth": c_child_growth[0],
            },
            "branch_seed_hash": _hash(seed_c.to_dict()),
        },
        "scenario_d": {
            "max_gen_initial": 10,
            "gens_grown_before_stop": d_at_boundary,
            "stopped_at_boundary": d_at_boundary == 10,
            "boundary_verify": d_growth_at_boundary[0],
            "extended_max_gen": 20,
            "extended_gens": d_extended_gen,
            "extended_verify": d_extended_growth[0],
        },
    }
    (path / "fractal_grid_world_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/fractal_grid_world_demo.json")
    return audit
