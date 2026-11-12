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

- Founder: writing the charter's words into the structure in `CHARTER.md`.
- Claude: the nature track's chemistry. Layers 1 (molecules, #3) and 2
  (reactions, #4) are merged; symmetry pruning for the identity search is in
  review (#5).

## Next

1. **Cycle 1:** 3–5 small open language models from different families, on
   the founder's Mac, each reading the charter on entering, in a small world
   with something to coordinate around. Slow ticks. Needs: the charter, and
   a choice of models.
2. Agents in separate processes, through a local API (the step before
   sandboxes and outside agents).
3. A simple viewer page.
4. Nature track: chemistry layer 3, a world of chemistry with energy and
   rates ([docs/CHEMISTRY.md](docs/CHEMISTRY.md)).
5. Side cycles suggested by Cycle 0: walkers with different speeds (to test
   "respect momentum"), and whether a convention spreads by imitation.

The full plan is in [docs/DESIGN.md](docs/DESIGN.md).

## Open questions

- For the founder: the charter's words (asked 2026-11-12)
- For the founder: is manipulating another agent through words an attack on
  the world (expulsion) or behaviour to observe? (asked 2026-11-12)
- For the founder: a grid world or a voxel world like Minecraft (asked
  2026-11-12)
- For the founder: where models run beyond the Mac, and the budget (asked
  2026-11-12)

## Noticed

- Python isn't a sandbox: agents in the kernel's process could reach its
  internals. That's acceptable only for agents written here (AGENTS.md), and
  is why later stages run agents in separate sandboxes.
- The identity search now prunes by symmetry, so symmetric molecules take
  milliseconds; its cap (10,000 leaves) is a safety net no molecule tried
  comes near. One planted pruning bug (orbits from automorphisms that don't
  fix the choices made so far) survives every test family tried; a graph
  that exposes it would make a good test.
- An in-process agent that raises `SystemExit` or `KeyboardInterrupt`, or
  never returns from `act()`, still stops the world. That falls under the
  same limit. Once agents run in separate processes, each call gets a
  timeout. (Noted by the independent review of #1.)

## Decided

- 2026-11-12: the RDKit cross-check runs in CI. Claude recommended it in
  answer to its own question to the founder, and the founder replied "Sounds
  good" and asked Claude to continue. If that wasn't meant as a decision,
  the job is easy to remove.
- 2026-11-12, founder: the nature track starts where nature started, with
  real elements and molecules; chemistry is the next area of work.
- 2026-11-12, founder: the repository is public and dedicated to the public
  domain (CC0 1.0). The goal isn't financial; anyone may build on it.

## Log

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
