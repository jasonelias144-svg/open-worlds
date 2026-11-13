"""Keeping keys safely (course step 6, first part).

An individual is its key, and so is a world (identity.py, protocol.py).
A key that lives only in memory is lost when the process ends, and with
it the individual's history: its passport can't be extended, and nobody
can prove to be it again. A world that restarts with a new key is a new
world, and its old stamps no longer link to it. So:

- **A key is saved to a file, encrypted with a passphrase** (`save_key`,
  `load_signer`, `load_individual`). The file is PKCS12, the standard
  container `openssl` also reads, holding only the key: PBES2 with
  PBKDF2-HMAC-SHA256 at 600,000 iterations (the current OWASP figure)
  and AES-256-CBC, from the `cryptography` package. PKCS8's "best
  available" encryption uses only 2,048 iterations, which a passphrase
  can't afford. The file is written readable by its owner only, and
  never over an existing file unless asked: losing a key file loses the
  key.
- **A backup is another saved copy,** somewhere else. The passphrase is
  the only way in: nobody, open-worlds included, can recover it.
- **A world keeps the numbers it has seen** (`save_seen`, `load_seen`),
  so that after a restart an old request can't be replayed to it
  (protocol.request_problem). The file is public data, signed by the
  world's key, so a changed file is refused.

Replacing a key while the old one still works, and what happens when a
key is lost, come next in this step (docs/COURSE.md).
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Dict, Union

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from cryptography.hazmat.primitives.serialization import pkcs12

from .identity import Individual, Signer, signature_valid, token_problem
from .protocol import PROTOCOL_VERSION

ROUNDS = 600_000
FRIENDLY_NAME = b"open-worlds key"
Passphrase = Union[str, bytes]


def _passphrase(passphrase: object) -> bytes:
    if type(passphrase) is str:
        passphrase = passphrase.encode("utf-8")
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
            os.link(tmp, path)          # fails if `path` exists
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
    encryption = (serialization.PrivateFormat.PKCS12.encryption_builder()
                  .kdf_rounds(ROUNDS)
                  .key_cert_algorithm(
                      pkcs12.PBES.PBESv2SHA256AndAES256CBC)
                  .build(_passphrase(passphrase)))
    key = Ed25519PrivateKey.from_private_bytes(signer._secret)
    data = pkcs12.serialize_key_and_certificates(
        FRIENDLY_NAME, key, None, None, encryption)
    _write_new(path, data, overwrite)


def _load_secret(path: str, passphrase: Passphrase) -> bytes:
    passphrase = _passphrase(passphrase)
    with open(path, "rb") as f:
        data = f.read()
    try:
        key, _, _ = pkcs12.load_key_and_certificates(data, passphrase)
    except ValueError:
        raise ValueError("the passphrase is wrong, or this isn't a key "
                         "file") from None
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("the file doesn't hold an Ed25519 key")
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
