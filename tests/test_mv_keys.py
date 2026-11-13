"""Keeping keys safely (course step 6, first part): keys saved encrypted
and read back, and a world's seen numbers kept across a restart."""
import base64
import errno
import json
import os
import shutil
import stat
import struct
import tempfile
import unicodedata
import unittest
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

from multiverse import keys
from multiverse.collaboration import leave_world, make_client, petition_world
from multiverse.identity import Individual, Signer
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import Admission, Refusal

PASS = "correct horse battery staple"


def openssh_header(data: bytes):
    """The cipher, the KDF, the KDF's salt and rounds, the public key and
    the encrypted part of an OpenSSH private-key file (PROTOCOL.key in
    OpenSSH's sources). Nothing else in the file depends on the
    passphrase."""
    lines = data.decode().strip().splitlines()
    assert lines[0] == "-----BEGIN OPENSSH PRIVATE KEY-----"
    raw = base64.b64decode("".join(lines[1:-1]))
    magic = b"openssh-key-v1\0"
    assert raw.startswith(magic)
    at = len(magic)

    def string():
        nonlocal at
        n, = struct.unpack(">I", raw[at:at + 4])
        value = raw[at + 4:at + 4 + n]
        at += 4 + n
        return value

    cipher, kdf, options = string(), string(), string()
    salt_len, = struct.unpack(">I", options[:4])
    salt = options[4:4 + salt_len]
    rounds, = struct.unpack(">I", options[4 + salt_len:8 + salt_len])
    count, = struct.unpack(">I", raw[at:at + 4])
    at += 4
    public, encrypted = string(), string()
    assert at == len(raw) and count == 1
    return cipher, kdf, salt, rounds, public, encrypted


