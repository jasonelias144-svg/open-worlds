"""Chemistry layer 2: reactions as rules that keep atoms, charge and valence.

Expected products are real reactions with their real formulas.
"""
import random
import unittest

from chem import Builder
from chem import catalogue as cat
from chem.catalogue import CATALOGUE
from chem.reactions import Rule, balance
from chem.rules import (ACID_TO_AMINE, AMIDE_FORMATION, AMIDE_HYDROLYSIS,
                        CARBONYL_HYDRATION, CYANOHYDRIN_FORMATION, O_H_TO_O,
                        RULES)
from tests.test_chem_molecules import shuffled


def glycylglycine():
    """H2N-CH2-CO-NH-CH2-COOH, the simplest dipeptide (C4H8N2O3)."""
    return (Builder().atom("n1", "N").atom("ca1", "C").atom("c1", "C")
            .atom("o1", "O").atom("n2", "N").atom("ca2", "C").atom("c2", "C")
            .atom("o2", "O").atom("o3", "O")
            .bond("n1", "ca1").bond("ca1", "c1").bond("c1", "o1", 2)
            .bond("c1", "n2").bond("n2", "ca2").bond("ca2", "c2")
            .bond("c2", "o2", 2).bond("c2", "o3")
            .hydrogens("n1", 2).hydrogens("ca1", 2).hydrogens("n2", 1)
            .hydrogens("ca2", 2).hydrogens("o3", 1).build())


def methanediol():
    return (Builder().atom("c", "C").atom("o1", "O").atom("o2", "O")
            .bond("c", "o1").bond("c", "o2").hydrogens("c", 2)
            .hydrogens("o1", 1).hydrogens("o2", 1).build())


def carbonic_acid():
    return (Builder().atom("c", "C").atom("o", "O").atom("o1", "O")
            .atom("o2", "O").bond("c", "o", 2).bond("c", "o1").bond("c", "o2")
            .hydrogens("o1", 1).hydrogens("o2", 1).build())


def glycolonitrile():
    return (Builder().atom("o", "O").atom("c", "C").atom("cn", "C")
            .atom("n", "N").bond("o", "c").bond("c", "cn").bond("cn", "n", 3)
            .hydrogens("o", 1).hydrogens("c", 2).build())


def ids(molecules):
    return sorted(m.identity() for m in molecules)


