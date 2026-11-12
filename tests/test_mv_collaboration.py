"""The apprentices and the first collaboration: the sketch's tests for
component 7, ported, with tests for the apprentice poets, which the
sketch didn't have."""
import contextlib
import io
import os
import tempfile
import unittest
from types import SimpleNamespace

from multiverse.apprentice import (Apprentice, ApprenticeVoice,
                                   CurriculumRunner, PortfolioPoem,
                                   TheoreticalStance, Turn)
from multiverse.collaboration import (CollaborationReport,
                                      FirstCollaboration, act_on_world,
                                      demo_portfolio, leave_world,
                                      log_entry_to_turn, main, make_client,
                                      petition_world, turn_to_act_payload)
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import Ack, Admission, LogEntry, Refusal

S = TheoreticalStance


def _prior(proposal, stance=None):
    return SimpleNamespace(proposal=proposal, stance_used=stance)


def _apprentice(portfolio, stances=tuple(S), seed=0):
    voice = ApprenticeVoice("Test", portfolio, [], list(stances), stances[0])
    return Apprentice("Test", voice, participant_position=1, seed=seed)


class TestApprentice(unittest.TestCase):

    def test_key_terms(self):
        a = _apprentice([])
        terms = a.key_terms(
            _prior("I never saw a moor,\nI never saw the sea;"))
        self.assertEqual(terms, ["never", "saw", "moor", "sea"])

    def test_turn_has_every_part_and_holds_open(self):
        a = _apprentice(demo_portfolio("Apprentice-A"))
        turn = a.generate_turn(_prior("A bird came down the walk:"), 0)
        self.assertIsInstance(turn, Turn)
        self.assertTrue(turn.acknowledgment and turn.proposal
                        and turn.invitation)
        self.assertTrue(turn.holds_open)
        self.assertEqual(a.turns_generated, 1)

    def test_never_repeats_the_prior_stance(self):
        a = _apprentice(demo_portfolio("Apprentice-A"),
                        stances=(S.FORMALIST, S.MARXIST))
        for _ in range(20):
            turn = a.generate_turn(_prior("the sea", S.FORMALIST), 0)
            self.assertEqual(turn.stance_used, S.MARXIST)

    def test_acknowledgment_names_the_prior_words(self):
        a = _apprentice(demo_portfolio("Apprentice-A"))
        turn = a.generate_turn(_prior("The soul selects her own society,"),
                               0)
        for word in ("soul", "selects", "own"):
            self.assertIn(word, turn.acknowledgment)

    def test_every_line_is_traced(self):
        a = _apprentice(demo_portfolio("Apprentice-A"))
        turn = a.generate_turn(_prior("I never saw the sea;"), 0)
        for line in turn.proposal.split("\n"):
            if line.strip():
                entry = a.provenance.trace(line)
                self.assertIsNotNone(entry, line)
                self.assertIn(f"stance:{turn.stance_used.value}",
                              entry.reworking)

    def test_no_matching_poem(self):
        a = _apprentice(demo_portfolio("Apprentice-A"))
        turn = a.generate_turn(_prior("Because I could not stop for Death,"),
                               0)
        self.assertEqual(turn.proposal, "(no seeds available for this stance)")

    def test_each_stance_reworks(self):
        poem = PortfolioPoem("I'm nobody! Who are you?\n"
                             "Are you nobody, too?\n"
                             "Then there's a pair of us — don't tell!",
                             "x", "t")
        expected = {
            S.FORMALIST: "Then there's a pair of us — don't tell!",
            S.STRUCTURALIST: "not-I'm\nnot-Are",
            S.DECONSTRUCTIVE: "I'm nobody! Who are you?\nand also\n"
                              "Are you nobody, too?\nand neither is the poem.",
            S.MARXIST: "the labor behind this:\nI'm nobody! Who are you?\n"
                       "Are you nobody, too?\n"
                       "Then there's a pair of us — don't tell!",
        }
        a = _apprentice([poem])
        for stance, text in expected.items():
            with self.subTest(stance=stance):
                self.assertEqual(a._rework([poem], stance), text)

    def test_holds_open_is_a_formal_check(self):
        self.assertFalse(Apprentice.holds_open(
            "In conclusion, hope is the thing with feathers."))
        self.assertTrue(Apprentice.holds_open(
            "Hope is the thing with feathers"))

    def test_curriculum(self):
        runner = CurriculumRunner("Apprentice-A", seed=1)
        a = runner.build_apprentice()
        self.assertEqual(runner.lessons_run, 69)
        self.assertEqual(a.voice.stances, list(S))
        tags = [p.lesson_tag for p in a.voice.portfolio]
        self.assertIn("theory/deconstructive/founder", tags)

    def test_seeded_apprentices_repeat(self):
        def run(seed):
            a = CurriculumRunner("A", seed=seed).build_apprentice()
            a.voice.portfolio = demo_portfolio("Apprentice-A")
            return [a.generate_turn(_prior("That perches in the soul,"), i)
                    .proposal for i in range(5)]
        self.assertEqual(run(3), run(3))


