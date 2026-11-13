"""Ed25519 signatures: the `cryptography` package signs and verifies; this
module adds the one check on public keys that the package doesn't make.

An individual in the multiverse is a key: the public half is its
identity, the private half signs what it does (identity.py). Everything
done with a private key, and the verification equation itself, is done
by `cryptography` (which uses OpenSSL), a vetted, maintained library
(requirements.txt). Course step 2 first wrote Ed25519 here from RFC 8032,
because the project then used the standard library only; the founder
has since lifted that rule, and the hand-written signing and verifying
are gone.

What stays here is a check on public data only: whether 32 bytes are a
usable public key. `cryptography` accepts any 32 bytes as a public key,
including the eight small-order points, and for those it accepts
signatures anyone can make without a secret (R = rB, S = r; the tests
show it). So `public_key_problem` refuses them, and `verify` refuses any
key it refuses. The check is curve arithmetic on public keys, never on
secrets, so its timing reveals nothing.

The curve is the twisted Edwards curve -x^2 + y^2 = 1 + d x^2 y^2 over the
field of P = 2^255 - 19. Points are kept in extended coordinates
(X, Y, Z, T) with x = X/Z, y = Y/Z and x*y = T/Z.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

P = 2 ** 255 - 19                 # the field
L = 2 ** 252 + 27742317777372353535851937790883648493   # the group order
D = -121665 * pow(121666, P - 2, P) % P                 # the curve constant
SQRT_M1 = pow(2, (P - 1) // 4, P)                       # a square root of -1

Point = Tuple[int, int, int, int]
NEUTRAL: Point = (0, 1, 1, 0)

_RAW = (serialization.Encoding.Raw, serialization.PublicFormat.Raw)


# -- signing and verifying: the library ------------------------------------

def _private_key(secret: bytes) -> Ed25519PrivateKey:
    if type(secret) is not bytes or len(secret) != 32:
        raise ValueError("an Ed25519 secret key is 32 bytes")
    return Ed25519PrivateKey.from_private_bytes(secret)


def public_key(secret: bytes) -> bytes:
    """The 32-byte public key of a 32-byte secret key."""
    return _private_key(secret).public_key().public_bytes(*_RAW)


def sign(secret: bytes, message: bytes) -> bytes:
    """A 64-byte signature of `message` (RFC 8032, section 5.1.6).
    Deterministic: the same key and message always give the same
    signature."""
    if type(message) is not bytes:
        raise ValueError("the message must be bytes")
    return _private_key(secret).sign(message)


def verify(public: bytes, message: bytes, signature: bytes) -> bool:
    """True only if `signature` is a valid signature of `message` by the
    holder of `public`. Anything malformed is False, never an error. A
    key that `public_key_problem` refuses never verifies."""
    if (type(public) is not bytes or type(message) is not bytes
            or type(signature) is not bytes or len(signature) != 64):
        return False
    if public_key_problem(public):
        return False
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(signature, message)
    except (InvalidSignature, ValueError):
        return False
    return True


# -- the check on public keys: here ----------------------------------------

def public_key_problem(public: bytes) -> str:
    """Why 32 bytes aren't a usable public key, or "" if they are: they
    must be the standard encoding of a point on the curve that isn't one
    of the eight small-order points."""
    if type(public) is not bytes or len(public) != 32:
        return "a public key is 32 bytes"
    point = _decode(public)
    if point is None:
        return "it is not a point on the curve"
    if _small_order(point):
        return ("it is one of the eight small-order points, for which "
                "anyone can make a signature that verifies")
    return ""


def _small_order(point: Point) -> bool:
    """Whether the point is one of the eight whose order divides 8: eight
    times it is the neutral point. For such a public key A, [k]A is the
    neutral point whenever k is a multiple of A's order (always, for the
    neutral point itself), and then R = rB, S = r is a signature that
    verifies, made without any secret. Since k comes from a hash, a
    forger only has to try a few values of r."""
    return _same(_multiply(8, point), NEUTRAL)


def _inverse(x: int) -> int:
    return pow(x, P - 2, P)


def _add(a: Point, b: Point) -> Point:
    """Point addition on the curve (RFC 8032, section 5.1.4)."""
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    e1 = (y1 - x1) * (y2 - x2) % P
    e2 = (y1 + x1) * (y2 + x2) % P
    e3 = 2 * D * t1 * t2 % P
    e4 = 2 * z1 * z2 % P
    e, f, g, h = e2 - e1, e4 - e3, e4 + e3, e2 + e1
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _multiply(scalar: int, point: Point) -> Point:
    """scalar times point, by doubling and adding. Used on public points
    only."""
    result = NEUTRAL
    while scalar:
        if scalar & 1:
            result = _add(result, point)
        point = _add(point, point)
        scalar >>= 1
    return result


def _same(a: Point, b: Point) -> bool:
    """The same point, whatever the projective scale."""
    return ((a[0] * b[2] - b[0] * a[2]) % P == 0
            and (a[1] * b[2] - b[1] * a[2]) % P == 0)


def _x_from_y(y: int, odd: int) -> Optional[int]:
    """The x for a given y and sign bit (section 5.1.3), or None."""
    if y >= P:
        return None
    u = (y * y - 1) % P
    v = (D * y * y + 1) % P
    x2 = u * _inverse(v) % P
    if x2 == 0:
        return None if odd else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P:
        return None
    if x & 1 != odd:
        x = P - x
    return x


def _decode(data: bytes) -> Optional[Point]:
    """The point that 32 bytes encode, or None if they encode none, or
    encode one in a non-standard way (section 5.1.3)."""
    if len(data) != 32:
        return None
    n = int.from_bytes(data, "little")
    y = n & ((1 << 255) - 1)
    x = _x_from_y(y, n >> 255)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


def _encode(point: Point) -> bytes:
    """32 bytes: y, with the low bit of x in the top bit (section 5.1.2).
    The tests use it, with BASE, to build the forgeries the check
    refuses."""
    z_inv = _inverse(point[2])
    x = point[0] * z_inv % P
    y = point[1] * z_inv % P
    return (y | (x & 1) << 255).to_bytes(32, "little")


def _hash_int(data: bytes) -> int:
    """SHA-512 as a little-endian integer (RFC 8032's hash). Only the
    tests use it, to build the forgeries the check refuses."""
    return int.from_bytes(hashlib.sha512(data).digest(), "little")


_BASE_Y = 4 * _inverse(5) % P
BASE: Point = (_x_from_y(_BASE_Y, 0), _BASE_Y, 1,
               _x_from_y(_BASE_Y, 0) * _BASE_Y % P)
