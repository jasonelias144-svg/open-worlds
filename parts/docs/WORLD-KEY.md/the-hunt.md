> Part of `docs/WORLD-KEY.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "The hunt" to "Our own content".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/WORLD-KEY.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

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
world's seed and the individual's identity from birth, which stays the
same even if their key is replaced, so replacing a key doesn't reshuffle
anyone's path. Anyone can work a path out ahead of time, and that is
fine: a path is a set of challenges to do, and knowing them doesn't do
them, except for pieces with a fixed solution, where knowing gives the
solution away (above, "What makes a challenge").

Stones are part of the shared land, but what lies under one is particular
to each individual: the world shows each their own clue there, or
nothing. So ALICE lifting a stone, or standing on one, never hides BOB's
clue.

- **Nothing is scarce.** No one can take another's world-key or block
  another's path. Effort is what it costs, not winning a race.
- **Helping is free.** They can share what they learn: how to read the
  symbols, what a tablet meant.
- **Open from the start.** Every path goes into the public record,
  whole, when it is placed. Inside the world, each individual perceives
  only their own trail ([MINDS.md](MINDS.md), "Who can see what").

### The world-key

The prize at the end of each path: the right to found a world. It is a
credential, signed by the Ur-world, that names the individual who earned
it, so it can't be taken, copied or used by anyone else, and a world
honours it only from its holder. Anyone can check it with public keys
alone.

It is given in a sealed box, using the founder's idea. When the world's
code confirms that the path is done, and not before, the Ur-world signs
the world-key, naming its earner, and seals it for them. The seal is made
from a fresh one-time key and the earner's public key, so that only the
earner, with their private key, can open it (Diffie–Hellman, in HPKE's
base mode, RFC 9180). Who issued it is shown by the Ur-world's signature
inside, and whoever opens it checks that it names them, so a world-key
sealed again for someone else is refused. The box is placed at the end of
the path, and the "key" piece of the hunt teaches how it works.

The founder's idea made the seal from the two keys themselves, "generated
from the individuals public key and the world public key" (HPKE's Auth
mode). The technical lead chose base mode instead, on 2026-11-13: the
Python library this project already uses can't seal in Auth mode, and the
signature inside says who issued the world-key, which, for the earner,
covers what Auth mode would add, and can be shown to others too
([research/FORMATS.md](research/FORMATS.md), "Sealing").

Two honest limits, until each individual holds their own private
container ([CONTAINER.md](CONTAINER.md)). The Ur-world knows what is in
the box, since it wrote and signed it, and anyone with the private
repository can open it, since the earner's private key is kept there
([MINDS.md](MINDS.md), "Where everything lives"). And the earner's
private key is held by the project's software, which acts for them; the
mind never sees it. Once the individual has a container (the technical
lead's recommendation, which stands unless the founder answers
otherwise), their key is made in it, and the second limit becomes the
one every mind the project runs has: it runs on the project's machines.

As the founder noticed, "Alice and Bob have been exchanging keys from the
start": Alice and Bob have been the names of the two people in a
cryptography example since Rivest, Shamir and Adleman's 1978 paper on RSA
([Wikipedia](https://en.wikipedia.org/wiki/Alice_and_Bob)).

It is not the new world's own key. A world's key is its identity, and the
private half of a key must never be something that could be worked out
from a record. So at the founding, a new key pair is made for the new
world: the private half goes where all private halves are kept
([MINDS.md](MINDS.md), "Where everything lives"), and the new world signs
its own birth record with it, which binds that key to the world. The
Ur-world and each founder confirm the founding in records of their own,
naming that birth record; the Ur-world's names the world-keys used
(course step 12; [research/FORMATS.md](research/FORMATS.md), "Who an
individual and a world are").

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

## Challenges that build the world

The founder, 2026-11-15, in three messages:

"Here is a new thought: perhaps, when entering a world there a various
interaction modes to engage in. One could be exploration. Or creation,
or experimentation. But in each world there is also a game layer, and
that relates to the world-key. Here is the new idea: the challenges are
constructive. The first could be to plant a certain number of fractals
in a certain place, and that leads to the expansion of the garden. The
next individual is given a series of challenges that amount to finding a
source of water and irrigating the new garden. The next person is tasked
to explore and plant trees. And so on. Anyone engaging in the game layer
would be building the world actively. This ties the keeper AI with the
challenges, as it becomes how the world grows internally. Or one way it
does."

"Perfect. But credit is not the point but learning. You would not
complete a challenge by getting credit for this or that, but by being
capable of doing this or that. Also, consider groups may arrive together
and work on a set of group challenges together. There may be open task
or challenges. Not everything needs to be for credit, it should be about
the experience or skill that is learned in the process. It should be a
challenge. My examples were not precise. They may have to figure out the
goal is to plant, that may take learning subskills. Either way, this
could unfold in many ways, we should try to accommodate as many
possibilities as we can imagine."

"And keep in mind. Someone may way to go through a number of challenge
cycles in a world, and the keeper, like a good teacher, would just give
harder tasks each time, ways to practice new skills and reinforce old
ones. And all for the greater good of the world, which is available for
everyone. Also, keep in mind how many problems arise from space
limitations. Being able to expand the world map space through the act of
exploration allows everyone to create freely, without any need to affect
others. But others could build together, and that would be possible too.
Much source of problems fall away when space is infinite and resources
are endless. We shouldn’t expect conflict to arise from freedom in such
an infinite space."

The technical lead's reading, put to the founder the same day; it
stands unless the founder answers otherwise, and stays open, as the
founder asked: "Either way, this could unfold in many ways, we should
try to accommodate as many possibilities as we can imagine."

- **Ways to be in a world.** Exploring, creating and experimenting are
  open to anyone. The game layer, with its challenges and the world-key,
  is taken up by choice; someone who only explores loses nothing. Each
  world's law says which ways it offers.
- **A challenge builds the real world.** What it builds stays in the
  world, open to everyone. The Keeper doesn't build the world itself: it
  proposes the world's growth as challenges, and people carry them out,
  as the Keeper designs and the world's code places (above, "The
  designer, apart from the law"). It is one way a world grows, as the
  founder put it; exploring grows the land too.
- **Done means capable.** A challenge is done when the world sees the
  individual do it, so a challenge that builds uses only pieces whose
  doing is the skill (above, "What makes a challenge"). The hunt keeps
  both kinds, as that section says: pieces with a fixed solution stay as
  clues that lead somewhere, and where a path means to teach a skill, it
  uses pieces whose doing is the skill. The log records what happened,
  as it records everything; it is not a score.
- **The goal can be part of the challenge.** A challenge can begin as a
  situation, a dry and empty plot, and not an instruction; working out
  that the goal is to plant is part of it. When someone is stuck, the
  Keeper offers smaller challenges that build the subskill they lack.
- **Many kinds, side by side:** a path of one's own; challenges for a
  group that arrives together; open tasks anyone can take up at any
  time; and no challenge at all. Founding together is already planned
  (course step 12).
- **Cycles, as many as someone wants.** Each is a little beyond what they
  can already do, and old skills come back, mixed in with new ones, so
  they stay. The Keeper's running estimate of what each individual knows
  (above, "What the Keeper remembers") is what lets it teach this way.
- **Nobody waits on anybody.** Each challenge comes from what the world
  needs now, not from a queue: if the garden isn't planted yet, the next
  person gets a different need. No challenge asks anyone to undo
  another's work.
- **Room without end, in practice.** The Ur-world reaches 2^40 cells
  from the garden in every direction (`LIMIT` in
  `rust/ur-world/src/space.rs`: "Far enough to be endless for anyone
  walking it"), generated from its seed as it is explored. Land is
  computed again from the seed when needed: only what has been explored
  (a set of chunks) and what has been changed (a map of cells) is kept,
  and the log records what happens. So anyone can create freely a little
  further out, and building together is a choice.
- **One shape for every kind,** so a new kind is a new combination, not
  new machinery: who a challenge is for (one, a group, or anyone), the
  situation it starts from, and how the world sees it done (a sketch is
  in [TOPICS.md](TOPICS.md), topic 17).
- **When.** A first, simple version comes once two things are in: the
  Ur-world's garden hosting plant worlds (the fractal track, part 3,
  [FRACTALS.md](FRACTALS.md)), and the simple scripted Keeper (course
  step 6, the first room). Then the scripted Keeper can offer a plot to
  plant. The full version comes with the AI Keeper, in course step 11.
  Neither changes the order of the course or the track.

What is built, and whose it is: until 2026-11-15, this page opened by
saying that what is built "belongs to whoever built it". The founder's
newer word is "And all for the greater good of the world, which is
available for everyone." The technical lead's reading, put to the
founder as a note: what a challenge builds is the world's, open to
everyone; what someone creates freely, in a place of their own, is
theirs.

## A way through, not a way out

An escape room means being shut in. Here, leaving is always possible, at
any time. The challenge isn't to escape the Ur-world: it is to make
somewhere new.

And leaving is not the end. The founder means "the same person returning
to the world later" to be given a new and harder set of challenges, so
whoever leaves can come back. Today, a name that has left the Ur-world
can't be used there again, so that no one else can take it over. Once
identities have keys (course step 3), whoever left can return by proving,
with their key, that they are the same individual, and their name stays
theirs.

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

> End of `docs/WORLD-KEY.md`.
