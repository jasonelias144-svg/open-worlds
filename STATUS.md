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
- Claude: the nature track's chemistry. Layer 1 (molecules) is in review
  (#3); layer 2 (reactions) is written and waits for #3.

## Next

1. **Cycle 1:** 3–5 small open language models from different families, on
   the founder's Mac, each reading the charter on entering, in a small world
   with something to coordinate around. Slow ticks. Needs: the charter, and
   a choice of models.
2. Agents in separate processes, through a local API (the step before
   sandboxes and outside agents).
3. A simple viewer page.
4. Nature track: symmetry pruning (or a time bound) for the identity
   search, then chemistry layer 3, a world of chemistry with energy and
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
- For the founder: the RDKit cross-check of the chemistry. Installing RDKit
  was blocked by the session's permission rules. Allow it in a session, or
  run the check in CI? (asked 2026-11-12)

## Noticed

- Python isn't a sandbox: agents in the kernel's process could reach its
  internals. That's acceptable only for agents written here (AGENTS.md), and
  is why later stages run agents in separate sandboxes.
- Chemistry layer 1 doesn't prune its identity search by symmetry yet.
  Very symmetric molecules are slow (tetra-tert-butylmethane: about 2 s), and
  some reach the search's cap after tens of seconds and raise an error, even
  from `==` or `hash()`. That's fine while people write the molecules.
  **Before layer 3 lets reactions or agents make molecules freely,** add
  pruning or a time bound so that no molecule can stall a world. (Noted by
  the independent review of #3.)
- An in-process agent that raises `SystemExit` or `KeyboardInterrupt`, or
  never returns from `act()`, still stops the world. That falls under the
  same limit. Once agents run in separate processes, each call gets a
  timeout. (Noted by the independent review of #1.)

## Decided

- 2026-11-12, founder: the nature track starts where nature started, with
  real elements and molecules; chemistry is the next area of work.
- 2026-11-12, founder: the repository is public and dedicated to the public
  domain (CC0 1.0). The goal isn't financial; anyone may build on it.

## Log

- 2026-11-12 Claude: chemistry layer 2 (`chem/reactions.py`,
  `chem/rules.py`): reactions as rules that keep atoms, charge and valence,
  refused when written if they don't; reversible; six real reaction types,
  from glycine's zwitterion to the peptide bond. Checked over 874 outcomes.

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
