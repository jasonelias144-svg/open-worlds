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

1. **Molecules** (done, this document): elements, valence, molecules, and an
   exact identity for each molecule.
2. **Reactions:** rules that rewrite part of a molecule (a pattern and a
   change), conserving atoms and charge. Examples are protonation,
   condensation to an amide, and hydrolysis.
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

**Symmetry.** The search prunes by symmetry, in the simplest form of what
nauty and bliss do. Two leaves with the same form reveal an automorphism of
the molecule. The search uses those automorphisms to skip branches whose
answers it already knows: branches that an automorphism fixing the choices
made so far maps onto an explored branch, and the rest of a branch once one
of its leaves matches the first leaf. Without pruning, the search tried
every branch, which made symmetric molecules slow:

| Molecule | Before | With pruning |
|---|---|---|
| tetra-tert-butylmethane, C17H36 | 31,104 leaves, about 2 s | under 20 leaves, milliseconds |
| C53H108 (one more level of branching) | over 200,000 leaves: hit the cap after tens of seconds | under 50 leaves, under 0.1 s |
| 9 separate waters (one invalid graph) | about 12 s | milliseconds |

Pruning must never change an identity, so the tests compare the pruned
search with the full one, string for string. They do this on:

- 300 random small graphs;
- every catalogue molecule;
- graphs refinement can't split at all (the Petersen graph, the cube, the
  4×4 rook's graph and the Shrikhande graph);
- random cubic hydrocarbons;
- copies of random graphs joined at a hub;
- two different rigid cubic hydrocarbons beside identical ammonias.

The last family catches pruning that jumps back too far: four planted bugs
in the pruning were caught. One planted bug was not: taking orbits from
every automorphism found, rather than only those fixing the choices made so
far. That is wrong in principle, but no graph tried exposes it: random
graphs, randomly symmetrized graphs, Cayley graphs of small groups, and
unions of these. Finding one would make a good test.

## Known limits of layer 1

- **Resonance.** Resonance forms are different graphs, so they can get
  different identities. Formamide drawn neutral and drawn charge-separated is
  one molecule with two identities, and so are the two Kekulé structures of
  o-xylene. A test records this, so any change to it is deliberate.
- **Handedness.** There's no stereochemistry, so L-alanine and D-alanine get
  the same identity. Life uses one hand, so a later layer will need this.
- **Elements and charges.** Only H, C, N and O, with charges −1, 0 and +1.
  Phosphorus and sulfur come when the chemistry needs them.
- **The search's cap.** A safety net: a graph that needs more than 10,000
  leaves raises an error instead of getting an identity, and so does
  comparing or hashing it. With symmetry pruning, no molecule tried so far
  needs more than about 50.
- **No radicals.** Every atom must have exactly its valence, so open-shell
  species can't be represented: nitric oxide (NO), the hydroxyl radical, the
  methyl radical, or oxygen as the diradical it really is. O2 can be drawn as
  O=O.
- **No energy, no geometry.** These belong to the layers that need them.

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
- **ReaDDy and Smoldyn:** particle-based simulators of reactions and
  diffusion, which are useful for layer 3.
- **ALIEN:** a large particle-based artificial-life world.

**The RDKit cross-check is planned and hasn't been run.** It would build each
catalogue molecule in RDKit and compare the formula, the charge, valence
acceptance and identity (via canonical SMILES). Installing RDKit in the
session that wrote this layer was blocked by that session's permission
rules. The cross-check can run in CI instead, or in a session that allows
it.
