"""The sketch's chemistry world: its tests for component 5, ported.

Two failed in the sketch. Its formula test used calcium, which its
element table lacked. Its two-worlds test counted log entries, but the
conformance test it ran first had written to both logs; here it counts
Alice's entries.
"""
import unittest

from multiverse.chemistry_world import (ELEMENTS, ChemistryWorld,
                                        ChemistryWorldLaw, parse_formula,
                                        reaction_balances,
                                        reactions_from_log)
from multiverse.conformance import run_conformance
from multiverse.identity import create_identity
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import Ack, Act, Admission, Petition, Refusal


class KeyBomb(str):
    """A key that hashes like the text it claims to be, so a dict lookup
    for that text calls its __eq__, which raises."""
    def __hash__(self): return str.__hash__(str(self))
    def __eq__(self, other): raise ValueError("no equality")


def _petition(name, token):
    return Petition(petitioner_token=token, petitioner_name=name,
                    passport_admissions=(), message=f"{name} petitions.")


def _reaction(actor, substrates, products, catalyst=None):
    payload = {"substrates": substrates, "products": products}
    if catalyst is not None:
        payload["catalyst"] = catalyst
    return Act(actor_token=actor, type="chemistry.react", payload=payload)


def _m(formula, count=1):
    return {"formula": formula, "count": count}


WATER = ([_m("H2", 2), _m("O2")], [_m("H2O", 2)])
METHANE = ([_m("CH4"), _m("O2", 2)], [_m("CO2"), _m("H2O", 2)])
NEUTRAL = ([_m("NH4+"), _m("OH-")], [_m("NH3"), _m("H2O")])


class TestFormulas(unittest.TestCase):

    def test_element_table(self):
        for symbol in ("H", "C", "N", "O", "Ca"):
            self.assertIn(symbol, ELEMENTS)
        self.assertEqual(len(ELEMENTS), 9)

    def test_parse_simple_formula(self):
        for formula, atoms in [("H2O", {"H": 2, "O": 1}),
                               ("CH4", {"C": 1, "H": 4}),
                               ("C2H6O", {"C": 2, "H": 6, "O": 1}),
                               ("O2", {"O": 2}),
                               ("NaCl", {"Na": 1, "Cl": 1})]:
            with self.subTest(formula=formula):
                m = parse_formula(formula)
                self.assertEqual(m.atoms, atoms)
                self.assertEqual(m.charge, 0)

    def test_parse_charges(self):
        for formula, atoms, charge in [("NH4+", {"N": 1, "H": 4}, 1),
                                       ("OH-", {"O": 1, "H": 1}, -1),
                                       ("SO4-2", {"S": 1, "O": 4}, -2),
                                       ("Ca+2", {"Ca": 1}, 2)]:
            with self.subTest(formula=formula):
                m = parse_formula(formula)
                self.assertEqual(m.atoms, atoms)
                self.assertEqual(m.charge, charge)

    def test_parse_rejects(self):
        for formula in ("Xx2O", "2H2O", "", "+", "h2o", None, "H0O",
                        "C00"):
            with self.subTest(formula=formula), self.assertRaises(ValueError):
                parse_formula(formula)


class TestBalance(unittest.TestCase):

    def test_balanced(self):
        cases = [WATER, METHANE, NEUTRAL,
                 ([_m("NH4+")], [_m("NH3"), _m("H+")])]
        for subs, prods in cases:
            with self.subTest(subs=subs):
                ok, reason = reaction_balances(subs, prods)
                self.assertTrue(ok, reason)

    def test_unbalanced_atoms(self):
        ok, reason = reaction_balances([_m("H2"), _m("O2")], [_m("H2O")])
        self.assertFalse(ok)
        self.assertIn("imbalance", reason.lower())

    def test_unbalanced_charge(self):
        ok, reason = reaction_balances([_m("NH4+")], [_m("NH4")])
        self.assertFalse(ok)
        self.assertIn("Charge", reason)

    def test_bad_formula(self):
        ok, reason = reaction_balances([_m("Xx2")], [_m("H2O")])
        self.assertFalse(ok)
        self.assertIn("Unknown element", reason)

    def test_bad_counts_and_shapes(self):
        # In the sketch, a count of "2" multiplied strings and -1 balanced
        # by subtraction.
        for subs in ([_m("H2", "2"), _m("O2")], [_m("H2", -2), _m("O2")],
                     [_m("H2", 0)], [_m("H2", True)], [_m("H2", 2.0)],
                     ["H2"], [{"formula": "H2"}], [_m(["H2"])]):
            with self.subTest(subs=subs):
                ok, reason = reaction_balances(subs, [_m("H2O", 2)])
                self.assertFalse(ok)
                self.assertIn("Formula error", reason)


