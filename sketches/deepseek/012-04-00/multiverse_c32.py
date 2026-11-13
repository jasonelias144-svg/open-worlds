"""
multiverse_c32.py — Component 32: Persistence.

C30 and C31 produce artifacts. C32 makes the artifact directory a
*self-verifying bundle*: save everything needed to re-derive the
federation state, load it back in a fresh process, re-verify every
signature.

What a bundle contains:
  - World's signed manifest (self-signed by the world's key)
  - World's log (append-only: admissions, acks, leaves, ...)
  - Registry's signed manifest (self-signed by the registry's key)
  - Registry's log (including signed_listing entries)
  - Passports (identity + entries with signatures)
  - Signed federation verdict (C31)
  - Verifier's public key (for the signed verdict)

What verification proves:
  - Each signed manifest self-verifies
  - Each signed_listing verifies against the registry's key
  - Each listing's embedded world manifest matches the world's own
    (same entity_id, same public_key)
  - Each passport entry verifies against the world's key from the
    listing (no world fetch)
  - The signed verdict verifies against the verifier's key

What it does NOT prove:
  - That the world, registry, or verifier are trustworthy (external)
  - That the bundle hasn't been tampered with (that's what the
    signatures are for — they're checked here)
  - That the bundle represents "current" state (snapshot at bundle time)

House rules honored:
  - "Nothing is described as run unless it was run" — the demo
    bundle is constructed from a real live federation.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per failure: malformed JSON, missing
    field, tampered manifest, tampered listing, tampered
    passport, tampered verdict.
  - "A world never raises on what a visitor sends" — analog:
    load_bundle and verify_loaded_bundle return results, never
    raise. Tested.
  - "History, not rank" — the bundle is a record, not a score.

Honest limits (documented, tested):
  - Snapshot, not continuous. The bundle describes ONE run at
    ONE moment. Later runs produce different bundles.
  - Trust anchor external. Verifying the bundle's claims does
    not tell you whether the verifier's key, the registry's
    key, or the world's key is genuinely held by the named
    entity. That decision is external — same as C13/C24/C29.
  - Log entries are not individually signed. The chain of
    trust flows from the signed manifest → the registry's
    listing → the passport. The log is a supporting record
    (useful for reconstruction), not a signed artifact.
  - No cross-bundle references. A bundle cannot point to
    another bundle (e.g., two worlds in one bundle). One world
    per bundle in this prototype.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from multiverse_c13 import (
    HAS_CRYPTO, canonical_bytes, verify_signature,
)
from multiverse_c15 import PassportEntry, PassportV2
from multiverse_c28 import (
    SignedManifest, verify_manifest_signature,
)
from multiverse_c29 import (
    SignedListing, verify_signed_listing,
    verify_listing_world_manifest,
)
from multiverse_c31 import (
    SignedFederationVerdict, verify_signed_federation_verdict,
)


# =====================================================================
# LogEntryRecord — a serializable log entry
# =====================================================================

@dataclass(frozen=True)
class LogEntryRecord:
    timestamp: str
    kind: str
    actor_token: Optional[str]
    data: Dict

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "kind": self.kind,
            "actor_token": self.actor_token,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "LogEntryRecord":
        return cls(
            timestamp=d["timestamp"],
            kind=d["kind"],
            actor_token=d.get("actor_token"),
            data=d.get("data", {}),
        )


# =====================================================================
# WorldState, RegistryState, PassportState
# =====================================================================

@dataclass(frozen=True)
class WorldState:
    entity_id: str
    signed_manifest: Dict
    log: List[LogEntryRecord]

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "signed_manifest": self.signed_manifest,
            "log": [e.to_dict() for e in self.log],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "WorldState":
        return cls(
            entity_id=d["entity_id"],
            signed_manifest=d["signed_manifest"],
            log=[LogEntryRecord.from_dict(e) for e in d["log"]],
        )


@dataclass(frozen=True)
class RegistryState:
    entity_id: str
    signed_manifest: Dict
    log: List[LogEntryRecord]

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "signed_manifest": self.signed_manifest,
            "log": [e.to_dict() for e in self.log],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RegistryState":
        return cls(
            entity_id=d["entity_id"],
            signed_manifest=d["signed_manifest"],
            log=[LogEntryRecord.from_dict(e) for e in d["log"]],
        )


@dataclass(frozen=True)
class PassportState:
    identity_token: str
    identity_name: str
    entries: List[Dict]

    def to_dict(self) -> Dict:
        return {
            "identity_token": self.identity_token,
            "identity_name": self.identity_name,
            "entries": list(self.entries),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "PassportState":
        return cls(
            identity_token=d["identity_token"],
            identity_name=d["identity_name"],
            entries=list(d["entries"]),
        )


# =====================================================================
# FederationBundle
# =====================================================================

@dataclass(frozen=True)
class FederationBundle:
    world: WorldState
    registry: RegistryState
    passports: List[PassportState]
    signed_verdict: Dict
    verifier_public_key: str
    created_at: str

    def __post_init__(self):
        if not isinstance(self.world, WorldState):
            raise ValueError("world must be a WorldState")
        if not isinstance(self.registry, RegistryState):
            raise ValueError("registry must be a RegistryState")
        if not isinstance(self.signed_verdict, dict):
            raise ValueError("signed_verdict must be a dict")
        if not isinstance(self.verifier_public_key, str) \
                or len(self.verifier_public_key) != 64:
            raise ValueError("verifier_public_key must be 64 hex chars")
        if not self.created_at:
            raise ValueError("created_at required")

    def to_dict(self) -> Dict:
        return {
            "kind": "federation_bundle",
            "created_at": self.created_at,
            "world": self.world.to_dict(),
            "registry": self.registry.to_dict(),
            "passports": [p.to_dict() for p in self.passports],
            "signed_verdict": self.signed_verdict,
            "verifier_public_key": self.verifier_public_key,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "FederationBundle":
        if d.get("kind") != "federation_bundle":
            raise ValueError(
                f"kind must be 'federation_bundle', "
                f"got {d.get('kind')!r}")
        return cls(
            world=WorldState.from_dict(d["world"]),
            registry=RegistryState.from_dict(d["registry"]),
            passports=[PassportState.from_dict(p)
                       for p in d.get("passports", [])],
            signed_verdict=d["signed_verdict"],
            verifier_public_key=d["verifier_public_key"],
            created_at=d["created_at"],
        )


# =====================================================================
# Bundle construction from live components
# =====================================================================

def bundle_from_live(
    world,
    registry,
    world_log,
    registry_log,
    passports: List[PassportV2],
    signed_verdict: SignedFederationVerdict,
    verifier_public_key: str,
    created_at: Optional[str] = None,
) -> FederationBundle:
    """Construct a bundle from live components.

    `world` and `registry` are the live signed entities (with
    .manifest_dict()). `world_log` and `registry_log` are their
    log_since(None) output. `passports` are PassportV2 instances.
    `signed_verdict` is C31's output. `verifier_public_key` is the
    key that signed the verdict.
    """
    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()

    world_state = WorldState(
        entity_id=world.manifest_dict()["entity_id"],
        signed_manifest=dict(world.manifest_dict()),
        log=[LogEntryRecord(
            timestamp=e.timestamp, kind=e.kind,
            actor_token=e.actor_token, data=dict(e.data))
             for e in world_log],
    )
    registry_state = RegistryState(
        entity_id=registry.manifest_dict()["entity_id"],
        signed_manifest=dict(registry.manifest_dict()),
        log=[LogEntryRecord(
            timestamp=e.timestamp, kind=e.kind,
            actor_token=e.actor_token, data=dict(e.data))
             for e in registry_log],
    )
    passport_states = [
        PassportState(
            identity_token=p.identity.token,
            identity_name=p.identity.name,
            entries=[
                {"entity_id": entry.entity_id,
                 "timestamp": entry.timestamp,
                 "subject_token": entry.subject_token,
                 "signature": entry.signature}
                for entry in p.entries
            ],
        )
        for p in passports
    ]
    return FederationBundle(
        world=world_state,
        registry=registry_state,
        passports=passport_states,
        signed_verdict=signed_verdict.to_dict(),
        verifier_public_key=verifier_public_key,
        created_at=created_at,
    )


# =====================================================================
# Save / load
# =====================================================================

def save_bundle(bundle: FederationBundle, path: str) -> None:
    """Write the bundle as JSON to path."""
    Path(path).write_text(json.dumps(bundle.to_dict(), indent=2))


def save_bundle_to_dir(bundle: FederationBundle, dir: str) -> Path:
    """Write to <dir>/federation_bundle.json. Returns the path."""
    path = Path(dir) / "federation_bundle.json"
    save_bundle(bundle, str(path))
    return path


@dataclass(frozen=True)
class LoadResult:
    valid: bool
    bundle: Optional[FederationBundle]
    reason: str


def load_bundle(path: str) -> LoadResult:
    """Load a bundle from path. Never raises.

    Returns LoadResult(valid=True, bundle=..., reason="loaded") on
    success; LoadResult(valid=False, bundle=None, reason="...") on
    any failure (missing file, malformed JSON, missing field, wrong
    type).
    """
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        return LoadResult(False, None, f"file not found: {path}")
    except OSError as e:
        return LoadResult(False, None, f"could not read file: {e}")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return LoadResult(False, None, f"invalid JSON: {e}")

    try:
        bundle = FederationBundle.from_dict(data)
    except (KeyError, ValueError, TypeError) as e:
        return LoadResult(False, None, f"invalid bundle shape: {e}")

    return LoadResult(True, bundle, "loaded")


# =====================================================================
# Verification of loaded bundle
# =====================================================================

@dataclass
class BundleVerification:
    valid: bool
    reason: str
    checks: Dict[str, bool] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    world_public_key: Optional[str] = None
    registry_public_key: Optional[str] = None

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Bundle Verification",
            "=" * 70,
        ]
        for name, ok in self.checks.items():
            marker = "✓" if ok else "✗"
            lines.append(f"  {marker} {name}")
        lines.append("")
        if self.world_public_key:
            lines.append(f"  world key:    "
                          f"{self.world_public_key[:16]}...")
        if self.registry_public_key:
            lines.append(f"  registry key: "
                          f"{self.registry_public_key[:16]}...")
        lines.append("")
        if self.valid:
            lines.append("  Result: ✓ VALID")
        else:
            lines.append("  Result: ✗ INVALID")
            lines.append(f"  Reason: {self.reason}")
            for f in self.failures:
                lines.append(f"    - {f}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "checks": dict(self.checks),
            "failures": list(self.failures),
            "world_public_key": self.world_public_key,
            "registry_public_key": self.registry_public_key,
        }


def verify_loaded_bundle(
    bundle: FederationBundle,
    expected_verifier_key: Optional[str] = None,
) -> BundleVerification:
    """Verify a loaded bundle without contacting any URL.

    If `expected_verifier_key` is provided, the bundle's
    verifier_public_key must match it AND the signed verdict must
    verify against it. If None, the signed verdict verifies against
    the bundle's own verifier_public_key (internal consistency only).

    Never raises. Every check failure is recorded in the result.
    """
    result = BundleVerification(valid=True, reason="all checks passed")

    def fail(name: str, reason: str) -> None:
        result.valid = False
        result.checks[name] = False
        result.failures.append(f"{name}: {reason}")

    if not HAS_CRYPTO:
        return BundleVerification(
            valid=False,
            reason="cryptography not installed",
            checks={"cryptography_available": False},
        )

    # -- Check 1: world's signed manifest self-verifies --
    try:
        sm = SignedManifest.from_dict(bundle.world.signed_manifest)
    except (KeyError, ValueError, TypeError) as e:
        fail("world_manifest_self_verified",
             f"could not parse: {e}")
        result.reason = "world manifest parse failed"
        return result
    if not verify_manifest_signature(sm, sm.public_key):
        fail("world_manifest_self_verified",
             "signature INVALID")
    else:
        result.checks["world_manifest_self_verified"] = True
        result.world_public_key = sm.public_key
    if sm.entity_id != bundle.world.entity_id:
        fail("world_manifest_entity_id_matches",
             f"{sm.entity_id!r} != {bundle.world.entity_id!r}")
    else:
        result.checks["world_manifest_entity_id_matches"] = True

    # -- Check 2: registry's signed manifest self-verifies --
    try:
        rsm = SignedManifest.from_dict(
            bundle.registry.signed_manifest)
    except (KeyError, ValueError, TypeError) as e:
        fail("registry_manifest_self_verified",
             f"could not parse: {e}")
        result.reason = "registry manifest parse failed"
        return result
    if not verify_manifest_signature(rsm, rsm.public_key):
        fail("registry_manifest_self_verified",
             "signature INVALID")
    else:
        result.checks["registry_manifest_self_verified"] = True
        result.registry_public_key = rsm.public_key

    # -- Check 3: at least one signed_listing in the registry log --
    signed_listings = [
        e for e in bundle.registry.log if e.kind == "signed_listing"
    ]
    if not signed_listings:
        fail("registry_has_signed_listing",
             "no signed_listing entries in registry log")
        result.reason = "no listings"
        return result
    result.checks["registry_has_signed_listing"] = True

    # -- Check 4: each signed_listing verifies against the registry key --
    listing_world_keys: Dict[str, str] = {}
    all_listings_ok = True
    for i, entry in enumerate(signed_listings):
        try:
            listing = SignedListing.from_log_dict({
                "timestamp": entry.timestamp,
                "kind": entry.kind,
                "data": entry.data,
            })
        except (KeyError, TypeError) as e:
            fail(f"listing_{i}_verified", f"parse failed: {e}")
            all_listings_ok = False
            continue
        if not verify_signed_listing(
                result.registry_public_key or "", listing):
            fail(f"listing_{i}_verified",
                 "registry signature INVALID")
            all_listings_ok = False
            continue
        if not verify_listing_world_manifest(listing):
            fail(f"listing_{i}_verified",
                 "world manifest signature INVALID")
            all_listings_ok = False
            continue
        result.checks[f"listing_{i}_verified"] = True
        if listing.signed_manifest is not None:
            try:
                wsm = SignedManifest.from_dict(
                    listing.signed_manifest)
                listing_world_keys[listing.entity_id] = wsm.public_key
            except (KeyError, ValueError, TypeError):
                pass
    if all_listings_ok:
        result.checks["all_listings_verified"] = True

    # -- Check 5: listing's world key matches world's own manifest --
    world_key_from_listing = listing_world_keys.get(
        bundle.world.entity_id)
    if world_key_from_listing is None:
        fail("listing_world_key_present",
             f"no listing for world {bundle.world.entity_id!r}")
    elif world_key_from_listing != result.world_public_key:
        fail("listing_world_key_matches",
             f"{world_key_from_listing[:16]}... != "
             f"{(result.world_public_key or '')[:16]}...")
    else:
        result.checks["listing_world_key_matches"] = True

    # -- Check 6: each passport verifies against the loaded listing key --
    if result.world_public_key is None:
        result.reason = "no world key"
        return result

    for i, p_state in enumerate(bundle.passports):
        check_name = f"passport_{i}_verified"
        passport = PassportV2(
            identity=_identity(p_state.identity_token,
                                p_state.identity_name),
            entries=tuple(
                PassportEntry(
                    entity_id=e["entity_id"],
                    timestamp=e["timestamp"],
                    subject_token=e.get("subject_token"),
                    signature=e.get("signature"),
                )
                for e in p_state.entries
            ),
        )
        report = passport.verify(
            lambda eid, _pk=result.world_public_key:
                _pk if eid == bundle.world.entity_id else None)
        if report.all_verified():
            result.checks[check_name] = True
        else:
            fail(check_name,
                 f"passport not fully verified: "
                 f"{[(v.entry.entity_id, v.status) for v in report.verdicts]}")

    # -- Check 7: signed verdict verifies --
    try:
        signed = SignedFederationVerdict.from_dict(
            bundle.signed_verdict)
    except (KeyError, ValueError, TypeError) as e:
        fail("verdict_verified", f"parse failed: {e}")
        result.reason = "verdict parse failed"
        return result

    if expected_verifier_key is not None:
        if bundle.verifier_public_key != expected_verifier_key:
            fail("verifier_key_matches",
                 f"bundle claims "
                 f"{bundle.verifier_public_key[:16]}..., "
                 f"caller expects "
                 f"{expected_verifier_key[:16]}...")
        else:
            result.checks["verifier_key_matches"] = True
        verify_against = expected_verifier_key
    else:
        verify_against = bundle.verifier_public_key

    if verify_signed_federation_verdict(signed, verify_against):
        result.checks["verdict_verified"] = True
    else:
        fail("verdict_verified",
             "signature does not verify against "
             + ("caller-provided key"
                if expected_verifier_key is not None
                else "bundle's verifier_public_key"))

    if not result.valid:
        result.reason = "; ".join(result.failures) \
            if result.failures else "unspecified"
    return result


def _identity(token: str, name: str):
    from multiverse_c1 import Identity
    return Identity(token=token, name=name)
