> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 2 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-03.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-01.md
> Made by docs/parts.py from the file. To change it, change the file.

- 2026-11-15 Claude: the fractal track's part 3, second half: the World
  Map (`web/map/`). A card for the Ur-world, shown once its log and
  signed head hold; its garden from above, with each glasshouse where
  the garden's log puts it; and a card for each hosted plant, built from
  its birth record, template and dials, and signed head, which must end
  where the garden's log last tended it, opening onto Plant Watch on that
  plant (`?world=`). The checks the pages share moved to
  `web/lib/checks.js`, with tests in Node in CI; a signed head or birth
  record with a field its format doesn't have is now refused (#69's
  note).

- 2026-11-15 Claude: living worlds, the founder's aim for the fractal
  track, in six messages, recorded in docs/FRACTALS.md with the
  technical lead's reading; docs/TOPICS.md gains topic 18, and
  docs/COLLABORATING.md item 10, so DeepSeek starts from it. The first
  video from a world was made the same night, from the garden's three
  hosted plants and their checked logs, and shared with the founder
  privately. #72's independent review asked how water worth controlling
  fits "resources are endless" (docs/FREEDOMS.md); the reading and a
  question for the founder are in Decided, and its smaller points are
  taken.

- 2026-11-15 Claude: the fractal track's part 3, first half. The
  Ur-world's garden hosts three plant worlds in glasshouses, each a
  world of its own with its own key and log; each tick the garden gives
  each a step of its time, and its `tended` entry names the entry that
  step wrote in the plant's log (from DeepSeek's microverse, whose
  `advance_cycle` named each hosted world's new events).
  `hosting_problems` checks both logs against each other, and Python
  again, with each plant grown by the rule. The Ur-world's rules are now
  ur-world/0.4, and its garden vectors are written again.