class ChemistryCase(unittest.TestCase):

    def world(self, **law):
        return ChemistryWorld("world:chemistry", "The Chemistry World",
                              law=ChemistryWorldLaw(**law) if law else None)

    def enter(self, w, name="Alice"):
        person = create_identity(name)
        self.assertIsInstance(w.petition(_petition(name, person.token)),
                              Admission)
        return person


class TestChemistryWorld(ChemistryCase):

    def test_law_is_readable(self):
        doc = ChemistryWorldLaw().describe()
        for part in ("chemistry.react", "balance", "may leave at any time"):
            self.assertIn(part, doc)

    def test_petition_and_act(self):
        w = self.world()
        alice = self.enter(w)
        self.assertIsInstance(w.act(_reaction(alice.token, *WATER)), Ack)
        self.assertEqual(len(w.reactions()), 1)
        self.assertEqual(w.molecules(), {"H2", "O2", "H2O"})

    def test_refuses_unbalanced(self):
        w = self.world()
        alice = self.enter(w)
        bad = w.act(_reaction(alice.token, [_m("H2"), _m("O2")], [_m("H2O")]))
        self.assertIsInstance(bad, Refusal)
        self.assertIn("balance", bad.reason.lower())
        self.assertEqual(w.reactions(), [])

    def test_refuses_missing_sides(self):
        w = self.world()
        alice = self.enter(w)
        for subs, prods in (([], [_m("H2O")]), ([_m("H2O")], None),
                            ("H2O", [_m("H2O")])):
            with self.subTest(subs=subs, prods=prods):
                r = w.act(_reaction(alice.token, subs, prods))
                self.assertIsInstance(r, Refusal)
                self.assertIn("required", r.reason)

    def test_plain_values_all_the_way_down(self):
        class Odd:
            pass

        w = self.world()
        alice = self.enter(w)
        for payload in ({KeyBomb("substrates"): []},
                        {"substrates": [_m("H2", 2),
                                        _m("O2") | {"note": Odd()}],
                         "products": [_m("H2O", 2)]}):
            with self.subTest(payload=list(payload)):
                r = w.act(Act(alice.token, "chemistry.react", payload))
                self.assertIsInstance(r, Refusal)
                self.assertIn("plain", r.reason)
        self.assertEqual(w.reactions(), [])

    def test_only_formula_and_count_are_kept(self):
        w = self.world()
        alice = self.enter(w)
        r = w.act(_reaction(alice.token,
                            [_m("H2", 2), _m("O2") | {"note": "x"}],
                            [_m("H2O", 2)]))
        self.assertIsInstance(r, Ack)
        self.assertEqual(w.reactions()[0]["substrates"],
                         [_m("H2", 2), _m("O2")])

    def test_catalyst(self):
        w = self.world()
        alice = self.enter(w)
        r = w.act(_reaction(alice.token, *WATER, catalyst={"Pt": 1}))
        self.assertIsInstance(r, Refusal)
        self.assertIn("catalyst", r.reason)
        self.assertIsInstance(
            w.act(_reaction(alice.token, *WATER, catalyst="Pt")), Ack)
        self.assertEqual(w.reactions()[0]["catalyst"], "Pt")

    def test_refuses_poetry_act(self):
        w = self.world()
        alice = self.enter(w)
        r = w.act(Act(actor_token=alice.token, type="poem.turn", payload={
            "acknowledgment": "x", "proposal": "y", "invitation": "z",
            "holds_open": True}))
        self.assertIsInstance(r, Refusal)
        self.assertIn("Unknown act type", r.reason)

    def test_refuses_strangers(self):
        w = self.world()
        stranger = create_identity("Mallory")
        r = w.act(_reaction(stranger.token, *WATER))
        self.assertIsInstance(r, Refusal)
        self.assertIn("not admitted", r.reason)

    def test_settles_when_nothing_new(self):
        w = self.world()
        alice = self.enter(w)
        for i in range(5):
            self.assertFalse(w.is_converged())
            w.act(_reaction(alice.token, *WATER))
        self.assertTrue(w.is_converged())
        r = w.act(_reaction(alice.token, *WATER))
        self.assertIsInstance(r, Refusal)
        self.assertIn("equilibrium", r.reason)

    def test_not_settled_with_new_molecules(self):
        w = self.world()
        alice = self.enter(w)
        for subs, prods in [WATER, METHANE,
                            ([_m("N2"), _m("H2", 3)], [_m("NH3", 2)]),
                            ([_m("Na", 2), _m("Cl2")], [_m("NaCl", 2)]),
                            ([_m("S"), _m("O2")], [_m("SO2")])]:
            self.assertIsInstance(w.act(_reaction(alice.token, subs, prods)),
                                  Ack)
        self.assertFalse(w.is_converged())

    def test_reaction_limit(self):
        w = self.world(max_reactions=1)
        alice = self.enter(w)
        w.act(_reaction(alice.token, *WATER))
        r = w.act(_reaction(alice.token, *METHANE))
        self.assertIsInstance(r, Refusal)
        self.assertIn("limit", r.reason)

    def test_leave(self):
        w = self.world(max_admitted=1)
        alice = self.enter(w)
        self.assertFalse(w.leave(alice.token).already_left)
        self.enter(w, "Bob")

    def test_conformance(self):
        self.assertTrue(run_conformance(self.world())["passed"])

    def test_end_to_end(self):
        w = self.world()
        alice, bob = self.enter(w, "Alice"), self.enter(w, "Bob")
        for who, reaction in ((alice, METHANE), (bob, WATER),
                              (alice, NEUTRAL)):
            self.assertIsInstance(w.act(_reaction(who.token, *reaction)), Ack)
        reactions = reactions_from_log(w.log_since(None))
        self.assertEqual([r["actor_name"] for r in reactions],
                         ["Alice", "Bob", "Alice"])
        self.assertEqual(reactions, w.reactions())


