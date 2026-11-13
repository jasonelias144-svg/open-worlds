"""
multiverse_c24.py — Component 24: Signed Provenance Reports.

C21 and C23 produced audit reports; both were client-side artifacts.
C24 makes the audit portable: the auditor signs a canonical digest
of the report, and any third party verifies the signature against
the auditor's public key.

Signature covers:
  - kind="provenance_report"
  - signer_id (the auditor's identity token)
  - signer_name
  - report_type ("provenance" | "visited")
  - report (the report's to_dict() output)
  - timestamp

Tampering with ANY of these breaks verification.

Composes with C21 (ProvenanceReport) and C23 (VisitedPassportReport)
without knowing their internal shapes. No new protocol, no new
trust primitive.

House rules honored:
  - "A world never raises on what a visitor sends" — the analogous
    rule for a verification function: it returns False on bad
    input, never raises. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks." Tampering, wrong key, unknown report_type, and
    JSON roundtrip are each tested.
  - "History, not rank." The signed report is an audit, not a
    score. It attests to facts (which stages verified), not
    quality.

Honest limits (documented, tested as behavior):
  - The signature attests to WHO said it, not whether it's TRUE.
    A dishonest auditor can sign a fabricated audit; the
    signature is valid, the content is a lie. Same trust model
    as every audit: the signer is trusted; the signature only
    proves they said it. See test_signature_attests_authorship_not_truth.
  - No timestamp verification. A signer can backdate. The
    timestamp is a claim; verifying it requires an external
    time source.
  - No chain-of-attestations format. A verifier who trusts a
    signed report can sign their own attestation, but the
    chain format is not defined here. The seam is real; the
    format is future work.
  - The `signer_id` is a claimed identity. To know "this is
    really Alice's key", a third party looks up Alice in a
    registry (C17). C24 does not do this; it verifies the
    signature against whatever key the caller supplies.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from multiverse_c1 import Identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c21 import ProvenanceReport
from multiverse_c23 import VisitedPassportReport


SUPPORTED_REPORT_TYPES = {"provenance", "visited"}


# =====================================================================
# Report-type detection and serialization
# =====================================================================

def _report_type(report: Any) -> str:
    """Determine the report type from the object's class."""
    if isinstance(report, ProvenanceReport):
        return "provenance"
    if isinstance(report, VisitedPassportReport):
        return "visited"
    raise TypeError(
        f"unsupported report type: {type(report).__name__} "
        f"(expected ProvenanceReport or VisitedPassportReport)")


def _to_report_dict(report: Any) -> Dict:
    """Extract the canonical dict from either report type."""
    if not hasattr(report, "to_dict"):
        raise TypeError(
            f"report must have to_dict(): got {type(report).__name__}")
    return report.to_dict()


# =====================================================================
# SignedProvenanceReport
# =====================================================================

