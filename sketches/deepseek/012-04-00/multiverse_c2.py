"""
multiverse_c2.py — Component 2: The Passport.

The first composite in the multiverse. The passport carries an
identity and the record of admissions to worlds.

An admission is *attested* by a world — it is the world's claim
that it admitted this identity at some time. In this component,
admissions are NOT cryptographically signed. Any holder of a
passport could forge an admission. This is documented as the
honest limitation of Component 2; Component 3 will add signatures.

Depends on Component 1 (Identity).
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from multiverse_c1 import Identity, same_identity


# =====================================================================
# Atom: Admission
# =====================================================================

@dataclass(frozen=True)
class Admission:
    """A world's claim that it admitted an identity.

    Frozen because the record is *attested* — once a world writes
    an admission, the admission is that world's statement. It is
    not editable. If the world made a mistake, the correct response
    is for the world to publish a *new* statement — not to modify
    the old one.

    `world_id` — the world's own token. Like an identity token, it is
                 stable and self-issued. Worlds are self-sovereign too.
    `timestamp` — ISO 8601 UTC. *Unverified.* The world *claims* it
                 was this time. This component has no time mechanism.
    """
    world_id: str
    timestamp: str

    def __post_init__(self):
        if not isinstance(self.world_id, str) or not self.world_id:
            raise ValueError("world_id must be a non-empty string")
        if len(self.world_id) < 8:
            raise ValueError(
                "world_id must be at least 8 characters"
            )
        if not isinstance(self.timestamp, str) or not self.timestamp:
            raise ValueError("timestamp must be a non-empty string")
        # Basic ISO 8601 sanity — will be replaced by a real
        # time mechanism later
        try:
            datetime.fromisoformat(self.timestamp)
        except ValueError:
            raise ValueError(
                f"timestamp must be ISO 8601: {self.timestamp!r}"
            )


def make_admission(world_id: str,
                   timestamp: Optional[str] = None) -> Admission:
    """Construct an admission. When a world admits an identity, it
    calls this with its own world_id and (optionally) the current
    time. The world attests to the admission."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    return Admission(world_id=world_id, timestamp=timestamp)


# =====================================================================
# Composite: Passport
# =====================================================================

@dataclass(frozen=True)
class Passport:
    """An identity + the record of admissions to worlds.

    Frozen because the identity is frozen. Passports are *appended
    to*, not *modified*. The `admit` method returns a *new* passport
    with the new admission added; it does not mutate the existing one.

    This mirrors the way real passports work: a stamp added to the
    passport creates a new *state* of the passport, but the identity
    of the passport is continuous.
    """
    identity: Identity
    admissions: Tuple[Admission, ...] = ()

    def with_admission(self, admission: Admission) -> "Passport":
        """Return a new passport with the admission appended."""
        return Passport(
            identity=self.identity,
            admissions=self.admissions + (admission,),
        )

    def with_identity(self, identity: Identity) -> "Passport":
        """Return a new passport with the identity replaced.

        Only meaningful for renaming — the token must be the same,
        or the new identity is a *different* identity, not a
        modification of the existing one.
        """
        if not same_identity(self.identity, identity):
            raise ValueError(
                "with_identity requires the same token; "
                "use a new passport for a new identity"
            )
        return Passport(
            identity=identity,
            admissions=self.admissions,
        )

    def worlds_visited(self) -> List[str]:
        """The world_ids this identity has been admitted to.
        Order preserved; duplicates preserved."""
        return [a.world_id for a in self.admissions]

    def last_admission(self) -> Optional[Admission]:
        return self.admissions[-1] if self.admissions else None

    def __len__(self) -> int:
        """The number of admissions. Not the size of the passport."""
        return len(self.admissions)


# =====================================================================
# Serialization
# =====================================================================

def to_dict(passport: Passport) -> dict:
    """Serialize for transport. The passport is portable."""
    return {
        "identity": {
            "token": passport.identity.token,
            "name": passport.identity.name,
        },
        "admissions": [
            {"world_id": a.world_id, "timestamp": a.timestamp}
            for a in passport.admissions
        ],
    }


def from_dict(d: dict) -> Passport:
    """Deserialize from transport. Does NOT verify — see Component 3."""
    from multiverse_c1 import Identity
    identity = Identity(
        token=d["identity"]["token"],
        name=d["identity"]["name"],
    )
    admissions = tuple(
        Admission(world_id=a["world_id"], timestamp=a["timestamp"])
        for a in d.get("admissions", [])
    )
    return Passport(identity=identity, admissions=admissions)
