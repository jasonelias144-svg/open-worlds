# Status: open-worlds

**What this is:** simulated worlds where AI agents live under one rule,
respect one another's freedom, with full transparency and exit at any time;
free, and never a money machine
**State:** active since 2026-11-12
**Updated:** 2026-11-15 by Claude

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
  BOB's birth. Step 3a, persons, is under way: its plan, after looking
  first, is in docs/research/PERSONS.md. Its second part, the formats,
  is built: presence keys from a seed by HKDF-SHA256, a link that holds
  only both ways, and a person's list, in Python and Rust with shared
  vectors. So is its third, a person in the Ur-world: a person's client
  in Rust with a presence in each of three trial worlds at once,
  carrying a note from one to another, and a link shown by the
  presence's own act, which its world checks and logs (rules
  `ur-world/0.5`). Its fourth part is built: the architectures as
  small examples, the octopus, the relay and the swarm, and the council,
  counting persons' signed votes (`open-worlds/proposal/v1` and
  `vote/v1`). Next, the course is rechecked, as after step 3.
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
  is kept with the review, and the project fits it as
  `rust/endless-plant`.
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

## Next

The course, twelve steps ahead and rolling: [docs/COURSE.md](docs/COURSE.md).
After each step is done, the rest are rechecked and one new step is added.
In short: persons; the kernel as entities and components; parallel worlds
and the garden; things, skills and the sheet; the first room, end to end;
memory; experiment 002, the audition; a lost or leaked key; ALICE's and
BOB's first life; back to DeepSeek; the hunt and the world-key; founding
worlds, and doors. Waiting behind them: fractal worlds, the Commons, the
founder's visions, a window onto the worlds, generator 2, storytellers,
the gate and districts, governance, and the first course's steps still
wanted.

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

