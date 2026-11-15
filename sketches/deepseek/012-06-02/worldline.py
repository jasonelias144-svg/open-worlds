"""
worldline.py — an individual's path through the multiverse.

A WorldlineSummary is the individual's signed claim about
their own history: the ordered list of worlds they've entered.
Built from a bundle's memory (world_entry records); signed by
the individual's key.

An AnnotatedWorldline is the map's signed view of that claim:
each visit augmented with the map's knowledge (cluster,
current status, whether the world is directly registered or
reached via a sub-map). The map's signature confirms it
produced the annotation; the individual's signature (carried
inside) confirms they made the original claim.

Verification: two signatures. Both must pass.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle,
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)


@dataclass(frozen=True)
class WorldVisit:
    world_id: str
    tier: str
    first_memory_index: int
    entered_at_ts: str

    def to_dict(self) -> Dict:
        return {
            "world_id": self.world_id,
            "tier": self.tier,
            "first_memory_index": self.first_memory_index,
            "entered_at_ts": self.entered_at_ts,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "WorldVisit":
        return cls(
            world_id=d["world_id"],
            tier=d["tier"],
            first_memory_index=int(d["first_memory_index"]),
            entered_at_ts=d.get("entered_at_ts", ""),
        )


@dataclass(frozen=True)
class WorldlineSummary:
    individual_id: str
    visits: Tuple[WorldVisit, ...]
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "kind": "worldline_summary",
            "individual_id": self.individual_id,
            "visits": [v.to_dict() for v in self.visits],
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    @classmethod
    def from_dict(cls, d: Dict) -> "WorldlineSummary":
        return cls(
            individual_id=d["individual_id"],
            visits=tuple(WorldVisit.from_dict(v)
                          for v in d["visits"]),
            ts=d["ts"], sig=d["sig"],
        )


def worldline_from_bundle(
    bundle: IndividualBundle, individual_kp,
) -> WorldlineSummary:
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")
    if _did_from_kp(individual_kp) != bundle.individual_id:
        raise ValueError("keypair does not match bundle")
    visits: List[WorldVisit] = []
    for rec in bundle.memory:
        if rec.get("type") != "world_entry":
            continue
        visits.append(WorldVisit(
            world_id=rec["world_id"],
            tier=rec["tier"],
            first_memory_index=rec["first_memory_index"],
            entered_at_ts=rec.get("ts", ""),
        ))
    ts = _now()
    body = {
        "kind": "worldline_summary",
        "individual_id": bundle.individual_id,
        "visits": [v.to_dict() for v in visits],
        "ts": ts,
    }
    sig = individual_kp.sign(_canonical(body)).hex()
    return WorldlineSummary(
        individual_id=bundle.individual_id,
        visits=tuple(visits), ts=ts, sig=sig,
    )


def verify_worldline_summary(
    summary: WorldlineSummary,
    expected_individual: Optional[str] = None,
) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if expected_individual is not None \
            and summary.individual_id != expected_individual:
        return (False, "individual_id mismatch")
    try:
        _pubkey_from_did(summary.individual_id).verify(
            bytes.fromhex(summary.sig),
            _canonical(summary.body()))
        return (True, "worldline summary verifies")
    except Exception:
        return (False, "signature invalid")


@dataclass(frozen=True)
class AnnotatedWorldline:
    individual_id: str
    map_id: str
    annotated_visits: Tuple[Dict, ...]
    original_summary: Dict  # full WorldlineSummary.to_dict()
    ts: str
    sig: str  # map's signature

    def body(self) -> Dict:
        return {
            "kind": "annotated_worldline",
            "individual_id": self.individual_id,
            "map_id": self.map_id,
            "annotated_visits": [dict(v)
                                  for v in self.annotated_visits],
            "original_summary": dict(self.original_summary),
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}


def annotate_worldline(
    map_world, summary: WorldlineSummary,
    fetch_live: bool = True,
) -> AnnotatedWorldline:
    """Map annotates the individual's signed summary. Returns a
    map-signed AnnotatedWorldline."""
    from map_world import _fetch_lobby
    from lobby import verify_lobby

    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")

    annotated: List[Dict] = []
    for v in summary.visits:
        entry: Dict = v.to_dict()
        entry["in_this_map"] = False
        entry["cluster"] = None
        entry["resolved_via"] = None
        entry["current_status"] = "not_registered"

        pin = map_world._registry.get_pin(v.world_id)
        if pin is not None:
            entry["in_this_map"] = True
            entry["cluster"] = pin.cluster
            entry["description"] = pin.description
            if fetch_live:
                lobby = _fetch_lobby(pin.url)
                if lobby is None:
                    entry["current_status"] = "unavailable"
                else:
                    ok, _ = verify_lobby(lobby, pin.world_signer)
                    entry["current_status"] = (
                        "live" if ok else "signature_invalid")
                    if ok:
                        entry["current_lobby_hash"] = \
                            lobby.record_hash()
                        entry["current_lobby_ts"] = lobby.ts
            else:
                entry["current_status"] = "not_fetched"
        else:
            # Try sub-maps
            sub_data, via_map = map_world._find_in_submaps(
                v.world_id)
            if sub_data is not None:
                entry["resolved_via"] = via_map
                entry["cluster"] = sub_data.get("cluster")
                entry["description"] = sub_data.get("description", "")
                if fetch_live:
                    url = sub_data.get("url")
                    signer = sub_data.get("world_signer")
                    if url and signer:
                        lobby = _fetch_lobby(url)
                        if lobby is None:
                            entry["current_status"] = "unavailable"
                        else:
                            ok, _ = verify_lobby(lobby, signer)
                            entry["current_status"] = (
                                "live" if ok
                                else "signature_invalid")
                            if ok:
                                entry["current_lobby_hash"] = \
                                    lobby.record_hash()
                else:
                    entry["current_status"] = "not_fetched"

        annotated.append(entry)

    ts = _now()
    body = {
        "kind": "annotated_worldline",
        "individual_id": summary.individual_id,
        "map_id": map_world._manifest.entity_id,
        "annotated_visits": annotated,
        "original_summary": summary.to_dict(),
        "ts": ts,
    }
    sig = map_world.world_kp().sign(_canonical(body)).hex()
    return AnnotatedWorldline(
        individual_id=summary.individual_id,
        map_id=map_world._manifest.entity_id,
        annotated_visits=tuple(annotated),
        original_summary=summary.to_dict(),
        ts=ts, sig=sig,
    )


def verify_annotated_worldline(
    aw: AnnotatedWorldline,
    expected_map: Optional[str] = None,
    expected_individual: Optional[str] = None,
) -> Tuple[bool, str]:
    """Two signatures. Never raises."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(aw, AnnotatedWorldline):
        return (False, "not an AnnotatedWorldline")
    if expected_map and aw.map_id != expected_map:
        return (False, "map_id mismatch")
    if expected_individual and aw.individual_id != expected_individual:
        return (False, "individual_id mismatch")
    # 1. Map's signature over the annotated body
    try:
        _pubkey_from_did(aw.map_id).verify(
            bytes.fromhex(aw.sig),
            _canonical(aw.body()))
    except Exception:
        return (False, "map signature invalid")
    # 2. Individual's signature over the original summary
    try:
        original = WorldlineSummary.from_dict(
            aw.original_summary)
    except (KeyError, ValueError, TypeError):
        return (False, "original summary malformed")
    if original.individual_id != aw.individual_id:
        return (False, "individual mismatch in summary")
    ok, reason = verify_worldline_summary(original)
    if not ok:
        return (False, f"individual signature: {reason}")
    # 3. Annotated visits must correspond to the original visits
    if len(aw.annotated_visits) != len(original.visits):
        return (False,
                 f"annotated visit count "
                 f"{len(aw.annotated_visits)} != "
                 f"original {len(original.visits)}")
    for i, (av, ov) in enumerate(
            zip(aw.annotated_visits, original.visits)):
        for f in ("world_id", "tier", "first_memory_index",
                   "entered_at_ts"):
            if av.get(f) != getattr(ov, f):
                return (False,
                         f"visit {i}: {f} mismatch")
    return (True,
             f"annotated worldline verifies "
             f"({len(aw.annotated_visits)} visits, "
             f"map + individual signed)")
