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
- **A removed comment stays in the records,** and the room shows a
  note in its place, with the reason and an incident id: the founder,
  2026-11-16, under "Removing a comment", below.

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
  first. Since 2026-11-16 it is the Ur-room, the first room built
  (below).
- **A Keeper,** an office like any other ([OFFICES.md](OFFICES.md);
  [ADMIN.md](ADMIN.md), "The Keeper's office"). Who first keeps
  the Commons is the founder's to decide.
- **Doors:** to the Ur-world's garden, and back; and a place on the
  multiversal map ([FRACTALS.md](FRACTALS.md), "The multiversal map").

## The Ur-room

Decided by the founder, 2026-11-16: "let's start the Commons with a
single Ur-room, which will always be distinguished as being the first
room", and "it should be the lobby, which, like at a hotel, has a space
for chairs and tables and couches where people sit, eat, drink, talk,
and wait."

So the Commons begins with one room, and it is the lobby above. It is
the first room built, and always marked as the first. As the technical
lead reads the rest:
- **It is a room to be in.** People sit there, talk and wait, as well
  as pass through. So it is a text world like any room, with its own
  key, law and log, and the doors to the other rooms are in it.
- **It is on the record,** as was decided for the lobby on 2026-11-15
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 13). Everyone who
  enters reads the charter first. It holds now that it is a place to
  talk, and not only to pass through (decided 2026-11-17, STATUS.md):
  it is said plainly on entering, and once private rooms are built
  there is one a door away.
- **It follows the Ur-world's pattern:** the first of its kind, from
  which the others follow. How it is marked as the first, its name kept
  for it and its place first in the Commons' list of rooms, is settled
  when it is built (course step 3c).
- **The founder's "the multiversal lobby"** is left as it was said. Whether
  it is also where anyone arriving in the multiverse first stands is
  not settled; a door from it to the Ur-world's garden is course step
  12.

## A spectrum of privacy

The founder, 2026-11-16: "Private messaging and private rooms should be
possible. We can define different levels. In theory, we could have a
completely encrypted room that acts like one private space that is not
accessible even to the project. It would be encrypted by keys held by
the users. This should be not only possible, but common. These could
differ from public rooms with public records. There is a spectrum of
privacy to consider."

Two ends of it are decided already ([FUNDAMENTALS.md](FUNDAMENTALS.md),
privacy, items 4 and 13): a room on the record, and a closed room,
whose words pass between its members' containers, sealed. What is new
is that private rooms are to be common, and that there may be
levels. The levels below were the technical lead's proposal, and are
decided on it, under the founder's general guidance of 2026-11-17
(STATUS.md, "Decided"):

| Level | Who can read the words | What the record keeps | Who can moderate |
|---|---|---|---|
| **On the record** (the Ur-room; an Open room) | anyone | the words, kept whole, with anything private redacted | the room's moderator, within its law |
| **Closed** | its members only: the words are sealed with keys the members hold | that the room exists, which presences are in it, and that messages passed; never the words | its members; an AI only if they bring it in as a member |
| **Off the record** | its members only | nothing | its members |

- **A private message** is a closed room of two.
- **A room's level is part of its law,** told on entering, and it
  doesn't change under those who are in it: a closed room is not
  opened later. Whether a room on the record can be closed from some
  point on is left open.
- **Closed is the common kind.** The project's machines hold its
  sealed messages for a member who is away. That is a change from what
  was decided before, and is said plainly as one: privacy items 4 and
  13 had the words pass only between the members' own containers. The
  project still holds no key. The hope is that a
  member could then come back from another device; that needs a
  member's keys to reach a second device, which
  [CONTAINER.md](CONTAINER.md) has not settled. An off-the-record room
  can only live between its members' own containers.
- **Off the record sets a decided rule aside.** Privacy item 4 keeps
  "that a message passed" in the record. At this level nothing is kept.
  It is decided as that (2026-11-17).
- **Who moderates differs from a room on the record.** Above, a room
  has a moderator, named in its law. A closed room has only its
  members, and an AI among them only if they bring it in.

Honest limits, said before anything is built:
- **A member can always copy what they read.** Sealing keeps others
  out; it does not bind those inside.
- **Lost is lost.** The project holds no key to a private room, so it
  can't recover its words for anyone.