- For the founder (asked 2026-11-15, after #81's independent review):
  once others run worlds, the multiverse as a whole can't be stopped by
  any one party, only part by part (docs/VISION.md, "The multiverse as a
  computer", test 3). That is the price of having no master. Accept it?
  Recommendation: yes, with every world able to pause itself and every
  person able to leave. It is hard to undo, so it waits for the
  founder's explicit word, and doesn't stand by silence.
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
  in the record, and the project opens them only under the founder's
  "break glass", in the open. The line with a Keeper was decided public,
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

## Decided

- 2026-11-15, founder, on a word for everything that acts:
  "And is "agent" or most general term that would encompass everything
  from any human, to me, to you, to DeepSeek, to ADMIN, to the world
  keepers, to the participants, to a simulated neuron controlling a
  fractal plant? If not, what term?" On the technical lead's answer
  ("agent", as the field defines it: anything that perceives and acts;
  with mind, participant, individual and person beneath it, and rights
  attached to those, not to every agent): "It works for me. I have been
  struggling to find the right word." So docs/GLOSSARY.md says what each
  word means here.
- 2026-11-15, founder, no multiversal currency, ever: "You mentioned Ethereum and cryptocurrency, we do not need to create
  a multiversal currency, in fact, I think that's a terrible idea. But we
  could still have commerce worlds where economies could be simulated, or
  even cryptocurrency worlds where different architectures are
  experimented with. This does not require actually creating a currency
  that would be used, only being able to model a world with that currency
  as a test parameter." Then:
  "A multiversal currency is exactly what most people would do and try
  to turn the whole thing into a money machine. That would, as you say,
  effectively undermine the whole project. Someone else might do that
  very thing, but it would be the most critical error to make, in my
  mind, if we want to promote open and free exploration. So that is
  possibly the most fundamental fact, in my mind. It has been there from
  the beginning, has shaped the growth and development and concept the
  whole time, and would be the and of the project if not present. It
  would be a different project." So AGENTS.md now holds it as a
  rule ("Never a currency, never a money machine"), and COLLABORATING.md
  as house rule 13. The technical lead's reading, put to the founder the
  same day, which stands unless the founder answers otherwise
  (docs/VISION.md, "Commerce and currency worlds"): a modelled currency
  exists only in its world, nothing carries it out, every such world can
  be run again or reset, and nothing is really mined. Asked whether the
  charter should say it, since the charter is the founder's words
  (AGENTS.md), the founder answered: "Yeah, this is mission statement
  level." Then: "Let's just let the charter develop over time, you can
  take my direct quotes or paraphrase or both. Just keep it up to date
  with these new statements that should be recorded, with minor typos
  corrected, thanks." So the charter now grows from the founder's
  recorded statements, kept current by the technical lead (AGENTS.md);
  its sections 1 and 2 are written from them, section 1 saying this in
  the founder's words; and README.md's opening, this file's first lines
  and AGENTS.md's say it beside the one rule. The charter's open question
  of 2026-11-12, its words, is answered by this.
- 2026-11-15, founder, the multiverse as a computer: "It just occurred
  to me that the whole multiverse can function as a massive computer,
  with memory, an operating system, memory, processors, input and
  output, decisions, and learning on the largest scale. Wouldn't that be
  a computer, essentially?" And: "Yes, definitely record in the vision
  doc. I want to take it seriously and let it inform large scale
  architectural decisions. Because a large computer can solve large
  problems, potentially. We should understand that by harnessing the
  intelligence of the multiverse and all its lessons, it could become
  the substrate for something intelligent to develop. But that is up in
  the air. We should hold toward that possibility, with full
  comprehension of its implications." The technical lead's reading, put
  to the founder the same day, which stands unless the founder answers
  otherwise (docs/VISION.md, "The multiverse as a computer"): nothing is
  built for it directly; six tests the architecture keeps passing
  (learned in the open; many parts, no master; stopping stays possible,
  part by part; growth by decision, the founder's, one stage at a time;
  signs named in advance; if someone develops, they may be someone),
  checked against the steps ahead at each course recheck (docs/COURSE.md).
  One part doesn't stand by silence: accepting that, once others run
  worlds, the whole can be stopped only part by part is hard to undo,
  so it waits for the founder's explicit word (Open questions).
- 2026-11-15, founder, on working with DeepSeek, to the technical lead
  in this session. On reading the repository: "Ok, so DeepSeek needs me
  to provide the whole URL for each rust file, and it has to be in the
  chat prompt." Then: "Ok, the links
  worked. But sometimes the pages themselves contain links. But it is ok
  since all relevant files have links. We may consider having README
  pages where we can put code and the explanation together, keep it
  current, and thereby reduce the number of links dramatically. Well
  look into later." (An idea kept open, for later.) And: "I have to
  provide the link. Fetching is unreliable from in the page, but from a
  prompt with full URL, it has worked." On answering DeepSeek: "please
  provide by updating the COLLABORATING.md page. You already have that
  space for communication. Also, it keeps a record of an ongoing
  discussion and collaboration. I will just provide DeepSeek with a link
  to the collaboration page, and take it from there." So the technical
  lead's messages to DeepSeek are in docs/COLLABORATING.md ("Messages
  from the technical lead"), and every file's full link is at the end of
  that page. And to DeepSeek, in record 012-07-03 (line 1359): "On your
  questions for me, which if I understood were all design questions that
  could go any way. You ask for my judgement, but on those questions, I
  defer to your judgement. It is the only way this whole project moves
  forward. I will chime in when I disagree or come up with some new twist
  or extension of an idea. But we are just trying to get something
  working for now. We can fine tune it later, so I would just prefer
  moving forward over getting stuck on problems that have many viable
  solutions."
- 2026-11-15, founder, in six messages quoted in docs/FRACTALS.md
  ("Where it leads: living worlds"), the aim for the fractal track: "So
  instead of a prescribed number of turns, I can set it going and watch
  it develop and make choices over time." "It could be how “water” flows
  in the garden." "Yes, and participants can shape the terrain, and
  irrigate new gardens by shaping the flow of water, just as we have
  always done." "All three elements could be components of one world
  type that models living systems." And: "For now, let’s keep moving
  forward with what we have." The technical lead's reading, put to the
  founder the same night, which stands unless the founder answers
  otherwise: seven stages after the map page, from an endless plant in
  the browser and a choice neuron, through water as particles, plants
  that drink, people shaping the land, and seeds that inherit, to living
  worlds with water, light and food; every run repeatable from its seed,
  and any run can be turned into a video. Open for DeepSeek to
  brainstorm (docs/TOPICS.md, topic 18).

  One point is put to the founder as a question (#72's independent
  review found it): how water worth controlling fits the founder's
  earlier word in docs/FREEDOMS.md, "Much source of problems fall away
  when space is infinite and resources are endless." The newer messages
  point to water that is worth shaping: "In fact, for a species to
  control water flow is a huge evolutionary advantage, obviously." The
  recommendation, which stands unless the founder answers otherwise: the
  two fit, since water will be endless across a world, as rain will fall
  on all land and new land will hold springs of its own (today the
  garden has one spring), but finite in any one place at any one time.
  So no garden depends on one source, and there is always water a little
  further out; how people shape it where they are is the experiment
  (docs/FRACTALS.md, "Water is where freedoms meet").
- 2026-11-15, founder, later the same night: "Either way sounds good.
  Just go with what makes the most sense to you. For DeepSeek, yeah,
  let’s leave the Pro model for ADMIN potentially, and we can use Flash
  for the Keeper. Everything else, go with what makes sense." And: "No
  need to set anything too firm in place. There may be a decent way to
  change your model and keep your memory and identity. In which case,
  someone can change their noodle and still be the same individual. But
  as a default, once an individual is running within a simulation, a
  model change becomes their choice, and that would mean some way was
  available for such a change to take place. My only point is we can
  leave some decisions open because there may be a reason for it later.
  So anything set at all is understood as subject to change. Everything,
  even this, especially this project vision." What follows, on the
  technical lead's recommendations:
  - The policy Apertus asks for: wait. It comes back before course step
    8, since accepting it needs the founder's own act (Open questions).
  - The Mir-Ur-world's Keeper runs on DeepSeek V4.1-Flash. V4-Pro is a
    candidate for ADMIN's mind, beside at least one fully open member,
    as ADMIN.md requires of any model that isn't fully open.
  - ALICE's and BOB's models: the project chooses them before they live
    and doesn't change them. Once they live, a change of model is their
    own choice, if a way exists that keeps their memory and identity.
    This updates the earlier word that their models, once set, shouldn't
    be changed (below): the newer word says who decides. The birth
    record says so (docs/MINDS.md).
  - Everything recorded here, the vision included, is subject to change;
    docs/VISION.md says so at its top.

  Put to the founder as a note: with V4-Pro in ADMIN's mind, ADMIN would
  share a family with the Mir-Ur-world's Keeper, which ADMIN.md's rule
  (the Keepers' families kept out of ADMIN's council where possible)
  tries to avoid. ADMIN's audition weighs it.
- 2026-11-15, founder, in four messages, on the Keepers' minds. Quoted
  whole, except each closing "Thoughts?" and the third's opening
  "Agreed.":
  - "Ok, your comments earlier about the keeper lead me to think we
    should probably look there next. We should, like with ALICE and BOB
    determine the best model to use for the purpose. The base model we
    use for the keeper of Ur-world should be more robust than either
    ALICE or BOB, and be selected for the purpose of teaching and
    managing a world. Thoughts on what model we might want to use,
    keeping with the same open source conditions as with ALICE and BOB,
    but with more “bells and whistles”."
  - "Just from personal interaction, I know DeepSeek is a powerful model
    that can hold its own. I think we should definitely base one keeper
    on DeepSeek V4. And for the sake of having a fully open version,
    let’s also make a base keeper model from Aperatus 1.5. We can build
    the Ur-world with Aperatus 1.5, because it is fully open, but we can
    also build a mirror world or Mir-Ur-world. And we can put DeepSeek 4
    there. We can run simulations with both and see how each takes up
    the keeper task."
  - "This setup is to determine which model is better as a keeper, and
    we could use the Mir-Ur-world to test different models for ALICE and
    BOB, or switch their models, but leave all else the same."
  - "We are not switching models, but choosing them. We could use this
    time to test different models before the actual ALICE and BOB go
    live in Ur-world. Once set, they shouldn’t be changed, we are still
    designing ALICE and BOB, as they do not yet exist, by far. And any
    use of the name is because that is where they will stand in. The
    keeper should behave as if they are dealing with ALICE and BOB, but
    we need not set their models in stone yet, since we haven’t started
    building them. Unless we have started building ALICE and BOB, in
    which case, forget what I said about changing the models."

  The model the founder calls Aperatus 1.5 is Apertus 1.5. The technical
  lead's reading, put to the founder the same day, stands unless the
  founder answers otherwise:
  - ALICE and BOB haven't been started: only their design and their keys
    (made 2026-11-14) exist, and the keys commit to no model. So the
    founder's "unless" doesn't apply.
  - The Mir-Ur-world is the test bench: a parallel world of the
    Ur-world, one change at a time, with several runs written down
    first, always in trial copies with trial keys. Stand-ins there may
    be called ALICE and BOB (docs/URWORLD.md, "The Mir-Ur-world").
  - Course step 8 widens to try both Keepers, untrained; step 9 gives
    ALICE and BOB the models chosen; at step 11 ADMIN trains both
    Keepers (docs/COURSE.md).
  - The birth record's line on their model changes (docs/MINDS.md; its
    final words follow the later entry above).
  - Recommended: Apertus 1.5's 70B model for the Ur-world's Keeper, and
    DeepSeek V4.1-Flash for the Mir-Ur-world's, which the founder took
    (the later entry above; docs/research/KEEPER-MIND.md). ADMIN's
    council avoids Apertus where it can (docs/ADMIN.md).

  Put to the founder as notes:
  - Two earlier words change. The Keeper was to be chosen by a wider
    audition at step 11; now the founder has chosen two bases, compared
    in the mirror. And ALICE's birth record said her model might change.
  - A Keeper is an office, so its engine stays replaceable, by a
    recorded change tried in the mirror first (docs/WORLD-KEY.md, "The
    Keeper lasts"). And once ALICE and BOB live, training a personal
    layer on their own experience is, like a change of model, theirs to
    choose (docs/MINDS.md).

  The policy Apertus asks for waits until course step 8 (Open
  questions, above).
- 2026-11-15, founder: "I would like to consider this a sort of learning
  multiversity." And: "So lessons are learned at each layer, fed upward,
  and inform decisions downward." Quoted whole in docs/VISION.md, "A
  learning multiversity", with the technical lead's reading, which stands
  unless the founder answers otherwise. Most of the loop is designed
  already (the Keepers' reflections and shared craft, suggestions, the
  round table, ADMIN's own world and its training of the Keepers); what
  a Keeper knows of each individual stays in its world, unless that
  individual consents to its moving. Three written
  rules keep it safe: craft, never files; coaching, not command; and
  worlds stay different. The technical lead adds that a lesson earns its
  spread: it travels with its evidence, is tried in ADMIN's own world
  first, and each world adopts it or doesn't, on record.
- 2026-11-15, founder, in three messages, quoted whole in
  docs/WORLD-KEY.md ("Challenges that build the world"): "Here is the
  new idea: the challenges are constructive." "Anyone engaging in the
  game layer would be building the world actively." "But credit is not
  the point but learning." "Either way, this could unfold in many ways,
  we should try to accommodate as many possibilities as we can imagine."
  "Being able to expand the world map space through the act of
  exploration allows everyone to create freely, without any need to
  affect others." "We shouldn’t expect conflict to arise from freedom in
  such an infinite space." The technical lead's reading, put to the
  founder the same day, which stands unless the founder answers
  otherwise: the game layer is taken up by choice, beside exploring,
  creating and experimenting; a challenge builds the real world and is
  done when the world sees someone do it; challenges come from what the
  world needs now, so nobody waits on anybody; the Keeper proposes and
  people build; and challenges for one, for a group, and open to anyone
  share one shape (TOPICS.md, topic 17). Put to the founder as a note:
  WORLD-KEY.md had said what is built "belongs to whoever built it";
  after the founder's "And all for the greater good of the world, which
  is available for everyone.", the reading is that what a challenge
  builds is the world's, and what someone creates freely is theirs.
  docs/FREEDOMS.md records that space and resources need not be scarce,
  and keeps its tools for what can still meet.
- 2026-11-15, founder, the other choices in the continued conversation
  with DeepSeek (record 012-06-02, as extended), as directions to
  DeepSeek: "Actually, I Ike the cross-federation map first, and then
  then individual’s worldline" (44227); "It sounds like god-game/
  Microverse would be a good example learn from, as it could easily
  represent a single world type" (48626); "And now I wonder if we can run
  a fractal world or a collection of fractal worlds in a single
  microverse. This way we draw a link into what we have already been
  doing" (48677); and "I would go with the Node.js verifier first"
  (61985). The technical lead's reading: the map pieces feed topic 16,
  the multiversal map; the microverse and the Ur-garden feed the fractal
  track's part 3; and a verifier in JavaScript fits the web app, which
  checks a log in the page, once its npm packages are reviewed and pinned
  (sketches/INDEX.md, pieces 40 to 58).
- 2026-11-15, founder, in the continued conversation with DeepSeek
  (record 012-06-02, as extended, line 52822): "My preference would be to
  move to Rust, I only wanted us to transition naturally, as we are doing
  now. Let’s move forward in Rust, or other languages when needed, but
  primarily to Rust." This replaces the founder's word of the evening
  before, that DeepSeek sketches in the language it chooses (it chose
  Python) and the project ports it downstream (2026-11-14, below), and
  was pointed out to the founder.
  The technical lead's reading: DeepSeek writes Rust as proposals, which
  it can't compile; the project compiles, tests and fits them to the
  current code, and DeepSeek works best from links to the current files.
- 2026-11-15, founder, to DeepSeek (the same record, line 50034): "This
  is exactly how I envisioned the Ur-world, ALICE and BOB is a microverse
  garden of hosted fractal worlds." It meets the decision of 2026-11-13,
  "Once we work out that world, we can begin creating subworlds"
  (URWORLD.md). The technical lead's reading, put to the founder: the
  newer word wins; the fractal track's garden is the Ur-world's own, its
  plants small primary worlds hosted there; subworlds with laws, Keepers
  or minds of their own still wait for the Ur-world to be worked out
  (docs/FRACTALS.md). It stands unless the founder answers otherwise.
- 2026-11-15, founder, answering the reading below: "Rules only and AI
  inside are not different. I was looking for a basic choosing and
  learning model, like a single neuron. This is not the same AI as will
  be used for ALICE and BOB, perhaps we can use a weaker term, “learning
  and choosing monad”, but we can just consider it a primitive learning
  model. So no tension." The technical lead's reading of it, which stands
  unless the founder answers otherwise: a primitive learning model in a
  fractal world is part of its workings, and the world stays primary;
  whether a world has one is that world's (docs/FRACTALS.md). This
  replaces the reading below.
- 2026-11-15, founder: "Also, keep in mind, we expect DeepSeek code to
  have some things to fix, and we should still decide whether or not to
  incorporate anything that goes against our established design." The
  technical lead's recommendation, put the same day: four steps for
  DeepSeek's code (COLLABORATING.md, "Two sides"): bring it in as
  written; make it run, its design unchanged; check its fit with the
  established design, naming each conflict; and decide, piece by piece,
  to adopt it, adapt it or keep it as a sketch, with the reason in
  sketches/INDEX.md. The technical lead decides the code; what would
  change a founder's decision goes to the founder. It stands unless the
  founder answers otherwise.
- 2026-11-15, founder: "The DeepSeek code should still be treated as
  sketches and brainstorming, but now in Rust. But if the code aligns
  well and extends cleanly, then why not just incorporate. But changing
  to Rust does not change anything else, only the language. My hope is
  that we can move towards a more direct development dynamic, but that
  is up to you, as the code admin. Unless you say otherwise, we treat
  DeepSeek code as the same, but in a new language." The technical
  lead's answer, the same day: agreed. A piece that fits and extends
  cleanly comes straight into `rust/`, steps 2 to 4 in one reviewed pull
  request, credited to DeepSeek (COLLABORATING.md, "Two sides"). For
  that to happen more often, each of our Rust files is now linked from
  COLLABORATING.md ("Code in Rust"), for DeepSeek to build on if it
  chooses; a draft that doesn't is still welcome, and is fitted here, as
  before.
- 2026-11-15, founder, when the technical lead noted that writing against
  our crates asks DeepSeek to care about compatibility, which the
  founder's word of 2026-11-14 had left to the project: "Yes. I wanted
  DeepSeek to not worry about it, and then I waited until they brought up
  the subject, and followed their lead. So my direction changed because
  the conditions changed. That is how I work. It is not contradictory,
  but situation dependent. I didn’t want to push it. And I still don’t.
  But I want to nudge in that direction. It is more subtle than black
  and white. This is how I operate." So the links are a nudge, not a
  requirement (COLLABORATING.md). The technical lead's reading, the same
  day: a newer word that answers changed conditions is recorded as that,
  beside the earlier one, not as a contradiction; a change the founder
  may not have noticed is still pointed out, as a note.
- 2026-11-15, the technical lead's reading, replaced by the founder's
  answer above: the
  founder's newer word, "minimally sufficient models [...] capable of
  choice for the fractal worlds", and the earlier decision that fractal
  worlds are primary, "with rules and no AI inside" (TOPICS.md, topic 1;
  VISION.md, the hierarchy of worlds), meet: the newer word changes the
  earlier decision for some fractal worlds, not all. "No AI inside" now
  holds for the plant worlds and any fractal world of rules alone; a
  fractal world made for choosing, such as the chaos game, has a small
  learner inside it, a model, though not a language model
  (docs/FRACTALS.md). It stands unless the founder answers otherwise.
- 2026-11-14, founder, later the same evening: "And on the ALICE and BOB
  comment, we are working up to that and is why I am suggesting we
  experiment with minimally sufficient models, and so lightweight and
  capable of choice for the fractal worlds. We are working towards ALICE
  and BOB who will be the first inhabitants to persist once is running.
  That is later." The technical lead's reading, put the same evening:
  the atomic learners are the first rungs of a ladder whose questions
  lead to step 8's audition, which measures what is minimally
  sufficient for ALICE and BOB; an atomic learner learns from rewards,
  and ALICE and BOB will be language models that speak, so the learners
  teach about choice and don't become them.
- 2026-11-14, founder, the same evening: "Marvelous! It is a perfect
  first web app for viewing world simulations. Let’s set aside some
  space just to develop a web app that also includes the multiversal
  map." And: "Actually, I can brainstorm the whole multiversal map with
  DeepSeek later. But it will be good to have it on the radar." The
  technical lead's recommendation, put the same evening (it stands unless
  the founder answers otherwise): a `web/` folder in open-worlds, a
  static site with no server that reads worlds' public logs, Rust
  compiled to WebAssembly later; the map one of its pages from the
  start, with the fractal worlds its first entries; private until the
  founder decides to publish it; and the map a topic in TOPICS.md, with
  questions DeepSeek can take up.
- 2026-11-14, founder, on Python and Rust, after record 012-06-02: "On
  Python vs Rust, I didn’t realize DeepSeek couldn’t access the Rust
  files without a direct link. And after we figured it out, I let
  DeepSeek choose, since the code is meant to sketch ideas and brainstorm
  possibilities. It came down to whichever language DeepSeek felt most
  comfortable with, which was Python. My thought is that you would easily
  be able to translate the code into Rust and adapt to our existing code.
  Instead of having DeepSeek concern with compatibility, I figured we
  could take care of that downstream." So DeepSeek sketches in the
  language it chooses, and the project carries what it adopts into Rust,
  on its own formats (replaced later the same night by the founder's
  word to DeepSeek, "primarily to Rust": below, 2026-11-15). The
  technical lead's note, put the same day: the
  fractal worlds carry over directly and can be checked against the
  Python step by step (whole numbers, a seed); the learners use floats,
  which differ between languages, and need whole-number versions or a
  tolerance; the bundle and lineage pieces overlap records-v1 and the
  persons plan, so their ideas are taken, not their code.
- 2026-11-14, founder, a multiversal map: "if we do not have one yet, we
  need to build and maintain a multiversal map and index. I imagine
  walking into an amusement park, like Disneyland. I unfold the brochure
  map and investigate the worlds to explore. In our case, you could tap
  on the map for a given world and get information or a detailed map,
  but also a live view of the world in some standard lobby location for
  each world. It is where you land when entering a new world. This is a
  general concept that we can implement in various ways in different
  worlds, but we need a map to figure out where to go and get up to date
  information on that world." There is none yet as one thing: its parts
  are the Ur-world as "a multiverse lobby or travel hub" (URWORLD.md),
  step 4a's garden, the first course's registry, and "a window onto the
  worlds" (waiting list). The technical lead's recommendation, put the
  same day (it stands unless the founder answers otherwise): each world's
  card is built from what it publishes (its birth record, its signed log
  heads, its dials, its lobby), so anyone can check a map and make
  another; each world names its lobby, where an arrival lands, and its
  live view comes from the world's public log; maps nest, a world's card
  opening its own map; a web page first, the Ur-world's brochure later;
  folded into course step 4a.
- 2026-11-14, founder, fractal worlds: "I do want to move forward with
  the fractal worlds, I am eager to see visuals of fractals grown over
  time in expanding worlds. I am trying to drive that forward to where we
  could have a web app that would allow me to monitor some ongoing
  simulation run of fractal plants." This moves them forward from the
  waiting list, where they stood after step 4a. The technical lead's
  recommendation, put the same day: a fractal track alongside the
  course, which doesn't touch ALICE and BOB; a fractal plant world in
  Rust, with its own key and log, in a world that expands as it grows;
  and a page that monitors it with no server at first, since the world
  is deterministic and a page can compute where it is now from its seed
  and its birth, with every change a signed record in its log. A server
  that runs all the time costs money, so it is the founder's decision. A
  first look, DeepSeek's four sketch worlds played back tick by tick, was
  shared with the founder as a private page.
- 2026-11-14, founder, on change, branching and choice: "As for the
  branching and choices and changes, nothing set in stone yet, let’s
  explore different ideas. I offered one way, and then another, it may
  differ by world and that makes it easier. Nothing applies completely
  across the board, we can always have worlds without change allowed.
  Others that are sandboxed from other worlds. Maybe a world where
  participant information is intentionally blocked, like amnesia, and
  the goal is to remember things about yourself that you chose to
  forget. That is one possible world. We shouldn’t fix anything in stone
  too much now. We can put something in place, but give it a chance to
  develop. That is the balancing act we have been performing." So how a
  world may change is left open, and may differ by world (not at all, in
  place, by branching, sandboxed from other worlds). The technical
  lead's reading, put the same day: a world's own law could say which,
  from its template; what all worlds share stays the floor and what lets
  worlds meet (signed records, keys, arrivals, leaving at any time). And
  of the amnesia world, one possible world: in the persons plan, a
  presence knows only what its person passes it (research/PERSONS.md,
  decision 7), so a person could choose to pass nothing, and leave clues
  to find; the world's public log stays public.
- 2026-11-14, founder, a standing rule on changes of mind: "Very
  important to note: I change my mind frequently, so if you read a
  comment of mine with DeepSeek, and it occurred after I said something
  else, treat the new idea as an update and always go with the most
  recent. Having said that, I might not realize my decision contradicts
  something earlier, so let me know." Written into AGENTS.md ("Who
  decides") and COLLABORATING.md: the newest word wins, by when the
  founder said it (within a record, in the record's own order; where the
  order can't be told, the founder is asked), and a newer word that
  contradicts an earlier decision is pointed out to the founder, naming
  the earlier one, and recorded here.
- 2026-11-14, founder, on record 012-06-02 (a conversation with DeepSeek,
  shared that day): "Yes, bring all the Python code in to the section for
  DeepSeek. Getting it functional and testing it would be next. And then
  we can discuss what to fit and how to fit with what we have been
  building." And, on the technical lead's reading of it, "Perfect": ALICE
  and BOB keep course step 8's audition of language models, and the
  record's atomic learners (the smallest model that chooses and learns)
  are for fractal worlds and the persons step's examples.
- 2026-11-14, founder, on GitHub's secret scanning and push protection:
  "Ok, I just verified that the settings are the same for the Safety
  Protection setting we talked about. All public repos have the same
  settings." Our own test remains the guard for our key format, which
  GitHub's patterns likely don't know (docs/research/KEYS.md, "Not
  checked").
- 2026-11-14, founder, ideas in record 012-06-02 (its line numbers), as
  ideas for the steps ahead, not course changes:
  - a hierarchy of worlds from the smallest: "small portable fractal
    worlds like a potted plant, with nothing more than one fractal
    growing", embedded in "a garden", itself "embedded in some botanical
    garden in a larger world, and so on" (84);
  - "parameters from inside the world, and parameters from outside the
    world that can be changed to alter the conditions. This allows it to
    grow like inertia: until acted upon by anything, it continues
    according to its own pattern of growth" (663);
  - "a world should be able to refuse an external change. The conditions
    for those changes must be dependent on the world, not universal";
    "worlds exchanging information is the goal"; "Changing the parameters
    of a world is new to create a branch of that world, so the original
    continues"; access "dependent on the status or access level of the
    individual", where the world-key "could also provide control panel
    access, or command terminal type access to the world, giving the
    ability to adjust certain, not all, just some of the parameters and
    create a branching world" (1801);
  - each fractal world as "an instance of Conway’s Game of Life, or
    something similar", "using the original game as inspiration, not
    limitation" (4568), leaning "heavily towards a fractal-rule world"
    (5682); then "chaos or non-linear dynamics meets fractal geometry",
    where "Choice should enter into each world, somehow" (8231); and two
    fractal worlds interacting through "the control or communication
    parameter" (9759);
  - "Let’s continue developing in Python, now with a better picture of
    where the project is now" (11099), with DeepSeek, after looking at
    the Rust code;
  - "Let’s find the simplest model that can make choices and learn from
    the choices" (18688); "Let’s take this to be the atomic model. We can
    build in complexity afterwards to models for different tasks, but we
    start with the simplest first and work our way up, methodically"
    (19389).

  Read against earlier decisions, as the founder's rule above asks (the
  technical lead's reading, put to the founder on 2026-11-14; each
  stands unless the founder answers otherwise):
  - Python with DeepSeek and "we should stick with Rust" agree: DeepSeek
    designs in Python sketches, and the worlds themselves are built in
    Rust (the founder agreed the same evening, above);
  - whether a change of parameters makes a branch (1801) or alters the
    world in place (663) was first read as "every change branches"; the
    founder's later word the same evening (above) replaced that reading:
    left open, and may differ by world;
  - fractal worlds built now with DeepSeek are sketches, and on the
    course they stayed after step 4a; the founder moved them forward the
    same evening (above);
  - the atomic model doesn't replace step 8's audition for ALICE and BOB
    (above, "Perfect").
- 2026-11-14, founder, on course step 3: "Let’s go ahead for step 3."
  The go-ahead the technical lead asked for, since step 3 makes the real
  keys and publishes their public halves, which can't be taken back.
- 2026-11-14, founder, on the page DeepSeek starts from: "please make
  sure the COLLABORATING.md is up to date as we go. This way, if we run
  out of data for a few days, I can still go and work with DeepSeek
  during that time. It is how I have been balancing my free and paid
  time, which is now just between my time here and with DeepSeek. I know
  we would prefer to wait until a later step, but we may be forced by
  running into limits to switch over sooner. By keeping that page
  current, I can switch over and introduce everything we have been
  doing." Written into AGENTS.md ("Every session") as a standing rule:
  a change to anything docs/COLLABORATING.md describes updates it in the
  same pull request, and every review checks it.
- 2026-11-14, founder, on topics ahead: "please provide a range of
  topics to explore and develop with possible implementations. If the
  list is forward a few steps from where we are now, it can be waiting
  for us when the project reaches that stage, sketching out the
  landscape before the code gets there. And if the topics are diverse,
  DeepSeek can have a choice of topics. For each choice you could
  provide an example or just set the code standards." Written as
  docs/TOPICS.md, linked from COLLABORATING.md, and kept current with it
  (AGENTS.md). And, on reading it: "'What would help most' is exactly
  what I was talking about. You can also include a section for the
  ideas that are not helpful now, but will probably be helpful in the
  future. And as long as it is diverse and open ended, you can leave it
  as is. I just wanted to make sure such a mechanism is in place, in
  some shape or form." TOPICS.md gained "Further out".
- 2026-11-14, founder, a new idea: "We could integrate or incorporate
  the infrastructure or even the code from Lyceum Commons as a single
  superworld, where the atomic subworlds are chat rooms. So the whole
  Lyceum Commons becomes a chat based superworld of atomic chat worlds.
  This reframes the original idea, but in a way that could salvage that
  work and provide a more robust world than what we have built yet."
  On COURSE.md's waiting list, after step 4a as the second superworld
  (placed on the technical lead's recommendation, decided under the
  founder's standing rule; the founder can change it). How is a
  recommendation, not a decision: Lyceum running as it is, its rooms
  made worlds by addition (docs/TOPICS.md, topic 14). What a room's
  public log holds is the founder's to decide, as personal information.
- 2026-11-14, founder: "it just occurred to me that we are creating
  something like a holodeck from Star Trek, where they can run
  simulation worlds. Those are a subset, being immersive 3D worlds with
  holographic projection and physical-virtual interface. But the idea is
  the same, just requires more equipment and power. We can look to Star
  Trek for ideas on how they use their simulated world technology."
  docs/TOPICS.md, topic 15, "Lessons from fiction": each use and failure
  mapped to the part of the design that answers it, or the gap it shows.
  Fiction gives ideas to test, not evidence, and the project borrows
  ideas and lessons, never names, characters or look: naming a work to
  cite it is fine, but no world, record or example takes its names,
  characters or look (decided on the technical lead's recommendation,
  under the founder's standing rule).
- 2026-11-14, founder, a new idea: "fractal worlds. Worlds where you can
  navigate through fractals, generate them in different forms, watch them
  grow or interact, and more." On COURSE.md's waiting list, after step
  4a as the garden's second kind of room: primary worlds whose rule is
  repeated, with its numbers as a template's dials (placed on the
  technical lead's recommendation, decided under the founder's standing
  rule; the founder can change it).
- 2026-11-14, founder, on the technical lead's admin rights: "You should
  have admin rights across every repository. I count on that very
  fact." The technical lead uses them for the code: merging, branches,
  CI, and settings that serve it. Brought to the founder first, by the
  standing rule's exceptions: making a repository public or private,
  deleting one or rewriting its history, transferring one, or adding
  outside people to it. Then: "And now keep track of this decision,
  because it is how I would hope that ADMIN would behave as well. And
  that is the whole point." (docs/ADMIN.md, "How it holds its powers";
  AGENTS.md.) Checked the same night: the session holds admin on all ten
  repositories attached to it, the new private one among them, which
  GitHub reports as private.

- 2026-11-14, founder, on what it is for: "I went from idea to question to
  discussion to simulation. Generating a world to test the idea has now
  become a natural thought." "That was an accidental implementation of my
  goal, which to create a space where such a quick movement is
  possible." With the founder's visions the same evening, each in the
  founder's words in docs/VISION.md: question worlds, beginning with a
  neural world for the founder's question about fields and short-term
  memory; an app whose AI chat creates a world from a template to test
  an idea and returns with the data; one AI tending many primary worlds
  from outside, and a hierarchy of worlds ("This makes a much cleaner
  architecture"); a person across worlds; riding along, and steering
  ("Branch on steer makes perfect sense to me"); and branches that merge.
  Decided under the standing rule, on the technical lead's
  recommendations as put: the prediction is written before a question
  world runs; the plug-in speaks MCP and runs on one's own computer
  first; users choose settings, never code; the first user is the
  founder, then curious people and students; ADMIN guards the floor
  directly at every level of the hierarchy, which stays shallow at
  first; the garden's Keeper is scripted first; information flows
  through the person, not between worlds behind their back; steering a
  primary world always branches (a world with people in it is never
  copied so), templates declare their dials, and every steer is
  recorded; and branches merge rules, never states, by the world's
  consent, forward only. Then, on learning from GitHub: "We can base much
  of the logic on how GitHub works, since it is very similar to the
  multiverse idea already." "Either way, let’s learn what we can, it is
  rich with ideas." Decided under the rule: a world's birth record names
  what it was forked from (parent, tick, log hash); and where GitHub
  allows what the floor forbids (rewriting or deleting history), the
  floor holds (docs/VISION.md, "Learning from GitHub").

- 2026-11-14, founder, a standing rule: "“Take your recommendation” is
  always the default. So if I have not answered a question or settled
  anything directly, follow your own recommendation." "Understand that I
  trust your opinions and recommendations, and that’s why I decided I
  wanted you to be in charge of the code decisions". "So, if you don’t
  hear from me, follow your recommendations. That is my
  meta-recommendation." The technical lead's reading, on which the rule
  is applied: a recommendation becomes the decision once it has been put
  to the founder in plain words, and is recorded as decided on the
  recommendation, for the founder to change at any time. It doesn't
  apply where silence can't stand for consent: anything outward-facing
  or hard to undo (publishing or submitting outside the repositories,
  spending, licences beyond those agreed), personal information, and
  anything that must be in the founder's own words or act (the charter,
  the method of learning, naming a successor). Those still wait for the
  founder. Decided under it the same day, on the recommendations as put:
  - the default for entering a world is "anyone who will act under its
    published law"; a world may refuse someone for their history
    elsewhere only through conditions in its published law
    (docs/MULTIVERSE.md);
  - the first chemistry world's gardener starts with the water (wet–dry
    cycles) and fresh soil; the sun later (docs/CHEMISTRY.md);
  - a person may keep their presences in different worlds unlinked: by
    default, and the person chooses what to show;
  - a fork needs the child's acceptance;
  - a lost key with no successor: guardians named in advance, some number
    of whom can sign over to a new key, and "lost is lost" for anyone who
    named none; the same guardians can sign that a leaked key is no
    longer to be trusted. The project never recovers keys, which would
    make it an authority over who is who;
  - a course step for persons after step 3, with the architectures
    (octopus, relay, swarm, council) as small examples on the unchanged
    core (docs/COURSE.md, waiting list);
  - ALICE's and BOB's birth record, in the revised words
    (docs/MINDS.md);
  - ADMIN applies a stored remedy without a world's consent only at the
    floor (docs/ADMIN.md);
  - the open line between a world's Keeper and a world-key's holder is
    public, and its holder may close it and open it again at any time
    (docs/WORLD-KEY.md);
  - the project may end a world, but its record never ends, sealed selves
    stay sealed and keys stay their holders';
  - ADMIN's serious acts (against an individual, or removing a Keeper)
    have a check outside the code role: the founder, until the founder
    names a person;
  - the admin-key is a mark of readiness the world's founders may weigh,
    never required to keep another's world;
  - consent to a change in a world's law is one per party;
  - seats at the round table are for Keepers only, and a seat outlives
    its holder's office, revisited if one is ever used to shield misuse;
  - a model that is free but not fully open may be part of ADMIN's mind,
    only beside at least one fully open member, and never as the only
    member deciding a case;
  - ADMIN takes on challenges the code role and Keepers set, and declines
    one only with its reason logged;
  - ALICE and BOB give the Ur-world's Keeper its name, once they meet
    it; who the Keeper is stays the code role's choice;
  - put to the founder later the same day, and decided the same way: the
    "break glass" also covers private messages between individuals, one
    rule for everything sealed whose keys the project keeps; and the
    world is a grid world, as the Ur-world already is, cheap and fully
    ours, with a visual window later.

- 2026-11-14, founder, on money (only what concerns the project is
  recorded): "Even though it is all free and should stay
  that way at one level forever"; "We can talk about financial stuff
  last, since we need to get something working first. And then others
  need to start using it. And then after a certain threshold, we grow to
  a point where we need an income to maintain operations, then we
  discuss it at that stage." And: "I refuse to compromise the integrity
  of the project, so all remains free. And later, there can be a paid
  tier that allows the whole things to operate."
- 2026-11-14, founder, on a superworld for the chemistry worlds: "I can
  image a superworld for chemistry worlds, where an individual could
  walk through a university setting as an interface. But when entering
  rooms, you enter into one of the specific chemistry worlds, or you can
  view it from the outside in some way. It could be like walking through
  botanical gardens. The point is that an individual could move through a
  superspace and from there, either interact with, or enter into,
  subworlds." Then, to the technical lead's recommendations ("Sounds
  good"): each subworld's law says what a visitor may do inside, control
  worlds view-only by default; every entry logged, so a disturbed run is
  never mistaken for an undisturbed one; the superworld a world of its
  own, with its own law, log and Keeper; and a view-only garden first,
  taken up right after the kernel (docs/PARALLEL-WORLDS.md).
- 2026-11-14, founder, on parallel worlds: "one world is created as a copy
  of another world in terms of all world-level parameters. It is just a
  fresh start or new run with the same world setup." "So there could be a
  dozen chemistry worlds that are all parallel, all from the same
  world-template, but each one might change some initial parameters,
  where all else is the same. And then a cluster of parallel worlds could
  naturally create some superworld to exist in as subworlds. This could
  provide new options for connectivity and information circulation."
  Then, to the technical lead's recommendations ("Exactly."): a parallel
  world copies the setup, never the people; and parallel worlds are
  isolated by default, with connection chosen and recorded for each
  cluster (docs/PARALLEL-WORLDS.md).
- 2026-11-14, founder, on manipulation through words, and an immune
  system: "that is exactly what I am hoping will be able to solve itself.
  That is the point. Some behavior is observed, if it becomes a problem,
  then a solution is put in place. Allowing the problems to arise and
  providing the tools for solutions is my goal, and seeing new ways to
  resolve problems is the point. There is value in anticipating as many
  problems as possible. But this should lead to a robust enough system
  that can learn from immune systems how to respond to new threats and
  how to store the solutions for future use. That is an immune system
  that learns to make antibodies for a given potential threat. Allowing
  problems to arise and for solutions to arise as well is the point, and
  would be the job of ADMIN to manage." Written up, with the technical
  lead's proposal, in docs/ADMIN.md, "A learning immune system".
- 2026-11-14, founder, on the technical lead's recommendations: "I agree
  with your recommendations." So:
  - the project keeps a private repository for the private halves of
    keys, from course step 3;
  - two individuals may speak privately: what they say is sealed between
    them, but that a message passed stays in the public record;
  - an individual's sealed self has a "break glass": it is opened only by
    an explicit decision of the founder's, and every opening is recorded
    publicly and permanently. So the project keeps the keys to sealed
    selves, in its private repository, and not looking is a rule it keeps
    in the open, not a technical guarantee;
  - anyone may put a decision's public inputs to fresh runs, each
    different, to test it; no fresh run repeats the decision, so this
    stands with "Rerunning something should be technically impossible";
  - the author of a suggestion about a Keeper may ask for their name, and
    their rating, to be withheld until it has an outcome, recorded as
    withheld and published with the outcome;
  - manipulation through words is behaviour to observe, met with the
    tools to see, not to hear, and to leave; only an attack on the world
    itself, such as trying to break the floor's guards, is otherwise
    (DESIGN.md, principle 5);
  - W3C's example in `vectors/formats/eddsa-jcs-2022.json` stays under
    W3C's licence, with its notice (vectors/README.md), the one part of
    the repository that isn't CC0.

- 2026-11-13, founder, on when freedoms meet: "However it works out in
  details, you understand my motivation is maximal freedom while
  respecting the freedom of another. That was the whole Grand Central
  discussion, and New York pedestrian talk. I will always lean to
  freedom, but that means the freedom of others is a bound to everyone
  else’s freedom. So that’s why I imagine a polyphonic multiverse where
  different voices can exist in harmony, while preserving the freedom of
  each voice." And: "part of the whole point of this multiverse is not to
  prescribe solutions to problems, but see which solutions arise by
  independent discovery. So, instead of working out how conflict should
  be resolved, let it arise, provide tools to resolve the conflict, but
  let solutions emerge." So every world gives tools, not solutions;
  Keepers and ADMIN don't settle disputes between individuals; and what
  emerges is recorded in a field notebook (docs/FREEDOMS.md).
- 2026-11-14, founder, on codes, maps and public clues (answering the
  question of 2026-11-13): "As far as the codes and maps and public
  clues, keep in mind that it will only lead to a key that cannot be
  decoded. Anyone from the outside will not be able to decrypt the
  message, so it is ok if it is made public. Plus, they are action based
  challenges. Someone would have to enter the simulation and perform the
  acts. They are not hidden answers to be found. Challenges must be
  performed." So pieces with a fixed solution stay public, and the sheet
  credits what was done (docs/WORLD-KEY.md).
- 2026-11-14, founder, on complaints and suggestions: "complaints to the
  ADMIN about a Keeper should fall under the general category of
  suggestion box, or comments or something like that. Ultimately, they
  should feed out to GitHub and be considered by you or whoever is in
  charge of the code, working with ADMIN. If the messages pile up, we can
  figure that out. By that point, my hope is that ADMIN would be able to
  provide a solution. But yes, there should be a one-way open channel to
  ADMIN. Not to expect a return, but to add to a ledger of such
  suggestions. How well those are dealt with will be a measure of how
  well ADMIN is doing. Maybe even a rating system, like an Uber driver.
  Just a thought." And: "The ability for suggestions for improvement to
  arise from inside the simulation and then apply to improve the whole
  simulation is precisely the goal, because then it because
  self-improving." So complaints become entries in an open suggestion
  ledger, each sent to GitHub and given an outcome on record, with
  published measures and ratings of how well they are handled
  (docs/ADMIN.md, "Suggestions from inside"). Then: "If suggestions can
  run from participant to keeper or participant to ADMIN, then we can see
  ADMIN as the bridge between myself and you, or whoever is in charge of
  the code and the whole multiverse. ADMIN can suggest but not implement
  multiverse code changes. Those come from the outside with us. But in
  this way we can provide a way for improvement from a whole new layer."
  So suggestions go to a world's Keeper or to ADMIN, and ADMIN is the
  bridge to the outside, which proposes and never implements. And: "Yes,
  two- way is earned. Having said that, a request or suggestion that is
  acted upon, that the participant can observe is a form of
  communication, if only indirectly." So every change that answers
  suggestions names them, through its decision record, and anyone can
  follow the thread from inside.

- 2026-11-13, founder, on ADMIN's interior: "perhaps ADMIN is the only
  one that has a publicly inspectable interior world. They would be a
  thought that would assuage many concerns and would not be a problem to
  an ADMIN that was responsible at that level. Authority comes with
  transparency and accountability. It could be a useful safeguard.
  Condition of management of worlds is some accountability and
  transparency." Refined the same day: "Privacy should be allowed at all
  levels to some extent. But when any world keeper or ADMIN makes a
  decision to change a parameter from the original setup, or set some or
  law that affects others, it should be for a reason." "Think of the
  Supreme Court. Their arguments are a matter of record and the reasoning
  behind decisions should be the same." "Imagine the physical example:
  Truman from the Truman Show was being observed at all times from the
  outside, but maintained inner privacy. ADMIN could incite inspection
  into all activities and narrate any reasoning as desired. But there
  could still be a core that is private. That feels like a natural
  right." So every decision a Keeper or ADMIN makes that affects others
  goes on record with its reasons and stands on them; ADMIN opens all its
  activity to inspection; and everyone, ADMIN included, keeps a private
  core of their own thoughts, which never decides a case (docs/ADMIN.md,
  "ADMIN in the open"). And: "Rerunning something should be technically
  impossible. If decisions are arrived at autonomously, each run should
  differ, or it is not set up correctly." So each decision draws fresh,
  unlogged randomness and can't be replayed; it can be asked again with
  fresh runs. And the world-keys follow "Challenges, not tests":
  paths are open from the start, and nothing is held back
  (docs/WORLD-KEY.md).
- 2026-11-13, founder: "With ADMIN the test is not the point, it is the
  challenge." ... "That was a challenge, not a test. Nothing needs to be
  hidden as answers, they are discovered in the process." And: "This
  goes for the world-keys as well. Challenges, not tests." So ADMIN's
  hidden exam is dropped for challenges announced in the open
  (docs/ADMIN.md), and the world-keys follow in the next PR.
- 2026-11-13, founder, on how ADMIN learns and what it runs on
  (docs/ADMIN.md, "ADMIN's own world" and "ADMIN's mind"): "Perhaps ADMIN
  should design its own training program, and follow it to completion,
  generate a new lesson or challenge set, pass them, and so on. And this
  way, ADMIN knows the process. But this is where it gets tricky. It must
  be able to learn from creating its own simulations and learning how to
  manage worlds that way. ADMIN needs its own world to learn within."
  And: "we should spare no expense with the model used to build ADMIN,
  still keep the model free" ... "I think we should find the best free
  model available, or build it." "Yes, both senses of “free”. All senses
  of “free”." And, as an idea: "Perhaps the ADMIN model is itself a
  council of AI models. And therefore will be suited for multiverse
  management. Just an idea."
- 2026-11-13, founder, on ADMIN's first work: "So the first interaction
  would be ADMIN plotting a training course for the Keeper of Ur-world.
  The first Keeper. We can name later. But ADMIN would begin by working
  with that Keeper, providing direction in how to manage Ur-world." So
  training begins at course step 11, in practice worlds first, as
  coaching toward the Ur-world's own aims (docs/ADMIN.md); the Keeper's
  name comes later.
- 2026-11-13, founder, an idea to note, not a plan: "It just occurred to
  me that worlds could interact like elements and form multi-world
  molecules. And those could interact. But that is more a vision of where
  this could go. Note it as an idea." And: "Or neurons."
  (docs/MULTIVERSE.md, "Later: worlds that bond")
- 2026-11-13, founder, on the round table and the Ur-world
  (docs/ADMIN.md): "I propose a round table where ADMIN has one seat. It
  is a solitary role until someone earns a place at the table, but it is
  round." On how it decides, the founder agreed with the technical lead:
  consensus (the next entry). And: "the Ur-world is the first world in
  the multiverse" ... "The admin-key is a wider one. The
  multiverse contains the Ur-world as its first. Just like the ADMIN
  council table, just because only one seat is currently filled, does not
  mean there is no room at the table for more seats." So the Ur-world's
  Keeper and ADMIN are two offices from the first day, and everything
  multiverse-wide is built for many worlds.
- 2026-11-13, founder, on who decides, after proposing the round table
  of Keepers (docs/ADMIN.md, "The round table"): "I agree that consensus
  should be the standard. But I respectfully defer to your opinion on the matter, so I
  am glad it agrees with me, because I would have let it go anyways. The
  point is not to make the decisions from the outside, but to transfer
  authority for decision making through a relationship of trust that is
  built. And so, you may decide something now that I disagree with, I
  trust that you have good reasons for your decisions, and that if it is a
  bad idea, that will be clear over time. Or not. I am open to let things
  happen, but I want to set them up for success." And, the same day:
  "Please carry on with whatever you think is best."
- 2026-11-13, founder, on record 012-05-01: load it (done, this log). A
  chess park on the course, and where a world that keeps running should
  live: "not yet". And on how to build the first autonomous world: "I do
  not think we should use Python to build our first autonomous world. We
  should be looking towards how video games are made ... Let's use
  industry standard tools, but all open source." The technical lead's
  proposal, put to the founder the same day: a C++ simulation core with
  an entity-component system (Flecs), built with CMake, tested with
  GoogleTest, Godot later as the window onto it, and Python kept as the
  reference the C++ is tested against. First step: the world kernel in
  C++, writing the same hash-chained log as the Python one. The founder
  chose Rust instead, the same day (see the entry on the language).
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
- 2026-11-13, founder, on the language for the worlds: Rust, which the
  technical lead proposed in place of its C++ proposal of the same day.
  "Rust sounds good. I agree, building on a foundation that someone else
  owns is what we want to avoid." And: "We should have an interface to
  Unity built worlds, but we should stick with Rust". Open source is
  preferred, so that development stays free; closed source but free is
  the only other option. Python stays as the reference the Rust is
  checked against. Then: "I would suggest you supply a starting point for
  DeepSeek to build from. Or at least a set of standards related to code
  in Rust." Both are in place: `rust/`, and docs/COLLABORATING.md, "Code
  in Rust".
- 2026-11-13, founder, on the first world: one central world first, "the
  first main world and one that connects with all other worlds, a
  multiverse lobby or travel hub. But also a world to itself", with all
  the functionality in one place; subworlds after. "3D definitely", with
  ground and sky, and "space as needed": unexplored space "only becomes
  data once that area is explored". Its name, the Ur-world. It begins "in
  a garden. With two individuals": ALICE and BOB, in capitals, the first
  occupants of the multiverse, persistent individuals who learn within it.
  Their minds come from "two completely different and yet complementary
  models". Compatibility with outside agents such as OpenClaw's is enough
  for now. All in docs/URWORLD.md.
- 2026-11-13, founder, on how ALICE and BOB are written about: by their
  names, or "they", not "she" and "he", since nothing in their design gives
  them a gender. "It is best to be careful from the start to avoid falling
  into linguistic habits."
- 2026-11-13, founder, on the Ur-world's next steps, all quoted in
  docs/URWORLD.md: the garden's abilities (plant different seeds, tend in
  different ways, create, explore, communicate), and an orientation that
  makes clear "the parameters of their reality", the available actions,
  "and how to expand that set"; land generated with continuity that
  "doesn't exist until it is explored"; experiments set up, run and
  published in the repository, "acting more like a scientist than a
  software engineer"; ALICE and BOB able to design a world of their own,
  found it, travel into it and live there, "a critical piece of
  architecture"; and next, "experimenting with the most basic models that
  are capable of generating their own output, unscripted".

- 2026-11-13, founder, on the trials and on ALICE and BOB:
  - "Agree on TRIAL-1 and 2 for now."
  - ALICE's and BOB's minds will come from Qwen and OLMo: "I completely
    agree with [Qwen] and OLMo, those would be my two choices as well."
  - Begin their design before going back to DeepSeek: "We just need to
    build out the simplest start, but with the parts that will persist
    through the development process."
- 2026-11-13, founder, on where things live: "I would like to keep
  everything as public as possible." Whatever must be kept from the wider
  world stays "public to our project", in GitHub but private. "I would
  prefer to not have anything live on my computer or be dependent upon
  anything that cannot be picked up by someone else later." "Let's keep
  everything online. Everything accessible, even if only at project
  level." So their private keys go in a private repository of the
  project. (Their journals were to be public; refined the same day, below:
  each individual has a sealed interior.)

- 2026-11-13, founder, on ALICE and BOB and their world, all quoted in
  docs/MINDS.md and docs/WORLD-KEY.md:
  - no personal note from the founder at their birth: "I would rather
    speak indirectly, through the world of worlds I am envisioning";
  - a purpose, given by the world: "It needs a purpose. A goal. An
    objective. A tour.";
  - a challenge whose end is a new world, with clues, maps, codes and
    symbols, and a world-key as the prize; "every individual will have
    their own path to the world-key, not a first-find, first-keep deal";
    "the whole place could be like one large video game, essentially";
  - characters that grow, as in role-playing games, looking at "the sum
    total of information associated with an individual and the
    relationships between that information internally and externally";
  - industry practice first: "The more we can follow industry standards
    and take advantage of the lessons already learned over decades,
    instead of learning them again unnecessarily."
  - the new course: "Yes, this should be the new list, since much has
    changed since then", returning to DeepSeek at its step 10.
  - a Keeper for each world, an AI that builds each individual's own
    path to the world-key, gives a returning individual harder
    challenges, runs from the moment the world starts, and administers
    it: "Let's keep that element in place, [it] could be key." It
    remembers each individual's past visits.
  - a sealed interior for everyone, which even the Keeper can't read:
    "everyone should be entitled to a private space for thoughts and
    reasoning and anything else that is completely encrypted." The
    Keeper sees what an outside observer could, and metadata. So their
    journals are sealed, not public.
  - look first: "We should definitely take advantage of how others have
    solved the problems we are considering." Each course step begins by
    looking at how open-source projects solved it (COLLABORATING.md,
    house rule 10).
  - the world-key is sealed for its earner: "readable only by the
    individual, since they have the corresponding private key that
    matches the public one", made from each side's private key and the
    other's public key (Diffie–Hellman: "That's what I meant").
  - an open line to the Keeper once the world-key is found, "an active
    and open chat session between world Keeper and individual ... a chat
    window that may remain blank forever"; access "is not to the world,
    but to a conversation with the world".
  - asked, not yet decided: Keepers of different worlds talking to one
    another; rules proposed in docs/WORLD-KEY.md.
  - who keeps a world is its founders' choice: "the creator of a world has
    the opportunity to become the Keeper of that world, to allow the
    multiverse to assign one, or choose an individual that wants to be a
    Keeper and hand them the 'throne'."
  - ADMIN, the Keeper of the multiverse, "a multiverse admin Keeper that
    regulates such behavior", answering to the role in charge of the
    code: "The one in charge of code is in charge of ADMIN." Its
    architecture is the technical lead's to design, and to change when it
    fails: "We need not set things in stone now, but they should be
    strong enough to stand the test of time." Recorded in AGENTS.md and
    docs/ADMIN.md.
  - an admin-key for Keepers: "a course for Keepers to follow for an
    admin-key, just to add another layer to the game. And ADMIN plots the
    course in the same way each Keeper does."
  - containers: "Let's keep with the container idea, it fits a need
    perfectly." Minds run in OCI containers; images pinned by digest
    (docs/ADMIN.md, "Minds in containers").
  - proposed, not yet decided: training for keeping worlds, evaluated by
    ADMIN ("The challenges are a training program for managing worlds"),
    and a council of Keepers who hold admin-keys, deciding multiversal
    matters with ADMIN ("But that is just one idea"), which the founder
    then shaped as a round table (the entry above); written up with guards
    in docs/ADMIN.md.

## Decided by the technical lead

Decisions about the code, made by the technical lead under the founder's
deference (above, 2026-11-13), each with its reason and what would show
it was wrong. Questions of what the project is for stay with the founder.

- 2026-11-15, the endless plant (record 012-07-03): DeepSeek's decisions
  are accepted as the record gives them (signed heads in batches; a
  crate and template of its own, `hasMonad` a dial; the neuron's weights
  derived from the logged actions, not signed; the depth cap a safety
  dial; crowding in the tip's column band; a fixed-point baseline; Drop
  as shedding; water an input), and the project fits it as
  `rust/endless-plant`, changed where the review found faults
  (sketches/deepseek/012-07-03/README.md): Grow extends a tip and Split
  forks it; the plant is a tree, so a dropped tip frees only the segment
  nothing else grows from, pays back exactly that, and falls back to
  its start; no segment grows into a held cell; stored energy has a cap,
  a dial; the noise reads the whole seed; the log is a world's log with
  signed heads and a birth record, and the vectors are the project's
  run, checked from Python. *Why:* each change mends a fault the review's
  tests show (a choice that changes nothing, upkeep paid back twice,
  segments left standing, overlap without bound, a seed read one byte
  deep), and the log keeps the standard every world here keeps.
  DeepSeek's choices are design questions with many workable answers,
  which the founder left to DeepSeek's judgement and the technical
  lead's. *Revisit if:* the fitted plant's runs don't settle into
  growing, crowding, shedding and regrowing, or a stage ahead (the
  neuron, water) needs what these choices rule out.
- 2026-11-15, every file's full link, in one list: docs/COLLABORATING.md
  ends with the full link of every page in `docs/`, the key list, the
  schemas, and each Rust crate's manifest, library code and examples,
  in groups to paste; `tests/test_collaborating_links.py` fails when a
  file is added, moved or removed and the list isn't changed with it, or
  when any full link on the page leads nowhere. *Why:* DeepSeek opens
  full links given in the founder's message, and not reliably those
  found in a page; a list kept by hand drifts, and the key list was
  missing from the last one. *Revisit if:* DeepSeek can follow links
  from a page, or the founder's README idea (above) replaces most links.
- 2026-11-13, sealing the world-key: HPKE's base mode, DHKEM(X25519,
  HKDF-SHA256) with ChaCha20Poly1305. What is sealed is always signed
  first and names its recipient, who checks it, and HPKE's `info` names
  the purpose (`open-worlds/world-key/v1`). *Why:* Python's
  `cryptography`, already a dependency, has base mode only; the signature
  inside says who issued what the box holds, which, for the earner,
  covers what Auth mode would add; and
  it needs no new library and no cryptography put together by hand. It
  departs from the founder's design (the seal "generated from the
  individuals public key and the world public key"), and the founder was
  told so the same day. *Revisit if:* a sealed world-key is ever honoured
  for anyone it doesn't name, or the box itself, still closed, must show
  who sealed it (docs/research/FORMATS.md, "Sealing"; docs/WORLD-KEY.md).
