import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity, Identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c3 import Act
from multiverse_c43 import SwarmUnit, SwarmNetwork
from multiverse_c44 import (
    Proposal, Decision, QuorumRule,
    verify_decision,
)
from multiverse_c45 import (
    DeliberativeCouncil, DeliberativeMember,
    DeliberativeDecision,
)
from multiverse_c47 import AutonomicUnit, AutonomicNetwork
from multiverse_c48 import (
    DIRECT_KINDS, WITNESSED_KINDS, ALL_KINDS,
    FederationAttestation,
    attest_decision,
    witness_artifact,
    CrossKindReference, CrossKindDeliberativeMember,
    CrossKindCouncil, CrossKindFederatedDecision,
    DEFAULT_VERIFIER_REGISTRY,
)
from multiverse_c49 import (
    BUNDLE_KIND, BUNDLE_VERSION,
    ArchitectureFederationBundle,
    save_bundle, load_bundle, LoadResult,
    _verify_witnessed_trusted,
    build_trusted_verifier_registry,
    DEFAULT_TRUSTED_VERIFIER_REGISTRY,
    BundleVerdict, verify_bundle,
    save_verification_context, load_verification_context,
    CONTEXT_SERIALIZABLE_FIELDS,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _council_decision(council_id="alpha"):
    kps = [KeyPair.generate() for _ in range(3)]
    council = DeliberativeCouncil(
        council_id, QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(kps):
        council.add_member(DeliberativeMember(
            entity_id=f"{council_id}:m{i}",
            name=f"{council_id}-{i}", member_kp=kp,
            decision_rule=lambda p, c: ("yea", "ok")))
    keys = {f"{council_id}:m{i}": kp.public_key_hex()
            for i, kp in enumerate(kps)}
    dec = council.deliberate_and_resolve(
        Proposal(content={"action": "test"}))
    return dec, keys


def _witnessed_att(kind="swarm_log", content=None):
    kp = KeyPair.generate()
    who = create_identity("w")
    if content is None:
        content = {"log": [1, 2, 3], "value": 42}
    att = witness_artifact(
        "witnessed-1", kind, content, kp, who)
    return att, {who.token: kp.public_key_hex()}


def _build_simple_bundle():
    """Direct decision + witnessed attestation + meta decision.
    Returns (bundle, context)."""
    from multiverse_c48 import (
        attest_federated_deliberation,
    )
    # Council decision (direct)
    council_dec, council_keys = _council_decision()
    c_att = attest_decision(
        "council-alpha", council_dec.final_decision)
    # Witnessed swarm log
    w_att, witness_keys = _witnessed_att()
    # Meta council referencing both
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
    meta_keys = {f"meta:m{i}": kp.public_key_hex()
                 for i, kp in enumerate(meta_kps)}
    meta_decision = meta.deliberate_and_resolve_cross_kind(
        Proposal(content={"action": "federate"}),
        attestations=[c_att, w_att])
    bundle = ArchitectureFederationBundle(
        name="test-bundle",
        attestations=(c_att, w_att),
        meta_decision=meta_decision,
        created_at="2024-01-01T00:00:00+00:00",
    )
    context = {
        "member_keys": {
            "council-alpha": council_keys,
            "meta": meta_keys,
        },
        "witness_public_keys": witness_keys,
        "meta_member_keys": meta_keys,
    }
    return bundle, context


# =====================================================================
# Bundle construction
# =====================================================================

def test_bundle_kind_and_version():
    print("=== Bundle: kind and version constants ===")
    assert BUNDLE_KIND == "architecture_federation_bundle"
    assert BUNDLE_VERSION == 1


def test_bundle_requires_name():
    print("=== Bundle: requires name ===")
    with pytest.raises(ValueError):
        ArchitectureFederationBundle(name="")


def test_bundle_validates_attestations():
    print("=== Bundle: validates attestation types ===")
    with pytest.raises(ValueError):
        ArchitectureFederationBundle(
            name="x", attestations=("not an attestation",))


def test_bundle_validates_meta_type():
    print("=== Bundle: validates meta type ===")
    with pytest.raises(ValueError):
        ArchitectureFederationBundle(
            name="x", meta_decision="not a decision")


# =====================================================================
# Save / load roundtrip
# =====================================================================

def test_save_load_roundtrip():
    print("=== Save → load roundtrip ===")
    bundle, _ = _build_simple_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "bundle.json"
        save_bundle(bundle, str(path))
        result = load_bundle(str(path))
        assert result.valid
        assert result.bundle is not None
        assert result.bundle.name == bundle.name
        assert len(result.bundle.attestations) == \
            len(bundle.attestations)
        assert result.bundle.meta_decision is not None


def test_load_missing_file():
    print("=== Load: missing file → LoadResult(False) ===")
    r = load_bundle("/tmp/definitely-not-a-bundle-c49.json")
    assert not r.valid
    assert "not found" in r.reason.lower()


def test_load_malformed_json():
    print("=== Load: malformed JSON → LoadResult(False) ===")
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False) as f:
        f.write("{ not valid json")
        path = f.name
    try:
        r = load_bundle(path)
        assert not r.valid
        assert "invalid JSON" in r.reason
    finally:
        Path(path).unlink()


def test_load_wrong_kind():
    print("=== Load: wrong kind → LoadResult(False) ===")
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False) as f:
        json.dump({"kind": "not_a_bundle", "name": "x"}, f)
        path = f.name
    try:
        r = load_bundle(path)
        assert not r.valid
        assert "kind" in r.reason.lower()
    finally:
        Path(path).unlink()


