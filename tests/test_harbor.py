"""Grounded moderator handoffs and the two recorded rooms."""
import importlib
import json
import os
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import patch

TRIAL = Path(__file__).resolve().parents[1] / "experiments/006-harbor"
with patch.dict(sys.modules), patch.object(sys, "path", [str(TRIAL), *sys.path]):
    for name in ("run", "play", "puzzle", "harbor"):
        sys.modules.pop(name, None)
    harbor = importlib.import_module("harbor")


class HarborTests(TestCase):
    def test_only_public_facts_reach_the_moderator(self):
        history = [(harbor.PIER, "I would start at the pier.")]
        for name in (harbor.MOD, harbor.PIER):
            msg = harbor.request(name, harbor.MARKET, history)["messages"][0]["content"]
            self.assertNotIn("07:00:45", msg)
            self.assertIn(history[0][1], msg)
        self.assertNotIn("07:00:10", harbor.request(harbor.MOD, harbor.MARKET, history)["messages"][0]["content"])

    def test_retry_grounds_a_question_in_the_immediately_preceding_guest(self):
        history = [(harbor.PIER, "Hear the bell."), (harbor.MARKET, "There is a shutter.")]
        answers = iter([("bell", "Where is the bell?"), ("shutter", "When will the shutter open?")])
        prompts = []

        def get(req):
            prompts.append(req)
            anchor, question = next(answers)
            return {"finish": "stop", "model": harbor.MODELS[harbor.MOD],
                    "public": json.dumps({"anchor": anchor, "question": question})}

        self.assertEqual(harbor.turn(harbor.MOD, harbor.PIER, history, get),
                         ("post", "When will the shutter open?"))
        self.assertIn("Copy an exact phrase", prompts[1]["messages"][0]["content"])

    def test_malformed_public_channel_keeps_a_digest_and_withholds_text(self):
        raw = "A synthetic delimiter </think> here"
        call = harbor.protect_public_channel({"public": raw, "finish": "stop"})
        self.assertIsNone(call["public"])
        self.assertEqual(call["public_omitted"]["bytes"], len(raw.encode()))
        with self.assertRaisesRegex(ValueError, "complete"):
            harbor.interpret(harbor.PIER, call, [])

    def test_only_finished_unambiguous_final_suffix_is_recoverable_in_writing_trial(self):
        for reason, wanted in [("stop", "The posted answer."), ("length", None)]:
            call = harbor.protect_public_channel({"public": "preface</think>The posted answer.",
                                                  "finish": reason}, recover_final=True)
            self.assertEqual(call["public"], wanted)
            self.assertIn("sha256", call["public_omitted"])

    def test_a_repeated_moderator_question_yields_the_floor(self):
        history = [(harbor.PIER, "Hear the bell."), (harbor.MOD, "When is the bell?"),
                   (harbor.MARKET, "The bell rings now.")]
        reply = {"finish": "stop", "model": harbor.MODELS[harbor.MOD],
                 "public": json.dumps({"anchor": "bell", "question": "When is the bell?"})}
        self.assertEqual(harbor.turn(harbor.MOD, harbor.PIER, history, lambda _: reply),
                         ("withheld", None))

    def test_guests_may_end_before_the_scheduled_followup(self):
        for actions in (["leave"], ["pass", "pass"]):
            offers = harbor.schedule(True, [])
            next(offers)
            for action in actions[:-1]:
                offers.send(action)
            with self.assertRaises(StopIteration):
                offers.send(actions[-1])

    def test_time_replays_only_change_the_token_allowance_between_calls(self):
        replay = json.loads((TRIAL / "time-check.json").read_text())
        turns = list(map(json.loads,(TRIAL / "sign/turns.jsonl").read_text().splitlines()))
        original = turns[replay["source_opportunity"] - 1]
        self.assertEqual(original["action"], "withheld")
        self.assertFalse(replay["room_posted"])
        body = original["calls"][0]["request"]
        self.assertEqual(len(replay["calls"]), 2)
        for call, limit in zip(replay["calls"], [448, 896]):
            self.assertEqual(call["request"], {**body, "max_tokens": limit, "cache_prompt": False})
            self.assertEqual(harbor.interpret(harbor.PIER, call, []),
                             (call["eligible_action"], call["eligible_words"]))

    def test_recorded_questions_and_control_match_each_signed_history(self):
        plugin = os.getenv("COMMONS_TRIAL_PLUGIN")
        for mode in ("moderated", "control", "fact-check", "sign"):
            with self.subTest(mode=mode):
                history = harbor.verify(TRIAL / mode, Path(plugin) if plugin else None)
                if mode == "control":
                    self.assertNotIn(harbor.MOD, {n for n, _ in history})
                self.assertTrue(history)
