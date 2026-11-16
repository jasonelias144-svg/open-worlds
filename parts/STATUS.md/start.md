> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "Noticed".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-06.md
> Made by docs/parts.py from the file. To change it, change the file.

# Status: open-worlds

**What this is:** simulated worlds where AI agents live under one rule,
respect one another's freedom, with full transparency and exit at any time;
free, and never a money machine
**State:** active since 2026-11-12
**Updated:** 2026-11-16 by Claude

## Live

- Where: not deployed
- Version: —
- Last check: —

## Now

- Claude: the new course ([docs/COURSE.md](docs/COURSE.md)), set on
  2026-11-13 for the Ur-world and ALICE and BOB. Step 1, the design pages,
  is in: [docs/MINDS.md](docs/MINDS.md) (what an individual is made of,
  what a mind is told, how information moves, where everything lives) and
  [docs/WORLD-KEY.md](docs/WORLD-KEY.md) (the purpose, the tour, and the
  hunt for the world-key), with the research behind them. Its second part,
  [docs/ADMIN.md](docs/ADMIN.md): what the multiverse must preserve, who
  keeps each world, and ADMIN, the Keeper of the multiverse, with the
  Keepers' training and the round table. Steps 1 to 3 are done
  (2026-11-14). Formats that last: every record signed the standard
  way, one schema read by Python and Rust, sealing, and who an
  individual and a world are
  ([docs/research/FORMATS.md](docs/research/FORMATS.md)). Keys and
  identities (docs/research/KEYS.md): the real keys were made on
  2026-11-14, the private halves in the project's private repository
  and the key list in keys/key-list.json; in the Ur-world, whoever
  enters signs an arrival, a name stays the key's that first used it,
  and a world signs its log's heads. The course was rechecked after
  step 3 and gained step 8a, a lost or leaked key, before ALICE's and
  BOB's birth. Step 3a, persons, is done (2026-11-15): its plan, after
  looking first, is in docs/research/PERSONS.md. Its second part, the formats,
  is built: presence keys from a seed by HKDF-SHA256, a link that holds
  only both ways, and a person's list, in Python and Rust with shared
  vectors. So is its third, a person in the Ur-world: a person's client
  in Rust with a presence in each of three trial worlds at once,
  carrying a note from one to another, and a link shown by the
  presence's own act, which its world checks and logs (rules
  `ur-world/0.5`). Its fourth part is built: the architectures as
  small examples, the octopus, the relay and the swarm, and the council,
  counting persons' signed votes (`open-worlds/proposal/v1` and
  `vote/v1`). The course was rechecked on 2026-11-16, with a new list
  of twelve (docs/COURSE.md, "Rechecked on 2026-11-16"). Step 3b is
  under way, a log whose fields can be redacted, with removals and
  restorings on record: its plan, after looking first, is in
  docs/research/REDACTION.md. Its second part is built: a form of the
  log whose fields are kept apart by salted fingerprints, with the
  contents beside it, the check that holds the two together, and the
  function that joins them (`world/apart.py`, `rust/world-log`, with
  shared vectors). Nothing is redacted yet: that is its third part,
  which waits for the founder's answer on the office's copy (Open
  questions). Then step 3c, the room, where DeepSeek's `chat-world` is
  fitted onto the project's formats.
