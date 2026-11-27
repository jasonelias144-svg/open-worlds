"""The room keeps control of its log; the audition only proposes a turn."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest

from minds.room_moderator import audition, observation, validate

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "experiments/002-room-moderator"
spec = importlib.util.spec_from_file_location("moderator_trial", TRIAL / "run.py")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


def view(room="one", text="Which cue could we try?"):
    return {"room_id": room, "entries": [
        {"seq": 0, "type": "created"},
        {"seq": 1, "type": "message", "redacted": False, "author": "room-specific-key", "text": text},
        {"seq": 2, "type": "message", "redacted": True, "author": "hidden-key", "text": "withdrawn speech",
         "reason": "hidden reason"},
        {"seq": 3, "type": "refused", "reason": "hidden reason"},
        {"seq": 4, "type": "message", "author": "another-key", "text": "ambiguous visibility"},
    ]}


def model(proposal):
    return lambda _: {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(proposal)}}]}


class RoomModeratorTests(unittest.TestCase):
    def test_projection_is_positive_and_pseudonymous(self):
        data = view()
        original = copy.deepcopy(data)
        seen = observation("one", "music", data)
        self.assertEqual(seen, {"topic": "music", "turns": [{"seq": 1, "speaker": 1, "text": "Which cue could we try?"}]})
        self.assertEqual(data, original)

    def test_wrong_room_and_conflicting_turn_numbers_do_not_reach_model(self):
        def forbidden(_):
            self.fail("inference on a mismatched view")
        with self.assertRaises(ValueError):
            audition("two", "music", view(), forbidden)
        data = view()
        data["entries"].append(data["entries"][1])
        with self.assertRaises(ValueError):
            audition("one", "music", data, forbidden)

    def test_empty_view_or_all_removed_waits_without_inference(self):
        data = view()
        data["entries"][1]["redacted"] = True
        result = audition("one", "music", data, lambda _: self.fail("unexpected inference"))
        self.assertEqual(result["proposal"], {"action": "wait"})
        self.assertFalse(result["model_called"])

    def test_same_backend_two_rooms_and_no_history_or_tools(self):
        requests = []
        def complete(body):
            requests.append(body)
            return model({"action": "wait"})(body)
        for room in ["one", "two"]:
            audition(room, "meeting", view(room, room + " marker"), complete, baseline=True)
        second = json.dumps(requests[1])
        self.assertIn("two marker", second)
        for item in ("one marker", "hidden reason", "room-specific-key", "withdrawn speech"):
            self.assertNotIn(item, second)
        self.assertEqual(len(requests[1]["messages"]), 2)
        self.assertNotIn("tools", requests[1])

    def test_only_a_question_addressing_visible_speech_or_silence(self):
        seen = observation("one", "music", view())
        good = {"action": "ask", "reply_to": 1, "question": "Which cue could we try first?"}
        self.assertEqual(audition("one", "music", view(), model(good), baseline=True)["proposal"], good)
        for bad in [dict(good, reply_to=2), dict(good, reply_to=True), dict(good, action="remove"),
                    dict(good, room_id="two"), dict(good, question="One? Two?"),
                    dict(good, question="You must leave."), {"action": "wait", "question": "Speak."}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate(bad, seen)

    def test_bad_model_reply_is_retained_and_no_action_is_released(self):
        result = audition("one", "music", view(), model({"action": "remove"}), baseline=True)
        self.assertIn("error", result)
        self.assertIn("remove", result["attempts"][0]["raw_reply"])
        self.assertNotIn("proposal", result)

    def test_invitations_are_scoped_to_both_room_and_latest_visible_turn(self):
        for invitation in [None, ("two", 1), ("one", 0), ("one", 2), ("one", True), ("one", 1.0)]:
            result = audition("one", "music", view(), lambda _: self.fail("model got the floor"),
                              invitation=invitation)
            self.assertFalse(result["model_called"])
            self.assertEqual(result["proposal"], {"action": "wait"})

    def test_invited_question_is_bound_by_reader_and_bad_attempts_are_kept(self):
        answers = iter(["Not a question.", "Which cue would be easy to see?"])
        def complete(_):
            return {"choices": [{"finish_reason": "stop", "message": {"content": next(answers)}}]}
        result = audition("one", "music", view(), complete, invitation=("one", 1))
        self.assertEqual(result["proposal"], {"action": "ask", "reply_to": 1,
                                              "question": "Which cue would be easy to see?"})
        self.assertEqual(len(result["attempts"]), 2)
        self.assertIn("error", result["attempts"][0])

    def test_repeated_malformed_reply_never_becomes_a_proposal(self):
        def complete(_):
            return {"choices": [{"finish_reason": "stop", "message": {"content": "One? Two?"}}]}
        result = audition("one", "music", view(), complete, invitation=("one", 1))
        self.assertEqual(len(result["attempts"]), 2)
        self.assertNotIn("proposal", result)
        self.assertIn("error", result)

    def test_invited_model_can_still_yield_the_floor(self):
        def complete(_):
            return {"choices": [{"finish_reason": "stop", "message": {"content": "WAIT"}}]}
        result = audition("one", "music", view(), complete, invitation=("one", 1))
        self.assertTrue(result["model_called"])
        self.assertEqual(result["proposal"], {"action": "wait"})

    def test_reader_rejects_out_of_scope_templates_before_opening_plugin(self):
        fixture = json.loads((TRIAL / "rooms/garden.json").read_bytes())
        for override in [{"personal": True}, {"join_policy": "closed"}]:
            log = copy.deepcopy(fixture)
            log["template"].update(override)
            log["records"][0]["template"].update(override)
            with self.subTest(override=override), self.assertRaisesRegex(ValueError, "public, non-personal"):
                trial.verified_view("/unused", trial.ROOMS["garden"], log)

    def test_window_and_question_reference_share_the_same_bound(self):
        data = {"room_id": "one", "entries": [dict(view()["entries"][1], seq=n, text="x" * 700)
                                              for n in range(1, 15)]}
        seen = observation("one", "music", data)
        self.assertEqual([t["seq"] for t in seen["turns"]], list(range(3, 15)))
        self.assertEqual(len(seen["turns"][0]["text"]), 600)
        with self.assertRaises(ValueError):
            validate({"action": "ask", "reply_to": 1, "question": "Who?"}, seen)


@unittest.skipUnless(os.environ.get("COMMONS_TRIAL_PLUGIN"), "set COMMONS_TRIAL_PLUGIN to the compiled sketch binary")
class RealRoomTests(unittest.TestCase):
    def setUp(self):
        self.plugin = os.environ["COMMONS_TRIAL_PLUGIN"]
        self.log = json.loads((TRIAL / "rooms/rehearsal.json").read_bytes())
        self.room = trial.ROOMS["rehearsal"]

    def test_signed_two_speaker_exchange_survives_and_withdrawn_line_stays_out(self):
        topic, visible = trial.verified_view(self.plugin, self.room, self.log)
        seen = observation(self.room, topic, visible)
        self.assertEqual([t["seq"] for t in seen["turns"]], [4, 5, 6])
        self.assertEqual([t["speaker"] for t in seen["turns"]], [1, 2, 1])
        self.assertNotIn("WITHDRAWN-COPPER-KITE", json.dumps(seen))

    def test_tampered_speech_fails_real_verifier(self):
        self.log["records"][-1]["text"] += " altered"
        with self.assertRaisesRegex(ValueError, "verify_room"):
            trial.verified_view(self.plugin, self.room, self.log)

    def test_room_cannot_be_substituted(self):
        with self.assertRaisesRegex(ValueError, "wrong room"):
            trial.verified_view(self.plugin, trial.ROOMS["garden"], self.log)
