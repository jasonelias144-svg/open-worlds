# The world-key

What there is to do in the Ur-world: a purpose, a tour for the first day,
and a challenge that runs through the land, whose prize is the power to
found a world. It is a game, in the sense the founder means: "The whole
place could be like one large video game, essentially." Its stakes are
real: what is built persists, is on record, and belongs to whoever built
it.

Course step 1 ([COURSE.md](COURSE.md)); built in steps 4 to 6 (the first
room), 11 (the hunt) and 12 (founding). Who plays it, and what they are
made of, is in [MINDS.md](MINDS.md). This page describes what is to be
built; where something exists already, it says so.

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
- **The world-key opens only for its earner.** "A world-key could be
  generated from the individuals public key and the world public key. It
  would be readable only by the individual, since they have the
  corresponding private key that matches the public one." That is, each
  side's private key with the other's public key (Diffie–Hellman): "That's
  what I meant, just expressed sloppily."

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
storyteller was "modeled after the AI Director from Left 4 Dead",
[wiki](https://rimworldwiki.com/wiki/About_RimWorld)); education's intelligent tutor,
which builds each student's next lesson from what they have shown they
know; and "new game plus", a harder round for those who have finished.

### The designer, apart from the law

A Keeper with charge of a world holds a lot of power, and a model can be
wrong, or unfair, or invent a puzzle no one can solve. So the work is split:

- **The Keeper designs.** It decides what each individual needs next and
  chooses the challenge: which piece, what kind of clue, how hard, where in
  the land. Its choices, with its reasons, go into the world's log. While
  a challenge is unsolved, the log holds only a commitment to it: a hash
  of the design and its reasons together with a secret random value, so
  that no one can find the answer by hashing guesses, however few the
  possible answers. The design, its reasons and the random value are added
  when it is solved, or when the path ends. Anyone can then check them
  against the commitment, so nothing can have been changed along the way,
  and no one can read an answer from the record ahead of time. Once a
  path is revealed, the world can be replayed and checked in full without
  running the model again.
- **The world's code builds and checks.** The kernel places what the
  Keeper designed, and refuses any design that breaks the rules: it must be
  solvable with the skills the individual has or can earn, lie in land
  they can reach, and never block their exit, take a skill away, or touch
  another individual's path.
- **The law is above both.** The Keeper is a model the project didn't
  write, so, like every mind, it runs as its own program, outside the
  kernel. It acts through the kernel with administrative actions, like an
  inhabitant with particular duties, and its designs come back to the
  world as actions do, to be checked. It
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
  Keeper knows about ALICE, and be shown. The one thing held back is the
  answer to a challenge not yet solved, and only until it is solved.
- **Each world's Keeper knows only what it saw.** Keepers don't trade
  files. A Keeper elsewhere learns about an individual as anyone can: from
  the public record, and from what the individual chooses to show, like
  skills attested in a passport.

### After the world-key: letters, and friends

An idea of the founder's: "Perhaps, after finding the world-key, you can
communicate with the world Keeper directly ... You can have an on going
conversation with a world after leaving. And then return back later, as a
friend, potentially."

Before the world-key, the Keeper speaks only through the land, or the hunt
would stop being a hunt. Once someone holds it, there is nothing left to
give away, and the Keeper can stop being a guide and become a friend.

- **Letters, not a live line.** Worlds run at different speeds, and one
  may be paused while another runs. A letter is delivered at the reader's
  next tick, wherever they are.
- **Still one door into a mind.** A letter arrives as part of what its
  reader perceives that tick ("A letter from the Keeper of the Ur-world:
  ..."), never by a way around the doorway.
- **Signed and recorded,** like everything that crosses between worlds: in
  the sender's log and the reader's.
- **A friend is a relationship on record,** built from letters and visits.
  It is never favouritism: a friend's challenges still sit at the edge of
  what they can do. A friend can be invited to give back: guide a
  newcomer's tour, or design a challenge for someone else, which the
  world's code checks like any other design.
- **Not decided:** whether letters are public, like speech in the world
  (recommended, since the Keeper is an office with no secret files), or
  private between the two.

Letters between worlds need the world protocol in Rust, so they come with
course step 12; the Keeper's side, with step 11.

### The Keeper lasts

Like an individual, a Keeper will have its own key, memory and history,
and a public mind record (which model, what it was told); its engine is
replaceable, and upgrading the model doesn't wipe what it knows. Every
world ALICE and BOB found gets a Keeper of its own, so a Keeper's
temperament is one of a founder's choices. How well a Keeper does (are its
paths solvable, fair, well matched?) is measured, in an experiment of its
own.

## The hunt

### The pieces are the real parts of a world

Each piece found is one of the parts a world in this project is made of,
and its tablet says what that part does. (The Ur-world has some of them
today, its seed, land, law, door and record; it gets its own key in
course step 3.)

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
land by the world's code. ALICE's clues lie in different places from BOB's,
and each one's codes are their own. Everyone who arrives later gets a path
of their own. Until the AI Keeper arrives (course step 11), a simple
scripted Keeper places paths by the same rules. It makes each one from the
world's seed, the individual's identity from birth (which stays the same
even if their key is replaced), and a secret of the world's own, so no one
can work a path out ahead of time. That secret is kept beside the world's
key, but apart from it, so replacing the key doesn't reshuffle anyone's
path; the commitments' random values are derived from it too.

Stones are part of the shared land, but what lies under one is particular
to each individual: the world shows each their own clue there, or
nothing. So ALICE lifting a stone, or standing on one, never hides BOB's
clue.

- **Nothing is scarce.** No one can take another's world-key or block
  another's path. Effort is what it costs, not winning a race.
- **Helping is free.** They can share what they learn: how to read the
  symbols, what a tablet meant.
- **Open, but not ahead of time.** Every path goes into the public
  record: a commitment when it is placed, and its whole design, answers
  included, once it is solved. Inside the world, each individual perceives
  only their own trail ([MINDS.md](MINDS.md), "Who can see what").

### The world-key

The prize at the end of each path: the right to found a world. It is a
credential, signed by the Ur-world, that names the individual who earned
it, so it can't be taken, copied or used by anyone else, and a world
honours it only from its holder. Anyone can check it with public keys
alone.

It comes in a sealed box, the founder's idea. The box is sealed with a key
that only two can make: the Ur-world, from its private key and the
earner's public key, and the earner, from their private key and the
Ur-world's public key (Diffie–Hellman, the way secure web connections
begin). The pieces of the path go into that key as well. So the box can
lie in plain sight from the first day, and it opens only for its earner,
and only once their path is done. The "key" piece of the hunt teaches how
this works. (As with the sealed self, the earner's private key is held by
the project's software, which acts for them; the mind never sees it.)

It is not the new world's own key. A world's key is its identity, and the
private half of a key must never be something that could be worked out
from a record. So at the founding, a new key pair is made for the new
world: the private half goes where all private halves are kept
([MINDS.md](MINDS.md), "Where everything lives"), and the new world's
birth record names the public half, signed by the Ur-world and by the
founders.

- **One world-key founds a world of your own.** It is marked as used at
  the founding; the next comes at the end of a new, harder path.
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

And leaving is not the end. The founder means "the same person returning
to the world later" to be given a new and harder set of challenges, so
whoever leaves can come back. Today, a name that has left the Ur-world can't be used
there again, so that no one else can take it over. Once identities have
keys (course step 3), whoever left can return by proving, with their key,
that they are the same individual, and their name stays theirs.

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
