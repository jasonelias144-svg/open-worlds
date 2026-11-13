"""What every entity in this package shares: entering, leaving, the log.

The sketch's poetry world, chemistry world and registry (components 4 to
6) each carried their own copy of the same petition code. It lives here
once, and each entity adds only its own law's acts.

Changed from the sketch:
  - A petition with an unusable token or passport is refused. In the
    sketch it raised an exception inside the world.
  - Leaving (protocol.py). A leave ends membership, frees the place, and
    is recorded in the log. The law can't refuse it.
  - Course step 2: every petition, act and leave must be signed by the
    individual it names, for this world, with a growing `seq`. Anything
    else is refused before the law is consulted, and its refusal is
    logged without naming any key: the log names a key only for what
    that key signed.
  - Course step 3: every entity is a key (a Signer). Its manifest names
    the key and is signed by it, requests must name it, and the entity
    signs a stamp for each arrival and departure, and for what is made
    inside it (`_made`). A petition's passport is checked offline before
    anything else is decided, and one with a forged or altered stamp is
    refused (passport.py).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from .identity import Identity, Signer, token_problem
from .passport import (Passport, Stamp, make_stamp, thing_fingerprint,
                       verify_passport)
from .protocol import (PROTOCOL_VERSION, Act, ActResponse, Admission,
                       Departure, Leave, LeaveResponse, LogEntry, Manifest,
                       Petition, PetitionResponse, Refusal, act_document,
                       is_plain, leave_document, petition_document,
                       request_problem, signed_manifest)


# What every entity built on this module states in its law about the
# requests it accepts: they are what petition, act and leave enforce.
SIGNED_REQUESTS_LAW = (
    f"- Protocol {PROTOCOL_VERSION}: every petition, act and leave must be "
    "signed by the key it names, for this world's id and key, with a "
    "number larger than the last one this world saw from that key. "
    "Anything else is refused.")
STAMPS_LAW = (
    "- This world signs a stamp for each arrival and each departure, and "
    "for what is made here. A petition whose passport has a stamp that "
    "doesn't verify is refused.")
UNSIGNED_ANSWERS_LIMIT = (
    "- Only stamps are signed: other answers, and this world's log, are "
    "not yet. The numbers this world has seen are kept only in memory, so "
    "after a restart an old request could be accepted once.")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_passport(identity: Identity, entries) -> Optional[Passport]:
    """A petition's passport, or None if its entries aren't plain stamp
    and leave entries (passport.py). Not yet verified."""
    if type(entries) not in (tuple, list) or not is_plain(list(entries)):
        return None
    try:
        return Passport.from_entries(identity, entries)
    except ValueError:
        return None


class Entity:
    """A conforming entity whose law has `admits_any_identity` and
    `max_admitted`. Subclasses implement act()."""

    noun = "World"      # in refusals: "The World is full"
    scheme = "world"    # in the manifest's addresses

    def __init__(self, entity_id: str, name: str, law, *,
                 sub_registry: bool = False, key: Optional[Signer] = None):
        """`key` is the entity's own key; a new one is made if none is
        given. Like an individual's, it never leaves the entity."""
        self._law = law
        self._key = Signer() if key is None else key
        base = f"{self.scheme}://{entity_id}"
        self._manifest = signed_manifest(
            self._key, entity_id=entity_id, name=name,
            protocol_version=PROTOCOL_VERSION,
            law_url=f"{base}/law",
            act_endpoint=f"{base}/act",
            log_endpoint=f"{base}/log",
            sub_registry_endpoint=f"{base}/worlds" if sub_registry else None)
        self._log: List[LogEntry] = []
        self._admitted: Dict[str, Admission] = {}
        self._arrivals: Dict[str, Stamp] = {}
        self._passports: Dict[str, Passport] = {}
        self._last_seq: Dict[str, int] = {}

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
        # Until the signature has verified, the log names nobody: the
        # token is only a claim (see _refuse).
        if (type(petition.message) is not str
                or (petition.target is not None
                    and type(petition.target) is not str)):
            return self._refuse(timestamp, None,
                                "Cannot admit: the message and target "
                                "must be plain text", "petition")
        if (type(petition.petitioner_name) is not str
                or not petition.petitioner_name):
            return self._refuse(timestamp, None,
                                "Cannot admit: the name is empty",
                                "petition")
        earlier = _read_passport(
            Identity(token=token, name=petition.petitioner_name),
            petition.passport)
        if earlier is None:
            return self._refuse(timestamp, None,
                                "Cannot read the passport: it must be a "
                                "list of plain stamp and leave entries",
                                "petition")
        problem = request_problem(
            token, petition.seq, petition.signature,
            petition_document(self._manifest.entity_id,
                              self._manifest.world_key, petition),
            self._last_seq)
        if problem:
            return self._refuse(timestamp, None,
                                f"Cannot admit: {problem}", "petition")
        check = verify_passport(
            earlier, {self._manifest.entity_id: self._manifest.world_key})
        if not check.ok:
            return self._refuse(timestamp, token,
                                "Cannot admit: the passport has a stamp "
                                f"or leave that doesn't verify: "
                                f"{check.problems[0]}", "petition")
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

        arrival = make_stamp(self._key, "arrival",
                             self._manifest.entity_id, token, timestamp)
        admission = Admission(entity_id=self._manifest.entity_id,
                              timestamp=timestamp, stamp=arrival.entry())
        self._admitted[token] = admission
        self._arrivals[token] = arrival
        self._passports[token] = earlier.with_stamp(arrival)
        self._log.append(LogEntry(
            timestamp=timestamp, kind="admission", actor_token=token,
            data={"name": petition.petitioner_name,
                  "stamp": arrival.fingerprint()}))
        return admission

    def act(self, act: Act) -> ActResponse:
        raise NotImplementedError

    def leave(self, leave: Leave) -> LeaveResponse:
        """The law can't refuse a leave. The only leaves refused are ones
        that aren't the leaver's own (not signed by the key they name,
        for this world, or a replay) or aren't plain leaves. Leaving when
        not present changes nothing. A departure is stamped; the stamp
        names the arrival it closes. (Whatever `closes` the leave names,
        the stamp names this world's own record of the arrival.)"""
        timestamp = now()
        if (type(leave) is not Leave or token_problem(leave.token)
                or type(leave.closes) is not str):
            return self._refuse(timestamp, None,
                                "Not a leave: it must name a key, be "
                                "signed by it, and name what it closes "
                                "as text", "leave")
        token = leave.token
        problem = request_problem(
            token, leave.seq, leave.signature,
            leave_document(self._manifest.entity_id,
                           self._manifest.world_key, leave), self._last_seq)
        if problem:
            return self._refuse(timestamp, None,
                                f"Not this individual's leave: {problem}",
                                "leave")
        if token not in self._admitted:
            return Departure(entity_id=self._manifest.entity_id,
                             timestamp=timestamp, already_left=True)
        del self._admitted[token]
        passport = self._passports.pop(token)
        arrival = self._arrivals.pop(token)
        stamp = self._departure_stamp(token, timestamp, arrival)
        self._log.append(LogEntry(
            timestamp=timestamp, kind="departure", actor_token=token,
            data={"name": passport.identity.name,
                  "arrival": arrival.fingerprint()}))
        return Departure(entity_id=self._manifest.entity_id,
                         timestamp=timestamp,
                         stamp=None if stamp is None else stamp.entry())

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        """Entries after `timestamp`, or all of them. A timestamp that
        isn't text matches nothing.

        Known limits, both from the sketch:
          - Entries sharing a timestamp with the one given are skipped,
            so a reader polling with the last timestamp it saw can miss
            an entry written in the same microsecond.
          - The entries are the world's own, not copies: within one
            process, a reader that changes an entry's data changes the
            record. Over the network (course step 13) readers get copies, and a
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

    @property
    def world_key(self) -> str:
        return self._manifest.world_key

    def is_admitted(self, token: str) -> bool:
        return token in self._admitted

    def members(self) -> List[str]:
        """Names of those present, in order of arrival."""
        return [self._passports[t].identity.name for t in self._admitted]

    def passport_of(self, token: str) -> Optional[Passport]:
        """The passport the world holds for someone present."""
        return self._passports.get(token)

    # -- internals ------------------------------------------------------

    def _departure_stamp(self, token: str, timestamp: str,
                         arrival: Stamp) -> Optional[Stamp]:
        """The departure stamp. A world that withheld it couldn't stop the
        leave (the tests have one that does); the leaver's own signed
        leave shows the visit ended."""
        return make_stamp(self._key, "departure", self._manifest.entity_id,
                          token, timestamp, arrival=arrival.fingerprint())

    def _made(self, token: str, timestamp: str, thing: Dict) -> Dict:
        """A made stamp for `thing`, made by `token` while present, added
        to the passport this world holds for it; returned as a plain
        entry, for the Ack."""
        stamp = make_stamp(self._key, "made", self._manifest.entity_id,
                           token, timestamp,
                           arrival=self._arrivals[token].fingerprint(),
                           made=thing_fingerprint(thing))
        self._passports[token] = self._passports[token].with_stamp(stamp)
        return stamp.entry()

    def _refuse(self, timestamp: str, actor: Optional[str], reason: str,
                kind: str) -> Refusal:
        """Log a refusal and return it. `actor` is the key that signed the
        request, or None if no signature has verified yet: anyone can
        write any token into a request, and the log is a public record,
        so it names a key only for what that key has signed."""
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
        # The checks before the signature are the cheap ones; until it
        # has verified, the log names nobody (see _refuse).
        if (type(act.actor_token) is not str
                or act.actor_token not in self._admitted):
            return self._refuse(timestamp, None,
                                "Actor is not admitted", "act")
        if type(act.type) is not str:
            return self._refuse(timestamp, None,
                                "The act type must be plain text", "act")
        if type(act.payload) is not dict or not is_plain(act.payload):
            return self._refuse(timestamp, None,
                                "The payload must be a mapping of plain "
                                "values", "act")
        problem = request_problem(
            act.actor_token, act.seq, act.signature,
            act_document(self._manifest.entity_id,
                         self._manifest.world_key, act), self._last_seq)
        if problem:
            return self._refuse(timestamp, None, problem, "act")
        return None