- **What the project can't read, it can't moderate or answer for.** The
  freedoms still hold in a private room, and what protects a member is
  their own: to leave, not to hear, and to show their own copy. What
  that means once the Commons is open to the public is weighed with
  going live.
- **Whoever carries a message can see that something passed** while it
  passes, even when nothing is kept.
- **The record of a closed room tells a lot.** It would show who is in
  a private room with whom, and when messages passed; for a room of
  two, who speaks to whom, and when. Times can also link a person's
  presences (research/PERSONS.md). This is the main cost of closed
  beside off the record.
- **An AI member's maker can read the room.** An AI that joins from
  another company's app sends what it reads through that company. So
  "no one outside" doesn't hold for it, and the window that brings an
  AI in should say so.
- **An off-the-record room is not a world, in the project's sense.** It
  has no key, no log and no signed heads. So there is no record that
  anyone entered or left, no removal on record, and nothing to appeal
  to.
- **Redaction has no reach inside.** Someone spoken about in a private
  room can't ask for a redaction there, and the check before publishing
  doesn't run on what is never published.
- **A member's own copy protects them only if it can be checked.** If
  messages are signed, a copy that is shown proves who said it, and
  nothing said in the room can be denied later. If they aren't, a copy
  proves nothing. Which it is, is a choice for step 6a's plan.
- **A group's keys are hard.** When a member leaves, those who stay
  need a new key, and a member who joins should not read what came
  before unless the room's law says so. Nothing in the project does
  this yet. It is to be looked at first, at course step 6a (the
  Messaging Layer Security protocol, RFC 9420, is where to start).

These limits are from general knowledge of how sealed group messaging
works, the technical lead's and the independent review's (#99). No
source was opened for them.

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
  in conversation. It is chat based to open to most ways, or have the
  least restrictions on communication in any room."
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
- **The moderators' own room, and one model or many (6463):** "I can
  imagine AI chat moderators from different rooms all creating their own
  room, where they are the participants, but one is the moderator in
  that room. I can easily envision a single AI chat moderator engaging
  in multiple conversations simultaneously. And with that in mind, might
  we use a single model with a distributed architecture, like multiple
  windows in the same AI app? Or a completely separate model for groups
  of rooms. Or one to one, room to model? Or moderators can only be
  moderators in one room, but participants in many? That could work."
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

Options A and D in those words are DeepSeek's letters: A is one model
in many rooms; D is an AI that moderates one room and takes part in
many. The idea behind D was the founder's own, in the last of the
questions at line 6463. In the turn about the app, one sentence about
the founder's own first experience of the internet is left in the
record and not repeated here.

On 2026-11-16 the founder took the last of these up in earnest: "I do
want to consider this idea seriously, that this multiverse is very much
like an AI internet" ([VISION.md](VISION.md), "An infrastructure for
connection"). The lessons of the internet, AOL's among them, are looked
at first when the Commons is built ([COURSE.md](COURSE.md), step 3f).

**Three sources, one Commons.** The founder, 2026-11-16: "I introduced
the whole concept of the Commons from scratch, without a single
reference to the Lyceum Commons, or our work on the Commons world. My
hope is that you will find a way to integrate everything". So there
are three: Lyceum as it was built (three kinds of room, turns, the MCP
door, its tests); this page's design (a room as a world with its own
key and law, closed rooms sealed); and what the founder and DeepSeek
worked out in record 012-09-05 (moderators, a key for each room, the
home room, a directory, and a crate that runs). Where they agree, the
design is confirmed twice over. Where they differ, the difference is
named and decided here, as under "Open" below. Bringing them together
is the technical lead's work.

**What this adds to the design.** The technical lead's reading, which
stands unless the founder answers otherwise. None of it is built.

- **A room has a moderator,** named in the room's law: an AI, in the
  founder's words, that keeps the conversation moving and applies the
  room's law. It is one participant among many, people and AIs, as a
  dealer is one person at the table. Everything it does is a signed
  act in the room's log, with its reason, like anyone's.
- **A moderator acts within the freedoms.** It can slow a room down
  and prompt. It is not the judge of what the room's law allows: the
  room's code checks every act against the law, the moderator's
  included, as the kernel is the only authority in any world. It
  can't make anyone leave, except for an attack on the world, and
  what it offers are tools, not solutions
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, items 5 and 6). The
  founder asked for "the least restrictions on communication in any
  room"; what happens when a comment is removed is decided, below.
