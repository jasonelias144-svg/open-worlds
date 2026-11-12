"""Ed25519 signatures, written from RFC 8032 (section 5.1), standard library
only.

An individual in the multiverse is a key: the public half is its
identity, the private half signs what it does. This module is the
signature scheme those keys use.

Checked against the RFC's own test values (section 7.1) in
tests/test_mv_ed25519.py, and in CI against the `cryptography` package.

Not hardened against timing attacks: Python's big integers take time
that depends on the numbers. That is acceptable while nothing of value
depends on these keys; a vetted library replaces this module before
anything does (docs/MULTIVERSE.md).

The curve is the twisted Edwards curve -x^2 + y^2 = 1 + d x^2 y^2 over the
field of P = 2^255 - 19. Points are kept in extended coordinates
(X, Y, Z, T) with x = X/Z, y = Y/Z and x*y = T/Z, so adding two points
needs no division.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

P = 2 ** 255 - 19                 # the field
L = 2 ** 252 + 27742317777372353535851937790883648493   # the group order
D = -121665 * pow(121666, P - 2, P) % P                 # the curve constant
SQRT_M1 = pow(2, (P - 1) // 4, P)                       # a square root of -1

Point = Tuple[int, int, int, int]
NEUTRAL: Point = (0, 1, 1, 0)


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
    """scalar times point, by doubling and adding."""
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


def _encode(point: Point) -> bytes:
    """32 bytes: y, with the low bit of x in the top bit (section 5.1.2)."""
    z_inv = _inverse(point[2])
    x = point[0] * z_inv % P
    y = point[1] * z_inv % P
    return (y | (x & 1) << 255).to_bytes(32, "little")


def _decode(data: bytes) -> Optional[Point]:
    """The point that 32 bytes encode, or None if they encode none."""
    if len(data) != 32:
        return None
    n = int.from_bytes(data, "little")
    y = n & ((1 << 255) - 1)
    x = _x_from_y(y, n >> 255)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


_BASE_Y = 4 * _inverse(5) % P
BASE: Point = (_x_from_y(_BASE_Y, 0), _BASE_Y, 1,
               _x_from_y(_BASE_Y, 0) * _BASE_Y % P)


def _hash_int(data: bytes) -> int:
    return int.from_bytes(hashlib.sha512(data).digest(), "little")


def _expand(secret: bytes) -> Tuple[int, bytes]:
    """The secret scalar and the nonce prefix (section 5.1.5)."""
    if type(secret) is not bytes or len(secret) != 32:
        raise ValueError("an Ed25519 secret key is 32 bytes")
    digest = hashlib.sha512(secret).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8      # clear the 3 low bits and the top bit
    scalar |= 1 << 254            # set the second-highest bit
    return scalar, digest[32:]


def public_key(secret: bytes) -> bytes:
    """The 32-byte public key of a 32-byte secret key."""
    scalar, _ = _expand(secret)
    return _encode(_multiply(scalar, BASE))


def sign(secret: bytes, message: bytes) -> bytes:
    """A 64-byte signature of `message` (section 5.1.6). Deterministic:
    the same key and message always give the same signature."""
    if type(message) is not bytes:
        raise ValueError("the message must be bytes")
    scalar, prefix = _expand(secret)
    public = _encode(_multiply(scalar, BASE))
    r = _hash_int(prefix + message) % L
    r_encoded = _encode(_multiply(r, BASE))
    k = _hash_int(r_encoded + public + message) % L
    s = (r + k * scalar) % L
    return r_encoded + s.to_bytes(32, "little")


def verify(public: bytes, message: bytes, signature: bytes) -> bool:
    """True only if `signature` is a valid signature of `message` by the
    holder of `public` (section 5.1.7). Anything malformed is False,
    never an error."""
    if (type(public) is not bytes or type(message) is not bytes
            or type(signature) is not bytes
            or len(public) != 32 or len(signature) != 64):
        return False
    a = _decode(public)
    r = _decode(signature[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= L:                    # reject a non-canonical s
        return False
    k = _hash_int(signature[:32] + public + message) % L
    return _same(_multiply(s, BASE), _add(r, _multiply(k, a)))
