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


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Build a C48 federation, save it, verify a subprocess can
    load and verify it against caller-supplied trust anchors.

    Bundle contents:
      - A C44 council decision (direct)
      - A C43 swarm log (witnessed)
      - A C48 meta-decision referencing both

    Subprocess:
      - Loads bundle and context from disk
      - Verifies via verify_bundle
      - Prints BUNDLE-VERIFIED on success, exits non-zero on
        any failure

    Then a second subprocess verifies a tampered copy and
    EXPECTS failure.

    Anchor: Dickinson, 'The Brain – is wider than the Sky –'
    (same line; the point is now that the record survives the
    process that made it).
    """
    import json
    import subprocess
    import sys
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c13 import KeyPair
    from multiverse_c43 import SwarmUnit, SwarmNetwork
    from multiverse_c44 import (
        Proposal as P44, QuorumRule,
    )
    from multiverse_c45 import (
        DeliberativeCouncil, DeliberativeMember,
    )
    from multiverse_c48 import (
        attest_decision, witness_artifact,
        CrossKindReference, CrossKindDeliberativeMember,
        CrossKindCouncil,
    )

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # -------------------------------------------------------------
    # Build the source artifacts
    # -------------------------------------------------------------
    # C44 council decision
    alpha_kps = [KeyPair.generate() for _ in range(3)]
    alpha = DeliberativeCouncil(
        "alpha", QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(alpha_kps):
        alpha.add_member(DeliberativeMember(
            entity_id=f"alpha:m{i}", name=f"Alpha-{i}",
            member_kp=kp,
            decision_rule=lambda p, c: ("yea", "approve")))
    alpha_keys = {
        f"alpha:m{i}": kp.public_key_hex()
        for i, kp in enumerate(alpha_kps)
    }
    alpha_dec = alpha.deliberate_and_resolve(
        P44(content={"action": "adopt-relay"}))
    a_att = attest_decision(
        "council-alpha", alpha_dec.final_decision)

    # C43 swarm log (witnessed)
    swarm_net = SwarmNetwork(food_target=(3, 3), max_epochs=15)
    for i in range(3):
        swarm_net.add_unit(f"ant-{i}", SwarmUnit(
            entity_id=f"world:ant-{i}", name=f"ant-{i}",
            env_stream=swarm_net.stream,
            initial_position=(i, i),
            seed=42 + i, sample_probability=1.0))
    # Trigger food discovery
    from multiverse_c3 import Act
    swarm_net.unit_by_name("ant-0").act(Act(
        actor_token="ext", type="find_food",
        payload={"location": [3, 3]}))
    swarm_epochs = []
    for _ in range(15):
        r = swarm_net.run_epoch()
        swarm_epochs.append({
            "epoch": r.epoch,
            "units_at_food": r.statistics["units_at_food"],
            "converged": r.statistics["converged"],
        })
        if r.statistics["converged"]:
            break
    swarm_content = {
        "epochs": swarm_epochs,
        "final_converged": swarm_net.converged(),
    }
    witness_kp = KeyPair.generate()
    witness_id = create_identity("swarm-recorder")
    c_att = witness_artifact(
        "swarm-1", "swarm_log", swarm_content,
        witness_kp, witness_id)
    witness_keys = {witness_id.token: witness_kp.public_key_hex()}

    # C48 meta-decision
    meta_kps = [KeyPair.generate() for _ in range(3)]
    def meta_rule(p, ctx):
        atts = ctx.get("cross_kind_attestations", {})
        refs = [
            CrossKindReference(
                source_id=sid,
                source_kind=s["source_kind"],
                artifact_hash=s["content_hash"])
            for sid, s in atts.items()
        ]
        return ("yea", f"saw {len(refs)}", refs)
    meta = CrossKindCouncil(
        "meta", QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(meta_kps):
        meta.add_member(CrossKindDeliberativeMember(
            entity_id=f"meta:m{i}", name=f"Meta-{i}",
            member_kp=kp, decision_rule=meta_rule))
    meta_keys = {
        f"meta:m{i}": kp.public_key_hex()
        for i, kp in enumerate(meta_kps)
    }
    meta_proposal = P44(content={
        "action": "federate",
        "note": "council + swarm",
    })
    meta_decision = meta.deliberate_and_resolve_cross_kind(
        meta_proposal, attestations=[a_att, c_att])

    # -------------------------------------------------------------
    # Bundle it up
    # -------------------------------------------------------------
    bundle = ArchitectureFederationBundle(
        name="demo-federation",
        attestations=(a_att, c_att),
        meta_decision=meta_decision,
        created_at=_now(),
    )

    # Context: the caller's trust anchors
    context = {
        "member_keys": {
            "council-alpha": alpha_keys,
            "meta": meta_keys,
        },
        "witness_public_keys": witness_keys,
        "meta_member_keys": meta_keys,
    }

    # In-process verification (sanity)
    in_proc_verdict = verify_bundle(bundle, context)

    # -------------------------------------------------------------
    # Write artifacts
    # -------------------------------------------------------------
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)
    bundle_path = path / "architecture_federation_bundle.json"
    context_path = path / "federation_verification_context.json"
    save_bundle(bundle, str(bundle_path))
    save_verification_context(context, str(context_path))

    # -------------------------------------------------------------
    # Subprocess verification of the honest bundle
    # -------------------------------------------------------------
    honest_script = f"""