class TestTwoWorlds(unittest.TestCase):

    def test_same_protocol_different_laws(self):
        poetry = PoetryWorld("world:poetry", "The Poetry World")
        chemistry = ChemistryWorld("world:chemistry", "The Chemistry World")
        for w in (poetry, chemistry):
            self.assertTrue(run_conformance(w)["passed"])

        alice = create_identity("Alice")
        for w in (poetry, chemistry):
            self.assertIsInstance(w.petition(_petition("Alice", alice.token)),
                                  Admission)
        turn = Act(actor_token=alice.token, type="poem.turn", payload={
            "acknowledgment": "seed", "proposal": "a poem line",
            "invitation": "what next?", "holds_open": True})
        reaction = _reaction(alice.token, *WATER)
        self.assertIsInstance(poetry.act(turn), Ack)
        self.assertIsInstance(poetry.act(reaction), Refusal)
        self.assertIsInstance(chemistry.act(reaction), Ack)
        self.assertIsInstance(chemistry.act(turn), Refusal)

        def alices(w):
            return [e.kind for e in w.log_since(None)
                    if e.actor_token == alice.token]
        self.assertEqual(alices(poetry), ["admission", "turn", "act_refused"])
        self.assertEqual(alices(chemistry),
                         ["admission", "reaction", "act_refused"])


if __name__ == "__main__":
    unittest.main()
