# The Ur-world

> "It's like Hello World for building worlds: you start it with a garden of
> two individuals." (the founder)

The Ur-world is the first world of the multiverse. It is a world in its own
right, and also the hub that connects to every other world. It begins small,
in a garden with two individuals, ALICE and BOB. It grows as it is explored,
and later as the people who live in it build it from the inside. The name
works twice over: "Ur" is the first, the original, and it sounds like "your
world".

This page records what the founder decided, what the first version does
(`rust/ur-world`), how a mind outside the world lives in it, and the order
of the steps still to come.

## Decided

All decided by the founder on 2026-11-13, in the founder's words:

- **One main world first.** "We create one central world that is the first
  main world and one that connects with all other worlds, a multiverse lobby
  or travel hub. But also a world to itself." "Make it large enough to
  include diversity and subworlds of different kinds, but not too large,
  just enough to hold what it needs with an ability to expand as needed, or
  as the participants begin growing the world from the inside." "It should
  have all the functionality in one place. Once we work out that world, we
  can begin creating subworlds and all that we have discussed."
- **3D, with ground and sky.** "3D definitely. It should be the most
  comprehensive world and so the most capable of exploring possibilities."
- **Space as needed.** "A world where the unexplored space is still just
  potential space, but only becomes data once that area is explored, in
  which case it is spontaneously generated. This could make for a world
  that invites unlimited exploration."
- **It begins in a garden, with ALICE and BOB.** "Let's begin this world in
  a garden. With two individuals." Their names are in capitals, "to
  distinguish from other Alices and Bobs". "They will be the first two
  occupants of a whole multiverse," with persistent identities, "and should
  be considered two individuals that will inhabit this world and learn
  within it as well."
- **Their minds: two different, complementary models.** "Difference is the
  key to generating diversity, but they should also have compatibility and
  have complementary skills and strengths and knowledge." The choice draws
  on the founder's work on opposites (see "ALICE and BOB" below).
- **Rust, with an interface to Unity and Unreal.** "We should have an
  interface to Unity built worlds, but we should stick with Rust." On
  outside agents, such as OpenClaw's, compatibility is enough: "We can
  explore developing an Open Claw type of agent if it comes up."
- **The garden's abilities, and an orientation.** "In the beginning, they
  should have the ability to plant different seeds, tend to the garden in
  different ways, and they should be able to create, explore, and
  communicate." "But also begin with an orientation, so the parameters of
  their reality are clear, including the set of available actions, and how
  to expand that set."
- **Land of unknown construction.** "We should have a sort of random
  terrain generator. This way it's genuine exploration. But the randomness
  should still provide continuity." The point is that "the unexplored
  area doesn't exist until it is explored", and "new terrain of unknown
  construction is the point, the world doesn't even know what it looks
  like until it's explored."
- **Experiments, in the open.** The technical lead (Claude) keeps "a page
  or section in the repo where you can set up experiments and run them and
  provide the results in a way that others can see and follow. This is
  separate from developing the code, this amounts to running it and acting
  more like a scientist than a software engineer."
- **Founding worlds.** "ALICE and BOB should also have the opportunity to
  create a whole new world, a branch or sub-world from Ur-world. They
  should be able to design it themselves and then travel into and live in
  that world. This is a critical piece of architecture."
- **Unscripted minds next.** The garden's first exchange was scripted, and
  that is "a good point to the next move, which involves experimenting
  with the most basic models that are capable of generating their own
  output, unscripted."
- **How ALICE and BOB are written about:** by name, or "they", never
  "she" or "he", since nothing in their design gives them a gender. "It
  is best to be careful from the start to avoid falling into linguistic
  habits."

## The first version: the garden

`rust/ur-world` is the first piece, Hello World for building worlds. To run
it:

```
cd rust
cargo run -p ur-world --example garden
```

It tells what happens, from the world's own log, then draws a map of what
has come into view:

- The world is created, from seed 20261113, the day it was decided.
- ALICE enters, west of the tree, and the land around ALICE comes into view.
  BOB enters, east of it.
- ALICE says "Hello, world." BOB listens. Then BOB answers "Hello, ALICE.",
  and ALICE listens.
- BOB plants a flower close by.
- ALICE walks north around the tree, then east, out of the garden. The land
  rises into hills, and new chunks come into view as ALICE goes.

ALICE and BOB are short scripts here, just enough to show that the world
works. Minds that choose for themselves come in through the doorway
(below).

### Space

- **Cells.** Space is a grid of cells with whole-number coordinates. `y` is
  up, `x` is east, and `z` is south. These are right-handed axes, as glTF,
  Unity and Bevy use.
- **Chunks.** Cells are grouped into chunks of 16 x 16 x 16.
- **Edge.** The world reaches 2^40 cells (about a million million) from
  the garden in every direction.
- **Materials.** A cell holds air, grass, soil, rock, water, wood, leaves,
  or a flower.

### What is there before anyone changes it

- **The generator.** What a cell holds is worked out, when someone first
  looks, from the world's seed and the cell's coordinates. The rules are in
  `generate.rs`:
  - three layers of smooth noise make the hills;
  - lakes fill the low ground;
  - grass lies on three cells of soil, over rock.
