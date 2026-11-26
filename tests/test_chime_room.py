"""Check the chime game against every hidden target and replay the published evidence."""

import importlib
import json
import os
import shutil
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TRIAL = Path(__file__).resolve().parents[1] / "experiments/004-chime-room"
with patch.dict(sys.modules), patch.object(sys, "path", [str(TRIAL), *sys.path]):
    for name in ("run", "verify", "play", "puzzle", "design", "playtest"):
        sys.modules.pop(name, None)
    rules = importlib.import_module("puzzle")
    verifier = importlib.import_module("verify")
    design_trial = importlib.import_module("design")
    playtest = importlib.import_module("playtest")


def move(action, bells=""):
    return {"move": action, "bells": bells, "speech": "A trial utterance."}


class ChimeTests(unittest.TestCase):
    def test_three_tests_identify_each_possible_target(self):
        for target in rules.BELLS:
            with self.subTest(target=target):
                b = rules.Puzzle(target)
                for mask, expected in zip(("ABCD", "ABEF", "ACEG"), (4, 2, 1)):
                    (notice,) = b.advance(move("DAMP", mask))
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
            self.assertEqual(
                b.advance(move("NAME", "A")),
                ["The evidence still permits more than one chime. No answer revealed."],
            )
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
        for data, phase in [
            (move("DAMP", "AA"), "puzzle"),
            (move("DAMP", "ABCDEFGH"), "puzzle"),
            (move("NAME", "BC"), "puzzle"),
            (move("DAMP", "B"), "open"),
        ]:
            with self.subTest(data=data, phase=phase), self.assertRaises(ValueError):
                rules.decode(json.dumps(data), phase)

    def test_console_depends_only_on_public_clues(self):
        boards = [rules.Puzzle(t) for t in "AB"]
        history = [("Keeper", "Trial ready.")]
        for b in boards:
            b.advance(move("DAMP", "ABCD"))
        self.assertEqual(
            rules.console_request("Qwen", history, boards[0]),
            rules.console_request("Qwen", history, boards[1]),
        )
        payload = rules.console_request("Qwen", history, boards[0])
        self.assertIn("Public candidates: ABCD", payload["messages"][-1]["content"])
        self.assertIn(
            "DAMP BCEG", payload["response_format"]["json_schema"]["schema"]["properties"]["choice"]["enum"]
        )
        boards[0].phase = "open"
        self.assertNotIn("response_format", rules.console_request("Qwen", history, boards[0]))

    def test_console_and_free_speech_retain_the_guests_actual_choices(self):
        self.assertEqual(
            rules.parse_response('{"choice":"DAMP AD","speech":"Try these two."}', "puzzle", True),
            {"move": "DAMP", "bells": "AD", "speech": "Try these two."},
        )
        self.assertEqual(
            rules.parse_response("What would change with two chimes?", "open", True)["move"], "TALK"
        )
        self.assertEqual(rules.parse_response("PASS", "open", True)["move"], "PASS")

    def test_altering_a_reveal_or_a_guest_input_breaks_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "copy"
            shutil.copytree(TRIAL / "trial-3", folder)
            reveal = folder / "reveal.json"
            original = reveal.read_text()
            altered = json.loads(original)
            altered["target"] = next(b for b in rules.BELLS if b != altered["target"])
            reveal.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError, "commitment"):
                verifier.replay(folder)
            reveal.write_text(original)
            trace = folder / "turns.jsonl"
            turns = [json.loads(line) for line in trace.read_text().splitlines()]
            turns[0]["request"]["messages"][-1]["content"] += "Added after the run."
            trace.write_text("\n".join(map(json.dumps, turns)))
            with self.assertRaisesRegex(ValueError, "signed history"):
                verifier.replay(folder)

    def test_design_room_replays_from_signed_preceding_questions(self):
        plugin = os.getenv("COMMONS_TRIAL_PLUGIN")
        for room in ("design-room", "direct-room"):
            design_trial.verify_design(TRIAL / room, Path(plugin) if plugin else None)
        for room in ("playtest-room", "memory-room"):
            playtest.verify(TRIAL / room, Path(plugin) if plugin else None)

    def test_repeat_check_uses_a_previously_answered_peer_question(self):
        prior = [
            ("Keeper", "A design brief."),
            ("Qwen", "Draw a line."),
            ("SmolLM2", "What if it bends?"),
            ("Qwen", "Draw it again."),
        ]
        self.assertEqual(
            playtest.settled(3, prior, "WHAT if it bends?!"), ("What if it bends?", "Draw it again.")
        )
        self.assertIsNone(playtest.settled(3, prior, "Where should it finish?"))
        self.assertIsNone(playtest.settled(2, prior, "What if it bends?"))

    def test_published_trials_replay(self):
        plugin = os.getenv("COMMONS_TRIAL_PLUGIN")
        directories = sorted(TRIAL.glob("trial-*"))
        self.assertTrue({"trial-1", "trial-2", "trial-3"}.issubset({d.name for d in directories}))
        for d in directories:
            with self.subTest(trial=d.name):
                verifier.replay(d, Path(plugin) if plugin else None, TRIAL / "PLAN.md")
