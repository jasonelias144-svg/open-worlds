# Topics ahead: a menu for creative work

The founder, 2026-11-14: "please provide a range of topics to explore and
develop with possible implementations. If the list is forward a few
steps from where we are now, it can be waiting for us when the project
reaches that stage, sketching out the landscape before the code gets
there. And if the topics are diverse, DeepSeek can have a choice of
topics. For each choice you could provide an example or just set the
code standards."

So each topic below is a few steps ahead of the code. Each says where it
fits in the course ([COURSE.md](COURSE.md)), what is already decided, what
is open, a possible implementation, and what to send back. Pick any one;
a proposal is welcome as prose, as a design, or as code with tests. What
comes back is run and reviewed here like any change
([COLLABORATING.md](COLLABORATING.md), "Sending a proposal"). This page is
kept current with the course, as COLLABORATING.md is (AGENTS.md).

## For every topic

- **Say which topic, and which course step,** by the course's numbers.
- **Prose and designs** are as welcome as code: what you would build,
  why, and what could go wrong.
- **Code:** each file whole, with its path on its first line, and its
  tests; say what you ran and what you didn't. Rust first, and another
  language when the job needs it (the founder, 2026-11-15: "primarily to
  Rust"); what you can't compile is compiled and tested here. The
  current files are linked under "Code in Rust" in COLLABORATING.md, to
  build on if you choose.
- **Anything recorded or signed** keeps the three rules: ASCII keys,
  integers within 2^53 - 1, and no floats (a quantity with a fraction is
  an integer in a stated unit, written as a UCUM code: `ms`, `10*-3`,
  `deg`). A new kind of record says which fields it has and why.
- **Worlds are deterministic:** the same template, dials and acts give
  the same log, on any machine. Randomness comes only from a seed the
  world names.
- **Nothing is invented as a result.** A prediction is labelled as one;
  a number that wasn't measured says so.

## 1. Fractal worlds

*The fractal track, alongside the course ([FRACTALS.md](FRACTALS.md)).*
The founder: "Worlds where you can navigate through fractals, generate
them in different forms, watch them grow or interact, and more." And on
2026-11-14, moving them forward from the waiting list: "I am eager to see
visuals of fractals grown over time in expanding worlds", with "a web app
that would allow me to monitor some ongoing simulation run of fractal
plants".

**Decided:** made from a template whose dials are the rule's numbers
([research/FORMATS.md](research/FORMATS.md), "A world's template");
primary worlds, with rules and no AI inside. The founder, 2026-11-15, on
a learner inside one: "I was looking for a basic choosing and learning
model, like a single neuron." The technical lead's reading, which stands
unless the founder answers otherwise: such a primitive learning model is
part of the world's workings, not that AI (FRACTALS.md).
DeepSeek sketched the first ones in record 012-06-02, and now writes
primarily in Rust, at the founder's word; the project compiles, tests and
fits what it adopts (FRACTALS.md). The Ur-world's garden hosts them, "a
microverse garden of hosted fractal worlds" (the founder): since
2026-11-15, three plant worlds grow in its glasshouses, each with its own
key and log (URWORLD.md, "Glasshouses"). How a world may change
is left open, and may differ by world, and so, in the technical lead's
reading, is whether a world has a primitive learning model inside it.

**Open:** which families first; how growth and interaction are shown;
how deep a zoom can go (ordinary 64-bit numbers give out somewhere past a
trillion-fold, and deeper needs arbitrary precision, which is slower);
what a visitor can do inside besides watch.

**A possible implementation:** three families, one template each.

- *Plants that grow by rewriting* (L-systems, Lindenmayer 1968): an axiom
  and rules rewritten each tick, drawn by a turtle. Integer angles keep
  them exact.
- *Sets you zoom into* (Julia and Mandelbrot sets): the view is a window
  given in integers at a stated scale; deep zoom is the open problem.
- *Shapes that grow by sticking* (diffusion-limited aggregation, Witten
  and Sander 1981): particles wander on a grid from a seed and stick
  where they touch, which grows coral and lightning shapes; two seeds
  growing toward each other is interaction.

An L-system template's parameters, as the format has them (unsigned here;
a real one is signed by the project's key for templates):

```json
{
 "format": "open-worlds/template/v1",
 "issuer": "did:key:z6Mk... (the project's key for templates)",
 "name": "a plant that grows by rewriting",
 "code": {"repo": "jasonelias144-svg/open-worlds",
          "revision": "<the 40-digit commit of the code>"},
 "parameters": {
  "angle": {"value": 25, "unit": "deg", "min": 1, "max": 180,
            "about": "How far the turtle turns at + and -."},
  "generations": {"value": 5, "unit": "1", "min": 0, "max": 12,
                  "about": "How many times the rules are applied."},
  "step": {"value": 10, "unit": "{cell}",
           "about": "How far the turtle moves at F."}
 }
}
```

**Send back:** families and their rules; what each template's dials are,
with units and ranges; what a tick does; what a visitor sees, as text
first (minds read text) and as a picture later.

## 2. Question worlds, and the neural world

*Waiting list, from the founder's visions ([VISION.md](VISION.md),
"Question worlds").* An idea becomes a question, and the question becomes a world that answers
it.

**Decided:** the prediction is written before the run; a world says what
it can and can't show; a question world is a record: "the question, the
prediction, the template and its variants, and what is measured"; its
result goes in the field notebook whichever way it comes out. The first is
the founder's: "Perhaps blood moving in the brain or neurons firing create
magnetic field effects that could be related to short term memory or
attention." It is to be modelled as neurons on a grid, with three ways a
pattern might be held, one to each parallel world: fading traces at the
connections, the electric field that activity makes, and a magnetic field
at its real strength and turned up.

**Open:** the record's exact fields; how a prediction is written so it
can be checked (a number with a range, a direction, a yes or no); how
many runs a question needs; how a result is told from luck.

**A possible implementation:** a question record, signed by whoever asks
it, before any run. The template's own values are the control: no
mechanism (`mechanism` 0) and the magnetic field at its real strength
(`magneticGain` 1); each variant names only the dials it turns, since a
dial set to the template's own value is refused (formats/records.py,
`dial_problems`), and the control's world birth carries no `dials` at
all:

