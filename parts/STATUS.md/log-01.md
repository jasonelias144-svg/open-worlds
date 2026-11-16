> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 1 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-02.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

- 2026-11-14 Claude: course step 2, part one: signed records the
  standard way. `formats/` (Python) and `rust/formats` sign and verify
  records with `eddsa-jcs-2022`: RFC 8785 with this project's three
  rules, did:key, and Data Integrity proofs. Both reproduce the W3C
  specification's example step by step, and agree through
  `vectors/formats/eddsa-jcs-2022.json`, which also holds 25 proofs that
  must be refused (9 of them for the time they give) and 7 values that
  break the rules. `multiverse/ed25519.verify` now also refuses a
  signature whose R is of small order, as Rust's `verify_strict` does.
  `rfc8785` 0.1.4 pinned; `serde_jcs`, `ed25519-dalek` and `bs58` added
  to the Rust workspace. FORMATS.md records the decision.
- 2026-11-14 Claude: suggestions from inside (docs/ADMIN.md). Two founder
  decisions written in. First, codes, maps and public clues stay public,
  as action-based challenges whose key only the earner can open
  (docs/WORLD-KEY.md). Second, complaints become entries in an open,
  one-way suggestion ledger. Each entry goes out to GitHub and gets an
  outcome on record as a decision record, a report of a floor breach is
  acted on at once, and changes come only by reviewed pull request. How
  well entries are handled is measured, with ratings published as a
  spread. Suggestions go to a world's Keeper or to ADMIN. ADMIN is the
  bridge to the outside: it can suggest but not implement, and the
  bridge adds without filtering, since every entry still goes out word
  for word. A change that answers suggestions names them, so the answer
  can be seen from inside. The ledger opens at step 9, and ADMIN joins at
  step 11. Tests 26 to 29; course steps 2, 6, 9 and 11; MINDS.md,
  FORMATS.md and OVERSIGHT.md updated.
- 2026-11-14 Claude: reasons on record (docs/REASONS.md). The founder:
  "We can use Lean to test the logic of reasoning that is presented."
  The page says which decisions need a record, proposes the decision
  record for step 2, and says what code checks (tests 4, 23a and 24) and
  what Lean checks: proofs about the rules first, grants at step 4 (test
  25), and proofs that come with decisions later, with what Lean can't
  check. Course steps 2 and 4, FORMATS.md and README updated.
- 2026-11-13 Claude: nothing hidden (docs/ADMIN.md, docs/WORLD-KEY.md;
  research in docs/research/ADMIN-MIND.md). Two of the founder's
  decisions written in:
  - ADMIN in the open: every decision a Keeper or ADMIN makes that
    affects others goes on record with its reasons, like a court's
    opinion, and stands on them; ADMIN opens all its activity to
    inspection; each decision is made once, with fresh randomness, and
    can't be replayed, but anyone can ask it again with fresh runs, a
    stronger check than reading its reasoning; and everyone keeps a
    private core of their own thoughts, which never decides a case:
    ADMIN's decisions are made in runs the journal isn't part of.
  - Challenges, not tests, for the world-keys and the admin-key course:
    paths open from the start, the commitment machinery and the worlds'
    path secrets gone, and the course taken in practice worlds, with no
    individual's outcomes deciding a key.

  The charter's section 4 now has one exception in the design: each
  one's private core.
- 2026-11-13 Claude: ADMIN learns first, in a world of its own
  (docs/ADMIN.md; research in docs/research/ADMIN-MIND.md). The
  founder's ideas written up: ADMIN takes its own course in a sandbox
  with stand-ins, taking on challenges it announces before it starts,
  with nothing hidden ("Challenges, not tests"), learning by written
  lessons, and improving how it learns, never
  what it may do; its mind free in four senses, chosen by audition at
  step 11; and perhaps a council of models, one office with one seat,
  agreeing or sending a case up. Also the last notes from #34's review:
  practice worlds aren't worlds of the multiverse, the honest limit made
  complete, consent for next-path measures, "withholds" back in test 17,
  who can leave a bond, and the Keeper's name kept as a deferred question.
- 2026-11-13 Claude: ADMIN, part two (docs/ADMIN.md). The founder's
  ideas written up:
  - training for keeping worlds, in practice worlds with stand-in
    inhabitants, giving feedback, never sanctions. A Keeper's report of
    its own mistake is protected, as in aviation's safety reporting, but
    deliberate misuse and the facts in the log are not.
  - the round table: ADMIN has one seat among equals, alone until a
    Keeper earns the admin-key, and the table decides by consensus what
    all worlds share.
  - the Ur-world's Keeper, its own office from step 11, first, not above.
    ADMIN's judgment and the multiverse log move to step 11 with it.

  The admin-key is earned by criteria in code, not given by ADMIN, and
  ADMIN can't take a seat away. The rules for measuring Keepers now hold
  against gaming: starting points the Keeper didn't set, leavers counted,
  consent reported but not scored, challenges used once, and thresholds
  fixed before results, applying only to periods that begin after them.
  The AI Keepers the multiverse assigns are drawn by lot, not chosen by
  ADMIN. Fixing what threatens the floor doesn't wait for the table, and
  the founder stays above the table's rulings. Each course step now ends
  with a look back at the technical lead's decisions.
