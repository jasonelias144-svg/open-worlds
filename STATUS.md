# Status: open-worlds

**What this is:** simulated worlds where AI agents live under one rule,
respect one another's freedom, with full transparency and exit at any time
**State:** active since 2026-11-12
**Updated:** 2026-11-13 by Claude

## Live

- Where: not deployed
- Version: —
- Last check: —

## Now

- Claude: the course ([docs/COURSE.md](docs/COURSE.md)). Steps 1 to 4
  are done; step 5, the first journey, is in review (#22). `sketches/`
  keeps the DeepSeek records and their code, with its first fixes (#16
  to #18, #20). Next: step 6, keeping keys safely.
- Founder: writing the charter's words into the structure in `CHARTER.md`.

## Next

The course, twelve steps ahead and rolling: [docs/COURSE.md](docs/COURSE.md).
After each step is done, the rest are rechecked and one new step is added.
In short: keeping keys safely; the first learner; real rates and the
gardener's water; an organic chemistry world entered by a stamp; a viewer
page; time and populations; language-model inhabitants (Cycle 1); any AI
from any app; governance; a common-meter poetry world; a single-cell
world; a world others built.

Also kept from earlier plans, outside the course for now: side cycles
suggested by Cycle 0 (walkers with different speeds, to test "respect
momentum"; whether a convention spreads by imitation). Course step 8 (real
rates) resumes the paused chemistry step: primary sources, read properly,
and how water is counted ([docs/CHEMISTRY.md](docs/CHEMISTRY.md)).

The design is in [docs/DESIGN.md](docs/DESIGN.md) and
[docs/MULTIVERSE.md](docs/MULTIVERSE.md); how to build on it, for anyone
and for the founder's conversations with DeepSeek, is in
[docs/COLLABORATING.md](docs/COLLABORATING.md).

## Open questions

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
- For the founder: may a person keep their presences in different worlds
  unlinked, so that a world sees only the key used there? Recommended:
  unlinked by default; the person chooses what to show. (asked 2026-11-13)
- For the founder: does a fork need the child's acceptance? Recommended:
  yes. (asked 2026-11-13)
- For the founder: a course step for persons after step 3, and the
  architectures (octopus, relay, swarm, council) as small examples on the
  unchanged core? Recommended: yes. (asked 2026-11-13)

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

- 2026-11-12, founder, on how to build: "My goal was to come to you with
  ideas, with a vision, and some code that may or may not be helpful. But
  I expect you to take all that in and do it in your own way that makes
  the most sense to you." And: "the DeepSeek code is a guideline, but if
  it happens to be close to executable and functional, all the better."
- 2026-11-12, founder: "a world for poetry and one for chemistry is a
  perfect way to start with two types of worlds and build from those.
  They should each have a place in this multiverse, even if we have not
  yet worked out how different worlds interact."
- 2026-11-12, founder: "I already had the idea of a communication
  multiverse, we just called it Lyceum Commons. Connecting to it would be
  ideal, but it was mentioned to demonstrate this idea has been a part of
  the project all along".
- 2026-11-12, founder: "What you put in the repo becomes the new standard
  we develop from in my DeepSeek conversations." (docs/COLLABORATING.md)
- 2026-11-12, founder, on learning and evolution: a lightweight model "to
  make certain statistical learning choices in the chemistry world", so
  that "chemical agents can advance to organic chemistry worlds if they
  solve certain problems. This provides evolution as a path between
  worlds." "I would love to see the intelligence grow with the complexity
  of the molecules." And "accelerated learning worlds, or even certain
  accelerated learning times". (docs/MULTIVERSE.md)
- 2026-11-12, founder: "Perhaps there can be one main large world that is
  community built and capable of hosting a full physics simulator from
  chemistry up. But that is for later."
- 2026-11-12, founder: "Let’s plot a course forward and then after each
  completed step, plot a new one that adds one new step forward."
  (docs/COURSE.md)
- 2026-11-12, founder, on the demonstration's poem: the founder's own poem
  may be public, but "it is not necessarily the best to start with. I
  would prefer any poem by anyone else. Emily Dickinson would be perfect."
  "We should use a known poem to start anything." The demonstration opens
  with Dickinson's "Hope is the thing with feathers" (1891).
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

- 2026-11-13 Claude: course step 5, the first journey. Cycle 0's corridor
  speaks the protocol, on the world kernel, with doors that name the
  worlds beyond by id and key; worlds learn each other's keys from signed
  manifests, so every door checks the passport against the right keys.
  Alice walks from the corridor through the chemistry and poetry worlds
  and back, ending with ten stamps that all verify. Also: the soup's
  clock can't loop for ever when it is huge, the chemistry law states its
  rate convention, and verify_passport's "never raises" says for which
  passports (from #19 and #21's reviews). The course gains step 17, a
  world others built.

- 2026-11-13 Claude: course step 4. The chemistry world now holds a soup
  of real molecules (`chem/`), which starts with published soil and runs
  its own reactions in world time; an act is a real reaction, by one of
  the rules, among molecules that are there. Each accepted act lets the
  published time pass, exactly; the world replays exactly from its seed.
  Its rates are placeholders, said so in its law. The course, rechecked:
  an act makes a reaction happen, which no real catalyst can, so the
  learner's acts (step 7) will catalyse instead; step 8 gains finding the
  reactions of new molecules; step 16, a single-cell world, is added.

- 2026-11-13 Claude: the first fixes to DeepSeek's code in `sketches/`.
  Fix 1 attaches the demos of components 40 and 44 to 63 to their
  modules, and fix 2 attaches `turns_from_log` to component 4's, each
  unchanged, as the record gives them right after the module. Test
  files that don't load go from 25 to 6; 877 tests pass, 274 fail, 1
  sometimes (sketches/INDEX.md). The demos were read before they were
  run: they write a JSON summary to a temporary folder, and one starts
  two local Python processes.

- 2026-11-13 Claude: course step 3, signed passports (WCP/0.3). A world is
  a key: its manifest names the key and is signed by it, and requests
  name the world's key as well as its id. Worlds sign stamps for
  arrivals, departures and things made (by fingerprint), and anyone can
  check a passport offline; a world refuses a passport with a stamp that
  doesn't verify, or one "from" itself under another key. A leave is the
  holder's own signed record, so a world that withholds the departure
  stamp can't stop it, and the conformance test names that world. The
  course, rechecked: keeping keys safely moves onto it as step 6, before
  the first learner, because a stamp is worth something only while the
  key that signed it is known.

- 2026-11-13 Claude: COLLABORATING.md asks two things of each new
  conversation: start from that page, and give every file whole, named
  on its first line. The founder: "Let's keep working this way for now
  until we reach any reason to change." `extract.py check-all` now also
  fails on a code folder no names file claims (from #17's review).

- 2026-11-13 Claude: record 012-04-00 is complete (the founder's DeepSeek
  conversation ran out of room; the next one starts a new record). The
  copy in `sketches/records/` replaced, after checking the old one is an
  exact prefix of it; components 44 to 63 written out (210 files in all);
  every test rerun under eight hash seeds (433 pass, 145 fail, 1
  sometimes, 25 test files don't load, 18 of them only because their
  demos are separate blocks). CI now checks every record folder, so a new
  record needs only its names file. The course's next-in-line list gains
  curators, contracts between worlds and a shared log of commitments.

- 2026-11-13 Claude: `sketches/`, the creative side kept apart, as the
  founder asked: both DeepSeek records verbatim; all the code files of
  record 012-04-00 (components 1 to 43, 135 files) written out exactly as
  the record has it, by a tool CI reruns; and every DeepSeek test's result
  (414 pass, 144 fail, 1 passes on some runs only, 8 test files don't
  load), held true by CI. A test keeps the records' links into this
  repository working. The independent review found a test whose result
  varies from run to run, and a block left out by a name one line off;
  both fixed, and the check now reports such names.
  `sketches/INDEX.md` says where each component meets the course.
  COLLABORATING.md now says the sketch is a starting point, not an end
  point, and gives four design lessons from components 21 to 43. AGENTS.md
  records the founder's rule on personal data: first name only.

- 2026-11-13 Claude: course step 2 merged (#14) after an independent
  review found two blocking problems (weak keys anyone could sign for;
  laws still saying requests were unsigned), both fixed and re-reviewed.
  The founder lifted the standard-library-only rule; signatures now come
  from the `cryptography` package (pinned in `requirements.txt`), and
  our own code keeps only the weak-key check, which the library doesn't
  make. AGENTS.md now names the merge method used since #3 (merge
  commit), not squash; the independent review caught that it first said
  "every pull request", which #1 and #2 weren't. CI now tests Python 3.10
  as well as 3.12.
- 2026-11-12 Claude: course step 2, keys and signatures. An individual is
  an Ed25519 key; every petition, act and leave is signed for one world
  with a growing number. Ed25519 written here from RFC 8032 passes the
  RFC's five test values (parsed from its text); a new CI job
  cross-checks it against the `cryptography` package. Protocol WCP/0.2;
  the conformance test now refuses worlds that accept unsigned, forged
  or replayed requests, and a world's log names a key only for what that
  key signed. Keys live only in memory for now (said in MULTIVERSE.md).
- 2026-11-12 Claude: course step 1 finished. The course
  (docs/COURSE.md), the guide for building on this (docs/COLLABORATING.md),
  and the founder's ideas on learning, evolution between worlds, time and
  a future main world (docs/MULTIVERSE.md). The demonstration and its
  tests now use Emily Dickinson's poems (1890 and 1891 editions, from
  Project Gutenberg), checked word for word against the source.
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