@dataclass(frozen=True)
class SignedProvenanceReport:
    """A signed audit. Attests: 'signer_id said this at timestamp'.

    This is a claim of authorship, not of truth. A third party who
    trusts the signer trusts the content; a third party who doesn't
    ignores it.

    Frozen: the signature covers the fields, so mutation would
    invalidate it. A modified signed report must be re-signed.
    """
    signer_id: str
    signer_name: str
    report_type: str
    report: Dict
    timestamp: str
    signature: str

    def __post_init__(self):
        if not isinstance(self.signer_id, str) or not self.signer_id:
            raise ValueError("signer_id must be a non-empty string")
        if not isinstance(self.signer_name, str) or not self.signer_name:
            raise ValueError("signer_name must be a non-empty string")
        if not isinstance(self.report_type, str) or not self.report_type:
            raise ValueError("report_type must be a non-empty string")
        if not isinstance(self.report, dict):
            raise ValueError("report must be a dict")
        if not isinstance(self.timestamp, str) or not self.timestamp:
            raise ValueError("timestamp must be a non-empty string")
        if not isinstance(self.signature, str) or not self.signature:
            raise ValueError("signature must be a non-empty string")

    def canonical_payload(self) -> bytes:
        """The exact bytes the auditor signed. Stable across runs
        (canonical_bytes sorts keys)."""
        return canonical_bytes({
            "kind": "provenance_report",
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "report_type": self.report_type,
            "report": self.report,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "kind": "signed_provenance_report",
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "report_type": self.report_type,
            "report": self.report,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "SignedProvenanceReport":
        return cls(
            signer_id=d["signer_id"],
            signer_name=d["signer_name"],
            report_type=d["report_type"],
            report=d["report"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# Sign
# =====================================================================

def sign_report(
    report: Union[ProvenanceReport, VisitedPassportReport],
    keypair: KeyPair,
    signer: Identity,
    timestamp: Optional[str] = None,
) -> SignedProvenanceReport:
    """Sign an audit report.

    `signer` is the auditor's identity (token + name). The
    signature covers the signer's token, the report content, the
    report type, and the timestamp. Tampering with any of them
    breaks verification.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_report requires `cryptography`. "
            "Install with: pip install cryptography")
    rtype = _report_type(report)
    report_dict = _to_report_dict(report)
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    payload = canonical_bytes({
        "kind": "provenance_report",
        "signer_id": signer.token,
        "signer_name": signer.name,
        "report_type": rtype,
        "report": report_dict,
        "timestamp": timestamp,
    })
    signature = keypair.sign(payload).hex()
    return SignedProvenanceReport(
        signer_id=signer.token,
        signer_name=signer.name,
        report_type=rtype,
        report=report_dict,
        timestamp=timestamp,
        signature=signature,
    )


# =====================================================================
# Verify
# =====================================================================

def verify_signed_report(
    signed: SignedProvenanceReport,
    public_key_hex: str,
) -> bool:
    """True iff the signature verifies against the given public key.

    Never raises. Malformed input, missing cryptography, unknown
    report_type, or invalid signature all return False.
    """
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(signed, SignedProvenanceReport):
            return False
        if signed.report_type not in SUPPORTED_REPORT_TYPES:
            return False
        payload = signed.canonical_payload()
    except Exception:
        return False
    return verify_signature(public_key_hex, payload, signed.signature)


def extract_report_content(
    signed: SignedProvenanceReport,
) -> Dict:
    """Return the report content after verification.

    The intended use: a verifier calls verify_signed_report first,
    then extract_report_content to inspect what was attested. The
    extraction itself does not re-verify — but the signature covers
    the content, so a tampered content cannot be extracted from a
    report that just verified.
    """
    return signed.report


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> SignedProvenanceReport:
    """A minimal demonstration: sign a stub report, verify it, save it.

    The report content is synthetic (three fabricated 'verified'
    entries). This is a demonstration of the signing mechanism, not
    of a real audit. A real audit uses C21's verify_cross_world_provenance
    or C23's verify_passport_visits. The signature is identical in
    either case — the mechanism doesn't care where the report came
    from.
    """
    import json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError(
            "demo requires `cryptography`. "
            "Install with: pip install cryptography")

    from multiverse_c15 import PassportEntry
    from multiverse_c21 import EntryProvenance

    kp = KeyPair.generate()
    auditor = create_identity_for_demo("Auditor")

    rep = ProvenanceReport(
        passport_token="demo:passport",
        passport_name="Demo Visitor",
        registry_url="http://demo/registry",
    )
    for eid in ("world:poetry", "world:chemistry", "world:a"):
        entry = PassportEntry(
            entity_id=eid,
            timestamp="2024-01-01T00:00:00+00:00",
            subject_token="demo:passport",
            signature="bb" * 64,
        )
        ep = EntryProvenance(entry=entry)
        ep.verdict = "verified"
        ep.reason = "registry → url → manifest → signature all verified"
        rep.entries.append(ep)

    signed = sign_report(rep, kp, auditor)
    ok = verify_signed_report(signed, kp.public_key_hex())

    print("=" * 70)
    print("Signed Provenance Report — demo")
    print("=" * 70)
    print(f"  signer:      {signed.signer_name} "
          f"({signed.signer_id[:16]}...)")
    print(f"  report_type: {signed.report_type}")
    print(f"  timestamp:   {signed.timestamp}")
    print(f"  entries:     {len(signed.report['entries'])}")
    print(f"  verified:    {ok}")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Much Madness is divinest Sense –'")
    print("    'To a discerning Eye –'")

    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "signed_provenance.json").write_text(
            json.dumps(signed.to_dict(), indent=2))
        print(f"\n  → {path}/signed_provenance.json")

    return signed


def create_identity_for_demo(name: str) -> Identity:
    """Lazy-import helper to avoid a top-level C1 dependency cycle."""
    from multiverse_c1 import create_identity
    return create_identity(name)
