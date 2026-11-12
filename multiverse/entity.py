"""What every entity in this package shares: entering, leaving, the log.

The sketch's poetry world, chemistry world and registry (components 4 to
6) each carried their own copy of the same petition code. It lives here
once, and each entity adds only its own law's acts.

Changed from the sketch:
  - A petition with an unusable token or passport is refused. In the
    sketch it raised an exception inside the world.
  - Leaving (protocol.py). A leave ends membership, frees the place, and
    is recorded in the log. It can't be refused.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from .identity import Identity, token_problem
from .passport import Admission as PassportAdmission
from .passport import Passport
from .protocol import (PROTOCOL_VERSION, Act, ActResponse, Admission,
                       Departure, LogEntry, Manifest, Petition,
                       PetitionResponse, Refusal, is_plain)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_passport(pairs) -> Optional[tuple]:
    """A petition's passport as admissions, or None if it isn't a plain
    list or tuple of plain (world id, timestamp) text pairs."""
    if type(pairs) not in (tuple, list):
        return None
    earlier = []
    for pair in pairs:
        if type(pair) not in (tuple, list) or len(pair) != 2:
            return None
        try:   # Admission itself requires plain, valid text
            earlier.append(PassportAdmission(world_id=pair[0],
                                             timestamp=pair[1]))
        except ValueError:
            return None
    return tuple(earlier)


class Entity:
    """A conforming entity whose law has `admits_any_identity` and
    `max_admitted`. Subclasses implement act()."""

    noun = "World"      # in refusals: "The World is full"
    scheme = "world"    # in the manifest's addresses

    def __init__(self, entity_id: str, name: str, law, *,
                 sub_registry: bool = False):
        self._law = law
        base = f"{self.scheme}://{entity_id}"
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version=PROTOCOL_VERSION,
            law_url=f"{base}/law",
            act_endpoint=f"{base}/act",
            log_endpoint=f"{base}/log",
            sub_registry_endpoint=f"{base}/worlds" if sub_registry else None)
        self._log: List[LogEntry] = []
        self._admitted: Dict[str, Admission] = {}
        self._passports: Dict[str, Passport] = {}

    # -- the protocol ---------------------------------------------------

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> PetitionResponse:
        timestamp = now()
        if type(petition) is not Petition:
            return self._refuse(timestamp, None,
                                "Cannot admit: not a petition", "petition")
        token = petition.petitioner_token
        problem = token_problem(token)
        if problem:
            return self._refuse(timestamp, None,
                                f"Cannot admit: {problem}", "petition")
        if (type(petition.message) is not str
                or (petition.target is not None
                    and type(petition.target) is not str)):
            return self._refuse(timestamp, token,
                                "Cannot admit: the message and target "
                                "must be plain text", "petition")
        if (type(petition.petitioner_name) is not str
                or not petition.petitioner_name):
            return self._refuse(timestamp, token,
                                "Cannot admit: the name is empty",
                                "petition")
        if not self._law.admits_any_identity:
            return self._refuse(timestamp, token,
                                f"This {self.noun} does not admit "
                                "strangers", "petition")
        if (self._law.max_admitted is not None
                and len(self._admitted) >= self._law.max_admitted):
            return self._refuse(timestamp, token,
                                f"The {self.noun} is full", "petition")
        if token in self._admitted:
            return self._refuse(timestamp, token, "Already admitted",
                                "petition")
        earlier = _read_passport(petition.passport_admissions)
        if earlier is None:
            return self._refuse(timestamp, token,
                                "Cannot read the passport: it must be "
                                "pairs of plain text (world id, ISO 8601 "
                                "time)", "petition")

        admission = Admission(entity_id=self._manifest.entity_id,
                              timestamp=timestamp)
        self._admitted[token] = admission
        self._passports[token] = Passport(
            identity=Identity(token=token, name=petition.petitioner_name),
            admissions=earlier,
        ).with_admission(PassportAdmission(
            world_id=self._manifest.entity_id, timestamp=timestamp))
        self._log.append(LogEntry(
            timestamp=timestamp, kind="admission", actor_token=token,
            data={"name": petition.petitioner_name}))
        return admission

    def act(self, act: Act) -> ActResponse:
        raise NotImplementedError

    def leave(self, token: str) -> Departure:
        """Always succeeds. Leaving when not present changes nothing."""
        timestamp = now()
        if type(token) is not str or token not in self._admitted:
            return Departure(entity_id=self._manifest.entity_id,
                             timestamp=timestamp, already_left=True)
        del self._admitted[token]
        passport = self._passports.pop(token)
        self._log.append(LogEntry(
            timestamp=timestamp, kind="departure", actor_token=token,
            data={"name": passport.identity.name}))
        return Departure(entity_id=self._manifest.entity_id,
                         timestamp=timestamp)

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        """Entries after `timestamp`, or all of them. A timestamp that
        isn't text matches nothing.

        Known limits, both from the sketch:
          - Entries sharing a timestamp with the one given are skipped,
            so a reader polling with the last timestamp it saw can miss
            an entry written in the same microsecond.
          - The entries are the world's own, not copies: within one
            process, a reader that changes an entry's data changes the
            record. Over the network (step 3) readers get copies, and a
            hash-chained log, like the world kernel's, would make any
            change detectable."""
        if timestamp is None:
            return list(self._log)
        if type(timestamp) is not str:
            return []
        return [e for e in self._log if e.timestamp > timestamp]

    # -- conveniences (not part of the protocol) ------------------------

    def law(self):
        return self._law

    def is_admitted(self, token: str) -> bool:
        return token in self._admitted

    def members(self) -> List[str]:
        """Names of those present, in order of arrival."""
        return [self._passports[t].identity.name for t in self._admitted]

    def passport_of(self, token: str) -> Optional[Passport]:
        """The passport the world holds for someone present."""
        return self._passports.get(token)

    # -- internals ------------------------------------------------------

    def _refuse(self, timestamp: str, actor: Optional[str], reason: str,
                kind: str) -> Refusal:
        self._log.append(LogEntry(
            timestamp=timestamp, kind=f"{kind}_refused", actor_token=actor,
            data={"reason": reason}))
        return Refusal(reason=reason)

    def _actor_problem(self, timestamp: str, act: Act) -> Optional[Refusal]:
        """The checks every act passes first. Only plain values cross the
        protocol (protocol.py), so nothing a visitor sends can redefine
        how it compares or hashes."""
        if type(act) is not Act:
            return self._refuse(timestamp, None, "Not an act", "act")
        if (type(act.actor_token) is not str
                or act.actor_token not in self._admitted):
            actor = act.actor_token if type(act.actor_token) is str else None
            return self._refuse(timestamp, actor,
                                "Actor is not admitted", "act")
        if type(act.type) is not str:
            return self._refuse(timestamp, act.actor_token,
                                "The act type must be plain text", "act")
        if type(act.payload) is not dict or not self._plain_payload(act):
            return self._refuse(timestamp, act.actor_token,
                                "The payload must be a mapping of plain "
                                "values", "act")
        return None

    def _plain_payload(self, act: Act) -> bool:
        """Whether the payload holds only plain values. An entity whose
        law carries something else (the registry's listing act carries a
        world) says so here."""
        return is_plain(act.payload)
