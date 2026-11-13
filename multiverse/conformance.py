"""The conformance test: does an entity speak WCP/0.4?

From the DeepSeek sketch's components 3 and 14. Anyone can run it
against their own entity. It checks only that the entity speaks the
protocol: not whom it admits, not whether its law is interesting, not
whether it is fast.

What it checks:
  - the manifest is a plain Manifest, with plain-text fields, of this
    protocol version, naming a usable key and signed by it;
  - an unsigned petition is not admitted, nor one signed for the same id
    but another world's key;
  - a signed petition gets an Admission, a Refusal with a reason, or a
    Route;
  - a signed act gets an Ack or a Refusal with a reason;
  - an act or a leave in someone's name but signed by another key is
    refused;
  - an admission carries the world's signed arrival stamp, and the
    departure of someone admitted its signed departure stamp, naming the
    arrival (passport.py);
  - leaving: the individual's own leave is never refused; it says whether
    the individual was present; a replay of it is refused; a second leave
    answers already_left; and a departure of someone present is in the
    public log;
  - the log is a list of entries, each with a timestamp and a kind.

What it can't check: like any test from outside, it sees only answers
and the log. A world that answered correctly but secretly kept someone
would pass. The public log is where anyone can catch that. And it knows
no world's acts, so its forged act is one the world's law would refuse
anyway: a world that ignored signatures on acts but refused unknown acts
would pass. Each world's own tests must send it a forged act its law
would otherwise accept.

Changed from the sketch:
  - The test petitions with a fresh key each run, and leaves afterwards.
    The sketch's test entered every world it checked and stayed, so a
    world with room for two lost a place to it. The visit is still
    recorded in the world's log: admissions, refusals, a departure. A
    public log should show it.
  - The leaving checks are new, and so are the checks on forged and
    replayed requests (course step 2), and on the world's key and stamps
    (course step 3).
"""
from __future__ import annotations

from dataclasses import replace
from typing import List, Optional, Tuple

