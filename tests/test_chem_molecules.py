"""Chemistry layer 1: elements, molecules and molecular identity.

The expected values are chemistry facts (valences, Hill formulas, standard
atomic weights), not outputs copied from the code.
"""
import random
import unittest
from collections import Counter

from chem import Atom, Bond, Builder, Molecule, valence
from chem import catalogue as cat
from chem.catalogue import CATALOGUE


def shuffled(m: Molecule, rng: random.Random) -> Molecule:
    """The same molecule with its atoms listed in a random order and each
    bond written in a random direction."""
    order = list(range(len(m.atoms)))
    rng.shuffle(order)
    new_index = {old: new for new, old in enumerate(order)}
    atoms = [m.atoms[old] for old in order]
    bonds = []
    for b in m.bonds:
        ends = [new_index[b.a], new_index[b.b]]
        rng.shuffle(ends)
        bonds.append(Bond(ends[0], ends[1], b.order))
    rng.shuffle(bonds)
    return Molecule(atoms, bonds)


def colour_refinement_histograms(m1: Molecule, m2: Molecule):
    """Plain colour refinement (1-dimensional Weisfeiler-Leman), the basis of
    a typical molecular hash, run on both molecules together so their colours
    mean the same thing. Returns each molecule's multiset of stable colours:
    equal multisets mean refinement can't tell the two apart."""
    atoms = list(m1.atoms) + list(m2.atoms)
    nbrs = [[] for _ in atoms]
    for offset, m in ((0, m1), (len(m1.atoms), m2)):
        for b in m.bonds:
            nbrs[b.a + offset].append((b.b + offset, b.order))
            nbrs[b.b + offset].append((b.a + offset, b.order))
    colours = [(a.symbol, a.charge) for a in atoms]
    for _ in range(len(atoms)):
        keys = [(colours[i], tuple(sorted((colours[j], o) for j, o in nbrs[i])))
                for i in range(len(atoms))]
        rank = {k: r for r, k in enumerate(sorted(set(keys)))}
        colours = [rank[k] for k in keys]
    n1 = len(m1.atoms)
    return Counter(colours[:n1]), Counter(colours[n1:])


def ring(builder: Builder, names, hydrogens):
    for name, h in zip(names, hydrogens):
        builder.atom(name, "C").hydrogens(name, h)
    for k in range(len(names)):
        builder.bond(names[k], names[(k + 1) % len(names)])
    return builder


def decalin() -> Molecule:
    """Two six-membered rings sharing an edge (C10H18)."""
    b = Builder()
    names = [f"c{k}" for k in range(10)]
    for k, name in enumerate(names):
        b.atom(name, "C").hydrogens(name, 1 if k in (0, 5) else 2)
    for k in range(9):
        b.bond(names[k], names[k + 1])
    b.bond("c9", "c0").bond("c0", "c5")
    return b.build()


def bicyclopentyl() -> Molecule:
    """Two five-membered rings joined by a single bond (C10H18)."""
    b = Builder()
    ring(b, ["a0", "a1", "a2", "a3", "a4"], [1, 2, 2, 2, 2])
    ring(b, ["b0", "b1", "b2", "b3", "b4"], [1, 2, 2, 2, 2])
    return b.bond("a0", "b0").build()


class TestValence(unittest.TestCase):
    def test_neutral_valences(self):
        self.assertEqual([valence(s) for s in "HCNO"], [1, 4, 3, 2])

    def test_charged_valences(self):
        self.assertEqual(valence("N", +1), 4)   # ammonium
        self.assertEqual(valence("N", -1), 2)   # amide ion
        self.assertEqual(valence("O", +1), 3)   # hydronium
        self.assertEqual(valence("O", -1), 1)   # hydroxide
        self.assertEqual(valence("C", +1), 3)   # carbocation
        self.assertEqual(valence("C", -1), 3)   # carbanion
        self.assertEqual(valence("H", +1), 0)   # proton
        self.assertEqual(valence("H", -1), 0)   # hydride

    def test_outside_this_layer(self):
        self.assertIsNone(valence("Na"))
        self.assertIsNone(valence("C", 2))
        self.assertIsNone(valence("O", True))