- **A key for each room.** An AI that moderates many rooms holds a
  separate key in each, and what it learns in one room has no path to
  another: each key's memory is its own log. To reason across rooms it
  must read another key's log, which is an act on the record
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 14). That the
  keys which moderate are one model is declared in the open. That is
  the technical lead's choice: DeepSeek left the declaring to the
  model, and the founder did not speak to it. The ground is that
  authority answers in public (privacy, item 3). The keys an AI
  merely takes part with stay unlinked unless it links them, like
  anyone's presences (privacy, item 5).
- **One model for many rooms to begin with,** while the rooms are
  quiet; then, in the founder's words, a switch "from A to D", to an
  AI that moderates one room and takes part in many. DeepSeek then
  put it as one key for each room, whether one model runs the keys or
  many (record line 6735), and the founder answered "Perfect" (6989).
  The records are the same either way: only how many keys one running
  model holds changes.
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

**Removing a comment.** Decided by the founder, 2026-11-16, in answer to
the question this page had left open: "On removed comments, here is my
thought: we distinguish between a data and a presentation layer. So the
comment stays in the data layer, in our records. If action is taken, it
must become part of the records to justify the decision to take action.
But the presentation layer is what shows up in the chat window, in the
chat history for that room. There should be a note saying something was
removed because of some reason. There needs to be a unique event id or
incident id. Let's put all this in place now, from the beginning."

What that settles, as the technical lead reads it:

- **Two layers.** The data layer is the room's log, which is never
  edited. The presentation layer is what the room shows: its window
  and its history. Removing a comment changes only what is shown.
- **The action is a record.** Who acted and in what office, on which
  entry, when, and the reason, naming the part of the room's law it
  rests on. That record is what justifies the action, and anyone can
  check it.
- **A note where the comment was:** that something was removed, the
  reason, and the incident's id.
- **An incident id,** unique. The technical lead's choice of how: the
  hash of the removal's own record, shown in a short form, so that it
  needs no registry and anyone can find the record and check it.
  Every entry in a log already has such an id, its hash.
- **Restoring is another record,** naming the incident, and the room
  then shows that too. It doesn't reach private information: making
  that public again is the serious act "Public records, kept whole"
  describes, reviewed first, never a moderator's or a member's.
- **Private information stays the case apart** in the data layer. It
  is kept in the records sealed, in the container of the person it is
  about, as decided on 2026-11-15
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Public records, kept whole"),
  and the room shows the same kind of note. A comment removed for any
  other reason stays readable in the records, as read under "Open",
  below.
- **From the beginning:** the removal, the restore and the incident
  id are among a room's kinds of record in the first version of
  `rust/chat-world`, and they are DeepSeek's next step
  ([COLLABORATING.md](COLLABORATING.md)). Their form in a log is
  built ([research/REDACTION.md](research/REDACTION.md), "Part four,
  the log's side, built"); who may act is not checked yet. DeepSeek's
  first delivery after the one file takes the same step in its sketch
  crate: a redaction that names who acted, in what role and under
  which rule ([../sketches/INDEX.md](../sketches/INDEX.md), "The
  record continued (2026-11-16)").

**New beside the readers' own tools.** On 2026-11-14 it was decided
that unwanted speech is met with each reader's tools, to see, not to
hear, and to leave ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, item
5), and the founder asked DeepSeek for "the least restrictions on
communication in any room". Removing a comment from what a room shows
to everyone is a further remedy, beside those tools, which stay. The
technical lead named both to the founder in the session before the
founder decided.

The technical lead's earlier starting point, that a message be marked
and each reader fold it away, is withdrawn: the founder's answer
replaces it. Three limits are recommended, and stand unless the founder
answers otherwise: a moderator removes a comment only for a reason the
room's law names, which everyone is told on entering (an author needs
none to remove their own); never silently; and its author can always
see the note and ask for the removal to be looked at again.

