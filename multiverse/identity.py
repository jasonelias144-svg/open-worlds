"""Identity: who an individual is, and how it proves it.

From the DeepSeek sketch's component 1, with the change course step 2
makes: an individual is a key. Its identity is (token, name), where the
token is its Ed25519 public key, written as 64 hexadecimal characters,
and the name is only a label that may change. The private key stays with
the individual (an `Individual`), and signs what it sends: a petition,
an act, a leave. A world checks the signature against the token, so
nobody who has merely seen a token can act as its owner.

No registry, no authority, no trust root: anyone can make a key.

Changed from the sketch: the sketch's token was a random string, and
anyone who saw it could act as its owner; signatures came at its
component 13, and only for worlds' answers. Here identity is the key
from the start.
"""
from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass, replace
from typing import Dict, Optional, Tuple

from . import ed25519

TOKEN_CHARS = 64
HEX = set("0123456789abcdef")


def token_problem(token: object) -> str:
    """Why a token is unusable, or "" if it is fine. A token is an Ed25519
    public key: 64 lowercase hexadecimal characters that encode a point
    on the curve, and not one of the eight weak points anyone can sign
    for (ed25519.public_key_problem)."""
    if type(token) is not str or not token:
        return "token must be non-empty plain text"
    if len(token) != TOKEN_CHARS or not set(token) <= HEX:
        return (f"token must be a public key: {TOKEN_CHARS} lowercase "
                "hexadecimal characters")
    problem = ed25519.public_key_problem(bytes.fromhex(token))
    if problem:
        return f"token is not a usable public key: {problem}"
    return ""


@dataclass(frozen=True)
class Identity:
    """Who an individual is: its public key and a name. Frozen: a changed
    token is a different individual, so `rename` keeps the token."""
    token: str
    name: str

    def __post_init__(self):
        problem = token_problem(self.token)
        if problem:
            raise ValueError(problem)
        if type(self.name) is not str or not self.name:
            raise ValueError("name must be non-empty plain text")


def same_identity(a: Identity, b: Identity) -> bool:
    """Same token, same individual, whatever the names."""
    return a.token == b.token


def rename(identity: Identity, new_name: str) -> Identity:
    return replace(identity, name=new_name)


def to_dict(identity: Identity) -> dict:
    return {"token": identity.token, "name": identity.name}


def from_dict(d: dict) -> Identity:
    return Identity(token=d["token"], name=d["name"])


# -- signing ---------------------------------------------------------------

def canonical(document: Dict) -> bytes:
    """The exact bytes that are signed: JSON with sorted keys, no spaces,
    UTF-8. Raises ValueError for anything JSON can't say exactly (such as
    NaN), so such a document can't be signed or verified."""
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def signature_valid(token: str, document: Dict, signature: object) -> bool:
    """Whether `signature` (128 hexadecimal characters) is the token's
    signature of `document`. Anything malformed is False."""
    if (token_problem(token) or type(signature) is not str
            or len(signature) != 128 or not set(signature) <= HEX):
        return False
    try:
        message = canonical(document)
    except (TypeError, ValueError):
        return False
    return ed25519.verify(bytes.fromhex(token), message,
                          bytes.fromhex(signature))


class Individual:
    """An individual with its private key. The key never leaves this
    object: what goes out is the identity (public) and signatures.

    Each request to a world carries a number, `seq`, that must grow with
    every request to that world, so a request can't be replayed: a
    captured petition can't bring someone back, and a captured leave
    can't push someone out. The numbers come from the clock (in
    microseconds), so they keep growing even after a restart, as long
    as the clock hasn't gone back. If it has, the worlds refuse the new
    requests as out of order until the clock catches up. (A request
    signed by hand with a huge `seq` locks its own key out of that
    world the same way.)"""

    def __init__(self, name: str, secret: Optional[bytes] = None):
        self._secret = secrets.token_bytes(32) if secret is None else secret
        self.identity = Identity(
            token=ed25519.public_key(self._secret).hex(), name=name)
        self._last_seq: Dict[str, int] = {}

    def __repr__(self) -> str:
        return f"Individual({self.identity.name!r}, {self.token[:12]}…)"

    @property
    def token(self) -> str:
        return self.identity.token

    @property
    def name(self) -> str:
        return self.identity.name

    def sign(self, document: Dict) -> str:
        return ed25519.sign(self._secret, canonical(document)).hex()

    def next_seq(self, world_id: str) -> int:
        seq = max(self._last_seq.get(world_id, 0) + 1,
                  time.time_ns() // 1000)
        self._last_seq[world_id] = seq
        return seq

    # The three signed requests. Building them here keeps the signed
    # documents and the messages in one place (protocol.py).

    def petition(self, world_id: str,
                 passport_admissions: Tuple[Tuple[str, str], ...] = (),
                 message: str = "", target: Optional[str] = None):
        from .protocol import Petition, petition_document
        seq = self.next_seq(world_id)
        unsigned = Petition(self.token, self.name,
                            tuple(tuple(p) for p in passport_admissions),
                            message, target, seq)
        return replace(unsigned, signature=self.sign(
            petition_document(world_id, unsigned)))

    def act(self, world_id: str, act_type: str, payload: Dict):
        from .protocol import Act, act_document
        seq = self.next_seq(world_id)
        unsigned = Act(self.token, act_type, payload, seq)
        return replace(unsigned, signature=self.sign(
            act_document(world_id, unsigned)))

    def leave(self, world_id: str):
        from .protocol import Leave, leave_document
        seq = self.next_seq(world_id)
        unsigned = Leave(self.token, seq)
        return replace(unsigned, signature=self.sign(
            leave_document(world_id, unsigned)))


def create_individual(name: str) -> Individual:
    """A new individual with a fresh key. The key is made here, by the
    individual: worlds verify; they don't create."""
    return Individual(name)
