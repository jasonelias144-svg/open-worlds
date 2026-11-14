"""Keys written as Multikey, and Ed25519 keys as did:key.

A Multikey is a key with a two-byte prefix saying what it is (0xed 0x01
for an Ed25519 public key, 0x80 0x26 for its secret; 0xec 0x01 and
0x82 0x26 for an X25519 sealing key and its secret), written in
base58-btc with a leading `z`. A did:key is `did:key:` and the public
Multikey; its one verification method is the did:key, `#`, and the
Multikey again. These are the names W3C's `eddsa-jcs-2022` test vectors
use, and docs/research/FORMATS.md ("Identifiers") proposes them for every
public key in this project.

Base58-btc is an encoding, not cryptography, so it is written here, and
checked against W3C's vectors and against the Rust crate `bs58`.
"""
from __future__ import annotations

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_INDEX = {c: i for i, c in enumerate(ALPHABET)}

ED25519_PUBLIC = b"\xed\x01"
ED25519_SECRET = b"\x80\x26"
# X25519, for sealing (formats/seal.py): multicodec x25519-pub (0xec) and
# x25519-priv (0x1302), as unsigned varints.
X25519_PUBLIC = b"\xec\x01"
X25519_SECRET = b"\x82\x26"
DID_KEY = "did:key:"


class KeyFormatError(ValueError):
    """Text that isn't the key it claims to be."""


def base58btc_encode(data: bytes) -> str:
    """`data` in base58-btc (the Bitcoin alphabet), leading zero bytes
    written as `1`."""
    zeros = len(data) - len(data.lstrip(b"\0"))
    n = int.from_bytes(data, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = ALPHABET[r] + out
    return "1" * zeros + out


def base58btc_decode(text: str) -> bytes:
    """The bytes `text` encodes in base58-btc."""
    n = 0
    for c in text:
        if c not in _INDEX:
            raise KeyFormatError(f"{c!r} isn't base58-btc")
        n = n * 58 + _INDEX[c]
    zeros = len(text) - len(text.lstrip("1"))
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\0" * zeros + body


def _encode(prefix: bytes, key: bytes) -> str:
    if type(key) is not bytes or len(key) != 32:
        raise KeyFormatError("a key is 32 bytes")
    return "z" + base58btc_encode(prefix + key)


def _decode(prefix: bytes, text: str) -> bytes:
    if type(text) is not str or not text.startswith("z"):
        raise KeyFormatError("a Multikey starts with z (base58-btc)")
    raw = base58btc_decode(text[1:])
    if len(raw) != 34 or raw[:2] != prefix:
        raise KeyFormatError("not a key of the expected kind")
    # Only one text may name a key: refuse any other spelling of it.
    if _encode(prefix, raw[2:]) != text:
        raise KeyFormatError("not the key's one written form")
    return raw[2:]


def public_multikey(public: bytes) -> str:
    """The Multikey of a 32-byte Ed25519 public key (z6Mk...)."""
    return _encode(ED25519_PUBLIC, public)


def public_from_multikey(text: str) -> bytes:
    """The 32-byte Ed25519 public key a Multikey names."""
    return _decode(ED25519_PUBLIC, text)


def secret_multikey(secret: bytes) -> str:
    """The Multikey of a 32-byte Ed25519 secret key (z3u2...). Only for
    test vectors: real secrets are never written down in the open."""
    return _encode(ED25519_SECRET, secret)


def secret_from_multikey(text: str) -> bytes:
    """The 32-byte Ed25519 secret key a secret Multikey holds."""
    return _decode(ED25519_SECRET, text)


def sealing_multikey(public: bytes) -> str:
    """The Multikey of a 32-byte X25519 public key, for sealing (z6LS...).
    Whether the key is fit to seal to is formats.seal.check_public's to
    say."""
    return _encode(X25519_PUBLIC, public)


def sealing_from_multikey(text: str) -> bytes:
    """The 32-byte X25519 public key a sealing Multikey names."""
    return _decode(X25519_PUBLIC, text)


def sealing_secret_multikey(secret: bytes) -> str:
    """The Multikey of a 32-byte X25519 secret key. Only for test
    vectors, like secret_multikey."""
    return _encode(X25519_SECRET, secret)


def sealing_secret_from_multikey(text: str) -> bytes:
    """The 32-byte X25519 secret key a secret sealing Multikey holds."""
    return _decode(X25519_SECRET, text)


def did_key(public: bytes) -> str:
    """did:key:z6Mk... for a 32-byte Ed25519 public key."""
    return DID_KEY + public_multikey(public)


def verification_method(public: bytes) -> str:
    """The did:key's one verification method: did:key:z6Mk...#z6Mk..."""
    key = public_multikey(public)
    return f"{DID_KEY}{key}#{key}"


def public_from_verification_method(text: str) -> bytes:
    """The public key a did:key verification method names. Only did:key
    is read: its key is in the identifier, so nothing is looked up."""
    if type(text) is not str or not text.startswith(DID_KEY):
        raise KeyFormatError("only did:key verification methods are read")
    identifier, sep, fragment = text[len(DID_KEY):].partition("#")
    if not sep or fragment != identifier:
        raise KeyFormatError("a did:key method is did:key:K#K")
    return public_from_multikey(identifier)
