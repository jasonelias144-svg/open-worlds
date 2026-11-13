"""
wcp_conformance.py — The WCP/0.1 conformance runner and CLI.

Two modes:
  --in-process module:factory   Test a Python WorldProtocol directly
  --url http://host:port/       Test any HTTP endpoint (any language)

The checks are identical in both modes. That is the point.

Exit codes:
  0  — entity conforms
  1  — entity does not conform
  2  — could not reach the entity
"""

import importlib
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from wcp_conformance_checks import (
    Check, Report,
    check_manifest_shape, check_manifest_version,
    check_manifest_entity_id_length, check_manifest_sub_registry,
    check_petition_response, check_act_response, check_log_shape,
)


# =====================================================================
# In-process runner
# =====================================================================

class InProcessEndpoint:
    """An endpoint that talks to a Python WorldProtocol directly."""

    def __init__(self, entity: Any):
        self.entity = entity

    def get_manifest(self) -> Dict:
        m = self.entity.manifest()
        return _manifest_dict(m)

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
        return _response_dict(r)

    def post_act(self, payload: Dict) -> Dict:
        from multiverse_c3 import Act
        a = Act(
            actor_token=payload["actor_token"],
            type=payload["type"],
            payload=payload["payload"],
        )
        r = self.entity.act(a)
        return _response_dict(r)

    def get_log(self, since: Optional[str] = None) -> Dict:
        entries = self.entity.log_since(since)
        return {"entries": [_log_entry_dict(e) for e in entries]}


def _manifest_dict(m: Any) -> Dict:
    return {
        "entity_id": m.entity_id,
        "name": m.name,
        "protocol_version": m.protocol_version,
        "law_url": m.law_url,
        "act_endpoint": m.act_endpoint,
        "log_endpoint": m.log_endpoint,
        "sub_registry_endpoint": m.sub_registry_endpoint,
    }


def _response_dict(r: Any) -> Dict:
    from multiverse_c3 import Admission, Refusal, Route, Ack
    if isinstance(r, Admission):
        return {"kind": "admission",
                "entity_id": r.entity_id, "timestamp": r.timestamp}
    if isinstance(r, Refusal):
        return {"kind": "refusal", "reason": r.reason}
    if isinstance(r, Route):
        return {"kind": "route",
                "target_manifest": _manifest_dict(r.target_manifest),
                "reason": r.reason}
    if isinstance(r, Ack):
        return {"kind": "ack",
                "entity_id": r.entity_id, "timestamp": r.timestamp}
    raise TypeError(f"Unknown response type: {type(r).__name__}")


def _log_entry_dict(e: Any) -> Dict:
    return {
        "timestamp": e.timestamp,
        "kind": e.kind,
        "actor_token": e.actor_token,
        "data": e.data,
    }


# =====================================================================
# HTTP runner
# =====================================================================

class HTTPEndpoint:
    """An endpoint that talks to any WCP/0.1 HTTP server, in any language."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str) -> Dict:
        url = f"{self.base_url}{path}"
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read().decode())

    def _post(self, path: str, body: Dict) -> Dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())

    def get_manifest(self) -> Dict:
        return self._get("/manifest")

    def post_petition(self, payload: Dict) -> Dict:
        return self._post("/petition", payload)

    def post_act(self, payload: Dict) -> Dict:
        return self._post("/act", payload)

    def get_log(self, since: Optional[str] = None) -> Dict:
        path = "/log"
        if since is not None:
            from urllib.parse import quote
            path += f"?since={quote(since)}"
        return self._get(path)


# =====================================================================
# Runner: run all checks against an endpoint
# =====================================================================

class ConformanceRunner:
    """Runs the full WCP/0.1 conformance test against an endpoint."""

    def __init__(self, endpoint: Any, endpoint_label: str):
        self.endpoint = endpoint
        self.label = endpoint_label
        self.report: Optional[Report] = None

    def run(self) -> Report:
        # First, manifest — everything else depends on it
        manifest = self.endpoint.get_manifest()
        eid = manifest.get("entity_id", "unknown")
        self.report = Report(entity_id=eid, endpoint=self.label)

        # Manifest checks (§4.1, §7.1)
        self.report.checks.append(check_manifest_shape(manifest))
        self.report.checks.append(check_manifest_version(manifest))
        self.report.checks.append(check_manifest_entity_id_length(manifest))
        self.report.checks.append(check_manifest_sub_registry(manifest))

        # Petition check (§4.2, §7.2)
        try:
            petition = self.endpoint.post_petition({
                "petitioner_token": "conformance:petitioner",
                "petitioner_name": "Conformance Petitioner",
                "passport_admissions": [],
                "message": "conformance test",
            })
            self.report.checks.append(check_petition_response(petition))
        except Exception as e:
            self.report.checks.append(Check(
                "petition_response_shape", False, "§7.2",
                f"petition raised: {e}", exception=str(e)))

        # Act check (§4.3, §7.3) — using an unadmitted actor; the
        # entity must still return a Refusal, not an error.
        try:
            act = self.endpoint.post_act({
                "actor_token": "conformance:actor",
                "type": "conformance.test",
                "payload": {},
            })
            self.report.checks.append(check_act_response(act))
        except Exception as e:
            self.report.checks.append(Check(
                "act_response_shape", False, "§7.3",
                f"act raised: {e}", exception=str(e)))

        # Log check (§4.4, §7.4)
        try:
            log = self.endpoint.get_log()
            self.report.checks.append(check_log_shape(log))
        except Exception as e:
            self.report.checks.append(Check(
                "log_shape", False, "§7.4",
                f"log raised: {e}", exception=str(e)))

        return self.report


# =====================================================================
# CLI
# =====================================================================

def _load_in_process(spec: str) -> Any:
    """Load a Python entity from 'module:factory'."""
    if ":" not in spec:
        raise ValueError(
            f"--in-process requires 'module:factory', got {spec!r}")
    mod_name, factory_name = spec.split(":", 1)
    mod = importlib.import_module(mod_name)
    factory = getattr(mod, factory_name)
    if isinstance(factory, type):
        return factory()  # class: instantiate with no args
    return factory()  # function: call with no args


def main(argv: List[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="wcp_conformance",
        description="WCP/0.1 conformance test.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--in-process", metavar="MODULE:FACTORY",
        help="Test a Python WorldProtocol directly.",
    )
    group.add_argument(
        "--url", metavar="BASE_URL",
        help="Test an HTTP endpoint.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Only print the final result.",
    )
    args = parser.parse_args(argv)

    try:
        if args.in_process:
            entity = _load_in_process(args.in_process)
            endpoint = InProcessEndpoint(entity)
            label = f"in-process:{args.in_process}"
        else:
            endpoint = HTTPEndpoint(args.url)
            label = args.url
    except Exception as e:
        print(f"ERROR: could not create endpoint: {e}", file=sys.stderr)
        return 2

    try:
        report = ConformanceRunner(endpoint, label).run()
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
