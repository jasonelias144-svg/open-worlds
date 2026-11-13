"""
multiverse_c1.py — Component 1: The Atom of Identity.

The smallest unit of the multiverse: an individual is identified by
a (token, name) pair. The token is stable, self-issued, and opaque.
The name is display, and may change without affecting identity.

Two identities are the same iff their tokens match. There is no
registry, no authority, no trust root. Identity is *self-sovereign*.

Depends on nothing (ground floor of the Multiverse cycle).
"""

from dataclasses import dataclass, replace
import uuid


@dataclass(frozen=True)
class Identity:
    """A self-sovereign identity.

    Frozen because the token is stable — a modified identity is a
    different identity. `rename` returns a *new* Identity with the
    same token and a different name; the token is preserved.
    """
    token: str
    name: str

    def __post_init__(self):
        if not isinstance(self.token, str) or not self.token:
            raise ValueError("token must be a non-empty string")
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("name must be a non-empty string")
        if len(self.token) < 16:
            raise ValueError(
                "token must be at least 16 characters (collision resistance)"
            )


def create_identity(name: str) -> Identity:
    """Create a new self-sovereign identity.

    The token is generated locally — the individual owns it, not any
    world. Worlds verify; worlds do not create.
    """
    return Identity(token=uuid.uuid4().hex, name=name)


def same_identity(a: Identity, b: Identity) -> bool:
    """Two identities are the same iff their tokens match.

    The name is display, not key. Two individuals named "Alice" are
    different individuals. One individual renamed "Alice" → "Bob" is
    the same individual.
    """
    return a.token == b.token


def rename(identity: Identity, new_name: str) -> Identity:
    """Return a new Identity with the same token and a new name."""
    return replace(identity, name=new_name)


def to_dict(identity: Identity) -> dict:
    """Serialize for transport."""
    return {"token": identity.token, "name": identity.name}


def from_dict(d: dict) -> Identity:
    """Deserialize from transport. Does not verify — see Component 2."""
    return Identity(token=d["token"], name=d["name"])