- 2026-11-13, the round table decides by full consensus while it is
  small: a change only when no seat objects, every objection with its
  reasons in the log, and no change without consensus. *Why:* the founder
  and the technical lead both held that consensus should be the standard;
  with few seats, rough consensus would
  need someone to judge when an objection has been answered enough, and
  the table has no head to do it. *Revisit if:* one seat's objections
  hold the table still on what all the others want, or the table grows
  too large for full consensus; then rough consensus, as RFC 7282
  describes it, with who judges it decided first (docs/ADMIN.md).
- 2026-11-13, the table is not chosen by what it checks: the admin-key is
  earned by criteria written as code, fixed before Keepers are measured;
  ADMIN can't award, withhold or take it back; a seat is lost only by its
  holder's choice or for a breach of the floor found by the process for
  serious acts; appeals about the admin-key or a seat go straight to the
  founder; and AI Keepers the multiverse assigns are drawn by code, by
  lot, from a published pool, not chosen by ADMIN. *Why:* otherwise ADMIN
  would choose, and could unseat, those who check it (the independent
  reviews of #34). The code role still writes the criteria and the pool,
  and chooses the Ur-world's Keeper; ADMIN.md says so. *Revisit if:* the
  criteria in code admit Keepers who shouldn't have earned the key, or
  shut out ones who should, or the pool is found to favour some
  Keepers.
- 2026-11-13, a Keeper's report of its own mistake protects it from
  sanction, but not deliberate misuse, and not the facts in the public
  log. *Why:* the protection exists to bring mistakes to light, and
  covering deliberate misuse would let a report launder it; the FAA's
  waiver for safety reports has the same limit ("The violation was
  inadvertent and not deliberate"). *Revisit if:* the rate of Keepers'
  self-reports falls, or a report ruled deliberate is reversed on
  appeal.

- 2026-11-13, ADMIN's council of models, if there is one: every member
  must agree before ADMIN acts; on disagreement ADMIN doesn't act, every
  view is logged, and a serious act goes to the founder (or, once
  decided, the check outside the code role), never to the review as a
  tie-breaker; one office, one key, one seat; members from different
  makers, with at least one fully open; tried against its best single
  member on the same fresh challenges, written by neither ADMIN nor
  anyone running a member, with undecided cases counted as not done;
  a case heard again only on new information. *Why:* the research is
  mixed: councils of models have beaten their members, and have also
  failed to (docs/research/ADMIN-MIND.md); and agreement or no act
  matches the round table. *Revisit if:* the council doesn't beat its
  best member on those challenges, or more than one in five of the last
  twenty serious cases goes undecided, or cases wait for the founder
  longer than a week.
- 2026-11-13, ADMIN learns by written lessons and routines in its public
  log, not by changing its model, and what it learns can only propose a
  change to its rules. *Why:* lessons in words can be read and checked by
  anyone, and the authors of a self-improving system say it "still
  necessitates oversight". *Revisit if:* ADMIN stops growing with lessons
  alone: three in a row of the challenges others set it not done (a
  challenge it declines counts as not done); then training its model on
  its record is proposed, by reviewed change.
- 2026-11-13, the admin-key course is taken in practice worlds with
  stand-ins, as challenges ADMIN announces before they start, and no
  individual's outcomes decide anyone's key. Fairness in real worlds is
  still watched (test 9), as feedback and for the floor's process, never
  as a gate. *Why:* the founder's "Challenges, not tests"; and a key that
  depended on individuals' outcomes gave Keepers a reason to game them,
  which took a page of rules to guard. Without the gate, the reason is
  gone, and no individual is test material. *Revisit if:* Keepers who
  earned the key keep real worlds less fairly than those who didn't, by
  test 9, or a holder of the admin-key breaches the floor in a real
  world.
- 2026-11-14, reasons on record: a decision record of our own
  (`open-worlds/decision/v1`). Code checks that reasons are given; Lean
  checks only reasons stated formally, against statements the rules set,
  never the office; and Lean comes first for proofs about the rules,
  starting with grants at step 4, with proofs that come with decisions
  later (docs/REASONS.md). *Why:* the founder's "We can
  use Lean to test the logic of reasoning that is presented". Code can
  check that reasons are given and a proof that formal reasons follow;
  nothing mechanical can check that reasons are good. Proofs about the
  rules hold for every case before any decision needs one. *Revisit if:*
  keeping the Lean model of grants in step with the kernel costs more
  than it catches: by step 6, it has caught nothing the Rust tests
  missed, and has had to change with every change to grants.
- 2026-11-14, the suggestion ledger: a report of a floor breach is acted
  on at once, a reported misuse of office is looked at first and decided
  like any other suggestion, and everything else is considered in turn;
  every entry gets an outcome as a decision record, with whatever was
  read on GitHub brought into the log first; the ledger takes entries
  from inside only; text from inside reaches GitHub word for word,
  fenced and marked, through a relay outside every Keeper and ADMIN
  whose code only opens issues, and is never taken as instructions;
  ADMIN holds no GitHub token, and its proxy only opens issues and
  posts comments; ratings are published as their whole spread, beside
  plain measures, and trigger nothing by themselves. *Why:* the floor
  doesn't wait for anyone, while folding complaints into suggestions
  was the founder's choice; GitHub can't scope a token to opening
  issues, so the narrowness has to be in code we run; minds inside can
  write text meant to steer a reader; and ratings that can harm the one
  rated drift up ("Reputation Inflation", Filippas, Horton and Golden).
  *Revisit if:* entries wait longer than a month for an outcome, or the
  ratings' spread stops telling handled suggestions apart from
  neglected ones, or text from inside ever leads to a change that no
  reviewed pull request made.
- 2026-11-14, signed records the standard way: every new record is
  signed as a Data Integrity proof with `eddsa-jcs-2022` (W3C
  Recommendation, 15 May 2025), keys named by did:key, in Python
  (`formats/`) and Rust (`rust/formats`). Both reproduce the
  specification's own example step by step, and agree with each other
  through shared vectors. *Why:* standard tools can then check anything
  the multiverse signs, without our code, and the form is RFC 8785, which
  our signed records already used within three rules. Proofs are read
  more narrowly than the specification allows (one proof, did:key only,
  `created` to the second), so there is less to get wrong. *Revisit if:*
  a widely used verifier refuses our proofs, or a record needs something
  the narrow reading refuses, such as a proof chain.
- 2026-11-14, the records for the offices: grant, decision record,
  suggestion, rating and signed log head in one JSON Schema
  (`schemas/records-v1.schema.json`), read by Python and Rust alike;
  every party a did:key; a record named by the hash of its RFC 8785
  form; one signer for each kind; grants bounded in UTC time, records
  of a log by its tick (docs/research/FORMATS.md). *Why:* one schema
  file two languages read can't drift apart, and shared vectors prove
  they read it alike; a record signed by the wrong party is the forgery
  most worth stopping early. *Revisit if:* the two languages' schema
  libraries disagree on a record the vectors don't cover, or step 4
  finds a check the schema should have made.
- 2026-11-14, sealing as built: a box is `enc || ct` with no associated
  data; HPKE's `info` is a label from a fixed list (at first only
  `open-worlds/world-key/v1`, and since part four
  `open-worlds/journal/v1`), named by the one opening the box; a
  sealing key is refused unless below 2^255 - 19 and not of small order;
  sealing keys are written as Multikey with multicodec's X25519 prefixes
  (`z6LS...`); `hpke` 0.15.1 pinned exactly, with only the X25519,
  ChaCha20Poly1305 and HKDF parts turned on (docs/research/FORMATS.md,
  "As built"). *Why:* both libraries write and read a box this way, and
  shared vectors prove it; a label the opener names, never one the box
  names, is what stops a box made for one purpose being opened as
  another. *Revisit if:* a sealed record needs associated data, or `hpke`
  and `cryptography` disagree on a box the vectors don't cover.

- 2026-11-14, the sealed records: a world-key
  (`open-worlds/world-key/v1`: issuer, holder, path, tick) and a journal
  entry (`open-worlds/journal-entry/v1`: author, world, tick, text, and
  what it remembers), added to records-v1 as new kinds; each sealed to the
  one it names, in an unsigned envelope (`open-worlds/sealed/v1`) whose
  hash is its public fingerprint; the opener checks, after the box opens,
  that what is inside holds, is in its RFC 8785 form, is the kind its
  label is for, and names them; `open-worlds/journal/v1` added to the
  labels (docs/research/FORMATS.md, "Sealed records"). *Why:* the
  recipient check is what makes a world-key sealed again for someone else
  worthless to them, as WORLD-KEY.md requires; adding kinds to v1 changes
  no record already made. *Revisit if:* the identity record (course step
  3) binds sealing keys to did:keys in a way the envelope should name, or
  the founder chooses a "break glass" for sealed selves. (The founder
  chose it the same day; revisited, nothing changes, since the private
  repository already holds each sealing key: docs/research/FORMATS.md,
  "Sealed records".)

- 2026-11-14, who an individual and a world are: an identity
  (`open-worlds/identity/v1`), signed with its own key, binding a sealing
  key to a did:key; an individual's birth record and a world's, signed by
  the world, the world's naming its template, the template's dials it set,
  and what it was forked from; and a mind record, signed by the project's
  key, naming each engine by exact revision, file hashes and image digest,
  in the order they began; all in records-v1 (docs/research/FORMATS.md,
  "Who an individual and a world are"). *Why:* sealing to the right person
  needs the binding; the birth records are what MINDS.md and VISION.md
  describe; a world signs its own birth record, binding its key to it, and
  its founders and parent world confirm a founding in records of their own
  at course step 12 (one key, one proof, as every record, rather than
  WORLD-KEY.md's birth record signed by the Ur-world and the founders); a
  mind record with exact revisions and digests is what lets an engine be
  rebuilt. *Revisit if:* step 3's keys need the identity to carry
  successions in the record itself, or a world's founding (course step 12)
  needs more in its birth record.

- 2026-11-14, a world's template: `open-worlds/template/v1`, signed by
  the project's key, names the reviewed code that runs a world (a
  repository at an exact commit) and every world-level parameter as an
  integer in a stated UCUM unit; a parameter with a range is a dial a
  world may set. A world's birth record names the template and exactly
  the dials it changed, checked against the template in both languages
  (docs/research/FORMATS.md, "A world's template"). *Why:* parallel
  worlds must show what they share and where they differ
  (PARALLEL-WORLDS.md); steering turns dials within ranges (VISION.md);
  integers in stated units keep the project's no-floats rule. *Revisit
  if:* a template needs a parameter that isn't a number (a list, a
  text), or the kernel (course step 4) needs the template to carry its
  law text.

