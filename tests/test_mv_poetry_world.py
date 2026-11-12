"""The poetry world: the sketch's tests for component 4, ported.

The verse here is Emily Dickinson's (public domain, as in
multiverse/collaboration.py). Its end-to-end test failed
because the third poet answered the second poet's question, which only
counted once an acknowledgment could answer the invitation (the law
change in multiverse/poetry_world.py).
"""
import unittest

from multiverse.conformance import run_conformance
from multiverse.identity import create_identity
from multiverse.poetry_world import PoetryWorld, PoetryWorldLaw, turns_from_log
from multiverse.protocol import (Ack, Act, Admission, Departure, Petition,
                                 Refusal)

class KeyBomb(str):
    """A key that hashes like the text it claims to be, so a dict lookup
    for that text calls its __eq__, which raises."""
    def __hash__(self): return str.__hash__(str(self))
    def __eq__(self, other): raise ValueError("no equality")


SEED = "Hope is the thing with feathers\nThat perches in the soul,"


def _petition(name, token, passport_admissions=()):
    return Petition(petitioner_token=token, petitioner_name=name,
                    passport_admissions=passport_admissions,
                    message=f"{name} petitions to enter.")


def _turn(actor, ack, proposal, invitation, holds_open=True,
          stance="formalist"):
    return Act(actor_token=actor, type="poem.turn", payload={
        "acknowledgment": ack, "proposal": proposal,
        "invitation": invitation, "holds_open": holds_open,
        "stance_used": stance})


class PoetryWorldCase(unittest.TestCase):

    def world(self, **law):
        return PoetryWorld("world:poetry", "The Poetry World",
                           law=PoetryWorldLaw(**law) if law else None)

    def enter(self, w, *names):
        people = [create_identity(n) for n in names]
        for p in people:
            self.assertIsInstance(w.petition(_petition(p.name, p.token)),
                                  Admission)
        return people


