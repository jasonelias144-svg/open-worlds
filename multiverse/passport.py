"""The passport: an identity and its record of admissions to worlds.

From the DeepSeek sketch's component 2. An admission is a world's claim
that it admitted the identity at some time. Passports are appended to,
never changed: `with_admission` returns a new passport.

Changed from the sketch: a world id no longer needs 8 characters. The
protocol never required that of a world's id, so a world with a shorter
id crashed while admitting someone.

Known limit, until step 2: admissions are not signed, so a passport's
holder could forge one. Step 2 has each world sign the stamps it gives.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .identity import Identity, same_identity


@dataclass(frozen=True)
class Admission:
    """A world's claim that it admitted an identity. `timestamp` is ISO
    8601 and unverified: it is what the world says."""
    world_id: str
    timestamp: str

    def __post_init__(self):
        if not isinstance(self.world_id, str) or not self.world_id:
            raise ValueError("world_id must be a non-empty string")
        if not isinstance(self.timestamp, str) or not self.timestamp:
            raise ValueError("timestamp must be a non-empty string")
        try:
            datetime.fromisoformat(self.timestamp)
        except ValueError:
            raise ValueError(
                f"timestamp must be ISO 8601: {self.timestamp!r}") from None


def make_admission(world_id: str,
                   timestamp: Optional[str] = None) -> Admission:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    return Admission(world_id=world_id, timestamp=timestamp)


@dataclass(frozen=True)
class Passport:
    identity: Identity
    admissions: Tuple[Admission, ...] = ()

    def with_admission(self, admission: Admission) -> "Passport":
        return Passport(self.identity, self.admissions + (admission,))

    def with_identity(self, identity: Identity) -> "Passport":
        """Rename the holder. The token must stay the same: a new token
        is a different individual, with a passport of its own."""
        if not same_identity(self.identity, identity):
            raise ValueError("with_identity requires the same token; "
                             "use a new passport for a new identity")
        return Passport(identity, self.admissions)

    def worlds_visited(self) -> List[str]:
        """World ids in order, repeats kept."""
        return [a.world_id for a in self.admissions]

    def last_admission(self) -> Optional[Admission]:
        return self.admissions[-1] if self.admissions else None

    def __len__(self) -> int:
        return len(self.admissions)


def to_dict(passport: Passport) -> dict:
    return {
        "identity": {"token": passport.identity.token,
                     "name": passport.identity.name},
        "admissions": [{"world_id": a.world_id, "timestamp": a.timestamp}
                       for a in passport.admissions],
    }


def from_dict(d: dict) -> Passport:
    """Reads a passport. Does not verify it (see the known limit)."""
    identity = Identity(token=d["identity"]["token"],
                        name=d["identity"]["name"])
    admissions = tuple(Admission(world_id=a["world_id"],
                                 timestamp=a["timestamp"])
                       for a in d.get("admissions", []))
    return Passport(identity=identity, admissions=admissions)
