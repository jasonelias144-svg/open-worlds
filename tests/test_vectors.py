"""The shared test vectors in vectors/ are exactly what this kernel writes
(world/vectors.py), so the Rust crate that reads them (rust/world-log) is
checked against this kernel, hash for hash."""
import json
import unittest

from world import World
from world.core import _digest
from world.vectors import BODIES, FOLDER, files


class TestTheVectors(unittest.TestCase):

    def test_the_files_are_what_the_kernel_writes_now(self):
        for name, content in files().items():
            with self.subTest(name):
                on_disk = (FOLDER / name).read_text(encoding="ascii")
                self.assertEqual(on_disk, content,
                                 "rewrite with: python3 -m world.vectors")

    def test_the_log_verifies_and_holds_every_kind_of_entry(self):
        log = json.loads((FOLDER / "world-log.json").read_text())
        self.assertTrue(World.verify_log(log))
        self.assertEqual(
            {e["kind"] for e in log},
            {"world_created", "entered", "moved", "blocked", "said",
             "invalid_action", "agent_error", "exited"})

    def test_each_digest_is_the_kernels(self):
        vectors = json.loads((FOLDER / "digests.json").read_text())
        self.assertEqual([v["body"] for v in vectors], BODIES)
        for v in vectors:
            self.assertEqual(v["hash"], _digest(v["body"]))


if __name__ == "__main__":
    unittest.main()
