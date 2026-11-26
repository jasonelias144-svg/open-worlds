"""Check the chime game against every hidden target and replay the published evidence."""

import importlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TRIAL = Path(__file__).resolve().parents[1] / "experiments/004-chime-room"
with patch.dict(sys.modules), patch.object(sys, "path", [str(TRIAL), *sys.path]):
    for name in ("run", "verify", "play", "puzzle"):
        sys.modules.pop(name, None)
    rules = importlib.import_module("puzzle")
    verifier = importlib.import_module("verify")


def move(action, bells=""):
    return {"move": action, "bells": bells, "speech": "A trial utterance."}


class ChimeTests(unittest.TestCase):
    def test_three_tests_identify_each_possible_target(self):
        for target in rules.BELLS:
            with self.subTest(target=target):
                b = rules.Puzzle(target)
                for mask, expected in zip(("ABCD", "ABEF", "ACEG"), (4, 2, 1)):
                    notice, = b.advance(move("DAMP", mask))
                    self.assertTrue(notice.endswith("STOPS." if target in mask else "CONTINUES."))
                    self.assertEqual(len(b.remaining), expected)
                    self.assertIn(target, b.remaining)
                b.advance(move("NAME", target))
                self.assertEqual((b.end, b.phase), ("solved", "open"))
                for _ in range(4):
                    b.advance(move("TALK"))
                self.assertTrue(b.done)

    def test_premature_name_returns_identical_public_feedback(self):
        for target in rules.BELLS:
            b = rules.Puzzle(target)
            self.assertEqual(b.advance(move("NAME", "A")),
                             ["The evidence still permits more than one chime. No answer revealed."])
            self.assertEqual(b.remaining, set(rules.BELLS))

    def test_redundant_tests_exhaust_the_budget(self):
        b = rules.Puzzle("B")
        for _ in range(4):
            b.advance(move("DAMP", "A"))
        self.assertEqual((b.tests, b.end, b.phase), (4, "test budget", "open"))
        self.assertEqual(len(b.remaining), 7)

    def test_two_consecutive_passes_close_the_room(self):
        b = rules.Puzzle("A")
        b.advance(move("PASS"))
        b.advance(move("TALK"))
        b.advance(move("PASS"))
        self.assertFalse(b.done)
        b.advance(move("PASS"))
        self.assertEqual(b.end, "two passes")
        self.assertTrue(b.done)

    def test_invalid_or_out_of_phase_move_is_rejected(self):
        for data, phase in [(move("DAMP", "AA"), "puzzle"), (move("DAMP", "ABCDEFGH"), "puzzle"),
                            (move("NAME", "BC"), "puzzle"), (move("DAMP", "B"), "open")]:
            with self.subTest(data=data, phase=phase), self.assertRaises(ValueError):
                rules.decode(json.dumps(data), phase)

    def test_published_trials_replay(self):
        plugin = os.getenv("COMMONS_TRIAL_PLUGIN")
        directories = sorted(TRIAL.glob("trial-*"))
        self.assertTrue({"trial-1", "trial-2"}.issubset({d.name for d in directories}))
        for d in directories:
            with self.subTest(trial=d.name):
                verifier.replay(d, Path(plugin) if plugin else None, TRIAL / "PLAN.md")
