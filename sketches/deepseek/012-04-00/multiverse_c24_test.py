# multiverse_c24_test.py
import json
import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c15 import PassportEntry
from multiverse_c21 import ProvenanceReport, EntryProvenance
from multiverse_c23 import (
    VisitedPassportReport, WorldProvenance,
    VisitProvenance, Visit,
)
from multiverse_c24 import (
    SUPPORTED_REPORT_TYPES,
    SignedProvenanceReport,
    sign_report, verify_signed_report, extract_report_content,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers — stub reports
# =====================================================================

class _StubEntryProv:
    """Minimal stand-in for C21/C22 EntryProvenance, with .verdict."""
    def __init__(self, entry, verdict="verified"):
        self.entry = entry
        self.verdict = verdict
        self.manifest_public_key = "aa" * 32


def _entry(eid: str) -> PassportEntry:
    return PassportEntry(
        entity_id=eid,
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token="alice-token",
        signature="bb" * 64,
    )


def _stub_provenance_report(name="Alice",
                             entity_ids=("world:a",)) -> ProvenanceReport:
    rep = ProvenanceReport(
        passport_token="alice-token",
        passport_name=name,
        registry_url="http://registry",
    )
    for eid in entity_ids:
        ep = EntryProvenance(entry=_entry(eid))
        ep.verdict = "verified"
        ep.reason = "all stages verified"
        rep.entries.append(ep)
    return rep


def _stub_visited_report(name="Alice",
                         entity_ids=("world:a",)) -> VisitedPassportReport:
    rep = VisitedPassportReport(
        passport_token="alice-token", passport_name=name,
    )
    for eid in entity_ids:
        entry = _entry(eid)
        visit = Visit(admission=entry, departure=None)
        vp = VisitProvenance(
            visit=visit, visit_index=1, is_last_visit=True,
            admission_provenance=_StubEntryProv(entry),
        )
        w = WorldProvenance(entity_id=eid, visits=[vp])
        rep.worlds.append(w)
    return rep


# =====================================================================
# Happy path
# =====================================================================

def test_sign_and_verify_provenance():
    print("=== Sign and verify: provenance report ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report()
    signed = sign_report(report, kp, auditor)
    assert verify_signed_report(signed, kp.public_key_hex())
    assert signed.report_type == "provenance"
    print(f"  signer: {signed.signer_name} "
          f"({signed.signer_id[:16]}...)")


def test_sign_and_verify_visited():
    print("=== Sign and verify: visited report ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_visited_report(entity_ids=("world:a", "world:b"))
    signed = sign_report(report, kp, auditor)
    assert verify_signed_report(signed, kp.public_key_hex())
    assert signed.report_type == "visited"


# =====================================================================
# Tampering — signature covers everything
# =====================================================================

def test_tampered_report_breaks_verification():
    print("=== Tampering with the report breaks the signature ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report()
    signed = sign_report(report, kp, auditor)
    tampered_report = dict(signed.report)
    tampered_report["all_verified"] = False
    tampered = SignedProvenanceReport(
        signer_id=signed.signer_id,
        signer_name=signed.signer_name,
        report_type=signed.report_type,
        report=tampered_report,
        timestamp=signed.timestamp,
        signature=signed.signature,
    )
    assert not verify_signed_report(tampered, kp.public_key_hex())


def test_tampered_signer_name_breaks_verification():
    print("=== Tampering with signer_name breaks the signature ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report()
    signed = sign_report(report, kp, auditor)
    tampered = SignedProvenanceReport(
        signer_id=signed.signer_id,
        signer_name="Impostor",
        report_type=signed.report_type,
        report=signed.report,
        timestamp=signed.timestamp,
        signature=signed.signature,
    )
    assert not verify_signed_report(tampered, kp.public_key_hex())


def test_tampered_report_type_breaks_verification():
    print("=== Tampering with report_type breaks the signature ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report()
    signed = sign_report(report, kp, auditor)
    tampered = SignedProvenanceReport(
        signer_id=signed.signer_id,
        signer_name=signed.signer_name,
        report_type="visited",   # was "provenance"
        report=signed.report,
        timestamp=signed.timestamp,
        signature=signed.signature,
    )
    assert not verify_signed_report(tampered, kp.public_key_hex())


def test_tampered_timestamp_breaks_verification():
    print("=== Tampering with the timestamp breaks the signature ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report()
    signed = sign_report(report, kp, auditor)
    tampered = SignedProvenanceReport(
        signer_id=signed.signer_id,
        signer_name=signed.signer_name,
        report_type=signed.report_type,
        report=signed.report,
        timestamp="2030-01-01T00:00:00+00:00",
        signature=signed.signature,
    )
    assert not verify_signed_report(tampered, kp.public_key_hex())


# =====================================================================
# Wrong key
# =====================================================================

def test_wrong_public_key():
    print("=== Wrong public key → verification fails ===")
    kp_real = KeyPair.generate()
    kp_other = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report()
    signed = sign_report(report, kp_real, auditor)
    assert verify_signed_report(signed, kp_real.public_key_hex())
    assert not verify_signed_report(signed, kp_other.public_key_hex())


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_json_roundtrip_preserves_verification():
    print("=== JSON roundtrip preserves verification ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report(entity_ids=("world:a", "world:b"))
    signed = sign_report(report, kp, auditor)
    wire = json.dumps(signed.to_dict())
    received = SignedProvenanceReport.from_dict(json.loads(wire))
    assert verify_signed_report(received, kp.public_key_hex())
    assert received.signer_name == signed.signer_name
    assert received.report_type == signed.report_type


# =====================================================================
# Extract
# =====================================================================

def test_extract_returns_report_content():
    print("=== extract_report_content returns the signed report ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report(
        entity_ids=("world:a", "world:b", "world:c"))
    signed = sign_report(report, kp, auditor)
    content = extract_report_content(signed)
    assert content == signed.report
    assert content["passport_name"] == "Alice"
    assert len(content["entries"]) == 3


# =====================================================================
# Never raises
# =====================================================================

def test_verifier_never_raises_on_bad_input():
    print("=== verify_signed_report never raises on bad input ===")
    # Not a SignedProvenanceReport at all
    assert not verify_signed_report("not-a-report", "aa" * 32)
    assert not verify_signed_report(None, "aa" * 32)
    assert not verify_signed_report({}, "aa" * 32)
    # Empty public key
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_provenance_report()
    signed = sign_report(report, kp, auditor)
    assert not verify_signed_report(signed, "")


def test_verifier_rejects_unknown_report_type():
    print("=== Unknown report_type → False ===")
    kp = KeyPair.generate()
    bad = SignedProvenanceReport(
        signer_id="x", signer_name="x",
        report_type="unknown",
        report={},
        timestamp="t",
        signature="aa" * 64,
    )
    assert not verify_signed_report(bad, kp.public_key_hex())


# =====================================================================
# Supported types — guard against drift
# =====================================================================

def test_supported_report_types_constant():
    print("=== SUPPORTED_REPORT_TYPES ===")
    assert SUPPORTED_REPORT_TYPES == {"provenance", "visited"}


# =====================================================================
# The honest limit, made a test
# =====================================================================

def test_signature_attests_authorship_not_truth():
    """The limit named in the module docstring, as a test.

    A dishonest auditor can sign a fabricated report. Every entry
    says 'verified', but nothing was verified. The signature is
    valid — the auditor really signed that report — and the content
    is a lie. The verifier's job is to verify the signature AND
    decide whether to trust the auditor; C24 does only the first.
    """
    print("=== Honest limit: signature attests authorship, not truth ===")
    kp = KeyPair.generate()
    dishonest = create_identity("Dishonest Auditor")
    fabricated = _stub_provenance_report(
        entity_ids=("world:a", "world:b"))
    # Every entry claims 'verified'; nothing was actually checked
    signed = sign_report(fabricated, kp, dishonest)
    # The signature IS valid — the auditor really did sign this
    assert verify_signed_report(signed, kp.public_key_hex())
    print("  signature valid: True")
    print("  content true:    ???  (signature cannot tell)")
    # What a real trust decision looks like:
    #   1. verify_signed_report(signed, known_auditor_key) → True
    #   2. Look up the auditor in a registry (C17)
    #   3. Decide whether to trust that auditor
    # C24 does (1). (2) and (3) are outside its scope.


# =====================================================================
# End-to-end: sign, transport, tamper, verify
# =====================================================================

def test_end_to_end_signed_visited_report():
    print("=== End-to-end: sign a visited report, transport, verify ===")
    kp = KeyPair.generate()
    auditor = create_identity("Auditor")
    report = _stub_visited_report(entity_ids=("world:a", "world:b"))
    signed = sign_report(report, kp, auditor)

    # Transport as JSON
    wire = json.dumps(signed.to_dict())
    received = SignedProvenanceReport.from_dict(json.loads(wire))

    # Original verifies
    assert verify_signed_report(received, kp.public_key_hex())

    # A tampered variant does not
    tampered_dict = received.to_dict()
    tampered_dict["report"] = {**tampered_dict["report"],
                                "all_verified": False}
    tampered = SignedProvenanceReport.from_dict(tampered_dict)
    assert not verify_signed_report(tampered, kp.public_key_hex())
    print("  original: verified")
    print("  tampered: rejected")


# =====================================================================
# Demo
# =====================================================================

def test_demo_runs(tmp_path):
    print("=== Demo: sign, verify, save ===")
    signed = demo(artifact_dir=str(tmp_path))
    assert verify_signed_report(
        signed,
        # The demo used a freshly generated key; recover it from
        # the signature is impossible. So this test only asserts
        # the demo ran without error. Signature verification for
        # a demo artifact is out of scope.
        "irrelevant",
    ) is False  # wrong key — but demo should have succeeded
    # Check the artifact was written
    artifact = tmp_path / "signed_provenance.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["kind"] == "signed_provenance_report"
    assert data["report_type"] == "provenance"
    assert "entries" in data["report"]


if __name__ == "__main__":
    test_sign_and_verify_provenance()
    test_sign_and_verify_visited()
    test_tampered_report_breaks_verification()
    test_tampered_signer_name_breaks_verification()
    test_tampered_report_type_breaks_verification()
    test_tampered_timestamp_breaks_verification()
    test_wrong_public_key()
    test_json_roundtrip_preserves_verification()
    test_extract_returns_report_content()
    test_verifier_never_raises_on_bad_input()
    test_verifier_rejects_unknown_report_type()
    test_supported_report_types_constant()
    test_signature_attests_authorship_not_truth()
    test_end_to_end_signed_visited_report()
