"""
multiverse_c22.py — Component 22: leave.

The fifth WCP operation. A protected freedom: leaving cannot be
refused by a world that has admitted you. The only refusal case
is "not admitted".

Maps to course step 1 (leaving) and step 3 (signed departures).
Repo shape: multiverse/protocol.py (Leave, LeavePetition,
SignedLeave), multiverse/poetry_world.py (leave method),
multiverse/passport.py (Departure, departures),
multiverse/provenance.py (residency).

House rules honored:
  - "A world never raises on what a visitor sends." Leaving for
    a world you were never in returns Refusal, not an exception.
  - "Protected freedoms have tests." Leaving is tested against
    every refusal-worthy condition.
  - "Every behaviour has a test that fails if the behaviour
    breaks." No try/except swallows.
"""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

from multiverse_c1 import Identity, same_identity
from multiverse_c3 import (
    Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c4 import PoetryWorld
from multiverse_c13 import (
    HAS_CRYPTO, SignedAdmission, SignedAck,
    canonical_bytes, verify_signature,
)
from multiverse_c15 import PassportEntry, PassportV2


# =====================================================================
# Protocol: Leave, LeavePetition, SignedLeave
# =====================================================================

@dataclass(frozen=True)
class LeavePetition:
    """A request to leave a world. The world MUST NOT refuse this
    if the leaver is currently admitted.

    `leaver_token` — the identity token (must match an admission).
    `message` — optional, for the world's log (has no protocol
    effect; worlds are free to record or ignore it).
    """
    leaver_token: str
    message: str = ""


@dataclass(frozen=True)
class Leave:
    """A plain (WCP/0.1) leave acknowledgment."""
    entity_id: str
    timestamp: str


@dataclass(frozen=True)
class SignedLeave:
    """A WCP/0.2 leave acknowledgment, signed by the world."""
    entity_id: str
    timestamp: str
    subject_token: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "leave",
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "subject_token": self.subject_token,
        })


LeaveResponse = Union[Leave, SignedLeave, Refusal]


# =====================================================================
# PoetryWorld: leave method (mixin-style — same shape applies to
# ChemistryWorld and MultiverseRegistry)
# =====================================================================

class LeaveCapableWorld(PoetryWorld):
    """PoetryWorld that supports leave.

    The subclass tracks `_left_at` alongside the parent's `_admitted`.
    On leave:
      - not admitted, not previously left → Refusal("not admitted")
      - already left (idempotent)        → Leave(same original ts)
      - currently admitted               → Leave(new ts), remove from
                                            admitted, log the leave
    On act after leave:
      - Refusal("Actor is not admitted") — the parent's check still
        governs; the parent's `_admitted` dict is the source of truth.
    On petition after leave:
      - New admission — leaving does not block re-entry. The world
        logs two admissions; the passport can hold both.
    """

    def __init__(self, entity_id: str, name: str, **kwargs):
        super().__init__(entity_id, name, **kwargs)
        self._left_at: Dict[str, str] = {}

    def leave(self, petition: LeavePetition) -> LeaveResponse:
        token = petition.leaver_token
        ts = datetime.now(timezone.utc).isoformat()

        if token in self._admitted:
            # Active resident — leaving is honored, unconditionally
            del self._admitted[token]
            self._left_at[token] = ts
            self._log.append(LogEntry(
                timestamp=ts, kind="leave",
                actor_token=token, data={},
            ))
            return Leave(entity_id=self._manifest.entity_id,
                         timestamp=ts)

        if token in self._left_at:
            # Idempotent — same original timestamp, no new log entry.
            # The house rule forbids refusing a leave; idempotence
            # is the only correct answer for "already left."
            return Leave(entity_id=self._manifest.entity_id,
                         timestamp=self._left_at[token])

        # Never was here
        self._refuse(ts, token, "not admitted", "leave")
        return Refusal(reason="not admitted")

    def is_resident(self, token: str) -> bool:
        return token in self._admitted


# =====================================================================
# SignedWorld: wraps any leave-capable world, signs the leave
# =====================================================================

class SignedLeaveWorld:
    """Wraps any leave-capable world, signing Leave → SignedLeave.

    Takes a world and a keypair. Signs the leave with the same key
    it uses for admissions and acks. Verifiable against the world's
    published public_key, same as any other signed response.
    """

    def __init__(self, base, keypair):
        self.base = base
        self.keypair = keypair
        # Delegate unknown attributes to base (is_converged, law, etc.)
        # — same pattern as DelegatingSignedWorld in C18.

    def __getattr__(self, name):
        return getattr(self.base, name)

    def manifest_dict(self) -> dict:
        m = self.base.manifest()
        return {
            "entity_id": m.entity_id, "name": m.name,
            "protocol_version": "WCP/0.2",
            "law_url": m.law_url, "act_endpoint": m.act_endpoint,
            "log_endpoint": m.log_endpoint,
            "sub_registry_endpoint": m.sub_registry_endpoint,
            "public_key": self.keypair.public_key_hex(),
        }

    def petition(self, petition: Petition):
        response = self.base.petition(petition)
        if isinstance(response, WCPAdmission):
            payload = canonical_bytes({
                "kind": "admission",
                "entity_id": response.entity_id,
                "timestamp": response.timestamp,
                "subject_token": petition.petitioner_token,
            })
            return SignedAdmission(
                entity_id=response.entity_id,
                timestamp=response.timestamp,
                subject_token=petition.petitioner_token,
                signature=self.keypair.sign(payload).hex(),
            )
        return response

    def act(self, act: Act):
        response = self.base.act(act)
        if isinstance(response, Ack):
            payload = canonical_bytes({
                "kind": "ack",
                "entity_id": response.entity_id,
                "timestamp": response.timestamp,
                "subject_token": act.actor_token,
            })
            return SignedAck(
                entity_id=response.entity_id,
                timestamp=response.timestamp,
                subject_token=act.actor_token,
                signature=self.keypair.sign(payload).hex(),
            )
        return response

    def leave(self, petition: LeavePetition) -> LeaveResponse:
        response = self.base.leave(petition)
        if isinstance(response, Leave):
            payload = canonical_bytes({
                "kind": "leave",
                "entity_id": response.entity_id,
                "timestamp": response.timestamp,
                "subject_token": petition.leaver_token,
            })
            return SignedLeave(
                entity_id=response.entity_id,
                timestamp=response.timestamp,
                subject_token=petition.leaver_token,
                signature=self.keypair.sign(payload).hex(),
            )
        return response

    def log_since(self, timestamp=None):
        return self.base.log_since(timestamp)