class TestEntering(PoetryWorldCase):

    def test_law_is_readable(self):
        doc = PoetryWorldLaw().describe()
        for section in ("Entering and leaving", "poem.turn", "Convergence",
                        "may leave at any time"):
            self.assertIn(section, doc)

    def test_manifest(self):
        m = self.world().manifest()
        self.assertEqual(m.protocol_version, "WCP/0.1")
        self.assertFalse(m.has_sub_registry())

    def test_petition_admits(self):
        w = self.world()
        alice = create_identity("Alice")
        r = w.petition(_petition("Alice", alice.token))
        self.assertIsInstance(r, Admission)
        self.assertEqual(r.entity_id, "world:poetry")

    def test_petition_already_admitted(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        r = w.petition(_petition("Alice", alice.token))
        self.assertIsInstance(r, Refusal)
        self.assertIn("Already", r.reason)

    def test_petition_preserves_passport_admissions(self):
        w = self.world()
        alice = create_identity("Alice")
        r = w.petition(_petition(
            "Alice", alice.token,
            passport_admissions=(("world:A", "2024-01-01T00:00:00+00:00"),)))
        self.assertIsInstance(r, Admission)
        self.assertEqual(w.passport_of(alice.token).worlds_visited(),
                         ["world:A", "world:poetry"])

    def test_bad_petitions_are_refused_not_raised(self):
        # The sketch's world raised inside petition() on these.
        w = self.world()
        token = create_identity("x").token
        for petition in [_petition("Alice", "short"),
                         _petition("Alice", None),
                         _petition("", token),
                         _petition("Alice", token, (("world:A", "never"),)),
                         _petition("Alice", token, (("only-one",),))]:
            with self.subTest(petition=petition):
                self.assertIsInstance(w.petition(petition), Refusal)
        self.assertEqual(w.members(), [])

    def test_full_world_refuses(self):
        w = self.world(max_admitted=1)
        self.enter(w, "Alice")
        bob = create_identity("Bob")
        r = w.petition(_petition("Bob", bob.token))
        self.assertIsInstance(r, Refusal)
        self.assertIn("full", r.reason)

    def test_closed_world_refuses(self):
        w = self.world(admits_any_identity=False)
        alice = create_identity("Alice")
        self.assertIsInstance(w.petition(_petition("Alice", alice.token)),
                              Refusal)


class TestLeaving(PoetryWorldCase):

    def test_leave_frees_the_place(self):
        w = self.world(max_admitted=1)
        alice, = self.enter(w, "Alice")
        d = w.leave(alice.token)
        self.assertIsInstance(d, Departure)
        self.assertFalse(d.already_left)
        self.assertEqual(w.members(), [])
        self.assertIsNone(w.passport_of(alice.token))
        self.assertFalse(w.is_admitted(alice.token))
        self.enter(w, "Bob")

    def test_leaving_twice(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        w.leave(alice.token)
        self.assertTrue(w.leave(alice.token).already_left)
        self.assertEqual([e.kind for e in w.log_since(None)],
                         ["admission", "departure"])

    def test_leave_works_after_convergence_and_turn_limit(self):
        w = self.world(max_turns=1)
        alice, = self.enter(w, "Alice")
        self.assertIsInstance(w.act(_turn(alice.token, "(seed)", SEED, "?")),
                              Ack)
        self.assertFalse(w.leave(alice.token).already_left)

    def test_only_plain_values_cross(self):
        # Text and mappings that redefine comparing or hashing are refused
        # at the boundary (protocol.py), so they can't make a world raise.
        class HashBomb(str):
            def __hash__(self): raise ValueError("no hash")

        class EqBomb(str):
            def __eq__(self, other): raise ValueError("no equality")
            def __ne__(self, other): raise ValueError("no inequality")
            __hash__ = str.__hash__

        class GetBomb(dict):
            def get(self, *a): raise ValueError("no get")

        w = self.world()
        alice, = self.enter(w, "Alice")
        bomb = HashBomb("x" * 32)
        self.assertIsInstance(w.petition(_petition("Bob", bomb)), Refusal)
        self.assertIsInstance(
            w.act(_turn(bomb, "(seed)", SEED, "?")), Refusal)
        self.assertTrue(w.leave(bomb).already_left)
        for act in (Act(alice.token, EqBomb("poem.turn"), {}),
                    Act(alice.token, "poem.turn",
                        GetBomb(acknowledgment="(seed)")),
                    None, "poem.turn"):
            with self.subTest(act=type(act).__name__):
                self.assertIsInstance(w.act(act), Refusal)
        for petition in (None, "Bob"):
            self.assertIsInstance(w.petition(petition), Refusal)
        for passport in ((("world:A",),), (["world:A", 7],),
                         ((EqBomb("world:A"), "2024-01-01T00:00:00+00:00"),),
                         "world:A", None):
            with self.subTest(passport=passport):
                carol = create_identity("Carol")
                self.assertIsInstance(
                    w.petition(_petition("Carol", carol.token, passport)),
                    Refusal)
        self.assertEqual(w.members(), ["Alice"])

    def test_plain_values_all_the_way_down(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        for payload in ({KeyBomb("proposal"): "x"},
                        {"acknowledgment": "(seed)", "proposal": SEED,
                         "invitation": "?", "holds_open": True,
                         "extra": [KeyBomb("x")]}):
            with self.subTest(payload=list(payload)):
                r = w.act(Act(alice.token, "poem.turn", payload))
                self.assertIsInstance(r, Refusal)
                self.assertIn("plain", r.reason)
        self.assertEqual(w.turns(), [])

    def test_petition_fields_and_passport_must_be_plain(self):
        class Odd:
            pass

        class Pairs(list):
            def __iter__(self): raise ValueError("no iteration")

        w = self.world()
        carol = create_identity("Carol")
        for petition in (
                Petition(carol.token, "Carol", (), Odd()),
                Petition(carol.token, "Carol", (), "hi", target=Odd()),
                Petition(carol.token, "Carol", Pairs(), "hi")):
            with self.subTest(petition=petition):
                self.assertIsInstance(w.petition(petition), Refusal)
        self.assertEqual(w.members(), [])

    def test_leave_with_odd_tokens(self):
        w = self.world()
        for token in (None, 7, "", ["list"]):
            with self.subTest(token=token):
                self.assertTrue(w.leave(token).already_left)

    def test_after_leaving_no_acts(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        w.leave(alice.token)
        r = w.act(_turn(alice.token, "(seed)", SEED, "What next?"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("not admitted", r.reason)

    def test_coming_back(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        w.leave(alice.token)
        self.assertIsInstance(w.petition(_petition("Alice", alice.token)),
                              Admission)

    def test_conformance_takes_no_place(self):
        # The sketch's conformance test entered and stayed.
        w = self.world(max_admitted=2)
        self.assertTrue(run_conformance(w)["passed"])
        self.assertEqual(w.members(), [])
        self.enter(w, "Alice", "Bob")


class TestTurns(PoetryWorldCase):

    def test_seed_turn(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        self.assertIsInstance(
            w.act(_turn(alice.token, "(seed)", SEED,
                        "What does the bird sing?")), Ack)
        self.assertEqual(len(w.turns()), 1)

    def test_subsequent_turn(self):
        w = self.world()
        alice, bob = self.enter(w, "Alice", "Bob")
        w.act(_turn(alice.token, "(seed)", SEED, "What of the bird?"))
        r = w.act(_turn(bob.token, "You said 'hope' and 'feathers'.",
                        "A bird came down the walk:\nHe did not know I saw;",
                        "What does the bird know?",
                        stance="psychoanalytic"))
        self.assertIsInstance(r, Ack)
        self.assertEqual(len(w.turns()), 2)

    def test_refusals(self):
        cases = [
            (dict(ack=""), "acknowledgment"),
            (dict(invitation=""), "invitation"),
            (dict(holds_open=False), "hold open"),
            (dict(proposal=""), "proposal"),
            (dict(proposal=["not", "text"]), "text"),
            (dict(stance=3), "stance"),
            (dict(holds_open="false"), "holds_open"),
            (dict(holds_open=1), "holds_open"),
        ]
        for change, reason in cases:
            with self.subTest(change=change):
                w = self.world()
                alice, = self.enter(w, "Alice")
                fields = dict(ack="(seed)", proposal="(proposal)",
                              invitation="(invitation)")
                fields.update(change)
                r = w.act(_turn(alice.token, fields.pop("ack"),
                                fields.pop("proposal"),
                                fields.pop("invitation"), **fields))
                self.assertIsInstance(r, Refusal)
                self.assertIn(reason, r.reason)
                self.assertEqual(w.turns(), [])

    def test_refusal_acknowledgment_does_not_reference(self):
        w = self.world()
        alice, bob = self.enter(w, "Alice", "Bob")
        w.act(_turn(alice.token, "(seed)", SEED, "What next?"))
        r = w.act(_turn(bob.token, "I agree.", "(proposal)", "(invitation)"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("reference", r.reason)

    def test_answering_the_invitation_counts_as_reference(self):
        w = self.world()
        alice, bob = self.enter(w, "Alice", "Bob")
        w.act(_turn(alice.token, "(seed)", SEED, "What is the bird's song?"))
        r = w.act(_turn(bob.token, "You asked about a song.",
                        "And sings the tune without the words,",
                        "And then?"))
        self.assertIsInstance(r, Ack)

    def test_refusal_not_admitted(self):
        w = self.world()
        stranger = create_identity("Alice")
        r = w.act(_turn(stranger.token, "(seed)", "(p)", "(i)"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("not admitted", r.reason)

    def test_refusal_wrong_type(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        r = w.act(Act(actor_token=alice.token, type="poem.not_a_turn",
                      payload={}))
        self.assertIsInstance(r, Refusal)
        self.assertIn("Unknown act type", r.reason)

    def test_payload_that_is_not_a_mapping(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        r = w.act(Act(actor_token=alice.token, type="poem.turn",
                      payload=["acknowledgment"]))
        self.assertIsInstance(r, Refusal)

    def test_turn_limit(self):
        w = self.world(max_turns=1)
        alice, = self.enter(w, "Alice")
        w.act(_turn(alice.token, "(seed)", SEED, "What next?"))
        r = w.act(_turn(alice.token, "the soul", "more", "What else?"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("turn limit", r.reason)


class TestConvergence(PoetryWorldCase):

    def test_convergence_by_invitation(self):
        w = self.world(convergence_window=3, convergence_similarity=0.99)
        alice, bob, charlie = self.enter(w, "Alice", "Bob", "Charlie")
        turns = [(alice, "(seed)", "first poem text here"),
                 (bob, "You said 'poem' and 'text' here",
                  "second poem text here"),
                 (charlie, "You said 'poem' and 'text' here",
                  "third poem text here")]
        for who, ack, proposal in turns:
            w.act(_turn(who.token, ack, proposal, "What is the poem?"))
            self.assertFalse(w.is_converged())
        w.act(_turn(alice.token, "You said 'poem' and 'text' here",
                    "fourth poem text here", "What is the poem?"))
        self.assertTrue(w.is_converged())
        self.assertIn("same invitation", w.convergence_reason())

    def test_convergence_by_echo(self):
        w = self.world(convergence_window=3, convergence_similarity=0.6)
        alice, bob = self.enter(w, "Alice", "Bob")
        w.act(_turn(alice.token, "(seed)", SEED, "Question one?"))
        lines = ["I never saw a moor, I never saw the sea",
                 "I never saw the sea, I never saw a moor",
                 "I never saw a moor, I never saw the sea"]
        for i, line in enumerate(lines):
            who = (bob, alice)[i % 2]
            self.assertIsInstance(w.act(_turn(
                who.token, "the soul, the sea", line, f"Question {i}?")),
                Ack)
        self.assertTrue(w.is_converged())
        self.assertIn("echo", w.convergence_reason())

    def test_refuses_after_convergence(self):
        w = self.world(convergence_window=2, convergence_similarity=0.99)
        alice, = self.enter(w, "Alice")
        for _ in range(3):
            w.act(_turn(alice.token, "I respond to the poem",
                        "a different poem line", "What is the poem?"))
        self.assertTrue(w.is_converged())
        extra = w.act(_turn(alice.token, "I respond to the poem",
                            "another line", "What is the poem?"))
        self.assertIsInstance(extra, Refusal)
        self.assertIn("converged", extra.reason)


class TestLog(PoetryWorldCase):

    def test_log_records_everything(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        w.act(_turn(alice.token, "(seed)", "a poem here", "what next?"))
        w.act(_turn(alice.token, "nothing", "x", "y"))
        w.leave(alice.token)
        self.assertEqual([e.kind for e in w.log_since(None)],
                         ["admission", "turn", "act_refused", "departure"])

    def test_log_query_by_timestamp(self):
        w = self.world()
        self.enter(w, "Alice")
        first = w.log_since(None)[0].timestamp
        self.assertEqual(w.log_since(first), [])
        self.assertEqual(len(w.log_since("")), 1)
        for odd in (5, ["x"], b"t"):
            self.assertEqual(w.log_since(odd), [])

    def test_log_keeps_its_own_copy(self):
        w = self.world()
        alice, = self.enter(w, "Alice")
        w.act(_turn(alice.token, "(seed)", SEED, "What next?"))
        w.turns()[0]["proposal"] = "changed by a reader of turns()"
        self.assertEqual(w.turns()[0]["proposal"], SEED)
        w.log_since(None)[-1].data["proposal"] = "changed in the log"
        self.assertEqual(w.turns()[0]["proposal"], SEED)

    def test_reconstruct_turns_from_log(self):
        w = self.world()
        alice, bob = self.enter(w, "Alice", "Bob")
        w.act(_turn(alice.token, "(seed)", SEED, "What of the bird?"))
        w.act(_turn(bob.token, "You said 'soul' and 'feathers'.",
                    "The soul selects her own society,", "What is the door?"))
        turns = turns_from_log(w.log_since(None))
        self.assertEqual([t["actor_name"] for t in turns], ["Alice", "Bob"])
        self.assertEqual(turns, w.turns())

    def test_conformance(self):
        self.assertTrue(run_conformance(self.world())["passed"])


class TestTwoWorlds(PoetryWorldCase):

    def test_two_worlds_independent(self):
        wa = PoetryWorld("world:poetry-A", "A",
                         law=PoetryWorldLaw(max_admitted=2))
        wb = PoetryWorld("world:poetry-B", "B",
                         law=PoetryWorldLaw(max_admitted=10))
        alice, bob, charlie = (create_identity(n)
                               for n in ("Alice", "Bob", "Charlie"))
        for w, p in [(wa, alice), (wb, alice), (wa, bob), (wb, charlie)]:
            self.assertIsInstance(w.petition(_petition(p.name, p.token)),
                                  Admission)
        # A is full: Charlie can't enter, and so can't act there.
        self.assertIsInstance(wa.petition(_petition("Charlie", charlie.token)),
                              Refusal)
        self.assertIsInstance(wa.act(_turn(charlie.token, "hi", "p", "i")),
                              Refusal)
        self.assertIsInstance(wa.act(_turn(alice.token, "hi", "alice poem",
                                           "invitation")), Ack)
        self.assertIsInstance(wa.act(_turn(bob.token, "you said 'alice'",
                                           "bob poem", "invitation")), Ack)
        self.assertEqual(len(wa.turns()), 2)
        self.assertEqual(len(wb.turns()), 0)

    def test_end_to_end(self):
        w = self.world(convergence_window=3, convergence_similarity=0.5)
        alice, bob, charlie = self.enter(w, "Alice", "Bob", "Charlie")
        dialogue = [
            (alice, "(seed)", SEED, "What does the bird sing?"),
            (bob, "You said 'hope' and 'feathers' and 'soul'.",
             "The soul selects her own society,\nThen shuts the door;",
             "What is the soul's song?"),
            # Answers Bob's question, not his lines: allowed since the law
            # change (an acknowledgment may reference the invitation).
            (charlie, "You said 'song' and 'tune' and 'words'.",
             "And sings the tune without the words,\nAnd never stops at all,",
             "What is the tune without words?"),
        ]
        for who, ack, proposal, invitation in dialogue:
            self.assertIsInstance(
                w.act(_turn(who.token, ack, proposal, invitation)), Ack)
        self.assertEqual(len(turns_from_log(w.log_since(None))), 3)


if __name__ == "__main__":
    unittest.main()