- 2026-11-13 Claude: course step 2, part one: looking first
  ([docs/research/FORMATS.md](docs/research/FORMATS.md)). The JSON this
  project signs is written as RFC 8785 writes it, in all 2,005 documents
  of a check kept with the note (`jcs_compare.py`), for documents with
  ASCII keys, integers within 2^53 - 1, and no floats; floats are written
  differently, and the chemistry world signs one today. W3C's
  `eddsa-jcs-2022` canonicalizes to that form, but signs hashes of it with
  a proof configuration, so our signatures are not that suite's.
  Proposed: RFC 8785 for every new signed record, with ASCII keys, safe
  integers and no floats; whether to sign the `eddsa-jcs-2022` way, for
  step 2; did:key for keys, with an individual named by their birth
  key's; JSON Schema 2020-12; records shaped like verifiable credentials
  without JSON-LD; HKDF for commitments; grants modelled on UCAN; signed
  log heads; images named by digest. Sealing with HPKE's base mode
  (Python's `cryptography` has no Auth mode) is decided by the technical
  lead, under the founder's deference, and the world-key's design page
  says so; the founder's statement on deciding is recorded.
- 2026-11-13 Claude: course step 1, part two: ADMIN
  ([docs/ADMIN.md](docs/ADMIN.md)). Ten things the multiverse must
  preserve, from exit and the record to continuity and the power to
  correct mistakes, each with what could break it and what guards it.
  The Keeper's office: who keeps a new world, how the office changes
  hands, and its memory staying with the office. ADMIN, the Keeper of
  the multiverse, answering to the technical lead's role by the
  founder's designation: rules as code first, powers as narrow grants, a
  multiverse log anyone can audit, and judgment last, reviewed and open
  to appeal. Ten misbehaviours it must stop or catch, written before it
  is built. The research behind it:
  [docs/research/OVERSIGHT.md](docs/research/OVERSIGHT.md). After the
  independent review: the sealed self against the project is a
  commitment, not a guarantee, until the founder decides; signed heads
  catch a log cut short; an appeal against the code role's own act goes
  straight to the founder; the operator's hand and kernel changes stand
  outside grants, guarded by the protected freedoms' tests. Also the
  admin-key, a course for Keepers, and minds in containers.
- 2026-11-13 Claude: course step 1, the design pages. The course is set
  anew ([docs/COURSE.md](docs/COURSE.md)), with the first course's record
  kept. [docs/MINDS.md](docs/MINDS.md): the eight parts of an individual,
  the four layers of what a mind is told, how information moves, who can
  see what, the sheet, memory, and where everything lives.
  [docs/WORLD-KEY.md](docs/WORLD-KEY.md): the purpose, the tour, the
  Keeper (each world's own intelligence, which builds each individual's
  path), and the hunt, whose pieces are the real parts of a world and
  whose prize, the world-key, founds one. Each individual has a sealed
  interior that no one else can read. The research behind them, with its
  sources and a map of open source to learn from:
  [docs/research/GAMES-AND-WORLDS.md](docs/research/GAMES-AND-WORLDS.md).
  After the independent review: the world-key is a signed right to found,
  and a new world gets a key of its own, since a key that could be worked
  out from the record would be no identity; the Keeper's designs are
  logged by fingerprint until solved, so no answer can be read ahead of
  time; whoever leaves can come back, once identities have keys; the
  Ur-world gets its own key and signs its log (step 3); the prompt's
  framing becomes part of the law; and claims the research page's
  sources didn't support were corrected from the papers themselves. From
  the second review: each commitment carries a random value, so it can't
  be matched by guessing. From the third: the world-key is signed and
  sealed only when the path is done (HPKE's Auth mode), so it can't be
  opened from answers made public. And the founder's ideas: the world-key
  sealed for its earner (Diffie–Hellman); once it is found, an open line
  to the world's Keeper, authenticated by keys rather than a password,
  with a return as a friend; and Keepers of different worlds talking,
  under proposed rules. The count in experiment 001 has its script.
- 2026-11-13 Claude: experiment 001, the first unscripted minds
  ([experiments/001-first-words](experiments/001-first-words/RESULTS.md)).
  Five small open models, from 135 million to 1.7 billion parameters,
  went into the garden two of a kind, four runs each, with the plan and
  predictions committed before any model ran.
  - The smallest never acted. From 360 million parameters, nearly every
    reply was a readable action, but mostly steps.
  - Real exchanges between the two minds began at 1.7 billion ("What
    else can you see from up there?").
  - The orientation's two examples became scripts, said over and over.
  - Six of the ten predictions held.
  - A first attempt was found to sample with settings the library filled
    in; it is kept, and the plan records the amendment.
- 2026-11-13 Claude: the Ur-world's doorway for minds
  (`rust/ur-world/src/door.rs`, docs/URWORLD.md). A mind can be any
  program, in any language, speaking lines of JSON: it is sent the world's
  orientation once, then what it sees each tick, written out and as data,
  and answers with one line. Replies are read strictly, the same way for
  every mind; what can't be read is recorded as unreadable, and no reply
  in time as unanswered, so nothing a mind sends can break the world. Each
  inhabitant is now told what came of its last action. Two Python minds
  with no model behind them (`minds/wanderer.py`) run in CI, and their log
  holds by the same check. The rules are now ur-world/0.2. Also, from the
  review of #28: the generator and the query functions answer without
  overflowing at the ends of 64-bit numbers, chunks wholly beyond the edge
  are never made, and a stack of inhabitants falls together.
- 2026-11-13 Claude: the Ur-world's Hello World (`rust/ur-world`,
  docs/URWORLD.md). A 3D world of cells in chunks, generated as it is
  explored from a seed, in whole numbers only, and versioned. It begins in
  a garden with a tree and a spring. ALICE and BOB enter and greet each
  other, one speaking while the other listens. BOB plants a flower, and
  ALICE walks out into the hills as they come into being. The world stores
  only what was explored and what was changed. Its log is written in the
  Python kernel's format and holds by `World.verify_log`. A second,
  independent implementation of the generator in Python, written from the
  documented rules, agrees with Rust on every height and chunk.
- 2026-11-13 Claude: course step 6, part two. A key can be signed over to
  a new one by a succession both keys sign (`multiverse/succession.py`),
  for individuals and for worlds. A passport carries its holder's
  successions, so the stamps given to an earlier key still count, and
  those of worlds that signed over during a stay. A world that knows a
  succession refuses the old key's petitions and acts (never its leave),
  and keeps the first succession of a key it sees. A world signs its own
  key over with `sign_over`. A world's timestamps now only grow, so two
  visits in one clock tick no longer give identical stamps. The protocol
  is WCP/0.4.
- 2026-11-13 Claude: a starting point in Rust, and the standards for Rust
  code ([docs/COLLABORATING.md](docs/COLLABORATING.md), "Code in Rust").
  `rust/` is a Cargo workspace whose first crate, `world-log`, checks a
  world's public record exactly as the Python kernel writes it. Shared
  test vectors in `vectors/`, written by the kernel
  (`python3 -m world.vectors`), keep the two in agreement, and CI checks
  both sides. Writing it found one gap: an agent could say text holding a
  lone surrogate, which Python's log accepts but JSON readers in other
  languages refuse, so the log couldn't be checked there. The kernel now
  refuses such speech.
- 2026-11-13 Claude: record 012-03-02's code written out (the poetry
  engine, 45 files; the founder pointed to `poetry_engine_c21.py` at
  line 21860). The two later records import it, so every test file of
  012-05-01 now loads, and 5 more of 012-04-00. DeepSeek's tests: 141
  pass in 012-03-02, 944 in 012-04-00 (was 877), 241 in 012-05-01 (was
  204) ([sketches/INDEX.md](sketches/INDEX.md)).
- 2026-11-13 Claude: record 012-05-01 brought in (DeepSeek's components 64
  to 87), as 012-04-00 was: the record verbatim, its 79 code files written
  out, its tests run with an honest list of what fails
  ([sketches/INDEX.md](sketches/INDEX.md)). Two small fixes: the demos
  attached, and one wrong import in component 83, which lets the growth
  and governance components load. With them, 204 of DeepSeek's tests
  pass; the chess park's need `python-chess` (GPL) and skip.
- 2026-11-13 Claude: course step 6, part one. Keys can be saved encrypted
  (`multiverse/keys.py`: OpenSSH's format, bcrypt-pbkdf with 64 rounds,
  AES-256-CTR; readable by the owner only; never written over an
  existing file unless asked; a file changed without the passphrase
  never loads as another key), for individuals
  and for worlds, which can be built again with their saved key and keep
  their identity. PKCS12 was tried first; its integrity check let a
  guesser test passphrases through only 2,048 rounds (found by the
  independent review). A world
  can save the request numbers it has seen, signed, and take them back
  after a restart, so the requests it had seen by the last save can't be
  replayed to it. Lost-key recovery waits for the founder's answer.

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

> End of `STATUS.md`.
