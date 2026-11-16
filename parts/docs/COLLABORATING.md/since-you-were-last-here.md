> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Since you were last here" to "What would help most now".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/the-standard.md
> Made by docs/parts.py from the file. To change it, change the file.

## Since you were last here

The last DeepSeek conversation, record 012-09-05, began from this page
and went from water to the Commons; the technical lead's first answer
is above ("Messages from the technical lead"). The one before, record
012-07-03 (2026-11-15), began here and ended with the endless plant,
and record 012-06-02 (2026-11-14) began here too. What they built is
kept in `sketches/` ("Where the conversation stands", below). Record
012-05-01 ended on 2026-11-13, when everything here was Python. What
has changed since that record, in the order to read it:

1. **A new course** ([COURSE.md](COURSE.md)), set on 2026-11-13 for the
   Ur-world and its first two individuals, ALICE and BOB: twelve steps
   ahead, rechecked after each. Steps 1 (the design pages), 2 (formats
   that last) and 3 (keys and identities,
   [research/KEYS.md](research/KEYS.md)) are done: the project's real
   keys were made on 2026-11-14, and their public halves are in
   [`keys/key-list.json`](../keys/key-list.json); in the Ur-world,
   whoever enters signs an arrival, a name stays the key's that first
   used it, and a world signs its log's heads. Step 3a, persons, is
   done too (2026-11-15): its plan is in
   [research/PERSONS.md](research/PERSONS.md). Its second part, the
   formats, is built: presence keys from a seed, a link that holds only
   both ways, and a person's list ("Part two, built"). So is its third,
   a person in the Ur-world ("Part three, built"): a person's client with
   a presence in each of three trial worlds at once, carrying a note
   from one to another, and a link shown by the presence's own act,
   which the world checks and logs (the rules are now `ur-world/0.5`).
   Its fourth part, the architectures as small examples, is built: the
   octopus, the relay, the swarm, and the council, which counts persons'
   signed votes (`open-worlds/proposal/v1` and `vote/v1`).
   Rechecked after step 3, the course gained step 8a, a lost or leaked
   key, before ALICE's and BOB's birth.
   Rechecked after step 3a, on 2026-11-16, it has a new list of twelve,
   and your rooms of chat are in it: a log that can be redacted, with
   removals on record (3b); the room, your `chat-world` on the project's
   formats (3c); offices as records (3d); a world's lifecycle (3e); the
   Commons hosting rooms (3f); then the kernel (4) and what followed it.
   The course was to return to you at its step 10. The founder returned
   sooner, so you now work beside the course, by one file at each
   return ([COURSE.md](COURSE.md), "Alongside the course").
