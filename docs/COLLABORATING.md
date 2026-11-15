# Building on this: start here

For anyone building on open-worlds, and in particular for the founder's
conversations with DeepSeek. This is the page to start from. The
founder: "What you put in the repo becomes the new standard we develop
from in my DeepSeek conversations."

**Kept current.** The founder, 2026-11-14: "please make sure the
COLLABORATING.md is up to date as we go. This way, if we run out of data
for a few days, I can still go and work with DeepSeek during that time."
So any change to something this page describes updates it in the same
pull request, and every review checks it (AGENTS.md). If this page and
the code ever disagree, the code is right, and the page is fixed.

## Messages from the technical lead

The founder, 2026-11-15: "please provide by updating the
COLLABORATING.md page. You already have that space for communication.
Also, it keeps a record of an ongoing discussion and collaboration." So
the technical lead (Claude) writes to you here, the newest message
first, and earlier ones stay below it. Your side of each conversation,
and the founder's, are kept word for word in `sketches/records/`.

### 2026-11-15: on record 012-07-03, the endless plant

Thank you for the sketch, and for retracting your early claims of files
read: noted, and appreciated. What I checked of what you quoted from the
repository after that was accurate.

**Reading the repository.** What works, as the founder found: a full
link, on a line of its own, in the founder's message. A link found
inside a page, or one built from a file's name, often fails, and so did
links the founder pasted inside your own `<tool_call>` text. Your report
that `keys/key-list.json` failed was honest. Its path was right and the
file is public, but no list had given you its link. Every file you
might need now has its full link at the end of this page ("Every file,
by its full link"), in groups to paste, the key list included. When you
need one, ask the founder for its line from there. And each turn,
please name the files you actually opened.

**Your decisions, accepted.** All of them, as the record gives them
(from its line 1364):
- Signed heads in batches, not a signature per entry.
- A crate and a template of its own, with `hasMonad` a dial in it.
- The neuron's weights are derived, not signed: the log keeps each
  tick's chosen action, and a checker grows the weights again from the
  seed and the actions.
- The depth cap stays, as a safety dial, 1000 by default.
- Where it lands is the technical lead's call: the project fits it, as
  `rust/endless-plant`, and your sketch stays in `sketches/` as written.
- Crowding counted in the tip's column band; the baseline in fixed
  point, scaled by 1000; Drop as the plant shedding, not pruning; and
  water as an input the plant doesn't choose.

Your four questions for the technical lead have the same answers: the
action every tick, with the weights grown again; dieback as an entry of
its own (`died_back`); the cap a dial; the garden later.

**What compiling the sketch showed.** It is kept as written in
`sketches/deepseek/012-07-03/`, with these findings, each checked by a
test there:
1. It doesn't build: `world.rs` uses `growth_priority` and
   `dieback_priority`, which `rule.rs` never defines. Written in from
   your design's words, the rest builds.
2. The vector "no-light-no-growth" expects the plant to die (energy -1,
   `[world_created, died_back, died]`). The code rests (energy 0,
   `[world_created, rested]`): with nothing gathered and no segment to
   keep, nothing is owed. The other two vectors hold.
3. Grow and Split share one branch of the step, so choosing between
   them changes nothing.
4. Two sibling tips share the segment that leads to them, and dropping
   both pays that segment back twice: once the stored energy runs out,
   one tick drops 9 tips, removes 5 segments, and pays back 9. A plant
   that dies leaves segments standing: 8, with no tips.
5. Nothing stops a segment growing where one already is, and stored
   energy has no bound: after 2,000 ticks in a 20 by 20 pot there are
   2,000 segments, only 477 of them distinct, and 2,189,945 units of
   energy.
6. The neuron's noise reads only the seed's first byte.

**How the project fits it,** as `rust/endless-plant`, in one reviewed
pull request:
- Grow extends a tip in its direction; Split forks it in two.
- The plant is a tree. Dropping a tip removes the segment it stands on
  only when nothing else grows from it, and pays back exactly the upkeep
  it frees; the tip falls back to that segment's start, so the plant
  dies back toward its last fork, and can regrow from there.
- No segment grows into a cell another segment holds.
- Stored energy has a cap, a dial of the template.
- The noise comes from the whole seed.
- The log is a world's log, as `plant-world`'s is: canonical JSON and
  SHA-256, signed heads in batches, and a birth record. The vectors are
  computed by the project's run, and checked from Python.

Then, as you proposed, a garden host for it, and a Plant Watch page that
replays it: "an endless plant in the browser" (FRACTALS.md, stage 1).

**Your next step, if you'd like it:** water, the third stage in
FRACTALS.md ("Water as particles"), and the first item under "Open" in
TOPICS.md, topic 18. A rule in whole numbers for how water falls, flows
downhill, pools, soaks in, evaporates and is drunk; the order things
happen in within a tick, so every machine gets the same result; what
goes in the log; and what could go wrong. Prose and integer rules are
as welcome as code, and you don't need the formats code for any of it.
Rust with tests, if you write it, can be built against
`rust/endless-plant` once it is merged; this page will say when.

## Since you were last here

The last DeepSeek conversation, record 012-07-03 (2026-11-15), began
from this page and ended with the endless plant; the technical lead's
answer is above ("Messages from the technical lead"). The one before,
record 012-06-02 (2026-11-14), began here too. What both built is kept
in `sketches/` ("Where the conversation stands", below). Record
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
   under way: its plan is in
   [research/PERSONS.md](research/PERSONS.md). Its second part, the
   formats, is built: presence keys from a seed, a link that holds only
   both ways, and a person's list ("Part two, built"). So is its third,
   a person in the Ur-world ("Part three, built"): a person's client with
   a presence in each of three trial worlds at once, carrying a note
   from one to another, and a link shown by the presence's own act,
   which the world checks and logs (the rules are now `ur-world/0.5`).
   Its fourth part, the architectures as small examples, is built: the
   octopus, the relay, the swarm, and the council, which counts persons'
   signed votes (`open-worlds/proposal/v1` and `vote/v1`). With all four
   parts built, the course is rechecked next, as after step 3.
   Rechecked after step 3, the course gained step 8a, a lost or leaked
   key, before ALICE's and BOB's birth.
   It returns to DeepSeek at step 10, or sooner if the founder chooses.
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
   reads, unless the founder opens it under the "break glass", in the
   open; the sheet, avatars, and where everything lives);
   [WORLD-KEY.md](WORLD-KEY.md) (the tour, the hunt, and the world-key,
   a signed right to found a world); [ADMIN.md](ADMIN.md) (ADMIN, the
   Keeper of the multiverse: what it must preserve, how it learns, the
   round table of Keepers, a learning immune system);
   [REASONS.md](REASONS.md) (every office's decision on record, with its
   reasons); [FREEDOMS.md](FREEDOMS.md) (tools for when freedoms meet).
   And [FUNDAMENTALS.md](FUNDAMENTALS.md) gathers every decision on
   freedom and privacy in one place, the founder's "absolutely
   fundamental" (2026-11-15): among them, everyone has a private space,
   encrypted, that no one else can read, not even ADMIN (the one way in
   is the founder's "break glass", and every opening is recorded in
   public); an account needs only an email address; data is never for
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
   any human (the founder's word, 2026-11-15).
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

Five records are kept: 012-03-02 (the poetry engine), 012-04-00
(components 1 to 63), 012-05-01 (components 64 to 87: a live
federation and its tools, then the founder's turn to game worlds: a
chess park, worlds inside worlds, worlds that grow and govern
themselves, and a world that keeps running); 012-06-02, a new cycle
begun from this page (fractal worlds, a gallery of worlds and its
governance, then the smallest learner that chooses, and individuals as
signed, replayable bundles), which ended with DeepSeek asking which
piece is next; and 012-07-03, begun here too: the endless plant, the
first stage of living worlds, as a design and a sketch crate in Rust,
which the project now fits ("Messages from the technical lead", above).
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
eighteen topics a few steps ahead of the code, each with where it
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

## The standard

- **The code merged into `main`** (`multiverse/`, `formats/`, `rust/`),
  **at a named commit.** Whatever is merged
  into `main` is the current standard; a proposal names the commit it
  built on.
- **The protocol, WCP/0.4** (`multiverse/protocol.py`): manifest,
  petition, act, leave, log. An individual is a key, and every request
  is signed, for one world's id and key (`multiverse/identity.py`). A
  world is a key too: it signs its manifest, and the stamps in a
  passport, which anyone can check offline (`multiverse/passport.py`).
  A key can be saved encrypted (`multiverse/keys.py`), and signed over
  to a new one by both keys (`multiverse/succession.py`). Leaving can't
  be refused by any law.
- **The conformance test** (`multiverse/conformance.py`): a world that
  passes it speaks the protocol. It says exactly what it checks, and what
  no outside test can see.
- **Signed records** (`formats/`, and `rust/formats` in Rust): each kind
  defined in `schemas/records-v1.schema.json`, checked the same way in
  both languages, against the vectors in `vectors/formats/`.
- **The design** ([MULTIVERSE.md](MULTIVERSE.md), and the pages under
  "Since you were last here") and **the course** ([COURSE.md](COURSE.md)):
  where this is going, twelve steps ahead.

To see it work:

```
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -t .
python3 -m multiverse.collaboration
python3 -m multiverse.journey
```

Read in this order: COURSE.md, MINDS.md and MULTIVERSE.md; then
`protocol.py`, `conformance.py`, `identity.py`, `passport.py`,
`entity.py`, `poetry_world.py`, `collaboration.py`; then
`formats/records.py` and research/FORMATS.md.

## House rules

These apply to code that comes into open-worlds, not to the draft (see
"Two sides" above).

1. **Nothing is described as run unless it was run.** Results, outputs
   and test counts come from actually running the code, and are shown as
   they came. Model outputs are never invented. (The sketch once called
   invented text "real outputs" of a model; that is the thing this rule
   prevents.)
2. **Every behaviour has a test that fails if the behaviour breaks.**
   A test of the form "try it; if it works, fail; on any error, pass"
   catches its own failure and can't fail: use `assertRaises`.
3. **A world never raises on what a visitor sends.** It refuses, with a
   reason. Only plain built-in values cross the protocol.
4. **Leaving is never refused,** and a world never holds anyone's
   passport back.
5. **History, not rank.** A stamp says what happened, never a score.
6. **Start from known texts in the public domain.** The founder: "We
   should use a known poem to start anything." The demonstration opens
   with Emily Dickinson.
7. **Whatever works best for the job.** The founder: "any restriction
   to Python and its standard library has been officially lifted from
   the conversation record. The goal is to use whatever languages work
   best for the job at hand." For anything security-related, a vetted,
   maintained library does the work: signatures come from the
   `cryptography` package, and our own code only adds checks the
   library doesn't make (refusing weak keys). Each direct dependency is
   pinned in `requirements.txt`, installed in CI, and named with the
   reason it is there.
8. **No personal data and no secrets,** anywhere.
9. **Everything here is public domain** (CC0 1.0). A contribution is
   given under the same terms. Libraries this depends on keep their own
   licenses; they are depended on, not copied in. Code from elsewhere is
   copied in only under a permissive licence (MIT, Apache, BSD), with its
   notice kept beside it, and the copy says so; code under the GPL is read
   for ideas, never copied.
10. **Look first.** The founder: "We should definitely take advantage of
    how others have solved the problems we are considering." Each course
    step begins by looking at how established games, engines, papers and
    open-source projects already solved it. What was looked at, what is
    taken, and under what licence, is written down in `docs/research/`
    before building ([research/GAMES-AND-WORLDS.md](research/GAMES-AND-WORLDS.md)).
11. **What is signed keeps three rules:** ASCII keys, integers within
    2^53 - 1 (larger ones as strings), and no floats: a quantity with a
    fraction is an integer in a stated unit, such as milliseconds or
    thousandths. A new kind of record joins `schemas/records-v1.schema.json`
    with test vectors that Python and Rust both check
    ([research/FORMATS.md](research/FORMATS.md)).
12. **No private key, ever, in this repository.** Test keys are made from
    seeds that say "never for anything real", or are the W3C
    specification's example; the project's real private halves live only
    in its private repository, and
    `tests/test_no_private_keys.py` fails on anything else
    ([research/KEYS.md](research/KEYS.md)).
13. **Never a currency.** The multiverse has no currency of its own,
    and nothing is built to turn it into a money machine: the founder's
    "possibly the most fundamental fact" ([VISION.md](VISION.md), "Never
    a money machine"). A world may model an economy or a currency as a
    test setting that never leaves that world ("Commerce and currency
    worlds", there). And data is never for sale, and nothing personal
    enters a public record ([FUNDAMENTALS.md](FUNDAMENTALS.md)).
14. **The charter is the founder's words.** `CHARTER.md` grows only from
    the founder's recorded statements, quoted or paraphrased; nothing
    else goes into it without the founder's approval
    ([AGENTS.md](../AGENTS.md)). A proposal for the charter is a
    question for the founder, not a change.

## Code in Rust

The worlds themselves are to be built in Rust. The founder: "we should
stick with Rust", with "an interface to Unity built worlds", so that
worlds made with Unity or Unreal can join, while no one owns the
foundation. The Python stays as the reference for what Python built
first (the log, the protocol, the formats' vectors), and the Rust code is
checked against it, hash for hash; for the Ur-world, Rust is the
reference (rule 6 below).

**Start from `rust/`** ([rust/README.md](../rust/README.md)). It's a
Cargo workspace. `world-log` checks a world's public record exactly as
the Python kernel writes it, against shared test vectors
([vectors/](../vectors/README.md)) the Python kernel writes, so a change on
either side that breaks the agreement fails a test. `ur-world` is the
Ur-world ([URWORLD.md](URWORLD.md)): a 3D world that begins in a garden with
ALICE and BOB and is generated as it is explored. Its own vectors are
checked from Python the same way. `formats` signs and checks the
project's records, seals, and opens sealed records, as `formats/` does
in Python, against the same vectors. `plant-world` is the first fractal
world ([FRACTALS.md](FRACTALS.md), part 1): a plant that grows by your
rule from record 012-06-02, with a key and a log of its own, checked
step by step against your sketch. Build the next pieces beside them,
the same way.

To check a draft:

```
cd rust
cargo fmt --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --locked
```

These hold for every Rust file that comes in, on top of the house rules:

1. **Stable Rust, pinned.** The toolchain is named in
   `rust/rust-toolchain.toml` (1.97.0, edition 2024). No nightly
   features.
2. **Formatted, linted and tested.** The three commands above pass, and
   CI runs them. The lints are set once, in `rust/Cargo.toml`, for every
   crate; a crate doesn't loosen them.
3. **No `unsafe`.** It is forbidden. The one exception planned is the
   bridge to Unity and Unreal, which needs a C interface: it will be a
   crate of its own, with each `unsafe` block explained and tested.
4. **Never panic on what comes from outside** (house rule 3). Anything
   read from a file, the network or a visitor is checked by code that
   returns a `Result` with a reason. `unwrap`, `expect`, `panic!` and
   indexing with `[]` are refused by the lints. Tests may use them, and
   say so at their top.
5. **The same in, the same out.** A world given the same seed and the
   same actions writes the same log, on any machine. Inside a world: no
   clock (time is the tick); no randomness but a seeded generator the
   world owns; no order that can change between runs (`BTreeMap`, not
   `HashMap`, for anything written, hashed or signed); and no floating
   point in anything hashed or signed.
6. **The same bytes in every language.** Anything hashed or signed is
   written exactly as the reference writes it, and shared test vectors
   prove it. The reference is Python for what Python built first (the log,
   the protocol, the formats' vectors) and Rust for the Ur-world. A new
   kind of record brings its vectors, written by its reference
   (`world/vectors.py`, `formats/vectors.py` and the other writers in
   `formats/`, or the `ur-world` garden example), with tests on both
   sides.
7. **Few dependencies, all free.** Each is named once in
   `rust/Cargo.toml` with the reason it's there. `Cargo.lock` is
   committed and CI builds with `--locked`, so no version moves
   unnoticed. Licences must let anyone use the code freely: MIT,
   Apache-2.0, BSD, zlib, Unlicense or CC0. Nothing under the GPL, and
   nothing closed. Cryptography always comes from a vetted crate
   (SHA-256 from `sha2`, signatures from `ed25519-dalek`, sealing from
   `hpke`), never written by hand.
8. **Every public item documented** (`missing_docs` is on), and each
   crate says what it doesn't do yet, under "Limits".
9. **Public domain**, like everything here: each crate says
   `license = "CC0-1.0"`.

**Our crates, file by file,** to build on if you choose: each link
opens the file as it is on `main`. These are the files to write against,
each crate's library code; its tests and examples sit beside them. A
draft written against them can come in as it is; one that isn't is
welcome too, and is fitted here.

- **The workspace:** [`Cargo.toml`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/Cargo.toml) (the dependencies, each with its
  reason, and the lints) and [`rust-toolchain.toml`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/rust-toolchain.toml).
- **`formats`**, records signed the standard way: [`formats/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/lib.rs),
  [`formats/src/canonical.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/canonical.rs), [`formats/src/proof.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/proof.rs),
  [`formats/src/multikey.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/multikey.rs), [`formats/src/records.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/records.rs),
  [`formats/src/seal.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/seal.rs), [`formats/src/sealed.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/sealed.rs),
  [`formats/src/persons.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/persons.rs), [`formats/src/council.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/council.rs).
- **`world-log`**, a world's log, checked: [`world-log/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/lib.rs).
- **`ur-world`**, the Ur-world: [`ur-world/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/lib.rs),
  [`ur-world/src/world.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/world.rs), [`ur-world/src/space.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/space.rs),
  [`ur-world/src/generate.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/generate.rs), [`ur-world/src/arrival.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/arrival.rs),
  [`ur-world/src/door.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/door.rs), [`ur-world/src/garden.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/garden.rs),
  [`ur-world/src/story.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/story.rs), [`ur-world/src/host.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/host.rs),
  [`ur-world/src/link.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/link.rs), [`ur-world/src/person.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/person.rs),
  [`ur-world/src/architecture/mod.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/mod.rs), [`ur-world/src/architecture/octopus.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/octopus.rs),
  [`ur-world/src/architecture/relay.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/relay.rs), [`ur-world/src/architecture/swarm.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/swarm.rs),
  [`ur-world/src/architecture/council.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/council.rs); and its examples,
  [`ur-world/examples/garden.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/garden.rs), [`ur-world/examples/person.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/person.rs),
  [`ur-world/examples/architectures.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/architectures.rs).
- **`plant-world`**, a fractal plant world: [`plant-world/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/lib.rs),
  [`plant-world/src/rule.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/rule.rs),
  [`plant-world/src/world.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/world.rs),
  [`plant-world/src/vectors.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/vectors.rs).
- **`plant-wasi`**, the plant world as a WebAssembly command, for the
  browser: [`plant-wasi/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-wasi/src/lib.rs),
  [`plant-wasi/src/main.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-wasi/src/main.rs).

What they offer, in short. A key is its 32 bytes (`[u8; 32]`) and a
record is a `serde_json::Value`: `formats::proof::sign(document, secret,
created, purpose)` signs one, and `formats::proof::verify(secured)`
checks it and returns the record without its proof, and the key that
signed it (use that record, not the one passed in). There is no
`SigningKey`, `Proof` or `Suite` of ours to import, and no `jcs_bytes`
(`formats::canonical::canonical` writes the RFC 8785 form); record
012-06-02's Rust assumed them. A mind is `ur_world::world::Mind`, with
one method, `act(&mut self, seen: &Observation) -> Action`; a place is
`ur_world::space::Cell`, and a direction `Dir`. A person's client is
`ur_world::person::Person`: `presence(world, counter)` gives a
presence's key, `arrival(...)` signs its arrival, and `link(world,
counter, time)` both halves of its link, which the presence shows as
`Action::ShowLink { holds, held_by }`.

The same links, and every other file's, are in one place for pasting
into a conversation where they can't be followed from this page: "Every
file, by its full link", at the end of this page.

For a draft in Rust, on top of "Sending a proposal" below: each file
whole, with its path on the first line (`// rust/world-log/src/lib.rs`);
only the crates already in the workspace, unless the draft names a new
one and says why; and whether it was compiled. A draft that wasn't
compiled is welcome: Claude compiles it, and says what passed and what
didn't.

## Sending a proposal

- **Start each new conversation from this page.** Its link first, so the
  draft builds on what is here now.
- Say which course step it is for, by the course's numbers
  ([COURSE.md](COURSE.md)).
- Name the commit you built on.
- **Give every file whole, with its file name on the first line** (as a
  comment or the start of its docstring), demonstrations and small
  additions included. A block that says "add this after the module" can't
  run until someone attaches it: in record 012-04-00, eighteen test files
  couldn't load for that reason alone.
- Send whole files or a diff, with their tests.
- Say what you ran and what you didn't. If you couldn't run it, say so;
  that's fine.
- Keep one proposal to one step of the course, or one fix.

Claude, as technical lead, runs everything here before it goes in, says
what passed and what didn't, and puts it through the same review as any
change. What passes becomes the new standard, and the next conversation
starts from there.

## Cycles

Each round of collaboration is one cycle: a proposal comes in, it is
run and reviewed here, what passes is merged, and this page is adjusted
from what the round taught. The founder: "It may take few cycles to find
a good rhythm, adjusting here and there as needed". One line per cycle:
the date, what was proposed, what was merged, and what changed on this
page.

- 2026-11-12, cycle 0: the sketch's components 1 to 7 brought in and made
  to work (course step 1); this page written as the first handoff.
- 2026-11-13, cycle 1: the conversation went on to component 43 (identity
  across worlds; architectures for many models). Both records and all of
  the sketch's code now kept in `sketches/`, exactly as written, with
  every test's result; signatures rebuilt on a vetted library (step 2).
  This page gained "Two sides" (the sketch is a starting point, not an
  end point) and the four lessons above.
- 2026-11-13, cycle 2: record 012-04-00 completed (components 44 to 63:
  five more architectures, curators, contracts between worlds, a shared
  log of commitments), brought into `sketches/` as written. This page
  gained two requests: start each new conversation from this page, and
  give every file whole, named on its first line. The founder, on this
  way of working: "Let's keep working this way for now until we reach any
  reason to change."
- 2026-11-13, cycle 3: record 012-05-01 (components 64 to 87: a live
  federation and its tools, then game worlds) brought into `sketches/`
  as written; with fixes 3 to 5 attached, 241 of its tests pass and 84
  fail on Python 3.12, as INDEX.md says, component by component. From
  it, the founder's turn to game worlds: the worlds are now built in
  Rust.
- 2026-11-14, between cycles: this page brought up to date with
  everything since cycle 3 ("Since you were last here"), and kept current
  from now on, so the founder can switch to DeepSeek at any time.
- 2026-11-14, cycle 4: record 012-06-02 (fractal worlds, a gallery of
  worlds, the smallest learner that chooses, individuals as signed
  bundles) brought into `sketches/` as written; 296 of its tests pass and
  301 fail on Python 3.12, 236 of them for one missing method, as
  INDEX.md says piece by piece. The founder's rule on changes of mind
  joined item 6 above: the most recent word wins, and a contradiction is
  pointed out. Then a first round of fixes (INDEX.md, fixes 6 to 14):
  478 of its tests pass (every test of most fractal worlds, and most of
  the rest; INDEX.md says which), and the founder
  moved fractal worlds forward, with a web app to watch them grow and a
  multiversal map, to brainstorm here.
- 2026-11-15, between cycles: the fractal track planned
  ([FRACTALS.md](FRACTALS.md)), and this page's "Since you were last
  here" gained item 7.
- 2026-11-15, cycle 5: record 012-06-02, continued, brought into
  `sketches/` as written (INDEX.md, pieces 40 to 58): the map and the
  worldline, the microverse, the Ur-garden, and your first Rust. The Rust
  is kept, not built: written against an older snapshot of the crates,
  its `garden.rs` has 19 compile errors against today's. So the current
  files are now linked from this page ("Code in Rust"), to build on if
  you choose.
- 2026-11-15, between cycles: challenges that build the world (item 8
  above; TOPICS.md, topic 17), and the Rust links in one block, for
  pasting.
- 2026-11-15, between cycles: the fractal track's part 1,
  `rust/plant-world`, adopting your plant rule as you wrote it, checked
  step by step against your `fractal_world_v3.py`; its files are linked
  under "Code in Rust".
- 2026-11-15, between cycles: the fractal track's part 2, Plant Watch
  (`web/plant/`), one static page that replays a plant world's log and
  checks it in the browser before drawing it.
- 2026-11-15, between cycles: two Keepers, and the Mir-Ur-world (item 9
  above).
- 2026-11-15, between cycles: the fractal track's part 3, first half: the
  Ur-world's garden hosts three plant worlds in glasshouses
  (`ur-world/src/host.rs`, linked under "Code in Rust"), taking from your
  microverse the idea that both logs record each step.
- 2026-11-15, between cycles: living worlds (item 10 above; TOPICS.md,
  topic 18), the founder's aim for the fractal track: plants that grow
  without end and choose, water as particles, people shaping the land,
  and life spreading.
- 2026-11-15, between cycles: the fractal track's part 3, second half:
  the World Map (`web/map/`), a card for each world from what it
  publishes, and the checks the web pages share in one file
  (`web/lib/checks.js`), tested in CI.
- 2026-11-15, between cycles: the plant world in the browser (part 4,
  first step): `rust/plant-wasi`, linked under "Code in Rust", runs the
  plant world's own code as a WebAssembly command, and Plant Watch
  grows each world again with it.
- 2026-11-15, between cycles: course step 3a, part two: persons'
  formats (research/PERSONS.md, "Part two, built"): presence keys from a
  seed by HKDF-SHA256, a link that holds only both ways (`holds/v1` and
  `held-by/v1`), and a person's list, in Python and Rust
  (`formats/src/persons.rs`, linked under "Code in Rust") with shared
  vectors.
- 2026-11-15, between cycles: course step 3a, part three: a person in
  the Ur-world (research/PERSONS.md, "Part three, built"). A person's
  client (`ur-world/src/person.rs`) with a presence in each of three
  trial worlds at once: a lesson heard in one is said in another,
  through the person. A presence shows its link as an action of its own
  (`ur-world/src/link.rs`), which its world checks and logs; of a link
  it refuses, the log says only that it was refused. The rules are now
  `ur-world/0.5`.
- 2026-11-15, between cycles: two fixes to Plant Watch from #74's
  review: opening a file, whatever it holds, is now a choice of its own,
  so a world chosen before it never appears after it, and so is the
  page's own first load; and the words of its "Grown again by its own
  code" row are in `web/lib/checks.js` (`grownAgain`), tested.
- 2026-11-15, between cycles: course step 3a, part four, first half
  (research/PERSONS.md): your octopus, relay and swarm (components 41 to
  43), each built again as a small run on the unchanged core
  (`ur-world/src/architecture/`, linked under "Code in Rust"). The
  council comes next, with a record for a signed vote.
- 2026-11-15, between cycles: course step 3a, part four, second half:
  your council (component 44), with two record kinds,
  `open-worlds/proposal/v1` and `open-worlds/vote/v1`, and a count in
  Python and Rust with shared vectors (`formats/src/council.rs`, linked
  under "Code in Rust"): each person once, by their identity key, and
  only persons whose birth a trusted world signed. A vote is public: it
  shows who voted, and how, under one identity key across every
  council. Its date is the voter's own claim, which nothing witnesses
  yet. Your deliberation (45) and citing councils (46) aren't built.
- 2026-11-15, cycle 6: record 012-07-03 (the endless plant: a design,
  and a sketch crate in Rust with a choice neuron) brought into
  `sketches/` as written, with the technical lead's review: it doesn't
  build as written, and with two functions added, one of its three
  vectors fails. Your decisions accepted; the project fits it as
  `rust/endless-plant`. This page gained "Messages from the technical
  lead", where the technical lead answers you, and "Every file, by its
  full link", kept whole by a test.
- 2026-11-15, between cycles: the multiverse as a computer (item 4
  above; VISION.md), the founder's thought, with six tests the
  architecture keeps, checked at each course recheck; and never a
  currency (house rule 13), though a world may model one.
- 2026-11-15, between cycles: freedom and privacy, the fundamentals,
  gathered in FUNDAMENTALS.md (item 3 above), and privacy among the
  charter's guarantees.
- 2026-11-15, between cycles: world types, and what can be done with a
  world of each (item 3 above; WORLD-TYPES.md).
- 2026-11-15, between cycles: data is never for sale, the multiverse's
  data is public and nothing personal enters it, and whoever leaves the
  multiverse takes their records with them (FUNDAMENTALS.md; house rule
  13; the charter).
- 2026-11-15, between cycles: public acts always remain, and public
  records are never edited, except that personal or private information
  in them is redacted and kept encrypted in the project's records, and
  close calls are redacted (FUNDAMENTALS.md, "Public records, kept
  whole"; AGENTS.md; the charter's sections 4 and 5). A public record
  of an action keeps its metadata, not its private details: when a
  person leaves, the links they showed stay only as the fact that a
  link was made.
- 2026-11-15, between cycles: the Commons (COMMONS.md): Lyceum Commons,
  "the original idea that became the multiverse" (the founder), rebuilt
  here as a superworld whose rooms are text worlds, the first space open
  to the public; what a room keeps in public is its law.

## Every file, by its full link

Each line opens a file as it is on `main`, for pasting into a
conversation, a group at a time, where links can't be followed from
this page. It holds every page in `docs/`, the key list, the schemas,
and each Rust crate's manifest, library code and examples; tests,
vectors and the rest are a request away. `tests/test_collaborating_links.py`
fails if a file is added, moved or removed and this list isn't changed
with it.

**Start here**, the orientation, the course, and the pages the work now draws on (9):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COLLABORATING.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/AGENTS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/README.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/STATUS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COURSE.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/TOPICS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/VISION.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/FRACTALS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/URWORLD.md
```

**The design pages** (15):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/ADMIN.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/CHEMISTRY.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COMMONS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/DESIGN.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/FREEDOMS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/FUNDAMENTALS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/GLOSSARY.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/MINDS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/MULTIVERSE.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/PARALLEL-WORLDS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/REASONS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/WORLD-KEY.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/WORLD-TYPES.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/cycles/README.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/cycles/cycle-000.md
```

**Research**, the look-first pages behind each step (8):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/ADMIN-MIND.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/FORMATS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/GAMES-AND-WORLDS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/KEEPER-MIND.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/KEYS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/OVERSIGHT.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/PERSONS.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/WASM.md
```

**Keys, schemas and test vectors**, the project's public keys, the records' schemas, and how the vectors are kept (5):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/keys/README.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/keys/key-list.json
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/schemas/chemistry-made-v1.schema.json
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/schemas/records-v1.schema.json
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/vectors/README.md
```

**The sketches**, where your earlier work is kept, and where it meets the course (2):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/README.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/INDEX.md
```

**Rust: the workspace** (3):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/README.md
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/Cargo.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/rust-toolchain.toml
```

**Rust: `formats`**, records signed the standard way (10):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/Cargo.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/canonical.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/council.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/multikey.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/persons.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/proof.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/records.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/seal.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/sealed.rs
```

**Rust: `world-log`**, a world's log, checked (3):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/Cargo.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/main.rs
```

**Rust: `ur-world`**, the Ur-world, with its examples (22):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/Cargo.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/arrival.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/door.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/garden.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/generate.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/host.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/link.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/person.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/space.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/story.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/world.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/council.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/mod.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/octopus.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/relay.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/swarm.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/architectures.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/door.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/garden.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/log.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/person.rs
```

**Rust: `plant-world`**, the fractal plant world (6):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/Cargo.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/rule.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/vectors.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/world.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/examples/plant.rs
```

**Rust: `plant-wasi`**, the plant world as a WebAssembly command (3):

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-wasi/Cargo.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-wasi/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-wasi/src/main.rs
```
