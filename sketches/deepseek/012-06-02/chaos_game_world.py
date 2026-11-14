"""
chaos_game_world.py — chaos, choice, and fractal geometry.

A ChaosGameWorld is an IFS attractor built by iterated random
map selection. Each step, the world picks one of N affine
transforms and applies it to the current point. The set of
visited points converges to the attractor — a fractal.

Two growth modes are implemented:

  "seeded_random"  — the world picks via a declared PRNG,
                     seeded in the seed record. The verifier
                     replays the PRNG to check each step.

  "external_input" — a declared authority supplies each
                     choice, per-step, signed. The verifier
                     checks the authority's signature.

The two modes differ in what verifiability means:

  seeded_random:    "I can reproduce this exact world."
  external_input:   "I can confirm this world was built by
                    the declared authority's choices."

Both are honest. Both are offline-checkable.

Composition: same shape as other atomic worlds (signed seed,
signed chain, per-record param hash, offline verification).

Honest limits (documented, tested):
  - IFS transforms are linear (affine). This is chaos of
    *choice*, not non-linear dynamics of state. A truly
    non-linear world (logistic map, Hénon) is a sibling
    world type, not this one.
  - Integer arithmetic with floor division loses precision
    at extreme depth. The world is what it records, not
    the exact real-valued IFS.
  - The PRNG is a small declared implementation
    (xorshift64*). Cross-platform reproducibility relies on
    Python's integer arithmetic, not on any library.
  - No branch-carrying-history. A branch inherits the
    current point but starts a fresh log with a fresh PRNG
    seed. That is deliberate: a branch is a divergence, not
    a continuation. A continuation-mode branch could be
    added later.
  - No act-based world-keys yet. External authority is one
    declared DID in the seed, not a rich permission model.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


SCALE = 1000
MASK_64 = (1 << 64) - 1
GROWTH_MODES = ("seeded_random", "external_input")


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
# PRNG — deterministic, in-code, platform-independent
# =====================================================================

def xorshift64_star_step(state: int) -> Tuple[int, int]:
    state ^= (state >> 12)
    state &= MASK_64
    state ^= (state << 25) & MASK_64
    state ^= (state >> 27)
    state &= MASK_64
    return state, (state * 0x2545F4914F6CDD1D) & MASK_64


def pick_weighted(output: int, weights: Tuple[int, ...]) -> int:
    total = sum(weights)
    n = output % total
    acc = 0
    for i, w in enumerate(weights):
        acc += w
        if n < acc:
            return i
    return len(weights) - 1


PRNG_ID = "xorshift64_star_v1"


# =====================================================================
# Transforms and presets
# =====================================================================

@dataclass(frozen=True)
class ChaosTransform:
    """x'_s = (a*x_s + b*y_s + c) // denom
       y'_s = (d*x_s + e*y_s + f) // denom

    Coordinates are integers scaled by SCALE. `denom` is the
    transform's integer divisor. F is in "true * SCALE * denom"
    units to preserve the translation.
    """
    name: str
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    denom: int
    weight: int

    def apply(self, point: Tuple[int, int]) -> Tuple[int, int]:
        x, y = point
        return ((self.a * x + self.b * y + self.c) // self.denom,
                (self.d * x + self.e * y + self.f) // self.denom)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "a": self.a, "b": self.b, "c": self.c,
            "d": self.d, "e": self.e, "f": self.f,
            "denom": self.denom, "weight": self.weight,
        }


@dataclass(frozen=True)
class ChaosPreset:
    preset_id: str
    transforms: Tuple[ChaosTransform, ...]

    def __post_init__(self):
        if not self.transforms:
            raise ValueError("preset needs at least one transform")
        for t in self.transforms:
            if t.denom < 1:
                raise ValueError(
                    f"transform {t.name}: denom must be >= 1")
            if t.weight < 1:
                raise ValueError(
                    f"transform {t.name}: weight must be >= 1")

    def preset_hash(self) -> str:
        return _hash({
            "preset_id": self.preset_id,
            "transforms": [t.to_dict() for t in self.transforms],
        })

    def weights(self) -> Tuple[int, ...]:
        return tuple(t.weight for t in self.transforms)


def _sierpinski() -> ChaosPreset:
    # Triangle with vertices at scaled (0,0), (1000,0), (500,866).
    # Each transform: move halfway to a vertex.
    return ChaosPreset(
        preset_id="sierpinski-v1",
        transforms=(
            ChaosTransform("v0", 1, 0, 0,   0, 1, 0,   2, 1),
            ChaosTransform("v1", 1, 0, 1000, 0, 1, 0,  2, 1),
            ChaosTransform("v2", 1, 0, 500, 0, 1, 866, 2, 1),
        ),
    )


def _barnsley_fern() -> ChaosPreset:
    # Classic Barnsley coefficients scaled by 1000.
    return ChaosPreset(
        preset_id="barnsley-fern-v1",
        transforms=(
            # stem: x' = 0, y' = 0.16 y
            ChaosTransform("stem", 0, 0, 0,
                            0, 160, 0, 1000, 1),
            # leaflet left
            ChaosTransform("leaflet_l", 200, -260, 0,
                            230, 220, 1600000, 1000, 7),
            # leaflet right
            ChaosTransform("leaflet_r", -150, 280, 0,
                            260, 240, 440000, 1000, 7),
            # main
            ChaosTransform("main", 850, 40, 0,
                            -40, 850, 1600000, 1000, 85),
        ),
    )


SIERPINSKI = _sierpinski()
BARNSLEY = _barnsley_fern()


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class ChaosSeedRecord:
    world_id: str
    preset_hash: str
    growth_mode: str
    prng_id: Optional[str]
    prng_seed: Optional[int]
    input_authority: Optional[str]
    initial_point: Tuple[int, int]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "chaos_seed",
            "world_id": self.world_id,
            "preset_hash": self.preset_hash,
            "growth_mode": self.growth_mode,
            "prng_id": self.prng_id,
            "prng_seed": self.prng_seed,
            "input_authority": self.input_authority,
            "initial_point": list(self.initial_point),
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


@dataclass(frozen=True)
class ChaosStepRecord:
    world_id: str
    step: int
    prev: Optional[str]
    p: str
    transform_idx: int
    point: Tuple[int, int]
    input_sig: Optional[str]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "chaos_step",
            "world_id": self.world_id,
            "step": self.step,
            "prev": self.prev,
            "p": self.p,
            "transform_idx": self.transform_idx,
            "point": list(self.point),
            "input_sig": self.input_sig,
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())


@dataclass(frozen=True)
class ChaosChoice:
    """A signed choice of transform at a specific step.
    Used only in external_input mode."""
    world_id: str
    step: int
    transform_idx: int
    authority_id: str
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "chaos_choice",
            "world_id": self.world_id,
            "step": self.step,
            "transform_idx": self.transform_idx,
            "authority_id": self.authority_id,
            "ts": self.ts,
        }

    def record_hash(self) -> str:
        return _hash(self.body())

    def to_dict(self) -> Dict:
        d = self.body()
        d["sig"] = self.sig
        return d


def sign_choice(world_id: str, step: int, transform_idx: int,
                 authority_kp, ts: Optional[str] = None) -> ChaosChoice:
    # Fix (ours): `ts` may be given, so a composite world can sign its
    # choices and its own step with one time (coupled_chaos_world.py).
    authority_id = _did_from_kp(authority_kp)
    ts = ts if ts is not None else _now()
    body = {
        "type": "chaos_choice",
        "world_id": world_id,
        "step": step,
        "transform_idx": transform_idx,
        "authority_id": authority_id,
        "ts": ts,
    }
    sig = authority_kp.sign(_canonical(body)).hex()
    return ChaosChoice(world_id=world_id, step=step,
                        transform_idx=transform_idx,
                        authority_id=authority_id,
                        ts=ts, sig=sig)


def verify_choice(choice: ChaosChoice,
                    expected_authority: Optional[str] = None) -> bool:
    try:
        if expected_authority is not None \
                and choice.authority_id != expected_authority:
            return False
        pub = _pubkey_from_did(choice.authority_id)
        pub.verify(bytes.fromhex(choice.sig),
                    _canonical(choice.body()))
        return True
    except Exception:
        return False


@dataclass(frozen=True)
class ChaosBranchSeed:
    new_world_id: str
    parent_id: str
    parent_branch_hash: Optional[str]
    preset_hash: str
    growth_mode: str
    prng_seed: Optional[int]
    input_authority: Optional[str]
    initial_point: Tuple[int, int]
    from_step: int
    ts: str
    sig_parent: str
    sig_branch: str

    def body(self) -> Dict:
        return {
            "type": "chaos_branch_seed",
            "new_world_id": self.new_world_id,
            "parent_id": self.parent_id,
            "parent_branch_hash": self.parent_branch_hash,
            "preset_hash": self.preset_hash,
            "growth_mode": self.growth_mode,
            "prng_seed": self.prng_seed,
            "input_authority": self.input_authority,
            "initial_point": list(self.initial_point),
            "from_step": self.from_step,
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        d = self.body()
        d["sig_parent"] = self.sig_parent
        d["sig_branch"] = self.sig_branch
        return d


@dataclass(frozen=True)
class ChaosBranchRecord:
    world_id: str
    step: int
    branch_seed: Dict
    prev: Optional[str]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "chaos_branch",
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

class ChaosGameWorld:
    def __init__(
        self,
        preset: ChaosPreset,
        growth_mode: str,
        initial_point: Tuple[int, int],
        keypair,
        prng_seed: Optional[int] = None,
        input_authority: Optional[str] = None,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        if growth_mode not in GROWTH_MODES:
            raise ValueError(
                f"growth_mode must be one of {GROWTH_MODES}; "
                f"got {growth_mode!r}")
        if growth_mode == "seeded_random" and prng_seed is None:
            raise ValueError(
                "seeded_random mode requires prng_seed")
        if growth_mode == "external_input" \
                and not input_authority:
            raise ValueError(
                "external_input mode requires input_authority")
        self._preset = preset
        self._mode = growth_mode
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._point = (int(initial_point[0]), int(initial_point[1]))
        self._initial_point = self._point
        self._prng_seed = prng_seed
        self._prng_state = prng_seed
        self._authority = input_authority
        self._step = 0
        self._records: List = []
        self._points: List[Tuple[int, int]] = [self._point]
        self._last_hash: Optional[str] = None
        seed_body = {
            "type": "chaos_seed",
            "world_id": self._world_id,
            "preset_hash": preset.preset_hash(),
            "growth_mode": growth_mode,
            "prng_id": (PRNG_ID
                        if growth_mode == "seeded_random"
                        else None),
            "prng_seed": prng_seed,
            "input_authority": input_authority,
            "initial_point": list(self._point),
            "ts": _now(),
        }
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(
            _canonical(seed_body)).hex()
        self._p_hash = _hash({
            "preset_hash": preset.preset_hash(),
            "growth_mode": growth_mode,
            "prng_id": seed_body["prng_id"],
        })

    @classmethod
    def from_branch(cls, seed: ChaosBranchSeed, keypair,
                     preset: ChaosPreset):
        obj = cls.__new__(cls)
        obj._preset = preset
        obj._mode = seed.growth_mode
        obj._keypair = keypair
        obj._world_id = seed.new_world_id
        obj._point = (int(seed.initial_point[0]),
                      int(seed.initial_point[1]))
        obj._initial_point = obj._point
        obj._prng_seed = seed.prng_seed
        obj._prng_state = seed.prng_seed
        obj._authority = seed.input_authority
        obj._step = 0
        obj._records = []
        obj._points = [obj._point]
        obj._last_hash = None
        obj._seed_body = seed.to_dict()
        obj._seed_sig = seed.sig_branch
        obj._p_hash = _hash({
            "preset_hash": seed.preset_hash,
            "growth_mode": seed.growth_mode,
            "prng_id": (PRNG_ID
                        if seed.growth_mode == "seeded_random"
                        else None),
        })
        return obj

    # -- Accessors ------------------------------------------

    @property
    def world_id(self) -> str:
        return self._world_id

    @property
    def preset(self) -> ChaosPreset:
        return self._preset

    @property
    def growth_mode(self) -> str:
        return self._mode

    def step(self) -> int:
        return self._step

    def point(self) -> Tuple[int, int]:
        return self._point

    def points(self) -> List[Tuple[int, int]]:
        return list(self._points)

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

    def p_hash(self) -> str:
        return self._p_hash

    # -- Growth ---------------------------------------------

    def grow(self) -> Optional[ChaosStepRecord]:
        """One step, using the world's declared growth mode.
        Returns None if the mode requires external input."""
        if self._mode != "seeded_random":
            return None
        weights = self._preset.weights()
        self._prng_state, output = xorshift64_star_step(
            self._prng_state)
        idx = pick_weighted(output, weights)
        transform = self._preset.transforms[idx]
        new_point = transform.apply(self._point)
        return self._record_step(idx, new_point, input_sig=None)

    def grow_n(self, n: int) -> int:
        steps = 0
        for _ in range(n):
            if self.grow() is None:
                break
            steps += 1
        return steps

    def grow_with_input(self, choice: ChaosChoice
                         ) -> Optional[ChaosStepRecord]:
        """One step, driven by a signed external choice."""
        if self._mode != "external_input":
            return None
        if not verify_choice(choice, expected_authority=self._authority):
            return None
        if choice.world_id != self._world_id:
            return None
        if choice.step != self._step:
            return None
        if not (0 <= choice.transform_idx
                < len(self._preset.transforms)):
            return None
        transform = self._preset.transforms[choice.transform_idx]
        new_point = transform.apply(self._point)
        # Fix (ours): the step keeps the time the choice was signed, so
        # the verifier can rebuild the choice from the step record.
        return self._record_step(
            choice.transform_idx, new_point,
            input_sig=choice.sig, ts=choice.ts)

    def _record_step(self, idx: int, new_point: Tuple[int, int],
                      input_sig: Optional[str],
                      ts: Optional[str] = None) -> ChaosStepRecord:
        new_step = self._step + 1
        body = {
            "type": "chaos_step",
            "world_id": self._world_id,
            "step": new_step,
            "prev": self._last_hash,
            "p": self._p_hash,
            "transform_idx": idx,
            "point": list(new_point),
            "input_sig": input_sig,
            "ts": ts if ts is not None else _now(),
        }
        rec = ChaosStepRecord(
            world_id=self._world_id,
            step=new_step,
            prev=self._last_hash,
            p=self._p_hash,
            transform_idx=idx,
            point=new_point,
            input_sig=input_sig,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._points.append(new_point)
        self._point = new_point
        self._step = new_step
        self._last_hash = rec.record_hash()
        return rec

    # -- Branching ------------------------------------------

    def request_branch(
        self,
        prng_seed: Optional[int] = None,
        input_authority: Optional[str] = None,
    ) -> Tuple[ChaosBranchSeed, "ChaosGameWorld"]:
        """Create a branch. Inherits current point; starts fresh
        log. New PRNG seed makes the branch diverge. A new
        authority, in external_input mode, makes the branch a
        different gardener's world.

        Branching always succeeds (no refusal path — this is a
        keeper operation, not a requested one).
        """
        child_kp = Ed25519PrivateKey.generate()
        child_id = _did_from_kp(child_kp)
        new_prng = prng_seed
        if self._mode == "seeded_random" and new_prng is None:
            new_prng = self._prng_state
        new_authority = input_authority or self._authority
        unsigned = {
            "type": "chaos_branch_seed",
            "new_world_id": child_id,
            "parent_id": self._world_id,
            "parent_branch_hash": self._last_hash,
            "preset_hash": self._preset.preset_hash(),
            "growth_mode": self._mode,
            "prng_seed": new_prng,
            "input_authority": new_authority,
            "initial_point": list(self._point),
            "from_step": self._step,
            "ts": _now(),
        }
        sig_parent = self._keypair.sign(
            _canonical(unsigned)).hex()
        sig_branch = child_kp.sign(
            _canonical(unsigned)).hex()
        seed = ChaosBranchSeed(
            new_world_id=child_id,
            parent_id=self._world_id,
            parent_branch_hash=self._last_hash,
            preset_hash=self._preset.preset_hash(),
            growth_mode=self._mode,
            prng_seed=new_prng,
            input_authority=new_authority,
            initial_point=self._point,
            from_step=self._step,
            ts=unsigned["ts"],
            sig_parent=sig_parent,
            sig_branch=sig_branch,
        )
        rec_body = {
            "type": "chaos_branch",
            "world_id": self._world_id,
            "step": self._step,
            "branch_seed": seed.to_dict(),
            "prev": self._last_hash,
            "ts": unsigned["ts"],
        }
        rec = ChaosBranchRecord(
            world_id=self._world_id,
            step=self._step,
            branch_seed=seed.to_dict(),
            prev=self._last_hash,
            ts=unsigned["ts"],
            sig=self._keypair.sign(_canonical(rec_body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        child = ChaosGameWorld.from_branch(
            seed, child_kp, self._preset)
        return seed, child


# =====================================================================
# Verification
# =====================================================================

def _verify_sig(did: str, body: Dict, sig: str) -> bool:
    try:
        pub = _pubkey_from_did(did)
        pub.verify(bytes.fromhex(sig), _canonical(body))
        return True
    except Exception:
        return False


def verify_chaos_log(world: ChaosGameWorld) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = world.seed_body()
    t = seed.get("type")
    if t == "chaos_seed":
        if not _verify_sig(world.world_id,
                            seed, world.seed_sig()):
            return (False, "seed signature invalid")
    elif t == "chaos_branch_seed":
        unsigned = {k: v for k, v in seed.items()
                     if k not in ("sig_parent", "sig_branch")}
        try:
            _pubkey_from_did(seed["parent_id"]).verify(
                bytes.fromhex(seed["sig_parent"]),
                _canonical(unsigned))
            _pubkey_from_did(seed["new_world_id"]).verify(
                bytes.fromhex(seed["sig_branch"]),
                _canonical(unsigned))
        except Exception as e:
            return (False, f"branch seed sig invalid: {e}")
    else:
        return (False, f"unknown seed type {t!r}")
    p_hash = world.p_hash()
    prev = None
    prev_step = 0
    for i, rec in enumerate(world.records()):
        if rec.world_id != world.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(world.world_id, rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, ChaosStepRecord):
            if rec.p != p_hash:
                return (False, f"record {i}: params hash changed")
            if rec.step != prev_step + 1:
                return (False, f"record {i}: step not monotonic")
            prev_step = rec.step
        elif isinstance(rec, ChaosBranchRecord):
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


def verify_chaos_growth(world: ChaosGameWorld
                        ) -> Tuple[bool, str]:
    """Verify that each step is a valid application of the
    world's growth mode."""
    ok, reason = verify_chaos_log(world)
    if not ok:
        return (False, reason)
    seed = world.seed_body()
    mode = seed["growth_mode"]
    preset = world.preset
    if mode == "seeded_random":
        state = seed["prng_seed"]
        expected_point = tuple(seed["initial_point"])
        weights = preset.weights()
        for i, rec in enumerate(world.records()):
            if not isinstance(rec, ChaosStepRecord):
                continue
            state, output = xorshift64_star_step(state)
            expected_idx = pick_weighted(output, weights)
            if rec.transform_idx != expected_idx:
                return (False,
                         f"record {i} (step {rec.step}): "
                         f"transform_idx {rec.transform_idx} "
                         f"!= PRNG-expected {expected_idx}")
            expected_point = preset.transforms[
                expected_idx].apply(expected_point)
            if tuple(rec.point) != expected_point:
                return (False,
                         f"record {i} (step {rec.step}): point "
                         f"does not match transform application")
    elif mode == "external_input":
        authority = seed["input_authority"]
        expected_point = tuple(seed["initial_point"])
        for i, rec in enumerate(world.records()):
            if not isinstance(rec, ChaosStepRecord):
                continue
            if rec.input_sig is None:
                return (False,
                         f"record {i}: external mode record "
                         f"has no input signature")
            # Fix (ours): a choice is signed for the step it grows
            # from, one before the step record's own.
            choice_body = {
                "type": "chaos_choice",
                "world_id": rec.world_id,
                "step": rec.step - 1,
                "transform_idx": rec.transform_idx,
                "authority_id": authority,
                "ts": rec.ts,
            }
            try:
                pub = _pubkey_from_did(authority)
                pub.verify(bytes.fromhex(rec.input_sig),
                            _canonical(choice_body))
            except Exception:
                return (False,
                         f"record {i}: choice signature invalid")
            if not (0 <= rec.transform_idx
                    < len(preset.transforms)):
                return (False,
                         f"record {i}: transform_idx out of range")
            expected_point = preset.transforms[
                rec.transform_idx].apply(expected_point)
            if tuple(rec.point) != expected_point:
                return (False,
                         f"record {i} (step {rec.step}): point "
                         f"does not match transform application")
    else:
        return (False, f"unknown growth mode {mode!r}")
    return (True, "growth verifies")


