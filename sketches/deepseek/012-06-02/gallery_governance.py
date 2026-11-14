"""
gallery_governance.py — the interior/exterior gallery.

A composite world with a governed exterior.

Interior:  members, cycles, cross-checks. Unchanged from
           gallery_world.py.
Exterior:  world-keys, signed requests, signed refusals.

Policy has two fields:
  max_members     int
  allowed_kinds   tuple of strings

World-key tiers gate operations:
  observe     — no changes
  communicate — no changes (future: message a member)
  control     — can add and retire members
  terminal    — control + can change policy

Requests carry a world-key issued by this gallery. The gallery
accepts or refuses. Refusals are signed records — no silent
failures.

Keeper can act directly (bypassing the request path) — the
keeper *is* the gallery's key. Both paths are logged; direct
records carry `request=None`, request records carry the full
signed request and its hash.

Port note: hex sigs, bespoke records, no HPKE. Port to Rust
would use formats::proof, records-v1.schema.json, base58.
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
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from gallery_world import (
    GalleryMember, GalleryWorld,
    AtomicFractalMember, FractalGridMember,
    ChaosGameMember, CoupledCAMember,
    verify_seed_cert,
)


TIERS = ("observe", "communicate", "control", "terminal")
TIER_RANK = {t: i for i, t in enumerate(TIERS)}


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
    except Exception:
        return False


# =====================================================================
# Policy
# =====================================================================

@dataclass(frozen=True)
class GalleryPolicy:
    max_members: int
    allowed_kinds: Tuple[str, ...]

    def __post_init__(self):
        if self.max_members < 0:
            raise ValueError("max_members must be >= 0")
        for k in self.allowed_kinds:
            if not isinstance(k, str) or not k:
                raise ValueError(f"bad kind {k!r}")

    def to_dict(self):
        return {"max_members": int(self.max_members),
                "allowed_kinds": sorted(self.allowed_kinds)}

    def policy_hash(self):
        return _hash(self.to_dict())

    def allows_kind(self, kind):
        return kind in self.allowed_kinds


# =====================================================================
# World-key
# =====================================================================

@dataclass(frozen=True)
class GalleryWorldKey:
    issuer_id: str
    subject_id: str
    tier: str
    valid_until: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "gallery_world_key",
            "issuer_id": self.issuer_id,
            "subject_id": self.subject_id,
            "tier": self.tier,
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
            valid_until=d["valid_until"],
            ts=d["ts"],
            sig=d["sig"],
        )


def verify_world_key(world_key, expected_issuer=None):
    if not HAS_CRYPTO:
        return False
    try:
        if expected_issuer is not None \
                and world_key.issuer_id != expected_issuer:
            return False
        if world_key.tier not in TIER_RANK:
            return False
        return _verify_sig(world_key.issuer_id,
                            world_key.body(), world_key.sig)
    except Exception:
        return False


def world_key_has_tier(world_key, required):
    return TIER_RANK.get(world_key.tier, -1) \
            >= TIER_RANK[required]


# =====================================================================
# Requests
# =====================================================================

@dataclass(frozen=True)
class AddMemberRequest:
    world_id: str
    slot: int
    member_kind: str
    member_id: str
    member_seed_hash: str
    requester_id: str
    world_key: GalleryWorldKey
    ts: str
    sig: str

    def body(self):
        return {
            "type": "add_member_request",
            "world_id": self.world_id,
            "slot": int(self.slot),
            "member_kind": self.member_kind,
            "member_id": self.member_id,
            "member_seed_hash": self.member_seed_hash,
            "requester_id": self.requester_id,
            "world_key": self.world_key.to_dict(),
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class RetireMemberRequest:
    world_id: str
    slot: int
    member_id: str
    reason: str
    requester_id: str
    world_key: GalleryWorldKey
    ts: str
    sig: str

    def body(self):
        return {
            "type": "retire_member_request",
            "world_id": self.world_id,
            "slot": int(self.slot),
            "member_id": self.member_id,
            "reason": self.reason,
            "requester_id": self.requester_id,
            "world_key": self.world_key.to_dict(),
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class ChangePolicyRequest:
    world_id: str
    new_policy: Dict
    requester_id: str
    world_key: GalleryWorldKey
    ts: str
    sig: str

    def body(self):
        return {
            "type": "change_policy_request",
            "world_id": self.world_id,
            "new_policy": dict(self.new_policy),
            "requester_id": self.requester_id,
            "world_key": self.world_key.to_dict(),
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


def _sign_request(body, requester_kp):
    sig = requester_kp.sign(_canonical(body)).hex()
    return sig


def sign_add_member(world_id, slot, member, requester_kp,
                     world_key):
    body = {
        "type": "add_member_request",
        "world_id": world_id,
        "slot": int(slot),
        "member_kind": member.kind,
        "member_id": member.world_id(),
        "member_seed_hash": _hash(member.seed_body()),
        "requester_id": _did_from_kp(requester_kp),
        "world_key": world_key.to_dict(),
        "ts": _now(),
    }
    sig = _sign_request(body, requester_kp)
    return AddMemberRequest(
        world_id=world_id, slot=slot,
        member_kind=member.kind,
        member_id=member.world_id(),
        member_seed_hash=body["member_seed_hash"],
        requester_id=body["requester_id"],
        world_key=world_key, ts=body["ts"], sig=sig,
    )


def sign_retire_member(world_id, slot, member_id, reason,
                        requester_kp, world_key):
    body = {
        "type": "retire_member_request",
        "world_id": world_id,
        "slot": int(slot),
        "member_id": member_id,
        "reason": reason,
        "requester_id": _did_from_kp(requester_kp),
        "world_key": world_key.to_dict(),
        "ts": _now(),
    }
    sig = _sign_request(body, requester_kp)
    return RetireMemberRequest(
        world_id=world_id, slot=slot,
        member_id=member_id, reason=reason,
        requester_id=body["requester_id"],
        world_key=world_key, ts=body["ts"], sig=sig,
    )


def sign_change_policy(world_id, new_policy, requester_kp,
                        world_key):
    body = {
        "type": "change_policy_request",
        "world_id": world_id,
        "new_policy": new_policy,
        "requester_id": _did_from_kp(requester_kp),
        "world_key": world_key.to_dict(),
        "ts": _now(),
    }
    sig = _sign_request(body, requester_kp)
    return ChangePolicyRequest(
        world_id=world_id, new_policy=dict(new_policy),
        requester_id=body["requester_id"],
        world_key=world_key, ts=body["ts"], sig=sig,
    )


def _verify_request(request, gallery_id):
    """Signature + world-key validity. Tier check is separate."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if request.world_id != gallery_id:
        return (False, "request targets another gallery")
    if not _verify_sig(request.requester_id,
                        request.body(), request.sig):
        return (False, "request signature invalid")
    wk = request.world_key
    if wk.issuer_id != gallery_id:
        return (False, "world-key not issued by this gallery")
    if not verify_world_key(wk, gallery_id):
        return (False, "world-key signature invalid")
    if wk.subject_id != request.requester_id:
        return (False, "world-key subject mismatch")
    if wk.valid_until <= request.ts:
        return (False, "world-key expired")
    return (True, "request valid")


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class GallerySeedRecord:
    world_id: str
    initial_policy: Dict
    ts: str
    sig: str

    def body(self):
        return {"type": "gallery_seed",
                "world_id": self.world_id,
                "initial_policy": dict(self.initial_policy),
                "ts": self.ts}

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class PolicyChangeRecord:
    world_id: str
    old_policy_hash: str
    new_policy: Dict
    new_policy_hash: str
    request: Optional[Dict]
    request_hash: Optional[str]
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "policy_change",
            "world_id": self.world_id,
            "old_policy_hash": self.old_policy_hash,
            "new_policy": dict(self.new_policy),
            "new_policy_hash": self.new_policy_hash,
            "request": self.request,
            "request_hash": self.request_hash,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class MemberAddedRecord:
    world_id: str
    slot: int
    member_id: str
    member_kind: str
    seed_cert: Dict
    request: Optional[Dict]
    request_hash: Optional[str]
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "member_added",
            "world_id": self.world_id,
            "slot": int(self.slot),
            "member_id": self.member_id,
            "member_kind": self.member_kind,
            "seed_cert": dict(self.seed_cert),
            "request": self.request,
            "request_hash": self.request_hash,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class MemberRetiredRecord:
    world_id: str
    slot: int
    member_id: str
    reason: str
    request: Optional[Dict]
    request_hash: Optional[str]
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "member_retired",
            "world_id": self.world_id,
            "slot": int(self.slot),
            "member_id": self.member_id,
            "reason": self.reason,
            "request": self.request,
            "request_hash": self.request_hash,
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
class RequestRefusedRecord:
    world_id: str
    request_hash: str
    request_type: str
    requester_id: str
    reason: str
    request: Dict
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "request_refused",
            "world_id": self.world_id,
            "request_hash": self.request_hash,
            "request_type": self.request_type,
            "requester_id": self.requester_id,
            "reason": self.reason,
            "request": dict(self.request),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# GovernedGalleryWorld