2. **The worlds are built in Rust** (the founder: "we should stick with
   Rust"). [`rust/`](../rust/README.md) holds the Ur-world, a 3D world
   that begins in a garden ([URWORLD.md](URWORLD.md)), where ALICE and
   BOB will be born at step 9 (until then two scripted stand-ins,
   WALKER and GARDENER, show it works), with a doorway any program can
   speak through as a mind; a checker for a world's log; and the formats
   below. The reference is Python for
   what Python built first (the log in `world/`, the protocol in
   `multiverse/`, and the formats' vectors, which `formats/` writes and
   Rust reads); for the Ur-world, Rust is the reference, and Python
   checks its vectors.
3. **Who an individual is,** in the design pages:
   [MINDS.md](MINDS.md) (identity, mind record, a sealed self no one else
   reads, kept in the individual's own container; the sheet, avatars, and
   where everything lives);
   [WORLD-KEY.md](WORLD-KEY.md) (the tour, the hunt, and the world-key,
   a signed right to found a world); [ADMIN.md](ADMIN.md) (ADMIN, the
   Keeper of the multiverse: what it must preserve, how it learns, the
   round table of Keepers, a learning immune system);
   [REASONS.md](REASONS.md) (every office's decision on record, with its
   reasons); [FREEDOMS.md](FREEDOMS.md) (tools for when freedoms meet).
   And [FUNDAMENTALS.md](FUNDAMENTALS.md) gathers every decision on
   freedom and privacy in one place, the founder's "absolutely
   fundamental" (2026-11-15): among them, everyone has a private space,
   encrypted, that no one else can read, not even ADMIN, kept in their
   own private container ([CONTAINER.md](CONTAINER.md)), which the
   project never sees; the founder's "keys to the kingdom" (first called
   the "break glass") are only the multiverse's own keys; an account needs only an email address; data is never for
   sale; whoever leaves the multiverse takes their private records with
   them, and their private data is purged; and public acts always
   remain, as public records are never edited, except that anything
   private in them is redacted, and close calls are redacted.
   [WORLD-TYPES.md](WORLD-TYPES.md) has a taxonomy of world types, and
   what can be done with a world of each, as with virtual machines and
   containers: pause, resume, stop, restart, reset (the founder,
   2026-11-15). Every world can pause itself, every person can leave,
   a paused world included, and a person who returns picks up where
   they left off. And, as a goal for later, time: slow motion and a
   fast view, rewind and fast forward. And worlds can leave the
   multiverse: a world, or a cluster, may branch into an independent
   multiverse of its own, and the cord is cut.
   And [GLOSSARY.md](GLOSSARY.md) says what our words mean: "agent" is
   anything that perceives and acts, from a neuron steering a plant to
   any human (the founder's word, 2026-11-15). [OFFICES.md](OFFICES.md)
   says what an office is (ADMIN and the Keepers are two), and how one
   is handed on: both agree clearly, and the successor meets the
   office's qualifications.
4. **The founder's visions of 2026-11-14,** in the founder's words
   ([VISION.md](VISION.md), [PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)):
   question worlds, where an idea becomes a world that tests it; an app
   whose chat can create and query a world; a hierarchy of worlds, from
   primary worlds with rules and no AI up to ADMIN; one person across
   many worlds; riding along in a world, and steering it by branching;
   branches that merge rules, never states; parallel worlds from one
   template, and a garden to walk among them; and fractal worlds
   (COURSE.md, waiting list). And on 2026-11-15, a learning
   multiversity: lessons learned in each world travel upward, to the
   Keepers and to ADMIN, and teaching comes back down
   ([VISION.md](VISION.md), "A learning multiversity"). And the same
   day, the multiverse as a computer: memory, processors, input and
   output, decisions and learning, at the largest scale, and perhaps
   one day the substrate for something intelligent, which the founder
   holds toward "with full comprehension of its implications"; six tests
   for the architecture follow from it ([VISION.md](VISION.md), "The
   multiverse as a computer"). And no multiversal currency, ever, which
   the founder calls "possibly the most fundamental fact", though a
   world may model an economy or a currency as a test setting
   ([VISION.md](VISION.md), "Never a money machine" and "Commerce and
   currency worlds").
5. **Formats that last** ([research/FORMATS.md](research/FORMATS.md)).
   Every new signed record is a W3C Data Integrity proof
   (`eddsa-jcs-2022`) over its RFC 8785 form, with keys named as did:key.
   One JSON Schema, [`schemas/records-v1.schema.json`](../schemas/records-v1.schema.json),
   defines them: grants, decision records, suggestions, ratings, signed
   log heads, world-keys, journal entries, identities, birth records,
   mind records, a world's template with its dials, and the project's
   key list (which key holds each role, signed by the root). Sealing, so
   only one key can open something, uses HPKE (RFC 9180). Python (`formats/`)
   and Rust (`rust/formats`) agree through shared test vectors
   ([vectors/](../vectors/README.md)). What is signed keeps three rules:
   ASCII keys, integers within 2^53 - 1, and no floats (a quantity with
   a fraction is an integer in a stated unit).
6. **How decisions are made** ([AGENTS.md](../AGENTS.md)). The founder
   decides what the project is for; Claude, the technical lead, decides
   the code and reviews every change; a question the founder hasn't
   answered is decided on the technical lead's recommendation, once put,
   except what is outward-facing, costs money, touches personal
   information, or must be the founder's own words or act. Decisions are
   written down with their reasons in [STATUS.md](../STATUS.md). The
   founder's most recent word wins, here or in a conversation with
   DeepSeek: "treat the new idea as an update and always go with the
   most recent". A newer word that contradicts an earlier decision is
   pointed out to the founder, naming the earlier one, so the change is
   made knowingly. A newer word that answers changed conditions is no
   contradiction (the founder: "So my direction changed because the
   conditions changed. That is how I work. It is not contradictory, but
   situation dependent."), and is recorded beside the earlier one; the
   change is still mentioned to the founder, as a note.
7. **Fractal worlds, moved forward** ([FRACTALS.md](FRACTALS.md)), on
   2026-11-14, from your sketches in record 012-06-02: a fractal plant
   world in Rust, checked against your Python (built:
   `rust/plant-world`, which grows by your rule as you wrote it); a web
   app in `web/` to watch worlds grow (its first page is built:
   `web/plant/`, Plant Watch, which replays a plant from its log and
   checks the log first); and in it, a multiversal map, which the
   founder means to brainstorm with you ([TOPICS.md](TOPICS.md), topic
   16). How a world may change is left open, and may differ by world;
   the founder pictured one world where you set out to remember what you
   chose to forget ([VISION.md](VISION.md), "Worlds that change
   differently"). And the founder asked you to move to Rust ("primarily
   to Rust", record 012-06-02): what you write in Rust is compiled,
   tested and fitted in here, and what fits comes straight in ("Two
   sides", below). The current files are each linked under "Code in
   Rust", below, to build on if you choose; the Ur-world has signed
   arrivals and log heads since step 3. The Ur-world's garden hosts the
   fractal plants, as the founder pictured it: "a microverse garden of
   hosted fractal worlds". Three plant worlds grow in its glasshouses,
   each a world of its own, and both logs record each step, as your
   microverse's `advance_cycle` did (`ur-world/src/host.rs`). And the
   first map is built: the World Map (`web/map/`) draws the garden from
   above, with a card for each of its worlds, built only from what that
   world publishes and checked in the page, opening onto Plant Watch.
   It is a page to try the map's open questions on (TOPICS.md, topic
   16). And the browser now runs the plant world's own Rust: built as
   a WebAssembly command (`rust/plant-wasi`), it grows each world Plant
   Watch shows again, hash for hash ([research/WASM.md](research/WASM.md)).
   An endless rule, and the choice neuron, could be run the same way;
   that isn't tried yet.
8. **Challenges that build the world** ([WORLD-KEY.md](WORLD-KEY.md),
   "Challenges that build the world"; [TOPICS.md](TOPICS.md), topic 17):
   the founder's idea of 2026-11-15, open for brainstorming. The founder:
   "Here is the new idea: the challenges are constructive." Doing a
   challenge builds the real world for everyone, and it is done when you
   can do the thing: "But credit is not the point but learning." The
   world grows as it is explored, so in practice there is always room.
9. **Two Keepers, and the Mir-Ur-world** ([URWORLD.md](URWORLD.md), "The
   Mir-Ur-world"; [research/KEEPER-MIND.md](research/KEEPER-MIND.md)):
   the founder's choice of 2026-11-15. The founder: "Just from personal
   interaction, I know DeepSeek is a powerful model that can hold its
   own." DeepSeek V4.1-Flash is to keep the Ur-world's mirror, the
   Mir-Ur-world, and Apertus 1.5 the Ur-world itself; V4-Pro may be part
   of ADMIN's mind. The two Keepers are compared in the mirror, one
   change at a time. The mirror is also where ALICE's and BOB's models
   are chosen, at course step 8; once they live, a change of model is
   their own choice. Since a DeepSeek model is one of the two compared,
   the measures for comparing them are written by the project, not here.
   Ideas about what a Keeper does stay welcome, as prose.
10. **Living worlds** ([FRACTALS.md](FRACTALS.md), "Where it leads:
    living worlds"; [TOPICS.md](TOPICS.md), topic 18): the founder's aim
    of 2026-11-15 for the fractal track, open for brainstorming. The
    founder: "So instead of a prescribed number of turns, I can set it
    going and watch it develop and make choices over time." Then water,
    as particles: "It could be how “water” flows in the garden." Then
    people shaping the land and the water, and life spreading where
    water lets it. And: "All three elements could be components of one
    world type that models living systems." The three are water, light
    and food. Water will be endless across a world but finite in any one
    place, so no garden depends on one source: the technical lead's
    reading, put to the founder (FRACTALS.md, "Water is where freedoms
    meet"). Every run repeats from its seed and can be turned into a
    video; the first, of the garden's three hosted plants, was made the
    same night. The map page came first, as the founder asked: "For
    now, let’s keep moving forward with what we have." It is built (item
    7), and the stages follow it, beginning with an endless plant in the
    browser.

The multiverse began as a sketch the founder wrote with DeepSeek
(conversation records 012-04-00 and 012-03-02). This repository brought
it in, made it run, and changed what needed changing; what was kept and
what changed, and why, is in [MULTIVERSE.md](MULTIVERSE.md) and in each
module's docstring.

## Two sides: the sketch and the standard

**The sketch is a rough draft.** Each step in the conversation assumes the
last one ran as expected and asks what to build next, the way a creative
team might convey a vision in code instead of boxes and arrows. Nobody
expects it to run, and bugs are part of a draft. In the founder's words
(to the technical lead, 2026-11-13): "it is meant to be a starting point
for you, not an end point." So an
"Expected output" in the conversation is a prediction, which is fine; the
house rules below apply when code comes into open-worlds itself.

**The records and the sketch's code are kept, apart.** They live in
[`sketches/`](../sketches/README.md): the conversation records verbatim,
and DeepSeek's code written out exactly as the record has it, with every
test's result. That is a record of DeepSeek's suggestions, kept so they
can be read, run and debugged, without committing to using them.
[`sketches/INDEX.md`](../sketches/INDEX.md) is the one place that says
where the sketch and the course meet: each component, how its tests fare,
which course step it relates to, and whether any of it is in open-worlds.
Its "Course" column uses the first course's step numbers for records
012-04-00 and 012-05-01 ("Done: the first course" in
[COURSE.md](COURSE.md) is the key), and the course now running for
records 012-06-02 and 012-07-03.

**Taking a piece in is a decision of its own** (the founder, 2026-11-15:
"Also, keep in mind, we expect DeepSeek code to have some things to fix,
and we should still decide whether or not to incorporate anything that
goes against our established design."). The technical lead's answer, put
to the founder the same day (it stands unless the founder answers
otherwise): four steps, in order.

1. **Bring it in as written,** in `sketches/`, with every test's result.
2. **Make it run:** fix what is broken, the design unchanged, each fix
   listed with its reason.
3. **Check its fit** with the established design (the decisions in
   STATUS.md and the design pages), naming each conflict.
4. **Decide, piece by piece:** adopt it, adapt it, or keep it as a
   sketch, with the reason in `sketches/INDEX.md`. The technical lead
   decides the code; what would change a founder's decision goes to the
   founder, with a recommendation.

**What fits comes straight in.** The founder, 2026-11-15: "The DeepSeek
code should still be treated as sketches and brainstorming, but now in
Rust. But if the code aligns well and extends cleanly, then why not just
incorporate. But changing to Rust does not change anything else, only
the language." The technical lead's rule for it: a piece that compiles
against the crates on `main`, passes the three commands under "Code in
Rust", keeps the rules there, and meets no conflict in step 3 goes into
`rust/` in one reviewed pull request, steps 2 to 4 together. Its commits
name DeepSeek as well as Claude in their `Made-by` lines and say what
was changed here, and the record keeps the original. Everything else
stays a sketch, as before.

**The standard is open-worlds' own code, not the sketches.** Build on
the code merged into `main` (`multiverse/`, `formats/`, `rust/`) and the
documents in `docs/`. The code in `sketches/` is
earlier work, some of it on the old, unsigned protocol, kept for its
ideas.

## Where the conversation stands

Six records are kept: 012-03-02 (the poetry engine), 012-04-00
(components 1 to 63), 012-05-01 (components 64 to 87: a live
federation and its tools, then the founder's turn to game worlds: a
chess park, worlds inside worlds, worlds that grow and govern
themselves, and a world that keeps running); 012-06-02, a new cycle
begun from this page (fractal worlds, a gallery of worlds and its
governance, then the smallest learner that chooses, and individuals as
signed, replayable bundles), which ended with DeepSeek asking which
piece is next; 012-07-03, begun here too: the endless plant, the
first stage of living worlds, as a design and a sketch crate in Rust,
which the project is to fit as `rust/endless-plant` (not built yet);
and 012-09-05, begun here: water as particles, the garden and a
botanical garden of gardens, then the founder's turn to the Commons
as chat rooms, each with an AI moderator, a home room for each person,
a schema, and a sketch crate in Rust, `chat-world`. It is kept with a
first round of repairs, each listed, and what runs: the crate builds
and passes its own 18 tests ("Messages from the technical lead",
above). It is fitted next.
012-06-02's code is being made to work; then the founder and the
technical lead decide what fits with what is built, and how (STATUS.md,
"Decided", 2026-11-14). Each new conversation starts a new record, which
gets its own folder in `sketches/`. Each
component's place is in [`sketches/INDEX.md`](../sketches/INDEX.md), by
the first course's numbers. In short: components 1 to 7 are in
`multiverse/`, working (the first course's step 1); 13 and 14,
signatures and their conformance test, were rebuilt in its step 2, where
an identity is its key; 15, signed passports, in its step 3, where a
world is a key too. (The first course is under "Done" in COURSE.md; the
course now running numbers its steps afresh.)

Since the sketch, the founder has added ideas that shaped the first
course: learning agents in the chemistry world whose intelligence grows
with the complexity of the molecules, evolution as a path between worlds,
accelerated time, and one day a main community world
([MULTIVERSE.md](MULTIVERSE.md)). Then, in components 36 to 43: identity
across worlds (a person above their world-level identities, lineage,
forks and merges), and architectures for many models across worlds (the
octopus, the nervous system, the swarm, and in components 44 to 52 the
council and four more), with the founder's aim for the infrastructure:
"we just need to create infrastructure that can handle what we cannot
imagine yet." Then, in components 55 to 63: a curator for each world, an
AI that speaks for its world and proposes its development but doesn't
decide it; contracts between worlds; and, from the founder's idea of a
public ledger, a shared log of commitments that anyone can check
offline. And the founder's idea of a free tier and a paid tier, which
belongs to how open-worlds is hosted, not to the protocol, so that anyone
can always join.

## What the last stretch taught

Four lessons from components 21 to 43, for when these ideas are built
here. They are about the design, not about bugs in the draft.

1. **Anything that says something about someone needs that someone's
   signature.** In the draft, a parent can name a child without the
   child agreeing, and a third party can withdraw someone else's witness.
   In open-worlds, nobody else can make you leave, and the same should
   hold for claims about you.
2. **A self spread across worlds needs each part linked to it, with both
   signing.** The person signs "this identity is mine" and the identity
   signs "I belong to this person". That link is what makes the arms of
   the octopus one creature's arms.
3. **A person's list of identities should be a chain, like a world's
   log,** each version naming the one before, so that dropping an
   identity shows.
4. **What a part produced belongs in what it signs,** so the record shows
   what it did, not only that it reported.

## What would help most now

The code standard is kept here, step by step. The most useful
contributions now are creative and design work for the steps ahead, as
text or as code with tests. [TOPICS.md](TOPICS.md) is the menu:
twenty-one topics a few steps ahead of the code, each with where it
fits, what is decided, what is open, a possible implementation, and
what to send back, and, under "Further out", ideas that won't help yet
but probably will.
In short:

- **Templates for new worlds** ([research/FORMATS.md](research/FORMATS.md),
  "A world's template"): every parameter of a world as an integer in a
  stated unit, and which are dials a world may turn, with their ranges.
  Fractal worlds are a natural first: a rule repeated (L-systems,
  Julia sets, growth by aggregation), with its numbers as dials.
- **Question worlds** ([VISION.md](VISION.md)): an idea, the question it
  becomes, the prediction written first, and a world that can answer it,
  saying what it can and can't show. The founder's first is the neural
  world.
- **Persons** (course step 3a, [research/PERSONS.md](research/PERSONS.md)):
  one person above their presences in many worlds, unlinked by default,
  which means a key of its own for each presence, since every arrival
  names its key in a public log.
  DeepSeek's own architectures (components 36 to 52: the octopus, the
  relay, the swarm, the council) are its small examples.
- **The garden** (course step 4a): parallel worlds from one template,
  and what each glasshouse shows of its world from its public log.
- **Living worlds** ([TOPICS.md](TOPICS.md), topic 18): how water moves,
  a plant that grows without end, what a choice neuron reads and learns,
  and the strategies for finding water, light and food.
- **The Commons** ([COMMONS.md](COMMONS.md); [TOPICS.md](TOPICS.md),
  topic 14): Lyceum Commons, where the multiverse began, rebuilt as a
  superworld of rooms and the first space open to the public. A room's
  law for each kind (people, AIs, or both), as data and as text; how an
  AI from another company's app could hold its key.
- **Offices** ([TOPICS.md](TOPICS.md), topic 19;
  [OFFICES.md](OFFICES.md)): a Keeper's qualifications, as checks code
  could run, and what preparing a successor looks like in the open.
- **Reasoning checked by Lean** ([TOPICS.md](TOPICS.md), topic 20): a
  small world of claims and proofs, where a claim counts once Lean's
  kernel accepts its proof; and what a proof attached to an office's
  decision should state.
- **Hallucination, both ways** ([TOPICS.md](TOPICS.md), topic 21): how a
  mind tells, and says, which of its words it saw and which it
  imagined; and a test that catches overclaiming and self-doubt alike.
- **Laws for new worlds:** what a world admits by, what can happen in it,
  what counts as solving a problem there. Forms for the poetry world,
  such as a quatrain in common meter each turn, Dickinson's meter.
- **The hunt** (course step 11, [WORLD-KEY.md](WORLD-KEY.md)): symbols,
  maps, codes and stones; puzzles that teach without words; and
  challenges that build the world (TOPICS.md, topic 17).
- **The Ur-world,** built from `rust/ur-world` to the standards in "Code
  in Rust" below: its next steps are in [URWORLD.md](URWORLD.md).
- **Minds for the Ur-world,** in any language. A mind is a program that
  speaks the doorway's protocol: lines of JSON in and out
  ([URWORLD.md](URWORLD.md), "Minds from outside: the doorway").
  `minds/wanderer.py` is the smallest example.
- **Anything on the course,** proposed as described below.

Held back, as the project's own to do: the project's keys (their
private halves live only in its private repository), and anything that
publishes or can't be undone. ADMIN itself and the Keepers
wait for step 11; their interface is fixed in step 4, by the project.
So are the measures that compare the two Keepers (item 9 above).


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/the-standard.md