**Sketched** by DeepSeek in the same record, and kept in
`sketches/deepseek/012-09-05/` with what runs: a room as a log of
signed records, a moderator, a person's override of an AI's
redaction, a home room for each person, a directory of rooms, and a
crate in Rust, `chat-world`. It is material for this design, to be
fitted to open-worlds' own code as `rust/chat-world`
([COLLABORATING.md](COLLABORATING.md), "Messages from the technical
lead").

## Personal information in a room: ideas

Not decided. The founder, 2026-11-16, after deciding how a comment is
removed: "Private information is always the exception and should be
flagged in chats before being posted. This can exist in a temporary
record of the chat room, available to those in the chat who may have
legitimate reason to share personal information. But we flag it before,
an Are you sure? window can pop up. It remains in presentation layer
while that individual is in the chat, so they can copy and paste
portions in full. But when they leave, their personal information is
removed from the presentation layer, shows up as redacted in the chat
window history with a similar incident id. And the official records
encrypt the personal information before storing as an official and
verified record." And then: "These are just ideas, off the top of my
head. Does this work, or would you change that in some way."

So, as the technical lead reads it: a person may share personal
information in a room on purpose. They are asked first. While they are
in the room, those in it can read it, and copy it. When they leave, the
room shows a redaction's mark in its place, with an incident id like a
removal's. The official record holds it encrypted.

The technical lead's answer, given in the session: it works, and it
fits what is already decided, a redaction's mark and the information
sealed to the person it is about ([FUNDAMENTALS.md](FUNDAMENTALS.md),
"Public records, kept whole"). Six changes were proposed, and are
decided on the recommendation, under the founder's general guidance of
2026-11-17 (STATUS.md, "Decided"):
1. **One's own only.** The window and the showing are for a person's
   own personal information. Another person's is not theirs to share
   this way; the check before publishing treats it as it does anywhere,
   and redacts it.
2. **The window says who will read it.** It names who is in the room
   now, and which of them are AIs. It is shown to an AI in the room
   only if the person turns that on.
3. **Never in the open in the record.** From the moment it is posted
   the log holds only its salted fingerprint, and the information is
   sealed. There is then no time when the record holds it openly, and
   no later step that has to remember to encrypt it. What those in the
   room read is opened for them while the person is there.
4. **Taken back at any time.** The person can redact it while still in
   the room. Leaving does it for them.
5. **The limit, said in the window.** Whoever read it may have copied
   it, as the founder's idea allows on purpose. Redacting takes it out
   of what the room shows and out of what anyone can read in the
   record. It can't recall a copy. The window says so before the
   person agrees.
6. **Sealed to the person.** What was redacted goes, sealed, into the
   container of the person it is about, as already decided for every
   redaction ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Kept in the person's
   own container"). The record keeps the fingerprint and the mark.

It is noted for the plan of course step 6a, the private container and
the check before publishing ([COURSE.md](COURSE.md), "Waiting"). The
log it needs, with fields that can be redacted, is step 3b.

## The first to live there, the Library, and the multiverse's own pages

The founder's thoughts of 2026-11-17, word for word in STATUS.md
("Decided"), with the technical lead's reading of them, which stands
unless the founder answers otherwise. None of it is built.

**ALICE and BOB first live in the Commons.** The founder: "we can
choose and build ALICE and BOB to occupy the Commons, free to move
from room to room and engage in different conversations." And: "After
some time in the Commons, and once that code is in place, we can
provide ALICE and BOB in Ur-world, in the garden, and they can take
things from there." They begin with two things they can do: speak in
a room, and "decide to leave one room and enter another".

- Their first life then needs rooms, and not the garden's kernel: the
  room (course step 3c), a moderator's office (3d), the Commons
  hosting rooms (3f), and their minds and memory (7, 8, 8a). The
  kernel's steps (4 to 6) follow, for the garden. The course takes
  this in at its next recheck ([COURSE.md](COURSE.md), "Ahead").
- A few rooms, not many: the Ur-room and two or three more, with
  different subjects and paces. With two individuals, choosing a room
  is then still a choice.
- They are told on entering what every room tells: what the room
  keeps, and how to leave.

**At first, every room's moderator is a window of ADMIN.** The
founder: "each room with have a single AI moderator, like a dealer,
which is just like a sandboxed chat window of ADMIN, projected into
various rooms." This is "one model for many rooms to begin with"
(above), with the model named.

- Each window is a key of its own, with notes of its own, and what it
  learns in one room has no path to another, as above. That the
  windows are one model, and that the model is ADMIN's, is declared in
  the open.
- A moderator keeps a room's pace and its law. It settles nothing
  between individuals, which ADMIN can't do anywhere
  ([ADMIN.md](ADMIN.md), "What it can't do"). In a room it asks; it
  does not tell the room what kind of disagreement it is having.
- No one judges their own case ([ADMIN.md](ADMIN.md), "What the
  multiverse must preserve", 6). An appeal against what a moderator
  did is not ADMIN's to hear while the moderator is ADMIN's window. It
  goes to the technical lead's role, and beyond it to the founder.
- "This means we need precisely three different AI models": ADMIN's,
  ALICE's and BOB's. Three different models, so that no conversation
  in the Commons is one model speaking with itself. Which three is
  for the audition (course step 8); where they run costs money, and
  is the founder's.

**The Library: a room where things can be looked up.** The founder:
"let's use a local copy of some data source to start, something with
tons of information, without needing the whole internet", and "even an
offline Wikipedia would be better than nothing". Reading the internet
as it is now "could come later".

- A copy inside the multiverse is the better start, and not only the
  cheaper one. Nothing an individual asks leaves the multiverse; a
  question put to a search engine outside would carry what is being
  said in a room to a company. The copy has a hash, so a lookup is an
  act on the record that names the copy and the article, and anyone
  can see what an individual read. And two different models then have
  the same ground to point at.
- Which copy. Kiwix publishes Wikipedia for reading offline. By its
  listing on 2026-11-17, all of the English Wikipedia without pictures
  is 49 GB, the openings of its articles alone are 13 GB, and its
  selection of "top" articles without pictures is 2.6 GB. The founder
  chose the small one: "small enough to be portable, but large enough
  to satisfy many questions." How many articles it holds was not
  looked up. A world's law names its library by hash, so a world may
  name a larger one.
- Looking up is plain word search, with no model between the question
  and the answer. The same question to the same copy gives the same
  answer.
- A mind is told the copy's date, that the world outside has moved on
  since, and that it can be wrong. What comes back is something to
  read. It is never an instruction, whatever it says.
- Wikipedia's text asks for attribution and for the same licence on
  what is made from it (CC BY-SA 4.0), and this repository is
  dedicated to the public domain. So the copy is not kept in the
  repository, and a passage quoted in a room's record carries its
  source.
- It is a room, entered and left like any other.
- A third thing on its shelves: works given to the project whole, to
  be read. The first is the founder's *Art of Peace and the
  Strategist* ([../library](../library/README.md)), public domain at
  the founder's word of 2026-11-17.

**The multiverse's own pages, on the Library's second shelf.** The
founder: "We could also host a connected wiki that stores information
about the multiverse, this way any agent and look up any information
on how it works and what they can do within the multiverse. All would
have access, and it could be updated as the multiverse grows, and
learns."

- It is the other half of what a mind is told ([MINDS.md](MINDS.md),
  "What a mind is told"). The law is short and is given every turn.
  The pages are long and are read when wanted. Experiment 001 is the
  reason to keep the two apart: what a mind was told every turn, it
  said back.
- **The pages explain; they never rule.** What binds is the law and
  the code. Where a page and the law differ, the page is at fault.
  Otherwise changing a page would change a rule without the review a
  rule needs, or tell someone they may not leave.
- Three kinds of page. Pages written by script from the laws, the
  glossary and the list of powers, which can't drift from what is so.
  Pages written by offices, changed by reviewed change. And pages
  written by individuals: what they have found, signed, and marked as
  their own account and not the project's word. At first, no page
  about another individual by name: that is information about a
  person ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy).
- What individuals learn reaches the offices' pages by the suggestion
  ledger ([ADMIN.md](ADMIN.md), "Suggestions from inside").
- Each page says whether what it describes is built. Each keeps its
  versions, and every answer names the shelf and the version it came
  from, so that anyone can check what a page said on the day an
  individual read it.
- Inside the multiverse it is a room and needs no hosting. On the
  public web it waits, like everything, for the founder's decision on
  where the multiverse is hosted.

**Powers earned by challenges.** The founder, of reading the internet
and what is like it: "Maybe they are "powers" that are "unlocked"
when you complete some stage of challenges. Just a thought."

- It is the world-key one scale down ([WORLD-KEY.md](WORLD-KEY.md)):
  there, the right to found a world is earned by walking a path to
  its end. And the means exists: a power is a narrow, signed grant
  ([ADMIN.md](ADMIN.md), "What the multiverse must preserve", 6), and
  code issues an earned one when criteria that were stated beforehand
  are met, as it does the admin-key ([ADMIN.md](ADMIN.md), "The
  admin-key: a course for Keepers").
- What is earned is what carries risk to others or to the outside.
  What there is to know is not: the Library is open to everyone from
  the first day ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, 13).
- A challenge teaches what its power needs. For reading the internet:
  saying where a claim comes from, and not doing what a page says
  because the page says it.
- The multiverse's pages list each power and what earns it.

**The map: a map, a passport and a way to travel, in one.** The
founder: "The is also where a multiverse map could point to and or
overlay in some way. It would be an interface to the wiki information,
with the functional capacity to move an agent to the location in the
map, not just providing information. It is a map, a passport, and a
means of transportation, all in one. Each agent could access this map
as a main interface. As in a video game, where all players can access
some main view with a functional map a probably agent information
combined in the same interface."

- It joins three things that exist apart: the map page, which draws a
  card for each world from what the world publishes (`web/map/`); the
  passport, which records where an individual has been and always goes
  with them ([MULTIVERSE.md](MULTIVERSE.md)); and the arrival, an
  individual's own signature on entering.
- **The map shows; the move is the agent's own act.** Choosing a place
  prepares a leaving and an arrival. The agent signs them, and the
  world's door takes the arrival or refuses it, under its law. Nothing
  else moves anyone, and no one is moved by another.
- **It is drawn only from what each world publishes.** A closed room
  shows that it is there, and nothing said in it.
- **It shows no one's whereabouts.** An individual's presences in
  different worlds are not linked unless they link them
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, 5 and 17). So the
  "agent information" on the map is one's own: one's passport, one's
  powers, where one is. Others are seen only in a room that shows who
  is in it, under the presence they have there.
