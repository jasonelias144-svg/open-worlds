# wcp_conformance_v02_test.py
import json
import pytest

from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c6 import MultiverseRegistry
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, SignedWorld, SignedAdmission, SignedAck,
    canonical_bytes, verify_signature,
)
from multiverse_c14 import PermissiveWorld
from wcp_conformance_v02 import (
    check_manifest_version_any, check_manifest_public_key,
    check_admission_signature, check_ack_signature,
    InProcessEndpointV02, ConformanceRunnerV02, ReportV02,
    _response_dict_v02,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO,
    reason="cryptography not installed (pip install cryptography)")


# =====================================================================
# Individual checks
# =====================================================================

def test_version_check_accepts_both():
    print("=== Version check accepts 0.1 and 0.2 ===")
    for v in ("WCP/0.1", "WCP/0.2"):
        c = check_manifest_version_any({"protocol_version": v})
        print(f"  {v}: passed={c.passed}")
        assert c.passed


def test_version_check_rejects_unknown():
    print("=== Version check rejects unknown versions ===")
    for v in ("", "WCP/0.3", "wcp/0.1", "0.1"):
        c = check_manifest_version_any({"protocol_version": v})
        print(f"  {v!r}: passed={c.passed}")
        assert not c.passed


def test_public_key_optional_for_01():
    print("=== public_key check: optional for WCP/0.1 ===")
    c = check_manifest_public_key({
        "protocol_version": "WCP/0.1",
        # no public_key
    })
    assert c.passed
    assert "not required" in c.detail


def test_public_key_required_for_02():
    print("=== public_key check: required for WCP/0.2 ===")
    c = check_manifest_public_key({
        "protocol_version": "WCP/0.2",
        # no public_key
    })
    assert not c.passed
    print(f"  {c.detail}")


def test_public_key_must_be_64_hex():
    print("=== public_key must be 64 hex chars ===")
    kp = KeyPair.generate()
    good = kp.public_key_hex()
    c = check_manifest_public_key({
        "protocol_version": "WCP/0.2",
        "public_key": good,
    })
    assert c.passed

    # Too short
    c = check_manifest_public_key({
        "protocol_version": "WCP/0.2",
        "public_key": "abc",
    })
    assert not c.passed

    # Not hex
    c = check_manifest_public_key({
        "protocol_version": "WCP/0.2",
        "public_key": "z" * 64,
    })
    assert not c.passed


# =====================================================================
# Signature checks
# =====================================================================

def test_signed_admission_passes_when_valid():
    print("=== Signed admission: valid passes ===")
    kp = KeyPair.generate()
    pub = kp.public_key_hex()
    subject = "alice:token"
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject,
    })
    response = {
        "kind": "admission",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject,
        "signature": kp.sign(canonical).hex(),
    }
    c = check_admission_signature(response, pub, subject)
    print(f"  passed: {c.passed}, detail: {c.detail}")
    assert c.passed


def test_signed_admission_fails_on_forgery():
    print("=== Signed admission: forgery fails ===")
    real_kp = KeyPair.generate()
    attacker_kp = KeyPair.generate()
    pub = real_kp.public_key_hex()
    subject = "attacker:token"
    # Attacker signs with attacker_kp, claims to be world:test
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject,
    })
    response = {
        "kind": "admission",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject,
        "signature": attacker_kp.sign(canonical).hex(),
    }
    c = check_admission_signature(response, pub, subject)
    print(f"  passed: {c.passed}, detail: {c.detail}")
    assert not c.passed
    assert "INVALID" in c.detail


def test_signed_admission_fails_on_wrong_subject():
    print("=== Signed admission: mismatched subject_token fails ===")
    kp = KeyPair.generate()
    pub = kp.public_key_hex()
    real_subject = "alice:token"
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": real_subject,
    })
    response = {
        "kind": "admission",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": real_subject,
        "signature": kp.sign(canonical).hex(),
    }
    # Ask verifier to expect a different subject
    c = check_admission_signature(response, pub, "bob:token")
    print(f"  passed: {c.passed}, detail: {c.detail}")
    assert not c.passed
    assert "subject_token" in c.detail


def test_signed_admission_n_a_for_refusal():
    print("=== Signed admission: N/A for refusal ===")
    response = {"kind": "refusal", "reason": "no thanks"}
    c = check_admission_signature(response, "", "alice:token")
    print(f"  passed: {c.passed}, detail: {c.detail}")
    assert c.passed
    assert "not an admission" in c.detail


def test_signed_ack_passes_when_valid():
    print("=== Signed ack: valid passes ===")
    kp = KeyPair.generate()
    pub = kp.public_key_hex()
    subject = "alice:token"
    canonical = canonical_bytes({
        "kind": "ack",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject,
    })
    response = {
        "kind": "ack",
        "entity_id": "world:test",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": subject,
        "signature": kp.sign(canonical).hex(),
    }
    c = check_ack_signature(response, pub, subject)
    print(f"  passed: {c.passed}")
    assert c.passed


