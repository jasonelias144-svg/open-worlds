# multiverse_c3_conformance.py — The WCP/0.1 conformance test.

"""
Any developer implementing WCP/0.1 should run this against their
entity. If all tests pass, the entity is a conforming member of
the federation. If any test fails, the entity is not.

The conformance test does NOT check:
  - whether the entity admits anyone
  - whether the entity's Law is interesting
  - whether the entity is fast, or reliable, or good

It checks ONLY that the entity correctly speaks the protocol.
"""

from typing import Callable, List
from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission, Refusal, Route, Ack,
    WorldProtocol,
)


def run_conformance(entity: WorldProtocol) -> dict:
    """Run the conformance test against an entity.

    Returns {"passed": bool, "failures": List[str]}.
    """
    failures: List[str] = []

    # --- manifest ---
    try:
        m = entity.manifest()
        if not isinstance(m, Manifest):
            failures.append("manifest() did not return a Manifest")
        else:
            if m.protocol_version != "WCP/0.1":
                failures.append(
                    f"protocol_version is {m.protocol_version!r}, "
                    f"expected 'WCP/0.1'")
            if not m.entity_id:
                failures.append("manifest.entity_id is empty")
            if not m.name:
                failures.append("manifest.name is empty")
            if not m.law_url:
                failures.append("manifest.law_url is empty")
            if not m.act_endpoint:
                failures.append("manifest.act_endpoint is empty")
            if not m.log_endpoint:
                failures.append("manifest.log_endpoint is empty")
    except Exception as e:
        failures.append(f"manifest() raised {type(e).__name__}: {e}")
        return {"passed": False, "failures": failures}

    # --- petition (any response is valid, but must be one of the three) ---
    test_petition = Petition(
        petitioner_token="test:petitioner",
        petitioner_name="Test Petitioner",
        passport_admissions=(),
        message="conformance test",
    )
    try:
        response = entity.petition(test_petition)
        if not isinstance(response, (Admission, Refusal, Route)):
            failures.append(
                f"petition() returned {type(response).__name__}, "
                f"expected Admission, Refusal, or Route")
        if isinstance(response, Refusal):
            if not response.reason:
                failures.append("Refusal.reason is empty")
        if isinstance(response, Admission):
            if not response.entity_id:
                failures.append("Admission.entity_id is empty")
            if not response.timestamp:
                failures.append("Admission.timestamp is empty")
        if isinstance(response, Route):
            if not isinstance(response.target_manifest, Manifest):
                failures.append(
                    "Route.target_manifest is not a Manifest")
    except Exception as e:
        failures.append(f"petition() raised {type(e).__name__}: {e}")

    # --- act (any response is valid, but must be one of the two) ---
    test_act = Act(
        actor_token="test:actor",
        type="conformance_test",
        payload={},
    )
    try:
        response = entity.act(test_act)
        if not isinstance(response, (Ack, Refusal)):
            failures.append(
                f"act() returned {type(response).__name__}, "
                f"expected Ack or Refusal")
        if isinstance(response, Refusal):
            if not response.reason:
                failures.append("Refusal.reason is empty")
        if isinstance(response, Ack):
            if not response.entity_id:
                failures.append("Ack.entity_id is empty")
            if not response.timestamp:
                failures.append("Ack.timestamp is empty")
    except Exception as e:
        failures.append(f"act() raised {type(e).__name__}: {e}")

    # --- log ---
    try:
        log = entity.log_since(None)
        if not isinstance(log, list):
            failures.append("log_since() did not return a list")
        else:
            for entry in log:
                if not isinstance(entry, LogEntry):
                    failures.append(
                        f"log_since() returned {type(entry).__name__}, "
                        f"expected LogEntry")
                    break
                if not entry.timestamp:
                    failures.append("LogEntry.timestamp is empty")
                if not entry.kind:
                    failures.append("LogEntry.kind is empty")
    except Exception as e:
        failures.append(f"log_since() raised {type(e).__name__}: {e}")

    # --- sub-registry consistency ---
    try:
        if m.has_sub_registry():
            # If has_sub_registry, there must be a way to enumerate
            # sub-entities. WCP doesn't specify *how* — but a
            # conforming multiverse must be able to answer "who is
            # in my sub-registry?" through *some* mechanism.
            # For now, this is an honest limitation of WCP/0.1:
            # the sub-registry enumeration is *not* part of the
            # protocol. A multiverse's sub-registry is *public*
            # (declared at manifest time) but *not queryable*.
            # Query is a WCP/0.2 feature.
            pass
    except Exception as e:
        failures.append(
            f"sub-registry check raised {type(e).__name__}: {e}")

    return {"passed": len(failures) == 0, "failures": failures}
