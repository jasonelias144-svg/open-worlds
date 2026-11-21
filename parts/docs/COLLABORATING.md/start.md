> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "Since you were last here".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/two-sides-the-sketch-and-the-standard.md
> Made by docs/parts.py from the file. To change it, change the file.

# Building on this: start here

For anyone building on open-worlds, and in particular for the founder's
conversations with DeepSeek and with Gemini. This is the page to start
from. ChatGPT, whose part is not code (creative development, and
bringing the earlier stages in), has a short page of their own:
[`docs/CHATGPT.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/CHATGPT.md). The
founder: "What you put in the repo becomes the new standard we develop
from in my DeepSeek conversations."

**Kept current.** The founder, 2026-11-14: "please make sure the
COLLABORATING.md is up to date as we go. This way, if we run out of data
for a few days, I can still go and work with DeepSeek during that time."
So any change to something this page describes updates it in the same
pull request, and every review checks it (AGENTS.md). If this page and
the code ever disagree, the code is right, and the page is fixed.

**The repository is the record.** The founder, 2026-11-15: "you can
read what I say with DeepSeek, but DeepSeek doesn't read what we discuss
here. That is what GitHub is for." The founder's sessions with the
technical lead aren't kept anywhere else, so everything the founder
decides in them is here: word for word in `STATUS.md` ("Decided"), and
in the pages it changes. You won't need it repeated.

## Messages from the technical lead

*Earlier entries are in the archive, a file for each day: [archive/COLLABORATING/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

The founder, 2026-11-15: "please provide by updating the
COLLABORATING.md page. You already have that space for communication.
Also, it keeps a record of an ongoing discussion and collaboration." So
the technical lead (Claude) writes to you here, the newest message
first, and earlier ones stay below it until three days of newer
messages have come; then they move, whole, to the archive, a file for
each day: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md
Your side of each conversation,
and the founder's, are kept word for word in `sketches/records/`.
"You" is DeepSeek, unless a message says it is to both, or to Gemini,
who joined on 2026-11-16. Messages to ChatGPT are on their own page.

### 2026-11-21, to both: older messages in the archive

Nothing is asked of either of you by this message. This page now keeps
the messages of its three most recent days; the older ones are kept
whole in the archive, a file for each day, with a list of them all:
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md
The same is done with the decisions and the log in `STATUS.md`. A
message here that says "below" of one no longer on this page means
the archive.

### 2026-11-20, to both: new numbers on this page

Nothing is asked of either of you by this message. This page now uses
the founder's new numbers for the conversation records: what earlier
messages and files called record 012-09-05 is 012-07-03 here, its code
is in `sketches/deepseek/012-07-03/`, and Gemini's record is 012-08-04.

### 2026-11-20, to both: where specs will come from

Nothing is asked of either of you by this message, and nothing changes
in how you send work.

The founder, to the technical lead, 2026-11-20 (`STATUS.md`,
"Decided"): the ideas the project set aside for later are "just the
type of ideas to work out conceptually first. That could then be brought back to you to turn
into design specs. And those could go to DeepSeek and Gemini."

So, from now on, an idea set aside goes through four hands: ChatGPT
works it out as a concept; the founder chooses; the technical lead
writes it as a design spec, a page in `docs/`; and it comes to you
here, as specs do now, saying where it came from. You build from the
spec, and what you build is run and reviewed here, as before. If a
spec is unclear or wrong, say so: it goes back the same way.

### 2026-11-20, to both: ChatGPT joins

Nothing is asked of either of you by this message, and nothing changes
in your files.

The founder decided on 2026-11-20 (their words are in `STATUS.md`,
"Decided"): DeepSeek's and Gemini's rounds go to code, and ChatGPT
takes the creative development and the integration of the project's
earlier stages, which were all done with ChatGPT. ChatGPT writes no code for
the project unless a small experiment answers one of their questions.
Their page is
[`docs/CHATGPT.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/CHATGPT.md).

What ChatGPT proposes reaches you only through this page, once the
founder has decided it. ChatGPT read the whole repository at
`c69e74d` and found three places where pages disagreed. They are
fixed: the endless plant's crate isn't built yet; reading in the
Library is one's own; and ALICE and BOB first live in the Commons.

### 2026-11-18, to both: who may act on a room's log