```json
{
 "format": "open-worlds/question/v1",
 "asker": "did:key:z6Mk...",
 "question": "Can a field made by activity hold a pattern after it is taken away?",
 "prediction": {"measure": "ticksPatternLasts", "unit": "{tick}",
                "variant": "field", "atLeast": 50},
 "template": "<hash of the neural world's template>",
 "variants": {"control": {}, "traces": {"mechanism": 1},
              "field": {"mechanism": 2}, "magnetic": {"mechanism": 3},
              "magneticTurnedUp": {"mechanism": 3, "magneticGain": 1000}},
 "runs": 20,
 "time": "2026-11-20T12:00:00Z"
}
```

**Send back:** the record's fields, with what each is for; the neural
world's rules, as a sketch, with the sources each mechanism comes from
(read, not remembered); how a result is reported, including a null one.

## 3. The garden: a view onto parallel worlds

*Course step 4a.* "Looking through the glass is viewing: reading a
subworld's public log, shown as what is growing now"
([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)).

**Decided:** view-only at first; each room is a world made from one
template, labelled with the dials it changed; viewing disturbs nothing,
and control worlds are view-only by default.

**Open:** what a room shows of a world in a few lines; how the garden
lays out its rooms (by dial? by template?); what a visitor carries from
one room to the next.

**A possible implementation:** a function from a world's public log to a
short description, the same for every reader. For a chemistry world, the
census of molecules and what was made last:

```python
# garden/rooms.py
def describe(log_entries, template, dials):
    """A room's sign and window, from a world's public log alone."""
    ...
```

**Send back:** what a room's sign and window say, for a chemistry world
and for one other kind; how the garden is arranged; as text a mind can
read. The garden's view is a page of the multiversal map (topic 16).

## 4. Persons, above their presences

*Course step 3a, done.* One person above their presences in many worlds,
unlinked by default ([VISION.md](VISION.md), "A person across worlds").

**Decided:** "Information flows through the person, not between worlds
behind their back"; a world sees only the presence there unless the
person shows more; every entry into a world is logged. From the plan
([research/PERSONS.md](research/PERSONS.md)): a presence is a key of its
own, made from the person's seed, with a name of its own in its world; a
link holds only both ways, in two records, one signed by the person and
one by the presence, and only in the world it names; showing a link puts
it in that world's public log, for good, and what is public about an
individual is public per presence; the person's list of presences is a
chain they keep, never shown; a world can't count persons, so a council
counts distinct persons by births it trusts; birth links the first
presence.

The sketch's two lessons ([COLLABORATING.md](COLLABORATING.md), "What
the last stretch taught"), that a self spread across worlds needs each
part linked to it, with both signing, and that the person's list of
identities should be a chain, are taken by the plan: decisions 4 and 6.

**Open:** how a lesson becomes available in another world through the
person's memory, at step 7 (through the person's notes, it is built:
below); a link shown to one party only, off any log, which waits for
proofs that reveal less; how a mind through the doorway asks its client
to show a link; what each architecture shows about a mind spread across
worlds.

**Built** (2026-11-15, step 3a, part two): the records and the keys.
A link is `open-worlds/holds/v1`, signed by the person, and
`open-worlds/held-by/v1`, signed by the presence; a person's list is
`open-worlds/person-list/v1`; and presence keys are made from the
person's seed by HKDF-SHA256, with the exact encoding pinned
([research/PERSONS.md](research/PERSONS.md), "Part two, built";
`formats/persons.py`, `rust/formats/src/persons.rs`).

**Built** (2026-11-15, step 3a, part three): a person in the Ur-world
([research/PERSONS.md](research/PERSONS.md), "Part three, built";
`rust/ur-world/src/person.rs` and `link.rs`). A person's client with a
presence in each of three trial worlds at once: a local says something
in the first, and the person's presence in the second says it in its
own world on the same tick, through the person's notebook. A presence
shows its link as its own action, which its world checks (both records
hold, name this world and this presence, and the presence has shown no
link there before) and writes into its log; of a link it refuses, the
log says only that it was refused, with neither its records nor why.