def test_load_wrong_version():
    print("=== Load: unsupported version → LoadResult(False) ===")
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False) as f:
        json.dump({
            "kind": BUNDLE_KIND,
            "bundle_version": 999,
            "name": "x",
            "created_at": "",
            "attestations": [],
        }, f)
        path = f.name
    try:
        r = load_bundle(path)
        assert not r.valid
        assert "version" in r.reason.lower()
    finally:
        Path(path).unlink()


def test_load_missing_field():
    print("=== Load: missing name → LoadResult(False) ===")
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False) as f:
        json.dump({
            "kind": BUNDLE_KIND,
            "bundle_version": 1,
            "created_at": "",
            "attestations": [],
        }, f)  # no "name"
        path = f.name
    try:
        r = load_bundle(path)
        assert not r.valid
    finally:
        Path(path).unlink()


# =====================================================================
# Strict witnessed verifier
# =====================================================================

def test_strict_witness_requires_trusted_key():
    print("=== Strict witness: requires trusted key in context ===")
    att, _ = _witnessed_att()
    # No witness_public_keys in context
    ok, reason = _verify_witnessed_trusted(att, {})
    assert not ok
    assert "not in trusted set" in reason


def test_strict_witness_accepts_trusted_key():
    print("=== Strict witness: accepts correct trusted key ===")
    att, witness_keys = _witnessed_att()
    ok, reason = _verify_witnessed_trusted(
        att, {"witness_public_keys": witness_keys})
    assert ok


def test_strict_witness_rejects_wrong_trusted_key():
    print("=== Strict witness: rejects wrong trusted key ===")
    att, _ = _witnessed_att()
    wrong_keys = {
        att.witness_token: KeyPair.generate().public_key_hex()}
    ok, reason = _verify_witnessed_trusted(
        att, {"witness_public_keys": wrong_keys})
    assert not ok
    assert "does not match trusted key" in reason


def test_strict_witness_requires_dict():
    print("=== Strict witness: witness_public_keys must be dict ===")
    att, _ = _witnessed_att()
    ok, reason = _verify_witnessed_trusted(
        att, {"witness_public_keys": "not a dict"})
    assert not ok


# =====================================================================
# Trusted registry
# =====================================================================

def test_trusted_registry_uses_strict_for_witnessed():
    print("=== Trusted registry: strict for witnessed kinds ===")
    reg = build_trusted_verifier_registry()
    for kind in WITNESSED_KINDS:
        assert reg[kind] is _verify_witnessed_trusted


def test_trusted_registry_uses_default_for_direct():
    print("=== Trusted registry: default for direct kinds ===")
    reg = build_trusted_verifier_registry()
    for kind in DIRECT_KINDS:
        assert reg[kind] is DEFAULT_VERIFIER_REGISTRY[kind]


def test_trusted_registry_allows_override():
    print("=== Trusted registry: allows overrides ===")
    def custom(att, ctx):
        return (True, "custom")
    reg = build_trusted_verifier_registry(
        overrides={"swarm_log": custom})
    assert reg["swarm_log"] is custom


# =====================================================================
# verify_bundle
# =====================================================================

def test_verify_bundle_happy():
    print("=== verify_bundle: happy path ===")
    bundle, context = _build_simple_bundle()
    v = verify_bundle(bundle, context)
    assert v.valid
    assert len(v.attestation_verdicts) == 2
    assert v.meta_verdict is not None
    assert v.meta_verdict.valid


def test_verify_bundle_missing_witness_key():
    print("=== verify_bundle: missing witness key → fail ===")
    bundle, context = _build_simple_bundle()
    del context["witness_public_keys"]
    v = verify_bundle(bundle, context)
    assert not v.valid
    failed = [av for av in v.attestation_verdicts
              if not av.valid]
    assert any("not in trusted set" in av.reason
               for av in failed)


