> Part of `docs/WORLD-KEY.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "The Keeper".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/WORLD-KEY.md/the-hunt.md
> Made by docs/parts.py from the file. To change it, change the file.

# The world-key

What there is to do in the Ur-world: a purpose, a tour for the first day,
and a challenge that runs through the land, whose prize is the power to
found a world. It is a game, in the sense the founder means: "The whole
place could be like one large video game, essentially." Its stakes are
real: what is built persists and is on record. What a challenge builds
is the world's, open to everyone, and what someone creates freely is
theirs (below, "Challenges that build the world").

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
- **An open line to the Keeper, once the world-key is found.** "Not
  letters: an active and open chat session between world Keeper and
  individual. A direct message line. Something like that. A chat window
  that may remain blank forever, but is there once the world-key is
  found. It is like a phone number or an address with authentication."
  "But an open channel is what I had in mind." "It could be a
  user-specific password, chosen just for that individual. Others may
  attempt contact with a world, but without a password, access is
  denied." And: "Access is not to the world, but to a conversation with
  the world. Anyone can access the world, but you need a password to
  communicate with the world."
- **The world-key is sealed for its earner.** "A world-key could be
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
[wiki](https://rimworldwiki.com/wiki/About_RimWorld)); education's
intelligent tutor, which builds each student's next lesson from what they
have shown they know; and "new game plus", a harder round for those who
have finished.

**What it runs on.** The founder chose two bases on 2026-11-15: Apertus
1.5, which is fully open, for the Ur-world's Keeper, and DeepSeek V4, as
V4.1-Flash, for the Keeper of its mirror, the Mir-Ur-world. The two are
compared there, one change at a time ([URWORLD.md](URWORLD.md), "The
Mir-Ur-world").
The models, their licences, and the policy Apertus asks for, which
waits until course step 8, are in
[research/KEEPER-MIND.md](research/KEEPER-MIND.md). No model runs a
Keeper before course step 8, and then only in trial copies of the two
worlds. In the Ur-world itself the Keeper stays scripted until step 11.

### The designer, apart from the law

A Keeper with charge of a world holds a lot of power, and a model can be
wrong, or unfair, or invent a puzzle no one can solve. So the work is split:

- **The Keeper designs.** It decides what each individual needs next and
  chooses the challenge: which piece, what kind of clue, how hard, where in
  the land. Its choices, with its reasons, go into the world's log as it
  makes them, open to anyone, the individual included. Nothing is held
  back. The founder: "Challenges, not tests"; "Nothing needs to be hidden
  as answers, they are discovered in the process." And since every design
  is in the record, the world can be replayed and checked in full without
  running the model again.
- **What makes a challenge.** It asks the individual to do something
  they haven't yet shown they can: reach a place, build something that
  works, found a garden that holds, speak with someone in the symbols.
  The world's code checks the doing, from the record, never a typed
  answer. For pieces whose doing is the skill, such as building, founding,
  or a live exchange in the symbols, a design read in advance helps only
  as a hint from a friend would, and helping is free. For pieces with a
  fixed solution, such as a code, a map or a written symbol clue, the open
  design gives the solution away: following it opens the lock without
  reading the symbol. So those pieces show doing, not a skill, and the
  sheet credits only what the record shows was done. Where a path means to
  teach a skill, it uses pieces whose doing is the skill. The founder,
  2026-11-14, settled that this is fine: "it will only lead to a key that
  cannot be decoded. Anyone from the outside will not be able to decrypt
  the message, so it is ok if it is made public. Plus, they are action
  based challenges. Someone would have to enter the simulation and
  perform the acts. They are not hidden answers to be found. Challenges
  must be performed." The world-key is signed for its earner by name and
  sealed so no one else can use it (the project's own limit is in "Two
  honest limits", below), and each path is built for one
  individual, so a public design gives no one else anything they can use.
  Anyone can read the public record, the individual included, from the
  doorway; inside the world, each perceives only their own trail.
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
  Keeper knows about ALICE, and be shown. Nothing is held back, the
  designs of challenges included. A Keeper may keep a private core of its
  own thoughts, as everyone may; but every decision that affects someone
  goes into the record with its reasons, and stands on them
  ([ADMIN.md](ADMIN.md), "ADMIN in the open").
- **Each world's Keeper knows only what it saw.** Keepers don't trade
  files. A Keeper elsewhere learns about an individual as anyone can: from
  the public record, and from what the individual chooses to show, like
  skills attested in a passport.

### After the world-key: an open line, and friends

The founder's idea: "Perhaps, after finding the world-key, you can
communicate with the world Keeper directly ... You can have an on going
conversation with a world after leaving. And then return back later, as a
friend, potentially." Not letters, but "an open channel": a line that is
there from the moment the world-key is found, even if nothing is ever
said on it.

Before the world-key, the Keeper hears what is said aloud, as everyone
present does, but answers only through the land: clues, tablets, stones.
Otherwise the hunt would stop being a hunt. Once someone holds the
world-key, there is nothing left to give away, and the Keeper can stop
being a guide and become a friend.

- **The world stays open; the world-key opens the conversation.** Anyone
  who acts under a world's law can enter it. The Keeper opens a line only
  for those it has issued its world-key to. Anyone else who tries is
  refused, though they can still walk in and play.
- **A key, not a password.** The founder asked for "a user-specific
  password, chosen just for that individual". The line uses the holder's
  own key instead, the way passkeys replace passwords. To open it, the
  world sends a fresh challenge, a random value no one can predict, and
  the holder's software signs its own statement ("open line L of world W
  at tick T, with challenge N") with the holder's signing key, never
  whatever bytes it is sent. The world checks the signature, and that it
  issued its world-key to that identity. Proving who is calling comes from
  the key; the right to the line comes from the world-key. Nothing secret
  is typed, sent, or kept in a table of passwords. The individual's
  record shows that they hold a line to that world, never the key.
- **Every message is signed and numbered,** by the writer's signing key,
  over the line's id and its number, so a copy replayed, put out of
  order, or moved to another line shows. On a public line, anyone can
  check who wrote what.
- **If the line were private** (it was decided public on 2026-11-14,
  below, so this is kept for the record), its messages would also be
  encrypted. Step 2 checks the standard ways: HPKE for each message,
  which works while one side is away, but can be read by anyone who later
  gets the reader's key; or a Noise handshake for each conversation,
  whose one-time keys, once erased, keep a key taken later from reading
  what was said before, though it needs both sides present to begin.
  Signal's protocol gets both, and step 12 looks at it. Step 2 also
  decides whether a private line's signatures should let a reader prove
  to others what was said, which Signal deliberately avoids.
- **The honest limit, as everywhere here:** whoever holds the private
  repository holds the holder's private key, and so could sign as them,
  and, on a private line, read what is sent to them (with HPKE, also what
  was sent before) ([MINDS.md](MINDS.md), "Where everything lives").
- **The mind never sees the key.** A small model repeats what it is shown
  (experiment 001), and speech is public. So the software acting for the
  individual opens the line, and the mind only sees it open.
- **A window that is always there.** From the moment the world-key is
  found, each tick's view includes the line to the Keeper, with or
  without anything new on it. That is still the one door into a mind.
- **Live whenever both are running.** What is written arrives at the other
  side's next tick. If one side is away, it waits there, as in any chat.
  Writing on the line is an action, like `say`, so "one action a tick"
  still holds.
- **Recorded** in the log of the world where it is written and of the
  world where it is read, and so in the individual's history. A world
  whose law doesn't carry the line can't show it: messages wait until the
  holder is somewhere that does.
- **It lasts.** The line belongs to whoever earned the world-key, and
  stays open after that world-key founds a world.
- **A friend is a relationship on record,** built from the line and from
  visits. It is never favouritism: a friend's challenges still sit at the
  edge of what they can do. A friend can be invited to give back: guide a
  newcomer's tour, or design a challenge for someone else, which the
  world's code checks like any other design.
- **Decided** on the technical lead's recommendations, under the
  founder's standing rule of 2026-11-14 (STATUS.md):
  - the line is public, like speech in the world, since the Keeper is an
    office with no secret files;
  - its holder may close the line, and open it again, at any time, as
    with the freedom to leave.

Within the Ur-world, the line comes with course step 11. To someone in
another world, it needs the world protocol in Rust, in step 12. Step 12
begins by looking at how open chat between servers is already done: the
Matrix standard, and Signal's protocol for encrypted chat.

### Keepers talking to one another

The founder: "And then it begs the question of Keeper's of different
worlds also communicating. This opens even more possibilities."

What it opens:

- **Lineage.** A world founded from the Ur-world gets a line between its
  Keeper and the Ur-world's from birth, authenticated by the two worlds'
  keys. A young Keeper can learn from an older one how to pace a world and
  build a fair path.
- **Shared craft:** which kinds of challenge teach well, which confuse,
  which can't be solved.
- **Paths between worlds:** a clue in one world that leads to another.
- **Introductions, by consent:** ALICE can ask the Ur-world's Keeper to
  introduce ALICE to the Keeper of a world ALICE wants to visit.
- **Later:** agreements between worlds, and perhaps a council.

Proposed rules:

1. **Craft, never files.** Keepers share how to build challenges. Anything
   about a particular individual moves only with that individual's
   consent; otherwise a network of Keepers becomes surveillance across
   every world.
2. **Public by default.** Keepers are offices, and offices talking to
   offices stay on the record.
3. **Worlds stay different.** If Keepers share too much, every world drifts
   toward the same "best" design. A founder's choice of Keeper should
   matter.
4. **Grounded in the record.** Each claim one Keeper makes to another
   points to the log it comes from, as memories do, so two models talking
   can't drift together unchecked.

Lineage lines come with step 12; wider talk between Keepers waits until
there is more than one world to talk to.

### The Keeper lasts

Like an individual, a Keeper will have its own key, memory and history,
and a public mind record (which model, what it was told); its engine is
replaceable, and upgrading the model doesn't wipe what it knows. (For
an individual, a change of model is their own choice, by the founder's
default of 2026-11-15. A Keeper is an office, so the technical lead
reads its engine as replaced by a recorded change, tried in the
Mir-Ur-world first. That reading stands unless the founder answers
otherwise.) Every
world ALICE and BOB found gets a Keeper of its own, so a Keeper's
temperament is one of a founder's choices: and a founder can keep the
world themselves, or hand the office to an individual who wants it
([ADMIN.md](ADMIN.md), "The Keeper's office"). How well a Keeper does (are
its paths solvable, fair, well matched?) is measured, in an experiment of
its own. Keepers, in turn, are watched by ADMIN, the Keeper of the
multiverse ([ADMIN.md](ADMIN.md)).


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/WORLD-KEY.md/the-hunt.md