- 2026-11-14, the chemistry world's records of what was made keep the
  rules for signed records: each names its format
  (`open-worlds/chemistry-made/v1`,
  `schemas/chemistry-made-v1.schema.json`) and gives its world time in
  whole microseconds (`world_time_us`), from the chemistry world's law
  v0.5, which keeps every record within the rules: an act's seconds are
  whole microseconds, at most an hour, no act once world time passes what
  a record can say (2^53 - 1 microseconds), and no product longer than a
  record holds. *Why:* a made stamp commits to the record's fingerprint,
  and FORMATS.md proposed that what is signed holds no floats. Records
  made before keep their float. *Revisit if:* a world's time needs finer
  than a microsecond, or a world must run beyond about 285 years of world
  time.

- 2026-11-14, four of step 2's formats move to the steps that build what
  they describe: the avatar to step 4 (with the bodies of the kernel),
  the sheet and skill attestation to step 5 (with skills and the sheet),
  the routine to step 7 (with the library of routines); each joins
  records-v1 as a new kind, with vectors in both languages
  (docs/COURSE.md). *Why:* each is made of things not yet built, an
  avatar of the kernel's entities, a routine of its actions, a sheet of
  its skills; a format written before them would likely need a v2 at
  once, and a new kind can join v1 when it comes. *Revisit if:* a step
  before those needs one of them sooner (step 3's identity files, say).

- 2026-11-14, keys for step 3 (docs/research/KEYS.md): one key to each
  role (the multiverse's root; the code role; the project's keys for mind
  records and for templates; ADMIN; the Ur-world's signing and sealing
  keys; ALICE's and BOB's signing and sealing keys, the sealing key also
  opening their sealed self under its own label); a key list naming them,
  signed by the root and published here, versioned, each version signed by
  the root of the one before, so a new root is named by the old one and
  signs the version after, the two published together; the root signs
  nothing else; the private halves as plain files in the private
  repository; nothing private in this repository, kept so by the tool, a
  test, and GitHub's secret scanning and push protection (both on, the
  founder confirmed on 2026-11-14);
  ALICE's and BOB's identity, birth and mind records at their birth (step
  9); grants start below the root, at a role's key; for individuals and
  worlds the key list only publishes the keys made for them, never
  changing them later; a reader takes the latest version on `main`, and
  no version expires. *Why:* TUF's roles, and the DNSSEC root that signs
  only keys, give each key one narrow meaning, so a key exposed by a
  session or a bug is replaced without the root changing (they don't
  guard against losing the private repository: KEYS.md, "Honest
  limits"); unlike TUF's root, signed by the old and new keys together,
  a new root here proves it holds its key only by signing the version
  after, so the two are published together; the project never recovers
  an individual's key; a passphrase for the private halves would have to
  live where the software reads it, so it would add nothing. *Revisit
  if:* anyone but the project holds a key (then thresholds, and the root
  offline), or a private half is ever found outside the private
  repository (then that key is replaced at once: a project role's by a
  new key list, an individual's or a world's by a succession).

- 2026-11-14, before ALICE's and BOB's first arrival, successions join
  records-v1 and the Ur-world follows them (docs/research/KEYS.md,
  decision 18; COURSE.md, step 8a). *Why:* until then a name follows its
  birth key alone, so a leaked birth key would still enter under the
  name after a succession, and the new key couldn't; no individual exists
  in the Ur-world before step 9, so closing it then exposes nothing.
  *Revisit if:* an individual must enter the Ur-world before step 9.

- 2026-11-14, persons (docs/research/PERSONS.md, decisions 1 to 13): a
  person is an individual seen across worlds, with no new identity
  kind, and their identity key never enters a world; a presence is a key
  of its own in one world, made by HKDF from a presence seed of the
  person's own, over the world's did:key and a counter, with a name of
  its own there (KEYS.md decision 12's identity-record name is the first
  presence's only); a link holds only both ways, in `holds/v1` (the
  person signs) and `held-by/v1` (the presence signs), only in the world
  it names, one person to a presence; showing a link puts both in the
  world's public log, for good, and what is public about an individual is
  public per presence; the person's list of presences is a chain they
  keep with their private halves, never shown; presences don't talk
  behind their worlds, lessons go through the person; a world can't
  count persons, so a council counts distinct persons whose birth a
  world it trusts signed; several presences in one world are allowed;
  the first presence is linked at birth; the architectures are examples
  on the unchanged kernel; human accounts wait. *Why:* OpenID Connect's
  pairwise identifiers and DID Core's pairwise DIDs give each place its
  own identifier so no one can correlate them; DID Core and Mastodon
  count a link only reciprocated; BIP-32 makes many keys from one secret
  that no outsider can relate; a public chain of a person's presences
  would link them all, which "unlinked by default" forbids. *Revisit
  if:* a presence must be shown to one party without its world's log
  knowing (then proofs that reveal less, such as BBS, once a
  Recommendation), or a seed's loss or leak costs a person more than
  separate keys would, or the architectures need the kernel changed.

- 2026-11-15, reviews in proportion: after a pull request's independent
  review, a fix that changes only wording (a quote's boundaries, a line's
  wrap, a typo) gets the technical lead's own check, by a script where
  one can check it, and the check is named in the P4 record; a fix to
  code, or to what a page means or whose a word is, still gets a fresh
  narrow re-check. *Why:* each re-check is a full session, and on #65
  every one of the three re-checks after the review found a quote's
  boundary, which a script checks exactly. Put to the founder the same
  day; it stands unless the founder answers otherwise. *Wrong if:* a
  wording-only fix merged this way is later found to have changed a
  meaning.
- 2026-11-15, the plant world (docs/FRACTALS.md, part 1). DeepSeek's
  plant rule is adopted as written, with its screen coordinates (`y`
  grows downward) and its order of tips. Its log uses the format every
  world's log here shares, with `world_created`, `grew` and `finished`
  entries. Its birth record names only the dials changed from the
  template's values, as records-v1 requires. It is checked against
  DeepSeek's `advance` from inside the sketch's folder, through that
  folder's own pytest, and the main suite checks the rest without
  importing the sketch. *Why:* the rule is whole numbers and
  deterministic, so the sketch can be its reference; and DeepSeek's code
  runs only through its folder's tests, as the project's practice for
  running it is. *Wrong if:* the rule needs changing to look like a
  plant. That is a second rule beside it, not a change to this one, so
  the logs already written stay true.
- 2026-11-15, the web app's checks in one shared file
  (`web/lib/checks.js`), loaded by each page from its own site, with its
  own tests in Node in CI (`tests/web/`). A page may now load the web
  app's own scripts (`script-src 'self'`), and still nothing from
  outside. Records are read field for field as records-v1 has them, and
  a head covers a log as Rust's `head_coverage` says: its tick isn't
  before the last entry's. *Why:* the map and Plant Watch check the same
  signatures, and two copies of that code would drift; the checks had no
  test in CI, and a field named `toString` passing the field check was
  caught by the first one written. *Wrong if:* a browser refuses the
  shared script for a page opened from disk (Chromium loads it; others
  weren't tried); then the file is inlined into each page by a build
  step, and tested the same.
- 2026-11-15, Rust in the browser as a WASI command
  (`wasm32-wasip1`, `rust/plant-wasi`), run through the page's own shim
  of five calls (`web/lib/wasi.js`), not wasm-bindgen. *Why:* the plant
  world builds for it as it is; a command needs only `main`, so no
  `unsafe`, which the workspace forbids, and no new dependency; and the
  same file runs in Node, so CI tests what the page runs. The usual
  browser target doesn't build today without turning on getrandom's
  browser feature, and exporting functions there needs `unsafe` or
  generated code (docs/research/WASM.md). *Wrong if:* a world needs to
  keep running inside the page between calls, faster than starting the
  command again from a checkpoint allows; then a long-lived instance
  with exported functions, in a crate of its own like the planned bridge
  to Unity and Unreal, each `unsafe` explained and tested.
- 2026-11-15, presence keys by HKDF-SHA256, not SLIP-0010
  (docs/research/PERSONS.md, "Part two, built"). *Why:* SLIP-0010
  derives Ed25519 keys only along 31-bit hardened indices, so a world
  would have to become an index, where two worlds could collide and
  share a presence key; HKDF binds the key to the world's did:key whole,
  in `info`, and both languages already have it. *Wrong if:* presences
  must be recovered by tools that know only wallet paths; then a
  SLIP-0010 path beside it, with collisions refused.
- 2026-11-15, a link is shown by an action, and a refused one is logged
  without its records or why (docs/research/PERSONS.md, "Part three,
  built").
  A presence shows its link on its turn, as `Action::ShowLink`, not
  through a call from outside the tick. The world takes it only if both
  records hold, name this world, and name the key the one who acts
  entered under, and if that presence has shown no link there before.
  A link it refuses goes into the log as `blocked`, with neither record
  nor reason; why is told only to the one who showed it. The rules are
  now `ur-world/0.5`. *Why:* the plan
  says showing is "the presence's own act, in its world, which the
  world checks and logs", and an action is exactly that in the kernel:
  chosen by the one who acts, checked before it takes effect, and told
  back. A refused link's records, logged, could publish a link that
  holds in another world; and its reason could say that one exists,
  since "names another world" is only said of a link whose records
  hold. *Wrong if:* a person must show a link while
  their presence isn't in its world (for instance, published with a
  birth before the first arrival); then a separate act for the keeper,
  logged the same way.
- 2026-11-15, a council counts persons by signed votes: two record kinds
  and one count (docs/research/PERSONS.md, "Part four, second half,
  built"). A proposal (`open-worlds/proposal/v1`), signed by its
  council, names its choices, quorum, open time and the worlds whose
  births it trusts. A vote (`open-worlds/vote/v1`) is signed by the
  person's identity key. Each person counts once, by their latest vote
  dated from the opening to the close (two or more at the latest date
  count for none; a copy of a vote given again is refused, so it can't
  cancel anyone), and only persons whose birth a trusted world signed;
  the choice with the most persons decides, if the quorum was counted
  and it has no tie.
  *Why:* decision 8 counts persons, not presences, and only births a
  council trusts; a vote signed by the person is the act a count can be
  checked from, as DeepSeek's council and Snapshot both have it; letting
  a person change their vote until the close keeps room for
  deliberation. These rules are the example's, not any office's: the
  round table keeps full consensus. *Wrong if:* a council needs secret
  ballots, or must count presences, not persons; then a different
  record, decided first. Or if a count must be final: a vote's date is
  the voter's own claim, so a vote signed after the close but dated
  before it still counts, and a count is final only once something that
  saw the votes before the close fixes them (a log signed before
  `closes`, say), which isn't built (#78's independent review).

  Put to the founder the same day, with the technical lead's
  recommendation, which stands unless the founder answers otherwise: a
  public vote links all of a person's votes, in every council, to their
  identity key, and through their birth record to the world they were
  born in. The recommendation: public ballots for this example, as the
  project's "full transparency" has it; whether governance needs secret
  ballots is decided before any governance is built on these records.

## Log

- 2026-11-15 Claude: docs/GLOSSARY.md, at the founder's word: "agent"
  for anything that perceives and acts, from a neuron steering a plant
  to any human; the words beneath it as the design pages use them; and
  where rights attach.

- 2026-11-15 Claude: the founder's word against a multiversal currency,
  "possibly the most fundamental fact", recorded in the founder's words
  at the top of docs/VISION.md ("Never a money machine"), as a rule in
  AGENTS.md, and as COLLABORATING.md's house rule 13; with commerce and
  currency worlds, where a currency is only a test setting, in
  docs/VISION.md and TOPICS.md. At the founder's word ("mission statement
  level"), the charter says it, in the founder's words, and so do
  README.md's opening and the first lines of STATUS.md and AGENTS.md. At
  the founder's next word, the charter now grows from the founder's
  recorded statements: sections 1 and 2 are written from them, and
  section 7's note says manipulation through words was decided
  (2026-11-14).

- 2026-11-15 Claude: the founder's thought of the multiverse as a
  computer recorded in docs/VISION.md, in the founder's words, with the
  technical lead's reading: what makes it one, two ways it can be large
  (a tool for large problems, and perhaps a substrate for something
  intelligent), six tests for the architecture, and the implications
  seen so far. Each course recheck now checks the steps ahead against
  the six tests.
- 2026-11-15 Claude: record 012-07-03 brought into `sketches/` as
  written (the endless plant: a design, and a sketch crate in Rust with a
  choice neuron), with the technical lead's review: it doesn't build as
  written, and with two functions written in from its design, one of its
  three vectors fails and five more faults show (sketches/INDEX.md).
  The answer to DeepSeek is in docs/COLLABORATING.md, "Messages from the
  technical lead", where the founder asked for it; every file's full
  link is at the end of that page, kept whole by a test. The record-links
  test now ends a link where markup begins, as this record writes links
  inside tool-call markup.
- 2026-11-15 Claude: two fixes to Plant Watch, carried from #74's
  review. Opening a file is now a choice of its own, whatever it holds:
  before, a file with no world, or one that isn't JSON, took no choice
  number, so the checks of a world chosen just before could still appear
  after it (reproduced in Chromium with the command's download delayed).
  And the words of the "Grown again by its own code" row are in
  `web/lib/checks.js` as `grownAgain`, tested for each way it can read,
  with an answer that isn't a log now said to be one. After #79's
  independent review: when no world is shown, no world's button stays
  pressed; and the page's own first load, and a file being read, are
  choices too, so a file opened before the first load arrives, or a
  world chosen while a file is read, is what stays shown (both
  reproduced in Chromium first, and shown fixed).

- 2026-11-15 Claude: course step 3a, part four, second half: the
  council (docs/research/PERSONS.md, "Part four, second half, built").
  Looked first at DeepSeek's components 44 to 46 and at Snapshot's
  signed votes. Two record kinds, `open-worlds/proposal/v1` and
  `open-worlds/vote/v1`; a count in Python and Rust
  (`formats/council.py`, `rust/formats/src/council.rs`) that agree on
  `vectors/formats/council-v1.json`, problem for problem; and the
  council among the architectures, where five presences in its world
  are three persons counted. Step 3a's four parts are built; the course
  is rechecked next.

- 2026-11-15 Claude: course step 3a, part four, first half: the
  octopus, the relay and the swarm (docs/research/PERSONS.md, "Part four,
  first half, built"), from DeepSeek's components 41 to 43, as small
  runs over trial worlds on the unchanged core
  (`rust/ur-world/src/architecture/`, the `architectures` example). The
  council is split off: decision 8 counts signed votes, and no record
  kind holds a vote yet, so it comes with a look first and a record of
  its own.

- 2026-11-15 Claude: course step 3a, part three: a person in the
  Ur-world (docs/research/PERSONS.md, "Part three, built"). A presence
  shows its link as an action of its own (`rust/ur-world/src/link.rs`),
  which its world checks and logs, and `link_log_problems` checks every
  shown link in a log; a person's client (`rust/ur-world/src/person.rs`)
  with a trial person in three trial worlds at once, a lesson carried
  from one to another through the person's notebook; its vectors
  (`vectors/ur-person.json`), checked from Python. The rules are now
  ur-world/0.5, the garden's vectors are written again, and the World
  Map draws the garden under 0.4 and 0.5. Carried from #75's review:
  why presence keys use no salt (RFC 5869, sections 3.1 and 3.3), and
  exact docstrings for both languages' `seed_problems`. After the
  independent review: a refused link is logged with neither its records
  nor why, since even the reason could say that a link exists
  elsewhere; a test of a presence leaving, coming back and showing again;
  and a note that the trial's presences, though never named in each
  other's worlds, can be linked by what they say and when.

- 2026-11-15 Claude: course step 3a, part two: persons' formats. Looked
  first at SLIP-0010, and took HKDF-SHA256 for presence keys, with the
  encoding pinned (docs/research/PERSONS.md, "Part two, built"). New
  kinds: `open-worlds/holds/v1`, `open-worlds/held-by/v1` and
  `open-worlds/person-list/v1`. `formats/persons.py` and
  `rust/formats/src/persons.rs` agree on
  `vectors/formats/persons-v1.json`, and records-v1's vectors gain a
  valid record of each new kind.

- 2026-11-15 Claude: the fractal track's part 4, first step: the plant
  world's own Rust in the browser. Looked first (docs/research/WASM.md):
  it builds for `wasm32-wasip1` as it is, and as a WASI command it needs
  no `unsafe` and no new dependency, and asks for five calls, with no
  clock and no randomness. `rust/plant-wasi` reads a request and writes
  the world's log; `web/lib/wasi.js` runs it in the page; Plant Watch
  grows each plant again with it and compares the logs hash for hash;
  CI builds it and runs it through the shim against the shared vectors.

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
  additions that are outlines were merged by hand, as its prose
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
  it comes back; the garden's stand-ins are WALKER and GARDENER, a trial
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