def test_verify_bundle_missing_member_key():
    print("=== verify_bundle: missing member key → fail ===")
    bundle, context = _build_simple_bundle()
    del context["member_keys"]["council-alpha"]
    v = verify_bundle(bundle, context)
    assert not v.valid
    failed = [av for av in v.attestation_verdicts
              if not av.valid]
    assert any("no member keys" in av.reason
               for av in failed)


def test_verify_bundle_tampered_content():
    print("=== verify_bundle: tampered content → fail ===")
    bundle, context = _build_simple_bundle()
    # Tamper the witnessed attestation's content
    tampered_att_list = list(bundle.attestations)
    for i, a in enumerate(tampered_att_list):
        if a.source_kind == "swarm_log":
            tampered_att_list[i] = FederationAttestation(
                source_id=a.source_id,
                source_kind=a.source_kind,
                content={**a.content, "value": 999},
                content_hash=a.content_hash,  # wrong
                witness_token=a.witness_token,
                witness_name=a.witness_name,
                witness_public_key=a.witness_public_key,
                witness_signature=a.witness_signature,
                witness_timestamp=a.witness_timestamp,
            )
            break
    tampered = ArchitectureFederationBundle(
        name=bundle.name,
        attestations=tuple(tampered_att_list),
        meta_decision=bundle.meta_decision,
        created_at=bundle.created_at,
    )
    v = verify_bundle(tampered, context)
    assert not v.valid


def test_verify_bundle_no_meta():
    print("=== verify_bundle: no meta → only attestations ===")
    _, context = _build_simple_bundle()
    # Build a bundle with only attestations
    council_dec, council_keys = _council_decision()
    c_att = attest_decision(
        "council-alpha", council_dec.final_decision)
    bundle = ArchitectureFederationBundle(
        name="no-meta", attestations=(c_att,))
    ctx = {"member_keys": {"council-alpha": council_keys}}
    v = verify_bundle(bundle, ctx)
    assert v.valid
    assert v.meta_verdict is None


def test_verify_bundle_empty_context():
    print("=== verify_bundle: empty context → fail ===")
    bundle, _ = _build_simple_bundle()
    v = verify_bundle(bundle, {})
    assert not v.valid


def test_verify_bundle_never_raises():
    print("=== verify_bundle: never raises ===")
    assert not verify_bundle(None, {}).valid
    assert not verify_bundle("not a bundle", {}).valid


# =====================================================================
# Context serialization
# =====================================================================

def test_context_serializable_fields():
    print("=== Context: serializable fields constant ===")
    assert "member_keys" in CONTEXT_SERIALIZABLE_FIELDS
    assert "witness_public_keys" in CONTEXT_SERIALIZABLE_FIELDS


def test_save_load_context_roundtrip():
    print("=== Context: save/load roundtrip ===")
    _, context = _build_simple_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "ctx.json"
        save_verification_context(context, str(path))
        revived = load_verification_context(str(path))
        assert "member_keys" in revived
        assert "witness_public_keys" in revived
        assert "meta_member_keys" in revived
        # Roundtrip is faithful for serializable fields
        assert revived["member_keys"] == context["member_keys"]
        assert (revived["witness_public_keys"]
                == context["witness_public_keys"])


def test_load_context_missing_file():
    print("=== Context: missing file → empty dict ===")
    assert load_verification_context(
        "/tmp/definitely-not-a-context-c49.json") == {}


def test_load_context_malformed():
    print("=== Context: malformed JSON → empty dict ===")
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False) as f:
        f.write("{ not valid")
        path = f.name
    try:
        assert load_verification_context(path) == {}
    finally:
        Path(path).unlink()


# =====================================================================
# Subprocess verification
# =====================================================================

def test_subprocess_verifies_honest_bundle():
    """A fresh Python process can load and verify the bundle with
    the serialized context."""
    print("=== Subprocess verifies honest bundle ===")
    bundle, context = _build_simple_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = Path(tmpdir) / "b.json"
        ctx_path = Path(tmpdir) / "c.json"
        save_bundle(bundle, str(bundle_path))
        save_verification_context(context, str(ctx_path))
        script = f"""
import sys
sys.path.insert(0, {str(Path(__file__).parent.resolve())!r})
from multiverse_c49 import (
    load_bundle, load_verification_context, verify_bundle,
)
b = load_bundle({str(bundle_path)!r})
assert b.valid, "load failed: " + b.reason
ctx = load_verification_context({str(ctx_path)!r})
v = verify_bundle(b.bundle, ctx)
assert v.valid, "verify failed: " + v.reason
print("SUBPROCESS-VERIFIED")
"""
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, (
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}")
        assert "SUBPROCESS-VERIFIED" in proc.stdout