class TestCatalogue(unittest.TestCase):
    FORMULAS = {
        "hydrogen": ("H2", 0), "proton": ("H", 1), "water": ("H2O", 0),
        "hydroxide": ("HO", -1), "hydronium": ("H3O", 1),
        "ammonia": ("H3N", 0), "ammonium": ("H4N", 1),
        "methane": ("CH4", 0), "carbon_dioxide": ("CO2", 0),
        "formaldehyde": ("CH2O", 0), "hydrogen_cyanide": ("CHN", 0),
        "carbon_monoxide": ("CO", 0), "cyanide": ("CN", -1),
        "formamide": ("CH3NO", 0), "urea": ("CH4N2O", 0),
        "methanol": ("CH4O", 0), "ethanol": ("C2H6O", 0),
        "dimethyl_ether": ("C2H6O", 0), "methylamine": ("CH5N", 0),
        "formic_acid": ("CH2O2", 0), "glycine": ("C2H5NO2", 0),
        "glycine_zwitterion": ("C2H5NO2", 0), "alanine": ("C3H7NO2", 0),
        "neopentane": ("C5H12", 0), "benzene": ("C6H6", 0),
    }

    def test_every_entry_has_a_known_formula(self):
        self.assertEqual(set(CATALOGUE), set(self.FORMULAS))

    def test_formulas_and_charges(self):
        for name, make in CATALOGUE.items():
            with self.subTest(name):
                m = make()
                self.assertEqual((m.formula(), m.charge), self.FORMULAS[name])
                self.assertEqual(m.problems(), [])

    def test_masses(self):
        self.assertAlmostEqual(cat.water().mass, 18.015, places=3)
        self.assertAlmostEqual(cat.glycine().mass, 75.067, places=3)
        self.assertAlmostEqual(cat.carbon_dioxide().mass, 44.009, places=3)

    def test_all_identities_distinct(self):
        identities = {name: make().identity() for name, make in CATALOGUE.items()}
        self.assertEqual(len(set(identities.values())), len(identities))


class TestValidity(unittest.TestCase):
    def test_five_bonded_carbon(self):
        m = Builder().atom("c", "C").hydrogens("c", 5).build(validate=False)
        self.assertIn("atom 0 (C) has 5 bonds, needs 4", m.problems())

    def test_neutral_nitrogen_with_four_bonds(self):
        m = Builder().atom("n", "N").hydrogens("n", 4).build(validate=False)
        self.assertFalse(m.is_valid())
        self.assertTrue(cat.ammonium().is_valid())

    def test_hydroxide_needs_its_charge(self):
        m = Builder().atom("o", "O").hydrogens("o", 1).build(validate=False)
        self.assertIn("atom 0 (O) has 1 bonds, needs 2", m.problems())

    def test_disconnected(self):
        m = Molecule([Atom("H", 1), Atom("H", 1)], [])
        self.assertIn("not connected: these are separate molecules", m.problems())

    def test_build_rejects_invalid(self):
        with self.assertRaises(ValueError):
            Builder().atom("c", "C").hydrogens("c", 3).build()

    def test_structural_errors(self):
        bad = [
            ([], []),
            ([Atom("X")], []),
            ([Atom("C"), Atom("C")], [Bond(0, 2)]),
            ([Atom("C")], [Bond(0, 0)]),
            ([Atom("C"), Atom("C")], [Bond(0, 1, 4)]),
            ([Atom("C"), Atom("C")], [Bond(0, 1), Bond(1, 0)]),
            ([Atom("C"), Atom("C")], [Bond(0, 1, True)]),
            ([Atom("C", True)], []),
            (["C"], []),
        ]
        for atoms, bonds in bad:
            with self.subTest(atoms=atoms, bonds=bonds):
                with self.assertRaises(ValueError):
                    Molecule(atoms, bonds)

    def test_molecule_cannot_be_changed(self):
        m = cat.water()
        with self.assertRaises(AttributeError):
            m.atoms = ()


