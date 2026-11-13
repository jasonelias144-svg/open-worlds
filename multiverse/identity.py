"""Identity: who an individual is, and how it proves it.

From the DeepSeek sketch's component 1, with the change course step 2
makes: an individual is a key. Its identity is (token, name), where the
token is its Ed25519 public key, written as 64 hexadecimal characters,
and the name is only a label that may change. The private key stays with
the individual (an `Individual`), and signs what it sends: a petition,
an act, a leave. A world checks the signature against the token, so
nobody who has merely seen a token can act as its owner. Since course
step 3, worlds are keys too (each a `Signer`), and sign the stamps they
give.

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


class Signer:
    """A key pair: the public half (`token`) says who it is, and the
    private half, which never leaves this object, signs. Individuals and
    worlds are both signers (course step 3)."""

    def __init__(self, secret: Optional[bytes] = None):
        self._secret = secrets.token_bytes(32) if secret is None else secret
        self._token = ed25519.public_key(self._secret).hex()

    @property
    def token(self) -> str:
        return self._token

    def sign(self, document: Dict) -> str:
        return ed25519.sign(self._secret, canonical(document)).hex()


class Individual(Signer):
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
    world the same way.)

    Requests are addressed to a world by its manifest: its id and its
    key (course step 3), so a request signed for one world can't be
    taken to another, even one that copies its id. The numbers are kept
    per world key."""

    def __init__(self, name: str, secret: Optional[bytes] = None):
        super().__init__(secret)
        self.identity = Identity(token=self._token, name=name)
        self._last_seq: Dict[str, int] = {}

    def __repr__(self) -> str:
        return f"Individual({self.identity.name!r}, {self.token[:12]}…)"

    @property
    def name(self) -> str:
        return self.identity.name

    def next_seq(self, world_key: str) -> int:
        seq = max(self._last_seq.get(world_key, 0) + 1,
                  time.time_ns() // 1000)
        self._last_seq[world_key] = seq
        return seq

    # The three signed requests. Building them here keeps the signed
    # documents and the messages in one place (protocol.py). `world` is
    # the world's Manifest.

    def petition(self, world, passport: Tuple[Dict, ...] = (),
                 message: str = "", target: Optional[str] = None):
        """A signed petition. `passport` is the petitioner's passport as
        plain entries (passport.Passport.entries())."""
        from .protocol import Petition, petition_document
        seq = self.next_seq(world.world_key)
        unsigned = Petition(self.token, self.name, tuple(passport),
                            message, target, seq)
        return replace(unsigned, signature=self.sign(
            petition_document(world.entity_id, world.world_key, unsigned)))

    def act(self, world, act_type: str, payload: Dict):
        from .protocol import Act, act_document
        seq = self.next_seq(world.world_key)
        unsigned = Act(self.token, act_type, payload, seq)
        return replace(unsigned, signature=self.sign(
            act_document(world.entity_id, world.world_key, unsigned)))

    def leave(self, world, closes: str = ""):
        """A signed leave. `closes` is the fingerprint of the arrival
        stamp it ends (passport.py), if the individual has one: with it,
        the signed leave is the individual's own record of leaving,
        whether or not the world stamps the departure."""
        from .protocol import Leave, leave_document
        seq = self.next_seq(world.world_key)
        unsigned = Leave(self.token, seq, closes=closes)
        return replace(unsigned, signature=self.sign(
            leave_document(world.entity_id, world.world_key, unsigned)))


def create_individual(name: str) -> Individual:
    """A new individual with a fresh key. The key is made here, by the
    individual: worlds verify; they don't create."""
    return Individual(name)
