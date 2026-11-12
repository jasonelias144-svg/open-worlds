# Status: open-worlds

**What this is:** simulated worlds where AI agents live under one rule,
respect one another's freedom, with full transparency and exit at any time
**State:** active since 2026-11-12
**Updated:** 2026-11-12 by Claude

## Live

- Where: not deployed
- Version: —
- Last check: —

## Now

- Claude: the multiverse, built from the founder's DeepSeek sketch
  (docs/MULTIVERSE.md). Step 1, the sketch's core (components 1 to 7)
  working and tested with leaving added, is in review. Then step 2: keys
  and signatures.
- Founder: writing the charter's words into the structure in `CHARTER.md`.
- Claude: the nature track's chemistry. Layers 1 (molecules, #3) and 2
  (reactions, #4), symmetry pruning (#5), the RDKit cross-check (#6), the
  layer 3 plan (#7), the engine of a world of chemistry (#8) and
  identifying separate parts (#9) are merged. Step 2 (real rates) is paused
  (see Next).

## Next

1. **Cycle 1:** 3–5 small open language models from different families, on
   the founder's Mac, each reading the charter on entering, in a small world
   with something to coordinate around. Slow ticks. Needs: the charter, and
   a choice of models.
2. Agents in separate processes, through a local API (the step before
   sandboxes and outside agents).
3. A simple viewer page.
4. Nature track: layer 3 step 2, real rates for the six rules with their
   sources ([docs/CHEMISTRY.md](docs/CHEMISTRY.md)). **Paused on purpose**
   until two things are in hand:
   - **Primary sources, read properly.** A first search gave only
     computational or secondary values: glycine's balance between its
     neutral form and its zwitterion differs by a factor of ten between
     sources; formaldehyde's hydration constant is quoted as about 10^3 to
     2x10^3; Schlesinger and Miller's 1973 paper on glycolonitrile formation
     wasn't found. Nothing goes into the world uncited.
   - **How water is counted,** which ties to the founder's water lever:
     as molecules, so that wet–dry cycles change real amounts, or as the
     solvent, the usual convention for constants measured in water. The
     recommendation will come with the answer to the gardener question.
5. Side cycles suggested by Cycle 0: walkers with different speeds (to test
   "respect momentum"), and whether a convention spreads by imitation.

The full plan is in [docs/DESIGN.md](docs/DESIGN.md).

## Open questions

- For the founder: may the poem of yours that opened the sketch's
  demonstration be in the repository? It is CC0, so the poem would become
  public domain. Until then the demonstration uses new lines.
  (asked 2026-11-12)
- For the founder: the charter's words (asked 2026-11-12)
- For the founder: is manipulating another agent through words an attack on
  the world (expulsion) or behaviour to observe? (asked 2026-11-12)
- For the founder: a grid world or a voxel world like Minecraft (asked
  2026-11-12)
- For the founder: where models run beyond the Mac, and the budget (asked
  2026-11-12)
- For the founder: is the default for entering a world "anyone who will act
  under its published law"? Recommended: yes. (asked 2026-11-12)
- For the founder: may a world refuse someone because of their history
  elsewhere? Recommended: only through conditions in its published law.
  (asked 2026-11-12)
- For the founder: which of the gardener's levers the first chemistry world
  starts with: the water (wet–dry cycles), the sun (energy from outside), or
  fresh soil (inflow of simple molecules). Recommended: water and soil
  first; the sun needs photochemistry rules that don't exist yet
  (docs/CHEMISTRY.md, layer 3 plan). (asked 2026-11-12)

## Noticed

- Python isn't a sandbox: agents in the kernel's process could reach its
  internals. That's acceptable only for agents written here (AGENTS.md), and
  is why later stages run agents in separate sandboxes.
- The identity search prunes by symmetry and identifies separate parts one
  at a time, so neither symmetric molecules nor repeated parts can stall it.
  Its cap (10,000 leaves) stays as a safety net: connected graphs built
  specially to defeat refinement can still need exponentially many leaves,
  though none is known among real molecules. A world running for a long
  time should still bound the time an identity may take.
- An in-process agent that raises `SystemExit` or `KeyboardInterrupt`, or
  never returns from `act()`, still stops the world. That falls under the
  same limit. Once agents run in separate processes, each call gets a
  timeout. (Noted by the independent review of #1.)

## Decided

- 2026-11-12, founder: "The multiverse is the same as open-worlds." Its
  design is in docs/MULTIVERSE.md.
- 2026-11-12, founder: "The goal would be to start with this code and these
  ideas, but build a working version in the repo." The DeepSeek sketch's
  code comes in a few components at a time, each made to work. Lyceum
  Commons is "the same idea, just larger".
- 2026-11-12: the RDKit cross-check runs in CI. Claude recommended it in
  answer to its own question to the founder, and the founder replied "Sounds
  good" and asked Claude to continue. If that wasn't meant as a decision,
  the job is easy to remove.
- 2026-11-12, founder: the nature track starts where nature started, with
  real elements and molecules; chemistry is the next area of work.
- 2026-11-12, founder: the repository is public and dedicated to the public
  domain (CC0 1.0). The goal isn't financial; anyone may build on it.

## Log

- 2026-11-12 Claude: multiverse step 1. The sketch's components 1 to 7
  are in `multiverse/`, working, with 160 tests. The sketch's 12 failing
  tests and the problems found by reading its code are fixed, and leaving
  is added. Four rounds of independent review asked for changes (ways a
  hostile entity or visitor could make code raise; docs that overstated
  what the conformance test proves) and found untested behaviours; all
  are fixed, the last by one rule: only plain built-in values cross the
  protocol, all the way down. Each of 60 deliberate breaks tried in the
  new behaviour is caught by a test.
  `python3 -m multiverse.collaboration` runs the first collaboration.
- 2026-11-12 Claude: the multiverse design revised to the founder's
  direction: build from the sketch's code, in steps; Lyceum Commons noted as
  the same idea with rooms. Checked by running it: the sketch's conformance
  test enters the world it checks and stays, taking a place.
- 2026-11-12 Claude: the multiverse design (docs/MULTIVERSE.md), from the
  founder's comments and the DeepSeek sketch (record 012-04-00), whose code
  was extracted and run: 108 of 131 runnable tests passed as written, 119
  after one fix.

- 2026-11-12 Claude: PR #8 (the chemistry engine) merged after an
  independent review that requested changes and a follow-up that approved.
  Step 2 (real rates) paused until its constants have primary sources and
  the founder has answered the gardener question.

- 2026-11-12 Claude: separate parts of a molecule are identified one at a
  time, so repeated parts can't multiply the identity search (seven copies
  of a rigid C10H10, which reached the cap, now take under 100 leaves).

- 2026-11-12 Claude: PR #5 (symmetry pruning) merged after an independent
  review, which also found the graph that exposes the one pruning bug no
  test caught (a 4x4 rook's graph with one square twisted); it is now a
  test. The independent review of #8 found a rare rounding fault in the
  engine (a count could go below zero, or the world could report rest while
  events remained); fixed and tested before merging.

- 2026-11-12 Claude: chemistry layer 3, step 1: the engine of a world of
  chemistry (`chem/soup.py`): a grid of well-mixed cells, mass-action
  reactions and diffusion run by Gillespie's exact method, every event kept
  in a log the agent worlds' verifier accepts. Tested against flux balance,
  even diffusion, conservation and exact replay.

- 2026-11-12 Claude: symmetry pruning for the molecular identity search
  (orbits of discovered automorphisms, and jumping back on a match with the
  first leaf). C53H108, which reached the old cap after tens of seconds, now
  takes under 0.1 s; the pruned search equals the full search on every graph
  tested.

- 2026-11-12 Claude: RDKit cross-check in CI (#6). Our molecular identity
  agrees exactly with RDKit's canonical SMILES on 1,344 molecules; the only
  valence differences are two that RDKit allows and we refuse on purpose
  (hydride with bonds, five-bonded carbocation).

- 2026-11-12 Claude: PR #4 (chemistry layer 2) merged after an independent
  review. Its three notes were taken up: a rule may not name an atom
  unconnected to its change (so bystanders can't count as reactants), the
  "rules are local" limit names what the rules also make, and bond pairs are
  type-checked.

- 2026-11-12 Claude: chemistry layer 2 (`chem/reactions.py`,
  `chem/rules.py`): reactions as rules that keep atoms, charge and valence,
  refused when written if they don't; reversible; six real reaction types,
  from glycine's zwitterion to the peptide bond. Checked over 874 outcomes.

- 2026-11-12 Claude: PR #3 (chemistry layer 1) merged after an independent
  review and a follow-up. The review found that no test caught a search that
  skipped branches or kept the wrong answer; random cubic hydrocarbons and a
  brute-force comparison now do.
- 2026-11-12 Claude: chemistry layer 1 (`chem/`): H, C, N, O with real
  valences including charged atoms, molecules as graphs, Hill formulas and
  masses, and an exact molecular identity (refinement plus search), with a
  catalogue of 25 real molecules and tests. Running the DeepSeek sketch
  showed three faults that layer 1 avoids (docs/CHEMISTRY.md).

- 2026-11-12 Claude: PR #1 merged after a follow-up independent review.
  Recorded the founder's gardener principle in docs/DESIGN.md, in the
  founder's words; took up the review's two notes (a test that keeps the
  tick guard in place; narrower wording in the Cycle 0 record).

- 2026-11-12 Claude: created the repository with the handbook files, the
  world kernel (exit, voice and information guaranteed, with tests), the
  design, the charter's structure, and Cycle 0 (corridor lanes). The
  independent review found four ways an agent's return value could crash or
  get around the kernel, one of which could block another agent's exit. All
  four are fixed, each with a test that fails on the old kernel.
