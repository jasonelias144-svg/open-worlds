"""
wcp_conformance_checks.py — Conformance checks for WCP/0.1.

Every check is derived from a sentence in the WCP/0.1 spec. Each
check's docstring names its source. If a check and the spec
disagree, the spec is correct and the check must be fixed.

These checks are *language-neutral*: they assert on the JSON shapes
of the four WCP messages. Any implementation in any language can be
tested with these checks.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# =====================================================================
# Check primitives
# =====================================================================

@dataclass
class Check:
    name: str
    passed: bool
    source: str             # which spec section justifies this check
    detail: str = ""
    exception: Optional[str] = None

    def format_line(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        line = f"  {status}  {self.name}"
        if self.detail:
            line += f"  —  {self.detail}"
        return line


@dataclass
class Report:
    entity_id: str
    endpoint: str
    checks: List[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)

    def failures(self) -> List[Check]:
        return [c for c in self.checks if not c.passed]

    def format(self) -> str:
        lines = [
            f"Entity:   {self.entity_id}",
            f"Endpoint: {self.endpoint}",
            "",
        ]
        for c in self.checks:
            lines.append(c.format_line())
        lines.append("")
        if self.passed:
            lines.append(
                f"Result: PASSES ({self.passed_count}/{self.total_count} checks)")
        else:
            lines.append(
                f"Result: FAILS ({self.passed_count}/{self.total_count} checks)")
            lines.append("")
            lines.append("Failures:")
            for c in self.failures():
                lines.append(f"  - {c.name}")
                lines.append(f"    {c.detail}")
                lines.append(f"    spec: {c.source}")
        return "\n".join(lines)


# =====================================================================
# Individual checks (§7 of the spec)
# =====================================================================

def check_manifest_shape(manifest: Any) -> Check:
    """§4.1: manifest is a JSON object with required string fields."""
    required = [
        "entity_id", "name", "protocol_version",
        "law_url", "act_endpoint", "log_endpoint",
    ]
    try:
        d = _as_dict(manifest)
    except Exception as e:
        return Check("manifest_shape", False, "§4.1",
                     f"could not read manifest as dict: {e}",
                     exception=str(e))

    missing = [f for f in required if f not in d]
    if missing:
        return Check("manifest_shape", False, "§4.1",
                     f"missing fields: {missing}")
    wrong_type = [f for f in required if not isinstance(d[f], str) or not d[f]]
    if wrong_type:
        return Check("manifest_shape", False, "§4.1",
                     f"empty or non-string fields: {wrong_type}")
    return Check("manifest_shape", True, "§4.1")


def check_manifest_version(manifest: Any) -> Check:
    """§7.1: protocol_version MUST be 'WCP/0.1'."""
    d = _as_dict(manifest)
    v = d.get("protocol_version")
    if v == "WCP/0.1":
        return Check("manifest_version", True, "§7.1")
    return Check("manifest_version", False, "§7.1",
                 f"got {v!r}, expected 'WCP/0.1'")


def check_manifest_entity_id_length(manifest: Any) -> Check:
    """§4.1: entity_id must be at least 8 characters."""
    d = _as_dict(manifest)
    eid = d.get("entity_id", "")
    if isinstance(eid, str) and len(eid) >= 8:
        return Check("manifest_entity_id_length", True, "§4.1")
    return Check("manifest_entity_id_length", False, "§4.1",
                 f"entity_id {eid!r} is shorter than 8 characters")


def check_manifest_sub_registry(manifest: Any) -> Check:
    """§4.1: sub_registry_endpoint is string or null, always present."""
    d = _as_dict(manifest)
    if "sub_registry_endpoint" not in d:
        return Check("manifest_sub_registry", False, "§4.1",
                     "sub_registry_endpoint field is missing")
    sr = d["sub_registry_endpoint"]
    if sr is None:
        return Check("manifest_sub_registry", True, "§4.1",
                     "(world — no sub-registry)")
    if isinstance(sr, str) and sr:
        return Check("manifest_sub_registry", True, "§4.1",
                     f"(multiverse — sub_registry at {sr})")
    return Check("manifest_sub_registry", False, "§4.1",
                 f"sub_registry_endpoint is {sr!r}; must be null or non-empty string")


def check_petition_response(response: Any) -> Check:
    """§7.2: petition returns Admission, Refusal, or Route."""
    try:
        d = _as_dict(response)
    except Exception as e:
        return Check("petition_response_shape", False, "§7.2",
                     f"response is not JSON-object-like: {e}")
    kind = d.get("kind")
    if kind not in ("admission", "refusal", "route"):
        return Check("petition_response_shape", False, "§7.2",
                     f"kind is {kind!r}, expected one of "
                     f"'admission', 'refusal', 'route'")
    if kind == "admission":
        for f in ("entity_id", "timestamp"):
            if not d.get(f):
                return Check("petition_response_shape", False, "§7.2",
                             f"admission missing {f}")
    elif kind == "refusal":
        if not d.get("reason"):
            return Check("petition_response_shape", False, "§7.2",
                         "refusal missing reason")
    elif kind == "route":
        if not d.get("target_manifest"):
            return Check("petition_response_shape", False, "§7.2",
                         "route missing target_manifest")
    return Check("petition_response_shape", True, "§7.2", f"kind={kind}")


def check_act_response(response: Any) -> Check:
    """§7.3: act returns Ack or Refusal."""
    try:
        d = _as_dict(response)
    except Exception as e:
        return Check("act_response_shape", False, "§7.3",
                     f"response is not JSON-object-like: {e}")
    kind = d.get("kind")
    if kind not in ("ack", "refusal"):
        return Check("act_response_shape", False, "§7.3",
                     f"kind is {kind!r}, expected 'ack' or 'refusal'")
    if kind == "ack":
        for f in ("entity_id", "timestamp"):
            if not d.get(f):
                return Check("act_response_shape", False, "§7.3",
                             f"ack missing {f}")
    elif kind == "refusal":
        if not d.get("reason"):
            return Check("act_response_shape", False, "§7.3",
                         "refusal missing reason")
    return Check("act_response_shape", True, "§7.3", f"kind={kind}")


def check_log_shape(log_response: Any) -> Check:
    """§7.4: log returns {"entries": [...]} with well-formed entries."""
    try:
        d = _as_dict(log_response)
    except Exception as e:
        return Check("log_shape", False, "§7.4",
                     f"log response is not JSON-object-like: {e}")
    if "entries" not in d:
        return Check("log_shape", False, "§7.4",
                     "response missing 'entries' field")
    entries = d["entries"]
    if not isinstance(entries, list):
        return Check("log_shape", False, "§7.4",
                     f"'entries' is {type(entries).__name__}, expected list")
    for i, e in enumerate(entries):
        ed = _as_dict(e)
        for f in ("timestamp", "kind", "data"):
            if f not in ed:
                return Check("log_shape", False, "§7.4",
                             f"entry {i} missing field {f!r}")
        if not isinstance(ed["kind"], str) or not ed["kind"]:
            return Check("log_shape", False, "§7.4",
                         f"entry {i} kind is empty or non-string")
    return Check("log_shape", True, "§7.4",
                 f"{len(entries)} entries, all well-formed")


def check_error_vs_refusal(distinguish_test: Any) -> Check:
    """§6: protocol errors use HTTP 4xx/5xx; refusals are 200."""
    # This check requires a probe that distinguishes the two — it
    # is run by the runner, which knows how to probe both modes.
    return distinguish_test


# =====================================================================
# Helper
# =====================================================================

def _as_dict(obj: Any) -> Dict:
    """Coerce an object into a dict for shape-checking."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return vars(obj)
    # Fall back to dataclass-like asdict
    import dataclasses
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    raise TypeError(f"Cannot convert {type(obj).__name__} to dict")
