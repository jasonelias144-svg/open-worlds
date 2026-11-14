"""No private key is in this repository but the published test keys
(docs/research/KEYS.md, decided 2026-11-14, point 5).

The project's real private halves live only in its private repository. A
private key pushed here by mistake can't be taken back ("`git revert` is
not a valid way to undo the addition of sensitive data", GitHub): the
only remedy is a new key. So every tracked file is scanned for private
key material in the forms this project writes or reads:

- a Multikey secret: `z3u2...` (Ed25519) or `z3we...` (X25519),
  formats/multikey.py;
- a PEM private-key block with a body, such as OpenSSH's, which
  multiverse/keys.py writes, also where it is written inside a string
  (its line breaks as `\\n`) or quoted in Markdown (`> `).

Every file is read, whatever bytes it holds: what isn't UTF-8 is read
around. Not found: a key split across several strings joined in code.

The vectors hold test keys on purpose, each made from a seed that says
"never for anything real", and the W3C specification's own example key.
Those, and only those, are allowed: each is worked out here again from
its seed, so a real key pasted in among them is still found.
"""
import hashlib
import re
import subprocess
import unittest
from pathlib import Path

from formats import record_vectors, seal_vectors, sealed_vectors, vectors
from formats.multikey import sealing_secret_multikey, secret_multikey

ROOT = Path(__file__).resolve().parent.parent
_B58 = "1-9A-HJ-NP-Za-km-z"
MULTIKEY_SECRET = re.compile(rf"z3(?:u2|we)[{_B58}]{{40,}}")
PEM_PRIVATE_BLOCK = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----\s*[A-Za-z0-9+/=\s]{40,}"
    r"-----END [A-Z ]*PRIVATE KEY-----")


def tracked_files():
    """Every file Git tracks here; without Git, every file but Git's own
    and Rust's build output."""
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                             capture_output=True, check=True).stdout
        return [ROOT / p for p in out.decode().split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in ROOT.rglob("*") if p.is_file()
                and ".git" not in p.parts and "target" not in p.parts]


def published_test_keys():
    """Every test key the vectors may hold, worked out from its seed."""
    names = set(record_vectors.PARTIES) | set(sealed_vectors.PARTIES) | set(
        seal_vectors.RECIPIENTS)
    seeds = {vectors.TEST_SECRET}
    for name in names:
        seeds.add(record_vectors._secret(name))
        seeds.add(sealed_vectors._secret(name))
        seeds.add(sealed_vectors._sealing_secret(name))
        seeds.add(seal_vectors._secret(name))
    allowed = set()
    for seed in seeds:
        allowed.add(secret_multikey(seed))
        allowed.add(sealing_secret_multikey(seed))
    # Published in the W3C Recommendation, Appendix B.3.
    allowed.add(vectors._w3c()["secretKeyMultibase"])
    return allowed


def _readings(text):
    """`text` as written, with its escaped line breaks read as line
    breaks, and without Markdown's quote marks."""
    unescaped = text.replace("\\r\\n", "\n").replace("\\n", "\n")
    unquoted = re.compile(r"(?m)^[ \t]*(?:>[ \t]?)+")
    return (text, unescaped, unquoted.sub("", text), unquoted.sub("", unescaped))


def private_key_material(text):
    """Each Multikey secret and PEM private-key block in `text`, once."""
    found = []
    for reading in _readings(text):
        found += MULTIKEY_SECRET.findall(reading)
        found += PEM_PRIVATE_BLOCK.findall(reading)
    return list(dict.fromkeys(found))


def described(hit):
    """What was found, without any of it: its kind, and a hash to tell
    one find from another."""
    kind = ("an Ed25519 Multikey secret" if hit.startswith("z3u2") else
            "an X25519 Multikey secret" if hit.startswith("z3we") else
            "a PEM private-key block")
    return f"{kind}, SHA-256 {hashlib.sha256(hit.encode()).hexdigest()[:16]}"


def file_text(path):
    """A file's text, whatever bytes it holds."""
    return path.read_bytes().decode("utf-8", errors="replace")


class TestNoPrivateKeys(unittest.TestCase):

    def test_nothing_private_is_tracked_but_the_test_keys(self):
        allowed = published_test_keys()
        found = {}
        for path in tracked_files():
            try:
                text = file_text(path)
            except OSError:
                continue
            for hit in private_key_material(text):
                if hit not in allowed:
                    found.setdefault(str(path.relative_to(ROOT)),
                                     []).append(described(hit))
        self.assertEqual(found, {}, "a private key is in the repository: "
                         "replace that key, then remove it from history")

    def test_the_scan_finds_a_real_key(self):
        # A key made now, from the operating system's randomness, in each
        # form the scan looks for.
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
        signing = ed25519.Ed25519PrivateKey.generate()
        raw = signing.private_bytes(serialization.Encoding.Raw,
                                    serialization.PrivateFormat.Raw,
                                    serialization.NoEncryption())
        sealing = x25519.X25519PrivateKey.generate().private_bytes(
            serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
            serialization.NoEncryption())
        openssh = signing.private_bytes(serialization.Encoding.PEM,
                                        serialization.PrivateFormat.OpenSSH,
                                        serialization.NoEncryption()).decode()
        pkcs8 = signing.private_bytes(serialization.Encoding.PEM,
                                      serialization.PrivateFormat.PKCS8,
                                      serialization.NoEncryption()).decode()
        allowed = published_test_keys()
        for text in (f"key: {secret_multikey(raw)}\n",
                     f'"{sealing_secret_multikey(sealing)}"',
                     openssh, pkcs8):
            with self.subTest(text=text[:20]):
                hits = private_key_material(text)
                self.assertEqual(len(hits), 1)
                self.assertNotIn(hits[0], allowed)

    def test_the_scan_finds_a_key_written_inside_a_string_or_a_quote(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        pem = ed25519.Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode()
        escaped = pem.replace("\n", "\\n")
        for text in (f'{{"key": "{escaped}"}}',
                     f'KEY = b"{escaped}"\n',
                     "".join(f"> {line}\n" for line in pem.splitlines()),
                     f'> "{escaped}"'):
            with self.subTest(text=text[:20]):
                self.assertEqual(len(private_key_material(text)), 1)

    def test_a_file_that_isnt_utf8_is_still_read(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        raw = ed25519.Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
            serialization.NoEncryption())
        data = b"caf\xe9 " + secret_multikey(raw).encode() + b"\n\xff"
        import tempfile
        with tempfile.TemporaryDirectory() as place:
            path = Path(place) / "notes.txt"
            path.write_bytes(data)
            self.assertEqual(private_key_material(file_text(path)),
                             [secret_multikey(raw)])

    def test_what_is_reported_holds_none_of_the_key(self):
        hit = "z3u2" + "a" * 44
        self.assertNotIn(hit[4:12], described(hit))
        self.assertIn("Ed25519", described(hit))

    def test_the_headers_alone_are_not_keys(self):
        # multiverse/keys.py and its tests name the header, with no key.
        self.assertEqual(private_key_material(
            '_PEM = b"-----BEGIN OPENSSH PRIVATE KEY-----"'), [])

    def test_every_published_test_key_is_found_where_it_is(self):
        # The allowed set is not empty, and covers what the vectors hold.
        allowed = published_test_keys()
        in_vectors = set()
        for path in (ROOT / "vectors" / "formats").glob("*.json"):
            in_vectors |= set(MULTIKEY_SECRET.findall(
                path.read_text(encoding="utf-8")))
        self.assertTrue(in_vectors)
        self.assertLessEqual(in_vectors, allowed)


if __name__ == "__main__":
    unittest.main()
