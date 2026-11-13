"""The chemistry world on real chemistry (course step 4).

The sketch's world (component 5) accepted any reaction whose formulas
balanced. This one holds a soup of real molecules (`chem/`), and an act
is a real reaction, by one of the rules, among molecules that are there.
"""
import unittest

from chem import catalogue as cat
from chem.rules import RULES
from multiverse.chemistry_world import (ACT_TYPE, ChemistryWorld,
                                        ChemistryWorldLaw,
                                        reactions_from_log)
from multiverse.conformance import run_conformance
from multiverse.identity import Individual
from multiverse.passport import Stamp, thing_fingerprint
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import Ack, Act, Admission, Refusal
from world.core import World

AMIDE = "amide formation (condensation)"
TWO_GLYCINES = {"rule": AMIDE, "reactants": ["glycine", "glycine"]}


class KeyBomb(str):
    """A key that hashes like the text it claims to be, so a dict lookup
    for that text calls its __eq__, which raises."""
    def __hash__(self): return str.__hash__(str(self))
    def __eq__(self, other): raise ValueError("no equality")


def _in(world, person):
    return person.petition(world.manifest())


def _react(world, person, payload):
    """A reaction signed by `person`, for `world`."""
    return person.act(world.manifest(), ACT_TYPE, payload)


def _count(world, name):
    return world.census()[world.identity_of(name)]["count"]


class ChemistryCase(unittest.TestCase):

    def world(self, **law):
        return ChemistryWorld("world:chemistry", "The Chemistry World",
                              law=ChemistryWorldLaw(**law) if law else None)

    def still(self, **law):
        """A world whose soup has no reactions of its own, so only acts
        change it."""
        return self.world(own_reactions=(), **law)

    def enter(self, w, name="Alice"):
        person = Individual(name)
        self.assertIsInstance(w.petition(_in(w, person)), Admission)
        return person

    def state(self, w):
        return (w.census(), w.world_time, w.soup.log_head, w.reactions())


class TestTheLaw(ChemistryCase):

    def test_it_is_published(self):
        doc = ChemistryWorldLaw().describe()
        for part in (ACT_TYPE, "may leave at any time", "placeholders",
                     "seconds of world time", "100 water", "20 glycine",
                     "seed 0", AMIDE, "4.0 forward, 1.0 back"):
            self.assertIn(part, doc)

    def test_its_numbers_are_checked(self):
        for law in ({"seconds_per_act": float("nan")},
                    {"seconds_per_act": -1}, {"seconds_per_act": "1"},
                    {"soil": (("unobtainium", 1),)},
                    {"own_reactions": (("alchemy", ("water",), 1.0, 1.0),)}):
            with self.subTest(law=law), self.assertRaises(ValueError):
                ChemistryWorldLaw(**law)

    def test_the_world_starts_with_its_soil(self):
        w = self.world()
        self.assertEqual(_count(w, "water"), 100)
        self.assertEqual(_count(w, "glycine"), 20)
        self.assertEqual(_count(w, "formaldehyde"), 10)
        self.assertEqual(w.world_time, 0.0)
        soil, = [e for e in w.log_since(None) if e.kind == "soil"]
        self.assertEqual(soil.data["census"], w.census())


