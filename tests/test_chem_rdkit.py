"""Cross-check of the chemistry against RDKit, the standard open-source
chemistry toolkit.

The main suite doesn't need RDKit, so these tests are skipped when RDKit
isn't installed. CI runs them in a separate job that installs a
pinned RDKit; there OPEN_WORLDS_REQUIRE_RDKIT=1 turns a missing RDKit into a
failure, so the check can't silently stop running.

What is compared:
- atoms, total charge and mass of every catalogue molecule;
- which atoms are acceptable: for every element and charge here, with every
  arrangement of up to five bonds, our validity against RDKit's (sanitized
  without error, and no unpaired electrons). The two known differences are
  listed in KNOWN_DIFFERENCES; any other difference fails;
- molecular identity: on the catalogue, every reaction product of layer 2,
  and shuffled copies of each, two molecules must share our identity
  exactly when they share RDKit's canonical SMILES.

RDKit is asked not to perceive aromaticity or tidy functional groups, so
that it compares the same graphs we do (with aromaticity on, it would merge
Kekule structures that this layer keeps apart, by design).
"""
import os
import random
import unittest
from collections import Counter

from chem import Atom, Bond, Builder, Molecule
from chem.catalogue import CATALOGUE
from chem.rules import RULES
from tests.test_chem_molecules import random_cubic_hydrocarbon, shuffled

try:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import Descriptors
except ImportError:
    Chem = None

REQUIRED = os.environ.get("OPEN_WORLDS_REQUIRE_RDKIT") == "1"

# Where RDKit (2024.3.5) accepts an atom that this chemistry doesn't, and why
# we keep our rule. Keyed by (element, charge, total bond order).
KNOWN_DIFFERENCES = {
    # A hydride ion is H- with two electrons and no bonds. RDKit lets H-
    # carry one or two bonds; we don't.
    ("H", -1, 1): "hydride with a bond",
    ("H", -1, 2): "hydride with two bonds",
    # RDKit also accepts C+ with five bonds: carbonium ions such as CH5+,
    # which exist in superacids and the gas phase. Their bonding (three-centre,
    # two-electron) can't be drawn as ordinary bonds, so this chemistry has
    # only the ordinary three-bonded carbocation, which RDKit accepts too.
    ("C", 1, 5): "five-bonded carbocation (carbonium ion)",
}


def to_rdkit(m: Molecule):
    mol = Chem.RWMol()
    for atom in m.atoms:
        a = Chem.Atom(atom.symbol)
        a.SetFormalCharge(atom.charge)
        a.SetNoImplicit(True)        # every hydrogen is explicit, as here
        a.SetNumExplicitHs(0)
        mol.AddAtom(a)
    orders = {1: Chem.BondType.SINGLE, 2: Chem.BondType.DOUBLE,
              3: Chem.BondType.TRIPLE}
    for b in m.bonds:
        mol.AddBond(b.a, b.b, orders[b.order])
    return mol.GetMol()


def sanitized(m: Molecule):
    """The RDKit molecule if RDKit accepts it, else None."""
    mol = to_rdkit(m)
    flags = (Chem.SanitizeFlags.SANITIZE_ALL
             ^ Chem.SanitizeFlags.SANITIZE_SETAROMATICITY
             ^ Chem.SanitizeFlags.SANITIZE_CLEANUP)
    try:
        Chem.SanitizeMol(mol, sanitizeOps=flags)
    except Exception:
        return None
    if any(a.GetNumRadicalElectrons() for a in mol.GetAtoms()):
        return None
    return mol


def arrangements():
    """A central atom (atom 0) of each element and charge, with up to five
    single bonds to hydrogens, plus at most one double bond to a CH2 or one
    triple bond to an N, whose partners are valid themselves."""
    for symbol in "HCNO":
        for charge in (-1, 0, 1):
            for extra in ("none", "double", "triple"):
                for singles in range(0, 6):
                    b = Builder().atom("x", symbol, charge)
                    if extra == "double":
                        b.atom("p", "C").bond("x", "p", 2).hydrogens("p", 2)
                    elif extra == "triple":
                        b.atom("p", "N").bond("x", "p", 3)
                    b.hydrogens("x", singles)
                    yield (symbol, charge, extra, singles), b.build(validate=False)


def molecules_to_compare():
    pool = [make() for make in CATALOGUE.values()]
    products = []
    for rule in RULES.values():
        for a in pool:
            for outcome in rule.apply(a):
                products.extend(outcome)
            for b in pool:
                for outcome in rule.apply(a, b):
                    products.extend(outcome)
    pool += products
    pool += [random_cubic_hydrocarbon(n, seed) for n, seed in
             [(10, 1), (10, 2), (12, 3), (12, 4)]]
    rng = random.Random(1)
    return pool + [shuffled(m, rng) for m in pool]


@unittest.skipUnless(Chem is not None or REQUIRED, "RDKit is not installed")
class TestAgainstRDKit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if Chem is None:
            raise AssertionError("OPEN_WORLDS_REQUIRE_RDKIT=1 but RDKit is missing")
        RDLogger.DisableLog("rdApp.*")

    def test_catalogue_atoms_charge_and_mass(self):
        for name, make in CATALOGUE.items():
            m = make()
            with self.subTest(name):
                mol = sanitized(m)
                self.assertIsNotNone(mol, "RDKit rejects it")
                self.assertEqual(Counter(a.GetSymbol() for a in mol.GetAtoms()),
                                 Counter(a.symbol for a in m.atoms))
                self.assertEqual(Chem.GetFormalCharge(mol), m.charge)
                self.assertAlmostEqual(Descriptors.MolWt(mol), m.mass, places=2)

    def test_which_atoms_are_acceptable(self):
        differences = set()
        count = 0
        for (symbol, charge, _, _), m in arrangements():
            count += 1
            ours, theirs = m.is_valid(), sanitized(m) is not None
            if ours != theirs:
                # Every difference so far is RDKit accepting what we refuse.
                self.assertFalse(ours, (symbol, charge, m.bond_sum(0)))
                differences.add((symbol, charge, m.bond_sum(0)))
        self.assertEqual(count, 4 * 3 * 3 * 6)
        self.assertEqual(differences, set(KNOWN_DIFFERENCES))

    def test_identity_matches_canonical_smiles(self):
        by_identity, by_smiles = {}, {}
        molecules = molecules_to_compare()
        for m in molecules:
            mol = sanitized(m)
            self.assertIsNotNone(mol, m)
            smiles = Chem.MolToSmiles(mol, canonical=True)
            by_identity.setdefault(m.identity(), set()).add(smiles)
            by_smiles.setdefault(smiles, set()).add(m.identity())
        split = {k: v for k, v in by_identity.items() if len(v) > 1}
        merged = {k: v for k, v in by_smiles.items() if len(v) > 1}
        self.assertEqual(split, {}, "one identity, several RDKit SMILES")
        self.assertEqual(merged, {}, "one RDKit SMILES, several identities")
        self.assertGreater(len(by_identity), 100)
        print(f"\n  compared {len(molecules)} molecules, "
              f"{len(by_identity)} distinct", flush=True)


if __name__ == "__main__":
    unittest.main()