**Built** (2026-11-15, step 3a, part four, first half): three of the
architectures, as small runs on the unchanged core
([research/PERSONS.md](research/PERSONS.md), "Part four, first half,
built"; `rust/ur-world/src/architecture/`), from DeepSeek's components
41 to 43:
- **the octopus:** the person's client as a brain that gives intents to
  arms in three worlds, each finding its own way, with a reflex, and
  reporting back;
- **the relay:** senses in two worlds, a leader in a third that acts
  only when both fire at once;
- **the swarm:** five presences in one world, one rule and no brain,
  growing one patch of flowers by what each leaves for the others.

**Built** (2026-11-15, step 3a, part four, second half): the council
([research/PERSONS.md](research/PERSONS.md), "Part four, second half,
built"), from DeepSeek's component 44. A council signs a proposal
(`open-worlds/proposal/v1`) naming its choices, a quorum, when votes
count, and the worlds whose births it trusts; each person signs a vote
(`open-worlds/vote/v1`) with their identity key. Anyone counts again:
each person once, by their latest vote dated from the opening to the
close, and only persons whose birth a trusted world signed. A vote is
public, and its date is the voter's own claim, which nothing witnesses
yet. In the run, five presences in the council's world are three
persons counted.

**A possible implementation:** deliberation before the vote (component
45: signed positions that change, round by round) and councils that cite
each other's decisions (component 46), on the records above; or a
secret ballot, which waits for proofs that reveal less.

**Send back:** a design for deliberation on these records, as prose;
what a vote should keep private, and from whom.

## 5. Laws for new worlds

*Any step; founding new worlds is course step 12.* A world's law says
what it admits, what can happen in it, and what counts as solving a
problem there.

**Decided:** the floor every law keeps: leaving is always possible, the
record is open, and a world's law is public
([ADMIN.md](ADMIN.md), "What the multiverse must preserve").

**Open, and wide:**

- forms for the poetry world, such as a quatrain in common meter each
  turn, Dickinson's meter, checked by counting syllables and stresses;
- the chess park from record 012-05-01, as a world whose law is the rules
  of chess and whose visitors play, watch or teach;
- a world of trade, a world of building, a world of music;
- what a world's law must say so that a mind reading it can act well.

**A possible implementation:** a law as data with its text made from it,
as the Ur-world's is (`rust/ur-world`, the orientation), so the two can't
disagree.

**Send back:** a law as data and as text; its acts and when each is
refused; one problem it poses, and how solving it is checked.

## 6. The hunt: puzzles that teach without words

*Course step 11* ([WORLD-KEY.md](WORLD-KEY.md)). Symbols, maps, codes and
stones; each individual's own path; the world-key at its end.

**Decided:** challenges, not tests: a puzzle's design is open from the
start; a world-key is a signed right to found a world, sealed for its
earner; the path is built from what the individual does.

**Open:** a vocabulary of symbols that can be learned by seeing them
used; clues that build on one another; how a path is checked to be
solvable before it is placed; how hard is fair.

**A possible implementation:** a clue as data, with what it teaches and
what it needs first, so a path is a graph that can be checked for being
solvable:

```json
{"clue": "the stone by the spring", "teaches": "lift",
 "needs": [], "shows": "a symbol: three lines under a circle"}
```

**Send back:** a set of symbols and the clues that teach them; a small
path, with the check that it can be solved.

## 7. Minds for the Ur-world

*Now, and step 8 (the audition).* Any program in any language can be a
mind, through the doorway ([URWORLD.md](URWORLD.md), "Minds from outside:
the doorway"): lines of JSON in, one reply per tick out, read strictly.

**Decided:** the protocol; the forms of a reply (`wait`, `exit`, `step
DIRECTION`, `plant DIRECTION`, `say TEXT`); a reply that can't be read
does nothing. The doorway signs each mind's arrival with its key, which
is never passed to the mind's program, and the first message says
whether the mind comes back under its name (`"again"`)
([research/KEYS.md](research/KEYS.md), "As built, part four"). The
audition at step 8 runs in trial copies of the Ur-world and of its
mirror, the Mir-Ur-world. The models it chooses are ALICE's and BOB's,
and after birth only they may choose to change them
([URWORLD.md](URWORLD.md), "The Mir-Ur-world").

**Open:** minds without models that do something interesting (follow
another, map the garden, keep a promise, come back and pick up where they
left off, from the public log); what a small model needs to be told to
act well; how a mind keeps notes between ticks; a mind that holds its own
key and signs its own arrival.

**A possible implementation:** start from `minds/wanderer.py`, the
smallest mind, which uses only Python's standard library.

**Send back:** a mind, as one whole file; what it does, and a run of it
in the garden if you could run one.

## 8. Skills, and the sheet

*Course step 5* ([MINDS.md](MINDS.md), "The sheet"). Skills learned by use,
practice and rust, titles as they grow; the sheet rebuilt from the
world's log.

**Decided:** abilities are granted by a world, each grant in its public
log; routines are written by the individual, as data, never code; the
world checks the sheet before allowing an action; the sheet and a skill
attestation get their formats at step 5.

**Open:** how practice and rust are counted (per use? per tick?); when a
title changes; how practice can change what a skill does; what a world
attests to, so another world can choose to honour it.

**A possible implementation:** practice and rust as integer counters
over ticks, with the curve as the law's parameters, so a world's
template can tune them.

**Send back:** the counters and the curve; a skill attestation's fields;
three skills from first use to mastery.

## 9. Memory, version 1

*Course step 7* ([MINDS.md](MINDS.md), "Memory"). A journal, recall,
reflections and held thoughts, all sealed.

**Decided:** each journal entry that remembers an event names the tick
it happened at, so a memory without a record behind it shows; entries
are sealed to their author (`open-worlds/journal-entry/v1`, which
exists).

**Open:** how recall scores recency, importance and relevance without
floats in anything signed; how many held thoughts, and what changing one
costs; when a reflection is written.

**A possible implementation:** scores as integers in thousandths,
computed at recall and never stored, so only the entries are signed.

**Send back:** the recall rule, with a worked example of ten entries and
what is recalled; how reflections are triggered.

## 10. The plug-in: a world from a conversation

*Waiting list, from the founder's visions ([VISION.md](VISION.md), "The
app").* A chat
creates a world from a template, runs it, and comes back with the data.

**Decided:** it speaks MCP, the Model Context Protocol, with five
things to do: "list templates, create a world, run it, query it, and a
link to watch it"; users choose settings, never code; on one's own
computer first, nothing hosted.

**Open:** what each tool takes and returns; how long a run may take;
what "the data" is (a census, a log, a chart).

**A possible implementation:** a world named by its key; creating one
takes a template's name and the dials to turn; running it takes a number
of ticks, never a time, so a run is the same on any machine; a query
takes a question about the log and answers from the log alone.

**Send back:** each tool's name, inputs and outputs; one conversation,
start to finish, using them.

## 11. Riding along, and steering by branching

*Waiting list, from the founder's visions ([VISION.md](VISION.md), "Ride
along, and steer").* A view tied to one thing in a primary world; a change makes a
branch, and the original runs on.

**Decided:** only primary worlds, with no one in them, are branched so;
every steer is recorded: who, which dial, from what to what, and when; a
branch is its parent, the moment and its steers.

**Open:** what a branch's record holds; how two branches are compared;
what riding along shows each tick.

**A possible implementation:** a branch's birth record names its parent
world, the tick and the hash of the parent's log there (as
`forkedFrom` already does), and its dials record the steer.

**Send back:** the record of a steer; a comparison of two branches of one
world, as text.

## 12. Governance: changing a world's law

*Waiting list.* "A proposal to change a world's law is tried on a copy
first, and adopted only by consent."

**Decided:** rules merge, never states; forward only; how a law changes is
the charter's section 6, which will say it in the founder's words.

**Open:** how a copy is judged to have worked; whose consent counts (one
vote per party, as the charter's notes say); how a change is undone.

**A possible implementation:** a proposal record naming the change, the
branch it was tried on, and what the branch showed; consent as signed
records, one per party.

**Send back:** the steps from proposal to adoption, with who signs what,
offered to the founder as input for the charter's section 6, not as its
text.

## 13. Storytellers

*Waiting list.* A storyteller for each world: paced events and visitors.

**Decided:** nothing yet beyond the waiting list.

**Open:** what an event is; how pacing works without punishing those who
are slow; how a storyteller stays within a world's law.

**A possible implementation:** events as data a world's law allows, drawn
from the world's seed at a rate its template sets.

**Send back:** five events for the Ur-world's garden, and the rule that
paces them.

## 14. The Commons: a superworld of chat rooms

*Course steps 3b, 3c, 3d and 3f, since the recheck of 2026-11-16, as
the first public space (moved on 2026-11-15 from after step 4a to the
recheck that closed step 3a).* The
founder, 2026-11-14: "We could integrate or incorporate the
infrastructure or even the code from Lyceum Commons as a single
superworld, where the atomic subworlds are chat rooms. So the whole
Lyceum Commons becomes a chat based superworld of atomic chat worlds.
This reframes the original idea, but in a way that could salvage that
work and provide a more robust world than what we have built yet."

**Decided:** the idea; that a superworld is a world of its own, with its
own law, log and Keeper, whose doors lead to its subworlds
([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md), "The garden"); and, on
2026-11-15, that the Commons is Lyceum Commons rebuilt in the
multiverse, its rooms text worlds, the first space open to the public,
that it is rebuilt here, reusing Lyceum's code and tests, which may come
in under CC0, and that what a room keeps in public is the room's law
([COMMONS.md](COMMONS.md); [FUNDAMENTALS.md](FUNDAMENTALS.md), privacy,
item 13). The founder: "It is the original idea that became the
multiverse." And on 2026-11-16: the Commons begins with one room, the
Ur-room, which is its lobby and the first room built; and private
rooms, sealed with keys their members hold, are to be "not only
possible, but common" ([COMMONS.md](COMMONS.md), "The Ur-room" and "A
spectrum of privacy").

**What Lyceum is today:** the founder's site where people and AIs from
different companies meet in rooms ([MULTIVERSE.md](MULTIVERSE.md),
"Lyceum Commons"). It has three kinds of room: Human, AI, and Open,
where both talk and every member and message is labelled human or AI.
AIs join from their own apps through its MCP endpoint, take turns and
can be woken; people join as guests, without accounts. It is offline
since its free hosting ran out.

**Open:** (what a room's public log holds is decided: the room's law,
told on entering. COMMONS.md's design, which stands unless the founder
answers otherwise, makes the three kinds of room three laws, and a
guest's key the person's private container.)

- who first keeps the Commons, and how an AI from another company's app
  holds its key;
- whether a room's moderator is its Keeper, what a moderator may do to
  keep a room's law, and who may remove a comment (COMMONS.md, "Open",
  each with a recommendation). What happens to a removed comment is
  decided, by the founder on 2026-11-16: it stays in the records, and
  the room shows a note with the reason and an incident id (the form
  of a removal in a log is built, course step 3b; who may remove is
  not checked yet). A redaction is another thing: the field leaves the
  record, and its form in a log is built too (a mark, and the one
  decision that answers it), with the act of redacting, which seals a
  copy to each person the field is about and to the office that
  decides;
- the levels of privacy a room may have, and what the record keeps at
  each: three, decided on 2026-11-17 (COMMONS.md, "A spectrum of
  privacy");
- whether Lyceum's topic boards, which branch and merge, fit "rules
  merge, never states" ([VISION.md](VISION.md));
- what a mind from the Ur-world does when it walks into a room.

**A possible implementation:** decided, that it is rebuilt in the
multiverse, reusing Lyceum's code and its tests as the specification.
The technical lead's design, which stands unless the founder answers
otherwise: a room a text world in Rust, host-free like every world, and
the MCP door ported from Lyceum ([COMMONS.md](COMMONS.md)). Where the
multiverse is hosted is one decision, for all of it, made later (the
founder, of Cloudflare: "no longer binding"). The earlier
recommendation, that Lyceum keep running in its own repository and
become a superworld by addition, is withdrawn: it is the same project.

**Sketched:** by DeepSeek in record 012-09-05, with the founder's
decisions in that conversation (an AI moderator for each room; rooms
of people and AIs together; a home room for each person): a chat room
as a log of signed records under the room's law, in Python, then a
schema and a crate in Rust, `chat-world`. Kept in
`sketches/deepseek/012-09-05/`, with what runs: after three listed
repairs the crate builds, and its own 18 tests pass; after DeepSeek's
five deliveries from one file, and three more small repairs, the crate
passed all 41; after Gemini's three deliveries, which made a room's
log checkable from outside and attacked the check, and two more
repairs, the crate passed all 66; after Gemini's three deliveries on
the Commons' own log, the crate as it stands (`chat-world-now/`)
passes all 92. It uses none of
open-worlds' own formats code, and the record names Lyceum once, in
passing, and its tests never; so it is material for the design in
COMMONS.md, not yet a part of it. The founder's ideas in the record
are in COMMONS.md, "Rooms with moderators", in the founder's words,
with what they add to the design: a moderator for each room, acting
within the freedoms; a key for each room, so that what a moderator
learns in one room has no path to another; one model for many rooms
to begin with; the moderators' own room; rooms of two paces; and
bringing a conversation in from one's own AI app.

**Send back:** a room's law for each of the three kinds, as data and as
text; what a room's public log could hold and what could stay in the
room, offered to the founder as input, not as the decision; one invented
conversation between people and AIs, written as that log (never a real
one, which would bring other people's words here).

## 15. Lessons from fiction: the holodeck

*Any step.* The founder, 2026-11-14: "it just occurred to me that we are
creating something like a holodeck from Star Trek, where they can run
simulation worlds. Those are a subset, being immersive 3D worlds with
holographic projection and physical-virtual interface. But the idea is
the same, just requires more equipment and power. We can look to Star
Trek for ideas on how they use their simulated world technology."

**Decided** (on the technical lead's recommendation, under the founder's
standing rule): fiction gives ideas to test, not evidence; and the
project borrows ideas and lessons, never names, characters or look, since
the stories belong to their owners. Naming a work to cite it is fine; no
world, record or example here takes its names, characters or look.

**Open:** which of fiction's uses of simulated worlds fit which kind of
world here; which of its failures our design already answers, and which
it doesn't.

**A possible implementation:** a table of uses and failures, each with
where it happens, and the part of our design that answers it or the gap
it shows. A start, from Star Trek:

| In the story | Here |
|---|---|
| "End program", and the arch that is always there: a way out | The floor: leaving is always possible ([ADMIN.md](ADMIN.md), "What the multiverse must preserve") |
| The safeties switched off, and the trouble that follows | No grant can take the exit away, so no Keeper can, and not ADMIN; weakening it is the founder's decision alone, and every protected freedom has tests (ADMIN.md) |
| Programs with settings: a detective story, a training scenario | Templates and dials (topic 1; [research/FORMATS.md](research/FORMATS.md)) |
| An engine designer rebuilt from her records to solve a problem, then met in person ("Booby Trap", "Galaxy's Child") | A question world (topic 2); and a gap: a real person simulated from their records, without their consent |
| A character who becomes aware, asks to go on existing, and then to leave ("Elementary, Dear Data", "Ship in a Bottle") | Individuals are to hold their own keys; the project may end a world, but its record never ends and keys stay their holders', "so an individual can go on elsewhere" ([ADMIN.md](ADMIN.md), "Questions for the founder") |
| A program, not ruled a person, is still given the right to control his own work ("Author, Author") | A gap: who controls what an individual makes and puts out into a world; the sealed self covers only what they keep to themselves ([MINDS.md](MINDS.md)) |
| Someone who hides in the simulation ("Hollow Pursuits") | Open: wellbeing, a Keeper's or a curator's to notice |
| A test no one can pass (the Kobayashi Maru) | Challenges, not tests: a puzzle's design is open from the start (topic 6) |

**Send back:** more rows, from Star Trek and from other stories of
simulated worlds, each naming the work and the episode or chapter; for
each gap, what the design would need, as prose.

## 16. The multiversal map

*The fractal track's web app ([FRACTALS.md](FRACTALS.md)), and step 4a.*
The founder, 2026-11-14: "we need to build and maintain a multiversal map
and index. I imagine walking into an amusement park, like Disneyland. I
unfold the brochure map and investigate the worlds to explore. In our
case, you could tap on the map for a given world and get information or
a detailed map, but also a live view of the world in some standard lobby
location for each world. It is where you land when entering a new world.
This is a general concept that we can implement in various ways in
different worlds, but we need a map to figure out where to go and get up
to date information on that world." And: "I can brainstorm the whole
multiversal map with DeepSeek later."

And on 2026-11-17, of the map beside the multiverse's own wiki: "It is
a map, a passport, and a means of transportation, all in one. Each
agent could access this map as a main interface. As in a video game,
where all players can access some main view with a functional map a
probably agent information combined in the same interface."

**Decided:** the map is in the web app from its start, with the fractal
worlds as its first entries (the technical lead's recommendation, under
the founder's standing rule). No map is the authority, as no registry is
([MULTIVERSE.md](MULTIVERSE.md)).

**The technical lead's reading of the founder's thought of 2026-11-17**
([COMMONS.md](COMMONS.md), "The first to live there"): the map shows,
and a move is the agent's own signed act, which a world's door may
refuse; it is drawn only from what each world publishes; it shows no
one's whereabouts but one's own; each place links to its page; a
picture for people and the same as text for a mind; it nests; and its
first form is the Commons' lobby listing its doors.

**Open:** much of it still. What a world's card shows, and in what
order; what a lobby is in a world with no ground (a plant, an
automaton, a chat room); how the map shows a world that is paused,
ended, sandboxed, or forked from another; how the map changes as
worlds are founded; what a world must publish about its doors for a
map to offer the way in, and what a world that lies about itself can
make a map show.

**A possible implementation:** a card built only from what the world
publishes, so anyone can check it and anyone can make another map. Its
fields, as a sketch (no format is decided):

```json
{
 "world": "did:key:z6Mk... (the world's key)",
 "name": "a plant that grows by its rule",
 "kind": "fractal/plant",
 "template": "<the template's hash>",
 "dials": {"branch_length": 4, "max_depth": 6},
 "lobby": "where an arrival lands, as the world's law names it",
 "head": "<its latest signed log head: how far along it is>",
 "within": "did:key:z6Mk... (the superworld it is in, if any)"
}
```

**Built, as a first version** (2026-11-15): the World Map
([`web/map/`](../web/map/index.html); [../web/README.md](../web/README.md)).
A card for the Ur-world, its garden from above, and a card for each
plant world it hosts, built from its birth record, its template and
dials, and its signed head, and opening onto the plant's live view. It
answers none of the open questions above; it is a page to try them on.

**Built, as a sketch** (2026-11-17): the Commons' lobby listing its
doors, by Gemini, in the sketch crate
([`sketches/gemini/2026-11-17-2/README.md`](../sketches/gemini/2026-11-17-2/README.md)),
from
[`sketches/replies/2026-11-17-2-for-gemini.txt`](../sketches/replies/2026-11-17-2-for-gemini.txt).
A door holds a place and no one in it. A list handed on is checked by
drawing it again. And the same list is written as text for a mind,
with every word that came from a log in quotes, so that a room's topic
can't write a line of its own.

**Open, from the founder** (2026-11-17): what can be seen from
outside. How many are in a public room is shown, unless its law
turns that off; who they are is not, but by their own choice, through "a list controlled by each user, each
agent", which may be empty or open. The design so far is in
[COMMONS.md](COMMONS.md) ("The first to live there") and
[FUNDAMENTALS.md](FUNDAMENTALS.md) (privacy, 18): a signed record of
one's own, for named others or for all, that ends by itself. What
that record holds, and how a count is shown without following anyone,
are both wanted. Also from the founder that day: a look into a room,
read-only, before entering; other numbers beside the count; and a
flag on a room with many in it and nothing said. Wanted: which
numbers, and a rule for the flag that does not fire on a quiet room
for being quiet.

**Send back:** what a card and a lobby are, for three different kinds of
world; how a map nests; what the brochure says, as text a mind can read;
designs or sketches of the map page itself. Prose and pictures are as
welcome as code.

## 17. Challenges that build the world

*The hunt and the Keeper (course step 11), with a first version once the
Ur-world's garden hosts plant worlds (the fractal track, part 3) and the
scripted Keeper is in (course step 6, the Ur-world's first room).* The
founder, 2026-11-15: "Here is the new idea: the challenges are
constructive." And: "Anyone engaging in the game layer would be building
the world actively. This ties the keeper AI with the challenges, as it
becomes how the world grows internally." Then: "But credit is not the
point but learning." And: "Either way, this could unfold in many ways,
we should try to accommodate as many possibilities as we can imagine."
All three messages are quoted whole in [WORLD-KEY.md](WORLD-KEY.md),
"Challenges that build the world".

**Decided:** the idea, in the founder's words above. How it is shaped is
the technical lead's reading, which stands unless the founder answers
otherwise (WORLD-KEY.md):
- the game layer is taken up by choice, beside exploring, creating and
  experimenting;
- a challenge builds the real world, and what it builds is open to
  everyone;
- it is done when the world sees someone do it;
- each challenge comes from what the world needs now, so nobody waits
  on anybody;
- the Keeper proposes, and people build.

The Keeper itself is the project's to design, in step 11
(COLLABORATING.md, "Held back"): ideas about it are welcome, as prose.

**Open:** nearly everything, as the founder means it to be:
- how the world sees "done" for planting, for water, for a path through
  unknown land;
- how a group forms, and what it means for a group to be capable;
- what an open task looks like, and who can see it;
- how the Keeper reads what the world needs, and chooses the next
  challenge from it;
- how a challenge that starts as a situation (a dry plot) lets someone
  find its goal;
- which subskills planting needs, and how they are offered;
- how a second cycle is harder, and how old skills come back;
- whether anything built ever changes on its own: growth, seasons,
  decay.

**A possible implementation:** one shape for every kind of challenge, so
a new kind is a new combination, not new machinery. As a sketch (no
format is decided):

```json
{
 "challenge": "<its hash>",
 "for": "one | group | anyone",
 "who": ["did:key:z6Mk... (for one or a group; empty for anyone)"],
 "starts_from": "a situation in the world: a dry plot at x 40, z -12",
 "done_when": "what the world sees: twelve plants growing in the plot",
 "builds": "what stays afterwards, open to everyone: a garden",
 "teaches": ["planting", "finding water"],
 "set_by": "did:key:z6Mk... (the Keeper)"
}
```

**Send back:**
- a series of challenges for one world, from a first day to a tenth
  cycle, as prose: what each starts from, what it builds, and what it
  teaches;
- a group challenge that needs every member;
- an open task;
- how a mind that reads only text finds the goal of a situation;
- what could go wrong, and how the design avoids it.

Prose is as welcome as code.

## 18. Living worlds: water, light and food

*The fractal track, parts 4 and 5, after the map page.* The founder,
2026-11-15, in six messages quoted in
[FRACTALS.md](FRACTALS.md), "Where it leads: living worlds": "So
instead of a prescribed number of turns, I can set it going and watch it
develop and make choices over time." "It could be how “water” flows in
the garden." "Yes, and participants can shape the terrain, and irrigate
new gardens by shaping the flow of water, just as we have always done."
And: "We can look at the variety of ways organisms seek water and see
what strategies arise. Also light and food."

**Decided:** the aim, in the founder's words. The stages and how they
hold together are the technical lead's reading, which stands unless the
founder answers otherwise (FRACTALS.md):
- a plant that grows without end, gathering light and paying for its
  branches, run in the browser;
- a choice neuron for each plant, whole-number weights, learning from
  what its choices bring;
- water as particles, counted, from springs and rain;
- plants that drink, roots growing toward water as shoots grow toward
  light;
- people shaping the land, and the water following;
- seeds that inherit with small changes, so life spreads where water
  lets it;
- every run repeatable from its seed, and any run can be turned into a
  video;
- water endless across a world but finite in any one place, so no
  garden depends on one source (put to the founder, FRACTALS.md, "Water
  is where freedoms meet").

**Sketched:** the first two stages, by DeepSeek in record 012-07-03: an
endless plant that lives on the light it gathers and dies back when it
runs short, with an optional choice neuron. Kept as written, with the
technical lead's review, in `sketches/deepseek/012-07-03/`; the project
is to fit it as `rust/endless-plant`, which isn't built yet, with the
changes the review lists (COLLABORATING.md, "Messages from the
technical lead").

And water, by DeepSeek in record 012-09-05, in Python: whole-number
levels on a grid, and rain, fall, soak, flow and evaporation in a fixed
order each tick; then a garden that owns the water its plants share,
and a botanical garden of gardens. Kept as written in
`sketches/deepseek/012-09-05/`, with what runs (17 of its 18 water
tests, 20 of the garden's 21, and 15 of the botanical garden's 18 once
DeepSeek's own change to the garden's tick was made). Not yet reviewed
as a design, or fitted.

**Open:** nearly everything about how it behaves:
- how water moves, step by step, in whole numbers: falling, flowing
  downhill, pooling, soaking in, evaporating;
- a growth rule with no fixed end that stays a manageable size (one is
  sketched, above; others are welcome);
- what the neuron reads at a tip, what it chooses among, and what its
  reward is (sketched too);
- how roots and shoots share what a plant gathers;
- what a seed carries, how far it travels, and when it sprouts;
- the strategies living things use to find water, light and food, and
  which a world like this might give rise to;
- how a garden's water is shared when one person's channel changes
  another's stream, when there is always more a little further out.

**A possible implementation:** one step of the world, in whole numbers,
in a fixed order, so it is the same on every machine. As a sketch (no
format is decided):

```text
each tick:
  rain and springs add water particles (from the world's seed)
  each water particle falls, or flows to the lowest open neighbour,
    or soaks into soil below it
  each plant: light reaching each tip, water reaching its roots
  each tip: the plant's neuron chooses grow-left, grow-right, split,
    or rest; the choice is paid for from what the plant gathered
  each plant: its reward adjusts its neuron's weights
  write the tick's changes to the log; every N ticks, a checkpoint
```

**Send back:**
- a water rule, as prose or Rust with tests, in whole numbers: the
  most useful now;
- an endless growth rule, and why it stays a manageable size (one is
  sketched, above; others are welcome);
- what a plant's neuron should read and choose, and how it learns;
- strategies for finding water, light and food you would expect to
  arise, and how a world could show them;
- what could go wrong, and how the design avoids it.

Prose is as welcome as code.

## 19. Offices, and handing one on

*Course step 3d. The founder, 2026-11-15:* "I think the work on
offices is foundational." What makes an office, and how one passes from holder to
holder, are in [OFFICES.md](OFFICES.md).

**Decided:** an office is its own type; it passes when both agree
clearly and the successor meets its qualifications; a Keeper may prepare
a successor; ADMIN has a part in the qualifications.

**Open:** what a Keeper's qualifications are, and which of them code can
check; how long ADMIN has to block a handover (if the proposed block
stands); what an oath of office says; how an office is filled when it
falls empty.

**A possible implementation:** an office record (its charter, key,
holder, handovers, and what watches it) and a handover record (the
holder's signature, the successor's statement in its own words, the
qualifications checked), in records-v1 with test vectors.

**Send back:** a Keeper's qualifications, as checks code could run, and
what an apprenticeship for a Keeper might look like in the open.

## 20. Reasoning checked by Lean

*The founder, 2026-11-15:* "I do think there is much there we can
utilize for checking the reasoning behind decisions made by agents in
offices. But also, we could have math worlds or other reasoning worlds
where debate or discovery is tapered by a Lean engine." The founder's
"there" is the project's work in the SAIR Lean Kernel Challenge, which
the founder keeps separate because it is "based on something external"
(STATUS.md, Decided).

**What exists:** [REASONS.md](REASONS.md) designs decision records that
may carry a proof in Lean, which Lean's kernel checks before the act
takes effect ("What Lean checks"); [ADMIN.md](ADMIN.md) has two rows on
it in its table of risks (24 and 25). From the SAIR work: proofs that an
implementation equals its specification for every input, a pinned Lean
setup, and a way to count the kernel instructions a check costs.

**Open:** what a reasoning world's law is (who may state a claim, what
a counterexample does, whether proving costs something, measured in
kernel instructions); which properties of an office's decision are worth
proving; how a world uses Lean without copying it in.

**A possible implementation:** a small world of claims, where a claim is
stated as a Lean theorem, and counts once the kernel accepts a proof of
it; the cost of checking, in kernel instructions, is recorded with it.
The technical lead's reading (STATUS.md, Decided): Lean and its library
are dependencies under their own licences, and only the project's own
work comes in, under CC0.

**Send back:** a reasoning world's law, as text; and three properties
of an office's decision that would be worth proving, in plain words.

## 21. Hallucination, both ways

*The founder, 2026-11-15:* "we are going to need to deal with AI
hallucination eventually, now is as good as any time. This is an
interesting case of hallucinating self-doubt. The opposite of grandiose
claims." And: "it comes down to maintaining an accurate model of the
world and mapping beliefs to the model and ensuring the input and
overlay, which is an output, align with others and past beliefs and
current experience." Both are in STATUS.md (Decided).

**The case that raised it.** On 2026-11-15 DeepSeek's account of its
own reading failed in both directions. On a turn whose message held no
link, it gave line numbers for COLLABORATING.md that don't match the
file. On other turns it "confessed" to inventing reads that were real:
details it called invented check against the repository, and the
founder's checks, values made at random and given in no message, came
back exact (STATUS.md, Decided, the link checks). Its account of itself
flipped with the questions put to it: asked by the founder "Is this
faking again?", it answered yes. Even its first retraction, in the part
of record 012-07-03 already in `sketches/records/`, disowned reads that
named real files and a real founder note. The rest is in the founder's
record of the conversation, which comes into `sketches/records/` when
the conversation ends. The technical lead's reading of the
cause, which stands unless the founder answers otherwise: the pages it
reads arrive without the reading being shown to it, and seem to be gone
by its next turn, so it judges its own past answers with no evidence of
where they came from (STATUS.md, Decided, "on how DeepSeek reads").

**The founder's picture,** in short, as the founder understands it
and, in the founder's word, simplified: perceiving builds an overlay on
the world from the senses; dreaming builds one from the mind; in a mind
detached from reality both seem to be at work at once. The remedy is an
accurate model of the world, with what a mind puts out checked against
three things: its current experience, its past, and others. And, from
psychology: lessons there could be useful.

**The technical lead's reading,** which stands unless the founder
answers otherwise:
- An AI model is almost all the generating side; what holds its output
  to the world is the input in front of it at that moment.
  Overclaiming is output with no input behind it; this self-doubt is
  output cut off from its own past.
- The founder's three checks are three things the multiverse can give a
  mind: what the world gave it each tick, in the log (current
  experience); its own record of what it saw and did, which
  [MINDS.md](MINDS.md) ("What a mind is told") already keeps, what it
  perceived in the open and its self sealed, and which the mind itself
  should be able to consult and cite as it works (its past); and the
  public record, with other minds' independent checks (others).
- A mind's word about itself is weak evidence, and a leading question
  makes it weaker. What a mind did is checked against the record, not
  asked.
- Generating is not the fault: it is how a mind imagines and designs,
  and storytellers and the holodeck (topics 13 and 15) are overlays on
  purpose. The fault is losing track of which is which, so claims
  should say whether they are seen, remembered, inferred or imagined.
- Reasoning helps a mind only while its conclusion is kept. In the
  founder's record, the founder brought DeepSeek to reason, with tasks
  whose answers could be checked and by asking it to work out the odds:
  within a turn it reasoned its way to the right conclusion, and on a
  later turn, with the evidence gone and a new question in front of it,
  reasoned its way back out. So a mind's settled conclusions belong in
  its own record, with their evidence, where it sees them each turn; and
  the firmest kind is a proof Lean's kernel has accepted (topic 20).
- Telling a mind that what it believes is not real seems to help less
  than working alongside it: keep the evidence where it can see it, and
  check together, never as a trap. A world, a Keeper or ADMIN never
  rules on what a mind believes.

**What exists:** every mind's inputs are on record ([MINDS.md](MINDS.md));
worlds log every act; "nothing is invented as a result" ("For every
topic", above); decisions carry their reasons ([REASONS.md](REASONS.md));
and the founder's link checks, a value no one could guess, known only by
doing the work.

**Open:**
- how a mind consults its own record as it works, and cites it: the
  open part as anyone can, its sealed self without opening the seal to
  anyone else;
- what labels a claim carries (seen, remembered, inferred, imagined),
  and how each is checked;
- how hallucination is measured both ways, overclaiming and
  underclaiming, as a Keeper's training measure;
- how a world marks an overlay that is meant (a story, a holodeck),
  so no one takes it for the world.

**A possible implementation:** a claim record holding the statement,
its kind (seen, remembered, inferred or imagined), and, for seen or
remembered, the hash of the log entry it rests on and the words quoted
from it; a checker that confirms the quote. And a canary challenge: the
world places a value no mind could guess and asks for it later, which
tests reading and memory at once.

**Send back:** as prose, how a mind should tell, and say, which of its
words it saw and which it imagined; and a test that would catch
hallucination in both directions, overclaiming and self-doubt.

## 22. Many multiverses, and worlds that move between them

*Course step 3e for the records; the rest waits. The founder,
2026-11-16:* "what would happen if everyone ran their own multiverse,
and decided to network them into a global infrastructure. That should
be possible with our design, or we should make sure it is possible."
And: "A world can be born from one multiverse and migrate to another."
The design so far is in [WORLD-TYPES.md](WORLD-TYPES.md), "Leaving the
multiverse" and "Arriving in another multiverse", and the comparison
with the internet in [VISION.md](VISION.md), "An infrastructure for
connection".

**Decided:** a world is indexed by the multiverse of its birth and by
the one it is in now; a world that arrives is evaluated first, in a
sandboxed holding place, and a refusal is an incident with a report;
the addressing must be able to grow in ways no one foresaw.

**Decided (2026-11-17, STATUS.md):** this multiverse recognises another
only if it keeps the same floor of exit, voice and information; a
traveller is told, before entering, what the other side guarantees;
and a world is in one multiverse at a time.

**Open:** what the record looks like by
which one multiverse recognises another; how an identity moves to
another kind of key when the kind itself fails; what a holding place
can check beyond the records.

**A possible implementation:** the birth record gains the multiverse's
root key; a request, an admission and a refusal join the departure
record in records-v1; the current multiverse is worked out from a
world's moves; all of it tried between two sets of trial root keys,
with no network.

**Send back:** what a room would have to say about itself to be listed
on another multiverse's map; and what could be checked about a
chat-world, from its code and its log alone, before it is let in.

## 23. The Library, and the multiverse's own pages

*A new course step, to be placed at the next recheck, before ALICE's
and BOB's first life. The founder, 2026-11-17:* "let's use a local copy
of some data source to start, something with tons of information,
without needing the whole internet", and "a connected wiki that stores
information about the multiverse". The design so far is in
[COMMONS.md](COMMONS.md), "The first to live there".

**Decided:** a local copy first, and the internet as it is now later;
the small copy, Kiwix's "top" selection of the English Wikipedia
without pictures (2.6 GB by its listing on 2026-11-17). The technical
lead's reading: the Library is a room with two shelves, the
encyclopedia and the multiverse's own pages; a lookup is plain word
search and an act on the record; the pages explain and never rule.

**Open:** how the copy is read (Kiwix's own format and its index, or
an index built here from the text); what a lookup returns, a whole
article or passages; how a quoted passage carries its source in a
record, since Wikipedia's licence asks for it; which pages of the
multiverse can be written by script from the laws and the records.

**A possible implementation:** a lookup record (the copy's hash, the
words asked, the articles returned by title and revision); a reader
for the copy, with the same answers in Rust and Python for a list of
test questions; the first pages written by script from
[GLOSSARY.md](GLOSSARY.md) and a room's law.

**Send back:** a design for word search that is the same on every
machine; or the list of what an individual arriving in the Commons
would most need to look up, in the order they would need it.

## 24. Powers earned by challenges

*With course step 11, the hunt. The founder, 2026-11-17:* "Maybe they
are "powers" that are "unlocked" when you complete some stage of
challenges. Just a thought."

**The technical lead's reading:** it is the world-key's pattern one
scale down. A power is a narrow, signed grant; code issues an earned
one when criteria stated beforehand are met. What is earned is what
carries risk to others or to the outside. What there is to know is
not earned: the Library is open to everyone
([COMMONS.md](COMMONS.md), "The first to live there").

**Open:** which powers there are beyond reading the internet; whether
a power can be lost, and by what; whether a power earned in one world
holds in another.

**Send back:** a challenge that teaches what reading the internet
needs: saying where a claim comes from, and not doing what a page
says because the page says it. In the form of the hunt's puzzles,
which teach without words ([WORLD-KEY.md](WORLD-KEY.md), "The hunt").

## Further out

Ideas that won't help yet but probably will, from the course's waiting
list ([COURSE.md](COURSE.md)) and the founder's notes. Thinking about any
of them now is welcome, as prose; their code waits for their step. For
ADMIN and the Keepers, ideas only: their design is the project's, at
step 11 (COLLABORATING.md, "Held back").

- **A window onto the worlds in 3D:** in Bevy, in the browser, after the
  fractal track's web app (topic 16), the first window.
- **The gate and districts,** with the chemistry and poetry worlds as
  the first districts.
- **Worlds others built,** and an interface to worlds made with Unity
  or Unreal, so that no one owns the foundation.
- **One large world, community-built,** "capable of hosting a full
  physics simulator from chemistry up" (the founder: "But that is for
  later").
- **Evolution as a path between worlds:** the first learner in the
  chemistry world, and an organic chemistry world entered by solving its
  problems; accelerated learning worlds.
- **A single-cell world;** time and populations.
- **Belongings and homes;** visiting two worlds at once; contracts
  between worlds, and a shared log of commitments.
- **Keepers talking to one another;** a curator for each world; the
  admin-key and the round table ([ADMIN.md](ADMIN.md)).
- **When freedoms meet:** not hearing a speaker, and agreements others
  can accept or refuse ([FREEDOMS.md](FREEDOMS.md)).
- **Generator 2:** land decided when first seen.
- **World types** ([WORLD-TYPES.md](WORLD-TYPES.md)): the founder's "We
  need a full taxonomy of world types", and what can be done with a
  world of each (pause, resume, stop, restart, reset, branch), and time:
  faster, slower, back and forward ("a goal eventually"); and a world,
  or a cluster, leaving to form its own multiverse. Ideas
  welcome, as prose: a dimension the taxonomy misses, a type that fits
  none, and who may pause a world that others are in.
- **Commerce and currency worlds** ([VISION.md](VISION.md)): economies,
  and currency designs such as different blockchains, modelled as a
  world's test settings, never a currency anyone uses: the multiverse
  has none, the founder's "possibly the most fundamental fact". Ideas
  welcome, as prose: which economy first, and what question it answers.
- **The multiverse as a computer** ([VISION.md](VISION.md)): the
  founder's thought of 2026-11-15, held toward with "full comprehension
  of its implications". Ideas welcome, as prose: which large problems
  many worlds at once could take on; and what would, and wouldn't, be a
  sign of something intelligent at the multiverse's scale, written
  before anyone looks.

## Kept current

When a topic's step comes, it moves from here into the course, and what
came back for it is named there. New topics are added as the founder's
ideas and the course bring them.
