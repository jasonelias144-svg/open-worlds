"""
wcp_conformance_v02.py — WCP/0.2 conformance test.

Extends the WCP/0.1 conformance test with signature checks. The
runner auto-detects the version from the manifest:

  - WCP/0.1: run the existing 8 checks. Report says "unsigned".
  - WCP/0.2: run the 8 checks, plus:
      * manifest_public_key (required)
      * admission_signature (verified)
      * ack_signature (verified if entity returns an Ack)

The canonical test is still one artifact. WCP/0.2 is WCP/0.1 plus
signatures; the test reflects that.

CLI:
  python -m wcp_conformance_v02 --url <endpoint>
  python -m wcp_conformance_v02 --url <endpoint> --expect-version 0.2
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from wcp_conformance_checks import (
    Check, Report,
    check_manifest_shape, check_manifest_entity_id_length,
    check_manifest_sub_registry, check_petition_response,
    check_act_response, check_log_shape,
)
from wcp_conformance import (
    InProcessEndpoint, HTTPEndpoint,
    _manifest_dict, _response_dict, _log_entry_dict,
)
from multiverse_c13 import (
    HAS_CRYPTO, canonical_bytes, verify_signature,
    SignedAdmission, SignedAck, SignedWorld,
)


# =====================================================================
# V02 checks
# =====================================================================

def check_manifest_version_any(manifest: Any) -> Check:
    """§8: protocol_version is 'WCP/0.1' or 'WCP/0.2'."""
    d = manifest if isinstance(manifest, dict) else _manifest_dict(
        _coerce_manifest(manifest))
    v = d.get("protocol_version", "")
    if v in ("WCP/0.1", "WCP/0.2"):
        return Check("manifest_version_any", True, "§8",
                     f"version={v}")
    return Check("manifest_version_any", False, "§8",
                 f"got {v!r}, expected WCP/0.1 or WCP/0.2")


def check_manifest_public_key(manifest: Any) -> Check:
    """§8: WCP/0.2 entities MUST publish a 32-byte public_key (64 hex)."""
    d = manifest if isinstance(manifest, dict) else _manifest_dict(
        _coerce_manifest(manifest))
    v = d.get("protocol_version", "")
    if v != "WCP/0.2":
        return Check("manifest_public_key", True, "§8",
                     "(not required for WCP/0.1)")
    pk = d.get("public_key")
    if not isinstance(pk, str):
        return Check("manifest_public_key", False, "§8",
                     "public_key missing or not a string")
    if len(pk) != 64:
        return Check("manifest_public_key", False, "§8",
                     f"public_key must be 64 hex chars, got {len(pk)}")
    try:
        bytes.fromhex(pk)
    except ValueError:
        return Check("manifest_public_key", False, "§8",
                     "public_key is not valid hex")
    return Check("manifest_public_key", True, "§8",
                 f"public_key={pk[:16]}...")


def check_admission_signature(response: Any, public_key_hex: str,
                               expected_subject: str) -> Check:
    """§8: a WCP/0.2 Admission MUST carry a valid signature.

    The canonical payload is defined in multiverse_c13.canonical_bytes.
    If the entity returns a Refusal instead, this check is not
    applicable (refusals are unsigned).
    """
    if not HAS_CRYPTO:
        return Check("admission_signature", True, "§8",
                     "SKIPPED — cryptography not installed")
    try:
        d = response if isinstance(response, dict) else _response_dict(response)
    except Exception as e:
        return Check("admission_signature", False, "§8",
                     f"could not read response: {e}")
    if d.get("kind") != "admission":
        return Check("admission_signature", True, "§8",
                     f"(not an admission: kind={d.get('kind')!r}; "
                     f"no signature expected)")
    required = ["entity_id", "timestamp", "subject_token", "signature"]
    missing = [f for f in required if not d.get(f)]
    if missing:
        return Check("admission_signature", False, "§8",
                     f"missing fields: {missing}")
    if d["subject_token"] != expected_subject:
        return Check("admission_signature", False, "§8",
                     f"subject_token {d['subject_token']!r} != "
                     f"expected {expected_subject!r}")
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": d["entity_id"],
        "timestamp": d["timestamp"],
        "subject_token": d["subject_token"],
    })
    ok = verify_signature(public_key_hex, canonical, d["signature"])
    return Check("admission_signature", ok, "§8",
                 "signature verified" if ok else "signature INVALID")


def check_ack_signature(response: Any, public_key_hex: str,
                         expected_subject: str) -> Check:
    """§8: a WCP/0.2 Ack MUST carry a valid signature.

    If the entity returns a Refusal (which any Law-bound world will
    do to a generic conformance act), this check is not applicable.
    """
    if not HAS_CRYPTO:
        return Check("ack_signature", True, "§8",
                     "SKIPPED — cryptography not installed")
    try:
        d = response if isinstance(response, dict) else _response_dict(response)
    except Exception as e:
        return Check("ack_signature", False, "§8",
                     f"could not read response: {e}")
    if d.get("kind") != "ack":
        return Check("ack_signature", True, "§8",
                     f"(not an ack: kind={d.get('kind')!r}; "
                     f"no signature expected)")
    required = ["entity_id", "timestamp", "subject_token", "signature"]
    missing = [f for f in required if not d.get(f)]
    if missing:
        return Check("ack_signature", False, "§8",
                     f"missing fields: {missing}")
    if d["subject_token"] != expected_subject:
        return Check("ack_signature", False, "§8",
                     f"subject_token {d['subject_token']!r} != "
                     f"expected {expected_subject!r}")
    canonical = canonical_bytes({
        "kind": "ack",
        "entity_id": d["entity_id"],
        "timestamp": d["timestamp"],
        "subject_token": d["subject_token"],
    })
    ok = verify_signature(public_key_hex, canonical, d["signature"])
    return Check("ack_signature", ok, "§8",
                 "signature verified" if ok else "signature INVALID")


def _coerce_manifest(manifest: Any) -> Any:
    """For non-dict manifests, recover the object we can call
    manifest() or manifest_dict() on."""
    if hasattr(manifest, "manifest_dict"):
        return manifest
    if hasattr(manifest, "manifest"):
        return manifest.manifest()
    return manifest


# =====================================================================
# Extended report
# =====================================================================

@dataclass
class ReportV02(Report):
    version: str = "unknown"
    signed: bool = False
    public_key_hex: Optional[str] = None

    def format(self) -> str:
        mode = (
            f"{self.version} (signed)"
            if self.signed
            else f"{self.version} (unsigned — signatures not required)"
        )
        lines = [
            f"Entity:   {self.entity_id}",
            f"Endpoint: {self.endpoint}",
            f"Version:  {mode}",
        ]
        if self.public_key_hex:
            lines.append(f"Public key: {self.public_key_hex[:16]}...")
        lines.append("")
        for c in self.checks:
            lines.append(c.format_line())
        lines.append("")
        if self.passed:
            lines.append(
                f"Result: PASSES ({self.passed_count}/{self.total_count})"
                f" — {mode}")
        else:
            lines.append(
                f"Result: FAILS ({self.passed_count}/{self.total_count})")
            lines.append("")
            lines.append("Failures:")
            for c in self.failures():
                lines.append(f"  - {c.name}")
                lines.append(f"    {c.detail}")
                lines.append(f"    spec: {c.source}")
        return "\n".join(lines)


# =====================================================================
# In-process endpoint that handles both WCP/0.1 and WCP/0.2
# =====================================================================

class InProcessEndpointV02(InProcessEndpoint):
    """Reads either .manifest() or .manifest_dict(); handles signed
    and unsigned responses."""

    def get_manifest(self) -> Dict:
        if hasattr(self.entity, "manifest_dict"):
            return self.entity.manifest_dict()
        return _manifest_dict(self.entity.manifest())

    def post_petition(self, payload: Dict) -> Dict:
        from multiverse_c3 import Petition
        p = Petition(
            petitioner_token=payload["petitioner_token"],
            petitioner_name=payload["petitioner_name"],
            passport_admissions=tuple(
                tuple(x) for x in payload.get("passport_admissions", [])),
            message=payload["message"],
            target=payload.get("target"),
        )
        r = self.entity.petition(p)
        return _response_dict_v02(r)

    def post_act(self, payload: Dict) -> Dict:
        from multiverse_c3 import Act
        a = Act(
            actor_token=payload["actor_token"],
            type=payload["type"],
            payload=payload["payload"],
        )
        r = self.entity.act(a)
        return _response_dict_v02(r)


def _response_dict_v02(r: Any) -> Dict:
    """Handle both WCP/0.1 response types and WCP/0.2 signed ones."""
    if isinstance(r, SignedAdmission):
        return {"kind": "admission",
                "entity_id": r.entity_id,
                "timestamp": r.timestamp,
                "subject_token": r.subject_token,
                "signature": r.signature}
    if isinstance(r, SignedAck):
        return {"kind": "ack",
                "entity_id": r.entity_id,
                "timestamp": r.timestamp,
                "subject_token": r.subject_token,
                "signature": r.signature}
    return _response_dict(r)


# =====================================================================
# The V02 runner
# =====================================================================

class ConformanceRunnerV02:
    """Runs WCP/0.1 checks, then WCP/0.2 checks if version is 0.2.

    Auto-detects from the manifest. `expect_version` enforces a
    minimum: passing "0.2" rejects a WCP/0.1 entity.
    """

    def __init__(self, endpoint: Any, endpoint_label: str,
                 expect_version: Optional[str] = None):
        self.endpoint = endpoint
        self.label = endpoint_label
        self.expect_version = expect_version
        self.report: Optional[ReportV02] = None

    def run(self) -> ReportV02:
        manifest = self.endpoint.get_manifest()
        eid = manifest.get("entity_id", "unknown")
        version = manifest.get("protocol_version", "unknown")
        is_v02 = version == "WCP/0.2"
        pubkey = manifest.get("public_key") if is_v02 else None

        self.report = ReportV02(
            entity_id=eid, endpoint=self.label,
            version=version, signed=is_v02,
            public_key_hex=pubkey,
        )

        # -- V01 checks (all versions) --

        self.report.checks.append(check_manifest_shape(manifest))
        self.report.checks.append(check_manifest_version_any(manifest))
        self.report.checks.append(check_manifest_entity_id_length(manifest))
        self.report.checks.append(check_manifest_sub_registry(manifest))

        # -- Enforce --expect-version if requested --

        if self.expect_version == "0.2" and not is_v02:
            self.report.checks.append(Check(
                "expect_version", False, "§8",
                f"expected WCP/0.2, got {version!r}"))

        # -- V02 manifest check --

        if is_v02:
            self.report.checks.append(check_manifest_public_key(manifest))

        # -- Petition --

        test_token = "conformance:petitioner"
        try:
            petition = self.endpoint.post_petition({
                "petitioner_token": test_token,
                "petitioner_name": "Conformance Petitioner",
                "passport_admissions": [],
                "message": "conformance test",
            })
            self.report.checks.append(check_petition_response(petition))
            if is_v02:
                self.report.checks.append(check_admission_signature(
                    petition, pubkey or "", test_token))
        except Exception as e:
            self.report.checks.append(Check(
                "petition_response_shape", False, "§7.2",
                f"petition raised: {e}"))

        # -- Act (as the same token, so a permissive world may Ack) --

        try:
            act = self.endpoint.post_act({
                "actor_token": test_token,
                "type": "conformance.test",
                "payload": {},
            })
            self.report.checks.append(check_act_response(act))
            if is_v02:
                self.report.checks.append(check_ack_signature(
                    act, pubkey or "", test_token))
        except Exception as e:
            self.report.checks.append(Check(
                "act_response_shape", False, "§7.3",
                f"act raised: {e}"))

        # -- Log --

        try:
            log = self.endpoint.get_log()
            self.report.checks.append(check_log_shape(log))
        except Exception as e:
            self.report.checks.append(Check(
                "log_shape", False, "§7.4",
                f"log raised: {e}"))

        return self.report


# =====================================================================
# CLI
# =====================================================================

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="wcp_conformance_v02",
        description="WCP/0.2 (or 0.1) conformance test.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--in-process", metavar="MODULE:FACTORY",
        help="Test a Python WorldProtocol or SignedWorld directly.")
    group.add_argument(
        "--url", metavar="BASE_URL",
        help="Test an HTTP endpoint.")
    parser.add_argument(
        "--expect-version", choices=["0.1", "0.2"], default=None,
        help="Enforce a minimum protocol version.")
    parser.add_argument(
        "--quiet", action="store_true",
        help="Only print PASS or FAIL.")
    args = parser.parse_args(argv)

    try:
        if args.in_process:
            from wcp_conformance import _load_in_process
            entity = _load_in_process(args.in_process)
            endpoint = InProcessEndpointV02(entity)
            label = f"in-process:{args.in_process}"
        else:
            endpoint = HTTPEndpoint(args.url)
            label = args.url
    except Exception as e:
        print(f"ERROR: could not create endpoint: {e}", file=sys.stderr)
        return 2

    try:
        report = ConformanceRunnerV02(
            endpoint, label, args.expect_version).run()
    except Exception as e:
        print(f"ERROR: could not reach endpoint: {e}", file=sys.stderr)
        return 2

    if args.quiet:
        print("PASS" if report.passed else "FAIL")
    else:
        print(report.format())
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