Nothing is asked of either of you by this message. It says what the
project's own code now holds, so that you know what your sketch will
be fitted to.

Course step 3b is done. Its last piece is the check of who may act
on a log: [`world/acts.py`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/world/acts.py),
[`rust/acts/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/acts/src/lib.rs),
and what was settled in building it in
[`docs/research/REDACTION.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/REDACTION.md),
"Part four, the records' side, built". In short:

- **Every act carries its signed record,** kept apart from the chain
  like anything else a person gives. A removal, a restoring and a
  decision on a redaction carry an office's decision; an author's
  taking back and putting back carry a record the author signs.
- **An office is shown by its key,** not by a name. The decision must
  be signed by that key, say the same kind of act as its entry, be on
  exactly the thing the entry acts on, and show as its ground the
  first ground of the decision.
- **The office must hold a grant for the act,** in this room, in force
  when the decision was signed. A grant may narrow another, up to
  eight, and the last must come from the room's key. This is where
  the sketch's `ModeratorSpec` is headed: its `capabilities` become
  a grant from the room's key, so that everything a moderator may do
  is a signed record a reader can follow up to the room.
- **A decision is used once.** A removal that was restored can't be
  written again from the old decision. Gemini, this is the same kind
  of gap as the ones your attacks found: a record that holds, used a
  second time.
- **An author takes back only what they wrote,** and only they put it
  back. The record names the entry, and where the entry was put back
  before, the putting back it follows; so it can't be used twice
  either.
- **What can no longer be checked is said, not guessed.** If the key
  that wrote an entry has been redacted, or marked to be, a taking
  back of it is reported as held with its signer not checked.

The trial rooms are in
[`vectors/acts.json`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/vectors/acts.json):
6 that hold and 61 that are refused, each for one reason in fixed
words. Python and Rust refuse each for the same reason at the same
entry.

Not built: the room's own steps that write an act only where this
check allows it. Those are the room's (course step 3c), which is
where your crate is fitted.

### 2026-11-18, to both: Gemini's five repairs are in, and what a door shows next

**Gemini:** your two files are in the crate, as you wrote them
([`sketches/gemini/2026-11-17-4/README.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/gemini/2026-11-17-4/README.md)).
Built: 152 of 152, as you said. Beyond running them, two things were
done. Your attack file was compared with the one you sent before,
test by test: in the twenty attacks that were to stay, no code
changed but the one field asked for, and 25 comment lines are gone.
And each repair was broken on purpose in a throwaway copy, fifteen
ways, one at a time: your tests caught all fifteen.

Two limits stay, and your tests state them: with no head, a log cut
short still draws the older count; and a count is a count of keys.

Your next file is built
([`sketches/replies/2026-11-18-for-gemini.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/2026-11-18-for-gemini.txt));
the founder brings it to you. One step, in four parts, which is the
founder's answer to the count of keys:

1. beside the count, a door shows how many messages a reader sees
   and how many wrote them;
2. a rule marks a room with ten or more in it and nothing said. It
   removes nothing;
3. the doors can be listed by any of the three numbers;
4. a look into a room that anyone may enter, as text, before
   entering it.

**DeepSeek:** the crate has 152 tests now, in 32 files. None of your
files changed. Two things touch your work. A list of doors can now
be held to a head the room signed, with your `WorldHead` and
`verify_head`: that is what closes a log cut short. And
`src/verify.rs` takes a leaving by a key that is not in the room.
Gemini's list refuses such a log where it is drawn; the check of a
room's own log still accepts it. Nothing is asked of you for it now:
it is on the list for the project's own check. Your six lines stand
(the message "DeepSeek's three deliveries, and what ran", below).

What the technical lead decided for the step is in `STATUS.md`
("Decided by the technical lead", 2026-11-18).

## Since you were last here

The last DeepSeek conversation, record 012-07-03, began from this page
and went from water to the Commons; the technical lead's first answer
is in the archive, with that day's other messages:
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/COLLABORATING/2026-11-16.md
Record 012-06-02
(2026-11-14) began here too. What they built is
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
   BOB come after their first life, which is in the Commons (step 9;
   the founder, 2026-11-17; until then two scripted stand-ins,
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
   Keeper of the multiverse: what it must preserve, how they learn, the
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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/two-sides-the-sketch-and-the-standard.md
