# Chemistry: the nature track

The agent worlds start with language models. The nature track starts where
nature started: elements and molecules first, then reactions, then a world
in which chemistry happens, and only much later anything like a cell. The
founder chose this direction on 2026-11-12.

## Approach: real elements, simplified rules

The elements are real: hydrogen, carbon, nitrogen and oxygen, with their real
atomic weights and their real valences, including charged atoms (ammonium,
hydroxide, hydronium). The molecules are real molecules, checked against
their real formulas and masses. What's simplified is the physics. There's no
quantum mechanics, no geometry and no energy yet. A molecule is a graph:
atoms joined by single, double or triple bonds.

This means that what the world produces can be compared with what nature
produced. If glycine appears, it is glycine.

## Layers

1. **Molecules** (done): elements, valence, molecules, and an exact
   identity for each molecule.
2. **Reactions** (done): rules that rewrite part of a molecule, keeping
   every atom, every charge and every valence. Examples are proton transfer,
   condensation to an amide (the peptide bond), and hydrolysis.
3. **A world of chemistry:** molecules in a space, moving and meeting, with
   energy coming in from outside. The gardener (DESIGN.md, principle 8)
   enters here as a declared law that tends the conditions, never the
   molecules.
4. **Thresholds:** the points where something new appears. Do molecules
   gather into structures? Do sets form that make more of themselves
   (autocatalytic sets)?
5. **Protocells:** an inside and an outside, and growth and division.

Each layer gets its own tests, and its own cycle record once it runs as a
world.

## Layer 1: molecules

The code is in [chem/](../chem/), and the tests are in
[tests/test_chem_molecules.py](../tests/test_chem_molecules.py).

**Valence.** Every atom is explicit, hydrogens included. The bond orders on
an atom must add up exactly to its valence, and the valence depends on the
atom's formal charge as it does in real chemistry:

| Element | Charge −1 | Neutral | Charge +1 |
|---|---|---|---|
| H | 0 (hydride) | 1 | 0 (proton) |
| C | 3 (carbanion) | 4 | 3 (carbocation) |
| N | 2 (amide ion) | 3 | 4 (ammonium) |
| O | 1 (hydroxide) | 2 | 3 (hydronium) |

Carbon monoxide shows the rule at work. It is a triple bond between C− and
O+, and both atoms then have valence 3.

**Identity.** Two molecules are the same exactly when one can be turned into
the other by relabelling its atoms. `Molecule.identity()` gives a string that
is equal for two molecules exactly when that's true. It is found by colour
refinement, followed by an exhaustive search over the ties refinement leaves.
This is individualization and refinement, the standard exact method. Ordinary
hydrogens are folded into their atom's label to keep the search small:

```
water                OH2|
glycine              CH0.CH2.NH2.OH0.OH1|0-1:1,0-3:2,0-4:1,1-2:1
glycine zwitterion   CH0.CH2.N+H3.O-H0.OH0|0-1:1,0-3:1,0-4:2,1-2:1
carbon monoxide      C-H0.O+H0|0-1:3
```

**What the tests check:**

- valences, including the charged ones;
- the Hill formula, charge and validity of all 25 catalogue molecules;
- masses (water 18.015, glycine 75.067, carbon dioxide 44.009);
- that isomers are told apart (ethanol from dimethyl ether, glycine from its
  zwitterion);
- that the identity doesn't change when the atoms are listed in a random
  order (20 random orders for each catalogue molecule).

They also check hard cases:

- **Decalin and bicyclopentyl** (both C10H18) look identical to colour
  refinement alone, so a hash built on refinement would call them one
  molecule. The test first shows that refinement really can't separate
  them, then shows that the identity does.
- **Random cubic hydrocarbons** (C10H10 to C14H14, each carbon bonded to
  three others). Refinement puts every carbon in one colour, so the search
  does all the work. These catch a search that skips branches or keeps the
  wrong answer: the catalogue alone can't, because its molecules are easy
  enough that any single path through the search gives the right answer.
- **Brute force.** On 250 random graphs of up to six atoms, valid or not,
  each also listed again in a shuffled order, the identity is checked
  against the slowest exact method there is: trying every ordering of the
  atoms.