class TestRealReactions(unittest.TestCase):
    def test_glycine_becomes_its_zwitterion(self):
        self.assertEqual(ACID_TO_AMINE.apply(cat.glycine()),
                         [(cat.glycine_zwitterion(),)])
        self.assertEqual(ACID_TO_AMINE.reverse().apply(cat.glycine_zwitterion()),
                         [(cat.glycine(),)])

    def test_water_self_ionization(self):
        outcomes = O_H_TO_O.apply(cat.water(), cat.water())
        self.assertEqual([ids(o) for o in outcomes],
                         [ids([cat.hydronium(), cat.hydroxide()])])

    def test_peptide_bond(self):
        outcomes = AMIDE_FORMATION.apply(cat.glycine(), cat.glycine())
        self.assertEqual([ids(o) for o in outcomes],
                         [ids([glycylglycine(), cat.water()])])
        self.assertEqual(glycylglycine().formula(), "C4H8N2O3")

    def test_hydrolysis_splits_the_dipeptide(self):
        outcomes = AMIDE_HYDROLYSIS.apply(glycylglycine(), cat.water())
        self.assertEqual([ids(o) for o in outcomes],
                         [ids([cat.glycine(), cat.glycine()])])

    def test_hydration(self):
        self.assertEqual(CARBONYL_HYDRATION.apply(cat.formaldehyde(), cat.water()),
                         [(methanediol(),)])
        self.assertEqual(CARBONYL_HYDRATION.apply(cat.carbon_dioxide(), cat.water()),
                         [(carbonic_acid(),)])
        self.assertEqual(carbonic_acid().formula(), "CH2O3")

    def test_cyanohydrin(self):
        self.assertEqual(
            CYANOHYDRIN_FORMATION.apply(cat.formaldehyde(), cat.hydrogen_cyanide()),
            [(glycolonitrile(),)])
        self.assertEqual(glycolonitrile().formula(), "C2H3NO")

    def test_no_reaction_without_the_groups(self):
        self.assertEqual(AMIDE_FORMATION.apply(cat.methane(), cat.ammonia()), [])
        self.assertEqual(CARBONYL_HYDRATION.apply(cat.methanol(), cat.water()), [])

    def test_every_reactant_must_take_part(self):
        # Glycine can react with itself, but a spectator methane may not
        # sneak into the outcome.
        self.assertTrue(AMIDE_FORMATION.apply(cat.glycine()))
        self.assertEqual(AMIDE_FORMATION.apply(cat.glycine(), cat.methane()), [])

    def test_two_amino_acids_make_two_dipeptides(self):
        # Sequence matters: glycine's acid with alanine's amine (Gly-Ala), or
        # alanine's acid with glycine's amine (Ala-Gly). Same formula,
        # different molecules.
        outcomes = AMIDE_FORMATION.apply(cat.glycine(), cat.alanine())
        self.assertEqual(len(outcomes), 2)
        dipeptides = [m for o in outcomes for m in o if m != cat.water()]
        self.assertEqual([m.formula() for m in dipeptides], ["C5H10N2O3"] * 2)
        self.assertNotEqual(dipeptides[0], dipeptides[1])

    def test_a_molecule_can_meet_itself(self):
        m = cat.glycine()
        self.assertEqual([ids(o) for o in AMIDE_FORMATION.apply(m, m)],
                         [ids([glycylglycine(), cat.water()])])

    def test_order_of_atoms_and_reactants_does_not_matter(self):
        rng = random.Random(11)
        expected = [ids(o) for o in AMIDE_FORMATION.apply(cat.glycine(), cat.alanine())]
        for _ in range(10):
            a, b = shuffled(cat.glycine(), rng), shuffled(cat.alanine(), rng)
            self.assertEqual([ids(o) for o in AMIDE_FORMATION.apply(a, b)], expected)
            self.assertEqual([ids(o) for o in AMIDE_FORMATION.apply(b, a)], expected)


class TestLawsOverTheWholeCatalogue(unittest.TestCase):
    """Every rule, on every catalogue molecule alone and every ordered pair:
    each outcome keeps atoms and charge, is valid, and running the reverse
    rule on the products gives the reactants back."""

    @classmethod
    def setUpClass(cls):
        cls.cases = []
        # The catalogue, plus products that only some reverse rules can use.
        molecules = [make() for make in CATALOGUE.values()] + [
            glycylglycine(), methanediol(), carbonic_acid(), glycolonitrile()]
        for rule in RULES.values():
            for a in molecules:
                for outcome in rule.apply(a):
                    cls.cases.append((rule, (a,), outcome))
                for b in molecules:
                    for outcome in rule.apply(a, b):
                        cls.cases.append((rule, (a, b), outcome))

    def test_there_is_something_to_check(self):
        self.assertGreater(len(self.cases), 100)
        self.assertEqual({rule.name for rule, _, _ in self.cases}, set(RULES))

    def test_atoms_and_charge_are_kept(self):
        for rule, reactants, products in self.cases:
            self.assertTrue(balance(reactants, products), (rule, reactants, products))
            self.assertAlmostEqual(sum(m.mass for m in reactants),
                                   sum(m.mass for m in products), places=9)

    def test_products_are_valid(self):
        for rule, reactants, products in self.cases:
            for m in products:
                self.assertEqual(m.problems(), [], (rule, reactants, products))

    def test_every_outcome_can_be_undone(self):
        reverses = {}
        for rule, reactants, products in self.cases:
            back = reverses.setdefault(rule.name, rule.reverse())
            self.assertIn(ids(reactants), [ids(o) for o in back.apply(*products)],
                          (rule, reactants, products))