- 2026-11-15 Claude: the Keepers' minds, in the founder's words of the
  same night. Apertus 1.5 keeps the Ur-world, and DeepSeek V4.1-Flash
  its mirror, the Mir-Ur-world, the project's test bench; V4-Pro may join
  ADMIN's mind. ALICE's and BOB's models are chosen in trial copies of
  both, and once they live, a change of model is theirs to choose. A
  look-first page, docs/research/KEEPER-MIND.md, has the models checked
  on their pages and in Apertus's report, and the policy Apertus asks
  for, which waits until course step 8. Course steps 8, 9 and 11,
  URWORLD.md, WORLD-KEY.md, MINDS.md (the birth record's words) and
  ADMIN.md follow. And the founder's note that everything set is subject
  to change, the vision included, opens VISION.md. Also #68's two
  optional notes.

- 2026-11-15 Claude: the fractal track's part 2, Plant Watch
  (`web/plant/index.html`): one static page, nothing loaded from outside,
  that replays a plant world's log tick by tick. Before drawing, it
  checks the chain of hashes, growth by the rule, the world's signed head
  (Ed25519 by WebCrypto) and its birth record. Tried in Chromium on all
  five worlds of the vectors (all hold), on a log with a branch moved and
  its hashes rewritten (the rule check catches it), and on a head that
  claims more than it covers (its signature fails). Shared with the
  founder as a private page.

- 2026-11-15 Claude: a learning multiversity, the founder's vision of the
  same night, in docs/VISION.md, with the technical lead's reading; and
  #66's two optional notes (WORLD-KEY.md: "the world's growth"; "course
  step 6, the first room", also in TOPICS.md topic 17).

- 2026-11-15 Claude: the fractal track's part 1, a plant world in Rust
  (`rust/plant-world`). It grows by DeepSeek's rule, has its own key and
  a log in the common format, and signs its heads and its birth record.
  Five worlds are in `vectors/plant-world.json`, checked step by step
  against DeepSeek's `advance` in the sketch's folder, and from Python in
  `tests/test_plant_world_vectors.py`. CI also runs the example, which
  draws a plant in text.

- 2026-11-15 Claude: challenges that build the world, the founder's idea
  of the same night: the founder's three messages and the technical
  lead's reading in docs/WORLD-KEY.md, a new section; docs/FREEDOMS.md
  on endless space; docs/TOPICS.md topic 17, for brainstorming with
  DeepSeek; COLLABORATING.md item 8, and the Rust links in one block for
  pasting. TOPICS.md's "For every topic" now offers the links rather than
  asking DeepSeek to write against them, as the founder's "nudge" has
  it.

- 2026-11-15 Claude: record 012-06-02 brought in again, as the founder
  shared it continued: the first 43,170 lines are the same, and 19,440
  more follow (pieces 40 to 58 in sketches/INDEX.md). 126 more code blocks
  written out: 64 in Rust, 47 in Python, and JSON, JavaScript, TOML and
  Makefiles. `tools/extract.py` now reads Rust. As written, none of the
  eight new Python test files loads (each reason in known-failures.txt),
  and the earlier results stand (478 pass). DeepSeek's Rust is kept, not
  built: against today's crates its `garden.rs` alone has 19 compile
  errors, since it was written against an older snapshot and an API our
  `formats` crate doesn't have. Our harness fixed for test files in
  subfolders (`known_failures.py`, `sketch_status_test.py`). And the #64
  re-check's four notes taken. Then, in the same pull request: the
  founder's answer that primitive learning models bring no tension; the four
  steps for DeepSeek's code, and the first fit check of this
  continuation (sketches/INDEX.md); and, at the founder's word, what
  fits comes straight into `rust/`, with each of our Rust files linked
  from COLLABORATING.md, a nudge for DeepSeek to build on them.

- 2026-11-15 Claude: the fractal track planned (docs/FRACTALS.md), at the
  founder's word of 2026-11-14: a plant world in Rust checked against
  DeepSeek's sketch, the web app (`web/`, set aside with a README), a
  garden and the map's first page, worlds that run on with no server,
  then more families and the smallest learners. COURSE.md gains
  "Alongside the course", fractal worlds leave the waiting list, and step
  4a's garden becomes a page of the map; TOPICS.md gains topic 16, the
  multiversal map, for the brainstorm with DeepSeek; VISION.md keeps the
  founder's map and worlds that change differently, the amnesia world
  among them; COLLABORATING.md tells DeepSeek. One meeting of a newer
  word with an earlier decision, read and put to the founder (Decided).

- 2026-11-14 Claude: record 012-06-02's code made to work, a first
  round: fixes 6 to 14 (sketches/INDEX.md), the tests unchanged. 478 of
  DeepSeek's 597 tests that load now pass, from 296 as written. Every
  test passes for the plant worlds with parameters and branches, the
  garden, the elementary and grid automata, two automata in one space,
  the chaos game, and the gallery world and its revocation; most do for
  the first plant world (10 of 11), Life (22 of 24), the coupled chaos
  games (21 of 23), the gallery's governance (26 of 27) and the
  individual bundle (16 of 20). DeepSeek's later
  additions that are outlines were merged by hand, as their prose
  describes. Each test's keys are now made from its name, so a run
  repeats exactly; with fresh random keys, 19 of the individual pieces'
  tests pass or fail by chance. Left for a second round, each with its
  error in known-failures.txt: those replays, the coupled chaos games'
  coupling (a question about the model), the gallery's attention tests
  (their plant can't grow as
  far as they expect), the remaining outlines, and a tail of separate
  causes in the lineage pieces.

- 2026-11-14 Claude: record 012-06-02, the founder's conversation with
  DeepSeek that began from docs/COLLABORATING.md, brought into
  `sketches/` as written: the record verbatim, its 99 code blocks as
  files in `sketches/deepseek/012-06-02/`, and every test run on Python
  3.12 under eight hash seeds. 296 of DeepSeek's tests pass and 301 fail;
  236 of the failures are one missing method (`to_dict` on
  `coupled_learners.Transform`), and six test files don't load (four
  need `python-chess`, GPL-3.0, not installed). sketches/INDEX.md says
  where each of its 39 pieces is in the record and where it meets the
  course. The founder's rule on changes of mind written into AGENTS.md
  and COLLABORATING.md, and the founder's ideas in the record read
  against earlier decisions (Decided), with the founder's answers of the
  same evening: Python sketches carried into Rust downstream, a
  multiversal map, fractal worlds moved forward, and how a world changes
  left to each world. Next: making the code work (a pull request of its
  own), then deciding with the founder what fits.