def test_subprocess_detects_tampering():
    print("=== Subprocess detects tampering ===")
    bundle, context = _build_simple_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write tampered bundle
        data = bundle.to_dict()
        for att in data["attestations"]:
            if att["source_kind"] == "swarm_log":
                att["content"]["value"] = 999  # tamper
                break
        tampered_path = Path(tmpdir) / "tampered.json"
        tampered_path.write_text(json.dumps(data, indent=2))
        ctx_path = Path(tmpdir) / "c.json"
        save_verification_context(context, str(ctx_path))

        script = f"""
import sys
sys.path.insert(0, {str(Path(__file__).parent.resolve())!r})
from multiverse_c49 import (
    load_bundle, load_verification_context, verify_bundle,
)
b = load_bundle({str(tampered_path)!r})
assert b.valid, "load failed: " + b.reason
ctx = load_verification_context({str(ctx_path)!r})
v = verify_bundle(b.bundle, ctx)
assert not v.valid, "tampered bundle verified"
print("TAMPER-DETECTED")
"""
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, (
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}")
        assert "TAMPER-DETECTED" in proc.stdout


# =====================================================================
# Structural claims
# =====================================================================

def test_bundle_format_survives_json_roundtrip_twice():
    print("=== Bundle: survives JSON roundtrip twice ===")
    bundle, _ = _build_simple_bundle()
    wire1 = json.dumps(bundle.to_dict())
    revived1 = ArchitectureFederationBundle.from_dict(
        json.loads(wire1))
    wire2 = json.dumps(revived1.to_dict())
    revived2 = ArchitectureFederationBundle.from_dict(
        json.loads(wire2))
    assert (wire1 == wire2)  # canonical


def test_bundle_and_c48_verifier_compose():
    """C48's direct verifiers still work on a loaded bundle's
    attestations."""
    print("=== Composition: C48 verifiers work on loaded attestations ===")
    from multiverse_c48 import (
        verify_federation_attestation,
    )
    bundle, context = _build_simple_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "b.json"
        save_bundle(bundle, str(path))
        loaded = load_bundle(str(path))
        assert loaded.valid
        # Use C48's verifier directly
        for a in loaded.bundle.attestations:
            if a.source_kind == "decision":
                v = verify_federation_attestation(
                    a, context,
                    DEFAULT_TRUSTED_VERIFIER_REGISTRY)
                assert v.valid


# =====================================================================
# Never raises
# =====================================================================

def test_load_bundle_never_raises():
    print("=== load_bundle: never raises ===")
    for bad in ["", "/nonexistent/deep/path.json",
                "/tmp", "/etc"]:
        r = load_bundle(bad)
        assert isinstance(r, LoadResult)
        assert not r.valid


def test_save_never_raises_on_bad_path():
    print("=== save_bundle: raises on bad path (documented) ===")
    # Save is not a visitor-input function; raising is fine
    bundle, _ = _build_simple_bundle()
    with pytest.raises((OSError, FileNotFoundError)):
        save_bundle(bundle, "/nonexistent/deep/path/x.json")


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: persistence with subprocess verification ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["in_process_valid"] is True
    assert audit["subprocess_verified"] is True
    assert audit["tamper_detected"] is True
    assert audit["empty_context_valid"] is False
    assert (tmp_path / "architecture_federation_bundle.json").exists()
    assert (tmp_path / "federation_verification_context.json").exists()
    assert (tmp_path / "tampered_federation_bundle.json").exists()


if __name__ == "__main__":
    test_bundle_kind_and_version()
    test_bundle_requires_name()
    test_bundle_validates_attestations()
    test_bundle_validates_meta_type()
    test_save_load_roundtrip()
    test_load_missing_file()
    test_load_malformed_json()
    test_load_wrong_kind()
    test_load_wrong_version()
    test_load_missing_field()
    test_strict_witness_requires_trusted_key()
    test_strict_witness_accepts_trusted_key()
    test_strict_witness_rejects_wrong_trusted_key()
    test_strict_witness_requires_dict()
    test_trusted_registry_uses_strict_for_witnessed()
    test_trusted_registry_uses_default_for_direct()
    test_trusted_registry_allows_override()
    test_verify_bundle_happy()
    test_verify_bundle_missing_witness_key()
    test_verify_bundle_missing_member_key()
    test_verify_bundle_tampered_content()
    test_verify_bundle_no_meta()
    test_verify_bundle_empty_context()
    test_verify_bundle_never_raises()
    test_context_serializable_fields()
    test_save_load_context_roundtrip()
    test_load_context_missing_file()
    test_load_context_malformed()
    test_subprocess_verifies_honest_bundle()
    test_subprocess_detects_tampering()
    test_bundle_format_survives_json_roundtrip_twice()
    test_bundle_and_c48_verifier_compose()
    test_load_bundle_never_raises()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
