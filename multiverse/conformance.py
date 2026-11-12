"""The conformance test: does an entity speak WCP/0.1?

From the DeepSeek sketch's component 3. Anyone can run it against their
own entity. It checks only that the entity speaks the protocol: not whom
it admits, not whether its law is interesting, not whether it is fast.

What it checks:
  - the manifest is a plain Manifest, with plain-text fields, of this
    protocol version;
  - a petition gets an Admission, a Refusal with a reason, or a Route;
  - an act gets an Ack or a Refusal with a reason;
  - leaving: a leave is never refused and never raises; it says whether
    the individual was present; a second leave answers already_left;
    and a departure of someone present is in the public log;
  - the log is a list of entries, each with a timestamp and a kind.

What it can't check: like any test from outside, it sees only answers
and the log. A world that answered correctly but secretly kept someone
would pass. The public log is where anyone can catch that.

Changed from the sketch:
  - The test petitions with a fresh identity each run, and leaves
    afterwards. The sketch's test entered every world it checked and
    stayed, so a world with room for two lost a place to it. The visit
    is still recorded in the world's log: an admission, a refused act and
    a departure. A public log should show it.
  - The leaving checks are new.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from .protocol import (PROTOCOL_VERSION, Ack, Act, Admission, Departure,
                       LogEntry, Manifest, Petition, Refusal, Route,
                       WorldProtocol)


def _describe(e: BaseException) -> str:
    """An exception as text, even if its own text can't be made."""
    try:
        name = type(e).__name__
    except Exception:
        name = "an exception"
    try:
        return f"{name}: {e}"
    except Exception:
        return f"{name} (whose message could not be read)"


def _test_token(role: str) -> str:
    return f"conformance-{role}-{uuid.uuid4().hex}"


def run_conformance(entity: WorldProtocol) -> dict:
    """Returns {"passed": bool, "failures": [str, ...]}."""
    return check(entity)[0]


def check(entity: WorldProtocol) -> Tuple[dict, Optional[Manifest]]:
    """The report, and the manifest the test checked (None if there was
    no valid one). Use this manifest, not a fresh call to manifest(),
    for whatever the result decides."""
    failures: List[str] = []

    def report():
        return {"passed": not failures, "failures": failures}

    # -- manifest --
    try:
        m = entity.manifest()
    except Exception as e:
        failures.append(f"manifest() raised {_describe(e)}")
        return report(), None
    if type(m) is not Manifest:
        failures.append("manifest() did not return a Manifest")
        return report(), None
    # A Manifest's own checks require plain text, but one built around
    # them could hold anything; only plain values may cross (protocol.py).
    if not (all(type(getattr(m, f)) is str
                for f in ("entity_id", "name", "protocol_version",
                          "law_url", "act_endpoint", "log_endpoint"))
            and (m.sub_registry_endpoint is None
                 or type(m.sub_registry_endpoint) is str)):
        failures.append("the manifest's fields are not plain text")
        return report(), None
    try:
        if m.protocol_version != PROTOCOL_VERSION:
            failures.append(f"protocol_version is {m.protocol_version!r}, "
                            f"expected {PROTOCOL_VERSION!r}")
    except Exception as e:
        failures.append(f"the manifest is unreadable: {_describe(e)}")
        return report(), None

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
        failures.append(f"petition() raised {_describe(e)}")

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
        failures.append(f"act() raised {_describe(e)}")

    # -- leave: always a Departure; the test leaves what it entered --
    for attempt, expect_already in (("first", not admitted),
                                    ("second", True)):
        try:
            response = entity.leave(petitioner)
            if not isinstance(response, Departure):
                failures.append(f"{attempt} leave() returned "
                                f"{type(response).__name__}, "
                                "expected Departure")
                break
            if not response.entity_id or not response.timestamp:
                failures.append(f"{attempt} Departure is missing its "
                                "entity_id or timestamp")
            if response.already_left is not expect_already:
                failures.append(
                    f"{attempt} leave() said already_left="
                    f"{response.already_left!r}, expected {expect_already}")
        except Exception as e:
            failures.append(f"{attempt} leave() raised, or answered "
                            f"unreadably: {_describe(e)}")
            break

    # -- log: a list of well-formed entries, with the departure in it --
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
            else:
                if admitted and not any(
                        e.kind == "departure" and e.actor_token == petitioner
                        for e in log):
                    failures.append("the log does not record the "
                                    "departure")
    except Exception as e:
        failures.append(f"log_since() raised {_describe(e)}")

    return report(), m
