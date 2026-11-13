"""
multiverse_c15.py — Component 15: Signed Passports.

Extends the passport to carry signed admissions. Any client can
verify the whole passport offline against a PublicKeyResolver,
without re-querying any world.

The critical property: a signed admission's subject_token MUST
equal the passport's identity token. This prevents admission theft
(placing Bob's signed admission into Alice's passport).

Prototype commitment: verification requires a PublicKeyResolver.
A passport that carried its own public keys would be self-signed
and therefore worthless — an attacker could mint any world and
sign it. The resolver is where trust lives.

Honest limits (documented, deferred):
  - The resolver's own trust is out of scope. Query the manifest,
    query a registry, use TOFU — that's the resolver's job, not
    the passport's.
  - There is no "revocation" or "expiry". A signed admission is
    valid forever, if the signature verifies. Revocation is future.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity, same_identity
from multiverse_c2 import Passport, Admission as PlainAdmission
from multiverse_c13 import (
    HAS_CRYPTO, canonical_bytes, verify_signature,
    SignedAdmission, SignedAck,
)


# =====================================================================
# PublicKeyResolver — the trust primitive
# =====================================================================

PublicKeyResolver = Callable[[str], Optional[str]]
# Given an entity_id, return the entity's public key as 64-hex,
# or None if unknown. The passport does not care how the resolver
# finds keys — manifest fetch, registry query, TOFU log, all fine.


class InMemoryKeyResolver:
    """A dict-backed resolver for testing and prototypes."""

    def __init__(self, keys: Optional[Dict[str, str]] = None):
        self._keys: Dict[str, str] = dict(keys) if keys else {}

    def register(self, entity_id: str, public_key_hex: str) -> None:
        self._keys[entity_id] = public_key_hex

    def __call__(self, entity_id: str) -> Optional[str]:
        return self._keys.get(entity_id)

    def known_entities(self) -> List[str]:
        return list(self._keys.keys())


# =====================================================================
# PassportEntry — one admission, signed or plain
# =====================================================================

@dataclass(frozen=True)
class PassportEntry:
    """One admission in a passport.

    A plain entry (from WCP/0.1 worlds) has entity_id and timestamp
    only. A signed entry (from WCP/0.2 worlds) also has subject_token
    and signature. The subject_token must match the passport's
    identity token — that binding is checked at verification time.
    """
    entity_id: str
    timestamp: str
    subject_token: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.entity_id, str) or not self.entity_id:
            raise ValueError("entity_id must be non-empty string")
        if not isinstance(self.timestamp, str) or not self.timestamp:
            raise ValueError("timestamp must be non-empty string")
        signed_fields = (self.subject_token, self.signature)
        present = [f is not None for f in signed_fields]
        if any(present) and not all(present):
            raise ValueError(
                "subject_token and signature must both be present "
                "(signed) or both be absent (plain)")

    @property
    def is_signed(self) -> bool:
        return self.signature is not None

    def to_plain(self) -> Tuple[str, str]:
        return (self.entity_id, self.timestamp)

    def canonical_payload(self) -> bytes:
        """The exact bytes the world signed. Matches C13."""
        return canonical_bytes({
            "kind": "admission",
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "subject_token": self.subject_token,
        })

    @classmethod
    def from_signed(cls, adm: SignedAdmission) -> "PassportEntry":
        return cls(
            entity_id=adm.entity_id,
            timestamp=adm.timestamp,
            subject_token=adm.subject_token,
            signature=adm.signature,
        )

    @classmethod
    def from_plain(cls, adm: PlainAdmission) -> "PassportEntry":
        return cls(entity_id=adm.world_id, timestamp=adm.timestamp)


# =====================================================================
# PassportV2 — the signed passport
# =====================================================================

@dataclass(frozen=True)
class PassportV2:
    """A passport carrying PassportEntries (signed or plain).

    Frozen, like the original Passport. Admissions are appended
    with `with_entry`, which returns a new PassportV2.
    """
    identity: Identity
    entries: Tuple[PassportEntry, ...] = ()

    def __len__(self) -> int:
        return len(self.entries)

    def with_entry(self, entry: PassportEntry) -> "PassportV2":
        return PassportV2(identity=self.identity,
                          entries=self.entries + (entry,))

    def with_identity(self, identity: Identity) -> "PassportV2":
        if not same_identity(self.identity, identity):
            raise ValueError(
                "with_identity requires the same token; "
                "use a new passport for a new identity")
        return PassportV2(identity=identity, entries=self.entries)

    def to_plain_entries(self) -> Tuple[Tuple[str, str], ...]:
        """The WCP/0.1 form — what worlds receive in a Petition."""
        return tuple(e.to_plain() for e in self.entries)

    def to_v1(self) -> Passport:
        """Downgrade to the WCP/0.1 Passport (signatures dropped)."""
        return Passport(
            identity=self.identity,
            admissions=tuple(
                PlainAdmission(world_id=e.entity_id,
                               timestamp=e.timestamp)
                for e in self.entries),
        )

    @classmethod
    def from_v1(cls, p: Passport) -> "PassportV2":
        """Upgrade a WCP/0.1 Passport (entries become plain)."""
        return cls(
            identity=p.identity,
            entries=tuple(PassportEntry.from_plain(a)
                          for a in p.admissions),
        )

    @classmethod
    def new(cls, identity: Identity) -> "PassportV2":
        return cls(identity=identity, entries=())

    def verify(self, resolver: PublicKeyResolver) -> "VerificationReport":
        return VerificationReport.verify(self, resolver)


# =====================================================================
# VerificationReport — the outcome
# =====================================================================

@dataclass
class EntryVerdict:
    entry: PassportEntry
    status: str          # verified | invalid | unverifiable | unverified
    reason: str


@dataclass
class VerificationReport:
    passport_token: str
    verdicts: List[EntryVerdict] = field(default_factory=list)

    def verified(self) -> List[EntryVerdict]:
        return [v for v in self.verdicts if v.status == "verified"]

    def invalid(self) -> List[EntryVerdict]:
        return [v for v in self.verdicts if v.status == "invalid"]

    def unverifiable(self) -> List[EntryVerdict]:
        return [v for v in self.verdicts if v.status == "unverifiable"]

    def unverified(self) -> List[EntryVerdict]:
        return [v for v in self.verdicts if v.status == "unverified"]

    @property
    def all_verified(self) -> bool:
        """Strictest bar: every entry is signed AND verified."""
        return (len(self.verdicts) > 0
                and len(self.verified()) == len(self.verdicts))

    @property
    def all_valid_or_verified(self) -> bool:
        """Loose bar: no entry is forged. Unsigned/unverifiable is OK."""
        return not self.invalid()

    def format(self) -> str:
        lines = [f"Passport verification: {self.passport_token[:16]}..."]
        for v in self.verdicts:
            short_id = v.entry.entity_id
            lines.append(
                f"  [{v.status:12s}] {short_id}: {v.reason}")
        lines.append("")
        lines.append(
            f"  counts: "
            f"{len(self.verified())} verified, "
            f"{len(self.invalid())} invalid, "
            f"{len(self.unverifiable())} unverifiable, "
            f"{len(self.unverified())} unverified")
        return "\n".join(lines)

    @classmethod
    def verify(cls, passport: PassportV2,
               resolver: PublicKeyResolver) -> "VerificationReport":
        report = cls(passport_token=passport.identity.token)
        for entry in passport.entries:
            report.verdicts.append(
                _verify_entry(entry, passport.identity.token, resolver))
        return report


def _verify_entry(entry: PassportEntry, identity_token: str,
                   resolver: PublicKeyResolver) -> EntryVerdict:
    # 1. Plain entries are structurally valid but unverified
    if not entry.is_signed:
        return EntryVerdict(
            entry=entry, status="unverified",
            reason="unsigned (WCP/0.1 admission)")

    # 2. Subject binding — the anti-theft check
    if entry.subject_token != identity_token:
        return EntryVerdict(
            entry=entry, status="invalid",
            reason=(f"subject_token does not match passport identity "
                    f"(stolen admission?)"))

    # 3. Resolve the world's public key
    pub = resolver(entry.entity_id)
    if pub is None:
        return EntryVerdict(
            entry=entry, status="unverifiable",
            reason=f"no public key for {entry.entity_id}")

    # 4. Verify signature
    if not HAS_CRYPTO:
        return EntryVerdict(
            entry=entry, status="unverifiable",
            reason="cryptography not installed")

    ok = verify_signature(pub, entry.canonical_payload(),
                          entry.signature)
    if ok:
        return EntryVerdict(
            entry=entry, status="verified",
            reason="signature valid")
    return EntryVerdict(
        entry=entry, status="invalid",
        reason="signature INVALID")


# =====================================================================
# Client helper — add a signed admission to a passport
# =====================================================================

def add_signed_admission(passport: PassportV2,
                         adm: SignedAdmission) -> PassportV2:
    """Add a signed admission to the passport.

    Refuses if the admission's subject_token does not match the
    passport's identity token. This is a client-side guard against
    a world accidentally (or maliciously) returning an admission
    for a different identity.
    """
    if adm.subject_token != passport.identity.token:
        raise ValueError(
            f"admission is for {adm.subject_token!r}, "
            f"passport is for {passport.identity.token!r}")
    return passport.with_entry(PassportEntry.from_signed(adm))


# =====================================================================
# Serialization
# =====================================================================

def entry_to_dict(e: PassportEntry) -> Dict:
    d = {"entity_id": e.entity_id, "timestamp": e.timestamp}
    if e.is_signed:
        d["subject_token"] = e.subject_token
        d["signature"] = e.signature
    return d


def entry_from_dict(d: Dict) -> PassportEntry:
    return PassportEntry(
        entity_id=d["entity_id"],
        timestamp=d["timestamp"],
        subject_token=d.get("subject_token"),
        signature=d.get("signature"),
    )


def passport_v2_to_dict(p: PassportV2) -> Dict:
    return {
        "identity": {"token": p.identity.token, "name": p.identity.name},
        "entries": [entry_to_dict(e) for e in p.entries],
    }


def passport_v2_from_dict(d: Dict) -> PassportV2:
    return PassportV2(
        identity=Identity(
            token=d["identity"]["token"],
            name=d["identity"]["name"],
        ),
        entries=tuple(entry_from_dict(e) for e in d.get("entries", [])),
    )
