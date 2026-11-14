"""
fractal_world_v3.py — Immutable worlds with branch-based parameter change.

The reframe from v2:

  - A world's parameters do not change in place. The world's log is a
    linear chain of growth records, all with the same params hash.
    Inertia, not influence.
  - A parameter change creates a *branch*: a new world whose seed
    references the parent, inherits its geometry at the branch point,
    and starts with new params. The parent is unchanged and continues.
  - A world can refuse a branch request. Refusals are signed records
    in the parent's log. What a world accepts depends on the world's
    policy, not a universal rule.

Access model:

  - The keeper (holder of the world's private key) issues WorldKeys to
    individuals. A WorldKey names the subject, a tier, and per-param
    ranges.
  - Tiers: observe < communicate < control < terminal.
  - The world's template carries a BranchPolicy: which tiers can branch
    which parameters, in which ranges. None = sandbox (never branches).
  - A branch request is accepted iff:
        request sig valid
        and branch point matches parent's last record
        and world-key is signed by parent, addressed to requester, unexpired
        and world-key tier appears in template's branch policy
        and every requested param is allowed for that tier
        and every value is in both the template's range and the
          world-key's scope (intersection)

Simplifications (marked for the standard's review):

  - `sig` fields are flat, not W3C DataIntegrityProof objects.
  - Short ASCII keys throughout; must match schemas/records-v1.schema.json.
  - Templates are passed in; not registered.
  - No HPKE; world-keys are plaintext.
  - No cross-world messaging (future protocol).
  - No world-key revocation (future).
  - Branch children generate their own keypair; parent signs the seed
    (authorization) and child signs it (acceptance).
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


def _did_from_kp(kp) -> str:
    return "did:key:" + kp.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()


def _pubkey_from_did(did) -> "Ed25519PublicKey":
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1),
              (0, 1), (-1, 1), (-1, 0), (-1, -1)]
PARAM_NAMES = ("branch_length", "max_depth", "water", "light")
TIERS = ("observe", "communicate", "control", "terminal")
TIER_RANK = {t: i for i, t in enumerate(TIERS)}


# =====================================================================
# ParamSet
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

    def with_overrides(self, overrides):
        d = self.to_dict()
        d.update(overrides)
        return ParamSet(**d)

    def effective_max_depth(self):
        return (self.max_depth if self.light >= 3
                else self.max_depth // 2)

    def can_grow(self):
        return self.water > 0


# =====================================================================
# BranchPolicy (embedded in template) — the world's own law
# =====================================================================

def _normalize_policy(policy):
    if policy is None:
        return None
    return {
        tier: {param: [int(lo), int(hi)]
                for param, (lo, hi) in params.items()}
        for tier, params in policy.items()
    }


# =====================================================================
# WorldTemplate
# =====================================================================

@dataclass(frozen=True)
class WorldTemplate:
    template_id: str
    branch_length: int = 2
    max_depth: int = 4
    water: int = 10
    light: int = 10
    branch_policy: Optional[Dict] = None
    # branch_policy: None = sandbox
    # {
    #   "control": {"branch_length": (1, 5), "water": (0, 10)},
    #   "terminal": {"branch_length": (1, 10), "max_depth": (1, 8),
    #                "water": (0, 10), "light": (0, 10)},
    # }

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "branch_length": self.branch_length,
            "max_depth": self.max_depth,
            "water": self.water,
            "light": self.light,
            "branch_policy": _normalize_policy(self.branch_policy),
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


# =====================================================================
# WorldKey — issued by the world (keeper) to an individual
# =====================================================================

@dataclass(frozen=True)
class WorldKey:
    issuer_id: str
    subject_id: str
    tier: str
    param_scopes: Dict[str, Tuple[int, int]]
    valid_until: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "world_key",
            "issuer_id": self.issuer_id,
            "subject_id": self.subject_id,
            "tier": self.tier,
            "param_scopes": {k: list(v)
                             for k, v in self.param_scopes.items()},
            "valid_until": self.valid_until,
            "ts": self.ts,
        }

    def to_dict(self):
        d = self.body()
        d["sig"] = self.sig
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(
            issuer_id=d["issuer_id"],
            subject_id=d["subject_id"],
            tier=d["tier"],
            param_scopes={k: tuple(v)
                          for k, v in d["param_scopes"].items()},
            valid_until=d["valid_until"],
            ts=d["ts"],
            sig=d["sig"],
        )


def verify_world_key(world_key, expected_issuer_id=None):
    if not HAS_CRYPTO:
        return False
    try:
        if expected_issuer_id is not None:
            if world_key.issuer_id != expected_issuer_id:
                return False
        pub = _pubkey_from_did(world_key.issuer_id)
        pub.verify(bytes.fromhex(world_key.sig),
                   _canonical(world_key.body()))
        return True
    except Exception:
        return False


# =====================================================================
# BranchRequest — signed by the requester
# =====================================================================

@dataclass(frozen=True)
class BranchRequest:
    parent_id: str
    branch_point_hash: str
    requested_params: Dict[str, int]
    requested_by: str
    world_key: WorldKey
    ts: str
    sig: str

    def body(self):
        return {
            "type": "branch_request",
            "parent_id": self.parent_id,
            "branch_point_hash": self.branch_point_hash,
            "requested_params": dict(self.requested_params),
            "requested_by": self.requested_by,
            "world_key": self.world_key.to_dict(),
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


def sign_branch_request(parent_id, branch_point_hash,
                        requested_params, requester_kp,
                        world_key, ts=None):
    requester_id = _did_from_kp(requester_kp)
    body = {
        "type": "branch_request",
        "parent_id": parent_id,
        "branch_point_hash": branch_point_hash,
        "requested_params": dict(requested_params),
        "requested_by": requester_id,
        "world_key": world_key.to_dict(),
        "ts": ts or _now(),
    }
    sig = requester_kp.sign(_canonical(body)).hex()
    return BranchRequest(
        parent_id=parent_id,
        branch_point_hash=branch_point_hash,
        requested_params=dict(requested_params),
        requested_by=requester_id,
        world_key=world_key,
        ts=body["ts"],
        sig=sig,
    )


def verify_branch_request(request):
    if not HAS_CRYPTO:
        return False
    try:
        pub = _pubkey_from_did(request.requested_by)
        pub.verify(bytes.fromhex(request.sig),
                   _canonical(request.body()))
        return True
    except Exception:
        return False


# =====================================================================
# BranchSeed — the branch's seed record
# =====================================================================

@dataclass(frozen=True)
class BranchSeed:
    new_world_id: str
    parent_id: str
    parent_branch_hash: str
    template_hash: str
    params: Dict[str, int]
    inherited_segments: List[Tuple[int, int, int, int]]
    initial_frontier: List[Tuple[int, int, int, int]]
    pot: Tuple[int, int, int, int]
    ts: str
    sig_parent: str
    sig_branch: str

    @property
    def world_id(self):
        return self.new_world_id

    def body(self):
        return {
            "type": "branch_seed",
            "new_world_id": self.new_world_id,
            "parent_id": self.parent_id,
            "parent_branch_hash": self.parent_branch_hash,
            "template_hash": self.template_hash,
            "params": dict(self.params),
            "inherited_segments": [list(s)
                                    for s in self.inherited_segments],
            "initial_frontier": [list(t)
                                  for t in self.initial_frontier],
            "pot": list(self.pot),
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())

    def to_dict(self):
        d = self.body()
        d["sig_parent"] = self.sig_parent
        d["sig_branch"] = self.sig_branch
        return d


def verify_branch_seed(seed):
    if not HAS_CRYPTO:
        return False
    try:
        parent_pub = _pubkey_from_did(seed.parent_id)
        parent_pub.verify(bytes.fromhex(seed.sig_parent),
                          _canonical(seed.body()))
        branch_pub = _pubkey_from_did(seed.new_world_id)
        branch_pub.verify(bytes.fromhex(seed.sig_branch),
                          _canonical(seed.body()))
        return True
    except Exception:
        return False


# =====================================================================
# Records
# =====================================================================

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


@dataclass(frozen=True)
class RefusalRecord:
    world_id: str
    step: int
    request_hash: str
    requester_id: str
    reason: str
    prior: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "refusal",
            "world_id": self.world_id,
            "step": self.step,
            "request_hash": self.request_hash,
            "requester_id": self.requester_id,
            "reason": self.reason,
            "prior": self.prior,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class BranchRecord:
    world_id: str
    step: int
    branch_seed_dict: Dict
    prior: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "branch",
            "world_id": self.world_id,
            "step": self.step,
            "branch_seed": dict(self.branch_seed_dict),
            "prior": self.prior,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())

    def seed(self):
        d = self.branch_seed_dict
        return BranchSeed(
            new_world_id=d["new_world_id"],
            parent_id=d["parent_id"],
            parent_branch_hash=d["parent_branch_hash"],
            template_hash=d["template_hash"],
            params=d["params"],
            inherited_segments=[tuple(s) for s in d["inherited_segments"]],
            initial_frontier=[tuple(t) for t in d["initial_frontier"]],
            pot=tuple(d["pot"]),
            ts=d["ts"],
            sig_parent=d["sig_parent"],
            sig_branch=d["sig_branch"],
        )


Record = Union[GrowthRecord, RefusalRecord, BranchRecord]


# =====================================================================
# Growth rule
# =====================================================================

def advance(tips, params, pot):
    if not params.can_grow():
        return [], list(tips)
    eff = params.effective_max_depth()
    segs, new_frontier = [], []
    px, py, pw, ph = pot
    for (x, y, d, depth) in tips:
        if depth >= eff:
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
    def __init__(self, template, pot, initial_tip, keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._template = template
        self._pot = pot
        self._keypair = keypair
        self._params = template.initial_params()
        self._world_id = _did_from_kp(keypair)
        seed_body = {
            "type": "seed",
            "world_id": self._world_id,
            "template_hash": template.template_hash(),
            "pot": list(pot),
            "initial_tip": list(initial_tip),
            "p0": self._params.to_dict(),
            "ts": _now(),
        }
        self._seed_dict = seed_body
        self._seed_sig = keypair.sign(_canonical(seed_body)).hex()
        self._records: List[Record] = []
        self._frontier = [(initial_tip[0], initial_tip[1],
                           initial_tip[2], 0)]
        self._segments: List[Tuple[int, int, int, int]] = []
        self._steps = 0
        self._last_hash: Optional[str] = None

    @classmethod
    def from_branch(cls, seed: BranchSeed, keypair, template):
        if template.template_hash() != seed.template_hash:
            raise ValueError("template hash mismatch")
        obj = cls.__new__(cls)
        obj._template = template
        obj._pot = seed.pot
        obj._keypair = keypair
        obj._params = ParamSet(**seed.params)
        obj._world_id = seed.new_world_id
        obj._seed_dict = seed.body()
        obj._seed_sig = seed.sig_branch  # child's own attestation
        obj._records = []
        obj._frontier = list(seed.initial_frontier)
        obj._segments = list(seed.inherited_segments)
        obj._steps = 0
        obj._last_hash = None
        return obj

    # -- Accessors --------------------------------------------

    @property
    def world_id(self):
        return self._world_id

    @property
    def params(self):
        return self._params

    @property
    def template(self):
        return self._template

    def seed_body(self):
        return dict(self._seed_dict)

    def seed_sig(self):
        return self._seed_sig

    def seed_hash(self):
        return _hash(self._seed_dict)

    def records(self):
        return list(self._records)

    def segments(self):
        return list(self._segments)

    def frontier(self):
        return list(self._frontier)

    def last_hash(self):
        return self._last_hash

    def is_growing(self):
        return bool(self._frontier) and self._params.can_grow()

    def is_sandboxed(self):
        return self._template.branch_policy is None

    # -- Growth -----------------------------------------------

    def grow(self):
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
            "seed": self.seed_hash(),
            "prev": self._last_hash,
            "p": self._params.param_hash(),
            "segs": [list(s) for s in segs],
            "tips": [list(t) for t in new_frontier],
            "ts": _now(),
        }
        rec = GrowthRecord(
            world_id=self._world_id,
            step=self._steps,
            seed_hash=self.seed_hash(),
            prev=self._last_hash,
            p=self._params.param_hash(),
            segs=segs, tips=new_frontier,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._segments.extend(segs)
        self._frontier = new_frontier
        self._steps += 1
        self._last_hash = rec.record_hash()
        return rec

    def grow_n(self, n):
        for _ in range(n):
            if self.grow() is None:
                break

    def grow_until(self, max_steps=200):
        n = 0
        while self.is_growing() and n < max_steps:
            if self.grow() is None:
                break
            n += 1
        return n

    # -- World-key issuance (keeper only) ---------------------

    def issue_world_key(self, subject_id, tier,
                        param_scopes=None, valid_until=None):
        """The keeper issues a world-key. In production, this is
        an admin-level action; here it is a method the keeper
        calls."""
        if tier not in TIER_RANK:
            raise ValueError(f"unknown tier {tier!r}")
        param_scopes = param_scopes or {}
        body = {
            "type": "world_key",
            "issuer_id": self._world_id,
            "subject_id": subject_id,
            "tier": tier,
            "param_scopes": {k: list(v)
                             for k, v in param_scopes.items()},
            "valid_until": valid_until or "2099-01-01T00:00:00+00:00",
            "ts": _now(),
        }
        return WorldKey(
            issuer_id=self._world_id,
            subject_id=subject_id,
            tier=tier,
            param_scopes=param_scopes,
            valid_until=body["valid_until"],
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )

    # -- Branch request ---------------------------------------

    def request_branch(self, request: BranchRequest):
        """The world decides whether to accept. Returns one of:
            (BranchSeed, new_world) — accepted
            RefusalRecord            — refused
            None                     — silent drop (should not happen)
        """
        # 1. Request signature
        if not verify_branch_request(request):
            return self._refuse(request, "invalid_request_signature")
        # 2. Branch point must match current state
        if request.branch_point_hash != self._last_hash:
            return self._refuse(request, "stale_branch_point")
        # 3. Sandbox
        if self._template.branch_policy is None:
            return self._refuse(request, "sandboxed")
        # 4. World-key checks
        wk = request.world_key
        if wk.issuer_id != self._world_id:
            return self._refuse(request, "foreign_world_key")
        if not verify_world_key(wk, self._world_id):
            return self._refuse(request, "invalid_world_key")
        if wk.subject_id != request.requested_by:
            return self._refuse(request,
                                "world_key_subject_mismatch")
        if wk.valid_until < _now():
            return self._refuse(request, "expired_world_key")
        if wk.tier not in self._template.branch_policy:
            return self._refuse(request, "insufficient_tier")
        allowed = self._template.branch_policy[wk.tier]
        # 5. Per-param checks
        for param, value in request.requested_params.items():
            if param not in PARAM_NAMES:
                return self._refuse(request,
                                    f"unknown_param:{param}")
            if param not in allowed:
                return self._refuse(request,
                                    f"param_not_allowed:{param}")
            lo, hi = allowed[param]
            if not (lo <= value <= hi):
                return self._refuse(
                    request, f"template_range:{param}")
            if param in wk.param_scopes:
                wlo, whi = wk.param_scopes[param]
                if not (wlo <= value <= whi):
                    return self._refuse(
                        request, f"world_key_scope:{param}")
        # 6. All checks pass — create the branch
        return self._accept_branch(request)

    def _accept_branch(self, request):
        # Child generates its own keypair.
        child_kp = Ed25519PrivateKey.generate()
        child_id = _did_from_kp(child_kp)
        new_params = self._params.with_overrides(
            request.requested_params)
        seed_body = {
            "type": "branch_seed",
            "new_world_id": child_id,
            "parent_id": self._world_id,
            "parent_branch_hash": self._last_hash,
            "template_hash": self._template.template_hash(),
            "params": new_params.to_dict(),
            "inherited_segments": [list(s) for s in self._segments],
            "initial_frontier": [list(t) for t in self._frontier],
            "pot": list(self._pot),
            "ts": _now(),
        }
        sig_parent = self._keypair.sign(
            _canonical(seed_body)).hex()
        sig_branch = child_kp.sign(
            _canonical(seed_body)).hex()
        seed = BranchSeed(
            new_world_id=child_id,
            parent_id=self._world_id,
            parent_branch_hash=self._last_hash,
            template_hash=self._template.template_hash(),
            params=new_params.to_dict(),
            inherited_segments=list(self._segments),
            initial_frontier=list(self._frontier),
            pot=self._pot,
            ts=seed_body["ts"],
            sig_parent=sig_parent,
            sig_branch=sig_branch,
        )
        # Record the branch in the parent's log.
        body = {
            "type": "branch",
            "world_id": self._world_id,
            "step": self._steps,
            "branch_seed": seed.to_dict(),
            "prior": self._last_hash,
            "ts": seed_body["ts"],
        }
        rec = BranchRecord(
            world_id=self._world_id,
            step=self._steps,
            branch_seed_dict=seed.to_dict(),
            prior=self._last_hash,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        child = AtomicFractalWorld.from_branch(
            seed, child_kp, self._template)
        return (seed, child)

    def _refuse(self, request, reason):
        body = {
            "type": "refusal",
            "world_id": self._world_id,
            "step": self._steps,
            "request_hash": request.request_hash(),
            "requester_id": request.requested_by,
            "reason": reason,
            "prior": self._last_hash,
            "ts": _now(),
        }
        rec = RefusalRecord(
            world_id=self._world_id,
            step=self._steps,
            request_hash=request.request_hash(),
            requester_id=request.requested_by,
            reason=reason,
            prior=self._last_hash,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        return rec


# =====================================================================
# Verification
# =====================================================================

def _verify_signature_body(did, body, sig):
    try:
        pub = _pubkey_from_did(did)
        pub.verify(bytes.fromhex(sig), _canonical(body))
        return True
    except Exception:
        return False


def verify_world_log(world: AtomicFractalWorld) -> Tuple[bool, str]:
    """Verify a world's log against its own seed and key.

    Checks:
      - seed sig
      - every record's signature
      - every record's prior chain
      - every growth record's p == params.param_hash()
        (inertia: all growth shares one params hash, because
        params never change in place)
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed_body = world.seed_body()
    if seed_body.get("type") == "seed":
        # Fresh world
        if not _verify_signature_body(
                world.world_id, seed_body, world.seed_sig()):
            return (False, "seed signature invalid")
    else:
        # Branch world
        branch_seed = BranchSeed(
            new_world_id=seed_body["new_world_id"],
            parent_id=seed_body["parent_id"],
            parent_branch_hash=seed_body["parent_branch_hash"],
            template_hash=seed_body["template_hash"],
            params=seed_body["params"],
            inherited_segments=[tuple(s)
                                for s in seed_body["inherited_segments"]],
            initial_frontier=[tuple(t)
                              for t in seed_body["initial_frontier"]],
            pot=tuple(seed_body["pot"]),
            ts=seed_body["ts"],
            sig_parent=seed_body.get("sig_parent", ""),
            sig_branch=seed_body.get("sig_branch", world.seed_sig()),
        )
        # Note: seed_body might not carry sig_parent; from_branch
        # only sets _seed_sig. Full chain verification of the
        # branch seed is a separate call (verify_branch_seed).
    prev = None
    params_hash = world.params.param_hash()
    for i, rec in enumerate(world.records()):
        if rec.world_id != world.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prior != prev:
            return (False, f"record {i}: prior mismatch")
        if not _verify_signature_body(
                world.world_id, rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, GrowthRecord):
            if rec.seed_hash != world.seed_hash():
                return (False, f"record {i}: seed_hash mismatch")
            if rec.p != params_hash:
                return (False, f"record {i}: params hash "
                               f"changed in place")
        elif isinstance(rec, BranchRecord):
            # The embedded seed must be verifiable
            bs = rec.seed()
            if not verify_branch_seed(bs):
                return (False, f"record {i}: branch seed "
                               f"signature invalid")
            if bs.parent_branch_hash != rec.prior:
                return (False, f"record {i}: branch seed "
                               f"parent_branch_hash mismatch")
            if bs.template_hash != world._template.template_hash():
                return (False, f"record {i}: branch seed "
                               f"template mismatch")
        elif isinstance(rec, RefusalRecord):
            pass  # Refusals are not otherwise validated
        else:
            return (False, f"record {i}: unknown type")
        prev = rec.record_hash()
    return (True, "log verifies")