def test_signed_ack_n_a_for_refusal():
    print("=== Signed ack: N/A for refusal ===")
    response = {"kind": "refusal", "reason": "not admitted"}
    c = check_ack_signature(response, "", "alice:token")
    print(f"  passed: {c.passed}, detail: {c.detail}")
    assert c.passed
    assert "not an ack" in c.detail


# =====================================================================
# Auto-detection: WCP/0.1 entities
# =====================================================================

def test_v01_poetry_world_passes():
    print("=== WCP/0.1 Poetry World passes ===")
    world = PoetryWorld("world:poetry", "The Poetry World")
    report = ConformanceRunnerV02(
        InProcessEndpointV02(world), label="poetry").run()
    print(f"  version: {report.version}")
    print(f"  signed:  {report.signed}")
    print(f"  passed:  {report.passed}")
    assert report.passed
    assert report.version == "WCP/0.1"
    assert report.signed is False
    # No signature checks were run (they're only added for 0.2)
    names = [c.name for c in report.checks]
    assert "admission_signature" not in names
    assert "ack_signature" not in names


def test_v01_multiverse_passes():
    print("=== WCP/0.1 Multiverse passes ===")
    mv = MultiverseRegistry("multiverse:main", "Main MV")
    report = ConformanceRunnerV02(
        InProcessEndpointV02(mv), label="mv").run()
    assert report.passed
    assert report.version == "WCP/0.1"


# =====================================================================
# Auto-detection: WCP/0.2 signed entities
# =====================================================================

def test_v02_signed_poetry_world_passes():
    print("=== WCP/0.2 signed Poetry World passes ===")
    base = PoetryWorld("world:poetry", "The Poetry World")
    signed = SignedWorld(base)
    report = ConformanceRunnerV02(
        InProcessEndpointV02(signed), label="signed-poetry").run()
    print(f"  version: {report.version}")
    print(f"  signed:  {report.signed}")
    print(f"  passed:  {report.passed}")
    print(f"  checks:  {[c.name for c in report.checks]}")
    assert report.passed
    assert report.version == "WCP/0.2"
    assert report.signed is True
    names = [c.name for c in report.checks]
    assert "manifest_public_key" in names
    assert "admission_signature" in names
    assert "ack_signature" in names


def test_v02_signed_permissive_world_acks_are_verified():
    print("=== WCP/0.2 signed Permissive World: acks verified ===")
    base = PermissiveWorld()
    signed = SignedWorld(base)
    report = ConformanceRunnerV02(
        InProcessEndpointV02(signed), label="signed-permissive").run()
    assert report.passed
    # Find the ack signature check
    ack_check = next(c for c in report.checks
                     if c.name == "ack_signature")
    print(f"  ack signature: {ack_check.passed}, {ack_check.detail}")
    assert ack_check.passed
    assert "verified" in ack_check.detail


def test_v02_signed_world_with_broken_signature_fails():
    print("=== WCP/0.2 signed world with broken signature fails ===")

    class BrokenSignedWorld(SignedWorld):
        """Claims to be signed but returns unsigned admissions."""
        def petition(self, petition):
            # Return WCP/0.1 Admission — no signature
            from multiverse_c3 import Admission
            response = self.base.petition(petition)
            if isinstance(response, Admission):
                # Convert to a fake SignedAdmission with empty sig
                return SignedAdmission(
                    entity_id=response.entity_id,
                    timestamp=response.timestamp,
                    subject_token=petition.petitioner_token,
                    signature="00" * 64,  # wrong
                )
            return response

    base = PoetryWorld("world:broken", "Broken")
    broken = BrokenSignedWorld(base)
    report = ConformanceRunnerV02(
        InProcessEndpointV02(broken), label="broken").run()
    print(f"  passed: {report.passed}")
    fails = [c.name for c in report.failures()]
    print(f"  failures: {fails}")
    assert not report.passed
    assert "admission_signature" in fails


def test_v02_world_missing_public_key_fails():
    print("=== WCP/0.2 manifest missing public_key fails ===")

    class NoKeyWorld(SignedWorld):
        def manifest_dict(self):
            d = super().manifest_dict()
            del d["public_key"]
            return d

    base = PermissiveWorld()
    nokey = NoKeyWorld(base)
    report = ConformanceRunnerV02(
        InProcessEndpointV02(nokey), label="nokey").run()
    print(f"  passed: {report.passed}")
    fails = [c.name for c in report.failures()]
    print(f"  failures: {fails}")
    assert not report.passed
    assert "manifest_public_key" in fails


# =====================================================================
# --expect-version enforcement
# =====================================================================

