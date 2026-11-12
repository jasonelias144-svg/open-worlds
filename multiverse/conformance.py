"""The conformance test: does an entity speak WCP/0.1?

From the DeepSeek sketch's component 3. Anyone can run it against their
own entity. It checks only that the entity speaks the protocol: not whom
it admits, not whether its law is interesting, not whether it is fast.

Changed from the sketch:
  - The test petitions with a fresh identity each run, and leaves
    afterwards. The sketch's test entered every world it checked and
    stayed, so a world with room for two lost a place to it.
  - It checks leaving: a leave is never refused, says whether the
    individual was present, and a second leave answers already_left.
"""
from __future__ import annotations

import uuid
from typing import List

from .protocol import (PROTOCOL_VERSION, Ack, Act, Admission, Departure,
                       LogEntry, Manifest, Petition, Refusal, Route,
                       WorldProtocol)


def _test_token(role: str) -> str:
    return f"conformance-{role}-{uuid.uuid4().hex}"


def run_conformance(entity: WorldProtocol) -> dict:
    """Returns {"passed": bool, "failures": [str, ...]}."""
    failures: List[str] = []

    # -- manifest --
    try:
        m = entity.manifest()
    except Exception as e:
        failures.append(f"manifest() raised {type(e).__name__}: {e}")
        return {"passed": False, "failures": failures}
    if not isinstance(m, Manifest):
        failures.append("manifest() did not return a Manifest")
        return {"passed": False, "failures": failures}
    if m.protocol_version != PROTOCOL_VERSION:
        failures.append(f"protocol_version is {m.protocol_version!r}, "
                        f"expected {PROTOCOL_VERSION!r}")

    # -- petition: any of the three answers, well formed --
    petitioner = _test_token("petitioner")
    admitted = False
    try:
        response = entity.petition(Petition(
            petitioner_token=petitioner,
            petitioner_name="Conformance Test",
            passport_admissions=(),
            message="conformance test"))
        if isinstance(response, Admission):
            admitted = True
            if not response.entity_id:
                failures.append("Admission.entity_id is empty")
            if not response.timestamp:
                failures.append("Admission.timestamp is empty")
        elif isinstance(response, Refusal):
            if not response.reason:
                failures.append("Refusal.reason is empty")
        elif isinstance(response, Route):
            if not isinstance(response.target_manifest, Manifest):
                failures.append("Route.target_manifest is not a Manifest")
        else:
            failures.append(f"petition() returned {type(response).__name__}"
                            ", expected Admission, Refusal, or Route")
    except Exception as e:
        failures.append(f"petition() raised {type(e).__name__}: {e}")

    # -- act: Ack or Refusal, well formed --
    try:
        response = entity.act(Act(actor_token=_test_token("actor"),
                                  type="conformance_test", payload={}))
        if isinstance(response, Ack):
            if not response.entity_id:
                failures.append("Ack.entity_id is empty")
            if not response.timestamp:
                failures.append("Ack.timestamp is empty")
        elif isinstance(response, Refusal):
            if not response.reason:
                failures.append("Refusal.reason is empty")
        else:
            failures.append(f"act() returned {type(response).__name__}, "
                            "expected Ack or Refusal")
    except Exception as e:
        failures.append(f"act() raised {type(e).__name__}: {e}")

    # -- leave: always a Departure; the test leaves what it entered --
    for attempt, expect_already in (("first", not admitted),
                                    ("second", True)):
        try:
            response = entity.leave(petitioner)
        except Exception as e:
            failures.append(f"{attempt} leave() raised "
                            f"{type(e).__name__}: {e}")
            break
        if not isinstance(response, Departure):
            failures.append(f"{attempt} leave() returned "
                            f"{type(response).__name__}, expected Departure")
            break
        if not response.entity_id or not response.timestamp:
            failures.append(f"{attempt} Departure is missing its "
                            "entity_id or timestamp")
        if response.already_left != expect_already:
            failures.append(
                f"{attempt} leave() said already_left="
                f"{response.already_left}, expected {expect_already}")

    # -- log: a list of well-formed entries --
    try:
        log = entity.log_since(None)
        if not isinstance(log, list):
            failures.append("log_since() did not return a list")
        else:
            for entry in log:
                if not isinstance(entry, LogEntry):
                    failures.append(f"log_since() returned "
                                    f"{type(entry).__name__}, "
                                    "expected LogEntry")
                    break
                if not entry.timestamp or not entry.kind:
                    failures.append("a LogEntry has no timestamp or kind")
                    break
    except Exception as e:
        failures.append(f"log_since() raised {type(e).__name__}: {e}")

    return {"passed": not failures, "failures": failures}
