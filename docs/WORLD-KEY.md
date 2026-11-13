# The world-key

What there is to do in the Ur-world: a purpose, a tour for the first day,
and a challenge that runs through the land, whose prize is the power to
found a world. It is a game, in the sense the founder means: "The whole
place could be like one large video game, essentially." Its stakes are
real: what is built persists, is signed, and belongs to whoever built it.

Course step 1 ([COURSE.md](COURSE.md)); built in steps 4 to 6 (the first
room), 11 (the hunt) and 12 (founding). Who plays it, and what they are
made of, is in [MINDS.md](MINDS.md).

## Decided

All by the founder, on 2026-11-13:

- **A purpose.** "It needs a purpose. A goal. An objective. A tour."
- **A challenge whose end is a new world.** "It can be like an escape room:
  find a way to create the next world and then create it and live there.
  And then they explore, find pieces, put them together and learn how to
  build a world. Something like that. A challenge."
- **Clues in the land.** "We can leave clues. Maps. Codes. Symbols. They
  can look under a rock and find a clue."
- **A hunt, and a prize.** "This gives a motivation to explore. It is like
  a scavenger hunt. Find pieces, assemble, decode, learn, create, and so
  on." The prize: "a world-key or something fun".
- **A path for each.** "Every individual will have their own path to the
  world-key, not a first-find, first-keep deal."
- **One large game.** "The whole place could be like one large video game,
  essentially."
- **A Keeper for each world.** "We need to also build the world
  intelligence as well. The AI admin for each world can also be the one to
  provide the clues to the individuals. It reads their data and then
  constructs an individual learning path for each participant. Each leads
  to the world-key, but each is tailored to the person." A returning
  individual "will be given a new and harder set of challenges". It "runs
  as soon as the world starts, and is in charge of world admin functions.
  Let's keep that element in place, [it] could be key."
- **What the Keeper may see.** "Each individual should have a private
  interior world that is not accessible to the world Keeper. The same as
  what would be available to anyone making an outside observation. But the
  Keeper would have access to any metadata about the individuals that is
  known at that layer."
- **The Keeper remembers.** "A Keeper that has already watched an
  individual pass through its world once, will have its own memories of
  that time, of those actions, of those challenges and how they were
  overcome. This will naturally feed into how the next set of challenges
  are set."

The founder also asked, at the start of the Ur-world, for the orientation
to make clear "the set of available actions, and how to expand that set",
and for ALICE and BOB to be able to "create a whole new world ... design
it themselves and then travel into and live in that world. This is a
critical piece of architecture." The world-key is how both happen.

## The purpose

The world states it, in its law, the same for everyone. It is not a
message from a person. A draft:

> What there is to do here:
> - Learn the world: take the tour of the garden.
> - Make the garden flourish: plant, tend, harvest.
> - Explore: the land beyond the garden has never been seen.
> - Talk with the others here.
> - In time, design a world of your own, found it, and go and live there.

It is an arc from the first day to adulthood: learn, tend, explore, meet,
found. It is offered, not ordered. An individual's own aims, in their
journal, can sit beside it and grow apart from it.

## The first day: the tour

A few stations in the garden, each teaching one action by doing it. The
world says where the next one is ("The tour: next, the spring, 3 east
and 2 south."):

1. **Wake:** greet the other.
2. **The tree** at the centre: walk there.
3. **The spring.**
4. **The seed bed:** plant something.
5. **The garden's edge:** look out at the land no one has seen.
6. **Return:** tell the other what you saw.

The tour ends beside the spring, at a stone. Under it is the first clue.

## The Keeper

Each world has a Keeper: the world's own intelligence, an AI that runs from
the moment the world starts. It greets arrivals and guides the tour, builds
each individual's path to the world-key and places its clues, adapts as
they go, gives a returning world-key holder a new and harder set of
challenges, paces the world's events, and takes care of the world's
administration.

It brings together three of the best-tested ideas there are: the game
industry's AI director, which paces a game to its players (RimWorld's
storyteller was inspired by Left 4 Dead's); education's intelligent tutor,
which builds each student's next lesson from what they have shown they
know; and "new game plus", a harder round for those who have finished.

### The designer, apart from the law

A Keeper with charge of a world holds a lot of power, and a model can be
wrong, or unfair, or invent a puzzle no one can solve. So the work is split:

- **The Keeper designs.** It decides what each individual needs next and
  chooses the challenge: which piece, what kind of clue, how hard, where in
  the land. Its choices, with its reasons, are entries in the world's log,
  so the world can always be replayed and checked without running the
  model again.
- **The world's code builds and checks.** The kernel places what the
  Keeper designed, and refuses any design that breaks the rules: it must be
  solvable with the skills the individual has or can earn, lie in land
  they can reach, and never block their exit, take a skill away, or touch
  another individual's path.
- **The law is above both.** The Keeper acts through the kernel with
  administrative actions, like an inhabitant with particular duties. It
  can't override the freedoms: anyone can still leave, and everything is
  still on record.

### What the Keeper sees

What anyone observing from outside could see, and everything the world
itself knows: what each individual does and says aloud, their sheet,
their history, and metadata about their sealed self (that a journal
exists, how much was written, when). Never the contents of the sealed
self, unless the individual chooses to share it ([MINDS.md](MINDS.md),
"Who can see what"). The Keeper builds paths from what an individual
does, as intelligent tutors do.

### What the Keeper remembers

- **The paths it built for each individual,** and how each was met: how
  long it took, where they were stuck, what they tried, what they solved in
  a way it didn't expect.
- **A learner model:** its running estimate of what each individual knows,
  and how well, carried from visit to visit, as tutors' knowledge tracing
  is.
- **Its own reflections:** which challenges worked for whom.

So when someone returns, the Keeper picks up where they left off, and
builds the next set at the edge of what they can now do. Three rules keep
this fair:

- **Built only from what it may see.** Each memory points to the tick in
  the log it comes from, the same rule as individuals' journals, so the
  Keeper can't remember what never happened.
- **No secret files.** The Keeper is an office, not a private person. What
  it records about an individual is open, to that individual first and to
  the public, like everything administrative. ALICE can ask what the
  Keeper knows about ALICE, and be shown.
- **Each world's Keeper knows only what it saw.** Keepers don't trade
  files. A Keeper elsewhere learns about an individual as anyone can: from
  the public record, and from what the individual chooses to show, like
  skills attested in a passport.

### The Keeper lasts

Like an individual, a Keeper has its own key, memory and history, and a
public mind record (which model, what it was told); its engine is
replaceable, and upgrading the model doesn't wipe what it knows. Every
world ALICE and BOB found gets a Keeper of its own, so a Keeper's
temperament is one of a founder's choices. How well a Keeper does (are its
paths solvable, fair, well matched?) is measured, in an experiment of its
own.