class TestClient(unittest.TestCase):

    def test_client_petitions_acts_and_leaves(self):
        world = PoetryWorld("world:test", "Test World")
        client = make_client("Alice")
        self.assertIsInstance(petition_world(client, world), Admission)
        self.assertEqual([w for w, _ in client.passport_admissions],
                         ["world:test"])
        ack = act_on_world(client, world, "poem.turn", {
            "acknowledgment": "(seed)", "proposal": "a line",
            "invitation": "what next?", "holds_open": True})
        self.assertIsInstance(ack, Ack)
        self.assertFalse(leave_world(client, world).already_left)
        self.assertEqual(client.is_admitted_to, {})
        # The passport keeps the stamp after leaving.
        self.assertEqual(len(client.passport_admissions), 1)

    def test_unadmitted_client_cannot_act(self):
        world = PoetryWorld("world:test", "Test World")
        r = act_on_world(make_client("Alice"), world, "poem.turn", {
            "acknowledgment": "(seed)", "proposal": "a line",
            "invitation": "?", "holds_open": True})
        self.assertIsInstance(r, Refusal)
        self.assertIn("not admitted", r.reason)

    def test_turn_adapter_roundtrip(self):
        turn = Turn(participant=None, round=0, line_count=1,
                    acknowledgment="you said 'bird'",
                    proposal="the little bird", invitation="what next?",
                    holds_open=True, stance_used=S.PSYCHOANALYTIC)
        back = log_entry_to_turn(LogEntry(
            timestamp="t", kind="turn", actor_token="x",
            data=turn_to_act_payload(turn)))
        self.assertEqual(back.proposal, turn.proposal)
        self.assertEqual(back.stance_used, S.PSYCHOANALYTIC)

    def test_demo_portfolio(self):
        slices = [demo_portfolio(n) for n in
                  ("Apprentice-A", "Apprentice-B", "Apprentice-C")]
        for p in slices:
            self.assertEqual(len(p), 8)
        self.assertNotEqual(slices[0][0].text, slices[1][0].text)


class TestFirstCollaboration(unittest.TestCase):

    def run_once(self, iterations=30, seed=42):
        fc = FirstCollaboration(seed=seed)
        fc.setup()
        return fc, fc.run_collaboration(max_iterations=iterations)

    def test_setup(self):
        fc = FirstCollaboration(seed=42)
        fc.setup()
        self.assertEqual(fc.multiverse.entity_ids(), ["world:poetry"])
        self.assertEqual(len(fc.apprentices), 3)
        for a in fc.apprentices:
            self.assertEqual(len(a.voice.portfolio), 8)
            self.assertEqual(len(a.voice.stances), 8)
        # Listing the world left no one in it.
        self.assertEqual(fc.world.members(), [])

    def test_run_before_setup(self):
        with self.assertRaises(RuntimeError):
            FirstCollaboration().run_collaboration()

    def test_full_collaboration(self):
        fc, report = self.run_once()
        kinds = [e["kind"] for e in report.world_log]
        self.assertTrue(report.converged)
        self.assertEqual(kinds.count("turn"), 4)
        # The conformance visit, the seed poet and three apprentices came
        # and went; nobody is left.
        self.assertEqual(kinds.count("admission"), 5)
        self.assertEqual(kinds.count("departure"), 5)
        self.assertEqual(fc.world.members(), [])
        for a in report.apprentices:
            self.assertEqual(a["passport"], ["world:poetry"])
            self.assertEqual(a["turns_failed"], 0)

    def test_same_seed_same_poem(self):
        a = self.run_once()[1].final_collaboration_text
        b = self.run_once()[1].final_collaboration_text
        self.assertEqual(a, b)

    def test_report_is_auditable(self):
        _, report = self.run_once(iterations=15)
        admitted = {e["actor_token"] for e in report.world_log
                    if e["kind"] == "admission"}
        turns = [e for e in report.world_log if e["kind"] == "turn"]
        self.assertGreaterEqual(len(turns), 2)
        self.assertLessEqual({e["actor_token"] for e in turns}, admitted)
        self.assertIn("world:poetry", [e["data"].get("entity_id")
                                       for e in report.multiverse_log])

    def test_report_roundtrip(self):
        _, report = self.run_once(iterations=10)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "collaboration.json")
            report.save(path)
            loaded = CollaborationReport.load(path)
        self.assertEqual(loaded.to_dict(), report.to_dict())

    def test_main_prints_the_poem(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main([]), 0)
        self.assertIn("--- Seed Poet ---\nHope is the thing with feathers",
                      out.getvalue())
        self.assertIn("departure: 5", out.getvalue())


if __name__ == "__main__":
    unittest.main()
