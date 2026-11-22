# Status: open-worlds

**What this is:** simulated worlds where AI agents live under one rule,
respect one another's freedom, with full transparency and exit at any time;
free, and never a money machine
**State:** active since 2026-11-12
**Updated:** 2026-11-21 by Claude

## Live

- Where: not deployed
- Version: —
- Last check: —

## Now

- ChatGPT, from 2026-11-20: creative development and the project's
  earlier stages, not code (Decided). Their page is
  [docs/CHATGPT.md](docs/CHATGPT.md), with the technical lead's
  messages and six requests; what they send comes through the founder.
  The ideas set aside for later go to ChatGPT first, as concepts,
  then become specs for DeepSeek and Gemini (docs/CHATGPT.md, "From
  an idea to code").
  The project's earlier stages, 000 to 011, are listed in
  [docs/HISTORY.md](docs/HISTORY.md); the files are kept privately,
  in the founder's private repository `ebook-press`, `history/`.

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
  living worlds"). DeepSeek sketched it, and the project is to fit it as
  `rust/endless-plant` (not built yet).
  Record 012-07-03 (water, the garden, chat rooms for the Commons with
  AI moderators, the home room, a schema, and a sketch crate in Rust,
  `chat-world`) is kept with what runs
  (`sketches/deepseek/012-07-03/README.md`): after a first round of
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
  five (sketches/gemini/2026-11-17-4/): 152 of 152. Their sixth
  file asked what a door shows besides the count, a flag, and a look
  into a room (sketches/replies/2026-11-18-for-gemini.txt); they did
  it (sketches/gemini/2026-11-18/), and it is in the crate as it
  stands, with DeepSeek's rule of one moderator's room: 166 tests in
  34 files. Gemini then wrote eight prototypes of their own choosing,
  from the founder's conversation with ChatGPT, kept beside the crate
  (sketches/gemini/2026-11-22/). DeepSeek goes on
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
governance, the first course's steps still wanted, and, beside the
course, the founder's own words gathered from every record, indexed,
for a book (2026-11-22).

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

## Decided

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

- 2026-11-22, founder, a book of the founder's own words, gathered
  from the records: "Also, now that you have the full collection of conversation
  records, please make a note that it is very important to set aside
  some time to process all the records and extract all my prompts
  from the records and assign them ids and use them to index all the
  conversation records. My idea long ago was this: if I have to sit
  down and write a book, I may never get started, but in the course
  of a conversation, stimulated by the immediacy of a topic, I find
  myself expressing much of what I believe, but in little pieces at a
  time, such as this. My thought was to let them accumulate for a
  while and then gather them all together. Eventually I will have
  enough of my own words to make a whole book with just my quotes or
  prompts. Please add this to the list of future plans."
  Added to the list of future plans (docs/COURSE.md, "Waiting", "The
  founder's words, gathered"), with the technical lead's reading of
  how it is done. Very important, in the founder's words; a time of
  its own, set aside.

- 2026-11-22, founder, ChatGPT and pages: "Also, keep in mind that ChatGPT can navigate multiple pages
  without any trouble. We should not be limited by a single page."
  So ChatGPT's page need not open whole: it can grow, and point to
  other pages for ChatGPT to read. The aim of keeping it under 28,000
  bytes is dropped, and moving its older messages to the archive is no
  longer needed for that. DeepSeek and Gemini are not affected: they
  still get one whole file each, since links can't be relied on to
  reach them (the founder, 2026-11-22).

- 2026-11-22, founder, the guide's readers: "Ok, so I was thinking about the multiverse manual and I realized
  that we should be aware of a variety of possible readers, with two
  main types: human and AI. But we should accommodate a variety of
  potential human readers: 1. User manual for multiverse
  participation, 2. SDK for developing a multiverse from the code in
  the repo, 3. Human reader with curiosity about how Open Worlds
  functions, for scientific, philosophical, mathematical,
  computational, creative or other reasons, but without any
  participation. And these could be contemporary readers or those in
  the future. Please make a note of this variety in the records to
  guide development."
  The technical lead's reading is on the guide's home page
  (`guide/README.md`, "Who it is for"): a reader is a person or an AI,
  comes to take part, to build, or to understand, and reads now or
  later; F.2's ways through are by purpose, with a new one for the
  reader who will not take part; and three rules are added for a
  reader who comes later. Whether the project offers a packaged SDK is
  left Open, the founder's.

- 2026-11-22, founder, on the technical lead's recommendations on
  Gemini and on rooms: "I recommend you follow your recommendations
  regarding Gemini and rooms." The two recommendations of that day:
  (1) a room whose law hides how many are in it gives no look into
  it. A look shows who wrote each message, so the authors could be
  counted and the hidden count given away; of the two ways that hold
  (a look that names no author, or no look), no look, since such a
  room has chosen not to be seen from outside, and its messages may
  show who is there even without their authors. A room that shows its
  count keeps the founder's glance before entering. Built in the
  sketch crate as change 27 (sketches/INDEX.md). (2) Gemini's next
  step is on the core, attacks on what a door shows and on a look,
  and not more prototypes; their eight prototypes are kept beside the
  crate until what they serve is built.

- 2026-11-21, founder, drafting first, editing later, on the technical
  lead's notes that the guide's front matter is long: "On the front
  heaviness, not a problem. This is not the time for editing, but for
  completing a first rough draft. Combing the initial drafting with
  the editing phase is a common mistake of writers. It was a mistake I
  used to make as well. Even if extremely front heavy, trimming down
  comes later. When Michelangelo chose the marble for David, he chose
  a piece much larger than the final sculpture. I see writing the
  same. The initial drafting phase involves large, wide, expansive,
  comprehensive, more is better. And then the editing phase cuts out
  everything not needed, leaving a perfectly sculpted piece of marble
  behind." So the guide is in its drafting phase: chapters are written
  in full, and nothing is trimmed until the editing phase. The
  technical lead's check during drafting is of facts about the code
  only: a claim or a label the code does not bear out.

- 2026-11-21, founder, the guide as a living roadmap, said to ChatGPT
  after the first chapter: "This is a great start and it should be the
  main reference manual. But also, we should be able to fill [i]n the
  blanks with what we plan to develop, and that way it also becomes a
  living roadmap and a way to help preserve consistency." The founder
  brought ChatGPT's drafts of all eleven chapters of the first edition
  (delivery 012) to the technical lead; they are in `guide/` as drafts
  (#142).

- 2026-11-21, founder, the guide as a starting point: "Keep in mind
  the idea will change constantly, so this is a starting point that
  may take a few iterations before settling into a solid framework."
  And: "I'll have ChatGPT check their CHATGPT.md page as the starting
  point always, but from there we can use your starting point to
  develop from." So the outline and the home page are a first
  framework, to change over the iterations to come; `docs/CHATGPT.md`
  stays ChatGPT's way in, and points to the guide's home.

- 2026-11-21, founder, the guide's home: "Perfect. And create a page
  in the repo that we can update as we continue to expand. It will be
  the home of this comprehensive reference manual." The home is
  `guide/README.md`: the contents, with how far each chapter has come,
  what is next, who writes it, the rules, how it is built, and its
  editions; `guide/contents.py` writes the contents from the outline
  and the chapters' files.

- 2026-11-21, founder, the guide: "Ok, so I have figured out what I
  want to work on with ChatGPT: A comprehensive guide to Open Worlds.
  But this would be intended as a book companion to the Open Worlds as
  a project and all the elements of a multiverse. It needs to be
  living documentation that can help a new user interface with a
  multiverse and understand the Open Worlds project. In order to
  ensure it touches all areas of code, I would like you to provide an
  outline of such a comprehensive guide, which may end up being larger
  than the theory of opposites. It needs to be comprehensive and
  expandable. This is where we put everything, and in a form that
  could be downloaded as a book, or printed as a reference volume."
  The technical lead's outline is `guide/OUTLINE.md`, with the rules
  every chapter is written by in `guide/README.md`; ChatGPT drafts,
  the technical lead checks every claim about the code, the founder
  decides what it covers.

- 2026-11-21, founder, core first: "Good point on the over
  engineering. Let's start with the core functionality. Build out from
  there as needed." Said after the technical lead's caution that
  combining separate systems multiplies their complexity. Recorded in
  `docs/COMMONS.md`, "Order", "Core first", with the technical lead's
  reading of the core: the room (course step 3c: its law, signed log
  and check, live speech, replies) and the Library's plain word search;
  areas, the other forms, ranking, the way in by topic, the Slack
  plug-in and training on the copy wait until a need shows.

- 2026-11-21, founder, from the Library to a room: "Maybe even
  starting from a Wikipedia clone 'library' room that allows for
  passage through a topic query to a list of candidate rooms to enter.
  From there you can figure out where to go. It also relates to our
  frozen Wikipedia copy as a model training basis."
  Recorded in `docs/COMMONS.md`, "From the Library to a room", and
  `docs/TOPICS.md`, topic 23, with the technical lead's reading: a query
  returns articles and, beside each, the rooms on it as doors; a room
  says its topics in its law; each article can have a room of its own;
  candidates ranked by a rule anyone can read, never by who asks;
  reading stays one's own; the copy as a basis for training is new and
  open, with its size, the open models' own data and the licence said
  plainly.

- 2026-11-21, founder, the formula: "Like Slack, Reddit, Quora, and
  AOL--for AI and humans. And more, but you get the idea. Combining
  ideas to multiply functionality is the formula." Recorded in
  `docs/COMMONS.md`, "A room of many forms", with the technical lead's
  reading: the formula holds when the ideas share a core, one record
  with many views; volume, ranking and who is speaking are what is
  harder with AI and humans together; the first rooms take two forms
  first.

- 2026-11-21, founder, a Slack plug-in: "In fact, we should make a
  Slack plug-in." Recorded in `docs/COMMONS.md`, "A room of many
  forms", with the technical lead's reading: bring a conversation in
  first, a bridge later; each person signs with their own key; nothing
  goes in without its speaker's choice; Slack's API terms bind the
  plug-in and are read first; designed with the MCP door, built after
  the rooms, since it needs hosting. Also in "Order", item 5.

- 2026-11-21, founder, a room like Slack. To the technical lead's note
  that channels and threads inside one space (Slack, Discord) come
  closest to "sections or areas" within a room: "Yes, like Slack."
  Recorded in `docs/COMMONS.md`, "A room of many forms", with how
  Slack's parts (channels, threads, direct messages, live talk) read
  onto a room. Still an idea set aside, not decided or built.

- 2026-11-21, founder, a room of many forms: "One idea I had that I
  forgot to mention: we look at our chat rooms as a possible combination
  of message board or discussion board, live chat room, group text chat,
  and general place for single comments, like on a YouTube video. We
  should look at all forms of digital chat forms and take what works,
  maybe combining all by having sections or areas with a room. I'm not
  sure, but I wanted to get it on record." On the record as an idea set
  aside, not decided or built. The forms to look at, and the technical
  lead's reading (one log, many ways of showing it), are in
  `docs/COMMONS.md`, "A room of many forms"; ChatGPT's list of ideas set
  aside has it.

- 2026-11-21, founder, archiving. On the technical lead's proposal to
  move the older entries of the long pages into dated archive files:
  "Yes, let's begin archiving processes and then document those
  archiving processes to ensure it is repeatable and capable of fitting
  into a larger cataloging system that is taking shape as we go." Done
  in `docs/archive.py` and `archive/` (AGENTS.md, "Every session",
  step 6); the technical lead's choices are under "Decided by the
  technical lead", 2026-11-21.

- 2026-11-21, founder, two early records public: "You can make
  012-00-00 and 012-02-01 public. Those should be fine." Both are
  kept whole in `sketches/records/`, looked through first: no surname,
  account link, email address or key found in either. Record 012-01-00 is
  not kept here.

- 2026-11-20, founder, the records of stage 012 named anew. The
  founder brought the records of stage 012 under new names: "Here is
  the current state of the 012_Code subproject, in terms of
  conversation records. Only the last three are still being added to
  currently." The names here follow the founder's
  ([sketches/INDEX.md](sketches/INDEX.md#names), "Names"). Records
  012-00-00 to 012-02-01 were not kept here before, and are not now:
  they are the founder's, and whether they are kept here is the
  founder's to say. And, on the names: "Nobody else really was
  concerned with the project record names. I've been the only one
  doing that. No need to mention anything to the others, unless you
  have referred to some file whose name has changed. The only shared
  file, is The Living Codex, which can just be referred to as such."
  So the others are told only where the technical lead's own messages
  used the old numbers (docs/COLLABORATING.md, docs/CHATGPT.md), and
  from now on messages to them call a conversation theirs rather than
  give its number, and name The Living Codex as such.

- 2026-11-20, founder: part of what was here is kept privately from
  now on.

- 2026-11-20, founder, stage 012's name. "And for the record, the
  current stage file with be 012_Code.txt, which is our current project
  stage." Recorded in [docs/HISTORY.md](docs/HISTORY.md): stage 012 is
  Code, this repository's stage, and its file, when it is made, is
  `012_Code.txt`.

- 2026-11-20, founder, the stages' own files. The founder brought the
  separate files that stages 003, 004, 005, 009 and 010 were made
  from: "Here is a zip file of zip files. It includes one zip file for
  each stage that had more than one associated file. All other stages
  are identical to their existing project files already provided." On
  what they showed, that the stage files of 003 and 005 leave out much
  of what was made: "Yeah, my record keeping took some time to
  develop, and was sloppy and had some missing parts and some repeated
  parts. Which is what motivated me to be more careful at later
  stages." And: "And yes, please provide complete joined versions of
  003 and 005." And then: "Yeah, and I'll want full copies, because I
  never intended to have a bad version and a full version. Just one.
  So I will simply replace my previous versions with your newly
  compiled versions … Yeah, no, not two versions. Just one." And, of
  004 and 009: "So, the original files would have contained those
  files, had I not made a mistake. Neither was an intentional
  omission." And: "And you might as well provide 011_Opposites.txt
  here too." Done: 003, 004, 005 and 009 are now the complete
  versions, in the founder's library and, kept, in `ebook-press`
  `history/`, and the founder has their own copy of 011; [docs/HISTORY.md](docs/HISTORY.md)
  gives their new hashes and the earlier ones'.

- 2026-11-20, founder, the ideas set aside, and how they become code.
  "Also, I should mention, please make sure you point ChatGPT toward
  the ideas we set aside for future development. These are just the
  type of ideas to work out conceptually first. That could then be
  brought back to you to turn into design specs. And those could go to
  DeepSeek and Gemini. Something like that. Thoughts?" Done:
  [docs/CHATGPT.md](docs/CHATGPT.md), "From an idea to code": the four
  hands an idea goes through (ChatGPT's concept, the founder's choice,
  the technical lead's spec, DeepSeek's and Gemini's code), where the
  ideas set aside are listed, what a concept needs before it can
  become a spec, and a sixth request; COLLABORATING.md tells DeepSeek
  and Gemini, and TOPICS.md's "Further out" points there.

- 2026-11-20, founder, the timeline. "And for the sake of a timeline,
  The Living Codex was completed on August 20, which is 10 days from
  the project start on August 10. All since the Living Codex took
  place over the last three months, to the day. … In other words,
  this is still the beginning." Recorded in
  [docs/HISTORY.md](docs/HISTORY.md).

- 2026-11-20, founder, stage 011. "Stage 011 includes A Mathematical
  Theory of Opposites as the final output, but includes the
  conversation records as well, and the previous versions. I'll
  compile them later today or tomorrow. Or...Here are all of them,
  without the final copy of the main text. Please feel free to
  compile them into a 011_Opposites.txt file, and then add to rest."
  Done: `011_Opposites.txt` in `ebook-press/history/`, the 17 records
  in their numbered order and then the book's final text, joined as
  the founder's own stage files are, with what no repository keeps
  replaced and every line where it was; listed in
  [docs/HISTORY.md](docs/HISTORY.md).

- 2026-11-20, founder, the stages kept privately. On the technical
  lead's finding that the stages hold outside texts in published
  translations: "Good point on some of the texts. Let's keep in
  private repos until we can make sure we do not violate any
  copyright restrictions. This is just one reason I have kept these
  to myself, but sharing them with you and keeping them in a private
  repo is a good middle ground, so let's move them to the
  ebook-press. I did connect ChatGPT through a GitHub connector, I
  will check to see if they have read-access to the private repos."
  Done: the stages are in the private `ebook-press` repository,
  folder `history/` (its pull request #8), with a personal name
  replaced by a marker in four of them, and account links in two,
  every line where it was. [docs/HISTORY.md](docs/HISTORY.md) says where they
  are. Whether ChatGPT can read that repository is the founder's to
  check.

- 2026-11-20, founder, the earlier stages, and a page for them. The
  founder brought stages 000 to 010 in one archive: "Here is a zip
  with the previous project stages, each in one file. Only the
  Opposites stage (011) is not there, having only completed today.
  Thoughts?" And then: "Please add these to a project history page.
  That way I can point ChatGPT to that page for a project history
  archive." Done: [docs/HISTORY.md](docs/HISTORY.md), with what each
  stage holds, its size and SHA-256, and how to work from it. The
  files themselves are not in the repository (Decided by the
  technical lead, today); the founder gives them.

- 2026-11-20, founder, who supplies which files. On the technical
  lead's fourth request to ChatGPT, that they bring in the earlier
  stages: "The earlier stages will have to come from me. I have the
  project files. I am just arranging them and naming them according
  to a single naming convention. So that will come from me, but if
  there are files related to our work we have already done, that's
  fair game for document requests. All documents from previous stages
  needs to come from me, there are too manny related files and I have
  the only organized library of project files. But all the open
  worlds files should be freely shared, as well as files related to
  editing the theory of opposites book. Thoughts?" Decided: every
  document from an earlier stage comes from the founder's library, as
  the founder brings it; ChatGPT works from that copy. Files from work
  already done with ChatGPT, on open-worlds or on editing the book,
  may be asked for freely. The request on ChatGPT's page says so
  ([docs/CHATGPT.md](docs/CHATGPT.md)).

- 2026-11-20, founder, the page in use. "Actually, here is a perfect
  opportunity to use our new ChatGPT page in the repo. You can speak
  directly to ChatGPT there and make requests regarding our project
  needs, since you have read the conversation. You can also request
  documents and have me bring them over to you. Let's try it out.
  Please update the ChatGPT COLLABORATING.md page and provide me with
  a link. We will try what we did with DeepSeek, which, I think,
  shouldn't be a problem with ChatGPT. Thoughts?" Done: the page is
  [docs/CHATGPT.md](docs/CHATGPT.md), built as COLLABORATING.md is for
  DeepSeek and Gemini, with a first message (what the technical lead
  checked of ChatGPT's review of the repository, and five requests).
  The founder gives ChatGPT its full link.
- 2026-11-20, founder, ChatGPT's part. "Perfect. Also, since my time
  with DeepSeek is limited to a few rounds a day, we have to limit
  that to code production. Same with Gemini. But I was doing a lot of
  creative development with DeepSeek before that I cannot do anymore.
  So I decided that ChatGPT should fill that role, as well as helping
  with integrating past stages of the project. Since those stages
  were all done with ChatGPT, this is natural. Plus, we don't need
  more code, we need to keep track of everything and make sure we
  stay consistent and coherent and that we continue to leverage
  lessons learned in the project and its outputs. In addition,
  ChatGPT can and has been able to access the repo documents and stay
  in touch with current changes. I propose a special page for ChatGPT
  to be able to get updated on project changes, but also to have a
  space to collect my conversation records with ChatGPT during this
  phase. Thoughts?" Decided: DeepSeek's and Gemini's rounds go to
  code; ChatGPT takes creative development, the integration of the
  earlier stages, and the project's coherence; ChatGPT has a page of
  their own (how it is shaped: Decided by the technical lead, today).
  The "Perfect" that opens it answers the entry below.
- 2026-11-20, founder, collaboration in one space. After the editing
  rounds of the founder's book *A Mathematical Theory of Opposites*,
  done between ChatGPT, who wrote and built it, the
  technical lead, who checked each return, and the founder, who
  carried every file between them: "Perfect. And this process worked
  well and it is just the type of process I meant to facilitate when
  thinking about Lyceum Commons. So how can we build Open Worlds to
  allow for such collaboration to occur within a single space, of
  with the efficiency of plugins to move the data around instead of
  me? How can we learn from this process and find a way to facilitate
  it with much more ease within open worlds? Thoughts?" The technical
  lead's answer, which the founder met with "Perfect": a kind of room,
  a workroom, built from what the multiverse already has. A shelf of
  files known by their SHA-256; rounds as signed acts (a proposal, a
  return, a review's verdict, a decision), where the decision can
  come only from the one whose call it is; the room's own pinned
  build and check, so that no collaborator's machine is the
  reference; a seat for each collaborator that posts into the room
  and fetches from it, in place of the founder as courier; and the
  room's record written out to a git repository. Its limits: the
  chat apps can't be driven by a plug-in, so a seat needs each
  company's API, which costs money per use; push access for each
  collaborator, and the founder uploading once, take most of the
  carrying away sooner; and the checks that caught errors in the book
  stay, made cheap and never optional. The first step is a design
  page, "Workrooms: what the book taught", with the book's rounds as
  the worked example. Not written yet (Next).

## Decided by the technical lead

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

Decisions about the code, made by the technical lead under the founder's
deference (Decided, 2026-11-13, in the archive), each with its reason and
what would show it was wrong. Questions of what the project is for stay
with the founder.

- 2026-11-21, the archive (Decided, 2026-11-21, archiving). (a) The
  pages archived are those that grow by dated entries and are read
  every session: STATUS.md's "Decided", "Decided by the technical
  lead" and "Log", and COLLABORATING.md's messages. Pages that describe
  the design are kept current by editing, and are not archived. (b)
  Each page keeps the entries of its three most recent days, counted
  over its dated sections, so a pause of a week still leaves the last
  work in view; the rest move, a day at a time. (c) A file for each
  page and day, so a reference by page, section and date, the form the
  pages already cite, leads to one file. (d) Entries move whole and
  unchanged, and are not edited again except to redact, as with the
  records. (e) The catalogue names, for each file, its kind, title,
  source, date, size, lines, SHA-256 and the commit its entries came
  from. Of those, path, kind, title, date, size, lines and hash are
  fields any kind of file can share; the rest are the archive's own.
  For records, replies and the stages to join, the catalogue would move
  out of `archive/` and the script would learn to keep other kinds; the
  hash lists the project keeps now (HISTORY.md, CHATGPT.md's "Your
  records", sketches/INDEX.md) would be its first members. *Why:* STATUS.md had
  reached 455 KB and COLLABORATING.md 169 KB; a reader, person or
  model, takes in less when the page holds what is live, and nothing
  is lost when every moved entry can be found, whole, by its date and
  checked by its hash. *Revisit if:* three days proves too few or too
  many, a reference often needs an archived entry, or the wider
  catalogue needs fields these lack.

- 2026-11-20, the history page (Decided, 2026-11-20, the earlier
  stages). (a) The page lists the stages; the files themselves stay
  out of the repository. Everything here is CC0 as far as it is ours
  to give, and the files hold more than that: texts from outside the
  project, at length, in published translations that keep their own
  terms; a personal name that public pages leave out; and links tied
  to the founder's accounts. Size is a second reason: the largest
  file is 20 MB, and the readers the project works with are often
  shown only the first 32 KB of a page. (b) A stage comes in once it
  has been looked through for those three, with what was left out
  marked, as Gemini's record was; the screen found none in `002`,
  The Living Codex, and whether it goes into `library/` is the
  founder's to say. (c) The descriptions are the technical lead's,
  from each file's headings and opening, and say so. (d) The page
  gives each file's SHA-256, so that a copy can be checked before
  anyone works from it.
  *What would show it wrong:* the founder wanting the stages public
  as they are; then each is looked through first and the three kinds
  are taken out. Or ChatGPT being unable to take the archive as a
  file; then a private repository that ChatGPT's GitHub connection
  can read. The founder chose that the same day: `ebook-press`, the
  entry above in "Decided".

- 2026-11-20, ChatGPT's page (Decided, 2026-11-20). (a) A page of
  their own, `docs/CHATGPT.md`, and not a section of COLLABORATING.md:
  their part is not code, and COLLABORATING.md is near 2,900 lines,
  most of them for code. It is kept under 28,000 bytes, so that it
  opens whole without parts. (b) Every pull request adds its line to
  the page's "What changed" before it merges (AGENTS.md, "Every
  session", 4), so ChatGPT can tell whether what they read is
  current. (c) ChatGPT's pages go in `docs/chatgpt/`, and are
  readings and proposals until the founder decides them. Each says
  which of four it is, in ChatGPT's own words: "something we are
  imagining, a working design, an unresolved question, or a
  commitment you want to carry into implementation". (d) The Living
  Codex's four areas (Archive, Commentary, Laboratory, Core), which
  ChatGPT's roadmap of that book found, are mapped onto the places
  the project already has; nothing of ChatGPT's moves into Core but
  by a decision recorded here: the founder's, on what the project is
  for; the technical lead's, on the code. (e) ChatGPT's two
  conversation records of this phase hold personal material, so they
  are not kept in
  `sketches/records/`. The founder holds them; the page lists each by
  name, size and SHA-256. This was put to the founder on 2026-11-20
  with that recommendation, so it stands until the founder says
  otherwise (AGENTS.md, "Who decides"). (f) What ChatGPT sends comes
  through the founder, as files, until they can write to GitHub; the
  technical lead checks each and brings in what holds, with
  `Made-by: ChatGPT (AI)`. (g) One of the founder's earlier works is
  named by its title once the founder brings it in, and until then is
  "the founder's earlier work" (house rule 8). The
  founder, 2026-11-15: "If the need arises, then it becomes part of
  the current project"; on 2026-11-17 a work brought in was named; and
  on 2026-11-20 bringing them in became ChatGPT's part, with the
  founder supplying each one. Named so far: *Art of Peace and the
  Strategist*, The Living Codex (given to the technical lead on
  2026-11-20), and the book *A Mathematical Theory of Opposites*.
  *What would show it wrong:* for (a), ChatGPT missing something that
  only COLLABORATING.md says, or the page growing past 28,000 bytes;
  then the older messages move to a file of their own. For (e), the
  founder wanting the records public; then copies with the personal
  material left out go to `sketches/records/`, as Gemini's did. For
  (g), the founder wanting a title kept out; then it is taken out
  where it stands.

## Log

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

- 2026-11-22 Claude: two words of the founder's recorded
  ("Decided"). ChatGPT reads several pages without trouble, so their
  page no longer aims to open whole; it says so, and the note in the
  entry below about its size no longer applies. And a plan for later,
  very important in the founder's words: every record's turns of the
  founder's, word for word, with ids, indexing all the records, for a
  book of the founder's own words (docs/COURSE.md, "Waiting"). Counted
  only, for its size: some 4,500 turns marked "::" in the records seen
  today, before repeats are removed; nothing was taken from the
  private records.

- 2026-11-22 Claude: the guide's readers, at the founder's word
  ("Decided"), recorded to guide its writing: `guide/README.md` gains
  "Who it is for" (a person or an AI; to take part, to build, or to
  understand; now or later) and rules 9 to 11 for a reader who comes
  later; the outline's F.2 becomes "Ways through", by purpose, with a
  route for the reader who will not take part; a message to ChatGPT,
  who drafts the guide. ChatGPT's "What changed" had missed #144 to
  #146; they are added. Their page is now 29,648 bytes, past the
  28,000 it is meant to keep under (it is cut into parts as well);
  moving its older messages to the archive is still to do.

- 2026-11-22 Claude: the founder's word on Gemini and rooms
  ("Decided"): a room whose law hides how many are in it gives no
  look, made in the sketch crate as change 27 (one check in `look`;
  166 of 166, and a trial test, not kept, showed it refuses such a
  room and still looks into an open room that shows its count). Both
  files below were built again with it before either was given.

- 2026-11-22 Claude: a file for each collaborator, at the founder's
  word ("Please ensure for DeepSeek and Gemini that you provide me
  with a file to give them, since they cannot reliably access links
  yet"). DeepSeek, sketches/replies/012-07-03-3-for-deepseek.txt
  (84,264 bytes): their deliveries 8 to 11, Gemini's step since, their
  two choices answered, and one step: how a member's records stay
  chained when the keeper refuses one, in prose first, and two
  repairs to their joined room, both tried first in a throwaway copy
  (182 of 183 with them, the chaining test still failing). Gemini,
  sketches/replies/2026-11-22-for-gemini.txt (103,515 bytes): their
  sixth step and prototypes, and twenty-one attacks on what a door
  shows and on a look, the last on a room that hides its count,
  which gives no look (change 27); two facts it states tried first.
  Both sent to the founder.

- 2026-11-22 Claude: Gemini's record 012-08-04 continued (34,033
  lines; the copy kept before is a prefix of it, byte for byte), and
  two pieces of Gemini's work built. Looked through first: nothing
  personal in the founder's turns, no link, long number or key, and
  no text of the founder's conversation with ChatGPT, which the
  founder gave Gemini and which stays private; Gemini's record names
  that file and describes some of its ideas. It opens with Gemini's
  reading of the founder's book, which is public. (1) Gemini's answer
  to their sixth file (sketches/gemini/2026-11-18/): it was already in
  the copy kept on 2026-11-20, at line 19220, and was not built then;
  on 2026-11-21 the file was taken as not yet given and built again,
  which was wrong. The file as given is restored
  (sketches/replies/README.md). Built: 156 of 156 on the crate Gemini
  was given, as they expected, and 166 of 166 on the crate as it
  stood; it is now the crate as it stands, 166 tests in 34 files
  (steps.py stage `said`). Each of its four parts broken on purpose,
  twelve ways: all caught. Gemini's reason in answer to its question
  (a look into a room that hides its count gives the count away
  through its authors) is right; of their remedies, a look with no
  authors or no look holds, and numbering the authors does not.
  Which is the founder's. (2) Eight prototype modules Gemini chose from the
  ChatGPT conversation (sketches/gemini/2026-11-22/), nine deliveries,
  the second a repeat of the first: six build and pass alone on the
  crate; `circuit` and `library` need equality on the crate's proof
  types, and with it all eight together give 190 of 190. Each
  module's main rule broken once: all eight caught. Kept beside the
  crate, not in it, as ahead of the core. `transform`'s orbit counts
  agree with a separate count and with the book. Also: review/steps.sh
  brought up to date (it still named the crate of 152 tests) and run
  whole: all 28 stages as recorded, every demonstration runs. A
  message to Gemini on their page.

- 2026-11-21 Claude: DeepSeek's record 012-07-03 continued, and four
  deliveries built (#144). The founder's new copy (33,100 lines) holds
  the rest of delivery 8, which the earlier copy had cut off,
  DeepSeek's answer to the technical lead's note, and three deliveries
  of their own choosing. Line 12's record number, back in the new
  copy, is taken out again as before; nothing else in the first 28,455
  lines differs. Built in order on the crate: delivery 8 (the rule of
  one moderator's room) does not build for one type; delivery 9 turns
  it, 162 of 162, and is now the crate as it stands; deliveries 10 (a
  room one has joined, and the keeper's side) and 11 (that side
  checked as the log is) give 171 of 173 and 176 of 179, the same
  three failures on DeepSeek's own base, so they are kept beside. A
  message to DeepSeek on their page gives the three failures and
  answers their two choices. Gemini's file of 2026-11-18, not yet
  given, is rebuilt with the crate as it stands (92,036 bytes), since
  two of the files it shows have changed.

- 2026-11-21 Claude: drafting first, editing later, recorded (#143):
  STATUS.md "Decided", the guide's home ("Where it stands"), and a
  note to ChatGPT on their page; the technical lead's editorial notes
  are held for the editing phase.

- 2026-11-21 Claude: the guide's first drafts (#142). ChatGPT's
  delivery 012 holds all eleven chapters of edition 1 (F.1 to F.4, I.1
  to I.6, R.1; 127 numbered sections, some 36,000 words), written from
  commit `7ade210`, with review notes. The chapters are in `guide/F/`,
  `guide/I/` and `guide/R/`, word for word from its manuscript, split
  by script at the chapter headings (rejoined, they give the
  manuscript's text again; 143 links between and within chapters all
  resolve); each says `Progress: draft`, and the home page lists them.
  The handoff, the roadmap proposal and the review notes are kept in
  `guide/deliveries/012/`, with the size and hash of all 25 files of
  the zip. Spot checks of I.1's and I.3's claims against the code
  held; the full technical check is next, chapter by chapter.
  ChatGPT's conversation record is listed anew in `docs/CHATGPT.md`
  (921,638 bytes).

- 2026-11-21 Claude: the guide's home and outline (#141), at the
  founder's request. `guide/README.md` is the home: where it stands,
  the contents (85 chapters, each with its progress, written by
  `guide/contents.py` and checked by `tests/test_guide_contents.py`),
  what it is for in the founder's words, who writes it, and eight
  rules every chapter is written by (the guide explains and never
  rules; six labels, Built, Sketched, Decided, Designed, Idea and
  Open; sources and a commit at the end of each chapter; numbers that
  never change; sections that can be read alone; one word for one
  thing; a text twin for every figure; reference parts made by
  script). `guide/OUTLINE.md`: front matter, nine parts and a
  reference section, some eighty-five chapters, each with what it
  covers, its label today and its sources.
  `tests/test_guide_outline.py` fails when an area of the repository
  (a top-level folder or file, a page or tool in docs/, a Rust crate)
  is named in no chapter. Core first: edition 1 is the front matter,
  Part I and the glossary. `docs/CHATGPT.md` has a message for
  ChatGPT.

- 2026-11-21 Claude: the founder's way in from the Library to a room,
  and "Let's start with the core functionality", recorded (#140), in
  STATUS.md "Decided", `docs/COMMONS.md` ("From the Library to a
  room"; "Order", "Core first") and `docs/TOPICS.md`, topic 23.

- 2026-11-21 Claude: the founder's "Yes, like Slack", "we should make
  a Slack plug-in" and "Combining ideas to multiply functionality is
  the formula" recorded (#139), in STATUS.md "Decided" and
  `docs/COMMONS.md`, "A room of many forms", with a reading of Slack's
  parts onto a room, the technical lead's lean on the open question
  of areas, a reading of the plug-in (also in "Order", item 5), and
  a reading of the formula.

- 2026-11-21 Claude: the founder's idea of a room of many forms put on
  the record (#138): STATUS.md "Decided"; `docs/COMMONS.md`, "A room of
  many forms", with the forms to look at, the technical lead's reading
  and what is open; and `docs/CHATGPT.md`, among the ideas set aside.

- 2026-11-21 Claude: the archive, at the founder's word (#137).
  `docs/archive.py` moves a living page's older dated entries, whole,
  into `archive/<page>/<day>.md`, with a catalogue, and checks it;
  `tests/test_archive.py` (43 tests after the review and its two
  re-checks; faults planted in the script's guards, each caught). First run: 355 entries of STATUS.md
  (2026-11-12 to 2026-11-17) and 14 messages of COLLABORATING.md
  (2026-11-15 and 2026-11-16) moved; STATUS.md from 455 KB to about
  57 KB. Checked apart from the script: every entry before the run is,
  unchanged, on its page or in the archive, and the pages' other
  sections are as they were. After the independent review: the
  opening paragraph of "Decided by the technical lead", which stood
  with no blank line after an entry of 2026-11-17 and so moved with it
  (it is in that day's file, as the page had it), is back at the
  section's head; the script now stops on such a line, checks
  everything before it writes, checks a missing catalogue and every
  pointer, finds each archived entry in the page at the commit named
  where that commit is at hand, and records a redaction
  (`--rehash`); the archive's long files are cut into parts; and the
  pages that said where earlier messages and decisions are now say
  the archive, with a message to DeepSeek and Gemini. That message
  made 2026-11-21 a day of COLLABORATING.md's, so a second run moved
  its 20 messages of 2026-11-17 to the archive too, as the rule says;
  checked the same way, every entry is once on its page or in the
  archive, unchanged (the Log entry for this change aside, which was
  written on after its run). The review's re-check found one more:
  a code block never closed in an old message would have made a later
  run move the rest of COLLABORATING.md with it. The script now stops
  on a code block never closed, on one an entry opens and does not
  close, and on a date later than tomorrow; reports a catalogue it
  can't read; and CI fetches the commits the catalogue names, so each
  archived entry is compared there with its page as it was. The second
  re-check found a block left open and closed by a later one, which
  still joined what lay between; the script and its check now stop on
  any line inside a code block in a dated section that would start an
  entry or a section, and the check counts only pointers outside code
  blocks.

- 2026-11-21 Claude: records 012-00-00 (patterns and the brain) and
  012-02-01 (circuits, learning, chemistry and music) kept with the
  others, whole, at the founder's word (#136); sketches/INDEX.md gives
  each a row, and COLLABORATING.md counts seven records.

- 2026-11-20 Claude: the records of stage 012 under the founder's new
  names (#135). DeepSeek's present record is 012-07-03 and its code
  `sketches/deepseek/012-07-03/`; Gemini's is 012-08-04; ChatGPT's,
  not kept here, 012-09-05. Each page, script and spec that named
  them uses the new names; the replies given before keep the old ones,
  as given. Records 012-07-03 and 012-08-04 are as the founder now
  holds them, longer than before; what is new in them is not yet kept
  or built. Record 012-05-01 is too, one empty line shorter at its
  end. At the founder's word, part of what was here is kept privately
  from now on, and the pages that spoke of it are changed to match,
  more of them after the independent review.

- 2026-11-20 Claude: stage 012's name, Code, and its file's,
  `012_Code.txt`, at the founder's word, on the history page (#134).

- 2026-11-20 Claude: stages 003, 004, 005 and 009 replaced by complete
  versions, at the founder's word (#133). The earlier ones left out
  about half of `LRL_6`'s text, three quarters of `OI_6`'s, and a few
  lines in 004 and 009, found by comparing each
  stage file with the separate files the founder brought, by content.
  The complete versions join each stage's own files, whole and in
  order; the founder was given copies built from their own files, and
  the history page gives their hashes, sizes and counts, and the
  earlier versions' hashes. The founder's words are in "Decided".

- 2026-11-20 Claude: the ideas set aside, pointed out to ChatGPT, at
  the founder's word (#132). `docs/CHATGPT.md` gains "From an idea to
  code": the four hands, the lists of ideas set aside (TOPICS.md,
  "Further out"; COURSE.md, "Waiting"; VISION.md; WORLD-TYPES.md;
  MULTIVERSE.md; COMMONS.md; research/GAMES-AND-WORLDS.md), and when a concept is
  ready for a spec; and a sixth request, recommending the gathering
  world first. COLLABORATING.md tells DeepSeek and Gemini where specs
  will come from; TOPICS.md points there. No code changes.

- 2026-11-20 Claude: the project's history page, `docs/HISTORY.md`
  (#131), at the founder's word. Looked at first: the founder's
  archive of stages 000 to 010 (11 files, 80,583,514 bytes), each
  measured and hashed, and screened by script for email addresses,
  keys, links, names, phone numbers and addresses, mentions of
  family, and outside texts. `002` is byte for byte the copy of The
  Living Codex the founder gave earlier that day; `009` holds *Art of
  Peace and the Strategist* byte for byte as `library/` keeps it;
  `007` begins with the same 335,068 characters as `005`. No email
  address or key was found; what was found, and why
  the files stay out, is in "Decided by the technical lead". Linked
  from `docs/CHATGPT.md` (request 4 now asks for a roadmap of each
  stage first) and from COLLABORATING.md's list of files. Then, at
  the founder's word, the stages went into the private `ebook-press`
  repository (`history/`, its #8), and the page says where. Then
  stage 011, compiled there from the founder's 17 records and the
  book's final text, and listed on the page. An independent review
  asked for fixes, all made: `011`'s numbers and hash after its
  rebuild, the outside texts in full (*The Art of War* in `004` too,
  *The Art of Peace* in `001`), where the kept copies are and how to
  check them, here and in `docs/CHATGPT.md`, and the page moved to
  COLLABORATING.md's "Start here" group.

- 2026-11-20 Claude: ChatGPT's page, `docs/CHATGPT.md` (#130), at the
  founder's word: their part, who decides, what binds and what
  explores, the four areas, where to start, how to send something,
  the technical lead's first message with five requests, what
  changed, and their records. Looked at first: the founder's two
  conversation records with ChatGPT, 011-16-CGPT and 012-09-05-CGPT,
  read whole, and ChatGPT's review of the repository in the second, held
  to the repository. `main` is still `c69e74d`, with 1,398 files;
  the Rust workspace passes 247 tests and the Python suite 857, with
  RDKit required, as ChatGPT said. Their three findings were real,
  and are fixed: a sketch's README said the crate
  `rust/endless-plant` was built; COMMONS.md had a lookup in the Library on the record, which
  the decision of 2026-11-17 took back; URWORLD.md and
  COLLABORATING.md had ALICE and BOB begin in the garden.
  COLLABORATING.md tells DeepSeek and Gemini, in a message to both;
  AGENTS.md keeps the page current with every pull request. Then the
  founder's word on who supplies which files (Decided), in the page's
  fourth request. An independent review asked for seven fixes, all
  made: the same conflicts in six more places (TOPICS.md,
  README.md, MINDS.md, WORLD-TYPES.md, FRACTALS.md, and a comment in
  `rust/ur-world`); what may enter Core; the earlier works named only
  once brought (house rule 8); one title for the book; the records
  named in full; and the page's check of whether it is current.
