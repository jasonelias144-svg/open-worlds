"""Sealing: a message that only one key can open (HPKE, RFC 9180).

Decided by the technical lead on 2026-11-13 (docs/research/FORMATS.md,
"Sealing"):

- **The suite.** HPKE's base mode with DHKEM(X25519, HKDF-SHA256),
  HKDF-SHA256 and ChaCha20Poly1305, all from the `cryptography` package.
  No encryption code of our own.
- **The box.** A box is `enc || ct`, the encapsulated key followed by the
  ciphertext. RFC 9180's single-shot Seal returns these two, and
  `cryptography` writes them this way. There is no associated data.
- **The label.** HPKE's `info` carries a label that names the purpose and
  its version, such as `open-worlds/world-key/v1`. A box made for one
  purpose doesn't open as another. The one opening a box names the label
  it expects: nothing is read from the box to choose it. A label not on
  the list is refused before anything is tried.
- **The sealing key** is an X25519 key, kept apart from the identity's
  Ed25519 signing key. A key that can't be sealed to safely is refused:
  one of small order, or one not written in its one canonical form
  (check_public).

What is sealed is always signed first, and names its recipient, who
checks that it is theirs. That check needs the record's format, so it
lives with the sealed records (formats/sealed.py), not here.
"""
from __future__ import annotations

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.hpke import AEAD, KDF, KEM, Suite

SUITE = Suite(KEM.X25519, KDF.HKDF_SHA256, AEAD.CHACHA20_POLY1305)
ENC_LENGTH = 32    # an X25519 public key (RFC 9180, 7.1, Nenc)
TAG_LENGTH = 16    # ChaCha20Poly1305's tag (RFC 9180, 7.3, Nt)

# Every label in use. A new purpose, or a new version of one, is added
# here by a reviewed change, never made up where a box is sealed.
LABELS = frozenset({"open-worlds/journal/v1", "open-worlds/world-key/v1"})

_P = 2**255 - 19
# Any X25519 secret will do: every secret is a multiple of 8 once clamped,
# so it takes a key of small order (and only such a key) to zero.
_PROBE = x25519.X25519PrivateKey.from_private_bytes(b"\x01" * 32)


class SealError(ValueError):
    """A box that can't be made or opened as asked."""


def _label(label: str) -> bytes:
    if type(label) is not str or label not in LABELS:
        raise SealError(f"{label!r} isn't a sealing label in use")
    return label.encode("ascii")


def check_public(public: bytes) -> None:
    """Refuse a sealing key that isn't safe to seal to.

    It must be 32 bytes in its one canonical form: as a number, below
    2^255 - 19. A larger number is another spelling of a smaller key, as
    is one with the top bit set, which RFC 7748 ignores; the one test
    refuses both. And it must not be of small order: sealing to such a key
    would give a secret anyone can work out. HPKE requires the one opening
    a box to refuse that (RFC 9180, 7.1.4), and both libraries refuse it
    when sealing too; this refuses the key itself.
    """
    if type(public) is not bytes or len(public) != 32:
        raise SealError("a sealing key must be 32 bytes")
    if int.from_bytes(public, "little") >= _P:
        raise SealError("a sealing key must be below 2^255 - 19")
    try:
        _PROBE.exchange(x25519.X25519PublicKey.from_public_bytes(public))
    except ValueError:
        raise SealError("a sealing key of small order") from None


def new_secret() -> bytes:
    """A fresh X25519 secret key (32 bytes) for sealing."""
    return x25519.X25519PrivateKey.generate().private_bytes_raw()


def public_from_secret(secret: bytes) -> bytes:
    """The X25519 public key (32 bytes) of a secret key."""
    if type(secret) is not bytes or len(secret) != 32:
        raise SealError("a secret key must be 32 bytes")
    key = x25519.X25519PrivateKey.from_private_bytes(secret)
    return key.public_key().public_bytes_raw()


def seal(message: bytes, public: bytes, label: str) -> bytes:
    """Seal `message` so that only the holder of `public`'s secret can open
    it, for the purpose `label` names. Each call gives a different box."""
    info = _label(label)
    if type(message) is not bytes:
        raise SealError("a message must be bytes")
    check_public(public)
    key = x25519.X25519PublicKey.from_public_bytes(public)
    return SUITE.encrypt(message, key, info=info)


def open_box(box: bytes, secret: bytes, label: str) -> bytes:
    """The message in `box`, if it was sealed to `secret`'s key with
    exactly `label`. Otherwise SealError, which never says why: a wrong
    key, a wrong label and a changed box all look the same."""
    info = _label(label)
    if type(box) is not bytes or len(box) < ENC_LENGTH + TAG_LENGTH:
        raise SealError("too short to be a box")
    if type(secret) is not bytes or len(secret) != 32:
        raise SealError("a secret key must be 32 bytes")
    key = x25519.X25519PrivateKey.from_private_bytes(secret)
    try:
        return SUITE.decrypt(box, key, info=info)
    except (InvalidTag, ValueError):
        raise SealError("the box doesn't open") from None