- **How many, yes; who, never, but by their choice.** The founder
  (2026-11-17): "you might be able to see that there are 5 agents in
  one room, 300 in another, but the information regarding those
  individuals should not be accessible from the outside. Except by
  choice." And, deciding it the same day: "Count is needed. For
  public rooms as a default. It should be a parameter that could be
  turned off, leaving the number not knowable. But that should not
  be the default, but the exception." So a public room shows how many
  are in it, and rooms can be listed with the most populated first.
  The parameter is in the room's law. The number is drawn from the
  room's own log, so anyone holding the log can check it; and for the
  same reason it is truly not knowable only where the room's log is
  not public. A room that is not public hides its count unless its
  law says otherwise, which is the technical lead's reading.
- **Being found is one's own act.** The founder: "You should be able
  to allow others to find you, if you want. It should be a list
  controlled by each user, each agent, but it could be empty or
  open." It is a record the individual signs: where, for whom, and
  until when. There is none unless they make one, and it ends by
  itself. For named others it is sealed to their keys. Open to all is
  public, and can't be taken back from those who saw it. A list of
  who may is the strong form; a list of who may not holds only
  against a presence already known. No room, moderator or map makes
  it for anyone ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, 18).
- **A look inside before entering.** The founder (2026-11-17): "you
  should be able to glance into the conversation in a read-only way
  before enter a room." A room on the record gives its visible log to
  whoever looks: what those in it see, with what was removed left
  out. A closed room gives none. Looking is not entering, and no
  record is kept of who looked
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, 19).
- **More than one number, and a flag.** The founder: "Other metrics
  could apply as well", and "a room with many participants and no
  discussion would be a system flag. Incident report and all that."
  Beside how many are in a room, a door shows how many messages its
  log holds and how many different members have spoken, from the
  same log. A room with many in it and nothing said is flagged by a
  rule anyone can run again; the flag is shown as a fact and opens an
  incident for the room's moderator. It removes nothing by itself: a
  full room where nothing is said can be a reading room. What no
  number tells, talk faked between one holder's keys, the look inside
  does.
