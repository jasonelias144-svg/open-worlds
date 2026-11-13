"""Keeping keys safely (course step 6, first part).

An individual is its key, and so is a world (identity.py, protocol.py).
A key that lives only in memory is lost when the process ends, and with
it the individual's history: its passport can't be extended, and nobody
can prove to be it again. A world that restarts with a new key is a new
world, and its old stamps no longer link to it. So:

- **A key is saved to a file, encrypted with a passphrase** (`save_key`,
  `load_signer`, `load_individual`). The file is in OpenSSH's private-key
  format, which `ssh-keygen` also reads, written by the `cryptography`
  package: the passphrase goes through bcrypt-pbkdf with 64 rounds
  (about half a second per try on an ordinary computer), and the key is
  encrypted with AES-256-CTR. A wrong passphrase is found out only after
  the whole derivation: the file holds no cheaper check. (PKCS12 was
  tried first, but its integrity check takes the same passphrase through
  only 2,048 rounds of PBKDF2, which a guesser can use instead of the
  key's; the independent review of #23 found it.) Half a second is the
  owner's cost, on one core: someone with many cores tries many
  passphrases at once, so the passphrase's own strength matters most.
  Text passphrases are normalised to Unicode NFC first, so the same words
  typed on different systems open the same file.
- **A changed file is refused.** AES-CTR has no check of its own, so a
  flipped bit of the encrypted secret would load as another key; the key
  loaded is checked against the public key the file holds in the clear.
- **The file is written readable by its owner only,** whole or not at
  all, and never over an existing file unless asked: losing a key file
  loses the key.
- **A backup is another saved copy,** somewhere else. The passphrase is
  the only way in: nobody, open-worlds included, can recover it.
- **A world keeps the numbers it has seen** (`save_seen`, `load_seen`),
  so that after a restart the requests it had seen by the last save
  can't be replayed to it (protocol.request_problem). The file is public
  data, signed by the world's key, so a changed file is refused. An
  older copy is still validly signed, though: restored from it, a world
  would accept, once, a request it saw after that copy was saved. Keep
  the file where only the world's operator can write, and save it as
  often as that matters.

Replacing a key while the old one still works, and what happens when a
key is lost, come next in this step (docs/COURSE.md).
"""
from __future__ import annotations

import base64
import binascii
import errno
import json
import os
import struct
import tempfile
import unicodedata
from typing import Dict, Union

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

from .identity import Individual, Signer, signature_valid, token_problem
from .protocol import PROTOCOL_VERSION

# bcrypt-pbkdf rounds. Each round costs the same, so the time per try
# grows with them: 64 took about 0.6 s here (ssh-keygen's default, 16,
# about 0.15 s; the bcrypt package warns below 50).
ROUNDS = 64
Passphrase = Union[str, bytes]


def _passphrase(passphrase: object) -> bytes:
    if type(passphrase) is str:
        passphrase = unicodedata.normalize("NFC", passphrase).encode("utf-8")
    if type(passphrase) is not bytes or not passphrase:
        raise ValueError("a passphrase must be non-empty text or bytes")
    return passphrase


def _write_new(path: str, data: bytes, overwrite: bool) -> None:
    """Write `data` to `path`, readable by its owner only. The bytes go to
    a new file in the same folder first, which then takes the name at
    once: a reader never sees half a file. Unless `overwrite`, an
    existing file is never replaced (FileExistsError)."""
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".open-worlds-", dir=folder)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if overwrite:
            os.replace(tmp, path)
        else:
            try:
                os.link(tmp, path)      # fails if `path` exists
            except FileExistsError:
                raise
            except OSError as e:
                if e.errno in (errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP,
                               errno.EXDEV, errno.EMLINK):
                    raise OSError(
                        e.errno, "this filesystem can't make the hard link "
                        "that saving without overwriting needs; save "
                        "elsewhere, or pass overwrite=True") from None
                raise
            os.unlink(tmp)
        tmp = None
        dir_fd = os.open(folder, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)


# -- keys ------------------------------------------------------------------

def save_key(signer: Signer, path: str, passphrase: Passphrase, *,
             overwrite: bool = False) -> None:
    """Save `signer`'s key to `path`, encrypted with `passphrase`."""
    if not isinstance(signer, Signer):
        raise ValueError("only a Signer's key can be saved")
    encryption = (serialization.PrivateFormat.OpenSSH.encryption_builder()
                  .kdf_rounds(ROUNDS).build(_passphrase(passphrase)))
    key = Ed25519PrivateKey.from_private_bytes(signer._secret)
    data = key.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.OpenSSH, encryption)
    _write_new(path, data, overwrite)