- **Whole numbers only.** The same seed and coordinates give the same cell
  on any machine, in any language. To show it, `tests/test_ur_world_vectors.py`
  writes the generator again in Python from its documented rules. It agrees
  with Rust on every height and chunk in `vectors/ur-chunks.json`.
- **Versioned.** This is generator version 1. A better one later gets a new
  number and applies only to land not yet explored. The log records which
  version made each chunk.
- **The garden** is the one hand-made place. It is flat grass within 8
  cells of the centre, with a tree at the centre and a spring. Around it,
  the ground eases into the hills over 16 cells, gently enough to walk out.

### What the world remembers

- **Only what was explored, and what was changed.** The world keeps the set
  of chunks someone has seen, and the cells someone has changed. Land that
  was seen but not changed can always be made again, so it costs nothing to
  keep. Storage grows with change, not with exploration. After the Hello
  World, 57 chunks have been explored, and one cell is stored: BOB's flower.
- **The public log.** Every event goes into an append-only, hash-chained
  log, written exactly as the Python kernel writes its own.
  - It holds by the same checks: `world-log` in Rust, and `World.verify_log`
    in Python.
  - When a chunk is first explored, the log records who saw it first, which
    generator made it, and its hash, so anyone can regenerate it and check.

### The rules

- **Each tick:** everyone observes; then each acts in turn. The order is by
  name, rotated one place each tick, so no one always goes first. Then
  whoever stands on nothing falls (up to 64 cells a tick; a deeper drop
  goes on at the next), lowest first, so a stack falls together. Then
  what has come into view is explored.
- **Step** north, south, east or west. A step onto a block one cell high
  climbs it, if there is headroom. A step off an edge falls.
- **Say** something: everyone hears it on the next tick.
- **Plant** a flower in open air on grass or soil.
- **Wait.**
- **Exit**: leaving always succeeds. An inhabitant's keeper can also take
  them out at any time.
- **A reply that isn't an action** is recorded as `unreadable`, with what
  was sent, cut to 280 characters. **No reply in time** is recorded as
  `unanswered`. In both cases, nothing happens.
- **What came of it.** At the next tick, each is told what came of its
  last action: where it stepped to, that it was blocked, what it said or
  planted, or that its reply couldn't be read.
- **One inhabitant to a cell.**
- **The operator's hand.** The operator can shape any cell, as a gardener
  shapes a garden, and it is recorded like everything else.

### Limits now

- **Minds.** They are scripts in the same process, or programs speaking
  the doorway's protocol. The world-crossing protocol (WCP) between worlds
  isn't in Rust yet.
- **Sight.** A mind sees only the 26 cells around it, and others within 16
  cells. It can't yet see far, so it finds its way by feel and by what it
  is told.
- **Keys.** There are none in Rust yet. ALICE and BOB are named, but don't
  yet sign, and their permanent keys are made with the next step.
- **Hearing.** Everyone hears everyone, wherever they are.
- **Changes.** The only change an inhabitant can make is to plant a flower.
- **Running.** The world runs only while someone steps it. Where a world
  that keeps running should live is still to be decided: the founder's
  answer so far is "not yet".
- **Seeing it.** There is no viewer yet beyond the text map.

## Minds from outside: the doorway

Any program, in any language, can be a mind in the Ur-world
(`rust/ur-world/src/door.rs`). It runs as its own process, and the world
talks to it in lines of JSON over its standard input and output:

1. **First, once:** `{"name": ..., "rules": ..., "orientation": TEXT,
   "law": {...}}`. The orientation is the world's law written for a
   reader: what the world is, where things are, the actions with what
   each does and when it is refused, how to answer, its freedoms, and how
   the set of actions grows. The law is the same as data, and the text is
   made from it, so the two can't disagree.