class TestRulesMustObeyTheLaws(unittest.TestCase):
    def test_charge_must_be_conserved(self):
        with self.assertRaisesRegex(ValueError, "charge is not conserved"):
            Rule("make a charge", atoms={"n": "N", "h": "H"},
                 before={}, after={("n", "h"): 1}, charges_after={"n": +1, "h": +1})

    def test_valence_must_balance(self):
        with self.assertRaisesRegex(ValueError, "valence changes by"):
            Rule("five-bonded carbon", atoms={"c": "C", "h": "H", "x": "H"},
                 before={("x", "h"): 1}, after={("c", "h"): 1})

    def test_charge_must_be_allowed(self):
        with self.assertRaisesRegex(ValueError, "can't carry"):
            Rule("dication", atoms={"c": "C", "o": "O"}, before={("c", "o"): 1},
                 after={}, charges_after={"c": 2, "o": -2})

    def test_bad_rules_are_refused(self):
        bad = [
            dict(atoms={"c": "X"}, before={}, after={}),
            dict(atoms={"c": "C", "o": "O"}, before={("c", "z"): 1}, after={}),
            dict(atoms={"c": "C", "o": "O"}, before={("c", "o"): 4}, after={}),
            dict(atoms={"c": "C", "o": "O"}, before={("c", "o"): True}, after={}),
            dict(atoms={"c": "C", "o": "O"}, before={("c", "c"): 1}, after={}),
            dict(atoms={"c": "C", "o": "O"}, before={("c", "o"): 1, ("o", "c"): 1},
                 after={}),
            dict(atoms={"c": "C", "o": "O"}, before={("c", "o"): 1},
                 after={("c", "o"): 1}),
            # Bonds given as two-letter strings: otherwise a valid rule
            # (water's self-ionization), so only the pair check refuses it.
            dict(atoms={"o": "O", "h": "H", "p": "O"}, before={"oh": 1},
                 after={"ph": 1}, charges_after={"o": -1, "p": +1}),
        ]
        for spec in bad:
            with self.subTest(spec):
                with self.assertRaises(ValueError):
                    Rule("bad", **spec)

    def test_every_named_atom_must_connect_to_a_change(self):
        # A named atom that nothing touches would let a bystander molecule
        # count as a reactant (independent review of #4, note 1).
        with self.assertRaisesRegex(ValueError, "atom w is not connected"):
            Rule("with a bystander", atoms={"o1": "O", "h": "H", "o2": "O", "w": "C"},
                 before={("o1", "h"): 1}, after={("o2", "h"): 1},
                 charges_after={"o1": -1, "o2": +1})
        # ... and so would an unchanged group of named atoms on its own.
        with self.assertRaisesRegex(ValueError, "atom c is not connected"):
            Rule("with an idle group",
                 atoms={"o1": "O", "h": "H", "o2": "O", "c": "C", "x": "O"},
                 before={("o1", "h"): 1, ("c", "x"): 2},
                 after={("o2", "h"): 1, ("c", "x"): 2},
                 charges_after={"o1": -1, "o2": +1})
        # Unchanged atoms bonded into the change are fine: they are context.
        self.assertTrue(ACID_TO_AMINE.apply(cat.glycine()))

    def test_reverse_of_reverse_behaves_the_same(self):
        twice = AMIDE_FORMATION.reverse().reverse()
        self.assertEqual([ids(o) for o in twice.apply(cat.glycine(), cat.glycine())],
                         [ids(o) for o in AMIDE_FORMATION.apply(cat.glycine(), cat.glycine())])


class TestKnownLimits(unittest.TestCase):
    def test_rules_do_not_know_strain(self):
        # Glycine condensing with itself would make a three-membered ring
        # (an alpha-lactam). Real chemistry hardly does this; the rule can't
        # tell. Energy belongs to layer 3.
        outcomes = AMIDE_FORMATION.apply(cat.glycine())
        self.assertEqual([[m.formula() for m in o] for o in outcomes],
                         [["C2H3NO", "H2O"]])


if __name__ == "__main__":
    unittest.main()