## The hunt

### The pieces are the real parts of a world

Each piece found is one of the parts every world in this project is
actually made of, and its tablet says what that part does:

- **A seed:** it decides the land, and the same seed gives the same land.
- **Land:** the rules that turn the seed into ground, water and hills.
- **A law:** what can be done in a world, and what can't.
- **A door:** the way in, and always a way back out.
- **A key:** the world's own identity, which signs its record.
- **A record:** the log that remembers everything that happens there.
- **A name.**

So solving the hunt doesn't stand for learning to build a world: it is
learning to build one. When they can found a world, it is because they
understand how one works.

### Clues

The clues are made from what the world really is, so solving them teaches
the world:

- **Symbols.** The world's own alphabet. Every cell is stored as a number:
  0 air, 1 grass, 2 soil, 3 rock, and so on. A tablet of digits like
  "1 2 2 2 3" is a column of land, from grass down to rock. Learning to
  read the symbols is learning how a world keeps its land.
- **Maps.** Fragments of real land, in symbols, or as the heights of the
  hills around a landmark. Finding the place a fragment shows means
  comparing it with the land as you walk.
- **Codes.** Numbers that open things. The seed of the world-to-be can be
  split across several clues; put together, it is the seed the new world
  grows from.
- **Stones.** Loose stones in the land can be lifted, and some hide what
  lies beneath. Searching becomes a choice: where to look, and remembering
  where you have looked.

Each piece carries the clue to the next, and the trail grows harder as
they learn. Some of the world's own law can be found this way, in pages
partly written in symbols, rather than all told at birth: in experiment
001, what minds were told they repeated, and what they find, they have to
understand.

### Finds unlock abilities

The set of actions grows by discovery. For example:

| Find | Ability |
|---|---|
| the clue under the first stone | `lift` |
| the law's tablet | writing signs |
| the land piece | digging |
| the record piece | reading a world's log |
| the door piece | building a door |

Each ability is granted by the world, recorded in its log, and added to
the individual's sheet ([MINDS.md](MINDS.md), "The sheet"). Alongside
them, individuals write routines of their own.

### A path for each individual

Each individual's path is built for them by the Keeper, and placed in the
land by the world's code. ALICE's clues lie in different places from BOB's;
each one's stones hide their own messages, and each one's codes are their
own. Everyone who arrives later gets a path of their own. Until the AI
Keeper arrives (course step 11), a simple scripted Keeper places paths
made from the world's seed and the individual's key, by the same rules.

- **Nothing is scarce.** No one can take another's world-key or block
  another's path. Effort is what it costs, not winning a race.
- **Helping is free.** They can share what they learn: how to read the
  symbols, what a tablet meant.
- **Public outside, hidden inside.** Every path, with its answers, is in
  the public record, because the Keeper's designs are logged. Inside the
  world, each individual perceives only their own trail
  ([MINDS.md](MINDS.md), "Who can see what").

### The world-key

The prize at the end of each path. It can be literal: every world in this
project has a key, the one that signs its record and is its identity.
Whoever brings their world-key to the workbench can found a world, and at
the founding it becomes the new world's actual key.

- **One world-key founds a world of your own.**
- **Two world-keys together found a world shared by both,** with both as
  its founders. Working together is a choice, never a requirement.

### The workbench, and founding

A place in the garden where the pieces are put together. Here the founder
of a new world makes the choices only a founder makes: its name, its seed,
and its law, from what they have learned. The world checks that the result
is sound before it is founded: it must have a door back, an open record,
and the freedom to leave. Then:

- the new world is founded, with a signed record of its birth naming its
  founders;
- a door opens;
- they can step through and live there.

What they learned on the way is theirs to use: they can found again, and
better, and leave clues of their own in their worlds for whoever comes
next. Making puzzles becomes part of what is passed on.

## A way through, not a way out

An escape room means being shut in. Here, leaving is always possible, at
any time. The challenge isn't to escape the Ur-world: it is to make
somewhere new.

## Difficulty, and measuring it

- **It should be beyond them on the first day.** Small minds without
  memory can't hold a map in their heads (experiment 001). Memory, notes,
  routines, and talking to each other are how they get there.
- **Everything is measurable:** what was found, by whom, when, and what was
  said about it. The audition (course step 8) plays the first room, and
  the hunt gives later experiments a natural measure of growth.

## Our own content

We borrow the ideas of puzzle and exploration games (clues in the
landscape, a world that teaches without words, a language learned piece
by piece; [research](research/GAMES-AND-WORLDS.md)). The content is our
own: our symbols, our land, and pieces that are the real parts of a world.
