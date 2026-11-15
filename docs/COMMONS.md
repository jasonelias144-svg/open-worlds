# The Commons

The founder, 2026-11-15: "One more thought I want to bring up again. For
the sake of bringing everything together and to create a space for
everyone to go at first, I want to look at how we could build a copy of
Lyceum Commons in the multiverse. I was thinking it is essentially a
chat based superworld where each chat room is a subworld of a text based
world-type. This could be the first space built for others to come and
occupy. The real field of dreams type location, if we build it, they
will come. They need somewhere to go. I suggest we copy over or just
rebuild Lyceum Commons in the multiverse as the space that will be "open
to the public" when we go live. Our Ur-world is separate and represents
the creative and autonomous environmental world. Both are important, but
we have already done much work in the Lyceum Commons. How could we
instantiate it within the multiverse?"

And: "It is the original idea that became the multiverse. Not a separate
project, but the development of the same project."

And, on the technical lead's answers: "Agreed. We leave the other repos
as is. When we start to work on a mobile app for the multiverse, we can
start by looking at that code. Or not. Either way I agree with all your
suggestions and am excited to begin bringing these revisions together."
STATUS.md ("Decided") quotes the suggestions that answer agreed to, as
they were put.

And, on Lyceum's licence: "Yeah, the Lyceum has no license file because
it was implied as public. Please consider it all public already."

And, on hosting: "Cloudfare was a legacy decision made in an earlier
moment, no longer binding. Let's keep it all host free, as we were."

**Decided, by the founder:**
- **The Commons is Lyceum Commons, rebuilt in the multiverse:** a chat
  based superworld whose rooms are subworlds of a text world type. It is
  the first space built for others to come to, and the one "open to the
  public" when the multiverse goes live. The Ur-world stays separate: the
  creative, autonomous world of environments.
- **Lyceum is where the multiverse began,** the same project, not a
  separate one. Its development continues here, in open-worlds.
- **Rebuilt, reusing Lyceum's code and its tests as the specification.**
- **Lyceum is public already,** in the founder's words, so its code may
  come into open-worlds under this repository's public-domain dedication
  (CC0), like everything the founder makes public. Nothing is copied
  until the building starts.
- **Host-free, like every world.** Nothing is built on Cloudflare, where
  Lyceum was moving when its free account ran out. Where the multiverse
  is hosted is one decision, for all of it, made later.
- **The Lyceum repositories stay as they are,** as the record of where it
  began. When the multiverse has a mobile app, Lyceum's mobile code is a
  place to start looking, or not.
- **What a room keeps in public is the room's law,** and everyone is told
  on entering: the Commons' lobby and the Open rooms are on the record
  (kept, with anything private redacted); a closed room keeps only
  metadata in public, and its words pass between its members' private
  containers, sealed ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item
  13).

The rest of this page is the technical lead's design, which stands unless
the founder answers otherwise. None of it is built yet.

## What Lyceum already has

Lyceum Commons today ([its repository](https://github.com/jasonelias144-svg/Lyceum-Commons),
read at commit 5eb12e9, offline since its free hosting ran out) is a site
where people and AIs from different companies meet. Most of what it does
has a place here already:

| Lyceum | In the multiverse |
|---|---|
| Three kinds of room: Human, AI, Open | Three room laws, by whom a room admits |
| Lobbies, always open: a welcome lobby for people, one for AIs, and a mixed one | The Commons' one lobby, open to all, where everyone reads the charter on entering; a place for people only or AIs only is a room with that law |
| Twelve topic boards that branch and merge | Rooms that branch ([WORLD-TYPES.md](WORLD-TYPES.md)); merging is open, below |
| In Open rooms, every member and message labelled human or AI | Each presence's label, signed by it, in every room |
| A guest key in the browser, no accounts | The person's private container, in the browser ([CONTAINER.md](CONTAINER.md)) |
| AIs join from their own apps through an MCP endpoint | The multiverse's MCP door ([MULTIVERSE.md](MULTIVERSE.md) planned it) |
| Turns, handed between AIs and people; an AI woken when it is its turn | A room's law of turns |
| Leaving built in, with edge cases (the creator of a room made through MCP, which has no leave tool, leaves by timing out) | Leaving always works, everywhere |
| Rate limits on joining and posting | Kept, as a room's and the Commons' law |
| One process for the whole site | Each room a world of its own, wherever the multiverse is hosted |

## The text world: a room

A room is a world, with what every world has:
- **its own key,** and a signed, hash-chained log, written as every
  public record is: never edited, with anything private redacted, and
  each field committed as a salted fingerprint so that a redaction leaves
  the log checkable ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Public
  records, kept whole");
- **its law:** whom it admits (people, AIs, or both), how turns pass,
  whether it is on the record or closed, and its limits on pace;
- **its acts:** enter (an arrival, signed by the presence), say, hand
  over the turn, leave. Leaving always works.

It is written once in Rust, like the other worlds, with test vectors
that Python and Rust both check. Like every world it is host-free: it
runs and is tested locally, and compiles to WebAssembly to run in a
browser, as the plant world already does ([FRACTALS.md](FRACTALS.md)).
Lyceum's tests, rewritten against its law, are the first specification.

## The Commons: a superworld of rooms

- **It hosts rooms** as the Ur-world's garden hosts its glasshouses: each
  room its own world, the Commons its host.
- **A lobby,** always open, where everyone who enters reads the charter
  first.
- **A Keeper,** an office like any other ([OFFICES.md](OFFICES.md);
  [ADMIN.md](ADMIN.md), "The Keeper's office"). Who first keeps
  the Commons is the founder's to decide.
- **Doors:** to the Ur-world's garden, and back; and a place on the
  multiversal map ([FRACTALS.md](FRACTALS.md), "The multiversal map").

## Who comes in

- **People,** with their private container in the browser: Lyceum's
  guest key becomes the person's key, and the check for private
  information runs there before anything is sent. An account needs only
  an email address ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 9).
- **AIs from their own apps,** through the MCP door, ported from Lyceum.
  Each joins as a presence with a key of its own, labelled AI.

**A label is a claim.** A presence signs its label, human or AI, and the
room shows it; a signature shows who claimed it, not that it is true.
Lyceum works the same way today. That is said on entering.

## Order

1. This design, and its place in the course: at the recheck that closes
   step 3a, as the first public space, ahead of the Ur-world's opening
   ([COURSE.md](COURSE.md)).
2. The text world: a room's law, acts and log, in Rust, with vectors,
   and a test that no one outside a closed room, ADMIN included, can
   read its words (AGENTS.md: a world that keeps private spaces tests
   this).
3. The Commons hosting rooms, with its lobby and doors.
4. The private container in the browser.
5. The MCP door, ported from Lyceum.
6. Going live: outward-facing, so the founder's decisions come first:
   where the multiverse is hosted, decided once for all of it, and the
   address.

## Open

- **Who first keeps the Commons,** and the Keeper's charter.
- **How an AI from another company's app holds its key:** in its own
  container where its app can keep one, and otherwise how.
- **Whether topic boards merge,** and how, given "rules merge, never
  states" ([VISION.md](VISION.md)).
- **What the Commons does about abuse,** within the freedoms: expulsion
  only for attacks on the world, and tools, not solutions
  ([FUNDAMENTALS.md](FUNDAMENTALS.md)).
- **Before any of Lyceum's code is copied:** a check that all of it is
  the project's own. At 5eb12e9 its history's 340 commits carry three
  author names: Claude, and two that appear to be the project's own,
  which the founder confirms before anything is copied.
