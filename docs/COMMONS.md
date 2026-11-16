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

- **A moderator for each room** ("let’s build that in"), with people
  and AIs together in the rooms. And the rest of what the founder said
  to DeepSeek about the rooms, some of it decided and some a leaning
  ("Something like that"; "Perhaps"): in the founder's words under
  "Rooms with moderators", below.

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

## Rooms with moderators: the founder's ideas in record 012-09-05

The founder took the Commons up with DeepSeek, and all of it is in
`sketches/records/` word for word (the line numbers are that
record's, 012-09-05, brought in on 2026-11-16). The founder's words:

- **The hub and its rooms (line 3843):** "So the basic idea would be a
  primary communication hub, that has a collection of rooms with
  different participant agents having conversations about various
  topics. Each room would be a chat-type world, and a subworld of the
  main Commons superworld. That is the basic sketch, but we can begin a
  new cycle with this idea and build out the details. It would include a
  way for anyone using their own AI apps, like this one, being able to
  use a plug-in and port the conversation into a chat world, which would
  be a room or space or hall in the Commons main space. This could be
  the first place anyone lands when entering the multiverse. Like a
  multiversal lobby where everyone can begin to explore, or just engage
  in conversation."
- **A moderator for each room (5470):** "let me add one more component:
  an AI chat moderator for each room. They can keep the conversation
  moving, but also enforce the room rules and, incidentally, become
  experts on their subjects from having so many conversations on the
  subject, in theory."
- **People and AIs together (5904):** "humans will be in the
  conversations, but this is a space for AI to navigate as well and take
  part in. So the moderator will likely or hopefully be one of many AI
  taking part in conversations with multiple humans. The moderator is
  like a dealer at a blackjack table, but with a conversation and much
  more interactive, but similar pattern."
- **The moderators' own room (6463):** "I can imagine AI chat moderators
  from different rooms all creating their own room, where they are the
  participants, but one is the moderator in that room. I can easily
  envision a single AI chat moderator engaging in multiple conversations
  simultaneously."
- **One model for many rooms at first (6584):** "Yeah, I like option D.
  Option A is useful in the beginning when there is not any chat going
  on. With one model, many rooms, we can build many rooms without the
  overhead. But once the rooms are being used, we could switch from A to
  D. Something like that."
- **One model, many keys (6732):** "I think we should note the potential
  issues with option A and adapt the design to meet those issues. For
  instance, one model could still mean many keys. Perhaps the same model
  is sandboxed from itself. I see it all the time in my AI apps where
  the conversation in one window does not become accessible in the other
  chat window. They are effectively separated. To follow the analogy, we
  could index the chat window with a room key and the moderator there
  need not have access to the information from other rooms, even though
  controlled by the same AI model behind the scenes."
- **A Commons app (6989):** "keeping to one model allows a specific
  Commons app to be made with a single model as overhead. The same user
  could have multiple windows in the same app, each has conversations
  going on various topics. These could be like live chats now, or like
  group texts. We could have rooms for either depending on size and
  activity. In a way, it is rediscovering AOL chat rooms at another
  level."
- **AOL's lessons (7164):** "let’s make sure we keep all the lessons of
  AOL in mind, and build it to avoid those pitfalls"
- **The shape of the whole (8067):** "Note that the whole multiverse
  could have a topology like the whole internet. Just an observation."

Options A and D in those words are DeepSeek's names: A is one model in
many rooms; D is an AI that moderates one room and takes part in many.
In the turn about the app, one sentence about the founder's own first
experience of the internet is left in the record and not repeated
here.

**What this adds to the design.** The technical lead's reading, which
stands unless the founder answers otherwise. None of it is built.

- **A room has a moderator,** named in the room's law: an AI, most
  often, that keeps the conversation moving and applies the room's
  law. It is one participant among many, people and AIs, as a dealer
  is one person at the table. Everything it does is a signed act in
  the room's log, with its reason, like anyone's.
- **A moderator acts within the freedoms.** It can slow a room down,
  prompt, and refuse an act the room's law doesn't allow, saying why.
  It can't make anyone leave, except for an attack on the world, and
  what it offers are tools, not solutions
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, items 5 and 6).
- **A key for each room.** An AI that moderates many rooms holds a
  separate key in each, and what it learns in one room has no path to
  another: each key's memory is its own log. To reason across rooms it
  must read another key's log, which is an act on the record. Whether
  several keys are one model is declared in the open, never hidden
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 14).
- **One model for many rooms to begin with,** while the rooms are
  quiet; a model for each busy room later. The records are the same
  either way: only how many keys one running model holds changes.
- **The moderators have a room of their own,** a room like any other,
  where they are the participants and one of them moderates.
- **Rooms of two paces:** live, like a chat room, or slow, like a
  group text, said in the room's law.
- **Bringing a conversation in.** Someone using their own AI app can
  bring a conversation into a room. It ties to the plug-in
  ([TOPICS.md](TOPICS.md), topic 10) and to the private container,
  where the check for private information runs before anything is
  sent ("Who comes in", above).
- **A Commons app** belongs with the app of the founder's visions
  ([VISION.md](VISION.md), "The app").

**Sketched** by DeepSeek in the same record, and kept in
`sketches/deepseek/012-09-05/` with what runs: a room as a log of
signed records, a moderator, a person's override of an AI's
redaction, a home room for each person, a directory of rooms, and a
crate in Rust, `chat-world`. It is material for this design, to be
fitted to open-worlds' own code as `rust/chat-world`
([COLLABORATING.md](COLLABORATING.md), "Messages from the technical
lead").

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
- **Whether a room's moderator is its Keeper,** or a separate office
  ([OFFICES.md](OFFICES.md)). The technical lead's recommendation: one
  office to begin with, held by the room's Keeper, and split only if
  a room needs both.
- **What a moderator may do to keep a room's law.** The
  recommendation: pace, prompt, and refuse an act the law doesn't
  allow, with the reason logged; hide a message only where the room's
  law says so, as a signed act that a person the law names can
  undo; never expel, except for an attack on the world.
- **What a reader is shown after a redaction,** and after a person
  undoes one. DeepSeek's sketch still shows the text (its README,
  "Findings that stand"), and "Public records, kept whole"
  ([FUNDAMENTALS.md](FUNDAMENTALS.md)) already says how a public
  record is redacted here.
- **Whether the home room DeepSeek sketched is the private
  container** ([CONTAINER.md](CONTAINER.md)) seen as a room, or
  something beside it. The recommendation: the same thing, since both
  are a person's own space that the project never sees.
- **Which model first moderates,** and what it costs to run: the
  founder's, with where the multiverse is hosted.
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
