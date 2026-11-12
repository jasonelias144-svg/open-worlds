"""Chemistry layer 1: elements, molecules and molecular identity.

The expected values are chemistry facts (valences, Hill formulas, standard
atomic weights), not outputs copied from the code.
"""
import itertools
import random
import unittest
from collections import Counter
from unittest import mock

from chem import Atom, Bond, Builder, Molecule, valence
from chem import catalogue as cat
from chem import molecule as molecule_module
from chem.molecule import _canonical_form
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


def random_cubic_hydrocarbon(n: int, seed: int) -> Molecule:
    """CnHn on a random connected cubic graph: each carbon bonded to three
    carbons and one hydrogen. Every carbon looks the same to colour
    refinement, so the search has to do all the work, and the graph usually
    has few or no symmetries, so a search that skips branches or keeps the
    wrong leaf gives answers that depend on the order of the atoms."""
    rng = random.Random(seed)
    while True:
        stubs = [v for v in range(n) for _ in range(3)]
        rng.shuffle(stubs)
        edges = {tuple(sorted(stubs[k:k + 2])) for k in range(0, len(stubs), 2)}
        if len(edges) * 2 != len(stubs) or any(a == b for a, b in edges):
            continue
        seen, todo = {0}, [0]
        while todo:
            v = todo.pop()
            for a, b in edges:
                for x, y in ((a, b), (b, a)):
                    if x == v and y not in seen:
                        seen.add(y)
                        todo.append(y)
        if len(seen) == n:
            break
    atoms = [Atom("C")] * n + [Atom("H")] * n
    bonds = [Bond(a, b) for a, b in sorted(edges)]
    bonds += [Bond(v, n + v) for v in range(n)]
    return Molecule(atoms, bonds)


def brute_force_form(m: Molecule):
    """The smallest description of the graph over every ordering of its
    atoms: slow, but exact by definition."""
    best = None
    for order in itertools.permutations(range(len(m.atoms))):
        pos = {v: k for k, v in enumerate(order)}
        form = (tuple((m.atoms[v].symbol, m.atoms[v].charge) for v in order),
                tuple(sorted((min(pos[b.a], pos[b.b]), max(pos[b.a], pos[b.b]), b.order)
                             for b in m.bonds)))
        if best is None or form < best:
            best = form
    return best


def random_small_graph(rng: random.Random) -> Molecule:
    """Any graph on 1-6 atoms of H, C and O, with any charge and bond order,
    valid or not, connected or not."""
    n = rng.randint(1, 6)
    atoms = [Atom(rng.choice("HHCO"), rng.choice((-1, 0, 0, 0, 1))) for _ in range(n)]
    bonds = [Bond(i, j, rng.choice((1, 1, 1, 2, 3)))
             for i in range(n) for j in range(i + 1, n) if rng.random() < 0.45]
    return Molecule(atoms, bonds)


def graph(n, edges, hydrogens=False) -> Molecule:
    """All-carbon graph; with hydrogens=True each carbon also gets one H."""
    atoms = [Atom("C")] * n + ([Atom("H")] * n if hydrogens else [])
    bonds = [Bond(a, b) for a, b in edges]
    if hydrogens:
        bonds += [Bond(v, n + v) for v in range(n)]
    return Molecule(atoms, bonds)


PETERSEN = ([(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)]
            + [(5 + i, 5 + (i + 2) % 5) for i in range(5)])
