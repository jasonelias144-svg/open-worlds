# multiverse_c32_test.py
import json
import subprocess
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

import pytest

from multiverse_c1 import create_identity, Identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, SignedWorld, SignedAdmission
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import PassportV2, PassportEntry
from multiverse_c28 import SignedManifestWorld, sign_manifest
from multiverse_c29 import SignedListingRegistry
from multiverse_c31 import (
    FederationVerdict, sign_federation_verdict,
)
from multiverse_c32 import (
    LogEntryRecord, WorldState, RegistryState, PassportState,
    FederationBundle, LoadResult,
    bundle_from_live, save_bundle, save_bundle_to_dir,
    load_bundle, verify_loaded_bundle, BundleVerification,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers — build a small but complete bundle in memory
# =====================================================================

def _build_live_federation():
    """Return the artifacts needed to build a bundle, plus the
    registries and worlds. Everything in-process; no HTTP."""
    from multiverse_c3 import Petition, Act

    world_kp = KeyPair.generate()
    reg_kp = KeyPair.generate()
    verifier_kp = KeyPair.generate()
    verifier = create_identity("Verifier")

    # World
    base = PermissiveWorld("world:a", "World A")
    signed_responses = SignedWorld(base, world_kp)
    world = SignedManifestWorld(signed_responses, world_kp)

    # Registry
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)

    # Registry admits world (in-process path)
    registry.petition(Petition(
        petitioner_token="admin", petitioner_name="Admin",
        passport_admissions=(), message="setup"))
    registry.act(Act(
        actor_token="admin", type="multiverse.admit",
        payload={"entity": world}))

    # Client petitions world
    alice = create_identity("Alice")
    adm = world.petition(Petition(
        petitioner_token=alice.token,
        petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    assert isinstance(adm, SignedAdmission)
    passport = PassportV2(
        identity=Identity(token=alice.token, name=alice.name),
        entries=(PassportEntry(
            entity_id=adm.entity_id,
            timestamp=adm.timestamp,
            subject_token=adm.subject_token,
            signature=adm.signature,
        ),),
    )

    # Signed verdict
    verdict = FederationVerdict(
        conformance_passed=True,
        world_admitted=True,
        world_offline_at_verification=True,
        listing_count=1,
        passport_verified_without_world=True,
        world_public_key=world_kp.public_key_hex(),
        registry_public_key=reg_kp.public_key_hex(),
    )
    signed_verdict = sign_federation_verdict(
        verdict, verifier_kp, verifier)

    return {
        "world": world,
        "registry": registry,
        "world_log": world.log_since(None),
        "registry_log": registry.log_since(None),
        "passports": [passport],
        "signed_verdict": signed_verdict,
        "verifier_kp": verifier_kp,
    }


def _make_bundle(**overrides) -> FederationBundle:
    parts = _build_live_federation()
    parts.update(overrides)
    return bundle_from_live(
        world=parts["world"],
        registry=parts["registry"],
        world_log=parts["world_log"],
        registry_log=parts["registry_log"],
        passports=parts["passports"],
        signed_verdict=parts["signed_verdict"],
        verifier_public_key=parts["verifier_kp"].public_key_hex(),
    )


# =====================================================================
# Bundle construction
# =====================================================================

def test_bundle_construction():
    print("=== Bundle: construction from live components ===")
    bundle = _make_bundle()
    assert bundle.world.entity_id == "world:a"
    assert bundle.registry.entity_id == "multiverse:main"
    assert len(bundle.passports) == 1
    assert bundle.signed_verdict["kind"] == "signed_federation_verdict"
    assert len(bundle.verifier_public_key) == 64


def test_bundle_to_dict_from_dict_roundtrip():
    print("=== Bundle: to_dict / from_dict roundtrip ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    wire = json.dumps(d)
    parsed = json.loads(wire)
    revived = FederationBundle.from_dict(parsed)
    assert revived.world.entity_id == bundle.world.entity_id
    assert revived.registry.entity_id == bundle.registry.entity_id
    assert len(revived.passports) == len(bundle.passports)
    assert revived.verifier_public_key == bundle.verifier_public_key
    assert len(revived.world.log) == len(bundle.world.log)


def test_bundle_from_dict_rejects_wrong_kind():
    print("=== Bundle rejects wrong kind field ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    d["kind"] = "not_a_bundle"
    with pytest.raises(ValueError):
        FederationBundle.from_dict(d)


def test_bundle_from_dict_rejects_missing_field():
    print("=== Bundle rejects missing required field ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    del d["world"]
    with pytest.raises(KeyError):
        FederationBundle.from_dict(d)


# =====================================================================
# Save / load
# =====================================================================

def test_save_and_load_roundtrip():
    print("=== Save → load → verify ===")
    bundle = _make_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_bundle_to_dir(bundle, tmpdir)
        assert path.exists()
        assert path.name == "federation_bundle.json"
        result = load_bundle(str(path))
        assert result.valid
        assert result.bundle is not None
        assert result.bundle.verifier_public_key == \
            bundle.verifier_public_key


def test_load_missing_file():
    print("=== Load: missing file returns LoadResult(False) ===")
    result = load_bundle("/tmp/definitely-not-a-bundle.json")
    assert not result.valid
    assert "not found" in result.reason.lower()


def test_load_malformed_json():
    print("=== Load: malformed JSON returns LoadResult(False) ===")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False) as f:
        f.write("{not valid json")
        path = f.name
    try:
        result = load_bundle(path)
        assert not result.valid
        assert "invalid JSON" in result.reason
    finally:
        Path(path).unlink()


def test_load_invalid_shape():
    print("=== Load: valid JSON, wrong shape → LoadResult(False) ===")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False) as f:
        json.dump({"kind": "not_a_bundle"}, f)
        path = f.name
    try:
        result = load_bundle(path)
        assert not result.valid
        assert "invalid bundle shape" in result.reason.lower() \
            or "kind" in result.reason.lower()
    finally:
        Path(path).unlink()


# =====================================================================
# Verification — happy path
# =====================================================================

def test_verify_valid_bundle():
    print("=== Verify: valid bundle passes all checks ===")
    bundle = _make_bundle()
    result = verify_loaded_bundle(
        bundle,
        expected_verifier_key=bundle.verifier_public_key)
    print(result.format())
    assert result.valid
    assert result.world_public_key is not None
    assert result.registry_public_key is not None
    assert result.checks["world_manifest_self_verified"]
    assert result.checks["registry_manifest_self_verified"]
    assert result.checks["registry_has_signed_listing"]
    assert result.checks["listing_world_key_matches"]
    assert result.checks["passport_0_verified"]
    assert result.checks["verdict_verified"]


def test_verify_without_expected_verifier_key():
    print("=== Verify: no expected key, uses bundle's own key ===")
    bundle = _make_bundle()
    result = verify_loaded_bundle(bundle)
    assert result.valid
    assert "verifier_key_matches" not in result.checks


def test_verify_contacts_no_urls():
    print("=== Verify: contacts no URLs ===")
    bundle = _make_bundle()
    # If verify_loaded_bundle touches urllib, this raises
    with mock.patch(
        "urllib.request.urlopen",
        side_effect=RuntimeError("should not fetch"),
    ):
        result = verify_loaded_bundle(bundle)
    assert result.valid


# =====================================================================
# Verification — failure cases
# =====================================================================

def test_tampered_world_manifest_rejected():
    print("=== Verify: tampered world manifest rejected ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    d["world"]["signed_manifest"]["name"] = "Tampered Name"
    tampered = FederationBundle.from_dict(d)
    result = verify_loaded_bundle(tampered)
    assert not result.valid
    assert not result.checks.get("world_manifest_self_verified", False)


def test_tampered_world_key_rejected():
    print("=== Verify: tampered world_public_key rejected ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    d["world"]["signed_manifest"]["public_key"] = "ff" * 32
    tampered = FederationBundle.from_dict(d)
    result = verify_loaded_bundle(tampered)
    assert not result.valid
    assert not result.checks.get("world_manifest_self_verified", False)


def test_tampered_registry_manifest_rejected():
    print("=== Verify: tampered registry manifest rejected ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    d["registry"]["signed_manifest"]["name"] = "Tampered"
    tampered = FederationBundle.from_dict(d)
    result = verify_loaded_bundle(tampered)
    assert not result.valid
    assert not result.checks.get("registry_manifest_self_verified",
                                  False)


def test_tampered_listing_rejected():
    print("=== Verify: tampered listing signature rejected ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    # Flip a byte in the first signed_listing's signature
    for entry in d["registry"]["log"]:
        if entry["kind"] == "signed_listing":
            sig = entry["data"]["signature_v2"]
            entry["data"]["signature_v2"] = \
                ("0" if sig[0] != "0" else "1") + sig[1:]
            break
    tampered = FederationBundle.from_dict(d)
    result = verify_loaded_bundle(tampered)
    assert not result.valid


def test_tampered_passport_rejected():
    print("=== Verify: tampered passport entry rejected ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    # Swap a byte in the passport's signature
    sig = d["passports"][0]["entries"][0]["signature"]
    d["passports"][0]["entries"][0]["signature"] = \
        ("0" if sig[0] != "0" else "1") + sig[1:]
    tampered = FederationBundle.from_dict(d)
    result = verify_loaded_bundle(tampered)
    assert not result.valid
    assert not result.checks.get("passport_0_verified", False)


def test_tampered_verdict_rejected():
    print("=== Verify: tampered verdict rejected ===")
    bundle = _make_bundle()
    d = bundle.to_dict()
    d["signed_verdict"]["verdict"]["passport_verified_without_world"] = \
        False
    tampered = FederationBundle.from_dict(d)
    result = verify_loaded_bundle(tampered)
    assert not result.valid
    assert not result.checks.get("verdict_verified", False)


def test_wrong_expected_verifier_key_rejected():
    print("=== Verify: wrong expected_verifier_key rejected ===")
    bundle = _make_bundle()
    wrong = KeyPair.generate().public_key_hex()
    result = verify_loaded_bundle(
        bundle, expected_verifier_key=wrong)
    assert not result.valid
    assert not result.checks.get("verifier_key_matches", False)


# =====================================================================
# Never raises
# =====================================================================

def test_verify_never_raises_on_bad_input():
    print("=== Verify: never raises on bad input ===")
    # Missing required sections
    bundle = _make_bundle()
    # Break the signed_verdict to a non-dict-like value
    d = bundle.to_dict()
    d["signed_verdict"] = "not a dict"
    try:
        broken = FederationBundle.from_dict(d)
        result = verify_loaded_bundle(broken)
        assert not result.valid
    except (KeyError, ValueError, TypeError):
        # Also acceptable: the constructor rejects it
        pass


def test_load_never_raises():
    print("=== Load: never raises on any input ===")
    # Pathologically bad paths
    for bad in ["", "/nonexistent/deeply/nested/x.json",
                "/tmp", "/etc"]:
        result = load_bundle(bad)
        assert not result.valid


# =====================================================================
# Bundle is internally consistent
# =====================================================================

def test_listing_world_key_matches_manifest():
    print("=== Listing's world key matches world's own manifest ===")
    bundle = _make_bundle()
    result = verify_loaded_bundle(bundle)
    assert result.checks["listing_world_key_matches"]


def test_world_manifest_entity_id_matches():
    print("=== World manifest entity_id matches world.entity_id ===")
    bundle = _make_bundle()
    result = verify_loaded_bundle(bundle)
    assert result.checks["world_manifest_entity_id_matches"]


# =====================================================================
# End-to-end: subprocess verification
# =====================================================================

def test_fresh_process_verification():
    """The bundle verifies in a subprocess with no shared state.
    This is the property that makes the artifact directory usable:
    a third party can load and verify without any of our live
    objects."""
    print("=== Fresh-process verification ===")
    bundle = _make_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_bundle_to_dir(bundle, tmpdir)
        # Save the expected verifier key alongside (real deployment
        # publishes it via a registry; the demo saves it)
        key_path = Path(tmpdir) / "verifier_public_key.txt"
        key_path.write_text(bundle.verifier_public_key)

        script = f"""
import json
import sys
sys.path.insert(0, {str(Path(__file__).parent)!r})
from multiverse_c32 import load_bundle, verify_loaded_bundle
key = open({str(key_path)!r}).read().strip()
result = load_bundle({str(path)!r})
assert result.valid, "load failed: " + result.reason
verify = verify_loaded_bundle(result.bundle, expected_verifier_key=key)
if not verify.valid:
    print(verify.format())
    sys.exit(1)
print("FRESH-PROCESS-VERIFIED")
"""
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, (
            f"subprocess failed:\n"
            f"stdout: {proc.stdout}\n"
            f"stderr: {proc.stderr}")
        assert "FRESH-PROCESS-VERIFIED" in proc.stdout
        print("  fresh-process verification: PASS")


if __name__ == "__main__":
    test_bundle_construction()
    test_bundle_to_dict_from_dict_roundtrip()
    test_bundle_from_dict_rejects_wrong_kind()
    test_bundle_from_dict_rejects_missing_field()
    test_save_and_load_roundtrip()
    test_load_missing_file()
    test_load_malformed_json()
    test_load_invalid_shape()
    test_verify_valid_bundle()
    test_verify_without_expected_verifier_key()
    test_verify_contacts_no_urls()
    test_tampered_world_manifest_rejected()
    test_tampered_world_key_rejected()
    test_tampered_registry_manifest_rejected()
    test_tampered_listing_rejected()
    test_tampered_passport_rejected()
    test_tampered_verdict_rejected()
    test_wrong_expected_verifier_key_rejected()
    test_verify_never_raises_on_bad_input()
    test_load_never_raises()
    test_listing_world_key_matches_manifest()
    test_world_manifest_entity_id_matches()
    test_fresh_process_verification()