The tests were themselves checked by planting bugs, one at a time:

- leaving out the search;
- searching only one branch (no backtracking);
- keeping the last answer instead of the least;
- folding every hydrogen, a charged one, a double-bonded one, or one bonded
  to another hydrogen;
- dropping the hydrogen count;
- ignoring charge;
- ignoring bond order.

Each one makes the tests fail. Two of them first went uncaught:

- **Ignoring bond order.** For valid molecules the hydrogen counts usually
  imply the bond orders, so a test with the two Kekulé structures of
  o-xylene was added.
- **The search bugs (no backtracking, wrong answer kept).** These were found
  by the independent review, which led to the cubic and brute-force tests.

## Known limits of layer 1

- **Resonance.** Resonance forms are different graphs, so they can get
  different identities. Formamide drawn neutral and drawn charge-separated is
  one molecule with two identities, and so are the two Kekulé structures of
  o-xylene. A test records this, so any change to it is deliberate.
- **Handedness.** There's no stereochemistry, so L-alanine and D-alanine get
  the same identity. Life uses one hand, so a later layer will need this.
- **Elements and charges.** Only H, C, N and O, with charges −1, 0 and +1.
  Phosphorus and sulfur come when the chemistry needs them.
- **Symmetry costs time.** The search doesn't yet prune by symmetry, as
  nauty and bliss do. Most molecules take milliseconds, but a very symmetric
  one takes longer: tetra-tert-butylmethane (C17H36) takes about 2 seconds.
  A cap stops the search with an error, but reaching it can take tens of
  seconds (for example C53H108), and comparing or hashing such a molecule
  raises the error too. That's acceptable while people write the molecules.
  Before reactions or agents make molecules freely (layer 3), the search
  needs symmetry pruning or a time bound, so that no molecule can stall a
  world.
- **No radicals.** Every atom must have exactly its valence, so open-shell
  species can't be represented: nitric oxide (NO), the hydroxyl radical, the
  methyl radical, or oxygen as the diradical it really is. O2 can be drawn as
  O=O.
- **No energy, no geometry.** These belong to the layers that need them.

## Layer 2: reactions

The code is in [chem/reactions.py](../chem/reactions.py) and
[chem/rules.py](../chem/rules.py), and the tests are in
[tests/test_chem_reactions.py](../tests/test_chem_reactions.py).

**A rule** names a few atoms and says how the bonds among them, and their
charges, change. Nothing else is touched. This is the graph-rewriting view
of chemistry. Amide formation, for example, names the acid's carbon, its two
oxygens and the OH hydrogen, and the amine's nitrogen and one of its
hydrogens. It moves two bonds, and water leaves.

**Three laws** hold for every rule. A rule that breaks one is refused when
it is written, not when it is used:

- **Atoms are kept.** A rule moves bonds and charges, never atoms.
- **Charge is kept.** The charges after add up to the charges before.
- **Valence is kept.** For each atom a rule names, the change in its bonds
  equals the change in valence that its change of charge requires. So a rule
  applied to valid molecules always gives valid molecules.

Every rule can be run backwards, and the reverse obeys the same laws.

**Applying a rule** to some molecules finds every place the rule's atoms fit.
Every molecule given must take part: a rule may not name an atom that isn't
connected to anything it changes, so a bystander can't count as a reactant.
So `apply(a, b)` is a reaction between
a and b, and `apply(a)` is a reaction within a. The result is each distinct
outcome, as a set of product molecules.

**The rules so far** are real reaction types:

| Rule | A real example |
|---|---|
| Proton transfer, acid to amine | glycine → its zwitterion (within one molecule) |
| Proton transfer, O–H to oxygen | H2O + H2O → H3O+ + OH− |
| Amide formation (condensation) | glycine + glycine → glycylglycine + H2O |
| Amide hydrolysis | glycylglycine + H2O → 2 glycine |
| Hydration of a carbonyl | CH2O + H2O → methanediol; CO2 + H2O → carbonic acid |
| Cyanohydrin formation | CH2O + HCN → glycolonitrile |