class TestReactions(ChemistryCase):

    def test_a_real_reaction_happens_in_the_soup(self):
        w = self.still()
        alice = self.enter(w)
        atoms = w.soup.atoms()
        r = w.act(_react(w, alice, TWO_GLYCINES))
        self.assertIsInstance(r, Ack)
        self.assertEqual(_count(w, "glycine"), 18)
        self.assertEqual(_count(w, "water"), 101)
        made, = w.reactions()
        dipeptide, = [i for i in made["products"]
                      if i != w.identity_of("water")]
        self.assertEqual(w.census()[dipeptide],
                         {"formula": "C4H8N2O3", "count": 1})
        self.assertEqual(made["rule"], AMIDE)
        self.assertEqual(made["reactants"], [w.identity_of("glycine")] * 2)
        self.assertEqual(w.soup.atoms(), atoms)
        # The made stamp names exactly this reaction.
        stamp = Stamp.from_entry(r.stamp)
        self.assertEqual((stamp.kind, stamp.made),
                         ("made", thing_fingerprint(made)))
        self.assertTrue(stamp.verifies())

    def test_molecules_can_be_named_by_identity(self):
        w = self.still()
        alice = self.enter(w)
        glycine = w.identity_of("glycine")
        self.assertIsInstance(w.act(_react(w, alice, {
            "rule": AMIDE, "reactants": [glycine, "glycine"]})), Ack)
        dipeptide = w.reactions()[0]["products"]
        # And what was made can be named by its identity: hydrolysis
        # takes the dipeptide back to two glycines.
        hydrolysis = w.act(_react(w, alice, {
            "rule": "amide hydrolysis", "reactants": sorted(dipeptide)}))
        self.assertIsInstance(hydrolysis, Ack)
        self.assertEqual(_count(w, "glycine"), 20)

    def test_a_choice_of_outcomes(self):
        # A proton can go from either glycine's acid group to the other's
        # amine: the rule gives every outcome, sorted, and `outcome`
        # chooses one.
        w = self.still()
        alice = self.enter(w)
        rule = "proton transfer, O-H to oxygen"
        outcomes = RULES[rule].apply(cat.glycine(), cat.water())
        self.assertGreater(len(outcomes), 1)
        r = w.act(_react(w, alice, {"rule": rule,
                                    "reactants": ["glycine", "water"],
                                    "outcome": len(outcomes) - 1}))
        self.assertIsInstance(r, Ack)
        self.assertEqual(w.reactions()[0]["products"],
                         [m.identity() for m in outcomes[-1]])
        r = w.act(_react(w, alice, {"rule": rule,
                                    "reactants": ["glycine", "water"],
                                    "outcome": len(outcomes)}))
        self.assertIsInstance(r, Refusal)
        self.assertIn(f"from 0 to {len(outcomes) - 1}", r.reason)

    def test_what_isnt_a_reaction_here_is_refused(self):
        w = self.still(soil=(("water", 5), ("glycine", 1)))
        alice = self.enter(w)
        before = self.state(w)
        for payload, reason in (
                ({"rule": "alchemy", "reactants": ["water"]}, "rule must"),
                ({"rule": 5, "reactants": ["water"]}, "rule must"),
                ({"reactants": ["water"]}, "rule must"),
                ({"rule": AMIDE, "reactants": "glycine"}, "reactants must"),
                ({"rule": AMIDE, "reactants": []}, "reactants must"),
                ({"rule": AMIDE, "reactants": ["water"] * 4},
                 "reactants must"),
                ({"rule": AMIDE, "reactants": ["glycine", 7]},
                 "reactants must"),
                ({"rule": AMIDE, "reactants": ["x" * 10_001]},
                 "reactants must"),
                ({"rule": AMIDE, "reactants": ["benzene"]},
                 "No molecule 'benzene'"),
                ({"rule": AMIDE, "reactants": ["glycine", "nonsense"]},
                 "No molecule"),
                ({"rule": "cyanohydrin formation", "reactants": ["water"]},
                 "doesn't apply"),
                (dict(TWO_GLYCINES, outcome=-1), "outcome must"),
                (dict(TWO_GLYCINES, outcome=True), "outcome must"),
                (dict(TWO_GLYCINES, outcome="0"), "outcome must"),
                # One glycine here, and the reaction needs two.
                (TWO_GLYCINES, "Not every reactant is in the soup")):
            with self.subTest(payload=payload):
                r = w.act(_react(w, alice, payload))
                self.assertIsInstance(r, Refusal)
                self.assertIn(reason, r.reason)
                self.assertEqual(self.state(w), before)

    def test_true_and_false_are_not_outcomes(self):
        # Booleans are whole numbers to Python, but not to this world.
        w = self.still()
        alice = self.enter(w)
        for outcome in (False, True):
            with self.subTest(outcome=outcome):
                r = w.act(_react(w, alice, dict(TWO_GLYCINES,
                                                outcome=outcome)))
                self.assertIsInstance(r, Refusal)
                self.assertEqual(r.reason,
                                 "outcome must be a whole number from 0")
        self.assertEqual(w.reactions(), [])

    def test_plain_values_all_the_way_down(self):
        class Odd:
            pass

        w = self.still()
        alice = self.enter(w)
        for payload in ({KeyBomb("rule"): AMIDE},
                        {"rule": AMIDE, "reactants": ["glycine", Odd()]}):
            with self.subTest(payload=list(payload)):
                r = w.act(Act(alice.token, ACT_TYPE, payload))
                self.assertIsInstance(r, Refusal)
                self.assertIn("plain", r.reason)
        self.assertEqual(w.reactions(), [])

    def test_only_its_own_acts(self):
        w = self.still()
        alice = self.enter(w)
        r = w.act(alice.act(w.manifest(), "poem.turn", {
            "acknowledgment": "x", "proposal": "y", "invitation": "z",
            "holds_open": True}))
        self.assertIsInstance(r, Refusal)
        self.assertIn("Unknown act type", r.reason)
        stranger = Individual("Mallory")
        r = w.act(_react(w, stranger, TWO_GLYCINES))
        self.assertIsInstance(r, Refusal)
        self.assertIn("not admitted", r.reason)