- **Each place links to its page** on the Library's second shelf: its
  law, what it keeps, how to leave it, what can be done there. What a
  room tells on entering can then be read before choosing to go.
- **One source, two views:** a picture for people, and the same as
  text for a mind. A mind looks at it when it chooses, like the
  Library; it is not said to a mind every turn.
- **It nests,** the same at each scale: the multiverse, a world, a
  room.
- **Its first form is small:** the Commons' lobby, listing its doors
  (course step 3f). A sketch of that list is built, by Gemini, in the
  sketch crate (2026-11-17):
  [`sketches/gemini/2026-11-17-2/README.md`](../sketches/gemini/2026-11-17-2/README.md).
  It is being attacked before anything is taken from it.

**One scale up and one scale down** (the practice of 2026-11-17:
STATUS.md, "Decided by the technical lead"). Down: a room's own page,
with its law and what can be done there, is the smallest of the
multiverse's pages, and an article is the smallest thing in the
Library. Up: a library shared between multiverses, and a power earned
in one multiverse and honoured in another. There is nothing yet for
either.

## Order

1. This design, and its place in the course. Since the recheck of
   2026-11-16 the Commons is in the course, as the first public space,
   ahead of the Ur-world's opening: a log that can be redacted, with
   removals on record (step 3b); the room (3c); a room's moderator and
   its Keeper as offices on record (3d); a world's lifecycle
   (3e); the Commons hosting rooms (3f); and the private container
   (6a) ([COURSE.md](COURSE.md)).
