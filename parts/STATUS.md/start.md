> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "Noticed".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-08.md
> Made by docs/parts.py from the file. To change it, change the file.

# Status: open-worlds

**What this is:** simulated worlds where AI agents live under one rule,
respect one another's freedom, with full transparency and exit at any time;
free, and never a money machine
**State:** active since 2026-11-12
**Updated:** 2026-11-20 by Claude

## Live

- Where: not deployed
- Version: —
- Last check: —

## Now

- ChatGPT, from 2026-11-20: creative development and the project's
  earlier stages, not code (Decided). Their page is
  [docs/CHATGPT.md](docs/CHATGPT.md), with the technical lead's first
  message and five requests; what they send comes through the founder.
  The project's earlier stages, 000 to 010, are listed in
  [docs/HISTORY.md](docs/HISTORY.md).

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
  built (2026-11-18), a log whose fields can be redacted, with
  removals and restorings on record: its plan, after looking first, is in
  docs/research/REDACTION.md. Its second part is built: a form of the
  log whose fields are kept apart by salted fingerprints, with the
  contents beside it, the check that holds the two together, and the
  function that joins them (`world/apart.py`, `rust/world-log`, with
  shared vectors). The log's side of its third part, redacting, is
  built: a mark says its office and its ground; one decision answers
  it, to keep the field public or that it stays redacted for good;
  and the writer takes a field out of the contents, and puts it back,
  in step with the log. Its other side is built too, the act of
  redacting: the field is sealed to each person it is about and to
  the office that decides (Decided, 2026-11-17), then marked and taken
  out, and the office decides from its own copy (`world/redact.py`,
  `rust/redact`). The keys are trial keys, and nothing real is
  redacted yet. The log's side of its fourth part is built: what a log
  says in the open when an entry is removed, restored, taken back or
  put back, and each entry's state worked out from that. Its records'
  side is built too: every act in a log is held to the signed record
  it carries, and every office to its grant, up to the room's key;
  and an author's taking back and putting back are records of their
  own in records-v1 (`world/acts.py`, `rust/acts`). Next the course is
  rechecked, as after every step. Then step 3c, the room, where
  DeepSeek's `chat-world` is fitted onto the project's formats.
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
  98 Python tests pass. The record goes on: given one file, DeepSeek
  sent five deliveries of the crate, each file whole. Then Gemini,
  given a file of their own, made the crate's log checkable from
  outside, attacked the check with 22 tests, and repaired what got
  through (sketches/gemini/2026-11-16/). Then, in a second round, they
  did the same for the Commons' own log
  (sketches/gemini/2026-11-17/). Then DeepSeek, from their second
  file, built a room that branches and a plug-in over standard input,
  and began the rule of one moderator's room, where their reply was cut
  off (sketches/INDEX.md, "DeepSeek's second file"). With six small
  repairs the crate as it stands (`chat-world-now/`) passes all 152
  of its tests. Gemini's fourth step, 17 attacks, shows eight gaps in
  the check of a room's log; they are built beside the crate, not
  laid into it, and are kept as the list of what the room's own check
  must refuse. Gemini then built the lobby's list of doors, which a
  map of the Commons is first drawn from
  (sketches/gemini/2026-11-17-2/), and attacked it with 25 tests
  (sketches/gemini/2026-11-17-3/): the crate refused twenty, and
  five got through, as Gemini said they would. Gemini repaired the
  five (sketches/gemini/2026-11-17-4/): 152 of 152. Their next file
  asks what a door shows besides the count, a flag, and a look into
  a room (sketches/replies/2026-11-18-for-gemini.txt). DeepSeek goes on
  with their third step. Fitting the crate to open-worlds' own code is
  step 3c.
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
world-key (11); founding worlds, and doors (12). Since 2026-11-17
ALICE and BOB first live in the Commons (Decided): at the next
recheck, after 3b, their first life moves ahead of the kernel's steps,
with a new step before it, the Library. DeepSeek works beside
the course, by one file at each return, and the fractal track runs
beside it too. Waiting: the Commons' MCP door and going live, the
founder's ideas of 2026-11-16 (personal information in a room, a
gathering world, competition worlds), the founder's visions, a window
onto the worlds, generator 2, storytellers, the gate and districts,
governance, and the first course's steps still wanted.

Beside the course, from 2026-11-20: a design page, "Workrooms: what
the book taught" (Decided, 2026-11-20, collaboration in one space);
and ChatGPT's deliveries, checked and brought in as they come
([docs/CHATGPT.md](docs/CHATGPT.md)).

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
recommendation" is a full answer. By the founder's general guidance of
2026-11-17 (Decided, below), which widens the standing rule of
2026-11-14, the technical lead decides what they can decide and says what
they decided; they do not keep asking. What is left here is only what they
can't do or undo for the founder: spending money, an act that is the
founder's own in law or on the founder's own accounts, and words that
have to be the founder's. None of it holds up the work today, and none
of it is asked again until it is needed.

- For the founder, when the time comes: what becomes of the accounts
  and keys, which are the founder's own today, if the director's office
  passes; and who designates the roles if the founder can't. The rule
  is decided (2026-11-17): the office passes only by the director's own
  recorded word, naming who takes it and from when. Naming a successor,
  or a process, is the founder's own act, recorded where the roles are.
  Neither is needed while the founder is the director. (asked
  2026-11-13 and 2026-11-16)
- For the founder: which model first moderates a room in the Commons,
  and what it costs to run. It is money, and is decided with where the
  multiverse is hosted (docs/COMMONS.md, "Open"), which the founder
  has put last (2026-11-17, Decided): "leave hosting for when the
  final picture is closer". Until then the technical lead measures
  what running the models costs, at the audition (course step 8), so
  that the size is known when it is decided. Whether such a model
  is an individual, with what that would owe them, is decided with it;
  no model is given the office before then.
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

- What the project can't read, it can't moderate or answer for. With
  closed rooms decided as the common kind (2026-11-17), this is looked
  at before the Commons is open to the public with private rooms in
  it: where it is hosted, and under what law. It is the technical
  lead's to look into; it comes to the founder only as what it would
  cost or commit the founder to.
- A log signed by heads in batches has a tail no one has signed.
  Gemini found it in the sketch crate (sketches/gemini/2026-11-16): in
  a room that signs a head every so many records, the records after
  the last head carried only their author's signature, so anyone could
  add one. docs/research/KEYS.md already says the general thing of
  open-worlds' own logs ("Only signed heads protect a reader"), and
  the log check reports how much the heads cover. Gemini's rule goes
  one step further, and is to be weighed when the room is fitted (step
  3c): a log that is published ends with a head that covers all of
  it, and the check refuses one that doesn't.
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
    begins; their entry in the key list names their key and nothing more
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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-08.md