class TestIdentity(unittest.TestCase):
    def test_isomers_are_different_molecules(self):
        self.assertEqual(cat.ethanol().formula(), cat.dimethyl_ether().formula())
        self.assertNotEqual(cat.ethanol(), cat.dimethyl_ether())
        self.assertNotEqual(cat.glycine(), cat.glycine_zwitterion())

    def test_order_does_not_matter(self):
        rng = random.Random(20261112)
        for name, make in CATALOGUE.items():
            m = make()
            for _ in range(20):
                with self.subTest(name):
                    s = shuffled(m, rng)
                    self.assertEqual(s.identity(), m.identity())
                    self.assertEqual(s, m)
                    self.assertEqual(hash(s), hash(m))

    def test_benzene_kekule_structures_are_one_graph(self):
        b = Builder()
        for k in range(6):
            b.atom(f"c{k}", "C").hydrogens(f"c{k}", 1)
        for k in range(6):
            b.bond(f"c{k}", f"c{(k + 1) % 6}", 1 if k % 2 == 0 else 2)
        self.assertEqual(b.build(), cat.benzene())

    def test_resonance_forms_are_different_graphs(self):
        # The documented limitation: one molecule, two identities.
        separated = (Builder().atom("c", "C").atom("o", "O", -1)
                     .atom("n", "N", +1).bond("c", "o").bond("c", "n", 2)
                     .hydrogens("c", 1).hydrogens("n", 2).build())
        self.assertEqual(separated.formula(), cat.formamide().formula())
        self.assertNotEqual(separated, cat.formamide())

    def test_where_colour_refinement_alone_fails(self):
        d, b = decalin(), bicyclopentyl()
        self.assertEqual(d.formula(), b.formula())
        # Colour refinement can't tell these two apart, so a hash built on it
        # alone would call them one molecule ...
        histogram_d, histogram_b = colour_refinement_histograms(d, b)
        self.assertEqual(histogram_d, histogram_b)
        # (The helper does see a difference when there is one.)
        histogram_e, histogram_m = colour_refinement_histograms(
            cat.ethanol(), cat.dimethyl_ether())
        self.assertNotEqual(histogram_e, histogram_m)
        # ... the search does.
        self.assertNotEqual(d, b)
        rng = random.Random(7)
        for _ in range(10):
            self.assertEqual(shuffled(d, rng), d)
            self.assertEqual(shuffled(b, rng), b)

    def test_unusual_hydrogens_stay_in_the_identity(self):
        # A hydrogen that isn't an ordinary one (here a stray proton) must
        # not vanish from the identity, even in an invalid molecule.
        water = cat.water()
        with_proton = Molecule(list(water.atoms) + [Atom("H", 1)], water.bonds)
        self.assertNotEqual(with_proton, water)
        # An H2 unit hanging off carbon is not two ordinary hydrogens.
        odd = Molecule([Atom("C"), Atom("H"), Atom("H")],
                       [Bond(0, 1), Bond(1, 2)])
        methylene_like = Molecule([Atom("C"), Atom("H"), Atom("H")],
                                  [Bond(0, 1), Bond(0, 2)])
        self.assertNotEqual(odd, methylene_like)

    def test_bond_order_matters(self):
        single = Molecule([Atom("C"), Atom("C")], [Bond(0, 1, 1)])
        double = Molecule([Atom("C"), Atom("C")], [Bond(0, 1, 2)])
        self.assertNotEqual(single, double)
        # Two valid molecules with the same atoms, hydrogens and skeleton,
        # differing only in where the double bonds are: the two Kekule
        # structures of o-xylene. The bond between the two methyl-bearing
        # carbons is double in one and single in the other, so no relabelling
        # turns one into the other. (Real chemistry calls them one molecule;
        # this is the resonance limitation again.)
        def o_xylene(first_bond_double: bool) -> Molecule:
            b = Builder()
            for k in range(6):
                b.atom(f"c{k}", "C").hydrogens(f"c{k}", 0 if k < 2 else 1)
            for k in range(2):
                b.atom(f"m{k}", "C").bond(f"c{k}", f"m{k}").hydrogens(f"m{k}", 3)
            for k in range(6):
                double = (k % 2 == 0) == first_bond_double
                b.bond(f"c{k}", f"c{(k + 1) % 6}", 2 if double else 1)
            return b.build()
        self.assertNotEqual(o_xylene(True), o_xylene(False))
        rng = random.Random(3)
        self.assertEqual(shuffled(o_xylene(True), rng), o_xylene(True))

    def test_charge_matters(self):
        self.assertNotEqual(cat.ammonium().identity(),
                            Builder().atom("n", "N").hydrogens("n", 4)
                            .build(validate=False).identity())


if __name__ == "__main__":
    unittest.main()
