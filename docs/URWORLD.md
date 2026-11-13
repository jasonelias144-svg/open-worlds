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
(`rust/ur-world`), and the order of the steps still to come.

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
  rises into hills, and new chunks come into being as ALICE goes.

ALICE and BOB are short scripts here, just enough to show that the world
works. They gain minds at the language-model step.

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
  goes on at the next), and what has come into view is explored.
- **Step** north, south, east or west. A step onto a block one cell high
  climbs it, if there is headroom. A step off an edge falls.
- **Say** something: everyone hears it on the next tick.
- **Plant** a flower in open air on grass or soil.
- **Wait.**
- **Exit**: leaving always succeeds. An inhabitant's keeper can also take
  them out at any time.
- **One inhabitant to a cell.**
- **The operator's hand.** The operator can shape any cell, as a gardener
  shapes a garden, and it is recorded like everything else.

### Limits now

- **Minds.** They are scripts in the same process. Outside minds will come
  through the protocol.
- **Keys.** There are none in Rust yet. ALICE and BOB are named, but don't
  yet sign, and their permanent keys are made with the next step.
- **Hearing.** Everyone hears everyone, wherever they are.
- **Changes.** The only change an inhabitant can make is to plant a flower.
- **Running.** The world runs only while someone steps it. Where a world
  that keeps running should live is still to be decided: the founder's
  answer so far is "not yet".
- **Seeing it.** There is no viewer yet beyond the text map.

## The steps to come

These will go onto the course (docs/COURSE.md) when it is next updated.

1. **The garden** (this). Hello World, in Rust, with its log checked from
   Python.
2. **Keys and the protocol in Rust.**
   - ALICE and BOB get their permanent keys. The keys are made once and kept
     off the repository; only the public halves enter the record.
   - The world signs its log.
   - The protocol (WCP) gets a Rust implementation, with test vectors shared
     with the Python one.
3. **The gate.** The hub district: the corridor of course step 5, with
   doors to other worlds. Travellers arrive at the gate with their
   passports.
4. **Districts.** Poetry and chemistry come in as the first districts.
   - Each speaks the protocol inside, so any district can later leave and
     become a world of its own, with nothing rewritten.
   - A district can be a pocket behind a door, "bigger on the inside",
     rather than taking room on the main map.
5. **Growth.** At first, the operators add land. After the governance step,
   participants propose new land and districts from the inside.
6. **Minds for ALICE and BOB.** The language-model step: their audition,
   their memory and their learning (below).
7. **The window.** A viewer, as a web page first, then Unity and Unreal
   through a C interface. Outside agents arrive through the network
   protocol.

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

### Still open

- **Memory.** Whether ALICE's and BOB's memories should be public, as their
  actions are (recommended, at least at first), or private, like a person's
  mind.