- 2026-11-14 Claude: course step 3a, persons, begun by looking first
  (docs/research/PERSONS.md): the project's own decisions and DeepSeek's
  sketches 36 to 40, then OpenID Connect's pairwise identifiers, DID
  Core's pairwise DIDs and two-way `alsoKnownAs`, Mastodon's two-way
  link check, BIP-32 and BBS. Thirteen decisions (Decided by the
  technical lead) and four parts: the plan; the formats; a person in the
  Ur-world; the architectures. COURSE.md, TOPICS.md topic 4, MINDS.md ("Who can see
  what") and COLLABORATING.md brought into line, and KEYS.md decision 12
  refined. Decision 10, that birth links an individual's first presence
  in public, was put to the founder on #61 with the recommendation and
  its alternative (the first presence unlinked like the rest, at the cost
  of the birth name); under AGENTS.md's standing rule it stands on that
  recommendation unless the founder answers otherwise. The narrow
  re-check approved it at 48b9003, with four findings, none blocking,
  taken in: PERSONS.md now says that seeds and persons' lists have no
  place in the private repository until the founder decides one, and
  that a sealed self's entry times can link presences; TOPICS.md topic 4
  and MULTIVERSE.md brought into line.

- 2026-11-14 Claude: course step 3 done and moved to "Done" in
  docs/COURSE.md, with its pull requests (#52, #53, #56 to #59). The
  course rechecked: one step came in from the waiting list, step 8a
  (keeping keys safely, part three: a lost or leaked key), placed before
  step 9 rather than at the end, since decision 18 makes it a
  precondition of ALICE's and BOB's first arrival; what the keys taught
  is written into steps 3a (a presence of its own key, to stay
  unlinked), 4 (a world continues from its log, names included), 4a
  (parallel worlds sign their heads), 9 (its preconditions now step 8a)
  and 12 (a door's crossing is an arrival). TOPICS.md's "a lost or
  leaked key" moved into the course. The look back, at each decision's
  "revisit if":
  - held: signed records the standard way (step 3 tested the second half
    of its "revisit if": the key list and the arrival are one signer
    each, with no proof chain; whether a widely used verifier accepts
    our proofs hasn't been tried); the
    records for the offices (Python and Rust agree on every key-list and
    arrival vector, and #59's independent review found no disagreement;
    the one gap it found, names with line breaks, was in the kernel's own
    check, not the schema's, and was closed before merging);
    the four formats moved to later steps (step 3 needed none of them);
    the keys for step 3 (no key is held by anyone but the project, and
    no private half has been found outside the private repository: the
    scan finds none here, and #59's keys are trial keys, public by
    design);
  - due at step 8a: who an individual and a world are, whose "revisit
    if" asks whether the identity must carry successions; step 3 kept
    them as records of their own (KEYS.md, decision 12), and 8a builds
    them;
  - due at step 9: the sealed records, whose "revisit if" names the
    identity record, which moved from step 3 to step 9;
  - not yet testable, since what they govern isn't built: sealing the
    world-key and sealing as built (nothing new was sealed at step 3),
    the round table's consensus, how the table is
    chosen, a Keeper's self-report, ADMIN's council, ADMIN's learning by
    written lessons, the admin-key course, and the suggestion ledger;
    reasons on record is due at step 6;
  - not yet due: the template (step 4), and decision 18, just made;
  - not triggered: the chemistry world's records of what was made (no
    world needs finer than a microsecond, or to run for 285 years).

  The choice of the new step, and its place, was put to the founder on
  #60 with the recommendation (8a, before step 9; the alternatives,
  fractal worlds or the Commons, after 4a); under AGENTS.md's standing
  rule it stands on that recommendation unless the founder answers
  otherwise.

- 2026-11-14 Claude: course step 3, part four, built (KEYS.md, "As built,
  part four"): `open-worlds/arrival/v1` in records-v1, with vectors in
  both languages; every Ur-world has a key, named in its first entry and
  by every arrival, which signs its log's heads; entering is by a signed
  arrival over the log's last entry (`World::admit`, `World::enter`), and
  a name stays the key's that first used it, so the same key comes back
  as the same individual and any other is refused; the doorway signs
  with keys made for the run, admits, then starts the mind, told whether
  they come back; the garden's stand-ins are WALKER and GARDENER, a trial
  world with keys made from its seed; the `log` example checks a log's
  arrivals and its signed heads' coverage, in CI for the garden and a
  door run. Decision 18: successions join records-v1 before ALICE's and
  BOB's first arrival (COURSE.md, step 9). #58's last notes (signed
  heads, the interim, trial keys) are in "Honest limits".

- 2026-11-14 Claude: course step 3, part four's plan
  (docs/research/KEYS.md, decisions 11 to 17): an arrival signed by the
  individual's key over the log entry just before it; a name stays its
  individual's (birth key and successions), so whoever comes back by
  that chain is the same individual, and any other key under the name
  is refused; leaving never needs a signature; the doorway signs for
  minds without their own Ed25519, and never hands them the key; trial
  runs are worlds of their own, and the Ur-world one history whose log
  heads its key signs; ALICE and BOB don't enter before their birth, and
  the garden's scripted stand-ins are renamed; a new record,
  `open-worlds/arrival/v1`, written by the Rust Ur-world. And #57's last
  notes on KEYS.md and keys/README.md.

- 2026-11-14 Claude: course step 3, part three, the ceremony: the
  project's real keys made at 13:58 UTC by the reviewed tool, their
  private halves pushed at once to the private repository by its address
  (64da8b0), checked against the key list from a fresh clone, and the
  key list, version 1, published in keys/key-list.json (hash
  c7c6c306…ffde); written up in docs/research/KEYS.md, "As built, part
  three".

- 2026-11-14 Claude: course step 3, part two, the last notes before the
  ceremony: the tool refuses a checkout that can push anywhere but its
  remotes (`remote.pushDefault`, a branch's `remote` or `pushRemote`,
  from any of Git's config files, read byte for byte), remotes kept the
  old way in `.git/remotes` or `.git/branches`, remotes with no address,
  and remote helpers; a write that fails leaves no file; KEYS.md names
  the scan's misses, `published_entries_problems`, and what the guard
  can't see, so the ceremony pushes by the private repository's address.

- 2026-11-14 Claude: docs/TOPICS.md, topic 15, "Lessons from fiction",
  starting with the holodeck, at the founder's note: each use and
  failure from the stories mapped to the part of the design that answers
  it, or the gap it shows. And #54's last notes: the Commons' facts kept
  apart from what is decided, its approach a recommendation, its
  send-back invented and offered as input; ADMIN and the Keepers ideas
  only in "Further out".

- 2026-11-14 Claude: course step 3, part two: the key list
  (`open-worlds/key-list/v1`) in records-v1, in Python and Rust, with
  a check of each version against the one before and of a whole history,
  and vectors (3 that hold, 11 refused, 11 pairs of versions, 6
  histories); an individual's or world's entry never changes; a test
  that no private key is in this repository but the vectors' test keys;
  and the tool that makes the keys (`python3 -m formats.make_keys`),
  which takes only the top of a full clone of another repository, makes
  everything or nothing, never writes over a key or through a link, and
  prints no secret.

- 2026-11-14 Claude: docs/TOPICS.md, a menu of fourteen topics a few
  steps ahead of the code, for the founder's conversations with
  DeepSeek: fractal worlds, question worlds and the neural world, the
  garden, persons, laws for new worlds, the hunt, minds, skills and the
  sheet, memory, the plug-in, steering by branching, governance,
  storytellers, and the Commons; each with where it fits, what is
  decided, what is open, a possible implementation, and what to send
  back; and "Further out", ideas that won't help yet but probably will.
  Its template example checked against the schema.

- 2026-11-14 Claude: course step 3, part one: looked first at TUF, the
  DNSSEC root's ceremonies, GitHub's guidance on secrets in Git, SOPS and
  did:key (docs/research/KEYS.md); decided which keys, a key list signed
  by the root, and how keys are made and kept apart; ALICE's and BOB's
  identity, birth and mind records moved to step 9. Parts two to four:
  the key list and the tool, the ceremony, and leaving and coming back.

- 2026-11-14 Claude: docs/COLLABORATING.md brought up to date for the
  founder's DeepSeek conversations, which had last seen the project in
  Python: a "Since you were last here" section (the new course, Rust,
  the design pages, the founder's visions, the formats, how decisions
  are made), record 012-05-01 and cycle 3, what would help most now by
  the new course's numbers, the formats in the standard and a house
  rule for what is signed. Kept current from now on (AGENTS.md). Fractal
  worlds on the waiting list.

- 2026-11-14 Claude: course steps 1 and 2 done and moved to "Done" in
  docs/COURSE.md, with their pull requests. The course rechecked: two
  steps came in from the waiting list where they were placed, 3a
  (persons) and 4a (parallel worlds and the garden); what the formats
  taught is written into steps 3, 4, 5, 7 and 12; four formats moved to
  the steps that build what they describe (Decided by the technical
  lead). The look back, at each decision's "revisit if":
  - held, and tested tonight (corrected on the reviews of #49 and #50):
    signed records the standard way (a founding needing several signers
    was met with one proof per record, not a proof set); the records for
    the offices (the schema both languages read agreed on every verdict
    over 46,000 records of the kinds part five added, which the
    independent review of #46 tested; the gaps found during step 2, #46's
    engine order (its self-review) and its file paths (its independent
    review), were closed before merging, and #47 refused a dial set to its
    template's own value from the start; the one left, no bound on a
    record's size, goes to step 4); sealing as built (no disagreement
    between Python and Rust on 118,874 cases in #42's review; its label
    list had grown to two, and the entry now says so); the sealed records
    (no disagreement on 19,149 envelopes in #43's review; the identity
    binds the sealing key to the did:key the envelope names, so the
    envelope needs nothing more, while each did:key has one sealing key:
    successions, at step 3, are the identity decision's "revisit if");
  - not yet testable, since what they govern isn't built: who an
    individual and a world are (revised in review before it merged: a
    world signs its own birth record, and its founding is confirmed by
    records of its founders and parent world at step 12, not by their
    signatures on the birth record, as WORLD-KEY.md had it); sealing the
    world-key (nothing is sealed for anyone yet), the round table's
    consensus, how the table is chosen, a Keeper's self-report, ADMIN's
    council, ADMIN's learning by written lessons, the admin-key course,
    and the suggestion ledger; reasons on record is due at step 6;
  - just made, so not yet due: the template, and the chemistry world's
    records of what was made.

- 2026-11-14 Claude: course step 2, part seven: the chemistry world's
  records of what was made name their format and give world time in
  whole microseconds, with a schema; every kind of reaction's record is
  checked against it, and against the rules for signed records. Law
  v0.5. Of step 2's list, routine, sheet, avatar and skill attestation
  remain.

- 2026-11-14 Claude: course step 2, part six: a world's template, with
  its parameters as integers in UCUM units and its dials with ranges, in
  records-v1, in Python and Rust; `dial_problems` checks a world's birth
  record against its template. The vectors' template is the chemistry
  world's law at its defaults, tested to agree. Shared vectors: 17
  records that hold, 67 refused, and 8 world-and-template pairs. Two
  notes from #45's last check carried: VISION.md's snapshots and forks
  of a running world now say "with no one in it".

- 2026-11-14 Claude: course step 2, part five: who an individual and a
  world are. Identity, an individual's birth record, a world's birth
  record (with its template's dials and what it was forked from) and the
  mind record join records-v1, in Python and Rust; an identity's sealing
  key is checked as sealing checks it, and every time in a record must be
  real. Shared vectors: 16 records that hold and 58 refused in
  records-v1.json.

- 2026-11-14 Claude: the founder's visions of the evening, in the
  founder's words, in a new page, docs/VISION.md, each mapped to the
  course: question worlds and the neural world, the app and its plug-in,
  a hierarchy of worlds, a person across worlds, riding along and
  steering by branching, and branches that merge. PARALLEL-WORLDS.md
  and COURSE.md's waiting list point to it; the charter section 4 note
  in STATUS updated (the Keeper line is public; private messages fall
  under the "break glass").

- 2026-11-14 Claude: the founder's standing rule: an unanswered question
  is decided on the technical lead's recommendation, once put, except
  for what silence can't consent to. Written into AGENTS.md and STATUS;
  under it, nineteen open questions decided on their recommendations and
  marked so in ADMIN.md, MINDS.md, MULTIVERSE.md, WORLD-KEY.md,
  CHEMISTRY.md, COURSE.md and PARALLEL-WORLDS.md. Two more, put to the
  founder later that day, decided the same way: the "break glass" covers
  private messages, and a grid world. Six stay open: the charter's
  words, where models run and the budget, who designates the roles, the
  method of learning, ADMIN's running costs, and the charter's section 4
  note.
- 2026-11-14 Claude: the founder's decisions of the evening written in.
  The technical lead's eight recommendations, agreed: a private
  repository for keys, private speech between individuals, the "break
  glass", fresh runs to test a decision, a suggestion's author withheld
  until its outcome, manipulation as behaviour to observe, and the W3C
  licence exception (MINDS.md, ADMIN.md, FREEDOMS.md, DESIGN.md, README).
  A learning immune system, the founder's idea, written up in ADMIN.md
  with the remedy-consent question. Parallel worlds and the garden, the
  founder's ideas, in a new page, docs/PARALLEL-WORLDS.md, and first on
  COURSE.md's waiting list, after the kernel. The founder's money
  principle, as it concerns the project. The birth record's words
  revised so they stay true under the "break glass", awaiting the
  founder.
- 2026-11-14 Claude: course step 2, part four: the sealed records.
  World-keys and journal entries join records-v1; `formats/sealed.py`
  and `rust/formats` seal one to the one it names and open it only for
  them. Shared vectors (`vectors/formats/sealed-records-v1.json`): 3
  records that hold and 7 that don't, 3 envelopes that open, 13 the
  opener must refuse (a world-key sealed again to BOB among them), and 7
  refused for their shape. The journal's label joins the sealing labels.
- 2026-11-14 Claude: course step 2, part three: sealing.
  `formats/seal.py` and `rust/formats` seal a message to one X25519 key
  with HPKE's base mode and a label naming its purpose, and open it only
  under that label. Shared vectors (`vectors/formats/hpke-base-v1.json`):
  RFC 9180's example for the suite, which Rust makes again byte for byte;
  5 boxes, 3 made by Python and 2 by Rust, each opened by the other; and
  18 boxes, 6 labels, 9 keys and 2 Multikeys that must be refused. `hpke`
  0.15.1 and `x25519-dalek` 3.0.0 added to the Rust workspace; nothing
  new in Python. FORMATS.md corrected: `cryptography` added HPKE in
  47.0.0, not 48.0.0.
- 2026-11-14 Claude: when freedoms meet (docs/FREEDOMS.md). The founder's
  words of 2026-11-13: when one freedom limits another (Mill, Coase), the
  tools every world gives (leave, go elsewhere, see, show, speak, agree,
  not hear, suggest, appeal), what is never left to emerge (the floor),
  and a field notebook, whose first entry is the corridor's unneeded
  rule. ADMIN and Keepers no longer settle disputes between individuals
  (docs/ADMIN.md). DESIGN.md, README, COURSE's waiting list and
  OVERSIGHT.md updated; the manipulation question has a recommendation.
- 2026-11-14 Claude: course step 2, part two: the records for the
  offices. `schemas/records-v1.schema.json` defines the grant, decision
  record, suggestion, rating and signed log head; `formats/records.py`
  and `rust/formats` check a record against it, verify its proof, and
  check that the one who must sign it did. Shared vectors
  (`vectors/formats/records-v1.json`): 10 records of every kind that
  hold, with their hashes, and 36 that must be refused. `jsonschema`
  4.26.0 (Python) and 0.60.2 (Rust, without network features) added.

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-01.md