ROOK_4X4 = [(a, b) for a in range(16) for b in range(a + 1, 16)
            if (a // 4 == b // 4) != (a % 4 == b % 4)]
SHRIKHANDE = sorted({tuple(sorted((x, ((x // 4 + di) % 4) * 4 + (x % 4 + dj) % 4)))
                     for x in range(16) for di, dj in ((0, 1), (1, 0), (1, 1))})
CUBE = [(a, a ^ bit) for a in range(8) for bit in (1, 2, 4) if a < a ^ bit]


def waters(k: int) -> Molecule:
    """k separate water molecules in one graph (invalid, but allowed)."""
    atoms, bonds = [], []
    for _ in range(k):
        o = len(atoms)
        atoms += [Atom("O"), Atom("H"), Atom("H")]
        bonds += [Bond(o, o + 1), Bond(o, o + 2)]
    return Molecule(atoms, bonds)


def branched_alkane(levels: int) -> Molecule:
    """A central carbon with four identical branches, each carbon branching
    into three: levels=2 is tetra-tert-butylmethane (C17H36), levels=3 is
    C53H108."""
    b = Builder().atom("r", "C")
    count = [0]

    def grow(parent, depth):
        name = f"x{count[0]}"
        count[0] += 1
        b.atom(name, "C").bond(parent, name)
        if depth == 0:
            b.hydrogens(name, 3)
        else:
            for _ in range(3):
                grow(name, depth - 1)
    for _ in range(4):
        grow("r", levels - 1)
    return b.build()


def copies_on_a_hub(part: Molecule, k: int, rng: random.Random) -> Molecule:
    """k copies of a graph, each joined by one bond to a shared hub atom:
    symmetric by construction."""
    atoms, bonds = [Atom("N")], []
    anchor = rng.randrange(len(part.atoms))
    for _ in range(k):
        offset = len(atoms)
        atoms += part.atoms
        bonds += [Bond(b.a + offset, b.b + offset, b.order) for b in part.bonds]
        bonds.append(Bond(0, offset + anchor))
    return Molecule(atoms, bonds)


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


class TestSymmetryPruning(unittest.TestCase):
    """The pruned search must give exactly the same identity string as the
    full search, which tries every branch. Pruning may only skip branches
    whose answers are already known."""

    def assert_same(self, m: Molecule, full_cap: int = 20_000) -> bool:
        with mock.patch.object(molecule_module, "MAX_SEARCH_LEAVES", full_cap):
            try:
                full = _canonical_form(m, prune=False)
            except ValueError:
                return False      # too slow to check the long way
        self.assertEqual(_canonical_form(m, prune=True), full)
        return True

    def test_random_small_graphs(self):
        rng = random.Random(99)
        for _ in range(300):
            self.assertTrue(self.assert_same(random_small_graph(rng)))

    def test_graphs_refinement_cannot_split(self):
        for edges, n, h in [(PETERSEN, 10, True), (CUBE, 8, True),
                            (ROOK_4X4, 16, False), (SHRIKHANDE, 16, False)]:
            self.assertTrue(self.assert_same(graph(n, edges, h)))
        for n, seed in [(10, 1), (10, 2), (12, 3), (12, 4), (12, 5), (14, 6)]:
            self.assertTrue(self.assert_same(random_cubic_hydrocarbon(n, seed)))
        for k in (2, 3, 4, 5, 6):
            self.assertTrue(self.assert_same(waters(k)))
        self.assertTrue(self.assert_same(branched_alkane(2), full_cap=40_000))
        for make in CATALOGUE.values():
            self.assertTrue(self.assert_same(make()))

    def test_symmetric_by_construction(self):
        rng = random.Random(2026)
        checked = 0
        for _ in range(120):
            part = random_small_graph(rng)
            if len(part.atoms) > 4:
                continue
            checked += self.assert_same(copies_on_a_hub(part, rng.choice((2, 3)), rng))
        self.assertGreater(checked, 40)

    def test_rigid_parts_beside_symmetric_ones(self):
        # Two different rigid cubic hydrocarbons (refinement can't tell
        # their carbons apart) beside identical ammonias. The search must
        # go two rigid levels deep before reaching the symmetric choice, so
        # jumping back too far after a symmetric match skips leaves that
        # matter. Each case here caught such a planted bug.
        for n, seed, k in [(10, 3, 2), (10, 8, 3), (12, 1, 2), (12, 3, 2)]:
            parts = [random_cubic_hydrocarbon(n, seed),
                     random_cubic_hydrocarbon(n, seed + 50)] + [cat.ammonia()] * k
            atoms, bonds = [], []
            for part in parts:
                offset = len(atoms)
                atoms += part.atoms
                bonds += [Bond(b.a + offset, b.b + offset, b.order) for b in part.bonds]
            m = Molecule(atoms, bonds)
            with mock.patch.object(molecule_module, "MAX_SEARCH_LEAVES", 10 ** 6):
                full = _canonical_form(m, prune=False)
            rng = random.Random(seed * 10 + k)
            for version in [m] + [shuffled(m, rng) for _ in range(4)]:
                with self.subTest(n=n, seed=seed, k=k):
                    self.assertEqual(_canonical_form(version, prune=True), full)

    def test_orbits_only_from_automorphisms_fixing_the_choices_so_far(self):
        # The 4x4 rook's graph with one 2x2 square twisted. Taking orbits
        # from every automorphism found, not only those fixing the choices
        # made so far, gives a wrong identity here. (Found by the
        # independent review of #5.)
        edges = sorted(set(ROOK_4X4) - {(0, 4), (1, 5)} | {(0, 5), (1, 4)})
        m = graph(16, edges)
        self.assertEqual(_canonical_form(m), _canonical_form(m, prune=False))

    def test_rook_and_shrikhande_differ(self):
        # Strongly regular with the same parameters: refinement can't tell
        # them apart at all.
        self.assertNotEqual(graph(16, ROOK_4X4), graph(16, SHRIKHANDE))

    def test_symmetric_molecules_need_few_leaves(self):
        # Without pruning, 9 waters needed hundreds of thousands of leaves
        # and C53H108 reached the old cap of 200,000 after tens of seconds.
        rng = random.Random(4)
        hard = [waters(9), waters(20), branched_alkane(2), branched_alkane(3),
                graph(16, ROOK_4X4), graph(10, PETERSEN, True)]
        with mock.patch.object(molecule_module, "MAX_SEARCH_LEAVES", 100):
            for m in hard:
                self.assertEqual({shuffled(m, rng).identity() for _ in range(3)},
                                 {m.identity()})
        self.assertEqual(branched_alkane(3).formula(), "C53H108")


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
        # A charged hydrogen, or one with a double bond, is not ordinary.
        c_h = Molecule([Atom("C"), Atom("H")], [Bond(0, 1)])
        self.assertNotEqual(Molecule([Atom("C"), Atom("H", 1)], [Bond(0, 1)]), c_h)
        self.assertNotEqual(Molecule([Atom("C"), Atom("H")], [Bond(0, 1, 2)]), c_h)
        # Folded hydrogens still count: water is not a bare oxygen.
        self.assertNotEqual(cat.water(), Molecule([Atom("O")], []))

    def test_search_must_explore_and_keep_the_least_leaf(self):
        rng = random.Random(1112)
        for n, seed in [(10, 1), (10, 2), (12, 3), (12, 4), (12, 5), (14, 6)]:
            m = random_cubic_hydrocarbon(n, seed)
            with self.subTest(n=n, seed=seed):
                self.assertEqual(m.problems(), [])
                # Refinement leaves every carbon in one colour.
                histogram, _ = colour_refinement_histograms(m, m)
                self.assertEqual(len(histogram), 2)
                identities = {shuffled(m, rng).identity() for _ in range(10)}
                self.assertEqual(identities, {m.identity()})

    def test_agrees_with_brute_force(self):
        # Exact means: same identity exactly when the brute-force form over
        # all atom orderings is the same. Checked on random graphs, valid or
        # not, each also listed again in a shuffled order.
        rng = random.Random(42)
        graphs = []
        for _ in range(250):
            g = random_small_graph(rng)
            graphs += [g, shuffled(g, rng)]
        by_identity, by_brute = {}, {}
        for g in graphs:
            identity, brute = g.identity(), brute_force_form(g)
            by_identity.setdefault(identity, set()).add(brute)
            by_brute.setdefault(brute, set()).add(identity)
        self.assertTrue(all(len(v) == 1 for v in by_identity.values()))
        self.assertTrue(all(len(v) == 1 for v in by_brute.values()))
        # The sample has repeats beyond the shuffled copies, so it tests
        # "equal when isomorphic" across independently drawn graphs too.
        self.assertLess(len(by_brute), len(graphs) // 2)

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
