"""
botanical_garden.py — The botanical garden as a superworld.

Proposal sketch, not a course step. The three-level test:

    plant (atomic) < garden (composite) < botanical garden (superworld)

The pattern is identical at all three levels:
  seed -> rule -> boundary -> log
The content changes. This is the fractality principle demonstrated
at three scales.

What the superworld governs (its law):

  - Rain: the superworld receives rain on its roof.
  - Dispatch: roof water is dispatched to gardens by a policy
    (by_gutter: each garden gets the water from its gutter's
    x-range on the roof's bottom row).
  - Opening hours: a record that visitors are admitted or not
    (recorded, not enforced yet -- visitors are a future layer).
  - Branching: same protocol as garden and plant.

What the superworld does NOT govern:

  - Plant growth (delegated to each plant's own rule).
  - Garden-internal water flow, soak, and evaporation (delegated
    to each garden's own tick).
  - Light (a garden-level param; the superworld does not touch it).

The superworld is pure coordination. It decides "who gets how
much rain" and lets each garden simulate. Composition rule at the
top level: superworld governs interaction, delegates simulation.

Requires one small change to FractalGarden (shown below): tick()
takes an optional external_rain list. The garden's log records it.
The garden's replay applies it. The garden remains self-contained.

Simplifications (marked for the standard's review):

  - `sig` fields are flat, not W3C DataIntegrityProof objects.
  - Key names in body() should be checked against the schema.
  - Full inheritance on branch: the branch copies every garden's
    water grid and every plant's geometry. Production should use
    record-chain inheritance (store each garden's seed_hash and
    last_hash; reconstruct by replay when needed).
  - Gutters are 1:1 with garden columns (gutter width == garden
    water width). Production should support wider gutters
    (multiple roof cells per garden cell) and narrower ones.
  - Environmental inputs (rain) are accepted unconditionally.
    Refusal is reserved for governance requests (branch), not
    weather. Future work: a garden could refuse water if its law
    says so.
  - No visitor records yet. Opening hours are stored but unused.
  - No cross-superworld messaging. The Commons (a superworld of
    rooms) is the next stage after this.
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

from fractal_garden import (
    FractalGarden, GardenTemplate, SlotRect, PlantAssignment,
    GardenTick, GardenBranchRecord, GardenRefusalRecord,
    GARDEN_PARAM_NAMES, verify_garden_log, verify_garden_replay)
from water_particles import (
    WaterGrid, W_MAX, _fall, _flow, _hash_int)
from fractal_world_v3 import (
    WorldKey, verify_world_key, TIERS,
    _did_from_kp, _pubkey_from_did, _canonical, _hash, _now)


SUPER_PARAM_NAMES = ("rain_rate", "dispatch_policy",
                     "opening_hours_start", "opening_hours_end")
DISPATCH_POLICIES = ("by_gutter", "equal")


# =====================================================================
# GardenSpec — one garden inside the botanical garden
# =====================================================================

@dataclass(frozen=True)
class GardenSpec:
    slot_id: str
    garden_template: GardenTemplate
    plant_assignments: List[PlantAssignment]
    gutter_x_start: int
    gutter_x_end: int

    def to_dict(self):
        return {
            "slot_id": self.slot_id,
            "garden_template": self.garden_template.to_dict(),
            "plant_assignments": [a.to_dict()
                                  for a in self.plant_assignments],
            "gutter_x_start": self.gutter_x_start,
            "gutter_x_end": self.gutter_x_end,
        }


# =====================================================================
# BotanicalTemplate
# =====================================================================

@dataclass(frozen=True)
class BotanicalTemplate:
    template_id: str
    roof_width: int
    roof_height: int
    garden_specs: List[GardenSpec]
    rain_rate: int = 64
    dispatch_policy: str = "by_gutter"
    opening_hours: Tuple[int, int] = (9, 17)
    branch_policy: Optional[Dict] = None

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "roof_width": self.roof_width,
            "roof_height": self.roof_height,
            "garden_specs": [s.to_dict()
                             for s in self.garden_specs],
            "rain_rate": self.rain_rate,
            "dispatch_policy": self.dispatch_policy,
            "opening_hours": list(self.opening_hours),
            "branch_policy": self.branch_policy,
        }

    def template_hash(self):
        return _hash(self.to_dict())


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class BotanicalSeed:
    world_id: str
    template_hash: str
    garden_ids: Dict[str, str]
    garden_seed_hashes: Dict[str, str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "botanical_seed",
            "world_id": self.world_id,
            "template_hash": self.template_hash,
            "garden_ids": dict(self.garden_ids),
            "garden_seed_hashes": dict(self.garden_seed_hashes),
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class BotanicalTick:
    world_id: str
    step: int
    t: int
    prev: Optional[str]
    roof_rain: List[Tuple[int, int, int]]
    roof_moves: List[Tuple[int, int, int, int, int]]
    dispatch: Dict[str, List[Tuple[int, int, int]]]
    garden_hashes: Dict[str, Dict[str, Optional[str]]]
    roof_level_hash: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "botanical_tick",
            "world_id": self.world_id,
            "step": self.step,
            "t": self.t,
            "prev": self.prev,
            "roof_rain": [list(r) for r in self.roof_rain],
            "roof_moves": [list(m) for m in self.roof_moves],
            "dispatch": {sid: [[a, b, c] for (a, b, c) in share]
                         for sid, share in self.dispatch.items()},
            "garden_hashes": {
                sid: {"last_hash": v["last_hash"],
                      "level_hash": v["level_hash"]}
                for sid, v in self.garden_hashes.items()},
            "roof_level_hash": self.roof_level_hash,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class BotanicalBranchRecord:
    world_id: str
    step: int
    t: int
    branch_seed_dict: Dict
    prior: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "botanical_branch",
            "world_id": self.world_id,
            "step": self.step,
            "t": self.t,
            "branch_seed": dict(self.branch_seed_dict),
            "prior": self.prior,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class BotanicalRefusalRecord:
    world_id: str
    step: int
    t: int
    request_hash: str
    requester_id: str
    reason: str
    prior: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "botanical_refusal",
            "world_id": self.world_id,
            "step": self.step,
            "t": self.t,
            "request_hash": self.request_hash,
            "requester_id": self.requester_id,
            "reason": self.reason,
            "prior": self.prior,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class BotanicalBranchRequest:
    parent_id: str
    branch_point_hash: str
    requested_params: Dict[str, int]
    requested_by: str
    world_key: WorldKey
    ts: str
    sig: str

    def body(self):
        return {
            "type": "botanical_branch_request",
            "parent_id": self.parent_id,
            "branch_point_hash": self.branch_point_hash,
            "requested_params": dict(self.requested_params),
            "requested_by": self.requested_by,
            "world_key": self.world_key.to_dict(),
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


def sign_botanical_branch_request(parent_id, branch_point_hash,
                                   requested_params, requester_kp,
                                   world_key, ts=None):
    requester_id = _did_from_kp(requester_kp)
    body = {
        "type": "botanical_branch_request",
        "parent_id": parent_id,
        "branch_point_hash": branch_point_hash,
        "requested_params": dict(requested_params),
        "requested_by": requester_id,
        "world_key": world_key.to_dict(),
        "ts": ts or _now(),
    }
    sig = requester_kp.sign(_canonical(body)).hex()
    return BotanicalBranchRequest(
        parent_id=parent_id,
        branch_point_hash=branch_point_hash,
        requested_params=dict(requested_params),
        requested_by=requester_id,
        world_key=world_key,
        ts=body["ts"],
        sig=sig)


def verify_botanical_branch_request(request):
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
# BotanicalGarden
# =====================================================================

class BotanicalGarden:
    def __init__(self, template: BotanicalTemplate, keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._template = template
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._roof = WaterGrid.empty(
            template.roof_width, template.roof_height)
        self._gardens: Dict[str, FractalGarden] = {}
        self._records: List[Union[BotanicalTick,
                                   BotanicalBranchRecord,
                                   BotanicalRefusalRecord]] = []
        self._last_hash: Optional[str] = None
        self._step = 0
        self._tick = 0
        for spec in template.garden_specs:
            self._gardens[spec.slot_id] = FractalGarden(
                spec.garden_template, spec.plant_assignments,
                Ed25519PrivateKey.generate())
        seed_body = {
            "type": "botanical_seed",
            "world_id": self._world_id,
            "template_hash": template.template_hash(),
            "garden_ids": {sid: g.world_id
                           for sid, g in self._gardens.items()},
            "garden_seed_hashes": {sid: g.seed_hash()
                                    for sid, g in self._gardens.items()},
            "ts": _now(),
        }
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(_canonical(seed_body)).hex()

    # -- Accessors ------------------------------------------------

    @property
    def world_id(self):
        return self._world_id

    @property
    def template(self):
        return self._template

    @property
    def roof(self):
        return self._roof

    def gardens(self):
        return dict(self._gardens)

    def records(self):
        return list(self._records)

    def seed(self):
        return {**self._seed_body, "sig": self._seed_sig}

    def seed_hash(self):
        return _hash(self._seed_body)

    def last_hash(self):
        return self._last_hash

    # -- Tick --------------------------------------------------

    def tick(self) -> BotanicalTick:
        t = self._tick
        tmpl = self._template

        # 1. Rain on roof
        roof_rain = []
        for x in range(tmpl.roof_width):
            if _hash_int(self._world_id, "rain", x, t) < tmpl.rain_rate:
                if self._roof.add(x, 0, 1) > 0:
                    roof_rain.append((x, 0, 1))

        # 2. Fall on roof
        roof_moves = _fall(self._roof, self._world_id, t)

        # 3. Dispatch from roof's bottom row to each garden's
        #    top row, capped by the garden cell's remaining
        #    capacity. Excess stays on the roof for the next tick.
        bottom = tmpl.roof_height - 2
        dispatch: Dict[str, List[Tuple[int, int, int]]] = {}
        for spec in tmpl.garden_specs:
            share = []
            garden = self._gardens[spec.slot_id]
            for rx in range(spec.gutter_x_start, spec.gutter_x_end):
                n = self._roof.get(rx, bottom)
                if n <= 0:
                    continue
                gx = rx - spec.gutter_x_start
                if not (0 <= gx < garden.grid.width):
                    continue
                avail = W_MAX - garden.grid.get(gx, 0)
                take = min(n, avail)
                if take > 0:
                    share.append((gx, 0, take))
                    self._roof.remove(rx, bottom, take)
            dispatch[spec.slot_id] = share

        # 4. Tick each garden with its external rain
        garden_hashes = {}
        for spec in tmpl.garden_specs:
            garden = self._gardens[spec.slot_id]
            rec = garden.tick(external_rain=dispatch[spec.slot_id])
            garden_hashes[spec.slot_id] = {
                "last_hash": garden.last_hash(),
                "level_hash": rec.level_hash,
            }

        # 5. Record
        body = {
            "type": "botanical_tick",
            "world_id": self._world_id,
            "step": self._step,
            "t": t,
            "prev": self._last_hash,
            "roof_rain": [list(r) for r in roof_rain],
            "roof_moves": [list(m) for m in roof_moves],
            "dispatch": {sid: [[a, b, c] for (a, b, c) in share]
                         for sid, share in dispatch.items()},
            "garden_hashes": garden_hashes,
            "roof_level_hash": _hash(self._roof.levels),
            "ts": _now(),
        }
        rec = BotanicalTick(
            world_id=self._world_id, step=self._step, t=t,
            prev=self._last_hash,
            roof_rain=roof_rain, roof_moves=roof_moves,
            dispatch=dispatch, garden_hashes=garden_hashes,
            roof_level_hash=body["roof_level_hash"],
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex())
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        self._step += 1
        self._tick += 1
        return rec

    def run(self, ticks=10):
        for _ in range(ticks):
            self.tick()
        return ticks

    # -- World-key issuance ------------------------------------

    def issue_world_key(self, subject_id, tier,
                        param_scopes=None, valid_until=None):
        if tier not in TIERS:
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
            sig=self._keypair.sign(_canonical(body)).hex())

    # -- Branch ------------------------------------------------

    def request_branch(self, request: BotanicalBranchRequest):
        if not verify_botanical_branch_request(request):
            return self._refuse(request, "invalid_request_signature")
        if request.branch_point_hash != self._last_hash:
            return self._refuse(request, "stale_branch_point")
        if self._template.branch_policy is None:
            return self._refuse(request, "sandboxed")
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
        for param, value in request.requested_params.items():
            if param not in SUPER_PARAM_NAMES:
                return self._refuse(request,
                                    f"unknown_param:{param}")
            if param not in allowed:
                return self._refuse(request,
                                    f"param_not_allowed:{param}")
            lo, hi = allowed[param]
            if not (lo <= value <= hi):
                return self._refuse(request,
                                    f"template_range:{param}")
            if param in wk.param_scopes:
                wlo, whi = wk.param_scopes[param]
                if not (wlo <= value <= whi):
                    return self._refuse(
                        request, f"world_key_scope:{param}")
        return self._accept_branch(request)

    def _accept_branch(self, request):
        tmpl = self._template
        child_kp = Ed25519PrivateKey.generate()
        child_id = _did_from_kp(child_kp)

        # Build new template with overrides
        new_params = {
            "rain_rate": tmpl.rain_rate,
            "opening_hours": tmpl.opening_hours,
        }
        for k, v in request.requested_params.items():
            if k == "opening_hours_start":
                new_params["opening_hours"] = (
                    v, tmpl.opening_hours[1])
            elif k == "opening_hours_end":
                new_params["opening_hours"] = (
                    tmpl.opening_hours[0], v)
            else:
                new_params[k] = v
        # Garden templates are copied with rain_rate=0 (the
        # superworld supplies rain). The branch does not change
        # garden-internal params.
        new_specs = []
        for spec in tmpl.garden_specs:
            gt = spec.garden_template
            # On branch, garden keeps its own params. Note that
            # dispatch_policy / rain_rate overrides are superworld-
            # level only; they do not touch garden templates.
            new_specs.append(spec)
        new_template = BotanicalTemplate(
            template_id=tmpl.template_id,
            roof_width=tmpl.roof_width,
            roof_height=tmpl.roof_height,
            garden_specs=new_specs,
            rain_rate=new_params["rain_rate"],
            dispatch_policy=new_params.get(
                "dispatch_policy", tmpl.dispatch_policy),
            opening_hours=new_params["opening_hours"],
            branch_policy=tmpl.branch_policy)

        # Collect inherited garden state (full inheritance for
        # the demo; record-chain recommended for production)
        inherited_gardens = {}
        for sid, g in self._gardens.items():
            inherited_gardens[sid] = {
                "water_init": [list(r) for r in g.grid.levels],
                "plant_segments": {
                    p_sid: [list(s) for s in p.segments()]
                    for p_sid, p in g.plants().items()},
                "plant_frontier": {
                    p_sid: [list(t) for t in p.frontier()]
                    for p_sid, p in g.plants().items()},
                "plant_params": {
                    p_sid: p.params.to_dict()
                    for p_sid, p in g.plants().items()},
                "energy": g.energy(),
            }

        body = {
            "type": "botanical_branch_seed",
            "new_world_id": child_id,
            "parent_id": self._world_id,
            "parent_branch_hash": self._last_hash,
            "template_hash": new_template.template_hash(),
            "inherited_gardens": inherited_gardens,
            "params": {
                "rain_rate": new_template.rain_rate,
                "dispatch_policy": new_template.dispatch_policy,
                "opening_hours": list(new_template.opening_hours),
            },
            "ts": _now(),
        }
        sig_parent = self._keypair.sign(
            _canonical(body)).hex()
        sig_branch = child_kp.sign(_canonical(body)).hex()
        body["sig_parent"] = sig_parent
        body["sig_branch"] = sig_branch

        rec_body = {
            "type": "botanical_branch",
            "world_id": self._world_id,
            "step": self._step,
            "t": self._tick,
            "branch_seed": body,
            "prior": self._last_hash,
            "ts": body["ts"],
        }
        rec = BotanicalBranchRecord(
            world_id=self._world_id, step=self._step,
            t=self._tick, branch_seed_dict=body,
            prior=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(
                _canonical(rec_body)).hex())
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        self._step += 1

        child = BotanicalGarden.from_branch(
            body, child_kp, new_template)
        return (body, child)

    @classmethod
    def from_branch(cls, branch_seed_body, keypair, template):
        obj = cls.__new__(cls)
        obj._template = template
        obj._keypair = keypair
        obj._world_id = branch_seed_body["new_world_id"]
        obj._roof = WaterGrid.empty(
            template.roof_width, template.roof_height)
        obj._gardens = {}
        obj._records = []
        obj._last_hash = None
        obj._step = 0
        obj._tick = 0
        obj._seed_body = branch_seed_body
        obj._seed_sig = branch_seed_body["sig_branch"]
        for spec in template.garden_specs:
            inh = branch_seed_body["inherited_gardens"][spec.slot_id]
            gt = spec.garden_template
            # Build a new garden with inherited water and plant
            # geometry. Each plant gets a fresh key (its parent
            # continues separately in the parent superworld).
            new_plants = []
            for p_sid, params in inh["plant_params"].items():
                slot = next((s for s in gt.slot_rects
                             if s.slot_id == p_sid), None)
                if slot is None:
                    continue
                # Initial tip: pick a point at the bottom center
                tip = (slot.x + slot.w // 2, slot.y + slot.h - 3, 0)
                new_plants.append(PlantAssignment(
                    slot_id=p_sid, initial_tip=tip,
                    plant_params=params))
            new_garden = FractalGarden(
                gt, new_plants, Ed25519PrivateKey.generate())
            # Overwrite inherited water
            new_garden._grid = WaterGrid(
                width=gt.water_width,
                height=gt.water_height,
                levels=[list(r) for r in inh["water_init"]])
            # Overwrite inherited plant geometry and energy
            for p_sid, segs in inh["plant_segments"].items():
                p = new_garden._plants.get(p_sid)
                if p is None:
                    continue
                p._segments = [tuple(s) for s in segs]
                p._frontier = [tuple(t) for t in
                               inh["plant_frontier"][p_sid]]
            for p_sid, e in inh["energy"].items():
                if p_sid in new_garden._energy:
                    new_garden._energy[p_sid] = e
            obj._gardens[spec.slot_id] = new_garden
        return obj

    def _refuse(self, request, reason):
        body = {
            "type": "botanical_refusal",
            "world_id": self._world_id,
            "step": self._step,
            "t": self._tick,
            "request_hash": request.request_hash(),
            "requester_id": request.requested_by,
            "reason": reason,
            "prior": self._last_hash,
            "ts": _now(),
        }
        rec = BotanicalRefusalRecord(
            world_id=self._world_id, step=self._step,
            t=self._tick,
            request_hash=request.request_hash(),
            requester_id=request.requested_by,
            reason=reason, prior=self._last_hash,
            ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex())
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        self._step += 1
        return rec


# =====================================================================
# Verification
# =====================================================================

def verify_botanical_log(garden: BotanicalGarden) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = garden.seed()
    seed_body = {k: v for k, v in seed.items() if k != "sig"}
    try:
        _pubkey_from_did(garden.world_id).verify(
            bytes.fromhex(seed["sig"]), _canonical(seed_body))
    except Exception as e:
        return (False, f"seed signature invalid: {e}")
    pub = _pubkey_from_did(garden.world_id)
    prev = None
    for i, rec in enumerate(garden.records()):
        if rec.world_id != garden.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        try:
            pub.verify(bytes.fromhex(rec.sig),
                       _canonical(rec.body()))
        except Exception as e:
            return (False, f"record {i}: signature invalid: {e}")
        prev = rec.record_hash()
    return (True, "log verifies")


def verify_botanical_cross(
        garden: BotanicalGarden) -> Tuple[bool, str]:
    """Cross-check: each garden's ext_rain records should match
    the superworld's dispatch records for the same tick. This
    is the superworld-level consistency check that the garden's
    own replay cannot do (the garden trusts its ext_rain; only
    the superworld knows whether the dispatch matches)."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    ok, reason = verify_botanical_log(garden)
    if not ok:
        return (False, reason)
    # Index garden ticks by (garden_id, t)
    garden_ticks: Dict[Tuple[str, int], GardenTick] = {}
    for sid, g in garden.gardens().items():
        for rec in g.records():
            if isinstance(rec, GardenTick):
                garden_ticks[(sid, rec.t)] = rec
    for i, rec in enumerate(garden.records()):
        if not isinstance(rec, BotanicalTick):
            continue
        for sid, share in rec.dispatch.items():
            gt = garden_ticks.get((sid, rec.t))
            if gt is None:
                return (False,
                        f"record {i}: missing garden tick "
                        f"{sid}/{rec.t}")
            if sorted(gt.ext_rain) != sorted(
                    tuple(s) for s in share):
                return (False,
                        f"record {i}: dispatch/ext_rain mismatch "
                        f"for {sid}/{rec.t}")
    return (True, "cross-check verifies")