class Folder(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def path(self, name):
        return os.path.join(self.dir, name)


class TestKeyFiles(Folder):

    def test_an_individual_comes_back_as_itself(self):
        alice = Individual("Alice")
        keys.save_key(alice, self.path("alice.key"), PASS)
        again = keys.load_individual(self.path("alice.key"), PASS, "Alice")
        self.assertEqual(again.token, alice.token)
        document = {"a": 1}
        self.assertEqual(again.sign(document), alice.sign(document))

    def test_text_passphrases_are_normalised(self):
        # "pâté" typed as one character per letter (NFC) or with combining
        # accents (NFD) opens the same file; bytes are taken as they are.
        alice = Individual("Alice")
        nfd = unicodedata.normalize("NFD", "pâté ✓")
        self.assertNotEqual(nfd, "pâté ✓")
        keys.save_key(alice, self.path("alice.key"), nfd)
        self.assertEqual(keys.load_signer(self.path("alice.key"),
                                          "pâté ✓").token, alice.token)
        self.assertEqual(keys.load_signer(self.path("alice.key"),
                                          "pâté ✓".encode()).token,
                         alice.token)

    def test_the_file_is_private_and_encrypted(self):
        alice = Individual("Alice")
        keys.save_key(alice, self.path("alice.key"), PASS)
        mode = stat.S_IMODE(os.stat(self.path("alice.key")).st_mode)
        self.assertEqual(mode, 0o600)
        with open(self.path("alice.key"), "rb") as f:
            data = f.read()
        self.assertNotIn(alice._secret, data)
        self.assertNotIn(base64.b64encode(alice._secret), data)
        self.assertEqual(os.listdir(self.dir), ["alice.key"])  # no leftovers

    def test_the_only_passphrase_check_is_the_slow_one(self):
        # The file is OpenSSH's format: bcrypt-pbkdf with ROUNDS rounds,
        # then AES-256-CTR. It holds no other check on the passphrase
        # (no MAC, unlike PKCS12, whose MAC used 2,048 PBKDF2 rounds).
        alice = Individual("Alice")
        keys.save_key(alice, self.path("alice.key"), PASS)
        with open(self.path("alice.key"), "rb") as f:
            cipher, kdf, salt, rounds, public, encrypted = \
                openssh_header(f.read())
        self.assertEqual((cipher, kdf, rounds),
                         (b"aes256-ctr", b"bcrypt", 64))
        self.assertEqual(keys.ROUNDS, 64)
        self.assertEqual(len(salt), 16)
        self.assertIn(bytes.fromhex(alice.token), public)  # public, as is
        self.assertNotIn(alice._secret, encrypted)

    def test_a_changed_key_file_is_refused(self):
        # AES-CTR has no check of its own: a flipped bit of the encrypted
        # secret would load, silently, as another key. The public key in
        # the file's clear header catches it.
        alice = Individual("Alice")
        keys.save_key(alice, self.path("alice.key"), PASS)
        with open(self.path("alice.key"), "rb") as f:
            data = f.read()
        raw = base64.b64decode(b"".join(data.strip().splitlines()[1:-1]))
        *_, public, encrypted = openssh_header(data)
        # Decrypted, the secret starts 63 bytes in: two check numbers (8),
        # the key type (4 + 11), the public key (4 + 32), a length (4).
        places = {"secret": raw.index(encrypted) + 63,
                  "public key in the clear": raw.index(public) + 19 + 5}
        for what, at in places.items():
            with self.subTest(what=what):
                changed = bytearray(raw)
                changed[at] ^= 1
                body = base64.b64encode(bytes(changed))
                with open(self.path("changed.key"), "wb") as f:
                    f.write(b"-----BEGIN OPENSSH PRIVATE KEY-----\n"
                            + b"\n".join(body[i:i + 70]
                                         for i in range(0, len(body), 70))
                            + b"\n-----END OPENSSH PRIVATE KEY-----\n")
                with self.assertRaisesRegex(ValueError, "changed"):
                    keys.load_signer(self.path("changed.key"), PASS)
        self.assertEqual(keys.load_signer(self.path("alice.key"),
                                          PASS).token, alice.token)

    def test_a_file_asking_for_huge_rounds_is_refused_at_once(self):
        # One flipped bit of the rounds field could make a load run for
        # hours before failing; it is refused before any derivation.
        import time
        keys.save_key(Individual("Alice"), self.path("a.key"), PASS)
        with open(self.path("a.key"), "rb") as f:
            data = f.read()
        raw = bytearray(base64.b64decode(b"".join(
            data.strip().splitlines()[1:-1])))
        _, _, salt, rounds, _, _ = openssh_header(data)
        at = raw.index(salt) + len(salt)
        self.assertEqual(struct.unpack(">I", raw[at:at + 4]), (rounds,))
        raw[at:at + 4] = struct.pack(">I", keys.MAX_ROUNDS + 1)
        body = base64.b64encode(bytes(raw))
        lines = [body[i:i + 70] for i in range(0, len(body), 70)]
        begin = b"-----BEGIN OPENSSH PRIVATE KEY-----"
        end = b"-----END OPENSSH PRIVATE KEY-----"
        # The library finds the block anywhere and skips stray characters,
        # so each of these layouts would reach the derivation if the cap
        # read the file differently (found by the independent review).
        layouts = {
            "plain": b"\n".join([begin, *lines, end]) + b"\n",
            "junk after": b"\n".join([begin, *lines, end, b"junk"]) + b"\n",
            "junk before": b"\n".join([b"junk", begin, *lines, end]),
            "space inside": b"\n".join([begin, lines[0][:9] + b" "
                                        + lines[0][9:], *lines[1:], end]),
            "CR line ends": b"\r".join([begin, *lines, end]) + b"\r",
        }
        for layout, data in layouts.items():
            with self.subTest(layout=layout):
                with open(self.path("huge.key"), "wb") as f:
                    f.write(data)
                start = time.monotonic()
                with self.assertRaisesRegex(ValueError, "rounds"):
                    keys.load_signer(self.path("huge.key"), PASS)
                self.assertLess(time.monotonic() - start, 1.0)

    def test_text_around_a_key_files_block_doesnt_change_the_key(self):
        alice = Individual("Alice")
        keys.save_key(alice, self.path("a.key"), PASS)
        with open(self.path("a.key"), "rb") as f:
            data = f.read()
        for name, changed in (("before", b"a note\n" + data),
                              ("after", data + b"a note\n")):
            with self.subTest(name=name):
                with open(self.path("noted.key"), "wb") as f:
                    f.write(changed)
                self.assertEqual(
                    keys.load_signer(self.path("noted.key"), PASS).token,
                    alice.token)

    def test_another_key_file_with_the_same_passphrase_loads_as_itself(self):
        # The limit the docs state: the check is that a file's secret
        # matches its own public key, so a whole other key file made with
        # the same passphrase, put in this one's place, loads as that key.
        a, b = Individual("A"), Individual("B")
        keys.save_key(a, self.path("a.key"), PASS)
        keys.save_key(b, self.path("b.key"), PASS)
        os.replace(self.path("b.key"), self.path("a.key"))
        self.assertEqual(keys.load_signer(self.path("a.key"), PASS).token,
                         b.token)

    def test_wrong_or_missing_passphrases(self):
        keys.save_key(Individual("Alice"), self.path("alice.key"), PASS)
        with self.assertRaisesRegex(ValueError, "passphrase is wrong"):
            keys.load_individual(self.path("alice.key"), "wrong", "Alice")
        # Refused here, by our own check, whatever the library would do.
        for bad in ("", b"", None, 5, ["x"]):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "non-empty"):
                    keys.save_key(Individual("Bob"), self.path("b.key"), bad)
                with self.assertRaisesRegex(ValueError, "non-empty"):
                    keys.load_signer(self.path("alice.key"), bad)
        self.assertEqual(os.listdir(self.dir), ["alice.key"])

    def test_a_key_file_is_never_overwritten_unless_asked(self):
        alice, bob = Individual("Alice"), Individual("Bob")
        keys.save_key(alice, self.path("key"), PASS)
        os.symlink(self.path("key"), self.path("link"))
        os.symlink(self.path("nowhere"), self.path("dangling"))
        os.mkdir(self.path("folder"))
        for target in ("key", "link", "dangling", "folder"):
            with self.subTest(target=target):
                with self.assertRaises(FileExistsError):
                    keys.save_key(bob, self.path(target), PASS)
        self.assertEqual(keys.load_signer(self.path("key"), PASS).token,
                         alice.token)
        keys.save_key(bob, self.path("key"), PASS, overwrite=True)
        self.assertEqual(keys.load_signer(self.path("key"), PASS).token,
                         bob.token)
        self.assertEqual(sorted(os.listdir(self.dir)),
                         ["dangling", "folder", "key", "link"])

    def test_without_hard_links_saving_fails_and_says_why(self):
        def no_links(src, dst):
            raise OSError(errno.EPERM, "Operation not permitted")
        with mock.patch("multiverse.keys.os.link", no_links):
            with self.assertRaisesRegex(OSError, "hard link"):
                keys.save_key(Individual("Alice"), self.path("a.key"), PASS)
        self.assertEqual(os.listdir(self.dir), [])

    def test_what_isnt_an_encrypted_ed25519_key_file_is_refused(self):
        def write(name, data):
            with open(self.path(name), "wb") as f:
                f.write(data)
        write("text", b"not a key")
        ssh = serialization.PrivateFormat.OpenSSH
        enc = ssh.encryption_builder().kdf_rounds(50).build(b"pw")
        write("ec", ec.generate_private_key(ec.SECP256R1()).private_bytes(
            serialization.Encoding.PEM, ssh, enc))
        write("plain", Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM, ssh, serialization.NoEncryption()))
        with open(self.path("whole"), "wb") as f:
            keys.save_key(Individual("A"), self.path("good"), PASS)
            with open(self.path("good"), "rb") as g:
                f.write(g.read()[:200])                     # cut short
        for name, phrase in (("text", PASS), ("ec", "pw"), ("plain", PASS),
                             ("whole", PASS)):
            with self.subTest(name=name), self.assertRaises(ValueError):
                keys.load_signer(self.path(name), phrase)
        with self.assertRaises(ValueError):
            keys.save_key("not a signer", self.path("x.key"), PASS)


