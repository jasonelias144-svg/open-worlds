"""
map_governance.py — world-keys and pin request records for the map.

The map registry is a fold of the map's log. Each mutation
(pin added, pin removed) is a signed log entry. External actors
must present a world-key issued by the map; the map checks it
and countersigns the log entry.

Tier model:
  observe — can read the registry
  edit    — can add and remove pins

The map itself is the implicit "admin" — its keeper key signs
its own acts directly, no world-key required.

Honest limits:
  - No "map.admin" tier yet. Changing the map's policy or
    keeper is out of scope; this cycle governs pins only.
  - World-keys don't carry per-pin scoping. An "edit" key can
    remove any pin, not just ones the same actor added. A
    future scoped tier would be small.
  - No revocation of world-keys. Same pattern as
    gallery_governance — expiry is the only revocation.
  - Request timestamps are self-reported by the actor. Clock
    skew across actors is not corrected; documented.
"""

import json
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)


TIERS = ("observe", "edit")
TIER_RANK = {"observe": 0, "edit": 1}
DEFAULT_REQUIRED_TIER = "edit"


# =====================================================================
# MapWorldKey
# =====================================================================

@dataclass(frozen=True)
class MapWorldKey:
    issuer_id: str
    subject_id: str
    tier: str
    valid_until: str
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "kind": "map_world_key",
            "issuer_id": self.issuer_id,
            "subject_id": self.subject_id,
            "tier": self.tier,
            "valid_until": self.valid_until,
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    @classmethod
    def from_dict(cls, d: Dict) -> "MapWorldKey":
        return cls(
            issuer_id=d["issuer_id"],
            subject_id=d["subject_id"],
            tier=d["tier"],
            valid_until=d["valid_until"],
            ts=d["ts"], sig=d["sig"],
        )


def sign_world_key(
    map_kp, map_id: str, subject_id: str, tier: str,
    valid_until: Optional[str] = None,
) -> MapWorldKey:
    if tier not in TIER_RANK:
        raise ValueError(f"bad tier {tier!r}; valid: {TIERS}")
    ts = _now()
    vu = valid_until or "2099-01-01T00:00:00+00:00"
    body = {
        "kind": "map_world_key",
        "issuer_id": map_id,
        "subject_id": subject_id,
        "tier": tier,
        "valid_until": vu,
        "ts": ts,
    }
    sig = map_kp.sign(_canonical(body)).hex()
    return MapWorldKey(
        issuer_id=map_id, subject_id=subject_id,
        tier=tier, valid_until=vu, ts=ts, sig=sig,
    )


def verify_world_key(
    wk: MapWorldKey,
    expected_issuer: Optional[str] = None,
) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(wk, MapWorldKey):
        return (False, "not a MapWorldKey")
    if expected_issuer is not None \
            and wk.issuer_id != expected_issuer:
        return (False, "issuer mismatch")
    if wk.tier not in TIER_RANK:
        return (False, f"bad tier {wk.tier!r}")
    try:
        _pubkey_from_did(wk.issuer_id).verify(
            bytes.fromhex(wk.sig), _canonical(wk.body()))
        return (True, "ok")
    except Exception:
        return (False, "sig invalid")


def tier_covers(granted: str, required: str) -> bool:
    return TIER_RANK.get(granted, -1) \
            >= TIER_RANK.get(required, -1)


# =====================================================================
# Requests
# =====================================================================

@dataclass(frozen=True)
class PinAddedRequest:
    actor_id: str
    pin: Dict
    world_key: Dict
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "kind": "pin_added_request",
            "actor_id": self.actor_id,
            "pin": dict(self.pin),
            "world_key": dict(self.world_key),
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    @classmethod
    def from_dict(cls, d: Dict) -> "PinAddedRequest":
        return cls(
            actor_id=d["actor_id"],
            pin=dict(d["pin"]),
            world_key=dict(d["world_key"]),
            ts=d["ts"], sig=d["sig"],
        )


def sign_pin_added_request(
    actor_kp, world_key: MapWorldKey, pin: Dict,
) -> PinAddedRequest:
    actor_id = _did_from_kp(actor_kp)
    ts = _now()
    body = {
        "kind": "pin_added_request",
        "actor_id": actor_id,
        "pin": dict(pin),
        "world_key": world_key.to_dict(),
        "ts": ts,
    }
    sig = actor_kp.sign(_canonical(body)).hex()
    return PinAddedRequest(
        actor_id=actor_id, pin=dict(pin),
        world_key=world_key.to_dict(),
        ts=ts, sig=sig,
    )


@dataclass(frozen=True)
class PinRemovedRequest:
    actor_id: str
    world_id: str
    world_key: Dict
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "kind": "pin_removed_request",
            "actor_id": self.actor_id,
            "world_id": self.world_id,
            "world_key": dict(self.world_key),
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    @classmethod
    def from_dict(cls, d: Dict) -> "PinRemovedRequest":
        return cls(
            actor_id=d["actor_id"],
            world_id=d["world_id"],
            world_key=dict(d["world_key"]),
            ts=d["ts"], sig=d["sig"],
        )


def sign_pin_removed_request(
    actor_kp, world_key: MapWorldKey, world_id: str,
) -> PinRemovedRequest:
    actor_id = _did_from_kp(actor_kp)
    ts = _now()
    body = {
        "kind": "pin_removed_request",
        "actor_id": actor_id,
        "world_id": world_id,
        "world_key": world_key.to_dict(),
        "ts": ts,
    }
    sig = actor_kp.sign(_canonical(body)).hex()
    return PinRemovedRequest(
        actor_id=actor_id, world_id=world_id,
        world_key=world_key.to_dict(),
        ts=ts, sig=sig,
    )


def verify_request_signature(request) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    try:
        _pubkey_from_did(request.actor_id).verify(
            bytes.fromhex(request.sig),
            _canonical(request.body()))
        return (True, "ok")
    except Exception:
        return (False, "sig invalid")


def verify_request_authorization(
    request, map_signer_id: str,
    required_tier: str = DEFAULT_REQUIRED_TIER,
) -> Tuple[bool, str]:
    try:
        wk = MapWorldKey.from_dict(request.world_key)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed world_key: {e}")
    ok, reason = verify_world_key(wk, expected_issuer=map_signer_id)
    if not ok:
        return (False, f"world_key: {reason}")
    if wk.subject_id != request.actor_id:
        return (False, "world_key.subject_id != actor_id")
    if not tier_covers(wk.tier, required_tier):
        return (False,
                 f"tier {wk.tier!r} does not cover "
                 f"{required_tier!r}")
    if wk.valid_until <= request.ts:
        return (False, "world_key expired at request time")
    return (True, "ok")
