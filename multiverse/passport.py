"""The passport: the stamps worlds have signed for an individual.

From the DeepSeek sketch's component 2, and the signed passports of its
component 15, as course step 3 builds them. A world is a key (protocol.py)
and signs a stamp, a short statement about one individual, at three
moments:

  arrival     it admitted the individual
  departure   the individual left; the stamp names the arrival it
              closes, by that stamp's fingerprint
  made        the individual made something there (a turn of a poem, a
              reaction); the stamp names the thing by its fingerprint,
              and the arrival it was made during

A passport is those stamps, plus the individual's own signed leaves. Any
world, or anyone, can check a passport offline with `verify_passport`,
without asking the worlds that stamped it: each stamp must be signed by
the key it names, for the passport's holder, and a departure or a made
stamp must point at an arrival stamp of the same world in the passport.

A world can't stop someone leaving by not stamping it. Leaving is the
individual's own signed request, and it names the arrival it closes; the
leave goes into the passport too, so a visit the world never stamped
closed shows as ended, on the holder's word, with no departure stamp.

What a stamp proves, and what it doesn't: it proves that whoever holds
`world_key` signed it, not that the key is the world's. Anyone can make
a key and sign an arrival "from" any world id with it. Which world a key
belongs to comes from that world's signed manifest
(protocol.manifest_problem), and over a network from a registry's
listing (course step 13); `verify_passport` checks stamps against the
keys it is given (`known_keys`), and every world gives it its own. The
times are the world's own claims. A holder can leave stamps out of the
passport it shows, but can't change, add or repeat one. A passport shows every
world in it to each world it is shown to; whether a person may keep some
presences unlinked is an open question for the founder (STATUS.md).

Changed from the sketch: the sketch's passport held unsigned
(world, time) pairs, which its holder could forge; its signed passports
(component 15) were signed by worlds whose identity was a name, not a
key, and had no departures or made things.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .identity import (Identity, Signer, canonical, same_identity,
                       signature_valid)
from .protocol import PROTOCOL_VERSION, Leave, leave_document

KINDS = ("arrival", "departure", "made")


def fingerprint(entry: Dict) -> str:
    """The SHA-256 of an entry's exact bytes, signature included, as 64
    hexadecimal characters. Changing anything in a stamp changes its
    fingerprint."""
    return hashlib.sha256(canonical(entry)).hexdigest()


def thing_fingerprint(thing: Dict) -> str:
    """The fingerprint of something made (a turn, a reaction), as a made
    stamp names it."""
    return hashlib.sha256(canonical(thing)).hexdigest()


def _text(d: Dict, key: str) -> str:
    value = d.get(key)
    if type(value) is not str:
        raise ValueError(f"{key} must be plain text")
    return value


@dataclass(frozen=True)
class Stamp:
    """A world's signed statement about one individual (see the module's
    docstring). `arrival` is the fingerprint of the arrival stamp a
    departure or made stamp belongs to ("" for an arrival); `made` is the
    fingerprint of what was made ("" otherwise). `wcp` is the protocol
    version it was signed under, so it still verifies when the protocol
    changes."""
    kind: str
    world_id: str
    world_key: str
    holder: str
    timestamp: str
    arrival: str = ""
    made: str = ""
    signature: str = ""
    wcp: str = PROTOCOL_VERSION

    def document(self) -> Dict:
        """What the world signs."""
        return {"wcp": self.wcp, "kind": "stamp",
                "stamp": self.kind, "world": self.world_id,
                "world_key": self.world_key, "holder": self.holder,
                "time": self.timestamp, "arrival": self.arrival,
                "made": self.made}

    def entry(self) -> Dict:
        """The stamp as a plain passport entry."""
        return dict(self.document(), entry="stamp",
                    signature=self.signature)

    def fingerprint(self) -> str:
        return fingerprint(self.entry())

    def verifies(self) -> bool:
        return signature_valid(self.world_key, self.document(),
                               self.signature)

    @classmethod
    def from_entry(cls, entry: object) -> "Stamp":
        """Read a stamp entry; ValueError if it isn't one. Reading doesn't
        check the signature: verify_passport does."""
        if type(entry) is not dict or entry.get("entry") != "stamp":
            raise ValueError("not a stamp")
        return cls(kind=_text(entry, "stamp"), world_id=_text(entry, "world"),
                   world_key=_text(entry, "world_key"),
                   holder=_text(entry, "holder"),
                   timestamp=_text(entry, "time"),
                   arrival=_text(entry, "arrival"),
                   made=_text(entry, "made"),
                   signature=_text(entry, "signature"),
                   wcp=_text(entry, "wcp"))


def make_stamp(signer: Signer, kind: str, world_id: str, holder: str,
               timestamp: str, arrival: str = "", made: str = "") -> Stamp:
    """A stamp signed by `signer`, the world's key."""
    if kind not in KINDS:
        raise ValueError(f"a stamp is one of {KINDS}")
    unsigned = Stamp(kind, world_id, signer.token, holder, timestamp,
                     arrival, made)
    return Stamp(kind, world_id, signer.token, holder, timestamp, arrival,
                 made, signer.sign(unsigned.document()))


