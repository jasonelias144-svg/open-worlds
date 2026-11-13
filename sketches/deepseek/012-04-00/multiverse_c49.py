"""
multiverse_c49.py — Component 49: Persistence of Federation.

C48 produced CrossKindFederatedDecisions in-process. C49 makes
them portable: save to disk, load in a fresh process, re-verify
with caller-supplied trust anchors.

Design:
  - ArchitectureFederationBundle: a versioned JSON artifact
    carrying attestations and (optionally) a meta-decision.
  - save_bundle / load_bundle: round-trip via JSON.
    load_bundle returns LoadResult and never raises.
  - verify_bundle: verifies every attestation and the meta
    decision (if present). Never raises.
  - _verify_witnessed_trusted: a strict witnessed verifier that
    requires the caller to supply witness_public_keys. This is
    the C49 addition over C48's more trusting default.

What travels in the bundle:
  - Attestations (direct and witnessed).
  - The meta-decision (with its embedded attestations).
  - Metadata (name, created_at).

What does NOT travel in the bundle:
  - Verifier registry (it's code, not data).
  - Trust anchors (member keys, witness keys). These are the
    CALLER's policy. A bundle verified against attacker-chosen
    keys verifies against attacker-chosen keys.
  - Resolvers for cross_world_attestations (they're functions;
    cross-world persistence requires the caller to reconstruct
    them).

This separation is the design commitment, not a limitation.
A bundle is a set of claims; a verifier is a policy for
checking claims. Keeping them separate is what makes the
artifact portable and the verification honest.

House rules honored:
  - "A world never raises on what a visitor sends" — load_bundle
    and verify_bundle never raise; all failures are LoadResult
    or BundleVerdict.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: load roundtrip, JSON malformed, wrong
    kind, missing field, verified happy, missing witness key,
    missing member key, tampered content, wrong witness key,
    subprocess verification, subprocess tamper detection.
  - "History, not rank" — the bundle is a record.

Honest limits (documented, tested):
  - Context is not in the bundle. Serializing it is the caller's
    job (see save_verification_context / load_verification_context
    for the caller-serializable subset).
  - Resolvers cannot be serialized. Bundles with
    cross_world_attestations require the loading process to
    reconstruct resolvers. Demo uses only direct decisions and
    witnessed attestations to avoid this.
  - No signature over the bundle as a whole. Tampering with
    metadata (bundle.name, created_at) is not detected; tampering
    with attestations IS detected (each attestation's own
    verifier).
  - No key rotation. Trust anchors are static at load time.
  - No revocation of bundles. A bundle is a historical artifact;
    the caller decides what to trust.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, canonical_bytes, verify_signature,
)
from multiverse_c44 import Proposal, Decision
from multiverse_c45 import DeliberativeDecision
from multiverse_c46 import FederatedDeliberativeDecision
from multiverse_c48 import (
    DIRECT_KINDS, WITNESSED_KINDS, ALL_KINDS,
    FederationAttestation,
    AttestationVerdict,
    DEFAULT_VERIFIER_REGISTRY,
    verify_federation_attestation,
    CrossKindFederatedDecision,
    CrossKindFederatedVerdict,
    verify_cross_kind_federation,
    _verify_witnessed,
    _hash_payload,
)


BUNDLE_KIND = "architecture_federation_bundle"
BUNDLE_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# ArchitectureFederationBundle
# =====================================================================

@dataclass(frozen=True)
class ArchitectureFederationBundle:
    """A portable federation artifact.

    Versioned. Version 1 carries:
      - name: str
      - attestations: tuple of FederationAttestation
      - meta_decision: optional CrossKindFederatedDecision
      - created_at: str
      - bundle_version: int
    """
    name: str
    attestations: Tuple[FederationAttestation, ...] = ()
    meta_decision: Optional[CrossKindFederatedDecision] = None
    created_at: str = ""
    bundle_version: int = BUNDLE_VERSION

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("name required")
        if self.bundle_version < 1:
            raise ValueError(
                "bundle_version must be >= 1")
        for a in self.attestations:
            if not isinstance(a, FederationAttestation):
                raise ValueError(
                    "attestations must be FederationAttestation")
        if self.meta_decision is not None and not isinstance(
                self.meta_decision, CrossKindFederatedDecision):
            raise ValueError(
                "meta_decision must be CrossKindFederatedDecision "
                "or None")

    def to_dict(self) -> Dict:
        d = {
            "kind": BUNDLE_KIND,
            "bundle_version": self.bundle_version,
            "name": self.name,
            "created_at": self.created_at,
            "attestations": [
                a.to_dict() for a in self.attestations],
        }
        if self.meta_decision is not None:
            d["meta_decision"] = self.meta_decision.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "ArchitectureFederationBundle":
        if d.get("kind") != BUNDLE_KIND:
            raise ValueError(
                f"kind must be {BUNDLE_KIND!r}, "
                f"got {d.get('kind')!r}")
        version = d.get("bundle_version", BUNDLE_VERSION)
        if version != BUNDLE_VERSION:
            raise ValueError(
                f"unsupported bundle_version {version}; "
                f"this loader supports {BUNDLE_VERSION}")
        meta = None
        if "meta_decision" in d:
            meta = CrossKindFederatedDecision.from_dict(
                d["meta_decision"])
        return cls(
            name=d["name"],
            attestations=tuple(
                FederationAttestation.from_dict(a)
                for a in d.get("attestations", [])),
            meta_decision=meta,
            created_at=d.get("created_at", ""),
            bundle_version=version,
        )

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Architecture Federation Bundle",
            "=" * 70,
            f"  name:        {self.name}",
            f"  version:     {self.bundle_version}",
            f"  created_at:  {self.created_at}",
            f"  attestations: {len(self.attestations)}",
            f"  meta:        "
            f"{'present' if self.meta_decision else 'absent'}",
        ]
        if self.attestations:
            lines.append("  Source attestations:")
            for a in self.attestations:
                mode = ("witnessed" if a.is_witnessed
                        else "direct")
                lines.append(
                    f"    · {a.source_id} ({a.source_kind}, {mode})")
        return "\n".join(lines)


# =====================================================================
# Save / load
# =====================================================================

def save_bundle(bundle: ArchitectureFederationBundle,
                 path: str) -> None:
    """Write the bundle as JSON."""
    Path(path).write_text(
        json.dumps(bundle.to_dict(), indent=2))


@dataclass(frozen=True)
class LoadResult:
    valid: bool
    bundle: Optional[ArchitectureFederationBundle]
    reason: str


def load_bundle(path: str) -> LoadResult:
    """Load a bundle from path. Never raises.

    Returns LoadResult(valid=True, bundle=...) on success;
    LoadResult(valid=False, bundle=None, reason=...) on any
    failure (missing file, bad JSON, wrong kind, wrong version,
    missing required field, invalid attestation shape).
    """
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        return LoadResult(False, None, f"file not found: {path}")
    except OSError as e:
        return LoadResult(False, None, f"could not read: {e}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return LoadResult(False, None, f"invalid JSON: {e}")
    try:
        bundle = ArchitectureFederationBundle.from_dict(data)
    except (KeyError, ValueError, TypeError) as e:
        return LoadResult(False, None,
                           f"invalid bundle: {e}")
    return LoadResult(True, bundle, "loaded")


# =====================================================================
# Strict witnessed verifier (C49 addition)
# =====================================================================

def _verify_witnessed_trusted(
    att: FederationAttestation, context: Dict,
) -> Tuple[bool, str]:
    """Stricter than C48's _verify_witnessed: requires the caller
    to supply witness_public_keys, and requires the attestation's
    declared witness token+key to match.

    This is the C49 addition. Without it, a bundle's own claimed
    witness keys would be the trust anchor — which is
    attacker-controlled.
    """
    trusted = context.get("witness_public_keys", {})
    if not isinstance(trusted, dict):
        return (False, "witness_public_keys must be a dict")
    if att.witness_token not in trusted:
        return (False,
                f"witness {att.witness_token!r} not in "
                f"trusted set")
    if trusted[att.witness_token] != att.witness_public_key:
        return (False,
                "declared witness key does not match trusted key")
    # Delegate to C48's verifier for the actual signature check
    return _verify_witnessed(att, context)


def build_trusted_verifier_registry(
    overrides: Optional[Dict[str, Callable]] = None,
) -> Dict[str, Callable]:
    """Build a verifier registry that uses the strict witnessed
    verifier for all witnessed kinds, and C48's defaults for
    direct kinds.

    `overrides` allows a caller to replace any kind's verifier.
    """
    registry: Dict[str, Callable] = dict(DEFAULT_VERIFIER_REGISTRY)
    for kind in WITNESSED_KINDS:
        registry[kind] = _verify_witnessed_trusted
    if overrides:
        registry.update(overrides)
    return registry


DEFAULT_TRUSTED_VERIFIER_REGISTRY = build_trusted_verifier_registry()


# =====================================================================
# Bundle verification
# =====================================================================

@dataclass
class BundleVerdict:
    valid: bool
    reason: str
    attestation_verdicts: List[AttestationVerdict]
    meta_verdict: Optional[CrossKindFederatedVerdict] = None

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Federation Bundle Verification",
            "=" * 70,
            f"  valid:        {self.valid}",
            f"  attestations: {len(self.attestation_verdicts)}",
            f"  meta:         "
            f"{'present' if self.meta_verdict else 'absent'}",
            "",
        ]
        if self.attestation_verdicts:
            lines.append("  Attestation verdicts:")
            for v in self.attestation_verdicts:
                lines.append(v.format())
        if self.meta_verdict is not None:
            lines.append("")
            lines.append("  Meta decision verdict:")
            for line in self.meta_verdict.format().split("\n"):
                lines.append(f"    {line}")
        if not self.valid:
            lines.append("")
            lines.append(f"  Reason: {self.reason}")
        return "\n".join(lines)


def verify_bundle(
    bundle: ArchitectureFederationBundle,
    context: Optional[Dict] = None,
    registry: Optional[Dict[str, Callable]] = None,
) -> BundleVerdict:
    """Verify a loaded bundle. Never raises.

    Verifies:
      1. Every bundle.attestations entry, via dispatch.
      2. If bundle.meta_decision exists, verify it (which
         internally verifies its own embedded attestations).

    The caller must supply `context` with the trust anchors:
      - member_keys: Dict[source_id, Dict[member_token, pk]]
      - witness_public_keys: Dict[witness_token, pk]
      - evidence_member_keys: Dict[source_id,
                                   Dict[source_id,
                                        Dict[member_token, pk]]]
    Missing keys yield per-attestation failures, not exceptions.

    `registry` defaults to DEFAULT_TRUSTED_VERIFIER_REGISTRY
    (strict witnessed verifier + C48's direct verifiers).
    """
    if not isinstance(bundle, ArchitectureFederationBundle):
        return BundleVerdict(
            valid=False, reason="not an ArchitectureFederationBundle",
            attestation_verdicts=[], meta_verdict=None)
    ctx = context or {}
    reg = registry or DEFAULT_TRUSTED_VERIFIER_REGISTRY

    attestation_verdicts: List[AttestationVerdict] = []
    for a in bundle.attestations:
        v = verify_federation_attestation(a, ctx, reg)
        attestation_verdicts.append(v)
    all_attestations_valid = all(
        v.valid for v in attestation_verdicts)

    meta_verdict: Optional[CrossKindFederatedVerdict] = None
    meta_valid = True
    if bundle.meta_decision is not None:
        local_keys = ctx.get("member_keys", {}).get(
            f"__meta__{bundle.name}")
        # Fallback: try by a conventional meta key
        if local_keys is None:
            local_keys = ctx.get("meta_member_keys")
        if local_keys is None:
            # The context may not know the meta council's ID.
            # Fail clearly rather than silently pass.
            meta_verdict = CrossKindFederatedVerdict(
                valid=False,
                reason=("no meta_member_keys in context; "
                        "cannot verify meta decision"),
                local_valid=False,
                attestation_verdicts=[],
                reference_errors=[],
            )
            meta_valid = False
        else:
            meta_verdict = verify_cross_kind_federation(
                bundle.meta_decision,
                local_member_keys=local_keys,
                context=ctx,
                registry=reg,
            )
            meta_valid = meta_verdict.valid

    all_valid = all_attestations_valid and meta_valid
    if all_valid:
        reason = "all attestations valid; meta (if present) valid"
    else:
        parts = []
        failed = [v for v in attestation_verdicts if not v.valid]
        if failed:
            parts.append(f"{len(failed)} attestation(s) failed")
        if not meta_valid:
            parts.append("meta decision invalid")
        reason = "; ".join(parts)
    return BundleVerdict(
        valid=all_valid,
        reason=reason,
        attestation_verdicts=attestation_verdicts,
        meta_verdict=meta_verdict)


# =====================================================================
# Context serialization (caller-serializable subset)
# =====================================================================

CONTEXT_SERIALIZABLE_FIELDS = (
    "member_keys",
    "witness_public_keys",
    "evidence_member_keys",
    "meta_member_keys",
)


def save_verification_context(context: Dict, path: str) -> None:
    """Write the caller-serializable subset of context to disk.

    Resolvers (dag_resolvers, dag_key_resolvers) and QuorumRule
    objects are NOT serializable; they must be reconstructed by
    the loading process. Documented in the module docstring.
    """
    out = {}
    for f in CONTEXT_SERIALIZABLE_FIELDS:
        if f in context:
            out[f] = context[f]
    Path(path).write_text(json.dumps(out, indent=2))


def load_verification_context(path: str) -> Dict:
    """Load the serializable subset of context. Never raises.

    Returns an empty dict on any failure.
    """
    try:
        data = json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data
