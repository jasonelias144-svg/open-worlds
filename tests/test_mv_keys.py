"""Keeping keys safely (course step 6, first part): keys saved encrypted
and read back, and a world's seen numbers kept across a restart."""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption, pkcs12)

from multiverse import keys
from multiverse.collaboration import leave_world, make_client, petition_world
from multiverse.identity import Individual, Signer
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import Admission, Refusal

PASS = "correct horse battery staple"


class Folder(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def path(self, name):
        return os.path.join(self.dir, name)


class TestKeyFiles(Folder):

    def test_an_individual_comes_back_as_itself(self):
        alice = Individual("Alice")
        keys.save_key(alice, self.path("alice.p12"), PASS)
        again = keys.load_individual(self.path("alice.p12"), PASS, "Alice")
        self.assertEqual(again.token, alice.token)
        document = {"a": 1}
        self.assertEqual(again.sign(document), alice.sign(document))
        # A passphrase may be any non-empty text or bytes.
        keys.save_key(alice, self.path("b.p12"), "pâté ✓")
        self.assertEqual(keys.load_signer(self.path("b.p12"),
                                          "pâté ✓".encode()).token,
                         alice.token)

    def test_the_file_is_private_and_encrypted(self):
        alice = Individual("Alice")
        keys.save_key(alice, self.path("alice.p12"), PASS)
        mode = stat.S_IMODE(os.stat(self.path("alice.p12")).st_mode)
        self.assertEqual(mode, 0o600)
        with open(self.path("alice.p12"), "rb") as f:
            data = f.read()
        self.assertNotIn(alice._secret, data)
        self.assertEqual(os.listdir(self.dir), ["alice.p12"])  # no leftovers

    @unittest.skipUnless(shutil.which("openssl"), "needs openssl")
    def test_openssl_reads_the_promised_encryption(self):
        keys.save_key(Individual("Alice"), self.path("alice.p12"), PASS)
        out = subprocess.run(
            ["openssl", "pkcs12", "-info", "-noout", "-in",
             self.path("alice.p12"), "-passin", f"pass:{PASS}"],
            capture_output=True, text=True)
        text = out.stdout + out.stderr
        for part in ("PBES2", "PBKDF2", "AES-256-CBC", "Iteration 600000",
                     "hmacWithSHA256"):
            self.assertIn(part, text)

    def test_wrong_or_missing_passphrases(self):
        keys.save_key(Individual("Alice"), self.path("alice.p12"), PASS)
        with self.assertRaises(ValueError):
            keys.load_individual(self.path("alice.p12"), "wrong", "Alice")
        # Refused here, by our own check, whatever the library would do.
        for bad in ("", b"", None, 5, ["x"]):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "non-empty"):
                    keys.save_key(Individual("Bob"), self.path("b.p12"), bad)
                with self.assertRaisesRegex(ValueError, "non-empty"):
                    keys.load_signer(self.path("alice.p12"), bad)
        self.assertEqual(os.listdir(self.dir), ["alice.p12"])

    def test_a_key_file_is_never_overwritten_unless_asked(self):
        alice, bob = Individual("Alice"), Individual("Bob")
        keys.save_key(alice, self.path("key.p12"), PASS)
        with self.assertRaises(FileExistsError):
            keys.save_key(bob, self.path("key.p12"), PASS)
        self.assertEqual(keys.load_signer(self.path("key.p12"), PASS).token,
                         alice.token)
        keys.save_key(bob, self.path("key.p12"), PASS, overwrite=True)
        self.assertEqual(keys.load_signer(self.path("key.p12"), PASS).token,
                         bob.token)
        self.assertEqual(os.listdir(self.dir), ["key.p12"])

    def test_what_isnt_an_ed25519_key_file_is_refused(self):
        with open(self.path("text"), "wb") as f:
            f.write(b"not a key")
        other = ec.generate_private_key(ec.SECP256R1())
        with open(self.path("ec.p12"), "wb") as f:
            f.write(pkcs12.serialize_key_and_certificates(
                b"x", other, None, None, BestAvailableEncryption(b"pw")))
        for path, phrase in (("text", PASS), ("ec.p12", "pw")):
            with self.subTest(path=path), self.assertRaises(ValueError):
                keys.load_signer(self.path(path), phrase)
        with self.assertRaises(ValueError):
            keys.save_key("not a signer", self.path("x.p12"), PASS)


class TestRestartedWorlds(Folder):

    def setUp(self):
        super().setUp()
        self.world = PoetryWorld("world:poetry", "Poetry")
        keys.save_key(self.world._key, self.path("world.p12"), PASS)

    def restart(self, seen=False, key=True):
        w = PoetryWorld("world:poetry", "Poetry",
                        key=keys.load_signer(self.path("world.p12"), PASS)
                        if key else None)
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
        key = keys.load_signer(self.path("world.p12"), PASS)
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
