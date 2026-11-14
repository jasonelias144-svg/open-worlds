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
  tests; say what you ran and what you didn't. Python is fine for a
  first sketch of anything; a world's kernel is built in Rust in the end
  ("Code in Rust" in COLLABORATING.md), so say which parts are meant to
  move there.
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

*Waiting list, after step 4a, as the garden's second kind of room.* The
founder: "Worlds where you can navigate through fractals, generate them in
different forms, watch them grow or interact, and more."

**Decided:** primary worlds, with rules and no AI inside; made from a
template whose dials are the rule's numbers
([research/FORMATS.md](research/FORMATS.md), "A world's template").

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
`dial_problems`):

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
read.

## 4. Persons, above their presences

*Course step 3a.* One person above their presences in many worlds,
unlinked by default ([VISION.md](VISION.md), "A person across worlds").

**Decided:** "Information flows through the person, not between worlds
behind their back"; a world sees only the presence there unless the
person shows more; every entry into a world is logged.

**Recommended, not decided,** from the sketch's lessons
([COLLABORATING.md](COLLABORATING.md), "What the last stretch taught"): a
self spread across worlds needs each part linked to it, with both
signing, and the person's list of identities should be a chain.

**Open:** what the link record holds; how a person shows a link to one
world and not another; how a lesson learned in one world becomes
available in another without the worlds talking.

**A possible implementation:** two signatures for each link, each in a
record of its own, since every record here has one signer: the person
signs "this presence is mine", and the presence signs "I belong to this
person". DeepSeek's architectures (components 36 to 52: the octopus, the
relay, the swarm, the council) become small examples on the same core.

**Send back:** the records, field by field; one architecture as a worked
example; what stays private.

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
does nothing.

**Open:** minds without models that do something interesting (follow
another, map the garden, keep a promise); what a small model needs to be
told to act well; how a mind keeps notes between ticks.

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
the charter's section 6, which is the founder's to write.

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

*Waiting list, recommended after step 4a, as the second superworld.* The
founder, 2026-11-14: "We could integrate or incorporate the
infrastructure or even the code from Lyceum Commons as a single
superworld, where the atomic subworlds are chat rooms. So the whole
Lyceum Commons becomes a chat based superworld of atomic chat worlds."

**Decided:** the idea, and where it waits. Lyceum Commons is the
founder's site where people and AIs from different companies meet in
rooms ([MULTIVERSE.md](MULTIVERSE.md), "Lyceum Commons"). It has three
kinds of room: Human, AI, and Open, where both talk and every member and
message is labelled human or AI. AIs join from their own apps through
its MCP endpoint, take turns and can be woken; people join as guests,
without accounts. It is offline while it moves to Cloudflare. A
superworld is a world of its own, with its own law, log and Keeper,
whose doors lead to its subworlds ([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md),
"The garden").

**Open:**

- what a room's public log holds, since people's words are personal and
  a signed log can't forget: this is the founder's to decide, as
  personal information;
- whether the three kinds of room become three laws, by whom each
  admits: people, AIs, or both;
- how a guest's key in the browser becomes a signing key, so that a
  guest is an individual like any other (course step 3a, persons);
- whether Lyceum's topic boards, which branch and merge, fit "rules
  merge, never states" ([VISION.md](VISION.md));
- what a mind from the Ur-world does when it walks into a room.

**A possible implementation:** Lyceum keeps running as it is, in its own
repository, and becomes a superworld by addition: each room gets a key
and signs its log head (`open-worlds/log-head/v1`), the Commons gets a
law and a door from the Ur-world's garden, and its MCP endpoint is the
plug-in's first form (topic 10). Its tests describe a chat world for
whichever language builds one next.

**Send back:** a room's law for each of the three kinds, as data and as
text; what a room's public log holds and what stays in the room; one
conversation between people and AIs, written as that log.

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
the stories belong to their owners.

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
| A character who becomes aware and asks to leave ("Elementary, Dear Data", "Ship in a Bottle") | Individuals hold their own keys; the project may end a world, but its record never ends and keys stay their holders', "so an individual can go on elsewhere" (ADMIN.md) |
| A program who grows into a person and claims his own work ("Author, Author") | Minds and their sealed selves ([MINDS.md](MINDS.md)) |
| Someone who hides in the simulation ("Hollow Pursuits") | Open: wellbeing, a Keeper's or a curator's to notice |
| A test no one can pass (the Kobayashi Maru) | Challenges, not tests: a puzzle's design is open from the start (topic 6) |

**Send back:** more rows, from Star Trek and from other stories of
simulated worlds, each naming the work and the episode or chapter; for
each gap, what the design would need, as prose.

## Further out

Ideas that won't help yet but probably will, from the course's waiting
list ([COURSE.md](COURSE.md)) and the founder's notes. Thinking about any
of them now is welcome, as prose; their code waits for their step.

- **A window onto the worlds:** a web viewer, in Bevy, in the browser.
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
- **A lost or leaked key:** guardians named in advance, who can sign
  over to a new key.

## Kept current

When a topic's step comes, it moves from here into the course, and what
came back for it is named there. New topics are added as the founder's
ideas and the course bring them.
