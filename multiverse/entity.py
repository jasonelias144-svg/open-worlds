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
  - Course step 6: a key can be signed over to a new one (succession.py).
    A world learns successions from the passports it is shown and from
    `know_succession`, and refuses requests a retired key signs, except a
    leave. A world signs its own key over with `sign_over`. Its
    timestamps only grow, so two stamps it gives are never the same.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .identity import Identity, Signer, token_problem
from .passport import (Passport, PassportCheck, Stamp, make_stamp,
                       thing_fingerprint, verify_passport)
from .protocol import (PROTOCOL_VERSION, Act, ActResponse, Admission,
                       Departure, Leave, LeaveResponse, LogEntry, Manifest,
                       Petition, PetitionResponse, Refusal, act_document,
                       is_plain, leave_document, manifest_problem,
                       petition_document, request_problem, signed_manifest)
from .succession import Lineage, Succession, sign_over


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
    "not yet. The numbers this world has seen are kept in memory; unless "
    "they are saved and restored across a restart (multiverse/keys.py), "
    "an old request could then be accepted once.")


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
        self._last_time: Optional[datetime] = None
        self._log: List[LogEntry] = []
        self._admitted: Dict[str, Admission] = {}
        self._arrivals: Dict[str, Stamp] = {}
        self._passports: Dict[str, Passport] = {}
        self._last_seq: Dict[str, int] = {}
        # World id -> key, for the worlds this one knows (know()). Its own
        # is always among them.
        self._known: Dict[str, str] = {entity_id: self._key.token}
        # The successions this world knows: its own, and others' it has
        # been shown (succession.py).
        self._lineage = Lineage()

    # -- the protocol ---------------------------------------------------

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> PetitionResponse:
        timestamp = self._now()
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
        if self._lineage.retired("", token):
            return self._refuse(timestamp, token,
                                "Cannot admit: this key has been signed "
                                "over to another key; petition with that "
                                "one", "petition")
        check = self._verify(earlier)
        if not check.ok:
            return self._refuse(timestamp, token,
                                "Cannot admit: the passport has an entry "
                                f"that doesn't verify: "
                                f"{check.problems[0]}", "petition")
        # Only what concerns this world: the petitioner's own line of
        # keys, and successions on the line of a world it knows (its own
        # past among them; `_learn` checks that). Anything else could be
        # junk made to fill its memory.
        self._learn((s for s in earlier.successions
                     if type(s) is Succession
                     and (s.of or s.old in check.earlier_keys)), shown=True)
        present = [k for k in check.earlier_keys if k in self._admitted]
        if present:
            return self._refuse(timestamp, token,
                                "Cannot admit: already here under an "
                                "earlier key; leave with that key first",
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
        problem = self._entry_problem(token, earlier)
        if problem:
            return self._refuse(timestamp, token, f"Cannot admit: {problem}",
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
        self._entered(token, timestamp)
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
        timestamp = self._now()
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
        self._left(token, timestamp)
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

    def know(self, manifest: Manifest) -> None:
        """Learn another world's key from its signed manifest, so that a
        stamp in that world's name under any other key is refused here
        (passport.verify_passport), unless a succession of that world
        links the two. ValueError if the manifest doesn't verify, or
        names this world's id, or a key this world knows was signed over,
        or an id already known by another key. (A world known by a key
        that signs over is followed to the new key by
        `know_succession`.)"""
        problem = manifest_problem(manifest)
        if problem:
            raise ValueError(f"not a usable manifest: {problem}")
        if manifest.entity_id == self._manifest.entity_id:
            raise ValueError("a world knows its own key already; this "
                             "manifest names its id")
        if self._lineage.retired(manifest.entity_id, manifest.world_key):
            raise ValueError(f"{manifest.entity_id}'s key in this manifest "
                             "has been signed over to another key; ask "
                             "for its latest manifest")
        known = self._known.get(manifest.entity_id)
        if known is not None and known != manifest.world_key:
            raise ValueError(f"{manifest.entity_id} is already known by "
                             "another key")
        self._known[manifest.entity_id] = manifest.world_key

    def know_succession(self, succession: Succession) -> None:
        """Learn that a key was signed over (succession.py): a world's,
        so that it is known by its new key and its stamps under either
        still count; or an individual's, so that requests its old key
        signs are refused here, except a leave. Of this world's own keys,
        only its past is taken (a succession that leads to its key now,
        as a restarted world may need): only `sign_over` signs its key
        over. ValueError if the succession isn't usable, would sign this
        world's key over, or signs over a key already signed over to
        another."""
        problem = self._learn((succession,))
        if problem:
            raise ValueError(f"can't take this succession: {problem}")

    def known_keys(self) -> Dict[str, str]:
        """The worlds this one knows, by id, with their keys."""
        return dict(self._known)

    def successions(self, of: Optional[str] = None) -> List[Succession]:
        """The successions this world knows: all, or those of one world
        (its own, `successions(world.manifest().entity_id)`, are what a
        visitor carries in a passport so that stamps given under its
        earlier keys still count; `Passport.with_succession`)."""
        return self._lineage.successions(of)

    def sign_over(self, new_key: Signer) -> Succession:
        """Sign this world's key over to `new_key`, which then signs its
        manifest, its stamps, and the seen-numbers file (keys.py).
        Requests must name the new key from now on: one signed for the
        old key is refused. Those present stay; the stamps they are given
        from now on link to their arrivals through the succession, which
        is added to the passports this world holds for them."""
        own = self._manifest.entity_id
        s = sign_over(self._key, new_key, of=own, timestamp=self._now())
        problem = self._lineage.add(s)
        if problem:
            raise ValueError(f"can't sign over: {problem}")
        self._key = new_key
        m = self._manifest
        self._manifest = signed_manifest(
            new_key, entity_id=m.entity_id, name=m.name,
            protocol_version=m.protocol_version, law_url=m.law_url,
            act_endpoint=m.act_endpoint, log_endpoint=m.log_endpoint,
            sub_registry_endpoint=m.sub_registry_endpoint)
        self._known[own] = new_key.token
        for token, passport in self._passports.items():
            self._passports[token] = passport.with_succession(s)
        self._log.append(LogEntry(timestamp=s.timestamp, kind="signed_over",
                                  data={"succession": s.entry()}))
        return s

    def seen_numbers(self) -> Dict[str, int]:
        """The highest request number this world has seen from each key
        (protocol.request_problem), to keep across a restart (keys.py)."""
        return dict(self._last_seq)

    def restore_seen(self, seen: Dict[str, int]) -> None:
        """Take back numbers saved before a restart, so an old request
        can't be replayed. Each number only ever grows. ValueError if
        any entry isn't a usable key with a whole number >= 1."""
        if type(seen) is not dict:
            raise ValueError("seen numbers are a mapping of key to number")
        for token, seq in seen.items():
            if token_problem(token) or type(seq) is not int or seq < 1:
                raise ValueError("a seen number must be a whole number "
                                 ">= 1 for a usable key")
        for token, seq in seen.items():
            self._last_seq[token] = max(self._last_seq.get(token, 0), seq)

    # -- for subclasses -------------------------------------------------

    def _now(self) -> str:
        """The time now, as this world records it: always later than the
        last time it gave, even on a coarse clock, so no two stamps it
        signs are the same."""
        t = datetime.now(timezone.utc)
        if self._last_time is not None and t <= self._last_time:
            t = self._last_time + timedelta(microseconds=1)
        self._last_time = t
        return t.isoformat()

    def _verify(self, passport: Passport) -> PassportCheck:
        """Check a passport against the keys and successions this world
        knows."""
        return verify_passport(passport, dict(self._known), self._lineage)

    def _entry_problem(self, token: str, passport: Passport) -> str:
        """Why this world can't take someone in now, beyond its law's
        published conditions (for example, a crowded entrance), or "".
        `passport` is the petitioner's, already verified."""
        return ""

    def _entered(self, token: str, timestamp: str) -> None:
        """Called once someone has been admitted."""

    def _left(self, token: str, timestamp: str) -> None:
        """Called once someone has left. It must not fail: leaving can't
        be refused."""

    # -- internals ------------------------------------------------------

    def _learn(self, successions, shown: bool = False) -> str:
        """Take successions, and follow any world this one knows to its
        new key. Of its own, only those that lead to its key now: nobody
        but the world signs its key over (`sign_over`), or a thief of its
        key could stop it from ever signing over. `shown` means they came
        in a passport: then, of another world's, only those on the line
        of the key this world knows it by (before it or after it), so
        that nobody can fill a world's memory with junk. "" if all were
        taken, else the first problem (the others are still taken)."""
        own = self._manifest.entity_id
        first = ""
        linked = []
        for s in successions:
            if type(s) is Succession and (s.of == own
                                          or (shown and s.of)):
                linked.append(s)
                continue
            problem = self._lineage.add(s)
            if problem and not first:
                first = problem
        # In whatever order shown: take what links, then look again.
        while linked:
            fits = [s for s in linked if self._links(s)]
            for s in fits:
                problem = self._lineage.add(s)
                if problem and not first:
                    first = problem
                linked.remove(s)
            self._follow()
            if not fits:
                first = first or ("it isn't on the line of a key this "
                                  "world knows, or it would sign this "
                                  "world's own key over")
                break
        self._follow()
        return first

    def _links(self, s: Succession) -> bool:
        """Whether `s` is on the line of the key this world knows that
        world by: its past (it leads to that key), or, for another world,
        its next step (it signs that key over)."""
        if s.of == self._manifest.entity_id:
            return self._lineage.leads_to(s.of, s.new, self._key.token)
        known = self._known.get(s.of)
        return known is not None and (
            self._lineage.leads_to(s.of, s.new, known) or s.old == known)

    def _follow(self) -> None:
        """Follow every other world this one knows to its latest key."""
        own = self._manifest.entity_id
        for world_id, key in self._known.items():
            if world_id != own:
                self._known[world_id] = self._lineage.latest(world_id, key)

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
        if self._lineage.retired("", act.actor_token):
            return self._refuse(timestamp, act.actor_token,
                                "This key has been signed over to another "
                                "key; it can still leave, but not act",
                                "act")
        return None