class TestRestartedWorlds(Folder):

    def setUp(self):
        super().setUp()
        self.world = PoetryWorld("world:poetry", "Poetry")
        keys.save_key(self.world._key, self.path("world.key"), PASS)
        # Loaded once: each load takes the slow passphrase check.
        self.key = keys.load_signer(self.path("world.key"), PASS)

    def restart(self, seen=False, key=True):
        w = PoetryWorld("world:poetry", "Poetry",
                        key=self.key if key else None)
        if seen:
            w.restore_seen(keys.load_seen(self.path("seen.json"), w))
        return w

    def test_its_stamps_still_count_after_a_restart(self):
        alice = make_client("Alice")
        self.assertIsInstance(petition_world(alice, self.world), Admission)
        leave_world(alice, self.world)
        # Same key: its own earlier stamps verify.
        self.assertIsInstance(petition_world(alice, self.restart()),
                              Admission)
        # A new key is a new world: stamps in its name under the old key
        # are refused.
        r = petition_world(alice, self.restart(key=False))
        self.assertIsInstance(r, Refusal)
        self.assertIn("isn't the one that world is known by", r.reason)

    def test_seen_numbers_stop_a_replay_after_a_restart(self):
        alice = Individual("Alice")
        captured = alice.petition(self.world.manifest())
        self.assertIsInstance(self.world.petition(captured), Admission)
        self.world.leave(alice.leave(self.world.manifest()))
        keys.save_seen(self.world, self.path("seen.json"))
        # Without them, the old petition brings Alice back (the risk).
        self.assertIsInstance(self.restart().petition(captured), Admission)
        r = self.restart(seen=True).petition(captured)
        self.assertIsInstance(r, Refusal)
        self.assertIn("Out of order", r.reason)
        # A new request still works.
        w = self.restart(seen=True)
        self.assertIsInstance(w.petition(alice.petition(w.manifest())),
                              Admission)

    def test_an_older_copy_lets_a_later_request_through_once(self):
        # What a signature can't stop: a file saved before a request was
        # seen is still validly signed. Restored from it, a world accepts
        # that request once (keys.py and MULTIVERSE.md say so).
        alice = Individual("Alice")
        keys.save_seen(self.world, self.path("seen.json"))
        shutil.copy(self.path("seen.json"), self.path("older.json"))
        later = alice.petition(self.world.manifest())
        self.assertIsInstance(self.world.petition(later), Admission)
        keys.save_seen(self.world, self.path("seen.json"))
        w = self.restart()
        w.restore_seen(keys.load_seen(self.path("older.json"), w))
        self.assertIsInstance(w.petition(later), Admission)
        self.assertIsInstance(self.restart(seen=True).petition(later),
                              Refusal)

    def test_a_changed_or_borrowed_seen_file_is_refused(self):
        alice = Individual("Alice")
        self.world.petition(alice.petition(self.world.manifest()))
        keys.save_seen(self.world, self.path("seen.json"))
        with open(self.path("seen.json")) as f:
            signed = json.load(f)
        self.assertEqual(oct(stat.S_IMODE(
            os.stat(self.path("seen.json")).st_mode)), "0o600")
        lowered = dict(signed, seen={alice.token: 1})
        other = PoetryWorld("world:other", "Other")
        keys.save_seen(other, self.path("other.json"))
        for name, content in (("lowered", json.dumps(lowered)),
                              ("garbage", "not json"),
                              ("list", "[]"),
                              ("extra", json.dumps(dict(signed, x=1)))):
            with self.subTest(name=name):
                with open(self.path("bad.json"), "w") as f:
                    f.write(content)
                with self.assertRaises(ValueError):
                    keys.load_seen(self.path("bad.json"), self.restart())
        with self.assertRaises(ValueError):          # another world's file
            keys.load_seen(self.path("other.json"), self.restart())
        with self.assertRaises(ValueError):          # signed, but not ours
            keys.load_seen(self.path("seen.json"),
                           PoetryWorld("world:poetry", "Impostor"))
        self.assertEqual(keys.load_seen(self.path("seen.json"),
                                        self.restart()),
                         self.world.seen_numbers())

    def test_every_kind_of_world_takes_its_key_back(self):
        from multiverse.chemistry_world import ChemistryWorld
        from multiverse.corridor_world import CorridorWorld
        from multiverse.registry import MultiverseRegistry
        key = self.key
        for kind in (PoetryWorld, ChemistryWorld, CorridorWorld,
                     MultiverseRegistry):
            with self.subTest(kind=kind.__name__):
                w = kind("world:x", "X", key=key)
                self.assertEqual(w.world_key, self.world.world_key)
                self.assertEqual(w.known_keys()["world:x"],
                                 self.world.world_key)

    def test_restored_numbers_only_grow(self):
        w = self.restart()
        token = Signer().token
        w.restore_seen({token: 50})
        w.restore_seen({token: 10})
        self.assertEqual(w.seen_numbers()[token], 50)
        for bad in ({token: 0}, {token: True}, {token: "5"}, {"nokey": 5},
                    [(token, 5)]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                w.restore_seen(bad)
        self.assertEqual(w.seen_numbers(), {token: 50})
        # What it gives out is a copy: changing it changes nothing here.
        w.seen_numbers()[token] = 1
        self.assertEqual(w.seen_numbers(), {token: 50})


if __name__ == "__main__":
    unittest.main()