def test_expect_v02_rejects_v01():
    print("=== --expect-version 0.2 rejects a WCP/0.1 entity ===")
    world = PoetryWorld("world:poetry", "The Poetry World")
    report = ConformanceRunnerV02(
        InProcessEndpointV02(world), label="poetry",
        expect_version="0.2").run()
    print(f"  passed: {report.passed}")
    fails = [c.name for c in report.failures()]
    print(f"  failures: {fails}")
    assert not report.passed
    assert "expect_version" in fails


def test_expect_v02_accepts_signed():
    print("=== --expect-version 0.2 accepts a WCP/0.2 entity ===")
    base = PermissiveWorld()
    signed = SignedWorld(base)
    report = ConformanceRunnerV02(
        InProcessEndpointV02(signed), label="signed",
        expect_version="0.2").run()
    assert report.passed


# =====================================================================
# Report formatting
# =====================================================================

def test_report_format_v01():
    print("=== Report format: WCP/0.1 ===")
    world = PoetryWorld("world:poetry", "The Poetry World")
    report = ConformanceRunnerV02(
        InProcessEndpointV02(world), label="poetry").run()
    text = report.format()
    assert "WCP/0.1 (unsigned" in text
    assert "PASSES" in text
    print(text[:400] + "...")


def test_report_format_v02():
    print("=== Report format: WCP/0.2 ===")
    base = PermissiveWorld()
    signed = SignedWorld(base)
    report = ConformanceRunnerV02(
        InProcessEndpointV02(signed), label="signed").run()
    text = report.format()
    assert "WCP/0.2 (signed)" in text
    assert "Public key:" in text
    print(text[:400] + "...")


# =====================================================================
# Over HTTP
# =====================================================================

def test_http_signed_world():
    print("=== Over HTTP: signed Poetry World ===")
    base = PoetryWorld("world:poetry", "The Poetry World")
    signed = SignedWorld(base)
    server = WorldProtocolServer(signed, port=0)
    server.serve_in_thread()
    try:
        import time; time.sleep(0.1)
        port = server._httpd.server_address[1]
        from wcp_conformance import HTTPEndpoint
        report = ConformanceRunnerV02(
            HTTPEndpoint(f"http://127.0.0.1:{port}"),
            label=f"http://127.0.0.1:{port}").run()
        print(f"  passed: {report.passed}")
        print(f"  version: {report.version}")
        if not report.passed:
            for c in report.failures():
                print(f"    {c.name}: {c.detail}")
        assert report.passed
        assert report.version == "WCP/0.2"
    finally:
        server.stop()


def test_http_v01_and_v02_agree_in_process():
    print("=== HTTP and in-process produce same result ===")
    base = PermissiveWorld()
    signed = SignedWorld(base)

    inproc = ConformanceRunnerV02(
        InProcessEndpointV02(signed), label="inproc").run()

    server = WorldProtocolServer(signed, port=0)
    server.serve_in_thread()
    try:
        import time; time.sleep(0.1)
        port = server._httpd.server_address[1]
        from wcp_conformance import HTTPEndpoint
        http_report = ConformanceRunnerV02(
            HTTPEndpoint(f"http://127.0.0.1:{port}"),
            label=f"http://127.0.0.1:{port}").run()
    finally:
        server.stop()

    print(f"  in-process: passed={inproc.passed}, "
          f"{inproc.passed_count}/{inproc.total_count}")
    print(f"  http:       passed={http_report.passed}, "
          f"{http_report.passed_count}/{http_report.total_count}")
    assert inproc.passed == http_report.passed
    assert inproc.total_count == http_report.total_count


# =====================================================================
# CLI
# =====================================================================

def test_cli_v01_entity_passes():
    print("=== CLI: WCP/0.1 entity passes ===")
    from wcp_conformance_v02 import main
    code = main(["--in-process", "multiverse_c4:PoetryWorld", "--quiet"])
    print(f"  exit: {code}")
    assert code == 0


def test_cli_signed_entity_passes():
    print("=== CLI: signed entity passes ===")
    from wcp_conformance_v02 import main
    # Sign a PermissiveWorld by name; but the CLI needs a factory.
    # Use a factory defined in multiverse_c14.
    code = main(["--in-process",
                 "multiverse_c14:_signed_permissive_factory",
                 "--quiet"])
    print(f"  exit: {code}")
    assert code == 0


def test_cli_expect_v02_on_v01_fails():
    print("=== CLI: --expect-version 0.2 on WCP/0.1 entity fails ===")
    from wcp_conformance_v02 import main
    code = main(["--in-process", "multiverse_c4:PoetryWorld",
                 "--expect-version", "0.2", "--quiet"])
    print(f"  exit: {code}")
    assert code == 1


# A factory for the CLI test above
def _signed_permissive_factory():
    return SignedWorld(PermissiveWorld())
