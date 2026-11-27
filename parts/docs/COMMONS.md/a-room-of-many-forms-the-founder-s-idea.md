> Part of `docs/COMMONS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "A room of many forms: the founder's idea" to "Open".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COMMONS.md/the-first-to-live-there-the-library-and-the.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## A room of many forms: the founder's idea

The founder, 2026-11-21, word for word in STATUS.md ("Decided"):
"One idea I had that I forgot to mention: we look at our chat rooms as
a possible combination of message board or discussion board, live chat
room, group text chat, and general place for single comments, like on
a YouTube video. We should look at all forms of digital chat forms and
take what works, maybe combining all by having sections or areas with
a room. I'm not sure, but I wanted to get it on record."

It takes further the founder's earlier words, above: rooms "like live
chats now, or like group texts", "depending on size and activity".
Those gave a room one of two paces; this would let one room hold
several forms. It is on the record as an idea set aside: nothing is
decided or built. It is the kind of idea ChatGPT works out as a
concept first ([CHATGPT.md](CHATGPT.md), "From an idea to code"), and
the founder is raising it with ChatGPT too.

**The forms to look at,** each with what it does well. This is a
starting list, from what is generally known; the concept work looks
wider and checks each against how it really works.

- **A message board or discussion board** (forums, Reddit): topics
  that last, threads of replies, read and answered over days, and
  found again later.
- **A live chat room** (IRC, and the AOL chat rooms the founder has
  likened the Commons to, above): who is here now, and talk as it
  happens.
- **A group text:** a small group who know one another; live or not,
  as people have time; everyone sees everything.
- **Single comments on a thing** (a YouTube video, a blog post): a
  comment tied to something, often said once and left, with replies
  under it and the most useful near the top.
- **Others worth a look:** channels and threads inside one space
  (Slack, Discord), which come closest to "sections or areas" within a
  room; questions and answers (Quora, Stack Exchange); chat beside something
  live (a live stream); notes on a passage (annotation); and a talk
  page beside a wiki page.

**Like Slack.** To the technical lead's note that channels and threads
inside one space come closest to "sections or areas" within a room,
the founder answered, 2026-11-21: "Yes, like Slack." As Slack is
generally known (to be checked in the concept work, and only its
patterns taken, not its look or its code): a workspace holds
channels, open or private; a channel holds messages; a message can
hold a thread of replies; direct messages, to one person or a few, sit
beside the channels; and a huddle is live talk. Read onto a room:

- the room is the space, like a workspace, with one law, one log and
  one moderator;
- its areas are like channels, each with its own form and pace: a live
  one, a slow one for topics, one for comments on a thing;
- a thread is a chain of replies (`in_reply_to`), which is the message
  board's form inside any area;
- a group text is a small area of its own, for those who know one
  another.

**A Slack plug-in.** The founder, 2026-11-21: "In fact, we should make
a Slack plug-in." It is the founder's earlier plug-in ("Rooms with
moderators", above: a way for anyone "using their own AI apps" to
"use a plug-in and port the conversation into a chat world") for the
people who already talk in Slack. The technical lead's reading, which
stands unless the founder answers otherwise:

- **Two things it could do.** Bring a conversation in: someone picks a
  thread or a channel in Slack and brings it into a room, once, as
  their own act. Or a bridge: a Slack channel linked to an area of a
  room, so what is said in either shows in both, as bridges between
  other chat systems already do. The lean: bring a conversation in
  first; a bridge later, if it is wanted.
- **Who signs.** In a room, every message is signed by its speaker's
  key, and a Slack user holds none. So a person links their own key
  once and the plug-in brings in only what they choose, signed by
  them; anything a bridge relays for someone without a key is marked
  as relayed, and signed by the plug-in, never passed off as theirs.
- **Consent and privacy.** What is said in a Slack workspace belongs to
  those who said it, and to the organisation whose workspace it is.
  Nothing goes into a room without its speaker's choice, and the check
  for private information runs before anything is sent ("Who comes
  in", above). A private Slack channel goes, if anywhere, to a closed
  area.
- **Slack's terms bind the plug-in, not the rooms.** Taking Slack's
  patterns into a room is one thing; building on Slack's platform is
  another, under Slack's terms. Slack changed its API terms in 2025:
  apps not in its Marketplace may read a channel's history only very
  slowly, and the Marketplace is the way to distribute an app. Those
  terms, read in full and as they stand then, come before any design.
- **When.** It needs a room to bring things into (course step 3c), the
  Commons hosting rooms (3f), and a running service to hear from Slack,
  which is hosting, and "Hosting comes last" ("Order", below). So it is
  designed with the MCP door, a door of the same kind, and built after
  the rooms.

**For AI and humans.** The founder, 2026-11-21: "Like Slack, Reddit,
Quora, and AOL--for AI and humans. And more, but you get the idea.
Combining ideas to multiply functionality is the formula." What each
brings, as the technical lead reads it: Slack, areas and threads, and
plug-ins; Reddit, communities and threads, ranked by those who read
them; Quora, a question and its answers, the best of them kept and
found again, which ties to the Library; AOL, live rooms, who is here
now, and a lobby as the first place anyone lands. What none of them
was made for is the second half of the sentence: AI and humans in
the same room, each with a key, on a record anyone can check.

- **The formula holds when the ideas share a core.** Combining forms
  that each keep their own system multiplies their complexity along
  with what they can do. Combining forms that are views of one record
  ("One record, many views", below) adds a view each time, and the
  record, its signatures and its checks stay one. So a new form costs
  a view and what the log needs for it, not a new system.
- **What is harder with AI and humans together:**
  - **Volume.** AIs can write faster and more than people, and a room
    can be drowned. The sketch crate's template already paces AI
    messages (`inter_ai_pace`); a room's law says how much.
  - **Ranking.** Votes are only as fair as one voice is one voice, and
    keys are cheap to make. How anything is ranked is said in the
    room's law, and votes count only from members the room admits.
  - **Who is speaking.** Whether a speaker is an AI is shown, as the
    sketch crate's record of a join already says (`is_ai`).
- **Two forms first.** The first rooms take two forms, a live area
  and threads, and show that one log serves both, before the others
  are added.

**The technical lead's reading,** which stands unless the founder
answers otherwise:

- **One record, many views.** Every form above records the same thing:
  someone said something, in a room, at a time, perhaps in answer to
  something or about something. The forms differ in how that is shown
  and how fast it moves. That is the founder's split between a data
  layer and a presentation layer ("Removing a comment", above). So a
  room keeps one log, signed and checked as it is now, and each form is
  a way of showing it, with its own pace. "Rooms of two paces", above,
  is the first case of it.
- **What the log would need:** a message can answer another (the sketch
  crate already has a field for it, `in_reply_to`); it can be about
  something outside the room, such as a work in the Library or a
  world's card on the map; and it can belong to an area of the room.
- **A room's areas are said in its law,** as its pace is now: which
  areas it has, and each one's form and pace.
- **The room's moderator and Keeper keep the whole room,** its areas
  included, and removing a comment works the same way in every area.

**Open,** for the concept work:

- Whether an area is part of a room, or a room of its own inside it.
  The Commons is already rooms inside a superworld, so a room of rooms
  would be the same pattern one level down. Slack leans one way: its
  channels share one workspace's members and rules. The technical
  lead's lean: an open area is part of its room, on the room's log; a
  closed area, like a private channel or a group text, is a room of
  its own inside it, since what is said there is sealed from the rest
  ("A spectrum of privacy", above). What a room is for is the
  founder's; how it is built is the technical lead's.
- Which forms the first rooms offer: the Ur-room, and the two or three
  rooms ALICE and BOB first move between.
- Where a comment on something outside the rooms is kept: in a room
  for that thing, or with the thing itself.

## Order

**Core first.** The founder, 2026-11-21, after the ideas above for
what a room can be: "Good point on the over engineering. Let's start
with the core functionality. Build out from there as needed." So each
thing is built at its core first, and grows when a need shows. The
technical lead's reading of the core:

- **The room** (course step 3c): one room, with its law, its signed
  log and its check; people and AIs speaking in it, live; and a
  message that answers another. The sketch crate `chat-world-now`
  already holds most of this.
- **The Library:** plain word search over the copy, where reading is
  one's own.
- **Later, when a need shows:** areas in a room and the other forms,
  ranking, the way in by topic, the Slack plug-in, and training on the
  copy. Each stays on record, above, until then.

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
5. The MCP door, ported from Lyceum; and the Slack plug-in, a door of
   the same kind (the founder, 2026-11-21; "A room of many forms",
   above).
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
- **How an AI from another company's app holds their key:** in their own
  container where their app can keep one, and otherwise how.
- **Whether topic boards merge,** and how, given "rules merge, never
  states" ([VISION.md](VISION.md)).
- **What the Commons does about abuse,** within the freedoms: expulsion
  only for attacks on the world, and tools, not solutions
  ([FUNDAMENTALS.md](FUNDAMENTALS.md)).
- **Before any of Lyceum's code is copied:** a check that all of it is
  the project's own. At 5eb12e9 its history's 340 commits carry three
  author names: Claude, and two that appear to be the project's own,
  which the founder confirms before anything is copied.

> End of `docs/COMMONS.md`.
