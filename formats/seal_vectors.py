"""Test vectors for sealing (formats/seal.py), in
vectors/formats/hpke-base-v1.json, which rust/formats reads too.

    python3 -m formats.seal_vectors     rewrite the file from this code

It holds:

- RFC 9180's own example for this suite (Appendix A.2.1, sequence 0),
  which both languages check;
- recipients, as test keys (public to everyone, never for anything real);
- boxes that open, some made by Python and some by Rust;
- boxes, labels and keys that must be refused.

Sealing is random, so a box can't be made again the same. This code keeps
each box already in the file if it still opens as stated, and seals a new
one only for a box that is missing. Boxes made by Rust are kept as they
were made: rust/formats/tests/seal.rs makes each again, byte for byte,
from its `ikmE`, and this code checks that each opens. If one is missing,
that Rust test prints it, to be pasted into the file.
tests/test_formats_seal.py checks that the file is still exactly what
this code writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from multiverse import ed25519

from . import seal
from .multikey import (public_multikey, sealing_multikey,
                       sealing_secret_multikey)

FILE = (Path(__file__).resolve().parent.parent
        / "vectors" / "formats" / "hpke-base-v1.json")
LABEL = "open-worlds/world-key/v1"
_P = 2**255 - 19

# RFC 9180, Appendix A.2.1: DHKEM(X25519, HKDF-SHA256), HKDF-SHA256,
# ChaCha20Poly1305, base mode, and its encryption with sequence number 0.
# The ciphertext is a single-shot Seal: with sequence number 0, the nonce
# is base_nonce itself.
RFC9180 = {
    "source": "RFC 9180, Appendix A.2.1 and A.2.1.1 (sequence number 0)",
    "mode": 0, "kem_id": 32, "kdf_id": 1, "aead_id": 3,
    "info": "4f6465206f6e2061204772656369616e2055726e",
    "ikmE": "909a9b35d3dc4713a5e72a4da274b55d3d3821a37e5d099e74a647db583a904b",
    "pkEm": "1afa08d3dec047a643885163f1180476fa7ddb54c6a8029ea33f95796bf2ac4a",
    "skRm": "8057991eef8f1f1af18f4a9491d16a1ce333f695d4db8e38da75975c4478e0fb",
    "pkRm": "4310ee97d88cc1f088a5576c77ab0cf5c3ac797f3d95139c6c84b5429c59662a",
    "enc": "1afa08d3dec047a643885163f1180476fa7ddb54c6a8029ea33f95796bf2ac4a",
    "pt": "4265617574792069732074727574682c20747275746820626561757479",
    "aad": "436f756e742d30",
    "ct": ("1c5250d8034ec2b784ba2cfd69dbdb8af406cfe3ff938e131f0def8c8b60b4db"
           "21993c62ce81883d2dd1b51a28"),
}

RECIPIENTS = ["the earner", "someone else"]

MESSAGES = {
    "a short message": b"a world-key, signed by the Ur-world",
    "an empty message": b"",
    "every byte value": bytes(range(256)),
}

# Made by rust/formats (tests/seal.rs, `boxes_made_by_rust_are_made_again`),
# sealing to "the earner" with a fixed ikmE in place of fresh randomness.
RUST_MADE: List[Dict[str, str]] = [
    {
        "name": "made by Rust: a short message",
        "message": "a short message",
        "ikmE": hashlib.sha256(b"open-worlds/seal-vectors/rust/1").hexdigest(),
    },
    {
        "name": "made by Rust: an empty message",
        "message": "an empty message",
        "ikmE": hashlib.sha256(b"open-worlds/seal-vectors/rust/2").hexdigest(),
    },
]

# Points of small order: sealing to one, or a box whose enc is one, gives
# a secret anyone can work out.
SMALL_ORDER = {
    "0, of order 2": "00" * 32,
    "1, of order 4": "01" + "00" * 31,
    "of order 8": ("e0eb7a7c3b41b8ae1656e3faf19fc46a"
                   "da098deb9c32b1fd866205165f49b800"),
    "of order 8, the other": ("5f9c95bca3508c24b1d0b1559c83ef5b"
                              "04445cc4581c8e86d8224eddd09f1157"),
    "2^255 - 20, of order 4 on the twist":
        (_P - 1).to_bytes(32, "little").hex(),
}


def _secret(name: str) -> bytes:
    return hashlib.sha256(
        f"open-worlds sealing test key: {name}; never for anything real"
        .encode()).digest()


def _public(name: str) -> bytes:
    return seal.public_from_secret(_secret(name))


def _opens(entry: Optional[Dict[str, Any]], secret: bytes, label: str,
           message: bytes) -> bool:
    if not entry or not isinstance(entry.get("box"), str):
        return False
    try:
        return seal.open_box(bytes.fromhex(entry["box"]), secret,
                             label) == message
    except (ValueError, seal.SealError):
        return False


def _raw_seal(message: bytes, public: bytes, info: bytes) -> bytes:
    """Seal under any `info`, for boxes made with a label not in use."""
    from cryptography.hazmat.primitives.asymmetric import x25519
    key = x25519.X25519PublicKey.from_public_bytes(public)
    return seal.SUITE.encrypt(message, key, info=info)


def _kept_or_new(old: Dict[str, Dict[str, Any]], name: str, make,
                 still_good) -> str:
    entry = old.get(name)
    if entry and still_good(entry):
        return entry["box"]
    return make().hex()


def _flip(data: bytes, index: int, mask: int = 0x01) -> bytes:
    out = bytearray(data)
    out[index] ^= mask
    return bytes(out)


def vectors(old: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    old = old or {}
    old_opens = {e["name"]: e for e in old.get("opens", [])}
    old_refused = {e["name"]: e for e in old.get("refused", [])}
    earner = _secret("the earner")
    earner_public = _public("the earner")

    opens: List[Dict[str, Any]] = []
    for name, message in MESSAGES.items():
        entry_name = f"made by Python: {name}"
        box = _kept_or_new(
            old_opens, entry_name,
            lambda m=message: seal.seal(m, earner_public, LABEL),
            lambda e, m=message: _opens(e, earner, LABEL, m))
        opens.append({"name": entry_name, "madeBy": "python",
                      "to": "the earner", "label": LABEL,
                      "message": message.hex(), "box": box})
    for spec in RUST_MADE:
        entry = old_opens.get(spec["name"], {})
        message = MESSAGES[spec["message"]]
        box = entry.get("box", "") if entry.get("ikmE") == spec["ikmE"] else ""
        if box and not _opens({"box": box}, earner, LABEL, message):
            raise SystemExit(f"{spec['name']}: the kept box doesn't open")
        opens.append({"name": spec["name"], "madeBy": "rust",
                      "to": "the earner", "label": LABEL,
                      "message": message.hex(), "ikmE": spec["ikmE"],
                      "box": box})

    base = bytes.fromhex(opens[0]["box"])
    refused: List[Dict[str, Any]] = []

    def refuse(name: str, box: bytes, why: str) -> None:
        refused.append({"name": name, "to": "the earner", "label": LABEL,
                        "box": box.hex(), "why": why})

    def kept_refusal(name: str, make, why: str) -> None:
        def still_refused(e: Dict[str, Any]) -> bool:
            return not _opens(e, earner, LABEL, MESSAGES["a short message"])
        box = _kept_or_new(old_refused, name, make, still_refused)
        refused.append({"name": name, "to": "the earner", "label": LABEL,
                        "box": box, "why": why})

    short = MESSAGES["a short message"]
    kept_refusal(
        "sealed for another purpose",
        lambda: _raw_seal(short, earner_public, b"open-worlds/journal/v1"),
        "sealed with the label open-worlds/journal/v1")
    kept_refusal(
        "sealed with no label",
        lambda: _raw_seal(short, earner_public, b""),
        "sealed with an empty info")
    kept_refusal(
        "sealed to someone else",
        lambda: seal.seal(short, _public("someone else"), LABEL),
        "sealed to another key")
    refuse("a bit of enc changed", _flip(base, 0), "enc changed")
    refuse("enc's top bit set", _flip(base, 31, 0x80),
           "X25519 ignores the bit, but HPKE binds enc as written")
    refuse("a bit of the ciphertext changed", _flip(base, 32),
           "the tag no longer matches")
    refuse("a bit of the tag changed", _flip(base, len(base) - 1),
           "the tag no longer matches")
    refuse("the last byte cut off", base[:-1], "the tag no longer matches")
    refuse("a byte added", base + b"\x00", "the tag no longer matches")
    refuse("enc alone", base[:32], "too short to be a box")
    refuse("one byte short of enc and a tag", base[:47],
           "too short to be a box")
    refuse("empty", b"", "too short to be a box")
    for name, point in SMALL_ORDER.items():
        refuse(f"enc of small order: {name}",
               bytes.fromhex(point) + base[32:],
               "the shared secret would be zero")
    refuse("enc is 2^255 - 19, another spelling of 0",
           _P.to_bytes(32, "little") + base[32:],
           "the shared secret would be zero")

    keys = [{"name": name, "key": point, "why": "of small order"}
            for name, point in SMALL_ORDER.items()]
    keys += [
        {"name": "2^255 - 19, another spelling of 0",
         "key": _P.to_bytes(32, "little").hex(),
         "why": "not below 2^255 - 19"},
        {"name": "2^255 - 18, another spelling of 1",
         "key": (_P + 1).to_bytes(32, "little").hex(),
         "why": "not below 2^255 - 19"},
        {"name": "2^255 - 10, another spelling of 9 (the base point)",
         "key": (_P + 9).to_bytes(32, "little").hex(),
         "why": "not below 2^255 - 19, though not of small order"},
        {"name": "the earner's key with its top bit set",
         "key": _flip(earner_public, 31, 0x80).hex(),
         "why": "the top bit is set"},
    ]

    return {
        "about": (
            "Sealing (formats/seal.py, rust/formats/src/seal.rs): HPKE "
            "base mode with DHKEM(X25519, HKDF-SHA256), HKDF-SHA256 and "
            "ChaCha20Poly1305, info a label in use, no associated data. A "
            "box is enc || ct, in hex. Written by python3 -m "
            "formats.seal_vectors; test keys only, never for anything real."),
        "labels": sorted(seal.LABELS),
        "rfc9180": RFC9180,
        "recipients": {
            name: {
                "secretKeyMultibase": sealing_secret_multikey(_secret(name)),
                "publicKeyMultibase": sealing_multikey(_public(name))}
            for name in RECIPIENTS},
        "opens": opens,
        "refused": refused,
        "refusedLabels": [
            "open-worlds/world-key/v2", "open-worlds/journal/v1", "",
            "open-worlds/world-key/v1 ", "Open-Worlds/world-key/v1",
            RFC9180_INFO_TEXT],
        "refusedKeys": keys,
        "refusedSealingMultikeys": [
            {"name": "an Ed25519 key, not a sealing key",
             "multikey": public_multikey(
                 ed25519.public_key(_secret("the earner"))),
             "why": "its prefix is 0xed 0x01"},
            {"name": "a secret sealing key given as public",
             "multikey": sealing_secret_multikey(_secret("the earner")),
             "why": "its prefix is 0x82 0x26"},
        ],
    }


RFC9180_INFO_TEXT = bytes.fromhex(RFC9180["info"]).decode("ascii")


def text(old: Optional[Dict[str, Any]] = None) -> str:
    return json.dumps(vectors(old), indent=1, ensure_ascii=False) + "\n"


def current() -> Optional[Dict[str, Any]]:
    """The file as it is now, if there is one."""
    if not FILE.exists():
        return None
    return json.loads(FILE.read_text(encoding="utf-8"))


def main() -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(text(current()), encoding="utf-8")
    print(f"wrote {FILE}")


if __name__ == "__main__":
    main()