@dataclass(frozen=True)
class LeaveNote:
    """The individual's own signed leave, kept in its passport: its
    record of having left a world, whatever the world stamped. `wcp` is
    the protocol version it was signed under."""
    world_id: str
    world_key: str
    holder: str
    closes: str
    seq: int
    signature: str
    wcp: str = PROTOCOL_VERSION

    def leave(self) -> Leave:
        return Leave(self.holder, self.seq, self.signature, self.closes)

    def verifies(self) -> bool:
        document = dict(leave_document(self.world_id, self.world_key,
                                       self.leave()), wcp=self.wcp)
        return signature_valid(self.holder, document, self.signature)

    def entry(self) -> Dict:
        return {"entry": "leave", "wcp": self.wcp, "world": self.world_id,
                "world_key": self.world_key, "holder": self.holder,
                "closes": self.closes, "seq": self.seq,
                "signature": self.signature}

    @classmethod
    def from_entry(cls, entry: object) -> "LeaveNote":
        if type(entry) is not dict or entry.get("entry") != "leave":
            raise ValueError("not a leave")
        seq = entry.get("seq")
        if type(seq) is not int:
            raise ValueError("seq must be a whole number")
        return cls(world_id=_text(entry, "world"),
                   world_key=_text(entry, "world_key"),
                   holder=_text(entry, "holder"),
                   closes=_text(entry, "closes"), seq=seq,
                   signature=_text(entry, "signature"),
                   wcp=_text(entry, "wcp"))

    @classmethod
    def of(cls, world_id: str, world_key: str, leave: Leave) -> "LeaveNote":
        return cls(world_id, world_key, leave.token, leave.closes,
                   leave.seq, leave.signature)


@dataclass(frozen=True)
class Visit:
    """One stay in one world, as a passport shows it. `left` is
    "stamped" (the world stamped the departure), "unstamped" (only the
    holder's own signed leave says it ended) or "" (still there, as far
    as the passport shows)."""
    world_id: str
    world_key: str
    arrived: str
    left: str
    made: int


@dataclass(frozen=True)
class PassportCheck:
    problems: Tuple[str, ...]
    visits: Tuple[Visit, ...]

    @property
    def ok(self) -> bool:
        return not self.problems


@dataclass(frozen=True)
class Passport:
    """An identity, the stamps worlds signed for it, and its own signed
    leaves. Appended to, never changed."""
    identity: Identity
    stamps: Tuple[Stamp, ...] = ()
    leaves: Tuple[LeaveNote, ...] = ()

    def with_stamp(self, stamp: Stamp) -> "Passport":
        return Passport(self.identity, self.stamps + (stamp,), self.leaves)

    def with_leave(self, note: LeaveNote) -> "Passport":
        return Passport(self.identity, self.stamps, self.leaves + (note,))

    def with_identity(self, identity: Identity) -> "Passport":
        """Rename the holder. The token must stay the same: a new token
        is a different individual, with a passport of its own."""
        if not same_identity(self.identity, identity):
            raise ValueError("with_identity requires the same token; "
                             "use a new passport for a new identity")
        return Passport(identity, self.stamps, self.leaves)

    def entries(self) -> Tuple[Dict, ...]:
        """The passport as plain entries, as a petition carries it."""
        return (tuple(s.entry() for s in self.stamps)
                + tuple(n.entry() for n in self.leaves))

    @classmethod
    def from_entries(cls, identity: Identity, entries: object) -> "Passport":
        """Read a passport's entries; ValueError if they aren't a list or
        tuple of stamp and leave entries. Doesn't verify them."""
        if type(entries) not in (list, tuple):
            raise ValueError("a passport is a list of entries")
        stamps, leaves = [], []
        for entry in entries:
            kind = entry.get("entry") if type(entry) is dict else None
            if kind == "stamp":
                stamps.append(Stamp.from_entry(entry))
            elif kind == "leave":
                leaves.append(LeaveNote.from_entry(entry))
            else:
                raise ValueError("an entry is a stamp or a leave")
        return cls(identity, tuple(stamps), tuple(leaves))

    def open_arrival(self, world_key: str) -> Optional[Stamp]:
        """The latest arrival stamp from `world_key` that no departure
        stamp or own leave has closed, if any."""
        closed = ({s.arrival for s in self.stamps if s.kind == "departure"}
                  | {n.closes for n in self.leaves})
        for stamp in reversed(self.stamps):
            if (stamp.kind == "arrival" and stamp.world_key == world_key
                    and stamp.fingerprint() not in closed):
                return stamp
        return None

    def worlds_visited(self) -> List[str]:
        """World ids of the arrivals, in order, repeats kept."""
        return [s.world_id for s in self.stamps if s.kind == "arrival"]

    def __len__(self) -> int:
        return len(self.stamps)