def verify_growth(world: AtomicFractalWorld) -> Tuple[bool, str]:
    """Verify that every growth record is a valid application
    of the rule under the (constant) params."""
    ok, reason = verify_world_log(world)
    if not ok:
        return (False, reason)
    # Start from the seed's inherited state
    seed_body = world.seed_body()
    if seed_body.get("type") == "seed":
        expected = [(seed_body["initial_tip"][0],
                     seed_body["initial_tip"][1],
                     seed_body["initial_tip"][2], 0)]
    else:
        expected = [tuple(t) for t in
                    seed_body["initial_frontier"]]
    pot = tuple(seed_body["pot"])
    params = world.params
    for i, rec in enumerate(world.records()):
        if isinstance(rec, GrowthRecord):
            exp_segs, exp_tips = advance(expected, params, pot)
            if sorted(rec.segs) != sorted(exp_segs):
                return (False, f"record {i}: segs mismatch")
            if sorted(rec.tips) != sorted(exp_tips):
                return (False, f"record {i}: tips mismatch")
            expected = exp_tips
        # Param/refusal/branch records don't affect growth state
    return (True, "growth verifies")


# =====================================================================
# Reconstruct
# =====================================================================

@dataclass
class Plant:
    pot: Tuple[int, int, int, int]
    segments: List[Tuple[int, int, int, int]]
    frontier: List[Tuple[int, int, int, int]]
    params: ParamSet
    steps: int
    branches_issued: int
    refusals_logged: int


def reconstruct(world: AtomicFractalWorld) -> Plant:
    seed_body = world.seed_body()
    if seed_body.get("type") == "seed":
        segments = []
        frontier = [(seed_body["initial_tip"][0],
                     seed_body["initial_tip"][1],
                     seed_body["initial_tip"][2], 0)]
    else:
        segments = [tuple(s)
                    for s in seed_body["inherited_segments"]]
        frontier = [tuple(t)
                    for t in seed_body["initial_frontier"]]
    steps = branches = refusals = 0
    for rec in world.records():
        if isinstance(rec, GrowthRecord):
            segments.extend(rec.segs)
            frontier = rec.tips
            steps += 1
        elif isinstance(rec, BranchRecord):
            branches += 1
        elif isinstance(rec, RefusalRecord):
            refusals += 1
    return Plant(pot=world._pot, segments=segments,
                 frontier=frontier, params=world.params,
                 steps=steps, branches_issued=branches,
                 refusals_logged=refusals)


def render_ascii(plant, width=40, height=20):
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