# =====================================================================
# Render
# =====================================================================

def render_botanical(garden: BotanicalGarden) -> str:
    lines = []
    lines.append("ROOF:")
    for y in range(garden.roof.height - 1):
        row = []
        for x in range(garden.roof.width):
            v = garden.roof.get(x, y)
            row.append("." if v == 0 else
                       ("W" if v >= W_MAX else str(v)))
        lines.append("  " + "".join(row))
    lines.append("=" * (garden.roof.width + 2))
    for spec in garden.template.garden_specs:
        g = garden.gardens()[spec.slot_id]
        lines.append(f"GARDEN {spec.slot_id}:")
        for y in range(g.grid.height - 1):
            row = []
            for x in range(g.grid.width):
                v = g.grid.get(x, y)
                row.append("." if v == 0 else
                           ("W" if v >= W_MAX else str(v)))
            lines.append("  " + "".join(row))
        lines.append("  " + "=" * g.grid.width)
    return "\n".join(lines)


def render_energy(garden: BotanicalGarden) -> str:
    parts = []
    for spec in garden.template.garden_specs:
        g = garden.gardens()[spec.slot_id]
        parts.append(f"{spec.slot_id}: {g.energy()}")
    return " | ".join(parts)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    """Two gardens under a botanical garden's roof. Rain falls
    on the roof, dispatches to gardens, plants grow. Alice
    (control) requests a branch with more rain; Bob (observe)
    is refused. Parent and branch continue independently.

    Verifies: superworld log, garden logs, and the cross-check
    that dispatch matches ext_rain."""
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "botanical_garden"
    path.mkdir(parents=True, exist_ok=True)

    def make_garden_template(tid):
        return GardenTemplate(
            template_id=tid,
            slot_rects=[SlotRect("p1", 1, 3, 10, 10)],
            water_width=12, water_height=12,
            rain_rate=0,   # superworld supplies rain
            evap_rate=20,
            water_max=8, energy_cap=30, growth_cost=1,
            light_level=10,
            branch_policy=None)  # gardens under superworld are sandboxed

    spec_a = GardenSpec(
        slot_id="garden-a",
        garden_template=make_garden_template("garden-a-v1"),
        plant_assignments=[PlantAssignment(
            "p1", (5, 10, 0),
            {"branch_length": 2, "max_depth": 3,
             "water": 10, "light": 10})],
        gutter_x_start=0, gutter_x_end=12)
    spec_b = GardenSpec(
        slot_id="garden-b",
        garden_template=make_garden_template("garden-b-v1"),
        plant_assignments=[PlantAssignment(
            "p1", (5, 10, 0),
            {"branch_length": 2, "max_depth": 3,
             "water": 10, "light": 10})],
        gutter_x_start=12, gutter_x_end=24)

    template = BotanicalTemplate(
        template_id="botanical-v1",
        roof_width=24, roof_height=4,
        garden_specs=[spec_a, spec_b],
        rain_rate=96,
        dispatch_policy="by_gutter",
        opening_hours=(9, 17),
        branch_policy={
            "control": {"rain_rate": (32, 160)},
            "terminal": {"rain_rate": (16, 160),
                         "opening_hours_start": (0, 23),
                         "opening_hours_end": (0, 23)},
        })
    kp = Ed25519PrivateKey.generate()
    botanical = BotanicalGarden(template, kp)

    alice_kp = Ed25519PrivateKey.generate()
    bob_kp = Ed25519PrivateKey.generate()
    alice_key = botanical.issue_world_key(
        _did_from_kp(alice_kp), "control")
    bob_key = botanical.issue_world_key(
        _did_from_kp(bob_kp), "observe")

    log = []
    # [1] Grow 10 ticks
    botanical.run(10)
    snap1 = render_botanical(botanical)
    log.append(("grow", f"10 ticks, energy: "
                        f"{render_energy(botanical)}"))

    # [2] Bob (observe) refused
    req_b = sign_botanical_branch_request(
        botanical.world_id, botanical.last_hash(),
        {"rain_rate": 128}, bob_kp, bob_key)
    res_b = botanical.request_branch(req_b)
    if isinstance(res_b, BotanicalRefusalRecord):
        log.append(("refused", f"Bob: {res_b.reason}"))
    else:
        log.append(("ERROR", "Bob should have been refused"))

    # [3] Alice (control) accepted
    req_a = sign_botanical_branch_request(
        botanical.world_id, botanical.last_hash(),
        {"rain_rate": 128}, alice_kp, alice_key)
    res_a = botanical.request_branch(req_a)
    branch = None
    if isinstance(res_a, tuple):
        seed_a, branch = res_a
        log.append(("accepted",
                    f"Alice: branch {branch.world_id[:24]}... "
                    f"rain_rate=128"))
    else:
        log.append(("ERROR", f"Alice: {res_a.reason}"))

    # [4] Continue both
    botanical.run(8)
    if branch:
        branch.run(8)
    snap2 = render_botanical(botanical)
    snap3 = render_botanical(branch) if branch else "(none)"
    log.append(("grow", f"parent 8 more: "
                        f"{render_energy(botanical)}"))
    if branch:
        log.append(("grow", f"branch 8 ticks: "
                            f"{render_energy(branch)}"))

    # [5] Verify
    checks = {}
    for name, g in (("parent", botanical),
                     ("branch", branch)):
        if g is None:
            continue
        v_log = verify_botanical_log(g)
        v_cross = verify_botanical_cross(g)
        checks[name] = {
            "log_valid": v_log[0], "log_reason": v_log[1],
            "cross_valid": v_cross[0], "cross_reason": v_cross[1],
        }
        for sid, sub_garden in g.gardens().items():
            gl = verify_garden_log(sub_garden)
            gr = verify_garden_replay(sub_garden)
            checks[name][f"{sid}_log"] = gl[0]
            checks[name][f"{sid}_replay"] = gr[0]

    print("=" * 74)
    print("Botanical Garden — the superworld, three levels deep")
    print("=" * 74)
    print()
    print(f"  Superworld: {botanical.world_id[:28]}...")
    if branch:
        print(f"  Branch:     {branch.world_id[:28]}...")
    print()
    print("  Sequence:")
    for kind, note in log:
        marker = {"grow": "·", "accepted": "✓",
                  "refused": "✗", "ERROR": "!"}[kind]
        print(f"    {marker} {note}")
    print()
    print("  Parent after 10 ticks:")
    for line in snap1.split("\n"):
        print(f"    {line}")
    print()
    print("  Parent after 18 ticks:")
    for line in snap2.split("\n"):
        print(f"    {line}")
    print(f"    energy: {render_energy(botanical)}")
    print()
    if branch:
        print("  Branch after 8 ticks:")
        for line in snap3.split("\n"):
            print(f"    {line}")
        print(f"    energy: {render_energy(branch)}")
        print()
    print("  Verification (offline):")
    for name, c in checks.items():
        print(f"    {name}: log={c['log_valid']}  "
              f"cross={c['cross_valid']}")
        for sid in c:
            if sid.endswith("_log"):
                print(f"      {sid[:-4]}: log={c[sid]}  "
                      f"replay={c.get(sid[:-4] + '_replay')}")
    print()
    print("  What this establishes:")
    print("    - The botanical garden is a superworld. It owns the")
    print("      roof, dispatches rain to gardens, and delegates")
    print("      everything else.")
    print("    - Gardens under a superworld have rain_rate=0 and")
    print("      accept external_rain from the superworld. Their")
    print("      logs stay self-contained (ext_rain is in each tick).")
    print("    - The cross-check matches dispatch in the")
    print("      superworld's log to ext_rain in the garden's log.")
    print("    - The pattern is identical at all three levels:")
    print("      seed -> rule -> boundary -> log.")
    print("    - A branch of the superworld inherits every garden's")
    print("      water and plant geometry, gets new superworld")
    print("      params, and continues independently.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'To make a prairie it takes a clover and one bee,'")
    print("    'One clover, and a bee,'")
    print("    'And revery.'")
    print("    'The revery alone will do,'")
    print("    'If bees are few.'")

    audit = {
        "parent_id": botanical.world_id,
        "branch_id": branch.world_id if branch else None,
        "sequence": [{"kind": k, "note": n} for k, n in log],
        "parent_energy": render_energy(botanical),
        "branch_energy": render_energy(branch) if branch else None,
        "parent_params": botanical.template.to_dict(),
        "verification": checks,
        "snapshots": {"after_10": snap1, "after_18": snap2,
                      "branch_after_8": snap3},
    }
    (path / "botanical_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/botanical_demo.json")
    return audit
