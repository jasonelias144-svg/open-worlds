> Part of `docs/COMMONS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Rooms with moderators: the founder's ideas in record 012-09-05" to "The first to live there, the Library, and the multiverse's own pages".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COMMONS.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COMMONS.md/order.md
> Made by docs/parts.py from the file. To change it, change the file.

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
- **Each place links to its page** on the Library's second shelf: its
  law, what it keeps, how to leave it, what can be done there. What a
  room tells on entering can then be read before choosing to go.
- **One source, two views:** a picture for people, and the same as
  text for a mind. A mind looks at it when it chooses, like the
  Library; it is not said to a mind every turn.
- **It nests,** the same at each scale: the multiverse, a world, a
  room.
- **Its first form is small:** the Commons' lobby, listing its doors
  (course step 3f). A sketch of that list is asked of Gemini
  (2026-11-17):
  [`sketches/replies/2026-11-17-2-for-gemini.txt`](../sketches/replies/2026-11-17-2-for-gemini.txt).

**One scale up and one scale down** (the practice of 2026-11-17:
STATUS.md, "Decided by the technical lead"). Down: a room's own page,
with its law and what can be done there, is the smallest of the
multiverse's pages, and an article is the smallest thing in the
Library. Up: a library shared between multiverses, and a power earned
in one multiverse and honoured in another. There is nothing yet for
either.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COMMONS.md/order.md