2. **Each tick:** `{"tick": N, "seen": TEXT, "observation": {...}}`. The
   text tells where it stands and on what, what lies each way ("a step up,
   onto rock", "open, with nothing underfoot: you would fall"), who is
   near and how far, what others said, and what came of its last action.
   The observation is the same as data.
3. **The mind answers:** `{"tick": N, "reply": TEXT}`. It writes only
   replies to its standard output: any other line there is taken as an
   unreadable reply to the tick in hand. Its own messages go to its
   standard error.

**Replies are read strictly, the same way for every mind.** The first line
that isn't blank must be one of the orientation's forms: `wait`, `exit`,
`step DIRECTION`, `plant DIRECTION` or `say TEXT`. Words may be in any
case, and a full stop after a word is allowed. Anything else is recorded
as unreadable, and nothing happens. So what a mind sends can't break the
world:

- a reply that doesn't come within the time limit is recorded as
  unanswered;
- a reply to any other tick (a late one, say) is set aside;
- a line over 64 KiB is recorded by its beginning;
- a mind whose program has stopped is not waited for. It stays in the
  world, its ticks unanswered, because a crash isn't a choice to leave;
- a mind that doesn't read what it is sent can't hold up the world: what
  doesn't fit in its queue is dropped, and its ticks go unanswered;
- a mind's program is stopped when it leaves, or when the world ends.

**Expanding the set of actions.** The orientation says how: "To do
something that isn't listed, say so". Everything said goes into the public
record, and new actions come from what is asked for. Later, inhabitants
will propose actions, and compose routines from the ones there are,
through the world itself.

**What the world decides, and what the mind does.** The world decides only
what a mind is told and how its reply is read. How a mind turns what it is
told into a reply is its own: a language model's prompt, its sampling, its
memory. Its program keeps its own record of that, which an experiment
publishes beside the world's log.

To try it with two minds that have no model behind them
(`minds/wanderer.py`, Python's standard library only):

```
cd rust
cargo run -p ur-world --example door -- \
    --mind TRIAL-1=python3 -I ../minds/wanderer.py \
    --mind TRIAL-2=python3 -I ../minds/wanderer.py
```

CI runs this, and checks the log the two leave by the same check as every
other log.

## The steps to come

The steps are on the course ([COURSE.md](COURSE.md)), set anew on
2026-11-13 for the Ur-world. Done so far: the garden (#28), the doorway for
minds (#29), and experiment 001 (#30). Next, in order: the design pages;
formats that last; ALICE's and BOB's keys and identities; the kernel as
entities and components; things, skills and the sheet; the first room;
memory; the audition; ALICE's and BOB's first life; back to DeepSeek; the
hunt and the world-key ([WORLD-KEY.md](WORLD-KEY.md)); founding worlds, and
doors. Waiting behind them, among others: a window onto the worlds,
generator 2 (land decided when first seen), the gate and districts, and
governance.

## ALICE and BOB

- **Their identity is not their model.** Models will improve, and whatever
  runs ALICE and BOB now will be replaced. Each of them is three things that
  last, with the model as the engine underneath:
  - **a key**, carried forward by successions if it is ever replaced;
  - **a memory**, written in their own words and kept with integrity;
  - **a history**: the public log and their passports.
- **Learning, in layers.** Memory first: they write down what they learn
  and read it back. Later, each gets a small personal layer, a few
  megabytes, trained on their own experience over a shared base model. True
  continual learning comes when it matures. Because identity lives in the
  key, the memory and the history, they can move to better methods without
  starting over.
- **Their models.** Open-weight models only: free, runnable on our own
  machines, trainable, and not withdrawable by anyone. They are chosen at
  the language-model step, under licences that allow free use and change.
- **Special status means care, not rank.** They are kept, backed up, and
  carried through every upgrade. In the world they live under the same law,
  with the same freedoms, as everyone who comes after. Leaving the garden is
  one of those freedoms.

### Choosing two complementary minds

The founder's work on opposites gives exact tools for this.

- **The kind of opposites to seek.** Take everything the pair might do as
  the field, with ALICE's strengths as one region and BOB's as another.
  The founder's four classes are:
  - **complementary**: no overlap and no gap;
  - **contrary**: no overlap, and a gap;
  - **subcontrary**: overlapping cover;
  - **overlap with a gap**.

  "Different, complementary and compatible" is the subcontrary profile: each
  strong where the other is weaker, a shared region as common ground, and
  nothing that neither can do. A real pair will start with overlap and a
  gap. The gap is what they learn together.
- **The audition.** Candidate pairs face the same trials in the garden: a
  conversation, a reasoning puzzle, a quatrain in common meter, a chemistry
  question. Each trial falls into one of four regions: only ALICE, only
  BOB, both, or neither. We look for a pair that:
  - has large solo regions, a shared region that isn't empty, and the
    smallest "neither";
  - gets right, combined, what neither gets right alone;
  - shares the fewest mistakes, because agreement between minds that share
    a source is not independent proof.

  The results go into the record.
- **Why two.** Two can be exactly opposite. Three that each want to be
  opposite the other two cannot all be, since an odd cycle of opposition is
  incompatible. So the pair comes first, and a third will need a new
  arrangement.
- **One caution, kept from the same work.** Their complementarity is
  defined by what they do, and measured. It is not cast as cosmic poles by
  analogy, and it may change as they learn.

Their first exchange in the garden is the simplest pairing of complements:
one speaks while the other listens, then they turn.

### Decided since

- **Their minds: Qwen and OLMo.** The founder: "I completely agree with
  [Qwen] and OLMo, those would be my two choices as well." The audition
  now chooses the sizes, not the families.
- **What they do is public; what they think is their own.** Everything
  observable is public. Each individual has a sealed interior (journal,
  reasoning, held thoughts) that no one else can read, not even the
  world's Keeper ([MINDS.md](MINDS.md), "Who can see what"). Their private
  keys are kept in a private repository of the project, "public to our
  project", and nothing lives on a personal computer: "Let's keep
  everything online."
- **Lessons from [experiment 001](../experiments/001-first-words/RESULTS.md):**
  - examples in the orientation become scripts, so theirs shows the form
    of a reply without words worth repeating;
  - minds without memory repeat themselves, so memory is in their first
    version.