Glycine and alanine give two dipeptides, Gly-Ala and Ala-Gly: same formula,
different molecules, as in real chemistry.

**What the tests check:**

- each real reaction above gives exactly the real products;
- every rule, on every catalogue molecule alone and on every ordered pair:
  874 outcomes. Each keeps atoms, charge and mass, each product is valid,
  and running the reverse rule on the products gives the reactants back;
- rules that break a law are refused;
- the outcome doesn't depend on the order of the atoms or the reactants.

The tests were checked by planting eight bugs in the reaction code, one at a
time, and each makes them fail:

- matching atoms of the wrong charge;
- matching bonds of the wrong order;
- forming a bond that already exists;
- letting a bystander molecule count as a reactant;
- dropping the charge law;
- dropping the valence law;
- reversing a rule without reversing its charges;
- reporting the same outcome twice.

## Known limits of layer 2

- **No energy, so no preferences.** Everything a rule allows can happen,
  and nothing says how often. Glycine condensing with itself gives a
  three-membered ring (an α-lactam) that real chemistry hardly makes,
  because the ring is strained. A test records this. Energies and rates
  come with layer 3.
- **Rules are local.** A rule sees only the atoms it names, so it applies
  wherever those atoms fit, not only to the group its name suggests:
  - the proton transfer "to an amine" takes any neutral nitrogen. It
    protonates an amide's nitrogen, which is far less basic in reality, and
    HCN, giving the nitrilium ion HCNH+;
  - hydration of a carbonyl takes any O–H, not only water's. With methanol it
    makes a hemiacetal, and on a carboxylic acid an orthoacid;
  - the proton transfer from O–H to oxygen also protonates carbonyl oxygens.

  All of these are valid molecules, and some are real but minor. Rules can
  be given more context when a world needs it.
- **Outcomes multiply.** With more rules and bigger molecules the number of
  outcomes grows fast. A world will sample reactions, not list them all.

## Where this came from

The founder's brainstorming sessions with DeepSeek sketched a chemistry
engine in nine components, each with tests. Claude extracted it, repaired
it until it ran, and checked it before using any of it. The plan of layers above
follows its order: molecules, then reaction patterns, then exploring what can
form, then self-assembly, then protocells. It also had the right idea of
making valence depend on formal charge.

The code here is written fresh rather than copied. Running the sketch showed
why:

- **Its valence rule gives a carbocation five bonds.** The rule was "8 minus
  the electrons", which is right for N, O and the carbanion. The real number
  for a carbocation is three: carbon with a positive charge has only six
  electrons around it, not eight.
- **Its identity changes with the order of the atoms.** Its colour-refinement
  signature numbers the colours in order of first appearance. Over 50 random
  orderings of ethanol it produced 17 different signatures, so a library
  built on it would count one molecule many times.
- **Both of its signatures call decalin and bicyclopentyl the same
  molecule.** It also ignores bond order. Its docstring says it "rarely
  collides". The collision isn't rare; it's structural.

None of this takes away from the sketch's value as a brainstorm. It showed
the shape of the whole climb, and its mistakes became tests here.

## Open-source work to learn from

- **RDKit:** the standard open-source chemistry toolkit, and the reference
  for checking valence and identity (canonical SMILES).
- **Squirm3:** an artificial chemistry of atoms on a grid that bond by
  simple rules, in which self-replicating molecules arise.
- **SimSoup:** an artificial chemistry built for studying autocatalytic sets.
- **MØD:** a chemistry package built on graph transformation, the model
  layer 2 follows: rules as rewrites of part of a molecular graph.
- **ReaDDy and Smoldyn:** particle-based simulators of reactions and
  diffusion, which are useful for layer 3.
- **ALIEN:** a large particle-based artificial-life world.

**The RDKit cross-check is planned and hasn't been run.** It would build each
catalogue molecule in RDKit and compare the formula, the charge, valence
acceptance and identity (via canonical SMILES). Installing RDKit in the
session that wrote this layer was blocked by that session's permission
rules. The cross-check can run in CI instead, or in a session that allows
it.