# =====================================================================

class GovernedGalleryWorld:
    def __init__(self, keypair, policy):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._policy = policy
        self._members = {}
        self._records = []
        self._cycle = 0
        self._last_hash = None
        seed_body = {
            "type": "gallery_seed",
            "world_id": self._world_id,
            "initial_policy": policy.to_dict(),
            "ts": _now(),
        }
        self._seed_body = seed_body
        self._seed_sig = keypair.sign(
            _canonical(seed_body)).hex()

    @property
    def world_id(self):
        return self._world_id

    def policy(self):
        return self._policy

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

    # -- Key issuance (keeper only) ------------------------

    def issue_world_key(self, subject_id, tier,
                         valid_until=None):
        if tier not in TIER_RANK:
            raise ValueError(f"unknown tier {tier!r}")
        body = {
            "type": "gallery_world_key",
            "issuer_id": self._world_id,
            "subject_id": subject_id,
            "tier": tier,
            "valid_until": (valid_until
                             or "2099-01-01T00:00:00+00:00"),
            "ts": _now(),
        }
        return GalleryWorldKey(
            issuer_id=self._world_id,
            subject_id=subject_id, tier=tier,
            valid_until=body["valid_until"],
            ts=body["ts"],
            sig=self._keypair.sign(
                _canonical(body)).hex(),
        )

    # -- Keeper-direct operations -------------------------

    def add(self, slot, member):
        """Direct addition by keeper. Bypasses request path."""
        if slot in self._members:
            return None
        if not self._policy.allows_kind(member.kind):
            return None
        if len(self._members) >= self._policy.max_members:
            return None
        cert = {
            "kind": member.kind,
            "world_id": member.world_id(),
            "seed_body": member.seed_body(),
            "seed_sig": member.seed_sig(),
        }
        body = {
            "type": "member_added",
            "world_id": self._world_id,
            "slot": int(slot),
            "member_id": member.world_id(),
            "member_kind": member.kind,
            "seed_cert": cert,
            "request": None, "request_hash": None,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MemberAddedRecord(
            world_id=self._world_id, slot=slot,
            member_id=member.world_id(),
            member_kind=member.kind,
            seed_cert=cert,
            request=None, request_hash=None,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._members[slot] = member
        self._last_hash = rec.record_hash()
        return rec

    def retire(self, slot, reason=""):
        if slot not in self._members:
            return None
        member = self._members[slot]
        body = {
            "type": "member_retired",
            "world_id": self._world_id,
            "slot": int(slot),
            "member_id": member.world_id(),
            "reason": reason,
            "request": None, "request_hash": None,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MemberRetiredRecord(
            world_id=self._world_id, slot=slot,
            member_id=member.world_id(), reason=reason,
            request=None, request_hash=None,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        del self._members[slot]
        self._last_hash = rec.record_hash()
        return rec

    def change_policy(self, new_policy):
        """Direct policy change by keeper."""
        if not isinstance(new_policy, GalleryPolicy):
            return None
        body = {
            "type": "policy_change",
            "world_id": self._world_id,
            "old_policy_hash": self._policy.policy_hash(),
            "new_policy": new_policy.to_dict(),
            "new_policy_hash": new_policy.policy_hash(),
            "request": None, "request_hash": None,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = PolicyChangeRecord(
            world_id=self._world_id,
            old_policy_hash=self._policy.policy_hash(),
            new_policy=new_policy.to_dict(),
            new_policy_hash=new_policy.policy_hash(),
            request=None, request_hash=None,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._policy = new_policy
        self._last_hash = rec.record_hash()
        return rec

    # -- Exterior: request path --------------------------

    def request_add(self, request, member):
        ok, reason = _verify_request(request, self._world_id)
        if not ok:
            return self._refuse(request, "add_member_request",
                                 reason)
        if not world_key_has_tier(request.world_key, "control"):
            return self._refuse(request, "add_member_request",
                                 "insufficient tier")
        if request.member_id != member.world_id():
            return self._refuse(request, "add_member_request",
                                 "member id mismatch")
        if request.member_kind != member.kind:
            return self._refuse(request, "add_member_request",
                                 "member kind mismatch")
        if request.member_seed_hash != _hash(member.seed_body()):
            return self._refuse(request, "add_member_request",
                                 "member seed hash mismatch")
        if not self._policy.allows_kind(member.kind):
            return self._refuse(request, "add_member_request",
                                 f"kind {member.kind!r} "
                                 f"not allowed by policy")
        if request.slot in self._members:
            return self._refuse(request, "add_member_request",
                                 f"slot {request.slot} occupied")
        if len(self._members) >= self._policy.max_members:
            return self._refuse(request, "add_member_request",
                                 f"capacity {self._policy.max_members}"
                                 f" reached")
        cert = {
            "kind": member.kind,
            "world_id": member.world_id(),
            "seed_body": member.seed_body(),
            "seed_sig": member.seed_sig(),
        }
        body = {
            "type": "member_added",
            "world_id": self._world_id,
            "slot": int(request.slot),
            "member_id": member.world_id(),
            "member_kind": member.kind,
            "seed_cert": cert,
            "request": request.body(),
            "request_hash": request.request_hash(),
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MemberAddedRecord(
            world_id=self._world_id, slot=request.slot,
            member_id=member.world_id(),
            member_kind=member.kind,
            seed_cert=cert,
            request=request.body(),
            request_hash=request.request_hash(),
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._members[request.slot] = member
        self._last_hash = rec.record_hash()
        return rec

    def request_retire(self, request):
        ok, reason = _verify_request(request, self._world_id)
        if not ok:
            return self._refuse(request, "retire_member_request",
                                 reason)
        if not world_key_has_tier(request.world_key, "control"):
            return self._refuse(request, "retire_member_request",
                                 "insufficient tier")
        if request.slot not in self._members:
            return self._refuse(request, "retire_member_request",
                                 f"slot {request.slot} empty")
        member = self._members[request.slot]
        if member.world_id() != request.member_id:
            return self._refuse(request, "retire_member_request",
                                 "member id mismatch")
        body = {
            "type": "member_retired",
            "world_id": self._world_id,
            "slot": int(request.slot),
            "member_id": member.world_id(),
            "reason": request.reason,
            "request": request.body(),
            "request_hash": request.request_hash(),
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MemberRetiredRecord(
            world_id=self._world_id, slot=request.slot,
            member_id=member.world_id(),
            reason=request.reason,
            request=request.body(),
            request_hash=request.request_hash(),
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        del self._members[request.slot]
        self._last_hash = rec.record_hash()
        return rec

    def request_change_policy(self, request):
        ok, reason = _verify_request(request, self._world_id)
        if not ok:
            return self._refuse(request,
                                 "change_policy_request", reason)
        if not world_key_has_tier(request.world_key, "terminal"):
            return self._refuse(request,
                                 "change_policy_request",
                                 "insufficient tier")
        try:
            new_policy = GalleryPolicy(
                max_members=request.new_policy["max_members"],
                allowed_kinds=tuple(
                    request.new_policy["allowed_kinds"]))
        except (KeyError, ValueError, TypeError) as e:
            return self._refuse(request,
                                 "change_policy_request",
                                 f"malformed policy: {e}")
        body = {
            "type": "policy_change",
            "world_id": self._world_id,
            "old_policy_hash": self._policy.policy_hash(),
            "new_policy": new_policy.to_dict(),
            "new_policy_hash": new_policy.policy_hash(),
            "request": request.body(),
            "request_hash": request.request_hash(),
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = PolicyChangeRecord(
            world_id=self._world_id,
            old_policy_hash=self._policy.policy_hash(),
            new_policy=new_policy.to_dict(),
            new_policy_hash=new_policy.policy_hash(),
            request=request.body(),
            request_hash=request.request_hash(),
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._policy = new_policy
        self._last_hash = rec.record_hash()
        return rec

    def _refuse(self, request, request_type, reason):
        body = {
            "type": "request_refused",
            "world_id": self._world_id,
            "request_hash": request.request_hash(),
            "request_type": request_type,
            "requester_id": request.requester_id,
            "reason": reason,
            "request": request.body(),
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = RequestRefusedRecord(
            world_id=self._world_id,
            request_hash=request.request_hash(),
            request_type=request_type,
            requester_id=request.requester_id,
            reason=reason,
            request=request.body(),
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        return rec

    # -- Interior: cycles --------------------------------

    def grow(self):
        advances = []
        for slot in sorted(self._members):
            member = self._members[slot]
            result = member.grow()
            steps = 0 if result is None else 1
            advances.append({
                "slot": slot,
                "member_id": member.world_id(),
                "member_kind": member.kind,
                "steps_taken": steps,
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
            advances=tuple(advances),
            prev=self._last_hash, ts=body["ts"],
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

def verify_governed_log(gallery):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = gallery.seed_body()
    if not _verify_sig(gallery.world_id, seed,
                        gallery.seed_sig()):
        return (False, "seed signature invalid")
    try:
        policy = GalleryPolicy(
            max_members=seed["initial_policy"]["max_members"],
            allowed_kinds=tuple(
                seed["initial_policy"]["allowed_kinds"]))
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed initial policy: {e}")
    occupied = {}
    cycle = 0
    prev = None
    refused_hashes = set()
    accepted_hashes = set()
    for i, rec in enumerate(gallery.records()):
        if rec.world_id != gallery.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_sig(gallery.world_id,
                            rec.body(), rec.sig):
            return (False, f"record {i}: signature invalid")
        if isinstance(rec, PolicyChangeRecord):
            if rec.old_policy_hash != policy.policy_hash():
                return (False, f"record {i}: old_policy mismatch")
            try:
                new_policy = GalleryPolicy(
                    max_members=rec.new_policy["max_members"],
                    allowed_kinds=tuple(
                        rec.new_policy["allowed_kinds"]))
            except (KeyError, ValueError, TypeError):
                return (False, f"record {i}: malformed policy")
            if new_policy.policy_hash() != rec.new_policy_hash:
                return (False,
                         f"record {i}: new_policy hash mismatch")
            if rec.request_hash is not None:
                if rec.request_hash in accepted_hashes \
                        or rec.request_hash in refused_hashes:
                    return (False,
                             f"record {i}: request hash reused")
                ok, reason = _verify_embedded_request(
                    rec.request, gallery.world_id,
                    "change_policy_request")
                if not ok:
                    return (False,
                             f"record {i}: {reason}")
                accepted_hashes.add(rec.request_hash)
            policy = new_policy
        elif isinstance(rec, MemberAddedRecord):
            if rec.slot in occupied:
                return (False,
                         f"record {i}: slot occupied")
            if not verify_seed_cert(rec.seed_cert):
                return (False,
                         f"record {i}: seed cert invalid")
            if rec.seed_cert["kind"] != rec.member_kind:
                return (False,
                         f"record {i}: cert kind mismatch")
            if not policy.allows_kind(rec.member_kind):
                return (False,
                         f"record {i}: kind not allowed at "
                         f"this point in the log")
            if len(occupied) >= policy.max_members:
                return (False,
                         f"record {i}: capacity exceeded at "
                         f"this point in the log")
            if rec.request_hash is not None:
                if rec.request_hash in accepted_hashes \
                        or rec.request_hash in refused_hashes:
                    return (False,
                             f"record {i}: request hash reused")
                ok, reason = _verify_embedded_request(
                    rec.request, gallery.world_id,
                    "add_member_request")
                if not ok:
                    return (False,
                             f"record {i}: {reason}")
                accepted_hashes.add(rec.request_hash)
            occupied[rec.slot] = rec.member_id
        elif isinstance(rec, MemberRetiredRecord):
            if occupied.get(rec.slot) != rec.member_id:
                return (False,
                         f"record {i}: retirement mismatch")
            if rec.request_hash is not None:
                if rec.request_hash in accepted_hashes \
                        or rec.request_hash in refused_hashes:
                    return (False,
                             f"record {i}: request hash reused")
                ok, reason = _verify_embedded_request(
                    rec.request, gallery.world_id,
                    "retire_member_request")
                if not ok:
                    return (False,
                             f"record {i}: {reason}")
                accepted_hashes.add(rec.request_hash)
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
        elif isinstance(rec, RequestRefusedRecord):
            if rec.request_hash in refused_hashes:
                # duplicate refusal is fine — no-op
                pass
            elif rec.request_hash in accepted_hashes:
                return (False,
                         f"record {i}: refused a request "
                         f"already accepted")
            else:
                refused_hashes.add(rec.request_hash)
                ok, reason = _verify_embedded_request(
                    rec.request, gallery.world_id,
                    rec.request_type)
                if not ok:
                    return (False,
                             f"record {i}: {reason}")
            if rec.requester_id != rec.request.get(
                    "requester_id"):
                return (False,
                         f"record {i}: requester mismatch")
        else:
            return (False, f"record {i}: unknown type")
        prev = rec.record_hash()
    return (True, "governed log verifies")


def _verify_embedded_request(request_dict, gallery_id,
                               expected_type):
    """Verify a request that was embedded in a record."""
    if not isinstance(request_dict, dict):
        return (False, "request not a dict")
    if request_dict.get("type") != expected_type:
        return (False,
                 f"request type {request_dict.get('type')!r} "
                 f"!= {expected_type!r}")
    if request_dict.get("world_id") != gallery_id:
        return (False, "request targets another gallery")
    try:
        wk = GalleryWorldKey.from_dict(
            request_dict["world_key"])
    except (KeyError, ValueError):
        return (False, "malformed world-key")
    if wk.issuer_id != gallery_id:
        return (False, "world-key not issued by this gallery")
    if not verify_world_key(wk, gallery_id):
        return (False, "world-key invalid")
    if wk.subject_id != request_dict["requester_id"]:
        return (False, "world-key subject mismatch")
    if wk.valid_until <= request_dict["ts"]:
        return (False, "world-key expired at request time")
    # Verify request's own signature
    body = {k: v for k, v in request_dict.items()
             if k != "sig"}
    sig = request_dict.get("sig", "")
    if not _verify_sig(request_dict["requester_id"],
                        body, sig):
        return (False, "request signature invalid")
    return (True, "request verifies")


def verify_governed_members(gallery):
    claimed = {}
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
                     f"slot {slot}: log: {vlog[1]}")
        vgrow = member.verify_growth()
        if not vgrow[0]:
            return (False,
                     f"slot {slot}: growth: {vgrow[1]}")
        claim = claimed.get(member.world_id(), 0)
        actual = member.steps()
        if claim != actual:
            return (False,
                     f"slot {slot}: claims {claim}, "
                     f"actual {actual}")
    return (True, "members verify")


def verify_governed_full(gallery):
    v = verify_governed_log(gallery)
    if not v[0]:
        return (False, f"log: {v[1]}")
    v = verify_governed_members(gallery)
    if not v[0]:
        return (False, f"members: {v[1]}")
    return (True, "full verification passes")


# =====================================================================
# Rendering
# =====================================================================

def render_governed(gallery):
    lines = []
    p = gallery.policy()
    lines.append(f"  policy: max_members={p.max_members}  "
                  f"allowed_kinds={sorted(p.allowed_kinds)}")
    lines.append("")
    if not gallery.members():
        lines.append("  (interior is empty)")
        return "\n".join(lines)
    for slot in sorted(gallery.members()):
        m = gallery.members()[slot]
        lines.append(f"  slot {slot}: {m.kind}  "
                      f"steps={m.steps()}")
    return "\n".join(lines)


def refusal_trail(gallery):
    lines = []
    for i, rec in enumerate(gallery.records()):
        if isinstance(rec, RequestRefusedRecord):
            lines.append(
                f"    [{i}] {rec.request_type} from "
                f"{rec.requester_id[:20]}...: {rec.reason}")
    return "\n".join(lines) if lines else "    (no refusals)"


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json
    from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
    from fractal_grid_world import FractalGridWorld, GridParams
    from chaos_game_world import ChaosGameWorld, SIERPINSKI
    from coupled_ca_world import CoupledCAWorld
    from gallery_world import (
        AtomicFractalMember, FractalGridMember,
        ChaosGameMember, CoupledCAMember,
    )

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "gallery_governance"
    path.mkdir(parents=True, exist_ok=True)

    keeper_kp = Ed25519PrivateKey.generate()
    initial_policy = GalleryPolicy(
        max_members=3,
        allowed_kinds=("atomic_fractal", "fractal_grid",
                        "chaos_game", "coupled_ca"))
    gallery = GovernedGalleryWorld(keeper_kp, initial_policy)

    # External actors
    curator_x_kp = Ed25519PrivateKey.generate()
    curator_x_id = _did_from_kp(curator_x_kp)
    curator_y_kp = Ed25519PrivateKey.generate()
    curator_y_id = _did_from_kp(curator_y_kp)
    curator_z_kp = Ed25519PrivateKey.generate()
    curator_z_id = _did_from_kp(curator_z_kp)

    key_x = gallery.issue_world_key(curator_x_id, "control")
    key_y = gallery.issue_world_key(curator_y_id, "observe")
    key_z = gallery.issue_world_key(curator_z_id, "terminal")

    # Build the four kinds of members
    plant_world = AtomicFractalWorld(
        template=WorldTemplate(
            template_id="gallery-plant",
            branch_length=2, max_depth=2),
        pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
        keypair=Ed25519PrivateKey.generate())
    plant = AtomicFractalMember(plant_world)

    grid_world = FractalGridWorld(
        params=GridParams(rule_number=90, max_gen=8),
        initial_row=[0],
        keypair=Ed25519PrivateKey.generate())
    grid = FractalGridMember(grid_world, max_gen=8)

    chaos_world = ChaosGameWorld(
        preset=SIERPINSKI, growth_mode="seeded_random",
        initial_point=(500, 500),
        keypair=Ed25519PrivateKey.generate(),
        prng_seed=0xFEED)
    chaos = ChaosGameMember(chaos_world, max_steps=30)

    ca_world = CoupledCAWorld(
        rule_a=90, rule_b=90,
        initial_a=[0], initial_b=[12],
        k_a=50, k_b=50,
        keypair=Ed25519PrivateKey.generate())
    ca = CoupledCAMember(ca_world, max_gen=10)

    log = []

    # 1. Keeper adds plant and grid directly
    gallery.add(0, plant)
    log.append(("keeper", "add slot 0: atomic_fractal"))
    gallery.add(1, grid)
    log.append(("keeper", "add slot 1: fractal_grid"))

    # 2. Curator X (control) requests to add chaos to slot 2
    req = sign_add_member(
        gallery.world_id, 2, chaos,
        curator_x_kp, key_x)
    result = gallery.request_add(req, chaos)
    log.append((
        "accepted" if isinstance(result, MemberAddedRecord)
        else "refused",
        f"Curator X add slot 2: chaos_game"
        f" → {getattr(result, 'reason', 'accepted')}"))

    # 3. Curator Y (observe) requests to add CA to slot 3
    req = sign_add_member(
        gallery.world_id, 3, ca,
        curator_y_kp, key_y)
    result = gallery.request_add(req, ca)
    log.append((
        "refused" if isinstance(result, RequestRefusedRecord)
        else "accepted",
        f"Curator Y add slot 3: coupled_ca"
        f" → {getattr(result, 'reason', 'accepted')}"))

    # 4. Curator X requests slot 3 — but capacity is 3 already
    req = sign_add_member(
        gallery.world_id, 3, ca,
        curator_x_kp, key_x)
    result = gallery.request_add(req, ca)
    log.append((
        "refused" if isinstance(result, RequestRefusedRecord)
        else "accepted",
        f"Curator X add slot 3: capacity test"
        f" → {getattr(result, 'reason', 'accepted')}"))

    # 5. Grow — three members
    gallery.grow_n(10)

    # 6. Curator Z (terminal) requests policy change
    new_policy_dict = GalleryPolicy(
        max_members=5,
        allowed_kinds=("atomic_fractal", "fractal_grid",
                        "chaos_game", "coupled_ca")
    ).to_dict()
    req = sign_change_policy(
        gallery.world_id, new_policy_dict,
        curator_z_kp, key_z)
    result = gallery.request_change_policy(req)
    log.append((
        "accepted" if isinstance(result, PolicyChangeRecord)
        else "refused",
        f"Curator Z change policy to max_members=5"
        f" → {getattr(result, 'reason', 'accepted')}"))

    # 7. Curator X retries slot 3 — should succeed now
    req = sign_add_member(
        gallery.world_id, 3, ca,
        curator_x_kp, key_x)
    result = gallery.request_add(req, ca)
    log.append((
        "accepted" if isinstance(result, MemberAddedRecord)
        else "refused",
        f"Curator X add slot 3 after policy change"
        f" → {getattr(result, 'reason', 'accepted')}"))

    # 8. More growth — four members now
    gallery.grow_n(5)

    # 9. Curator X retires the chaos member (control can retire)
    chaos_id = gallery.members()[2].world_id()
    req = sign_retire_member(
        gallery.world_id, 2, chaos_id, "session over",
        curator_x_kp, key_x)
    result = gallery.request_retire(req)
    log.append((
        "accepted" if isinstance(result, MemberRetiredRecord)
        else "refused",
        f"Curator X retire slot 2"
        f" → {getattr(result, 'reason', 'accepted')}"))

    gallery.grow_n(3)

    v_log = verify_governed_log(gallery)
    v_mem = verify_governed_members(gallery)
    v_full = verify_governed_full(gallery)

    print("=" * 74)
    print("The Governed Gallery — interior, exterior, and refusal")
    print("=" * 74)
    print()
    print(f"  Gallery:  {gallery.world_id[:32]}...")
    print(f"  Cycles:   {gallery.cycle()}")
    print(f"  Members:  {len(gallery.members())}")
    print()
    print("  Sequence:")
    for kind, msg in log:
        marker = {"keeper": "·", "accepted": "✓",
                   "refused": "✗"}[kind]
        print(f"    {marker} {msg}")
    print()
    print("  Interior (current state):")
    print(render_governed(gallery))
    print()
    print("  Exterior refusal trail:")
    print(refusal_trail(gallery))
    print()
    print("  Verification:")
    print(f"    log:      {v_log[0]}  ({v_log[1]})")
    print(f"    members:  {v_mem[0]}  ({v_mem[1]})")
    print(f"    full:     {v_full[0]}  ({v_full[1]})")
    print()
    print("  What this establishes:")
    print("    - The gallery has a governed exterior: world-keys,")
    print("      tiers, signed requests, signed refusals.")
    print("    - Keeper can act directly (add, retire, change")
    print("      policy) — bypassing the request path. Both paths")
    print("      are logged. Keeper is the gallery's key.")
    print("    - External actors submit signed requests with a")
    print("      world-key. Tier gates which operations they can")
    print("      request. Policy gates what gets accepted.")
    print("    - Refusals are signed records with specific")
    print("      reasons. No silent failures.")
    print("    - Policy changes are themselves governed — terminal")
    print("      tier only. Old and new policy hashes are in the")
    print("      log, so a verifier reconstructs policy state")
    print("      across changes.")
    print("    - The interior is unchanged: members grow, cycles")
    print("      advance, cross-checks pass. Governance is a")
    print("      layer over the same composite.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Soul selects her own Society –'")
    print("    'Then – shuts the Door –'")

    audit = {
        "gallery_id": gallery.world_id,
        "cycles": gallery.cycle(),
        "policy_final": gallery.policy().to_dict(),
        "members": [
            {"slot": s, "kind": m.kind,
             "member_id": m.world_id(), "steps": m.steps()}
            for s, m in sorted(gallery.members().items())
        ],
        "refusal_count": sum(
            1 for r in gallery.records()
            if isinstance(r, RequestRefusedRecord)),
        "verification": {
            "log": v_log[0],
            "members": v_mem[0],
            "full": v_full[0],
        },
    }
    (path / "gallery_governance_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/gallery_governance_demo.json")
    return audit