def _entry_fingerprint(item: object) -> Optional[str]:
    """The fingerprint of a stamp's or a leave's entry, or None if it
    isn't one whose fields are plain text (a leave's seq, a whole number)
    that can be written as exact bytes."""
    if type(item) not in (Stamp, LeaveNote):
        return None
    for name, value in vars(item).items():
        if type(value) is not (int if name == "seq" else str):
            return None
    try:
        return fingerprint(item.entry())
    except (TypeError, ValueError):
        return None


def verify_passport(passport: Passport,
                    known_keys: Optional[Dict[str, str]] = None
                    ) -> PassportCheck:
    """Check every stamp and leave in a passport, offline. Never raises,
    for any passport its constructors or `from_entries` can build.
    `known_keys` maps world ids to the keys the checker knows them by
    (from their manifests): a stamp naming one of those ids under another
    key is a problem. Without it, a stamp shows only which key signed.
    A stamp or leave that appears twice is a problem too: a holder can
    leave stamps out, but not change, add or repeat one."""
    if (type(passport) is not Passport
            or type(passport.identity) is not Identity
            or type(passport.identity.token) is not str
            or type(passport.stamps) is not tuple
            or type(passport.leaves) is not tuple):
        return PassportCheck(("not a passport",), ())
    known = known_keys if type(known_keys) is dict else {}
    problems: List[str] = []
    holder = passport.identity.token
    stamp_fps = [_entry_fingerprint(s) for s in passport.stamps]
    arrivals: Dict[str, Stamp] = {
        fp: stamp for fp, stamp in zip(stamp_fps, passport.stamps)
        if fp is not None and stamp.kind == "arrival"}
    seen: Dict[str, int] = {}
    departures: Dict[str, Stamp] = {}
    made: Dict[str, int] = {}
    for i, (stamp, fp) in enumerate(zip(passport.stamps, stamp_fps)):
        if fp is None:
            problems.append(f"stamp {i + 1}: it isn't a stamp of plain "
                            "text that can be written as exact bytes")
            continue
        where = f"stamp {i + 1} ({stamp.kind}, {stamp.world_id})"
        if fp in seen:
            problems.append(f"{where}: it repeats stamp {seen[fp]}")
            continue
        seen[fp] = i + 1
        if stamp.kind not in KINDS:
            problems.append(f"{where}: not a kind of stamp")
            continue
        if stamp.holder != holder:
            problems.append(f"{where}: it is for another individual")
            continue
        if not stamp.verifies():
            problems.append(f"{where}: its signature does not verify "
                            "against the world key it names")
            continue
        if known.get(stamp.world_id, stamp.world_key) != stamp.world_key:
            problems.append(f"{where}: it is signed by a key that isn't "
                            "the one that world is known by")
            continue
        if stamp.kind == "arrival":
            continue
        arrival = arrivals.get(stamp.arrival)
        if (arrival is None or arrival.world_key != stamp.world_key
                or arrival.world_id != stamp.world_id):
            problems.append(f"{where}: it names no arrival of this world "
                            "in the passport")
            continue
        if stamp.kind == "departure":
            if stamp.arrival in departures:
                problems.append(f"{where}: that arrival already has a "
                                "departure stamp")
                continue
            departures[stamp.arrival] = stamp
        else:
            made[stamp.arrival] = made.get(stamp.arrival, 0) + 1
    unstamped = set()
    seen_leaves: Dict[str, int] = {}
    for i, note in enumerate(passport.leaves):
        fp = _entry_fingerprint(note)
        if fp is None:
            problems.append(f"leave {i + 1}: it isn't a leave of plain "
                            "values that can be written as exact bytes")
            continue
        where = f"leave {i + 1} ({note.world_id})"
        arrival = arrivals.get(note.closes)
        if fp in seen_leaves:
            problems.append(f"{where}: it repeats leave {seen_leaves[fp]}")
            continue
        seen_leaves[fp] = i + 1
        if note.holder != holder:
            problems.append(f"{where}: it is another individual's")
        elif not note.verifies():
            problems.append(f"{where}: its signature does not verify")
        elif (arrival is None or arrival.world_key != note.world_key
              or arrival.world_id != note.world_id):
            problems.append(f"{where}: it closes no arrival of this world "
                            "in the passport")
        else:
            unstamped.add(note.closes)
    visits = []
    for fp, arrival in arrivals.items():
        if (not arrival.verifies() or arrival.holder != holder
                or known.get(arrival.world_id, arrival.world_key)
                != arrival.world_key):
            continue
        left = ("stamped" if fp in departures
                else "unstamped" if fp in unstamped else "")
        visits.append(Visit(arrival.world_id, arrival.world_key,
                            arrival.timestamp, left, made.get(fp, 0)))
    return PassportCheck(tuple(problems), tuple(visits))


def to_dict(passport: Passport) -> dict:
    return {"identity": {"token": passport.identity.token,
                         "name": passport.identity.name},
            "entries": list(passport.entries())}


def from_dict(d: dict) -> Passport:
    """Reads a passport; ValueError if it can't. Doesn't verify it:
    verify_passport does."""
    identity = Identity(token=d["identity"]["token"],
                        name=d["identity"]["name"])
    return Passport.from_entries(identity, d.get("entries", []))