# =====================================================================
# PassportV2 extension: departures
# =====================================================================

@dataclass(frozen=True)
class Departure:
    """One departure record in a passport.

    Unsigned (from a WCP/0.1 world) or signed (from WCP/0.2). The
    `subject_token` must match the passport's identity token — same
    anti-theft rule as admissions.
    """
    entity_id: str
    timestamp: str
    subject_token: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        signed_fields = (self.subject_token, self.signature)
        present = [f is not None for f in signed_fields]
        if any(present) and not all(present):
            raise ValueError(
                "subject_token and signature must both be present "
                "or both be absent")

    @property
    def is_signed(self) -> bool:
        return self.signature is not None

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "leave",
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "subject_token": self.subject_token,
        })

    @classmethod
    def from_signed(cls, leave: SignedLeave) -> "Departure":
        return cls(
            entity_id=leave.entity_id,
            timestamp=leave.timestamp,
            subject_token=leave.subject_token,
            signature=leave.signature,
        )

    @classmethod
    def from_plain(cls, leave: Leave) -> "Departure":
        return cls(entity_id=leave.entity_id,
                   timestamp=leave.timestamp)


@dataclass(frozen=True)
class PassportV2WithDepartures:
    """PassportV2 extended with departures. Frozen; additions return
    new passports. Compositional with the base passport via `.base`.
    """
    base: PassportV2
    departures: Tuple[Departure, ...] = ()

    def with_admission(self, adm: SignedAdmission
                       ) -> "PassportV2WithDepartures":
        # Add to base passport, keep departures
        entry = PassportEntry.from_signed(adm)
        new_base = self.base.with_entry(entry)
        return PassportV2WithDepartures(
            base=new_base, departures=self.departures)

    def with_departure(self, leave: Union[Leave, SignedLeave]
                       ) -> "PassportV2WithDepartures":
        if isinstance(leave, SignedLeave):
            if leave.subject_token != self.base.identity.token:
                raise ValueError(
                    f"departure is for {leave.subject_token!r}, "
                    f"passport is for {self.base.identity.token!r}")
            dep = Departure.from_signed(leave)
        elif isinstance(leave, Leave):
            dep = Departure.from_plain(leave)
        else:
            raise TypeError(f"unsupported leave type: "
                            f"{type(leave).__name__}")
        return PassportV2WithDepartures(
            base=self.base, departures=self.departures + (dep,))

    def departure_for(self, entity_id: str
                      ) -> Optional[Departure]:
        for d in self.departures:
            if d.entity_id == entity_id:
                return d
        return None

    @property
    def identity(self):
        return self.base.identity

    @property
    def entries(self):
        return self.base.entries


# =====================================================================
# Provenance extension: residency
# =====================================================================

@dataclass
class EntryProvenance:
    """One entry's provenance, extended for departures."""
    entry: PassportEntry
    # Registry, URL, manifest — as in C21
    registry_listing: Optional[object] = None
    registry_verified: bool = False
    listed_url: Optional[str] = None
    manifest_fetched: bool = False
    manifest_public_key: Optional[str] = None
    signature_valid: bool = False
    # NEW: departure/residency
    departure: Optional[Departure] = None
    departure_signature_valid: bool = False
    residency: str = "unknown"  # resident | departed | unknown
    # Final
    verdict: str = "unverified"
    reason: str = ""
    failure_stage: Optional[str] = None


def verify_departure(dep: Optional[Departure],
                      identity_token: str,
                      public_key_hex: Optional[str]) -> bool:
    """True iff the departure is signed and its signature verifies
    against the given public key, AND the subject_token matches.

    Unsigned departures return False (unverified, not forged).
    """
    if dep is None or not dep.is_signed:
        return False
    if dep.subject_token != identity_token:
        return False
    if public_key_hex is None:
        return False
    if not HAS_CRYPTO:
        return False
    return verify_signature(public_key_hex,
                            dep.canonical_payload(),
                            dep.signature)


def enrich_with_departure(
    entry_prov: EntryProvenance,
    passport: PassportV2WithDepartures,
) -> EntryProvenance:
    """Given a verified EntryProvenance (from C21), add departure
    information from the passport."""
    dep = passport.departure_for(entry_prov.entry.entity_id)
    if dep is None:
        entry_prov.residency = "resident"
        return entry_prov
    entry_prov.departure = dep
    entry_prov.departure_signature_valid = verify_departure(
        dep,
        passport.identity.token,
        entry_prov.manifest_public_key,
    )
    entry_prov.residency = "departed"
    return entry_prov