from .identity import Individual, Signer
from .passport import Stamp
from .protocol import (PROTOCOL_VERSION, Ack, Act, Admission, Departure,
                       Leave, LogEntry, Manifest, Petition, Refusal, Route,
                       WorldProtocol, act_document, leave_document,
                       manifest_problem)


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
                          "law_url", "act_endpoint", "log_endpoint",
                          "world_key", "signature"))
            and (m.sub_registry_endpoint is None
                 or type(m.sub_registry_endpoint) is str)):
        failures.append("the manifest's fields are not plain text")
        return report(), None
    try:
        if m.protocol_version != PROTOCOL_VERSION:
            failures.append(f"protocol_version is {m.protocol_version!r}, "
                            f"expected {PROTOCOL_VERSION!r}")
        problem = manifest_problem(m)
    except Exception as e:
        failures.append(f"the manifest is unreadable: {_describe(e)}")
        return report(), None
    if problem:
        failures.append(f"the manifest: {problem}")
        return report(), None

    world_id, world_key = m.entity_id, m.world_key
    petitioner = Individual("Conformance Test")
    stranger = Individual("Conformance Stranger")
    admitted = False
    arrival: Optional[Stamp] = None

    def own_stamp(entry, kind: str, what: str) -> Optional[Stamp]:
        """The stamp in an answer, if it is this world's `kind` stamp for
        the petitioner and verifies; else a failure, and None."""
        try:
            stamp = Stamp.from_entry(entry)
        except ValueError:
            failures.append(f"{what} carries no {kind} stamp")
            return None
        if (stamp.kind != kind or stamp.world_id != world_id
                or stamp.world_key != world_key
                or stamp.holder != petitioner.token or not stamp.verifies()):
            failures.append(f"{what}: its stamp is not this world's signed "
                            f"{kind} stamp for the petitioner")
            return None
        return stamp

    def well_formed(response, what: str, allowed) -> bool:
        """Record failures for a malformed answer; True if it is one of
        `allowed` and well formed."""
        if isinstance(response, Admission) and Admission in allowed:
            if not response.entity_id or not response.timestamp:
                failures.append(f"{what}: Admission is missing its "
                                "entity_id or timestamp")
            return True
        if isinstance(response, Ack) and Ack in allowed:
            if not response.entity_id or not response.timestamp:
                failures.append(f"{what}: Ack is missing its entity_id "
                                "or timestamp")
            return True
        if isinstance(response, Refusal) and Refusal in allowed:
            if not response.reason:
                failures.append(f"{what}: Refusal.reason is empty")
            return True
        if isinstance(response, Route) and Route in allowed:
            if not isinstance(response.target_manifest, Manifest):
                failures.append(f"{what}: Route.target_manifest is not a "
                                "Manifest")
            return True
        names = ", ".join(a.__name__ for a in allowed)
        failures.append(f"{what} returned {type(response).__name__}, "
                        f"expected {names}")
        return False

    # -- an unsigned petition is not admitted --
    try:
        unsigned = Petition(petitioner.token, petitioner.name, (),
                            "conformance test", None, 1, "")
        response = entity.petition(unsigned)
        if well_formed(response, "petition() unsigned",
                       (Admission, Refusal, Route)):
            if isinstance(response, Admission):
                admitted = True
                failures.append("an unsigned petition was admitted")
    except Exception as e:
        failures.append(f"petition() raised {_describe(e)}")

    # -- a petition signed for this id but another world's key: a world
    #    that copied this one's id must not be able to pass it on --
    if not admitted:
        try:
            elsewhere = replace(m, world_key=Signer().token)
            response = entity.petition(petitioner.petition(
                elsewhere, message="conformance test"))
            if isinstance(response, Admission):
                admitted = True
                failures.append("a petition signed for another world's key "
                                "was admitted")
        except Exception as e:
            failures.append(f"petition() raised {_describe(e)}")

    # -- a signed petition: any of the three answers, well formed --
    if not admitted:
        try:
            response = entity.petition(petitioner.petition(
                m, message="conformance test"))
            if (well_formed(response, "petition()",
                            (Admission, Refusal, Route))
                    and isinstance(response, Admission)):
                admitted = True
                arrival = own_stamp(response.stamp, "arrival",
                                    "the Admission")
        except Exception as e:
            failures.append(f"petition() raised {_describe(e)}")

    # -- a signed act by a stranger: Ack or Refusal, well formed --
    try:
        well_formed(entity.act(stranger.act(m, "conformance_test", {})),
                    "act()", (Ack, Refusal))
    except Exception as e:
        failures.append(f"act() raised {_describe(e)}")

    # -- forgeries are refused: an act and a leave in the petitioner's
    #    name, signed by the stranger --
    try:
        act = petitioner.act(m, "conformance_test", {})
        forged_act = Act(act.actor_token, act.type, act.payload, act.seq,
                         stranger.sign(act_document(world_id, world_key,
                                                    act)))
        if isinstance(entity.act(forged_act), Ack):
            failures.append("an act signed by another key was accepted")
        leave = petitioner.leave(m)
        forged = Leave(leave.token, leave.seq,
                       stranger.sign(leave_document(world_id, world_key,
                                                    leave)))
        response = entity.leave(forged)
        if not isinstance(response, Refusal):
            failures.append("a leave signed by another key was not refused")
        elif not response.reason:
            failures.append("leave() forged: Refusal.reason is empty")
    except Exception as e:
        failures.append(f"a forged request raised {_describe(e)}")

    # -- leaving: the petitioner's own leave is never refused; it says
    #    whether it was present; a replay of it is refused; a second
    #    leave answers already_left --
    try:
        first = petitioner.leave(
            m, closes=arrival.fingerprint() if arrival else "")
        for attempt, request, expect_already in (
                ("first", first, not admitted),
                ("replayed", first, None),
                ("second", petitioner.leave(m), True)):
            response = entity.leave(request)
            if expect_already is None:
                if not isinstance(response, Refusal):
                    failures.append("a replayed leave was not refused")
                continue
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
            if (attempt == "first" and arrival is not None
                    and response.already_left is False):
                departure = own_stamp(response.stamp, "departure",
                                      "the Departure")
                if (departure is not None
                        and departure.arrival != arrival.fingerprint()):
                    failures.append("the departure stamp does not name the "
                                    "arrival it closes")
    except Exception as e:
        failures.append(f"leave() raised, or answered unreadably: "
                        f"{_describe(e)}")

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
                        e.kind == "departure"
                        and e.actor_token == petitioner.token
                        for e in log):
                    failures.append("the log does not record the "
                                    "departure")
    except Exception as e:
        failures.append(f"log_since() raised {_describe(e)}")

    return report(), m