import json
import sys
sys.path.insert(0, {str(Path(__file__).parent.resolve())!r})
from multiverse_c49 import (
    load_bundle, load_verification_context, verify_bundle,
)
b = load_bundle({str(bundle_path)!r})
if not b.valid:
    print("LOAD FAILED:", b.reason)
    sys.exit(1)
ctx = load_verification_context({str(context_path)!r})
v = verify_bundle(b.bundle, ctx)
print(v.format())
if not v.valid:
    sys.exit(1)
print("BUNDLE-VERIFIED")
"""
    honest_proc = subprocess.run(
        [sys.executable, "-c", honest_script],
        capture_output=True, text=True, timeout=60)
    honest_ok = (honest_proc.returncode == 0
                 and "BUNDLE-VERIFIED" in honest_proc.stdout)

    # -------------------------------------------------------------
    # Tampered bundle: flip a byte in the meta decision's proposal
    # -------------------------------------------------------------
    tampered_bundle_path = path / "tampered_federation_bundle.json"
    bundle_data = bundle.to_dict()
    # Tamper: change the swarm log's final_converged flag without
    # changing the content_hash (so the hash check catches it)
    for att in bundle_data["attestations"]:
        if att["source_kind"] == "swarm_log":
            att["content"]["final_converged"] = (
                not att["content"]["final_converged"])
            break
    tampered_bundle_path.write_text(
        json.dumps(bundle_data, indent=2))

    tampered_script = f"""
import sys
sys.path.insert(0, {str(Path(__file__).parent.resolve())!r})
from multiverse_c49 import (
    load_bundle, load_verification_context, verify_bundle,
)
b = load_bundle({str(tampered_bundle_path)!r})
if not b.valid:
    print("LOAD FAILED:", b.reason)
    sys.exit(1)
ctx = load_verification_context({str(context_path)!r})
v = verify_bundle(b.bundle, ctx)
if v.valid:
    print("ERROR: tampered bundle verified")
    sys.exit(1)
print("TAMPER-DETECTED")
"""
    tampered_proc = subprocess.run(
        [sys.executable, "-c", tampered_script],
        capture_output=True, text=True, timeout=60)
    tamper_detected = (
        tampered_proc.returncode == 0
        and "TAMPER-DETECTED" in tampered_proc.stdout)

    # -------------------------------------------------------------
    # Missing-context: verify with empty context
    # -------------------------------------------------------------
    empty_ctx_verdict = verify_bundle(bundle, {})

    # -------------------------------------------------------------
    # Print
    # -------------------------------------------------------------
    print("=" * 70)
    print("Persistence of Federation — demo")
    print("=" * 70)
    print()
    print("  Bundle:")
    for line in bundle.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Saved to:")
    print(f"    {bundle_path}")
    print(f"    {context_path}")
    print()
    print("  In-process verification (same session):")
    print(f"    valid: {in_proc_verdict.valid}")
    print()
    print("  Subprocess verification (fresh process, "
          "loaded from disk):")
    print(f"    returncode: {honest_proc.returncode}")
    print(f"    BUNDLE-VERIFIED in output: "
          f"{'BUNDLE-VERIFIED' in honest_proc.stdout}")
    if honest_proc.stdout.strip():
        for line in honest_proc.stdout.strip().split("\n")[-6:]:
            print(f"      {line}")
    print()
    print("  Tampered bundle (byte flipped in swarm log):")
    print(f"    returncode: {tampered_proc.returncode}")
    print(f"    TAMPER-DETECTED in output: "
          f"{'TAMPER-DETECTED' in tampered_proc.stdout}")
    print()
    print("  Empty-context verification (no trust anchors):")
    print(f"    valid: {empty_ctx_verdict.valid}")
    print(f"    reason: {empty_ctx_verdict.reason}")
    print()
    print("  What this demonstrates:")
    print("    - The bundle is a file. A fresh process can load it.")
    print("    - Trust anchors are the caller's policy, not the")
    print("      bundle's claim. Empty context fails; correct")
    print("      context verifies.")
    print("    - Tampering with any attestation is caught by that")
    print("      attestation's own verifier, not by the bundle")
    print("      format.")
    print("    - The verifier registry is code, not data. The")
    print("      loading process re-imports it; a custom verifier")
    print("      would need to be re-registered by the caller.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    (the record survives the process that made it)")

    audit = {
        "bundle_path": str(bundle_path),
        "context_path": str(context_path),
        "tampered_path": str(tampered_bundle_path),
        "in_process_valid": in_proc_verdict.valid,
        "subprocess_verified": honest_ok,
        "tamper_detected": tamper_detected,
        "empty_context_valid": empty_ctx_verdict.valid,
        "empty_context_reason": empty_ctx_verdict.reason,
    }
    (path / "persistence_demo.json").write_text(
        json.dumps(audit, indent=2))
    print(f"\n  → {path}/persistence_demo.json")
    return audit