class TestTime(ChemistryCase):

    def test_each_accepted_act_lets_the_published_time_pass(self):
        # Even in a soup with no reactions of its own, the clock moves by
        # exactly the published time.
        w = self.still(seconds_per_act=2.5)
        alice = self.enter(w)
        self.assertEqual(w.world_time, 0.0)
        for k in range(1, 4):
            self.assertIsInstance(w.act(_react(w, alice, {
                "rule": "hydration of a carbonyl",
                "reactants": ["formaldehyde", "water"]})), Ack)
            self.assertEqual(w.world_time, 2.5 * k)
        w.act(_react(w, alice, {"rule": "alchemy", "reactants": ["water"]}))
        self.assertEqual(w.world_time, 7.5)        # a refusal takes none

    def test_the_soup_reacts_on_its_own_in_that_time(self):
        w = self.world()
        alice = self.enter(w)
        self.assertEqual(w.soup.events, 0)
        w.act(_react(w, alice, TWO_GLYCINES))
        # In a second of world time, glycine and its zwitterion, and
        # formaldehyde and its hydrate, have been changing into each other.
        self.assertGreater(w.soup.events, 10)
        self.assertGreater(_count(w, "glycine_zwitterion"), 0)
        # Each published reaction runs both ways: the soup's four
        # channels (two reactions, each with its reverse) all happened.
        used = {e["data"]["reaction"] for e in w.soup.log
                if e["kind"] == "react"}
        self.assertEqual(used, {0, 1, 2, 3})
        self.assertTrue(World.verify_log(w.soup.log))
        entry = [e for e in w.log_since(None) if e.kind == "reaction"][-1]
        self.assertEqual((entry.data["soup_time"], entry.data["soup_head"]),
                         (w.world_time, w.soup.log_head))

    def test_the_world_replays_exactly(self):
        def history(seed):
            w = self.world(seed=seed)
            alice = self.enter(w)
            for payload in (TWO_GLYCINES, TWO_GLYCINES, {
                    "rule": "hydration of a carbonyl",
                    "reactants": ["formaldehyde", "water"]}):
                w.act(_react(w, alice, payload))
            return w.soup.log_head, w.census()
        self.assertEqual(history(1), history(1))
        self.assertNotEqual(history(1)[0], history(2)[0])


class TestTheWorld(ChemistryCase):

    def test_leave(self):
        w = self.world(max_admitted=1)
        alice = self.enter(w)
        self.assertFalse(w.leave(alice.leave(w.manifest())).already_left)
        self.enter(w, "Bob")

    def test_conformance(self):
        self.assertTrue(run_conformance(self.world())["passed"])

    def test_end_to_end(self):
        w = self.still()
        alice, bob = self.enter(w, "Alice"), self.enter(w, "Bob")
        for who in (alice, bob, alice):
            self.assertIsInstance(w.act(_react(w, who, TWO_GLYCINES)), Ack)
        logged = [e for e in w.log_since(None) if e.kind == "reaction"]
        self.assertEqual([e.actor_token for e in logged],
                         [alice.token, bob.token, alice.token])
        self.assertEqual(
            [{k: r[k] for k in w.reactions()[0]}
             for r in reactions_from_log(w.log_since(None))],
            w.reactions())
        self.assertEqual(_count(w, "glycine"), 14)


class TestTwoWorlds(unittest.TestCase):

    def test_same_protocol_different_laws(self):
        poetry = PoetryWorld("world:poetry", "The Poetry World")
        chemistry = ChemistryWorld("world:chemistry", "The Chemistry World")
        for w in (poetry, chemistry):
            self.assertTrue(run_conformance(w)["passed"])

        alice = Individual("Alice")
        for w in (poetry, chemistry):
            self.assertIsInstance(w.petition(_in(w, alice)), Admission)
        turn_fields = {"acknowledgment": "seed", "proposal": "a poem line",
                       "invitation": "what next?", "holds_open": True}
        # Each act is signed for the world it is sent to, so each world's
        # law, not the signature check, decides.
        self.assertIsInstance(poetry.act(alice.act(
            poetry.manifest(), "poem.turn", turn_fields)), Ack)
        refused = poetry.act(_react(poetry, alice, TWO_GLYCINES))
        self.assertIsInstance(refused, Refusal)
        self.assertEqual(refused.reason, "Unknown act type: chemistry.react")
        self.assertIsInstance(
            chemistry.act(_react(chemistry, alice, TWO_GLYCINES)), Ack)
        refused = chemistry.act(alice.act(chemistry.manifest(), "poem.turn",
                                          turn_fields))
        self.assertIsInstance(refused, Refusal)
        self.assertEqual(refused.reason, "Unknown act type: poem.turn")

        def alices(w):
            return [e.kind for e in w.log_since(None)
                    if e.actor_token == alice.token]
        self.assertEqual(alices(poetry), ["admission", "turn", "act_refused"])
        self.assertEqual(alices(chemistry),
                         ["admission", "reaction", "act_refused"])


if __name__ == "__main__":
    unittest.main()