def _public_key_in_the_clear(data: bytes) -> bytes:
    """The Ed25519 public key an OpenSSH private-key file holds outside
    its encrypted part (PROTOCOL.key in OpenSSH's sources): after the
    magic, the cipher, KDF and KDF-options strings, and the key count,
    a string holding the key type and the 32-byte key."""
    lines = data.strip().splitlines()
    try:
        raw = base64.b64decode(b"".join(lines[1:-1]), validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("this key file has been changed") from None
    magic = b"openssh-key-v1\0"
    at = len(magic)

    def string(blob: bytes, at: int):
        if at + 4 > len(blob):
            raise ValueError("this key file has been changed")
        n, = struct.unpack(">I", blob[at:at + 4])
        if at + 4 + n > len(blob):
            raise ValueError("this key file has been changed")
        return blob[at + 4:at + 4 + n], at + 4 + n

    if not raw.startswith(magic):
        raise ValueError("this key file has been changed")
    for _ in range(3):                  # cipher, KDF, KDF options
        _, at = string(raw, at)
    at += 4                             # the number of keys
    blob, _ = string(raw, at)
    kind, at = string(blob, 0)
    public, at = string(blob, at)
    if kind != b"ssh-ed25519" or len(public) != 32 or at != len(blob):
        raise ValueError("this key file has been changed")
    return public


def _load_secret(path: str, passphrase: Passphrase) -> bytes:
    """The key in a file save_key wrote. A file someone else made could
    ask for any number of rounds and so take long to open: open only
    your own."""
    passphrase = _passphrase(passphrase)
    with open(path, "rb") as f:
        data = f.read()
    try:
        key = serialization.load_ssh_private_key(data, passphrase)
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise ValueError("the passphrase is wrong, or this isn't an "
                         "encrypted key file, or it has been changed"
                         ) from None
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("the file doesn't hold an Ed25519 key")
    # The encryption (AES-CTR) has no check of its own: a changed bit of
    # the secret decrypts to another secret. The public key in the clear
    # must be the one the secret makes.
    if (key.public_key().public_bytes_raw()
            != _public_key_in_the_clear(data)):
        raise ValueError("this key file has been changed: its secret "
                         "doesn't match its public key")
    return key.private_bytes_raw()


def load_signer(path: str, passphrase: Passphrase) -> Signer:
    """A world's key (or any signer's), from a file save_key wrote. Give
    it to the world when building it: `PoetryWorld(..., key=signer)`."""
    return Signer(_load_secret(path, passphrase))


def load_individual(path: str, passphrase: Passphrase,
                    name: str) -> Individual:
    """An individual, from its key file. The name is only a label, and
    isn't kept in the file."""
    return Individual(name, _load_secret(path, passphrase))


# -- a world's seen numbers ------------------------------------------------

def seen_document(world_id: str, world_key: str,
                  seen: Dict[str, int]) -> Dict:
    return {"wcp": PROTOCOL_VERSION, "kind": "seen", "world": world_id,
            "world_key": world_key, "seen": dict(sorted(seen.items()))}


def save_seen(world, path: str) -> None:
    """Save the request numbers `world` has seen, signed by its key, so a
    restarted world can take them back (`load_seen`, then
    `world.restore_seen`). Replaces the file: the latest numbers are the
    ones that matter."""
    m = world.manifest()
    document = seen_document(m.entity_id, m.world_key, world.seen_numbers())
    signed = dict(document, signature=world._key.sign(document))
    _write_new(path, json.dumps(signed, sort_keys=True).encode("utf-8"),
               overwrite=True)


def load_seen(path: str, world) -> Dict[str, int]:
    """The numbers saved for `world`, if the file is signed by its key and
    names it. ValueError otherwise."""
    with open(path, "rb") as f:
        try:
            signed = json.loads(f.read().decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise ValueError("not a file of seen numbers") from None
    if type(signed) is not dict or type(signed.get("seen")) is not dict:
        raise ValueError("not a file of seen numbers")
    m = world.manifest()
    document = {k: v for k, v in signed.items() if k != "signature"}
    # The protocol version it was saved under is part of what was signed,
    # and isn't required to be today's.
    if (set(document) != {"wcp", "kind", "world", "world_key", "seen"}
            or document["kind"] != "seen"
            or document["world"] != m.entity_id
            or document["world_key"] != m.world_key
            or not signature_valid(m.world_key, document,
                                   signed.get("signature"))):
        raise ValueError("these numbers aren't signed by this world's key "
                         "for this world")
    for token, seq in document["seen"].items():
        if token_problem(token) or type(seq) is not int or seq < 1:
            raise ValueError("a seen number must be a whole number >= 1 "
                             "for a usable key")
    return dict(document["seen"])
