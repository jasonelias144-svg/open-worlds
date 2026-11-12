"""Identity: who an individual is.

From the DeepSeek sketch's component 1 (record 012-04-00), unchanged in
substance. An individual is a (token, name) pair. The token is stable,
self-issued and opaque; the name is only a label and may change. Two
identities are the same exactly when their tokens match. No registry,
no authority, no trust root.

Known limit, until step 2 (docs/MULTIVERSE.md): anyone who has seen a
token can act as its owner. Step 2 makes the token a public key, and
acting needs the matching private key.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, replace

MIN_TOKEN_CHARS = 16


def token_problem(token: object) -> str:
    """Why a token is unusable, or "" if it is fine."""
    if type(token) is not str or not token:
        return "token must be non-empty plain text"
    if len(token) < MIN_TOKEN_CHARS:
        return f"token must be at least {MIN_TOKEN_CHARS} characters"
    return ""


@dataclass(frozen=True)
class Identity:
    """A self-issued identity. Frozen: a changed token is a different
    individual, so `rename` returns a new Identity with the same token."""
    token: str
    name: str

    def __post_init__(self):
        problem = token_problem(self.token)
        if problem:
            raise ValueError(problem)
        if type(self.name) is not str or not self.name:
            raise ValueError("name must be a non-empty string")


def create_identity(name: str) -> Identity:
    """A new identity. The token is made locally: the individual owns it,
    not any world. Worlds verify; they don't create."""
    return Identity(token=uuid.uuid4().hex, name=name)


def same_identity(a: Identity, b: Identity) -> bool:
    """Same token, same individual, whatever the names."""
    return a.token == b.token


def rename(identity: Identity, new_name: str) -> Identity:
    return replace(identity, name=new_name)


def to_dict(identity: Identity) -> dict:
    return {"token": identity.token, "name": identity.name}


def from_dict(d: dict) -> Identity:
    return Identity(token=d["token"], name=d["name"])