# =====================================================================
# Rendering
# =====================================================================

def render_ascii(world: ChaosGameWorld,
                  width: int = 60, height: int = 24,
                  skip_initial: bool = True) -> str:
    """Downsample the point set to ASCII.

    skip_initial=True omits the starting point from the bbox
    (which is not representative of the attractor).
    """
    points = world.points()
    if skip_initial and len(points) > 1:
        points = points[1:]
    if not points:
        return "(no points)"
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs) + 1
    y0, y1 = min(ys), max(ys) + 1
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return "(degenerate bbox)"
    grid = [[" " for _ in range(width)] for _ in range(height)]
    for (px, py) in points:
        gx = (px - x0) * width // (x1 - x0)
        gy = (py - y0) * height // (y1 - y0)
        gx = min(gx, width - 1)
        gy = min(gy, height - 1)
        grid[gy][gx] = "#"
    return "\n".join("".join(row) for row in grid)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Four scenarios:
      A. Sierpinski, seeded_random. PRNG decides each step.
         Verifier replays the PRNG.
      B. Sierpinski, external_input. Gardener signs each choice.
         Verifier checks signatures.
      C. Barnsley fern, seeded_random. Same discipline,
         different geometry.
      D. Branch: same parent, new PRNG seed → different world.
    """
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "chaos_game"
    path.mkdir(parents=True, exist_ok=True)

    # ---- A: Sierpinski, seeded_random ----
    kp_a = Ed25519PrivateKey.generate()
    world_a = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="seeded_random",
        initial_point=(500, 500), keypair=kp_a,
        prng_seed=0xDEADBEEFCAFEBABE)
    world_a.grow_n(5000)
    a_log = verify_chaos_log(world_a)
    a_growth = verify_chaos_growth(world_a)
    a_render = render_ascii(world_a, width=60, height=24)
    a_unique = len({p[0] for p in world_a.points()})

    # ---- B: Sierpinski, external_input ----
    kp_b = Ed25519PrivateKey.generate()
    gardener_kp = Ed25519PrivateKey.generate()
    gardener_id = _did_from_kp(gardener_kp)
    world_b = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="external_input",
        initial_point=(500, 500), keypair=kp_b,
        input_authority=gardener_id)
    # Drive 3000 steps, gardener picks by another PRNG (deterministic
    # for the demo, but the world only sees signed choices)
    g_state = 0x1234567890ABCDEF
    g_weights = SIERPINSKI.weights()
    for _ in range(3000):
        g_state, out = xorshift64_star_step(g_state)
        idx = pick_weighted(out, g_weights)
        choice = sign_choice(
            world_b.world_id, world_b.step(), idx,
            gardener_kp)
        world_b.grow_with_input(choice)
    b_log = verify_chaos_log(world_b)
    b_growth = verify_chaos_growth(world_b)
    b_render = render_ascii(world_b, width=60, height=24)
    # Tamper check: bogus choice is refused
    bad_choice = sign_choice(
        world_b.world_id, world_b.step(), 0,
        Ed25519PrivateKey.generate())  # wrong signer
    b_rejects_bad_sig = world_b.grow_with_input(bad_choice) is None

    # ---- C: Barnsley fern, seeded_random ----
    kp_c = Ed25519PrivateKey.generate()
    world_c = ChaosGameWorld(
        preset=BARNSLEY, growth_mode="seeded_random",
        initial_point=(0, 0), keypair=kp_c,
        prng_seed=0xFEEDFACECAFED00D)
    world_c.grow_n(4000)
    c_log = verify_chaos_log(world_c)
    c_growth = verify_chaos_growth(world_c)
    c_render = render_ascii(world_c, width=40, height=24)

    # ---- D: Branch → divergence ----
    # Branch A into a different world with a different PRNG seed
    seed_d, world_d = world_a.request_branch(
        prng_seed=0x0123456789ABCDEF)
    world_d.grow_n(3000)
    # Parent continues
    world_a.grow_n(3000)
    d_log = verify_chaos_log(world_d)
    d_growth = verify_chaos_growth(world_d)
    d_parent_growth = verify_chaos_growth(world_a)
    a_points = frozenset(world_a.points())
    d_points = frozenset(world_d.points())
    d_divergence = len(a_points ^ d_points)

    print("=" * 74)
    print("Chaos game worlds — choice, chaos, and fractal geometry")
    print("=" * 74)
    print()

    print("  [A] Sierpinski, seeded_random  (PRNG picks)")
    print(f"      preset: {SIERPINSKI.preset_id}   "
          f"seed: 0xDEADBEEFCAFEBABE")
    print(f"      steps: {world_a.step()}   unique x-positions: "
          f"{a_unique}")
    print()
    print("      The fractal (5000 points, downsampled):")
    for line in a_render.split("\n"):
        print(f"        {line}")
    print()
    print(f"      verify_log:    {a_log[0]}  ({a_log[1]})")
    print(f"      verify_growth: {a_growth[0]}  ({a_growth[1]})")
    print()

    print("  [B] Sierpinski, external_input  (gardener signs)")
    print(f"      preset: {SIERPINSKI.preset_id}   "
          f"gardener: {gardener_id[:24]}...")
    print(f"      steps: {world_b.step()}")
    print()
    print("      The fractal (3000 points, downsampled):")
    for line in b_render.split("\n"):
        print(f"        {line}")
    print()
    print(f"      verify_log:       {b_log[0]}  ({b_log[1]})")
    print(f"      verify_growth:    {b_growth[0]}  ({b_growth[1]})")
    print(f"      rejects wrong sig: {b_rejects_bad_sig}")
    print()

    print("  [C] Barnsley fern, seeded_random")
    print(f"      preset: {BARNSLEY.preset_id}")
    print()
    print("      The fern (4000 points, downsampled):")
    for line in c_render.split("\n"):
        print(f"        {line}")
    print()
    print(f"      verify_log:    {c_log[0]}")
    print(f"      verify_growth: {c_growth[0]}")
    print()

    print("  [D] Branch divergence")
    print(f"      parent step: {world_a.step()}   "
          f"branch step: {world_d.step()}")
    print(f"      parent verified: log={verify_chaos_log(world_a)[0]}"
          f"  growth={d_parent_growth[0]}")
    print(f"      branch verified: log={d_log[0]}"
          f"  growth={d_growth[0]}")
    print(f"      symmetric difference: {d_divergence} points")
    print(f"      (both continue to be Sierpinski-shaped, but "
          f"visit different points)")
    print()

    print("  What this establishes:")
    print("    - A chaos game world is an atomic fractal world.")
    print("      Every step is a choice among transforms; the")
    print("      visited points converge to a fractal attractor.")
    print("    - Two growth modes. 'seeded_random': verifier")
    print("      replays the PRNG. 'external_input': verifier")
    print("      checks the gardener's signature on each choice.")
    print("      Both are offline-checkable. Both make different")
    print("      claims about what the world is.")
    print("    - The preset determines the fractal. Sierpinski")
    print("      from a 3-vertex midpoint IFS. Barnsley fern from")
    print("      a 4-transform weighted IFS. Same code, different")
    print("      geometry.")
    print("    - Branching inherits the current point and starts")
    print("      a fresh log with a fresh PRNG seed. The branch is")
    print("      a divergence, not a continuation. Both verify")
    print("      independently; both share the parent's fractal")
    print("      character.")
    print("    - 'Choice enters the world' is explicit: the")
    print("      growth_mode says who chooses, and the verification")
    print("      strategy matches. No hidden agency.")
    print()
    print("  Honest limit: this is chaos of *choice* (the")
    print("  transform sequence is unpredictable without replay),")
    print("  not non-linear dynamics of state (like a Lorenz")
    print("  attractor, where small perturbations blow up).")
    print("  A truly non-linear sibling — the logistic-map world —")
    print("  is the natural next step.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")

    audit = {
        "scenario_a": {
            "preset": SIERPINSKI.preset_id,
            "mode": "seeded_random",
            "prng_seed": 0xDEADBEEFCAFEBABE,
            "steps": world_a.step(),
            "unique_x": a_unique,
            "verify_log": a_log[0],
            "verify_growth": a_growth[0],
        },
        "scenario_b": {
            "preset": SIERPINSKI.preset_id,
            "mode": "external_input",
            "steps": world_b.step(),
            "verify_log": b_log[0],
            "verify_growth": b_growth[0],
            "rejects_wrong_sig": b_rejects_bad_sig,
        },
        "scenario_c": {
            "preset": BARNSLEY.preset_id,
            "mode": "seeded_random",
            "steps": world_c.step(),
            "verify_log": c_log[0],
            "verify_growth": c_growth[0],
        },
        "scenario_d": {
            "parent_steps": world_a.step(),
            "branch_steps": world_d.step(),
            "branch_verified_log": d_log[0],
            "branch_verified_growth": d_growth[0],
            "parent_verified_growth": d_parent_growth[0],
            "divergence_points": d_divergence,
        },
    }
    (path / "chaos_game_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/chaos_game_demo.json")
    return audit