- Claude: the fractal track, alongside the course (docs/FRACTALS.md),
  set by the founder on 2026-11-14: a fractal plant world in Rust, the
  web app in `web/` to watch worlds grow, and in it the multiversal map.
  Its plan is in, and its first part, the plant world, is built
  (`rust/plant-world`), and so is its second, Plant Watch, the page that
  replays a plant tick by tick and checks its log first (`web/plant/`).
  The third is built: the Ur-world's garden hosts three plant worlds in
  glasshouses, and both logs record each step
  (`rust/ur-world/src/host.rs`); and the first map, the World Map
  (`web/map/`), draws the garden from above with a card for each world,
  built from what it publishes and opening onto Plant Watch. The fourth
  has begun: the browser runs the plant world's own Rust, built as a
  WebAssembly command (`rust/plant-wasi`), and Plant Watch grows each
  plant again with it (docs/research/WASM.md). Next, the founder's aim:
  living worlds, where plants grow without end and choose, water flows
  as particles, people shape the land, and life spreads, beginning with
  an endless plant in the browser (docs/FRACTALS.md, "Where it leads:
  living worlds"). DeepSeek sketched it in record 012-07-03; the sketch
  is kept with the review, and the project is to fit it as
  `rust/endless-plant` (not built yet).
  Record 012-09-05 (water, the garden, chat rooms for the Commons with
  AI moderators, the home room, a schema, and a sketch crate in Rust,
  `chat-world`) is kept with what runs
  (`sketches/deepseek/012-09-05/README.md`): after a first round of
  repairs the crate builds and passes its own 18 tests, and 73 of the
  98 Python tests pass. Fitting it to open-worlds' own code is next,
  piece by piece.
  DeepSeek's code from record 012-06-02 works in part (#63), with a
  second round to come.
- Claude: the Ur-world so far: the garden (#28), the doorway for minds
  (#29), and experiment 001, the first unscripted minds
  ([results](experiments/001-first-words/RESULTS.md), #30). The first
  course's steps 1 to 6 (keys, two parts) are done; what is still wanted
  from it is on the new course's waiting list. `sketches/` keeps the
  DeepSeek records and their code.
- Claude: the Keepers' minds. On 2026-11-15 the founder chose two bases:
  Apertus 1.5 for the Ur-world's Keeper, and DeepSeek V4 for the Keeper
  of its mirror, the Mir-Ur-world. The mirror is the project's test bench,
  where ALICE's and BOB's models are also chosen, at course step 8.
  Once they live, a change of model is their own choice
  ([docs/URWORLD.md](docs/URWORLD.md), "The Mir-Ur-world";
  [docs/research/KEEPER-MIND.md](docs/research/KEEPER-MIND.md)). The
  mirror's Keeper runs on V4.1-Flash, and V4-Pro may be part of ADMIN's
  mind. The policy Apertus asks for waits until course step 8 (Open
  questions).
- Claude: the charter, kept from the founder's recorded words as they
  come (`CHARTER.md`; the founder, 2026-11-15, in Decided).

- Claude: the licence in the founder's other public repositories: a
  pull request in each that has the wrong licence or none, CC0 1.0 by
  the founder's standing choice (Decided, 2026-11-15), each with its own
  review.

## Next

The course, twelve steps ahead and rolling: [docs/COURSE.md](docs/COURSE.md).
After each step is done, the rest are rechecked and one new step is added.
In short, since the recheck of 2026-11-16: a log that can be redacted,
with removals on record (3b); the room (3c); offices as records (3d); a
world's lifecycle, and a world leaving (3e); the Commons hosting rooms
(3f); the kernel as entities and components (4); parallel worlds and the
garden (4a); things, skills and the sheet (5); the Ur-world's first
room, end to end (6); the private container, private rooms and the
check before publishing (6a); memory (7); experiment 002, the audition (8). Behind
the twelve, in their old order: a lost or leaked key (8a); ALICE's and
BOB's first life (9); a development container (10); the hunt and the
world-key (11); founding worlds, and doors (12). DeepSeek works beside
the course, by one file at each return, and the fractal track runs
beside it too. Waiting: the Commons' MCP door and going live, the
founder's ideas of 2026-11-16 (personal information in a room, a
gathering world, competition worlds), the founder's visions, a window
onto the worlds, generator 2, storytellers, the gate and districts,
governance, and the first course's steps still wanted.

Also kept from earlier plans, outside the course for now: side cycles
suggested by Cycle 0 (walkers with different speeds, to test "respect
momentum"; whether a convention spreads by imitation). The first course's
step 8 (real rates, now on the new course's waiting list) resumes the
paused chemistry step: primary sources, read properly,
and how water is counted ([docs/CHEMISTRY.md](docs/CHEMISTRY.md)).

The design is in [docs/DESIGN.md](docs/DESIGN.md) and
[docs/MULTIVERSE.md](docs/MULTIVERSE.md); how to build on it, for anyone
and for the founder's conversations with DeepSeek, is in
[docs/COLLABORATING.md](docs/COLLABORATING.md).

## Open questions

Each question for the founder comes with a recommendation, and "take your
recommendation" is a full answer, recorded as the founder's decision on
the technical lead's recommendation. And by the founder's standing rule
of 2026-11-14, a question the founder hasn't answered is decided on the
recommendation once it has been put (Decided, below), except where it
needs the founder's own words or act, money, personal information, or
anything outward-facing or hard to undo. What is left here is of that
kind.

- For the founder, on many multiverses (2026-11-16; Decided, the
  entries of that day):
  1. The floor between multiverses. The internet has no rule above its
     protocol; this project has exit, voice and information. In
     someone else's multiverse they may not hold. Recommended, both: a
     traveller is always told, before entering, what the other side
     guarantees; and this multiverse recognises another (lists it on
     the map, trusts the births its worlds sign) only if it keeps the
     same floor. The first keeps this multiverse from being a
     gatekeeper; the second keeps the floor meaning something. It is a
     question of what the project is for, so it waits for the
     founder's word.
  2. One sentence about the founder's own first computer is left out of
     that day's record, as the one about the founder's first experience
     of the internet is left out of docs/COMMONS.md. Say if either
     should be kept.

- For the founder, on redaction (docs/research/REDACTION.md, "For the
  founder"), from the plan for course step 3b:
  1. An office's copy of what was redacted. FUNDAMENTALS.md has a
     redaction made at once and decided after, and lets the office
     decide to keep it public. That needs the office to be able to put
     it back, and "Kept in the person's own container" (2026-11-15)
     seals it to the person alone. Proposed: a second sealed copy for
     the office that decides, kept only until the decision and any
     appeal are over, then deleted, with an entry that says so. For
     that while an office of the project can read it. Recommended:
     yes. Redacting is not built before the answer.
  2. Whether the key that acted may ever be redacted. The plan keeps
     the key apart, so that either answer can be built; nothing about
     it is hidden unless it is redacted. The cost of allowing it: once
     a key is redacted, no reader can check again that an act was that
     key's; it would rest on the world's word at the time of writing.
     Recommended: keep the option, and decide with the purging of a
     person who leaves (course step 8a).
- For the founder, on private rooms and the Ur-room (docs/COMMONS.md,
  "A spectrum of privacy" and "The Ur-room"), from the founder's words
  of 2026-11-16:
  1. The levels. Proposed, three: on the record; closed, where the
     words are sealed with keys the members hold and the record keeps
     only that the room exists, who is in it and that messages passed;
     and off the record, where nothing is kept. Recommended: these
     three, with closed as the common kind. Two things to weigh with
     it. Closed, as proposed, changes one thing in what is decided: the
     project's machines would hold a closed room's sealed messages for
     a member who is away, where the decisions of 2026-11-14 and
     2026-11-15 have the words pass between the members' own
     containers; the project would still hold no key. And what the
     record keeps of a closed room tells a lot: who is in a private
     room with whom, and when messages passed. That is the main cost of
     closed beside off the record.
  2. Whether "completely encrypted" meant that nothing at all is kept
     of a private room. The decisions of 2026-11-14 and 2026-11-15 keep
     that a message passed, and a closed room's metadata, in the
     record. Recommended: keep that rule for a closed room, and let
     "off the record" be the level where nothing is kept.
  3. What the project can't read, it can't moderate or answer for.
     Before the Commons is open to the public with private rooms in
     it, that is weighed with going live: where it is hosted, and under
     what law. No recommendation yet; it needs looking at first.
  4. The Ur-room on the record. The lobby was decided to be on the
     record on 2026-11-15, when it was where everyone reads the
     charter. As the Ur-room it is where people sit and talk, so the
     record would keep the first talk of everyone who arrives.
     Recommended: on the record, said plainly on entering; and, once
     private rooms are built (course step 6a), with one a door away.
- For the founder, from the session of 2026-11-16, four things that
  wait for the founder's own word:
  1. The founder's ideas on personal information in a room, and the six
     changes the technical lead proposes to them (docs/COMMONS.md,
     "Personal information in a room: ideas"): one's own only; the
     window says who will read it, with AIs off unless turned on; never
     in the open in the record; taken back at any time; the limit on
     copies said in the window; sealed to the person. They touch
     personal information, so nothing here stands on a recommendation.
     Recommended: all six.
  2. Parts of the founder's messages of 2026-11-16 are left out of the
     record, as personal, and marked where they were (Decided, the two
     newest entries). Recommended: leave them out. They can be recorded
     if the founder says so.
  3. Whether a model that moderates a room is an individual, in
     MINDS.md's sense, with what that would owe it (docs/VISION.md, the
     sixth of the six tests; noted at the course's recheck).
     Recommended: decide it together with which model first moderates;
     no model is given the office before then.
  4. Step 10 of the course. The founder said on 2026-11-13: "I like
     that we return to DeepSeek at step 10". The founder returned to
     DeepSeek on 2026-11-14, and the recheck of 2026-11-16 reads that
     as the step being overtaken: DeepSeek works beside the course, and
     step 10 keeps only the development container. It changes a step
     the founder spoke for, so it is put here, and not left to stand by
     silence alone. Recommended: as the recheck has it.
- For the founder, on the Commons' moderators (docs/COMMONS.md, "Open"),
  six questions. Four have a recommendation and stand on it unless the
  founder answers otherwise: whether a room's moderator is its Keeper
  (two offices); what a moderator may do to keep a room's law (pace and
  prompt, remove a comment where the law allows, never expel); who may
  remove a comment (the room's moderator, for a reason the law names,
  and a comment's author for their own; this one bears on voice and
  information, and is put plainly); and whether the home room is the
  private container (yes). One reads the founder's own words on a
  protected freedom, so it is put plainly too: the founder decided on
  2026-11-16 that a removed comment "stays in the data layer, in our
  records", and the technical lead reads that, for a room on the record,
  as readable there by anyone who goes to the records, private
  information apart, which is sealed. The last, which model first
  moderates and its cost, is money, and waits for the founder.
- For the founder: where models run beyond the Mac, and the budget (asked
  2026-11-12). Since 2026-11-15 this includes the two Keepers: about
  144 GB of weights for Apertus 1.5's 70B model, and about 763 GB for
  DeepSeek V4.1-Flash, by arithmetic, not measured
  (docs/research/KEEPER-MIND.md).
- For the founder, before course step 8: the policy Apertus 1.5 asks for
  before it can be downloaded (version 1.5, July 14, 2026). It has two
  parts:
  - an indemnity of ETH Zurich and EPFL against third-party claims
    arising from the project's use, with no limit stated;
  - a duty to make everyone who receives a copy accept the same policy,
    by an express act, and pass it on in turn.

  The options:
  1. accept it and keep Apertus for the Ur-world's Keeper;
  2. use OLMo for the fully open Keeper instead;
  3. wait, and decide before course step 8.

  As first put, option 3 was to wait for Apertus 1.5's data and code.
  They were already out, by its technical report of October 2026
  (arXiv 2610.15542), which the technical lead missed and #70's
  independent review found. So only the policy is open.

  Decided for now: 3, wait, on the recommendation (the founder,
  2026-11-15: "Either way sounds good. Just go with what makes the most
  sense to you."). Nothing needs Apertus before course step 8, and until
  then nothing is downloaded and no one clicks "Agree"
  (docs/research/KEEPER-MIND.md). It comes back before step 8:
  accepting it is a legal promise, and needs the founder's own act,
  agreeing and giving an email address. (asked 2026-11-15)
- For the founder: who designates the roles if the founder can't? Every
  other office has a succession. Recommended: the founder names a
  successor, or a process, recorded where the roles are. (asked
  2026-11-13)
- For the founder, whenever ready: the method of learning the founder
  hopes to pass to ADMIN, in the founder's words, to be ADMIN's first
  routine and tested with and without it (docs/ADMIN.md). (asked
  2026-11-13)
- For the founder, with the budget question above: what running ADMIN's
  models will cost, and whether to own the machines or rent them. Renting
  from providers that can be swapped keeps ADMIN free of dependence;
  priced before course step 11. (noted 2026-11-13)
- For the founder, when writing the charter's section 4 ("nothing is known
  about the world that its participants can't also know"): one exception
  now stands in the design, and the section should name it: each one's
  private core of their own thoughts, an individual's sealed self, and the
  core every Keeper and ADMIN keeps too, which never decides a case. The
  answer to a challenge is no longer one:
  under "Challenges, not tests", nothing is held back. Private speech
  between individuals, decided 2026-11-14, is another: what two say to
  each other is sealed between them, though that a message passed stays
  in the record; since 2026-11-15 they go from one person's container to
  the other's, beyond the "keys to the kingdom", which are only the
  multiverse's own keys (docs/CONTAINER.md). The line with a Keeper was decided public,
  so it is no exception. (noted 2026-11-13; updated the same day and
  2026-11-14)

## Noticed

- The formats' test vectors (`formats/record_vectors.py`,
  `vectors/formats/records-v1.json`) still carry the birth record's
  words of 2026-11-14, with "It may change one day; you remain ALICE."
  They are example data, signed by test keys; the real words are written
  at step 9. The vectors are rewritten with the next change to the
  formats. (Noted 2026-11-15.)

- A key list compares names byte for byte, so `ALICE` beside `Alice`, or
  one name in two Unicode forms, would be two holders. The tool's own
  first list can't make that happen; when individuals are added after
  version 1, compare names case-folded and in NFC, in both languages.
  (Noted by #53's narrow check.) The Ur-world's names are the same: it
  refuses only control characters, so U+2028, a zero-width character,
  another case or another form makes another name. One rule for both,
  before step 9 (COURSE.md; noted by #59's independent review).

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
- From #38's approving review, for when the ledger is built (before
  step 9, and step 3 for keys):
  - a copy of a GitHub thread brought into the log names other people's
    accounts; keep the text and replace other accounts with a role or a
    hash, or take it to the founder (P8);
  - which key issues ADMIN's grants: decided at step 11, when ADMIN
    begins; its entry in the key list names its key and nothing more
    (docs/research/KEYS.md, point 8);
  - say who holds the private half of the multiverse's root key, and
    how its every use is logged: answered at step 3
    (docs/research/KEYS.md, point 8): the project, in its private
    repository; the root signs only key lists, and every version is
    published in this repository's history;
  - the ledger and outcomes use the multiverse log from step 9, which
    "When each part is built" brings at step 11: say that a first form
    exists from step 9, or that until step 11 those entries go into the
    Ur-world's log;
  - count entries marked as a floor breach that weren't one only in
    total, never per author, so that marking in good faith costs nothing.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-06.md