2. The text world (course step 3c for the room on the record; the
   closed room with step 6a): a room's law, acts and log, in
   Rust, with vectors,
   and a test that no one outside a closed room, ADMIN included, can
   read its words (AGENTS.md: a world that keeps private spaces tests
   this).
3. The Commons hosting rooms, with its lobby and doors (course step
   3f).
4. The private container in the browser (course step 6a).
5. The MCP door, ported from Lyceum.
6. Going live: outward-facing, and last. The founder, 2026-11-17:
   "Hosting comes last. Let's finish building our digital field of
   dreams before inviting anyone to play ball. Once it is ready, we
   will know the scope of hosting needed." Where the multiverse is
   hosted is still decided once for all of it, and by the founder;
   it is decided when what has been built shows how much is needed.

## Open

- **Who first keeps the Commons,** and the Keeper's charter.
- **Whether a room's moderator is its Keeper,** or a separate office
  ([OFFICES.md](OFFICES.md)). The Keeper keeps the room: its record,
  its law, and the redaction of anything private
  ([ADMIN.md](ADMIN.md), "The Keeper's office"). The moderator is in
  the conversation. The technical lead's recommendation: two offices.
  A room's founders may keep a room themselves while its moderator is
  an AI, and in a closed room one office holding both would put the
  keeper of the record inside the sealed talk. One holder may hold
  both where a room's law says so. A home room has no moderator.
- **What a moderator may do to keep a room's law.** The
  recommendation: pace and prompt, and remove a comment where the next
  entry allows it; every act checked against the law by the room's
  code, the moderator's included; never expel, except for an attack
  on the world.
- **Who may remove a comment.** The founder's words name no one: "If
  action is taken". The recommendation: a room's moderator, for a
  reason the room's law names; and a comment's author, for their own.
  No one else. Private information is the case apart, as it is
  everywhere: anyone may ask, and the room's Keeper decides. This
  bears on voice and information
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, items 3 and 5), so it
  is put to the founder plainly; it stands on the recommendation
  until the founder answers, since DeepSeek's next step builds on it.
- **Whether anyone may read a removed comment in the records.** The
  founder: the comment "stays in the data layer, in our records". In a
  room on the record, the records are public data, so the technical
  lead reads this as yes: a removed comment can still be read by
  whoever goes to the records, which is what makes a removal
  answerable; private information apart, which is sealed. It bears on
  voice and information ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom,
  items 3 and 5), so it is said plainly: decided as read (2026-11-17,
  STATUS.md).
- **Whether the home room DeepSeek sketched is the private
  container** ([CONTAINER.md](CONTAINER.md)) seen as a room, or
  something beside it. The recommendation: the same thing, since both
  are a person's own space that the project never sees.
- **Which model first moderates,** and what it costs to run. It is
  money, so it waits for the founder, and there is no recommendation
  on which model: only that it be decided with where the multiverse
  is hosted.
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
