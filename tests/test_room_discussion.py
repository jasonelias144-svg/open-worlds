"""The published attempts must replay from their own signed conversation."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

TRIAL = Path(__file__).resolve().parents[1] / "experiments/003-room-discussion"
with patch.dict(sys.modules), patch.object(sys, "path", [str(TRIAL), *sys.path]):
    sys.modules.pop("run", None)
    spec = importlib.util.spec_from_file_location("discussion_verifier", TRIAL / "verify.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)


def evidence(number):
    folder = TRIAL / f"run-{number:02d}"
    return (json.loads((folder / "room.json").read_bytes()),
            json.loads((folder / "speakers.json").read_bytes()),
            list(map(json.loads, (folder / "turns.jsonl").read_text().splitlines())))


class DiscussionTests(unittest.TestCase):
    def test_all_four_runs_match_the_observed_inputs_and_signed_messages(self):
        for number in range(1, 5):
            with self.subTest(run=number):
                verifier.match_trace(*evidence(number), partial=number <= 2)

    def test_consciousness_room_matches_the_actual_model_endpoints_and_prompts(self):
        for run in ("room", "peer-room", "question-room", "native-room"):
            with self.subTest(run=run):
                folder = TRIAL.parent / "005-consciousness" / run
                log = json.loads((folder / "room.json").read_text())
                actors = json.loads((folder / "speakers.json").read_text())
                trace = list(map(json.loads, (folder / "turns.jsonl").read_text().splitlines()))
                posts = verifier.match_trace(log, actors, trace)
                self.assertEqual({p["speaker"] for p in posts}, {"DeepSeek 1.5B", "DeepSeek 7B"})
                trace[0]["reported_model"] = trace[1]["reported_model"]
                with self.assertRaisesRegex(ValueError, "endpoint identity mismatch"):
                    verifier.match_trace(log, actors, trace)

    def test_unexpected_thinking_delimiter_is_never_room_speech(self):
        with self.assertRaisesRegex(ValueError, "unexpected thinking delimiter"):
            verifier.public_words("<think>Unclosed.", "consciousness")

    def test_words_changed_after_inference_do_not_match_room(self):
        log, actors, trace = evidence(3)
        post = next(turn for turn in trace if turn.get("action") == "post")
        post["raw"] = "Invented words."
        with self.assertRaisesRegex(ValueError, "signed message mismatch"):
            verifier.match_trace(log, actors, trace)

    def test_peer_received_the_room_as_it_stood_at_that_turn(self):
        log, actors, trace = evidence(3)
        trace[-1]["request"]["messages"][-1]["content"] = "A different conversation."
        with self.assertRaisesRegex(ValueError, "model input differs"):
            verifier.match_trace(log, actors, trace)

    def test_interrupted_attempt_cannot_count_as_a_completed_discussion(self):
        with self.assertRaisesRegex(ValueError, "errored turn"):
            verifier.match_trace(*evidence(1))

    @unittest.skipUnless(os.environ.get("COMMONS_TRIAL_PLUGIN"), "supply the standing room reader to check signatures")
    def test_independent_reader_verifies_consciousness_room(self):
        for run in ("room", "peer-room", "question-room", "native-room"):
            with self.subTest(run=run):
                subprocess.run([sys.executable, str(TRIAL / "verify.py"), "--plugin",
                                os.environ["COMMONS_TRIAL_PLUGIN"], str(TRIAL.parent / "005-consciousness" / run)],
                               check=True, capture_output=True)

    @unittest.skipUnless(os.environ.get("COMMONS_TRIAL_PLUGIN"), "supply the standing room reader to check signatures")
    def test_independent_reader_verifies_all_four_rooms(self):
        for number in range(1, 5):
            cmd = [sys.executable, str(TRIAL / "verify.py"), "--plugin", os.environ["COMMONS_TRIAL_PLUGIN"],
                   str(TRIAL / f"run-{number:02d}")]
            if number <= 2:
                cmd.append("--partial")
            with self.subTest(run=number):
                subprocess.run(cmd, check=True, capture_output=True)
